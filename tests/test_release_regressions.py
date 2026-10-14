import json
import os
from pathlib import Path
import subprocess
import sys
from test_core import Project
from two_k_law.gitio import LawError
from two_k_law.ratchet import check, parse_manifest

REPO = Path(__file__).resolve().parents[1]


class ReleaseRegressions(Project):
    def test_git_symlink_placeholder_is_not_regular_source(self):
        self.init()
        self.git("config", "core.symlinks", "false")
        self.put("target.md", "x\n" * 2001)
        self.put("alias.py", "target.md")
        oid = self.git("hash-object", "-w", "alias.py")
        self.git("update-index", "--add", "--cacheinfo", "120000", oid, "alias.py")
        self.git("add", "target.md")
        self.git("commit", "-qm", "Git symlink represented as ordinary checkout file")
        self.assertFalse((self.root / "alias.py").is_symlink())
        with self.assertRaisesRegex(LawError, "mode"):
            check(self.root)

    def test_large_json_integer_uses_input_error_protocol(self):
        payload = b'{"version":1,"limit":2000,"files":{"a.py":' + b'1' * 5000 + b'}}'
        self.put(".2k-law.json", payload)
        with self.assertRaises(LawError):
            parse_manifest(payload)
        result = subprocess.run([sys.executable, "-I", "-m", "two_k_law", "check", "--root", str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stderr)["status"], "error")
        self.assertFalse(json.loads(result.stderr)["complete"])

    def test_nested_root_cannot_borrow_ancestor_allowance(self):
        self.init()
        self.put("legacy.py", "x\n" * 2010)
        self.ledger()
        base = self.commit()
        self.put("new-project/legacy.py", "x\n" * 2005)
        self.put("new-project/.2k-law.json", json.dumps({"version": 1, "limit": 2000, "files": {"legacy.py": 2005}}))
        nested = self.root / "new-project"
        result = subprocess.run([sys.executable, "-I", "-m", "two_k_law", "check", "--root", str(nested), "--base", base], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertFalse(json.loads(result.stderr)["complete"])
        env = os.environ.copy()
        env.update(TWO_K_ROOT=str(nested), TWO_K_BASE=base)
        result = subprocess.run([sys.executable, "-I", str(REPO / "action_runner.py")], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertFalse(json.loads(result.stderr)["complete"])
        self.assertEqual(check(self.root, base)["status"], "fail")
