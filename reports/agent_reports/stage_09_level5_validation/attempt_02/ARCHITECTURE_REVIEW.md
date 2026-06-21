# Role / stage / attempt

Independent architecture, large-universe, and portfolio/risk reviewer / Stage 9 - Level 5 validation / attempt 02.

## Scope

Reviewed Stage 9 attempt 02 for shared-architecture compliance, 100+ pair Level 5 validation evidence, point-in-time scoring, next-open timing, dynamic portfolio/risk controls, monitoring/fail-safes, artifact provenance, and final-test quarantine.

No implementation, config, test, or generated trading artifact files were edited.

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
- `reports/agent_reports/stage_08_level4_validation/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_09_level5_validation/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_09_level5_validation/attempt_02/IMPLEMENTATION_REPORT.md`

## Assumptions and decisions

- I treated Stage 9 as a validation-stage architecture gate, not a final-test or profitability gate.
- I did not run `make final-test`, `make pretest-freeze`, or any final-test command.
- I decided the short late-December 2024 validation window is acceptable for Stage 9 under the frozen data constraint because it proves the hard 100-pair shared-pipeline path before final-test exposure. It is not sufficient evidence for robust performance claims or final model/policy confidence by itself.
- I accepted active-market survivorship as inherited project risk already disclosed in earlier stages, not a new Stage 9 blocker.

## Files inspected or changed

Inspected:

- Stage 9 diffs in `.gitignore`, `configs/default.yaml`, `configs/fast.yaml`, `src/crypto_hedge_fund/cli.py`, `src/crypto_hedge_fund/experiments/__init__.py`, `src/crypto_hedge_fund/portfolio/allocators.py`.
- New Level 5 implementation and tests: `src/crypto_hedge_fund/experiments/level_5.py`, `src/crypto_hedge_fund/features/level5.py`, `tests/unit/test_level5_validation.py`, `tests/unit/test_large_universe_monitoring.py`.
- Shared architecture files: `src/crypto_hedge_fund/data/universe.py`, `src/crypto_hedge_fund/execution/broker.py`, `src/crypto_hedge_fund/clock.py`, `src/crypto_hedge_fund/risk/pre_allocation.py`, `src/crypto_hedge_fund/risk/post_allocation.py`, `src/crypto_hedge_fund/portfolio/allocators.py`.
- Level 5 artifacts under `artifacts/metrics`, `artifacts/equity`, `artifacts/weights`, `artifacts/orders`, `artifacts/fills`, `artifacts/figures`, and `artifacts/monitoring`.

Changed:

- `reports/agent_reports/stage_09_level5_validation/attempt_02/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_09_level5_validation/attempt_02/command_logs/arch_*.log`
- `reports/agent_reports/stage_09_level5_validation/attempt_02/command_logs/arch_*.status`

## Deliverables

- This architecture review report.
- Read-only review logs under `reports/agent_reports/stage_09_level5_validation/attempt_02/command_logs/`.

## Acceptance-criteria mapping

