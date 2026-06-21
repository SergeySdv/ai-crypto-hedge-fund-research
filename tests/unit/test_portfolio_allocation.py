from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pandas as pd
import pytest

from crypto_hedge_fund.portfolio import (
    AlwaysRebalancePolicy,
    CvarDownsideAllocator,
    EqualWeightAllocator,
    FailingAllocator,
    InverseVolatilityAllocator,
    MinimumVarianceAllocator,
)
from crypto_hedge_fund.risk import (
    PostAllocationRiskPolicy,
    RiskActionResolutionError,
    resolve_risk_approval_targets,
)
from crypto_hedge_fund.types import (
    AgentContext,
    PortfolioProposal,
    ReasonCode,
    RebalanceDecision,
    ResearchClock,
    RiskAction,
    RiskApproval,
    RiskConstraints,
)


def _clock() -> ResearchClock:
    start = datetime(2024, 6, 1, tzinfo=UTC)
    return ResearchClock(
        bar_start=start,
        bar_end=start + timedelta(days=1),
        feature_cutoff=start + timedelta(days=1),
        decision_time=start + timedelta(days=1),
        execution_time=start + timedelta(days=1),
    )


def _context(**health_state: float | bool) -> AgentContext:
    clock = _clock()
    return AgentContext(
        clock=clock,
        symbols=("BTC/USDT", "ETH/USDT"),
        model_fit_cutoff=clock.feature_cutoff,
        portfolio_nav=1_000_000,
        current_weights={"BTC/USDT": 0.20, "ETH/USDT": 0.10},
        health_state=health_state,
    )


def _constraints() -> RiskConstraints:
    clock = _clock()
    return RiskConstraints(
        decision_time=clock.decision_time,
        max_gross_exposure=0.98,
        per_asset_caps={"BTC/USDT": 0.60, "ETH/USDT": 0.60},
        blocked_symbols=(),
        volatility_target=None,
        turnover_cap=1.0,
        reason_codes=(ReasonCode.OK,),
        metadata={"cost_buffer_weight": 0.02},
    )


def _returns() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "BTC/USDT": [0.01, -0.01, 0.02, 0.00],
            "ETH/USDT": [0.02, -0.02, 0.01, 0.00],
        }
    )


def _rebalance(context: AgentContext, proposal: PortfolioProposal) -> RebalanceDecision:
    return AlwaysRebalancePolicy().decide(
        proposal,
        pd.Series(context.current_weights, dtype="float64"),
        context,
    )


def test_equal_weight_allocator_returns_long_only_targets_with_cash_buffer() -> None:
    proposal = EqualWeightAllocator().allocate(
        pd.Series({"BTC/USDT": 0.5, "ETH/USDT": 0.2}),
        _returns(),
        _constraints(),
        pd.Series({"BTC/USDT": 0.0, "ETH/USDT": 0.0}),
    )

    assert proposal.optimizer_status == "ok"
    assert sum(proposal.target_weights.values()) == 0.98
    assert proposal.cash_weight == pytest.approx(0.02)
    assert all(weight >= 0 for weight in proposal.target_weights.values())


def test_inverse_volatility_allocator_reports_optimizer_failure_explicitly() -> None:
    proposal = InverseVolatilityAllocator(min_periods=3).allocate(
        pd.Series({"BTC/USDT": 0.5}),
        pd.DataFrame({"BTC/USDT": [0.01]}),
        _constraints(),
        pd.Series(dtype="float64"),
    )

    assert proposal.optimizer_status == "optimizer_failure"
    assert proposal.reason_codes == (ReasonCode.OPTIMIZER_FAILURE,)


