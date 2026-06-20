from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from crypto_hedge_fund.agents import FixedSignalAgent, TypedAgentOrchestrator
from crypto_hedge_fund.monitoring import events_to_frame, merge_decision_trace, trace_to_frame
from crypto_hedge_fund.portfolio import AlwaysRebalancePolicy, EqualWeightAllocator
from crypto_hedge_fund.risk import PostAllocationRiskPolicy, PreAllocationRiskPolicy
from crypto_hedge_fund.types import (
    AgentContext,
    EventSeverity,
    MonitoringEvent,
    ReasonCode,
    ResearchClock,
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


def _context() -> AgentContext:
    clock = _clock()
    return AgentContext(
        clock=clock,
        symbols=("BTC/USDT", "ETH/USDT"),
        model_fit_cutoff=clock.feature_cutoff,
        portfolio_nav=1_000_000,
        current_weights={"BTC/USDT": 0.0, "ETH/USDT": 0.0},
    )


def test_monitoring_events_convert_to_frame() -> None:
    event = MonitoringEvent(
        timestamp=_clock().decision_time,
        component="risk",
        severity=EventSeverity.ERROR.value,
        reason_codes=(ReasonCode.STALE_DATA,),
        message="stale data blocked symbol",
        metadata={"symbol": "BTC/USDT"},
    )

    frame = events_to_frame([event])

    assert frame.loc[0, "severity"] == "error"
    assert frame.loc[0, "reason_codes"] == "stale_data"
    assert frame.loc[0, "metadata_symbol"] == "BTC/USDT"


def test_decision_trace_is_notebook_ready_from_agent_to_approval() -> None:
    context = _context()
    agent_result = TypedAgentOrchestrator(
        [
            FixedSignalAgent(name="alpha", scores={"BTC/USDT": 0.8, "ETH/USDT": 0.3}),
            FixedSignalAgent(name="risk_regime", scores={"BTC/USDT": 0.2, "ETH/USDT": 0.1}),
        ]
    ).run(pd.DataFrame(), context)
    snapshot = pd.DataFrame(
        {
            "symbol": ["BTC/USDT", "ETH/USDT"],
            "bar_end_utc": [context.clock.feature_cutoff, context.clock.feature_cutoff],
            "dollar_volume": [10_000_000, 8_000_000],
        }
    )
    constraints = PreAllocationRiskPolicy(cost_buffer_weight=0.02).constraints(
        list(agent_result.aggregated_signals),
        context,
        snapshot,
    )
    signal_series = pd.Series(
        {signal.symbol: signal.score for signal in agent_result.aggregated_signals},
        dtype="float64",
    )
    proposal = EqualWeightAllocator().allocate(
        signal_series,
        pd.DataFrame({"BTC/USDT": [0.01, -0.01], "ETH/USDT": [0.02, -0.02]}),
        constraints,
        pd.Series(context.current_weights, dtype="float64"),
    )
    rebalance = AlwaysRebalancePolicy().decide(
        proposal,
        pd.Series(context.current_weights, dtype="float64"),
        context,
    )
    approval = PostAllocationRiskPolicy().approve(
        proposal,
        rebalance,
        constraints,
        context,
        pd.DataFrame({"BTC/USDT": [0.01, -0.01], "ETH/USDT": [0.02, -0.02]}),
    )
    trace = merge_decision_trace(
        agent_result.trace,
        constraints=constraints,
        proposal=proposal,
        approval=approval,
    )

    frame = trace_to_frame(trace)

    assert set(frame["symbol"]) == {"BTC/USDT", "ETH/USDT"}
    assert "agent_alpha_score" in frame.columns
    assert "candidate_weight" in frame.columns
    assert "approved_weight" in frame.columns
    assert frame["execution_time"].notna().all()
    assert approval.cash_weight >= 0.005
