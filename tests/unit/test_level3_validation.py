from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from crypto_hedge_fund.experiments.level_3 import (
    build_level_3_target_schedule,
    run_level_3_validation,
    select_level_3_universe,
)
from crypto_hedge_fund.portfolio import FailingAllocator
from crypto_hedge_fund.types import ReasonCode

SYMBOL_VOLUMES = {
    "BTC/USDT": 1000.0,
    "ETH/USDT": 900.0,
    "XRP/USDT": 800.0,
    "BNB/USDT": 700.0,
    "SOL/USDT": 600.0,
    "ADA/USDT": 500.0,
    "PUMP/USDT": 100.0,
    "LOW/USDT": 50.0,
}


def _fixture_frame() -> pd.DataFrame:
    rows = []
    dates = pd.date_range("2023-01-01", "2024-01-10", tz="UTC")
    for symbol_idx, (symbol, base_volume) in enumerate(SYMBOL_VOLUMES.items()):
        for idx, timestamp in enumerate(dates):
            price = 10.0 + symbol_idx * 3.0 + idx * (0.03 + symbol_idx * 0.001)
            volume = base_volume
            if symbol == "PUMP/USDT" and timestamp >= pd.Timestamp("2024-01-01", tz="UTC"):
                volume = 3000.0
            rows.append(
                {
                    "bar_start_utc": timestamp,
                    "bar_end_utc": timestamp + pd.Timedelta(days=1),
                    "symbol": symbol,
                    "open": price,
                    "high": price * 1.02,
                    "low": price * 0.98,
                    "close": price * (1.0 + 0.001 * ((idx % 7) - 3)),
                    "volume": volume,
                    "dollar_volume": price * volume,
                    "exchange": "fixture",
                    "market_type": "spot",
                    "timeframe": "1d",
                }
            )
    return pd.DataFrame(rows)


def _instruments() -> pd.DataFrame:
    rows = []
    for symbol in SYMBOL_VOLUMES:
        base, quote = symbol.split("/")
        rows.append(
            {
                "symbol": symbol,
                "exchange_symbol": symbol.replace("/", ""),
                "base": base,
                "quote": quote,
                "market_type": "spot",
                "active": True,
            }
        )
    return pd.DataFrame(rows)


def _config(tmp_path: Path, market_path: Path, artifacts_dir: Path) -> Path:
    config = {
        "project": {"name": "test", "seed": 42, "timezone": "UTC", "mode": "test"},
        "paths": {
            "market_data": str(market_path),
            "instruments": str(tmp_path / "instruments.parquet"),
            "manifest": str(tmp_path / "manifest.json"),
            "artifacts": str(artifacts_dir),
        },
        "data": {
            "exchange": "fixture",
            "market_type": "spot",
            "quote_currency": "USDT",
            "timeframe": "1d",
            "start": "2023-01-01",
            "end": "2024-01-10",
            "min_history_days": 365,
            "preferred_history_days": 365,
            "large_universe_size": 8,
            "liquidity_lookback_days": 90,
            "small_portfolio_lookback_days": 365,
            "stable_bases": ["USDT", "USDC"],
        },
        "splits": {
            "train_start": "2023-01-01",
            "train_end": "2023-12-31",
            "validation_start": "2024-01-01",
            "validation_end": "2024-01-10",
            "test_start": "2025-01-01",
            "test_end": "2025-12-31",
            "embargo_days": 1,
        },
        "backtest": {
            "initial_capital_usd": 1000.0,
            "annualization_periods": 365,
            "risk_free_rate": 0.0,
            "fee_bps_one_way": 10.0,
            "slippage_bps_one_way": 5.0,
        },
        "level_3": {
            "small_size": 6,
            "methods": ["equal_weight", "inverse_volatility", "minimum_variance", "cvar_downside"],
            "validation_cutoff": "2023-12-31",
            "validation_estimation_start": "2023-01-01",
            "validation_estimation_end": "2023-12-31",
            "validation_evaluation_start": "2024-01-01",
            "validation_evaluation_end": "2024-01-10",
            "final_cutoff": "2024-12-31",
            "final_estimation_start": "2024-01-01",
            "final_estimation_end": "2024-12-31",
            "final_evaluation_start": "2025-01-01",
            "final_evaluation_end": "2025-12-31",
            "min_estimation_days": 365,
            "covariance_shrinkage": 0.1,
            "cvar_tail_fraction": 0.05,
            "selection_metric": "net_sharpe",
            "cost_buffer_weight": 0.005,
            "min_cash_buffer": 0.005,
            "min_dollar_volume": 0.0,
            "write_final_vintage_plan": True,
        },
        "portfolio": {
            "small_size": 6,
            "small_max_weight": 0.30,
            "max_gross_exposure": 1.0,
            "large_max_weight": 0.05,
            "large_top_k": 5,
        },
        "rebalance": {"selection_metric": "net_sharpe", "max_drawdown_constraint": 0.95},
        "liquidity": {
            "assumed_aum_usd": 1000.0,
            "adv_lookback_days": 20,
            "max_participation": 0.01,
            "enforce_min_notional_if_available": True,
        },
        "risk": {
            "max_drawdown_stop": 0.95,
            "high_volatility_threshold_annual": 5.0,
            "max_agent_disagreement": 1.0,
            "min_effective_holdings": 5,
            "post_allocation_validation": True,
        },
        "statistics": {"random_seeds": [42]},
        "final_test": {
            "require_lock": True,
            "lock_path": str(artifacts_dir / "final_test_lock.json"),
            "refuse_hash_mismatch": True,
        },
    }
    _instruments().to_parquet(tmp_path / "instruments.parquet", index=False)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


