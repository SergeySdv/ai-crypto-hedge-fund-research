"""Long-only unlevered portfolio allocators for Stage 4 orchestration."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize

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


def _failure_proposal(
    *,
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


def _cap_and_normalize(
    raw_weights: dict[str, float], constraints: RiskConstraints
) -> dict[str, float]:
    if not raw_weights:
        return {}
    raw = {
        symbol: max(0.0, float(weight))
        for symbol, weight in raw_weights.items()
        if constraints.per_asset_caps.get(symbol, 0.0) > 0 and float(weight) > 0
    }
    if not raw:
        return {}
    caps = {symbol: float(constraints.per_asset_caps.get(symbol, 0.0)) for symbol in raw}
    target_gross = min(float(constraints.max_gross_exposure), sum(caps.values()))
    if target_gross <= 0:
        return {}
    weights = dict.fromkeys(raw, 0.0)
    remaining = set(raw)
    remaining_gross = target_gross
    for _ in range(len(raw)):
        raw_sum = sum(raw[symbol] for symbol in remaining)
        if raw_sum <= 0 or remaining_gross <= 0:
            break
        capped_this_round = set()
        for symbol in sorted(remaining):
            candidate = remaining_gross * raw[symbol] / raw_sum
            if candidate >= caps[symbol]:
                weights[symbol] = caps[symbol]
                capped_this_round.add(symbol)
        if not capped_this_round:
            for symbol in remaining:
                weights[symbol] = remaining_gross * raw[symbol] / raw_sum
            remaining.clear()
            break
        remaining -= capped_this_round
        remaining_gross = target_gross - sum(weights.values())
    return {symbol: weight for symbol, weight in weights.items() if weight > 1e-12}


def _target_gross(symbols: list[str], constraints: RiskConstraints) -> float:
    cap_sum = sum(
        max(0.0, float(constraints.per_asset_caps.get(symbol, 0.0))) for symbol in symbols
    )
    return min(float(constraints.max_gross_exposure), cap_sum)


def _clean_returns(
    historical_returns: pd.DataFrame,
    symbols: list[str],
    *,
    min_periods: int,
) -> pd.DataFrame:
    if historical_returns.empty or len(historical_returns) < min_periods:
        msg = "not enough return history"
        raise ValueError(msg)
    returns = historical_returns.reindex(columns=symbols).dropna(how="any")
    if len(returns) < min_periods:
        msg = "not enough complete return history"
        raise ValueError(msg)
    numeric = returns.astype("float64")
    if not np.isfinite(numeric.to_numpy()).all():
        msg = "return history contains non-finite values"
        raise ValueError(msg)
    return numeric


def _shrink_covariance(returns: pd.DataFrame, shrinkage: float) -> np.ndarray:
    values = returns.to_numpy(dtype="float64")
    covariance = np.cov(values, rowvar=False, ddof=0)
    covariance = np.atleast_2d(covariance).astype("float64")
    if not np.isfinite(covariance).all():
        msg = "covariance matrix contains non-finite values"
        raise ValueError(msg)
    diagonal = np.diag(np.diag(covariance))
    alpha = min(1.0, max(0.0, float(shrinkage)))
    covariance = (1.0 - alpha) * covariance + alpha * diagonal
    covariance += np.eye(covariance.shape[0]) * 1e-10
    return covariance


def _optimize_capped_weights(
    *,
    objective,
    symbols: list[str],
    constraints: RiskConstraints,
    previous_weights: pd.Series,
    objective_name: str,
    metadata: dict[str, object],
) -> PortfolioProposal:
    target_gross = _target_gross(symbols, constraints)
    if target_gross <= 0:
        return _failure_proposal(
            constraints=constraints,
            previous_weights=previous_weights,
            reason="target gross exposure is zero",
        )
    caps = np.array([constraints.per_asset_caps.get(symbol, 0.0) for symbol in symbols])
    if float(caps.sum()) + 1e-12 < target_gross:
        return _failure_proposal(
            constraints=constraints,
            previous_weights=previous_weights,
            reason="per-asset caps cannot fund target gross exposure",
        )
    x0 = np.full(len(symbols), target_gross / len(symbols), dtype="float64")
    x0 = np.minimum(x0, caps)
    if float(x0.sum()) <= 0:
        return _failure_proposal(
            constraints=constraints,
            previous_weights=previous_weights,
            reason="initial optimizer weights are zero",
        )
    x0 *= target_gross / float(x0.sum())
    result = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=[(0.0, float(cap)) for cap in caps],
        constraints=({"type": "eq", "fun": lambda weights: float(weights.sum() - target_gross)},),
        options={"ftol": 1e-12, "maxiter": 500, "disp": False},
    )
    if not result.success or not np.isfinite(result.x).all():
        return _failure_proposal(
            constraints=constraints,
            previous_weights=previous_weights,
            reason=f"{objective_name} optimizer failed: {result.message}",
        )
    weights = {
        symbol: max(0.0, float(weight))
        for symbol, weight in zip(symbols, result.x, strict=True)
        if float(weight) > 1e-12
    }
    objective_value = float(objective(result.x))
    return _proposal(
        constraints=constraints,
        weights=weights,
        previous_weights=previous_weights,
        objective_value=objective_value,
        metadata={**metadata, "objective": objective_name},
    )


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
        if not symbols:
            return _proposal(
                constraints=constraints,
                weights={},
                previous_weights=previous_weights,
                objective_value=None,
                status="no_eligible_symbols",
                reason_codes=(ReasonCode.ABSTAIN,),
            )
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
        return _failure_proposal(
            constraints=constraints,
            previous_weights=previous_weights,
            reason=reason,
        )


@dataclass(frozen=True)
class MinimumVarianceAllocator:
    """Long-only capped minimum-variance allocator with covariance shrinkage."""

    name: str = "minimum_variance"
    min_periods: int = 30
    shrinkage: float = 0.10

    def allocate(
        self,
        signals: pd.Series,
        historical_returns: pd.DataFrame,
        constraints: RiskConstraints,
        previous_weights: pd.Series,
    ) -> PortfolioProposal:
        symbols = _eligible_symbols(signals, constraints)
        try:
            returns = _clean_returns(historical_returns, symbols, min_periods=self.min_periods)
            covariance = _shrink_covariance(returns, self.shrinkage)
        except ValueError as exc:
            return _failure_proposal(
                constraints=constraints,
                previous_weights=previous_weights,
                reason=str(exc),
            )

        def objective(weights: np.ndarray) -> float:
            return float(weights @ covariance @ weights)

        return _optimize_capped_weights(
            objective=objective,
            symbols=symbols,
            constraints=constraints,
            previous_weights=previous_weights,
            objective_name="minimize w' Sigma_shrunk w subject to long-only caps and gross budget",
            metadata={
                "allocator": self.name,
                "shrinkage": self.shrinkage,
                "min_periods": self.min_periods,
            },
        )


@dataclass(frozen=True)
class CvarDownsideAllocator:
    """Robust inverse-CVaR allocator using standalone downside tail risk."""

    name: str = "cvar_downside"
    min_periods: int = 30
    tail_fraction: float = 0.05

    def allocate(
        self,
        signals: pd.Series,
        historical_returns: pd.DataFrame,
        constraints: RiskConstraints,
        previous_weights: pd.Series,
    ) -> PortfolioProposal:
        symbols = _eligible_symbols(signals, constraints)
        try:
            returns = _clean_returns(historical_returns, symbols, min_periods=self.min_periods)
        except ValueError as exc:
            return _failure_proposal(
                constraints=constraints,
                previous_weights=previous_weights,
                reason=str(exc),
            )
        tail_count = max(1, math.ceil(len(returns) * self.tail_fraction))
        standalone_cvar: dict[str, float] = {}
        for symbol in symbols:
            sorted_returns = returns[symbol].sort_values(kind="mergesort").head(tail_count)
            cvar = max(1e-8, -float(sorted_returns.mean()))
            if not math.isfinite(cvar) or cvar <= 0:
                return _failure_proposal(
                    constraints=constraints,
                    previous_weights=previous_weights,
                    reason=f"invalid downside CVaR for {symbol}",
                )
            standalone_cvar[symbol] = cvar
        inv = pd.Series({symbol: 1.0 / value for symbol, value in standalone_cvar.items()})
        weights = (inv / inv.sum() * _target_gross(symbols, constraints)).to_dict()
        weights = _cap_and_normalize(weights, constraints)
        if not weights:
            return _failure_proposal(
                constraints=constraints,
                previous_weights=previous_weights,
                reason="CVaR allocation produced no feasible weights",
            )
        objective_value = float(
            sum(weights[symbol] * standalone_cvar[symbol] for symbol in weights)
        )
        return _proposal(
            constraints=constraints,
            weights=weights,
            previous_weights=previous_weights,
            objective_value=objective_value,
            metadata={
                "allocator": self.name,
                "objective": (
                    "allocate inverse to standalone 5% downside CVaR subject to long-only caps "
                    "and gross budget"
                ),
                "tail_fraction": self.tail_fraction,
                "tail_observation_count": tail_count,
            },
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
