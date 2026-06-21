# Role / stage / attempt

Independent QA reviewer / Stage 7 - Level 3 static portfolio validation / attempt 02.

## Scope

Validated the Stage 7 attempt 02 remediation without declaring global stage completion. Focus was attempt 01 HIGH H-001 net-after-cost metric remediation, required gate commands, Level 1/2 artifact side effects, Level 3 artifact validity/checkpoint safety, and final-test quarantine.

I did not run `make final-test`, create a final-test lock, inspect 2025 performance outputs, edit implementation/config/tests/artifacts/management docs, commit, or tag.

## Sources read

- `AGENTS.md`
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
- `reports/agent_reports/stage_07_level3_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_02/IMPLEMENTATION_REPORT.md`

## Assumptions and decisions

- Stage 7 remains validation-only. 2025 final-test performance remains quarantined.
- The Level 3 validation vintage must select and estimate using 2023 data and evaluate in 2024.
- The final-vintage plan may compute 2024-estimated weights for later frozen execution, but must not compute 2025 returns, fills, rankings, charts, or metrics.
- `make experiments-val` is a required QA command and may regenerate artifacts. I did not restore artifact side effects because this QA write scope is limited to `QA_REPORT.md` and `qa_*` logs.
- Existing Binance active-market survivorship/listing bias remains an accepted project limitation, not a new Stage 7 blocker.

## Files inspected or changed

Inspected:

- `src/crypto_hedge_fund/experiments/level_3.py`
- `tests/unit/test_level3_validation.py`
- `src/crypto_hedge_fund/portfolio/allocators.py`
- `configs/default.yaml`
- `configs/fast.yaml`
- `artifacts/metrics/level_3.csv`
- `artifacts/equity/level_3.parquet`
- `artifacts/weights/level_3.parquet`
- `artifacts/orders/level_3.parquet`
- `artifacts/fills/level_3.parquet`
- `artifacts/monitoring/level_3_decision_trace.json`
- `artifacts/monitoring/level_3_universe_selection.csv`
- `artifacts/monitoring/level_3_final_vintage_plan.json`
- Level 3 metadata sidecars.
- Attempt 02 worker command logs, including `git_status_after_restore.log`.

Changed by me:

- `reports/agent_reports/stage_07_level3_validation/attempt_02/QA_REPORT.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/qa_*`

Observed command side effects:

- The independent QA run of `make experiments-val` regenerated tracked Level 1/2 artifacts and left them modified in the worktree. Attempt 02's own `git_status_after_restore.log` shows Level 1/2 artifact drift had been restored before this QA run.

## Deliverables

- Verified attempt 01 H-001 is closed in source: `src/crypto_hedge_fund/experiments/level_3.py` now prepends an initial-capital baseline before shared metrics calculation.
- Verified attempt 01 H-001 is closed in tests: `test_level3_positive_costs_keep_net_return_below_gross_return` asserts positive costs imply net ROI/return below gross and validates initial-capital normalization.
- Verified attempt 01 H-001 is closed in artifacts: current `artifacts/metrics/level_3.csv` has positive costs and net ROI/total return below gross for all four methods.
- Verified Level 3 artifacts exist, are Git-visible/addable, validation-labeled, and have null final-test lock hash.
- Verified required commands pass.
- Verified final-test exposure remains `NOT_EXPOSED`.

## Acceptance-criteria mapping

