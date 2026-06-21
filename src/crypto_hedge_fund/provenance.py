"""Hashing and source-control provenance helpers."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

UNKNOWN = "UNKNOWN"
_SOURCE_HASH_EXCLUDES = ("artifacts", "reports")


def file_sha256(path: str | Path) -> str:
    """Return the SHA-256 hex digest for a file."""
    file_path = Path(path)
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, tuple | list):
        return [_canonicalize(item) for item in value]
    if isinstance(value, set | frozenset):
        return [_canonicalize(item) for item in sorted(value, key=repr)]
    return value


def canonical_json(value: Mapping[str, Any] | Sequence[Any]) -> str:
    """Return deterministic JSON for hashable artifact metadata."""
    return json.dumps(_canonicalize(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_config_hash(config: Mapping[str, Any]) -> str:
    """Return a SHA-256 digest for a configuration mapping."""
    return hashlib.sha256(canonical_json(config).encode("utf-8")).hexdigest()


def git_commit(repo_root: str | Path | None = None, *, raise_on_error: bool = False) -> str:
    """Return the current Git commit hash, or UNKNOWN when unavailable."""
    cmd = ["git", "rev-parse", "HEAD"]
    try:
        completed = subprocess.run(
            cmd,
            cwd=Path(repo_root) if repo_root is not None else None,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        if raise_on_error:
            raise
        return UNKNOWN
    commit = completed.stdout.strip()
    return commit if commit else UNKNOWN


def git_worktree_dirty(repo_root: str | Path | None = None) -> bool:
    """Return whether Git reports uncommitted tracked or untracked changes."""
    try:
        completed = _run_git(
            ["status", "--porcelain", "--untracked-files=all"],
            repo_root=repo_root,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return bool(completed.stdout.strip())


def git_diff_sha256(repo_root: str | Path | None = None) -> str:
    """Return a deterministic hash of the uncommitted source state.

    The payload includes staged and unstaged tracked diffs against HEAD plus
    untracked, non-ignored source files. Generated artifacts and agent reports
    are excluded so regenerating outputs does not recursively change the source
    hash embedded in those outputs.
    """
    try:
        diff = _run_git(
            [
                "diff",
                "--binary",
                "HEAD",
                "--",
                ".",
                *[f":(exclude){path}" for path in _SOURCE_HASH_EXCLUDES],
            ],
            repo_root=repo_root,
        ).stdout.encode("utf-8")
        untracked = _run_git(
            [
                "ls-files",
                "--others",
                "--exclude-standard",
                "-z",
                "--",
                ".",
                *[f":(exclude){path}" for path in _SOURCE_HASH_EXCLUDES],
            ],
            repo_root=repo_root,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return UNKNOWN

    root = _repo_cwd(repo_root)
    digest = hashlib.sha256()
    digest.update(b"tracked-diff\0")
    digest.update(diff)
    digest.update(b"\0untracked-files\0")
    paths = sorted(path for path in untracked.split("\0") if path)
    for relative in paths:
        file_path = root / relative
        if not file_path.is_file():
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_sha256(file_path).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _repo_cwd(repo_root: str | Path | None) -> Path:
    return Path(repo_root) if repo_root is not None else Path.cwd()


def _run_git(
    args: list[str],
    *,
    repo_root: str | Path | None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=_repo_cwd(repo_root),
        check=True,
        capture_output=True,
        text=True,
    )
