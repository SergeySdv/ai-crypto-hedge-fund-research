# Role / stage / attempt

Independent QA reviewer / Stage 4: Typed Agents, Orchestration, Risk, and Decision Trace / attempt 01.

## Scope

Report-only QA validation of the current working tree against the Stage 4 gate. I inspected the typed agent/orchestrator, aggregation, pre-allocation risk, allocation, post-allocation risk, rebalance and monitoring trace implementation and reran the required commands. I did not implement fixes, commit, tag, access final-test metrics, or run final-test/notebook/presentation workflows.

## Sources read

- `AGENTS.md`
- `MASTER_PROMPT_CODEX_TEAMLEAD.md`
- `docs/02_ARCHITECTURE.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/IMPLEMENTATION_REPORT.md`

## Assumptions and decisions

- Final-test exposure remains `NOT_EXPOSED`; I did not run `make final-test` or inspect final-test returns.
- Stage 4 is allowed to add shared plumbing and tests only; Levels 1-5, experiments, final notebook, presentation and final-test lock remain out of scope.
- Team-lead management document edits in `reports/teamlead/` are treated as control-plane changes, not worker implementation changes.
- I treated the missing explicit `inf` score fixture as a test-evidence note because the implementation uses a non-finite guard that covers both NaN and infinity, and all required gate commands pass.

## Files inspected or changed

Inspected:

- `src/crypto_hedge_fund/types.py`
- `src/crypto_hedge_fund/agents/__init__.py`
- `src/crypto_hedge_fund/agents/aggregate.py`
- `src/crypto_hedge_fund/agents/base.py`
- `src/crypto_hedge_fund/agents/orchestrator.py`
- `src/crypto_hedge_fund/risk/__init__.py`
- `src/crypto_hedge_fund/risk/pre_allocation.py`
- `src/crypto_hedge_fund/risk/post_allocation.py`
- `src/crypto_hedge_fund/portfolio/__init__.py`
- `src/crypto_hedge_fund/portfolio/allocators.py`
- `src/crypto_hedge_fund/portfolio/rebalance.py`
- `src/crypto_hedge_fund/monitoring/__init__.py`
- `src/crypto_hedge_fund/monitoring/trace.py`
- `tests/unit/test_agents_risk.py`
- `tests/unit/test_orchestration.py`
- `tests/unit/test_portfolio_allocation.py`
- `tests/unit/test_monitoring_trace.py`
- `tests/unit/test_types.py`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/IMPLEMENTATION_REPORT.md`

Changed by this QA pass:

- `reports/agent_reports/stage_04_agents_risk/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/qa_uv_sync_frozen.log`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/qa_make_lint.log`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/qa_make_test.log`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/qa_focused_stage4_pytest.log`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/qa_git_diff_stat.log`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/qa_git_status_short_branch_untracked.log`

## Deliverables

- Fresh QA command logs for every required command.
- Independent source/test inspection against Stage 4 invariants.
- This QA report in the required schema.

## Acceptance-criteria mapping

| Criterion | QA result | Evidence |
|---|---:|---|
| Panel-native shared agent/risk layer | PASS | Agent/risk/allocation functions operate on symbol tuples, signal lists/series and panel snapshots. |
| Signal agents cannot place orders or mutate broker/ledger state | PASS | Agents receive only `frame` and immutable `AgentContext`; `test_signal_agents_cannot_mutate_context_or_emit_execution_records` verifies a mutation attempt fails closed and no `OrderIntent`/`Fill` is emitted. |
| At least two agents communicate through orchestrator and trace | PASS | `test_two_concrete_agents_communicate_through_orchestrator_and_trace`; `test_decision_trace_is_notebook_ready_from_agent_to_approval`. |
| Aggregation handles confidence, abstentions, disagreement, cutoffs and reason codes | PASS | `SignalAggregator`, `TypedAgentOrchestrator`, `test_nan_agent_score_fails_closed_as_abstention`, `test_excessive_agent_disagreement_is_reason_coded`, typed cutoff validation in `test_types.py`. |
| Two-stage risk: pre-allocation plus post-allocation validation/veto | PASS | `PreAllocationRiskPolicy` and `PostAllocationRiskPolicy`; focused tests cover both gates. |
| Fail-safe controlled stops are explicit and reason-coded | PASS_WITH_NOTES | Required stop classes are covered; explicit NaN test exists, but no separate explicit infinity fixture. |
| Allocation/risk reserves cash/cost buffer before broker submission | PASS | `PreAllocationRiskPolicy.cost_buffer_weight`; `test_pre_allocation_blocks_low_liquidity_and_reserves_cost_buffer`; `test_equal_weight_allocator_returns_long_only_targets_with_cash_buffer`; trace test asserts cash buffer. |
| No strategies/final-test/notebooks/presentation/live trading | PASS | Source scan found no Stage 4 additions for those surfaces; no final-test command was run. |
| Final-test exposure remains `NOT_EXPOSED` | PASS | Command set excludes final-test; artifact scan shows only prior Stage 2 monitoring proof artifacts. |

