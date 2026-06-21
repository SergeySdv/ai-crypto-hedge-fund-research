# Role / stage / attempt

Implementation worker / Stage 7 - Level 3 static portfolio validation / attempt 01.

## Scope

Implemented validation-only Level 3 static portfolio construction for a 5-7 asset crypto basket through the existing panel-native broker, cost model, risk gates, metrics and artifact contract. This attempt does not claim the stage is passed; it is a worker handoff for team-lead review.

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
- `docs/10_RISKS_AND_DECISIONS.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/teamlead/PROJECT_STATE.md`
- `reports/teamlead/STAGE_BOARD.md`
- `reports/teamlead/REQUIREMENTS_STATUS.md`
- `reports/teamlead/RISK_REGISTER.md`
- `reports/agent_reports/stage_06_level2_validation/attempt_02/TEAMLEAD_DECISION.md`

## Assumptions and decisions

- Validation Level 3 uses the documented prior vintage: select universe and estimate weights on `2023-01-01` through `2023-12-31`; execute at the first 2024 open; evaluate through `2024-12-31`.
- The quarantined final-test year remains unscored. A final-vintage plan is written from 2024 data only, with no 2025 orders, fills, metrics, rankings or charts.
- The small universe defaults to 7 assets selected by complete 12-month coverage and trailing 12-month median dollar volume. Validation selection produced `BTC/USDT, ETH/USDT, XRP/USDT, BNB/USDT, SOL/USDT, DOGE/USDT, LTC/USDT`.
- Portfolio methods are equal weight, inverse volatility, shrinkage minimum variance and CVaR-style downside allocation. The validation-selected method is `cvar_downside` by net Sharpe, with configured drawdown filter and turnover/simplicity tie-breakers.
- Level 3 target weights reserve the configured 0.5% cash buffer for execution costs; all risky weights are long-only and capped.
- `make experiments-val` refreshes Level 1/2 tracked artifacts as a side effect. Those earlier-level artifact changes were restored after the required run to keep this worker diff Stage 7-scoped.

## Files inspected or changed

Changed implementation/config/test files:

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

Generated Level 3 artifacts:

- `artifacts/metrics/level_3.csv` and sidecar
- `artifacts/equity/level_3.parquet` and sidecar
- `artifacts/weights/level_3.parquet` and sidecar
- `artifacts/orders/level_3.parquet` and sidecar
- `artifacts/fills/level_3.parquet` and sidecar
- `artifacts/figures/level_3_equity_curve.png` and sidecar
- `artifacts/monitoring/level_3_decision_trace.json` and sidecar
- `artifacts/monitoring/level_3_universe_selection.csv` and sidecar
- `artifacts/monitoring/level_3_final_vintage_plan.json` and sidecar

Report/log files:

- `reports/agent_reports/stage_07_level3_validation/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/*`

## Deliverables

- Added Level 3 config for exact trailing 12-month validation and final-vintage planning.
- Added minimum-variance and CVaR-downside allocators under the existing `portfolio` package.
- Added validation-only `run_level_3_validation(...)`, wired into `crypto-hedge-fund experiments-val`.
- Generated validation-labeled Level 3 artifacts with provenance sidecars and `final_test_lock_hash: null`.
- Added tests for exact 5-7 asset selection, exact 12-month window, validation-only timing, optimizer fail-closed behavior, shared broker usage, artifact visibility and provenance.

## Acceptance-criteria mapping

- L3 5-7 assets: implemented and evidenced by `artifacts/monitoring/level_3_universe_selection.csv`; validation run uses 7 assets.
- Exact trailing 12 months: implemented by config and `_validate_trailing_12_months`; validation artifacts record `2023-01-01` through `2023-12-31`.
- Static portfolio management: one target schedule per method at `2023-12-31`, executed next open in 2024 and held OOS.
- Required methods: equal weight, inverse volatility, minimum variance and CVaR-downside robust method are implemented and compared.
- Shared stack: schedules execute through `SimulatedBroker`; pre/post allocation risk gates and shared metrics/artifact writer conventions are used.
- No final-test exposure: no `make final-test`, no lock creation, no 2025 performance metrics; final-vintage plan is explicitly `NOT_EXPOSED`.
- Real-trading limitations: recorded in `level_3_decision_trace.json` and artifact provenance warnings.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `command_logs/uv_sync_frozen.log` |
| `make lint` | 0 | `command_logs/make_lint.log` |
| `make test` | 0 | `command_logs/make_test.log` |
| `make experiments-val` | 0 | `command_logs/make_experiments_val.log` |
| `uv run pytest tests/unit/test_level3_validation.py` | 0 | `command_logs/focused_level3_pytest.log` |
| Level 3 artifact inspection | 0 | `command_logs/artifact_inspection_level3.log` |
| Level 3 artifact Git visibility probe | 0 | `command_logs/git_visibility_level3_artifacts.log` |

## Test and artifact evidence

- Full test suite: `82 passed in 9.77s`.
- Focused Level 3 suite: `4 passed`.
- `make experiments-val` output includes `levels: ["level_1", "level_2", "level_3"]` and `final_test_exposure: "NOT_EXPOSED"`.
- Level 3 metrics inspection:
  - equal weight net Sharpe `1.680429`, net ROI `1.284866`, max drawdown `-0.363251`.
  - inverse volatility net Sharpe `1.671700`, net ROI `1.221742`, max drawdown `-0.351633`.
  - minimum variance net Sharpe `1.658232`, net ROI `1.116686`, max drawdown `-0.328017`.
  - CVaR downside selected, net Sharpe `1.701317`, net ROI `1.264349`, max drawdown `-0.347085`.
- All four methods target risky weight sum `0.995` and cash weight `0.005`.
- Level 3 artifacts include 26 orders and 26 fills across the selected validation basket.
- `level_3_final_vintage_plan.json` reports `status: planned_not_executed` and `final_test_exposure: NOT_EXPOSED`.

## Findings by severity

- BLOCKER: None identified by this worker.
- HIGH: None identified by this worker.
- MEDIUM: `make experiments-val` still regenerates Level 1/2 artifacts as a command side effect; I restored those tracked side effects after the required run. The team lead may want a later policy for multi-level artifact refreshes.
- LOW: Level 3 and later artifacts generated before a Stage 7 checkpoint record `git_worktree_dirty=true`, as expected for worker-generated artifacts before commit.

## Unresolved risks and limitations

- Active Binance market survivorship/delisting limitation remains inherited from Stage 2 and is disclosed in Level 3 provenance/trace warnings.
- CVaR-downside is a transparent standalone downside-risk heuristic, not a full scenario CVaR linear program.
- Daily bars do not model intraday liquidity, order-book spread, custody, tax, exchange outages or real reconciliation.
- Final 2025 static evaluation is intentionally not run until the project reaches pretest lock/final-test stages.

## Recommendation

PASS_WITH_NOTES
