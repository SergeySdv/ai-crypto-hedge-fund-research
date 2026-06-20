# Role / stage / attempt

Independent execution/accounting specialist and architecture reviewer / Stage 3: Shared Panel-Native Execution Kernel / attempt 02.

## Scope

Audited the Stage 3 attempt 02 remediation for architecture and accounting correctness. Focus areas were completed-bar to next-open execution semantics, ledger state transitions, risky-notional transaction-cost accounting, benchmark contract, metrics suitability, fail-closed behavior, panel-native reuse for Levels 1-5, artifact provenance, final-test quarantine, and absence of live trading.

No implementation code, tests, configs, data, notebooks, presentation files, strategy artifacts, commits, tags, or destructive Git operations were changed or run. Writes were limited to this report and `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_*.log`.

## Sources read

- `AGENTS.md`
- `MASTER_PROMPT_CODEX_TEAMLEAD.md`
- `docs/00_GLOBAL_PLAN_AND_AUDIT.md`
- `docs/11_REQUIREMENTS_TRACEABILITY.md`
- `docs/01_ASSIGNMENT_AND_SCOPE.md`
- `docs/02_ARCHITECTURE.md`
- `docs/03_REPOSITORY_LAYOUT.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `docs/05_IMPLEMENTATION_PLAN.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`
- `docs/07_PRESENTATION_OUTLINE.md`
- `docs/10_RISKS_AND_DECISIONS.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/teamlead/PROJECT_STATE.md`
- `reports/teamlead/STAGE_BOARD.md`
- `reports/teamlead/RISK_REGISTER.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/IMPLEMENTATION_REPORT.md`

## Assumptions and decisions

- I treated the governing docs as binding, especially the convention that a completed daily bar starting at `t` executes at the next daily open, which is the timestamp `t+1` for bar-start-labeled UTC data.
- I accepted `feature_cutoff == decision_time == execution_time` as valid for daily UTC candles because the completed bar close and next bar open share the same boundary timestamp. This is documented in the attempt 02 implementation and enforced by `ResearchClock` ordering as non-decreasing after `bar_end`.
- I treated `PanelMarketData.benchmark_open_to_open` as an explicit price-normalized open-to-open helper, not a broker-costed benchmark result. Later strategy comparisons that require broker-costed benchmarks should submit benchmark weights through `SimulatedBroker`.
- Reading config test-period dates, Stage 2 universe proof artifacts, and final-test fail-closed code is not final-test metric exposure. I did not run `make final-test` and did not inspect strategy/model/portfolio final-test returns.

## Files inspected or changed

Inspected:

- `src/crypto_hedge_fund/clock.py`
- `src/crypto_hedge_fund/types.py`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/execution/__init__.py`
- `src/crypto_hedge_fund/execution/panel.py`
- `src/crypto_hedge_fund/execution/costs.py`
- `src/crypto_hedge_fund/execution/ledger.py`
- `src/crypto_hedge_fund/execution/broker.py`
- `src/crypto_hedge_fund/metrics/performance.py`
- `src/crypto_hedge_fund/artifacts/writers.py`
- `tests/unit/test_clock.py`
- `tests/unit/test_types.py`
- `tests/unit/test_execution_kernel.py`
- `tests/unit/test_costs.py`
- `tests/unit/test_metrics.py`
- `tests/unit/test_artifacts.py`
- `configs/default.yaml`
- `Makefile`

Changed:

- `reports/agent_reports/stage_03_shared_engine/attempt_02/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_uv_sync_frozen.log`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_make_test.log`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_pytest_clock_execution_costs_metrics.log`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_git_diff_stat.log`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_git_status_short_branch_untracked.log`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_execution_accounting_probe.log`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_final_test_live_scan.log`

## Deliverables

- Inspected the Stage 3 execution, cost, ledger, metrics, artifact, clock and typed-record source/tests.
- Ran and logged every required command.
- Ran a synthetic execution/accounting probe to confirm `2024-01-01` completed-bar input fills at `2024-01-02` open, with first PnL after that fill and explicit missing-open failure.
- Verified/refuted each attempt 01 failed item with source and test evidence.
- Identified no blocker or high-severity rework item for Stage 3 attempt 02.

## Acceptance-criteria mapping

