# Role / stage / attempt

Independent architecture/risk reviewer / Stage 4: Typed Agents, Orchestration, Risk, and Decision Trace / attempt 01.

## Scope

Report-only audit of whether the Stage 4 attempt preserves the global architecture and risk invariants needed for later Levels 1-5 to run through the shared Stage 3 broker, ledger, cost model and execution clock.

I did not implement fixes, commit, tag, run final-test, inspect final-test strategy metrics, add live trading code, or edit implementation files.

Final-test exposure status: `NOT_EXPOSED`.

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
- `reports/teamlead/RISK_REGISTER.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/IMPLEMENTATION_REPORT.md`

## Assumptions and decisions

- Stage 4 is an architecture/risk foundation only. It is not expected to implement Levels 1-5, final-test lock, notebooks, presentation, strategy experiments, or live trading.
- Stage 3 is the accepted execution baseline at commit `b1f3f0f` / tag `stage/03-shared-engine`.
- The review standard is the global invariant set, not only whether the Stage 4 unit tests pass.
- The Stage 4 safe-fallback records are acceptable for this stage if later integration treats `RiskApproval.action` as authoritative and does not infer behavior from the `approved` boolean alone.

## Files inspected or changed

Inspected:

- `src/crypto_hedge_fund/types.py`
- `src/crypto_hedge_fund/agents/base.py`
- `src/crypto_hedge_fund/agents/aggregate.py`
- `src/crypto_hedge_fund/agents/orchestrator.py`
- `src/crypto_hedge_fund/risk/pre_allocation.py`
- `src/crypto_hedge_fund/risk/post_allocation.py`
- `src/crypto_hedge_fund/portfolio/allocators.py`
- `src/crypto_hedge_fund/portfolio/rebalance.py`
- `src/crypto_hedge_fund/monitoring/trace.py`
- `tests/unit/test_agents_risk.py`
- `tests/unit/test_orchestration.py`
- `tests/unit/test_portfolio_allocation.py`
- `tests/unit/test_monitoring_trace.py`
- required governance and prior-stage reports listed above

Changed:

- `reports/agent_reports/stage_04_agents_risk/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_uv_sync_frozen.log`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_make_test.log`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_focused_stage4_pytest.log`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_git_diff_stat.log`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_git_status_short_branch_untracked.log`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_final_test_live_scan.log`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_stage4_file_inventory.log`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_stage4_symbol_scan.log`

## Deliverables

- This architecture/risk review report.
- Required command logs under `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_*.log`.

## Acceptance-criteria mapping

| Criterion | Status | Evidence |
|---|---:|---|
| Panel-native architecture preserved | PASS | Agent/risk/allocation APIs accept tuples/series/dataframes keyed by symbols; one-symbol tests use same contracts as multi-symbol tests. |
| Signal agents only emit typed messages | PASS | Agents return `AgentSignal`; they are not passed broker/ledger objects. Mutation attempt fails against immutable context in `test_signal_agents_cannot_mutate_context_or_emit_execution_records`. |
| Orchestrator uses typed messages and preserves cutoffs/reasons | PASS_WITH_NOTE | `TypedAgentOrchestrator` validates `AgentSignal`, converts malformed/failing output to abstention, emits events and aggregates reasons. Clock strictness note below. |
| Agent outputs include score, confidence, horizon, cutoffs, reason codes | PASS | `AgentSignal` runtime validation in `types.py`; focused orchestration tests cover concrete agents and invalid score. |
| Abstentions and model failures fail closed | PASS | Invalid/NaN agent output becomes `(abstain, invalid_data)`; thrown agent errors become `(abstain, model_failure)`. |
| Pre-allocation risk gate present | PASS | `PreAllocationRiskPolicy` blocks kill switch, missing/stale data, stale model, low liquidity and excessive disagreement, and emits typed constraints. |
| Post-allocation risk gate present | PASS | `PostAllocationRiskPolicy` validates candidate weights and handles optimizer failure, invalid weights, blocked symbols, drawdown/volatility, turnover, capacity and reconciliation stops. |
| Risk can cap, block, freeze or move to cash | PASS_WITH_NOTE | Blocks and caps are explicit; prior-weights and cash actions exist. Downstream action semantics must be preserved. |
| Allocation/risk reserves cash/cost buffer before broker | PASS | Pre-risk reduces max gross exposure by `cost_buffer_weight`; post-risk enforces `min_cash_buffer`. |
| Controlled stop scenarios exist | PASS | Tests cover stale data, invalid score, stale model cutoff, disagreement, optimizer failure, invalid weights, drawdown/volatility, capacity and reconciliation failures. |
| Decision trace is notebook-ready | PASS | `DecisionTrace`, `MonitoringEvent`, `merge_decision_trace`, `trace_to_frame`; test covers agent-to-approval trace. |
| Stage 4 does not implement strategies/final-test/notebook/presentation/live trading | PASS | Source scan and artifact inventory found no Stage 4 strategy/final-test outputs or live order adapter additions. |
| Final-test exposure remains `NOT_EXPOSED` | PASS | Did not run `make final-test`; no final-test lock or metrics artifacts found. |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_uv_sync_frozen.log` |
| `make test` | 0 | `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_make_test.log` |
| `uv run pytest tests/unit/test_agents_risk.py tests/unit/test_orchestration.py tests/unit/test_portfolio_allocation.py tests/unit/test_monitoring_trace.py` | 0 | `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_focused_stage4_pytest.log` |
| `git diff --stat` | 0 | `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_git_diff_stat.log` |
| `git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_git_status_short_branch_untracked.log` |
| `rg -n "final-test\|final_test\|final test\|2025\|live order\|submit_order\|create_order\|privateKey\|apiKey\|secret\|CEXBroker\|paper\|notebook\|presentation" ...` | 0 | `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_final_test_live_scan.log` |
| Stage 4 file inventory | 0 | `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_stage4_file_inventory.log` |
| Stage 4 symbol/reason-code scan | 0 | `reports/agent_reports/stage_04_agents_risk/attempt_01/command_logs/arch_stage4_symbol_scan.log` |

