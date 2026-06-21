# Role / stage / attempt

Implementation fixer / Stage 5: Level 1 validation / attempt 02.

## Scope

Remediated only the Stage 5 attempt 01 artifact tracking and provenance failures.

No Level 1 methodology, SMA selection logic, broker path, risk path, validation split, final-test lock, notebook, presentation, final report, Level 2-5 code or live-trading path was changed. No final-test command was run and no final-test metrics, rankings, charts or model outputs were inspected.

## Sources read

- `AGENTS.md`
- `MASTER_PROMPT_CODEX_TEAMLEAD.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/TEAMLEAD_DECISION.md`

## Assumptions and decisions

- The correct fix is to keep `artifacts/*` ignored by default, preserve existing Stage 2 proof exceptions, and add narrow exceptions only for required Level 1 validation artifacts and metadata sidecars.
- Because the Stage 5 implementation remains uncommitted by design, regenerated artifacts should still record `git_commit=40d748b27a284ce3c8efa7c0b7204a5608b3904b`, but must also record `git_worktree_dirty=true` and a deterministic dirty source-state hash.
- `git_diff_sha256` is implemented as a source-state hash: tracked staged/unstaged diff against `HEAD` plus untracked, non-ignored source files, excluding generated `artifacts/` and `reports/` so artifact regeneration and report logging do not recursively change the embedded source hash.
- `git check-ignore -v` prints matching negation patterns for explicitly unignored paths and exits 0. A companion non-verbose probe records the effective result as `NOT_IGNORED` for each required path.

## Files inspected or changed

Inspected:

- `.gitignore`
- `src/crypto_hedge_fund/provenance.py`
- `src/crypto_hedge_fund/artifacts/writers.py`
- `src/crypto_hedge_fund/experiments/level_1.py`
- `tests/unit/test_level1_validation.py`
- `tests/unit/test_experiments_validation.py`
- generated Level 1 validation artifacts and sidecar metadata

Changed:

- `.gitignore`
- `src/crypto_hedge_fund/provenance.py`
- `src/crypto_hedge_fund/artifacts/writers.py`
- `src/crypto_hedge_fund/experiments/level_1.py`
- `tests/unit/test_level1_validation.py`
- regenerated `artifacts/metrics/level_1.csv*`
- regenerated `artifacts/equity/level_1.parquet*`
- regenerated `artifacts/weights/level_1.parquet*`
- regenerated `artifacts/orders/level_1.parquet*`
- regenerated `artifacts/fills/level_1.parquet*`
- regenerated `artifacts/figures/level_1_equity_curve.png*`
- regenerated `artifacts/monitoring/level_1_decision_trace.json`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/*`
- this report

## Deliverables

- Required Level 1 validation artifacts are checkpoint-safe and no longer effectively ignored by Git.
- Stage 2 proof artifact exceptions remain present:
  - `artifacts/monitoring/level_5_pair_count_proof.json`
  - `artifacts/monitoring/universe_eligibility_full.csv`
- `ArtifactProvenance` now carries `git_worktree_dirty` and `git_diff_sha256`.
- Level 1 provenance populates those fields at artifact generation time.
- Tests cover both required regressions:
  - Level 1 artifact paths are not ignored by Git.
  - dirty/source-state provenance fields are written into metrics and sidecar metadata.
- Level 1 validation artifacts were regenerated after the provenance/tracking fix.

## Acceptance-criteria mapping

- Checkpoint-safe Level 1 artifacts: PASS. `.gitignore` now unignores required Level 1 artifact files and sidecars while preserving broad generated-artifact ignores.
- Preserve Stage 2 proof exceptions: PASS. Existing Stage 2 monitoring proof exceptions were not removed.
- Honest source-state provenance: PASS. Regenerated artifacts record `git_commit`, `git_worktree_dirty=True`, and `git_diff_sha256=387f60845b1de7b78a3ad7c51e54c19a161d39a841d765bdb6f1c6ef787954ee`.
- Regenerate artifacts after fix: PASS. `make experiments-val` reran and rewrote Level 1 validation artifacts.
- Tests updated: PASS. Full suite now has 71 tests; focused Level 1 suite has 5 tests.
- Validation label and quarantine: PASS. Artifacts and CLI output remain `split=validation`, `final_test_exposure=NOT_EXPOSED`, and `final_test_lock_hash=None`.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/make_test.log` |
| `make experiments-val` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/make_experiments_val.log` |
| `uv run pytest tests/unit/test_level1_validation.py tests/unit/test_experiments_validation.py` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/focused_level1_pytest.log` |
| `git check-ignore -v` on required Level 1 artifacts and sidecars | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/git_check_ignore_level1_artifacts.log` |
| Effective ignored/not-ignored probe for required Level 1 artifacts and sidecars | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/git_check_ignore_nonignored_probe.log` |
| Artifact provenance inspection command | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/artifact_provenance_inspection.log` |
| `git status --short --branch --untracked-files=all --ignored=matching` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/git_status_short_branch_untracked_ignored.log` |

## Test and artifact evidence

- `make lint`: Ruff format check and Ruff check passed.
- `make test`: 71 passed.
- Focused Level 1 pytest: 5 passed.
- `make experiments-val`: selected SMA fast `30`, slow `100`; wrote metrics/equity/weights/orders/fills/figure/trace artifacts; reported `split=validation` and `final_test_exposure=NOT_EXPOSED`.
- Effective Git ignore probe returned `NOT_IGNORED` for all required Level 1 artifacts and metadata sidecars.
- `git check-ignore -v` shows the applicable `.gitignore` negation rules for Level 1 files, confirming explicit unignore coverage.
- Metrics/sidecar/trace provenance inspection:
  - `split=validation`
  - `period=2024-01-01` to `2024-12-31`
  - `git_commit=40d748b27a284ce3c8efa7c0b7204a5608b3904b`
  - `git_worktree_dirty=True`
  - `git_diff_sha256=387f60845b1de7b78a3ad7c51e54c19a161d39a841d765bdb6f1c6ef787954ee`
  - `final_test_lock_hash=None`
  - warnings include `validation_only_no_final_test_metrics` and `survivorship_bias_active_markets`
- Regenerated artifact hashes:
  - metrics: `3eba6747313cf9383f7a69bdb0bbc324567a67e1644d5c5b5b10f2e37dcf7525`
  - equity: `8edfe31f4e360be3406b071164c688fdf3878c910144089c4f9ceabd63dbd80f`
  - weights: `8c25d8d5eb4a3017e11831587c61627dc1ba495d50cf956b5b876a67d4f93e84`
  - orders: `1ae3a16cde24558a9dcf268dfe4270a4eb76fa9dc78dc96ea3cf49bce7eec037`
  - fills: `d0b335573cf4abbc730565091fe937f592be0dad618bb92f276b26aed2abb9d1`
  - figure: `d7dbeb4d288202bc5f66fdd02244e3681d3879bd450fd9914f48f96d8167406d`
  - trace: `6a092752b6446664bce620827a8d96bbb03f527c9853508a5f1b3041855c8354`

## Findings by severity

- BLOCKER
  - None.
- HIGH
  - None.
- MEDIUM
  - The artifacts honestly record a dirty source state rather than a clean Stage 5 checkpoint. This satisfies the attempt 02 remediation request, but the team lead should still commit/checkpoint and may choose to regenerate once the stage is accepted.
- LOW
  - `git check-ignore -v` is easy to misread because it prints negation matches for unignored files. The report includes a companion effective probe with `NOT_IGNORED` results.

## Unresolved risks and limitations

- Final-test exposure remains `NOT_EXPOSED`; `make final-test` was not run.
- Active-market survivorship/delisting limitation remains inherited from Stage 2 and is still disclosed in artifact warnings.
- Stage 5 remains Level 1 only. Levels 2-5, pretest lock, final-test suite, notebook, report and presentation remain future work.
- Existing uncommitted attempt 01 implementation files remain in the worktree and are intentionally represented by dirty/source-state provenance.

## Recommendation

PASS_WITH_NOTES