| Criterion | Status | Evidence |
|---|---|---|
| Completed-bar `t` executes at `open(t+1)`, not same close and not `t+2` | PASS | `build_daily_research_clock` sets `bar_end`, `feature_cutoff`, `decision_time`, and `execution_time` to `t+1` (`src/crypto_hedge_fund/clock.py:38-48`). `tests/unit/test_clock.py:14-22` asserts `2024-01-01` executes at `2024-01-02`. `tests/unit/test_execution_kernel.py:38-66` asserts the Jan 1 signal fills Jan 2, with no Jan 1 exposure and PnL starting after the Jan 2 open. |
| Missing `open(t+1)` fails closed | PASS | `SimulatedBroker.run` checks execution schedule timestamps against available opens and raises `MissingPriceError` (`src/crypto_hedge_fund/execution/broker.py:115-120`). `PanelMarketData.open_prices` also rejects missing/invalid requested opens (`src/crypto_hedge_fund/execution/panel.py:88-115`). `tests/unit/test_execution_kernel.py:69-83` covers the missing Jan 2 open. |
| Ledger cash/holdings/equity consistency automated for transition cases | PASS | Only `_execute_rebalance` mutates holdings/cash and emits orders/fills (`src/crypto_hedge_fund/execution/broker.py:218-305`). Equity/weights are recorded from post-fill ledger state (`src/crypto_hedge_fund/execution/broker.py:183-209`). `tests/unit/test_execution_kernel.py:153-193` automates cash-to-asset, no-change, partial rebalance, asset rotation, and liquidation. |
| Cost model charges risky notional exactly and does not charge cash | PASS | `WeightDeltaCostModel` computes chargeable notional as `sum(abs(target_i - pretrade_i)) * nav`; cash is used only for reporting turnover (`src/crypto_hedge_fund/execution/costs.py:117-143`). Tests cover cash-to-asset, asset-to-cash, asset-to-asset rotation, partial rebalance, no-change, and invalid weights (`tests/unit/test_costs.py:20-68`). |
| Invalid weights fail closed | PASS | Target schedules and cost inputs reject non-finite, negative, duplicate, or leveraged risky weights (`src/crypto_hedge_fund/execution/broker.py:47-72`; `src/crypto_hedge_fund/execution/costs.py:70-90`). `tests/unit/test_execution_kernel.py:86-110` and `tests/unit/test_costs.py:61-68` cover failures. |
| Panel-native one/many symbol path | PASS | `PanelMarketData` normalizes long-form `(bar_start_utc, symbol)` data (`src/crypto_hedge_fund/execution/panel.py:45-76`). `SimulatedBroker` operates on schedule columns and holdings symbols without a separate single-asset path. `tests/unit/test_execution_kernel.py:113-150` runs one-symbol and multi-symbol schedules through the same engine. |
| Metrics surface adequate for later levels and not level-specific | PASS_WITH_NOTES | `calculate_performance_metrics` now covers return, ROI, CAGR, volatility, Sharpe, Sortino, downside deviation, Calmar, drawdown, VaR/CVaR, turnover, exposure, cash exposure, costs, concentration/effective N, per-symbol average risky-weight contribution, and benchmark-relative fields (`src/crypto_hedge_fund/metrics/performance.py:104-201`). `tests/unit/test_metrics.py:7-66` covers the surface. Covariance-based risk contribution/correlation diagnostics remain appropriate for later portfolio stages. |
| Benchmark contract cannot be mistaken for broker-costed performance if price-normalized | PASS_WITH_NOTES | `benchmark_open_to_open` returns `benchmark_nav` and `benchmark_return` from open prices only (`src/crypto_hedge_fund/execution/panel.py:117-138`). `tests/unit/test_execution_kernel.py:196-216` names and asserts the helper is price-normalized and has no fee column. Later costed benchmarks should use `SimulatedBroker`. |
| Deterministic outputs and artifact provenance | PASS | Deterministic repeated execution is tested with DataFrame equality (`tests/unit/test_execution_kernel.py:113-150`). Artifact writer attaches provenance columns and metadata sidecars with level, split, data/config/git hashes, period, costs, benchmark, seed, warnings, and optional final-lock hash (`src/crypto_hedge_fund/artifacts/writers.py:18-132`; `tests/unit/test_artifacts.py:9-56`). |
| Typed-record negative tests close attempt 01 gap | PASS | `AgentSignal` validates score, confidence, positive horizon, cutoff ordering, and reason codes (`src/crypto_hedge_fund/types.py:217-240`). `tests/unit/test_types.py:56-90` parametrizes invalid cases for each mandated field. |
| No final-test metrics accessed | PASS | I did not run `make final-test`. `src/crypto_hedge_fund/cli.py:71-84` still fails closed unless `artifacts/final_test_lock.json` exists and even then states the final-test runner is later-stage. Artifact scan found only Stage 2 universe proof files under `artifacts/monitoring`; no strategy final-test metrics/equity/weights/orders/fills were present. |
| No live trading | PASS | Stage 3 execution contains `SimulatedBroker` only. No live order submission adapter was added in `src/crypto_hedge_fund/execution/`. The `ccxt` references are in the Stage 2 public data downloader, not order execution. |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_uv_sync_frozen.log` |
| `make test` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_make_test.log` |
| `uv run pytest tests/unit/test_clock.py tests/unit/test_execution_kernel.py tests/unit/test_costs.py tests/unit/test_metrics.py` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_pytest_clock_execution_costs_metrics.log` |
| `git diff --stat` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_git_diff_stat.log` |
| `git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_git_status_short_branch_untracked.log` |
| Synthetic execution/accounting probe | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_execution_accounting_probe.log` |
| Final-test/live-trading artifact scan | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/arch_final_test_live_scan.log` |

