# Team Lead Decision / Stage 7 Level 3 Static Portfolio / Attempt 01

## Reports considered

- `reports/agent_reports/stage_07_level3_validation/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- Stage 6 checkpoint decision: `reports/agent_reports/stage_06_level2_validation/attempt_02/TEAMLEAD_DECISION.md`

## Targeted diffs inspected

- `git status --short --branch --untracked-files=all`
- `git diff --stat`
- Stage 7 report files and reviewer command logs.
- Level 3 artifact probes for:
  - `artifacts/metrics/level_3.csv`
  - `artifacts/equity/level_3.parquet`
  - `artifacts/monitoring/level_3_universe_selection.csv`
  - `artifacts/monitoring/level_3_decision_trace.json`
  - `artifacts/monitoring/level_3_final_vintage_plan.json`
- Review summaries for:
  - `src/crypto_hedge_fund/experiments/level_3.py`
  - `src/crypto_hedge_fund/portfolio/allocators.py`
  - `tests/unit/test_level3_validation.py`
  - `tests/unit/test_portfolio_allocation.py`

## Commands independently rerun or accepted as reviewer evidence

Reviewer evidence shows:

| Command | Status | Evidence |
|---|---:|---|
| `uv sync --frozen` | PASS | Worker and QA logs. |
| `make lint` | PASS | Worker and QA logs. |
| `make test` | PASS | Worker and QA logs; 82 tests passed. |
| `make experiments-val` | PASS | Worker and QA logs; Levels 1-3 validation, final-test exposure `NOT_EXPOSED`. |
| `uv run pytest tests/unit/test_level3_validation.py` | PASS | Worker and QA logs; 4 tests passed. |
| `uv run pytest tests/unit/test_level3_validation.py tests/unit/test_portfolio_allocation.py` | PASS | Architecture review log; 15 tests passed. |
| Level 3 artifact/provenance probes | PASS/REWORK evidence | QA identified the net/gross cost-accounting failure. |

The lead did not perform a final acceptance gate rerun because QA found an unresolved HIGH issue. A full lead rerun will be performed after remediation.

## Acceptance criteria passed

- Level 3 implementation uses exactly 7 validation-selected assets.
- Validation estimation window is exactly `2023-01-01T00:00:00+00:00` through `2023-12-31T00:00:00+00:00`.
- Validation holdout artifacts are bounded to 2024 and final-test exposure remains `NOT_EXPOSED`.
- Equal weight, inverse volatility, minimum variance, and `cvar_downside` robust heuristic methods are implemented and compared.
- Level 3 uses the shared broker, risk policies, metrics and artifact conventions.
- Required Level 3 artifacts and sidecars exist and are Git-visible.
- No `make final-test` was run and no 2025 final-test performance metrics, rankings, charts or fills were generated or inspected.

## Acceptance criteria failed

- Net-after-cost metrics are unreliable because Level 3 computes returns from the first post-cost validation row. With positive entry costs, `level_3.csv` reports `net_roi` higher than `gross_roi`, for example `cvar_downside` has `gross_roi=1.262462` and `net_roi=1.264349`.
- Required `make experiments-val` regenerated tracked Level 1/2 artifacts and left them modified in the worktree.

## Unresolved risks

- The method-selection drawdown filter falls back when no method satisfies the configured drawdown threshold. Architecture review rates this as MEDIUM; remediation should record fallback status, feasible count, constraint, and tie-breaker in metrics/trace if feasible.
- Active Binance/CCXT universe survivorship and delisting bias remains accepted from Stage 2 and must remain disclosed.
- `cvar_downside` must stay described as a robust heuristic, not a full scenario CVaR optimizer.

## Decision

REWORK

Stage 7 attempt 01 cannot pass because independent QA found an unresolved HIGH issue in net-after-cost metrics.

## Remediation packet for attempt 02

Assign a fresh implementation fixer with this constrained mission:

- Fix Level 3 metric calculation so net performance includes initial entry costs in return normalization. Net ROI/total return must be computed from the configured initial capital or another explicitly correct pre-trade baseline, not from the first post-cost equity row.
- Regenerate Level 3 artifacts after the fix.
- Add a regression test proving that, when costs are positive and price paths are otherwise identical, net ROI/total return cannot exceed gross ROI/total return for Level 3.
- Add or update tests/probes so the corrected `level_3.csv` shows positive costs with net performance below gross on the current validation artifacts.
- Restore tracked Level 1/2 artifact side effects after running required validation commands unless the worker can document a deliberate coordinated refresh. The preferred Stage 7 checkpoint should remain scoped to Stage 7 artifacts and reports.
- If feasible, record drawdown-filter fallback status, feasible method count, drawdown constraint, and tie-breaker in Level 3 metrics or decision trace.
- Preserve `NOT_EXPOSED`; do not run `make final-test`, create a final-test lock, or inspect 2025 final-test returns, rankings, charts, fills, or model results.
- Rerun `uv sync --frozen`, `make lint`, `make test`, `make experiments-val`, `uv run pytest tests/unit/test_level3_validation.py`, and a focused net/gross cost consistency probe.

After remediation, assign fresh independent QA and portfolio/risk reviewers for attempt 02. The team lead will rerun decisive gates and inspect artifacts before any commit/tag.
