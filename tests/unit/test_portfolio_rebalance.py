from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from crypto_hedge_fund.portfolio.rebalance import DynamicRebalancePolicy
from crypto_hedge_fund.types import (
    AgentContext,
    PortfolioProposal,
    ReasonCode,
    ResearchClock,
)


def _clock(day: int = 1) -> ResearchClock:
    start = datetime(2024, 6, day, tzinfo=UTC)
    return ResearchClock(
        bar_start=start,
        bar_end=start + timedelta(days=1),
        feature_cutoff=start + timedelta(days=1),
        decision_time=start + timedelta(days=1),
        execution_time=start + timedelta(days=1),
    )


def _context(
    *,
    previous_rebalance_time: datetime | None = None,
    score_change: float = 0.0,
    risk_trigger: bool = False,
) -> AgentContext:
    clock = _clock()
    metadata = {}
    if previous_rebalance_time is not None:
        metadata["previous_rebalance_time"] = previous_rebalance_time
    return AgentContext(
        clock=clock,
        symbols=("BTC/USDT", "ETH/USDT"),
        model_fit_cutoff=clock.feature_cutoff,
        portfolio_nav=1_000_000,
        current_weights={"BTC/USDT": 0.20, "ETH/USDT": 0.10},
        health_state={
            "aggregate_score_change": score_change,
            "risk_trigger_active": risk_trigger,
        },
        metadata=metadata,
    )


def _proposal(
    weights: dict[str, float] | None = None,
    *,
    turnover: float = 0.20,
    status: str = "ok",
    reason_codes: tuple[ReasonCode, ...] = (ReasonCode.OK,),
) -> PortfolioProposal:
    target = weights or {"BTC/USDT": 0.30, "ETH/USDT": 0.20}
    return PortfolioProposal(
        decision_time=_clock().decision_time,
        target_weights=target,
        cash_weight=1.0 - sum(target.values()),
        optimizer_status=status,
        expected_turnover=turnover,
        objective_value=None,
        reason_codes=reason_codes,
        metadata={"expected_gross_benefit": 0.01},
    )


def test_dynamic_rebalance_policy_triggers_monthly_calendar() -> None:
    policy = DynamicRebalancePolicy(name="calendar", calendar="monthly")
    decision = policy.decide(
        _proposal(),
        pd.Series({"BTC/USDT": 0.20, "ETH/USDT": 0.10}),
        _context(previous_rebalance_time=datetime(2024, 5, 15, tzinfo=UTC)),
    )

    assert decision.should_rebalance
    assert "calendar_monthly" in decision.trigger_codes
    assert decision.reason_codes == (ReasonCode.OK,)


def test_dynamic_rebalance_policy_triggers_weight_drift_without_calendar() -> None:
    policy = DynamicRebalancePolicy(name="drift", calendar="none", drift_threshold_abs=0.05)
    decision = policy.decide(
        _proposal({"BTC/USDT": 0.30, "ETH/USDT": 0.10}),
        pd.Series({"BTC/USDT": 0.20, "ETH/USDT": 0.10}),
        _context(previous_rebalance_time=datetime(2024, 6, 1, tzinfo=UTC)),
    )

    assert decision.should_rebalance
    assert decision.trigger_codes == ("weight_drift",)


def test_dynamic_rebalance_policy_triggers_signal_and_risk_reasons() -> None:
    policy = DynamicRebalancePolicy(
        name="signal_risk",
        calendar="none",
        score_change_threshold=0.15,
        risk_trigger=True,
    )
    decision = policy.decide(
        _proposal({"BTC/USDT": 0.30, "ETH/USDT": 0.20}),
        pd.Series({"BTC/USDT": 0.20, "ETH/USDT": 0.10}),
        _context(
            previous_rebalance_time=datetime(2024, 6, 1, tzinfo=UTC),
            score_change=0.25,
            risk_trigger=True,
        ),
    )

    assert decision.should_rebalance
    assert "signal_change" in decision.trigger_codes
    assert "risk_trigger" in decision.trigger_codes


def test_dynamic_rebalance_policy_skips_minimum_trade_and_turnover_cap() -> None:
    min_trade_policy = DynamicRebalancePolicy(name="min", calendar="none", min_trade_abs=0.02)
    min_trade = min_trade_policy.decide(
        _proposal({"BTC/USDT": 0.205, "ETH/USDT": 0.10}, turnover=0.005),
        pd.Series({"BTC/USDT": 0.20, "ETH/USDT": 0.10}),
        _context(previous_rebalance_time=datetime(2024, 6, 1, tzinfo=UTC)),
    )
    turnover_policy = DynamicRebalancePolicy(name="turnover", calendar="daily", turnover_cap=0.05)
    turnover = turnover_policy.decide(
        _proposal({"BTC/USDT": 0.60, "ETH/USDT": 0.20}, turnover=0.50),
        pd.Series({"BTC/USDT": 0.20, "ETH/USDT": 0.10}),
        _context(previous_rebalance_time=datetime(2024, 6, 1, tzinfo=UTC)),
    )

    assert not min_trade.should_rebalance
    assert "minimum_trade_not_met" in min_trade.trigger_codes
    assert not turnover.should_rebalance
    assert turnover.reason_codes == (ReasonCode.TURNOVER_LIMIT,)


def test_dynamic_rebalance_policy_fails_closed_on_optimizer_failure() -> None:
    policy = DynamicRebalancePolicy(name="failure", calendar="daily")
    decision = policy.decide(
        _proposal(
            {},
            turnover=0.0,
            status="optimizer_failure",
            reason_codes=(ReasonCode.OPTIMIZER_FAILURE,),
        ),
        pd.Series({"BTC/USDT": 0.20, "ETH/USDT": 0.10}),
        _context(previous_rebalance_time=datetime(2024, 6, 1, tzinfo=UTC)),
    )

    assert not decision.should_rebalance
    assert decision.trigger_codes == ("optimizer_not_ok",)
    assert decision.reason_codes == (ReasonCode.OPTIMIZER_FAILURE,)
