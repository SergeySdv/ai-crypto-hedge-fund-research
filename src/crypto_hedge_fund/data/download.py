"""CCXT-backed public OHLCV download and freeze support."""

from __future__ import annotations

import json
import time
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import ccxt
import pandas as pd

from crypto_hedge_fund.config import load_config
from crypto_hedge_fund.data.schema import SCHEMA_VERSION, TIMEFRAME
from crypto_hedge_fund.data.storage import write_market_data
from crypto_hedge_fund.data.universe import UniverseRules, deterministic_exclusion_reason
from crypto_hedge_fund.provenance import file_sha256, git_commit

OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


class DownloadError(RuntimeError):
    """Raised when the public data freeze cannot be completed."""


def _exchange(exchange_id: str) -> ccxt.Exchange:
    try:
        exchange_class = getattr(ccxt, exchange_id)
    except AttributeError as exc:
        msg = f"Unsupported CCXT exchange: {exchange_id}"
        raise DownloadError(msg) from exc
    return exchange_class({"enableRateLimit": True, "timeout": 30000})


def load_spot_usdt_symbols(
    exchange: ccxt.Exchange,
    *,
    rules: UniverseRules,
    max_symbols: int,
) -> list[str]:
    """Load active spot USDT symbols and rank them by current quote volume when available."""
    markets = exchange.load_markets()
    candidates: list[tuple[str, float]] = []
    tickers: dict[str, Any] = {}
    try:
        tickers = exchange.fetch_tickers()
    except Exception:
        tickers = {}
    for symbol, market in markets.items():
        if not market.get("spot") or market.get("quote") != rules.quote_currency:
            continue
        row = {
            "symbol": symbol,
            "base": market.get("base"),
            "quote": market.get("quote"),
            "market_type": "spot",
            "active": bool(market.get("active", True)),
        }
        if deterministic_exclusion_reason(pd.Series(row), rules=rules):
            continue
        ticker = tickers.get(symbol, {}) if isinstance(tickers, dict) else {}
        quote_volume = ticker.get("quoteVolume") or ticker.get("baseVolume") or 0.0
        try:
            rank_value = float(quote_volume or 0.0)
        except (TypeError, ValueError):
            rank_value = 0.0
        candidates.append((symbol, rank_value))
    candidates.sort(key=lambda item: (-item[1], item[0]))
    return [symbol for symbol, _ in candidates[:max_symbols]]


