# Role / stage / attempt

Independent QA reviewer / Stage 5: Level 1 validation / attempt 02.

## Scope

Report-only QA for the attempt 02 remediation of Stage 5 Level 1 validation. I verified that Level 1 validation artifacts are checkpoint-safe, that regenerated artifact provenance honestly records the dirty/uncommitted source state, that required commands pass, and that final-test quarantine remains intact.

No implementation files, commits, tags, destructive Git operations, final-test commands, notebooks, presentation files or live-trading paths were touched.

## Sources read

- `AGENTS.md`
- `MASTER_PROMPT_CODEX_TEAMLEAD.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/IMPLEMENTATION_REPORT.md`

Additional inspected evidence:

- `.gitignore`
- `src/crypto_hedge_fund/provenance.py`
- `src/crypto_hedge_fund/artifacts/writers.py`
- `src/crypto_hedge_fund/experiments/level_1.py`
- `src/crypto_hedge_fund/cli.py`
- `tests/unit/test_level1_validation.py`
- `tests/unit/test_experiments_validation.py`
- Generated Level 1 artifacts and sidecar metadata under `artifacts/`

## Assumptions and decisions

- This review is scoped to attempt 02 remediation for Level 1 validation only.
- Validation-period Level 1 metrics may be inspected; final-test metrics, returns, rankings, charts and model outputs remain forbidden.
- `make final-test` is forbidden for Stage 5 and was not run.
- A dirty worktree is acceptable for this attempt only if artifact provenance explicitly records the dirty state and deterministic source-state hash.
- `git check-ignore -v` can show negation rules for unignored files, so I used a companion effective `git check-ignore -q` probe to verify checkpoint-safety.

## Files inspected or changed

Inspected:

- Mandatory source documents and prior reports listed above.
- Remediation files: `.gitignore`, `src/crypto_hedge_fund/provenance.py`, `src/crypto_hedge_fund/artifacts/writers.py`, `src/crypto_hedge_fund/experiments/level_1.py`, `src/crypto_hedge_fund/cli.py`, `tests/unit/test_level1_validation.py`, `tests/unit/test_experiments_validation.py`.
- Required Level 1 artifacts:
  - `artifacts/metrics/level_1.csv`
  - `artifacts/equity/level_1.parquet`
  - `artifacts/weights/level_1.parquet`
  - `artifacts/orders/level_1.parquet`
  - `artifacts/fills/level_1.parquet`
  - `artifacts/figures/level_1_equity_curve.png`
  - `artifacts/monitoring/level_1_decision_trace.json`
  - corresponding `.metadata.json` sidecars where applicable

Changed:

- `reports/agent_reports/stage_05_level1_validation/attempt_02/QA_REPORT.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_uv_sync_frozen.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_make_lint.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_make_test.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_make_experiments_val.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_focused_level1_pytest.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_git_check_ignore_level1_artifacts.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_git_check_ignore_nonignored_probe.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_artifact_provenance_inspection.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_git_diff_stat.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_git_status_short_branch_untracked_ignored.log`

## Deliverables

- Fresh QA logs for all required commands and probes.
- Independent evidence that required Level 1 artifacts and sidecars are not ignored by Git.
- Independent provenance inspection proving `git_worktree_dirty` and `git_diff_sha256` are present on regenerated artifacts.
- This QA report.

## Acceptance-criteria mapping

- Required commands pass: PASS. `uv sync --frozen`, `make lint`, `make test`, `make experiments-val`, and focused Level 1 pytest all exited 0.
- Required Level 1 artifacts exist: PASS. Metrics, equity, weights, orders, fills, figure and decision trace are present after a fresh `make experiments-val`.
- Required Level 1 artifacts are checkpoint-safe: PASS. `.gitignore` has narrow Level 1 exceptions, and the effective probe reports `NOT_IGNORED` for every required artifact and sidecar.
- Honest dirty-source provenance: PASS. Regenerated metrics, parquet sidecars and trace provenance record `git_worktree_dirty=True` and `git_diff_sha256=387f60845b1de7b78a3ad7c51e54c19a161d39a841d765bdb6f1c6ef787954ee`.
- Validation labeling and final-test quarantine: PASS. `make experiments-val` reports `"split": "validation"` and `"final_test_exposure": "NOT_EXPOSED"`; sidecars record `split=validation` and `final_test_lock_hash=None`; `artifacts/final_test_lock.json` does not exist.
- Shared Stage 3/4 architecture for Level 1: PASS. Source and tests still show `SimulatedBroker`, shared artifact writer, typed provenance, pre-allocation/post-allocation risk, and Level 1 regression coverage.
- No notebooks/presentation/live trading: PASS. No notebook, presentation, live execution path or final-test command was run or modified by QA.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_make_test.log` |
| `make experiments-val` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_make_experiments_val.log` |
| `uv run pytest tests/unit/test_level1_validation.py tests/unit/test_experiments_validation.py` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_focused_level1_pytest.log` |
| `git check-ignore -v --stdin` for required Level 1 artifacts and sidecars | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_git_check_ignore_level1_artifacts.log` |
| Effective non-ignored probe using `git check-ignore -q` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_git_check_ignore_nonignored_probe.log` |
| Artifact provenance inspection | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_artifact_provenance_inspection.log` |
| `git diff --stat` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_git_diff_stat.log` |
| `git status --short --branch --untracked-files=all --ignored=matching` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_02/command_logs/qa_git_status_short_branch_untracked_ignored.log` |

