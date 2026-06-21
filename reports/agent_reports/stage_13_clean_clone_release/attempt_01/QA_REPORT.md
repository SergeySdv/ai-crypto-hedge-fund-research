# Role / stage / attempt

Independent QA/release reviewer for Stage 13: Clean-clone release and submission audit, attempt 01.

## Scope

Reviewed Stage 13 release-readiness claims after Stage 12 acceptance and Stage 13 worker documentation changes. I did not run `make final-test` or `crypto-hedge-fund final-test`, did not retune methodology, did not change source implementation, and did not regenerate final-test artifacts.

The review focused on clean-clone command evidence, current release docs, required artifact visibility, notebook/deck state, final lock and Level 5 counts, secret/live-trading scans, public URL status, and the two unresolved worker issues: absolute local provenance paths in frozen final artifacts and missing separate `reports/model_cards/*` files.

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
- `reports/agent_reports/stage_13_clean_clone_release/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_12_notebook_report_presentation/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_11_final_test/attempt_01/TEAMLEAD_DECISION.md`
- `README.md`
- `THIRD_PARTY_LICENSES.md`
- `reports/final_report.md`

## Assumptions and decisions

- Final-test exposure is `EXPOSED`; no final-test command is acceptable in this QA pass.
- Stage 13 worker command logs are accepted as clean-clone evidence where they show execution from `/private/tmp/codex_crypto_hedge_fund_stage13_clean`; the `clean_clone_setup.log` itself is thin and only records detached HEAD state.
- I independently reran the allowed release command suite in the current checkout and wrote `qa_*` logs under the attempt command-log directory.
- `make validate-data`, `make notebook-full`, and `make presentation` dirtied generated tracked files during QA. Those side effects were restored because the user write scope allowed only the QA report and `qa_*` logs.
- The first required-artifact inventory log used a zsh-reserved variable name and is invalid; the corrected evidence is `qa_required_artifact_inventory_v2.log`.

## Files inspected or changed

Inspected:

- Required sources listed above.
- Stage 13 worker command logs under `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/`.
- Final lock, final-test summary, Level 5 proof, final notebook JSON, deck PDF, tracked artifact inventory, Git status, and release scans.

Changed:

- `reports/agent_reports/stage_13_clean_clone_release/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_*`

Temporary QA-generated changes to `artifacts/monitoring/level_5_data_pair_count_proof.json`, `notebooks/ai_crypto_hedge_fund.ipynb`, and `presentation/deck.pdf` were restored and are not left as report changes.

## Deliverables

- This QA report.
- QA command logs covering command reruns, artifact inventory, hash/notebook/PDF probes, secret/live-trading scans, model-card probe, remote probe, and final Git status.

## Acceptance-criteria mapping

| Criterion | QA status | Evidence |
| --- | --- | --- |
| Do not rerun final-test | PASS | No final-test command executed. |
| Clean-clone command evidence exists and is credible | PASS_WITH_NOTES | Worker logs show `/private/tmp/codex_crypto_hedge_fund_stage13_clean` for `uv sync`, tests, notebook, and presentation; setup log is minimal. |
| `uv sync --frozen` | PASS | `qa_uv_sync_frozen.log`, exit 0. |
| `make validate-data` | PASS | `qa_validate_data.log`, exit 0, 158,511 rows, 163 symbols, 104 eligible/scored data proof. |
| `make lint` | PASS | `qa_lint.log`, exit 0, Ruff format/check passed. |
| `make test` | PASS | `qa_test.log`, exit 0, 109 passed. |
| `make notebook-full` | PASS | `qa_notebook_full.log`, exit 0, full-final mode, lock hash and Level 5 counts reported. |
| `make presentation` | PASS | `qa_presentation.log`, exit 0, deck page count 10. |
| Required release artifacts tracked and visible | PASS | `qa_required_artifact_inventory_v2.log`, final per-level metrics/equity/weights/orders/fills and cross-cutting artifacts exist and are tracked. |
| Notebook outputs committed | PASS | `qa_notebook_pdf_lock_probe.log`, 11 code cells, execution counts 1-11, outputs on all code cells. |
| Deck PDF committed and <=10 pages | PASS | `qa_notebook_pdf_lock_probe.log` and `qa_presentation.log`, page count 10. |
| Final lock/hash and Level 5 counts consistent | PASS | `qa_notebook_pdf_lock_probe.log`, lock hash matches summary; Level 5 proof reports 120 eligible, 120 scored, 25 selected. |
| Release docs coherent and honest | PASS_WITH_NOTES | `README.md` and `reports/final_report.md` disclose negative results, final-test exposure, limitations, dirty runner provenance, and absolute provenance paths. |
| Third-party license inventory release-visible | HIGH ISSUE | `THIRD_PARTY_LICENSES.md` exists but is `NOT_TRACKED` in `qa_tracked_release_files.log` and `qa_final_git_status.log`. |
| No obvious tracked secrets | PASS_WITH_NOTES | `qa_secret_scan.log` found false-positive words only, such as "leveraged_token" and docs mentioning secrets. |
| No live trading enabled | PASS | `qa_live_trading_scan.log` finds CCXT public data/downloader references and documentation disclaimers; no enabled order submission path found. |
| Public repository URL | MANUAL OWNER STEP | `qa_remote_probe.log` shows no configured remote. |
| Absolute local paths in frozen final artifacts | MEDIUM RISK | `qa_abs_path_scan.log` finds `/Users/sergei/...` paths in Stage 11 final summary/evidence JSON. |
| Separate `reports/model_cards/*` files | LOW RISK | `qa_model_cards_probe.log` reports `reports/model_cards MISSING`; evidence exists elsewhere but the file contract is not met literally. |