def test_level3_universe_selection_uses_2023_liquidity_and_exact_asset_count(
    tmp_path: Path,
) -> None:
    frame = _fixture_frame()
    config_path = _config(tmp_path, tmp_path / "ohlcv.parquet", tmp_path / "artifacts")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    universe = select_level_3_universe(
        frame,
        _instruments(),
        config=config,
        estimation_start=pd.Timestamp("2023-01-01", tz="UTC"),
        estimation_end=pd.Timestamp("2023-12-31", tz="UTC"),
        cutoff_bar_start=pd.Timestamp("2023-12-31", tz="UTC"),
    )

    assert len(universe) == 6
    assert set(universe["symbol"]) == {
        "BTC/USDT",
        "ETH/USDT",
        "XRP/USDT",
        "BNB/USDT",
        "SOL/USDT",
        "ADA/USDT",
    }
    assert universe["estimation_median_dollar_volume"].is_monotonic_decreasing
    assert "PUMP/USDT" not in set(universe["symbol"])
    assert set(universe["estimation_window_calendar_months"]) == {12}
    assert set(universe["estimation_valid_days"]) == {365}


def test_level3_validation_writes_artifacts_and_validation_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import crypto_hedge_fund.experiments.level_3 as level_3_module

    frame = _fixture_frame()
    market_path = tmp_path / "ohlcv.parquet"
    frame.to_parquet(market_path, index=False)
    artifacts_dir = tmp_path / "artifacts"
    config_path = _config(tmp_path, market_path, artifacts_dir)
    monkeypatch.setattr(level_3_module, "git_worktree_dirty", lambda: True)
    monkeypatch.setattr(level_3_module, "git_diff_sha256", lambda: "dirty-source-sha256")

    result = run_level_3_validation(config_path=config_path)

    metrics = pd.read_csv(result.artifact_paths["metrics"])
    weights = pd.read_parquet(result.artifact_paths["weights"])
    metadata = json.loads(
        result.artifact_paths["metrics"]
        .with_suffix(".csv.metadata.json")
        .read_text(encoding="utf-8")
    )
    trace = json.loads(result.trace_path.read_text(encoding="utf-8"))
    final_plan = json.loads(result.final_vintage_plan_path.read_text(encoding="utf-8"))

    assert set(metrics["method"]) == {
        "equal_weight",
        "inverse_volatility",
        "minimum_variance",
        "cvar_downside",
    }
    assert metrics["selected_for_level_3"].sum() == 1
    assert set(metrics["universe_count"]) == {6.0}
    assert metadata["split"] == "validation"
    assert metadata["final_test_lock_hash"] is None
    assert metadata["git_worktree_dirty"] is True
    assert metadata["period_end"] == "2024-01-10"
    assert max(pd.to_datetime(weights["timestamp"], utc=True)) <= pd.Timestamp(
        "2024-01-10", tz="UTC"
    )
    assert trace["portfolio_protocol"]["final_vintage_status"] == (
        "planned_not_executed_no_2025_performance"
    )
    assert final_plan["final_test_exposure"] == "NOT_EXPOSED"
    assert result.figure_path.exists()


