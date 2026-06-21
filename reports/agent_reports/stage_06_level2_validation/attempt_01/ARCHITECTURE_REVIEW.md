# Role / stage / attempt

Independent modeling/leakage architecture reviewer / Stage 6: Level 2 validation implementation / attempt 01.

## Scope

Report-only audit of Stage 6 attempt 01 for Level 2 modeling methodology, leakage safety, shared-architecture consistency, artifact reproducibility and final-test quarantine.

Focus areas:

- Causal feature/target alignment for completed-bar features and next-open execution.
- Temporal train/validation split, walk-forward fitting and fit-audit evidence.
- Meaningful econometric, ML and interacting-agent behavior.
- Continued use of the Stage 3 broker/ledger/cost engine and Stage 4 two-stage risk path.
- Validation-only robustness artifacts.
- Checkpoint-safe required Level 2 artifacts.
- Final-test state remaining `NOT_EXPOSED`.

## Sources read

- `AGENTS.md`
- `MASTER_PROMPT_CODEX_TEAMLEAD.md`
- `docs/02_ARCHITECTURE.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `docs/11_REQUIREMENTS_TRACEABILITY.md`
- `docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/teamlead/PROJECT_STATE.md`
- `reports/teamlead/RISK_REGISTER.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_04_agents_risk/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/IMPLEMENTATION_REPORT.md`

Additional implementation and evidence inspected:

- `.gitignore`
- `configs/default.yaml`
- `configs/fast.yaml`
- `src/crypto_hedge_fund/agents/aggregate.py`
- `src/crypto_hedge_fund/agents/level2.py`
- `src/crypto_hedge_fund/agents/orchestrator.py`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/experiments/level_2.py`
- `src/crypto_hedge_fund/features/level2.py`
- `src/crypto_hedge_fund/models/econometric.py`
- `src/crypto_hedge_fund/models/ml.py`
- `src/crypto_hedge_fund/risk/pre_allocation.py`
- `src/crypto_hedge_fund/risk/post_allocation.py`
- `tests/unit/test_level2_validation.py`
- Generated Level 2 artifacts under `artifacts/`

## Assumptions and decisions

- I accepted the stage base as `4719e135667647ec595964581745f6822eb40be9` / `stage/05-level-1`; the current branch is `main`.
- I did not run `make final-test`, create a final-test lock, inspect final-test metrics, commit, tag, or edit implementation/config/data/artifact files.
- I did not rerun `make experiments-val` because this review scope forbids implementation/config/data/artifact edits and the command regenerates artifacts. I inspected existing Level 2 artifacts and ran tests/probes only.
- I treated validation artifacts that cover 2024 and have `final_test_lock_hash=None` as compatible with final-test quarantine unless contradicted by logs or source scans.

## Files inspected or changed

Inspected the files listed above plus:

- `artifacts/metrics/level_2.csv`
- `artifacts/metrics/level_2.csv.metadata.json`
- `artifacts/equity/level_2.parquet`
- `artifacts/equity/level_2.parquet.metadata.json`
- `artifacts/weights/level_2.parquet`
- `artifacts/orders/level_2.parquet`
- `artifacts/fills/level_2.parquet`
- `artifacts/figures/level_2_equity_curve.png`
- `artifacts/monitoring/level_2_decision_trace.json`
- `artifacts/monitoring/level_2_robustness.json`
- `artifacts/monitoring/level_2_model_predictions.parquet`
- `artifacts/monitoring/level_2_fit_audit.parquet`

Changed manually only:

- `reports/agent_reports/stage_06_level2_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/arch_uv_sync_frozen.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/arch_pytest_level2_validation.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/arch_make_test.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/arch_git_status.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/arch_git_check_ignore_level2.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/arch_final_quarantine_scan.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/arch_final_quarantine_scan_all.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/arch_source_level2_features_numbered.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/arch_source_level2_experiment_numbered.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/arch_gitignore_numbered.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/arch_artifact_probe.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/arch_artifact_probe_columns.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/arch_fit_cadence_probe.log`

## Deliverables

- Independent architecture/modeling review report: this file.
- Command logs and probes under `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/arch_*.log`.

## Acceptance-criteria mapping

