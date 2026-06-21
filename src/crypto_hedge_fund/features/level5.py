"""Vectorized large-universe Level 5 scoring features."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from crypto_hedge_fund.types import ReasonCode


@dataclass(frozen=True)
class Level5ScoringConfig:
    """Causal feature parameters for large-universe scoring."""

    scoring_lookback_days: int = 90
    momentum_short_days: int = 20
    momentum_long_days: int = 60
    volatility_days: int = 60
    drawdown_days: int = 90
    horizon_open_days: int = 7


def build_level5_score_frame(
    frame: pd.DataFrame,
    universe: pd.DataFrame,
    *,
    decision_bar: pd.Timestamp,
    feature_cutoff: pd.Timestamp,
    config: Level5ScoringConfig,
) -> pd.DataFrame:
    """Return one vectorized score row per point-in-time eligible symbol.

    The function only reads bars whose ``bar_end_utc`` is at or before
    ``feature_cutoff``. It emits explicit reason codes for symbols that are
    eligible at the universe layer but cannot be scored from completed bars.
    """

    normalized = _normalize_frame(frame, feature_cutoff=feature_cutoff)
    decision_bar = pd.Timestamp(decision_bar).tz_convert("UTC")
    symbols = tuple(str(symbol) for symbol in universe["symbol"].tolist())
    if not symbols:
        return _empty_scores()

    lookback = max(
        config.scoring_lookback_days,
        config.momentum_short_days,
        config.momentum_long_days,
        config.volatility_days,
        config.drawdown_days,
    )
    start = decision_bar - pd.Timedelta(days=lookback * 2)
    data = normalized.loc[
        (normalized["bar_start_utc"] >= start)
        & (normalized["bar_start_utc"] <= decision_bar)
        & (normalized["symbol"].isin(symbols))
    ].copy()
    if data.empty:
        return _invalid_score_rows(
            universe,
            decision_bar=decision_bar,
            feature_cutoff=feature_cutoff,
            horizon_open_days=config.horizon_open_days,
            reason=ReasonCode.STALE_DATA,
        )

    close = data.pivot(index="bar_start_utc", columns="symbol", values="close").sort_index()
    dollar_volume = data.pivot(
        index="bar_start_utc", columns="symbol", values="dollar_volume"
    ).sort_index()
    close = close.reindex(columns=list(symbols))
    dollar_volume = dollar_volume.reindex(columns=list(symbols))
    returns = close.pct_change()

    features = pd.DataFrame(index=pd.Index(symbols, name="symbol"))
    features["return_short"] = (
        close.iloc[-1] / close.shift(config.momentum_short_days).iloc[-1] - 1.0
    )
    features["return_long"] = close.iloc[-1] / close.shift(config.momentum_long_days).iloc[-1] - 1.0
    features["realized_volatility"] = returns.tail(config.volatility_days).std(ddof=0) * math.sqrt(
        365.0
    )
    rolling_max = close.tail(config.drawdown_days).max()
    features["drawdown"] = close.iloc[-1] / rolling_max - 1.0
    features["trailing_mean_dollar_volume"] = dollar_volume.tail(
        config.scoring_lookback_days
    ).mean()
    features["trailing_median_dollar_volume"] = universe.set_index("symbol")[
        "trailing_median_dollar_volume"
    ].reindex(symbols)
    features["valid_history_days"] = universe.set_index("symbol")["valid_history_days"].reindex(
        symbols
    )
    features["trailing_valid_days"] = universe.set_index("symbol")["trailing_valid_days"].reindex(
        symbols
    )

    momentum = 0.65 * features["return_short"] + 0.35 * features["return_long"]
    raw = (
        _zscore(momentum)
        - 0.35 * _zscore(features["realized_volatility"])
        + 0.15 * _zscore(np.log1p(features["trailing_median_dollar_volume"]))
        + 0.10 * _zscore(features["drawdown"])
    )
    features["raw_score"] = raw.replace([np.inf, -np.inf], np.nan)
    features["score"] = (features["raw_score"] / 3.0).clip(lower=-1.0, upper=1.0)
    liquidity_rank = features["trailing_median_dollar_volume"].rank(pct=True).fillna(0.0)
    history_confidence = (features["valid_history_days"] / 365.0).clip(lower=0.0, upper=1.0)
    features["confidence"] = (0.25 + 0.50 * history_confidence + 0.25 * liquidity_rank).clip(
        lower=0.0,
        upper=1.0,
    )

    output = features.reset_index()
    output["decision_bar_start"] = decision_bar
    output["feature_cutoff"] = pd.Timestamp(feature_cutoff).tz_convert("UTC")
    output["horizon_open_days"] = int(config.horizon_open_days)
    output["data_quality_flag"] = "ok"
    output["reason_codes"] = ReasonCode.OK.value
    invalid = (
        output[["return_short", "return_long", "realized_volatility", "score", "confidence"]]
        .replace([np.inf, -np.inf], np.nan)
        .isna()
        .any(axis=1)
    )
    output.loc[invalid, "score"] = 0.0
    output.loc[invalid, "confidence"] = 0.0
    output.loc[invalid, "data_quality_flag"] = "invalid_features"
    output.loc[invalid, "reason_codes"] = ReasonCode.INVALID_DATA.value
    output["scored"] = True
    return output.sort_values(["score", "confidence", "symbol"], ascending=[False, False, True])


def _normalize_frame(frame: pd.DataFrame, *, feature_cutoff: pd.Timestamp) -> pd.DataFrame:
    source = frame.copy()
    if isinstance(source.index, pd.MultiIndex) and "bar_start_utc" in source.index.names:
        source = source.reset_index()
    required = {
        "bar_start_utc",
        "bar_end_utc",
        "symbol",
        "close",
        "dollar_volume",
    }
    missing = sorted(required.difference(source.columns))
    if missing:
        msg = f"Level 5 scoring input is missing columns: {missing}"
        raise ValueError(msg)
    source["bar_start_utc"] = pd.to_datetime(source["bar_start_utc"], utc=True)
    source["bar_end_utc"] = pd.to_datetime(source["bar_end_utc"], utc=True)
    source["symbol"] = source["symbol"].astype(str)
    for column in ("close", "dollar_volume"):
        source[column] = pd.to_numeric(source[column], errors="coerce")
    source = source.loc[source["bar_end_utc"] <= pd.Timestamp(feature_cutoff).tz_convert("UTC")]
    return source.sort_values(["bar_start_utc", "symbol"], kind="mergesort")


def _zscore(series: pd.Series) -> pd.Series:
    clean = series.astype("float64").replace([np.inf, -np.inf], np.nan)
    std = clean.std(ddof=0)
    if not math.isfinite(float(std)) or float(std) <= 1e-12:
        return pd.Series(0.0, index=clean.index, dtype="float64")
    return (clean - clean.mean()) / std


def _empty_scores() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "symbol",
            "return_short",
            "return_long",
            "realized_volatility",
            "drawdown",
            "trailing_mean_dollar_volume",
            "trailing_median_dollar_volume",
            "valid_history_days",
            "trailing_valid_days",
            "raw_score",
            "score",
            "confidence",
            "decision_bar_start",
            "feature_cutoff",
            "horizon_open_days",
            "data_quality_flag",
            "reason_codes",
            "scored",
        ]
    )


def _invalid_score_rows(
    universe: pd.DataFrame,
    *,
    decision_bar: pd.Timestamp,
    feature_cutoff: pd.Timestamp,
    horizon_open_days: int,
    reason: ReasonCode,
) -> pd.DataFrame:
    output = universe[["symbol", "trailing_median_dollar_volume"]].copy()
    output["return_short"] = np.nan
    output["return_long"] = np.nan
    output["realized_volatility"] = np.nan
    output["drawdown"] = np.nan
    output["trailing_mean_dollar_volume"] = np.nan
    output["valid_history_days"] = universe["valid_history_days"].to_numpy()
    output["trailing_valid_days"] = universe["trailing_valid_days"].to_numpy()
    output["raw_score"] = np.nan
    output["score"] = 0.0
    output["confidence"] = 0.0
    output["decision_bar_start"] = decision_bar
    output["feature_cutoff"] = pd.Timestamp(feature_cutoff).tz_convert("UTC")
    output["horizon_open_days"] = int(horizon_open_days)
    output["data_quality_flag"] = reason.value
    output["reason_codes"] = reason.value
    output["scored"] = True
    return output
