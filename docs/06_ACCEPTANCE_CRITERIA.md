# 06 — Acceptance criteria and Definition of Done

The project is complete only when every applicable item passes or is explicitly reported as blocked with evidence. A limitation cannot replace a hard source requirement such as the 100+ pair Level 5 run.

## A. Assignment and submission coverage

- [ ] Public GitHub/GitLab URL is confirmed by the human owner.
- [ ] Part 1 and Part 2 use the same architecture, agents, risk concepts and portfolio methods.
- [ ] Presentation source and rendered PDF exist.
- [ ] `deck.pdf` contains at most 10 slides and addresses all four conceptual sections.
- [ ] Every major design choice in the deck has a rationale and limitation.
- [ ] One and only one final notebook is clearly designated and committed with full outputs.
- [ ] Notebook headings visibly follow Levels 1–5 in assignment order.
- [ ] Data preparation, model validation, backtesting, visualization and explanation are all present.

## B. Reproducibility and data delivery

- [ ] Python version is declared.
- [ ] `pyproject.toml` and committed `uv.lock` exist.
- [ ] `uv sync --frozen` succeeds in a clean environment.
- [ ] Frozen real `ohlcv_daily.parquet`, `instruments.parquet` and manifest are physically delivered with the project or via a repository mechanism fetched by normal checkout.
- [ ] The full notebook runs after checkout without a live data download, private exchange key, LLM key or paid service.
- [ ] Manifest records source, dates, schema, row/symbol counts and SHA-256 hashes.
- [ ] Random seed and package versions are recorded.
- [ ] Notebook prints data/config/git/final-lock hashes.
- [ ] Deleting generated artifacts and rerunning recreates headline outputs.
- [ ] Docker build and documented run command succeed, unless explicitly marked as the optional bonus that was not completed.

## C. Data correctness and time semantics

- [ ] Daily bars have explicit UTC start and end timestamps.
- [ ] `(bar_start_utc, symbol)` uniqueness is tested.
- [ ] OHLC invariants, positive prices and non-negative volume checks pass.
- [ ] Coverage/missingness and first/last bar reports exist.
- [ ] Stable, leveraged, invalid and non-spot pairs are filtered deterministically.
- [ ] No forward/backward fill creates artificial returns or features.
- [ ] No future liquidity or future active status selects historical universe members.
- [ ] Missing execution price blocks the trade.
- [ ] Existing stale holdings follow a documented marked-valuation/freeze policy.
- [ ] Survivorship, delisting, symbol-change and USDT-cash limitations are documented.
- [ ] A full-mode date proves at least 100 eligible pairs.

## D. Shared-engine architecture

- [ ] One panel-native market-data model handles one and many symbols.
- [ ] Levels 1–5 use the same broker, ledger, time convention, cost model and core metrics.
- [ ] No duplicated single-asset and portfolio backtest engines exist.
- [ ] Signal, risk, portfolio, rebalance, execution, ledger and monitoring boundaries are explicit.
- [ ] Business logic is in `src/`, not duplicated in notebook cells.
- [ ] All target weights include explicit cash and reconcile to one within tolerance.

## E. Backtest and execution correctness

- [ ] Features from a completed bar execute only at the next available open.
- [ ] A dedicated regression test proves no same-close or prior-period PnL.
- [ ] Pre-trade drifted holdings/weights are used.
- [ ] Orders/fills are separate from target weights; only fills alter the ledger.
- [ ] Fee-bearing notional uses risky assets actually traded.
- [ ] Cash→asset, asset→cash and asset A→asset B cost tests pass.
- [ ] Cash is included in reconciliation/reporting turnover but is not charged as a traded instrument.
- [ ] Fees and slippage are deducted and gross/net results are available; net is primary.
- [ ] Benchmarks use the same clock, tradability and costs.
- [ ] Zero risky exposure produces zero risky PnL when cash rate is zero.
- [ ] Invalid weights, NaN/inf, missing prices and infeasible optimization fail closed.

## F. Validation and final-test integrity

- [ ] Train, validation and final-test dates are fixed/displayed.
- [ ] No shuffled split is used.
- [ ] Purging/embargo accounts for forward-label horizon.
- [ ] Preprocessing is fit only within historical folds.
- [ ] All models, thresholds, agent weights, universes, constraints and rebalance policies are selected without final-test outcomes.
- [ ] Levels 1–5 are implemented/selected before final-test execution.
- [ ] `artifacts/final_test_lock.json` exists and records git/data/config/lock hashes plus selected choices.
- [ ] Final artifacts reference a matching lock hash.
- [ ] Final-test command refuses mismatched methodology/data hashes.
- [ ] Block-bootstrap confidence interval is included.
- [ ] Signal-randomization/circular-shift test is included.
- [ ] Stochastic models are checked across multiple seeds.
- [ ] Major parameters and transaction costs have sensitivity analysis.

## G. Agent architecture and interaction

- [ ] Agents have clear responsibilities and typed inputs/outputs.
- [ ] Outputs include score, confidence, horizon, fit cutoff, feature cutoff and reason codes.
- [ ] Agents can abstain/fail safely.
- [ ] An orchestrator invokes multiple agents and resolves/aggregates outputs.
- [ ] Per-agent contributions and disagreement are logged.
- [ ] Notebook shows at least one end-to-end agent decision trace.
- [ ] Signal agents cannot submit orders or mutate the ledger.
- [ ] Default run has no external LLM/network inference dependency.
- [ ] Optional narrative/LLM output cannot alter positions or risk.

