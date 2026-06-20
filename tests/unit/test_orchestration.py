from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pandas as pd

from crypto_hedge_fund.agents import (
    FixedSignalAgent,
    MomentumSignalAgent,
    SignalAggregator,
    TypedAgentOrchestrator,
    VolatilityRegimeAgent,
)
from crypto_hedge_fund.types import AgentContext, Fill, OrderIntent, ReasonCode, ResearchClock


def _clock() -> ResearchClock:
    start = datetime(2024, 6, 1, tzinfo=UTC)
    return ResearchClock(
        bar_start=start,
        bar_end=start + timedelta(days=1),
        feature_cutoff=start + timedelta(days=1),
        decision_time=start + timedelta(days=1),
        execution_time=start + timedelta(days=1),
    )


def _context(symbols: tuple[str, ...] = ("BTC/USDT",)) -> AgentContext:
    clock = _clock()
    return AgentContext(
        clock=clock,
        symbols=symbols,
        model_fit_cutoff=clock.feature_cutoff,
        portfolio_nav=1_000_000,
        current_weights=dict.fromkeys(symbols, 0.0),
    )


def _feature_frame() -> pd.DataFrame:
    times = pd.date_range("2024-05-29", periods=4, tz="UTC", freq="D")
    return pd.DataFrame(
        {
            "bar_start_utc": list(times) * 2,
            "symbol": ["BTC/USDT"] * 4 + ["ETH/USDT"] * 4,
            "close": [100, 101, 102, 104, 50, 49, 48, 47],
            "realized_vol": [0.2, 0.2, 0.2, 0.2, 0.3, 0.3, 0.3, 0.3],
        }
    ).set_index("bar_start_utc")


def test_two_concrete_agents_communicate_through_orchestrator_and_trace() -> None:
    context = _context(("BTC/USDT", "ETH/USDT"))
    agents = [MomentumSignalAgent(lookback=2), VolatilityRegimeAgent()]
    orchestrator = TypedAgentOrchestrator(agents, aggregator=SignalAggregator())

    result = orchestrator.run(_feature_frame(), context)

    assert {signal.agent for signal in result.signals} == {"momentum", "regime"}
    assert {signal.symbol for signal in result.aggregated_signals} == {"BTC/USDT", "ETH/USDT"}
    btc = next(signal for signal in result.aggregated_signals if signal.symbol == "BTC/USDT")
    assert set(btc.contributions) == {"momentum", "regime"}
    assert result.trace.signals == result.signals
    assert result.trace.aggregated_signals == result.aggregated_signals


class BadNanAgent:
    name = "bad_nan"

    def predict(self, frame: pd.DataFrame, context: AgentContext) -> list[SimpleNamespace]:
        del frame
        return [
            SimpleNamespace(
                symbol=context.symbols[0],
                agent=self.name,
                score=float("nan"),
                confidence=1.0,
                horizon_open_days=1,
                fit_cutoff=context.model_fit_cutoff,
                feature_cutoff=context.clock.feature_cutoff,
                reason_codes=(ReasonCode.OK,),
                metadata={},
            )
        ]


class BadInfAgent:
    name = "bad_inf"

    def predict(self, frame: pd.DataFrame, context: AgentContext) -> list[SimpleNamespace]:
        del frame
        return [
            SimpleNamespace(
                symbol=context.symbols[0],
                agent=self.name,
                score=float("inf"),
                confidence=1.0,
                horizon_open_days=1,
                fit_cutoff=context.model_fit_cutoff,
                feature_cutoff=context.clock.feature_cutoff,
                reason_codes=(ReasonCode.OK,),
                metadata={},
            )
        ]


def test_nan_agent_score_fails_closed_as_abstention() -> None:
    result = TypedAgentOrchestrator([BadNanAgent()]).run(_feature_frame(), _context())

    assert result.signals[0].reason_codes == (ReasonCode.ABSTAIN, ReasonCode.INVALID_DATA)
    assert result.aggregated_signals[0].confidence == 0.0
    assert ReasonCode.INVALID_DATA in result.aggregated_signals[0].reason_codes
    assert any(event.reason_codes == (ReasonCode.INVALID_DATA,) for event in result.events)


def test_inf_agent_score_fails_closed_as_abstention() -> None:
    result = TypedAgentOrchestrator([BadInfAgent()]).run(_feature_frame(), _context())

    assert result.signals[0].score == 0.0
    assert result.signals[0].confidence == 0.0
    assert result.signals[0].reason_codes == (ReasonCode.ABSTAIN, ReasonCode.INVALID_DATA)
    assert result.aggregated_signals[0].confidence == 0.0
    assert ReasonCode.INVALID_DATA in result.aggregated_signals[0].reason_codes
    assert any(event.reason_codes == (ReasonCode.INVALID_DATA,) for event in result.events)


def test_excessive_agent_disagreement_is_reason_coded() -> None:
    context = _context()
    result = TypedAgentOrchestrator(
        [
            FixedSignalAgent(name="bull", scores={"BTC/USDT": 1.0}),
            FixedSignalAgent(name="bear", scores={"BTC/USDT": -1.0}),
        ],
        aggregator=SignalAggregator(disagreement_threshold=0.50),
    ).run(_feature_frame(), context)

    aggregate = result.aggregated_signals[0]
    assert aggregate.disagreement == 1.0
    assert ReasonCode.AGENT_DISAGREEMENT in aggregate.reason_codes


class MutatingAgent:
    name = "mutator"

    def predict(self, frame: pd.DataFrame, context: AgentContext) -> list[object]:
        del frame
        context.current_weights["BTC/USDT"] = 1.0
        return []


def test_signal_agents_cannot_mutate_context_or_emit_execution_records() -> None:
    context = _context()

    result = TypedAgentOrchestrator([MutatingAgent()]).run(_feature_frame(), context)

    assert context.current_weights["BTC/USDT"] == 0.0
    assert result.signals[0].reason_codes == (ReasonCode.ABSTAIN, ReasonCode.MODEL_FAILURE)
    assert not any(isinstance(item, OrderIntent | Fill) for item in result.signals)
    assert not hasattr(context, "orders")
    assert not hasattr(context, "fills")
