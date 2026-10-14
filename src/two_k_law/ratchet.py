"""A legacy allowance is measured debt, never a candidate-owned permission."""
from __future__ import annotations
import json
from pathlib import Path
from .gitio import LawError, blobs, tree
from .inventory import LIMIT, METRIC, POLICY, Inventory, is_link, safe_path, scan_tree, scan_worktree

MANIFEST = ".2k-law.json"


def strict_json(data: bytes):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise LawError(f"Duplicate JSON key: {key}")
            out[key] = value
        return out
    def bad(value):
        raise LawError(f"Non-finite JSON value: {value}")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=bad)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise LawError(f"Invalid UTF-8 JSON: {exc}") from exc


def read_local(root: Path, name: str, max_bytes: int = 32 * 1024 * 1024) -> bytes:
    safe_path(name)
    current = root
    for part in name.split("/"):
        current = current / part
        if is_link(current.lstat()):
            raise LawError(f"Symlink/reparse input refused: {name}")
    if not current.is_file() or current.stat().st_size > max_bytes:
        raise LawError(f"Input is not a bounded regular file: {name}")
    return current.read_bytes()


def parse_manifest(data: bytes | None) -> dict[str, int]:
    if data is None:
        return {}
    if len(data) > 1024 * 1024:
        raise LawError("Manifest exceeds 1 MiB")
    obj = strict_json(data)
    if not isinstance(obj, dict) or set(obj) != {"version", "limit", "files"}:
        raise LawError("Manifest requires exactly version, limit, files")
    if type(obj["version"]) is not int or obj["version"] != 1 or type(obj["limit"]) is not int or obj["limit"] != LIMIT:
        raise LawError("Unsupported manifest version or ceiling")
    if not isinstance(obj["files"], dict):
        raise LawError("Manifest files must be an object")
    for name, count in obj["files"].items():
        safe_path(name)
        if type(count) is not int or count <= LIMIT:
            raise LawError(f"Legacy count must be an integer above {LIMIT}: {name}")
    return obj["files"]


def current_manifest(root: Path) -> dict[str, int]:
    p = root / MANIFEST
    if not p.exists() and not p.is_symlink():
        return {}
    return parse_manifest(read_local(root, MANIFEST, 1024 * 1024))


def base_manifest(root: Path, base: str) -> dict[str, int]:
    found = [row for row in tree(root, base) if row[0] == MANIFEST]
    if not found:
        return {}
    _, mode, oid, size = found[0]
    if mode not in ("100644", "100755") or size > 1024 * 1024:
        raise LawError("Base manifest must be a bounded regular blob")
    return parse_manifest(blobs(root, [(oid, size)])[0])


def debt(inventory: Inventory) -> dict[str, int]:
    return {name: row["lines"] for name, row in inventory.files.items() if row["lines"] > LIMIT}


def baseline(root: Path) -> dict:
    return {"version": 1, "limit": LIMIT, "files": debt(scan_worktree(root))}


def check(root: Path, base: str | None = None) -> dict:
    current = scan_worktree(root)
    remaining = debt(current)
    ledger = current_manifest(root)
    findings = []
    def issue(code, path, **details):
        findings.append({"code": code, "path": path, **details})
    for path in sorted(set(ledger) | set(remaining)):
        if path in ledger and path not in remaining:
            issue("stale_allowance", path, recorded=ledger[path])
        elif path in remaining and path not in ledger:
            issue("untracked_debt", path, lines=remaining[path])
        elif ledger[path] != remaining[path]:
            issue("stale_measurement", path, recorded=ledger[path], measured=remaining[path])
    previous = None
    if base:
        old = scan_tree(root, base)
        accepted = base_manifest(root, base)
        previous = debt(old)
        if accepted != previous:
            raise LawError("Accepted base ledger does not exactly enumerate its measured debt; choose a reviewed adoption commit")
        for path in sorted(remaining):
            if path not in accepted:
                issue("new_legacy_debt", path, lines=remaining[path])
            elif remaining[path] > previous[path]:
                issue("legacy_growth", path, before=previous[path], after=remaining[path])
        for path in sorted(set(ledger) - set(accepted)):
            issue("new_allowance", path)
    elif remaining:
        issue("trusted_base_required", "", message="Legacy debt requires --base with an independently accepted full commit SHA")
    return {
        "tool": "2k-law", "schema_version": 1, "policy": POLICY, "metric": METRIC,
        "complete": True, "status": "fail" if findings else ("pass_with_debt" if remaining else "pass"),
        "base": base, "ratchet_verified": bool(base), "ceiling_compliant": not remaining,
        "source_files": len(current.files), "excluded_entries": len(current.exclusions),
        "debt_files": len(remaining), "excess_lines": sum(n - LIMIT for n in remaining.values()),
        "previous_debt_files": len(previous) if previous is not None else None,
        "files": current.files, "exclusions": current.exclusions, "findings": findings,
    }
