"""Level 2 one-pair causal features and next-open targets."""

from __future__ import annotations

import numpy as np
import pandas as pd

LEVEL2_FEATURE_COLUMNS = (
    "open_return_1d",
    "close_return_1d",
    "return_5d",
    "return_10d",
    "return_20d",
    "sma_ratio_10_50",
    "ema_ratio_12_26",
    "rsi_14",
    "macd",
    "macd_signal",
    "atr_14_norm",
    "realized_vol_7",
    "realized_vol_20",
    "realized_vol_60",
    "range_norm",
    "close_open_return",
    "gap_return",
    "drawdown_60",
    "volume_z_20",
    "dollar_volume_z_20",
)


def build_level2_feature_frame(
    frame: pd.DataFrame,
    *,
    symbol: str,
    horizon_open_days: int = 1,
    threshold_return: float = 0.0,
) -> pd.DataFrame:
    """Return one causal row per completed bar with aligned open-to-open target.

    Features use data available at ``bar_start_utc`` after that daily bar has
    completed. The label starts at the next open and ends after the requested
    open-day horizon. ``label_observation_time`` records when that target return
    is knowable and is used by the walk-forward model code to prevent leakage.
    """

    if horizon_open_days != 1:
        msg = "Level 2 currently supports the required one open-day horizon"
        raise ValueError(msg)
    data = _normalize(frame, symbol=symbol)
    close = data["close"].astype("float64")
    open_ = data["open"].astype("float64")
    high = data["high"].astype("float64")
    low = data["low"].astype("float64")
    volume = data["volume"].astype("float64")
    dollar_volume = data["dollar_volume"].astype("float64")

    out = data[
        [
            "bar_start_utc",
            "bar_end_utc",
            "symbol",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "dollar_volume",
            "exchange",
            "market_type",
            "timeframe",
        ]
    ].copy()
    open_returns = open_.pct_change()
    close_returns = close.pct_change()
    out["open_return_1d"] = open_returns
    out["close_return_1d"] = close_returns
    out["return_5d"] = close.pct_change(5)
    out["return_10d"] = close.pct_change(10)
    out["return_20d"] = close.pct_change(20)
    out["sma_ratio_10_50"] = (
        close.rolling(10, min_periods=10).mean() / close.rolling(50, min_periods=50).mean() - 1.0
    )
    out["ema_ratio_12_26"] = (
        close.ewm(span=12, adjust=False, min_periods=12).mean()
        / close.ewm(span=26, adjust=False, min_periods=26).mean()
        - 1.0
    )
    rsi = _rsi(close, window=14)
    out["rsi_14"] = rsi / 100.0
    macd = (
        close.ewm(span=12, adjust=False, min_periods=12).mean()
        - close.ewm(span=26, adjust=False, min_periods=26).mean()
    )
    macd_signal = macd.ewm(span=9, adjust=False, min_periods=9).mean()
    out["macd"] = macd / close
    out["macd_signal"] = macd_signal / close
    out["atr_14_norm"] = _atr(high, low, close, window=14) / close
    out["realized_vol_7"] = close_returns.rolling(7, min_periods=7).std(ddof=0) * np.sqrt(365.0)
    out["realized_vol_20"] = close_returns.rolling(20, min_periods=20).std(ddof=0) * np.sqrt(365.0)
    out["realized_vol_60"] = close_returns.rolling(60, min_periods=60).std(ddof=0) * np.sqrt(365.0)
    out["range_norm"] = (high - low) / close
    out["close_open_return"] = close / open_ - 1.0
    out["gap_return"] = open_ / close.shift(1) - 1.0
    out["drawdown_60"] = close / close.rolling(60, min_periods=60).max() - 1.0
    out["volume_z_20"] = _rolling_zscore(volume, window=20)
    out["dollar_volume_z_20"] = _rolling_zscore(dollar_volume, window=20)

    execution_open = open_.shift(-1)
    future_open = open_.shift(-2)
    out["execution_time"] = out["bar_start_utc"] + pd.Timedelta(days=1)
    out["future_open_time"] = out["bar_start_utc"] + pd.Timedelta(days=2)
    out["feature_cutoff"] = out["bar_end_utc"]
    out["forward_return"] = future_open / execution_open - 1.0
    out["target_label"] = (out["forward_return"] > threshold_return).astype("int64")
    out["target_threshold_return"] = float(threshold_return)
    out["label_observation_time"] = out["future_open_time"]
    out["feature_set"] = "level2_daily_causal_v1"
    out = out.replace([np.inf, -np.inf], np.nan)
    return out.dropna(subset=[*LEVEL2_FEATURE_COLUMNS, "forward_return"]).reset_index(drop=True)


def _normalize(frame: pd.DataFrame, *, symbol: str) -> pd.DataFrame:
    source = frame.copy()
    if isinstance(source.index, pd.MultiIndex) and "bar_start_utc" in source.index.names:
        source = source.reset_index()
    if "bar_start_utc" not in source.columns or "symbol" not in source.columns:
        msg = "Level 2 feature input requires bar_start_utc and symbol columns"
        raise ValueError(msg)
    source["bar_start_utc"] = pd.to_datetime(source["bar_start_utc"], utc=True)
    source["bar_end_utc"] = (
        pd.to_datetime(source["bar_end_utc"], utc=True)
        if "bar_end_utc" in source.columns
        else source["bar_start_utc"] + pd.Timedelta(days=1)
    )
    source["symbol"] = source["symbol"].astype(str)
    source = source.loc[source["symbol"] == symbol].sort_values("bar_start_utc", kind="mergesort")
    if source["bar_start_utc"].duplicated().any():
        msg = f"duplicate bars for {symbol}"
        raise ValueError(msg)
    required = ("open", "high", "low", "close", "volume", "dollar_volume")
    missing = [column for column in required if column not in source.columns]
    if missing:
        msg = f"Level 2 feature input is missing columns: {missing}"
        raise ValueError(msg)
    for column in required:
        source[column] = pd.to_numeric(source[column], errors="coerce")
    if not ((source[["open", "high", "low", "close"]] > 0).all().all()):
        msg = "Level 2 feature input prices must be positive"
        raise ValueError(msg)
    for optional in ("exchange", "market_type", "timeframe"):
        if optional not in source.columns:
            source[optional] = ""
    return source.reset_index(drop=True)


def _rsi(close: pd.Series, *, window: int) -> pd.Series:
    delta = close.diff()
    gains = delta.clip(lower=0.0).rolling(window, min_periods=window).mean()
    losses = (-delta.clip(upper=0.0)).rolling(window, min_periods=window).mean()
    rs = gains / losses.replace(0.0, np.nan)
    return 100.0 - 100.0 / (1.0 + rs)


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, *, window: int) -> pd.Series:
    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(window, min_periods=window).mean()


def _rolling_zscore(series: pd.Series, *, window: int) -> pd.Series:
    mean = series.rolling(window, min_periods=window).mean()
    std = series.rolling(window, min_periods=window).std(ddof=0)
    return (series - mean) / std.replace(0.0, np.nan)