def _fetch_symbol_ohlcv(
    exchange: ccxt.Exchange,
    symbol: str,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    timeframe: str = TIMEFRAME,
) -> pd.DataFrame:
    since = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    rows: list[list[Any]] = []
    limit = 1000
    while since < end_ms:
        batch = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
        if not batch:
            break
        rows.extend(batch)
        next_since = int(batch[-1][0]) + 24 * 60 * 60 * 1000
        if next_since <= since:
            break
        since = next_since
        time.sleep(float(getattr(exchange, "rateLimit", 0) or 0) / 1000.0)
        if int(batch[-1][0]) >= end_ms:
            break
    if not rows:
        return pd.DataFrame(columns=OHLCV_COLUMNS)
    frame = pd.DataFrame(rows, columns=OHLCV_COLUMNS)
    frame = frame.drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
    frame["bar_start_utc"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
    frame = frame.loc[(frame["bar_start_utc"] >= start) & (frame["bar_start_utc"] <= end)]
    frame["bar_end_utc"] = frame["bar_start_utc"] + pd.Timedelta(days=1)
    frame["symbol"] = symbol
    frame["dollar_volume"] = frame["close"] * frame["volume"]
    frame["exchange"] = exchange.id
    frame["market_type"] = "spot"
    frame["timeframe"] = timeframe
    return frame[
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
    ]


def _instrument_frame(
    exchange: ccxt.Exchange,
    market_data: pd.DataFrame,
    symbols: Sequence[str],
) -> pd.DataFrame:
    markets = exchange.markets or exchange.load_markets()
    rows = []
    grouped = market_data.groupby("symbol", sort=False)
    for symbol in symbols:
        if symbol not in grouped.groups:
            continue
        group = grouped.get_group(symbol)
        market = markets.get(symbol, {})
        first = group["bar_start_utc"].min()
        last = group["bar_start_utc"].max()
        expected = int(pd.date_range(first, last, freq="D", tz=UTC).size)
        bar_count = int(group["bar_start_utc"].nunique())
        precision = market.get("precision") or {}
        limits = market.get("limits") or {}
        amount_limits = limits.get("amount") or {}
        cost_limits = limits.get("cost") or {}
        rows.append(
            {
                "symbol": symbol,
                "base": market.get("base") or symbol.split("/", 1)[0],
                "quote": market.get("quote") or symbol.split("/", 1)[1],
                "exchange": exchange.id,
                "market_type": "spot",
                "active": bool(market.get("active", True)),
                "first_bar_start_utc": first,
                "last_bar_start_utc": last,
                "bar_count": bar_count,
                "expected_bar_count": expected,
                "missing_bar_count": expected - bar_count,
                "coverage_ratio": bar_count / expected if expected else 0.0,
                "min_amount": amount_limits.get("min"),
                "min_cost": cost_limits.get("min"),
                "precision_amount": precision.get("amount"),
                "precision_price": precision.get("price"),
            }
        )
    return pd.DataFrame(rows)


def _write_manifest(
    *,
    manifest_path: Path,
    config: dict,
    market_data_path: Path,
    instruments_path: Path,
    market_data: pd.DataFrame,
    instruments: pd.DataFrame,
    selected_symbols: Sequence[str],
    zero_row_symbols: Sequence[str],
    failures: Sequence[dict[str, str]],
) -> dict[str, Any]:
    coverage = (
        instruments[
            [
                "symbol",
                "first_bar_start_utc",
                "last_bar_start_utc",
                "bar_count",
                "expected_bar_count",
                "missing_bar_count",
                "coverage_ratio",
            ]
        ]
        .sort_values("symbol")
        .to_dict(orient="records")
    )
    for row in coverage:
        row["first_bar_start_utc"] = row["first_bar_start_utc"].isoformat()
        row["last_bar_start_utc"] = row["last_bar_start_utc"].isoformat()
    data_cfg = config["data"]
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "collection_timestamp_utc": datetime.now(UTC).isoformat(),
        "source": {
            "exchange": data_cfg["exchange"],
            "library": "ccxt",
            "library_version": ccxt.__version__,
            "market_type": data_cfg["market_type"],
            "quote_currency": data_cfg["quote_currency"],
            "timeframe": data_cfg["timeframe"],
        },
        "request": {
            "start": data_cfg["start"],
            "end": data_cfg["end"],
            "requested_symbol_count": len(selected_symbols),
            "symbols": list(selected_symbols),
            "selection": "active_spot_usdt_ranked_by_current_quote_volume",
        },
        "requested_symbol_exclusions": [
            {"symbol": symbol, "reason": "no_ohlcv_rows_returned"} for symbol in zero_row_symbols
        ],
        "download_failures": list(failures),
        "actual_min_bar_start_utc": market_data["bar_start_utc"].min().isoformat(),
        "actual_max_bar_start_utc": market_data["bar_start_utc"].max().isoformat(),
        "row_count": len(market_data),
        "symbol_count": int(market_data["symbol"].nunique()),
        "file_sha256": file_sha256(market_data_path),
        "instrument_sha256": file_sha256(instruments_path),
        "git_commit": git_commit(),
        "preprocessing": {
            "dollar_volume": "close * volume approximation",
            "bar_timestamp_semantics": "bar_start_utc is candle open; bar_end_utc is +1 day",
            "missing_ohlcv_fill": "none",
        },
        "per_symbol_coverage": coverage,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def freeze_data(
    *,
    config_path: str | Path | None = None,
    max_symbols: int | None = None,
) -> dict[str, Any]:
    """Download and freeze the configured public daily OHLCV snapshot."""
    config = load_config(config_path or "configs/default.yaml", resolve_paths=True)
    data_cfg = config["data"]
    exchange = _exchange(str(data_cfg["exchange"]))
    rules = UniverseRules.from_config(config)
    symbol_count = int(max_symbols or max(int(data_cfg["large_universe_size"]) + 50, 180))
    symbols = load_spot_usdt_symbols(exchange, rules=rules, max_symbols=symbol_count)
    if not symbols:
        msg = f"No candidate {rules.quote_currency} spot symbols found on {exchange.id}"
        raise DownloadError(msg)

    start = pd.Timestamp(data_cfg["start"], tz=UTC)
    end = pd.Timestamp(data_cfg["end"], tz=UTC)
    frames: list[pd.DataFrame] = []
    failures: list[dict[str, str]] = []
    zero_row_symbols: list[str] = []
    for index, symbol in enumerate(symbols, start=1):
        try:
            frame = _fetch_symbol_ohlcv(exchange, symbol, start=start, end=end)
        except Exception as exc:
            failures.append({"symbol": symbol, "error": repr(exc)})
            continue
        if not frame.empty:
            frames.append(frame)
        else:
            zero_row_symbols.append(symbol)
        print(f"[{index}/{len(symbols)}] {symbol}: {len(frame)} rows", flush=True)
    if not frames:
        msg = f"No OHLCV rows downloaded from {exchange.id}"
        raise DownloadError(msg)
    market_data = pd.concat(frames, ignore_index=True)
    instruments = _instrument_frame(exchange, market_data, list(market_data["symbol"].unique()))

    paths = config["paths"]
    market_data_path = Path(paths["market_data"])
    instruments_path = Path(paths["instruments"])
    manifest_path = Path(paths["manifest"])
    write_market_data(
        market_data,
        instruments,
        market_data_path=market_data_path,
        instruments_path=instruments_path,
    )
    written_data = pd.read_parquet(market_data_path)
    written_instruments = pd.read_parquet(instruments_path)
    manifest = _write_manifest(
        manifest_path=manifest_path,
        config=config,
        market_data_path=market_data_path,
        instruments_path=instruments_path,
        market_data=written_data,
        instruments=written_instruments,
        selected_symbols=symbols,
        zero_row_symbols=zero_row_symbols,
        failures=failures,
    )
    return manifest


def main(argv: Iterable[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Freeze public CCXT OHLCV data.")
    parser.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    parser.add_argument("--max-symbols", type=int, default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)
    manifest = freeze_data(config_path=args.config, max_symbols=args.max_symbols)
    print(json.dumps({k: manifest[k] for k in ("source", "row_count", "symbol_count")}, indent=2))
    return 0
