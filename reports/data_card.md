# Data Card

## Dataset

Frozen Binance spot USDT daily OHLCV panel for the educational AI Crypto Hedge Fund
research system.

## Collection

- Adapter: CCXT public REST API.
- Exchange: Binance.
- Market type: spot.
- Quote currency: USDT.
- Timeframe: daily.
- Requested period: 2021-01-01 through 2025-12-31 where available.
- Collection command: `make data`.
- Validation command: `make validate-data`.

## Included Files

- `data/processed/ohlcv_daily.parquet`
- `data/processed/instruments.parquet`
- `data/manifests/ohlcv_daily_manifest.json`

Manifest hashes:

- OHLCV: `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`
- Instruments: `df7777139dd4106032280339818ba18179882c8e19141f374d87cb8e7bddf18b`

## Coverage

- Rows: 158,511.
- Symbols with rows: 163.
- Minimum bar start: `2021-01-01T00:00:00+00:00`.
- Maximum bar start: `2025-12-31T00:00:00+00:00`.
- Full-mode proof: at least 100 eligible/scored symbols at the in-period decision
  cutoff recorded in `artifacts/monitoring/level_5_pair_count_proof.json`.

## Transformations

- Raw CCXT OHLCV candles are normalized into long-form Parquet.
- `bar_end_utc = bar_start_utc + 1 day`.
- `dollar_volume = close * volume` and is labeled as an approximation.
- Rows are sorted by `(bar_start_utc, symbol)`.
- No forward-fill, backward-fill or synthetic OHLCV generation is applied.

## Validation

The validation gate checks:

- required schemas;
- UTC-aware timestamps;
- unique `(bar_start_utc, symbol)` keys;
- sorted rows;
- finite numeric values;
- OHLC sanity;
- positive prices and nonnegative volume;
- manifest/data hash agreement;
- source/config agreement;
- full-mode 100+ eligible/scored pair proof.

## Intended Use

This bundle supports offline historical research, validation-only strategy development,
and later final-test execution after a pretest lock exists.

## Leakage Safeguards

The data layer only validates schema, coverage and point-in-time eligibility using bars
available at or before the proof cutoff. It does not compute strategy returns, tune
parameters, select models or inspect final-test performance.

## Limitations

The symbol universe is selected from currently active Binance spot markets and therefore
has survivorship/delisting bias. Historical delisted markets, order-book depth, bid/ask
spreads, exchange maintenance incidents and real execution constraints are not included.
USDT is treated as the quote/cash proxy in later stages.

The frozen manifest records 180 requested symbols and 163 symbols with OHLCV rows, but
this snapshot predates reason-coded persistence for the 17 requested symbols that
returned no rows. The downloader now writes those future omissions as
`no_ohlcv_rows_returned`; this snapshot remains documented rather than silently altered.
