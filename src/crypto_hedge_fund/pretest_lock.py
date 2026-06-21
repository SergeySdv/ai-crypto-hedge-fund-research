"""Pretest freeze helpers for the final-test quarantine gate."""

from __future__ import annotations

import csv
import json
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from crypto_hedge_fund.config import find_repo_root, load_config, resolve_repo_path
from crypto_hedge_fund.provenance import (
    canonical_config_hash,
    canonical_json,
    file_sha256,
    git_commit,
    git_diff_sha256,
    git_worktree_dirty,
)

LOCK_SCHEMA_VERSION = "pretest-final-test-lock-v1"
VALIDATION_SELECTED_PATH = Path("configs/validation_selected.yaml")
FINAL_TEST_LOCK_PATH = Path("artifacts/final_test_lock.json")
FINAL_TEST_LOCK_METADATA_PATH = Path("artifacts/final_test_lock.json.metadata.json")
DATA_PAIR_COUNT_PROOF_RELATIVE_PATH = Path(
    "artifacts/monitoring/level_5_data_pair_count_proof.json"
)
LEVEL_5_PAIR_COUNT_PROOF_ARTIFACT = "monitoring/level_5_pair_count_proof.json"

LEVEL_ARTIFACTS: tuple[str, ...] = (
    "metrics/level_{level}.csv",
    "equity/level_{level}.parquet",
    "weights/level_{level}.parquet",
    "orders/level_{level}.parquet",
    "fills/level_{level}.parquet",
    "figures/level_{level}_equity_curve.png",
)
MONITORING_ARTIFACTS: tuple[str, ...] = (
    "monitoring/level_1_decision_trace.json",
    "monitoring/level_2_decision_trace.json",
    "monitoring/level_2_robustness.json",
    "monitoring/level_2_model_predictions.parquet",
    "monitoring/level_2_fit_audit.parquet",
    "monitoring/level_3_decision_trace.json",
    "monitoring/level_3_universe_selection.csv",
    "monitoring/level_3_final_vintage_plan.json",
    "monitoring/level_4_decision_trace.json",
    "monitoring/level_4_rebalance_log.parquet",
    "monitoring/level_4_final_vintage_plan.json",
    "monitoring/level_5_pair_count_proof.json",
    "monitoring/level_5_universe_scores.parquet",
    "monitoring/level_5_rebalance_log.parquet",
    "monitoring/level_5_decision_trace.json",
    "monitoring/health_summary.csv",
    "monitoring/alerts.parquet",
)
ALLOWED_DIRTY_PREFIXES: tuple[str, ...] = (
    ".gitignore",
    "artifacts/",
    "configs/validation_selected.yaml",
    "reports/",
    "src/crypto_hedge_fund/cli.py",
    "src/crypto_hedge_fund/data/validation.py",
    "src/crypto_hedge_fund/pretest_lock.py",
    "src/crypto_hedge_fund/provenance.py",
    "tests/unit/test_data_layer.py",
    "tests/unit/test_pretest_freeze.py",
)


class PretestFreezeError(RuntimeError):
    """Raised when the repository is not eligible for a pretest freeze."""


class FinalTestLockValidationError(RuntimeError):
    """Raised when a final-test lock no longer matches the frozen inputs."""


@dataclass(frozen=True)
class PretestFreezeResult:
    """Paths and hashes created by the pretest freeze command."""

    validation_selected_path: Path
    final_test_lock_path: Path
    metadata_path: Path
    validation_selected_sha256: str
    final_test_lock_sha256: str
    final_test_exposure_state: str
    forbidden_dirty_paths: tuple[str, ...]


@dataclass(frozen=True)
class FinalTestLockValidationResult:
    """Summary of a successful final-test lock validation."""

    lock_path: Path
    metadata_path: Path
    final_test_lock_sha256: str
    validation_selected_sha256: str
    validation_artifact_count: int
    data_pair_count_proof_sha256: str | None
    final_test_exposure_state: str


