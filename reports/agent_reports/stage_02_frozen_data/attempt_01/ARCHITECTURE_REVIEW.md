# Architecture/requirements reviewer / Stage 2 Frozen Data / attempt 01

## Scope

Independent architecture and requirements audit of the uncommitted Stage 2 frozen-data implementation. I reviewed only the data layer, manifest, validation gate, point-in-time universe proof, documentation, and Stage 2 reports. I did not implement fixes, inspect strategy/final-test performance, run `make final-test`, or edit implementation/data/config files.

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
- `reports/agent_reports/stage_02_frozen_data/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_01/SPECIALIST_REVIEW.md`
- `reports/agent_reports/stage_02_data_feasibility.md`
- `reports/agent_reports/stage_02_implementation.md`
- Stage 2 changed paths and artifacts listed below.

## Assumptions and decisions

- Stage 2 is a feasibility/data-contract gate, not a strategy gate. I treated broker, ledger, portfolio, agent, and strategy functionality as out of scope except where Stage 2 would block later architecture.
- Reading 2025 bar timestamps, coverage, and eligibility counts is data validation, not final-test strategy exposure. I did not inspect returns, strategy metrics, charts, model rankings, or portfolio results.
- The worker's PASS claim is not sufficient evidence; I reran the required validation command and inspected actual generated artifacts.
- Synthetic data in `tests/unit/test_data_layer.py` is acceptable as test fixture data because it is labeled test-only and not used for the default data bundle.

## Files inspected or changed

Inspected:

- `README.md`
- `.gitignore`
- `Makefile`
- `configs/default.yaml`
- `configs/fast.yaml`
- `data/README.md`
- `data/manifests/ohlcv_daily_manifest.json`
- `data/processed/ohlcv_daily.parquet`
- `data/processed/instruments.parquet`
- `reports/data_card.md`
- `artifacts/monitoring/level_5_pair_count_proof.json`
- `artifacts/monitoring/universe_eligibility_full.csv`
- `scripts/download_data.py`
- `scripts/freeze_data.py`
- `scripts/validate_data.py`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/data/__init__.py`
- `src/crypto_hedge_fund/data/download.py`
- `src/crypto_hedge_fund/data/schema.py`
- `src/crypto_hedge_fund/data/storage.py`
- `src/crypto_hedge_fund/data/universe.py`
- `src/crypto_hedge_fund/data/validation.py`
- `tests/unit/test_data_layer.py`

Changed:

- `reports/agent_reports/stage_02_frozen_data/attempt_01/ARCHITECTURE_REVIEW.md`

## Deliverables

- This architecture/requirements review report.
- Verdict: `REWORK` before Stage 3.

## Acceptance-criteria mapping

| Criterion | Status | Evidence |
|---|---|---|
| Included frozen OHLCV, instrument metadata and manifest exist | PASS | `data/processed/ohlcv_daily.parquet`, `data/processed/instruments.parquet`, and `data/manifests/ohlcv_daily_manifest.json` exist. Validation output reports 158,511 rows, 163 symbols, data hash `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`, instrument hash `df7777139dd4106032280339818ba18179882c8e19141f374d87cb8e7bddf18b`. |
| Manifest records source, timestamps, request, counts and hashes | PASS_WITH_NOTES | Manifest records Binance/CCXT 4.5.59, request range, 180 requested symbols, actual 2021-01-01 through 2025-12-31 coverage, row/symbol counts, hashes and per-symbol coverage. It does not record no-row requested symbols as reason-coded exclusions. |
| Validation covers schema, duplicate, timezone, OHLC, positive/finite values and hashes | PASS | `src/crypto_hedge_fund/data/validation.py` validates required columns, UTC timestamp dtypes, unique `(bar_start_utc, symbol)`, sorted rows, `bar_end_utc = bar_start_utc + 1 day`, finite numeric values, positive prices, non-negative volume/dollar volume, OHLC sanity, source/config agreement and manifest hashes. |
| Validation covers continuity/gap/stale requirements | FAIL | Current data has `missing_bar_count_sum=0` and coverage min 1.0, but the validation gate does not independently fail per-symbol gaps/stale metadata. `_validate_instruments` only checks required columns, uniqueness, metadata coverage range and symbol inclusion; it does not recompute and assert `first_bar`, `last_bar`, `bar_count`, `missing_bar_count`, or stale cutoff consistency against OHLCV. Tests do not include gap/stale corruption cases. |
| Universe selection is deterministic and point-in-time | PASS_WITH_NOTES | `eligible_universe_at` uses `bar_end_utc <= decision_cutoff_utc`, static exclusions, minimum valid history and trailing 90-day liquidity. However, the freeze candidate list is ranked by current ticker quote volume before download, so survivorship/current-liquidity bias remains a documented limitation. |
| Full-mode proof records at least 100 eligible/scored pairs | PASS_WITH_NOTES | `uv run python scripts/validate_data.py` generated `eligible_count=115`, `scored_count=115`. The CSV contains symbol-level reason, valid history, trailing valid days, trailing median dollar volume, first/last bars, rank and selected flag. The JSON records mode, cutoff, hashes, rules, counts, selected symbols, exclusion counts and runtime. Proof cutoff is `2026-01-01T00:00:00+00:00`, just after the configured final-test period, so an in-period proof date should also be recorded before relying on this for later Stage 5 evidence. |
| Proof artifacts are checkpoint-safe for public review | FAIL | Required proof files exist locally under `artifacts/monitoring/`, but `.gitignore` ignores `artifacts/`, `git check-ignore` confirms both proof files are ignored, and `git ls-files` shows they are not tracked. They can be regenerated by validation, but Stage 2 checkpoint handling is unresolved. |
| Default clean-clone path can validate included data offline | PASS_WITH_NOTES | `uv run python scripts/validate_data.py` validates included Parquet and manifest without a download. A true clean clone cannot be fully proven until the untracked data files and proof handling are committed/forced as intended. |
| No strategy/final-test metrics generated or inspected | PASS | Only data validation/proof artifacts exist under `artifacts/monitoring/`; no `artifacts/metrics`, equity, weights, orders, fills, or figures were present. I did not run strategy commands. |
| Scope stayed within data layer/reporting; no standalone backtester | PASS | New implementation paths are data scripts/modules, CLI data commands, data docs, and data tests. No strategy, broker, ledger, risk, portfolio, or backtest engine was added in Stage 2. |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `git status --short --branch --untracked-files=all` | 0 | Branch `main`; tracked modifications in `README.md` and `src/crypto_hedge_fund/cli.py`; Stage 2 data/code/report files untracked; proof artifacts not shown because ignored. |
| `git diff --stat` | 0 | Tracked diff only: `README.md` and `src/crypto_hedge_fund/cli.py`, 66 insertions and 7 deletions. |
| `uv run python scripts/validate_data.py` | 0 | Reproduced validation result: 158,511 rows, 163 symbols, 115 eligible/scored pairs, data hash `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`, instrument hash `df7777139dd4106032280339818ba18179882c8e19141f374d87cb8e7bddf18b`. |
| `find artifacts -maxdepth 3 -type f \| sort` | 0 | Only `artifacts/monitoring/level_5_pair_count_proof.json` and `artifacts/monitoring/universe_eligibility_full.csv` exist. |
| `jq . artifacts/monitoring/level_5_pair_count_proof.json` | 0 | Proof JSON records mode `full`, cutoff `2026-01-01T00:00:00+00:00`, 115 eligible/scored, hashes, rules, selected symbols, exclusion counts and runtime. |
| `head -n 20 artifacts/monitoring/universe_eligibility_full.csv` | 0 | CSV includes per-symbol eligibility, reason, valid history days, trailing valid days, trailing median dollar volume, first/last bar, rank, cutoff and selected flag. |
| `wc -l artifacts/monitoring/universe_eligibility_full.csv` | 0 | 164 lines: one header plus 163 symbols with rows. |
| `uv run python - <<'PY' ... parquet summary ... PY` | 0 | Data shape `(158511, 12)`, instruments shape `(163, 16)`, coverage min 1.0, missing-bar sum 0, active false count 0, market type `spot`. |
| `uv run python - <<'PY' ... eligibility by cutoff ... PY` | 0 | Eligibility counts: 2024-01-01=69, 2024-07-01=77, 2025-01-01=87, 2025-04-01=95, 2025-07-01=104, 2025-10-01=110, 2026-01-01=115. |
| `git check-ignore -v artifacts/monitoring/level_5_pair_count_proof.json artifacts/monitoring/universe_eligibility_full.csv` | 0 | Both proof files ignored by `.gitignore:25:artifacts/`. |
| `git ls-files data/processed/ohlcv_daily.parquet data/processed/instruments.parquet data/manifests/ohlcv_daily_manifest.json artifacts/monitoring/level_5_pair_count_proof.json artifacts/monitoring/universe_eligibility_full.csv` | 0 | No output: these files are not tracked at review time. |

## Test and artifact evidence

- `scripts/validate_data.py` is a thin wrapper around `validate_data_bundle`; the gate passes.
- `src/crypto_hedge_fund/data/validation.py` enforces core schema/hash/timestamp/OHLC checks and writes the full-mode proof.
- `src/crypto_hedge_fund/data/universe.py` implements deterministic static exclusions, `bar_end_utc <= decision_cutoff_utc`, minimum history days, trailing liquidity window and median dollar volume ranking.
- `artifacts/monitoring/level_5_pair_count_proof.json` records 115 eligible/scored pairs, `mode=full`, decision cutoff, data/instrument/config/git hashes, eligibility rules, exclusion counts, selected symbols and runtime.
- `artifacts/monitoring/universe_eligibility_full.csv` records all 163 symbols with data, eligibility reason codes and symbol-level coverage/liquidity fields.
- Current included data summary shows zero missing bars in `instruments.parquet`, but that is not equivalent to a robust validation check for future regenerated bundles.
- No strategy artifacts or final-test performance outputs were found.

## Findings by severity

- BLOCKER
  - None found during this review.

- HIGH
  - Validation does not satisfy the required continuity/gap/stale coverage gate. `docs/04_EXPERIMENT_PROTOCOL.md` requires coverage, missingness, first/last bars, data hashes and 100+ proof as automated checks, and `docs/06_ACCEPTANCE_CRITERIA.md` requires coverage/missingness/stale semantics. The implementation validates schema and hashes but `_validate_instruments` does not recompute per-symbol continuity from OHLCV or fail when `missing_bar_count > 0`, metadata first/last/bar counts are inconsistent, or a symbol is stale relative to the proof cutoff. Tests in `tests/unit/test_data_layer.py` cover synthetic proof, hash mismatch and static exclusions, but not duplicate, gap, stale, timezone or OHLC corruption fixtures. This should be reworked before Stage 3 because later next-open execution and risk blocks depend on trustworthy gap/stale semantics.
  - Required Stage 2 proof artifacts are not checkpoint-safe. `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md` requires `artifacts/monitoring/universe_eligibility_full.csv` and `artifacts/monitoring/level_5_pair_count_proof.json` as Stage 2 evidence. They exist locally after validation, but `.gitignore` ignores `artifacts/`, `git check-ignore` confirms both files are ignored, and `git ls-files` shows neither proof artifact nor the data files are tracked yet. The lead must choose force-add, ignore-policy exception, or deterministic regeneration plus an accepted checkpoint policy before Stage 2 is accepted.

- MEDIUM
  - The 100+ pair proof cutoff is `2026-01-01T00:00:00+00:00`, generated by `_proof_cutoff` as `test_end + 1 day` bounded by `max_bar_end`. That proves post-period data availability but is not itself an in-2025 rebalance date. Read-only eligibility counts show the data reaches 100+ by 2025-07-01, so this is likely fixable by recording an in-period full-mode proof date or multiple proof dates. Without that, the Stage 2 proof is weaker than the later Level 5 full-run claim will need.
  - The freeze path silently omits requested symbols that return no OHLCV rows. `load_spot_usdt_symbols` selects up to 180 current active symbols, while `_fetch_symbol_ohlcv` can return an empty frame; the freeze loop prints the zero-row status but does not persist those symbols as exclusions or download failures unless an exception occurs. The manifest records 180 requested symbols and 163 data symbols but no reason-coded no-data list. This weakens provenance and exclusion auditability.
  - Instrument metadata schema drifts from the documented required names. `docs/02_ARCHITECTURE.md` calls for `exchange_symbol`, `status_at_download`, precision fields and minimum notional where available. `src/crypto_hedge_fund/data/schema.py` requires `active`, coverage fields and optional `min_amount`, `min_cost`, `precision_amount`, `precision_price`, but not `exchange_symbol` or `status_at_download`. The current data is usable, but the mismatch should be resolved or explicitly documented as an intentional schema decision.

- LOW
  - `level_5_pair_count_proof.json` stores `eligibility_csv` as an absolute local path under `/Users/sergei/...`. Since proof files may be committed or reviewed outside this machine, artifact paths should be repository-relative or generated at validation time only.
  - The proof JSON does not directly include exchange/source/date coverage/row count; those are in the manifest and validation output. This is acceptable if the proof is always reviewed with the manifest, but the Stage 2 prompt asks the proof to record source, timestamps, filters, counts and runtime. Adding the manifest hash and basic source/date fields would make the proof more self-contained.

## Unresolved risks and limitations

- Binance/CCXT active-market snapshot has survivorship and delisting bias. This is documented in `README.md`, `data/README.md`, and `reports/data_card.md`; it remains a real limitation and must not be described later as a true institutional point-in-time universe.
- The initial downloader candidate ranking uses current ticker quote volume. The later eligibility proof is point-in-time over included bars, but the data source universe itself is still current-active/current-liquidity biased.
- Stage 2 did not and should not implement broker, ledger, cost model, risk gates, agents, portfolio allocation, final-test lock, notebook or deck. Those remain later-stage risks.
- Final-test exposure remains `NOT_EXPOSED` based on inspected artifacts and commands; no strategy metrics were generated or read.

## Recommendation

REWORK

Stage 2 has a credible included data bundle and a passing 115-pair validation proof, and it stays within data-layer scope. However, it should not pass the architecture gate until the validation gate explicitly covers continuity/gap/stale corruption and the required proof artifacts have a checkpoint-safe handling plan. The proof cutoff and provenance details should also be tightened before Stage 3 to avoid carrying ambiguity into the shared execution kernel and Level 5 implementation.