- Shared architecture: PASS. Level 5 uses `PanelMarketData`, `SimulatedBroker`, shared cost/ledger artifacts, `InverseVolatilityAllocator`, `DynamicRebalancePolicy`, and shared pre/post risk policies.
- Completed-bar / next-open timing: PASS. Level 5 builds `ResearchClock` from the decision bar, filters features by `bar_end_utc <= feature_cutoff`, and broker execution maps schedule rows to next opens.
- Point-in-time 100-pair universe: PASS_WITH_NOTES. `eligible_universe_at` uses bars at or before cutoff and trailing liquidity. Active-market survivorship remains disclosed.
- Actual 100-symbol scoring: PASS. `level_5_universe_scores.parquet` contains 2,400 rows: 100 scored symbols on each of 24 decision dates.
- Dynamic portfolio/risk: PASS_WITH_NOTES. Top-25 selection, liquidity caps, max weights, turnover/cost controls, pre-risk, post-risk, and cash fail-safe behavior are present. The validation run is dominated by volatility-limit cash actions.
- Monitoring/fail-safes: PASS_WITH_NOTES. Health and alerts include runtime, memory, coverage, drift proxies, calibration proxy, fallback rate, cost decay proxy, incidents, and fail-safe evidence. Some fail-safe evidence is unit-test referenced rather than all being naturally triggered in the validation artifact.
- Artifact provenance: PASS. Level 5 artifacts include split, data/config/git hashes, costs, warnings, dirty-worktree flag, and no final lock hash.
- Final-test quarantine: PASS. No final lock exists; artifacts are validation split and report `NOT_EXPOSED`.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `git diff --stat` | 0 | `command_logs/arch_git_diff_stat.log` |
| `git diff -- configs/default.yaml configs/fast.yaml src/crypto_hedge_fund/cli.py src/crypto_hedge_fund/experiments/__init__.py src/crypto_hedge_fund/portfolio/allocators.py .gitignore` | 0 | `command_logs/arch_tracked_diff.log` |
| `git status --short --branch --untracked-files=all` | 0 | `command_logs/arch_git_status.log` |
| Number Level 5 experiment source with `nl -ba` | 0 | `command_logs/arch_level5_experiment_numbered.log` |
| Number Level 5 feature source with `nl -ba` | 0 | `command_logs/arch_level5_features_numbered.log` |
| Number two tests in one `nl` command | 1 | `command_logs/arch_level5_tests_numbered.log` |
| Number Level 5 test files separately | 0 | `command_logs/arch_level5_test_validation_numbered.log`, `command_logs/arch_large_universe_monitoring_test_numbered.log` |
| Initial artifact probe | 1 | `command_logs/arch_artifact_probe.log` |
| Fixed schema-aware artifact probe | 0 | `command_logs/arch_artifact_probe_v2.log` |
| Final-lock find probe | 0 | `command_logs/arch_final_lock_find.log` |
| Final-quarantine string scan | 0 | `command_logs/arch_final_quarantine_scan.log` |
| Attempt 02 command status summary | 0 | `command_logs/arch_attempt02_status_summary.log` |
| `make experiments-val` excerpt and Level 5 grep | 0 | `command_logs/arch_make_experiments_val_excerpt.log`, `command_logs/arch_make_experiments_val_level5_grep.log` |
| `make test` tail inspection | 0 | `command_logs/arch_make_test_tail.log` |
| `make lint` tail inspection | 0 | `command_logs/arch_make_lint_tail.log` |
| `uv run pytest tests/unit/test_level5_validation.py tests/unit/test_large_universe_monitoring.py` | 0 | `command_logs/arch_focused_level5_pytest.log` |
| Number universe/broker/clock/risk/allocator source excerpts | 0, except one failed combined risk `nl` retry | `command_logs/arch_universe_numbered_excerpt.log`, `command_logs/arch_broker_numbered_excerpt.log`, `command_logs/arch_clock_numbered_excerpt.log`, `command_logs/arch_pre_risk_numbered_excerpt.log`, `command_logs/arch_post_risk_numbered_excerpt.log`, `command_logs/arch_allocators_numbered_excerpt.log`, `command_logs/arch_risk_numbered_excerpt.log` |
| Rebalance reason-code probe | 0 | `command_logs/arch_rebalance_reason_probe.log` |

The two failed reviewer probes were command-construction issues, not implementation failures; both were followed by successful corrected probes.

## Test and artifact evidence

- Attempt 02 logged gates all passed: `uv sync --frozen`, `make lint`, `make test`, `make experiments-val`, focused Level 5 pytest, artifact/proof probe, and runtime/memory/health probe all have status `0`.
- I independently reran focused Level 5 tests: 6 passed in 20.48s.
- `make test` log reports 98 tests passed.
- `make lint` log reports Ruff format/check passed.
- `make experiments-val` log reports Level 5 `scored_count=100`, `selected_count=25`, and final-test exposure `NOT_EXPOSED`.
- Artifact probe evidence:
  - `level_5_universe_scores.parquet`: 2,400 rows, 100 symbols per decision, 100 scored per decision, 25 selected per decision.
  - Decision dates: `2024-12-07` through `2024-12-30`; execution/evaluation dates: `2024-12-08` through `2024-12-31`.
  - Weights artifact: 100 symbol columns, max risky symbol weight `0.0500747365`, max risky sum `0.9964872572`, minimum cash `0.0035127428`.
  - Orders/fills: 135 orders and 135 fills, timestamps `2024-12-08` through `2024-12-31`.
  - Rebalance log: 24 rows, approval actions `approve=4`, `cash=20`; cash actions have `volatility_limit` reason.
  - Health summary: split `validation`, mode `full`, scored count min/max `100/100`, runtime `4.279s`, peak RSS `593.28125 MiB`, final-test exposure `NOT_EXPOSED`.
  - Pair-count proof: required/scored `100/100`, selected `25`, valid history min `241`, trailing valid days min `90`, full-universe excluded count `63`.
