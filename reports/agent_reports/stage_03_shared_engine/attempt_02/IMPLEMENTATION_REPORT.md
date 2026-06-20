# Role / stage / attempt

Implementation fixer / Stage 3: Shared Panel-Native Execution Kernel / attempt 02.

## Scope

Remediated the Stage 3 attempt 01 review failures only. Work was limited to the shared clock, typed records, execution-kernel tests, metrics surface/tests, and attempt-02 report/log artifacts. No strategy levels, agents/orchestrator, risk gates, optimizers, notebooks, presentation, final-test code, live trading, commits, tags, or history changes were added.

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
- `reports/teamlead/REQUIREMENTS_STATUS.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/TEAMLEAD_DECISION.md`

## Assumptions and decisions

- Daily bars are UTC open-to-open intervals. The completed bar starting at date `t` ends at the timestamp that is also the open of bar `t+1`; therefore `build_daily_research_clock("2024-01-01")` now produces `execution_time=2024-01-02T00:00:00+00:00`.
- `ResearchClock` now allows `feature_cutoff == decision_time == execution_time` for this daily boundary while still rejecting execution before a completed bar is available.
- The broker already routes schedules through `build_daily_research_clock`, so fixing the clock realigns broker fills without adding a second execution path.
- The Stage 3 benchmark helper remains an explicit price-normalized open-to-open benchmark series, not a broker/costed strategy result. The contract is now tested by name; later strategy benchmarks can still be run through the broker if a costed benchmark is required.
- Metrics are scalar artifact-ready fields. Per-symbol contribution is exposed as clearly named average risky-weight contribution keys, e.g. `average_risky_weight_contribution_btc_usdt`.
- Final-test state remains `NOT_EXPOSED`; `make final-test` was not run.

## Files inspected or changed

Inspected:

- `src/crypto_hedge_fund/clock.py`
- `src/crypto_hedge_fund/types.py`
- `src/crypto_hedge_fund/execution/broker.py`
- `src/crypto_hedge_fund/execution/costs.py`
- `src/crypto_hedge_fund/execution/panel.py`
- `src/crypto_hedge_fund/metrics/performance.py`
- `src/crypto_hedge_fund/artifacts/writers.py`
- `tests/unit/test_clock.py`
- `tests/unit/test_types.py`
- `tests/unit/test_execution_kernel.py`
- `tests/unit/test_costs.py`
- `tests/unit/test_metrics.py`
- `tests/unit/test_artifacts.py`

Changed:

- `src/crypto_hedge_fund/clock.py`
- `src/crypto_hedge_fund/types.py`
- `src/crypto_hedge_fund/metrics/performance.py`
- `tests/unit/test_clock.py`
- `tests/unit/test_types.py`
- `tests/unit/test_execution_kernel.py`
- `tests/unit/test_metrics.py`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/*`

## Deliverables

- Realigned daily clock semantics so a completed bar at date `t` fills at open `t+1`.
- Updated clock and broker tests proving no prior-bar exposure/PnL and preserving explicit missing `open(t+1)` failure.
- Completed the shared Stage 3 metrics surface for return, ROI, CAGR, volatility, Sharpe, Sortino, downside deviation, Calmar, max drawdown, drawdown duration, VaR, CVaR, turnover, exposure, cash exposure, trade count, fees, slippage, total cost, concentration, effective N, per-symbol contribution, and benchmark-relative fields.
- Added mandatory typed-record negative tests for invalid score, confidence, horizon, cutoff ordering, and reason-code values.
- Converted broker ledger transition probes into automated regression tests covering cash-to-asset, no-change, partial rebalance, asset rotation, and liquidation to cash.
- Added a tested benchmark contract showing `benchmark_open_to_open` is a price-normalized open-to-open series starting from the execution open, not a broker/costed result.
- Saved required command logs under the attempt-02 command-log directory.

## Acceptance-criteria mapping

| Criterion | Status | Evidence |
|---|---|---|
| `t` decision fills at open `t+1`, not `t+2` | Implemented and tested | `src/crypto_hedge_fund/clock.py`; `tests/unit/test_clock.py`; `tests/unit/test_execution_kernel.py::test_completed_bar_signal_fills_only_at_next_open_and_has_no_earlier_pnl` |
| Same-close/prior PnL remains impossible | Tested | The Jan 1 completed-bar signal has zero exposure and NAV 1000 on Jan 1; fill occurs on Jan 2; PnL begins after the Jan 2 open in `tests/unit/test_execution_kernel.py` |
| Missing `open(t+1)` fails explicitly | Tested | `tests/unit/test_execution_kernel.py::test_missing_next_open_price_blocks_execution_explicitly` |
| Metrics cover documented Stage 3 surface | Implemented and tested | `src/crypto_hedge_fund/metrics/performance.py`; `tests/unit/test_metrics.py` |
| Typed records reject invalid score, confidence, horizon, cutoff, and reason code | Tested | `tests/unit/test_types.py::test_agent_signal_rejects_invalid_typed_record_fields` |
| Ledger transition probes are automated tests | Tested | `tests/unit/test_execution_kernel.py::test_broker_ledger_transitions_are_consistent_across_rebalance_cases` |
| Benchmark semantics are tested/documented in code/test names | Tested | `tests/unit/test_execution_kernel.py::test_benchmark_series_is_price_normalized_open_to_open_not_a_broker_result` |
| No final-test contamination | Preserved | No `make final-test`; no final-test artifacts or metrics inspected; command log set excludes final-test |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/make_test.log` |
| `uv run pytest tests/unit/test_clock.py tests/unit/test_types.py tests/unit/test_execution_kernel.py tests/unit/test_costs.py tests/unit/test_metrics.py tests/unit/test_artifacts.py` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/pytest_stage3_unit.log` |
| `git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/git_status_short_branch_untracked.log` |

## Test and artifact evidence

- Full suite: `46 passed` via `make test`.
- Focused Stage 3 unit suite: `29 passed`.
- `make lint`: Ruff format check and Ruff check passed.
- `uv sync --frozen`: dependency lock audit passed.
- No final-test command was run and no strategy/final-test metrics were produced.
- Attempt 01 untracked reports/logs were preserved.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None.

- MEDIUM
  - Stage 3 still intentionally fails closed for fully invested risky targets with nonzero costs when the allocator does not reserve cost cash. This behavior is unchanged and should be handled by Stage 4 risk/allocation.
  - Benchmark helper is price-normalized and not a broker/costed result by Stage 3 contract. If later comparisons require costed buy-and-hold, they should submit benchmark weights through `SimulatedBroker`.

- LOW
  - Many Stage 3 attempt 01 files remain untracked, so `git status --untracked-files=all` remains the clearest inventory until the team lead stages/commits a passing checkpoint.

## Unresolved risks and limitations

- Stage 3 does not implement agents, orchestration, pre/post allocation risk gates, portfolio optimizers, strategy levels, notebooks, reports, presentation, monitoring, or final-test lock/final-test execution.
- Precision, exchange minimums, participation/capacity, stale valuation windows, partial fills, and rejected-order modeling remain later-stage work.
- Active-market survivorship/delisting limitations from Stage 2 remain unchanged and must stay disclosed.
- The equality of `feature_cutoff`, `decision_time`, and `execution_time` is specific to daily UTC bars where completed bar close and next bar open share the same timestamp.

## Recommendation

PASS_WITH_NOTES