## Commands executed

| Command | Exit status | Evidence/log |
| --- | ---: | --- |
| `git status --short --branch` | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_git_status.log` |
| `git diff --check` | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_git_diff_check.log` |
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_uv_sync_frozen.log` |
| `make validate-data` | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_validate_data.log` |
| `make lint` | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_test.log` |
| `make notebook-full` | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_notebook_full.log` |
| `make presentation` | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_presentation.log` |
| `git status --short --branch` after release commands | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_git_status_after.log` |
| Representative tracked-file probe | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_tracked_release_files.log` |
| SHA-256 probe | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_hash_probe.log` |
| Notebook/PDF/lock probe | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_notebook_pdf_lock_probe.log` |
| Absolute-path scan | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_abs_path_scan.log` |
| Secret scan | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_secret_scan.log` |
| Live-trading scan | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_live_trading_scan.log` |
| Model-card file probe | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_model_cards_probe.log` |
| Git remote probe | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_remote_probe.log` |
| Tracked status detail | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_tracked_status_detail.log` |
| Restore QA-generated tracked-file side effects | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_restore_generated_side_effects.log` |
| Final Git status | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_final_git_status.log` |
| Required artifact inventory v2 | 0 | `reports/agent_reports/stage_13_clean_clone_release/attempt_01/command_logs/qa_required_artifact_inventory_v2.log` |

## Test and artifact evidence

- `uv sync --frozen`: exit 0, audited 79 packages.
- `make validate-data`: exit 0, data hash `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`, instrument hash `df7777139dd4106032280339818ba18179882c8e19141f374d87cb8e7bddf18b`, 158,511 rows, 163 symbols, 104 eligible/scored data-level proof.
- `make lint`: exit 0, 82 files formatted, Ruff checks passed.
- `make test`: exit 0, 109 tests passed.
- `make notebook-full`: exit 0, mode `FULL_FINAL_NOTEBOOK`, exposure `EXPOSED`, final lock `dab407601cbaf8198361e5e3d074260546ed4bbab4c4be2555248b246631308b`, Level 5 counts 120 eligible, 120 scored, 25 selected.
- `make presentation`: exit 0, PDF page count 10.
- Notebook probe: 11 code cells, execution counts `[1,2,3,4,5,6,7,8,9,10,11]`, outputs on all code cells.
- Final lock hash matches `artifacts/final_test_lock.json` SHA-256 and final suite summary lock hash.
- Corrected artifact inventory: all required lock-specific final metrics/equity/weights/orders/fills, monitoring files, notebook, final report, deck source, and deck PDF exist and are tracked.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - `THIRD_PARTY_LICENSES.md` is not tracked. Stage 13 claims the license inventory gap was fixed, and `README.md` references the file, but `qa_tracked_release_files.log` and `qa_final_git_status.log` show it is `NOT_TRACKED`. A public release from the current tracked state would omit the inventory.

- MEDIUM
  - Frozen Stage 11 final summary/evidence JSON files preserve absolute local paths such as `/Users/sergei/PycharmProjects/...`. This is disclosed in `README.md` and `reports/final_report.md`, and clean-clone commands pass because the paths are provenance strings, but it remains a release artifact polish/privacy issue.
  - Clean-clone setup evidence is incomplete. The worker command logs are credible because they show `/private/tmp/codex_crypto_hedge_fund_stage13_clean`, but `clean_clone_setup.log` itself only contains `## HEAD (no branch)` and does not capture the clone/checkout command.

- LOW
  - No separate `reports/model_cards/*` files exist. This does not contradict the Stage 11/12 accepted functional evidence, but it does not satisfy the literal model-card file contract in `docs/03_REPOSITORY_LAYOUT.md`.
  - No public GitHub/GitLab remote is configured locally. This remains a manual owner publication/verification step.
  - `make validate-data`, `make notebook-full`, and `make presentation` dirty generated files when run in-place. QA restored those side effects; release reviewers should expect those commands to rewrite generated outputs locally.

## Unresolved risks and limitations

- Final-test exposure remains `EXPOSED`; no methodology retuning or final-test rerun should occur from this point.
- Accepted methodology limitations remain: survivorship/delisting bias from active Binance/CCXT market selection, daily-bar liquidity proxy, USDT-cash simplification, simplified next-open fills, cash-heavy risk behavior, short late-December 2024 Level 5 validation proof window, and BTC-normalized Level 5 benchmark.
- Stage 11 dirty runner-source provenance remains disclosed.
- Public repository URL, default branch visibility, and release/tag verification require the human owner.
- Stage 13 packaging must ensure the untracked license inventory and Stage 13 reports/logs are included in the checkpoint if they are part of release evidence.

## Recommendation

REWORK

The release command suite and core artifact evidence pass, and I found no blocker in the frozen methodology or final artifacts. However, Stage 13 is not yet release-ready because a claimed release deliverable, `THIRD_PARTY_LICENSES.md`, is untracked and therefore not public-checkout visible from the current tracked state. Track/include that file, decide whether separate `reports/model_cards/*` files are required or formally waived, and keep the public repository URL as an owner verification step.
