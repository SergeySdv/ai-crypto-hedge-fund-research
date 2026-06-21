# Role / stage / attempt

Independent QA/reproducibility reviewer / Stage 10 - Pretest freeze / attempt 01.

## Scope

Independently reviewed the Stage 10 pretest-freeze handoff. I ran the required reproducibility gates, verified the final-test lock and selected-config hashes, checked validation artifact hash coverage, checked Git visibility/ignore state, verified freeze failure behavior via temporary-repository unit tests, and inspected current dirty-worktree scope.

I did not run `make final-test`. I did not inspect final-test metrics, returns, rankings, charts, orders, or fills. Final-test exposure is `LOCKED` after `make pretest-freeze`, with `final_test_results_inspected=false`.

## Sources read

- `AGENTS.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_01/IMPLEMENTATION_REPORT.md`
- `configs/validation_selected.yaml`
- `artifacts/final_test_lock.json`
- Supporting implementation/test files for failure-behavior review: `src/crypto_hedge_fund/pretest_lock.py`, `tests/unit/test_pretest_freeze.py`

## Assumptions and decisions

- Treated command-generated validation artifact changes as expected side effects of the required `make experiments-val` and `make pretest-freeze` QA commands.
- Treated uncommitted Stage 10 implementation files as acceptable for this uncheckpointed attempt only; they still must be reviewed/checkpointed before Stage 11.
- Used filename-only artifact scanning for final-like outputs to avoid inspecting any final-test result content.
- Used the corrected Git visibility probe `qa_git_visibility_probe_v2.*`; the first probe incorrectly treated a negated `.gitignore` allow rule as ignored even though `git status` showed the lock file as visible.

## Files inspected or changed

Inspected:

- Mandatory sources listed above.
- `src/crypto_hedge_fund/pretest_lock.py`
- `tests/unit/test_pretest_freeze.py`
- Current Git status and `.gitignore` visibility for the lock/config.
- Lock sidecar metadata and validation artifact hashes.

Changed:

- `reports/agent_reports/stage_10_pretest_freeze/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_01/command_logs/qa_*.log`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_01/command_logs/qa_*.status`

## Deliverables

- QA report: `reports/agent_reports/stage_10_pretest_freeze/attempt_01/QA_REPORT.md`
- QA command logs and status files under `reports/agent_reports/stage_10_pretest_freeze/attempt_01/command_logs/`

## Acceptance-criteria mapping

- Required gates: PASS. `uv sync --frozen`, `make validate-data`, `make lint`, `make test`, `make experiments-val`, and `make pretest-freeze` all exited `0`.
- Lock exposure/quarantine: PASS. Lock reports `final_test_exposure_state=LOCKED` and `final_test_results_inspected=false`.
- Sidecar lock hash: PASS. Current lock SHA-256 equals sidecar `final_test_lock_sha256`.
- Selected config hash: PASS. Current `configs/validation_selected.yaml` SHA-256 and canonical config hash match the lock.
- Validation artifact hashes: PASS. All 47 recorded validation artifact hashes match current files; no missing or mismatched artifacts.
- Final-test artifact absence: PASS. Filename scan found only the lock/sidecar and planned-not-executed Level 3/4 final vintage plan files; no final-test result artifact names were found.
- Git visibility: PASS. `artifacts/final_test_lock.json` and `configs/validation_selected.yaml` are visible to Git status and are not ignored by exclude-standard rules.
- Failure behavior: PASS. Focused temp-repository tests passed for missing validation artifacts and forbidden dirty methodology/config changes.
- Dirty-worktree/cache policy: PASS_WITH_NOTES. The worktree is broad but Stage 10-scoped: regenerated validation artifacts, new lock/config, implementation helper/test files, and report/log files. `.pytest_cache`, `.ruff_cache`, and `.venv` are ignored.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `command_logs/qa_uv_sync_frozen.log`, `command_logs/qa_uv_sync_frozen.status` |
| `make validate-data` | 0 | `command_logs/qa_make_validate_data.log`, `command_logs/qa_make_validate_data.status` |
| `make lint` | 0 | `command_logs/qa_make_lint.log`, `command_logs/qa_make_lint.status` |
| `make test` | 0 | `command_logs/qa_make_test.log`, `command_logs/qa_make_test.status` |
| `make experiments-val` | 0 | `command_logs/qa_make_experiments_val.log`, `command_logs/qa_make_experiments_val.status` |
| `make pretest-freeze` | 0 | `command_logs/qa_make_pretest_freeze.log`, `command_logs/qa_make_pretest_freeze.status` |
| Lock/hash/quarantine Python probe | 0 | `command_logs/qa_lock_hash_quarantine_probe.log`, `command_logs/qa_lock_hash_quarantine_probe.status` |
| Git visibility/ignore probe v2 | 0 | `command_logs/qa_git_visibility_probe_v2.log`, `command_logs/qa_git_visibility_probe_v2.status` |
| `uv run pytest tests/unit/test_pretest_freeze.py -q` | 0 | `command_logs/qa_pretest_failure_behavior_tests.log`, `command_logs/qa_pretest_failure_behavior_tests.status` |
| Git status/cache-noise probe | 0 | `command_logs/qa_git_status_scope_noise.log`, `command_logs/qa_git_status_scope_noise.status` |

## Test and artifact evidence

- `make validate-data`: 158,511 rows, 163 symbols, data SHA-256 `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`, instrument SHA-256 `df7777139dd4106032280339818ba18179882c8e19141f374d87cb8e7bddf18b`, and 104 eligible/scored pairs at `2025-07-01T00:00:00+00:00`.
- `make test`: 100 tests passed in 30.79s.
- `make experiments-val`: split `validation`, final-test exposure `NOT_EXPOSED`, Level 5 `scored_count=100`, `selected_count=25`.
- `make pretest-freeze`: wrote `artifacts/final_test_lock.json` with SHA-256 `19292d3daec5b64beabad4c22c530943e6f54ac8eceef8e35655e94a6cf50eb4`; wrote `configs/validation_selected.yaml` with SHA-256 `6b36f9665c6adcbef9a9a61a2d8578b10dd7c95c069682c8ae7936350e7289b3`; exposure `LOCKED`.
- Lock probe: sidecar hash match `true`; config hash match `true`; config canonical hash match `true`; validation artifact missing count `0`; validation artifact mismatch count `0`; unexpected final-like files `[]`.
- Git visibility probe: lock/config both show as `??` in Git status, are not listed by `git ls-files --others --ignored --exclude-standard`, and are therefore visible/not ignored.
- Failure-behavior tests: 2 passed, covering missing validation artifacts and forbidden dirty methodology/config changes.

## Findings by severity

- BLOCKER
  - None identified for Stage 10 attempt 01 QA scope.

- HIGH
  - None identified for Stage 10 attempt 01 QA scope.

- MEDIUM
  - The Stage 10 worktree is not checkpoint-clean. Current status includes regenerated tracked validation artifacts, new untracked lock/config files, `.gitignore`, `src/crypto_hedge_fund/cli.py`, untracked `src/crypto_hedge_fund/pretest_lock.py`, untracked `tests/unit/test_pretest_freeze.py`, and Stage 10 report/log files. This is consistent with an uncommitted attempt but must be intentionally reviewed and checkpointed before Stage 11.

- LOW
  - The attempt directory also contains untracked `ARCHITECTURE_REVIEW.md` and `arch_*` logs from another review stream. They are Stage 10 report artifacts, not cache/noise, but they are outside this QA reviewer’s allowed write set and should be handled deliberately by the team lead.
  - Initial `qa_git_visibility_probe.*` exited `1` because it interpreted a negated `.gitignore` match as ignored. The corrected `qa_git_visibility_probe_v2.*` passed and is the evidence used for Git visibility.

## Unresolved risks and limitations

- This report does not declare Stage 10 globally passed.
- `make final-test` remains unrun and must not be run until the team lead accepts the freeze state.
- Stage 11 final-test runner behavior was not exercised because `make final-test` is forbidden in this review.
- Known methodology limitations remain from the lock/report: active Binance/CCXT survivorship and delisting bias, daily liquidity proxies instead of order-book depth, short late-December 2024 Level 5 validation proof window, and BTC-normalized Level 5 benchmark disclosure.

## Recommendation

PASS_WITH_NOTES for Stage 10 attempt 01 QA scope.

The required gates passed, the lock/config/artifact hashes match current files, final-test quarantine markers are correct, Git visibility is acceptable, and failure behavior is covered by focused temp-repository tests. Do not treat this as a global Stage 10 pass until the team lead reviews the dirty worktree and checkpoints the accepted freeze state.
