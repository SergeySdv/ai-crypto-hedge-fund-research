# Role / stage / attempt

Independent QA reviewer / Stage 9 - Level 5 large-universe validation / attempt 02.

## Scope

Review-only validation of the attempt 02 Level 5 implementation and artifacts. I did not edit implementation files, did not run `make pretest-freeze`, did not run `make final-test`, did not commit or tag, and did not intentionally modify source or methodology.

The required `make experiments-val` command regenerates validation artifacts as a side effect. I did not restore those generated changes because the QA role is constrained to reporting and command logs.

## Sources read

- `AGENTS.md`
- `docs/11_REQUIREMENTS_TRACEABILITY.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`
- `reports/agent_reports/stage_09_level5_validation/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_09_level5_validation/attempt_02/IMPLEMENTATION_REPORT.md`

## Assumptions and decisions

- Treated `final-test exposure status: NOT_EXPOSED` as a hard invariant; no final-test or pretest-lock command was run.
- Treated the required QA commands as mandatory even though `make experiments-val` rewrites generated artifacts.
- Treated ignored required artifacts/metadata and Level 1-4 tracked artifact drift as acceptance issues, not implementation changes for QA to fix.
- Used sidecar metadata as provenance evidence where the artifact body did not carry direct hash fields.

## Files inspected or changed

Inspected:

- Mandatory sources listed above.
- `src/crypto_hedge_fund/experiments/level_5.py`
- `src/crypto_hedge_fund/features/level5.py`
- `tests/unit/test_level5_validation.py`
- `tests/unit/test_large_universe_monitoring.py`
- `configs/default.yaml`
- `configs/fast.yaml`
- Level 5 artifacts under `artifacts/metrics`, `artifacts/equity`, `artifacts/weights`, `artifacts/orders`, `artifacts/fills`, `artifacts/figures`, and `artifacts/monitoring`.

Changed:

- `reports/agent_reports/stage_09_level5_validation/attempt_02/QA_REPORT.md`
- `reports/agent_reports/stage_09_level5_validation/attempt_02/command_logs/qa_*.log`
- `reports/agent_reports/stage_09_level5_validation/attempt_02/command_logs/qa_*.status`

## Deliverables

- QA report: `reports/agent_reports/stage_09_level5_validation/attempt_02/QA_REPORT.md`
- Command logs and status files under `reports/agent_reports/stage_09_level5_validation/attempt_02/command_logs/`

## Acceptance-criteria mapping

- Level 5 scores at least 100 pairs: PASS. Proof reports `eligible_count=100`, `scored_count=100`, `selected_count=25`; score table has 2,400 rows over 24 decision dates and 100 unique symbols.
- Validation-only quarantine: PASS. Proof, health, and trace report `final_test_exposure=NOT_EXPOSED`; feature/evaluation period remains before 2025.
- Runtime/memory evidence: PASS. Proof and health report `runtime_seconds=4.309063708002213`, `peak_rss_mb=598.484375`, `peak_rss_unit=MiB`.
- Health/alerts presence: PASS. Health summary exists with 44 columns; alerts exist with 4 rows, including info and warning severities.
- Required artifacts present: PASS for Level 5 artifact files probed.
- Required artifacts visible to Git and not ignored: FAIL. `artifacts/monitoring/health_summary.csv.metadata.json` is ignored.
- Level 1-4 tracked artifact drift restored: FAIL. After the required `make experiments-val`, many tracked Level 1-4 artifacts are modified.
- Cache/noise check: PASS. No untracked `__pycache__`, `.pyc`, `.pytest_cache`, `.ruff_cache`, notebook checkpoint, or `.DS_Store` candidates were reported.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `command_logs/qa_uv_sync_frozen.log`, `command_logs/qa_uv_sync_frozen.status` |
| `make lint` | 0 | `command_logs/qa_make_lint.log`, `command_logs/qa_make_lint.status` |
| `make test` | 0 | `command_logs/qa_make_test.log`, `command_logs/qa_make_test.status` |
| `make experiments-val` | 0 | `command_logs/qa_make_experiments_val.log`, `command_logs/qa_make_experiments_val.status` |
| `uv run pytest tests/unit/test_level5_validation.py tests/unit/test_large_universe_monitoring.py` | 0 | `command_logs/qa_focused_level5_pytest.log`, `command_logs/qa_focused_level5_pytest.status` |
| Level 5 artifact probe | 1 | `command_logs/qa_level5_artifact_probe.log`, `command_logs/qa_level5_artifact_probe.status` |
| Level 5 artifact probe v2 | 1 | `command_logs/qa_level5_artifact_probe_v2.log`, `command_logs/qa_level5_artifact_probe_v2.status` |
| Level 5 artifact summary probe | 0 | `command_logs/qa_level5_artifact_summary.log`, `command_logs/qa_level5_artifact_summary.status` |
| Level 5 corrected count probe | 0 | `command_logs/qa_level5_count_probe.log`, `command_logs/qa_level5_count_probe.status` |
| Git visibility/drift/noise probe | 1 | `command_logs/qa_git_visibility_and_drift.log`, `command_logs/qa_git_visibility_and_drift.status` |

