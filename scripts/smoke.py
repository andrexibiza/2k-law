"""Exercise the installed package's documented adoption and rejection path."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def run(command, cwd, expected=0):
    p = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if p.returncode != expected:
        raise AssertionError((command, p.returncode, p.stdout, p.stderr))
    return p.stdout


with tempfile.TemporaryDirectory(prefix="2k-law-tutorial-") as temp:
    root = Path(temp)
    cli = [sys.executable, "-I", "-m", "two_k_law"]
    (root / "legacy.py").write_bytes(b"# measured debt\n" * 2001)
    first = json.loads(run([*cli, "check", "--root", str(root)], root, 1))
    assert first["status"] == "fail" and first["debt_files"] == 1
    proposal = run([*cli, "baseline", "--root", str(root)], root)
    (root / ".2k-law.json").write_text(proposal, encoding="utf-8")
    git = ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + str(root / "no-hooks")]
    for args in [("init", "-q"), ("config", "user.name", "Tutorial fixture"), ("config", "user.email", "tutorial@example.invalid"), ("add", "."), ("commit", "-qm", "Accepted measured baseline")]:
        run([*git, *args], root)
    pin = run([*git, "rev-parse", "HEAD"], root).strip()
    accepted = json.loads(run([*cli, "check", "--root", str(root), "--base", pin], root))
    assert accepted["status"] == "pass_with_debt" and not accepted["ceiling_compliant"]
    (root / "legacy.py").write_bytes(b"# measured debt\n" * 2002)
    (root / ".2k-law.json").write_text(run([*cli, "baseline", "--root", str(root)], root), encoding="utf-8")
    rejected = json.loads(run([*cli, "check", "--root", str(root), "--base", pin], root, 1))
    assert any(f["code"] == "legacy_growth" for f in rejected["findings"])
    (root / "legacy.py").write_bytes(b"# measured debt\n" * 2000)
    (root / ".2k-law.json").write_text(run([*cli, "baseline", "--root", str(root)], root), encoding="utf-8")
    retired = json.loads(run([*cli, "check", "--root", str(root), "--base", pin], root))
    assert retired["status"] == "pass" and retired["ceiling_compliant"]
    print(json.dumps({"tutorial": "PASS", "initial_violation": first["status"], "adopted": accepted["status"], "growth": rejected["status"], "retired": retired["status"]}))
