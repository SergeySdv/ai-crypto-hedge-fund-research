# Role / stage / attempt

Implementation worker / Stage 8 - Level 4 dynamic portfolio rebalancing / attempt 01.

## Scope

Implemented validation-only Level 4 dynamic rebalancing for the existing small 5-7 asset portfolio through the shared panel-native broker, risk, metrics and artifact stack.

No final-test command was run. No final-test lock was created. Final-test exposure remains `NOT_EXPOSED`.

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
- `reports/agent_reports/stage_07_level3_validation/attempt_02/TEAMLEAD_DECISION.md`
- `src/crypto_hedge_fund/experiments/level_3.py`
- `src/crypto_hedge_fund/portfolio/rebalance.py`
- `src/crypto_hedge_fund/portfolio/allocators.py`
- `tests/unit/test_level3_validation.py`
- `tests/unit/test_portfolio_allocation.py`

## Assumptions and decisions

- Level 4 keeps the Stage 7 validation small universe fixed: `BTC/USDT`, `ETH/USDT`, `XRP/USDT`, `BNB/USDT`, `SOL/USDT`, `DOGE/USDT`, `LTC/USDT`.
- The Level 4 allocator uses the Stage 7 selected `cvar_downside` allocator by default. It remains described as a downside-risk heuristic, not a full scenario CVaR optimizer.
- Candidate policies are dynamic policies only; `static_level3_benchmark` is reported as a benchmark and is not eligible for Level 4 policy selection.
- The selected dynamic policy is `calendar_monthly`. `drift_monthly` and `signal_risk_monthly` had stronger validation return/risk metrics but breached the configured annual turnover constraint, so the validation utility selected the feasible lower-turnover policy.
- Rolling estimates use completed historical bars only and execute through the existing next-open `SimulatedBroker`.
- The optional Level 4 final-vintage plan is planning-only and contains no 2025 performance.

## Files inspected or changed

Changed:

