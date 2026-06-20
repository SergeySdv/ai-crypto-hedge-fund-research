"""Configuration loading and repository-relative path resolution."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_MARKERS = ("AGENTS.md", ".git")
DEFAULT_CONFIG_PATH = Path("configs/default.yaml")
FAST_CONFIG_PATH = Path("configs/fast.yaml")


def find_repo_root(start: str | Path | None = None) -> Path:
    """Locate the repository root by walking upward from ``start``."""
    current = Path(start).resolve() if start is not None else PACKAGE_ROOT
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if all((candidate / marker).exists() for marker in REPO_MARKERS):
            return candidate
    msg = f"Could not find repository root from {current}"
    raise FileNotFoundError(msg)


def resolve_repo_path(path: str | Path, *, repo_root: str | Path | None = None) -> Path:
    """Resolve a path relative to the repository root unless already absolute."""
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return find_repo_root(repo_root) / candidate


def read_yaml(path: str | Path) -> dict[str, Any]:
    """Read a YAML mapping from disk."""
    resolved = Path(path)
    with resolved.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        msg = f"YAML file must contain a mapping: {resolved}"
        raise TypeError(msg)
    return data


def deep_merge(
    base: Mapping[str, Any],
    overlay: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Recursively merge ``overlay`` onto ``base`` without mutating either input."""
    result: dict[str, Any] = deepcopy(dict(base))
    if overlay is None:
        return result
    for key, value in overlay.items():
        existing = result.get(key)
        if isinstance(existing, MutableMapping) and isinstance(value, Mapping):
            result[key] = deep_merge(existing, value)
        else:
            result[key] = deepcopy(value)
    return result


def resolve_config_paths(
    config: Mapping[str, Any],
    *,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Return a config copy whose ``paths`` values are absolute ``Path`` objects."""
    resolved = deepcopy(dict(config))
    root = find_repo_root(repo_root)
    paths = resolved.get("paths", {})
    if paths is None:
        return resolved
    if not isinstance(paths, Mapping):
        msg = "config['paths'] must be a mapping"
        raise TypeError(msg)
    resolved["paths"] = {
        str(key): resolve_repo_path(value, repo_root=root) for key, value in paths.items()
    }
    return resolved


def load_config(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    overlay_path: str | Path | None = None,
    repo_root: str | Path | None = None,
    resolve_paths: bool = True,
) -> dict[str, Any]:
    """Load the default methodology config with an optional overlay."""
    root = find_repo_root(repo_root)
    base = read_yaml(resolve_repo_path(config_path, repo_root=root))
    overlay = read_yaml(resolve_repo_path(overlay_path, repo_root=root)) if overlay_path else None
    merged = deep_merge(base, overlay)
    return resolve_config_paths(merged, repo_root=root) if resolve_paths else merged


def load_default_config(
    *,
    repo_root: str | Path | None = None,
    resolve_paths: bool = True,
) -> dict[str, Any]:
    """Load the full default configuration."""
    return load_config(repo_root=repo_root, resolve_paths=resolve_paths)


def load_fast_config(
    *,
    repo_root: str | Path | None = None,
    resolve_paths: bool = True,
) -> dict[str, Any]:
    """Load the default configuration with the CI-oriented fast overlay."""
    return load_config(
        overlay_path=FAST_CONFIG_PATH, repo_root=repo_root, resolve_paths=resolve_paths
    )