The two failed artifact probes were reviewer assertions. They surfaced that direct `final_test_exposure`/`split` fields are not present in `artifacts/metrics/level_5.csv`; the same file carries `provenance_split` and related provenance fields, and sidecars carry hashes.

## Test and artifact evidence

- `make test`: 98 tests passed in 30.47s.
- Focused Level 5 pytest: 6 tests passed in 20.61s.
- `make experiments-val`: completed Levels 1-5 validation and reported Level 5 `scored_count=100`, `selected_count=25`.
- Level 5 proof:
  - mode: `full`
  - split: `validation`
  - final-test exposure: `NOT_EXPOSED`
  - validation decision date: `2024-12-07T00:00:00+00:00`
  - evaluation period: `2024-12-08` to `2024-12-31`
  - eligible/scored/selected: `100 / 100 / 25`
  - approved nonzero max: `25`
  - runtime/memory: `4.309063708002213` seconds / `598.484375 MiB`
- Provenance:
  - data hash: `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`
  - config hash: `3f802390b94d313468f1a778c65350eecb10b220ac8515d2ee5ec5b8a2e64683`
  - git commit: `ab4225a6021c37ad21da015fc2b7349dc99bcf00`
  - final test lock hash: `null`
- Level 5 artifacts present: metrics, equity, weights, orders, fills, figure, pair-count proof, universe scores, rebalance log, decision trace, health summary, alerts, and metadata sidecars.
- Git visibility probe: all listed Level 5 artifacts were visible except `artifacts/monitoring/health_summary.csv.metadata.json`, which is ignored.
- Git drift probe: tracked Level 1-4 artifacts remain modified after the validation rerun.

## Findings by severity

- BLOCKER
  - Level 1-4 tracked artifact drift remains after the required validation run. `qa_git_visibility_and_drift.log` lists modified tracked artifacts across `artifacts/equity`, `artifacts/fills`, `artifacts/metrics`, `artifacts/monitoring`, `artifacts/orders`, and `artifacts/weights` for Levels 1-4. This directly fails the mission item to verify Level 1-4 artifact drift is restored.

- HIGH
  - One generated Level 5 provenance sidecar is ignored by Git: `artifacts/monitoring/health_summary.csv.metadata.json`. The required review explicitly includes verifying artifacts are visible to Git and not ignored; the Git visibility probe exits 1 for this reason.

- MEDIUM
  - `artifacts/metrics/level_5.csv` lacks direct `split` and `final_test_exposure` columns. It does include `provenance_split` and related provenance columns, and sidecars include hashes, but the quarantine flag is less directly inspectable in the primary metrics artifact than in proof/health/trace.
  - The 100-pair validation proof is concentrated in a short late-December 2024 window. This is disclosed in provenance warnings and remains validation-only, but reviewers should decide whether that is sufficient for Stage 9 acceptance.

- LOW
  - Survivorship bias from active Binance/CCXT-style market coverage and capacity based on daily dollar-volume proxies remain documented limitations.
  - The initial QA command wrapper used a zsh reserved variable name before running `uv`; the gate was rerun correctly and passed. No implementation effect.

## Unresolved risks and limitations

- Final test remains unrun, and no pretest lock exists. This is correct for this Stage 9 QA scope.
- The worktree includes many untracked attempt 01/attempt 02 process logs and reports from other reviewers; I did not delete or alter them.
- The required `make experiments-val` command reintroduces Level 1-4 artifact drift, so the implementation handoff claim that drift had been restored is not stable after the required gate.
- Metrics/provenance schema is inconsistent across artifacts: proof/health/trace carry direct quarantine fields, while metrics relies on provenance-prefixed fields and sidecars.

## Recommendation

REWORK
