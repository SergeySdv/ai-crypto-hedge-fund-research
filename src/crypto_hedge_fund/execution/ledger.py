"""Typed ledger snapshots for holdings and equity rows."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime

import pandas as pd


def _timestamp(value: datetime | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        msg = "timestamp must be timezone-aware UTC"
        raise ValueError(msg)
    timestamp = timestamp.tz_convert(UTC)
    if timestamp != pd.Timestamp(value):
        msg = "timestamp must already be normalized to UTC"
        raise ValueError(msg)
    return timestamp


def _finite_non_negative(value: float, *, field_name: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        msg = f"{field_name} must be finite and non-negative"
        raise ValueError(msg)
    return number


@dataclass(frozen=True)
class PositionSnapshot:
    """One symbol holding at a valuation timestamp."""

    timestamp: datetime | pd.Timestamp
    symbol: str
    quantity: float
    price: float
    market_value: float
    weight: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", _timestamp(self.timestamp))
        if not self.symbol:
            msg = "symbol must be non-empty"
            raise ValueError(msg)
        object.__setattr__(
            self, "quantity", _finite_non_negative(self.quantity, field_name="quantity")
        )
        object.__setattr__(self, "price", _finite_non_negative(self.price, field_name="price"))
        object.__setattr__(
            self,
            "market_value",
            _finite_non_negative(self.market_value, field_name="market_value"),
        )
        object.__setattr__(self, "weight", _finite_non_negative(self.weight, field_name="weight"))


@dataclass(frozen=True)
class EquitySnapshot:
    """Portfolio-level ledger row after valuation and optional execution."""

    timestamp: datetime | pd.Timestamp
    cash: float
    risky_value: float
    nav: float
    turnover: float
    fees: float
    slippage: float
    exposure: float
    trade_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", _timestamp(self.timestamp))
        for field_name in (
            "cash",
            "risky_value",
            "nav",
            "turnover",
            "fees",
            "slippage",
            "exposure",
        ):
            object.__setattr__(
                self,
                field_name,
                _finite_non_negative(getattr(self, field_name), field_name=field_name),
            )
        if self.nav <= 0:
            msg = "nav must be positive"
            raise ValueError(msg)
        if self.trade_count < 0:
            msg = "trade_count must be non-negative"
            raise ValueError(msg)