## Test and artifact evidence

- `uv sync --frozen`: passed; 79 packages audited.
- `make test`: passed; 46 tests collected and passed.
- Focused Stage 3 pytest command requested by this review: passed; 18 tests collected and passed.
- Synthetic probe: `build_daily_research_clock("2024-01-01")` returned execution at `2024-01-02T00:00:00+00:00`; the broker produced a Jan 2 buy fill at the Jan 2 open, Jan 1 exposure stayed zero, and missing Jan 2 execution open raised `MissingPriceError`.
- Artifact scan found only Stage 2 monitoring proof artifacts:
  - `artifacts/monitoring/level_5_pair_count_proof.json`
  - `artifacts/monitoring/universe_eligibility_full.csv`
- Fresh `git diff --stat` shows tracked attempt 02 remediation in `clock.py`, `types.py`, `test_clock.py`, and `test_types.py`. The broader Stage 3 kernel remains untracked, so `git status --short --branch --untracked-files=all` is the complete inventory until the team lead stages/commits a passing checkpoint.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None.

- MEDIUM
  - Cost-bearing fully invested risky targets still fail closed if upstream allocation does not reserve cash for fees/slippage. This is acceptable execution-layer behavior and safer than silent leverage, but Stage 4 risk/allocation must reserve a cost buffer or cap risky exposure before broker submission.
  - The current benchmark helper is deliberately price-normalized and not broker-costed. This is now tested and named clearly, but later strategy-level benchmark comparisons must either label this helper as price-only or route benchmark weights through the broker for same-cost comparisons.

- LOW
  - `reports/teamlead/PROJECT_STATE.md` and `reports/teamlead/STAGE_BOARD.md` still describe Stage 3 as attempt 01 / not started. This is control-plane lag, not a kernel defect, but the team lead should update them after deciding this attempt.
  - `src/crypto_hedge_fund/types.py` defines a `CostModel` protocol whose return/signature does not match the concrete `WeightDeltaCostModel` returning `CostBreakdown`. This does not affect runtime tests, but the public typed contract should be reconciled before stricter static typing or external integrations rely on it.
  - Many Stage 3 files remain untracked. Reviewers must use `git status --untracked-files=all`, not only `git diff --stat`, until the stage is checkpointed.

## Unresolved risks and limitations

- Stage 3 intentionally does not implement agents, orchestrator, concrete pre/post risk gates, portfolio optimizers, strategy levels, notebooks, final report, presentation, monitoring, final-test lock, or final-test execution.
- Precision, exchange minimums, participation/capacity, stale valuation windows, partial fills, rejected orders, and conservative stale-holding policy remain later-stage work.
- Metrics now cover the Stage 3 shared scalar surface, but covariance-based portfolio risk contributions, correlation diagnostics, statistical uncertainty, predictive metrics, and system-quality monitoring remain later stages.
- Stage 2 active-market survivorship/delisting limitation remains unchanged and must stay disclosed.
- Final-test exposure remains `NOT_EXPOSED`.

## Recommendation

PASS_WITH_NOTES

Attempt 02 closes the attempt 01 HIGH findings: the clock now matches documented `open(t+1)` semantics, missing next-open execution fails closed, ledger transition probes are automated, risky-notional costs are correct and do not charge cash, mandatory typed-record negative tests exist, metrics are materially expanded, and the price-normalized benchmark helper is explicitly tested as not broker-costed. The remaining issues are integration notes for later stages, not Stage 3 rework blockers.
