from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml
from test_level3_validation import _config as _level3_config
from test_level3_validation import _fixture_frame

from crypto_hedge_fund.experiments.level_4 import (
    build_level_4_target_schedule,
    run_level_4_validation,
)
from crypto_hedge_fund.portfolio import FailingAllocator
from crypto_hedge_fund.portfolio.rebalance import DynamicRebalancePolicy
from crypto_hedge_fund.types import ReasonCode


def _config(tmp_path: Path, market_path: Path, artifacts_dir: Path) -> Path:
    path = _level3_config(tmp_path, market_path, artifacts_dir)
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    config["portfolio"]["turnover_cap"] = 1.0
    config["rebalance"].update(
        {
            "small_calendar": "monthly",
            "drift_threshold_abs": 0.05,
            "score_change_threshold": 0.15,
            "risk_trigger": True,
            "annual_turnover_constraint": 6.0,
        }
    )
    config["level_4"] = {
        "small_size": config["level_3"]["small_size"],
        "allocator": "cvar_downside",
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
        "rolling_window_months": 12,
        "min_estimation_days": 365,
        "covariance_shrinkage": 0.1,
        "cvar_tail_fraction": 0.05,
        "cost_buffer_weight": 0.005,
        "min_cash_buffer": 0.005,
        "min_dollar_volume": 0.0,
        "min_trade_abs": 0.001,
        "expected_benefit_scale": 0.002,
        "risk_rebalance_volatility_threshold_annual": 0.01,
        "selection_metric": "net_sharpe",
        "write_final_vintage_plan": True,
        "policies": [
            {
                "name": "calendar_monthly",
                "calendar": "monthly",
                "drift_threshold_abs": 1.0,
                "score_change_threshold": 1.0,
                "risk_trigger": False,
            },
            {
                "name": "signal_risk_monthly",
                "calendar": "monthly",
                "drift_threshold_abs": 0.05,
                "score_change_threshold": 0.15,
                "risk_trigger": True,
            },
        ],
    }
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


def test_level4_validation_writes_artifacts_rebalance_log_and_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import crypto_hedge_fund.experiments.level_4 as level_4_module

    frame = _fixture_frame()
    market_path = tmp_path / "ohlcv.parquet"
    frame.to_parquet(market_path, index=False)
    artifacts_dir = tmp_path / "artifacts"
    config_path = _config(tmp_path, market_path, artifacts_dir)
    monkeypatch.setattr(level_4_module, "git_worktree_dirty", lambda: True)
    monkeypatch.setattr(level_4_module, "git_diff_sha256", lambda: "dirty-source-sha256")

    result = run_level_4_validation(config_path=config_path)

    metrics = pd.read_csv(result.artifact_paths["metrics"])
    weights = pd.read_parquet(result.artifact_paths["weights"])
    log = pd.read_parquet(result.rebalance_log_path)
    metadata = json.loads(
        result.artifact_paths["metrics"]
        .with_suffix(".csv.metadata.json")
        .read_text(encoding="utf-8")
    )
    trace = json.loads(result.trace_path.read_text(encoding="utf-8"))
    final_plan = json.loads(result.final_vintage_plan_path.read_text(encoding="utf-8"))

    assert {"static_level3_benchmark", "calendar_monthly", "signal_risk_monthly"}.issubset(
        set(metrics["policy"])
    )
    assert metrics["selected_for_level_4"].sum() == 1
    assert not metrics.loc[metrics["selected_for_level_4"], "is_static_benchmark"].iloc[0]
    assert metadata["split"] == "validation"
    assert metadata["final_test_lock_hash"] is None
    assert metadata["period_end"] == "2024-01-10"
    assert metadata["git_worktree_dirty"] is True
    assert max(pd.to_datetime(weights["timestamp"], utc=True)) <= pd.Timestamp(
        "2024-01-10", tz="UTC"
    )
    assert set(log["policy"]).issuperset({"calendar_monthly", "signal_risk_monthly"})
    assert log["trigger_codes"].str.contains("calendar_monthly").any()
    assert (log["skipped_reason"].astype(str) != "").any()
    assert trace["final_test_exposure"] == "NOT_EXPOSED"
    assert trace["portfolio_protocol"]["final_vintage_status"] == (
        "planned_not_executed_no_2025_performance"
    )
    assert final_plan["final_test_exposure"] == "NOT_EXPOSED"
    assert result.figure_path.exists()


def test_level4_validation_uses_shared_simulated_broker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import crypto_hedge_fund.experiments.level_4 as level_4_module
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

    monkeypatch.setattr(level_4_module, "SimulatedBroker", TrackingBroker)

    result = run_level_4_validation(config_path=config_path)

    assert result.symbols
    assert len(calls) >= 4
    assert all(call == "SimulatedBroker.run" for call in calls)


def test_level4_constraints_keep_approved_weights_within_caps(tmp_path: Path) -> None:
    frame = _fixture_frame()
    market_path = tmp_path / "ohlcv.parquet"
    frame.to_parquet(market_path, index=False)
    artifacts_dir = tmp_path / "artifacts"
    config_path = _config(tmp_path, market_path, artifacts_dir)

    result = run_level_4_validation(config_path=config_path)
    log = pd.read_parquet(result.rebalance_log_path)
    dynamic_log = log.loc[(log["policy"] == result.selected_policy) & log["submitted_to_broker"]]

    for encoded in dynamic_log["approved_weights"]:
        weights = json.loads(encoded)
        assert all(0.0 <= float(weight) <= 0.30 + 1e-12 for weight in weights.values())


def test_level4_failing_allocator_moves_to_cash_without_final_test(tmp_path: Path) -> None:
    frame = _fixture_frame()
    market_path = tmp_path / "ohlcv.parquet"
    frame.to_parquet(market_path, index=False)
    config_path = _config(tmp_path, market_path, tmp_path / "artifacts")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    symbols = ("BTC/USDT", "ETH/USDT", "XRP/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT")
    policy = DynamicRebalancePolicy(name="daily_failure", calendar="daily", min_trade_abs=0.0)

    schedule, log, traces = build_level_4_target_schedule(
        frame=frame,
        symbols=symbols,
        allocator=FailingAllocator(),
        policy=policy,
        config=config,
        initial_estimation_end=pd.Timestamp("2023-12-31", tz="UTC"),
        validation_start=pd.Timestamp("2024-01-01", tz="UTC"),
        validation_end=pd.Timestamp("2024-01-10", tz="UTC"),
    )

    assert schedule.sum(axis=1).eq(0.0).all()
    assert set(log["approval_action"]) == {"cash"}
    assert traces[0].approval is not None
    assert traces[0].approval.reason_codes == (ReasonCode.OPTIMIZER_FAILURE,)
