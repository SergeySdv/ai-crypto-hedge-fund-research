# Stage 02 Frozen Data - Specialist Review

## Metadata

- Stage: 2 - Frozen data layer
- Attempt: 01
- Source report: `reports/agent_reports/stage_02_data_feasibility.md`
- Review type: pre-implementation data feasibility review
- Team-lead status: reference input for Stage 2 review
- Final-test exposure state: NOT_EXPOSED

## Review Scope

The specialist reviewed `AGENTS.md` and the data, Level 5, final-test, artifact, architecture, config and stage-gate docs. At the time of this feasibility review, the repository was still a planning handoff without `pyproject.toml`, `uv.lock`, source package, data files, manifests, notebook, presentation or generated artifacts.

This report is preserved as pre-implementation guidance. It is not an independent QA pass on the returned Stage 2 implementation.

## Frozen Data Requirements Identified

The default run must use included, offline, real historical spot data:

- `data/processed/ohlcv_daily.parquet`
- `data/processed/instruments.parquet`
- `data/manifests/ohlcv_daily_manifest.json`

Required market data contract:

- one primary spot exchange snapshot, not silently mixed sources;
- USDT quote, daily timeframe, UTC bar boundaries;
- requested coverage: 2021-01-01 through 2025-12-31 where available;
- long-form key: `(bar_start_utc, symbol)`;
- required columns: `bar_start_utc`, `bar_end_utc`, `symbol`, `open`, `high`, `low`, `close`, `volume`, `dollar_volume`, `exchange`, `market_type`, `timeframe`;
- `dollar_volume = close * volume` is acceptable only if labeled as an approximation.

Required instrument metadata:

- `symbol`, `exchange_symbol`, `base`, `quote`, `market_type`;
- `first_bar_utc`, `last_bar_utc`;
- `status_at_download`;
- precision and minimum-notional fields where available.

The manifest must record collection timestamp, source exchange, CCXT/library version, request parameters, schema version, actual min/max dates, row/symbol counts, coverage summaries, OHLCV file hash, instrument metadata hash and preprocessing/git version.

The data layer must preserve next-open timing: completed daily bars generate features only after `bar_end_utc`, decisions occur after that cutoff, and execution occurs at the next available open.

## Source Decision Risks

- Downloading only currently active CCXT markets creates survivorship and listing bias.
- A single exchange may not provide 100+ USDT spot pairs with enough valid history.
- Some symbols may have insufficient 2021-2025 coverage or late listings.
- CCXT market status at download time is not historical status.
- Symbol renames, delistings, migrations and redenominations require deterministic handling or exclusion.
- Stablecoins, fiat-like bases, leveraged tokens, non-spot markets and impossible OHLC data must be filtered mechanically.
- Rate limits, pagination gaps and partial candles must be handled explicitly.
- Processed snapshot provenance and hashes must be complete if raw payloads are omitted.
- If the preferred source cannot prove 100+ eligible pairs, the source must change before strategy work.

Recommendation preserved: treat CCXT as downloader/freeze mechanism only. The submitted system must run from frozen Parquet and manifest without network access.

## 100+ Pair Proof Design

Required proof artifacts:

- `artifacts/monitoring/universe_eligibility_full.csv`
- `artifacts/monitoring/level_5_pair_count_proof.json`

Proof logic should run inside `make validate-data` in full mode and use the same eligibility code intended for Level 5.

Minimum proof contents:

- mode: `full`;
- decision/rebalance date used for the proof;
- data/config/git hashes;
- manifest hash and input file hashes;
- exchange, quote, timeframe and date coverage;
- eligibility rules and thresholds;
- eligible count and scored count;
- selected/scored symbols;
- exclusions with reason codes;
- per-symbol first/last bar, valid-bar count, missingness and stale status;
- trailing 90-day median dollar volume used for ranking;
- 365-day prior valid-bar proof and preferred 730-day flag;
- runtime and memory or comparable scalability evidence.

Acceptance threshold:

- at least one full-mode rebalance date must have `eligible_count >= 100` and `scored_count >= 100`;
- fast mode cannot be used as final evidence;
- the full notebook and final artifacts must later display the same proof.

## Validation Artifacts Expected

`make validate-data` should create or verify:

- manifest hash match for OHLCV and instruments;
- UTC-aware timestamps and valid `bar_start_utc < bar_end_utc`;
- unique `(bar_start_utc, symbol)` keys;
- sorted rows;
- finite numeric values;
- positive prices and non-negative volume;
- OHLC invariant: `low <= min(open, close) <= max(open, close) <= high`;
- no duplicate bars;
- coverage, missingness and first/last bar reports;
- deterministic exclusion report;
- proof that no forward/backward fill creates features or returns;
- proof that missing execution prices block trading;
- stale valuation policy report;
- Level 5 100+ eligibility proof.

Required documentation outputs:

- `data/README.md`
- `reports/data_card.md`

Both should document source terms caveats, survivorship/delisting limitations, symbol-change handling, USDT-as-cash limitation, missing-bar behavior and offline reproducibility.

## Pre-Implementation Blockers Recorded

At the time of the feasibility review:

- No frozen data files existed.
- No manifest existed.
- No data validation command existed.
- No `pyproject.toml`, `uv.lock`, Makefile, package or tests existed.
- No Level 5 100+ pair proof artifacts existed.
- No source decision had been proven feasible.
- No stale/missing data policy had been implemented in code.
- No artifact metadata writer or hash validation existed.

These blockers were inputs to Stage 2 implementation. They should be reassessed during independent Stage 2 review rather than carried forward automatically.

## Current Review Use

Use this specialist report as a checklist for Stage 2 QA. It does not mark Stage 2 passed.
