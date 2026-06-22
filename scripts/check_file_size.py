"""Fail when reviewable tracked files become unexpectedly large."""

from __future__ import annotations

import subprocess
from pathlib import Path

MAX_BYTES = 1_000_000
EXCLUDED_PREFIXES = (
    "artifacts/",
    "data/processed/",
)
EXCLUDED_SUFFIXES = (
    ".lock",
    ".pdf",
    ".parquet",
    ".png",
    ".jpg",
    ".jpeg",
)
EXCLUDED_FILES = {
    "uv.lock",
}


def _tracked_files() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files"], text=True)
    return [Path(line) for line in output.splitlines() if line]


def _is_excluded(path: Path) -> bool:
    normalized = path.as_posix()
    return (
        normalized in EXCLUDED_FILES
        or normalized.endswith(EXCLUDED_SUFFIXES)
        or normalized.startswith(EXCLUDED_PREFIXES)
    )


def main() -> int:
    oversized: list[tuple[Path, int]] = []
    for path in _tracked_files():
        if _is_excluded(path) or not path.exists():
            continue
        size = path.stat().st_size
        if size > MAX_BYTES:
            oversized.append((path, size))

    if oversized:
        print(f"Files exceed {MAX_BYTES:,} bytes:")
        for path, size in oversized:
            print(f"- {path}: {size:,} bytes")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
