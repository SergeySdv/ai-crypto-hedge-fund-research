"""Pre-allocation risk gate for signal and market-health validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import pandas as pd

from crypto_hedge_fund.types import (
    AgentContext,
    AggregatedSignal,
    ReasonCode,
    RiskConstraints,
)


def _market_by_symbol(market_snapshot: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(market_snapshot, pd.DataFrame):
        msg = "market_snapshot must be a pandas DataFrame"
        raise TypeError(msg)
    if market_snapshot.empty:
        return pd.DataFrame()
    snapshot = market_snapshot.copy()
    if "symbol" in snapshot.columns:
        snapshot["symbol"] = snapshot["symbol"].astype(str)
        snapshot = snapshot.set_index("symbol", drop=False)
    else:
        snapshot.index = snapshot.index.astype(str)
    return snapshot


def _dedupe(codes: list[ReasonCode]) -> tuple[ReasonCode, ...]:
    ordered: list[ReasonCode] = []
    seen: set[ReasonCode] = set()
    for code in codes:
        if code not in seen:
            ordered.append(code)
            seen.add(code)
    return tuple(ordered) or (ReasonCode.OK,)


@dataclass(frozen=True)
class PreAllocationRiskPolicy:
    """Validate data/model health and create allocation constraints."""

    max_gross_exposure: float = 1.0
    max_per_asset_weight: float = 0.30
    cost_buffer_weight: float = 0.01
    min_dollar_volume: float = 0.0
    max_stale_data_days: int = 0
    max_model_age_days: int = 370
    max_agent_disagreement: float = 0.75
    volatility_target: float | None = None
    turnover_cap: float | None = 0.35

    def constraints(
        self,
        signals: list[AggregatedSignal],
        context: AgentContext,
        market_snapshot: pd.DataFrame,
    ) -> RiskConstraints:
        snapshot = _market_by_symbol(market_snapshot)
        signal_by_symbol = {signal.symbol: signal for signal in signals}
        blocked: list[str] = []
        reasons: list[ReasonCode] = []
        per_asset_caps: dict[str, float] = {}

        if context.health_state.get("kill_switch", False):
            blocked.extend(context.symbols)
            reasons.append(ReasonCode.KILL_SWITCH)

        for symbol in context.symbols:
            cap = min(
                self.max_per_asset_weight,
                max(0.0, self.max_gross_exposure - self.cost_buffer_weight),
            )
            signal = signal_by_symbol.get(symbol)
            row = snapshot.loc[symbol] if symbol in snapshot.index else None

            if signal is None:
                blocked.append(symbol)
                reasons.append(ReasonCode.INVALID_DATA)
                per_asset_caps[symbol] = 0.0
                continue
            if (
                ReasonCode.INVALID_DATA in signal.reason_codes
                or ReasonCode.STALE_DATA in signal.reason_codes
                or ReasonCode.STALE_MODEL in signal.reason_codes
            ):
                blocked.append(symbol)
                reasons.extend(code for code in signal.reason_codes if code != ReasonCode.OK)
            if signal.disagreement > self.max_agent_disagreement or (
                ReasonCode.AGENT_DISAGREEMENT in signal.reason_codes
            ):
                blocked.append(symbol)
                reasons.append(ReasonCode.AGENT_DISAGREEMENT)
            if context.clock.feature_cutoff - context.model_fit_cutoff > timedelta(
                days=self.max_model_age_days
            ):
                blocked.append(symbol)
                reasons.append(ReasonCode.STALE_MODEL)

            if row is None:
                blocked.append(symbol)
                reasons.append(ReasonCode.STALE_DATA)
            else:
                cutoff_value = row.get("feature_cutoff", row.get("bar_end_utc", None))
                if cutoff_value is None or pd.isna(cutoff_value):
                    blocked.append(symbol)
                    reasons.append(ReasonCode.STALE_DATA)
                else:
                    cutoff = pd.Timestamp(cutoff_value).tz_convert("UTC").to_pydatetime()
                    if context.clock.feature_cutoff - cutoff > timedelta(
                        days=self.max_stale_data_days
                    ):
                        blocked.append(symbol)
                        reasons.append(ReasonCode.STALE_DATA)
                dollar_volume = float(row.get("dollar_volume", 0.0))
                if dollar_volume < self.min_dollar_volume:
                    blocked.append(symbol)
                    reasons.append(ReasonCode.LOW_LIQUIDITY)
                if "max_weight_by_liquidity" in row and pd.notna(row["max_weight_by_liquidity"]):
                    cap = min(cap, max(0.0, float(row["max_weight_by_liquidity"])))

            if symbol in blocked:
                per_asset_caps[symbol] = 0.0
            else:
                per_asset_caps[symbol] = cap

        effective_max_gross = max(0.0, min(self.max_gross_exposure, 1.0 - self.cost_buffer_weight))
        return RiskConstraints(
            decision_time=context.clock.decision_time,
            max_gross_exposure=effective_max_gross,
            per_asset_caps=per_asset_caps,
            blocked_symbols=tuple(sorted(set(blocked))),
            volatility_target=self.volatility_target,
            turnover_cap=self.turnover_cap,
            reason_codes=_dedupe(reasons),
            metadata={"cost_buffer_weight": self.cost_buffer_weight},
        )
