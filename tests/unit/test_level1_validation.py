from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest
import yaml

from crypto_hedge_fund.experiments.level_1 import (
    build_level_1_target_schedule,
    run_level_1_validation,
)


def _fixture_frame(*, include_final_rows: bool = True) -> pd.DataFrame:
    rows = []
    dates = pd.date_range("2023-12-25", "2025-01-05", tz="UTC")
    for idx, timestamp in enumerate(dates):
        if timestamp >= pd.Timestamp("2025-01-01T00:00:00+00:00"):
            price = 1_000_000.0 if include_final_rows else 150.0
        else:
            price = 100.0 + idx * 2.0
        rows.append(
            {
                "bar_start_utc": timestamp,
                "bar_end_utc": timestamp + pd.Timedelta(days=1),
                "symbol": "BTC/USDT",
                "open": price,
                "high": price * 1.01,
                "low": price * 0.99,
                "close": price,
                "volume": 1000.0,
                "dollar_volume": price * 1000.0,
                "exchange": "fixture",
                "market_type": "spot",
                "timeframe": "1d",
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
        "splits": {
            "train_start": "2021-01-01",
            "train_end": "2023-12-31",
            "validation_start": "2024-01-01",
            "validation_end": "2024-01-05",
            "test_start": "2025-01-01",
            "test_end": "2025-12-31",
            "embargo_days": 5,
        },
        "backtest": {
            "initial_capital_usd": 1000.0,
            "annualization_periods": 365,
            "risk_free_rate": 0.0,
            "fee_bps_one_way": 10.0,
            "slippage_bps_one_way": 5.0,
        },
        "level_1": {
            "symbol": "BTC/USDT",
            "fast_windows": [2],
            "slow_windows": [3],
            "selection_metric": "net_sharpe",
            "max_weight": 1.0,
            "cost_buffer_weight": 0.005,
            "min_cash_buffer": 0.005,
            "min_dollar_volume": 0.0,
        },
        "portfolio": {"max_gross_exposure": 1.0},
        "risk": {
            "max_drawdown_stop": 0.20,
            "high_volatility_threshold_annual": 0.80,
            "max_agent_disagreement": 0.75,
        },
        "final_test": {
            "require_lock": True,
            "lock_path": str(artifacts_dir / "final_test_lock.json"),
            "refuse_hash_mismatch": True,
        },
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


def test_level1_schedule_uses_completed_bar_and_next_open_validation_only(tmp_path: Path) -> None:
    frame = _fixture_frame()
    market_path = tmp_path / "ohlcv.parquet"
    frame.to_parquet(market_path, index=False)
    config_path = _config(tmp_path, market_path, tmp_path / "artifacts")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    schedule, traces = build_level_1_target_schedule(
        frame=frame,
        symbol="BTC/USDT",
        fast_window=2,
        slow_window=3,
        config=config,
    )

    assert schedule.index.min() == pd.Timestamp("2023-12-31T00:00:00+00:00")
    assert schedule.index.max() == pd.Timestamp("2024-01-04T00:00:00+00:00")
    assert all(
        pd.Timestamp(trace.clock.execution_time) <= pd.Timestamp("2024-01-05T00:00:00+00:00")
        for trace in traces
    )
    assert all(trace.clock.bar_end == trace.clock.feature_cutoff for trace in traces)
    assert all(trace.clock.execution_time >= trace.clock.feature_cutoff for trace in traces)
    assert traces[0].metadata["resolved_action"] in {"approve", "cap"}


def test_level1_validation_writes_artifacts_with_provenance_and_ignores_2025_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import crypto_hedge_fund.experiments.level_1 as level_1_module

    frame = _fixture_frame(include_final_rows=True)
    market_path = tmp_path / "ohlcv.parquet"
    frame.to_parquet(market_path, index=False)
    artifacts_dir = tmp_path / "artifacts"
    config_path = _config(tmp_path, market_path, artifacts_dir)
    monkeypatch.setattr(level_1_module, "git_worktree_dirty", lambda: True)
    monkeypatch.setattr(level_1_module, "git_diff_sha256", lambda: "dirty-source-sha256")

    result = run_level_1_validation(config_path=config_path)

    metrics = pd.read_csv(result.artifact_paths["metrics"])
    equity = pd.read_parquet(result.artifact_paths["equity"])
    fills = pd.read_parquet(result.artifact_paths["fills"])
    metadata = json.loads(
        result.artifact_paths["equity"]
        .with_suffix(".parquet.metadata.json")
        .read_text(encoding="utf-8")
    )
    trace = json.loads(result.trace_path.read_text(encoding="utf-8"))

    assert metrics.loc[0, "provenance_split"] == "validation"
    assert bool(metrics.loc[0, "provenance_git_worktree_dirty"])
    assert metrics.loc[0, "provenance_git_diff_sha256"] == "dirty-source-sha256"
    assert metrics.loc[0, "net_roi"] == pytest.approx(result.metrics["net_roi"])
    assert metadata["period_end"] == "2024-01-05"
    assert metadata["final_test_lock_hash"] is None
    assert metadata["git_worktree_dirty"] is True
    assert metadata["git_diff_sha256"] == "dirty-source-sha256"
    assert pd.to_datetime(equity["timestamp"], utc=True).max() == pd.Timestamp(
        "2024-01-05T00:00:00+00:00"
    )
    assert equity["nav"].max() < 2_000
    assert fills["timestamp"].tolist()[0] == pd.Timestamp("2024-01-01T00:00:00+00:00")
    assert result.figure_path.exists()
    assert trace["provenance"]["split"] == "validation"
    assert trace["representative_decision_trace"]["signals"][0]["agent"] == "sma_crossover"
    assert trace["representative_decision_trace"]["metadata"]["resolved_weights"]["BTC/USDT"] > 0


def test_level1_validation_uses_shared_simulated_broker(tmp_path: Path, monkeypatch) -> None:
    import crypto_hedge_fund.experiments.level_1 as level_1_module
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

    monkeypatch.setattr(level_1_module, "SimulatedBroker", TrackingBroker)

    run_level_1_validation(config_path=config_path)

    assert calls
    assert all(call == "SimulatedBroker.run" for call in calls)


def test_level1_required_artifacts_are_not_ignored_by_git() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    required_paths = [
        "artifacts/metrics/level_1.csv",
        "artifacts/metrics/level_1.csv.metadata.json",
        "artifacts/equity/level_1.parquet",
        "artifacts/equity/level_1.parquet.metadata.json",
        "artifacts/weights/level_1.parquet",
        "artifacts/weights/level_1.parquet.metadata.json",
        "artifacts/orders/level_1.parquet",
        "artifacts/orders/level_1.parquet.metadata.json",
        "artifacts/fills/level_1.parquet",
        "artifacts/fills/level_1.parquet.metadata.json",
        "artifacts/figures/level_1_equity_curve.png",
        "artifacts/figures/level_1_equity_curve.png.metadata.json",
        "artifacts/monitoring/level_1_decision_trace.json",
    ]

    ignored: list[str] = []
    for path in required_paths:
        completed = subprocess.run(
            ["git", "check-ignore", path],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0:
            ignored.append(path)

    assert ignored == []
