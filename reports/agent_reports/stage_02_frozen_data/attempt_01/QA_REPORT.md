# Role / stage / attempt

Independent QA reviewer for Stage 2: Frozen Data and Point-in-Time Universe, attempt 01.

## Scope

Validated the Stage 2 implementation without implementation edits. I ran the required gates, inspected the frozen data files, manifest, proof artifacts, validation code path, command surface, documentation, and Git tracking/ignore state. I did not inspect or compute strategy returns or final-test performance metrics.

Final-test exposure state observed for this review: `NOT_EXPOSED`.

## Sources read

- `AGENTS.md`
- `MASTER_PROMPT_CODEX_TEAMLEAD.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/03_REPOSITORY_LAYOUT.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/11_REQUIREMENTS_TRACEABILITY.md`
- `reports/agent_reports/stage_02_implementation.md`
- `reports/agent_reports/stage_02_data_feasibility.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/SPECIALIST_REVIEW.md`
- Data/code/docs inspected under `src/crypto_hedge_fund/data/`, `scripts/*data*.py`, `scripts/freeze_data.py`, `src/crypto_hedge_fund/cli.py`, `tests/unit/test_data_layer.py`, `data/`, `reports/data_card.md`, and `artifacts/monitoring/`.

## Assumptions and decisions

- I did not rerun `make data`, because the stage objective is to validate the included frozen files offline and rerunning data would perform a live network freeze.
- I treated `make validate-data` and `uv run python scripts/validate_data.py` as the decisive offline validation gates.
- The current-active Binance universe limitation is acceptable only as a documented limitation; it is not a true historical delisted-symbol universe.
- The 2025 bars were inspected for schema/date/hash/proof coverage only. No strategy returns, metrics, charts, rankings, or parameter choices were inspected.

## Files inspected or changed

Changed only allowed QA deliverables:

