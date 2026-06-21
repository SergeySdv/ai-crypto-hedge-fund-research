# Role / stage / attempt

Implementation worker / Stage 6 Level 2 validation / attempt 01.

## Scope

Implemented Level 2 validation for one BTC/USDT pair through the existing shared panel-native architecture. The run compares a technical SMA agent, an AutoReg plus GARCH-style econometric agent, Logistic Regression, HistGradientBoostingClassifier, and a four-agent ensemble under the same validation period, shared broker, cost assumptions, benchmark, risk gates and artifact contract.

No final-test command was run. Final-test exposure remains `NOT_EXPOSED`.

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
- `reports/teamlead/RISK_REGISTER.md`
- `reports/teamlead/DECISION_LOG.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/TEAMLEAD_DECISION.md`

## Assumptions and decisions

- Default Level 2 pair is `BTC/USDT`, matching Level 1.
- Primary target is one open-to-open day after next-open execution: `open(t+2) / open(t+1) - 1`.
- Label threshold is one-way fee plus slippage plus the configured safety margin.
- ML models use a monthly expanding validation refit. Each monthly model uses labels whose observation time is before the first execution in that month; fit audits prove no future labels are used.
- Econometric forecasts use an AutoReg expected-return component plus GARCH(1,1) conditional volatility via `arch` when available, with a deterministic educational GARCH fallback in `src/crypto_hedge_fund/models/econometric.py`.
- The canonical Level 2 artifacts contain all compared approaches with an `approach` column; `agent_ensemble` is marked as the selected Level 2 run for this stage.
- Existing Stage 5 compatibility is preserved: CLI configs without a `level_2` block still run Level 1 only.

## Files inspected or changed

Inspected key shared architecture files:

- `src/crypto_hedge_fund/experiments/level_1.py`
- `src/crypto_hedge_fund/agents/base.py`
- `src/crypto_hedge_fund/agents/orchestrator.py`
- `src/crypto_hedge_fund/agents/aggregate.py`
- `src/crypto_hedge_fund/risk/pre_allocation.py`
- `src/crypto_hedge_fund/risk/post_allocation.py`
- `src/crypto_hedge_fund/execution/broker.py`
- `src/crypto_hedge_fund/artifacts/writers.py`
- `src/crypto_hedge_fund/metrics/performance.py`
- `tests/unit/test_level1_validation.py`
- `tests/unit/test_experiments_validation.py`

Changed or created:

- `configs/default.yaml`
- `configs/fast.yaml`
- `src/crypto_hedge_fund/agents/__init__.py`
- `src/crypto_hedge_fund/agents/level2.py`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/experiments/__init__.py`
- `src/crypto_hedge_fund/experiments/level_2.py`
- `src/crypto_hedge_fund/features/__init__.py`
- `src/crypto_hedge_fund/features/level2.py`
- `src/crypto_hedge_fund/models/__init__.py`
- `src/crypto_hedge_fund/models/econometric.py`
- `src/crypto_hedge_fund/models/ml.py`
- `tests/unit/test_level2_validation.py`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/*`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/IMPLEMENTATION_REPORT.md`

Generated Level 2 artifacts:

- `artifacts/metrics/level_2.csv`
- `artifacts/metrics/level_2.csv.metadata.json`
- `artifacts/equity/level_2.parquet`
- `artifacts/equity/level_2.parquet.metadata.json`
- `artifacts/weights/level_2.parquet`
- `artifacts/weights/level_2.parquet.metadata.json`
- `artifacts/orders/level_2.parquet`
- `artifacts/orders/level_2.parquet.metadata.json`
- `artifacts/fills/level_2.parquet`
- `artifacts/fills/level_2.parquet.metadata.json`
- `artifacts/figures/level_2_equity_curve.png`
- `artifacts/figures/level_2_equity_curve.png.metadata.json`
- `artifacts/monitoring/level_2_decision_trace.json`
- `artifacts/monitoring/level_2_robustness.json`
- `artifacts/monitoring/level_2_model_predictions.parquet`
- `artifacts/monitoring/level_2_model_predictions.parquet.metadata.json`
- `artifacts/monitoring/level_2_fit_audit.parquet`
- `artifacts/monitoring/level_2_fit_audit.parquet.metadata.json`

Note: Level 2 artifacts are currently ignored by `.gitignore`; see HIGH finding.

## Deliverables

- Causal Level 2 feature table with explicit `feature_cutoff`, `execution_time`, `future_open_time`, `label_observation_time`, feature column list, target threshold and target label.
- Econometric expected-return and volatility model helper using AutoReg and GARCH(1,1)-style volatility.
- Classical ML walk-forward helper comparing Logistic Regression and HistGradientBoostingClassifier.
- Typed Level 2 prediction-table agent integrated with the existing `TypedAgentOrchestrator`.
- Level 2 validation experiment runner using shared pre-risk, allocator, rebalance policy, post-risk resolver and `SimulatedBroker`.
- Approach comparison artifacts for technical, econometric, ML logistic, ML HGB and ensemble approaches.
- Robustness artifact with block bootstrap, circular-shift randomization, multiple-seed note and cost-sensitivity fields.
- Fit audit artifact proving zero future-label uses in the default validation run.
- Focused unit tests for feature/target alignment, walk-forward leakage guard, artifact provenance/trace/robustness, and shared broker usage.

## Acceptance-criteria mapping

- L2-01 / J technical, econometric, ML and agents: implemented in `src/crypto_hedge_fund/experiments/level_2.py`, `agents/level2.py`, `models/econometric.py`, `models/ml.py`; trace shows `sma_crossover`, `econometric_ar_garch`, `ml_logistic`, `ml_hist_gradient_boosting`.
- L2-02 single pair: default `level_2.symbol: BTC/USDT`.
- L2-03 same OOS period/costs/sizing/benchmark: `artifacts/metrics/level_2.csv` contains all approaches for validation `2024-01-01` through `2024-12-31`, same costed buy-and-hold benchmark and shared broker outputs.
- L2-04/L2-05 feature and target definition: `features/level2.py` and `level_2_decision_trace.json` record feature set, columns and target formula.
- L2-06/L2-07 train/validation and retraining: monthly expanding validation refit recorded in config, trace and fit audit.
- L2-08 predictive vs trading metrics: predictive metrics are prefixed `predictive_*`; trading metrics are `net_*` and `gross_*`.
- L2-09 random-chance/overfitting checks: `level_2_robustness.json` records 1,000 bootstrap and 1,000 circular-shift repetitions in default mode.
- Shared architecture D/E/G/H: Level 2 uses `TypedAgentOrchestrator`, `PreAllocationRiskPolicy`, `PostAllocationRiskPolicy`, `resolve_risk_approval_targets`, and `SimulatedBroker`; `tests/unit/test_level2_validation.py` includes shared-broker and no-leakage assertions.
- Final-test quarantine F: no `make final-test`; CLI output and artifact inspection record `NOT_EXPOSED` and validation-only provenance.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/uv_sync_frozen.log` |
| `make lint` | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/make_lint.log` |
| `make test` | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/make_test.log` |
| `make experiments-val` | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/make_experiments_val.log` |
| `uv run pytest tests/unit/test_level2_validation.py` | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/pytest_level2_validation.log` |
| Artifact inspection script | 0 PASS | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/artifact_inspection.log` |
| `git check-ignore` for Level 2 artifacts | 0, artifacts ignored | `reports/agent_reports/stage_06_level2_validation/attempt_01/command_logs/git_check_ignore_level2_artifacts.log` |

During development, two exploratory `uv run crypto-hedge-fund experiments-val` runs were manually interrupted while diagnosing runtime; the final logged `make experiments-val` gate passed.

## Test and artifact evidence

- Full suite: 75 tests passed.
- Focused Level 2 suite: 4 tests passed.
- `artifacts/metrics/level_2.csv` has 5 rows:
  - `technical_sma`
  - `econometric_ar_garch`
  - `ml_logistic`
  - `ml_hist_gradient_boosting`
  - `agent_ensemble`
- `agent_ensemble` is marked `selected_for_level_2=True`.
- Artifact inspection found:
  - `provenance_split=['validation']`
  - `period_start=['2024-01-01']`
  - `period_end=['2024-12-31']`
  - `fit_audit_rows=2555`
  - `future_label_flags=0`
  - trace agents: `sma_crossover`, `econometric_ar_garch`, `ml_logistic`, `ml_hist_gradient_boosting`
  - `bootstrap_repetitions=1000`
  - `permutation_repetitions=1000`
  - `final_test_exposure NOT_EXPOSED`

## Findings by severity

- BLOCKER
  - None.
- HIGH
  - Level 2 artifact files are currently ignored by `.gitignore`, confirmed in `git_check_ignore_level2_artifacts.log`. I did not edit `.gitignore` because it was outside this worker’s allowed write scope. Before Stage 6 checkpointing, the team lead should either expand scope for a narrow `.gitignore` update or explicitly decide how to preserve these required artifacts.
- MEDIUM
  - `make experiments-val` now regenerates Level 1 and Level 2 artifacts together. I restored tracked Level 1 artifacts after the logged gate to keep the visible worktree Stage 6-scoped; future lead validation may want a policy for preserving regenerated Level 1 outputs during multi-level validation runs.
  - Level 2 uses monthly expanding ML refits for runtime and methodological clarity. The assignment allows a recorded retraining cadence; this is documented in config, trace and fit audit.
- LOW
  - The econometric GARCH helper includes an educational deterministic fallback if the `arch` fit fails. This is intentional and reason-coded/metadata-recorded, not a silent optimistic fallback.

## Unresolved risks and limitations

- Active-market survivorship/delisting limitation remains inherited from Stage 2.
- Level 2 results are validation-only and not a profitability claim; BTC buy-and-hold outperformed all Level 2 approaches in the generated validation metrics.
- The artifacts are physically present in the working directory but ignored by Git until `.gitignore` is updated or they are force-added by the lead.
- Final-test state remains `NOT_EXPOSED`; no final-test lock or 2025 strategy metrics were generated.

## Recommendation

PASS_WITH_NOTES

The implementation and required validation commands pass, but the ignored Level 2 artifact paths need a team-lead decision or a scoped `.gitignore` follow-up before checkpointing Stage 6 evidence.