## Test and artifact evidence

- `uv sync --frozen`: audited 79 packages.
- `make lint`: `ruff format --check .` reported 56 files already formatted; `ruff check .` passed.
- `make test`: 71 tests passed.
- Focused Level 1 pytest: 5 tests passed.
- `make experiments-val`: selected SMA fast `30`, slow `100`; wrote Level 1 metrics/equity/weights/orders/fills/figure/trace artifacts; reported net ROI `1.186110921467134`, net Sharpe `1.9535370402802261`, net max drawdown `-0.20027161004621163`, split `validation`, final-test exposure `NOT_EXPOSED`.
- Required artifact hashes from the fresh QA run:
  - `artifacts/metrics/level_1.csv`: `46487110e7b464cfbe1f2f46d5d9bb84350f0ba0da5a88e91f76a99a99635ebc`
  - `artifacts/equity/level_1.parquet`: `c0872a2fb9de294ede154699e8cd6d36f571352f35f7d3c615332409ee0be280`
  - `artifacts/weights/level_1.parquet`: `2c6a20869a419329e4b5c44bcb9bbc801d20f24e348f0a6cf46734021a341c4c`
  - `artifacts/orders/level_1.parquet`: `3dc31a60526c05f6c243cf12d6d6941c15603e797d28ca8829a590ecfc3614d9`
  - `artifacts/fills/level_1.parquet`: `b0e0b6eb85585be9a83ee2fee4ce427a64f77bf3ce3a21cc9d5621943de9b032`
  - `artifacts/figures/level_1_equity_curve.png`: `d7dbeb4d288202bc5f66fdd02244e3681d3879bd450fd9914f48f96d8167406d`
  - `artifacts/monitoring/level_1_decision_trace.json`: `e453c74155a2c8f00fee69731db75e8880c86edb18c45be8222d079c0ea643b5`
- Parquet artifact ranges are validation-only: equity and weights each have 366 rows from `2024-01-01 00:00:00+00:00` through `2024-12-31 00:00:00+00:00`; orders and fills each have 262 rows in the same date range.
- Metadata sidecars for metrics/equity/weights/orders/fills/figure record `split=validation`, `git_commit=40d748b27a284ce3c8efa7c0b7204a5608b3904b`, `git_worktree_dirty=True`, `git_diff_sha256=387f60845b1de7b78a3ad7c51e54c19a161d39a841d765bdb6f1c6ef787954ee`, `final_test_lock_hash=None`, and warnings including `validation_only_no_final_test_metrics` and `survivorship_bias_active_markets`.
- Effective Git ignore probe reports `NOT_IGNORED` for all required Level 1 artifacts and sidecars.
- `git status --short --branch --untracked-files=all --ignored=matching` shows Level 1 artifacts as `??`, not `!!`; ignored paths are limited to local caches, `.venv`, `artifacts/models/`, and Python cache directories.
- `git diff --stat` shows tracked remediation changes in `.gitignore`, configs, artifact writer, CLI and provenance helper. Untracked Stage 5 source, tests, artifacts and reports remain visible in the status log.

## Findings by severity

- BLOCKER
  - None.
- HIGH
  - None.
- MEDIUM
  - None.
- LOW
  - The artifacts correctly record a dirty source state rather than a clean Stage 5 checkpoint. This satisfies the attempt 02 remediation request, but the team lead should include the source files, tests, artifacts and reports in the checkpoint and may choose to regenerate after commit so later artifacts can reference the Stage 5 commit directly.
  - Active-market survivorship/delisting limitation remains inherited from earlier stages. It is disclosed in Level 1 artifact warnings and must remain visible in later reports/notebook/deck.

## Unresolved risks and limitations

- Final-test exposure remains `NOT_EXPOSED`; `make final-test` was not run.
- Levels 2-5, pretest freeze, final-test suite, notebook, final report and presentation remain out of scope for this Stage 5 Level 1 review.
- The current worktree is intentionally dirty/uncommitted; artifact provenance records that state, but only a team-lead checkpoint can make the stage repository state durable.
- Validation metrics are not final-test evidence and must not be used for post-lock tuning after final-test exposure.

## Recommendation

PASS_WITH_NOTES

Only the team lead can pass the stage.
