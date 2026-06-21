from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from crypto_hedge_fund.config import find_repo_root
from crypto_hedge_fund.experiments.level_5 import (
    build_level_5_target_schedule,
    run_level_5_validation,
)


def _default_level5_config(tmp_path: Path, *, kill_switch: bool = False) -> Path:
    root = find_repo_root()
    config = yaml.safe_load((root / "configs/default.yaml").read_text(encoding="utf-8"))
    config["paths"]["market_data"] = str(root / config["paths"]["market_data"])
    config["paths"]["instruments"] = str(root / config["paths"]["instruments"])
    config["paths"]["manifest"] = str(root / config["paths"]["manifest"])
    config["paths"]["artifacts"] = str(tmp_path / "artifacts")
    config["level_5"]["kill_switch"] = kill_switch
    config["final_test"]["lock_path"] = str(tmp_path / "artifacts" / "final_test_lock.json")
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


@pytest.fixture()
def level5_result(tmp_path: Path):
    return run_level_5_validation(config_path=_default_level5_config(tmp_path))


def test_level5_full_mode_scores_100_pairs_and_writes_validation_artifacts(level5_result) -> None:
    proof = json.loads(level5_result.pair_count_proof_path.read_text(encoding="utf-8"))
    metrics = pd.read_csv(level5_result.artifact_paths["metrics"])
    scores = pd.read_parquet(level5_result.universe_scores_path)
    log = pd.read_parquet(level5_result.rebalance_log_path)
    metadata = json.loads(
        level5_result.artifact_paths["metrics"]
        .with_suffix(".csv.metadata.json")
        .read_text(encoding="utf-8")
    )

    assert proof["split"] == "validation"
    assert proof["final_test_exposure"] == "NOT_EXPOSED"
    assert proof["scored_count"] >= 100
    assert proof["selected_count"] == 25
    assert metrics["provenance_split"].iloc[0] == "validation"
    assert metadata["final_test_lock_hash"] is None
    assert metrics["scored_count_max"].iloc[0] >= 100
    assert scores.groupby("decision_bar_start")["symbol"].nunique().max() >= 100
    assert scores["selected_top_k"].any()
    assert log["submitted_to_broker"].any()
    assert level5_result.figure_path.exists()


def test_level5_cutoffs_and_artifacts_do_not_enter_final_test(level5_result) -> None:
    scores = pd.read_parquet(level5_result.universe_scores_path)
    weights = pd.read_parquet(level5_result.artifact_paths["weights"])
    trace = json.loads(level5_result.decision_trace_path.read_text(encoding="utf-8"))

    assert pd.to_datetime(scores["feature_cutoff"], utc=True).max() < pd.Timestamp(
        "2025-01-01", tz="UTC"
    )
    assert pd.to_datetime(weights["timestamp"], utc=True).max() <= pd.Timestamp(
        "2024-12-31", tz="UTC"
    )
    assert trace["final_test_exposure"] == "NOT_EXPOSED"
    assert trace["portfolio_protocol"]["point_in_time_universe"] is True


def test_level5_topk_liquidity_and_weight_caps_hold(level5_result) -> None:
    scores = pd.read_parquet(level5_result.universe_scores_path)
    log = pd.read_parquet(level5_result.rebalance_log_path)
    weights = pd.read_parquet(level5_result.artifact_paths["weights"])
    symbol_columns = [column for column in weights.columns if "/" in column]

    assert scores.loc[scores["selected_top_k"], "max_weight_by_liquidity"].gt(0.0).all()
    assert log["selected_count"].max() == 25
    assert log["approved_nonzero_count"].max() <= 25
    assert weights[symbol_columns].max().max() <= 0.05 + 0.01
    assert log["max_approved_weight"].max() <= 0.05 + 1e-12


def test_level5_kill_switch_scores_but_moves_schedule_to_cash(tmp_path: Path) -> None:
    config_path = _default_level5_config(tmp_path, kill_switch=True)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    frame = pd.read_parquet(config["paths"]["market_data"])
    instruments = pd.read_parquet(config["paths"]["instruments"])

    schedule, scores, log, traces = build_level_5_target_schedule(
        frame=frame,
        instruments=instruments,
        config=config,
        decision_start=pd.Timestamp(config["level_5"]["validation_decision_start"], tz="UTC"),
        decision_end=pd.Timestamp(config["level_5"]["validation_decision_start"], tz="UTC"),
    )

    assert scores["scored"].sum() >= 100
    assert schedule.sum(axis=1).eq(0.0).all()
    assert set(log["approval_action"]) == {"cash"}
    assert traces[0].approval is not None
    assert traces[0].approval.reason_codes[0].value == "kill_switch"


def test_level5_schedule_repeatability_on_same_inputs(tmp_path: Path) -> None:
    config_path = _default_level5_config(tmp_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    frame = pd.read_parquet(config["paths"]["market_data"])
    instruments = pd.read_parquet(config["paths"]["instruments"])
    kwargs = {
        "frame": frame,
        "instruments": instruments,
        "config": config,
        "decision_start": pd.Timestamp(config["level_5"]["validation_decision_start"], tz="UTC"),
        "decision_end": pd.Timestamp(config["level_5"]["validation_decision_start"], tz="UTC"),
    }

    schedule_a, scores_a, _, _ = build_level_5_target_schedule(**kwargs)
    schedule_b, scores_b, _, _ = build_level_5_target_schedule(**kwargs)

    pd.testing.assert_frame_equal(schedule_a, schedule_b)
    pd.testing.assert_series_equal(
        scores_a.sort_values("symbol").set_index("symbol")["score"],
        scores_b.sort_values("symbol").set_index("symbol")["score"],
    )
