# Role / stage / attempt

Independent QA reviewer / Stage 7 - Level 3 static portfolio validation / attempt 01.

## Scope

Validation-only QA of the Stage 7 implementation result. I did not declare the stage globally complete, did not run final-test commands, and did not edit implementation, configs, data, tests, artifacts, management docs or Git history.

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
- `reports/agent_reports/stage_06_level2_validation/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/IMPLEMENTATION_REPORT.md`

## Assumptions and decisions

- The Stage 7 gate is validation-only. 2025 final-test returns, rankings and charts remain quarantined.
- The Level 3 validation vintage must select and estimate from 2023 data, execute at the first 2024 open, and evaluate in 2024.
- A final-vintage plan may be prepared from 2024 data if it does not compute or inspect 2025 performance.
- Existing Stage 2 active-market survivorship/delisting bias is inherited and remains a documented limitation, not a Stage 7 blocker.
- Required commands were allowed to write their normal artifacts. I did not manually restore side effects because the QA write scope was limited to this report and `qa_*` command logs.

## Files inspected or changed

Inspected:

- Stage docs and management reports listed above.
- `src/crypto_hedge_fund/experiments/level_3.py`
- `src/crypto_hedge_fund/portfolio/allocators.py`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/experiments/__init__.py`
- `configs/default.yaml`
- `configs/fast.yaml`
- `tests/unit/test_level3_validation.py`
- `tests/unit/test_portfolio_allocation.py`
- Required Level 3 artifacts and metadata sidecars under `artifacts/`.

Changed by me:

- `reports/agent_reports/stage_07_level3_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/qa_*`

Command side effects observed:

- `make experiments-val` regenerated tracked Level 1/2 artifacts and left them modified in the working tree. See `qa_git_status_after_gates.log`.

## Deliverables

- Required gate logs captured under `reports/agent_reports/stage_07_level3_validation/attempt_01/command_logs/qa_*`.
- Artifact, provenance, final-test quarantine and Git visibility probes completed.
- This QA report with findings and recommendation.

## Acceptance-criteria mapping

- Required commands: all mandatory gate commands passed.
- Level 3 universe: PASS. Validation artifacts show 7 selected assets: `BTC/USDT`, `ETH/USDT`, `XRP/USDT`, `BNB/USDT`, `SOL/USDT`, `DOGE/USDT`, `LTC/USDT`.
- Exact trailing 12 months: PASS. Config and artifacts use `2023-01-01` through `2023-12-31` for validation estimation.
- Static validation holdout: PASS. Weights/orders/fills/equity are timestamped from `2024-01-01` through `2024-12-31`, with one initial order/fill set on `2024-01-01`.
- Required methods: PASS. `level_3.csv` contains `equal_weight`, `inverse_volatility`, `minimum_variance`, and `cvar_downside`; `cvar_downside` is selected.
- Shared stack: PASS. Implementation calls `SimulatedBroker`, `PreAllocationRiskPolicy`, `PostAllocationRiskPolicy`, and `resolve_risk_approval_targets`.
- Artifact presence and Git visibility: PASS. Required Level 3 artifacts and `.metadata.json` sidecars exist and are not ignored.
- Provenance: PASS_WITH_NOTES. Sidecars include validation split, data/config/git hashes, dirty-state hash, period, cost assumptions, benchmark, seed and `final_test_lock_hash: null`. They do not include full train/validation/test-period arrays, but current Stage 3 artifact convention appears to use `period_start`/`period_end`.
- Final-test exposure: PASS. No `artifacts/final_test_lock.json` exists, Level 3 metrics are validation-labeled, and the final-vintage plan states `NOT_EXPOSED` / `planned_not_executed`.
- Gross/net metric correctness: FAIL. See HIGH finding.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `command_logs/qa_uv_sync_frozen.log` |
| `make lint` | 0 | `command_logs/qa_make_lint.log` |
| `make test` | 0 | `command_logs/qa_make_test.log` |
| `make experiments-val` | 0 | `command_logs/qa_make_experiments_val.log` |
| `uv run pytest tests/unit/test_level3_validation.py` | 0 | `command_logs/qa_focused_level3_pytest.log` |
| Level 3 artifact contract probe v1 | 1 | `command_logs/qa_level3_artifact_contract.log`; QA script assumed direct period/status columns, superseded by v2 |
| Level 3 artifact contract probe v2 | 0 | `command_logs/qa_level3_artifact_contract_v2.log` |
| Level 3 trace probe v1 | 1 | `command_logs/qa_level3_trace_probe.log`; QA script failed on nested final-plan weight dict, superseded by v2 |
| Level 3 trace probe v2 | 0 | `command_logs/qa_level3_trace_probe_v2.log` |
| Level 3 no-final-metrics probe | 0 | `command_logs/qa_level3_no_final_metrics_probe.log` |
| Level 3 gross/net cost consistency probe | 0 | `command_logs/qa_level3_gross_net_cost_probe.log` |
| Final-test exposure state probe | 0 | `command_logs/qa_final_test_state_probe.log` |
| Git visibility probe for Level 3 artifacts | 0 | `command_logs/qa_git_visibility_level3.log` |
| Git status/diff scope after gates | 0 | `command_logs/qa_git_status_after_gates.log` |

## Test and artifact evidence

- `make test`: 82 tests passed.
- Focused Level 3 tests: 4 tests passed.
- `make experiments-val`: generated Levels 1, 2 and 3 validation artifacts and printed `final_test_exposure: "NOT_EXPOSED"`.
- Required Level 3 artifacts exist with sidecars:
  - `artifacts/metrics/level_3.csv`
  - `artifacts/equity/level_3.parquet`
  - `artifacts/weights/level_3.parquet`
  - `artifacts/orders/level_3.parquet`
  - `artifacts/fills/level_3.parquet`
  - `artifacts/figures/level_3_equity_curve.png`
  - `artifacts/monitoring/level_3_decision_trace.json`
  - `artifacts/monitoring/level_3_universe_selection.csv`
  - `artifacts/monitoring/level_3_final_vintage_plan.json`
- Git visibility probe reports each required Level 3 artifact as `VISIBLE`; all Level 3 artifacts and sidecars appear in `git ls-files --others --exclude-standard`.
- Metrics shape is 4 rows x 134 columns. Methods are exactly `cvar_downside`, `equal_weight`, `inverse_volatility`, `minimum_variance`.
- Metrics provenance period is only `2024-01-01` to `2024-12-31`. The only `2025` occurrence in `level_3.csv` is the warning `final_vintage_plan_has_no_2025_performance`.
- Final-vintage plan records `status: planned_not_executed`, `final_test_exposure: NOT_EXPOSED`, estimation `2024-01-01` to `2024-12-31`, and evaluation period not run `2025-01-01` to `2025-12-31`.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - H-001: Level 3 after-cost performance metrics rebase away the entry cost, so net ROI/return/Sharpe are not reliable as net-after-fees primary metrics. In `artifacts/metrics/level_3.csv`, every method has positive `net_total_cost` (`1492.5`) but `net_roi` is higher than `gross_roi`; for example `cvar_downside` reports `gross_roi=1.262462` and `net_roi=1.264349`. The cost probe shows the first validation row already has post-cost `nav=998507.5` and `gross_nav=1000000.0`, so metrics calculated from the first row exclude the entry cost from return normalization. From initial capital, `cvar_downside` net ROI is `1.2609696597`, below gross ROI `1.2624621597`, as expected. Implementation evidence: [level_3.py](/Users/sergei/PycharmProjects/codex_crypto_hedge_fund_handoff/src/crypto_hedge_fund/experiments/level_3.py:140) trims the broker result before metrics, and [level_3.py](/Users/sergei/PycharmProjects/codex_crypto_hedge_fund_handoff/src/crypto_hedge_fund/experiments/level_3.py:616) calculates metrics from the trimmed equity. Evidence: `qa_level3_gross_net_cost_probe.log`. This violates the Stage 7 artifact requirement that net after fees/slippage is primary.

- MEDIUM
  - M-001: `make experiments-val` still regenerates tracked Level 1/2 validation artifacts as a side effect and left them modified after the required QA run. This is an operational scoping risk already tracked as R-015. Evidence: `qa_git_status_after_gates.log`. Team lead should decide whether to restore previous-level artifacts before checkpointing or intentionally commit a coordinated refresh with documentation.

- LOW
  - L-001: The focused Level 3 tests cover artifact writing/provenance but do not automate the Git ignore visibility check. QA verified visibility externally in `qa_git_visibility_level3.log`, so this is not blocking.
  - L-002: The final-vintage plan sidecar reuses validation provenance (`split: validation`, validation period), while the payload itself contains final estimation dates and `planned_not_executed` status. This is acceptable for quarantine, but a clearer final-plan-specific provenance period would reduce reviewer confusion before pretest freeze.

## Unresolved risks and limitations

- Active Binance/CCXT universe survivorship and delisting bias remains inherited from Stage 2 and is disclosed in Level 3 warnings.
- Final-test state remains `NOT_EXPOSED`; no final-test lock exists.
- Level 3 artifacts record `git_worktree_dirty=true`, expected for worker-generated artifacts before a Stage 7 checkpoint.
- CVaR-downside is a transparent standalone downside-risk heuristic, not a full scenario CVaR optimization program.
- Daily bars do not model intraday liquidity, order-book depth, custody, exchange outages, tax, or real reconciliation.

## Recommendation

REWORK

All required commands passed and the main Level 3 structure is present, but the unresolved HIGH finding means the stage should not be accepted yet. Regenerate Level 3 artifacts after fixing net metric calculation so initial execution costs are included in net performance normalization, and add a regression test that net after-cost total return/ROI cannot exceed gross when costs are positive and price paths are otherwise identical.
