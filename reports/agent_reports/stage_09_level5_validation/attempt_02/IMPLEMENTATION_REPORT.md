# Role / stage / attempt

Implementation fixer / Stage 9 - Level 5 large-universe dynamic portfolio validation / attempt 02.

## Scope

Repaired the partial attempt 01 Level 5 implementation into a reviewable validation-only large-universe run. The implementation uses the existing panel-native data, broker, ledger, cost, risk, allocator, metrics and artifact stack.

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
- `reports/teamlead/PROJECT_STATE.md`
- `reports/teamlead/STAGE_BOARD.md`
- `reports/agent_reports/stage_08_level4_validation/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_09_level5_validation/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_09_level5_validation/attempt_01/command_logs/report_recovery_artifact_probe_fixed.log`
- `reports/agent_reports/stage_09_level5_validation/attempt_01/command_logs/report_recovery_prior_artifact_drift.log`

## Assumptions and decisions

- The attempt 01 implementation was repaired, not replaced, because it already used the shared architecture and produced validation-only Level 5 artifacts.
- Default/full Level 5 validation uses the first 2024 validation dates where the frozen active Binance universe reaches 100 eligible pairs under the Stage 9 rules: decisions `2024-12-07` through `2024-12-30`, evaluation `2024-12-08` through `2024-12-31`.
- The universe rule keeps `universe_min_history_days=240` and `universe_min_trailing_valid_days=72` to include newer late-2024 listings while still requiring causal trailing history. This is disclosed in artifact warnings.
- Runtime memory was corrected from the attempt 01 macOS unit bug. `ru_maxrss` is bytes on Darwin and KiB on Linux; artifacts now report `peak_rss_mb` with `peak_rss_unit=MiB`.
- Level 5 scores 100 eligible pairs and holds up to top-25 positive priority names. Risk can move allocations to cash.
- Earlier Level 1-4 generated artifact drift from `make experiments-val` was restored to `HEAD` with a scoped `git restore` path list.

## Files inspected or changed

Changed:

- `.gitignore`
- `configs/default.yaml`
- `configs/fast.yaml`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/experiments/__init__.py`
- `src/crypto_hedge_fund/experiments/level_5.py`
- `src/crypto_hedge_fund/features/level5.py`
- `src/crypto_hedge_fund/portfolio/allocators.py`
- `tests/unit/test_level5_validation.py`
- `tests/unit/test_large_universe_monitoring.py`
- `artifacts/**/level_5*`
- `artifacts/monitoring/health_summary.csv`
- `artifacts/monitoring/alerts.parquet`
- `reports/agent_reports/stage_09_level5_validation/attempt_02/**`

Inspected:

- Mandatory sources listed above.
- Existing universe selection, shared broker, Stage 3/4 experiment helpers, risk gates, rebalance policy, allocator and artifact writer.

Restored:

- All tracked `artifacts/**/level_1*`, `level_2*`, `level_3*` and `level_4*` drift paths listed in `command_logs/level1_4_restore_paths.log`.

## Deliverables

- Validation-only Level 5 runner wired into `make experiments-val`.
- Vectorized large-universe scoring features in `features/level5.py`.
- Dynamic target schedule using point-in-time eligibility, top-K priority scoring, inverse-volatility allocation, capacity caps, pre-risk, rebalance policy and post-risk approval.
- Level 5 monitoring artifacts with runtime, memory, data/model/system quality fields, long-term quality proxies and fail-safe evidence.
- Focused Level 5 tests for 100-pair scoring, final-test quarantine, cutoffs, weight caps, kill-switch cash behavior, repeatability and monitoring fields.
- Required Level 5 artifacts and metadata sidecars.

## Acceptance-criteria mapping

- Full/default validation scores at least 100 pairs: artifact probe confirmed `scored_count=100`.
- Validation-only quarantine: proof, metrics, health and trace report `NOT_EXPOSED`; max feature cutoff is `2024-12-31`.
- Point-in-time universe and filters: proof records eligibility rules, filters, symbols, selected symbols, exclusion counts and reason codes.
- Dynamic portfolio: rebalance log has 24 decisions, top-25 selection, 100 scored symbols per decision and shared broker outputs.
- Two-stage risk: pre-risk constraints feed allocation; post-risk approval produced explicit `approve` and `cash` actions with reason codes.
- Monitoring beyond KPIs: health summary includes coverage, drift, calibration proxy, fallback rate, cost decay proxy, incident count, runtime and memory.
- Fail-safe evidence: kill-switch cash schedule unit test passed; validation artifacts record cash approvals under risk controls.
- Runtime/memory evidence: proof and health report `runtime_seconds=4.2793826250126585`, `peak_rss_mb=593.28125`, `peak_rss_unit=MiB`.
- Level 1-4 artifact drift: scoped restore completed after validation generation.
- Final-test exposure: no final-test command, no final lock, final-test exposure remains `NOT_EXPOSED`.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_09_level5_validation/attempt_02/command_logs/uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_09_level5_validation/attempt_02/command_logs/make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_09_level5_validation/attempt_02/command_logs/make_test.log` |
| `make experiments-val` | 0 | `reports/agent_reports/stage_09_level5_validation/attempt_02/command_logs/make_experiments_val.log` |
| `uv run pytest tests/unit/test_level5_validation.py tests/unit/test_large_universe_monitoring.py` | 0 | `reports/agent_reports/stage_09_level5_validation/attempt_02/command_logs/focused_level5_pytest.log` |
| Artifact/proof/scored-count probe | 0 | `reports/agent_reports/stage_09_level5_validation/attempt_02/command_logs/artifact_proof_scored_count_probe.log` |
| Runtime/memory/health/alerts probe | 0 | `reports/agent_reports/stage_09_level5_validation/attempt_02/command_logs/runtime_memory_health_alerts_probe.log` |
| Scoped restore of tracked Level 1-4 artifact drift | 0 | `reports/agent_reports/stage_09_level5_validation/attempt_02/command_logs/level1_4_restore_paths.log` |

