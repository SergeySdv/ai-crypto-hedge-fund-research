"""Typed agent orchestrator and decision trace construction."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import pandas as pd

from crypto_hedge_fund.agents.aggregate import SignalAggregator
from crypto_hedge_fund.types import (
    AgentContext,
    AgentSignal,
    AggregatedSignal,
    DecisionTrace,
    EventSeverity,
    MonitoringEvent,
    ReasonCode,
)


@dataclass(frozen=True)
class AgentRunResult:
    """Signals, aggregates and trace events for one orchestrator run."""

    signals: tuple[AgentSignal, ...]
    aggregated_signals: tuple[AggregatedSignal, ...]
    events: tuple[MonitoringEvent, ...]
    trace: DecisionTrace


class TypedAgentOrchestrator:
    """Calls signal agents, validates typed outputs and aggregates proposals."""

    def __init__(
        self,
        agents: Iterable[Any],
        *,
        aggregator: SignalAggregator | None = None,
    ) -> None:
        self.agents = tuple(agents)
        if not self.agents:
            msg = "at least one agent is required"
            raise ValueError(msg)
        self.aggregator = aggregator or SignalAggregator()

    def run(self, frame: pd.DataFrame, context: AgentContext) -> AgentRunResult:
        signals: list[AgentSignal] = []
        events: list[MonitoringEvent] = []
        for agent in self.agents:
            agent_name = str(getattr(agent, "name", agent.__class__.__name__))
            try:
                raw_signals = agent.predict(frame, context)
            except Exception as exc:
                signals.extend(
                    self._failure_signal(
                        symbol=symbol,
                        agent=agent_name,
                        context=context,
                        reason=ReasonCode.MODEL_FAILURE,
                        message=str(exc),
                    )
                    for symbol in context.symbols
                )
                events.append(
                    self._event(
                        context,
                        component=f"agent:{agent_name}",
                        severity=EventSeverity.ERROR,
                        reason=ReasonCode.MODEL_FAILURE,
                        message="agent prediction failed closed",
                        metadata={"exception": str(exc)},
                    )
                )
                continue

            for raw_signal in raw_signals:
                signal = self._validate_or_failure(raw_signal, agent_name, context)
                signals.append(signal)
                if signal.reason_codes != (ReasonCode.OK,):
                    events.append(
                        self._event(
                            context,
                            component=f"agent:{signal.agent}",
                            severity=EventSeverity.WARNING,
                            reason=signal.reason_codes[-1],
                            message="agent emitted abstention or failure reason",
                            metadata={"symbol": signal.symbol},
                        )
                    )

        aggregated = tuple(self.aggregator.aggregate(signals, context.symbols))
        for aggregate in aggregated:
            if ReasonCode.AGENT_DISAGREEMENT in aggregate.reason_codes:
                events.append(
                    self._event(
                        context,
                        component="orchestrator",
                        severity=EventSeverity.WARNING,
                        reason=ReasonCode.AGENT_DISAGREEMENT,
                        message="agent disagreement exceeds aggregation threshold",
                        metadata={
                            "symbol": aggregate.symbol,
                            "disagreement": aggregate.disagreement,
                        },
                    )
                )

        trace = DecisionTrace(
            clock=context.clock,
            signals=tuple(signals),
            aggregated_signals=aggregated,
            constraints=None,
            proposal=None,
            approval=None,
            events=tuple(events),
            metadata={"stage": "agents"},
        )
        return AgentRunResult(
            signals=tuple(signals),
            aggregated_signals=aggregated,
            events=tuple(events),
            trace=trace,
        )

    def _validate_or_failure(
        self,
        raw_signal: Any,
        agent_name: str,
        context: AgentContext,
    ) -> AgentSignal:
        try:
            if not isinstance(raw_signal, AgentSignal):
                raw_score = float(raw_signal.score)
                raw_confidence = float(raw_signal.confidence)
                if not math.isfinite(raw_score) or not math.isfinite(raw_confidence):
                    raise ValueError("score and confidence must be finite")
                raw_signal = AgentSignal(
                    symbol=str(raw_signal.symbol),
                    agent=str(getattr(raw_signal, "agent", agent_name)),
                    score=raw_score,
                    confidence=raw_confidence,
                    horizon_open_days=int(raw_signal.horizon_open_days),
                    fit_cutoff=raw_signal.fit_cutoff,
                    feature_cutoff=raw_signal.feature_cutoff,
                    reason_codes=tuple(getattr(raw_signal, "reason_codes", (ReasonCode.OK,))),
                    metadata=dict(getattr(raw_signal, "metadata", {})),
                )
            if raw_signal.symbol not in context.symbols:
                msg = f"signal symbol {raw_signal.symbol} not in context symbols"
                raise ValueError(msg)
            if raw_signal.feature_cutoff > context.clock.feature_cutoff:
                msg = "signal feature_cutoff is after context feature_cutoff"
                raise ValueError(msg)
            if raw_signal.feature_cutoff > context.clock.decision_time:
                msg = "signal feature_cutoff is after decision_time"
                raise ValueError(msg)
        except Exception as exc:
            return self._failure_signal(
                symbol=str(getattr(raw_signal, "symbol", context.symbols[0])),
                agent=agent_name,
                context=context,
                reason=ReasonCode.INVALID_DATA,
                message=str(exc),
            )
        return raw_signal

    @staticmethod
    def _failure_signal(
        *,
        symbol: str,
        agent: str,
        context: AgentContext,
        reason: ReasonCode,
        message: str,
    ) -> AgentSignal:
        if symbol not in context.symbols:
            symbol = context.symbols[0]
        return AgentSignal(
            symbol=symbol,
            agent=agent,
            score=0.0,
            confidence=0.0,
            horizon_open_days=1,
            fit_cutoff=context.model_fit_cutoff,
            feature_cutoff=context.clock.feature_cutoff,
            reason_codes=(ReasonCode.ABSTAIN, reason),
            metadata={"error": message},
        )

    @staticmethod
    def _event(
        context: AgentContext,
        *,
        component: str,
        severity: EventSeverity,
        reason: ReasonCode,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> MonitoringEvent:
        return MonitoringEvent(
            timestamp=context.clock.decision_time,
            component=component,
            severity=severity.value,
            reason_codes=(reason,),
            message=message,
            metadata=metadata or {},
        )
