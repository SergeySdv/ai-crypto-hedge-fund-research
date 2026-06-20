"""Panel-native OHLCV access for execution and valuation."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

import pandas as pd


class MissingPriceError(ValueError):
    """Raised when a required execution or valuation open price is unavailable."""


def _utc_timestamp(value: datetime | pd.Timestamp) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        msg = f"timestamp must be timezone-aware UTC: {value!r}"
        raise ValueError(msg)
    ts = ts.tz_convert(UTC)
    if ts != pd.Timestamp(value):
        msg = f"timestamp must already be normalized to UTC: {value!r}"
        raise ValueError(msg)
    return ts


@dataclass(frozen=True)
class PanelMarketData:
    """Long-form daily OHLCV data indexed by ``(bar_start_utc, symbol)``."""

    frame: pd.DataFrame

    def __post_init__(self) -> None:
        normalized = self._normalize(self.frame)
        object.__setattr__(self, "frame", normalized)

    @classmethod
    def from_ohlcv(cls, frame: pd.DataFrame) -> PanelMarketData:
        """Build panel data from the repository OHLCV schema."""
        return cls(frame)

    @staticmethod
    def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(frame, pd.DataFrame):
            msg = "frame must be a pandas DataFrame"
            raise TypeError(msg)
        source = frame.copy()
        if isinstance(source.index, pd.MultiIndex) and {"bar_start_utc", "symbol"}.issubset(
            source.index.names
        ):
            source = source.reset_index()
        required = {"bar_start_utc", "symbol", "open", "close"}
        missing = sorted(required.difference(source.columns))
        if missing:
            msg = f"market data missing required columns: {missing}"
            raise ValueError(msg)
        source["bar_start_utc"] = pd.to_datetime(source["bar_start_utc"], utc=True)
        source["symbol"] = source["symbol"].astype(str)
        source["open"] = source["open"].astype("float64")
        source["close"] = source["close"].astype("float64")
        if source.duplicated(["bar_start_utc", "symbol"]).any():
            msg = "market data contains duplicate (bar_start_utc, symbol) rows"
            raise ValueError(msg)
        for column in ("open", "close"):
            valid = source[column].map(math.isfinite) & (source[column] > 0)
            if not valid.all():
                msg = f"market data column {column!r} must be finite and positive"
                raise ValueError(msg)
        source = source.sort_values(["bar_start_utc", "symbol"], kind="mergesort")
        indexed = source.set_index(["bar_start_utc", "symbol"])
        if not indexed.index.is_unique:
            msg = "market data index must be unique"
            raise ValueError(msg)
        return indexed

    @property
    def symbols(self) -> tuple[str, ...]:
        """Sorted symbol universe present in the panel."""
        return tuple(sorted(self.frame.index.get_level_values("symbol").unique()))

    @property
    def open_times(self) -> pd.DatetimeIndex:
        """Sorted UTC bar-open timestamps present in the panel."""
        return pd.DatetimeIndex(sorted(self.frame.index.get_level_values("bar_start_utc").unique()))

    def open_prices(
        self,
        execution_time: datetime | pd.Timestamp,
        symbols: Iterable[str],
        *,
        reason: str = "execution",
    ) -> pd.Series:
        """Return valid open prices for all requested symbols or fail explicitly."""
        requested = tuple(str(symbol) for symbol in symbols)
        if not requested:
            return pd.Series(dtype="float64")
        time = _utc_timestamp(execution_time)
        try:
            rows = self.frame.xs(time, level="bar_start_utc")
        except KeyError as exc:
            msg = f"missing {reason} open for all symbols at {time.isoformat()}"
            raise MissingPriceError(msg) from exc
        missing = [symbol for symbol in requested if symbol not in rows.index]
        if missing:
            msg = f"missing {reason} open at {time.isoformat()} for symbols: {missing}"
            raise MissingPriceError(msg)
        prices = rows.loc[list(requested), "open"].astype("float64")
        valid = prices.map(math.isfinite) & (prices > 0)
        if not valid.all():
            bad = prices.index[~valid].tolist()
            msg = f"invalid {reason} open at {time.isoformat()} for symbols: {bad}"
            raise MissingPriceError(msg)
        return prices

    def benchmark_open_to_open(
        self,
        symbol: str,
        *,
        start_time: datetime | pd.Timestamp,
        end_time: datetime | pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        """Return a one-symbol buy-and-hold benchmark using open-to-open prices."""
        start = _utc_timestamp(start_time)
        end = _utc_timestamp(end_time) if end_time is not None else None
        rows = self.frame.xs(str(symbol), level="symbol").sort_index()
        rows = rows.loc[rows.index >= start]
        if end is not None:
            rows = rows.loc[rows.index <= end]
        if rows.empty:
            msg = f"no benchmark prices for {symbol} from {start.isoformat()}"
            raise MissingPriceError(msg)
        first = float(rows["open"].iloc[0])
        benchmark = rows[["open"]].copy()
        benchmark["benchmark_nav"] = benchmark["open"] / first
        benchmark["benchmark_return"] = benchmark["benchmark_nav"].pct_change().fillna(0.0)
        return benchmark.reset_index().rename(columns={"bar_start_utc": "timestamp"})
