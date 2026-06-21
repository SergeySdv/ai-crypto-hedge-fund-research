"""Validation gate for included processed data, manifest hashes and universe proof."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from crypto_hedge_fund.config import find_repo_root, load_config, resolve_repo_path
from crypto_hedge_fund.data.schema import (
    INSTRUMENT_REQUIRED_COLUMNS,
    OHLCV_NUMERIC_COLUMNS,
    OHLCV_REQUIRED_COLUMNS,
    SCHEMA_VERSION,
)
from crypto_hedge_fund.data.storage import read_market_data
from crypto_hedge_fund.data.universe import (
    UniverseRules,
    eligible_universe_at,
    selected_large_universe,
)
from crypto_hedge_fund.provenance import canonical_config_hash, file_sha256, git_commit


class DataValidationError(ValueError):
    """Raised when the frozen data bundle fails a hard Stage 2 data gate."""


@dataclass(frozen=True)
class ValidationResult:
    """Summary of a successful data-bundle validation."""

    row_count: int
    symbol_count: int
    min_bar_start_utc: str
    max_bar_start_utc: str
    proof_path: Path
    eligibility_path: Path
    eligible_count: int
    scored_count: int
    decision_cutoff_utc: str
    data_sha256: str
    instrument_sha256: str
    write_policy: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_count": self.row_count,
            "symbol_count": self.symbol_count,
            "min_bar_start_utc": self.min_bar_start_utc,
            "max_bar_start_utc": self.max_bar_start_utc,
            "proof_path": _repo_relative_path(self.proof_path),
            "eligibility_path": _repo_relative_path(self.eligibility_path),
            "eligible_count": self.eligible_count,
            "scored_count": self.scored_count,
            "decision_cutoff_utc": self.decision_cutoff_utc,
            "data_sha256": self.data_sha256,
            "instrument_sha256": self.instrument_sha256,
            "write_policy": self.write_policy,
        }


def _require_columns(frame: pd.DataFrame, required: tuple[str, ...], *, label: str) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        msg = f"{label} missing required columns: {missing}"
        raise DataValidationError(msg)


def _require_utc(series: pd.Series, *, column: str) -> None:
    dtype = series.dtype
    if not isinstance(dtype, pd.DatetimeTZDtype) or str(dtype.tz) != "UTC":
        msg = f"{column} must be timezone-aware UTC, got {dtype}"
        raise DataValidationError(msg)


def _validate_ohlcv_schema(frame: pd.DataFrame, config: dict) -> None:
    _require_columns(frame, OHLCV_REQUIRED_COLUMNS, label="OHLCV data")
    for column in ("bar_start_utc", "bar_end_utc"):
        _require_utc(frame[column], column=column)
    if frame.empty:
        raise DataValidationError("OHLCV data is empty")
    if frame.duplicated(["bar_start_utc", "symbol"]).any():
        duplicates = frame.loc[
            frame.duplicated(["bar_start_utc", "symbol"], keep=False),
            ["bar_start_utc", "symbol"],
        ].head()
        msg = f"Duplicate (bar_start_utc, symbol) keys found: {duplicates.to_dict('records')}"
        raise DataValidationError(msg)
    sorted_frame = frame.sort_values(["bar_start_utc", "symbol"], kind="mergesort")
    if not frame[["bar_start_utc", "symbol"]].equals(sorted_frame[["bar_start_utc", "symbol"]]):
        raise DataValidationError("OHLCV rows must be sorted by bar_start_utc, symbol")
    expected_end = frame["bar_start_utc"] + pd.Timedelta(days=1)
    if not frame["bar_end_utc"].equals(expected_end):
        raise DataValidationError("bar_end_utc must equal bar_start_utc + 1 day")
    for column in OHLCV_NUMERIC_COLUMNS:
        values = frame[column].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise DataValidationError(f"{column} contains NaN or non-finite values")
    if (frame[["open", "high", "low", "close"]] <= 0).any().any():
        raise DataValidationError("OHLC prices must be positive")
    if (frame["volume"] < 0).any():
        raise DataValidationError("volume must be non-negative")
    if (frame["dollar_volume"] < 0).any():
        raise DataValidationError("dollar_volume must be non-negative")
    low = frame["low"]
    high = frame["high"]
    min_oc = frame[["open", "close"]].min(axis=1)
    max_oc = frame[["open", "close"]].max(axis=1)
    if not ((low <= min_oc) & (min_oc <= max_oc) & (max_oc <= high)).all():
        raise DataValidationError("OHLC sanity failed: low <= min(open, close) <= high")
    data_cfg = config["data"]
    if set(frame["exchange"].unique()) != {str(data_cfg["exchange"])}:
        raise DataValidationError("OHLCV exchange column does not match config")
    if set(frame["market_type"].unique()) != {str(data_cfg["market_type"])}:
        raise DataValidationError("OHLCV market_type column does not match config")
    if set(frame["timeframe"].unique()) != {str(data_cfg["timeframe"])}:
        raise DataValidationError("OHLCV timeframe column does not match config")


def _symbol_coverage_from_ohlcv(market_data: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for symbol, group in market_data.groupby("symbol", sort=False):
        first = group["bar_start_utc"].min()
        last = group["bar_start_utc"].max()
        expected = int(pd.date_range(first, last, freq="D", tz=UTC).size)
        bar_count = int(group["bar_start_utc"].nunique())
        missing = expected - bar_count
        rows.append(
            {
                "symbol": symbol,
                "first_bar_start_utc": first,
                "last_bar_start_utc": last,
                "bar_count": bar_count,
                "expected_bar_count": expected,
                "missing_bar_count": missing,
                "coverage_ratio": bar_count / expected if expected else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values("symbol", kind="mergesort").reset_index(drop=True)


def _validate_instruments(
    instruments: pd.DataFrame,
    market_data: pd.DataFrame,
    *,
    proof_cutoff_utc: pd.Timestamp,
    max_stale_days: int,
) -> None:
    _require_columns(instruments, INSTRUMENT_REQUIRED_COLUMNS, label="Instrument metadata")
    for column in ("first_bar_start_utc", "last_bar_start_utc"):
        _require_utc(instruments[column], column=column)
    if instruments.empty:
        raise DataValidationError("Instrument metadata is empty")
    if instruments["symbol"].duplicated().any():
        raise DataValidationError("Instrument symbols must be unique")
    data_symbols = set(market_data["symbol"])
    instrument_symbols = set(instruments["symbol"])
    if not data_symbols <= instrument_symbols:
        missing = sorted(data_symbols - instrument_symbols)[:10]
        raise DataValidationError(f"Missing instrument metadata for data symbols: {missing}")
    if (instruments["coverage_ratio"] < 0).any() or (instruments["coverage_ratio"] > 1).any():
        raise DataValidationError("coverage_ratio must be in [0, 1]")
    recomputed = _symbol_coverage_from_ohlcv(market_data).set_index("symbol")
    metadata = instruments.set_index("symbol")
    comparable = metadata.loc[recomputed.index]
    for column in ("first_bar_start_utc", "last_bar_start_utc"):
        mismatched = comparable[column] != recomputed[column]
        if bool(mismatched.any()):
            examples = mismatched[mismatched].index[:10].tolist()
            raise DataValidationError(
                f"Instrument metadata {column} does not match recomputed OHLCV coverage: {examples}"
            )
    for column in ("bar_count", "expected_bar_count", "missing_bar_count"):
        observed = comparable[column].astype("int64")
        expected = recomputed[column].astype("int64")
        mismatched = observed != expected
        if bool(mismatched.any()):
            examples = mismatched[mismatched].index[:10].tolist()
            raise DataValidationError(
                f"Instrument metadata {column} does not match recomputed OHLCV coverage: {examples}"
            )
    coverage_mismatch = ~np.isclose(
        comparable["coverage_ratio"].astype(float),
        recomputed["coverage_ratio"].astype(float),
        rtol=0.0,
        atol=1e-12,
    )
    if bool(coverage_mismatch.any()):
        examples = comparable.index[coverage_mismatch][:10].tolist()
        raise DataValidationError(
            "Instrument metadata coverage_ratio does not match recomputed OHLCV coverage: "
            f"{examples}"
        )
    missing = recomputed.loc[recomputed["missing_bar_count"] > 0]
    if not missing.empty:
        examples = missing[["missing_bar_count"]].head(10).to_dict(orient="index")
        raise DataValidationError(f"Per-symbol OHLCV continuity gaps found: {examples}")

    cutoff = pd.Timestamp(proof_cutoff_utc)
    cutoff = cutoff.tz_localize(UTC) if cutoff.tzinfo is None else cutoff.tz_convert(UTC)
    usable = market_data.loc[market_data["bar_end_utc"] <= cutoff]
    if usable.empty:
        raise DataValidationError(
            f"No completed OHLCV bars are available at proof cutoff {cutoff.isoformat()}"
        )
    latest_completed_start = cutoff - pd.Timedelta(days=1)
    stale_after = pd.Timedelta(days=max(0, max_stale_days))
    latest_by_symbol = usable.groupby("symbol", sort=False)["bar_start_utc"].max()
    stale_symbols: list[str] = []
    for symbol, latest_start in latest_by_symbol.items():
        if latest_completed_start - latest_start > stale_after:
            stale_symbols.append(str(symbol))
    if stale_symbols:
        raise DataValidationError(
            f"Stale OHLCV coverage at proof cutoff {cutoff.isoformat()}: {stale_symbols[:10]}"
        )


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        msg = f"Missing manifest: {path}"
        raise DataValidationError(msg)
    with path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, dict):
        raise DataValidationError("Manifest must be a JSON object")
    return manifest


def _validate_manifest(
    manifest: dict[str, Any],
    *,
    config: dict,
    market_data_path: Path,
    instruments_path: Path,
    market_data: pd.DataFrame,
) -> tuple[str, str]:
    required = {
        "schema_version",
        "collection_timestamp_utc",
        "source",
        "request",
        "actual_min_bar_start_utc",
        "actual_max_bar_start_utc",
        "row_count",
        "symbol_count",
        "file_sha256",
        "instrument_sha256",
        "git_commit",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise DataValidationError(f"Manifest missing fields: {missing}")
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise DataValidationError(f"Unsupported manifest schema: {manifest['schema_version']}")
    data_sha = file_sha256(market_data_path)
    instrument_sha = file_sha256(instruments_path)
    if manifest["file_sha256"] != data_sha:
        raise DataValidationError("Manifest OHLCV SHA-256 does not match data file")
    if manifest["instrument_sha256"] != instrument_sha:
        raise DataValidationError("Manifest instrument SHA-256 does not match metadata file")
    data_cfg = config["data"]
    source = manifest["source"]
    for key in ("exchange", "market_type", "quote_currency", "timeframe"):
        if str(source.get(key)) != str(data_cfg[key]):
            raise DataValidationError(f"Manifest source.{key} does not match config")
    if int(manifest["row_count"]) != len(market_data):
        raise DataValidationError("Manifest row_count does not match data")
    if int(manifest["symbol_count"]) != int(market_data["symbol"].nunique()):
        raise DataValidationError("Manifest symbol_count does not match data")
    min_start = market_data["bar_start_utc"].min().isoformat()
    max_start = market_data["bar_start_utc"].max().isoformat()
    if manifest["actual_min_bar_start_utc"] != min_start:
        raise DataValidationError("Manifest actual_min_bar_start_utc does not match data")
    if manifest["actual_max_bar_start_utc"] != max_start:
        raise DataValidationError("Manifest actual_max_bar_start_utc does not match data")
    return data_sha, instrument_sha


def _proof_cutoff(config: dict, market_data: pd.DataFrame) -> pd.Timestamp:
    test_start = pd.Timestamp(config["splits"]["test_start"], tz=UTC)
    test_end = pd.Timestamp(config["splits"]["test_end"], tz=UTC)
    in_period_cutoff = min(test_start + pd.Timedelta(days=181), test_end)
    max_bar_end = market_data["bar_end_utc"].max()
    return min(in_period_cutoff, max_bar_end)


def _repo_relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(find_repo_root()).as_posix()
    except ValueError:
        return resolved.as_posix()


@dataclass(frozen=True)
class _UniverseProof:
    eligibility: pd.DataFrame
    selected: pd.DataFrame
    eligible_count: int
    scored_count: int
    cutoff: pd.Timestamp


def _final_test_lock_payload(config: dict) -> tuple[Path, dict[str, Any]] | None:
    final_test = config.get("final_test")
    if not isinstance(final_test, dict) or not final_test.get("lock_path"):
        return None

    lock_path = resolve_repo_path(final_test["lock_path"])
    if not lock_path.exists():
        return None

    with lock_path.open("r", encoding="utf-8") as handle:
        lock_payload = json.load(handle)
    if not isinstance(lock_payload, dict):
        raise DataValidationError(f"Final-test lock must be a JSON object: {lock_path}")
    return lock_path, lock_payload


def _detected_final_test_state(config: dict) -> str:
    locked = _final_test_lock_payload(config)
    if locked is None:
        return "NOT_LOCKED"
    lock_path, lock_payload = locked
    lock_hash = file_sha256(lock_path)
    artifacts_dir = Path(config["paths"]["artifacts"])
    final_dir = artifacts_dir / "final_test" / lock_hash[:12]
    for evidence_name in ("final_test_exposure_evidence.json", "final_test_suite_summary.json"):
        evidence_path = final_dir / evidence_name
        if not evidence_path.exists():
            continue
        with evidence_path.open("r", encoding="utf-8") as handle:
            evidence = json.load(handle)
        if isinstance(evidence, dict) and evidence.get("final_test_exposure") == "EXPOSED":
            return "EXPOSED"
    state = lock_payload.get("final_test_exposure_state")
    return str(state) if isinstance(state, str) else "LOCKED"


def _locked_data_proof_path(config: dict, proof_path: Path) -> Path | None:
    """Return and verify the lock-covered data proof path, if one is declared."""
    locked = _final_test_lock_payload(config)
    if locked is None:
        return None
    _, lock_payload = locked
    if lock_payload.get("final_test_exposure_state") != "LOCKED":
        return None

    hashes = lock_payload.get("hashes")
    if not isinstance(hashes, dict):
        return None
    locked_hash = hashes.get("data_validation_pair_count_proof_sha256")
    locked_path_value = hashes.get("data_validation_pair_count_proof_path")
    if not isinstance(locked_hash, str) or not isinstance(locked_path_value, str):
        return None

    locked_path = resolve_repo_path(locked_path_value)
    if locked_path.resolve() != proof_path.resolve():
        return None
    if not locked_path.exists():
        raise DataValidationError(
            "Locked data-validation proof is missing; restore "
            f"{_repo_relative_path(locked_path)} before running validate-data"
        )
    actual_hash = file_sha256(locked_path)
    if actual_hash != locked_hash:
        raise DataValidationError(
            "Locked data-validation proof hash mismatch before validate-data; "
            f"expected {locked_hash}, got {actual_hash}. Restore "
            f"{_repo_relative_path(locked_path)} from the accepted checkpoint."
        )
    return locked_path


def _compute_universe_proof(
    *,
    config: dict,
    market_data: pd.DataFrame,
    instruments: pd.DataFrame,
) -> _UniverseProof:
    rules = UniverseRules.from_config(config)
    cutoff = _proof_cutoff(config, market_data)
    eligibility = eligible_universe_at(
        market_data,
        instruments,
        decision_cutoff_utc=cutoff,
        rules=rules,
    )
    selected = selected_large_universe(eligibility, rules=rules)
    eligible_count = int(eligibility["eligible"].sum())
    scored_count = len(selected)
    if eligible_count < 100 or scored_count < 100:
        msg = (
            "Full-mode Level 5 universe proof requires at least 100 eligible/scored pairs; "
            f"eligible={eligible_count}, scored={scored_count}, cutoff={cutoff.isoformat()}"
        )
        raise DataValidationError(msg)
    return _UniverseProof(
        eligibility=eligibility,
        selected=selected,
        eligible_count=eligible_count,
        scored_count=scored_count,
        cutoff=cutoff,
    )


def _proof_payload(
    *,
    config: dict,
    proof: _UniverseProof,
    manifest: dict[str, Any],
    manifest_path: Path,
    data_sha: str,
    instrument_sha: str,
    eligibility_path: Path,
) -> dict[str, Any]:
    rules = UniverseRules.from_config(config)
    selected = proof.selected
    return {
        "mode": "full",
        "proof_owner": "data_validation",
        "generated_by": "make generate-data-proof",
        "write_policy": "pre_lock_primary_proof",
        "decision_cutoff_utc": proof.cutoff.isoformat(),
        "eligible_count": proof.eligible_count,
        "scored_count": proof.scored_count,
        "required_min_pairs": 100,
        "large_universe_size": rules.large_universe_size,
        "selected_scored_symbols": selected["symbol"].tolist(),
        "eligibility_rules": {
            "quote_currency": rules.quote_currency,
            "min_history_days": rules.min_history_days,
            "preferred_history_days": rules.preferred_history_days,
            "liquidity_lookback_days": rules.liquidity_lookback_days,
            "min_trailing_valid_days": rules.min_trailing_valid_days,
            "rank_metric": "trailing_90_day_median_dollar_volume",
        },
        "data_sha256": data_sha,
        "instrument_sha256": instrument_sha,
        "manifest_sha256": file_sha256(manifest_path),
        "source": manifest.get("source", {}),
        "data_period": {
            "actual_min_bar_start_utc": manifest.get("actual_min_bar_start_utc"),
            "actual_max_bar_start_utc": manifest.get("actual_max_bar_start_utc"),
            "row_count": manifest.get("row_count"),
            "symbol_count": manifest.get("symbol_count"),
        },
        "config_hash": canonical_config_hash(config),
        "git_commit": git_commit(),
        "eligibility_csv": _repo_relative_path(eligibility_path),
        "locked_data_validation_proof": None,
        "exclusion_counts": proof.eligibility["reason"].value_counts().sort_index().to_dict(),
        "trailing_liquidity_stats": {
            "median": float(selected["trailing_median_dollar_volume"].median()),
            "min": float(selected["trailing_median_dollar_volume"].min()),
            "max": float(selected["trailing_median_dollar_volume"].max()),
        },
    }


def _proof_paths(config: dict) -> tuple[Path, Path]:
    artifacts = Path(config["paths"]["artifacts"])
    monitoring = artifacts / "monitoring"
    return (
        monitoring / "level_5_data_pair_count_proof.json",
        monitoring / "universe_eligibility_full.csv",
    )


def _verify_existing_universe_proof(
    *,
    config: dict,
    proof: _UniverseProof,
    manifest: dict[str, Any],
    manifest_path: Path,
    data_sha: str,
    instrument_sha: str,
) -> tuple[Path, Path]:
    proof_path, eligibility_path = _proof_paths(config)
    locked_proof_path = _locked_data_proof_path(config, proof_path)
    if locked_proof_path is not None:
        proof_path = locked_proof_path
    if not proof_path.exists():
        raise DataValidationError(
            "Missing canonical data-validation proof; run `make generate-data-proof` "
            "before locking or restore the accepted proof artifact."
        )
    if not eligibility_path.exists():
        raise DataValidationError(
            "Missing canonical data-validation eligibility CSV; run `make generate-data-proof` "
            "before locking or restore the accepted proof artifact."
        )

    with proof_path.open("r", encoding="utf-8") as handle:
        saved = json.load(handle)
    if not isinstance(saved, dict):
        raise DataValidationError(f"Data-validation proof must be a JSON object: {proof_path}")
    expected = _proof_payload(
        config=config,
        proof=proof,
        manifest=manifest,
        manifest_path=manifest_path,
        data_sha=data_sha,
        instrument_sha=instrument_sha,
        eligibility_path=eligibility_path,
    )
    comparable_fields = {
        "mode",
        "proof_owner",
        "decision_cutoff_utc",
        "eligible_count",
        "scored_count",
        "required_min_pairs",
        "large_universe_size",
        "selected_scored_symbols",
        "eligibility_rules",
        "data_sha256",
        "instrument_sha256",
        "manifest_sha256",
        "source",
        "data_period",
        "exclusion_counts",
        "trailing_liquidity_stats",
    }
    if locked_proof_path is None:
        comparable_fields.add("config_hash")
        comparable_fields.add("eligibility_csv")
    for field in sorted(comparable_fields):
        if saved.get(field) != expected.get(field):
            raise DataValidationError(
                f"Canonical data-validation proof mismatch for {field}; "
                "run `make generate-data-proof` before locking or restore the accepted proof."
            )
    return proof_path, eligibility_path


def _write_universe_proof(
    *,
    config: dict,
    proof: _UniverseProof,
    manifest: dict[str, Any],
    manifest_path: Path,
    data_sha: str,
    instrument_sha: str,
) -> tuple[Path, Path]:
    proof_path, eligibility_path = _proof_paths(config)
    monitoring = proof_path.parent
    monitoring.mkdir(parents=True, exist_ok=True)
    output = proof.eligibility.copy()
    output["decision_cutoff_utc"] = proof.cutoff.isoformat()
    output["selected_for_scoring"] = output["symbol"].isin(proof.selected["symbol"])
    output.to_csv(eligibility_path, index=False)
    payload = _proof_payload(
        config=config,
        proof=proof,
        manifest=manifest,
        manifest_path=manifest_path,
        data_sha=data_sha,
        instrument_sha=instrument_sha,
        eligibility_path=eligibility_path,
    )
    proof_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return proof_path, eligibility_path


def _validate_data_inputs(
    config_path: str | Path,
) -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
    Path,
    str,
    str,
]:
    config = load_config(config_path, resolve_paths=True)
    market_data_path = Path(config["paths"]["market_data"])
    instruments_path = Path(config["paths"]["instruments"])
    manifest_path = Path(config["paths"]["manifest"])
    market_data, instruments = read_market_data(
        market_data_path=market_data_path,
        instruments_path=instruments_path,
    )
    _validate_ohlcv_schema(market_data, config)
    proof_cutoff = _proof_cutoff(config, market_data)
    _validate_instruments(
        instruments,
        market_data,
        proof_cutoff_utc=proof_cutoff,
        max_stale_days=int(config.get("clock", {}).get("max_stale_valuation_days", 0)),
    )
    manifest = _load_manifest(manifest_path)
    data_sha, instrument_sha = _validate_manifest(
        manifest,
        config=config,
        market_data_path=market_data_path,
        instruments_path=instruments_path,
        market_data=market_data,
    )
    return config, market_data, instruments, manifest, manifest_path, data_sha, instrument_sha


def validate_data_bundle(
    *,
    config_path: str | Path = "configs/default.yaml",
) -> ValidationResult:
    """Validate included processed data and verify the frozen universe proof read-only."""
    config, market_data, instruments, manifest, manifest_path, data_sha, instrument_sha = (
        _validate_data_inputs(config_path)
    )
    proof = _compute_universe_proof(
        config=config,
        market_data=market_data,
        instruments=instruments,
    )
    proof_path, eligibility_path = _verify_existing_universe_proof(
        config=config,
        proof=proof,
        manifest=manifest,
        manifest_path=manifest_path,
        data_sha=data_sha,
        instrument_sha=instrument_sha,
    )
    return ValidationResult(
        row_count=len(market_data),
        symbol_count=int(market_data["symbol"].nunique()),
        min_bar_start_utc=market_data["bar_start_utc"].min().isoformat(),
        max_bar_start_utc=market_data["bar_start_utc"].max().isoformat(),
        proof_path=proof_path,
        eligibility_path=eligibility_path,
        eligible_count=proof.eligible_count,
        scored_count=proof.scored_count,
        decision_cutoff_utc=proof.cutoff.isoformat(),
        data_sha256=data_sha,
        instrument_sha256=instrument_sha,
        write_policy="read_only_verify_existing_proof",
    )


def generate_data_proof(
    *,
    config_path: str | Path = "configs/default.yaml",
) -> ValidationResult:
    """Generate the canonical data proof before final-test lock/exposure."""
    config, market_data, instruments, manifest, manifest_path, data_sha, instrument_sha = (
        _validate_data_inputs(config_path)
    )
    exposure_state = _detected_final_test_state(config)
    if exposure_state != "NOT_LOCKED":
        raise DataValidationError(
            "Data-proof generation is allowed only before final-test lock/exposure; "
            f"detected state={exposure_state}. Restore the accepted proof instead."
        )
    proof = _compute_universe_proof(
        config=config,
        market_data=market_data,
        instruments=instruments,
    )
    proof_path, eligibility_path = _write_universe_proof(
        config=config,
        proof=proof,
        manifest=manifest,
        manifest_path=manifest_path,
        data_sha=data_sha,
        instrument_sha=instrument_sha,
    )
    return ValidationResult(
        row_count=len(market_data),
        symbol_count=int(market_data["symbol"].nunique()),
        min_bar_start_utc=market_data["bar_start_utc"].min().isoformat(),
        max_bar_start_utc=market_data["bar_start_utc"].max().isoformat(),
        proof_path=proof_path,
        eligibility_path=eligibility_path,
        eligible_count=proof.eligible_count,
        scored_count=proof.scored_count,
        decision_cutoff_utc=proof.cutoff.isoformat(),
        data_sha256=data_sha,
        instrument_sha256=instrument_sha,
        write_policy="pre_lock_primary_proof",
    )