- `uv sync --frozen`: PASS.
- `make lint`: PASS.
- `make test`: PASS, 83 tests.
- `make experiments-val`: PASS, Levels 1-3 validation only, final-test exposure `NOT_EXPOSED`.
- `uv run pytest tests/unit/test_level3_validation.py`: PASS, 5 tests.
- Focused net/gross cost consistency probe: PASS on v2 artifact-contract probe.
- Attempt 01 H-001: PASS. Net metrics now use configured initial capital rather than first post-cost row.
- Level 3 artifact safety: PASS. Required artifacts and metadata sidecars exist and are addable under Git; metrics split is validation and final lock hash is null.
- Level 1/2 side effects: PASS_WITH_NOTES. Attempt 02 restored them before QA, but the required independent `make experiments-val` run reintroduced tracked Level 1/2 modifications. Team lead should restore or deliberately document a coordinated refresh before checkpointing.
- Final-test quarantine: PASS. No `artifacts/final_test_lock.json`; final-vintage plan is `planned_not_executed` / `NOT_EXPOSED`.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/qa_uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/qa_make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/qa_make_test.log` |
| `make experiments-val` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/qa_make_experiments_val.log` |
| `uv run pytest tests/unit/test_level3_validation.py` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/qa_focused_level3_pytest.log` |
| Level 3 net/gross cost consistency probe v1 | 1 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/qa_level3_net_gross_cost_probe.log`; QA probe assumed direct `split`/`final_test_lock_hash` CSV columns and was superseded by v2 |
| Level 3 net/gross cost consistency probe v2 | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/qa_level3_net_gross_cost_probe_v2.log` |
| Final-test exposure state probe | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/qa_final_test_state_probe.log` |
| `git status --short --branch --untracked-files=all` and Level 3 Git visibility checks | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/qa_git_status_visibility.log` |

## Test and artifact evidence

- `make test`: `83 passed`.
- Focused Level 3 pytest: `5 passed`.
- `make experiments-val`: generated validation artifacts for `level_1`, `level_2`, and `level_3`; output reports `final_test_exposure: "NOT_EXPOSED"`.
- Source remediation evidence: `_combined_metrics` now calls `_with_initial_capital_baseline(...)` for net and gross equity and `_benchmark_with_initial_capital_baseline(...)` before `calculate_performance_metrics`.
- Regression evidence: the new Level 3 test asserts `net_roi < gross_roi`, `net_total_return < gross_total_return`, positive gross-to-net decay, and final-return equality to final NAV divided by initial capital.
- Current Level 3 metrics from `qa_level3_net_gross_cost_probe_v2.log`:

| Method | Gross ROI | Net ROI | Gross total return | Net total return | Net cost | Decay |
|---|---:|---:|---:|---:|---:|---:|
| `equal_weight` | 1.282948 | 1.281455 | 1.282948 | 1.281455 | 1492.5 | 0.001493 |
| `inverse_volatility` | 1.219919 | 1.218426 | 1.219919 | 1.218426 | 1492.5 | 0.001492 |
| `minimum_variance` | 1.115019 | 1.113527 | 1.115019 | 1.113527 | 1492.5 | 0.001492 |
| `cvar_downside` | 1.262462 | 1.260970 | 1.262462 | 1.260970 | 1492.5 | 0.001492 |

- Current Level 3 universe remains 7 symbols: `BTC/USDT`, `ETH/USDT`, `XRP/USDT`, `BNB/USDT`, `SOL/USDT`, `DOGE/USDT`, `LTC/USDT`.
- Current Level 3 estimation window remains `2023-01-01T00:00:00+00:00` through `2023-12-31T00:00:00+00:00`; validation period is `2024-01-01` through `2024-12-31`.
- Selection diagnostics are now recorded: `selection_drawdown_constraint=0.25`, `selection_feasible_method_count=0`, `selection_fallback_used=True`, selected method `cvar_downside`, tie-breaker `max_metric_then_min_net_turnover_then_method_order`.
- Final-vintage plan records `status: planned_not_executed`, `final_test_exposure: NOT_EXPOSED`, and warning that no 2025 returns/metrics/rankings/charts/fills are computed.
- Git visibility: `git ls-files --others --exclude-standard` lists all required Level 3 artifacts and metadata sidecars. `git check-ignore -v` matches explicit `.gitignore` negation rules for Level 3 artifacts, so they are not hidden by broad artifact ignores.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None. Attempt 01 H-001 is remediated in source, regression tests, and regenerated Level 3 artifacts.

- MEDIUM
  - M-001: The required independent `make experiments-val` run reintroduced tracked Level 1/2 artifact modifications in the final QA worktree. Evidence: `qa_git_status_visibility.log` lists modified tracked `artifacts/**/level_1*` and `artifacts/**/level_2*` files. Attempt 02's own restore log shows these were restored before QA, so this is a reproducible command side effect rather than a Level 3 methodology bug. Team lead should restore Level 1/2 tracked artifacts again, or deliberately document and commit a coordinated refresh, before the Stage 7 checkpoint.

- LOW
  - L-001: The first QA net/gross probe failed because it assumed direct `split` and `final_test_lock_hash` CSV columns. The repo stores those as `provenance_split` and `provenance_final_test_lock_hash` plus sidecar metadata. The corrected v2 probe passed.
  - L-002: `level_3.csv` contains the substring `2025` only in quarantine warning text / final-vintage-plan references. The final-test state probe confirmed metrics period is 2024 validation and the final-vintage plan is not executed.

## Unresolved risks and limitations

- Active Binance/CCXT market survivorship/listing bias remains inherited from Stage 2 and must stay disclosed in later notebook/report/deck work.
- Daily bars do not model intraday liquidity, order-book depth, custody, exchange outages, taxes, or real reconciliation.
- `cvar_downside` remains a transparent standalone downside-risk heuristic, not a full scenario CVaR optimization program.
- Level 3 artifacts are untracked until the Stage 7 checkpoint is reviewed and committed.
- Because QA write scope excludes artifact restoration, tracked Level 1/2 artifact drift caused by the independent gate run remains for team lead handling.

## Recommendation

PASS_WITH_NOTES
