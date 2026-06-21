# Role / stage / attempt

Independent architecture/leakage reviewer / Stage 5: Level 1 validation / attempt 01.

## Scope

Report-only audit of whether the Level 1 validation implementation preserves the global shared architecture and research protocol.

Focus areas:

- Level 1 as a one-symbol configuration of the shared engine.
- No standalone single-asset backtester or notebook-only path.
- Completed-bar SMA signal and next-open execution via the Stage 3 broker.
- Stage 4 typed agent, orchestration, pre-risk, post-risk and risk-action resolution path.
- Validation-only artifacts and no final-test exposure.
- Frozen included data only for the default validation run.
- Risky-notional cost accounting, net-primary metrics and broker-costed benchmark.
- Artifact provenance and reproducibility labels.
- No live trading.

## Sources read

- `AGENTS.md`
- `MASTER_PROMPT_CODEX_TEAMLEAD.md`
- `docs/01_ASSIGNMENT_AND_SCOPE.md`
- `docs/02_ARCHITECTURE.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/teamlead/RISK_REGISTER.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_04_agents_risk/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/IMPLEMENTATION_REPORT.md`

Additional implementation files inspected:

- `Makefile`
- `configs/default.yaml`
- `configs/fast.yaml`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/clock.py`
- `src/crypto_hedge_fund/agents/orchestrator.py`
- `src/crypto_hedge_fund/agents/aggregate.py`
- `src/crypto_hedge_fund/artifacts/writers.py`
- `src/crypto_hedge_fund/execution/broker.py`
- `src/crypto_hedge_fund/execution/panel.py`
- `src/crypto_hedge_fund/experiments/level_1.py`
- `src/crypto_hedge_fund/portfolio/allocators.py`
- `src/crypto_hedge_fund/portfolio/rebalance.py`
- `src/crypto_hedge_fund/risk/pre_allocation.py`
- `src/crypto_hedge_fund/risk/post_allocation.py`
- `src/crypto_hedge_fund/strategies/sma.py`
- `tests/unit/test_level1_validation.py`
- `tests/unit/test_experiments_validation.py`

## Assumptions and decisions

- The stated final-test exposure status is accepted as `NOT_EXPOSED` unless contradicted by commands or artifact/source inspection.
- Validation may use 2024 outcomes to select Level 1 SMA windows because this is a validation-only stage. These selected choices must later be frozen before final-test execution.
- The inherited daily-boundary convention `decision_time == execution_time == next open` remains an accepted Stage 4 risk. It does not create same-close fills because the completed bar is `2023-12-31` and the first fill is at the `2024-01-01` open.
- The local Level 1 binary allocator is treated as a low-risk one-symbol allocation rule because it still emits `PortfolioProposal` and passes through post-risk and `resolve_risk_approval_targets(...)` before broker submission.
- I did not run `make final-test`, inspect final-test metrics, create a final-test lock, commit, tag or edit implementation code.

## Files inspected or changed

Inspected the files listed above plus generated Level 1 artifacts under:

- `artifacts/metrics/level_1.csv`
- `artifacts/equity/level_1.parquet`
- `artifacts/weights/level_1.parquet`
- `artifacts/orders/level_1.parquet`
- `artifacts/fills/level_1.parquet`
- `artifacts/figures/level_1_equity_curve.png`
- `artifacts/monitoring/level_1_decision_trace.json`

Changed only:

- `reports/agent_reports/stage_05_level1_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/arch_uv_sync_frozen.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/arch_make_test.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/arch_make_experiments_val.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/arch_focused_level1_pytest.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/arch_git_diff_stat.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/arch_git_status_short_branch_untracked.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/arch_artifact_evidence.log`

## Deliverables

- Independent architecture/leakage review report: this file.
- Required command logs using `arch_*.log`.
- Additional reviewer artifact-evidence log: `command_logs/arch_artifact_evidence.log`.

## Acceptance-criteria mapping

| Criterion | Review result | Evidence |
|---|---|---|
| Level 1 is one-symbol configuration of shared architecture | Pass | `run_level_1_validation(...)` builds a `PanelMarketData`, typed SMA agent, `TypedAgentOrchestrator`, pre-risk constraints, `PortfolioProposal`, rebalance decision, post-risk approval, risk-action resolution and `SimulatedBroker` run. |
| No standalone backtester | Pass | Execution and benchmark both call `SimulatedBroker.run(...)`; tests monkeypatch the shared broker and require it to be used. |
| Completed-bar signal, next-open execution | Pass | Target schedule index is the completed bar; broker maps schedule rows through `build_daily_research_clock(...)` to execution opens. First trace uses bar start `2023-12-31`, feature cutoff `2024-01-01`, execution `2024-01-01`. |
| Stage 4 risk/action resolver path | Pass | Level 1 calls `PreAllocationRiskPolicy`, `PostAllocationRiskPolicy` and `resolve_risk_approval_targets(...)` before broker submission. |
| Validation-only, no final-test selection | Pass | Runner refuses `validation_end >= test_start`, loads rows only through validation end, outputs `split=validation`, and `artifacts/final_test_lock.json` is absent. |
| Frozen included data only | Pass | Default `make experiments-val` reads configured local `data/processed/ohlcv_daily.parquet`; no downloader or live network path is used by the experiment command. |
| Costs from risky notional, net primary | Pass | Stage 3 broker/cost model is used. Metrics contain unprefixed net fields, `net_*`, `gross_*`, total costs and broker-costed buy-and-hold benchmark. |
| Provenance-labeled artifacts | Pass | Artifacts include split, period, data/config/git hashes, cost assumptions, benchmark, seed, warnings and empty final-lock hash. |
| No live trading | Pass | Stage 5 Level 1 path uses only `SimulatedBroker`; final-test remains fail-closed without a lock. No live order-submission API is used. |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/arch_uv_sync_frozen.log` |
| `make test` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/arch_make_test.log` |
| `make experiments-val` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/arch_make_experiments_val.log` |
| `uv run pytest tests/unit/test_level1_validation.py tests/unit/test_experiments_validation.py` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/arch_focused_level1_pytest.log` |
| `git diff --stat` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/arch_git_diff_stat.log` |
| `git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/arch_git_status_short_branch_untracked.log` |

