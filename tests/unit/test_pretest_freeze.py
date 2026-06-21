from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

from crypto_hedge_fund.pretest_lock import (
    LOCK_SCHEMA_VERSION,
    FinalTestLockValidationError,
    PretestFreezeError,
    run_pretest_freeze,
    validate_final_test_lock,
)
from crypto_hedge_fund.provenance import canonical_config_hash, file_sha256


def test_pretest_freeze_fails_when_validation_artifacts_are_missing(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "configs").mkdir()
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "data" / "manifests").mkdir(parents=True)
    (tmp_path / "uv.lock").write_text("lock", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("contract", encoding="utf-8")
    (tmp_path / "data" / "processed" / "ohlcv_daily.parquet").write_bytes(b"data")
    (tmp_path / "data" / "processed" / "instruments.parquet").write_bytes(b"instruments")
    (tmp_path / "data" / "manifests" / "ohlcv_daily_manifest.json").write_text(
        '{"file_sha256":"x","instrument_sha256":"y"}\n',
        encoding="utf-8",
    )
    (tmp_path / "configs" / "default.yaml").write_text(
        """
project: {seed: 42, timezone: UTC, mode: full}
paths:
  market_data: data/processed/ohlcv_daily.parquet
  instruments: data/processed/instruments.parquet
  manifest: data/manifests/ohlcv_daily_manifest.json
  artifacts: artifacts
level_5: {min_scored_pairs_full: 100}
""",
        encoding="utf-8",
    )
    _git_add_commit(tmp_path)

    with pytest.raises(PretestFreezeError, match="Missing required validation artifacts"):
        run_pretest_freeze(repo_root=tmp_path)


def test_pretest_freeze_refuses_forbidden_methodology_dirty_path(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "AGENTS.md").write_text("contract", encoding="utf-8")
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "default.yaml").write_text("project: {}\n", encoding="utf-8")
    _git_add_commit(tmp_path)
    (tmp_path / "configs" / "default.yaml").write_text("project: {seed: 7}\n", encoding="utf-8")

    with pytest.raises(PretestFreezeError, match="Forbidden uncommitted methodology"):
        run_pretest_freeze(repo_root=tmp_path)


def test_validate_final_test_lock_accepts_matching_hashes(tmp_path: Path) -> None:
    paths = _write_lock_validation_fixture(tmp_path)

    result = validate_final_test_lock(repo_root=tmp_path)

    assert result.final_test_exposure_state == "LOCKED"
    assert result.final_test_lock_sha256 == file_sha256(paths["lock"])
    assert result.validation_selected_sha256 == file_sha256(paths["selected"])
    assert result.validation_artifact_count == 1
    assert result.data_pair_count_proof_sha256 == file_sha256(paths["data_proof"])


def test_validate_final_test_lock_refuses_mutated_selected_config(tmp_path: Path) -> None:
    paths = _write_lock_validation_fixture(tmp_path)
    paths["selected"].write_text("schema_version: changed\n", encoding="utf-8")

    with pytest.raises(FinalTestLockValidationError, match="validation-selected config hash"):
        validate_final_test_lock(repo_root=tmp_path)


def test_validate_final_test_lock_refuses_mutated_validation_artifact(tmp_path: Path) -> None:
    paths = _write_lock_validation_fixture(tmp_path)
    paths["artifact"].write_text('{"split":"validation","mutated":true}\n', encoding="utf-8")

    with pytest.raises(FinalTestLockValidationError, match="Validation artifact hash mismatch"):
        validate_final_test_lock(repo_root=tmp_path)


