"""Small JSON-speaking CLI; exit 0 pass, 1 violation, 2 invalid/incomplete."""
from __future__ import annotations
import argparse
import json
import sys
from . import __version__
from .gitio import LawError
from .inventory import project_root
from .ratchet import baseline, check
from .seams import byte_window, runtime_seams


def parser():
    p = argparse.ArgumentParser(description="Axl's 2K Law: size ratchet and explicit extraction evidence")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)
    for command in ("check", "baseline", "bytes", "seam"):
        child = sub.add_parser(command)
        child.add_argument("--root", default=".")
        if command == "check":
            child.add_argument("--base", help="Independently accepted full commit SHA; required for legacy debt")
        if command == "bytes":
            child.add_argument("--base", required=True)
            child.add_argument("--source", required=True)
            child.add_argument("--start", required=True, type=int)
            child.add_argument("--end", required=True, type=int)
            child.add_argument("--target", required=True)
            child.add_argument("--target-start", required=True, type=int)
        if command == "seam":
            child.add_argument("--spec", required=True)
            child.add_argument("--allow-execution", action="store_true")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        root = project_root(args.root)
        if args.command == "baseline":
            result = baseline(root)
        elif args.command == "check":
            result = check(root, args.base)
        elif args.command == "bytes":
            result = byte_window(root, args.base, args.source, args.start, args.end, args.target, args.target_start)
        else:
            result = runtime_seams(root, args.spec, args.allow_execution)
        print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=True))
        return 1 if result.get("status") == "fail" else 0
    except (LawError, OSError, UnicodeError, ImportError, AttributeError) as exc:
        print(json.dumps({"status": "error", "complete": False, "error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