Additional read-only/evidence command:

| Command | Exit status | Evidence/log |
|---|---:|---|
| Artifact evidence probe | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/arch_artifact_evidence.log` |

## Test and artifact evidence

- `uv sync --frozen`: passed, audited 79 packages.
- `make test`: passed, 70 tests.
- Focused Level 1 tests: passed, 4 tests.
- `make experiments-val`: passed and wrote Level 1 validation artifacts.
- Selected validation SMA windows: fast `30`, slow `100`.
- Metrics evidence:
  - `net_roi`: `1.186110921467134`
  - `net_sharpe`: `1.953537040280226`
  - `net_max_drawdown`: `-0.2002716100462116`
  - `gross_roi`: `1.1991902392661182`
  - `gross_to_net_total_return_decay`: `0.0130793177989843`
- Artifact bounds:
  - equity rows: `366`, timestamps `2024-01-01T00:00:00+00:00` to `2024-12-31T00:00:00+00:00`
  - weights rows: `366`, timestamps `2024-01-01T00:00:00+00:00` to `2024-12-31T00:00:00+00:00`
  - orders rows: `262`, timestamps `2024-01-01T00:00:00+00:00` to `2024-12-31T00:00:00+00:00`
  - fills rows: `262`, timestamps `2024-01-01T00:00:00+00:00` to `2024-12-31T00:00:00+00:00`
- Provenance evidence:
  - split: `validation`
  - period: `2024-01-01` to `2024-12-31`
  - benchmark: `broker_costed_buy_and_hold`
  - git commit recorded: `40d748b27a284ce3c8efa7c0b7204a5608b3904b`
  - data hash: `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`
  - config hash: `0ac673b154e14619aeb516523913f3ff479e688b67a25c247fee1cef810bd2e1`
  - final-test lock hash: `None` in sidecars/trace, blank repeated provenance column in parquet artifacts
  - warnings include `validation_only_no_final_test_metrics` and `survivorship_bias_active_markets`
- Decision trace evidence:
  - signal agent: `sma_crossover`
  - representative completed bar: `2023-12-31T00:00:00+00:00`
  - feature cutoff: `2024-01-01T00:00:00+00:00`
  - execution time: `2024-01-01T00:00:00+00:00`
  - resolved action: `approve`
  - constraints and approval objects are present
  - selection block records `candidate_count=9`
- Git evidence:
  - `HEAD`: `40d748b27a284ce3c8efa7c0b7204a5608b3904b`, tag `stage/04-agents-risk`
  - tracked diff stat from required command: `configs/default.yaml`, `configs/fast.yaml`, `src/crypto_hedge_fund/cli.py`
  - full status log also shows untracked Level 1 experiment/strategy modules, tests, implementation report and command logs.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None.

- MEDIUM
  - Inherited active-market survivorship/delisting limitation remains open. The Stage 5 artifacts disclose `survivorship_bias_active_markets`, and this is already recorded in the team-lead risk register. It is acceptable for this Level 1 validation slice, but must remain prominent in later reports/deck/notebook and must not be represented as a true delisted-inclusive point-in-time universe.

- LOW
  - Level 1 defines a local `_BinarySignalAllocator` inside `src/crypto_hedge_fund/experiments/level_1.py` even though `EqualWeightAllocator` exists in the shared portfolio package and would be equivalent for one eligible symbol under the same risk caps. This does not bypass risk or execution, but moving this rule into the shared portfolio layer before later levels would reduce the chance of allocation-path drift.
  - The daily clock still records `decision_time == execution_time == next open`, matching the accepted Stage 4 convention but not the stricter wording in some architecture text that says `decision_time < execution_time`. This is not leakage in the current implementation because the signal bar is already complete and the fill is at the next open.
  - Required `git diff --stat` does not include untracked implementation files. The separate required `git status --short --branch --untracked-files=all` log captures those files.

## Unresolved risks and limitations

- Final-test exposure remains `NOT_EXPOSED`; later stages must keep quarantine until all five validation levels are implemented and frozen.
- Level 1 validation chooses SMA windows on validation and reports selected validation metrics. This is valid for Stage 5, but these results are not independent final-test evidence.
- Levels 2-5, pretest freeze, final-test suite, full notebook, final report and presentation are not part of this attempt.
- Existing Stage 3/4 open risks remain relevant: benchmark labeling discipline for later stages, public typing cleanup around cost model protocol, capacity integration for later levels, and daily clock wording reconciliation before methodology freeze.
- The generated artifacts are under `artifacts/`; repository ignore/unignore policy for required strategy artifacts should be verified by the team lead before checkpointing.

## Recommendation

PASS_WITH_NOTES

The Level 1 validation implementation preserves the shared engine and research protocol for this stage. I found no blocker or high-severity architecture/leakage issues. Only the team lead can pass the stage.
