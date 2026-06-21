# Project State

Updated: 2026-06-21

## Current Stage

- Stage: 6 - Level 2 validation
- Attempt: 01
- Status: NOT_STARTED
- Final-test exposure state: NOT_EXPOSED

## Git Checkpoint

- Current branch: main
- Last passing commit: Stage 5 checkpoint commit
- Last passing tag: `stage/05-level-1`
- Base for Stage 6: `stage/05-level-1`

## Active Work And Reports

- Stage 1: PASSED, committed and tagged.
- Stage 2: PASSED by team lead after attempt 02 remediation.
- Stage 2 decision: `reports/agent_reports/stage_02_frozen_data/attempt_02/TEAMLEAD_DECISION.md`
- Stage 3: PASSED by team lead after attempt 02 remediation.
- Stage 3 decision: `reports/agent_reports/stage_03_shared_engine/attempt_02/TEAMLEAD_DECISION.md`
- Stage 4: PASSED by team lead after attempt 02 remediation.
- Stage 4 decision: `reports/agent_reports/stage_04_agents_risk/attempt_02/TEAMLEAD_DECISION.md`
- Stage 5: PASSED by team lead after attempt 02 remediation.
- Stage 5 decision: `reports/agent_reports/stage_05_level1_validation/attempt_02/TEAMLEAD_DECISION.md`
- Stage 2 proof:
  - `artifacts/monitoring/level_5_pair_count_proof.json`
  - `artifacts/monitoring/universe_eligibility_full.csv`

## Validated Capabilities

- Stage 1 environment skeleton: `uv sync --frozen`, `make lint`, `make test`, package import, and final-test fail-closed guard passed before commit.
- Stable command surface exists through `Makefile`.
- Stage 2 frozen data validates offline with Binance spot CCXT snapshot, 158,511 rows, 163 symbols, and 104 eligible/scored pairs at `2025-07-01T00:00:00+00:00`.
- Stage 2 validation includes explicit corruption tests for continuity gaps, stale coverage, inconsistent metadata, duplicate keys, timestamp semantics, invalid OHLC, and manifest hash mismatch.
- Stage 3 shared execution kernel validates completed-bar to `open(t+1)` timing, panel-native one/many symbol execution, risky-notional cost accounting, ledger transitions, metrics, artifact provenance and fail-closed invalid states.
- Stage 4 typed agents, orchestration, aggregation, two-stage risk gates, allocation interface, action resolver, monitoring events and decision traces validate through 66 tests.
- Stage 5 Level 1 validation generates BTC/USDT SMA validation artifacts through the shared agent/risk/broker/metrics/artifact stack. Latest lead gate: 71 tests passed and `make experiments-val` generated validation artifacts.

## Current Worktree Notes

- `MASTER_PROMPT_CODEX_TEAMLEAD.md` is owner prompt material used as process context.
- Required Stage 2 proof artifacts are explicitly unignored and checkpoint-safe.
- Stage 5 changes are ready to be committed and tagged.

## Open Blockers

- No Stage 5 blockers.
- Survivorship/delisting limitation remains for the active Binance CCXT universe and must be disclosed later.
- Stage 6 must keep final-test exposure `NOT_EXPOSED` and use temporal validation only.

## Next Action

Commit and tag Stage 5, then assign Stage 6 Level 2 validation implementation.
