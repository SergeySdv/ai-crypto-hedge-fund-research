# Role / stage / attempt

Implementation worker / Stage 3: Shared Panel-Native Execution Kernel / attempt 01.

## Scope

Implemented the shared panel-native execution foundation for later strategy levels:
market-data access, next-open simulated broker, ledger outputs, risky-notional cost
accounting, performance metrics, and provenance-aware artifact writers. No strategy
levels, agents, risk gates, notebook, presentation, final report, live trading, or
final-test runs were implemented.

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
- `reports/agent_reports/stage_02_frozen_data/attempt_02/TEAMLEAD_DECISION.md`

## Assumptions and decisions

- Used the existing Stage 1 `build_daily_research_clock` convention: a signal from a
  completed daily bar executes at the first later daily open, never at the same close.
- Kept the engine panel-native: one-symbol schedules are a special case of the same
  DataFrame/MultiIndex panel path used for multi-symbol schedules.
- Target weights are long-only risky weights; cash is the residual and is never a
  fee-bearing instrument.
- Valid but unfundable trades, such as 100% risky target weights with nonzero costs
  and no cash buffer, fail closed with `InfeasibleTradeError`.
- Artifact provenance is stored both as repeated artifact columns and sidecar JSON
  metadata files for reviewability.

## Files inspected or changed

Inspected:

- `src/crypto_hedge_fund/types.py`
- `src/crypto_hedge_fund/config.py`
- `src/crypto_hedge_fund/provenance.py`
- `src/crypto_hedge_fund/clock.py`
- `src/crypto_hedge_fund/data/storage.py`
- `src/crypto_hedge_fund/data/schema.py`
- `configs/default.yaml`
- `configs/fast.yaml`
- `pyproject.toml`
- `Makefile`
- existing unit tests under `tests/unit/`

Changed or created:

- `src/crypto_hedge_fund/execution/__init__.py`
- `src/crypto_hedge_fund/execution/panel.py`
- `src/crypto_hedge_fund/execution/costs.py`
- `src/crypto_hedge_fund/execution/ledger.py`
- `src/crypto_hedge_fund/execution/broker.py`
- `src/crypto_hedge_fund/metrics/__init__.py`
- `src/crypto_hedge_fund/metrics/performance.py`
- `src/crypto_hedge_fund/artifacts/__init__.py`
- `src/crypto_hedge_fund/artifacts/writers.py`
- `tests/unit/test_execution_kernel.py`
- `tests/unit/test_costs.py`
- `tests/unit/test_metrics.py`
- `tests/unit/test_artifacts.py`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/*`

## Deliverables

- `PanelMarketData` normalizes long-form OHLCV into a UTC `(bar_start_utc, symbol)`
  panel and fails explicitly on missing/invalid execution or valuation opens.
- `CostAssumptions`, `CostBreakdown`, and `WeightDeltaCostModel` implement
  risky-notional fee/slippage and reporting-turnover accounting.
- `PositionSnapshot` and `EquitySnapshot` provide typed ledger records for holdings
  and portfolio-level equity rows.
- `SimulatedBroker` executes target-risky-weight schedules through the shared broker
  and ledger path only, creating equity, weights, orders, and fills DataFrames.
- Long-only unlevered target validation rejects negative, non-finite, duplicate, and
  over-budget risky weights.
- `calculate_performance_metrics` reports ROI/total return, CAGR, volatility,
  Sharpe, Sortino, Calmar, maximum drawdown, drawdown duration, turnover, exposure,
  trade count, fees, slippage, and total costs.
- `BacktestArtifactWriter` writes metrics/equity/weights/orders/fills artifacts with
  stable provenance columns and JSON metadata sidecars.

## Acceptance-criteria mapping

- Completed-bar signal cannot affect same-close or prior PnL:
  `tests/unit/test_execution_kernel.py::test_completed_bar_signal_fills_only_at_next_open_and_has_no_earlier_pnl`.
- Cash to asset, asset to cash, asset A to asset B, partial rebalance, and no-change
  costs: `tests/unit/test_costs.py`.
- Cash is not charged as a traded instrument:
  `test_cash_to_asset_charges_one_risky_trade_and_no_cash_instrument`.
- Missing next-open price blocks execution:
  `test_missing_next_open_price_blocks_execution_explicitly`.
- Invalid weights fail closed:
  `test_invalid_and_infeasible_weights_fail_closed` and `test_invalid_weights_fail_closed`.
- One-symbol and multi-symbol configurations use the same engine:
  `test_one_symbol_and_multi_symbol_use_same_engine_and_are_deterministic`.
- Deterministic repeatability:
  same test compares repeated equity and order DataFrames.
- Artifacts carry provenance and stable schema:
  `tests/unit/test_artifacts.py::test_artifact_writers_add_provenance_and_stable_schema`.
- No final-test contamination:
  no final-test command was run; no strategy returns, rankings, or charts were created.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/make_test.log` |
| `uv run pytest tests/unit/test_execution_kernel.py tests/unit/test_costs.py tests/unit/test_metrics.py tests/unit/test_artifacts.py` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/pytest_stage3_unit.log` |
| `git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/git_status_short_branch_untracked.log` |

## Test and artifact evidence

- Full suite: 39 tests passed in `make_test.log`.
- Stage 3 suite: 13 tests passed in `pytest_stage3_unit.log`.
- Lint: Ruff format check and Ruff check passed in `make_lint.log`.
- Artifact writer test verifies metrics CSV, Parquet artifact metadata columns, and
  metadata sidecar JSON. Test artifacts are written only to pytest `tmp_path`.

## Findings by severity

- BLOCKER: None.
- HIGH: None.
- MEDIUM: Stage 4 risk gates should account for cost cash buffers before sending
  fully invested target weights to the broker; Stage 3 currently fails closed when
  costs make an otherwise valid target unfundable.
- LOW: The broker models full fills at daily open with fixed one-way fee/slippage.
  Precision, minimum notional, participation, stale valuation windows, and partial
  fills remain future stage work.

## Unresolved risks and limitations

- No pre/post risk gates are implemented in this stage; only clean contracts and
  fail-closed execution behavior exist for later integration.
- Metrics are deterministic point estimates. Statistical uncertainty, bootstrap,
  benchmark-relative analytics beyond total return, and prediction metrics remain
  later-stage responsibilities.
- Artifact writers provide the schema and provenance contract but no level artifacts
  were generated in repository `artifacts/`.
- Binance active-market survivorship/delisting bias from Stage 2 remains disclosed
  and unchanged.

## Recommendation

PASS_WITH_NOTES