Controlled-stop test mapping:

| Required stop | Evidence |
|---|---|
| stale/missing data | `test_pre_allocation_blocks_stale_or_missing_data` |
| NaN/inf score | NaN: `test_nan_agent_score_fails_closed_as_abstention`; infinity is covered by the same `math.isfinite` implementation path but lacks a separate fixture. |
| stale model cutoff | `test_pre_allocation_blocks_stale_model_cutoff` |
| excessive agent disagreement | `test_pre_allocation_blocks_excessive_agent_disagreement`; `test_excessive_agent_disagreement_is_reason_coded` |
| optimizer failure | `test_inverse_volatility_allocator_reports_optimizer_failure_explicitly`; `test_post_allocation_rejects_optimizer_failure` |
| invalid weights | `test_post_allocation_rejects_invalid_weights` |
| drawdown/volatility stop | `test_post_allocation_drawdown_and_volatility_stops_move_to_cash` |
| liquidity/capacity breach | `test_pre_allocation_blocks_low_liquidity_and_reserves_cost_buffer`; `test_post_allocation_capacity_and_reconciliation_fail_closed` |
| reconciliation failure | `test_post_allocation_capacity_and_reconciliation_fail_closed` |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/qa_uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/qa_make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/qa_make_test.log` |
| `uv run pytest tests/unit/test_agents_risk.py tests/unit/test_orchestration.py tests/unit/test_portfolio_allocation.py tests/unit/test_monitoring_trace.py` | 0 | `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/qa_focused_stage4_pytest.log` |
| `git diff --stat` | 0 | `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/qa_git_diff_stat.log` |
| `git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/qa_git_status_short_branch_untracked.log` |

## Test and artifact evidence

- `uv sync --frozen`: audited 79 packages.
- `make lint`: Ruff format check reported 50 files already formatted; Ruff check passed.
- `make test`: 62 tests passed in 2.81s.
- Focused Stage 4 pytest: 16 tests passed in 0.25s.
- `git diff --stat`: tracked diffs currently include `reports/teamlead/PROJECT_STATE.md`, `reports/teamlead/STAGE_BOARD.md` and `src/crypto_hedge_fund/types.py`.
- `git status --short --branch --untracked-files=all`: current branch `main`; HEAD is `b1f3f0f` tagged `stage/03-shared-engine`; Stage 4 source/tests/reports are untracked pending lead review/commit.
- Artifact scan found only prior Stage 2 monitoring proof artifacts under `artifacts/`; no strategy metrics, final-test outputs, notebooks or presentation artifacts were created by this QA pass.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None.

- MEDIUM
  - None.

- LOW
  - The controlled-stop test evidence has an explicit NaN score fixture but no separate explicit infinity score fixture. The implementation path uses `math.isfinite` and should fail closed for both, but the Stage 4 required-check wording asks for `NaN/inf score` test evidence.
  - The current working tree is not checkpointed: Stage 4 source/test/report files are untracked, and `types.py` plus team-lead control docs are modified. This is expected before team-lead integration, but it should be resolved during the gate rerun/checkpoint.

## Unresolved risks and limitations

- Stage 4 allocators are foundation allocators only; minimum-variance and robust portfolio methods remain future-stage work behind the same interface.
- Capacity breach is currently explicit proposal metadata and liquidity caps; later stages still need actual ADV/AUM participation calculations.
- Stage 4 does not implement Levels 1-5, validation experiments, pretest lock, final-test execution, final notebook, final report or presentation.
- The Stage 2 active-market survivorship/delisting limitation and Stage 3 benchmark-labeling note remain unchanged.

## Recommendation

PASS_WITH_NOTES
