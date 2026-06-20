"""Post-allocation risk gate for candidate portfolio vetoes and caps."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd

from crypto_hedge_fund.types import (
    AgentContext,
    ExecutableTargetWeights,
    PortfolioProposal,
    ReasonCode,
    RebalanceDecision,
    RiskAction,
    RiskApproval,
    RiskConstraints,
)


def _dedupe(codes: list[ReasonCode]) -> tuple[ReasonCode, ...]:
    seen: set[ReasonCode] = set()
    ordered: list[ReasonCode] = []
    for code in codes:
        if code not in seen:
            ordered.append(code)
            seen.add(code)
    return tuple(ordered) or (ReasonCode.OK,)


class RiskActionResolutionError(ValueError):
    """Raised when a risk action cannot produce executable target weights."""

    def __init__(self, message: str, reason_codes: tuple[ReasonCode, ...]) -> None:
        super().__init__(message)
        self.reason_codes = _dedupe(list(reason_codes))


def resolve_risk_approval_targets(
    approval: RiskApproval,
    context: AgentContext,
) -> ExecutableTargetWeights:
    """Resolve post-risk action semantics before any broker/order integration.

    The action field is authoritative. Safe fallbacks with ``approved=False`` must
    still produce explicit target weights instead of being skipped by callers.
    """

    try:
        action = RiskAction(approval.action)
    except ValueError as exc:
        raise RiskActionResolutionError(
            f"unsupported risk action: {approval.action}",
            (*approval.reason_codes, ReasonCode.INVALID_DATA),
        ) from exc

    if action in {RiskAction.APPROVE, RiskAction.CAP}:
        return ExecutableTargetWeights(
            risky_weights=approval.approved_weights,
            cash_weight=approval.cash_weight,
            action=action.value,
            reason_codes=approval.reason_codes,
            metadata={"approved": approval.approved, **dict(approval.metadata)},
        )
    if action is RiskAction.CASH:
        return ExecutableTargetWeights(
            risky_weights={},
            cash_weight=1.0,
            action=action.value,
            reason_codes=approval.reason_codes,
            metadata={"approved": approval.approved, **dict(approval.metadata)},
        )
    if action is RiskAction.PRIOR_WEIGHTS:
        risky_weights, cash_weight = _current_context_targets(context)
        return ExecutableTargetWeights(
            risky_weights=risky_weights,
            cash_weight=cash_weight,
            action=action.value,
            reason_codes=approval.reason_codes,
            metadata={"approved": approval.approved, **dict(approval.metadata)},
        )

    raise RiskActionResolutionError(
        f"risk action {action.value!r} is not executable",
        (*approval.reason_codes, ReasonCode.INVALID_DATA),
    )


def _current_context_targets(context: AgentContext) -> tuple[dict[str, float], float]:
    risky_weights = {
        str(symbol): _finite_non_negative_weight(symbol, weight)
        for symbol, weight in context.current_weights.items()
        if str(symbol).lower() != "cash"
    }
    risky_sum = sum(risky_weights.values())
    if risky_sum > 1.0 + 1e-8:
        raise RiskActionResolutionError(
            f"current risky weights sum above 1.0: {risky_sum}",
            (ReasonCode.WEIGHT_RECONCILIATION_FAILURE,),
        )
    return risky_weights, max(0.0, 1.0 - risky_sum)


def _finite_non_negative_weight(symbol: object, weight: object) -> float:
    value = float(weight)
    if not math.isfinite(value) or value < 0:
        raise RiskActionResolutionError(
            f"current weight for {symbol} must be finite and non-negative",
            (ReasonCode.WEIGHT_RECONCILIATION_FAILURE,),
        )
    return value


def _cash_approval(reason: ReasonCode, metadata: dict[str, Any] | None = None) -> RiskApproval:
    return RiskApproval(
        approved=False,
        approved_weights={},
        cash_weight=1.0,
        action=RiskAction.CASH.value,
        reason_codes=(reason,),
        metadata=metadata or {},
    )


def _prior_weights_approval(context: AgentContext, reason: ReasonCode) -> RiskApproval:
    try:
        risky, cash_weight = _current_context_targets(context)
    except RiskActionResolutionError:
        return _cash_approval(ReasonCode.WEIGHT_RECONCILIATION_FAILURE)
    return RiskApproval(
        approved=False,
        approved_weights=risky,
        cash_weight=cash_weight,
        action=RiskAction.PRIOR_WEIGHTS.value,
        reason_codes=(reason,),
    )


@dataclass(frozen=True)
class PostAllocationRiskPolicy:
    """Validate actual target weights after allocation and before broker submission."""

    max_drawdown_stop: float = 0.20
    high_volatility_threshold: float = 0.80
    min_cash_buffer: float = 0.005
    annualization_periods: int = 365

    def approve(
        self,
        proposal: PortfolioProposal,
        rebalance: RebalanceDecision,
        constraints: RiskConstraints,
        context: AgentContext,
        historical_returns: pd.DataFrame,
    ) -> RiskApproval:
        reasons: list[ReasonCode] = []

        if context.health_state.get("kill_switch", False):
            return _cash_approval(ReasonCode.KILL_SWITCH)
        if float(context.health_state.get("drawdown", 0.0)) >= self.max_drawdown_stop:
            return _cash_approval(ReasonCode.DRAWDOWN_STOP)
        if (
            float(context.health_state.get("realized_volatility", 0.0))
            >= self.high_volatility_threshold
        ):
            return _cash_approval(ReasonCode.VOLATILITY_LIMIT)

        if (
            ReasonCode.OPTIMIZER_FAILURE in proposal.reason_codes
            or proposal.optimizer_status != "ok"
        ):
            return _cash_approval(ReasonCode.OPTIMIZER_FAILURE)

        if not rebalance.should_rebalance:
            return _prior_weights_approval(context, ReasonCode.DRIFT_ALERT)

        metadata = dict(proposal.metadata)
        if metadata.get("reconciliation_failure", False):
            return _cash_approval(ReasonCode.RECONCILIATION_FAILURE)
        if metadata.get("capacity_breach", False) or metadata.get("capacity_breach_symbols"):
            return _cash_approval(ReasonCode.CAPACITY_LIMIT)

        try:
            weights = {
                str(symbol): float(weight) for symbol, weight in proposal.target_weights.items()
            }
            cash_weight = float(proposal.cash_weight)
            self._validate_weight_map(weights, cash_weight)
        except (TypeError, ValueError) as exc:
            return _cash_approval(
                ReasonCode.WEIGHT_RECONCILIATION_FAILURE,
                metadata={"error": str(exc)},
            )

        for blocked_symbol in constraints.blocked_symbols:
            if weights.get(blocked_symbol, 0.0) > 1e-12:
                return _cash_approval(
                    ReasonCode.WEIGHT_RECONCILIATION_FAILURE,
                    metadata={"blocked_symbol": blocked_symbol},
                )

        capped = False
        for symbol, cap in constraints.per_asset_caps.items():
            if weights.get(symbol, 0.0) > cap + 1e-12:
                weights[symbol] = cap
                capped = True
                reasons.append(ReasonCode.CONCENTRATION_LIMIT)
        risky_sum = sum(weights.values())
        max_risky_sum = min(constraints.max_gross_exposure, 1.0 - self.min_cash_buffer)
        if risky_sum > max_risky_sum + 1e-12:
            scale = max_risky_sum / risky_sum if risky_sum > 0 else 0.0
            weights = {symbol: weight * scale for symbol, weight in weights.items()}
            capped = True
            reasons.append(ReasonCode.TURNOVER_LIMIT)
            risky_sum = sum(weights.values())
        cash_weight = 1.0 - risky_sum

        if (
            constraints.turnover_cap is not None
            and proposal.expected_turnover > constraints.turnover_cap
        ):
            return _prior_weights_approval(context, ReasonCode.TURNOVER_LIMIT)

        if constraints.volatility_target is not None:
            estimated_vol = self._estimate_portfolio_volatility(weights, historical_returns)
            if estimated_vol is not None and estimated_vol > constraints.volatility_target:
                return _cash_approval(
                    ReasonCode.VOLATILITY_LIMIT,
                    metadata={"estimated_volatility": estimated_vol},
                )

        return RiskApproval(
            approved=True,
            approved_weights=weights,
            cash_weight=cash_weight,
            action=RiskAction.CAP.value if capped else RiskAction.APPROVE.value,
            reason_codes=_dedupe(reasons),
            metadata={
                "cost_buffer_feasible": cash_weight >= self.min_cash_buffer,
                "min_cash_buffer": self.min_cash_buffer,
            },
        )

    @staticmethod
    def _validate_weight_map(weights: dict[str, float], cash_weight: float) -> None:
        if not math.isfinite(cash_weight) or cash_weight < 0:
            msg = "cash_weight must be finite and non-negative"
            raise ValueError(msg)
        for symbol, weight in weights.items():
            if not symbol:
                msg = "weight symbols must be non-empty"
                raise ValueError(msg)
            if not math.isfinite(weight) or weight < 0:
                msg = f"invalid weight for {symbol}: {weight}"
                raise ValueError(msg)
        total = sum(weights.values()) + cash_weight
        if abs(total - 1.0) > 1e-8:
            msg = f"weights plus cash must sum to 1.0, got {total}"
            raise ValueError(msg)

    def _estimate_portfolio_volatility(
        self,
        weights: dict[str, float],
        historical_returns: pd.DataFrame,
    ) -> float | None:
        if historical_returns.empty or not weights:
            return None
        returns = historical_returns.reindex(columns=list(weights)).fillna(0.0)
        weight_series = pd.Series(weights, dtype="float64").reindex(returns.columns).fillna(0.0)
        portfolio_returns = returns @ weight_series
        volatility = float(portfolio_returns.std(ddof=0) * math.sqrt(self.annualization_periods))
        return volatility if math.isfinite(volatility) else None
