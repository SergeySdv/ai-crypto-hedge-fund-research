"""Typed deterministic agents and orchestration helpers."""

from crypto_hedge_fund.agents.aggregate import SignalAggregator
from crypto_hedge_fund.agents.base import (
    FixedSignalAgent,
    MomentumSignalAgent,
    VolatilityRegimeAgent,
)
from crypto_hedge_fund.agents.level2 import PredictionTableSignalAgent
from crypto_hedge_fund.agents.orchestrator import AgentRunResult, TypedAgentOrchestrator

__all__ = [
    "AgentRunResult",
    "FixedSignalAgent",
    "MomentumSignalAgent",
    "PredictionTableSignalAgent",
    "SignalAggregator",
    "TypedAgentOrchestrator",
    "VolatilityRegimeAgent",
]
