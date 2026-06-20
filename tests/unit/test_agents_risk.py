from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from crypto_hedge_fund.agents import FixedSignalAgent, SignalAggregator, TypedAgentOrchestrator
from crypto_hedge_fund.risk import PreAllocationRiskPolicy
from crypto_hedge_fund.types import AgentContext, ReasonCode, ResearchClock


def _clock() -> ResearchClock:
    start = datetime(2024, 6, 1, tzinfo=UTC)
    return ResearchClock(
        bar_start=start,
        bar_end=start + timedelta(days=1),
        feature_cutoff=start + timedelta(days=1),
        decision_time=start + timedelta(days=1),
        execution_time=start + timedelta(days=1),
    )


def _context(*, model_age_days: int = 0) -> AgentContext:
    clock = _clock()
    return AgentContext(
        clock=clock,
        symbols=("BTC/USDT",),
        model_fit_cutoff=clock.feature_cutoff - timedelta(days=model_age_days),
        portfolio_nav=1_000_000,
        current_weights={"BTC/USDT": 0.0},
    )


def _snapshot(
    *,
    cutoff_delta_days: int = 0,
    dollar_volume: float = 10_000_000,
) -> pd.DataFrame:
    clock = _clock()
    return pd.DataFrame(
        {
            "symbol": ["BTC/USDT"],
            "bar_end_utc": [clock.feature_cutoff - timedelta(days=cutoff_delta_days)],
            "dollar_volume": [dollar_volume],
        }
    )


def _aggregate(context: AgentContext):
    result = TypedAgentOrchestrator(
        [FixedSignalAgent(name="agent_a", scores={"BTC/USDT": 0.4})]
    ).run(pd.DataFrame(), context)
    return list(result.aggregated_signals)


def test_pre_allocation_blocks_stale_or_missing_data() -> None:
    context = _context()
    gate = PreAllocationRiskPolicy(max_stale_data_days=0)

    stale = gate.constraints(_aggregate(context), context, _snapshot(cutoff_delta_days=1))
    missing = gate.constraints(_aggregate(context), context, pd.DataFrame())

    assert stale.blocked_symbols == ("BTC/USDT",)
    assert ReasonCode.STALE_DATA in stale.reason_codes
    assert missing.blocked_symbols == ("BTC/USDT",)
    assert ReasonCode.STALE_DATA in missing.reason_codes


def test_pre_allocation_blocks_stale_model_cutoff() -> None:
    context = _context(model_age_days=400)

    constraints = PreAllocationRiskPolicy(max_model_age_days=365).constraints(
        _aggregate(context),
        context,
        _snapshot(),
    )

    assert constraints.blocked_symbols == ("BTC/USDT",)
    assert ReasonCode.STALE_MODEL in constraints.reason_codes


def test_pre_allocation_blocks_excessive_agent_disagreement() -> None:
    context = _context()
    result = TypedAgentOrchestrator(
        [
            FixedSignalAgent(name="bull", scores={"BTC/USDT": 1.0}),
            FixedSignalAgent(name="bear", scores={"BTC/USDT": -1.0}),
        ],
        aggregator=SignalAggregator(disagreement_threshold=0.5),
    ).run(pd.DataFrame(), context)

    constraints = PreAllocationRiskPolicy(max_agent_disagreement=0.5).constraints(
        list(result.aggregated_signals),
        context,
        _snapshot(),
    )

    assert constraints.blocked_symbols == ("BTC/USDT",)
    assert ReasonCode.AGENT_DISAGREEMENT in constraints.reason_codes


def test_pre_allocation_blocks_low_liquidity_and_reserves_cost_buffer() -> None:
    context = _context()

    constraints = PreAllocationRiskPolicy(
        max_gross_exposure=1.0,
        cost_buffer_weight=0.02,
        min_dollar_volume=1_000_000,
    ).constraints(_aggregate(context), context, _snapshot(dollar_volume=10_000))

    assert constraints.max_gross_exposure == 0.98
    assert constraints.per_asset_caps["BTC/USDT"] == 0.0
    assert ReasonCode.LOW_LIQUIDITY in constraints.reason_codes
