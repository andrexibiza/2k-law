"""Conservative, read-only source inventory. No target modules are imported."""
from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
import os
from pathlib import Path, PurePosixPath
import stat
from .gitio import LawError, blobs, git, tree

LIMIT = 2000
METRIC = "physical-crlf-cr-lf-v1"
POLICY = "2k-law-source-v1"
MAX_FILE = 32 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024
MAX_FILES = 50000
ROOT_EXCLUDES = {".git", ".venv", "venv", "node_modules", "dist", "build", "vendor", ".next"}
CACHE_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"}
DOCUMENTS = {".md", ".txt", ".rst", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".lock", ".ini", ".cfg", ".csv", ".tsv"}
BINARY = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".pdf", ".zip", ".gz", ".7z", ".tar", ".mp4", ".webm", ".mp3", ".wav", ".woff", ".woff2", ".ttf", ".otf", ".exe", ".dll", ".so", ".dylib", ".pyc", ".pyo", ".sqlite", ".db", ".bin"}
DOCUMENT_NAMES = {"license", "notice", "copying", "authors", "contributors", "changelog", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"}
CODE = {".py", ".pyi", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".rs", ".go", ".c", ".cc", ".cpp", ".h", ".hpp", ".java", ".kt", ".swift", ".cs", ".rb", ".php", ".sh", ".bash", ".zsh", ".bat", ".cmd", ".ps1", ".css", ".scss", ".html", ".astro", ".vue", ".svelte", ".sql", ".lua", ".r"}


def safe_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\0" in value:
        raise LawError("Expected a nonempty repository-relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ("", ".", "..") for p in value.split("/")) or ":" in value:
        raise LawError(f"Unsafe relative path: {value!r}")
    return value


def excluded(path: str, *, directory: bool = False) -> str | None:
    parts = PurePosixPath(path).parts
    if parts[0] in ROOT_EXCLUDES and (directory or len(parts) > 1 or parts[0] == ".git"):
        return "root dependency/build/vendor directory"
    if any(part in CACHE_DIRS for part in (parts if directory else parts[:-1])):
        return "dependency/cache directory"
    if directory:
        return None
    name = parts[-1].lower()
    suffix = PurePosixPath(name).suffix
    if name in DOCUMENT_NAMES or suffix in DOCUMENTS:
        return "non-code document/configuration"
    if suffix in BINARY:
        return "known binary asset"
    return None


def count_lines(data: bytes) -> int:
    if not data:
        return 0
    return data.count(b"\n") + data.count(b"\r") - data.count(b"\r\n") + int(not data.endswith((b"\r", b"\n")))


@dataclass
class Inventory:
    files: dict[str, dict] = field(default_factory=dict)
    exclusions: dict[str, str] = field(default_factory=dict)
    bytes_read: int = 0

    def add(self, path: str, data: bytes) -> None:
        self.bytes_read += len(data)
        if self.bytes_read > MAX_TOTAL or len(data) > MAX_FILE:
            raise LawError("Source byte budget exceeded; inventory is incomplete")
        if data.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\0" in data:
            if PurePosixPath(path).suffix.lower() in CODE or data.startswith((b"\xff\xfe", b"\xfe\xff")):
                raise LawError(f"Unsupported source encoding or NUL bytes: {path}")
            self.exclusions[path] = "binary content (NUL detected)"
            return
        self.files[path] = {"lines": count_lines(data), "sha256": sha256(data).hexdigest()}


def is_link(st: os.stat_result) -> bool:
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, "st_file_attributes", 0) & 0x400)


def project_root(value: str | Path) -> Path:
    path = Path(value).absolute()
    try:
        st = path.lstat()
    except OSError as exc:
        raise LawError(f"Root is unavailable: {path}") from exc
    if is_link(st) or not stat.S_ISDIR(st.st_mode):
        raise LawError("Root must be an ordinary directory, not a symlink/reparse point")
    return path.resolve()


def scan_worktree(root: Path) -> Inventory:
    result = Inventory()
    seen = set()
    entries = 0
    def fail(error):
        raise LawError(f"Directory enumeration failed: {error}")
    for current, dirs, names in os.walk(root, followlinks=False, onerror=fail):
        for name in sorted(dirs + names):
            entries += 1
            if entries > MAX_FILES:
                raise LawError("Entry budget exceeded; inventory is incomplete")
            item = Path(current) / name
            relative = item.relative_to(root).as_posix()
            safe_path(relative)
            reason = excluded(relative, directory=name in dirs)
            if reason:
                result.exclusions[relative] = reason
                if name in dirs:
                    dirs.remove(name)
                continue
            try:
                before = item.lstat()
                if is_link(before):
                    raise LawError(f"Unsupported symlink/reparse point: {relative}")
                if stat.S_ISDIR(before.st_mode):
                    continue
                if not stat.S_ISREG(before.st_mode):
                    raise LawError(f"Unsupported source object: {relative}")
                if before.st_size > MAX_FILE:
                    raise LawError(f"Source exceeds byte budget: {relative}")
                data = item.read_bytes()
                after = item.lstat()
                if is_link(after) or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
                    raise LawError(f"Source changed during scan: {relative}")
            except OSError as exc:
                raise LawError(f"Source read failed: {relative}: {exc}") from exc
            seen.add(relative)
            result.add(relative, data)
    if (root / ".git").exists():
        top = Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve()
        if top != root:
            raise LawError("Selected root does not match its Git repository")
        for raw in git(root, "ls-files", "-z").split(b"\0"):
            if raw:
                path = raw.decode("utf-8", "strict")
                if not excluded(path) and path not in seen:
                    raise LawError(f"Tracked source missing from inventory: {path}")
    result.files = dict(sorted(result.files.items()))
    result.exclusions = dict(sorted(result.exclusions.items()))
    return result


def scan_tree(root: Path, pin: str) -> Inventory:
    result = Inventory()
    selected = []
    total = 0
    records = tree(root, pin)
    if len(records) > MAX_FILES:
        raise LawError("Base entry budget exceeded")
    for path, mode, oid, size in records:
        safe_path(path)
        reason = excluded(path)
        if reason:
            result.exclusions[path] = reason
            continue
        if mode not in ("100644", "100755"):
            raise LawError(f"Unsupported Git source mode {mode}: {path}")
        total += size
        if size < 0 or size > MAX_FILE or total > MAX_TOTAL:
            raise LawError("Base source byte budget exceeded")
        selected.append((path, oid, size))
    for (path, _, _), data in zip(selected, blobs(root, [(oid, size) for _, oid, size in selected]), strict=True):
        result.add(path, data)
    return result