- `reports/agent_reports/stage_02_frozen_data/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/command_logs/qa_uv_sync_frozen.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/command_logs/qa_make_lint.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/command_logs/qa_make_test.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/command_logs/qa_make_validate_data.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/command_logs/qa_script_validate_data.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/command_logs/qa_manifest_proof_inspect.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/command_logs/qa_git_status.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/command_logs/qa_tracking_ignore_status.log`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/command_logs/qa_git_log.log`

Inspected but did not edit: Stage 2 source, tests, data, manifest, README/data card, Makefile, config, proof artifacts, and Git state.

## Deliverables

- Independent QA report: this file.
- Command logs under `reports/agent_reports/stage_02_frozen_data/attempt_01/command_logs/`.
- Offline artifact/hash/proof inspection evidence in `qa_manifest_proof_inspect.log`.
- Tracking/ignore checkpoint evidence in `qa_tracking_ignore_status.log` and `qa_git_status.log`.

## Acceptance-criteria mapping

- `uv sync --frozen`: PASS.
- `make lint`: PASS.
- `make test`: PASS, 20 tests passed.
- `make validate-data`: PASS offline from included Parquet/manifest files.
- Direct `uv run python scripts/validate_data.py`: PASS.
- Included data files exist: PASS for `data/processed/ohlcv_daily.parquet`, `data/processed/instruments.parquet`, and `data/manifests/ohlcv_daily_manifest.json`.
- Documentation exists: PASS for `data/README.md` and `reports/data_card.md`.
- Manifest hashes match files: PASS, independently recomputed.
- Validation covers schema, UTC timestamps, unique keys, sorted rows, bar-end semantics, finite values, OHLC sanity, positive prices, nonnegative volume, manifest hash/count agreement, and deterministic universe proof: PASS.
- Full-mode Level 5 proof has at least 100 eligible/scored pairs: PASS, 115 eligible and 115 scored.
- `make data` behavior understood: PASS. It runs `uv run crypto-hedge-fund data`, which calls the CCXT freezer for the single configured source `binance` from `configs/default.yaml`; no silent exchange mixing was found. I did not run it.
- Data/proof tracking state checked: PASS with checkpoint note. Data files are untracked and not ignored; proof artifacts are ignored by `artifacts/` and require force-add or an ignore-policy exception if they must be committed.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `command_logs/qa_uv_sync_frozen.log` |
| `make lint` | 0 | `command_logs/qa_make_lint.log` |
| `make test` | 0 | `command_logs/qa_make_test.log` |
| `make validate-data` | 0 | `command_logs/qa_make_validate_data.log` |
| `uv run python scripts/validate_data.py` | 0 | `command_logs/qa_script_validate_data.log` |
| `python3 - <<'PY' ... inspect manifest/proof counts/hashes ... PY` | 0 | `command_logs/qa_manifest_proof_inspect.log` |
| `git status --short --branch --untracked-files=all` | 0 | `command_logs/qa_git_status.log` |
| `git ls-files ...; git check-ignore ...` | 0 | `command_logs/qa_tracking_ignore_status.log` |
| `git log --oneline --decorate --max-count=5` | 0 | `command_logs/qa_git_log.log` |

## Test and artifact evidence

Gate outputs:

- `uv sync --frozen`: `Audited 79 packages`.
- `make lint`: Ruff format check and Ruff lint both passed.
- `make test`: 20 tests passed.
- `make validate-data`: row count 158,511; symbol count 163; eligible count 115; scored count 115.
- Direct validation script returned the same counts and hashes.

Independent artifact probe:

- OHLCV file: `data/processed/ohlcv_daily.parquet`, 5,580,881 bytes.
- Instruments file: `data/processed/instruments.parquet`, 13,760 bytes.
- Manifest: `data/manifests/ohlcv_daily_manifest.json`, 48,926 bytes.
- Proof: `artifacts/monitoring/level_5_pair_count_proof.json`, 3,153 bytes.
- Eligibility CSV: `artifacts/monitoring/universe_eligibility_full.csv`, 22,667 bytes.
- OHLCV SHA-256: `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`, matches manifest and proof.
- Instruments SHA-256: `df7777139dd4106032280339818ba18179882c8e19141f374d87cb8e7bddf18b`, matches manifest and proof.
- Source: Binance, CCXT 4.5.59, spot, USDT, daily.
- Actual coverage: `2021-01-01T00:00:00+00:00` through `2025-12-31T00:00:00+00:00`.
- Schema sanity: 0 duplicate keys, sorted keys true, 0 bad bar-end rows, 0 OHLC-invalid rows, 0 nonpositive price rows, 0 negative volume rows, 0 negative dollar-volume rows.
- Proof mode: `full`; decision cutoff: `2026-01-01T00:00:00+00:00`; eligible/scored: 115/115; required minimum: 100.
- Eligibility CSV agrees with proof: 115 eligible and 115 selected/scored.
- Only generated files under `artifacts/` are the Stage 2 monitoring proof artifacts; no strategy metric artifacts were present.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None.

- MEDIUM
  - Instrument metadata does not exactly match the feasibility checklist naming: `exchange_symbol`, `status_at_download`, `first_bar_utc`, and `last_bar_utc` are not present under those names. Equivalent or near-equivalent fields exist for Stage 2 validation (`symbol`, `active`, `first_bar_start_utc`, `last_bar_start_utc`, precision/min-cost fields). This does not break the Stage 2 gates, but the team lead should decide whether to normalize the metadata contract before later execution/order translation stages depend on it.

- LOW
  - Checkpoint handling is required. `data/README.md`, processed Parquet files, manifest, data card, Stage 2 scripts/source/tests, and worker reports are untracked. The required proof artifacts are ignored by `.gitignore:25` via `artifacts/`; they need `git add -f` or a narrow `.gitignore` exception before a passing Stage 2 checkpoint can preserve the proof.
  - The manifest request selection is `active_spot_usdt_ranked_by_current_quote_volume`. This is disclosed in `data/README.md` and `reports/data_card.md` as survivorship/delisting bias, but later reports must not describe the universe as institutional point-in-time delisted-symbol coverage.
  - Proof JSON does not include a separate manifest-file SHA-256 or memory metric. It includes data/instrument hashes, config hash, Git commit, runtime, rules, counts, selected symbols, exclusion counts, and trailing liquidity stats, which satisfy the core Stage 2 gate.

## Unresolved risks and limitations

- The dataset is from currently active Binance spot markets. Delisted, renamed, migrated, and inactive historical markets are not reconstructed.
- The downloader uses current ticker volume for initial symbol selection. Stage 2 documents this limitation; downstream Level 5 selection must continue to use only frozen bars available at each decision cutoff.
- The proof cutoff is after the last 2025 bar (`2026-01-01T00:00:00+00:00`). This is acceptable for data feasibility proof, but it must not become a strategy-selection input.
- Raw exchange payloads are not included; reproducibility depends on the processed Parquet, manifest, hashes, and supplementary downloader.
- Stage 2 does not implement broker/ledger execution-price blocking or stale-holding valuation behavior; those belong to later execution stages.

## Recommendation

PASS_WITH_NOTES

Stage 2 QA gates pass and the included frozen dataset validates offline with a full-mode 115 eligible/scored pair proof. Before team-lead checkpointing, explicitly handle untracked/ignored data and proof artifacts, and decide whether to normalize the instrument metadata column contract now or carry the naming delta as a documented later-stage task.
