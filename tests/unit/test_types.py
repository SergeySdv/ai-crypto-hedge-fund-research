from datetime import UTC, datetime, timedelta

import pytest

from crypto_hedge_fund.types import (
    AgentContext,
    AgentSignal,
    Fill,
    OrderIntent,
    PortfolioProposal,
    ReasonCode,
    ResearchClock,
    RiskApproval,
)


def _clock() -> ResearchClock:
    start = datetime(2024, 1, 1, tzinfo=UTC)
    return ResearchClock(
        bar_start=start,
        bar_end=start + timedelta(days=1),
        feature_cutoff=start + timedelta(days=1),
        decision_time=start + timedelta(days=1, microseconds=1),
        execution_time=start + timedelta(days=2),
    )


def test_agent_signal_validates_score_confidence_and_cutoffs() -> None:
    clock = _clock()
    signal = AgentSignal(
        symbol="BTC/USDT",
        agent="technical",
        score=0.5,
        confidence=0.7,
        horizon_open_days=1,
        fit_cutoff=clock.feature_cutoff,
        feature_cutoff=clock.feature_cutoff,
        reason_codes=(ReasonCode.OK,),
    )

    assert signal.score == 0.5
    assert signal.reason_codes == (ReasonCode.OK,)

    with pytest.raises(ValueError, match="score"):
        AgentSignal(
            symbol="BTC/USDT",
            agent="technical",
            score=2.0,
            confidence=0.7,
            horizon_open_days=1,
            fit_cutoff=clock.feature_cutoff,
            feature_cutoff=clock.feature_cutoff,
        )


def test_agent_context_validates_fit_cutoff_and_nav() -> None:
    clock = _clock()

    context = AgentContext(
        clock=clock,
        symbols=("BTC/USDT",),
        model_fit_cutoff=clock.feature_cutoff,
        portfolio_nav=1_000_000,
        current_weights={"BTC/USDT": 0.0},
    )

    assert context.symbols == ("BTC/USDT",)

    with pytest.raises(ValueError, match="portfolio_nav"):
        AgentContext(
            clock=clock,
            symbols=("BTC/USDT",),
            model_fit_cutoff=clock.feature_cutoff,
            portfolio_nav=0,
            current_weights={"BTC/USDT": 0.0},
        )


def test_portfolio_proposal_reconciles_cash_and_risky_weights() -> None:
    clock = _clock()

    proposal = PortfolioProposal(
        decision_time=clock.decision_time,
        target_weights={"BTC/USDT": 0.6, "ETH/USDT": 0.2},
        cash_weight=0.2,
        optimizer_status="ok",
        expected_turnover=0.3,
        objective_value=1.0,
        reason_codes=(ReasonCode.OK,),
    )

    assert sum(proposal.target_weights.values()) + proposal.cash_weight == pytest.approx(1.0)

    with pytest.raises(ValueError, match=r"sum to 1\.0"):
        PortfolioProposal(
            decision_time=clock.decision_time,
            target_weights={"BTC/USDT": 0.8},
            cash_weight=0.3,
            optimizer_status="ok",
            expected_turnover=0.3,
            objective_value=None,
            reason_codes=(ReasonCode.OK,),
        )


def test_risk_approval_validates_action_and_weights() -> None:
    approval = RiskApproval(
        approved=True,
        approved_weights={"BTC/USDT": 0.5},
        cash_weight=0.5,
        action="approve",
        reason_codes=(ReasonCode.OK,),
    )

    assert approval.approved

    with pytest.raises(ValueError):
        RiskApproval(
            approved=False,
            approved_weights={},
            cash_weight=1.0,
            action="ignore",
            reason_codes=(ReasonCode.OK,),
        )


def test_order_and_fill_validate_side_status_and_prices() -> None:
    clock = _clock()
    order = OrderIntent(
        order_id="o1",
        symbol="BTC/USDT",
        side="buy",
        execution_time=clock.execution_time,
        target_notional=1000,
        reference_price=50000,
        reason_codes=(ReasonCode.OK,),
    )

    assert order.side == "buy"

    fill = Fill(
        order_id="o1",
        symbol="BTC/USDT",
        side="buy",
        fill_time=clock.execution_time,
        quantity=0.02,
        fill_price=50000,
        fee=1.0,
        slippage_cost=0.5,
        status="filled",
        reason_codes=(ReasonCode.OK,),
    )
    assert fill.status == "filled"

    with pytest.raises(ValueError):
        OrderIntent(
            order_id="o2",
            symbol="BTC/USDT",
            side="hold",
            execution_time=clock.execution_time,
            target_notional=1000,
            reference_price=50000,
            reason_codes=(ReasonCode.OK,),
        )
