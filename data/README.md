# Frozen Data Bundle

This Stage 2 bundle provides the default offline market data for later notebook and
final-test stages. It is educational research data, not a live trading feed.

## Source

- Exchange/source: Binance through CCXT.
- CCXT version: 4.5.59.
- Market: spot.
- Quote currency: USDT.
- Timeframe: daily (`1d`).
- Requested date range: 2021-01-01 through 2025-12-31 where available.
- Primary snapshot rule: one exchange/source only; no exchange mixing.

The included snapshot was built with:

```bash
make data
make validate-data
```

## Files

- `data/processed/ohlcv_daily.parquet`: long-form daily OHLCV panel.
- `data/processed/instruments.parquet`: symbol metadata and coverage statistics.
- `data/manifests/ohlcv_daily_manifest.json`: source, request parameters, per-symbol
  coverage, schema version and SHA-256 hashes.

Current hashes:

- OHLCV SHA-256: `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`
- Instruments SHA-256: `df7777139dd4106032280339818ba18179882c8e19141f374d87cb8e7bddf18b`

## OHLCV Schema

Required columns:

```text
bar_start_utc, bar_end_utc, symbol,
open, high, low, close, volume, dollar_volume,
exchange, market_type, timeframe
```

`bar_start_utc` is the exchange candle open in UTC. `bar_end_utc` is exactly one day
after `bar_start_utc`. Features may only use completed bars. Later execution stages must
use next-open execution rather than filling at the same close used to create a signal.

`dollar_volume` is `close * volume`; it is an approximation, not order-book depth.

## Coverage

- Actual minimum bar start: `2021-01-01T00:00:00+00:00`.
- Actual maximum bar start: `2025-12-31T00:00:00+00:00`.
- Rows: 158,511.
- Symbols with at least one row: 163.

Per-symbol first/last bars, row counts, expected row counts, missing row counts and
coverage ratios are stored in both `instruments.parquet` and the manifest.

## Universe Rules

Validation applies deterministic exclusions before the full-mode proof:

- quote must be USDT;
- market type must be spot;
- instrument must be active in CCXT metadata;
- stablecoin and fiat-like bases are excluded;
- leveraged-token suffix/name patterns are excluded;
- symbols need at least 365 valid prior bars;
- symbols need sufficient 90-day trailing liquidity-window coverage;
- ranked full-mode selection uses trailing 90-day median approximate dollar volume.

`make validate-data` writes:

- `artifacts/monitoring/universe_eligibility_full.csv`
- `artifacts/monitoring/level_5_pair_count_proof.json`

The current proof has at least 100 eligible/scored symbols at the in-period decision
cutoff recorded in `artifacts/monitoring/level_5_pair_count_proof.json`.

## Limitations

The downloader uses currently active Binance spot markets. That creates survivorship and
delisting bias because delisted or renamed markets are not reconstructed point-in-time.
The data also lacks order-book depth, bid/ask spreads and exchange outage information.
No OHLCV values are forward-filled or backward-filled.

The current frozen manifest records 180 requested symbols and 163 symbols with OHLCV
rows. It was produced before zero-row requested symbols were persisted as reason-coded
manifest exclusions, so the 17 omitted no-row candidates are a provenance limitation of
this snapshot. Future freezes write those omissions as `no_ohlcv_rows_returned`.