def test_minimum_variance_allocator_returns_capped_long_only_weights() -> None:
    proposal = MinimumVarianceAllocator(min_periods=3).allocate(
        pd.Series({"BTC/USDT": 1.0, "ETH/USDT": 1.0}),
        _returns(),
        _constraints(),
        pd.Series(dtype="float64"),
    )

    assert proposal.optimizer_status == "ok"
    assert proposal.cash_weight == pytest.approx(0.02)
    assert sum(proposal.target_weights.values()) == pytest.approx(0.98)
    assert all(0.0 <= weight <= 0.60 for weight in proposal.target_weights.values())
    assert proposal.metadata["allocator"] == "minimum_variance"


def test_cvar_downside_allocator_returns_robust_capped_weights() -> None:
    proposal = CvarDownsideAllocator(min_periods=3).allocate(
        pd.Series({"BTC/USDT": 1.0, "ETH/USDT": 1.0}),
        _returns(),
        _constraints(),
        pd.Series(dtype="float64"),
    )

    assert proposal.optimizer_status == "ok"
    assert proposal.cash_weight == pytest.approx(0.02)
    assert sum(proposal.target_weights.values()) == pytest.approx(0.98)
    assert proposal.metadata["allocator"] == "cvar_downside"


def test_post_allocation_rejects_optimizer_failure() -> None:
    context = _context()
    proposal = FailingAllocator().allocate(
        pd.Series({"BTC/USDT": 0.5}),
        _returns(),
        _constraints(),
        pd.Series(context.current_weights, dtype="float64"),
    )

    approval = PostAllocationRiskPolicy().approve(
        proposal,
        _rebalance(context, proposal),
        _constraints(),
        context,
        _returns(),
    )

    assert not approval.approved
    assert approval.action == RiskAction.CASH.value
    assert approval.reason_codes == (ReasonCode.OPTIMIZER_FAILURE,)


def test_cash_risk_action_resolves_to_executable_all_cash_when_not_approved() -> None:
    proposal = EqualWeightAllocator().allocate(
        pd.Series({"BTC/USDT": 0.5}),
        _returns(),
        _constraints(),
        pd.Series(dtype="float64"),
    )
    approval = PostAllocationRiskPolicy().approve(
        proposal,
        _rebalance(_context(drawdown=0.25), proposal),
        _constraints(),
        _context(drawdown=0.25),
        _returns(),
    )

    targets = resolve_risk_approval_targets(approval, _context(drawdown=0.25))

    assert not approval.approved
    assert approval.action == RiskAction.CASH.value
    assert targets.action == RiskAction.CASH.value
    assert dict(targets.risky_weights) == {}
    assert targets.cash_weight == 1.0
    assert targets.reason_codes == (ReasonCode.DRAWDOWN_STOP,)


def test_prior_weights_risk_action_resolves_current_context_when_not_approved() -> None:
    context = _context()
    proposal = EqualWeightAllocator().allocate(
        pd.Series({"BTC/USDT": 0.5, "ETH/USDT": 0.2}),
        _returns(),
        _constraints(),
        pd.Series(context.current_weights, dtype="float64"),
    )
    hold_decision = RebalanceDecision(
        _clock().decision_time,
        False,
        ("drift_below_threshold",),
        None,
        (ReasonCode.OK,),
    )
    approval = PostAllocationRiskPolicy().approve(
        proposal,
        hold_decision,
        _constraints(),
        context,
        _returns(),
    )

    targets = resolve_risk_approval_targets(approval, context)

    assert not approval.approved
    assert approval.action == RiskAction.PRIOR_WEIGHTS.value
    assert targets.action == RiskAction.PRIOR_WEIGHTS.value
    assert dict(targets.risky_weights) == {"BTC/USDT": 0.20, "ETH/USDT": 0.10}
    assert targets.cash_weight == pytest.approx(0.70)
    assert targets.reason_codes == (ReasonCode.DRIFT_ALERT,)


