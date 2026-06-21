# 05 — Implementation plan and gates

## Core sequencing rule

Implement vertical slices, but do not reveal final-test results after each slice. Levels 1–5 are developed and selected on train/validation data first. The frozen final suite runs only after all levels, interfaces and policies are complete.

## Phase 0 — repository inventory and requirement freeze

Tasks:

- inspect the existing tree, dependencies, data and tests;
- read the complete handoff and source traceability matrix;
- write `docs/DECISIONS.md` for ambiguities;
- freeze global choices: panel schema, timestamp semantics, next-open execution, costs, missing-data behavior, risk sequence, splits and artifact contracts;
- identify anything that cannot be automated by Codex, especially public repository publication.

Exit criteria:

- short inventory and non-destructive implementation plan exist;
- no strategy code is written against an undefined time/cost convention;
- all five levels map to one shared architecture.

## Phase 1 — environment and project skeleton

Tasks:

- Python 3.11, `pyproject.toml`, `uv.lock` and `src/` package;
- Ruff, pytest, notebook tooling and CI skeleton;
- Makefile targets including validation, freeze, final test and presentation;
- config loading, provenance hashes, UTC clock utilities and centralized seed;
- typed domain records and protocols.

Exit criteria:

- `uv sync --frozen` succeeds;
- package imports;
- lint/test skeleton runs;
- config/data/git hash utilities are tested.

## Phase 2 — included data layer

Tasks:

- implement exchange-neutral public OHLCV adapter;
- download/freeze one primary spot-exchange snapshot;
- create `ohlcv_daily.parquet`, `instruments.parquet` and manifest;
- normalize bar start/end timestamps to UTC;
- deterministic symbol filtering and point-in-time eligibility;
- schema, OHLC, coverage, missingness and hash checks;
- fixtures and corruption tests;
- data README and data card.

Exit criteria:

- default data is physically present and validates offline;
- a full-mode date has at least 100 eligible pairs;
- rerunning normalization is deterministic;
- corrupted/stale fixtures fail loudly;
- no silent source substitution or fill.

## Phase 3 — shared panel-native execution kernel

Build this before any level-specific strategy.

Tasks:

- multi-asset holdings and cash ledger;
- pre-trade drifted weights;
- next-open order generation and simulated fills;
- chargeable risky-notional and reporting-turnover calculations;
- fees/slippage and optional capacity diagnostics;
- benchmarks;
- performance/risk/system metrics;
- artifact writers and provenance metadata;
- pre/post risk gate interfaces;
- rebalance controller interface.

Required hand-calculated tests:

- signal from a completed bar cannot affect same-close or prior PnL;
- cash→asset, asset→cash and asset A→asset B cost cases;
- buy-and-hold direct calculation;
- no position means zero risky PnL;
- weight/cash reconciliation;
- blocked asset and infeasible target fail closed;
- missing next-open price prevents execution.

Exit criteria:

- one engine handles one and many symbols;
- no duplicate single-asset logic is needed later;
- all timing/cost tests pass.

## Phase 4 — agent orchestration and risk skeleton

Tasks:

- implement `AgentContext`, signals, abstentions and reason codes;
- implement orchestrator and aggregator;
- pre-allocation risk constraints;
- post-allocation validation/veto;
- decision trace and audit logs;
- controlled fail-safe fixtures for stale data, NaN score, extreme weights, optimizer failure and kill switch.

Exit criteria:

- at least two dummy/test agents interact through typed records;
- a complete proposal→risk→allocation→execution trace is testable;
- signal agents cannot mutate the ledger;
- risk gates demonstrably veto unsafe decisions.

## Phase 5 — Level 1 on train/validation only

Tasks:

- SMA technical agent on BTC/USDT;
- bounded candidate windows;
- same shared engine, cash and benchmark;
- choose/freeze windows using validation only;
- performance and risk metrics, gross/net;
- explain baseline-to-agent mapping.

Exit criteria:

- validation artifacts exist and are labeled `validation`;
- no 2025 return metric is exposed;
- notebook section can call the experiment API without custom logic.

## Phase 6 — Level 2 on train/validation only

Tasks:

- causal feature pipeline and purged walk-forward validation;
- Technical, Econometric, ML and Regime Agents;
- common position-sizing/risk overlay for fair comparison;
- validation of retraining cadence, thresholds and ensemble weights;
- predictive and after-cost trading/risk metrics;
- block bootstrap, circular shift, sensitivity and multiple seeds;
- model/agent cards and full decision trace.

Exit criteria:

- each prediction records fit and feature cutoffs;
- approaches are compared on identical periods/costs/benchmarks;
- failed model fits abstain safely;
- selected settings are persisted without reading final-test outcomes.

## Phase 7 — Level 3 on train/validation only

Tasks:

- cutoff-based 5–7 liquid-asset selection with separate 2023 validation and 2024 final vintages;
- equal weight, inverse volatility, minimum variance and robust alternative;
- explicit objectives/constraints;
- validation criterion for selecting the submitted method;
- validate methods by estimating on 2023 and holding in 2024; then implement the final 2024 trailing-12-month estimation path without executing 2025 yet;
- concentration/risk contribution diagnostics;
- write real-trading application subsection.

Exit criteria:

- universe selection uses no later popularity/performance data;
- all weights feasible and reproducible;
- optimizer failures have explicit safe fallbacks;
- the 12-month rule is covered by tests/config.

## Phase 8 — Level 4 on train/validation only

Tasks:

- rolling 12-month estimates using the 2023-cutoff universe for 2024 validation and the 2024-cutoff universe for 2025 final test;
- calendar, drift, score-change and risk triggers;
- predeclared net-risk-turnover utility and tie-breakers;
- rebalance reason logs;
- turnover/cost sensitivity.

Exit criteria:

- policy selection is validation-only;
- candidate weights, triggers and final approvals are logged;
- static Level 3 benchmark uses the same engine.

## Phase 9 — Level 5 on train/validation only

Tasks:

- dynamic point-in-time eligibility;
- vectorized panel/cross-sectional features;
- pooled/lightweight score model rather than heavyweight per-pair models;
- score at least 100 pairs in full-mode validation where available;
- net-alpha/confidence/risk/liquidity priority and top-K allocation;
- AI/regime-driven rebalance intent plus deterministic risk approval;
- capacity diagnostics;
- system-health, long-term quality and fail-safe artifacts;
- runtime/memory/scalability tests.

Exit criteria:

- at least one full-mode rebalance handles >=100 pairs before final freeze;
- dropped symbols and reasons are recorded;
- no risk/capacity failure is silent;
- fast mode is CI-safe and explicitly non-final.

## Phase 10 — pretest acceptance and freeze

Tasks:

- run lint, tests, data validation and all validation experiments;
- resolve every selected model/method/policy into `validation_selected.yaml`;
- verify notebook structure and deck outline without test results;
- create `artifacts/final_test_lock.json` with git/data/config/lock hashes;
- tag or commit the pretest state where practical.

Exit criteria:

- all applicable acceptance criteria pass;
- no uncommitted methodology change remains;
- lock contains Levels 1–5 selections;
- final test command refuses mismatched hashes.

## Phase 11 — frozen final test for all levels

Tasks:

- run Levels 1–5 from the same lock;
- generate gross/net performance and risk results, benchmarks and statistical checks;
- record warnings, runtime and actual Level 5 universe count;
- do not search/tune on test.

Exit criteria:

- all final artifacts reference the lock hash;
- Level 5 proves >=100 scored pairs;
- any bug-induced rerun is documented according to `12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`.

## Phase 12 — notebook, report and presentation

Tasks:

- build the one final notebook with exact Level 1–5 headings;
- execute full mode from a clean kernel and clean artifacts directory;
- include hashes, actual tables/charts, decision trace, monitoring and limitations;
- write final report;
- create the 10-slide deck source and render `deck.pdf`;
- validate slide count and visual readability.

Exit criteria:

- one executed notebook runs cleanly and recreates headline artifacts;
- deck PDF has at most 10 slides;
- deck claims match code/results and future items are labeled.

## Phase 13 — Docker, CI, clean clone and publication

Tasks:

- Dockerfile with non-root user where practical;
- CI: lint, tests, data validation and fast notebook;
- third-party license inventory;
- clean-clone rehearsal;
- submission report with exact commands/results;
- publish or hand off the final public GitHub/GitLab step to the owner.

Exit criteria:

- documented clone/run commands are accurate;
- no secret or absolute path is committed;
- public URL is confirmed by the human owner;
- known limitations and skipped checks are explicit.

## Suggested dependencies

Core:

```text
numpy, pandas, pyarrow, scipy, pyyaml, pydantic,
scikit-learn, statsmodels, arch, skfolio,
ccxt, matplotlib, plotly, jupyter, nbclient
```

Development:

```text
pytest, pytest-cov, ruff, pip-licenses
```

Optional reporting:

```text
quantstats
```

Pin exact versions in `uv.lock`. Transparent in-house calculations remain the source of truth; external libraries are helpers/verification layers.