def run_pretest_freeze(
    *,
    repo_root: str | Path | None = None,
    config_path: str | Path = "configs/default.yaml",
    validation_selected_path: str | Path = VALIDATION_SELECTED_PATH,
    lock_path: str | Path = FINAL_TEST_LOCK_PATH,
) -> PretestFreezeResult:
    """Write validation-selected config and final-test lock after gate checks."""
    root = find_repo_root(repo_root)
    forbidden_dirty = _forbidden_dirty_paths(root)
    if forbidden_dirty:
        joined = ", ".join(forbidden_dirty)
        raise PretestFreezeError(f"Forbidden uncommitted methodology/config changes: {joined}")

    config = load_config(config_path, repo_root=root, resolve_paths=False)
    artifacts_root = resolve_repo_path(config["paths"]["artifacts"], repo_root=root)
    validation = _collect_validation_state(root, config=config, artifacts_root=artifacts_root)

    validation_selected = _build_validation_selected(config, validation)
    selected_output = resolve_repo_path(validation_selected_path, repo_root=root)
    selected_output.parent.mkdir(parents=True, exist_ok=True)
    _write_yaml(selected_output, validation_selected)
    validation_selected_sha256 = file_sha256(selected_output)
    validation_selected_canonical_sha256 = canonical_config_hash(
        load_config(selected_output, repo_root=root, resolve_paths=False)
    )

    lock_output = resolve_repo_path(lock_path, repo_root=root)
    lock_output.parent.mkdir(parents=True, exist_ok=True)
    lock_payload = _build_lock_payload(
        root,
        config=config,
        validation=validation,
        validation_selected_path=selected_output,
        validation_selected_sha256=validation_selected_sha256,
        validation_selected_canonical_sha256=validation_selected_canonical_sha256,
    )
    _write_json(lock_output, lock_payload)
    lock_sha256 = file_sha256(lock_output)

    metadata_output = resolve_repo_path(FINAL_TEST_LOCK_METADATA_PATH, repo_root=root)
    metadata = {
        "artifact": lock_output.relative_to(root).as_posix(),
        "final_test_lock_sha256": lock_sha256,
        "lock_schema_version": LOCK_SCHEMA_VERSION,
        "created_at_utc": lock_payload["created_at_utc"],
        "final_test_exposure_state": lock_payload["final_test_exposure_state"],
        "config_sha256": validation_selected_sha256,
    }
    _write_json(metadata_output, metadata)
    return PretestFreezeResult(
        validation_selected_path=selected_output,
        final_test_lock_path=lock_output,
        metadata_path=metadata_output,
        validation_selected_sha256=validation_selected_sha256,
        final_test_lock_sha256=lock_sha256,
        final_test_exposure_state=str(lock_payload["final_test_exposure_state"]),
        forbidden_dirty_paths=(),
    )