def _write_lock_validation_fixture(tmp_path: Path) -> dict[str, Path]:
    _init_git_repo(tmp_path)
    (tmp_path / "AGENTS.md").write_text("contract", encoding="utf-8")
    (tmp_path / "configs").mkdir()
    (tmp_path / "artifacts" / "monitoring").mkdir(parents=True)
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "data" / "manifests").mkdir(parents=True)

    uv_lock = tmp_path / "uv.lock"
    pyproject = tmp_path / "pyproject.toml"
    market_data = tmp_path / "data" / "processed" / "ohlcv_daily.parquet"
    instruments = tmp_path / "data" / "processed" / "instruments.parquet"
    manifest_path = tmp_path / "data" / "manifests" / "ohlcv_daily_manifest.json"
    selected_path = tmp_path / "configs" / "validation_selected.yaml"
    artifact_path = tmp_path / "artifacts" / "monitoring" / "level_5_pair_count_proof.json"
    data_proof_path = tmp_path / "artifacts" / "monitoring" / "level_5_data_pair_count_proof.json"
    lock_path = tmp_path / "artifacts" / "final_test_lock.json"
    metadata_path = tmp_path / "artifacts" / "final_test_lock.json.metadata.json"

    uv_lock.write_text("lock\n", encoding="utf-8")
    pyproject.write_text("[project]\nname='fixture'\n", encoding="utf-8")
    market_data.write_bytes(b"data")
    instruments.write_bytes(b"instruments")
    manifest_path.write_text(
        json.dumps(
            {
                "file_sha256": file_sha256(market_data),
                "instrument_sha256": file_sha256(instruments),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    selected_payload = {
        "schema_version": "validation-selected-methodology-v1",
        "final_test_exposure_state_before_lock": "NOT_EXPOSED",
        "selected": {"level_5": {"validated_scored_count": 100}},
    }
    selected_path.write_text(yaml.safe_dump(selected_payload, sort_keys=False), encoding="utf-8")
    artifact_path.write_text(
        '{"split":"validation","final_test_exposure":"NOT_EXPOSED","scored_count":100}\n',
        encoding="utf-8",
    )
    data_proof_path.write_text(
        '{"proof_owner":"data_validation","scored_count":104}\n',
        encoding="utf-8",
    )
    default_config = {
        "paths": {
            "market_data": "data/processed/ohlcv_daily.parquet",
            "instruments": "data/processed/instruments.parquet",
            "manifest": "data/manifests/ohlcv_daily_manifest.json",
            "artifacts": "artifacts",
        },
        "final_test": {
            "lock_path": "artifacts/final_test_lock.json",
            "refuse_hash_mismatch": True,
        },
    }
    (tmp_path / "configs" / "default.yaml").write_text(
        yaml.safe_dump(default_config, sort_keys=False),
        encoding="utf-8",
    )

    selected_config = yaml.safe_load(selected_path.read_text(encoding="utf-8"))
    lock_payload = {
        "lock_schema_version": LOCK_SCHEMA_VERSION,
        "final_test_exposure_state": "LOCKED",
        "final_test_results_inspected": False,
        "hashes": {
            "uv_lock_sha256": file_sha256(uv_lock),
            "pyproject_sha256": file_sha256(pyproject),
            "data_sha256": file_sha256(market_data),
            "instruments_sha256": file_sha256(instruments),
            "manifest_sha256": file_sha256(manifest_path),
            "manifest_recorded_data_sha256": file_sha256(market_data),
            "manifest_recorded_instruments_sha256": file_sha256(instruments),
            "validation_selected_path": "configs/validation_selected.yaml",
            "validation_selected_sha256": file_sha256(selected_path),
            "validation_selected_canonical_sha256": canonical_config_hash(selected_config),
            "default_config_canonical_sha256": canonical_config_hash(default_config),
            "validation_artifact_hashes": {
                "artifacts/monitoring/level_5_pair_count_proof.json": file_sha256(artifact_path)
            },
            "data_validation_pair_count_proof_path": (
                "artifacts/monitoring/level_5_data_pair_count_proof.json"
            ),
            "data_validation_pair_count_proof_sha256": file_sha256(data_proof_path),
        },
    }
    lock_path.write_text(
        json.dumps(lock_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    metadata_path.write_text(
        json.dumps(
            {
                "artifact": "artifacts/final_test_lock.json",
                "final_test_lock_sha256": file_sha256(lock_path),
                "lock_schema_version": LOCK_SCHEMA_VERSION,
                "final_test_exposure_state": "LOCKED",
                "config_sha256": file_sha256(selected_path),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "lock": lock_path,
        "metadata": metadata_path,
        "selected": selected_path,
        "artifact": artifact_path,
        "data_proof": data_proof_path,
    }


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path,
        check=True,
        capture_output=True,
    )


def _git_add_commit(path: Path) -> None:
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=path, check=True, capture_output=True)
