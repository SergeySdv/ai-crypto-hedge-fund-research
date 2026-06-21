# Role / stage / attempt

Independent portfolio/risk specialist and architecture reviewer / Stage 7 - Level 3 static portfolio validation / attempt 01.

## Scope

Reviewed the uncommitted Stage 7 implementation for Level 3 static portfolio methodology, risk controls, trailing-window correctness, shared architecture use, artifact provenance, requirement traceability and final-test quarantine. I did not run or inspect final-test results and I do not declare the stage globally complete.

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
- `reports/agent_reports/stage_06_level2_validation/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/IMPLEMENTATION_REPORT.md`

## Assumptions and decisions

- Stage 7 is validation-only. The correct Level 3 validation vintage is 2023 estimation and 2024 OOS holdout; the 2024 estimation and 2025 OOS path may be planned but must not execute or report 2025 performance before final-test freeze.
- I treat the `cvar_downside` method as acceptable for Stage 7 only because it is transparently implemented and labeled as inverse standalone downside-tail-risk allocation, not as a full portfolio CVaR linear program.
- Active-market survivorship/listing bias remains an accepted project limitation from Stage 2 and is not a new Stage 7 blocker, provided it remains disclosed.

## Files inspected or changed

Inspected implementation/config/test/artifact paths:

- `.gitignore`
- `configs/default.yaml`
- `configs/fast.yaml`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/experiments/__init__.py`
- `src/crypto_hedge_fund/experiments/level_3.py`
- `src/crypto_hedge_fund/portfolio/__init__.py`
- `src/crypto_hedge_fund/portfolio/allocators.py`
- `tests/unit/test_level3_validation.py`
- `tests/unit/test_portfolio_allocation.py`
- `artifacts/metrics/level_3.csv`
- `artifacts/equity/level_3.parquet`
- `artifacts/weights/level_3.parquet`
- `artifacts/orders/level_3.parquet`
- `artifacts/fills/level_3.parquet`
- `artifacts/monitoring/level_3_decision_trace.json`
- `artifacts/monitoring/level_3_universe_selection.csv`
- `artifacts/monitoring/level_3_final_vintage_plan.json`

Changed only:

- `reports/agent_reports/stage_07_level3_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/arch_git_diff_status.log`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/arch_git_diff_status.status`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/arch_targeted_rg.log`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/arch_targeted_rg.status`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/arch_focused_pytest.log`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/arch_focused_pytest.status`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/arch_level3_artifact_probe.log`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/arch_level3_artifact_probe.status`

## Deliverables

- Verified the validation universe contains exactly 7 assets: `BTC/USDT`, `ETH/USDT`, `XRP/USDT`, `BNB/USDT`, `SOL/USDT`, `DOGE/USDT`, `LTC/USDT`.
- Verified those assets are liquid/popular enough for Level 3 under the frozen data proxy: 2023 median dollar volumes range from about USD 45.9M to USD 1.32B, ranked at the 2023 cutoff.
- Verified the validation estimation window is exactly `2023-01-01T00:00:00+00:00` through `2023-12-31T00:00:00+00:00`, with execution at `2024-01-01T00:00:00+00:00` and validation artifacts bounded to 2024.
- Verified universe selection uses 2023 coverage/liquidity and excludes a fixture symbol whose liquidity only improves after the cutoff.
- Verified equal weight, inverse volatility, shrinkage minimum variance and `cvar_downside` methods are implemented and compared.
- Verified long-only/unlevered constraints, explicit cash buffer, 30% per-asset cap, pre-allocation risk, post-allocation risk and optimizer-failure-to-cash behavior.
- Verified Level 3 uses `SimulatedBroker` and shared broker/fill/order/ledger/metrics/artifact paths rather than standalone portfolio math for reported performance.
- Verified artifacts contain validation provenance, costs, git/data/config hashes, `final_test_lock_hash: null`, and warnings for validation-only/no-final-test metrics.
- Verified real-trading limitations are disclosed in the decision trace.

## Acceptance-criteria mapping

- 5-7 liquid assets: PASS. `level_3_universe_selection.csv` has 7 selected assets with complete 365-day 2023 estimation coverage and high trailing median dollar volume.
- Exact trailing 12-month window: PASS. Config and `_validate_trailing_12_months` enforce 2023-01-01 through 2023-12-31 for validation; focused tests cover exactness.
- Validation holdout semantics: PASS. Metrics/weights are validation split, period `2024-01-01` to `2024-12-31`; final-vintage plan says `planned_not_executed`.
- Absence of look-ahead/future universe membership: PASS_WITH_NOTES. Validation selection is cutoff-based and tested. The final-vintage plan uses 2024 data only to compute planned 2025 weights, without 2025 performance. Active-market survivorship bias remains disclosed.
- Required methods: PASS. Four methods exist and produce artifacts.
- Robust method defensibility: PASS_WITH_NOTES. `cvar_downside` is a defensible robust heuristic if described as inverse standalone 5% downside CVaR allocation, not as a full portfolio CVaR optimizer.
- Risk controls and fail-closed behavior: PASS_WITH_NOTES. Allocation uses pre/post risk and optimizer failure resolves to cash. Method selection has a drawdown-filter fallback that should be logged more explicitly; see MEDIUM finding.
- Shared architecture: PASS. Experiment calls `SimulatedBroker`, shared risk policies, shared metrics and artifact writer conventions.
- Provenance and decision trace: PASS_WITH_NOTES. Trace is adequate, but selection-filter fallback metadata should be added before final freeze.
- Real-trading limitations: PASS. Trace discusses orders from weights, costs, daily-bar/no-order-book limits, survivorship, custody/reconciliation and exchange metadata approximation.
- Final-test quarantine: PASS. I did not run `make final-test`. Artifacts show validation split, `final_test_lock_hash: null`, and `final_test_exposure: NOT_EXPOSED`.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `git diff --stat; git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/arch_git_diff_status.log` |
| `rg -n ... level_3.py allocators.py tests configs cli.py` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/arch_targeted_rg.log` |
| `PYTEST_ADDOPTS='-p no:cacheprovider' uv run pytest tests/unit/test_level3_validation.py tests/unit/test_portfolio_allocation.py` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/arch_focused_pytest.log` |
| `uv run python - <<'PY' ... Level 3 artifact/provenance probe ... PY` | 0 | `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/arch_level3_artifact_probe.log` |

