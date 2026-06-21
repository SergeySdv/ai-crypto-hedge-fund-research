"""Level 2 typed agents backed by causal model prediction tables."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from crypto_hedge_fund.types import AgentContext, AgentSignal, ReasonCode


@dataclass(frozen=True)
class PredictionTableSignalAgent:
    """Emit precomputed causal model predictions as typed agent signals."""

    name: str
    predictions: pd.DataFrame
    horizon_open_days: int = 1

    def fit(self, frame: pd.DataFrame, *, fit_cutoff: pd.Timestamp) -> None:
        del frame, fit_cutoff

    def predict(self, frame: pd.DataFrame, context: AgentContext) -> list[AgentSignal]:
        del frame
        table = self._normalized_predictions()
        bar_start = pd.Timestamp(context.clock.bar_start)
        rows = table.loc[table["bar_start_utc"] == bar_start]
        signals: list[AgentSignal] = []
        for symbol in context.symbols:
            if rows.empty:
                signals.append(self._abstain(symbol, context, ReasonCode.WARMUP, "missing row"))
                continue
            row = rows.iloc[-1]
            status = str(row.get("status", "ok"))
            fit_cutoff = row.get("fit_cutoff", context.model_fit_cutoff)
            if pd.isna(fit_cutoff):
                fit_cutoff = context.model_fit_cutoff
            reason_codes = (ReasonCode.OK,)
            if status != "ok":
                reason_codes = (ReasonCode.ABSTAIN, ReasonCode.MODEL_FAILURE)
            signals.append(
                AgentSignal(
                    symbol=symbol,
                    agent=self.name,
                    score=float(row["score"]),
                    confidence=float(row["confidence"]),
                    horizon_open_days=self.horizon_open_days,
                    fit_cutoff=pd.Timestamp(fit_cutoff).to_pydatetime(),
                    feature_cutoff=pd.Timestamp(row["feature_cutoff"]).to_pydatetime(),
                    reason_codes=reason_codes,
                    metadata={
                        "model_status": status,
                        "probability": float(row.get("probability", 0.5)),
                        "expected_return": float(row.get("expected_return", 0.0)),
                        "forecast_volatility": float(row.get("forecast_volatility", 0.0)),
                        "method": str(row.get("method", self.name)),
                    },
                )
            )
        return signals

    def _normalized_predictions(self) -> pd.DataFrame:
        table = self.predictions.copy()
        for column in ("bar_start_utc", "execution_time", "feature_cutoff", "fit_cutoff"):
            if column in table.columns:
                table[column] = pd.to_datetime(table[column], utc=True)
        return table

    def _abstain(
        self,
        symbol: str,
        context: AgentContext,
        reason: ReasonCode,
        message: str,
    ) -> AgentSignal:
        return AgentSignal(
            symbol=symbol,
            agent=self.name,
            score=0.0,
            confidence=0.0,
            horizon_open_days=self.horizon_open_days,
            fit_cutoff=context.model_fit_cutoff,
            feature_cutoff=context.clock.feature_cutoff,
            reason_codes=(ReasonCode.ABSTAIN, reason),
            metadata={"error": message},
        )
