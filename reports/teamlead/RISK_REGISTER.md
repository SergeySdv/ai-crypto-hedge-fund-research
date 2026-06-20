# Risk Register

Updated: 2026-06-21

| ID | Risk | Severity | Status | Mitigation / Owner |
|---|---|---:|---|---|
| R-001 | Final-test contamination before pretest lock | Critical | Open | Keep final-test state NOT_EXPOSED. Do not inspect strategy returns or 2025 final metrics until `artifacts/final_test_lock.json` exists. |
| R-002 | Stage 2 worker PASS claim not independently reviewed | High | Closed | Attempt 02 QA and architecture reviews passed with notes; lead reran gates. |
| R-003 | Generated pair-count proof is under ignored `artifacts/` | High | Closed | `.gitignore` now explicitly unignores the required Stage 2 proof artifacts. |
| R-004 | Active Binance CCXT markets create survivorship/delisting bias | High | Accepted limitation for MVP | Document prominently in `data/README.md`, `reports/data_card.md`, final report and deck. Do not claim true institutional point-in-time universe. |
| R-005 | Stage 2 data source may not satisfy later strategy-level Level 5 scoring semantics | Medium | Open | Later Stage 5 must use same eligibility code and prove 100+ scored pairs in full mode. |
| R-006 | Stage 2 uncommitted changes include implementation files outside lead write scope | Medium | Closed | Worker/reviewer scope reviewed; lead will checkpoint accepted worker changes. |
| R-007 | `MASTER_PROMPT_CODEX_TEAMLEAD.md` is owner prompt material | Low | Accepted | Preserve as process context; do not modify unless owner explicitly requests. |
| R-008 | Missing stale/delisting reconstruction can affect historical realism | Medium | Open | Maintain explicit limitation; fail closed on missing execution prices in later execution stages. |