## Test and artifact evidence

- Focused tests: `15 passed in 2.67s`.
- Level 3 metrics include four rows and one selected method:
  - `equal_weight`: net Sharpe `1.680429`, net max drawdown `-0.363251`.
  - `inverse_volatility`: net Sharpe `1.671700`, net max drawdown `-0.351633`.
  - `minimum_variance`: net Sharpe `1.658232`, net max drawdown `-0.328017`.
  - `cvar_downside`: selected, net Sharpe `1.701317`, net max drawdown `-0.347085`.
- Target risky weight sum is `0.995` and target cash weight is `0.005` for all methods; target max weight is at or below the 30% cap.
- Universe evidence:
  - all 7 selected symbols have `estimation_valid_days = 365`;
  - `selection_cutoff_bar_start = 2023-12-31T00:00:00+00:00`;
  - `selection_feature_cutoff = 2024-01-01T00:00:00+00:00`;
  - `estimation_start = 2023-01-01T00:00:00+00:00`;
  - `estimation_end = 2023-12-31T00:00:00+00:00`.
- Execution evidence:
  - orders and fills are timestamped `2024-01-01T00:00:00+00:00`;
  - fills charge fees and slippage separately;
  - artifacts contain 26 orders and 26 fills across all methods.
- Decision trace evidence:
  - representative clock has bar start `2023-12-31`, feature/decision/execution time `2024-01-01`;
  - representative `cvar_downside` proposal metadata states: `allocate inverse to standalone 5% downside CVaR subject to long-only caps and gross budget`;
  - `final_vintage_status` is `planned_not_executed_no_2025_performance`.
- Final-vintage plan evidence:
  - `status = planned_not_executed`;
  - `final_test_exposure = NOT_EXPOSED`;
  - final estimation is `2024-01-01` through `2024-12-31`;
  - `evaluation_period_not_run = ["2025-01-01", "2025-12-31"]`;
  - warning says no 2025 returns, metrics, rankings, charts or fills are computed.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None.

- MEDIUM
  - The configured method-selection drawdown filter is not transparent when no method satisfies it. `_select_method` filters on `rebalance.max_drawdown_constraint = 0.25`, but the artifact probe shows all methods breach that threshold: absolute net max drawdowns are about 32.8% to 36.3%. The implementation falls back to selecting from all methods and chooses `cvar_downside` by net Sharpe, but the trace does not explicitly say the drawdown filter had zero feasible candidates or that fallback selection was used. This is not a leakage or final-test issue, but it weakens reviewability of the predeclared validation criterion. Recommended remediation before freeze: record feasible count, drawdown constraint, fallback status and tie-breaker in metrics/trace.

- LOW
  - `cvar_downside` should remain labeled as a heuristic robust allocation, not a full CVaR optimizer. Current source/artifacts are mostly clear, but later notebook/deck/report wording must avoid claiming a solved portfolio CVaR program.
  - Level 3 artifacts are generated from a dirty uncommitted worktree, with `git_worktree_dirty=true`. This is expected for a worker handoff but should be regenerated from a clean Stage 7 checkpoint before pretest/final artifacts.
  - `make experiments-val` side effects on earlier-level artifacts remain a process risk inherited from Stage 6/worker report. Not a Level 3 methodology blocker, but the team lead should maintain an explicit artifact refresh/restore policy.

## Unresolved risks and limitations

- Active Binance market survivorship/delisting bias remains accepted for the MVP and is disclosed; it must stay prominent in final report/deck/notebook.
- Daily OHLCV bars do not model intraday liquidity, spreads, order-book depth, exchange outages, custody, tax or operational reconciliation.
- The final 2025 Level 3 evaluation remains intentionally unrun until final-test freeze.
- The validation-selected method relies on one 2024 holdout year; the outcome is high variance and should be presented as educational/research evidence, not an alpha claim.

## Recommendation

PASS_WITH_NOTES

No BLOCKER or HIGH findings were identified. Stage 7 attempt 01 is architecturally compatible with later Level 4 dynamic rebalancing and Level 5 large-universe work, provided the team records the drawdown-filter fallback explicitly and preserves the robust-method wording as a transparent heuristic.
