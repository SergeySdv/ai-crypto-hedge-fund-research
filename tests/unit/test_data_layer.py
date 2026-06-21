"""Synthetic test-only fixtures for the Stage 2 data layer."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest
import yaml

from crypto_hedge_fund.data.storage import write_market_data
from crypto_hedge_fund.data.universe import UniverseRules, eligible_universe_at
from crypto_hedge_fund.data.validation import DataValidationError, validate_data_bundle
from crypto_hedge_fund.provenance import file_sha256


def _synthetic_bundle(tmp_path: Path, *, symbols: int = 100) -> Path:
    """Create a labeled synthetic test-only bundle with enough pairs for validation."""
    dates = pd.date_range("2024-01-01", "2025-01-05", freq="D", tz=UTC)
    rows = []
    instrument_rows = []
    for index in range(symbols):
        symbol = f"T{index:03d}/USDT"
        base = f"T{index:03d}"
        for offset, bar_start in enumerate(dates):
            open_price = 10.0 + index + offset * 0.01
            close = open_price + 0.05
            high = close + 0.10
            low = open_price - 0.10
            volume = 1000.0 + index
            rows.append(
                {
                    "bar_start_utc": bar_start,
                    "bar_end_utc": bar_start + pd.Timedelta(days=1),
                    "symbol": symbol,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                    "dollar_volume": close * volume,
                    "exchange": "synthetic",
                    "market_type": "spot",
                    "timeframe": "1d",
                }
            )
        instrument_rows.append(
            {
                "symbol": symbol,
                "base": base,
                "quote": "USDT",
                "exchange": "synthetic",
                "market_type": "spot",
                "active": True,
                "first_bar_start_utc": dates.min(),
                "last_bar_start_utc": dates.max(),
                "bar_count": len(dates),
                "expected_bar_count": len(dates),
                "missing_bar_count": 0,
                "coverage_ratio": 1.0,
            }
        )

    market_path = tmp_path / "data/processed/ohlcv_daily.parquet"
    instruments_path = tmp_path / "data/processed/instruments.parquet"
    manifest_path = tmp_path / "data/manifests/ohlcv_daily_manifest.json"
    write_market_data(
        pd.DataFrame(rows),
        pd.DataFrame(instrument_rows),
        market_data_path=market_path,
        instruments_path=instruments_path,
    )
    written = pd.read_parquet(market_path)
    manifest = {
        "schema_version": "ohlcv-daily-v1",
        "collection_timestamp_utc": datetime.now(UTC).isoformat(),
        "source": {
            "exchange": "synthetic",
            "library": "pytest",
            "library_version": "test-only",
            "market_type": "spot",
            "quote_currency": "USDT",
            "timeframe": "1d",
        },
        "request": {
            "start": "2024-01-01",
            "end": "2025-01-05",
            "symbols": [f"T{index:03d}/USDT" for index in range(symbols)],
        },
        "actual_min_bar_start_utc": written["bar_start_utc"].min().isoformat(),
        "actual_max_bar_start_utc": written["bar_start_utc"].max().isoformat(),
        "row_count": len(written),
        "symbol_count": symbols,
        "file_sha256": file_sha256(market_path),
        "instrument_sha256": file_sha256(instruments_path),
        "git_commit": "synthetic-test-only",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    config = {
        "project": {"name": "synthetic-test-only", "seed": 42, "timezone": "UTC", "mode": "full"},
        "paths": {
            "market_data": market_path.as_posix(),
            "instruments": instruments_path.as_posix(),
            "manifest": manifest_path.as_posix(),
            "artifacts": (tmp_path / "artifacts").as_posix(),
        },
        "data": {
            "exchange": "synthetic",
            "market_type": "spot",
            "quote_currency": "USDT",
            "timeframe": "1d",
            "start": "2024-01-01",
            "end": "2025-01-05",
            "min_history_days": 365,
            "preferred_history_days": 365,
            "large_universe_size": 100,
            "liquidity_lookback_days": 90,
            "stable_bases": ["USDT", "USDC"],
        },
        "splits": {
            "train_start": "2024-01-01",
            "train_end": "2024-06-30",
            "validation_start": "2024-07-01",
            "validation_end": "2024-12-31",
            "test_start": "2025-01-01",
            "test_end": "2025-01-05",
        },
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path


def _bundle_paths(config_path: Path) -> tuple[Path, Path]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return Path(config["paths"]["market_data"]), Path(config["paths"]["instruments"])


def _rewrite_symbol_metadata(
    instruments: pd.DataFrame, market_data: pd.DataFrame, symbol: str
) -> None:
    group = market_data.loc[market_data["symbol"] == symbol]
    first = group["bar_start_utc"].min()
    last = group["bar_start_utc"].max()
    expected = int(pd.date_range(first, last, freq="D", tz=UTC).size)
    bar_count = int(group["bar_start_utc"].nunique())
    mask = instruments["symbol"] == symbol
    instruments.loc[mask, "first_bar_start_utc"] = first
    instruments.loc[mask, "last_bar_start_utc"] = last
    instruments.loc[mask, "bar_count"] = bar_count
    instruments.loc[mask, "expected_bar_count"] = expected
    instruments.loc[mask, "missing_bar_count"] = expected - bar_count
    instruments.loc[mask, "coverage_ratio"] = bar_count / expected


def test_validate_data_bundle_writes_100_pair_proof_for_synthetic_fixture(
    tmp_path: Path,
) -> None:
    config_path = _synthetic_bundle(tmp_path)

    result = validate_data_bundle(config_path=config_path)

    assert result.symbol_count == 100
    assert result.eligible_count == 100
    assert result.scored_count == 100
    assert result.proof_path.exists()
    assert result.proof_path.name == "level_5_data_pair_count_proof.json"
    assert result.eligibility_path.exists()


def test_validate_data_bundle_rejects_manifest_hash_mismatch(tmp_path: Path) -> None:
    config_path = _synthetic_bundle(tmp_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    manifest_path = Path(config["paths"]["manifest"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["file_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(DataValidationError, match="SHA-256"):
        validate_data_bundle(config_path=config_path)


def test_validate_data_bundle_rejects_continuity_gap(tmp_path: Path) -> None:
    config_path = _synthetic_bundle(tmp_path)
    market_path, instruments_path = _bundle_paths(config_path)
    market_data = pd.read_parquet(market_path)
    instruments = pd.read_parquet(instruments_path)
    symbol = "T000/USDT"
    gap_day = pd.Timestamp("2024-06-01", tz=UTC)
    market_data = market_data.loc[
        ~((market_data["symbol"] == symbol) & (market_data["bar_start_utc"] == gap_day))
    ].copy()
    _rewrite_symbol_metadata(instruments, market_data, symbol)
    market_data.to_parquet(market_path, index=False, compression="zstd")
    instruments.to_parquet(instruments_path, index=False, compression="zstd")

    with pytest.raises(DataValidationError, match="continuity gaps"):
        validate_data_bundle(config_path=config_path)


def test_validate_data_bundle_rejects_inconsistent_instrument_metadata(tmp_path: Path) -> None:
    config_path = _synthetic_bundle(tmp_path)
    _, instruments_path = _bundle_paths(config_path)
    instruments = pd.read_parquet(instruments_path)
    instruments.loc[instruments["symbol"] == "T000/USDT", "bar_count"] += 1
    instruments.to_parquet(instruments_path, index=False, compression="zstd")

    with pytest.raises(DataValidationError, match="bar_count does not match"):
        validate_data_bundle(config_path=config_path)


def test_validate_data_bundle_rejects_stale_cutoff_coverage(tmp_path: Path) -> None:
    config_path = _synthetic_bundle(tmp_path)
    market_path, instruments_path = _bundle_paths(config_path)
    market_data = pd.read_parquet(market_path)
    instruments = pd.read_parquet(instruments_path)
    symbol = "T000/USDT"
    stale_after = pd.Timestamp("2025-01-02", tz=UTC)
    market_data = market_data.loc[
        ~((market_data["symbol"] == symbol) & (market_data["bar_start_utc"] > stale_after))
    ].copy()
    _rewrite_symbol_metadata(instruments, market_data, symbol)
    market_data.to_parquet(market_path, index=False, compression="zstd")
    instruments.to_parquet(instruments_path, index=False, compression="zstd")

    with pytest.raises(DataValidationError, match="Stale OHLCV coverage"):
        validate_data_bundle(config_path=config_path)


def test_validate_data_bundle_rejects_duplicate_key(tmp_path: Path) -> None:
    config_path = _synthetic_bundle(tmp_path)
    market_path, _ = _bundle_paths(config_path)
    market_data = pd.read_parquet(market_path)
    market_data = pd.concat([market_data, market_data.iloc[[0]]], ignore_index=True)
    market_data = market_data.sort_values(["bar_start_utc", "symbol"], kind="mergesort")
    market_data.to_parquet(market_path, index=False, compression="zstd")

    with pytest.raises(DataValidationError, match="Duplicate"):
        validate_data_bundle(config_path=config_path)


def test_validate_data_bundle_rejects_bar_end_semantic_error(tmp_path: Path) -> None:
    config_path = _synthetic_bundle(tmp_path)
    market_path, _ = _bundle_paths(config_path)
    market_data = pd.read_parquet(market_path)
    market_data.loc[0, "bar_end_utc"] = market_data.loc[0, "bar_start_utc"] + pd.Timedelta(days=2)
    market_data.to_parquet(market_path, index=False, compression="zstd")

    with pytest.raises(DataValidationError, match="bar_end_utc"):
        validate_data_bundle(config_path=config_path)


def test_validate_data_bundle_rejects_invalid_ohlc(tmp_path: Path) -> None:
    config_path = _synthetic_bundle(tmp_path)
    market_path, _ = _bundle_paths(config_path)
    market_data = pd.read_parquet(market_path)
    market_data.loc[0, "high"] = market_data.loc[0, "low"] - 0.01
    market_data.to_parquet(market_path, index=False, compression="zstd")

    with pytest.raises(DataValidationError, match="OHLC sanity"):
        validate_data_bundle(config_path=config_path)


def test_universe_rules_exclude_stable_and_leveraged_tokens() -> None:
    rules = UniverseRules(
        quote_currency="USDT",
        stable_bases=("USDT", "USDC"),
        min_history_days=2,
        preferred_history_days=2,
        liquidity_lookback_days=2,
        large_universe_size=2,
        min_trailing_valid_days=2,
    )
    dates = pd.date_range("2025-01-01", periods=3, freq="D", tz=UTC)
    instruments = pd.DataFrame(
        [
            {
                "symbol": "AAA/USDT",
                "base": "AAA",
                "quote": "USDT",
                "market_type": "spot",
                "active": True,
            },
            {
                "symbol": "USDC/USDT",
                "base": "USDC",
                "quote": "USDT",
                "market_type": "spot",
                "active": True,
            },
            {
                "symbol": "FOOUP/USDT",
                "base": "FOOUP",
                "quote": "USDT",
                "market_type": "spot",
                "active": True,
            },
        ]
    )
    rows = []
    for symbol in instruments["symbol"]:
        for bar_start in dates:
            rows.append(
                {
                    "bar_start_utc": bar_start,
                    "bar_end_utc": bar_start + pd.Timedelta(days=1),
                    "symbol": symbol,
                    "open": 1.0,
                    "high": 1.2,
                    "low": 0.9,
                    "close": 1.1,
                    "volume": 100.0,
                    "dollar_volume": 110.0,
                }
            )

    eligibility = eligible_universe_at(
        pd.DataFrame(rows),
        instruments,
        decision_cutoff_utc=pd.Timestamp("2025-01-04", tz=UTC),
        rules=rules,
    )

    reasons = eligibility.set_index("symbol")["reason"].to_dict()
    assert reasons["AAA/USDT"] == "eligible"
    assert reasons["USDC/USDT"] == "stable_or_fiat_base"
    assert reasons["FOOUP/USDT"] == "leveraged_token_suffix"
