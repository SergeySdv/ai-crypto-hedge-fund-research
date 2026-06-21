# Role / stage / attempt

Independent QA reviewer / Stage 6: Level 2 validation implementation / attempt 02.

## Scope

Report-only QA for the attempt-02 remediation. I verified the attempt-01 HIGH artifact visibility issue and the cadence-evidence issue, reran the required gates, inspected Level 2 artifacts/provenance/cadence, checked final-test quarantine, and wrote fresh QA logs under `command_logs/qa_*.log`.

No implementation, config, data, artifact, commit or tag changes were intentionally made by QA. The required `make experiments-val` rerun regenerated tracked Level 1 artifacts as a side effect; I did not restore them because the allowed write scope for this review is limited to this report and QA logs.

## Sources read

- `AGENTS.md`
- `MASTER_PROMPT_CODEX_TEAMLEAD.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `docs/11_REQUIREMENTS_TRACEABILITY.md`
- `docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/teamlead/PROJECT_STATE.md`
- `reports/teamlead/STAGE_BOARD.md`
- `reports/teamlead/RISK_REGISTER.md`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/IMPLEMENTATION_REPORT.md`

Additional inspected evidence:

- `src/crypto_hedge_fund/experiments/level_2.py`
- `src/crypto_hedge_fund/agents/level2.py`
- `tests/unit/test_level2_validation.py`
- Generated Level 2 artifacts and metadata sidecars under `artifacts/`

## Assumptions and decisions

- Validation-period Level 2 outputs are in scope for inspection; final-test metrics, rankings, charts and model outputs remain forbidden.
- `make final-test` is forbidden for this stage and was not run.
- This report is an independent QA recommendation only. It does not declare Stage 6 globally complete.
- Existing dirty worktree state is expected for an implementation attempt, but artifact visibility must be checkpoint-safe.

## Files inspected or changed

Inspected:

- Mandatory documents and reports listed above.
- Level 2 implementation/test files listed above.
- Required Level 2 artifacts:
  - `artifacts/metrics/level_2.csv`
  - `artifacts/equity/level_2.parquet`
  - `artifacts/weights/level_2.parquet`
  - `artifacts/orders/level_2.parquet`
  - `artifacts/fills/level_2.parquet`
  - `artifacts/figures/level_2_equity_curve.png`
  - `artifacts/monitoring/level_2_decision_trace.json`
  - `artifacts/monitoring/level_2_robustness.json`
  - `artifacts/monitoring/level_2_model_predictions.parquet`
  - `artifacts/monitoring/level_2_fit_audit.parquet`
  - corresponding `.metadata.json` sidecars where applicable.

Changed by QA:

- `reports/agent_reports/stage_06_level2_validation/attempt_02/QA_REPORT.md`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_uv_sync_frozen.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_make_lint.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_make_test.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_make_experiments_val.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_pytest_level2_validation.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_git_check_ignore_level2_artifacts.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_artifact_inventory_provenance_cadence.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_metrics_columns_probe.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_trace_structure_probe.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_source_architecture_probe.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_final_quarantine_status.log`

## Deliverables

- Fresh QA command logs for all required gates and artifact probes.
- Independent Git visibility proof for Level 2 artifacts.
- Independent artifact/provenance/cadence inspection.
- This QA report.

## Acceptance-criteria mapping

- Required gates pass: PASS. `uv sync --frozen`, `make lint`, `make test`, `make experiments-val`, and focused Level 2 pytest all exited 0.
- Attempt-01 HIGH artifact issue fixed: PASS. `git check-ignore` reports `NOT_IGNORED` for all 18 required Level 2 artifact paths and sidecars.
- Required Level 2 artifacts exist and include sidecars/provenance: PASS. Artifact inspection found 18 required files, metrics shape `5 x 119`, sidecars for metrics/equity/weights/orders/fills/figure/model predictions/fit audit, and provenance with validation split, period, data/config/git hashes, dirty-source hash, seed, benchmark and cost assumptions.
- Validation-only and final-test quarantine: PASS. `make experiments-val` reports `final_test_exposure: NOT_EXPOSED`; artifacts are split `validation`, period `2024-01-01` to `2024-12-31`, no inspected Level 2 table contains 2025 rows, and `artifacts/final_test_lock.json` is absent.
- Cadence-evidence issue fixed: PASS. Metrics warnings, decision trace, robustness JSON, model predictions and fit audit consistently record ML `monthly` and econometric `daily_causal`.
- Future-label flags: PASS. Fit audit has 2,555 rows, `future_label_flags=0`, and all fit cutoffs precede execution time.
- Shared architecture path: PASS. Source and tests show Level 2 uses `TypedAgentOrchestrator`, `SignalAggregator`, pre/post risk policies, `resolve_risk_approval_targets`, `PanelMarketData`, and `SimulatedBroker`; focused test monkeypatches the broker to prove the shared broker path is used.
- Agent interaction trace: PASS. Representative trace contains 4 typed signals (`sma_crossover`, `econometric_ar_garch`, `ml_logistic`, `ml_hist_gradient_boosting`), aggregated contributions/disagreement, constraints, proposal and approval.
- Predictive and trading metrics separation: PASS. Metrics include separate after-cost net/gross trading metrics and predictive diagnostics for econometric/ML models.
- Random-chance/overfitting checks: PASS. Robustness artifact records 1,000 block-bootstrap repetitions, 1,000 circular-shift randomization repetitions and seeds `[7, 42, 137]`.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_uv_sync_frozen.log` |
| `make lint` | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_make_lint.log` |
| `make test` | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_make_test.log` |
| `make experiments-val` | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_make_experiments_val.log` |
| `uv run pytest tests/unit/test_level2_validation.py` | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_pytest_level2_validation.log` |
| Git check-ignore Level 2 artifact visibility probe | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_git_check_ignore_level2_artifacts.log` |
| Artifact inventory/provenance/cadence inspection | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_artifact_inventory_provenance_cadence.log` |
| Metrics schema probe | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_metrics_columns_probe.log` |
| Representative trace structure probe | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_trace_structure_probe.log` |
| Source architecture probe | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_source_architecture_probe.log` |
| Final-test quarantine/status probe | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/qa_final_quarantine_status.log` |

