# Role / stage / attempt

Independent QA reviewer / Stage 8 - Level 4 dynamic portfolio rebalancing / attempt 01.

## Scope

Validated the Stage 8 attempt 01 Level 4 implementation and artifacts only. I did not declare global stage completion, did not run final-test commands, did not create a final-test lock, and did not edit implementation/config/test/artifact files.

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
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/teamlead/PROJECT_STATE.md`
- `reports/teamlead/STAGE_BOARD.md`
- `reports/teamlead/REQUIREMENTS_STATUS.md`
- `reports/teamlead/RISK_REGISTER.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_08_level4_validation/attempt_01/IMPLEMENTATION_REPORT.md`
- Relevant implementation/tests/artifacts: `src/crypto_hedge_fund/experiments/level_4.py`, `src/crypto_hedge_fund/portfolio/rebalance.py`, `tests/unit/test_level4_validation.py`, `tests/unit/test_portfolio_rebalance.py`, Level 4 artifact files and sidecars.

## Assumptions and decisions

- Treated `*.metadata.json` as the repository's sidecar convention.
- Treated provenance-prefixed metrics columns as satisfying split/period/final-lock labeling where bare columns are absent.
- Treated the planning-only Level 4 final vintage file as acceptable because it explicitly says no 2025 metrics/charts/fills are computed.
- Initial artifact probe attempts used mismatched column/sidecar assumptions; the corrected schema-aware probe is `qa_level4_artifact_rebalance_provenance_probe_v4.log`.

## Files inspected or changed

Changed:

- `reports/agent_reports/stage_08_level4_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/qa_*`

Inspected:

- Mandatory docs/reports listed above.
- Level 4 source/tests and generated Level 4 metrics, equity, weights, orders, fills, figure, rebalance log, decision trace, final-vintage plan and metadata sidecars.

Command side effects observed:

- `make experiments-val` regenerated tracked Level 1-3 validation artifacts and created Level 4 artifacts. This is identified for lead cleanup/checkpoint policy.

## Deliverables

- Required gate logs under `command_logs/qa_*`.
- Independent artifact/rebalance/provenance probe.
- Git visibility/status probe for Level 4 artifacts and sidecars.
- This QA report.

## Acceptance-criteria mapping

- Gate commands: PASS.
- Level 4 artifacts and sidecars: present.
- Git visibility: Level 4 artifacts are untracked but visible to Git via `.gitignore` negation rules.
- Metrics: include `static_level3_benchmark`, `calendar_monthly`, `drift_monthly`, `signal_risk_monthly`; selected policy is `calendar_monthly`; provenance split is `validation`; period is `2024-01-01` to `2024-12-31`; final lock hash is null.
- Rebalance log: includes trigger/reason codes, submitted and skipped rows, calendar/drift/signal/risk evidence, before/candidate/approved weights, cost/turnover/risk fields.
- Final-test quarantine: `artifacts/final_test_lock.json` absent; trace and plan report `NOT_EXPOSED`; no final-test command run.
- Stage 8 scope: no implementation edits by QA.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `command_logs/qa_uv_sync_frozen.log` |
| `make lint` | 0 | `command_logs/qa_make_lint.log` |
| `make test` | 0 | `command_logs/qa_make_test.log` |
| `make experiments-val` | 0 | `command_logs/qa_make_experiments_val.log` |
| `uv run pytest tests/unit/test_level4_validation.py` | 0 | `command_logs/qa_pytest_level4_validation.log` |
| Level 4 artifact/rebalance/provenance probe | 0 | `command_logs/qa_level4_artifact_rebalance_provenance_probe_v4.log` |
| Level 4 rebalance cross-tab probe | 0 | `command_logs/qa_level4_rebalance_cross_tab_probe.log` |
| Git status and Level 4 visibility probe | 0 | `command_logs/qa_git_visibility_status_probe.log` |

## Test and artifact evidence

- `make test`: 92 passed.
- Focused Level 4 pytest: 4 passed.
- `make experiments-val`: generated Levels 1-4 validation outputs and reported final-test exposure `NOT_EXPOSED`.
- Level 4 required files and `*.metadata.json` sidecars all exist.
- Metrics policies:
  - `static_level3_benchmark`
  - `calendar_monthly` selected
  - `drift_monthly`
  - `signal_risk_monthly`
- Metrics evidence:
  - split: `validation`
  - period: `2024-01-01` through `2024-12-31`
  - final lock hash: null
  - selected policy: `calendar_monthly`
- Rebalance log:
  - shape: 1099 rows x 38 columns
  - submitted-to-broker rows: 191
  - skipped policy rows: 908
  - evidence rows: calendar 602, drift 1536, signal 3, risk 18
  - non-empty weight fields: before 1099, candidate 1012, approved 1099
- Artifact shapes:
  - equity: 1227 rows
  - weights: 1227 rows
  - orders: 118 rows
  - fills: 118 rows
- Final quarantine:
  - `artifacts/final_test_lock.json` absent
  - `level_4_decision_trace.json` has `final_test_exposure=NOT_EXPOSED`
  - `level_4_final_vintage_plan.json` warns no 2025 metrics/charts/fills are computed.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None.

- MEDIUM
  - `make experiments-val` regenerated tracked Level 1-3 artifact files in the working tree. This is consistent with prior-stage risk R-015 and needs lead cleanup/checkpoint policy before commit, but it does not invalidate Level 4 behavior.
  - Dynamic Level 4 policies underperformed the static Level 3 benchmark in validation net ROI and Sharpe. The selected feasible dynamic policy is valid under the declared turnover constraint, but the narrative must not imply it improved on static validation performance.

- LOW
  - `drift_monthly` and `signal_risk_monthly` have identical validation metrics in this run. The rebalance log contains signal/risk trigger evidence, but the final executions after turnover/risk controls converge to the same result; this needs narrative clarity.
  - The rebalance log has `before_weights`, `candidate_weights`, and `approved_weights`, but no separate explicit `after_weights` column. The post-execution timeline is available through `artifacts/weights/level_4.parquet`; adding an explicit after/post-trade column would make the audit trace easier to review.
  - Management docs still list Stage 8 as `NOT_STARTED`, while the worker implementation/report exists. This is expected before team-lead acceptance but should be updated only by the lead.
  - Active Binance/CCXT survivorship and delisting bias remains inherited from prior stages.

## Unresolved risks and limitations

- Final test remains unrun and must stay quarantined until all Levels 1-5 are complete and locked.
- Level 4 final-vintage plan contains 2025 period dates for planning only; it does not contain 2025 performance.
- Capacity/liquidity controls use trailing daily dollar-volume proxies, not order-book depth or intraday liquidity.
- Daily OHLCV execution does not model exchange outages, custody, taxes, or real reconciliation.
- Artifacts record `git_worktree_dirty=true`, expected because Stage 8 changes are not yet checkpointed.

## Recommendation

PASS_WITH_NOTES

Stage 8 attempt 01 satisfies the Level 4 QA gates with no BLOCKER or HIGH findings. Lead cleanup should address earlier-level artifact drift and preserve honest narrative around static benchmark outperformance, identical drift/signal metrics, and final-test quarantine.
