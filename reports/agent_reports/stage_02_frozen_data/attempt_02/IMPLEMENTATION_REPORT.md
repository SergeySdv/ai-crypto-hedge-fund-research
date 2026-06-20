# Role / stage / attempt

Implementation fixer / Stage 2 - Frozen Data and Point-in-Time Universe / attempt 02.

## Scope

Remediated the attempt 01 HIGH findings only. The changes stay within the Stage 2 data validation, universe proof, artifact checkpoint policy, data documentation and attempt 02 reporting scope. No strategy, broker, ledger, agent, portfolio, notebook, live execution or final-test behavior was implemented or inspected.

Final-test exposure state remained `NOT_EXPOSED`.

## Sources read

- `AGENTS.md`
- `MASTER_PROMPT_CODEX_TEAMLEAD.md`
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
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/teamlead/PROJECT_STATE.md`
- `reports/teamlead/STAGE_BOARD.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/TEAMLEAD_DECISION.md`

## Assumptions and decisions

- Stage 2 proof cutoff should be an in-period decision cutoff. The implementation now selects `min(test_start + 181 days, test_end, max_bar_end)`, which yields `2025-07-01T00:00:00+00:00` for the default data.
- Instrument metadata must be treated as derived evidence, not trusted input. Validation now recomputes per-symbol `first_bar_start_utc`, `last_bar_start_utc`, `bar_count`, `expected_bar_count`, `missing_bar_count` and `coverage_ratio` from OHLCV and compares them to `instruments.parquet`.
- Continuity gaps are hard validation failures. A metadata row that accurately reports a positive `missing_bar_count` still fails the Stage 2 gate.
- Stale coverage at the proof cutoff is a hard validation failure for symbols with completed-bar history before the cutoff when their latest completed bar is older than the configured stale allowance.
- Required monitoring proofs are intended checkpoint artifacts. `.gitignore` now unignores exactly `artifacts/monitoring/level_5_pair_count_proof.json` and `artifacts/monitoring/universe_eligibility_full.csv`.
- The current frozen manifest is not silently rewritten to add no-row requested-symbol exclusions because that would alter a frozen artifact without a refreeze. The downloader now persists those exclusions for future freezes, and the limitation is documented for this snapshot.

## Files inspected or changed

Changed:

- `.gitignore`
- `data/README.md`
- `reports/data_card.md`
- `src/crypto_hedge_fund/data/download.py`
- `src/crypto_hedge_fund/data/universe.py`
- `src/crypto_hedge_fund/data/validation.py`
- `tests/unit/test_data_layer.py`
- `artifacts/monitoring/level_5_pair_count_proof.json`
- `artifacts/monitoring/universe_eligibility_full.csv`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/*`

Inspected additionally:

- `configs/default.yaml`
- `scripts/validate_data.py`
- `src/crypto_hedge_fund/data/schema.py`
- `src/crypto_hedge_fund/data/storage.py`
- `data/manifests/ohlcv_daily_manifest.json`
- `data/processed/ohlcv_daily.parquet`
- `data/processed/instruments.parquet`

## Deliverables

- Validation recomputes per-symbol OHLCV coverage and rejects inconsistent instrument metadata.
- Validation rejects positive per-symbol missing-bar counts and stale proof-cutoff coverage.
- Corruption tests now cover continuity gap, stale cutoff coverage, inconsistent metadata, duplicate key, timestamp/bar-end semantic error and invalid OHLC.
- Level 5 proof regenerated at `2025-07-01T00:00:00+00:00` with 104 eligible/scored pairs.
- Proof JSON uses repository-relative `eligibility_csv` and validation summaries use repository-relative proof paths.
- Proof CSV includes all 163 symbols, including explicit `no_completed_bars_by_cutoff` reason codes for symbols with no completed bars by the in-period cutoff.
- Required proof artifacts are no longer hidden by the broad `artifacts/` ignore rule.
- Future downloader runs persist zero-row requested symbols as `no_ohlcv_rows_returned` exclusions.

## Acceptance-criteria mapping

