# AGENTS.md - repository working contract

## Mission

Maintain this repository as a public, reproducible, and reviewable Python
submission for the AI Crypto Hedge Fund assignment. The project is an
educational/research historical trading system. It is not investment advice, not
a profitability claim, and not an enabled live trading bot.

The five technical levels are configurations of one shared architecture. Do not
rebuild them as independent stacks.

## Current Documentation

Read these files before changing core behavior:

1. `docs/README.md`
2. `docs/01_PROJECT_OVERVIEW.md`
3. `docs/02_ARCHITECTURE.md`
4. `docs/03_COMPONENTS_AND_FLOW.md`
5. `docs/04_DATA_AND_ARTIFACTS.md`
6. `docs/05_EXPERIMENT_PROTOCOL.md`
7. `docs/06_REPRODUCIBILITY_AND_SUBMISSION.md`
8. `docs/07_LIMITATIONS_AND_ATTRIBUTION.md`

These docs replaced the earlier implementation-plan, stage-gate, audit, and
prompt-oriented files. Keep the docs reader-facing: explain what the project is,
how it works, how to reproduce it, and what its limitations are.

## Architecture Rules

1. Panel-native from day one. Data, features, signals, weights, costs, and ledger
   logic support one or many symbols through the same APIs.
2. One broker and ledger for all levels. Level 1 is a one-symbol configuration of
   the same engine used by Levels 2-5.
3. Next-open execution. Features use completed daily bars; decisions execute at
   the next available open.
4. Two-stage risk. Apply pre-allocation constraints before allocation and validate
   the candidate portfolio after allocation.
5. Agents exchange typed messages with score, confidence, horizon, cutoffs, and
   reason codes. Agents cannot place orders or mutate ledger state.
6. Final-test quarantine. Do not tune models, thresholds, assets, risk limits,
   benchmarks, or rebalance policy from exposed final-test results.
7. Level 3 uses a trailing 12-month final estimation window: estimate on 2024 and
   evaluate out of sample in 2025.
8. Level 5 full mode must score at least 100 eligible pairs. The current final
   proof reports 120 eligible and 120 scored pairs.
9. The frozen processed dataset, instrument metadata, lock, final artifacts,
   executed notebook, final report, and deck are committed for offline review.

## Research And Safety Rules

1. No look-ahead, target leakage, future universe membership, or shuffled time
   split.
2. Report net results after fees and slippage as primary.
3. Calculate costs from risky-asset notional actually traded; do not charge cash
   as a fee-bearing instrument.
4. Never fabricate data, metrics, charts, model outputs, or passing checks.
5. Synthetic data is test-fixture-only and must be labeled.
6. No exchange credential, external LLM, paid service, or live download is
   required for the default run.
7. Risk can cap exposure, block assets, freeze trading, or move to cash.
8. No live order submission is enabled.
9. Core MVP is long-only, unlevered, spot, daily bars.
10. UTC timestamp semantics are required throughout.
11. Missing/stale data, failed models, and infeasible optimization must produce
    explicit errors or reason codes.

## Stable Commands

```bash
make setup
make validate-data
make lint
make test
make experiments-val
make pretest-freeze
make notebook-fast
make notebook-full
make report
make presentation
make all-fast
make release-verify
```

`make final-test` exists for the frozen final suite, but ordinary release review
should not rerun it now that final-test exposure is complete.

## Current Release State

- Final-test lock:
  `c33b5eb396f60b1e2a7890616b8d9ae1cd69e91375dec925b68b6673d843af5e`.
- Final artifacts:
  `artifacts/final_test/c33b5eb396f6/`.
- Final notebook:
  `notebooks/ai_crypto_hedge_fund.ipynb`, committed with outputs.
- Final report:
  `reports/final_report.md`.
- Presentation:
  `presentation/deck.pdf`, 10 pages.
- Public docs:
  `docs/README.md` plus `docs/01_...` through `docs/07_...`.

## Required Release-Facing Artifacts

Keep these tracked unless the artifact contract is intentionally redesigned and
`make release-verify` passes afterward:

```text
data/processed/ohlcv_daily.parquet
data/processed/instruments.parquet
data/manifests/ohlcv_daily_manifest.json
artifacts/final_test_lock.json
artifacts/final_test_lock.json.metadata.json
artifacts/final_test/c33b5eb396f6/
artifacts/metrics/level_*.csv
artifacts/equity/level_*.parquet
artifacts/weights/level_*.parquet
artifacts/orders/level_*.parquet
artifacts/fills/level_*.parquet
artifacts/figures/level_*.png
artifacts/monitoring/
reports/final_report.md
reports/data_card.md
reports/model_cards/
notebooks/ai_crypto_hedge_fund.ipynb
presentation/deck.md
presentation/deck.pdf
```

## Cleanup Policy

Internal prompt files, stage logs, scratch audits, and handoff reports are not
part of the final submission surface. The cleaned repository intentionally keeps
only public-facing docs and reproducibility artifacts.

When removing tracked files, first verify they are not required by:

```bash
make release-verify
```

After cleanup, commit the change and run `make release-verify` again at the new
HEAD.

## Completion Report

Before declaring a release-ready state, report:

1. Commands run and pass/fail status.
2. Final notebook execution status.
3. Level 5 pair-count proof.
4. Deck page count.
5. Final-test lock verification status.
6. Any skipped or blocked checks.
7. Reminder that the human owner must publish or verify the public GitHub/GitLab
   URL if the agent cannot.
