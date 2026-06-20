# Role / stage / attempt

Replacement independent QA reviewer / Stage 3: Shared Panel-Native Execution Kernel / attempt 02.

## Scope

Report-only QA of Stage 3 attempt 02 remediation. I validated whether attempt 01 HIGH findings were closed and whether the attempt is ready for team-lead gate rerun. I did not implement fixes, commit, tag, run final-test, or inspect final-test metrics.

## Sources read

- `AGENTS.md`
- `MASTER_PROMPT_CODEX_TEAMLEAD.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/ARCHITECTURE_REVIEW.md`

## Assumptions and decisions

- I treated Stage 3 benchmark support as acceptable if its current helper is explicitly price-normalized/open-to-open and tests prevent it from being mistaken for broker-costed benchmark performance.
- I treated `feature_cutoff == decision_time == execution_time` as acceptable for daily UTC bars where the completed bar boundary and next bar open share the same timestamp.
- I did not run `make final-test` and did not inspect final-test returns, rankings, charts, or model outputs. Final-test exposure remains `NOT_EXPOSED` based on command history and current artifact scan.

## Files inspected or changed

Inspected:
- Stage governance/source documents listed above.
- `src/crypto_hedge_fund/clock.py`
- `src/crypto_hedge_fund/types.py`
- `src/crypto_hedge_fund/execution/broker.py`
- `src/crypto_hedge_fund/execution/costs.py`
- `src/crypto_hedge_fund/execution/ledger.py`
- `src/crypto_hedge_fund/execution/panel.py`
- `src/crypto_hedge_fund/metrics/performance.py`
- `src/crypto_hedge_fund/artifacts/writers.py`
- `src/crypto_hedge_fund/cli.py`
- `tests/unit/test_clock.py`
- `tests/unit/test_types.py`
- `tests/unit/test_execution_kernel.py`
- `tests/unit/test_costs.py`
- `tests/unit/test_metrics.py`
- `tests/unit/test_artifacts.py`

Changed:
- `reports/agent_reports/stage_03_shared_engine/attempt_02/QA_REPORT.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/qa_replacement_*.log`

## Deliverables

- Replacement QA report: `reports/agent_reports/stage_03_shared_engine/attempt_02/QA_REPORT.md`
- Command logs: `reports/agent_reports/stage_03_shared_engine/attempt_02/command_logs/qa_replacement_*.log`

## Acceptance-criteria mapping

