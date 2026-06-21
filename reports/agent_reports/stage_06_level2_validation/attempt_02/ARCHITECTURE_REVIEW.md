# Role / stage / attempt

Independent modeling/leakage architecture reviewer / Stage 6: Level 2 validation implementation / attempt 02.

## Scope

Report-only audit of Stage 6 attempt 02 for Level 2 modeling methodology, leakage safety, shared-architecture consistency, artifact checkpointability and final-test quarantine.

Focus areas:

- Causal Level 2 feature/target alignment under completed-bar to next-open execution.
- Fit availability: labels observed only after execution and never used before available.
- Consistent cadence evidence: ML monthly; econometric daily causal.
- Meaningful econometric, ML and typed-agent implementation.
- Continued use of Stage 4 orchestrator/risk and Stage 3 broker/ledger/cost engine.
- Validation-only robustness and artifact evidence.
- Effective `.gitignore` remediation for required Level 2 artifacts.
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
- `reports/agent_reports/stage_06_level2_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/IMPLEMENTATION_REPORT.md`

Additional implementation and evidence inspected:

- `.gitignore`
- `configs/default.yaml`
- `configs/fast.yaml`
- `src/crypto_hedge_fund/features/level2.py`
- `src/crypto_hedge_fund/models/econometric.py`
- `src/crypto_hedge_fund/models/ml.py`
- `src/crypto_hedge_fund/agents/level2.py`
- `src/crypto_hedge_fund/agents/orchestrator.py`
- `src/crypto_hedge_fund/agents/aggregate.py`
- `src/crypto_hedge_fund/experiments/level_2.py`
- `tests/unit/test_level2_validation.py`
- Generated Level 2 artifacts under `artifacts/**/level_2*`

## Assumptions and decisions

- I accepted the stage base as `4719e135667647ec595964581745f6822eb40be9` / `stage/05-level-1`; current branch is `main`.
- I did not run `make final-test`, create a final-test lock, inspect final-test strategy metrics, commit, tag, or edit implementation/config/data/artifact files.
- I did not rerun `make experiments-val` because it regenerates artifacts and this review's write scope is limited to the architecture review and `arch_*.log` files. I relied on existing attempt-02 worker/QA logs for that gate and independently inspected the generated artifacts.
- I treated the pre-existing Stage 2 2025 universe proof artifacts as outside Level 2 final-test exposure; the Level 2 strategy artifacts inspected here are validation-bounded to 2024.

## Files inspected or changed

Changed manually only:

- `reports/agent_reports/stage_06_level2_validation/attempt_02/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/arch_*.log`

No implementation, config, data, generated strategy artifact, commit, or tag changes were made by this reviewer.

## Deliverables

- Independent architecture/modeling review report: this file.
- Command logs and probes under `reports/agent_reports/stage_06_level2_validation/attempt_02/command_logs/arch_*.log`.

## Acceptance-criteria mapping

| Criterion | Review result | Evidence |
|---|---:|---|
| Features and labels are causally aligned | PASS | `build_level2_feature_frame` sets `feature_cutoff=bar_end_utc`, `execution_time=bar_start+1d`, `future_open_time=bar_start+2d`, and `forward_return=open(t+2)/open(t+1)-1`. Focused test passed. |
| Label observation is after execution and not used before available | PASS | ML uses `label_observation_time < first_execution` for each monthly validation group; econometric uses `label_observation_time < execution_time` for each daily decision. Fit audit has `used_future_labels=0` and all non-null fit cutoffs before execution. |
| ML monthly and econometric daily-causal cadence are consistent | PASS | Config, trace, robustness, predictions and fit audit show ML `monthly` and econometric `daily_causal`. Fit audit has 12 unique ML fit cutoffs per classifier and 365 econometric fit cutoffs. |
| Econometric expected return and GARCH volatility are meaningful | PASS | `fit_econometric_forecast` fits AutoReg expected return and GARCH(1,1) volatility through `arch`; persisted predictions contain 365 `arch_garch_1_1` rows with finite nonzero volatility and varying expected returns. |
| Logistic Regression and HGB/equivalent are meaningful and causal | PASS | `models/ml.py` uses scikit-learn pipelines for Logistic Regression with imputer/scaler and HistGradientBoostingClassifier with expanding historical fits. Persisted probabilities and scores are non-constant. |
| At least two agents communicate through typed records/orchestrator | PASS | Representative trace includes `sma_crossover`, `econometric_ar_garch`, `ml_logistic` and `ml_hist_gradient_boosting` signals, aggregate contributions and disagreement. |
| Level 2 does not bypass Stage 4 risk path | PASS | `build_level_2_target_schedule` calls `TypedAgentOrchestrator`, pre-allocation risk, allocator proposal, rebalance policy, post-allocation risk and `resolve_risk_approval_targets` before broker execution. |
| Signal agents cannot place orders or mutate ledger | PASS | Level 2 model agents emit `AgentSignal` only from prediction tables. Orders/fills are generated only by `SimulatedBroker`. Existing Stage 4 tests cover side-effect boundaries. |
| Shared broker/ledger/cost/metrics architecture | PASS | All Level 2 approaches route schedules through `SimulatedBroker`; benchmark is labeled `broker_costed_buy_and_hold`; metrics include gross/net fields and cost decay. |
| Robustness checks are validation-only and not fabricated | PASS_WITH_NOTE | `level_2_robustness.json` records 1,000 block-bootstrap repetitions and 1,000 circular shifts. Multiple-seed evidence is honest but limited: first seed drives trading artifacts. |
| Required Level 2 artifacts are checkpoint-safe after `.gitignore` remediation | PASS | Effective probe reports `NOT_IGNORED` for all 18 required Level 2 artifact and sidecar paths; `git status` shows them as untracked, not ignored. |
| Final-test quarantine remains intact | PASS | No final-test lock exists; Level 2 metadata has `split=validation`, period `2024-01-01` to `2024-12-31`, `final_test_lock_hash=None`, and no Level 2 artifact timestamps in 2025. Existing attempt-02 logs report `final_test_exposure=NOT_EXPOSED`. |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 PASS | `command_logs/arch_uv_sync_frozen.log` |
| `uv run pytest tests/unit/test_level2_validation.py` | 0 PASS | `command_logs/arch_pytest_level2_validation.log` |
| `make test` | 0 PASS | `command_logs/arch_make_test.log` |
| Source snapshots for Level 2 features/experiment/models | 0 PASS | `command_logs/arch_source_*.log` |
| Level 2 artifact and cadence probe | 0 PASS | `command_logs/arch_artifact_cadence_probe.log` |
| Econometric/ML method probe | 0 PASS | `command_logs/arch_model_method_probe.log` |
| Effective `git check-ignore` probe for Level 2 artifacts | 0 PASS | `command_logs/arch_git_check_ignore_level2_effective.log` |
| Final-test quarantine artifact probe | 0 PASS | `command_logs/arch_final_quarantine_probe.log` |
| Final-test string scan over focused text artifacts/source | 0 PASS | `command_logs/arch_final_test_string_scan.log` |
| Git status/diff/log/tag inventory | 0 PASS | `command_logs/arch_git_status_short_branch_untracked_ignored.log`, `command_logs/arch_git_diff_stat.log`, `command_logs/arch_git_log_head.log`, `command_logs/arch_git_tags.log` |

