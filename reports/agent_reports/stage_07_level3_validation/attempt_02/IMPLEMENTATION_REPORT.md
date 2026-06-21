# Role / stage / attempt

Implementation fixer / Stage 7 - Level 3 static portfolio validation / attempt 02.

## Scope

Remediated attempt 01 HIGH finding H-001 by fixing Level 3 net/gross performance normalization for entry costs, adding focused regression coverage, regenerating Level 3 validation artifacts, restoring tracked Level 1/2 artifact drift from `make experiments-val`, and logging the required validation commands. I did not run final-test commands, create a final-test lock, inspect 2025 final-test outputs, commit, or tag.

## Sources read

- `AGENTS.md`
- `docs/00_GLOBAL_PLAN_AND_AUDIT.md`
- `docs/11_REQUIREMENTS_TRACEABILITY.md`
- `docs/01_ASSIGNMENT_AND_SCOPE.md`
- `docs/02_ARCHITECTURE.md`
- `docs/03_REPOSITORY_LAYOUT.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/05_IMPLEMENTATION_PLAN.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/07_PRESENTATION_OUTLINE.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `docs/10_RISKS_AND_DECISIONS.md`
- `docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/teamlead/PROJECT_STATE.md`
- `reports/teamlead/STAGE_BOARD.md`
- `reports/teamlead/REQUIREMENTS_STATUS.md`
- `reports/teamlead/RISK_REGISTER.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/TEAMLEAD_DECISION.md`

## Assumptions and decisions

- The metric bug was local to Level 3 reporting: shared broker/ledger outputs were already charging entry fees/slippage, but metrics were normalized from the first post-cost validation equity row.
- I left the shared metrics API unchanged and added a Level 3 metric baseline row using configured `backtest.initial_capital_usd`. This includes initial entry costs in `net_total_return`, `net_roi`, CAGR/drawdown-derived metrics, and benchmark-relative calculations without changing the written equity ledger.
- I added drawdown-filter fallback diagnostics in Level 3 metrics and decision trace because all validation methods breach the configured `rebalance.max_drawdown_constraint=0.25`, so method selection falls back to all methods.
- I restored only tracked Level 1/2 artifact files after `make experiments-val`. Source/config/report changes from attempt 01 that pre-existed this attempt were not reverted.

## Files inspected or changed

Inspected:

- `src/crypto_hedge_fund/experiments/level_3.py`
- `src/crypto_hedge_fund/portfolio/allocators.py`
- `src/crypto_hedge_fund/metrics/performance.py`
- `src/crypto_hedge_fund/execution/broker.py`
- `tests/unit/test_level3_validation.py`
- current Level 3 artifacts under `artifacts/**/level_3*`

Changed by this attempt:

- `src/crypto_hedge_fund/experiments/level_3.py`
- `tests/unit/test_level3_validation.py`
- `artifacts/metrics/level_3.csv`
- `artifacts/equity/level_3.parquet`
- `artifacts/weights/level_3.parquet`
- `artifacts/orders/level_3.parquet`
- `artifacts/fills/level_3.parquet`
- `artifacts/figures/level_3_equity_curve.png`
- `artifacts/monitoring/level_3_decision_trace.json`
- `artifacts/monitoring/level_3_universe_selection.csv`
- `artifacts/monitoring/level_3_final_vintage_plan.json`
- associated Level 3 metadata sidecars
- `reports/agent_reports/stage_07_level3_validation/attempt_02/**`

## Deliverables

- Fixed Level 3 net/gross metric normalization by prepending an initial-capital metric baseline before calling shared performance metrics.
- Added regression test `test_level3_positive_costs_keep_net_return_below_gross_return`.
- Regenerated Level 3 artifacts from validation-only `make experiments-val`.
- Added Level 3 selection diagnostics: configured drawdown constraint, feasible method count, fallback flag, selected method, selection metric, and tie-breaker.
- Restored tracked Level 1/2 artifact drift after the required validation run.

## Acceptance-criteria mapping

- Correct net normalization: PASS. The probe confirms positive costs and `net_roi`/`net_total_return` below gross for every Level 3 method.
- Regression coverage: PASS. `tests/unit/test_level3_validation.py` now asserts the failure mode cannot recur on fixture price paths with positive costs.
- Regenerated Level 3 artifacts: PASS. `make experiments-val` passed and wrote current Level 3 artifacts.
- Preserve Stage 7 behavior: PASS. Level 3 still uses 7 assets, 2023-01-01 through 2023-12-31 estimation, 2024 validation holdout, four methods, shared broker/risk/metrics/artifacts, and final-test exposure `NOT_EXPOSED`.
- Drawdown fallback metadata: PASS. Metrics and trace record `selection_feasible_method_count=0`, `selection_fallback_used=True`, and tie-breaker policy.
- Restore Level 1/2 artifact drift: PASS. Tracked Level 1/2 artifact paths were restored to `HEAD`; post-restore git status is logged.
- Required command gates: PASS. All final recorded required statuses are `0`.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/make_test.log` |
| `make experiments-val` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/make_experiments_val.log` |
| `uv run pytest tests/unit/test_level3_validation.py` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/focused_level3_pytest.log` |
| Level 3 net/gross cost consistency probe over `artifacts/metrics/level_3.csv` and `artifacts/equity/level_3.parquet` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/level3_net_gross_cost_probe.log` |
| `git status --short --branch --untracked-files=all` after Level 1/2 artifact restore | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/git_status_after_restore.log` |

## Test and artifact evidence

- `make test`: `83 passed`.
- Focused Level 3 pytest: `5 passed`.
- `make experiments-val`: PASS, levels `level_1`, `level_2`, and `level_3`, `final_test_exposure=NOT_EXPOSED`.
- Current Level 3 universe: 7 symbols, `BTC/USDT`, `ETH/USDT`, `XRP/USDT`, `BNB/USDT`, `SOL/USDT`, `DOGE/USDT`, `LTC/USDT`.
- Current Level 3 estimation window: `2023-01-01T00:00:00+00:00` through `2023-12-31T00:00:00+00:00`.
- Net/gross probe values:

| Method | Gross ROI | Net ROI | Net cost | Decay |
|---|---:|---:|---:|---:|
| `equal_weight` | 1.282948 | 1.281455 | 1492.5 | 0.001493 |
| `inverse_volatility` | 1.219919 | 1.218426 | 1492.5 | 0.001492 |
| `minimum_variance` | 1.115019 | 1.113527 | 1492.5 | 0.001492 |
| `cvar_downside` | 1.262462 | 1.260970 | 1492.5 | 0.001492 |

- Drawdown selection diagnostics: `selection_drawdown_constraint=0.25`, `selection_feasible_method_count=0`, `selection_fallback_used=True`, `selection_selected_method=cvar_downside`, `selection_tie_breaker=max_metric_then_min_net_turnover_then_method_order`.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None. Attempt 01 H-001 is remediated and covered by regression plus artifact probe.

- MEDIUM
  - None newly introduced. The attempt 01 drawdown-filter transparency concern is remediated in metrics and trace.

- LOW
  - Pre-existing uncommitted Stage 7 attempt 01 source/config/report changes remain visible in git status. This attempt did not revert them because they are outside the permitted restore scope and were not Level 1/2 artifact drift.

## Unresolved risks and limitations

- Final-test state remains `NOT_EXPOSED`; no final-test lock was created and no 2025 results were inspected.
- Active-market survivorship/listing bias, daily-bar execution, no order book depth, and no custody/reconciliation remain disclosed MVP limitations.
- `cvar_downside` remains a transparent standalone downside-risk heuristic, not a full scenario CVaR optimizer.
- Level 3 artifacts are untracked in this worktree until the Stage 7 checkpoint is reviewed and committed.

## Recommendation

PASS_WITH_NOTES
