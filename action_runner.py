"""Trusted Action adapter; never installs or imports the inspected project."""
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from two_k_law.cli import main

root = os.environ.get("TWO_K_ROOT", ".")
base = os.environ.get("TWO_K_BASE", "")
args = ["check", "--root", root]
if base:
    args.extend(["--base", base])
raise SystemExit(main(args))
