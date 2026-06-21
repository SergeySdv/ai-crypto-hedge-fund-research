# Role / stage / attempt

Independent QA reviewer / Stage 6: Level 2 validation implementation / attempt 01.

## Scope

Report-only QA for Stage 6 Level 2 validation. I reran the required gates, inspected Level 2 validation artifacts, checked shared-architecture usage, verified validation-only provenance and final-test quarantine, and recorded all QA commands under `command_logs/qa_*.log`.

No implementation files, configs, data files, artifacts, commits, tags, branch rewrites, final-test commands, notebooks, presentation files or live-trading paths were intentionally changed. The required `make experiments-val` gate regenerated tracked Level 1 artifacts as a side effect; I restored only those tracked Level 1 artifact side effects and logged that restoration in `qa_restore_level1_artifact_side_effects.log`.

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
- `reports/agent_reports/stage_05_level1_validation/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/IMPLEMENTATION_REPORT.md`

Additional inspected evidence:

- `src/crypto_hedge_fund/experiments/level_2.py`
- `src/crypto_hedge_fund/agents/level2.py`
- `src/crypto_hedge_fund/features/level2.py`
- `src/crypto_hedge_fund/models/econometric.py`
- `src/crypto_hedge_fund/models/ml.py`
- `tests/unit/test_level2_validation.py`
- Generated Level 2 artifacts and metadata sidecars under `artifacts/`
- Git ignore visibility for required Level 2 artifacts

## Assumptions and decisions

- This review is scoped to Stage 6 attempt 01 only; it is not a global stage-completion decision.
- Validation-period Level 2 metrics and model outputs may be inspected; final-test metrics, rankings, charts and model outputs remain forbidden.
- `make final-test` is forbidden for this stage and was not run.
- The reported `.gitignore` issue is evaluated as a checkpoint-safety risk, not as a runtime/modeling failure.
- A dirty worktree is expected for a worker attempt, but generated artifacts must either be checkpoint-safe or explicitly flagged before team-lead checkpointing.

## Files inspected or changed

Inspected:

- Mandatory source documents and prior reports listed above.
- Level 2 implementation, model, feature and focused-test files.
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
  - corresponding `.metadata.json` sidecars where present

Changed:

- `reports/agent_reports/stage_06_level2_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_uv_sync_frozen.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_make_lint.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_make_test.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_make_experiments_val.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_focused_level2_pytest.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_artifact_inventory_inspection.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_trace_robustness_inspection.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_trace_structure_inspection.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_git_check_ignore_level2_artifacts.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_git_check_ignore_level2_effective_probe.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_source_architecture_probe.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_model_acceptance_probe.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_final_status_quarantine_snapshot.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_restore_level1_artifact_side_effects.log`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_post_restore_status_snapshot.log`

## Deliverables

- Fresh QA logs for all required commands and probes.
- Independent artifact inventory and metadata inspection.
- Independent Git ignore visibility proof for Level 2 artifacts.
- Shared-architecture and model-acceptance probes.
- This QA report.

## Acceptance-criteria mapping

- Required commands pass: PASS. `uv sync --frozen`, `make lint`, `make test`, `make experiments-val`, and focused Level 2 pytest all exited 0.
- Required Level 2 artifacts exist: PASS. Metrics, equity, weights, orders, fills, figure, trace, robustness, model predictions and fit audit artifacts are physically present after a fresh `make experiments-val`.
- Required Level 2 artifacts are checkpoint-safe or flagged: FLAGGED HIGH. All required Level 2 artifacts are currently ignored by `.gitignore`; see `qa_git_check_ignore_level2_effective_probe.log`.
- Validation split and final-test quarantine: PASS. `make experiments-val` reported `"split": "validation"` and `"final_test_exposure": "NOT_EXPOSED"`; artifact provenance records split `validation`, period `2024-01-01` through `2024-12-31`, null final-test lock hash, and `artifacts/final_test_lock.json` is absent.
- Metrics/artifacts include provenance, costs, benchmark, seed, period and warnings: PASS. Metrics, parquet provenance columns and sidecars include data/config/git hashes, dirty-state hash, seed `42`, broker-costed buy-and-hold benchmark, fee/slippage assumptions, validation period and warnings including validation-only and survivorship-bias limitations.
- Shared broker/risk/orchestrator path: PASS. Source and tests show `TypedAgentOrchestrator`, `PreAllocationRiskPolicy`, `PostAllocationRiskPolicy`, `resolve_risk_approval_targets`, and `SimulatedBroker`; focused tests monkeypatch `SimulatedBroker.run` to prove the shared broker path is used.
- Required Level 2 models/agents: PASS. Evidence shows technical SMA, AutoReg plus GARCH(1,1)-style econometric forecast, Logistic Regression, HistGradientBoostingClassifier, and deterministic ensemble comparison.
- Leakage and timing controls: PASS with note. Feature target uses `open(t+2) / open(t+1) - 1`; fit audit has 2,555 rows with `used_future_labels=False`; focused tests cover feature/target alignment and walk-forward leakage guard. Existing Stage 4/5 note about daily `decision_time == execution_time` boundary remains a low documentation risk, not a Stage 6 failure.
- Predictive and after-cost metrics separated: PASS. Metrics include `predictive_*` columns for model diagnostics and separate net/gross trading metrics with cost fields.
- Random-chance/overfitting checks: PASS. Robustness artifact records 1,000 block-bootstrap repetitions, 1,000 circular-shift randomization repetitions, multiple-seed evidence and cost-sensitivity fields.
- No live trading or external credential dependency observed: PASS. The default validation gate ran from local data and package code only.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_make_test.log` |
| `make experiments-val` | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_make_experiments_val.log` |
| `uv run pytest tests/unit/test_level2_validation.py` | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_focused_level2_pytest.log` |
| Artifact inventory and metadata inspection | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_artifact_inventory_inspection.log` |
| Nested trace and robustness inspection | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_trace_robustness_inspection.log` |
| Representative trace structure inspection | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_trace_structure_inspection.log` |
| Git ignore visibility probe | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_git_check_ignore_level2_artifacts.log` |
| Effective Git ignore per-path probe | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_git_check_ignore_level2_effective_probe.log` |
| Source architecture probe | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_source_architecture_probe.log` |
| Model acceptance detail probe | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_model_acceptance_probe.log` |
| Final quarantine and worktree snapshot | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_final_status_quarantine_snapshot.log` |
| Restore QA side-effect changes to tracked Level 1 artifacts only | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_restore_level1_artifact_side_effects.log` |
| Post-restore status snapshot | 0 | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/qa_post_restore_status_snapshot.log` |