def validate_final_test_lock(
    *,
    repo_root: str | Path | None = None,
    config_path: str | Path = "configs/default.yaml",
    lock_path: str | Path | None = None,
    metadata_path: str | Path = FINAL_TEST_LOCK_METADATA_PATH,
) -> FinalTestLockValidationResult:
    """Validate the frozen pretest lock before any final-test computation."""
    root = find_repo_root(repo_root)
    config = load_config(config_path, repo_root=root, resolve_paths=False)
    lock_output = resolve_repo_path(
        lock_path if lock_path is not None else config["final_test"]["lock_path"],
        repo_root=root,
    )
    metadata_output = resolve_repo_path(metadata_path, repo_root=root)
    if not lock_output.exists():
        raise FinalTestLockValidationError(
            f"Missing final-test lock: {lock_output.relative_to(root).as_posix()}"
        )
    if not metadata_output.exists():
        raise FinalTestLockValidationError(
            f"Missing final-test lock metadata: {metadata_output.relative_to(root).as_posix()}"
        )

    lock_payload = _read_json(lock_output)
    metadata = _read_json(metadata_output)
    actual_lock_sha = file_sha256(lock_output)
    _require_equal(
        "final-test lock sidecar hash",
        metadata.get("final_test_lock_sha256"),
        actual_lock_sha,
    )
    _require_equal(
        "lock schema version",
        lock_payload.get("lock_schema_version"),
        LOCK_SCHEMA_VERSION,
    )
    _require_equal(
        "lock metadata schema version",
        metadata.get("lock_schema_version"),
        LOCK_SCHEMA_VERSION,
    )
    _require_equal(
        "final-test exposure state",
        lock_payload.get("final_test_exposure_state"),
        "LOCKED",
    )
    if lock_payload.get("final_test_results_inspected") is not False:
        raise FinalTestLockValidationError("Lock must record final_test_results_inspected=false")

    hashes = lock_payload.get("hashes")
    if not isinstance(hashes, Mapping):
        raise FinalTestLockValidationError("Lock hashes section is missing or invalid")

    _require_equal("uv.lock hash", hashes.get("uv_lock_sha256"), file_sha256(root / "uv.lock"))
    _require_equal(
        "pyproject.toml hash",
        hashes.get("pyproject_sha256"),
        file_sha256(root / "pyproject.toml"),
    )
    market_data_path = resolve_repo_path(config["paths"]["market_data"], repo_root=root)
    instruments_path = resolve_repo_path(config["paths"]["instruments"], repo_root=root)
    manifest_path = resolve_repo_path(config["paths"]["manifest"], repo_root=root)
    data_sha = file_sha256(market_data_path)
    instruments_sha = file_sha256(instruments_path)
    manifest_sha = file_sha256(manifest_path)
    _require_equal("market data hash", hashes.get("data_sha256"), data_sha)
    _require_equal("instrument metadata hash", hashes.get("instruments_sha256"), instruments_sha)
    _require_equal("manifest hash", hashes.get("manifest_sha256"), manifest_sha)

    manifest = _read_json(manifest_path)
    _require_equal(
        "manifest recorded data hash",
        hashes.get("manifest_recorded_data_sha256"),
        manifest.get("file_sha256"),
    )
    _require_equal(
        "manifest recorded instrument hash",
        hashes.get("manifest_recorded_instruments_sha256"),
        manifest.get("instrument_sha256"),
    )
    _require_equal("manifest data file hash", manifest.get("file_sha256"), data_sha)
    _require_equal(
        "manifest instrument file hash",
        manifest.get("instrument_sha256"),
        instruments_sha,
    )

    selected_path_value = hashes.get("validation_selected_path")
    if not isinstance(selected_path_value, str) or not selected_path_value:
        raise FinalTestLockValidationError("Lock missing validation_selected_path")
    selected_path = resolve_repo_path(selected_path_value, repo_root=root)
    if not selected_path.exists():
        raise FinalTestLockValidationError(f"Missing selected config: {selected_path_value}")
    selected_sha = file_sha256(selected_path)
    _require_equal(
        "validation-selected config hash",
        hashes.get("validation_selected_sha256"),
        selected_sha,
    )
    _require_equal("metadata selected config hash", metadata.get("config_sha256"), selected_sha)
    selected_config = load_config(selected_path, repo_root=root, resolve_paths=False)
    _require_equal(
        "validation-selected canonical config hash",
        hashes.get("validation_selected_canonical_sha256"),
        canonical_config_hash(selected_config),
    )
    _require_equal(
        "default config canonical hash",
        hashes.get("default_config_canonical_sha256"),
        canonical_config_hash(config),
    )

    artifact_hashes = hashes.get("validation_artifact_hashes")
    if not isinstance(artifact_hashes, Mapping) or not artifact_hashes:
        raise FinalTestLockValidationError("Lock missing validation artifact hashes")
    mismatches = _hash_mismatches(root, artifact_hashes)
    if mismatches:
        first = mismatches[0]
        raise FinalTestLockValidationError(
            f"Validation artifact hash mismatch for {first[0]}: expected {first[1]}, got {first[2]}"
        )

    data_proof_sha: str | None = None
    data_proof_hash = hashes.get("data_validation_pair_count_proof_sha256")
    data_proof_path = hashes.get("data_validation_pair_count_proof_path")
    if data_proof_hash is not None:
        if not isinstance(data_proof_path, str) or not data_proof_path:
            raise FinalTestLockValidationError("Lock missing data-validation proof path")
        proof_path = resolve_repo_path(data_proof_path, repo_root=root)
        if not proof_path.exists():
            raise FinalTestLockValidationError(f"Missing data-validation proof: {data_proof_path}")
        data_proof_sha = file_sha256(proof_path)
        _require_equal("data-validation proof hash", data_proof_hash, data_proof_sha)

    return FinalTestLockValidationResult(
        lock_path=lock_output,
        metadata_path=metadata_output,
        final_test_lock_sha256=actual_lock_sha,
        validation_selected_sha256=selected_sha,
        validation_artifact_count=len(artifact_hashes),
        data_pair_count_proof_sha256=data_proof_sha,
        final_test_exposure_state=str(lock_payload["final_test_exposure_state"]),
    )