I did not run `make final-test`. I did not rerun `make experiments-val` to avoid regenerating artifacts within this read-only review scope.

## Test and artifact evidence

- Focused Level 2 suite: 5 passed.
- Full test suite: 76 passed.
- Level 2 required artifact inventory contains 18 files:
  - metrics CSV and sidecar;
  - equity, weights, orders and fills Parquet files plus sidecars;
  - equity-curve PNG plus sidecar;
  - decision trace JSON;
  - robustness JSON;
  - model predictions Parquet plus sidecar;
  - fit audit Parquet plus sidecar.
- Level 2 metrics artifact:
  - shape: 5 rows, 119 columns;
  - approaches: `technical_sma`, `econometric_ar_garch`, `ml_logistic`, `ml_hist_gradient_boosting`, `agent_ensemble`;
  - selected approach: `agent_ensemble`;
  - split: `validation`;
  - period: `2024-01-01` to `2024-12-31`;
  - final-test lock hash: null.
- Level 2 artifact date bounds:
  - equity and weights: `2024-01-01T00:00:00+00:00` to `2024-12-31T00:00:00+00:00`;
  - orders and fills: `2024-01-01T00:00:00+00:00` to `2024-12-30T00:00:00+00:00`.
- Fit and prediction audit:
  - prediction rows: 1,095;
  - fit-audit rows: 2,555;
  - refit frequencies: econometric `daily_causal`, ML `monthly`;
  - future-label flags: 0;
  - all non-null fit cutoffs are before execution time.
- Econometric method evidence:
  - 365 econometric prediction rows;
  - 365 `ok`;
  - 365 `arch_garch_1_1`;
  - forecast volatility range approximately `0.0213` to `0.0477`.
- Representative trace evidence:
  - four agents in the ensemble trace;
  - aggregate includes per-agent contributions;
  - pre-risk reason codes: `ok`;
  - post-risk action: `approve`.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None.

- MEDIUM
  - None.

- LOW
  - Current `git status` still shows tracked Level 1 artifact files modified, despite the attempt-02 implementation report saying Level 1 artifact side effects were restored. This does not invalidate Level 2 modeling or leakage safety, and Level 2 artifacts themselves are now checkpoint-visible, but the team lead should decide whether to restore or intentionally include those Level 1 artifact changes before checkpointing Stage 6. Evidence: `command_logs/arch_git_status_short_branch_untracked_ignored.log`, `command_logs/arch_git_diff_stat.log`.
  - Multiple-seed robustness remains limited at the strategy-artifact level. The ML helper fits across configured seeds and records `seed_count`, but the persisted trading artifacts use the first seed. This is honestly documented in the robustness payload and is not fabricated, but deeper strategy-level seed sensitivity remains future work.

## Unresolved risks and limitations

- Final-test exposure remains `NOT_EXPOSED`; this review did not run or inspect final-test outputs.
- Stage 6 remains validation-only. Levels 3-5, pretest lock, final suite, notebook, report and presentation remain future work.
- Active-market survivorship/delisting limitation remains inherited from Stage 2 and is disclosed in artifact warnings.
- Worktree is intentionally dirty pending team-lead decision; Level 2 artifacts record dirty-source provenance.
- Level 2 ensemble weights are fixed equal weights in this attempt. That is acceptable for this validation stage only if frozen/documented before later final-test work.

## Recommendation

PASS_WITH_NOTES

Attempt 02 remediates the attempt-01 blockers. The Level 2 modeling path is causally aligned, cadence evidence is consistent, econometric and ML models are substantive, typed multi-agent interaction flows through the Stage 4 risk path, artifacts are validation-only and checkpoint-visible, and final-test quarantine remains intact. The only residual issue is checkpoint hygiene around modified Level 1 artifacts, which should be resolved or explicitly accepted by the team lead before committing/tagging Stage 6.