| Criterion | Review result | Evidence |
|---|---|---|
| Features and labels are causally aligned | Pass | `features/level2.py` creates `feature_cutoff=bar_end_utc`, `execution_time=bar_start+1d`, `future_open_time=bar_start+2d`, and `forward_return=open(t+2)/open(t+1)-1`; focused test and artifact fit audit show no future-label flags. |
| No future-open leakage into model features/training selection | Pass | ML and econometric training rows are filtered with `label_observation_time < execution_time`; artifact probe shows `fit_audit_future_label_flags 0` and all non-null `fit_cutoff < execution_time`. |
| Temporal train/validation and monthly expanding refit | Partial | ML models have 12 unique monthly fit cutoffs. Econometric model has 365 unique fit cutoffs in 2024, so it is causal but not monthly despite the trace wording saying monthly refit. |
| Econometric expected-return and GARCH volatility | Pass with note | `models/econometric.py` fits AutoReg expected return and `arch_garch_1_1` when available, with deterministic GARCH-style fallback. Generated econometric predictions have 365 `ok` rows and nonzero forecast volatility metadata. |
| Logistic Regression and HistGradientBoosting/equivalent | Pass | `models/ml.py` defines scikit-learn pipelines for Logistic Regression with imputer/scaler and HistGradientBoostingClassifier, using causal expanding folds. |
| At least two agents communicate through typed orchestrator | Pass | Level 2 ensemble trace contains `sma_crossover`, `econometric_ar_garch`, `ml_logistic`, and `ml_hist_gradient_boosting` signals plus aggregate contributions. |
| Stage 4 risk path not bypassed | Pass | `build_level_2_target_schedule(...)` uses `TypedAgentOrchestrator`, `PreAllocationRiskPolicy`, allocator proposal, rebalance policy, `PostAllocationRiskPolicy`, `resolve_risk_approval_targets(...)`, then `SimulatedBroker`. |
| Signal agents cannot place orders/mutate ledger | Pass | Level 2 agents emit `AgentSignal` rows from feature/prediction tables; order/fill generation remains inside `SimulatedBroker`. |
| Robustness checks are validation-only artifacts | Pass with limitation | `level_2_robustness.json` includes real block bootstrap and circular-shift calculations with 1,000 repetitions each. Multiple-seed evidence is limited because first seed drives trading artifacts. |
| Benchmark/trading metrics use shared broker/cost conventions | Pass | Benchmark metadata is `broker_costed_buy_and_hold`; metrics have gross and net fields, and all approaches route through `SimulatedBroker` with the same validation window. |
| Required artifacts are persisted and checkpoint-safe | Fail | Level 2 artifact files exist, but effective `git check-ignore` shows they are ignored by `.gitignore`. |
| Final-test quarantine remains intact | Pass | No `make final-test` was run by this reviewer; existing Stage 6 logs report `final_test_exposure=NOT_EXPOSED`; artifacts are validation-labeled with `final_test_lock_hash=None` and period `2024-01-01` to `2024-12-31`. |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `command_logs/arch_uv_sync_frozen.log` |
| `uv run pytest tests/unit/test_level2_validation.py` | 0 | `command_logs/arch_pytest_level2_validation.log` |
| `make test` | 0 | `command_logs/arch_make_test.log` |
| `git status --short --branch --untracked-files=all --ignored=matching` | 0 | `command_logs/arch_git_status.log` |
| Level 2 artifact/provenance probe | 0 | `command_logs/arch_artifact_probe.log`, `command_logs/arch_artifact_probe_columns.log` |
| Level 2 fit cadence probe | 0 | `command_logs/arch_fit_cadence_probe.log` |
| `git check-ignore` for Level 2 artifacts | 0, paths ignored | `command_logs/arch_git_check_ignore_level2.log` |
| Final-test/quarantine text scan including ignored artifacts | 0 | `command_logs/arch_final_quarantine_scan_all.log` |
| Numbered source snapshots for findings | 0 | `command_logs/arch_source_level2_features_numbered.log`, `command_logs/arch_source_level2_experiment_numbered.log`, `command_logs/arch_gitignore_numbered.log` |

## Test and artifact evidence

- Focused Level 2 suite: 4 passed.
- Full test suite: 75 passed.
- Level 2 metrics artifact:
  - shape: 5 rows, 119 columns;
  - approaches: `technical_sma`, `econometric_ar_garch`, `ml_logistic`, `ml_hist_gradient_boosting`, `agent_ensemble`;
  - selected approach: `agent_ensemble`;
  - provenance split: `validation`;
  - provenance period: `2024-01-01` to `2024-12-31`;
  - benchmark: `broker_costed_buy_and_hold`;
  - final-test lock hash: all null.