## Test and artifact evidence

- `uv sync --frozen`: audited 79 packages.
- `make lint`: Ruff format check reported 64 files already formatted; Ruff check passed.
- `make test`: 75 tests passed.
- Focused Level 2 pytest: 4 tests passed.
- `make experiments-val`: generated Level 1 and Level 2 validation outputs and reported final-test exposure `NOT_EXPOSED`.
- `artifacts/metrics/level_2.csv`: 5 rows and 119 columns for `technical_sma`, `econometric_ar_garch`, `ml_logistic`, `ml_hist_gradient_boosting` and `agent_ensemble`; `agent_ensemble` is the selected Level 2 approach.
- Level 2 parquet artifacts are validation-only: equity and weights each have 1,830 rows from `2024-01-01 00:00:00+00:00` through `2024-12-31 00:00:00+00:00`; orders and fills have validation-period timestamps through `2024-12-30 00:00:00+00:00`.
- Decision trace contains 20 causal feature columns, target text `forward_return = open(t+2) / open(t+1) - 1`, monthly expanding validation refit protocol, 4 typed agent signals, aggregated contributions/disagreement, pre-allocation constraints, portfolio proposal and post-allocation approval.
- Fit audit: 2,555 rows, status `ok`, models `ml_logistic`, `ml_hist_gradient_boosting` and `econometric_ar_garch`, and `used_future_labels=False` for all rows.
- Robustness artifact records 1,000 block-bootstrap repetitions, 1,000 circular-shift randomization repetitions and multiple seeds `[7, 42, 137]`.
- Effective Git ignore probe reports `IGNORED` for every required Level 2 artifact and sidecar.
- Final-test lock is absent; no QA command ran `make final-test`.

## Findings by severity

- BLOCKER: None.
- HIGH: Required Level 2 artifacts are physically present but ignored by `.gitignore`, so they are not checkpoint-safe by normal `git add` behavior. The team lead must either add narrow `.gitignore` exceptions for Level 2 artifacts or make an explicit force-add/checkpoint decision before Stage 6 can be durable.
- MEDIUM: `make experiments-val` regenerates Level 1 and Level 2 artifacts together. QA restored tracked Level 1 artifact side effects, but the team lead should decide whether multi-level validation gates should preserve prior committed artifacts, regenerate all levels intentionally, or isolate per-level artifact output during staged reviews.
- LOW: Artifact provenance records `git_commit=4719e135667647ec595964581745f6822eb40be9` and `git_worktree_dirty=true`, which is expected before the Stage 6 checkpoint but should be regenerated or clearly accepted after the implementation is committed.
- LOW: Active-market survivorship/delisting limitation remains inherited from Stage 2 and is disclosed in Level 2 warnings; it must remain visible in later notebook/report/deck claims.

## Unresolved risks and limitations

- Final-test exposure remains `NOT_EXPOSED`; `make final-test` was not run.
- Levels 3-5, pretest freeze, final-test suite, notebook, final report and presentation remain out of scope for this Stage 6 review.
- The current worktree is intentionally dirty/uncommitted for the worker attempt.
- Level 2 artifacts are ignored and therefore vulnerable to being omitted from the Stage 6 checkpoint unless remediated or force-added.
- Validation metrics are not final-test evidence and must not be used for post-lock tuning after final-test exposure.

## Recommendation

PASS_WITH_NOTES

The Level 2 implementation gates and acceptance evidence pass, and final-test quarantine remains intact. Do not tag the stage globally complete until the team lead resolves the HIGH artifact checkpoint-safety issue.
