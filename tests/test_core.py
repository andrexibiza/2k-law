import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from two_k_law.gitio import LawError
from two_k_law.inventory import count_lines, project_root, scan_worktree
from two_k_law.ratchet import baseline, check, parse_manifest


class Project(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="two-k-law-")
        self.root = Path(self.temp.name).resolve()
        self.addCleanup(self.temp.cleanup)

    def put(self, name, data):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode())
        return p

    def git(self, *args):
        result = subprocess.run(["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + str(self.root / "no-hooks"), "-C", str(self.root), *args], capture_output=True, check=True)
        return result.stdout.decode().strip()

    def init(self):
        self.git("init", "-q")
        self.git("config", "user.name", "Test Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "core.autocrlf", "false")

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        return self.git("rev-parse", "HEAD")

    def ledger(self):
        self.put(".2k-law.json", json.dumps(baseline(self.root)))


class Counting(Project):
    def test_newlines(self):
        for data, expected in [(b"", 0), (b"x", 1), (b"x\n", 1), (b"\n", 1), (b"x\r", 1), (b"x\r\ny", 2), (b"\r\n\r\n", 2), (b"a\rb\nc\r\nd", 4)]:
            with self.subTest(data=data): self.assertEqual(count_lines(data), expected)

    def test_ceiling_boundary(self):
        self.put("code.py", b"# x\n" * 2000)
        self.assertEqual(check(self.root)["status"], "pass")
        self.put("code.py", b"# x\n" * 2001)
        self.assertEqual(check(self.root)["status"], "fail")

    def test_cr_only_cannot_hide_giant(self):
        self.put("code.py", b"# x\r" * 2001)
        self.assertEqual(check(self.root)["files"]["code.py"]["lines"], 2001)
        self.assertEqual(check(self.root)["status"], "fail")

    def test_unknown_text_and_extensionless_count(self):
        for name in ["command", "program.newlang", "mod.mjs", "test.java"]:
            self.put(name, "x\n" * 2001)
        self.assertEqual(check(self.root)["debt_files"], 4)

    def test_documents_and_binary_are_accounted(self):
        self.put("README.md", "word\n" * 2001)
        self.put("image.png", b"binary")
        result = check(self.root)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["excluded_entries"], 2)

    def test_nested_owned_build_is_not_excluded(self):
        self.put("src/build/owner.py", "x\n" * 2001)
        self.assertEqual(check(self.root)["status"], "fail")

    def test_directory_document_suffix_not_exclusion(self):
        self.put("source.json/owner.py", "x\n" * 2001)
        self.assertEqual(check(self.root)["status"], "fail")

    def test_absolute_build_ancestor_does_not_hide_source(self):
        child = self.root / "build" / "project"
        child.mkdir(parents=True)
        (child / "code.py").write_text("x\n" * 2001)
        self.assertEqual(check(child)["status"], "fail")

    def test_prefix_does_not_exclude(self):
        self.put("node_modules_owned/code.py", "x\n" * 2001)
        self.assertEqual(check(self.root)["status"], "fail")

    def test_root_aliases_are_canonicalized(self):
        (self.root / "inner").mkdir()
        self.assertEqual(project_root(self.root / "inner" / ".."), self.root)

    def test_missing_root_errors(self):
        with self.assertRaises(LawError): project_root(self.root / "absent")

    def test_nul_in_source_errors(self):
        self.put("code.py", b"x\0y")
        with self.assertRaises(LawError): scan_worktree(self.root)

    def test_utf16_errors(self):
        self.put("source.unknown", "x\n".encode("utf-16"))
        with self.assertRaises(LawError): scan_worktree(self.root)

    def test_ignored_source_is_counted(self):
        self.init()
        self.put(".gitignore", "ignored.py\n")
        self.put("ignored.py", "x\n" * 2001)
        self.assertEqual(check(self.root)["status"], "fail")

    def test_tracked_missing_source_errors(self):
        self.init()
        file = self.put("code.py", "x\n")
        self.commit()
        file.unlink()
        with self.assertRaisesRegex(LawError, "Tracked source missing"): check(self.root)

    def test_source_symlink_errors_when_available(self):
        outside = self.put("target.md", "x\n" * 2001)
        try: (self.root / "link.py").symlink_to(outside)
        except OSError: self.skipTest("Host does not allow symbolic links")
        with self.assertRaises(LawError): check(self.root)


class Ratchet(Project):
    def adopted(self):
        self.init()
        self.put("old.py", "x\n" * 2010)
        self.ledger()
        return self.commit()

    def test_baseline_proposes_without_writing(self):
        self.put("old.py", "x\n" * 2010)
        self.assertEqual(baseline(self.root)["files"], {"old.py": 2010})
        self.assertFalse((self.root / ".2k-law.json").exists())

    def test_debt_needs_base(self):
        self.adopted()
        self.assertEqual(check(self.root)["status"], "fail")

    def test_same_state_passes_with_explicit_debt(self):
        pin = self.adopted()
        result = check(self.root, pin)
        self.assertEqual(result["status"], "pass_with_debt")
        self.assertFalse(result["ceiling_compliant"])

    def test_one_line_growth_fails_even_with_inflated_ledger(self):
        pin = self.adopted()
        self.put("old.py", "x\n" * 2011)
        self.ledger()
        self.assertIn("legacy_growth", [x["code"] for x in check(self.root, pin)["findings"]])

    def test_new_self_exemption_fails(self):
        pin = self.adopted()
        self.put("new.py", "x\n" * 2001)
        self.ledger()
        self.assertIn("new_allowance", [x["code"] for x in check(self.root, pin)["findings"]])

    def test_shrink_requires_exact_ledger(self):
        pin = self.adopted()
        self.put("old.py", "x\n" * 2005)
        self.assertEqual(check(self.root, pin)["status"], "fail")
        self.ledger()
        self.assertEqual(check(self.root, pin)["status"], "pass_with_debt")

    def test_shrink_then_regrowth_fails_at_new_base(self):
        self.adopted()
        self.put("old.py", "x\n" * 2005)
        self.ledger()
        pin = self.commit()
        self.put("old.py", "x\n" * 2006)
        self.ledger()
        self.assertEqual(check(self.root, pin)["status"], "fail")

    def test_retirement_removes_entry(self):
        pin = self.adopted()
        self.put("old.py", "x\n" * 2000)
        self.assertEqual(check(self.root, pin)["status"], "fail")
        self.ledger()
        self.assertEqual(check(self.root, pin)["status"], "pass")

    def test_oversized_rename_not_new_allowance(self):
        pin = self.adopted()
        self.git("mv", "old.py", "renamed.py")
        self.ledger()
        self.assertEqual(check(self.root, pin)["status"], "fail")

    def test_deleted_file_retires(self):
        pin = self.adopted()
        self.git("rm", "old.py")
        self.ledger()
        self.assertEqual(check(self.root, pin)["status"], "pass")

    def test_invalid_base_is_error(self):
        self.init()
        with self.assertRaises(LawError): check(self.root, "main")

    def test_base_ledger_cannot_be_stale(self):
        pin = self.adopted()
        self.put("old.py", "x\n" * 2005)
        stale = self.commit()
        with self.assertRaises(LawError): check(self.root, stale)

    def test_manifest_strictness(self):
        for data in [b'{"version":1,"limit":2000,"files":{},"extra":1}', b'{"version":1,"version":1,"limit":2000,"files":{}}', b'{"version":true,"limit":2000,"files":{}}', b'{"version":1,"limit":2000,"files":{"../x.py":3000}}', b'{"version":1,"limit":2000,"files":{"x.py":true}}', b'{"version":1,"limit":2000,"files":{"x.py":2000}}', b'NaN']:
            with self.subTest(data=data), self.assertRaises(LawError): parse_manifest(data)
