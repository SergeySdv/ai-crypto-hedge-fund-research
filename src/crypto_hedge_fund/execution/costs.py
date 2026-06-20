"""Transaction-cost accounting for risky-asset weight changes."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


class InvalidWeightsError(ValueError):
    """Raised when target or pre-trade risky weights are invalid."""


@dataclass(frozen=True)
class CostAssumptions:
    """One-way fee and slippage assumptions in basis points."""

    fee_bps_one_way: float = 10.0
    slippage_bps_one_way: float = 5.0

    def __post_init__(self) -> None:
        for field_name, value in (
            ("fee_bps_one_way", self.fee_bps_one_way),
            ("slippage_bps_one_way", self.slippage_bps_one_way),
        ):
            number = float(value)
            if not math.isfinite(number) or number < 0:
                msg = f"{field_name} must be finite and non-negative"
                raise ValueError(msg)
            object.__setattr__(self, field_name, number)

    @property
    def fee_rate(self) -> float:
        """One-way fee rate as a fraction of risky notional."""
        return self.fee_bps_one_way / 10_000.0

    @property
    def slippage_rate(self) -> float:
        """One-way slippage rate as a fraction of risky notional."""
        return self.slippage_bps_one_way / 10_000.0

    @property
    def total_rate(self) -> float:
        """Combined one-way cost rate as a fraction of risky notional."""
        return self.fee_rate + self.slippage_rate


@dataclass(frozen=True)
class CostBreakdown:
    """Detailed cost and turnover decomposition for a rebalance."""

    nav: float
    gross_traded_notional: float
    gross_traded_notional_fraction: float
    reporting_turnover: float
    fee: float
    slippage: float
    total_cost: float


def _validate_nav(nav: float) -> float:
    number = float(nav)
    if not math.isfinite(number) or number <= 0:
        msg = "nav must be finite and positive"
        raise ValueError(msg)
    return number


def _validate_weights(weights: pd.Series, *, label: str) -> pd.Series:
    if not isinstance(weights, pd.Series):
        msg = f"{label} must be a pandas Series"
        raise TypeError(msg)
    clean = weights.astype("float64").copy()
    clean.index = clean.index.astype(str)
    if clean.index.has_duplicates:
        msg = f"{label} contains duplicate symbols"
        raise InvalidWeightsError(msg)
    if not clean.map(math.isfinite).all():
        msg = f"{label} must contain only finite weights"
        raise InvalidWeightsError(msg)
    if (clean < -1e-12).any():
        msg = f"{label} must be long-only"
        raise InvalidWeightsError(msg)
    clean[clean.abs() < 1e-15] = 0.0
    risky_sum = float(clean.sum())
    if risky_sum > 1.0 + 1e-10:
        msg = f"{label} risky weights exceed the unlevered budget: {risky_sum}"
        raise InvalidWeightsError(msg)
    return clean


def validate_target_risky_weights(
    weights: pd.Series,
    *,
    label: str = "target_weights",
) -> pd.Series:
    """Validate long-only unlevered risky weights and return a normalized copy."""
    return _validate_weights(weights, label=label)


class WeightDeltaCostModel:
    """Charge costs on risky-asset notional traded, never on cash."""

    def __init__(self, assumptions: CostAssumptions | None = None) -> None:
        self.assumptions = assumptions or CostAssumptions()

    def estimate_from_weight_deltas(
        self,
        target_risky_weights: pd.Series,
        pretrade_risky_weights: pd.Series,
        market_snapshot_or_nav: pd.DataFrame | float,
        nav: float | None = None,
    ) -> CostBreakdown:
        """Estimate costs from target and pre-trade risky weights.

        The chargeable notional is ``sum(abs(target_i - pretrade_i)) * nav`` over
        risky assets only. Cash is used for reconciliation in reporting turnover
        but is not a fee-bearing instrument.
        """
        nav_value = _validate_nav(market_snapshot_or_nav if nav is None else nav)
        target = _validate_weights(target_risky_weights, label="target_risky_weights")
        pretrade = _validate_weights(pretrade_risky_weights, label="pretrade_risky_weights")
        symbols = target.index.union(pretrade.index)
        target = target.reindex(symbols, fill_value=0.0)
        pretrade = pretrade.reindex(symbols, fill_value=0.0)

        risky_delta = target - pretrade
        gross_fraction = float(risky_delta.abs().sum())
        target_cash = 1.0 - float(target.sum())
        pretrade_cash = 1.0 - float(pretrade.sum())
        reporting_turnover = 0.5 * (gross_fraction + abs(target_cash - pretrade_cash))
        gross_notional = gross_fraction * nav_value
        fee = gross_notional * self.assumptions.fee_rate
        slippage = gross_notional * self.assumptions.slippage_rate
        return CostBreakdown(
            nav=nav_value,
            gross_traded_notional=gross_notional,
            gross_traded_notional_fraction=gross_fraction,
            reporting_turnover=reporting_turnover,
            fee=fee,
            slippage=slippage,
            total_cost=fee + slippage,
        )
