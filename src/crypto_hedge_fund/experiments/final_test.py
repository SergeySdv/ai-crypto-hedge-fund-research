"""Frozen final-test suite runner for the accepted Stage 10 lock."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from crypto_hedge_fund.config import find_repo_root, load_config, resolve_repo_path
from crypto_hedge_fund.experiments.level_1 import Level1ValidationResult, run_level_1_validation
from crypto_hedge_fund.experiments.level_2 import Level2ValidationResult, run_level_2_validation
from crypto_hedge_fund.experiments.level_3 import Level3ValidationResult, run_level_3_validation
from crypto_hedge_fund.experiments.level_4 import Level4ValidationResult, run_level_4_validation
from crypto_hedge_fund.experiments.level_5 import Level5ValidationResult, run_level_5_validation
from crypto_hedge_fund.pretest_lock import (
    FinalTestLockValidationError,
    FinalTestLockValidationResult,
    validate_final_test_lock,
)
from crypto_hedge_fund.provenance import canonical_config_hash, file_sha256, git_commit

ACCEPTED_STAGE_10_LOCK_SHA256: str | None = None


@dataclass(frozen=True)
class FinalTestSuiteResult:
    """Summary of one frozen final-test suite execution."""

    lock_validation: FinalTestLockValidationResult
    output_dir: Path
    generated_config_path: Path
    summary_path: Path
    exposure_path: Path
    level_1: Level1ValidationResult
    level_2: Level2ValidationResult
    level_3: Level3ValidationResult
    level_4: Level4ValidationResult
    level_5: Level5ValidationResult

    def to_dict(self) -> dict[str, Any]:
        """Return a stable JSON summary for CLI output."""
        root = find_repo_root(self.output_dir)
        return {
            "split": "final_test",
            "final_test_exposure": "EXPOSED",
            "final_test_lock_sha256": self.lock_validation.final_test_lock_sha256,
            "output_dir": _portable_path(self.output_dir, root),
            "generated_config_path": _portable_path(self.generated_config_path, root),
            "summary_path": _portable_path(self.summary_path, root),
            "exposure_path": _portable_path(self.exposure_path, root),
            "levels": {
                "level_1": _paths(self.level_1.artifact_paths, root),
                "level_2": _paths(self.level_2.artifact_paths, root),
                "level_3": _paths(self.level_3.artifact_paths, root),
                "level_4": _paths(self.level_4.artifact_paths, root),
                "level_5": _paths(self.level_5.artifact_paths, root),
            },
            "level_5": {
                "eligible_count": _level5_eligible_count(self.level_5.pair_count_proof_path),
                "scored_count": self.level_5.scored_count,
                "selected_count": self.level_5.selected_count,
                "pair_count_proof_path": _portable_path(self.level_5.pair_count_proof_path, root),
                "health_summary_path": _portable_path(self.level_5.health_summary_path, root),
            },
        }


def run_frozen_final_test(
    *,
    repo_root: str | Path | None = None,
    config_path: str | Path = "configs/default.yaml",
    expected_lock_hash: str | None = ACCEPTED_STAGE_10_LOCK_SHA256,
) -> FinalTestSuiteResult:
    """Validate the accepted lock, then run all five levels once on final-test data."""
    root = find_repo_root(repo_root)
    validation = validate_final_test_lock(repo_root=root, config_path=config_path)
    if expected_lock_hash is not None and validation.final_test_lock_sha256 != expected_lock_hash:
        raise FinalTestLockValidationError(
            "accepted final-test lock hash mismatch: expected "
            f"{expected_lock_hash}, got {validation.final_test_lock_sha256}"
        )

    lock_payload = _read_json(validation.lock_path)
    selected_path = resolve_repo_path(
        str(lock_payload["hashes"]["validation_selected_path"]),
        repo_root=root,
    )
    selected_config = load_config(selected_path, repo_root=root, resolve_paths=False)
    base_config = load_config(config_path, repo_root=root, resolve_paths=False)
    final_config = _build_final_config(base_config, selected_config)
    output_dir = root / "artifacts" / "final_test" / validation.final_test_lock_sha256[:12]
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_config_path = output_dir / "frozen_final_config.yaml"
    with generated_config_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(final_config, handle, sort_keys=False)

    level_1 = run_level_1_validation(
        config_path=generated_config_path,
        artifacts_dir=output_dir,
        split="final_test",
        final_test_lock_hash=validation.final_test_lock_sha256,
    )
    level_2 = run_level_2_validation(
        config_path=generated_config_path,
        artifacts_dir=output_dir,
        split="final_test",
        final_test_lock_hash=validation.final_test_lock_sha256,
    )
    level_3 = run_level_3_validation(
        config_path=generated_config_path,
        artifacts_dir=output_dir,
        split="final_test",
        final_test_lock_hash=validation.final_test_lock_sha256,
    )
    level_4 = run_level_4_validation(
        config_path=generated_config_path,
        artifacts_dir=output_dir,
        split="final_test",
        final_test_lock_hash=validation.final_test_lock_sha256,
    )
    level_5 = run_level_5_validation(
        config_path=generated_config_path,
        artifacts_dir=output_dir,
        split="final_test",
        final_test_lock_hash=validation.final_test_lock_sha256,
    )

    summary_path, exposure_path = _write_suite_evidence(
        output_dir=output_dir,
        validation=validation,
        lock_payload=lock_payload,
        selected_config_path=selected_path,
        generated_config_path=generated_config_path,
        final_config=final_config,
        level_1=level_1,
        level_2=level_2,
        level_3=level_3,
        level_4=level_4,
        level_5=level_5,
    )
    return FinalTestSuiteResult(
        lock_validation=validation,
        output_dir=output_dir,
        generated_config_path=generated_config_path,
        summary_path=summary_path,
        exposure_path=exposure_path,
        level_1=level_1,
        level_2=level_2,
        level_3=level_3,
        level_4=level_4,
        level_5=level_5,
    )


def _build_final_config(
    base_config: dict[str, Any], selected_config: dict[str, Any]
) -> dict[str, Any]:
    config = json.loads(json.dumps(base_config))
    selected = selected_config["selected"]
    config.setdefault("project", {})["evaluation_split"] = "final_test"

    level_1 = selected["level_1"]
    config["level_1"]["fast_windows"] = [int(level_1["fast_window"])]
    config["level_1"]["slow_windows"] = [int(level_1["slow_window"])]
    config["level_1"]["symbol"] = str(level_1["symbol"])

    level_2 = selected["level_2"]
    config["level_2"]["symbol"] = str(level_2["symbol"])
    config["level_2"]["technical_fast_window"] = int(level_2["technical_windows"]["fast"])
    config["level_2"]["technical_slow_window"] = int(level_2["technical_windows"]["slow"])
    config["level_2"]["technical_weight"] = float(level_2["agent_weights"]["technical"])
    config["level_2"]["econometric_weight"] = float(level_2["agent_weights"]["econometric"])
    config["level_2"]["logistic_weight"] = float(level_2["agent_weights"]["logistic"])
    config["level_2"]["hgb_weight"] = float(level_2["agent_weights"]["hist_gradient_boosting"])
    config["level_2"]["ml_default_retrain"] = str(level_2["ml_retrain"])
    config["level_2"]["econometric_refit"] = str(level_2["econometric_refit"])
    config["level_2"]["safety_margin_bps"] = float(level_2["safety_margin_bps"])
    config["level_2"]["max_model_age_days"] = int(level_2["max_model_age_days"])

    level_3 = selected["level_3"]
    config["level_3"]["locked_selected_method"] = str(level_3["selected_method"])
    config["level_3"]["locked_final_symbols"] = list(level_3["final_symbols"])
    config["level_3"]["final_estimation_start"] = str(level_3["final_estimation_window"][0])
    config["level_3"]["final_estimation_end"] = str(level_3["final_estimation_window"][1])
    config["level_3"]["final_evaluation_start"] = str(level_3["final_evaluation_window_not_run"][0])
    config["level_3"]["final_evaluation_end"] = str(level_3["final_evaluation_window_not_run"][1])

    level_4 = selected["level_4"]
    config["level_4"]["locked_selected_policy"] = str(level_4["selected_policy"])
    config["level_4"]["locked_final_symbols"] = list(level_3["final_symbols"])
    config["level_4"]["allocator"] = str(level_4["allocator"])
    config["level_4"]["final_estimation_start"] = str(level_4["final_estimation_window"][0])
    config["level_4"]["final_estimation_end"] = str(level_4["final_estimation_window"][1])
    config["level_4"]["final_evaluation_start"] = str(level_4["final_evaluation_window_not_run"][0])
    config["level_4"]["final_evaluation_end"] = str(level_4["final_evaluation_window_not_run"][1])

    level_5 = selected["level_5"]
    config["level_5"]["allocator"] = str(level_5["allocator"])
    config["level_5"]["top_k"] = int(level_5["top_k"])
    config["level_5"]["max_weight"] = float(level_5["max_weight"])
    config["level_5"]["rebalance_calendar"] = str(level_5["rebalance_calendar"])
    config["level_5"]["score_change_threshold"] = float(level_5["score_change_threshold"])
    config["level_5"]["turnover_cap"] = float(level_5["turnover_cap"])
    config["level_5"]["min_scored_pairs_full"] = int(level_5["required_min_pairs"])
    return config


def _write_suite_evidence(
    *,
    output_dir: Path,
    validation: FinalTestLockValidationResult,
    lock_payload: dict[str, Any],
    selected_config_path: Path,
    generated_config_path: Path,
    final_config: dict[str, Any],
    level_1: Level1ValidationResult,
    level_2: Level2ValidationResult,
    level_3: Level3ValidationResult,
    level_4: Level4ValidationResult,
    level_5: Level5ValidationResult,
) -> tuple[Path, Path]:
    created_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    root = find_repo_root(output_dir)
    level5_proof = _read_json(level_5.pair_count_proof_path)
    artifact_paths = {
        "level_1": _paths(level_1.artifact_paths, root),
        "level_2": _paths(level_2.artifact_paths, root),
        "level_3": _paths(level_3.artifact_paths, root),
        "level_4": _paths(level_4.artifact_paths, root),
        "level_5": _paths(level_5.artifact_paths, root),
        "level_5_pair_count_proof": _portable_path(level_5.pair_count_proof_path, root),
        "level_5_universe_scores": _portable_path(level_5.universe_scores_path, root),
        "level_5_health_summary": _portable_path(level_5.health_summary_path, root),
        "level_5_alerts": _portable_path(level_5.alerts_path, root),
    }
    common = {
        "split": "final_test",
        "final_test_exposure": "EXPOSED",
        "created_at_utc": created_at,
        "final_test_lock_path": _portable_path(validation.lock_path, root),
        "final_test_lock_sha256": validation.final_test_lock_sha256,
        "validation_selected_path": _portable_path(selected_config_path, root),
        "validation_selected_sha256": validation.validation_selected_sha256,
        "generated_final_config_path": _portable_path(generated_config_path, root),
        "generated_final_config_sha256": file_sha256(generated_config_path),
        "generated_final_config_canonical_sha256": canonical_config_hash(final_config),
        "data_sha256": lock_payload["hashes"]["data_sha256"],
        "instruments_sha256": lock_payload["hashes"]["instruments_sha256"],
        "manifest_sha256": lock_payload["hashes"]["manifest_sha256"],
        "git_commit": git_commit(),
        "locked_git_commit": lock_payload["git"]["commit"],
        "period": lock_payload["periods"]["final_test"],
        "timestamp_semantics": {
            "bar_timestamp_semantics": final_config["clock"]["bar_timestamp_semantics"],
            "decision_after_bar_close": final_config["clock"]["decision_after_bar_close"],
            "execution": final_config["clock"]["execution"],
            "holding_return": final_config["clock"]["holding_return"],
        },
        "cost_assumptions": lock_payload["cost_assumptions"],
        "benchmarks": lock_payload["benchmarks"],
        "seeds": lock_payload["seeds"],
        "warnings_limitations": lock_payload.get("known_limitations_to_disclose", []),
        "artifact_paths": artifact_paths,
        "level_5_counts": {
            "eligible_count": level5_proof["eligible_count"],
            "scored_count": level5_proof["scored_count"],
            "selected_count": level5_proof["selected_count"],
            "runtime_seconds": level5_proof["runtime_seconds"],
            "peak_rss_mb": level5_proof["peak_rss_mb"],
        },
    }
    summary_path = output_dir / "final_test_suite_summary.json"
    exposure_path = output_dir / "final_test_exposure_evidence.json"
    _write_json(summary_path, common)
    _write_json(
        exposure_path,
        {
            **common,
            "exposure_transition": {
                "start_state": "LOCKED",
                "generated_evidence_state": "EXPOSED",
                "lock_file_mutated": False,
            },
        },
    )
    return summary_path, exposure_path


def _paths(paths: dict[str, Path], repo_root: Path) -> dict[str, str]:
    return {key: _portable_path(value, repo_root) for key, value in paths.items()}


def _portable_path(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _level5_eligible_count(path: Path) -> int:
    return int(_read_json(path)["eligible_count"])


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        msg = f"JSON artifact must contain an object: {path}"
        raise TypeError(msg)
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
