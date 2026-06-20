# Role / stage / attempt

Independent QA reviewer / Stage 2 - Frozen Data and Point-in-Time Universe / attempt 02.

## Scope

Independent validation of attempt 02 remediation for Stage 2. I reviewed the frozen data layer, point-in-time universe proof, validation behavior, tests, proof artifact policy, and final-test quarantine state. I did not edit implementation, tests, data, configs, management files, or run `make data`, `make final-test`, experiments, notebooks, or any strategy-performance command.

## Sources read

- `AGENTS.md`
- `MASTER_PROMPT_CODEX_TEAMLEAD.md`
- `docs/11_REQUIREMENTS_TRACEABILITY.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/IMPLEMENTATION_REPORT.md`

## Assumptions and decisions

- Stage 2 is a data feasibility gate. Reading schema, timestamps, hashes, universe eligibility counts and reason-coded exclusions is data QA, not final-test strategy exposure.
- I treated `2025-07-01T00:00:00+00:00` as the intended in-period Level 5 proof cutoff because the attempt 02 report and acceptance prompt call it out explicitly.
- I treated the two required monitoring proof files as checkpoint-safe when `git check-ignore -v` resolves them through explicit negated `.gitignore` exceptions and `git status` shows them as untracked files available for commit.
- Existing uncommitted and untracked work outside the QA write scope was treated as implementation/team-lead state and was not modified.

## Files inspected or changed

Inspected:

- `.gitignore`
- `Makefile`
- `configs/default.yaml`
- `data/README.md`
- `data/manifests/ohlcv_daily_manifest.json`
- `data/processed/instruments.parquet`
- `data/processed/ohlcv_daily.parquet`
- `reports/data_card.md`
- `scripts/validate_data.py`
- `src/crypto_hedge_fund/data/download.py`
- `src/crypto_hedge_fund/data/schema.py`
- `src/crypto_hedge_fund/data/universe.py`
- `src/crypto_hedge_fund/data/validation.py`
- `tests/unit/test_data_layer.py`
- `artifacts/monitoring/level_5_pair_count_proof.json`
- `artifacts/monitoring/universe_eligibility_full.csv`

Changed:

- `reports/agent_reports/stage_02_frozen_data/attempt_02/QA_REPORT.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_uv_sync_frozen.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_make_lint.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_make_test.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_make_validate_data.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_script_validate_data.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_git_status_short_branch_untracked.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_git_check_ignore_proof_artifacts.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_artifact_proof_inspection.log`

## Deliverables

- Fresh QA command logs for all required commands.
- Read-only proof/artifact inspection log.
- This QA report with explicit attempt 01 HIGH finding closure assessment.

## Acceptance-criteria mapping

| Criterion | Status | Evidence |
|---|---:|---|
| `uv sync --frozen` passes | PASS | `command_logs/qa_uv_sync_frozen.log` |
| `make lint` passes | PASS | `command_logs/qa_make_lint.log` |
| `make test` passes | PASS | `command_logs/qa_make_test.log`: 26 passed |
| Tests include corruption/failure coverage | PASS | `tests/unit/test_data_layer.py` includes gap, stale cutoff coverage, inconsistent metadata, duplicate key, bar-end semantic error and invalid OHLC tests |
| `make validate-data` passes offline | PASS | `command_logs/qa_make_validate_data.log` |
| `uv run python scripts/validate_data.py` passes offline | PASS | `command_logs/qa_script_validate_data.log` |
| Proof JSON and CSV record full mode, in-period cutoff and >=100 pairs | PASS | `level_5_pair_count_proof.json` has `mode=full`, cutoff `2025-07-01T00:00:00+00:00`, `eligible_count=104`, `scored_count=104`; CSV confirms 104 selected/scored rows |
| Proof records hashes, filters, reason-coded rows, runtime and repo-relative paths | PASS | Proof has data/instrument/manifest/config/git hashes, eligibility rules, exclusion counts, runtime and relative CSV path; CSV has 163 symbol rows with reason codes |
| Proof artifacts are not ignored/checkpoint-safe | PASS | `command_logs/qa_git_check_ignore_proof_artifacts.log` shows explicit negated `.gitignore` exceptions for both required proof artifacts; `git status` shows them as untracked |
| No final-test strategy metrics inspected | PASS | Only data validation/proof commands were run; `qa_artifact_proof_inspection.log` reports no strategy artifact files under metrics/equity/weights/orders/fills/figures |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_make_test.log` |
| `make validate-data` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_make_validate_data.log` |
| `uv run python scripts/validate_data.py` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_script_validate_data.log` |
| `git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_git_status_short_branch_untracked.log` |
| `git check-ignore -v artifacts/monitoring/level_5_pair_count_proof.json artifacts/monitoring/universe_eligibility_full.csv || true` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_git_check_ignore_proof_artifacts.log` |
| Read-only proof inspection command | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/qa_artifact_proof_inspection.log` |

## Test and artifact evidence

- `make test` collected 26 tests and passed all 26. `tests/unit/test_data_layer.py` contributes 9 data-layer tests.
- Attempt 01 HIGH finding 1 is closed in behavior and tests. `src/crypto_hedge_fund/data/validation.py` recomputes per-symbol first/last bars, bar counts, expected counts, missing counts and coverage ratios from OHLCV, rejects any positive missing-bar count, and rejects stale latest completed bars at the proof cutoff. Tests cover continuity gap, stale coverage and inconsistent metadata.
- Attempt 01 HIGH finding 2 is closed in artifact policy. `.gitignore` keeps broad generated artifacts ignored but unignores exactly `artifacts/monitoring/level_5_pair_count_proof.json` and `artifacts/monitoring/universe_eligibility_full.csv`; the proof paths are repo-relative.
- `make validate-data` and `uv run python scripts/validate_data.py` both report 158,511 rows, 163 symbols, proof cutoff `2025-07-01T00:00:00+00:00`, 104 eligible pairs and 104 scored pairs.
- `qa_artifact_proof_inspection.log` verifies CSV and JSON counts match, reason counts are `eligible=104`, `insufficient_history=34`, `no_completed_bars_by_cutoff=22`, `stable_or_fiat_base=3`, and no strategy artifact files exist.
- Final-test exposure remains `NOT_EXPOSED` by inspected artifacts and commands.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None.

- MEDIUM
  - The frozen Binance/CCXT snapshot remains a current-active-market snapshot with survivorship and delisting bias. This is documented and acceptable for Stage 2 only if later claims do not describe it as a true historical institutional point-in-time universe.
  - The repository state is not checkpointed during this QA pass. Required data and proof files are visible to git but remain untracked until the team lead stages and commits the Stage 2 checkpoint.

- LOW
  - The existing frozen manifest still predates reason-coded persistence for the 17 requested symbols that returned no rows. The downloader now records future zero-row omissions and the current limitation is documented, but the current manifest itself was not refrozen.
  - Instrument metadata names still do not fully match broader target-schema wording such as `exchange_symbol` and `status_at_download`. The current schema is sufficient for Stage 2 validation and proof.

## Unresolved risks and limitations

- Stage 2 still has no strategy, broker, ledger, agents, portfolio layer, notebook, deck or final-test lock by design; those remain later-stage gates.
- The included data source does not reconstruct delisted markets or historical exchange membership.
- `git status` shows multiple uncommitted tracked modifications and untracked files outside the QA report/logs. I did not edit or revert any of them.
- Only the team lead can accept the stage and create the passing checkpoint.

## Recommendation

PASS_WITH_NOTES
