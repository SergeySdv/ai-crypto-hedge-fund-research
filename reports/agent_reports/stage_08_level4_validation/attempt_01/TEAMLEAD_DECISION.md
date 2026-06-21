# Team Lead Decision / Stage 8 Level 4 Dynamic Rebalancing / Attempt 01

## Reports considered

- `reports/agent_reports/stage_08_level4_validation/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_08_level4_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_08_level4_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- Stage 7 checkpoint decision: `reports/agent_reports/stage_07_level3_validation/attempt_02/TEAMLEAD_DECISION.md`

## Targeted diffs inspected

- `git status --short --branch --untracked-files=all`
- `git diff --stat`
- `src/crypto_hedge_fund/experiments/level_4.py`
- `src/crypto_hedge_fund/portfolio/rebalance.py`
- `tests/unit/test_level4_validation.py`
- `tests/unit/test_portfolio_rebalance.py`
- Level 4 artifacts and metadata sidecars under `artifacts/`
- Level 4 monitoring artifacts:
  - `artifacts/monitoring/level_4_rebalance_log.parquet`
  - `artifacts/monitoring/level_4_decision_trace.json`
  - `artifacts/monitoring/level_4_final_vintage_plan.json`

## Commands independently rerun

| Command | Status | Key result |
|---|---:|---|
| `uv sync --frozen` | PASS | Audited 79 packages. |
| `make lint` | PASS | Ruff format/check passed on 69 files. |
| `make test` | PASS | 92 tests passed. |
| `make experiments-val` | PASS | Levels 1-4 validation artifacts regenerated; final-test exposure `NOT_EXPOSED`. |
| `uv run pytest tests/unit/test_level4_validation.py` | PASS | 4 tests passed. |
| Lead Level 4 artifact probe | PASS | Four policies, selected `calendar_monthly`, rebalance log submitted/skipped rows and calendar/drift/signal/risk trigger evidence, final-test exposure `NOT_EXPOSED`. |
| Scoped restore of Level 1-3 artifact drift | PASS | Tracked Level 1-3 artifact side effects from `make experiments-val` restored to `HEAD` before checkpoint. |

## Acceptance criteria passed

- Level 4 uses the Stage 7 seven-asset small portfolio and shared broker/risk/metrics/artifact stack.
- Dynamic policy candidates are implemented for monthly calendar, drift threshold, and signal/risk-triggered rebalancing.
- Rebalance controls include transaction costs, turnover cap, minimum trade threshold, target max weight, liquidity/capacity proxy constraints, pre-allocation risk, post-allocation risk and fail-closed behavior.
- Rebalance log records reason/trigger codes, submitted and skipped rows, and before/candidate/approved weights.
- Required Level 4 artifacts and metadata sidecars are present and Git-visible.
- Policy selection is validation-only. The static Level 3 benchmark is reported but not eligible for Level 4 selection.
- Selected feasible dynamic policy is `calendar_monthly`.
- No `make final-test` was run, no final lock was created, and no 2025 returns, rankings, charts, fills or final-test metrics were inspected.
- Final-test exposure remains `NOT_EXPOSED`.

## Acceptance criteria failed

- None for Stage 8.

## Unresolved risks

- Dynamic Level 4 underperformed the static Level 3 benchmark in 2024 validation. This is accepted as negative research evidence and must be disclosed without implying improvement.
- `drift_monthly` and `signal_risk_monthly` produced identical validation metrics after turnover/risk controls. Signal and risk trigger rows are present, but the narrative must explain that they did not add incremental accepted trades in this run.
- Max-weight controls cap submitted target weights, while drifted actual holdings can exceed target caps between accepted trades. This must be disclosed and revisited before Level 5 if max weight is treated as a continuous hard holding cap.
- Active Binance/CCXT market survivorship and delisting bias remains accepted from Stage 2 and must stay visible in the notebook, final report and deck.

## Decision

PASS

Stage 8 is accepted. The checkpoint will be committed and tagged as `stage/08-level-4`.

## Checkpoint

- Commit: this Stage 8 checkpoint commit.
- Tag: `stage/08-level-4`.
