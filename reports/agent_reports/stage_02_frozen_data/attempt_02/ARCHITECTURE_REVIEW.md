# Role / stage / attempt

Independent architecture/requirements reviewer / Stage 2 - Frozen Data and Point-in-Time Universe / attempt 02.

## Scope

Reviewed the attempt 02 remediation for the Stage 2 frozen data layer against the repository architecture invariants, Stage 2 gate, and the attempt 01 HIGH findings. I focused on data validation, point-in-time universe eligibility, proof artifacts, documentation, tests, and final-test quarantine.

I did not edit implementation, tests, data, configs, management files, or strategy code. I did not run `make data`, `make final-test`, any strategy experiment, or any command intended to inspect strategy performance.

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
- `reports/teamlead/REQUIREMENTS_STATUS.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/IMPLEMENTATION_REPORT.md`
- Stage 2 implementation files, tests, data docs, manifest, and proof artifacts listed below.

## Assumptions and decisions

- Reading 2025 bar coverage and universe eligibility counts is data validation/proof work for Stage 2, not strategy final-test exposure. I did not inspect returns, model outputs, strategy rankings, portfolio metrics, charts, or final-test artifacts.
- Stage 2 does not need broker, ledger, cost, risk, portfolio, agent, notebook, or presentation implementation. I audited only whether the data foundation preserves those future requirements.
- The required `uv run python scripts/validate_data.py` command regenerates monitoring proof artifacts by design. I treated that command-side rewrite as validation evidence, not as a manual data edit.
- Proof artifacts are considered checkpoint-safe when they are visible to Git and can be deliberately committed. They are not yet tracked because the whole Stage 2 attempt is still uncommitted.

## Files inspected or changed

Inspected:

- `.gitignore`
- `configs/default.yaml`
- `data/README.md`
- `data/manifests/ohlcv_daily_manifest.json`
- `data/processed/instruments.parquet`
- `data/processed/ohlcv_daily.parquet`
- `reports/data_card.md`
- `artifacts/monitoring/level_5_pair_count_proof.json`
- `artifacts/monitoring/universe_eligibility_full.csv`
- `scripts/validate_data.py`
- `src/crypto_hedge_fund/data/download.py`
- `src/crypto_hedge_fund/data/schema.py`
- `src/crypto_hedge_fund/data/storage.py`
- `src/crypto_hedge_fund/data/universe.py`
- `src/crypto_hedge_fund/data/validation.py`
- `tests/unit/test_data_layer.py`

Changed by this review:

- `reports/agent_reports/stage_02_frozen_data/attempt_02/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/arch_*`

Command side effects:

- `uv run python scripts/validate_data.py` regenerated `artifacts/monitoring/level_5_pair_count_proof.json` and `artifacts/monitoring/universe_eligibility_full.csv`.

## Deliverables

- This architecture/requirements review report.
- Reviewer command logs under `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/arch_*`.
- Recommendation: `PASS_WITH_NOTES`.

## Acceptance-criteria mapping

| Criterion | Status | Evidence |
|---|---:|---|
| Attempt 01 HIGH 1: validation recomputes and enforces continuity/gap/stale checks | PASS | `src/crypto_hedge_fund/data/validation.py` recomputes per-symbol first/last bars, bar counts, expected counts, missing counts and coverage ratios from OHLCV, compares them to metadata, rejects positive `missing_bar_count`, and rejects stale coverage at the proof cutoff. |
| Attempt 01 HIGH 1: tests cover gap/stale/corruption failure modes | PASS | `tests/unit/test_data_layer.py` includes corruption tests for continuity gap, inconsistent metadata, stale cutoff coverage, duplicate keys, bar-end semantic error, invalid OHLC and manifest hash mismatch. Focused pytest run passed: 9 tests. |
| Attempt 01 HIGH 2: proof artifacts are checkpoint-safe | PASS_WITH_NOTES | `.gitignore` now unignores exactly `artifacts/monitoring/level_5_pair_count_proof.json` and `artifacts/monitoring/universe_eligibility_full.csv`; `git status` shows both files as untracked, not hidden. `git check-ignore -q` returned exit 1 for both files. Team lead still must include them in the Stage 2 checkpoint. |
| Full proof is in-period and has at least 100 eligible/scored pairs | PASS | Validation proof cutoff is `2025-07-01T00:00:00+00:00` with `eligible_count=104` and `scored_count=104`. |
| Proof provenance is sufficient and repository-relative | PASS | Proof JSON records mode, cutoff, data/instrument/manifest/config/git hashes, source, data period, rules, selected/scored symbols, counts, exclusion reason counts, runtime, liquidity stats and repo-relative `eligibility_csv`. |
| Point-in-time universe avoids future bars/returns | PASS_WITH_NOTES | `eligible_universe_at` uses `bar_end_utc <= decision_cutoff_utc`; no strategy returns or metrics are computed. The source universe is still a current-active Binance snapshot, documented as survivorship/delisting biased. |
| Completed-bar/next-open semantics remain supportable | PASS | OHLCV schema has UTC `bar_start_utc` and `bar_end_utc`; validation enforces `bar_end_utc = bar_start_utc + 1 day`. Later execution can use completed-bar decisions and next-open fills. |
| Missing/stale/corrupt data fails explicitly | PASS | Validation raises `DataValidationError` for duplicate keys, timestamp semantics, non-finite/invalid OHLCV, metadata mismatch, continuity gaps, stale proof-cutoff coverage and hash mismatch. |
| Frozen data and metadata are included for offline validation | PASS_WITH_NOTES | Parquet data, instruments, manifest, data README and data card are present in the worktree and validation runs offline. They are still untracked until the Stage 2 commit. |
| Panel-native architecture preserved | PASS | Data is long-form keyed by `(bar_start_utc, symbol)` and universe functions work on one or many symbols without a separate single-asset path. |
| One future broker/ledger/cost/metric layer preserved | PASS | Attempt 02 did not introduce strategy, backtester, broker, ledger, cost, metric, risk or portfolio code. No standalone backtester was added. |
| Final-test quarantine remains `NOT_EXPOSED` | PASS | Inspected artifacts are data/proof only; no metrics/equity/weights/orders/fills/figures or final-test lock artifacts were generated or read. |
| No live trading/secrets/private APIs/default network dependency | PASS | Default validation uses included files. Downloader remains supplementary; no live order or credential path was added. |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/arch_git_status_short_branch_untracked.log` |
| `git diff --stat` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/arch_git_diff_stat.log` |
| `uv run python scripts/validate_data.py` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/arch_validate_data.log` |
| `git check-ignore -v artifacts/monitoring/level_5_pair_count_proof.json artifacts/monitoring/universe_eligibility_full.csv || true` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/arch_git_check_ignore_proof_artifacts.log` |
| `rg -n "missing_bar_count\|Stale OHLCV\|proof_cutoff\|eligibility_csv\|test_validate_data_bundle_rejects\|artifacts/monitoring\|no_completed_bars_by_cutoff" ...` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/arch_code_test_proof_inspection.log` |
| `uv run pytest tests/unit/test_data_layer.py` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/arch_pytest_data_layer.log` |
| `git check-ignore -q ...; printf ...` | 0 | `reports/agent_reports/stage_02_frozen_data/attempt_02/command_logs/arch_check_ignore_quiet_status.log` |

