"""Educational AutoReg plus GARCH(1,1)-style forecasting helpers."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.ar_model import AutoReg


@dataclass(frozen=True)
class EconometricForecast:
    """One-step expected-return and conditional-volatility forecast."""

    expected_return: float
    volatility: float
    method: str
    status: str
    reason: str


def fit_econometric_forecast(
    returns: pd.Series,
    *,
    max_lags: int = 5,
) -> EconometricForecast:
    """Fit an AutoReg mean and GARCH-style volatility forecast on past returns only."""

    clean = pd.Series(returns, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < 80 or clean.std(ddof=0) <= 0:
        return EconometricForecast(0.0, 0.0, "insufficient_history", "abstain", "warmup")
    expected = _autoregressive_mean(clean, max_lags=max_lags)
    volatility, method = _garch_volatility(clean - clean.mean())
    if not math.isfinite(expected) or not math.isfinite(volatility) or volatility <= 0:
        return EconometricForecast(0.0, 0.0, method, "abstain", "model_failure")
    return EconometricForecast(float(expected), float(volatility), method, "ok", "ok")


def _autoregressive_mean(returns: pd.Series, *, max_lags: int) -> float:
    lags = min(max_lags, max(1, len(returns) // 40))
    try:
        model = AutoReg(returns.to_numpy(), lags=lags, old_names=False).fit()
        forecast = float(model.predict(start=len(returns), end=len(returns))[0])
    except Exception:
        forecast = float(returns.tail(20).mean())
    return forecast


def _garch_volatility(residuals: pd.Series) -> tuple[float, str]:
    """Forecast daily conditional volatility with arch when available, else EWMA GARCH."""

    clean = residuals.replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < 80:
        return 0.0, "insufficient_history"
    try:
        from arch import arch_model

        scaled = clean.to_numpy() * 100.0
        model = arch_model(scaled, mean="Zero", vol="GARCH", p=1, q=1, rescale=False)
        fit = model.fit(disp="off", show_warning=False)
        variance = float(fit.forecast(horizon=1).variance.iloc[-1, 0]) / 10_000.0
        if math.isfinite(variance) and variance > 0:
            return math.sqrt(variance), "arch_garch_1_1"
    except Exception:
        pass
    return _educational_garch_fallback(clean), "educational_garch_1_1_fallback"


def _educational_garch_fallback(residuals: pd.Series) -> float:
    """Deterministic GARCH(1,1)-style EWMA recursion without external solvers."""

    clean = residuals.to_numpy(dtype="float64")
    unconditional = float(np.var(clean, ddof=0))
    if not math.isfinite(unconditional) or unconditional <= 0:
        return 0.0
    alpha = 0.08
    beta = 0.90
    omega = max(1e-12, unconditional * (1.0 - alpha - beta))
    variance = unconditional
    for value in clean:
        variance = omega + alpha * float(value * value) + beta * variance
    return math.sqrt(max(variance, 1e-12))