def test_invalid_or_unsupported_risk_action_fails_closed_with_reason_codes() -> None:
    invalid_approval = SimpleNamespace(
        approved=False,
        action="liquidate",
        reason_codes=(ReasonCode.INVALID_DATA,),
        metadata={},
    )
    reject_approval = RiskApproval(
        approved=False,
        approved_weights={},
        cash_weight=1.0,
        action=RiskAction.REJECT.value,
        reason_codes=(ReasonCode.WEIGHT_RECONCILIATION_FAILURE,),
    )

    with pytest.raises(RiskActionResolutionError) as exc_info:
        resolve_risk_approval_targets(invalid_approval, _context())  # type: ignore[arg-type]

    assert exc_info.value.reason_codes == (ReasonCode.INVALID_DATA,)

    with pytest.raises(RiskActionResolutionError) as exc_info:
        resolve_risk_approval_targets(reject_approval, _context())

    assert exc_info.value.reason_codes == (
        ReasonCode.WEIGHT_RECONCILIATION_FAILURE,
        ReasonCode.INVALID_DATA,
    )


def test_post_allocation_rejects_invalid_weights() -> None:
    context = _context()
    bad_proposal = SimpleNamespace(
        target_weights={"BTC/USDT": 1.2},
        cash_weight=0.0,
        optimizer_status="ok",
        expected_turnover=0.0,
        reason_codes=(ReasonCode.OK,),
        metadata={},
    )

    approval = PostAllocationRiskPolicy().approve(
        bad_proposal,  # type: ignore[arg-type]
        RebalanceDecision(_clock().decision_time, True, ("test",), None, (ReasonCode.OK,)),
        _constraints(),
        context,
        _returns(),
    )

    assert approval.reason_codes == (ReasonCode.WEIGHT_RECONCILIATION_FAILURE,)
    assert approval.cash_weight == 1.0


def test_post_allocation_drawdown_and_volatility_stops_move_to_cash() -> None:
    proposal = EqualWeightAllocator().allocate(
        pd.Series({"BTC/USDT": 0.5}),
        _returns(),
        _constraints(),
        pd.Series(dtype="float64"),
    )

    drawdown_approval = PostAllocationRiskPolicy().approve(
        proposal,
        _rebalance(_context(drawdown=0.25), proposal),
        _constraints(),
        _context(drawdown=0.25),
        _returns(),
    )
    volatility_approval = PostAllocationRiskPolicy().approve(
        proposal,
        _rebalance(_context(realized_volatility=0.90), proposal),
        _constraints(),
        _context(realized_volatility=0.90),
        _returns(),
    )

    assert drawdown_approval.reason_codes == (ReasonCode.DRAWDOWN_STOP,)
    assert volatility_approval.reason_codes == (ReasonCode.VOLATILITY_LIMIT,)
    assert drawdown_approval.cash_weight == 1.0
    assert volatility_approval.cash_weight == 1.0


def test_post_allocation_capacity_and_reconciliation_fail_closed() -> None:
    context = _context()
    base_kwargs = {
        "decision_time": _clock().decision_time,
        "target_weights": {"BTC/USDT": 0.5},
        "cash_weight": 0.5,
        "optimizer_status": "ok",
        "expected_turnover": 0.2,
        "objective_value": None,
        "reason_codes": (ReasonCode.OK,),
    }
    capacity = PortfolioProposal(**base_kwargs, metadata={"capacity_breach": True})
    reconciliation = PortfolioProposal(**base_kwargs, metadata={"reconciliation_failure": True})

    capacity_approval = PostAllocationRiskPolicy().approve(
        capacity,
        _rebalance(context, capacity),
        _constraints(),
        context,
        _returns(),
    )
    reconciliation_approval = PostAllocationRiskPolicy().approve(
        reconciliation,
        _rebalance(context, reconciliation),
        _constraints(),
        context,
        _returns(),
    )

    assert capacity_approval.reason_codes == (ReasonCode.CAPACITY_LIMIT,)
    assert reconciliation_approval.reason_codes == (ReasonCode.RECONCILIATION_FAILURE,)
