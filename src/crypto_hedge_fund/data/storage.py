"""Parquet storage helpers for processed OHLCV and instrument metadata."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from crypto_hedge_fund.data.schema import (
    INSTRUMENT_REQUIRED_COLUMNS,
    OHLCV_REQUIRED_COLUMNS,
)


def _require_columns(frame: pd.DataFrame, required: tuple[str, ...], *, label: str) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        msg = f"{label} missing required columns: {missing}"
        raise ValueError(msg)


def normalize_ohlcv_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a sorted copy with UTC timestamps and stable column ordering."""
    _require_columns(frame, OHLCV_REQUIRED_COLUMNS, label="OHLCV data")
    normalized = frame.copy()
    for column in ("bar_start_utc", "bar_end_utc"):
        normalized[column] = pd.to_datetime(normalized[column], utc=True)
    normalized["symbol"] = normalized["symbol"].astype(str)
    normalized["exchange"] = normalized["exchange"].astype(str)
    normalized["market_type"] = normalized["market_type"].astype(str)
    normalized["timeframe"] = normalized["timeframe"].astype(str)
    normalized = normalized.sort_values(["bar_start_utc", "symbol"], kind="mergesort")
    ordered_columns = [*OHLCV_REQUIRED_COLUMNS]
    extra_columns = [column for column in normalized.columns if column not in ordered_columns]
    return normalized.loc[:, [*ordered_columns, *extra_columns]].reset_index(drop=True)


def normalize_instruments_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a sorted copy of instrument metadata with UTC timestamp columns."""
    _require_columns(frame, INSTRUMENT_REQUIRED_COLUMNS, label="Instrument metadata")
    normalized = frame.copy()
    for column in ("first_bar_start_utc", "last_bar_start_utc"):
        normalized[column] = pd.to_datetime(normalized[column], utc=True)
    for column in ("symbol", "base", "quote", "exchange", "market_type"):
        normalized[column] = normalized[column].astype(str)
    normalized["active"] = normalized["active"].astype(bool)
    normalized = normalized.sort_values("symbol", kind="mergesort")
    ordered_columns = [*INSTRUMENT_REQUIRED_COLUMNS]
    extra_columns = [column for column in normalized.columns if column not in ordered_columns]
    return normalized.loc[:, [*ordered_columns, *extra_columns]].reset_index(drop=True)


def write_market_data(
    market_data: pd.DataFrame,
    instruments: pd.DataFrame,
    *,
    market_data_path: str | Path,
    instruments_path: str | Path,
) -> None:
    """Write normalized processed data and metadata as compressed Parquet."""
    ohlcv_path = Path(market_data_path)
    instrument_path = Path(instruments_path)
    ohlcv_path.parent.mkdir(parents=True, exist_ok=True)
    instrument_path.parent.mkdir(parents=True, exist_ok=True)
    normalize_ohlcv_frame(market_data).to_parquet(ohlcv_path, index=False, compression="zstd")
    normalize_instruments_frame(instruments).to_parquet(
        instrument_path, index=False, compression="zstd"
    )


def read_market_data(
    *,
    market_data_path: str | Path,
    instruments_path: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read processed OHLCV and instrument metadata from Parquet."""
    ohlcv_path = Path(market_data_path)
    instrument_path = Path(instruments_path)
    if not ohlcv_path.exists():
        msg = f"Missing processed OHLCV file: {ohlcv_path}"
        raise FileNotFoundError(msg)
    if not instrument_path.exists():
        msg = f"Missing instrument metadata file: {instrument_path}"
        raise FileNotFoundError(msg)
    return (
        normalize_ohlcv_frame(pd.read_parquet(ohlcv_path)),
        normalize_instruments_frame(pd.read_parquet(instrument_path)),
    )