def _collect_validation_state(
    repo_root: Path,
    *,
    config: Mapping[str, Any],
    artifacts_root: Path,
) -> dict[str, Any]:
    required = _required_artifacts(artifacts_root)
    missing = [relative for relative, path in required.items() if not path.exists()]
    if missing:
        raise PretestFreezeError(f"Missing required validation artifacts: {', '.join(missing)}")

    level_rows = {
        f"level_{level}": _read_csv_rows(artifacts_root / "metrics" / f"level_{level}.csv")
        for level in range(1, 6)
    }
    for level, rows in level_rows.items():
        if not rows:
            raise PretestFreezeError(f"{level} metrics file is empty")
        _require_validation_provenance(level, rows)

    pair_count_proof = _read_json(artifacts_root / LEVEL_5_PAIR_COUNT_PROOF_ARTIFACT)
    if pair_count_proof.get("final_test_exposure") != "NOT_EXPOSED":
        raise PretestFreezeError("Level 5 pair-count proof indicates final-test exposure")
    required_scored = int(config["level_5"]["min_scored_pairs_full"])
    if int(pair_count_proof.get("scored_count", 0)) < required_scored:
        raise PretestFreezeError("Level 5 pair-count proof is below required scored-pair count")

    level_3_plan = _read_json(artifacts_root / "monitoring/level_3_final_vintage_plan.json")
    level_4_plan = _read_json(artifacts_root / "monitoring/level_4_final_vintage_plan.json")
    for label, plan in (("level_3", level_3_plan), ("level_4", level_4_plan)):
        if plan.get("final_test_exposure") != "NOT_EXPOSED":
            raise PretestFreezeError(f"{label} final vintage plan indicates final-test exposure")
        if plan.get("status") != "planned_not_executed":
            raise PretestFreezeError(f"{label} final vintage plan must be planned_not_executed")

    selected = {
        "level_1": _selected_level_1(level_rows["level_1"]),
        "level_2": _selected_by_flag(level_rows["level_2"], "selected_for_level_2", "approach"),
        "level_3": _selected_by_flag(level_rows["level_3"], "selected_for_level_3", "method"),
        "level_4": _selected_by_flag(level_rows["level_4"], "selected_for_level_4", "policy"),
        "level_5": {
            "scored_count": int(pair_count_proof["scored_count"]),
            "eligible_count": int(pair_count_proof["eligible_count"]),
            "selected_count": int(pair_count_proof["selected_count"]),
            "selected_symbols": list(pair_count_proof["selected_symbols"]),
            "decision_dates": list(pair_count_proof["decision_dates"]),
        },
    }

    return {
        "selected": selected,
        "level_rows": level_rows,
        "level_3_final_vintage_plan": level_3_plan,
        "level_4_final_vintage_plan": level_4_plan,
        "level_5_pair_count_proof": pair_count_proof,
        "artifact_hashes": _artifact_hashes(repo_root, required.values()),
        "data_pair_count_proof_hash": _optional_file_hash(
            repo_root / DATA_PAIR_COUNT_PROOF_RELATIVE_PATH
        ),
    }