## H. Risk, portfolio and rebalance controls

- [ ] Pre-allocation risk gate blocks data/model/liquidity violations and emits constraints.
- [ ] Post-allocation risk gate validates actual candidate weights and can veto/cap/move to cash.
- [ ] Per-asset, gross exposure, volatility, concentration, turnover and liquidity/capacity limits are enforced.
- [ ] Risk Agent has hard veto authority.
- [ ] Portfolio optimizer failures have explicit safe fallback and reason code.
- [ ] Rebalance controller logs calendar/drift/signal/risk trigger reasons.
- [ ] Fail-safe scenarios are demonstrated, not only described.

## I. Level 1

- [ ] BTC/USDT SMA strategy runs through the shared engine.
- [ ] BTC buy-and-hold benchmark uses identical evaluation window.
- [ ] ROI, Sharpe and drawdown are shown with additional performance/risk/cost metrics.
- [ ] Explanation maps the simple strategy to the typed agent architecture.

## J. Level 2

- [ ] Technical strategy/agent exists.
- [ ] Econometric expected-return model exists.
- [ ] Econometric conditional-volatility model exists and affects score/risk.
- [ ] At least two classical ML models are compared.
- [ ] Interacting deterministic ensemble/orchestrator exists.
- [ ] Features, target, fit/test and retraining cadence are documented.
- [ ] All approaches use the same OOS period, costs, sizing/risk overlay and benchmark.
- [ ] Predictive metrics and after-cost performance/risk metrics are separated.
- [ ] Random-chance/overfitting checks are included.

## K. Level 3

- [ ] 5–7 assets are selected at each vintage cutoff using only then-available liquidity/coverage information.
- [ ] Validation uses a 2023-cutoff universe/weights evaluated in 2024; final uses a 2024-cutoff universe/weights evaluated in 2025.
- [ ] Final static weights use exactly the prior 12 months of history.
- [ ] Weights are frozen before OOS execution.
- [ ] Equal weight and inverse volatility baselines exist.
- [ ] Minimum variance and at least one robust alternative exist.
- [ ] Every optimizer has an explicit objective and constraints.
- [ ] The submitted “optimal” method is selected by a predefined validation criterion, not final test.
- [ ] Portfolio performance, risk, concentration, liquidity and cost metrics are reported.
- [ ] Real-trading application section covers weights→orders, exchange precision/minimum notional, costs, liquidity, custody and reconciliation limitations.

## L. Level 4

- [ ] Within each vintage, the Level 3 universe remains fixed; validation and final vintages are selected at their own prior cutoffs.
- [ ] Rolling historical estimates are causal.
- [ ] Calendar, drift, signal-change and/or risk triggers are implemented.
- [ ] The policy-selection utility and tie-breakers are declared before final test.
- [ ] Rebalance reason log and weight timeline are saved.
- [ ] Static benchmark and turnover/cost comparison are shown.

## M. Level 5

- [ ] Full run handles and scores at least 100 eligible pairs on at least one rebalance date.
- [ ] Full committed notebook/artifacts prove the count; fast-mode count is not used as evidence.
- [ ] Point-in-time coverage/liquidity selection is implemented.
- [ ] Vectorized panel features and a pooled/lightweight modeling approach avoid heavyweight per-pair loops.
- [ ] Agent signals are prioritized using a documented net-alpha/confidence/risk/liquidity rule.
- [ ] Dynamic top-K portfolio, cash and constraints are implemented.
- [ ] Agent/regime changes can trigger rebalance intent; deterministic risk approves/rejects.
- [ ] Monitoring goes beyond return KPIs.
- [ ] Long-term quality includes rolling stability, drift/calibration, failures, cost decay and incidents.
- [ ] Stale data, invalid signals, high drawdown/volatility, optimizer failure and reconciliation/weight failure stop scenarios are demonstrated.
- [ ] Runtime and peak-memory or comparable scalability evidence is reported.

## N. Artifacts, narrative and engineering quality

- [ ] Metrics, equity, weights, orders/fills and figures are persisted.
- [ ] Artifacts identify periods, validation/test status, config/cost assumptions, benchmark, seed and hashes.
- [ ] `reports/final_report.md` explains positive, negative and inconclusive results honestly.
- [ ] Presentation uses actual generated results only.
- [ ] README has exact clean-clone commands and expected runtime.
- [ ] Known limitations are prominent.
- [ ] `ruff check .`, formatting check and pytest pass.
- [ ] Fast notebook CI passes and is clearly labeled non-final.
- [ ] Public APIs have type hints.
- [ ] No secrets, local absolute paths, large temporary files or notebook caches are committed.
- [ ] Third-party licenses are inventoried.
- [ ] No code is copied from `autofin` or incompatible sources.

## Mandatory commands

```bash
uv sync --frozen
make validate-data
make lint
make test
make experiments-val
make pretest-freeze
make final-test
make notebook-full
make report
make presentation
```

## Completion report template

```markdown
## Public submission
- URL:
- commit/tag:

## Commands executed
- `...` — pass/fail, runtime

## Final-test lock
- path/hash:
- data/config/git hashes:

## Generated artifacts
- path — description

## Hard proofs
- full Level 5 eligible/scored count:
- deck slide count:
- clean notebook run:

## Final test protocol
- dates, costs, benchmark, selected choices

## Limitations
- ...

## Skipped/blocked checks
- exact reason and evidence
```