- Final-test quarantine evidence:
  - `artifacts/final_test_lock.json` was not present.
  - Level 5 artifact metadata has `final_test_lock_hash` null/empty and `provenance_split=validation`.
  - Max score feature cutoff was `2024-12-31 00:00:00+00:00`, before the `2025-01-01` final-test start.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None.

- MEDIUM
  - The Level 5 full validation window is short and late: decisions `2024-12-07` to `2024-12-30`, execution/evaluation `2024-12-08` to `2024-12-31`. I accept this for Stage 9 architecture validation because it proves the 100-pair pipeline before final-test exposure, but it is not enough for strong performance or model-selection claims.
  - Dynamic risk behavior is dominated by fail-safe cash: 20 of 24 decisions moved to cash due `volatility_limit`. This is valid risk-veto evidence, but the final narrative must frame Level 5 as a guarded architecture validation rather than evidence of robust active trading alpha.
  - Level 5 benchmark provenance is `price_normalized_btc_open_to_open`, not the contract-preferred equal-weight eligible-universe or equal-weight top-K benchmark for Level 5. This does not block the Stage 9 architecture proof, but it should be corrected before final reporting/notebook claims.
  - The priority score is a documented proxy using momentum, volatility, liquidity, confidence, and capacity; it is not a fully explicit expected net-alpha-after-cost estimate. Keep the claim precise unless a net-alpha/cost-adjusted priority field is added.

- LOW
  - The Level 5 decision trace uses one pooled cross-sectional ranker represented as typed `AgentSignal` and `AggregatedSignal` rows. That is acceptable for scalable Level 5 validation, but the notebook/deck should not imply multiple independent Level 5 agents if the evidence is the single ranker plus shared risk/rebalance machinery.
  - Active Binance/CCXT survivorship and delisting bias remains inherited from earlier stages.
  - Capacity uses daily dollar-volume/ADV proxy and no order-book depth or spread model.
  - The worktree still contains untracked attempt 01 process evidence and untracked attempt 02 artifacts/logs. This is acceptable for an uncommitted review handoff but not a clean checkpoint state.
  - The repository clock encodes feature cutoff, decision time, and execution time at the same UTC boundary for daily bars. This preserves next-open execution in the broker, but the final explanation should make the boundary convention explicit.

## Unresolved risks and limitations

- Final-test remains unrun and must stay quarantined until all levels are frozen and `artifacts/final_test_lock.json` is created.
- The frozen active-market dataset only reaches 100 eligible symbols in late December 2024 under the current Stage 9 rules (`min_history_days=240`, `min_trailing_valid_days=72`). A broader/delisted-symbol source would be needed for stronger institutional point-in-time claims.
- Level 5 performance metrics over the short late-December window should not be used to tune final-test methodology.
- Monitoring fields are present, but some long-term quality values are proxies because Stage 9 has only a short Level 5 validation window.

## Recommendation

PASS_WITH_NOTES

Stage 9 attempt 02 satisfies the architecture-focused Level 5 validation gate: it routes 100 scored symbols through the shared panel-native, next-open, broker/ledger/risk/portfolio artifact stack; it records dynamic top-K, risk veto, monitoring and fail-safe evidence; and it preserves final-test quarantine. The medium findings above should be addressed or explicitly disclosed before pretest freeze, final notebook, and final reporting.
