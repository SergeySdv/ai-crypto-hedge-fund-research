from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

from crypto_hedge_fund.experiments import final_test
from crypto_hedge_fund.pretest_lock import (
    FinalTestLockValidationError,
    FinalTestLockValidationResult,
)


def test_final_test_refuses_mismatched_lock_before_computation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "AGENTS.md").write_text("contract\n", encoding="utf-8")
    calls: list[str] = []

    def fail_validation(**_: Any) -> FinalTestLockValidationResult:
        raise FinalTestLockValidationError("lock mismatch")

    monkeypatch.setattr(final_test, "validate_final_test_lock", fail_validation)
    monkeypatch.setattr(
        final_test,
        "run_level_1_validation",
        lambda **_: calls.append("level_1"),
    )

    with pytest.raises(FinalTestLockValidationError, match="lock mismatch"):
        final_test.run_frozen_final_test(repo_root=repo, expected_lock_hash=None)

    assert calls == []


def test_final_test_valid_lock_writes_final_test_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _minimal_repo(tmp_path)
    lock_hash = "abc123"
    lock_path = repo / "artifacts" / "final_test_lock.json"

    def pass_validation(**_: Any) -> FinalTestLockValidationResult:
        return FinalTestLockValidationResult(
            lock_path=lock_path,
            metadata_path=repo / "artifacts" / "final_test_lock.json.metadata.json",
            final_test_lock_sha256=lock_hash,
            validation_selected_sha256="selected-sha",
            validation_artifact_count=47,
            data_pair_count_proof_sha256="data-proof-sha",
            final_test_exposure_state="LOCKED",
        )

    calls: list[tuple[str, str, str]] = []

    def fake_runner(level: int):
        def run(**kwargs: Any) -> SimpleNamespace:
            calls.append((f"level_{level}", kwargs["split"], kwargs["final_test_lock_hash"]))
            artifacts_dir = Path(kwargs["artifacts_dir"])
            metric_path = artifacts_dir / "metrics" / f"level_{level}.csv"
            metric_path.parent.mkdir(parents=True, exist_ok=True)
            metric_path.write_text(
                "provenance_split,provenance_final_test_lock_hash\n"
                f"final_test,{kwargs['final_test_lock_hash']}\n",
                encoding="utf-8",
            )
            paths = {"metrics": metric_path}
            if level == 5:
                proof = artifacts_dir / "monitoring" / "level_5_pair_count_proof.json"
                proof.parent.mkdir(parents=True, exist_ok=True)
                proof.write_text(
                    json.dumps(
                        {
                            "eligible_count": 104,
                            "scored_count": 100,
                            "selected_count": 25,
                            "runtime_seconds": 1.25,
                            "peak_rss_mb": 256.0,
                        }
                    ),
                    encoding="utf-8",
                )
                return SimpleNamespace(
                    artifact_paths=paths,
                    pair_count_proof_path=proof,
                    universe_scores_path=artifacts_dir
                    / "monitoring"
                    / "level_5_universe_scores.parquet",
                    health_summary_path=artifacts_dir / "monitoring" / "health_summary.csv",
                    alerts_path=artifacts_dir / "monitoring" / "alerts.parquet",
                    scored_count=100,
                    selected_count=25,
                )
            return SimpleNamespace(artifact_paths=paths)

        return run

    monkeypatch.setattr(final_test, "validate_final_test_lock", pass_validation)
    for level in range(1, 6):
        monkeypatch.setattr(final_test, f"run_level_{level}_validation", fake_runner(level))

    result = final_test.run_frozen_final_test(
        repo_root=repo,
        config_path="configs/default.yaml",
        expected_lock_hash=None,
    )

    summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
    exposure = json.loads(result.exposure_path.read_text(encoding="utf-8"))
    metrics = (result.output_dir / "metrics" / "level_5.csv").read_text(encoding="utf-8")

    assert [call[0] for call in calls] == [f"level_{level}" for level in range(1, 6)]
    assert {call[1] for call in calls} == {"final_test"}
    assert {call[2] for call in calls} == {lock_hash}
    assert summary["split"] == "final_test"
    assert summary["final_test_exposure"] == "EXPOSED"
    assert summary["final_test_lock_sha256"] == lock_hash
    assert not summary["final_test_lock_path"].startswith("/")
    assert not summary["artifact_paths"]["level_5"]["metrics"].startswith("/")
    assert summary["level_5_counts"]["eligible_count"] == 104
    assert summary["level_5_counts"]["scored_count"] == 100
    assert summary["level_5_counts"]["selected_count"] == 25
    assert exposure["exposure_transition"]["start_state"] == "LOCKED"
    assert exposure["exposure_transition"]["generated_evidence_state"] == "EXPOSED"
    assert "final_test,abc123" in metrics


