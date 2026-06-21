# Role / stage / attempt

Independent architecture/provenance reviewer / Stage 5: Level 1 Validation / attempt 02.

## Scope

Report-only audit of whether attempt 02 closes the attempt 01 provenance/checkpoint rework finding while preserving the Level 1 shared-architecture and research invariants.

Focus areas:

- Required Level 1 validation artifacts and sidecars are checkpoint-safe.
- Artifact provenance honestly records an uncommitted source state through dirty/source-state fields.
- Level 1 remains a one-symbol configuration of the shared agent, risk, broker, ledger, metrics and artifact stack.
- Completed-bar, next-open execution and Stage 4 risk/action resolver path remain intact.
- Validation-only workflow and final-test quarantine remain intact.
- No live trading path is introduced.

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
- `reports/agent_reports/stage_05_level1_validation/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/IMPLEMENTATION_REPORT.md`

Additional implementation and evidence files inspected:

- `.gitignore`
- `configs/default.yaml`
- `configs/fast.yaml`
- `src/crypto_hedge_fund/artifacts/writers.py`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/provenance.py`
- `src/crypto_hedge_fund/experiments/level_1.py`
- `src/crypto_hedge_fund/strategies/sma.py`
- `tests/unit/test_level1_validation.py`
- `tests/unit/test_experiments_validation.py`
- Generated Level 1 validation artifacts under `artifacts/`

## Assumptions and decisions

- I accepted the handoff final-test exposure status as `NOT_EXPOSED` unless contradicted by commands or artifact inspection.
- Running `make experiments-val` is required by the review packet and regenerates Level 1 validation artifacts; I treated those command side effects as gate evidence, not implementation edits.
- A dirty worktree is acceptable for attempt 02 only if artifacts record both `git_worktree_dirty=true` and a deterministic dirty/source-state hash.
- I treated `git_diff_sha256` as a source-state hash because the implementation intentionally excludes generated `artifacts/` and `reports/` from the hash payload.
- I did not implement fixes, commit, tag, run `make final-test`, create a final-test lock, inspect final-test metrics or use any live-trading path.

## Files inspected or changed

Inspected the files listed above plus:

- `artifacts/metrics/level_1.csv`
- `artifacts/metrics/level_1.csv.metadata.json`
- `artifacts/equity/level_1.parquet`
- `artifacts/equity/level_1.parquet.metadata.json`
- `artifacts/weights/level_1.parquet`
- `artifacts/weights/level_1.parquet.metadata.json`
- `artifacts/orders/level_1.parquet`
- `artifacts/orders/level_1.parquet.metadata.json`
- `artifacts/fills/level_1.parquet`
- `artifacts/fills/level_1.parquet.metadata.json`
- `artifacts/figures/level_1_equity_curve.png`
- `artifacts/figures/level_1_equity_curve.png.metadata.json`
- `artifacts/monitoring/level_1_decision_trace.json`

Changed manually only:

- `reports/agent_reports/stage_05_level1_validation/attempt_02/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/arch_uv_sync_frozen.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/arch_make_test.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/arch_make_experiments_val.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/arch_focused_level1_pytest.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/arch_artifact_provenance_inspection.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/arch_git_diff_stat.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/arch_git_status_short_branch_untracked_ignored.log`

Required command side effect:

- `make experiments-val` regenerated the current Level 1 validation artifacts listed above.

## Deliverables

- Independent architecture/provenance review report: this file.
- Required command logs with `arch_*.log` names.
- Artifact/provenance inspection log proving effective Git ignore status and embedded dirty-source provenance.

## Acceptance-criteria mapping

| Criterion | Review result | Evidence |
|---|---|---|
| Attempt 01 checkpoint-safety finding closed | Pass | `.gitignore` now explicitly unignores required Level 1 artifacts and sidecars; effective probe reports `NOT_IGNORED` for all required Level 1 artifact paths. |
| Stage 2 proof exceptions preserved | Pass | `artifacts/monitoring/level_5_pair_count_proof.json` and `artifacts/monitoring/universe_eligibility_full.csv` still exist and remain unignored by the preserved exceptions. |
| Honest source-state provenance | Pass | Metrics, sidecars and trace record `git_worktree_dirty=True` and `git_diff_sha256=387f60845b1de7b78a3ad7c51e54c19a161d39a841d765bdb6f1c6ef787954ee`, matching the current source-state hash from `crypto_hedge_fund.provenance.git_diff_sha256()`. |
| Artifact provenance still identifies commit/config/data | Pass | Artifacts record `git_commit=40d748b27a284ce3c8efa7c0b7204a5608b3904b`, validation period, config hash, data hash, costs, benchmark and warnings. |
| Level 1 uses shared architecture | Pass | `run_level_1_validation(...)` still uses typed SMA agent, `TypedAgentOrchestrator`, pre-risk, `PortfolioProposal`, rebalance policy, post-risk, `resolve_risk_approval_targets(...)` and `SimulatedBroker`. |
| Completed-bar next-open execution preserved | Pass | The Level 1 schedule is built from completed decision bars and executed through the shared broker; tests still cover completed-bar/next-open validation-only behavior. |
| Stage 4 risk/action resolver path preserved | Pass | Level 1 still calls pre-risk, post-risk and `resolve_risk_approval_targets(...)` before broker submission. |
| Validation-only and final-test quarantine | Pass | `make experiments-val` output reports `split=validation` and `final_test_exposure=NOT_EXPOSED`; artifacts cover `2024-01-01` to `2024-12-31`; no final-test lock or final-test metrics were produced. |
| No live trading | Pass | The path uses the simulated broker only; no CEX adapter or order-submission path is enabled. |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/arch_uv_sync_frozen.log` |
| `make test` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/arch_make_test.log` |
| `make experiments-val` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/arch_make_experiments_val.log` |
| `uv run pytest tests/unit/test_level1_validation.py tests/unit/test_experiments_validation.py` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/arch_focused_level1_pytest.log` |
| Artifact/provenance inspection | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/arch_artifact_provenance_inspection.log` |
| `git diff --stat` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/arch_git_diff_stat.log` |
| `git status --short --branch --untracked-files=all --ignored=matching` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/arch_git_status_short_branch_untracked_ignored.log` |