## Test and artifact evidence

- `uv sync --frozen`: audited 79 packages.
- `make lint`: Ruff format check and Ruff lint passed.
- `make test`: 76 tests passed.
- Focused Level 2 pytest: 5 tests passed.
- `make experiments-val`: generated validation artifacts for Levels 1-2 and reported `final_test_exposure: NOT_EXPOSED`.
- Level 2 metrics approaches: `technical_sma`, `econometric_ar_garch`, `ml_logistic`, `ml_hist_gradient_boosting`, `agent_ensemble`; selected approach is `agent_ensemble`.
- Prediction artifact: 1,095 rows; refit frequencies are econometric `daily_causal`, ML models `monthly`; no 2025 rows.
- Fit audit: 2,555 rows; econometric has 365 unique fit cutoffs, each ML model has 12; `used_future_labels` is false for every row.
- Decision trace cadence: ML `monthly`, econometric `daily_causal`, with explicit note that AutoReg/GARCH forecasts are refit for each validation decision using only labels observed before execution.

## Findings by severity

- BLOCKER: None.
- HIGH: None. The attempt-01 artifact checkpoint-safety issue is remediated.
- MEDIUM: The required QA rerun of `make experiments-val` regenerated tracked Level 1 artifacts and left them modified. This is a known multi-level artifact side effect, not a Level 2 remediation failure, but the team lead should restore or intentionally include those side effects before any checkpoint.
- LOW: Metadata sidecars encode limitations such as `survivorship_bias_active_markets` in the `warnings` list rather than a distinct `limitations` field. This satisfies the Stage 6 review intent, but final submission artifacts should keep limitations prominent.
- LOW: Artifacts record `git_worktree_dirty=true` and a dirty-source diff hash, which is expected pre-checkpoint. Regenerate or explicitly accept after commit/tag if clean provenance is required.

## Unresolved risks and limitations

- Final-test exposure remains `NOT_EXPOSED`; `make final-test` was not run.
- Levels 3-5, pretest freeze, final-test suite, final notebook, report and deck are out of scope.
- Active-market survivorship/delisting limitation remains inherited from Stage 2.
- Current worktree is intentionally dirty with attempt implementation files, Level 2 artifacts and QA/architecture/implementation reports.

## Recommendation

PASS_WITH_NOTES.

The attempt-01 HIGH artifact issue and cadence-evidence issue are fixed, all required gates pass, Level 2 artifacts are visible to Git, cadence is consistent, future-label flags are zero, shared architecture usage is evidenced, and final-test quarantine remains intact. Do not declare the stage globally complete from this QA report alone; the team lead still needs to make the stage decision and handle the Level 1 artifact side effects before checkpointing.
