"""Read exact Git objects without replacement refs or checkout filters."""
from __future__ import annotations
import os
from pathlib import Path
import re
import subprocess

class LawError(ValueError):
    """Invalid input or an incomplete observation; never a passing result."""


def git(root: Path, *args: str, input: bytes | None = None) -> bytes:
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(key, None)
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0")
    try:
        result = subprocess.run(
            ["git", "--no-replace-objects", "-C", str(root), *args], input=input,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LawError(f"Git read failed: {exc}") from exc
    if result.returncode:
        raise LawError("Git read failed: " + result.stderr.decode("utf-8", "replace").strip())
    return result.stdout


def commit(root: Path, value: str) -> str:
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value):
        raise LawError("--base must be a full lowercase commit SHA, not a branch or abbreviation")
    top = Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if top != root.resolve():
        raise LawError("Base-backed checks require --root to equal the Git repository top-level")
    actual = git(root, "rev-parse", "--verify", value + "^{commit}").decode().strip()
    if actual != value:
        raise LawError("The requested base is not that exact commit")
    return actual


def tree(root: Path, pin: str) -> list[tuple[str, str, str, int]]:
    commit(root, pin)
    records = []
    for record in git(root, "ls-tree", "-rzl", "--full-tree", pin).split(b"\0"):
        if not record:
            continue
        meta, raw_path = record.split(b"\t", 1)
        mode, kind, oid, size = meta.split()
        try:
            path = raw_path.decode("utf-8", "strict")
        except UnicodeError as exc:
            raise LawError("Git path is not UTF-8") from exc
        records.append((path, mode.decode(), oid.decode(), int(size) if size != b"-" else -1))
    return records


def blobs(root: Path, objects: list[tuple[str, int]]) -> list[bytes]:
    if not objects:
        return []
    response = git(root, "cat-file", "--batch", input=("\n".join(oid for oid, _ in objects) + "\n").encode())
    offset = 0
    contents = []
    for expected, expected_size in objects:
        end = response.find(b"\n", offset)
        fields = response[offset:end].split()
        if end < 0 or len(fields) != 3 or fields[0].decode() != expected or fields[1] != b"blob":
            raise LawError("Missing or unexpected Git blob in batch response")
        size = int(fields[2])
        if size != expected_size:
            raise LawError("Git blob size changed from tree inventory")
        start = end + 1
        if start + size >= len(response) or response[start + size:start + size + 1] != b"\n":
            raise LawError("Truncated Git blob")
        contents.append(response[start:start + size])
        offset = start + size + 1
    if offset != len(response):
        raise LawError("Unexpected trailing Git output")
    return contents
