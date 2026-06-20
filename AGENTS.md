# AGENTS.md — implementation contract for Codex

## Mission

Build a public, reproducible and reviewable Python repository satisfying the complete “AI Crypto Hedge Fund” assignment. The result is an educational/research historical trading system, not a profitability claim and not an enabled live trading bot.

The five technical levels are incremental views of **one shared architecture**. Never implement them as independent stacks.

## Read before editing

Read in this exact order:

1. `docs/00_GLOBAL_PLAN_AND_AUDIT.md`
2. `docs/11_REQUIREMENTS_TRACEABILITY.md`
3. `docs/01_ASSIGNMENT_AND_SCOPE.md`
4. `docs/02_ARCHITECTURE.md`
5. `docs/03_REPOSITORY_LAYOUT.md`
6. `docs/04_EXPERIMENT_PROTOCOL.md`
7. `docs/09_CONFIG_AND_INTERFACES.md`
8. `docs/05_IMPLEMENTATION_PLAN.md`
9. `docs/06_ACCEPTANCE_CRITERIA.md`
10. `docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`
11. `docs/07_PRESENTATION_OUTLINE.md`
12. `docs/10_RISKS_AND_DECISIONS.md`

Then inventory the existing repository, dependencies, data, tests and conventions before changing files.

## Highest-priority architecture rules

1. **Panel-native from day one.** Data, features, signals, weights, costs and the ledger support one or many symbols through the same APIs. Level 1 is a one-symbol configuration of the final engine.
2. **One broker and ledger for all levels.** Do not write a toy single-asset backtester and replace it later.
3. **Next-open execution.** Features use a completed daily bar; decisions execute at the next available open. Do not fill at the same close used to create a signal.
4. **Two-stage risk.** Apply risk constraints before allocation and validate/veto the candidate portfolio after allocation.
5. **Actual agent interaction.** Agents exchange typed messages with score, confidence, horizon, cutoffs and reason codes. Add an orchestrator and a visible decision trace. Renaming ordinary functions is insufficient.
6. **Final-test quarantine.** Implement and select all five levels on train/validation data, write a pretest lock, then run the 2025 final suite. Do not inspect final-test metrics level by level during development.
7. **Level 3 uses exactly a trailing 12-month estimation window.** With the default study, estimate on 2024 and hold OOS in 2025.
8. **Level 5 is hard, not aspirational.** A full run must actually score at least 100 eligible pairs. Fast CI may be smaller, but final artifacts may not be.
9. **Data is delivered.** The frozen processed dataset, instrument metadata and manifest must be present and sufficient for an offline final notebook run.
10. **One final notebook.** It is the end-to-end narrative and execution entry point, imports reusable package code, runs from a clean kernel and is committed with full outputs.
11. **An actual presentation is required.** Commit `presentation/deck.md` and rendered `presentation/deck.pdf`, maximum 10 slides.

## Research and safety rules

1. No look-ahead, target leakage, future universe membership or shuffled time split.
2. The final test may not choose models, thresholds, agent weights, portfolio constraints, assets or rebalance policies.
3. Report every strategy gross and net; net after fees/slippage is primary.
4. Calculate costs from risky-asset notional actually traded; do not charge cash as an instrument and do not undercount asset-to-asset rotation.
5. Never fabricate data, metrics, charts, model outputs or passing checks.
6. Synthetic data is test-fixture-only and must be labeled.
7. No external LLM, exchange credential or paid service is required for the default run.
8. Signal agents cannot place orders or override risk.
9. Risk can cap exposure, block assets, freeze trading or move to cash.
10. No live order submission. Any future execution adapter is disabled and fails closed.
11. Core MVP is long-only, unlevered, spot, daily bars. State the limitation and keep interfaces extensible.
12. UTC everywhere, with explicit bar-start, bar-close, decision and execution timestamps.
13. Missing/stale data, failed models and infeasible optimization must produce explicit errors/reason codes, not silent methodological fallbacks.
14. Prefer permissive dependencies. Do not copy `denisalpino/autofin` code; its notice is not an open-source license. Treat GPL/AGPL projects as references unless the owner accepts those obligations.

## Required baseline stack

- Python 3.11.
- `uv`, `pyproject.toml`, committed `uv.lock`.
- Package under `src/crypto_hedge_fund/`.
- Frozen daily spot OHLCV plus instrument metadata; CCXT downloader is supplementary.
- Econometrics: AutoReg/ARIMA-family expected-return model and GARCH(1,1) conditional volatility.
- ML: Logistic Regression and HistGradientBoostingClassifier or equivalent classical models.
- Portfolio: transparent equal-weight/inverse-volatility plus minimum-variance and one robust method.
- Tests: pytest; quality: Ruff; type hints on public APIs.
- Notebook execution: nbclient/nbconvert or equivalent clean-kernel runner.
- Presentation: Marp Markdown rendered to PDF, at most 10 slides.

## Stable commands

Create a Makefile or equivalent with:

```bash
make setup               # uv sync --frozen or initial lock creation
make data                # optional downloader/freeze path
make validate-data       # schema, hashes, coverage, 100+ eligibility proof
make lint
make test
make experiments-val     # Levels 1–5 on train/validation only
make pretest-freeze      # create final_test_lock.json
make final-test          # frozen Levels 1–5 only
make notebook-fast       # CI smoke, clearly labeled non-final
make notebook-full       # included data, frozen full methodology
make report
make presentation        # render deck.pdf and verify <=10 slides
make all-fast
```

`make notebook-full` and `make final-test` must not need exchange credentials, an LLM key or a live data download.

## Work order

1. Inventory the repository and write a short plan.
2. Freeze global architecture decisions: data clock, execution, costs, missing-data rules, typed contracts, risk sequence and artifacts.
3. Build environment, data schema, included snapshot and validation.
4. Build the shared panel-native broker, ledger, metrics, risk gates and unit tests.
5. Implement Levels 1–5 using train/validation only; do not read final-test returns.
6. Demonstrate agent interaction, dynamic rebalancing, monitoring and fail-safes.
7. Run acceptance checks and create the pretest lock.
8. Run the frozen final suite once for all levels.
9. Build/execute the single full notebook and render the 10-slide deck.
10. Perform a clean-clone rehearsal and prepare the public-repository submission report.

## Required artifacts

Per level:

```text
artifacts/metrics/level_<n>.csv
artifacts/equity/level_<n>.parquet
artifacts/weights/level_<n>.parquet       # where applicable
artifacts/orders/level_<n>.parquet
artifacts/fills/level_<n>.parquet
artifacts/figures/level_<n>_*.png
```

Cross-cutting:

```text
artifacts/final_test_lock.json
artifacts/monitoring/health_summary.csv
artifacts/monitoring/alerts.parquet
reports/final_report.md
presentation/deck.pdf
```

Every result identifies data/config/git hashes, periods, cost assumptions, benchmark, seed and whether it is validation or final-test output.

## Completion report

Before declaring completion:

1. Show commands run and exact pass/fail status.
2. Prove the final notebook runs from a clean artifacts directory.
3. Prove Level 5 handled at least 100 pairs in full mode.
4. Prove `deck.pdf` has at most 10 slides.
5. Show final-test lock and matching artifact hashes.
6. List skipped/blocked checks and known limitations honestly.
7. Remind the human owner to publish/verify the public GitHub or GitLab URL if the agent lacks permission.