| Criterion | Status | Evidence |
|---|---:|---|
| `uv sync --frozen` passes | PASS | `qa_replacement_10_uv_sync_frozen.log`, exit 0 |
| `make lint` passes | PASS | `qa_replacement_11_make_lint.log`, exit 0 |
| `make test` passes | PASS | `qa_replacement_12_make_test.log`, 46 passed, exit 0 |
| Focused Stage 3 pytest passes | PASS | `qa_replacement_13_focused_stage3_pytest.log`, 29 passed, exit 0 |
| No BLOCKER/HIGH remains | PASS | No blocker/high findings identified in this review |
| Attempt 01 HIGH 1: `open(t+1)`, no same-close PnL, missing `open(t+1)` fail-closed | PASS | `tests/unit/test_clock.py` asserts Jan 1 bar executes Jan 2; `tests/unit/test_execution_kernel.py:38` asserts fill Jan 2, no Jan 1 exposure/PnL, and PnL only after execution; `tests/unit/test_execution_kernel.py:69` asserts missing next-open raises `MissingPriceError` |
| Attempt 01 HIGH 2: metrics coverage for VaR, CVaR, downside deviation, cash exposure, concentration/effective-N, risk contribution, benchmark-relative metrics | PASS_WITH_NOTES | `src/crypto_hedge_fund/metrics/performance.py` includes VaR/CVaR, downside deviation, cash exposure, concentration HHI, effective N, average per-symbol risky-weight contributions, and benchmark-relative fields; `tests/unit/test_metrics.py` covers these. Covariance-based risk contribution/correlation diagnostics remain later-stage scope. |
| Attempt 01 HIGH 3: typed-record negative tests for score, confidence, horizon, cutoff ordering, reason code | PASS | `tests/unit/test_types.py:59` parametrizes invalid `AgentSignal` cases for all required fields |
| Attempt 01 HIGH 4: ledger transition regression tests | PASS | `tests/unit/test_execution_kernel.py:153` covers cash-to-asset, no-change, partial rebalance, asset rotation, and liquidation ledger states |
| Attempt 01 HIGH 5: benchmark timing/cost convention documented/tested | PASS_WITH_NOTES | `tests/unit/test_execution_kernel.py:196` asserts the benchmark helper starts from execution open, is open-to-open price-normalized, and has no fee column. Later costed benchmarks should route weights through `SimulatedBroker`. |
| Stage 3 stayed within scope | PASS | No strategies, agents/orchestrator implementation, notebooks, presentation, live trading, or final-test execution added by this attempt |
| Final-test exposure remains `NOT_EXPOSED` | PASS | No `make final-test` run; `qa_replacement_17_artifact_file_scan.log` shows only Stage 2 monitoring artifacts |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| Workspace/report path check | 0 | `qa_replacement_00_workspace_check.log` |
| `wc -l` mandatory sources | 0 | `qa_replacement_01_sources_wc.log` |
| `cat` mandatory sources | 0 | `qa_replacement_02_sources_full.log` |
| Invariant scan of mandatory sources with `rg` | 0 | `qa_replacement_03_source_invariant_scan.log` |
| Stage 3 file inventory with `rg --files` | 0 | `qa_replacement_04_repo_inventory_stage3_files.log` |
| Numbered source inspection with `nl -ba` | 0 | `qa_replacement_05_relevant_source_numbered.log` |
| Key source symbol scan with `rg` | 0 | `qa_replacement_06_source_key_scan.log` |
| Numbered focused-test inspection with `nl -ba` | 0 | `qa_replacement_07_relevant_tests_numbered.log` |
| Key focused-test scan with `rg` | 0 | `qa_replacement_08_test_key_scan.log` |
| Timing test excerpt with `nl -ba`/`sed` | 0 | `qa_replacement_09_timing_test_excerpt.log` |
| `uv sync --frozen` | 0 | `qa_replacement_10_uv_sync_frozen.log` |
| `make lint` | 0 | `qa_replacement_11_make_lint.log` |
| `make test` | 0 | `qa_replacement_12_make_test.log` |
| `uv run pytest tests/unit/test_clock.py tests/unit/test_types.py tests/unit/test_execution_kernel.py tests/unit/test_costs.py tests/unit/test_metrics.py tests/unit/test_artifacts.py` | 0 | `qa_replacement_13_focused_stage3_pytest.log` |
| `git diff --stat` | 0 | `qa_replacement_14_git_diff_stat.log` |
| `git status --short --branch --untracked-files=all` | 0 | `qa_replacement_15_git_status.log` |
| Ledger/benchmark test excerpt with `nl -ba`/`sed` | 0 | `qa_replacement_16_ledger_benchmark_test_excerpt.log` |
| Artifact file scan with `find` | 0 | `qa_replacement_17_artifact_file_scan.log` |
| Types protocol excerpt with `nl -ba`/`sed` | 0 | `qa_replacement_18_types_protocol_excerpt.log` |
| Types protocol tail with `nl -ba`/`sed` | 0 | `qa_replacement_19_types_protocol_tail.log` |
| CostModel protocol search with `rg` | 0 | `qa_replacement_20_costmodel_protocol_search.log` |
| CostModel protocol excerpt with `nl -ba`/`sed` | 0 | `qa_replacement_21_costmodel_protocol_excerpt.log` |
| Concrete cost model excerpt with `nl -ba`/`sed` | 0 | `qa_replacement_22_costmodel_concrete_excerpt.log` |
| Final `git status --short --branch --untracked-files=all` after QA report write | 0 | `qa_replacement_23_final_git_status.log` |

## Test and artifact evidence

- `make test`: 46 tests passed in 2.90s.
- Focused Stage 3 pytest: 29 tests passed in 0.40s.
- `git diff --stat` shows tracked remediation in `clock.py`, `types.py`, `test_clock.py`, and `test_types.py`.
- `git status --short --branch --untracked-files=all` shows many Stage 3 implementation/test/report files remain untracked. This is not a kernel failure, but the team lead must account for untracked files before checkpointing.
- Artifact scan found only `artifacts/monitoring/level_5_pair_count_proof.json` and `artifacts/monitoring/universe_eligibility_full.csv`; no Stage 3 strategy/final-test metrics artifacts were present.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None.

- MEDIUM
  - None.

- LOW
  - Many Stage 3 implementation, test, report, and log files are untracked. Reviewers and the team lead must use `git status --untracked-files=all`, not only `git diff --stat`, until a checkpoint is staged/committed.
  - `types.py` defines `CostModel.estimate_from_weight_deltas(...) -> float` while `WeightDeltaCostModel.estimate_from_weight_deltas(...)` returns `CostBreakdown`. Current runtime tests pass and the concrete broker path is unaffected, but the public typing contract should be reconciled before stricter type checking or external integrations rely on it.

## Unresolved risks and limitations

- Fully invested risky targets with nonzero transaction costs still fail closed unless an upstream allocator/risk layer reserves a cash buffer. This is acceptable Stage 3 execution-layer behavior and should be handled in Stage 4 allocation/risk.
- The current benchmark helper is price-normalized and not broker-costed. This is now explicit and tested; later user-facing strategy comparisons requiring costed benchmarks should submit benchmark weights through `SimulatedBroker`.
- Stage 3 intentionally does not implement agents, orchestrator, concrete two-stage risk gates, portfolio optimizers, strategy levels, notebooks, final report, presentation, monitoring, pretest lock, or final-test execution.
- Final-test exposure remains `NOT_EXPOSED`; this QA did not validate final-test behavior.

## Recommendation

PASS_WITH_NOTES

Stage 3 attempt 02 closes the attempt 01 HIGH findings sufficiently for team-lead gate rerun. Remaining notes are low-severity checkpoint/type-contract/later-stage integration risks, not Stage 3 blockers.
