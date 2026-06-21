# 03 — Repository layout and file contracts

## Target tree

```text
.
├── AGENTS.md
├── README.md
├── LICENSE
├── Makefile
├── Dockerfile
├── pyproject.toml
├── uv.lock
├── .python-version
├── .env.example                         # no secret required by default
├── .github/
│   └── workflows/ci.yml
├── configs/
│   ├── default.yaml
│   ├── fast.yaml
│   ├── validation_selected.yaml         # generated/frozen choices
│   └── schema.yaml                      # optional config schema
├── data/
│   ├── README.md
│   ├── manifests/
│   │   └── ohlcv_daily_manifest.json
│   ├── processed/
│   │   ├── ohlcv_daily.parquet          # included frozen default data
│   │   └── instruments.parquet          # included symbol metadata
│   └── fixtures/                        # small synthetic test-only data
├── notebooks/
│   └── ai_crypto_hedge_fund.ipynb       # the one final executed notebook
├── presentation/
│   ├── deck.md                          # Marp source, <=10 slides
│   ├── deck.pdf                         # rendered final deliverable
│   └── assets/
├── reports/
│   ├── final_report.md
│   ├── data_card.md
│   ├── model_cards/
│   └── submission_report.md
├── artifacts/
│   ├── final_test_lock.json
│   ├── metrics/
│   ├── equity/
│   ├── weights/
│   ├── orders/
│   ├── fills/
│   ├── trades/
│   ├── monitoring/
│   ├── figures/
│   └── models/
├── scripts/
│   ├── download_data.py
│   ├── freeze_data.py
│   ├── validate_data.py
│   ├── run_experiments.py
│   ├── freeze_final_test.py
│   ├── execute_notebook.py
│   ├── build_report.py
│   └── build_presentation.py
├── src/
│   └── crypto_hedge_fund/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── clock.py
│       ├── types.py
│       ├── provenance.py
│       ├── data/
│       │   ├── adapters.py
│       │   ├── download.py
│       │   ├── schema.py
│       │   ├── validation.py
│       │   ├── universe.py
│       │   └── storage.py
│       ├── features/
│       │   ├── technical.py
│       │   ├── statistical.py
│       │   ├── liquidity.py
│       │   ├── cross_sectional.py
│       │   └── pipeline.py
│       ├── validation/
│       │   ├── splits.py
│       │   ├── purging.py
│       │   ├── bootstrap.py
│       │   └── randomization.py
│       ├── models/
│       │   ├── technical.py
│       │   ├── econometric.py
│       │   ├── ml.py
│       │   ├── calibration.py
│       │   └── registry.py
│       ├── agents/
│       │   ├── base.py
│       │   ├── orchestrator.py
│       │   ├── technical.py
│       │   ├── econometric.py
│       │   ├── ml.py
│       │   ├── regime.py
│       │   ├── aggregate.py
│       │   └── monitoring.py
│       ├── risk/
│       │   ├── pre_allocation.py
│       │   ├── post_allocation.py
│       │   ├── limits.py
│       │   └── kill_switch.py
│       ├── portfolio/
│       │   ├── allocators.py
│       │   ├── covariance.py
│       │   ├── constraints.py
│       │   ├── rebalance.py
│       │   └── selection.py
│       ├── execution/
│       │   ├── orders.py
│       │   ├── broker.py
│       │   ├── costs.py
│       │   ├── fills.py
│       │   └── future_exchange.py      # disabled interface/stub only
│       ├── backtest/
│       │   ├── engine.py
│       │   ├── ledger.py
│       │   └── benchmarks.py
│       ├── metrics/
│       │   ├── performance.py
│       │   ├── risk.py
│       │   ├── prediction.py
│       │   ├── system_quality.py
│       │   └── reporting.py
│       ├── monitoring/
│       │   ├── data_quality.py
│       │   ├── drift.py
│       │   ├── health.py
│       │   └── alerts.py
│       └── experiments/
│           ├── common.py
│           ├── level_1.py
│           ├── level_2.py
│           ├── level_3.py
│           ├── level_4.py
│           └── level_5.py
└── tests/
    ├── unit/
    ├── integration/
    └── regression/
```

The exact number of files may be reduced, but the boundaries among data, clock, features, agents, risk, portfolio, rebalance, execution, ledger, metrics and monitoring must remain explicit.

## Architectural anti-patterns

Do not create:

- a separate single-asset engine and portfolio engine;
- per-level copies of metrics or cost code;
- notebook-only business logic;
- an `agents/` folder where classes are simple aliases with no typed interaction;
- a risk function that runs only before portfolio construction;
- a live exchange implementation enabled by default;
- multiple “final” notebooks;
- final results that depend on a network download.

