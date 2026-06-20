"""Deterministic symbol exclusions and point-in-time universe eligibility."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC

import numpy as np
import pandas as pd

LEVERAGED_SUFFIXES: tuple[str, ...] = (
    "UP",
    "DOWN",
    "BULL",
    "BEAR",
    "3L",
    "3S",
    "4L",
    "4S",
    "5L",
    "5S",
    "2L",
    "2S",
    "HALF",
    "HEDGE",
)

FIAT_LIKE_BASES: frozenset[str] = frozenset(
    {
        "USD",
        "USDT",
        "USDC",
        "FDUSD",
        "TUSD",
        "DAI",
        "USDP",
        "BUSD",
        "USD1",
        "RLUSD",
        "BFUSD",
        "XUSD",
        "EUR",
        "GBP",
        "TRY",
        "BRL",
        "AUD",
        "JPY",
        "CAD",
        "CHF",
        "RUB",
        "UAH",
        "ZAR",
    }
)


@dataclass(frozen=True)
class UniverseRules:
    """Rules used by the Stage 2 full-mode Level 5 universe proof."""

    quote_currency: str
    stable_bases: tuple[str, ...]
    min_history_days: int
    preferred_history_days: int
    liquidity_lookback_days: int
    large_universe_size: int
    min_trailing_valid_days: int | None = None
    min_median_dollar_volume: float = 0.0

    @classmethod
    def from_config(cls, config: dict) -> UniverseRules:
        data = config["data"]
        min_trailing = max(1, int(data["liquidity_lookback_days"]) * 4 // 5)
        return cls(
            quote_currency=str(data["quote_currency"]),
            stable_bases=tuple(str(item) for item in data.get("stable_bases", ())),
            min_history_days=int(data["min_history_days"]),
            preferred_history_days=int(data["preferred_history_days"]),
            liquidity_lookback_days=int(data["liquidity_lookback_days"]),
            large_universe_size=int(data["large_universe_size"]),
            min_trailing_valid_days=min_trailing,
        )


def split_symbol(symbol: str) -> tuple[str, str]:
    """Split a CCXT-style symbol into base and quote components."""
    if "/" not in symbol:
        msg = f"Expected CCXT symbol with base/quote separator: {symbol}"
        raise ValueError(msg)
    base, quote = symbol.split("/", 1)
    return base, quote.split(":", 1)[0]


def deterministic_exclusion_reason(
    row: pd.Series,
    *,
    rules: UniverseRules,
) -> str | None:
    """Return an exclusion reason for static instrument filters, or ``None``."""
    symbol = str(row["symbol"])
    base = str(row.get("base") or split_symbol(symbol)[0]).upper()
    quote = str(row.get("quote") or split_symbol(symbol)[1]).upper()
    stable_bases = {item.upper() for item in rules.stable_bases} | FIAT_LIKE_BASES
    if quote != rules.quote_currency.upper():
        return "wrong_quote_currency"
    if str(row.get("market_type", "")).lower() != "spot":
        return "non_spot"
    if not bool(row.get("active", False)):
        return "inactive"
    if base in stable_bases:
        return "stable_or_fiat_base"
    if any(base.endswith(suffix) for suffix in LEVERAGED_SUFFIXES):
        return "leveraged_token_suffix"
    if any(token in base for token in ("BULL", "BEAR")):
        return "leveraged_token_name"
    return None


def exclusion_table(
    instruments: pd.DataFrame,
    *,
    rules: UniverseRules,
) -> pd.DataFrame:
    """Return one static exclusion row per instrument."""
    rows = []
    for _, row in instruments.iterrows():
        reason = deterministic_exclusion_reason(row, rules=rules)
        rows.append(
            {
                "symbol": row["symbol"],
                "base": row["base"],
                "quote": row["quote"],
                "excluded": reason is not None,
                "reason": reason or "eligible_static",
            }
        )
    return pd.DataFrame(rows)


def eligible_universe_at(
    market_data: pd.DataFrame,
    instruments: pd.DataFrame,
    *,
    decision_cutoff_utc: pd.Timestamp,
    rules: UniverseRules,
) -> pd.DataFrame:
    """Compute point-in-time eligible symbols using only data at or before cutoff."""
    cutoff = pd.Timestamp(decision_cutoff_utc)
    cutoff = cutoff.tz_localize(UTC) if cutoff.tzinfo is None else cutoff.tz_convert(UTC)
    usable = market_data.loc[market_data["bar_end_utc"] <= cutoff].copy()
    if usable.empty:
        return pd.DataFrame(
            columns=[
                "symbol",
                "eligible",
                "reason",
                "valid_history_days",
                "trailing_valid_days",
                "trailing_median_dollar_volume",
                "first_bar_start_utc",
                "last_bar_start_utc",
                "rank",
            ]
        )

    static = exclusion_table(instruments, rules=rules).set_index("symbol")
    trailing_start = cutoff - pd.Timedelta(days=rules.liquidity_lookback_days)
    history_rows = []
    seen_symbols: set[str] = set()
    for symbol, group in usable.groupby("symbol", sort=False):
        seen_symbols.add(str(symbol))
        instrument = static.loc[symbol] if symbol in static.index else None
        if instrument is None:
            static_reason = "missing_instrument_metadata"
        elif bool(instrument["excluded"]):
            static_reason = str(instrument["reason"])
        else:
            static_reason = None

        valid_group = group.dropna(subset=["open", "high", "low", "close", "volume"])
        trailing = valid_group.loc[valid_group["bar_start_utc"] >= trailing_start]
        valid_days = int(valid_group["bar_start_utc"].nunique())
        trailing_days = int(trailing["bar_start_utc"].nunique())
        median_dollar_volume = float(trailing["dollar_volume"].median())
        if not np.isfinite(median_dollar_volume):
            median_dollar_volume = 0.0

        reason = static_reason
        eligible = reason is None
        if eligible and valid_days < rules.min_history_days:
            eligible = False
            reason = "insufficient_history"
        if eligible and trailing_days < int(rules.min_trailing_valid_days or 1):
            eligible = False
            reason = "insufficient_trailing_liquidity_window"
        if eligible and median_dollar_volume <= rules.min_median_dollar_volume:
            eligible = False
            reason = "low_liquidity"

        history_rows.append(
            {
                "symbol": symbol,
                "eligible": eligible,
                "reason": reason or "eligible",
                "valid_history_days": valid_days,
                "trailing_valid_days": trailing_days,
                "trailing_median_dollar_volume": median_dollar_volume,
                "first_bar_start_utc": valid_group["bar_start_utc"].min(),
                "last_bar_start_utc": valid_group["bar_start_utc"].max(),
            }
        )
    for _, row in instruments.loc[~instruments["symbol"].isin(seen_symbols)].iterrows():
        reason = deterministic_exclusion_reason(row, rules=rules) or "no_completed_bars_by_cutoff"
        history_rows.append(
            {
                "symbol": row["symbol"],
                "eligible": False,
                "reason": reason,
                "valid_history_days": 0,
                "trailing_valid_days": 0,
                "trailing_median_dollar_volume": 0.0,
                "first_bar_start_utc": pd.NaT,
                "last_bar_start_utc": pd.NaT,
            }
        )

    result = pd.DataFrame(history_rows)
    result = result.sort_values(
        ["eligible", "trailing_median_dollar_volume", "symbol"],
        ascending=[False, False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    result["rank"] = np.nan
    eligible_mask = result["eligible"]
    result.loc[eligible_mask, "rank"] = np.arange(1, int(eligible_mask.sum()) + 1)
    return result


def selected_large_universe(eligibility: pd.DataFrame, *, rules: UniverseRules) -> pd.DataFrame:
    """Return the full-mode selected/scored universe ranked by trailing liquidity."""
    eligible = eligibility.loc[eligibility["eligible"]].copy()
    eligible = eligible.sort_values(
        ["trailing_median_dollar_volume", "symbol"],
        ascending=[False, True],
        kind="mergesort",
    )
    selected = eligible.head(rules.large_universe_size).reset_index(drop=True)
    selected["selected_for_scoring"] = True
    return selected
