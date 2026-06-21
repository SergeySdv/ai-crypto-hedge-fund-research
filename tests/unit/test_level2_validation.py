from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest
import yaml

from crypto_hedge_fund.experiments.level_2 import run_level_2_validation
from crypto_hedge_fund.features import LEVEL2_FEATURE_COLUMNS, build_level2_feature_frame
from crypto_hedge_fund.models import walk_forward_ml_predictions


def _fixture_frame() -> pd.DataFrame:
    rows = []
    dates = pd.date_range("2023-01-01", "2024-01-20", tz="UTC")
    for idx, timestamp in enumerate(dates):
        trend = 100.0 + idx * 0.4
        cycle = 4.0 * ((idx % 17) / 17.0)
        price = trend + cycle
        rows.append(
            {
                "bar_start_utc": timestamp,
                "bar_end_utc": timestamp + pd.Timedelta(days=1),
                "symbol": "BTC/USDT",
                "open": price,
                "high": price * 1.02,
                "low": price * 0.98,
                "close": price * (1.0 + 0.002 * ((idx % 5) - 2)),
                "volume": 1000.0 + idx,
                "dollar_volume": price * (1000.0 + idx),
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
        "level_2": {
            "symbol": "BTC/USDT",
            "prediction_horizon_open_days": 1,
            "default_retrain": "monthly",
            "ml_default_retrain": "monthly",
            "econometric_refit": "daily_causal",
            "safety_margin_bps": 5.0,
            "technical_fast_window": 5,
            "technical_slow_window": 20,
            "technical_weight": 0.25,
            "econometric_weight": 0.25,
            "logistic_weight": 0.25,
            "hgb_weight": 0.25,
            "min_train_samples": 40,
            "max_weight": 1.0,
            "cost_buffer_weight": 0.005,
            "min_cash_buffer": 0.005,
            "min_confidence": 0.0,
            "min_dollar_volume": 0.0,
            "max_model_age_days": 400,
        },
        "portfolio": {"max_gross_exposure": 1.0},
        "risk": {
            "max_drawdown_stop": 0.95,
            "high_volatility_threshold_annual": 5.0,
            "max_agent_disagreement": 1.0,
        },
        "statistics": {
            "bootstrap_repetitions": 10,
            "permutation_repetitions": 10,
            "block_length_days": 3,
            "random_seeds": [42, 137],
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


def test_level2_features_align_next_open_target_without_final_rows() -> None:
    frame = _fixture_frame()
    features = build_level2_feature_frame(
        frame,
        symbol="BTC/USDT",
        horizon_open_days=1,
        threshold_return=0.002,
    )
    row = features.iloc[0]

    assert row["feature_cutoff"] == row["bar_end_utc"]
    assert row["execution_time"] == row["bar_start_utc"] + pd.Timedelta(days=1)
    assert row["label_observation_time"] == row["bar_start_utc"] + pd.Timedelta(days=2)
    source = frame.set_index("bar_start_utc")
    execution_open = source.loc[row["execution_time"], "open"]
    future_open = source.loc[row["future_open_time"], "open"]
    assert row["forward_return"] == pytest.approx(future_open / execution_open - 1.0)


def test_level2_ml_walk_forward_never_uses_future_labels(tmp_path: Path) -> None:
    frame = _fixture_frame()
    features = build_level2_feature_frame(frame, symbol="BTC/USDT", threshold_return=0.0)
    validation_mask = features["execution_time"].between(
        pd.Timestamp("2024-01-01T00:00:00+00:00"),
        pd.Timestamp("2024-01-10T00:00:00+00:00"),
    )

    outputs = walk_forward_ml_predictions(
        features,
        feature_columns=LEVEL2_FEATURE_COLUMNS,
        validation_mask=validation_mask,
        seeds=(42,),
        min_train_samples=40,
    )

    assert {output.model_name for output in outputs} == {
        "ml_logistic",
        "ml_hist_gradient_boosting",
    }
    for output in outputs:
        audit = output.fit_audit
        assert not audit["used_future_labels"].any()
        assert (pd.to_datetime(audit["fit_cutoff"], utc=True) < audit["execution_time"]).all()
        assert output.predictive_metrics["seed_count"] == 1.0
    assert tmp_path.exists()


def test_level2_validation_writes_comparison_artifacts_and_trace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import crypto_hedge_fund.experiments.level_2 as level_2_module

    frame = _fixture_frame()
    market_path = tmp_path / "ohlcv.parquet"
    frame.to_parquet(market_path, index=False)
    artifacts_dir = tmp_path / "artifacts"
    config_path = _config(tmp_path, market_path, artifacts_dir)
    monkeypatch.setattr(level_2_module, "git_worktree_dirty", lambda: True)
    monkeypatch.setattr(level_2_module, "git_diff_sha256", lambda: "dirty-source-sha256")

    result = run_level_2_validation(config_path=config_path)

    metrics = pd.read_csv(result.artifact_paths["metrics"])
    equity = pd.read_parquet(result.artifact_paths["equity"])
    fit_audit = pd.read_parquet(result.prediction_paths["fit_audit"])
    predictions = pd.read_parquet(result.prediction_paths["predictions"])
    metadata = json.loads(
        result.artifact_paths["equity"]
        .with_suffix(".parquet.metadata.json")
        .read_text(encoding="utf-8")
    )
    trace = json.loads(result.trace_path.read_text(encoding="utf-8"))
    robustness = json.loads(result.robustness_path.read_text(encoding="utf-8"))

    assert set(metrics["approach"]) == {
        "technical_sma",
        "econometric_ar_garch",
        "ml_logistic",
        "ml_hist_gradient_boosting",
        "agent_ensemble",
    }
    assert metrics.loc[metrics["approach"] == "agent_ensemble", "selected_for_level_2"].item()
    assert metadata["split"] == "validation"
    assert metadata["final_test_lock_hash"] is None
    assert metadata["git_worktree_dirty"] is True
    assert pd.to_datetime(equity["timestamp"], utc=True).max() <= pd.Timestamp(
        "2024-01-10T00:00:00+00:00"
    )
    assert not fit_audit["used_future_labels"].any()
    cadence = trace["feature_definition"]["cadence"]
    assert cadence == {
        "ml_refit_frequency": "monthly",
        "econometric_refit_frequency": "daily_causal",
        "econometric_note": (
            "AutoReg/GARCH forecasts are refit for each validation decision using "
            "only labels observed before that execution time"
        ),
    }
    assert robustness["robustness"]["cadence"] == {
        "ml_refit_frequency": "monthly",
        "econometric_refit_frequency": "daily_causal",
    }
    refits = fit_audit.groupby("model")["refit_frequency"].unique().to_dict()
    assert set(refits["ml_logistic"]) == {"monthly"}
    assert set(refits["ml_hist_gradient_boosting"]) == {"monthly"}
    assert set(refits["econometric_ar_garch"]) == {"daily_causal"}
    prediction_refits = predictions.groupby("approach")["refit_frequency"].unique().to_dict()
    assert set(prediction_refits["ml_logistic"]) == {"monthly"}
    assert set(prediction_refits["ml_hist_gradient_boosting"]) == {"monthly"}
    assert set(prediction_refits["econometric_ar_garch"]) == {"daily_causal"}
    agents = {signal["agent"] for signal in trace["representative_decision_trace"]["signals"]}
    assert {"sma_crossover", "econometric_ar_garch", "ml_logistic"}.issubset(agents)
    assert robustness["robustness"]["block_bootstrap"]["repetitions"] == 10
    assert result.figure_path.exists()


def test_level2_validation_uses_shared_simulated_broker(tmp_path: Path, monkeypatch) -> None:
    import crypto_hedge_fund.experiments.level_2 as level_2_module
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

    monkeypatch.setattr(level_2_module, "SimulatedBroker", TrackingBroker)

    run_level_2_validation(config_path=config_path)

    assert calls
    assert all(call == "SimulatedBroker.run" for call in calls)


def test_level2_required_artifacts_are_not_git_ignored() -> None:
    repo = Path(__file__).resolve().parents[2]
    if not (repo / ".git").exists():
        pytest.skip("git metadata is unavailable")
    required_paths = [
        "artifacts/metrics/level_2.csv",
        "artifacts/metrics/level_2.csv.metadata.json",
        "artifacts/equity/level_2.parquet",
        "artifacts/equity/level_2.parquet.metadata.json",
        "artifacts/weights/level_2.parquet",
        "artifacts/weights/level_2.parquet.metadata.json",
        "artifacts/orders/level_2.parquet",
        "artifacts/orders/level_2.parquet.metadata.json",
        "artifacts/fills/level_2.parquet",
        "artifacts/fills/level_2.parquet.metadata.json",
        "artifacts/figures/level_2_equity_curve.png",
        "artifacts/figures/level_2_equity_curve.png.metadata.json",
        "artifacts/monitoring/level_2_decision_trace.json",
        "artifacts/monitoring/level_2_robustness.json",
        "artifacts/monitoring/level_2_model_predictions.parquet",
        "artifacts/monitoring/level_2_model_predictions.parquet.metadata.json",
        "artifacts/monitoring/level_2_fit_audit.parquet",
        "artifacts/monitoring/level_2_fit_audit.parquet.metadata.json",
    ]
    probe = subprocess.run(
        ["git", "check-ignore", "-q", "--stdin"],
        cwd=repo,
        input="\n".join(required_paths),
        text=True,
        check=False,
    )

    assert probe.returncode == 1
