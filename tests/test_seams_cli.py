import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from test_core import Project
from two_k_law.cli import main
from two_k_law.gitio import LawError
from two_k_law.seams import byte_window, inherited, runtime_seams

REPO = Path(__file__).resolve().parents[1]


class Seams(Project):
    def test_raw_bytes_and_line_endings(self):
        self.init()
        self.put("old.py", b"# header\ndef f():\n    return 1\n")
        pin = self.commit()
        self.put("moved.py", b"def f():\n    return 1\n")
        self.assertEqual(byte_window(self.root, pin, "old.py", 2, 3, "moved.py", 1)["status"], "pass")
        self.put("moved.py", b"def f():\r\n    return 1\r\n")
        self.assertEqual(byte_window(self.root, pin, "old.py", 2, 3, "moved.py", 1)["status"], "fail")
        with self.assertRaises(LawError): byte_window(self.root, pin, "old.py", 1, 9, "moved.py", 1)

    def test_descriptor_aware_inheritance(self):
        class Mixin:
            def plain(self): return 1
            @staticmethod
            def static(): return 2
            @classmethod
            def cls(cls): return cls
            @property
            def prop(self): return 4
        class Original(Mixin): pass
        for name in ("plain", "static", "cls", "prop"):
            with self.subTest(name=name): self.assertTrue(inherited(Original, Mixin, name)[0])
        class Shadow(Mixin): plain = Mixin.plain
        self.assertFalse(inherited(Shadow, Mixin, "plain")[0])
        class Other:
            def plain(self): return 5
        class Wrong(Other, Mixin): pass
        self.assertFalse(inherited(Wrong, Mixin, "plain")[0])

    def test_opt_in_precedes_import(self):
        self.put("seams.json", json.dumps({"version":1,"checks":[{"kind":"object","original":"original:f","moved":"moved:f"}]}))
        self.put("original.py", "raise RuntimeError('must not import')")
        with self.assertRaisesRegex(LawError, "allow-execution"):
            runtime_seams(self.root, "seams.json")

    def test_real_runtime_subprocess(self):
        self.put("moved.py", "def f(): return 1\n")
        self.put("original.py", "from moved import f\n")
        self.put("seams.json", json.dumps({"version":1,"checks":[{"kind":"object","original":"original:f","moved":"moved:f"}]}))
        command = [sys.executable, "-I", "-m", "two_k_law", "seam", "--root", str(self.root), "--spec", "seams.json", "--allow-execution"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "pass")
        self.put("original.py", "def f(): return 1\n")
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)

    def test_scalar_identity_rejected(self):
        self.put("numbers.py", "x = 1\n")
        self.put("seams.json", json.dumps({"version":1,"checks":[{"kind":"object","original":"numbers:x","moved":"numbers:x"}]}))
        result = subprocess.run([sys.executable,"-I","-m","two_k_law","seam","--root",str(self.root),"--spec","seams.json","--allow-execution"],capture_output=True,text=True)
        self.assertEqual(result.returncode, 2, result.stderr)


class CLI(Project):
    def run_cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = main([*args, "--root", str(self.root)])
        return result, stdout.getvalue(), stderr.getvalue()

    def test_exit_codes_and_json(self):
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["status"], "pass")
        self.put("giant.py", "x\n" * 2001)
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["status"], "fail")
        self.put(".2k-law.json", "invalid")
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(err)["complete"])

    def test_check_does_not_import_project(self):
        self.put("danger.py", "raise RuntimeError('must not import')\n")
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_action_adapter_matches_cli_and_rejects_injection(self):
        self.put("giant.py", "x\n" * 2001)
        env = os.environ.copy()
        env.update(TWO_K_ROOT=str(self.root), TWO_K_BASE="")
        result = subprocess.run([sys.executable,"-I",str(REPO/"action_runner.py")],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout), json.loads(self.run_cli("check")[1]))
        env["TWO_K_BASE"] = "$(touch should-not-exist)"
        self.init()
        result = subprocess.run([sys.executable,"-I",str(REPO/"action_runner.py")],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root/"should-not-exist").exists())

    def test_checks_do_not_mutate_source(self):
        self.put("example.py", "print('hello')\n")
        before = {p.name:p.read_bytes() for p in self.root.iterdir()}
        self.run_cli("check")
        self.assertEqual(before, {p.name:p.read_bytes() for p in self.root.iterdir()})