- Artifact date bounds:
  - equity: `2024-01-01T00:00:00+00:00` to `2024-12-31T00:00:00+00:00`;
  - weights: `2024-01-01T00:00:00+00:00` to `2024-12-31T00:00:00+00:00`;
  - orders/fills: `2024-01-01T00:00:00+00:00` to `2024-12-30T00:00:00+00:00`.
- Prediction/audit evidence:
  - prediction rows: 1,095;
  - fit-audit rows: 2,555;
  - fit-audit models: `econometric_ar_garch`, `ml_hist_gradient_boosting`, `ml_logistic`;
  - future-label flags: 0;
  - all non-null fit cutoffs are before execution time.
- Representative trace evidence:
  - agents: `sma_crossover`, `econometric_ar_garch`, `ml_logistic`, `ml_hist_gradient_boosting`;
  - aggregate includes per-agent contributions and disagreement;
  - pre-risk reason codes: `ok`;
  - post-risk action: `approve`.
- Robustness evidence:
  - block bootstrap repetitions: 1,000;
  - circular-shift repetitions: 1,000;
  - configured seeds recorded: `[7, 42, 137]`;
  - trading artifacts use the first seed only, as stated in the robustness payload.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - Required Level 2 validation artifacts are ignored by Git. The required files exist under `artifacts/`, but `.gitignore` only unignores Level 1 artifacts and Stage 2 proof files. Effective `git check-ignore` reports ignored status for `artifacts/metrics/level_2.csv`, `artifacts/equity/level_2.parquet`, `artifacts/weights/level_2.parquet`, `artifacts/orders/level_2.parquet`, `artifacts/fills/level_2.parquet`, `artifacts/figures/level_2_equity_curve.png`, `artifacts/monitoring/level_2_decision_trace.json`, `artifacts/monitoring/level_2_robustness.json`, `artifacts/monitoring/level_2_model_predictions.parquet`, and `artifacts/monitoring/level_2_fit_audit.parquet`. This violates the required artifact contract and makes the Stage 6 evidence not checkpoint-safe. Evidence: `command_logs/arch_git_check_ignore_level2.log`, `.gitignore` numbered in `command_logs/arch_gitignore_numbered.log`.

- MEDIUM
  - Econometric refit cadence is causal but not monthly, while the trace describes monthly refit. ML fit audit shows one fit cutoff per execution month, but `econometric_ar_garch` has 365 unique fit cutoffs and up to 31 unique cutoffs per month. The source fits the econometric forecast inside the per-row validation loop, so this is a documentation/traceability mismatch against the stage expectation that monthly expanding refit is real and recorded. It is not look-ahead leakage, but it should be resolved before checkpointing by either documenting the econometric daily cadence as an intentional validation-selected cadence or changing it to the shared monthly cadence. Evidence: `command_logs/arch_fit_cadence_probe.log`, `src/crypto_hedge_fund/experiments/level_2.py` numbered in `command_logs/arch_source_level2_experiment_numbered.log`.

- LOW
  - Multiple-seed robustness evidence is limited. The ML helper fits across configured seeds, but the persisted trading prediction table and trading artifacts use the first seed, and the robustness payload says exactly that. This is honest and not fabricated, but it is not yet a full strategy-level multi-seed sensitivity. Evidence: `command_logs/arch_artifact_probe.log`, `src/crypto_hedge_fund/models/ml.py`.

## Unresolved risks and limitations

- Final-test exposure remains `NOT_EXPOSED`; this review did not run or inspect final-test results.
- Stage 6 remains validation-only. Levels 3-5, pretest lock, final-test suite, notebook, final report and presentation remain future work.
- Active-market survivorship/delisting limitation remains inherited from Stage 2 and is disclosed in artifact warnings.
- Worktree remains dirty by design pending team-lead decision; artifacts record `git_worktree_dirty=true` and a dirty-source hash.
- Level 2 approach weights are configured as equal fixed weights for this attempt; broader validation selection of ensemble weights remains future methodology work unless frozen explicitly.

## Recommendation

REWORK_REQUIRED

The core Level 2 modeling path is mostly sound: causal features/labels, walk-forward ML, meaningful econometric forecasts, typed multi-agent interaction, two-stage risk, shared broker/costed benchmark and validation-only artifacts are all present. However, the ignored Level 2 artifacts are a HIGH checkpoint-safety failure and must be fixed before Stage 6 can be accepted. The econometric cadence/trace mismatch should also be reconciled so the recorded methodology precisely matches what ran.
