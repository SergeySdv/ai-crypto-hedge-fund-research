# Decision Log

Updated: 2026-06-21

| ID | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| D-001 | 2026-06-21 | Use Git tags as stage checkpoints. | Stage gate docs define Git as the project control plane. | Active |
| D-002 | 2026-06-21 | Last passing baseline is `7df063f` / `stage/01-env-skeleton`. | `git log` and tags show Stage 1 committed at HEAD. | Active |
| D-003 | 2026-06-21 | Stage 2 attempt 01 required rework. | Architecture review found unresolved HIGH findings for gap/stale validation and ignored proof artifacts. | Superseded |
| D-004 | 2026-06-21 | Preserve final-test exposure state as NOT_EXPOSED. | No final-test lock exists and this turn is documentation-only. | Active |
| D-005 | 2026-06-21 | Normalize Stage 2 reports under `reports/agent_reports/stage_02_frozen_data/attempt_01/`. | Human inspection requires stable attempt-level report paths. | Active |
| D-006 | 2026-06-21 | Do not modify `MASTER_PROMPT_CODEX_TEAMLEAD.md`. | It is an untracked owner prompt file and outside the requested write scope. | Active |
| D-007 | 2026-06-21 | Stage 2 attempt 02 passed. | Independent QA and architecture reviews found no blocker/high findings; lead reran gates and verified 104 eligible/scored pairs at `2025-07-01T00:00:00+00:00`. | Active |
| D-008 | 2026-06-21 | Preserve Stage 2 proof artifacts in Git. | Required monitoring proofs are part of the Stage 2 acceptance evidence and are explicitly unignored. | Active |
| D-009 | 2026-06-21 | Stage 3 attempt 01 required rework. | QA and execution/accounting reviews found unresolved HIGH findings in clock semantics, metrics coverage and typed-record/ledger regression coverage. | Superseded |
| D-010 | 2026-06-21 | Stage 3 attempt 02 passed. | Fresh QA and execution/accounting architecture reviews found no blocker/high findings; lead reran gates and verified `open(t+1)` timing, cost accounting, ledger transitions, metrics and artifact provenance. | Active |
| D-011 | 2026-06-21 | Stage 4 must reserve cost cash before broker submission. | Stage 3 intentionally fails closed for fully invested cost-bearing target weights instead of silently creating leverage. | Active |
| D-012 | 2026-06-21 | Stage 4 attempt 01 required rework. | Lead required explicit infinity-score controlled-stop evidence and authoritative risk-action resolver semantics before strategy execution integration. | Superseded |
| D-013 | 2026-06-21 | Stage 4 attempt 02 passed. | Fresh QA and architecture/risk reviews found no blocker/high/medium findings; lead reran gates and verified agent interaction, two-stage risk, controlled stops and risk-action resolver behavior. | Active |
| D-014 | 2026-06-21 | Stage 5 attempt 01 required rework. | Level 1 artifacts were ignored and provenance pointed only to the Stage 4 commit while Stage 5 code was uncommitted. | Superseded |
| D-015 | 2026-06-21 | Stage 5 attempt 02 passed. | Artifacts are checkpoint-safe and record dirty source-state provenance; lead reran validation-only gates and verified Level 1 artifacts. | Active |
| D-016 | 2026-06-21 | Stage 6 attempt 01 required rework. | Required Level 2 artifacts were ignored and econometric refit cadence evidence was inconsistent. | Superseded |
| D-017 | 2026-06-21 | Stage 6 attempt 02 passed. | Independent QA and modeling/leakage reviews found no blocker/high findings; lead reran gates and verified Level 2 artifacts, cadence, future-label audit and final-test quarantine. | Active |
| D-018 | 2026-06-21 | Restore tracked Level 1 artifact side effects before Stage 6 checkpoint. | `make experiments-val` regenerates earlier levels; Stage 6 commit should stay scoped to Level 2 evidence and code. | Active |
| D-019 | 2026-06-21 | Stage 7 attempt 01 required rework. | QA found Level 3 net metrics normalized from first post-cost row, making net ROI exceed gross despite positive costs. | Superseded |
| D-020 | 2026-06-21 | Stage 7 attempt 02 passed. | Independent QA and portfolio/risk reviews found no blocker/high findings; lead reran gates and verified 7 assets, exact 2023 estimation, 2024 validation, net below gross with positive costs and final-test quarantine. | Active |
| D-021 | 2026-06-21 | Restore tracked Level 1/2 artifact side effects before Stage 7 checkpoint. | `make experiments-val` regenerates earlier levels; Stage 7 commit should stay scoped to Level 3 evidence and code. | Active |
| D-022 | 2026-06-21 | Stage 8 attempt 01 passed. | Independent QA and portfolio/risk reviews found no blocker/high findings; lead reran gates and verified dynamic policies, rebalance logs, Level 4 artifacts and final-test quarantine. | Active |
| D-023 | 2026-06-21 | Accept negative Level 4 dynamic-vs-static validation result. | Assignment requires honest dynamic rebalancing evaluation, not improvement. Dynamic underperformance is disclosed as validation evidence. | Active |
| D-024 | 2026-06-21 | Restore tracked Level 1/2/3 artifact side effects before Stage 8 checkpoint. | `make experiments-val` regenerates earlier levels; Stage 8 commit should stay scoped to Level 4 evidence and code. | Active |
