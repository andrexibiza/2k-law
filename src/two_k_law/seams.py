"""Explicit, bounded evidence: byte relocation and opted-in Python identity."""
from __future__ import annotations
from hashlib import sha256
import importlib
import inspect
from pathlib import Path
import sys
from .gitio import LawError, blobs, tree
from .inventory import safe_path
from .ratchet import read_local, strict_json


def byte_window(root: Path, base: str, source: str, start: int, end: int, target: str, target_start: int) -> dict:
    safe_path(source)
    safe_path(target)
    if start < 1 or end < start or target_start < 1:
        raise LawError("Line windows are inclusive and 1-based")
    rows = [r for r in tree(root, base) if r[0] == source]
    if not rows or rows[0][1] not in ("100644", "100755") or rows[0][3] > 32 * 1024 * 1024:
        raise LawError("Source is not a bounded regular blob at the pin")
    _, _, oid, size = rows[0]
    before = blobs(root, [(oid, size)])[0].splitlines(keepends=True)
    after = read_local(root, target).splitlines(keepends=True)
    length = end - start + 1
    if end > len(before) or target_start - 1 + length > len(after):
        raise LawError("Declared source/target window exceeds the file")
    original = b"".join(before[start - 1:end])
    moved = b"".join(after[target_start - 1:target_start - 1 + length])
    return {"status": "pass" if original == moved else "fail", "kind": "byte_window",
            "base": base, "source": source, "start": start, "end": end, "target": target,
            "target_start": target_start, "source_sha256": sha256(original).hexdigest(),
            "target_sha256": sha256(moved).hexdigest(), "bytes": len(original),
            "boundary": "Exact raw bytes only; not runtime or behavioral equivalence"}


def endpoint(root: Path, spec: str):
    if not isinstance(spec, str) or spec.count(":") != 1:
        raise LawError("Endpoint must be module:qualified_name")
    module_name, names = spec.split(":")
    if not all(p.isidentifier() for p in module_name.split(".")) or not all(p.isidentifier() for p in names.split(".")):
        raise LawError("Invalid endpoint identifier")
    module = importlib.import_module(module_name)
    filename = getattr(module, "__file__", None)
    if not filename or not Path(filename).resolve().is_relative_to(root):
        raise LawError(f"Endpoint resolved outside the selected root: {spec}")
    value = module
    for name in names.split("."):
        value = getattr(value, name)
    return value


def inherited(original, moved, name: str) -> tuple[bool, str]:
    if not inspect.isclass(original) or not inspect.isclass(moved):
        raise LawError("Inherited endpoints must resolve to classes")
    if not name.isidentifier():
        raise LawError("Member must be an identifier")
    if name in original.__dict__ or name not in moved.__dict__:
        return False, "original shadows the member or moved class does not own it"
    owner = next((c for c in original.__mro__ if name in c.__dict__), None)
    if owner is not moved:
        return False, "declared moved class is not the actual MRO owner"
    raw = moved.__dict__[name]
    resolved = getattr(original, name)
    if isinstance(raw, classmethod):
        ok = inspect.ismethod(resolved) and resolved.__func__ is raw.__func__ and resolved.__self__ is original
    elif isinstance(raw, staticmethod):
        ok = resolved is raw.__func__
    elif isinstance(raw, property):
        ok = inspect.getattr_static(original, name) is raw
    elif inspect.isfunction(raw):
        ok = resolved is raw
    else:
        raise LawError("Only Python functions, staticmethods, classmethods and properties are supported")
    return ok, "descriptor-aware identity and MRO ownership"


def runtime_seams(root: Path, spec_path: str, allow_execution: bool = False) -> dict:
    if not allow_execution:
        raise LawError("Runtime seams execute target imports. Explicit --allow-execution is required; this is not a sandbox")
    spec = strict_json(read_local(root, spec_path, 1024 * 1024))
    if not isinstance(spec, dict) or set(spec) != {"version", "checks"} or type(spec["version"]) is not int or spec["version"] != 1:
        raise LawError("Seam specification requires version=1 and checks")
    if not isinstance(spec["checks"], list) or not spec["checks"] or len(spec["checks"]) > 1000:
        raise LawError("Seam checks must be a nonempty list (at most 1000)")
    for row in spec["checks"]:
        if not isinstance(row, dict) or row.get("kind") not in ("object", "inherited"):
            raise LawError("Unknown seam kind")
        expected = {"kind", "original", "moved"} | ({"member"} if row["kind"] == "inherited" else set())
        if set(row) != expected or not all(isinstance(v, str) for v in row.values()):
            raise LawError("Unexpected or non-string seam fields")
    results = []
    sys.path.insert(0, str(root))
    try:
        importlib.invalidate_caches()
        for row in spec["checks"]:
            original = endpoint(root, row["original"])
            moved = endpoint(root, row["moved"])
            if row["kind"] == "object":
                if not (inspect.isfunction(original) or inspect.isclass(original)) or not (inspect.isfunction(moved) or inspect.isclass(moved)):
                    raise LawError("Object seams require functions or classes; scalar identity is not extraction evidence")
                ok, detail = original is moved, "same function or class object through both namespaces"
            else:
                ok, detail = inherited(original, moved, row["member"])
            results.append({**row, "passed": ok, "detail": detail})
    finally:
        sys.path.pop(0)
    return {"status": "pass" if all(r["passed"] for r in results) else "fail", "kind": "runtime_identity",
            "checks": results, "boundary": "Imports execute project code. Identity is not proof of patch effects, initialization safety or behavior."}
