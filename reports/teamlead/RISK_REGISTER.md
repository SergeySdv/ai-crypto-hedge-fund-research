# Risk Register

Updated: 2026-06-21

| ID | Risk | Severity | Status | Mitigation / Owner |
|---|---|---:|---|---|
| R-001 | Final-test contamination before pretest lock | Critical | Closed | Stage 10 accepted `artifacts/final_test_lock.json` with exposure `LOCKED`; Stage 11 ran the final suite from that accepted lock and now records exposure `EXPOSED`. |
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
| R-015 | Multi-level validation regenerates earlier-level artifacts | Medium | Mitigated | Stage 6, Stage 7 and Stage 8 leads restored tracked earlier-level artifact side effects before checkpointing. Later stages need an explicit policy for whether `make experiments-val` commits all refreshed validation artifacts or restores previous levels. |
| R-016 | Level 2 multiple-seed robustness is limited at trading-artifact level | Low | Accepted limitation for Stage 6 | Robustness reports seed checks, but committed trading artifacts use the primary seed. Keep disclosed and broaden only if later modeling stages require it. |
| R-017 | Level 3 net metrics excluded entry costs from return normalization | High | Closed | Stage 7 attempt 02 fixed initial-capital metric baseline and added regression coverage; lead probe verified net ROI below gross with positive costs. |
| R-018 | Level 3 robust method overclaim risk | Low | Open | Keep `cvar_downside` described as a standalone downside-risk heuristic, not a full scenario CVaR optimization program, in notebook/report/deck. |
| R-019 | Level 4 dynamic policy underperforms static benchmark | Medium | Accepted limitation for Stage 8 | Preserve as negative validation evidence. Notebook/report/deck must not imply dynamic rebalancing improved return or Sharpe versus the static Level 3 benchmark. |
| R-020 | Level 4 target caps are not continuous mark-to-market caps | Medium | Open | Stage 8 caps submitted targets, but drifted holdings can exceed target caps between accepted trades. Tighten or explicitly define continuous cap handling before Level 5/final narrative. |
| R-021 | Level 4 drift and signal/risk candidates converge after controls | Low | Accepted limitation for Stage 8 | Rebalance log contains signal/risk trigger rows, but accepted trades matched drift policy. Explain in narrative rather than tuning. |
| R-022 | Stage 9 100-pair validation window is short | Medium | Accepted limitation for Stage 9 | Stage 9 proves the 100-pair shared-pipeline path in late December 2024 only. Do not use it for broad performance claims; disclose in notebook/report/deck. |
| R-023 | Level 5 risk veto moves most decisions to cash | Medium | Accepted limitation for Stage 9 | Treat as fail-safe evidence, not alpha evidence. Preserve reason-code logs and avoid tuning based on validation outcomes. |
| R-024 | Level 5 benchmark is BTC-normalized rather than equal-weight eligible/top-K | Medium | Open | Fix benchmark before final narrative or disclose precisely. Do not overstate benchmark-relative Level 5 conclusions. |
| R-025 | Stage 9 `make experiments-val` regenerates prior-level artifacts | Medium | Mitigated | Attempt 03 restores tracked Level 1-4 artifact drift after validation runs. Repeat this cleanup before checkpointing later stages. |
| R-026 | Stage 10 lock records pre-commit dirty state | Medium | Accepted for Stage 10 | Accepted lock hash `dab407601cbaf8198361e5e3d074260546ed4bbab4c4be2555248b246631308b` transparently records dirty Stage 10 artifact/report state from the Stage 9 base. Stage 11 must validate this exact lock and fail closed on mismatch. |
| R-027 | Stale Stage 10 lock hashes in worker/reviewer logs | Medium | Mitigated | Team-lead decision pins the accepted lock hash. Ignore stale attempt 02 hashes `2aee73e8...` and `2b8ea386...` for Stage 11. |
| R-028 | Stage 11 first final-test run failed after partial artifacts | High | Mitigated | Worker and reviewers documented the failure. The accepted rerun regenerated final artifacts after a broker correctness fix, and no methodology retuning or result-driven selection was found. |
| R-029 | Stage 11 final artifacts ignored by default artifact policy | High | Closed | Narrow packaging fix explicitly unignored `artifacts/final_test/dab407601cba/**`; lead verified representative files are not ignored. |
| R-030 | Stage 11 final artifacts record dirty runner source provenance | Medium | Accepted limitation for Stage 11 | Final-test runner and broker fix were uncommitted when the frozen suite ran. Artifacts record dirty provenance and the final report must disclose it. |
