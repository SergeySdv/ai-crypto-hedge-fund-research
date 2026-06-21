# Team Lead Decision / Stage 7 Level 3 Static Portfolio / Attempt 02

## Reports considered

- `reports/agent_reports/stage_07_level3_validation/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_02/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_02/QA_REPORT.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_02/ARCHITECTURE_REVIEW.md`
- Stage 6 checkpoint decision: `reports/agent_reports/stage_06_level2_validation/attempt_02/TEAMLEAD_DECISION.md`

## Targeted diffs inspected

- `git status --short --branch --untracked-files=all`
- `git diff --stat`
- `src/crypto_hedge_fund/experiments/level_3.py`
- `src/crypto_hedge_fund/portfolio/allocators.py`
- `tests/unit/test_level3_validation.py`
- `tests/unit/test_portfolio_allocation.py`
- Level 3 artifacts and metadata sidecars under `artifacts/`
- Level 3 monitoring artifacts:
  - `artifacts/monitoring/level_3_decision_trace.json`
  - `artifacts/monitoring/level_3_universe_selection.csv`
  - `artifacts/monitoring/level_3_final_vintage_plan.json`

## Commands independently rerun

| Command | Status | Key result |
|---|---:|---|
| `uv sync --frozen` | PASS | Audited 79 packages. |
| `make lint` | PASS | Ruff format/check passed on 66 files. |
| `make test` | PASS | 83 tests passed. |
| `make experiments-val` | PASS | Levels 1-3 validation artifacts regenerated; final-test exposure `NOT_EXPOSED`. |
| `uv run pytest tests/unit/test_level3_validation.py` | PASS | 5 tests passed. |
| Lead Level 3 artifact probe | PASS | 7 symbols, exact 2023 estimation window, 2024 validation, four methods, selected `cvar_downside`, positive costs with net ROI below gross, final-test exposure `NOT_EXPOSED`. |
| Scoped restore of Level 1/2 artifact drift | PASS | Tracked Level 1/2 artifact side effects from `make experiments-val` restored to `HEAD` before checkpoint. |

## Acceptance criteria passed

- Level 3 uses exactly 7 validation-selected assets: `BTC/USDT`, `ETH/USDT`, `XRP/USDT`, `BNB/USDT`, `SOL/USDT`, `DOGE/USDT`, and `LTC/USDT`.
- Estimation window is exactly `2023-01-01T00:00:00+00:00` through `2023-12-31T00:00:00+00:00`.
- Validation holdout is 2024 only; final 2025 performance remains unrun.
- Required methods are implemented and compared: equal weight, inverse volatility, minimum variance, and `cvar_downside`.
- Level 3 uses the shared broker, risk, metric and artifact paths rather than a standalone portfolio backtester.
- Attempt 01 HIGH H-001 is remediated: Level 3 net metrics now normalize from initial capital, positive costs are recorded, and net ROI/total return is below gross for every method.
- Regression coverage was added for the net/gross cost failure mode.
- Drawdown-filter fallback metadata is recorded: drawdown constraint, feasible method count, fallback flag, selected method, selection metric and tie-breaker.
- Required Level 3 artifacts and metadata sidecars are present and Git-visible.
- No `make final-test` was run, no final lock was created, and no 2025 returns, rankings, charts, fills or final-test metrics were inspected.
- Final-test exposure remains `NOT_EXPOSED`.

## Acceptance criteria failed

- None for Stage 7.

## Unresolved risks

- Active Binance/CCXT market survivorship and delisting bias remains accepted from Stage 2 and must stay visible in the notebook, final report and deck.
- `cvar_downside` is a robust standalone downside-risk heuristic, not a full scenario CVaR optimizer; downstream narrative must preserve that wording.
- Daily OHLCV validation does not model intraday liquidity, order-book depth, exchange outages, custody, tax or real reconciliation.
- `make experiments-val` still regenerates earlier-level artifacts as a command side effect. The Stage 7 checkpoint restores Level 1/2 tracked artifact drift before commit; a broader artifact refresh policy remains useful before final release.

## Decision

PASS

Stage 7 is accepted. The checkpoint will be committed and tagged as `stage/07-level-3`.

## Checkpoint

- Commit: this Stage 7 checkpoint commit.
- Tag: `stage/07-level-3`.
