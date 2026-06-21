"""SMA crossover signal agent for the Level 1 baseline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from crypto_hedge_fund.types import AgentContext, AgentSignal, ReasonCode


def _symbol_frame(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    source = frame.copy()
    if isinstance(source.index, pd.MultiIndex) and "symbol" in source.index.names:
        source = source.xs(symbol, level="symbol", drop_level=False)
    elif "symbol" in source.columns:
        source = source.loc[source["symbol"].astype(str) == symbol]
    return source.sort_index(kind="mergesort")


@dataclass
class SMACrossoverSignalAgent:
    """Emit a typed long/cash proposal from completed-bar SMA history."""

    fast_window: int
    slow_window: int
    name: str = "sma_crossover"
    horizon_open_days: int = 1
    fit_cutoff: datetime | None = None

    def __post_init__(self) -> None:
        if self.fast_window <= 0 or self.slow_window <= 0:
            msg = "SMA windows must be positive"
            raise ValueError(msg)
        if self.fast_window >= self.slow_window:
            msg = "fast_window must be smaller than slow_window"
            raise ValueError(msg)

    def fit(self, frame: pd.DataFrame, *, fit_cutoff: pd.Timestamp) -> None:
        """Record the fit cutoff; the SMA baseline has no learned parameters."""
        del frame
        self.fit_cutoff = fit_cutoff.to_pydatetime()

    def predict(self, frame: pd.DataFrame, context: AgentContext) -> list[AgentSignal]:
        """Return one signal per symbol using close data available at feature cutoff."""
        fit_cutoff = self.fit_cutoff or context.model_fit_cutoff
        signals: list[AgentSignal] = []
        for symbol in context.symbols:
            history = _symbol_frame(frame, symbol)
            if "close" not in history.columns or len(history) < self.slow_window:
                signals.append(self._abstain(symbol, fit_cutoff, context, ReasonCode.WARMUP))
                continue
            close = history["close"].astype("float64").tail(self.slow_window)
            if close.isna().any() or (close <= 0).any():
                signals.append(self._abstain(symbol, fit_cutoff, context, ReasonCode.INVALID_DATA))
                continue
            fast_sma = float(close.tail(self.fast_window).mean())
            slow_sma = float(close.mean())
            spread = fast_sma / slow_sma - 1.0
            long_signal = fast_sma > slow_sma
            score = 1.0 if long_signal else -1.0
            confidence = max(0.1, min(1.0, abs(spread) * 20.0))
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
                    metadata={
                        "fast_window": self.fast_window,
                        "slow_window": self.slow_window,
                        "fast_sma": fast_sma,
                        "slow_sma": slow_sma,
                        "spread": spread,
                        "state": "long" if long_signal else "cash",
                    },
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
            metadata={"fast_window": self.fast_window, "slow_window": self.slow_window},
        )
