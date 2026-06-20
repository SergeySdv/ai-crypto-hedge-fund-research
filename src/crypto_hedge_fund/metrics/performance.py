"""Performance and risk metrics for shared backtest artifacts."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _zero_series(index: pd.Index) -> pd.Series:
    return pd.Series(0.0, index=index, dtype="float64")


def _max_drawdown(nav: pd.Series) -> tuple[float, int]:
    cumulative_max = nav.cummax()
    drawdown = nav / cumulative_max - 1.0
    max_dd = float(drawdown.min())
    underwater = drawdown < 0
    longest = 0
    current = 0
    for value in underwater:
        if bool(value):
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return max_dd, longest


def _annualized_return(total_return: float, periods: int, periods_per_year: int) -> float:
    if periods <= 1:
        return 0.0
    years = periods / periods_per_year
    if years <= 0 or total_return <= -1.0:
        return 0.0
    return (1.0 + total_return) ** (1.0 / years) - 1.0


def _historical_var_cvar(returns: pd.Series, confidence: float) -> tuple[float, float]:
    if returns.empty:
        return 0.0, 0.0
    alpha = 1.0 - confidence
    quantile = float(returns.quantile(alpha))
    tail = returns[returns <= quantile]
    var = max(0.0, -quantile)
    cvar = max(0.0, -float(tail.mean())) if not tail.empty else var
    return var, cvar


def _safe_symbol_key(symbol: object) -> str:
    return str(symbol).lower().replace("/", "_").replace("-", "_").replace(" ", "_")


def _weight_metrics(weights: pd.DataFrame | None, equity: pd.DataFrame) -> dict[str, float]:
    metrics: dict[str, float] = {
        "average_cash_exposure": 0.0,
        "average_concentration_hhi": 0.0,
        "average_effective_n": 0.0,
        "max_symbol_weight": 0.0,
    }
    if weights is None or weights.empty:
        if "cash" in equity.columns and "nav" in equity.columns:
            cash_weight = (equity["cash"].astype("float64") / equity["nav"].astype("float64")).clip(
                lower=0.0
            )
            metrics["average_cash_exposure"] = float(cash_weight.mean())
        elif "exposure" in equity.columns:
            metrics["average_cash_exposure"] = float(
                (1.0 - equity["exposure"].astype("float64")).clip(lower=0.0).mean()
            )
        return metrics

    frame = weights.copy()
    if "timestamp" in frame.columns:
        frame = frame.drop(columns=["timestamp"])
    if "run_label" in frame.columns:
        frame = frame.drop(columns=["run_label"])
    numeric = frame.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    cash_weight = (
        numeric["cash_weight"] if "cash_weight" in numeric.columns else _zero_series(numeric.index)
    )
    risky = numeric.drop(columns=["cash_weight"], errors="ignore")
    risky = risky.loc[
        :, [column for column in risky.columns if not str(column).startswith("provenance_")]
    ]
    hhi = (risky**2).sum(axis=1)
    effective_n = hhi.where(hhi <= 0.0, 1.0 / hhi).where(hhi > 0.0, 0.0)
    metrics.update(
        {
            "average_cash_exposure": float(cash_weight.mean()),
            "average_concentration_hhi": float(hhi.mean()) if not hhi.empty else 0.0,
            "average_effective_n": float(effective_n.mean()) if not effective_n.empty else 0.0,
            "max_symbol_weight": float(risky.max(axis=1).max()) if not risky.empty else 0.0,
        }
    )
    risky_sum = risky.sum(axis=1).replace(0.0, np.nan)
    contribution = risky.div(risky_sum, axis=0).fillna(0.0).mean(axis=0)
    for symbol, value in contribution.items():
        metrics[f"average_risky_weight_contribution_{_safe_symbol_key(symbol)}"] = float(value)
    return metrics


def calculate_performance_metrics(
    equity: pd.DataFrame,
    *,
    periods_per_year: int = 365,
    risk_free_rate: float = 0.0,
    weights: pd.DataFrame | None = None,
    benchmark_nav: pd.Series | None = None,
) -> dict[str, float]:
    """Calculate shared return, risk, cost, concentration and benchmark metrics."""
    if "nav" not in equity.columns:
        msg = "equity must contain a 'nav' column"
        raise ValueError(msg)
    nav = equity["nav"].astype("float64")
    if nav.empty or not nav.map(math.isfinite).all() or (nav <= 0).any():
        msg = "equity nav must be finite, positive and non-empty"
        raise ValueError(msg)
    returns = nav.pct_change().dropna()
    total_return = float(nav.iloc[-1] / nav.iloc[0] - 1.0)
    cagr = _annualized_return(total_return, len(nav), periods_per_year)
    volatility = float(returns.std(ddof=1) * np.sqrt(periods_per_year)) if len(returns) > 1 else 0.0
    rf_per_period = risk_free_rate / periods_per_year
    excess = returns - rf_per_period
    sharpe = (
        float(excess.mean() / returns.std(ddof=1) * np.sqrt(periods_per_year))
        if len(returns) > 1 and returns.std(ddof=1) > 0
        else 0.0
    )
    downside = returns[returns < rf_per_period] - rf_per_period
    downside_dev = (
        float(np.sqrt((downside**2).mean()) * np.sqrt(periods_per_year))
        if not downside.empty
        else 0.0
    )
    sortino = (
        float((returns.mean() - rf_per_period) * periods_per_year / downside_dev)
        if downside_dev > 0
        else 0.0
    )
    max_dd, drawdown_duration = _max_drawdown(nav)
    calmar = float(cagr / abs(max_dd)) if max_dd < 0 else 0.0
    var_95, cvar_95 = _historical_var_cvar(returns, 0.95)

    metrics = {
        "total_return": total_return,
        "roi": total_return,
        "cagr": cagr,
        "volatility": volatility,
        "sharpe": sharpe,
        "sortino": sortino,
        "downside_deviation": downside_dev,
        "calmar": calmar,
        "max_drawdown": max_dd,
        "drawdown_duration": float(drawdown_duration),
        "var_95": var_95,
        "cvar_95": cvar_95,
        "turnover": float(equity.get("turnover", _zero_series(equity.index)).sum()),
        "average_exposure": float(equity.get("exposure", _zero_series(equity.index)).mean()),
        "trade_count": float(equity.get("trade_count", _zero_series(equity.index)).sum()),
        "fees": float(equity.get("fees", _zero_series(equity.index)).sum()),
        "slippage": float(equity.get("slippage", _zero_series(equity.index)).sum()),
        "total_cost": float(equity.get("total_cost", _zero_series(equity.index)).sum()),
    }
    metrics.update(_weight_metrics(weights, equity))
    if benchmark_nav is not None:
        benchmark = benchmark_nav.astype("float64")
        if len(benchmark) == len(nav):
            benchmark = pd.Series(benchmark.to_numpy(), index=nav.index, dtype="float64")
        else:
            benchmark = benchmark.reindex(nav.index).ffill()
        if benchmark.isna().any() or (benchmark <= 0).any():
            msg = "benchmark_nav must align to equity and contain finite positive values"
            raise ValueError(msg)
        benchmark_returns = benchmark.pct_change().dropna()
        benchmark_total_return = float(benchmark.iloc[-1] / benchmark.iloc[0] - 1.0)
        benchmark_volatility = (
            float(benchmark_returns.std(ddof=1) * np.sqrt(periods_per_year))
            if len(benchmark_returns) > 1
            else 0.0
        )
        active_returns = returns - benchmark_returns.reindex(returns.index).fillna(0.0)
        tracking_error = (
            float(active_returns.std(ddof=1) * np.sqrt(periods_per_year))
            if len(active_returns) > 1
            else 0.0
        )
        metrics["benchmark_total_return"] = float(benchmark.iloc[-1] / benchmark.iloc[0] - 1.0)
        metrics["benchmark_cagr"] = _annualized_return(
            benchmark_total_return, len(benchmark), periods_per_year
        )
        metrics["benchmark_volatility"] = benchmark_volatility
        metrics["excess_total_return"] = total_return - benchmark_total_return
        metrics["tracking_error"] = tracking_error
        metrics["information_ratio"] = (
            float(active_returns.mean() / active_returns.std(ddof=1) * np.sqrt(periods_per_year))
            if len(active_returns) > 1 and active_returns.std(ddof=1) > 0
            else 0.0
        )
    return metrics
