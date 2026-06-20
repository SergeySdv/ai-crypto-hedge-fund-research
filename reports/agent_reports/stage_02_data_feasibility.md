# Stage 02 Data Feasibility Report

## Review Scope

Reviewed `AGENTS.md` plus the data, Level 5, final-test, artifact, architecture, config and stage-gate docs. Current repository state is still a planning handoff: directories exist, but no `pyproject.toml`, `uv.lock`, source package, data files, manifests, notebook, presentation, or generated artifacts are present yet.

## Frozen Data Requirements

The default run must use included, offline, real historical spot data:

- `data/processed/ohlcv_daily.parquet`
- `data/processed/instruments.parquet`
- `data/manifests/ohlcv_daily_manifest.json`

Required market data contract:

- one primary spot exchange snapshot, not silently mixed sources;
- USDT quote, daily timeframe, UTC bar boundaries;
- requested coverage: `2021-01-01` through `2025-12-31` where available;
- long-form key: `(bar_start_utc, symbol)`;
- required columns: `bar_start_utc`, `bar_end_utc`, `symbol`, `open`, `high`, `low`, `close`, `volume`, `dollar_volume`, `exchange`, `market_type`, `timeframe`;
- `dollar_volume = close * volume` is acceptable only if labeled as an approximation.

Required instrument metadata:

- `symbol`, `exchange_symbol`, `base`, `quote`, `market_type`;
- `first_bar_utc`, `last_bar_utc`;
- `status_at_download`;
- precision and minimum-notional fields where available.

The manifest must record collection timestamp, source exchange, CCXT/library version, request parameters, schema version, actual min/max dates, row/symbol counts, coverage summaries, OHLCV file hash, instrument metadata hash, and preprocessing/git version.

The data layer must enforce next-open timing: completed daily bars generate features only after `bar_end_utc`, decisions occur after that cutoff, and execution occurs at the next available open.

## CCXT / Source Decision Risks

Primary risk: downloading only currently active CCXT markets creates survivorship and listing bias. The docs allow this only with explicit disclosure; it cannot be described as a true institutional point-in-time universe unless delisted-symbol history is available.

Key source risks to resolve before strategy work:

- A single exchange may not provide 100+ USDT spot pairs with enough valid history for Level 5.
- Some symbols may have insufficient 2021-2025 coverage or late listings, reducing eligible counts after 365/730-day history filters.
- CCXT market status at download time is not historical status; this affects point-in-time tradability claims.
- Exchange symbol renames, delistings, migrations and redenominations need deterministic handling or exclusion.
- Stablecoins, fiat-like bases, leveraged tokens, non-spot markets and impossible OHLC data must be filtered mechanically.
- Rate limits, pagination gaps and partial candles must be handled explicitly.
- Raw exchange payloads may be omitted, but processed snapshot provenance and hashes must be complete.
- If the preferred source cannot prove 100+ eligible pairs, the source must be changed before continuing; documenting shortage is not an acceptable completion path.

Recommendation: treat CCXT as the downloader/freeze mechanism only. The submitted system must run from the frozen Parquet and manifest without network access.

## 100+ Pair Proof Design

Stage 2 must produce a hard proof before any strategy implementation proceeds.

Required proof artifacts:

- `artifacts/monitoring/universe_eligibility_full.csv`
- `artifacts/monitoring/level_5_pair_count_proof.json`

Proof logic should run inside `make validate-data` in full mode and must use the same eligibility code intended for Level 5.

Minimum proof contents:

- mode: `full`;
- decision/rebalance date used for the proof;
- data/config/git hashes;
- manifest hash and input file hashes;
- exchange, quote, timeframe and date coverage;
- eligibility rules and configured thresholds;
- eligible count and scored count;
- selected/scored symbols;
- exclusions with reason codes;
- per-symbol first/last bar, valid-bar count, missingness, stale status;
- trailing 90-day median dollar volume used for ranking;
- whether each selected symbol has at least 365 prior valid bars, with preferred 730-day flag;
- runtime and memory or comparable scalability evidence.

Acceptance threshold:

- at least one full-mode rebalance date must have `eligible_count >= 100` and `scored_count >= 100`;
- fast mode may be smaller, but cannot be used as final evidence;
- the full notebook and final artifacts must later display the same proof.

## Validation Artifacts

`make validate-data` should create or verify:

- manifest hash match for OHLCV and instruments;
- UTC-aware timestamps and valid `bar_start_utc < bar_end_utc`;
- unique `(bar_start_utc, symbol)` keys;
- sorted rows;
- finite numeric values;
- positive prices and non-negative volume;
- OHLC invariant: `low <= min(open, close) <= max(open, close) <= high`;
- no duplicate bars;
- coverage, missingness, first/last bar reports;
- deterministic exclusion report for stable, leveraged, invalid, stale, low-liquidity and non-spot symbols;
- proof that no forward/backward fill creates features or returns;
- proof that missing execution prices block trading;
- stale valuation policy report;
- Level 5 100+ eligibility proof.

Required documentation outputs:

- `data/README.md`
- `reports/data_card.md`

Both must document source terms caveats, survivorship/delisting limitations, symbol-change handling, USDT-as-cash limitation, missing-bar behavior, and offline reproducibility.

## Blockers Before Strategy Work

Blocking items:

- No frozen data files exist yet.
- No manifest exists yet.
- No data validation command exists yet.
- No `pyproject.toml`, `uv.lock`, Makefile, package, or tests exist yet.
- No Level 5 100+ pair proof artifacts exist.
- No source decision has been proven feasible.
- No stale/missing data policy has been implemented in code.
- No artifact metadata writer or hash validation exists yet.

Stage 2 should not be considered closed until `make validate-data` passes offline and proves a full-mode date with at least 100 eligible and scored pairs. Strategy work should not start before this gate, because source infeasibility would force a methodology/data-source change that could invalidate later implementation.