## Test and artifact evidence

- `uv run python scripts/validate_data.py` passed and reported:
  - rows: 158,511
  - symbols: 163
  - min bar start: `2021-01-01T00:00:00+00:00`
  - max bar start: `2025-12-31T00:00:00+00:00`
  - proof path: `artifacts/monitoring/level_5_pair_count_proof.json`
  - eligibility path: `artifacts/monitoring/universe_eligibility_full.csv`
  - decision cutoff: `2025-07-01T00:00:00+00:00`
  - eligible/scored: 104/104
  - data hash: `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`
  - instrument hash: `df7777139dd4106032280339818ba18179882c8e19141f374d87cb8e7bddf18b`
- `uv run pytest tests/unit/test_data_layer.py` passed: 9 tests.
- `level_5_pair_count_proof.json` records `mode=full`, source metadata, data/config/git/manifest hashes, in-period cutoff, 104 eligible/scored pairs, selected symbols, exclusion counts and repo-relative CSV path.
- `universe_eligibility_full.csv` has one row per included symbol with eligibility, reason code, valid history, trailing valid days, trailing median dollar volume, first/last bars, rank, cutoff and selected flag.
- `git status --short --branch --untracked-files=all` shows the proof artifacts and frozen data files are visible as untracked files, not hidden by `.gitignore`.
- `git check-ignore -q` returned exit 1 for both proof files, confirming they are not ignored. The required verbose check prints the negated `.gitignore` exception lines.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None. The two attempt 01 HIGH findings are closed for architecture review purposes.

- MEDIUM
  - The frozen data source remains a current-active Binance/CCXT spot snapshot, not a true historical point-in-time exchange universe with delisted markets. This is documented in `data/README.md` and `reports/data_card.md`; later reports must preserve that limitation and avoid institutional point-in-time claims.
  - The frozen manifest predates the new downloader behavior that records zero-row requested symbols as `no_ohlcv_rows_returned`. The limitation is documented instead of silently refreezing the manifest, which is acceptable for Stage 2 but should remain visible in provenance discussions.
  - Stage 2 files, including the delivered data and proof artifacts, are still untracked because the stage is not committed. The ignore-policy defect is fixed, but the team lead must explicitly include the intended data/proof files in the checkpoint.

- LOW
  - `git check-ignore -v` prints negated unignore rules for the proof files; this can look confusing in logs. The quiet check confirms both files are not ignored.
  - The proof JSON includes `created_at_utc` and `runtime_seconds`, so rerunning validation can dirty a tracked proof artifact. That is acceptable for a generated proof, but the team lead should expect it during gate reruns.

## Unresolved risks and limitations

- Stage 2 remains in review until independent QA/team-lead decision; this report is not the stage pass decision.
- Broker, ledger, cost model, risk gates, agents, portfolio allocation, notebook, presentation, final-test lock and strategy artifacts remain later-stage work.
- Data coverage is sufficient for Stage 2 proof, but the later Level 5 strategy still must actually score at least 100 eligible pairs in full mode using the shared architecture.
- The final-test exposure state remains `NOT_EXPOSED` based on inspected commands and artifacts.
- No public repository or clean-clone proof exists yet; those are later-stage requirements.

## Recommendation

PASS_WITH_NOTES

Attempt 02 resolves the attempt 01 HIGH findings. Validation now fails explicit continuity/gap/stale/corruption cases, tests cover the remediated failure modes, and the required proof artifacts are no longer ignored. The in-period proof at `2025-07-01T00:00:00+00:00` shows 104 eligible/scored pairs with sufficient provenance. Stage 3 can proceed after the team lead records the stage decision and checkpoints the intended data/proof artifacts.