## Test and artifact evidence

- `make test`: 98 tests passed.
- Focused Level 5 pytest: 6 tests passed.
- `make experiments-val`: Levels 1-5 validation succeeded; CLI payload reported Level 5 `scored_count=100`, `selected_count=25`, final-test exposure `NOT_EXPOSED`.
- Artifact probe summary:
  - mode: `full`;
  - split: `validation`;
  - decision dates: 24;
  - proof decision date: `2024-12-07T00:00:00+00:00`;
  - evaluation period: `2024-12-08` to `2024-12-31`;
  - eligible/scored/selected: `100 / 100 / 25`;
  - score rows: 2400;
  - max symbols per decision: 100;
  - max selected per decision: 25;
  - weight symbol columns: 100;
  - max risky weight: `0.05007473654429236`;
  - max risky sum: `0.996487257231418`;
  - rebalance actions: `approve=4`, `cash=20`;
  - full universe excluded count on proof date: 63.

## Findings by severity

- BLOCKER: None known.
- HIGH: None known.
- MEDIUM: Full 100-pair evidence is necessarily late in 2024 under the frozen active Binance dataset and 240-day history rule. This is validation-only and disclosed, but reviewers should decide whether the short December validation window is sufficient for Stage 9.
- MEDIUM: Many validation approvals move to cash due risk controls. This is valid fail-safe behavior, not a profitability claim, but the final narrative must avoid implying robust alpha.
- LOW: Active Binance/CCXT survivorship and delisting bias remains inherited from earlier stages.
- LOW: Capacity uses daily dollar-volume proxies rather than order-book depth.

## Unresolved risks and limitations

- Final-test remains unrun and must stay quarantined until pretest freeze.
- Level 5 uses a lightweight cross-sectional score, not per-pair heavyweight econometric or ML models.
- The default full Level 5 validation period is short because the frozen dataset reaches 100 eligible pairs only in December 2024 under the configured rules.
- Stage 9 does not claim profitability or production readiness.
- Pre-existing untracked attempt 01 decision/recovery report files remain in the worktree as process evidence; attempt 02 did not modify them.

## Recommendation

PASS_WITH_NOTES

Stage 9 attempt 02 is reviewable and satisfies the hard validation-only 100-pair scoring proof, required artifacts, monitoring fields, fail-safe evidence and command gates. The lead should specifically review whether the late-December validation window is acceptable before passing the stage.