## Test and artifact evidence

- `uv sync --frozen`: PASS, audited 79 packages.
- `make test`: PASS, 62 tests passed.
- Focused Stage 4 pytest: PASS, 16 tests passed.
- Existing artifacts remain limited to Stage 2 monitoring proof files:
  - `artifacts/monitoring/level_5_pair_count_proof.json`
  - `artifacts/monitoring/universe_eligibility_full.csv`
- No `artifacts/final_test_lock.json`, final-test metrics, strategy-level outputs, notebook, presentation, or live trading deliverable was created by Stage 4.
- Current Git HEAD remains `b1f3f0f` on `main`, tagged `stage/03-shared-engine`.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None.

- MEDIUM
  - Safe fallback execution semantics need an explicit downstream contract before strategy integration. `PostAllocationRiskPolicy` represents move-to-cash and preserve-prior-weights fallbacks as `RiskApproval(approved=False, action="cash"|"prior_weights", ...)`. This is acceptable as a typed risk result, but later order-generation integration must route by `action`, not simply skip all approvals where `approved` is false. Otherwise a drawdown/volatility/capacity/reconciliation stop could accidentally become "do nothing" instead of the intended cash or freeze action. Evidence: `src/crypto_hedge_fund/risk/post_allocation.py`.

- LOW
  - Clock strictness should be reconciled before Levels 1-5. The interface docs say `fit_cutoff <= feature_cutoff <= decision_time < execution_time`, while `ResearchClock` currently allows `decision_time == execution_time`, and Stage 4 tests use equality at the daily bar boundary. This did not expose final-test data or break current tests, but the project should document whether equality is allowed for bar-close/next-open boundary timestamps or enforce strict separation with a distinct decision timestamp. Evidence: `src/crypto_hedge_fund/types.py`, `tests/unit/test_orchestration.py`, `tests/unit/test_agents_risk.py`, `tests/unit/test_portfolio_allocation.py`.
  - Stage 4 allocators are foundation methods only. Equal-weight and inverse-volatility are present behind the shared interface; minimum-variance and robust portfolio methods remain later-stage work and should reuse the same `PortfolioAllocator` contract.
  - Worktree state includes modified `reports/teamlead/PROJECT_STATE.md` and `reports/teamlead/STAGE_BOARD.md` plus untracked Stage 4 files from the worker attempt. This is not an architecture blocker, but the team lead should decide which control-plane edits belong in the Stage 4 checkpoint.

## Unresolved risks and limitations

- Stage 4 has not yet integrated risk approvals into a full broker order-generation loop. That belongs to later strategy/backtest stages, but the action semantics noted above should be pinned before execution integration.
- Capacity checks are currently explicit metadata/constraint plumbing, not full ADV/AUM participation calculations from real rolling liquidity. Later Levels 4-5 must connect this to the data layer.
- The accepted Stage 2 active-market survivorship/delisting limitation remains unchanged.
- Stage 4 does not implement model training, validation selection, final-test lock, notebook, report, deck, or any Level 1-5 strategy artifacts.
- QA is running separately; this report is an independent architecture/risk review, not the team-lead stage decision.

## Recommendation

PASS_WITH_NOTES

The Stage 4 attempt is coherent with the shared architecture and risk-control direction. It adds typed agent interaction, orchestration, two-stage risk, safe stops, allocation plumbing, and decision trace surfaces without final-test exposure or live-trading expansion. The team lead should require the fallback-action and clock-boundary notes to be resolved or explicitly documented before connecting Stage 4 outputs to strategy experiment execution.
