"""Rebalance decision helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from crypto_hedge_fund.types import AgentContext, PortfolioProposal, ReasonCode, RebalanceDecision


@dataclass(frozen=True)
class AlwaysRebalancePolicy:
    """Deterministic policy for Stage 4 plumbing and tests."""

    trigger_code: str = "stage4_always"

    def decide(
        self,
        proposal: PortfolioProposal,
        current_weights: pd.Series,
        context: AgentContext,
    ) -> RebalanceDecision:
        del current_weights
        should_rebalance = proposal.optimizer_status == "ok"
        return RebalanceDecision(
            decision_time=context.clock.decision_time,
            should_rebalance=should_rebalance,
            trigger_codes=(self.trigger_code,) if should_rebalance else (),
            expected_net_benefit=None,
            reason_codes=(ReasonCode.OK,) if should_rebalance else proposal.reason_codes,
        )
