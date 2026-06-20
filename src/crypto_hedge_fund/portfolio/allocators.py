"""Long-only unlevered portfolio allocators for Stage 4 orchestration."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from crypto_hedge_fund.types import PortfolioProposal, ReasonCode, RiskConstraints


def _eligible_symbols(signals: pd.Series, constraints: RiskConstraints) -> list[str]:
    clean = signals.astype("float64").replace([math.inf, -math.inf], math.nan).dropna()
    clean.index = clean.index.astype(str)
    return [
        symbol
        for symbol, score in clean.items()
        if symbol not in constraints.blocked_symbols
        and constraints.per_asset_caps.get(symbol, 0.0) > 0
        and score > 0
    ]


def _proposal(
    *,
    constraints: RiskConstraints,
    weights: dict[str, float],
    previous_weights: pd.Series,
    objective_value: float | None,
    status: str = "ok",
    reason_codes: tuple[ReasonCode, ...] = (ReasonCode.OK,),
    metadata: dict[str, object] | None = None,
) -> PortfolioProposal:
    weights = {symbol: max(0.0, float(weight)) for symbol, weight in weights.items()}
    risky_sum = sum(weights.values())
    cash_weight = 1.0 - risky_sum
    previous = previous_weights.astype("float64").reindex(weights, fill_value=0.0)
    target = pd.Series(weights, dtype="float64")
    expected_turnover = float((target - previous).abs().sum())
    return PortfolioProposal(
        decision_time=constraints.decision_time,
        target_weights=weights,
        cash_weight=cash_weight,
        optimizer_status=status,
        expected_turnover=expected_turnover,
        objective_value=objective_value,
        reason_codes=reason_codes,
        metadata=metadata or {},
    )


def _cap_and_normalize(
    raw_weights: dict[str, float], constraints: RiskConstraints
) -> dict[str, float]:
    if not raw_weights:
        return {}
    capped = {
        symbol: min(weight, constraints.per_asset_caps.get(symbol, 0.0))
        for symbol, weight in raw_weights.items()
        if constraints.per_asset_caps.get(symbol, 0.0) > 0
    }
    risky_sum = sum(capped.values())
    if risky_sum <= 0:
        return {}
    max_gross = constraints.max_gross_exposure
    if risky_sum > max_gross:
        capped = {symbol: weight * max_gross / risky_sum for symbol, weight in capped.items()}
    return capped


@dataclass(frozen=True)
class EqualWeightAllocator:
    """Allocate equal risky weights to approved positive-score symbols."""

    name: str = "equal_weight"

    def allocate(
        self,
        signals: pd.Series,
        historical_returns: pd.DataFrame,
        constraints: RiskConstraints,
        previous_weights: pd.Series,
    ) -> PortfolioProposal:
        del historical_returns
        symbols = _eligible_symbols(signals, constraints)
        if not symbols:
            return _proposal(
                constraints=constraints,
                weights={},
                previous_weights=previous_weights,
                objective_value=None,
                status="no_eligible_symbols",
                reason_codes=(ReasonCode.ABSTAIN,),
            )
        base_weight = constraints.max_gross_exposure / len(symbols)
        weights = _cap_and_normalize(dict.fromkeys(symbols, base_weight), constraints)
        return _proposal(
            constraints=constraints,
            weights=weights,
            previous_weights=previous_weights,
            objective_value=None,
        )


@dataclass(frozen=True)
class InverseVolatilityAllocator:
    """Allocate by inverse realized volatility with explicit failure on invalid inputs."""

    name: str = "inverse_volatility"
    min_periods: int = 2

    def allocate(
        self,
        signals: pd.Series,
        historical_returns: pd.DataFrame,
        constraints: RiskConstraints,
        previous_weights: pd.Series,
    ) -> PortfolioProposal:
        symbols = _eligible_symbols(signals, constraints)
        if historical_returns.empty or len(historical_returns) < self.min_periods:
            return self._failure(constraints, previous_weights, "not enough return history")
        returns = historical_returns.reindex(columns=symbols)
        vol = returns.std(ddof=0).replace(0.0, math.nan)
        if vol.isna().any() or (vol <= 0).any():
            return self._failure(
                constraints, previous_weights, "non-positive or missing volatility"
            )
        inv = 1.0 / vol
        inv = inv / inv.sum() * constraints.max_gross_exposure
        weights = _cap_and_normalize(inv.to_dict(), constraints)
        return _proposal(
            constraints=constraints,
            weights=weights,
            previous_weights=previous_weights,
            objective_value=float(-vol.mean()),
        )

    def _failure(
        self,
        constraints: RiskConstraints,
        previous_weights: pd.Series,
        reason: str,
    ) -> PortfolioProposal:
        return _proposal(
            constraints=constraints,
            weights={},
            previous_weights=previous_weights,
            objective_value=None,
            status="optimizer_failure",
            reason_codes=(ReasonCode.OPTIMIZER_FAILURE,),
            metadata={"error": reason},
        )


@dataclass(frozen=True)
class FailingAllocator:
    """Explicit failure fixture used to verify safe optimizer stops."""

    name: str = "failing_allocator"
    message: str = "configured optimizer failure"

    def allocate(
        self,
        signals: pd.Series,
        historical_returns: pd.DataFrame,
        constraints: RiskConstraints,
        previous_weights: pd.Series,
    ) -> PortfolioProposal:
        del signals, historical_returns
        return _proposal(
            constraints=constraints,
            weights={},
            previous_weights=previous_weights,
            objective_value=None,
            status="optimizer_failure",
            reason_codes=(ReasonCode.OPTIMIZER_FAILURE,),
            metadata={"error": self.message},
        )