## Test and artifact evidence

- `uv sync --frozen`: passed, audited 79 packages.
- `make test`: passed, 71 tests.
- Focused Level 1 pytest: passed, 5 tests.
- `make experiments-val`: passed; selected SMA fast `30`, slow `100`; reported `split=validation` and `final_test_exposure=NOT_EXPOSED`.
- Metrics from the regenerated validation run:
  - `net_roi`: `1.186110921467134`
  - `net_sharpe`: `1.9535370402802261`
  - `net_max_drawdown`: `-0.20027161004621163`
- Artifact date bounds:
  - equity rows: `366`, `2024-01-01T00:00:00+00:00` to `2024-12-31T00:00:00+00:00`
  - weights rows: `366`, `2024-01-01T00:00:00+00:00` to `2024-12-31T00:00:00+00:00`
  - orders rows: `262`, `2024-01-01T00:00:00+00:00` to `2024-12-31T00:00:00+00:00`
  - fills rows: `262`, `2024-01-01T00:00:00+00:00` to `2024-12-31T00:00:00+00:00`
- Provenance evidence:
  - `split=validation`
  - `period_start=2024-01-01`
  - `period_end=2024-12-31`
  - `git_commit=40d748b27a284ce3c8efa7c0b7204a5608b3904b`
  - `git_worktree_dirty=True`
  - `git_diff_sha256=387f60845b1de7b78a3ad7c51e54c19a161d39a841d765bdb6f1c6ef787954ee`
  - `final_test_lock_hash=None`
  - `benchmark=broker_costed_buy_and_hold`
  - warnings include `validation_only_no_final_test_metrics` and `survivorship_bias_active_markets`
- Effective Git ignore evidence:
  - All required Level 1 artifacts and metadata sidecars exist.
  - All required Level 1 artifacts and metadata sidecars returned `NOT_IGNORED` in the effective `git check-ignore` probe.
- Regenerated artifact hashes from reviewer inspection:
  - metrics: `46487110e7b464cfbe1f2f46d5d9bb84350f0ba0da5a88e91f76a99a99635ebc`
  - equity: `c0872a2fb9de294ede154699e8cd6d36f571352f35f7d3c615332409ee0be280`
  - weights: `2c6a20869a419329e4b5c44bcb9bbc801d20f24e348f0a6cf46734021a341c4c`
  - orders: `3dc31a60526c05f6c243cf12d6d6941c15603e797d28ca8829a590ecfc3614d9`
  - fills: `b0e0b6eb85585be9a83ee2fee4ce427a64f77bf3ce3a21cc9d5621943de9b032`
  - figure: `d7dbeb4d288202bc5f66fdd02244e3681d3879bd450fd9914f48f96d8167406d`
  - trace: `e453c74155a2c8f00fee69731db75e8880c86edb18c45be8222d079c0ea643b5`
- Git evidence:
  - `git diff --stat` shows tracked changes in `.gitignore`, configs, artifact writer, CLI and provenance helper.
  - Full status shows the required Level 1 artifacts and Stage 5 source/test files as untracked rather than ignored.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None.

- MEDIUM
  - None.

- LOW
  - The artifacts now honestly record a dirty source state, which satisfies the attempt 02 remediation packet. The team lead should still checkpoint the accepted source/artifact set and may choose to regenerate artifacts after a clean Stage 5 commit so future reviewers can trace to a clean commit without relying on dirty-source hash reconstruction.
  - `git_worktree_dirty` reports all uncommitted changes, while `git_diff_sha256` intentionally excludes `artifacts/` and `reports/` and therefore represents source state rather than every dirty file. This is documented in code/reporting and is acceptable, but future report wording should keep calling it a source-state hash.

## Unresolved risks and limitations

- Final-test exposure remains `NOT_EXPOSED`; `make final-test` was not run.
- Stage 5 remains Level 1 validation only. Levels 2-5, pretest lock, final-test suite, full notebook, final report and presentation remain future work.
- Active-market survivorship/delisting limitation remains inherited from Stage 2 and is still disclosed in artifact warnings.
- Existing open risks from the team-lead register still apply where relevant, including benchmark labeling discipline for later stages, daily clock wording reconciliation before final methodology freeze, and later Level 5 proof using strategy-level scoring semantics.
- The worktree remains dirty by design pending team-lead checkpoint.

## Recommendation

PASS_WITH_NOTES

Attempt 02 closes the attempt 01 provenance/checkpoint rework finding and preserves the Level 1 shared-architecture, validation-only, next-open, risk-gated and no-live-trading invariants. Only the team lead can pass the stage.