| Criterion | Status | Evidence |
|---|---:|---|
| `uv sync --frozen` passes | PASS | `command_logs/uv_sync_frozen.log` |
| `make lint` passes | PASS | `command_logs/make_lint.log` |
| `make test` passes | PASS | `command_logs/make_test.log`, 26 tests passed |
| `make validate-data` passes offline | PASS | `command_logs/make_validate_data.log` |
| `uv run python scripts/validate_data.py` passes offline | PASS | `command_logs/script_validate_data.log` |
| Continuity/gap/stale metadata failures are explicit | PASS | `tests/unit/test_data_layer.py` corruption tests |
| Proof artifacts checkpoint-safe | PASS | `.gitignore` narrow unignore exceptions and `command_logs/git_check_ignore_proof_artifacts.log` |
| Proof has >=100 eligible/scored pairs | PASS | JSON and command logs show 104 eligible/scored at `2025-07-01T00:00:00+00:00` |
| Proof paths are repository-relative | PASS | JSON `eligibility_csv` is `artifacts/monitoring/universe_eligibility_full.csv`; command summaries use relative paths |
| No final-test strategy metrics inspected | PASS | Only data validation/proof artifacts and tests were run |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/make_test.log` |
| `make validate-data` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/make_validate_data.log` |
| `uv run python scripts/validate_data.py` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/script_validate_data.log` |
| `git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/git_status_short_branch_untracked.log` |
| `git check-ignore -v artifacts/monitoring/level_5_pair_count_proof.json artifacts/monitoring/universe_eligibility_full.csv || true` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/git_check_ignore_proof_artifacts.log` |

## Test and artifact evidence

- `make test`: 26 passed, including 9 Stage 2 data-layer tests.
- Corruption tests added:
  - `test_validate_data_bundle_rejects_continuity_gap`
  - `test_validate_data_bundle_rejects_inconsistent_instrument_metadata`
  - `test_validate_data_bundle_rejects_stale_cutoff_coverage`
  - `test_validate_data_bundle_rejects_duplicate_key`
  - `test_validate_data_bundle_rejects_bar_end_semantic_error`
  - `test_validate_data_bundle_rejects_invalid_ohlc`
- `artifacts/monitoring/level_5_pair_count_proof.json`:
  - `decision_cutoff_utc`: `2025-07-01T00:00:00+00:00`
  - `eligible_count`: 104
  - `scored_count`: 104
  - `eligibility_csv`: `artifacts/monitoring/universe_eligibility_full.csv`
  - includes `manifest_sha256`, source metadata and data period summary.
- `artifacts/monitoring/universe_eligibility_full.csv`:
  - 163 symbol rows plus header.
  - 104 eligible and 104 selected/scored rows.
  - reason counts: `eligible=104`, `insufficient_history=34`, `no_completed_bars_by_cutoff=22`, `stable_or_fiat_base=3`.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None after remediation.

- MEDIUM
  - The frozen Binance/CCXT active-market snapshot still has survivorship and delisting bias. This is documented and remains a methodology limitation for later reporting.
  - The current frozen manifest predates reason-coded persistence for 17 requested symbols that returned no rows. Future freezes now record these as `no_ohlcv_rows_returned`, and the current snapshot limitation is documented rather than silently modified.
  - Instrument metadata naming still differs from the broader target schema in the architecture docs for fields such as `exchange_symbol` and `status_at_download`. The current schema remains sufficient for Stage 2 validation and proof.

- LOW
  - `git check-ignore -v` prints the negated `.gitignore` exception lines for the two proof artifacts. This confirms they are explicitly unignored, but reviewers should not mistake the output for an active ignore rule.

## Unresolved risks and limitations

- Stage 2 remains uncommitted and awaits independent attempt 02 QA/architecture review and team-lead decision.
- Data source universe is current-active Binance spot and is not a true historical point-in-time exchange universe with delisted markets.
- No strategy, backtester, broker/ledger, agents, portfolio logic, notebook, presentation or final-test lock exists from this attempt.
- Final-test exposure remains `NOT_EXPOSED`; no strategy returns, rankings, model outputs, charts or final-test metrics were inspected.

## Recommendation

PASS_WITH_NOTES
