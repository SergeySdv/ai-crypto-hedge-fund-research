from pathlib import Path

from crypto_hedge_fund.config import (
    deep_merge,
    load_default_config,
    load_fast_config,
    resolve_repo_path,
)


def test_load_default_config_resolves_paths() -> None:
    config = load_default_config()

    assert config["project"]["name"] == "ai-crypto-hedge-fund"
    assert config["clock"]["execution"] == "next_open"
    assert isinstance(config["paths"]["artifacts"], Path)
    assert config["paths"]["artifacts"].is_absolute()


def test_fast_config_preserves_causal_and_cost_invariants() -> None:
    full = load_default_config(resolve_paths=False)
    fast = load_fast_config(resolve_paths=False)

    assert fast["project"]["mode"] == "fast"
    assert fast["clock"] == full["clock"]
    assert fast["backtest"] == full["backtest"]
    assert fast["risk"] == full["risk"]
    assert fast["data"]["large_universe_size"] < full["data"]["large_universe_size"]


def test_deep_merge_does_not_mutate_base() -> None:
    base = {"a": {"b": 1, "c": 2}}
    merged = deep_merge(base, {"a": {"b": 3}})

    assert merged == {"a": {"b": 3, "c": 2}}
    assert base == {"a": {"b": 1, "c": 2}}


def test_resolve_repo_path_uses_repository_root() -> None:
    resolved = resolve_repo_path("configs/default.yaml")

    assert resolved.exists()
    assert resolved.name == "default.yaml"