def _build_validation_selected(
    config: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    selected = validation["selected"]
    l3_plan = validation["level_3_final_vintage_plan"]
    l4_plan = validation["level_4_final_vintage_plan"]
    l5_proof = validation["level_5_pair_count_proof"]
    return {
        "schema_version": "validation-selected-methodology-v1",
        "final_test_exposure_state_before_lock": "NOT_EXPOSED",
        "quarantine_statement": (
            "All choices were selected from train/validation artifacts only; no 2025 "
            "final-test returns, rankings, metrics, charts, orders or fills have been inspected."
        ),
        "project": {
            "seed": config["project"]["seed"],
            "timezone": config["project"]["timezone"],
            "mode": config["project"]["mode"],
        },
        "data": {
            "exchange": config["data"]["exchange"],
            "market_type": config["data"]["market_type"],
            "quote_currency": config["data"]["quote_currency"],
            "timeframe": config["data"]["timeframe"],
            "start": config["data"]["start"],
            "end": config["data"]["end"],
            "large_universe_size": config["data"]["large_universe_size"],
            "liquidity_lookback_days": config["data"]["liquidity_lookback_days"],
            "stable_bases": list(config["data"]["stable_bases"]),
        },
        "clock": dict(config["clock"]),
        "splits": dict(config["splits"]),
        "costs": {
            "initial_capital_usd": config["backtest"]["initial_capital_usd"],
            "annualization_periods": config["backtest"]["annualization_periods"],
            "risk_free_rate": config["backtest"]["risk_free_rate"],
            "fee_bps_one_way": config["backtest"]["fee_bps_one_way"],
            "slippage_bps_one_way": config["backtest"]["slippage_bps_one_way"],
            "allow_short": config["backtest"]["allow_short"],
            "allow_leverage": config["backtest"]["allow_leverage"],
            "allow_cash": config["backtest"]["allow_cash"],
        },
        "risk": dict(config["risk"]),
        "liquidity": dict(config["liquidity"]),
        "statistics": dict(config["statistics"]),
        "benchmarks": {
            "levels_1_2": "broker_costed_buy_and_hold",
            "level_3": "broker_costed_equal_weight_static_basket",
            "level_4": "broker_costed_level3_static_benchmark",
            "level_5": "price_normalized_btc_open_to_open",
        },
        "selected": {
            "level_1": {
                "symbol": config["level_1"]["symbol"],
                "strategy": "sma_crossover",
                "fast_window": selected["level_1"]["fast_window"],
                "slow_window": selected["level_1"]["slow_window"],
                "candidate_fast_windows": list(config["level_1"]["fast_windows"]),
                "candidate_slow_windows": list(config["level_1"]["slow_windows"]),
                "selection_metric": config["level_1"]["selection_metric"],
                "max_weight": config["level_1"]["max_weight"],
            },
            "level_2": {
                "symbol": config["level_2"]["symbol"],
                "selected_approach": selected["level_2"]["name"],
                "prediction_horizon_open_days": config["level_2"]["prediction_horizon_open_days"],
                "technical_windows": {
                    "fast": config["level_2"]["technical_fast_window"],
                    "slow": config["level_2"]["technical_slow_window"],
                },
                "agent_weights": {
                    "technical": config["level_2"]["technical_weight"],
                    "econometric": config["level_2"]["econometric_weight"],
                    "logistic": config["level_2"]["logistic_weight"],
                    "hist_gradient_boosting": config["level_2"]["hgb_weight"],
                },
                "ml_models": ["logistic_regression", "hist_gradient_boosting_classifier"],
                "ml_retrain": config["level_2"]["ml_default_retrain"],
                "econometric_refit": config["level_2"]["econometric_refit"],
                "calibration": config["level_2"]["calibration"],
                "safety_margin_bps": config["level_2"]["safety_margin_bps"],
                "max_model_age_days": config["level_2"]["max_model_age_days"],
            },
            "level_3": {
                "selected_method": selected["level_3"]["name"],
                "candidate_methods": list(config["level_3"]["methods"]),
                "validation_symbols": _split_symbols(
                    selected["level_3"]["row"]["selected_symbols"]
                ),
                "final_symbols": list(l3_plan["symbols"]),
                "validation_estimation_window": [
                    config["level_3"]["validation_estimation_start"],
                    config["level_3"]["validation_estimation_end"],
                ],
                "final_estimation_window": [
                    config["level_3"]["final_estimation_start"],
                    config["level_3"]["final_estimation_end"],
                ],
                "final_evaluation_window_not_run": list(l3_plan["evaluation_period_not_run"]),
                "estimation_window_rule": "exact_trailing_12_months",
                "selection_metric": config["level_3"]["selection_metric"],
                "covariance_shrinkage": config["level_3"]["covariance_shrinkage"],
                "cvar_tail_fraction": config["level_3"]["cvar_tail_fraction"],
                "final_weights_by_method": l3_plan["weights_by_method"],
            },
            "level_4": {
                "selected_policy": selected["level_4"]["name"],
                "candidate_policies": list(config["level_4"]["policies"]),
                "allocator": config["level_4"]["allocator"],
                "rolling_window_months": config["level_4"]["rolling_window_months"],
                "validation_estimation_window": [
                    config["level_4"]["validation_estimation_start"],
                    config["level_4"]["validation_estimation_end"],
                ],
                "final_estimation_window": [
                    l4_plan["estimation_start"],
                    l4_plan["estimation_end"],
                ],
                "final_evaluation_window_not_run": list(l4_plan["evaluation_period_not_run"]),
                "selection_metric": config["level_4"]["selection_metric"],
                "selection_constraints": {
                    "max_drawdown": config["rebalance"]["max_drawdown_constraint"],
                    "annual_turnover": config["rebalance"]["annual_turnover_constraint"],
                    "tie_breaker": config["rebalance"]["tie_breaker"],
                },
            },
            "level_5": {
                "mode": l5_proof["mode"],
                "universe_rules": l5_proof["eligibility_rules"],
                "filters": l5_proof["filters"],
                "required_min_pairs": l5_proof["required_min_pairs"],
                "validated_scored_count": l5_proof["scored_count"],
                "validated_selected_count": l5_proof["selected_count"],
                "selected_symbols": l5_proof["selected_symbols"],
                "allocator": config["level_5"]["allocator"],
                "top_k": config["level_5"]["top_k"],
                "max_weight": config["level_5"]["max_weight"],
                "rebalance_calendar": config["level_5"]["rebalance_calendar"],
                "score_change_threshold": config["level_5"]["score_change_threshold"],
                "turnover_cap": config["level_5"]["turnover_cap"],
                "priority_score": (
                    "expected return proxy times confidence divided by forecast volatility "
                    "with liquidity/capacity penalties"
                ),
                "monitoring_artifacts": {
                    "pair_count_proof": "artifacts/monitoring/level_5_pair_count_proof.json",
                    "health_summary": "artifacts/monitoring/health_summary.csv",
                    "alerts": "artifacts/monitoring/alerts.parquet",
                },
            },
        },
    }


def _build_lock_payload(
    repo_root: Path,
    *,
    config: Mapping[str, Any],
    validation: Mapping[str, Any],
    validation_selected_path: Path,
    validation_selected_sha256: str,
    validation_selected_canonical_sha256: str,
) -> dict[str, Any]:
    manifest_path = resolve_repo_path(config["paths"]["manifest"], repo_root=repo_root)
    market_data_path = resolve_repo_path(config["paths"]["market_data"], repo_root=repo_root)
    instruments_path = resolve_repo_path(config["paths"]["instruments"], repo_root=repo_root)
    manifest = _read_json(manifest_path)
    dirty_paths = _git_dirty_paths(repo_root)
    return {
        "lock_schema_version": LOCK_SCHEMA_VERSION,
        "created_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "final_test_exposure_state": "LOCKED",
        "final_test_results_inspected": False,
        "quarantine_statement": (
            "Final-test results have not been inspected; this lock freezes validation-selected "
            "methodology before any final-test metrics are run."
        ),
        "git": {
            "commit": git_commit(repo_root, raise_on_error=True),
            "tags_pointing_at_commit": _git_tags_pointing_at_head(repo_root),
            "base_tag": "stage/09-level-5-100pairs",
            "dirty_worktree": git_worktree_dirty(repo_root),
            "dirty_paths": dirty_paths,
            "dirty_policy": (
                "Forbidden methodology/config changes fail pretest-freeze. Stage 10 lock, "
                "report, artifact, CLI/helper/test and .gitignore changes are allowed before "
                "the team-lead checkpoint commit."
            ),
            "diff_sha256_excluding_artifacts_reports": git_diff_sha256(repo_root),
        },
        "hashes": {
            "uv_lock_sha256": file_sha256(repo_root / "uv.lock"),
            "pyproject_sha256": file_sha256(repo_root / "pyproject.toml"),
            "data_sha256": file_sha256(market_data_path),
            "instruments_sha256": file_sha256(instruments_path),
            "manifest_sha256": file_sha256(manifest_path),
            "manifest_recorded_data_sha256": manifest.get("file_sha256"),
            "manifest_recorded_instruments_sha256": manifest.get("instrument_sha256"),
            "validation_selected_path": validation_selected_path.relative_to(repo_root).as_posix(),
            "validation_selected_sha256": validation_selected_sha256,
            "validation_selected_canonical_sha256": validation_selected_canonical_sha256,
            "default_config_canonical_sha256": canonical_config_hash(config),
            "validation_artifact_hashes": validation["artifact_hashes"],
            "data_validation_pair_count_proof_path": DATA_PAIR_COUNT_PROOF_RELATIVE_PATH.as_posix(),
            "data_validation_pair_count_proof_sha256": validation["data_pair_count_proof_hash"],
        },
        "periods": {
            "train": [config["splits"]["train_start"], config["splits"]["train_end"]],
            "validation": [
                config["splits"]["validation_start"],
                config["splits"]["validation_end"],
            ],
            "final_test": [config["splits"]["test_start"], config["splits"]["test_end"]],
            "level_5_validation": [
                config["level_5"]["validation_evaluation_start"],
                config["level_5"]["validation_evaluation_end"],
            ],
        },
        "cost_assumptions": {
            "fee_bps_one_way": config["backtest"]["fee_bps_one_way"],
            "slippage_bps_one_way": config["backtest"]["slippage_bps_one_way"],
            "initial_capital_usd": config["backtest"]["initial_capital_usd"],
            "risk_free_rate": config["backtest"]["risk_free_rate"],
            "chargeable_notional": "risky_asset_notional_traded_only",
        },
        "seeds": {
            "project_seed": config["project"]["seed"],
            "statistical_random_seeds": list(config["statistics"]["random_seeds"]),
        },
        "benchmarks": {
            "levels_1_2": "broker_costed_buy_and_hold",
            "level_3": "broker_costed_equal_weight_static_basket",
            "level_4": "broker_costed_level3_static_benchmark",
            "level_5": "price_normalized_btc_open_to_open",
        },
        "selected": _build_validation_selected(config, validation)["selected"],
        "validation_evidence": {
            "level_5_scored_count": validation["selected"]["level_5"]["scored_count"],
            "level_5_selected_count": validation["selected"]["level_5"]["selected_count"],
            "level_5_pair_count_proof": "artifacts/monitoring/level_5_pair_count_proof.json",
            "level_3_final_vintage_status": validation["level_3_final_vintage_plan"]["status"],
            "level_4_final_vintage_status": validation["level_4_final_vintage_plan"]["status"],
            "all_validation_artifacts_split": "validation",
            "artifact_final_test_lock_hashes": "null_or_empty_before_lock",
        },
        "final_test_policy": {
            "may_run_final_test_after_lock": True,
            "final_test_must_not_change_methodology": True,
            "final_test_command_must_refuse_hash_mismatch": bool(
                config["final_test"]["refuse_hash_mismatch"]
            ),
            "locked_choices_source": validation_selected_path.relative_to(repo_root).as_posix(),
        },
        "known_limitations_to_disclose": [
            "active Binance/CCXT universe has survivorship and delisting bias",
            "daily bars use liquidity proxies rather than order-book depth",
            "Level 5 validation 100-pair proof uses a short late-December 2024 window",
            "Level 5 benchmark is BTC-normalized pending final-report disclosure or improvement",
        ],
    }


def _required_artifacts(artifacts_root: Path) -> dict[str, Path]:
    required: dict[str, Path] = {}
    for level in range(1, 6):
        for pattern in LEVEL_ARTIFACTS:
            relative = pattern.format(level=level)
            required[relative] = artifacts_root / relative
    for relative in MONITORING_ARTIFACTS:
        required[relative] = artifacts_root / relative
    return required


def _optional_file_hash(path: Path) -> str | None:
    return file_sha256(path) if path.exists() else None


def _hash_mismatches(
    repo_root: Path, expected_hashes: Mapping[Any, Any]
) -> list[tuple[str, str, str]]:
    mismatches: list[tuple[str, str, str]] = []
    for relative, expected in sorted(
        ((str(path), str(digest)) for path, digest in expected_hashes.items()),
        key=lambda item: item[0],
    ):
        path = repo_root / relative
        actual = file_sha256(path) if path.exists() else "<missing>"
        if actual != expected:
            mismatches.append((relative, expected, actual))
    return mismatches


def _require_equal(label: str, expected: Any, actual: Any) -> None:
    if expected != actual:
        raise FinalTestLockValidationError(f"{label} mismatch: expected {expected}, got {actual}")


def _artifact_hashes(repo_root: Path, paths: Iterable[Path]) -> dict[str, str]:
    return {
        path.relative_to(repo_root).as_posix(): file_sha256(path)
        for path in sorted(paths, key=lambda item: item.as_posix())
    }


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise PretestFreezeError(f"JSON artifact must contain an object: {path}")
    return data


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_yaml(path: Path, payload: Mapping[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def _require_validation_provenance(level: str, rows: Sequence[Mapping[str, str]]) -> None:
    first = rows[0]
    if first.get("provenance_split") != "validation":
        raise PretestFreezeError(f"{level} metrics are not validation split")
    if first.get("provenance_final_test_lock_hash") not in ("", None):
        raise PretestFreezeError(f"{level} metrics already reference a final-test lock")
    warnings = first.get("provenance_warnings", "")
    if "validation_only_no_final_test_metrics" not in warnings:
        raise PretestFreezeError(f"{level} metrics lack validation-only quarantine warning")


def _selected_level_1(rows: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    row = rows[0]
    return {
        "fast_window": int(float(row["selected_fast_window"])),
        "slow_window": int(float(row["selected_slow_window"])),
        "row": dict(row),
    }


def _selected_by_flag(
    rows: Sequence[Mapping[str, str]],
    flag_column: str,
    name_column: str,
) -> dict[str, Any]:
    selected = [row for row in rows if _truthy(row.get(flag_column))]
    if len(selected) != 1:
        raise PretestFreezeError(f"Expected exactly one selected row for {flag_column}")
    row = selected[0]
    return {"name": row[name_column], "row": dict(row)}


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "1.0", "yes"}


def _split_symbols(value: str) -> list[str]:
    return [symbol.strip() for symbol in value.split(",") if symbol.strip()]


def _git_dirty_paths(repo_root: Path) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    paths: list[str] = []
    for line in completed.stdout.splitlines():
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return tuple(sorted(paths))


def _forbidden_dirty_paths(repo_root: Path) -> tuple[str, ...]:
    return tuple(path for path in _git_dirty_paths(repo_root) if not _is_allowed_dirty_path(path))


def _is_allowed_dirty_path(path: str) -> bool:
    return any(
        path == prefix.rstrip("/") or path.startswith(prefix) for prefix in ALLOWED_DIRTY_PREFIXES
    )


def _git_tags_pointing_at_head(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "tag", "--points-at", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(tag for tag in completed.stdout.splitlines() if tag)


def lock_payload_sha256(payload: Mapping[str, Any]) -> str:
    """Return the SHA-256 digest of a lock-like payload."""
    import hashlib

    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