def test_level3_positive_costs_keep_net_return_below_gross_return(tmp_path: Path) -> None:
    frame = _fixture_frame()
    market_path = tmp_path / "ohlcv.parquet"
    frame.to_parquet(market_path, index=False)
    artifacts_dir = tmp_path / "artifacts"
    config_path = _config(tmp_path, market_path, artifacts_dir)

    result = run_level_3_validation(config_path=config_path)

    metrics = pd.read_csv(result.artifact_paths["metrics"])
    equity = pd.read_parquet(result.artifact_paths["equity"])
    initial_capital = 1000.0

    assert (metrics["net_total_cost"] > 0).all()
    assert (metrics["net_roi"] < metrics["gross_roi"]).all()
    assert (metrics["net_total_return"] < metrics["gross_total_return"]).all()
    assert (metrics["gross_to_net_total_return_decay"] > 0).all()
    for row in metrics.itertuples(index=False):
        method_equity = equity.loc[equity["method"] == row.method].copy()
        net_final_nav = float(method_equity["nav"].iloc[-1])
        gross_final_nav = float(method_equity["gross_nav"].iloc[-1])
        assert row.net_total_return == pytest.approx(net_final_nav / initial_capital - 1.0)
        assert row.gross_total_return == pytest.approx(gross_final_nav / initial_capital - 1.0)


def test_level3_static_schedule_uses_next_open_and_fails_optimizer_to_cash(
    tmp_path: Path,
) -> None:
    frame = _fixture_frame()
    market_path = tmp_path / "ohlcv.parquet"
    frame.to_parquet(market_path, index=False)
    config_path = _config(tmp_path, market_path, tmp_path / "artifacts")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    symbols = ("BTC/USDT", "ETH/USDT", "XRP/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT")

    schedule, trace = build_level_3_target_schedule(
        frame=frame,
        symbols=symbols,
        allocator=FailingAllocator(),
        config=config,
        estimation_start=pd.Timestamp("2023-01-01", tz="UTC"),
        estimation_end=pd.Timestamp("2023-12-31", tz="UTC"),
        evaluation_start=pd.Timestamp("2024-01-01", tz="UTC"),
        previous_weights=pd.Series(dict.fromkeys(symbols, 0.0), dtype="float64"),
    )

    assert schedule.index[0] == pd.Timestamp("2023-12-31", tz="UTC")
    assert pd.Timestamp(trace.clock.execution_time) == pd.Timestamp("2024-01-01", tz="UTC")
    assert schedule.iloc[0].sum() == 0.0
    assert trace.approval is not None
    assert trace.approval.reason_codes == (ReasonCode.OPTIMIZER_FAILURE,)


def test_level3_validation_uses_shared_simulated_broker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import crypto_hedge_fund.experiments.level_3 as level_3_module
    from crypto_hedge_fund.execution import SimulatedBroker as RealBroker

    frame = _fixture_frame()
    market_path = tmp_path / "ohlcv.parquet"
    frame.to_parquet(market_path, index=False)
    config_path = _config(tmp_path, market_path, tmp_path / "artifacts")
    calls: list[str] = []

    class TrackingBroker(RealBroker):
        def run(self, *args, **kwargs):
            calls.append("SimulatedBroker.run")
            return super().run(*args, **kwargs)

    monkeypatch.setattr(level_3_module, "SimulatedBroker", TrackingBroker)

    result = run_level_3_validation(config_path=config_path)

    assert result.symbols
    assert calls
    assert all(call == "SimulatedBroker.run" for call in calls)