def _minimal_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "AGENTS.md").write_text("contract\n", encoding="utf-8")
    (repo / "configs").mkdir()
    (repo / "artifacts").mkdir()

    root = Path(__file__).resolve().parents[2]
    base_config = yaml.safe_load((root / "configs" / "default.yaml").read_text(encoding="utf-8"))
    (repo / "configs" / "default.yaml").write_text(
        yaml.safe_dump(base_config, sort_keys=False),
        encoding="utf-8",
    )
    selected = {
        "selected": {
            "level_1": {"symbol": "BTC/USDT", "fast_window": 30, "slow_window": 100},
            "level_2": {
                "symbol": "BTC/USDT",
                "technical_windows": {"fast": 10, "slow": 50},
                "agent_weights": {
                    "technical": 0.25,
                    "econometric": 0.25,
                    "logistic": 0.25,
                    "hist_gradient_boosting": 0.25,
                },
                "ml_retrain": "monthly",
                "econometric_refit": "daily_causal",
                "safety_margin_bps": 5.0,
                "max_model_age_days": 60,
            },
            "level_3": {
                "selected_method": "cvar_downside",
                "final_symbols": [
                    "BTC/USDT",
                    "ETH/USDT",
                    "SOL/USDT",
                    "PEPE/USDT",
                    "BNB/USDT",
                    "XRP/USDT",
                    "DOGE/USDT",
                ],
                "final_estimation_window": ["2024-01-01", "2024-12-31"],
                "final_evaluation_window_not_run": ["2025-01-01", "2025-12-31"],
            },
            "level_4": {
                "selected_policy": "calendar_monthly",
                "allocator": "cvar_downside",
                "final_estimation_window": ["2024-01-01", "2024-12-31"],
                "final_evaluation_window_not_run": ["2025-01-01", "2025-12-31"],
            },
            "level_5": {
                "allocator": "inverse_volatility",
                "top_k": 25,
                "max_weight": 0.05,
                "rebalance_calendar": "weekly",
                "score_change_threshold": 0.1,
                "turnover_cap": 1.0,
                "required_min_pairs": 100,
            },
        }
    }
    selected_path = repo / "configs" / "validation_selected.yaml"
    selected_path.write_text(yaml.safe_dump(selected, sort_keys=False), encoding="utf-8")
    lock = {
        "hashes": {
            "validation_selected_path": "configs/validation_selected.yaml",
            "data_sha256": "data-sha",
            "instruments_sha256": "instrument-sha",
            "manifest_sha256": "manifest-sha",
        },
        "git": {"commit": "locked-commit"},
        "periods": {"final_test": ["2025-01-01", "2025-12-31"]},
        "cost_assumptions": {"fee_bps_one_way": 10.0, "slippage_bps_one_way": 5.0},
        "benchmarks": {"level_5": "broker_costed_equal_weight_top_k_universe"},
        "seeds": {"project_seed": 42, "statistical_random_seeds": [7, 42, 137]},
        "known_limitations_to_disclose": ["survivorship_bias_active_markets"],
    }
    (repo / "artifacts" / "final_test_lock.json").write_text(
        json.dumps(lock),
        encoding="utf-8",
    )
    (repo / "artifacts" / "final_test_lock.json.metadata.json").write_text(
        "{}",
        encoding="utf-8",
    )
    return repo
