"""Schema constants for the frozen daily spot OHLCV dataset."""

from __future__ import annotations

from dataclasses import dataclass

SCHEMA_VERSION = "ohlcv-daily-v1"
TIMEFRAME = "1d"

OHLCV_REQUIRED_COLUMNS: tuple[str, ...] = (
    "bar_start_utc",
    "bar_end_utc",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "dollar_volume",
    "exchange",
    "market_type",
    "timeframe",
)

OHLCV_NUMERIC_COLUMNS: tuple[str, ...] = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "dollar_volume",
)

OHLCV_KEY_COLUMNS: tuple[str, ...] = ("bar_start_utc", "symbol")

INSTRUMENT_REQUIRED_COLUMNS: tuple[str, ...] = (
    "symbol",
    "base",
    "quote",
    "exchange",
    "market_type",
    "active",
    "first_bar_start_utc",
    "last_bar_start_utc",
    "bar_count",
    "expected_bar_count",
    "missing_bar_count",
    "coverage_ratio",
)

INSTRUMENT_OPTIONAL_COLUMNS: tuple[str, ...] = (
    "min_amount",
    "min_cost",
    "precision_amount",
    "precision_price",
)


@dataclass(frozen=True)
class DataBundlePaths:
    """Repository-relative or absolute paths for the frozen data bundle."""

    market_data: str
    instruments: str
    manifest: str
    artifacts: str
