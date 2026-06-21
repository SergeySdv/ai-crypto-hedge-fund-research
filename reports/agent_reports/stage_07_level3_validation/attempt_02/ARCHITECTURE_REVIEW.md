# Role / stage / attempt

Independent portfolio/risk specialist and architecture reviewer / Stage 7 - Level 3 static portfolio validation / attempt 02.

## Scope

Reviewed the attempt 02 remediation for Level 3 static portfolio architecture, cost/metric methodology, drawdown-filter fallback metadata, final-test quarantine, and compatibility with later Level 4/5 work. I did not edit implementation, configs, tests, artifacts, management docs, Git history, or final-test state, and I do not declare global stage completion.

## Sources read

- `AGENTS.md`
- `docs/00_GLOBAL_PLAN_AND_AUDIT.md`
- `docs/11_REQUIREMENTS_TRACEABILITY.md`
- `docs/01_ASSIGNMENT_AND_SCOPE.md`
- `docs/02_ARCHITECTURE.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`
- `docs/10_RISKS_AND_DECISIONS.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/teamlead/PROJECT_STATE.md`
- `reports/teamlead/STAGE_BOARD.md`
- `reports/teamlead/REQUIREMENTS_STATUS.md`
- `reports/teamlead/RISK_REGISTER.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_02/IMPLEMENTATION_REPORT.md`

## Assumptions and decisions

- Stage 7 remains validation-only. The valid Level 3 development vintage is 2023 estimation and 2024 OOS validation; 2025 final-test returns must remain uninspected.
- The attempt 01 H-001 bug was a reporting-normalization defect, not a broker/ledger cost-charging defect. A metric-only initial-capital baseline is the right scope because it preserves the written ledger while including initial entry fees/slippage in return calculations.
- `cvar_downside` is acceptable as the required robust method only as a transparent inverse standalone downside-CVaR heuristic, not as a claim of solving a full scenario CVaR portfolio program.
- Existing active-market survivorship/listing bias is inherited from Stage 2 and remains a disclosed limitation, not a new Stage 7 blocker.

## Files inspected or changed

Inspected:

- `src/crypto_hedge_fund/experiments/level_3.py`
- `src/crypto_hedge_fund/portfolio/allocators.py`
- `tests/unit/test_level3_validation.py`
- `tests/unit/test_portfolio_allocation.py`
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

Changed only:

- `reports/agent_reports/stage_07_level3_validation/attempt_02/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/arch_*`

## Deliverables

- Reviewed and accepted the cost-normalization remediation from a portfolio/risk methodology perspective.
- Verified the Level 3 validation artifact set still uses exactly 7 selected assets, a 2023 trailing 12-month estimation window, 2024 validation holdout, four required allocation methods, and shared broker/risk/metrics/artifact paths.
- Verified drawdown-filter fallback metadata is present in both metrics and decision trace.
- Verified final-test quarantine remains `NOT_EXPOSED`; no final lock exists and no 2025 performance artifact was inspected.
- Verified `cvar_downside` remains labeled in source/trace as an inverse standalone downside-CVaR heuristic.

## Acceptance-criteria mapping