## File contracts

### `README.md`

Must contain:

- project purpose, scope and financial disclaimer;
- architecture diagram;
- exact setup/run commands;
- data provenance and included-file locations;
- explicit next-open execution convention;
- five-level summary;
- primary frozen final-test results table generated from artifacts;
- full/fast runtime expectations and hardware used;
- limitations, including survivorship, daily bars, USDT-as-cash and execution simplification;
- license and third-party attribution;
- public repository/release URL when submitted.

### `data/README.md`

Must explain:

- exchange, spot market and quote currency;
- bar-start/bar-end timestamp semantics;
- symbols and point-in-time selection rules;
- timeframe/date range;
- OHLCV and instrument schemas;
- how the snapshot was downloaded/frozen;
- included file sizes and hashes;
- data-source terms caveat;
- survivorship, delisting, symbol-change and stablecoin limitations;
- missing-bar/valuation/tradability policy.

### `data/manifests/ohlcv_daily_manifest.json`

Contains at least:

- collection timestamp;
- exchange and CCXT/library version;
- request parameters;
- actual min/max timestamps;
- row/symbol counts;
- per-symbol coverage summary or referenced table;
- file SHA-256;
- instrument metadata SHA-256;
- schema/version identifier;
- preprocessing code/git version.

### `reports/data_card.md`

Documents source, collection, transformations, exclusions, missingness, leakage safeguards, intended use and limitations.

### Model/agent cards

Create at least:

- `technical_agent.md`;
- `econometric_agent.md`;
- `ml_agent.md`;
- `regime_agent.md`;
- `ensemble_orchestrator.md`.

Each card includes responsibility, features, target, fit/retrain schedule, cutoffs, validation, confidence/abstention behavior, trading mapping, metrics, risks and intended use.

### `artifacts/final_test_lock.json`

Records the immutable pretest selection state:

- git commit;
- data/config/lock hashes;
- train/validation/test dates;
- selected Level 1–5 parameters and methods;
- cost assumptions;
- creation timestamp.

Final-test artifact metadata must reference this lock.

### Final notebook

Use exact visible chapter order:

1. Executive summary and coherent fund vision.
2. Reproducibility/environment/data hashes.
3. Data preparation, provenance and quality.
4. Architecture and agent interaction trace.
5. Model validation and no-leakage protocol.
6. **Level 1 — Baseline Strategy for a Single Cryptocurrency.**
7. **Level 2 — Adding AI Agents, Econometrics and ML.**
8. **Level 3 — Portfolio Management on Historical Data (5–7 assets, prior 12 months).**
9. **Level 4 — Dynamic Portfolio Rebalancing.**
10. **Level 5 — Portfolio Expansion to 100+ Pairs.**
11. Cross-level comparison, monitoring and fail-safes.
12. Limitations, real-trading application and production roadmap.

The notebook must:

- run top-to-bottom in a clean kernel;
- use included data and repository-relative paths;
- call package APIs rather than duplicate algorithms;
- recreate or verify headline artifacts from an empty artifacts directory;
- display concise actual tables/charts and explanations;
- show full-mode Level 5 symbol count;
- show data/config/git/final-lock hashes;
- avoid giant raw tables and unbounded logs;
- be committed with full executed outputs.

### Presentation

`presentation/deck.md` is source. `presentation/deck.pdf` is the reviewer deliverable.

- maximum 10 slides;
- all four required conceptual sections;
- roughly two slides per section where possible;
- actual generated results only;
- clear architecture interactions;
- readable without external speaker explanation;
- no placeholder performance numbers.

### Artifacts

Every artifact carries or references:

- experiment/level;
- validation or final-test label;
- creation timestamp;
- data/config/git/final-lock hashes;
- periods;
- fee/slippage assumptions;
- benchmark;
- seed;
- symbol/universe count;
- warnings/fallbacks.

## Configuration strategy

- `configs/default.yaml`: complete methodology and full data.
- `configs/fast.yaml`: reduced runtime for CI only; it may use fewer symbols and fewer statistical repetitions but cannot alter causal timing or cost logic.
- `configs/validation_selected.yaml`: generated frozen choices selected without final-test data.
- No hidden constants in notebook cells.
- Full committed notebook/results must use full mode, not fast mode.

## Packaging and quality rules

- `src/` layout and installable package.
- No imports from scripts or notebook cells.
- Public functions/classes have type hints and concise docstrings.
- No mutable module-level experiment state.
- Use `pathlib.Path` and root-resolution helpers.
- Pin dependency versions via `uv.lock`.
- Numerical core independently testable without notebook/UI.
- No secrets, absolute local paths, caches or temporary downloads committed.
