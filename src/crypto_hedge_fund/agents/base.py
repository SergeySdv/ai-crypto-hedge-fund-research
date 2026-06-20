"""Concrete signal agents that emit typed proposals only."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from crypto_hedge_fund.types import AgentContext, AgentSignal, ReasonCode


def _frame_for_symbol(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if "symbol" in frame.columns:
        subset = frame.loc[frame["symbol"].astype(str) == symbol]
    elif isinstance(frame.index, pd.MultiIndex) and "symbol" in frame.index.names:
        subset = frame.xs(symbol, level="symbol", drop_level=False)
    else:
        subset = frame
    return subset.sort_index(kind="mergesort")


@dataclass
class FixedSignalAgent:
    """Small deterministic agent useful for validation and fixtures."""

    name: str
    scores: dict[str, float]
    confidence: float = 1.0
    horizon_open_days: int = 1
    reason_codes: tuple[ReasonCode, ...] = (ReasonCode.OK,)
    fit_cutoff: datetime | None = None

    def fit(self, frame: pd.DataFrame, *, fit_cutoff: pd.Timestamp) -> None:
        del frame
        self.fit_cutoff = fit_cutoff.to_pydatetime()

    def predict(self, frame: pd.DataFrame, context: AgentContext) -> list[AgentSignal]:
        del frame
        fit_cutoff = self.fit_cutoff or context.model_fit_cutoff
        return [
            AgentSignal(
                symbol=symbol,
                agent=self.name,
                score=self.scores.get(symbol, 0.0),
                confidence=self.confidence,
                horizon_open_days=self.horizon_open_days,
                fit_cutoff=fit_cutoff,
                feature_cutoff=context.clock.feature_cutoff,
                reason_codes=self.reason_codes,
            )
            for symbol in context.symbols
        ]


@dataclass
class MomentumSignalAgent:
    """Trend agent using only completed-bar close history."""

    name: str = "momentum"
    lookback: int = 3
    horizon_open_days: int = 1
    fit_cutoff: datetime | None = None

    def fit(self, frame: pd.DataFrame, *, fit_cutoff: pd.Timestamp) -> None:
        del frame
        self.fit_cutoff = fit_cutoff.to_pydatetime()

    def predict(self, frame: pd.DataFrame, context: AgentContext) -> list[AgentSignal]:
        signals: list[AgentSignal] = []
        fit_cutoff = self.fit_cutoff or context.model_fit_cutoff
        for symbol in context.symbols:
            subset = _frame_for_symbol(frame, symbol)
            if "close" not in subset or len(subset) <= self.lookback:
                signals.append(self._abstain(symbol, fit_cutoff, context, ReasonCode.WARMUP))
                continue
            close = subset["close"].astype("float64").tail(self.lookback + 1)
            if close.isna().any() or (close <= 0).any():
                signals.append(self._abstain(symbol, fit_cutoff, context, ReasonCode.INVALID_DATA))
                continue
            raw_return = float(close.iloc[-1] / close.iloc[0] - 1.0)
            score = max(-1.0, min(1.0, raw_return * 10.0))
            confidence = max(0.05, min(1.0, abs(score)))
            signals.append(
                AgentSignal(
                    symbol=symbol,
                    agent=self.name,
                    score=score,
                    confidence=confidence,
                    horizon_open_days=self.horizon_open_days,
                    fit_cutoff=fit_cutoff,
                    feature_cutoff=context.clock.feature_cutoff,
                    reason_codes=(ReasonCode.OK,),
                    metadata={"lookback": self.lookback, "raw_return": raw_return},
                )
            )
        return signals

    def _abstain(
        self,
        symbol: str,
        fit_cutoff: datetime,
        context: AgentContext,
        reason: ReasonCode,
    ) -> AgentSignal:
        return AgentSignal(
            symbol=symbol,
            agent=self.name,
            score=0.0,
            confidence=0.0,
            horizon_open_days=self.horizon_open_days,
            fit_cutoff=fit_cutoff,
            feature_cutoff=context.clock.feature_cutoff,
            reason_codes=(ReasonCode.ABSTAIN, reason),
        )


@dataclass
class VolatilityRegimeAgent:
    """Risk-state agent that reduces score/confidence in high realized volatility."""

    name: str = "regime"
    volatility_column: str = "realized_vol"
    high_volatility_threshold: float = 0.8
    horizon_open_days: int = 1
    fit_cutoff: datetime | None = None

    def fit(self, frame: pd.DataFrame, *, fit_cutoff: pd.Timestamp) -> None:
        del frame
        self.fit_cutoff = fit_cutoff.to_pydatetime()

    def predict(self, frame: pd.DataFrame, context: AgentContext) -> list[AgentSignal]:
        signals: list[AgentSignal] = []
        fit_cutoff = self.fit_cutoff or context.model_fit_cutoff
        for symbol in context.symbols:
            subset = _frame_for_symbol(frame, symbol)
            if self.volatility_column not in subset or subset.empty:
                signals.append(self._abstain(symbol, fit_cutoff, context, ReasonCode.WARMUP))
                continue
            value = float(subset[self.volatility_column].iloc[-1])
            if not math.isfinite(value) or value < 0:
                signals.append(self._abstain(symbol, fit_cutoff, context, ReasonCode.INVALID_DATA))
                continue
            if value >= self.high_volatility_threshold:
                score = -1.0
                confidence = 1.0
                reasons = (ReasonCode.OK, ReasonCode.VOLATILITY_LIMIT)
            else:
                score = 0.25
                confidence = max(0.1, 1.0 - value / self.high_volatility_threshold)
                reasons = (ReasonCode.OK,)
            signals.append(
                AgentSignal(
                    symbol=symbol,
                    agent=self.name,
                    score=score,
                    confidence=confidence,
                    horizon_open_days=self.horizon_open_days,
                    fit_cutoff=fit_cutoff,
                    feature_cutoff=context.clock.feature_cutoff,
                    reason_codes=reasons,
                    metadata={self.volatility_column: value},
                )
            )
        return signals

    def _abstain(
        self,
        symbol: str,
        fit_cutoff: datetime,
        context: AgentContext,
        reason: ReasonCode,
    ) -> AgentSignal:
        return AgentSignal(
            symbol=symbol,
            agent=self.name,
            score=0.0,
            confidence=0.0,
            horizon_open_days=self.horizon_open_days,
            fit_cutoff=fit_cutoff,
            feature_cutoff=context.clock.feature_cutoff,
            reason_codes=(ReasonCode.ABSTAIN, reason),
        )
