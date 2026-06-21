# Team Lead Decision / Stage 5 Level 1 Validation / Attempt 02

## Reports considered

- `reports/agent_reports/stage_05_level1_validation/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/QA_REPORT.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_02/ARCHITECTURE_REVIEW.md`

## Targeted diffs inspected

- `.gitignore`
- `configs/default.yaml`
- `configs/fast.yaml`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/provenance.py`
- `src/crypto_hedge_fund/artifacts/writers.py`
- `src/crypto_hedge_fund/experiments/level_1.py`
- `src/crypto_hedge_fund/strategies/sma.py`
- `tests/unit/test_level1_validation.py`
- `tests/unit/test_experiments_validation.py`
- Generated Level 1 artifacts and sidecars under `artifacts/`

## Commands independently rerun

| Command | Status | Key result |
|---|---:|---|
| `uv sync --frozen` | PASS | Audited 79 packages. |
| `make lint` | PASS | Ruff format/check passed; 56 files already formatted. |
| `make test` | PASS | 71 tests passed. |
| `make experiments-val` | PASS | Generated Level 1 validation artifacts; final-test exposure `NOT_EXPOSED`. |
| `uv run pytest tests/unit/test_level1_validation.py tests/unit/test_experiments_validation.py` | PASS | 5 focused tests passed. |
| Level 1 artifact inspection | PASS | Required artifacts exist, are validation-labeled, include required metrics, and carry source-state provenance. |
| `git check-ignore` Level 1 artifact checks | PASS | Level 1 artifacts are explicitly unignored and checkpoint-safe. |

## Acceptance criteria passed

- Level 1 validation runner is reachable through `make experiments-val`.
- BTC/USDT SMA baseline uses frozen data, completed bars, Stage 4 risk/action resolver and Stage 3 `SimulatedBroker`.
- The run is validation-only and does not inspect or create final-test metrics.
- Required artifacts exist:
  - `artifacts/metrics/level_1.csv`
  - `artifacts/equity/level_1.parquet`
  - `artifacts/weights/level_1.parquet`
  - `artifacts/orders/level_1.parquet`
  - `artifacts/fills/level_1.parquet`
  - `artifacts/figures/level_1_equity_curve.png`
  - `artifacts/monitoring/level_1_decision_trace.json`
- Metrics include net/gross ROI, CAGR, volatility, Sharpe, Sortino, Calmar, max drawdown, drawdown duration, turnover, exposure, trade count, costs and benchmark-relative fields.
- Artifacts and sidecars include validation split, data hash, config hash, git commit, dirty worktree flag, `git_diff_sha256`, period, benchmark, seed, costs and warnings.
- Level 1 artifacts are checkpoint-safe through narrow `.gitignore` exceptions.
- No notebook, presentation, final-test lock, final-test command or live trading was introduced.
- Final-test exposure remains `NOT_EXPOSED`.

## Acceptance criteria failed

- None for Stage 5 attempt 02.

## Unresolved risks

- Artifacts intentionally record `git_worktree_dirty=true` because they were generated before the Stage 5 checkpoint commit; this is accepted because the deterministic source-state hash is recorded. Later pretest/final artifacts should be regenerated from clean committed states.
- Active-market survivorship/delisting limitation remains inherited from Stage 2.
- Level 1 is a transparent validation baseline and not a profitability claim.
- The local binary allocator should be folded into or kept aligned with shared portfolio abstractions as later levels add richer allocation methods.

## Decision

PASS

Stage 5 attempt 02 is accepted. The checkpoint will be committed and tagged as `stage/05-level-1`.

## Checkpoint

- Commit: this Stage 5 checkpoint commit.
- Tag: `stage/05-level-1`.