- `.gitignore`
- `configs/default.yaml`
- `configs/fast.yaml`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/experiments/__init__.py`
- `src/crypto_hedge_fund/experiments/level_4.py`
- `src/crypto_hedge_fund/portfolio/rebalance.py`
- `tests/unit/test_level4_validation.py`
- `tests/unit/test_portfolio_rebalance.py`
- `artifacts/**/level_4*`
- `artifacts/monitoring/level_4_*`
- `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/*`
- `reports/agent_reports/stage_08_level4_validation/attempt_01/IMPLEMENTATION_REPORT.md`

Inspected:

- All mandatory sources listed above.
- Existing Level 3 validation implementation, allocators, shared broker, risk gates, artifact writer and tests.

Earlier-level artifact drift from `make experiments-val` was restored to `HEAD` for tracked Level 1/2/3 artifact paths. Source/config/test/report files were not restored.

## Deliverables

- Dynamic rebalance policy helper with calendar, weight-drift, signal-change, risk-trigger, minimum-trade and turnover/cost gating.
- Validation-only Level 4 runner that writes metrics, equity, weights, orders, fills, figure, rebalance log, decision trace and planning-only final vintage plan.
- CLI wiring so `make experiments-val` runs Levels 1-4 validation.
- Focused unit tests for trigger behavior, min trade/turnover controls, shared broker usage, constraints, provenance, no final-test exposure and fail-closed optimizer behavior.
- Level 4 validation artifacts:
  - `artifacts/metrics/level_4.csv`
  - `artifacts/equity/level_4.parquet`
  - `artifacts/weights/level_4.parquet`
  - `artifacts/orders/level_4.parquet`
  - `artifacts/fills/level_4.parquet`
  - `artifacts/figures/level_4_equity_curve.png`
  - `artifacts/monitoring/level_4_rebalance_log.parquet`
  - `artifacts/monitoring/level_4_decision_trace.json`
  - `artifacts/monitoring/level_4_final_vintage_plan.json`
  - metadata sidecars for all of the above.

## Acceptance-criteria mapping

- Same small portfolio universe semantics as Stage 7: implemented and artifact probe confirmed 7 symbols.
- Time-based schedule: implemented monthly policy, selected `calendar_monthly`.
- Drift trigger: implemented and tested; `drift_monthly` candidate generated validation artifacts.
- Signal/risk triggers: implemented and tested; artifact probe found signal and risk trigger rows in the rebalance log.
- Transaction-cost/turnover controls: implemented through policy gating and post-allocation risk; selection excludes policies breaching annual turnover constraint.
- Minimum trade threshold: implemented and unit-tested.
- Max weight, liquidity and capacity constraints: enforced through existing pre/post risk gates and Level 4 snapshot capacity caps; tested on approved weights.
- Validation-only selection: implemented; artifacts are split `validation`, period `2024-01-01` to `2024-12-31`, final lock hash null.
- Rebalance log and decision trace: written with reason codes, trigger codes, before/candidate/approved weights and skip reasons.
- Shared broker usage: Level 4 tests monkeypatch and verify `SimulatedBroker.run` calls.
- Final-test quarantine: no `make final-test`; no final lock; probe confirms `NOT_EXPOSED`.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/make_test.log` |
| `make experiments-val` | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/make_experiments_val.log` |
| `uv run pytest tests/unit/test_level4_validation.py` | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/pytest_level4_validation.log` |
| Level 4 artifact/provenance/rebalance-log inspection probe | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/level4_artifact_probe.log` |
| Git visibility/status probe after restoring earlier-level artifact drift | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/git_visibility_status_probe.log` |

## Test and artifact evidence

- `make test`: 92 tests passed.
- Focused Level 4 pytest: 4 tests passed.
- Artifact probe confirmed all required Level 4 artifacts and sidecars exist.
- Artifact probe summary:
  - policies: `static_level3_benchmark`, `calendar_monthly`, `drift_monthly`, `signal_risk_monthly`;
  - selected policy: `calendar_monthly`;
  - split: `validation`;
  - period: `2024-01-01` to `2024-12-31`;
  - final lock hash: `null`;
  - trace final-test exposure: `NOT_EXPOSED`;
  - rebalance log rows: 1099;
  - submitted rebalances: 191;
  - skipped rebalances: 908;
  - calendar trigger rows: 602;
  - signal trigger rows: 3;
  - risk trigger rows: 18;
  - max weight timestamp: `2024-12-31 00:00:00+00:00`.
- Metrics inspection showed `calendar_monthly` was selected because the higher-return drift/signal policies breached the configured annual turnover constraint.

## Findings by severity

- BLOCKER: None known.
- HIGH: None known.
- MEDIUM: Dynamic Level 4 policies underperformed the static Level 3 benchmark in validation net return; this is an honest validation result, not a blocker. The selected policy is the best feasible dynamic candidate under the declared turnover constraint, not the best absolute return strategy.
- MEDIUM: `drift_monthly` and `signal_risk_monthly` produced identical validation metrics in this run, likely because signal/risk triggers did not add executions beyond the drift/calendar decisions after turnover controls. This should be reviewed by the lead for narrative clarity.
- LOW: Active Binance/CCXT survivorship and delisting bias remains inherited from prior stages.
- LOW: Daily OHLCV lacks order-book depth, intraday liquidity, custody, tax and reconciliation modeling.

## Unresolved risks and limitations

- Final-test remains unrun and must stay quarantined until all Levels 1-5 are complete and locked.
- Level 4 uses validation-only 2024 results; no 2025 performance, rankings, charts or fills were inspected.
- Capacity uses trailing daily dollar-volume participation proxies, not order-book depth.
- The Level 4 `annual_turnover` metric equals the one-year 2024 validation turnover, which is appropriate for the default validation period but should be named carefully in narrative material.
- `make experiments-val` still regenerates earlier-level artifacts as a side effect; tracked Level 1/2/3 artifact drift was restored after validation.

## Recommendation

PASS_WITH_NOTES

Level 4 dynamic validation is implemented and the required gates passed, but the lead should review the policy-selection narrative because the selected feasible dynamic policy underperforms the static benchmark and the drift/signal candidate metrics are identical in this validation run.