- Cost normalization methodology: PASS. `_combined_metrics` now prepends an initial-capital baseline before shared metric calculation for both net and gross equity. Current artifacts have positive costs and `net_roi`/`net_total_return` below gross for every method.
- Shared metrics compatibility: PASS. The implementation still calls the shared `calculate_performance_metrics`; it changes only the metric input baseline, not the broker ledger or artifact equity series.
- Level 3 5-7 assets: PASS. Probe found 7 assets: `BTC/USDT`, `ETH/USDT`, `XRP/USDT`, `BNB/USDT`, `SOL/USDT`, `DOGE/USDT`, `LTC/USDT`.
- Exact trailing window and validation holdout: PASS. Universe artifacts show `2023-01-01T00:00:00+00:00` through `2023-12-31T00:00:00+00:00`, selected at `2023-12-31T00:00:00+00:00`, with validation split `2024-01-01` through `2024-12-31`.
- Required methods: PASS. Metrics contain `equal_weight`, `inverse_volatility`, `minimum_variance`, and `cvar_downside`.
- Shared architecture: PASS. Code uses `SimulatedBroker`, `PreAllocationRiskPolicy`, `PostAllocationRiskPolicy`, `resolve_risk_approval_targets`, shared metrics, and shared artifact sidecars.
- Drawdown fallback metadata: PASS. Metrics and trace record drawdown constraint `0.25`, feasible method count `0`, fallback flag `True`, selected method `cvar_downside`, selection metric `net_sharpe`, and tie-breaker `max_metric_then_min_net_turnover_then_method_order`.
- No look-ahead/final-test exposure: PASS. Validation artifacts are 2024-only; final-vintage plan is `planned_not_executed`; `artifacts/final_test_lock.json` is absent.
- Robust method labeling: PASS_WITH_NOTES. Source says `Robust inverse-CVaR allocator using standalone downside tail risk`, and metadata says inverse allocation to standalone 5% downside CVaR. Later notebook/deck/report wording must preserve that nuance.
- Compatibility with Stage 8/9: PASS. Static schedule, fixed small universe, shared broker/risk/artifact interfaces, and explicit fallback metadata are compatible with rolling Level 4 rebalancing and larger Level 5 universe scoring.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `git diff --stat; git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/arch_git_diff_status.log` |
| `rg -n ... level_3.py tests allocators configs` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/arch_targeted_rg.log` |
| `sed -n ... src/crypto_hedge_fund/experiments/level_3.py` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/arch_level3_sed.log` |
| `sed -n ... tests/unit/test_level3_validation.py` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/arch_level3_test_sed.log` |
| `sed -n ... src/crypto_hedge_fund/portfolio/allocators.py` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/arch_allocator_cvar_sed.log` |
| `PYTEST_ADDOPTS='-p no:cacheprovider' uv run pytest tests/unit/test_level3_validation.py tests/unit/test_portfolio_allocation.py` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/arch_focused_pytest.log` |
| Level 3 artifact probe v1 | 1 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/arch_level3_artifact_probe.log`; reviewer script assumed an `execution_time` column, superseded by v4 |
| Level 3 artifact probe v2 | 1 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/arch_level3_artifact_probe_v2.log`; shell quoting issue, superseded by v4 |
| Level 3 artifact probe v3 | 1 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/arch_level3_artifact_probe_v3.log`; optional trace-print key assumption, substantive checks passed, superseded by v4 |
| Level 3 artifact probe v4 | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_02/command_logs/arch_level3_artifact_probe_v4.log` |

## Test and artifact evidence

- Focused pytest: `16 passed in 3.00s`.
- Current Level 3 methods: `cvar_downside`, `equal_weight`, `inverse_volatility`, `minimum_variance`; selected method is `cvar_downside`.
- Current Level 3 universe size: 7 symbols listed above.
- Estimation evidence: `estimation_start=['2023-01-01T00:00:00+00:00']`, `estimation_end=['2023-12-31T00:00:00+00:00']`, `selection_cutoff=['2023-12-31T00:00:00+00:00']`.
- Validation artifact metadata: split `validation`, period `2024-01-01..2024-12-31`, `final_test_lock_hash=None`.
- Cost/metric evidence:
  - `equal_weight`: gross ROI `1.282948`, net ROI `1.281455`, net cost `1492.5`.
  - `inverse_volatility`: gross ROI `1.219919`, net ROI `1.218426`, net cost `1492.5`.
  - `minimum_variance`: gross ROI `1.115019`, net ROI `1.113527`, net cost `1492.5`.
  - `cvar_downside`: gross ROI `1.262462`, net ROI `1.260970`, net cost `1492.5`.
- Execution evidence: orders and fills occur only at `2024-01-01T00:00:00+00:00`; equity/weights run through `2024-12-31T00:00:00+00:00`.
- Drawdown fallback evidence: trace has `selection_drawdown_constraint=0.25`, `selection_feasible_method_count=0`, `selection_fallback_used=True`, `selection_selected_method=cvar_downside`.
- Final-test quarantine evidence: final-vintage plan status is `planned_not_executed`, exposure is `NOT_EXPOSED`, and evaluation period not run is `['2025-01-01', '2025-12-31']`.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None. Attempt 01 H-001 is closed from a methodology perspective.

- MEDIUM
  - None.

- LOW
  - Stage 7 source/artifact/report files remain untracked or dirty in the worktree, which is expected before the team lead checkpoint but should be resolved at the Stage 7 commit/tag gate.
  - Teamlead management docs still describe Stage 7 as not started/attempt 01 in places. I did not update them because this review write scope is restricted.

## Unresolved risks and limitations

- Final-test state remains `NOT_EXPOSED`; the 2025 Level 3 final evaluation is intentionally unrun until the project-wide final-test lock.
- Active Binance/CCXT universe survivorship and delisting bias remains an accepted MVP limitation and must stay visible in final narrative artifacts.
- Daily OHLCV validation does not model intraday spreads, order-book depth, exchange outages, custody, tax, or real reconciliation.
- `cvar_downside` is a robust heuristic based on standalone downside tail risk, not a full portfolio CVaR optimizer.
- One-year 2024 validation is inherently high variance; results should be presented as educational/research evidence, not a profitability claim.

## Recommendation

PASS_WITH_NOTES

Attempt 02 resolves the net/gross metric defect, adds adequate fallback-selection metadata, and preserves the Level 3 validation architecture and final-test quarantine. No unresolved BLOCKER or HIGH findings remain.
