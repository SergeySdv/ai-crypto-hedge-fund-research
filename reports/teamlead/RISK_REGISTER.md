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
| R-009 | Fully invested risky targets can be infeasible after costs | Medium | Open | Stage 3 broker fails closed; Stage 4 pre/post risk and allocation must reserve cash or cap risky weights before broker submission. |
| R-010 | Benchmark helper is price-normalized rather than broker-costed | Medium | Open | Strategy stages must label price-normalized benchmarks explicitly or run costed benchmarks through `SimulatedBroker`. |
| R-011 | `CostModel` protocol does not match concrete cost breakdown return type | Low | Open | Reconcile public typing before strict static typing or external integrations rely on this protocol. |
| R-012 | Risk fallback actions skipped by downstream integration | Medium | Mitigated | Stage 4 added `resolve_risk_approval_targets(...)`; Stage 5+ must call it before broker submission. |
| R-013 | Clock boundary wording conflicts with daily equality behavior | Low | Open | Document or reconcile `decision_time == execution_time` daily boundary behavior before final methodology freeze. |
| R-014 | Validation artifacts generated from dirty source state | Medium | Mitigated | Stage 5 artifacts record `git_worktree_dirty=true` and `git_diff_sha256`; later pretest/final artifacts should be regenerated from clean committed states. |
| R-015 | Multi-level validation regenerates earlier-level artifacts | Medium | Open | Stage 6 lead restored tracked Level 1 artifact side effects before checkpointing. Later stages need an explicit policy for whether `make experiments-val` commits all refreshed validation artifacts or restores previous levels. |
| R-016 | Level 2 multiple-seed robustness is limited at trading-artifact level | Low | Accepted limitation for Stage 6 | Robustness reports seed checks, but committed trading artifacts use the primary seed. Keep disclosed and broaden only if later modeling stages require it. |
