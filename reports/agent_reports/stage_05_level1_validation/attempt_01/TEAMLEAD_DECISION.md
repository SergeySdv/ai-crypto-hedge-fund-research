# Team Lead Decision / Stage 5 Level 1 Validation / Attempt 01

## Reports considered

- `reports/agent_reports/stage_05_level1_validation/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_04_agents_risk/attempt_02/TEAMLEAD_DECISION.md`

## Targeted diffs inspected

- `src/crypto_hedge_fund/experiments/level_1.py`
- `src/crypto_hedge_fund/strategies/sma.py`
- `src/crypto_hedge_fund/cli.py`
- `configs/default.yaml`
- `configs/fast.yaml`
- `tests/unit/test_level1_validation.py`
- `tests/unit/test_experiments_validation.py`
- Generated Level 1 artifacts under `artifacts/`
- `.gitignore`
- `git status --short --branch --untracked-files=all --ignored=matching`
- `git check-ignore -v` for Level 1 artifacts

## Commands independently rerun

| Command | Status | Key result |
|---|---:|---|
| `uv sync --frozen` | PASS | Audited 79 packages. |
| `make lint` | PASS | Ruff format/check passed; 56 files already formatted. |
| `make test` | PASS | 70 tests passed. |
| `make experiments-val` | PASS | Generated Level 1 validation metrics/equity/weights/orders/fills/figure/trace artifacts. |
| `uv run pytest tests/unit/test_level1_validation.py tests/unit/test_experiments_validation.py` | PASS | 4 focused tests passed. |
| Level 1 artifact inspection | PASS/REWORK evidence | Required artifacts exist, but are ignored by Git and provenance points to pre-Stage-5 commit. |

## Acceptance criteria passed

- Level 1 validation runner exists behind `make experiments-val`.
- The baseline uses frozen data, BTC/USDT, SMA signals, Stage 4 risk/action resolver and Stage 3 `SimulatedBroker`.
- Generated outputs are labeled `validation`; final-test exposure remains `NOT_EXPOSED`.
- Required metrics and artifacts exist locally after the run:
  - `artifacts/metrics/level_1.csv`
  - `artifacts/equity/level_1.parquet`
  - `artifacts/weights/level_1.parquet`
  - `artifacts/orders/level_1.parquet`
  - `artifacts/fills/level_1.parquet`
  - `artifacts/figures/level_1_equity_curve.png`
  - `artifacts/monitoring/level_1_decision_trace.json`
- Metrics include net/gross returns, ROI, CAGR, volatility, Sharpe, Sortino, Calmar, max drawdown, drawdown duration, turnover, exposure, trade count, fees/slippage/total cost and benchmark-relative fields.
- No final-test command, final-test lock, notebook, presentation or live trading was introduced.

## Acceptance criteria failed

- Required Level 1 validation artifacts are ignored by the current `.gitignore` and are therefore not checkpoint-safe.
- Artifact provenance records `provenance_git_commit=40d748b...`, the Stage 4 checkpoint, while the Level 1 runner and strategy code are still uncommitted. This is not honest enough for stage evidence unless the dirty/uncommitted source state is recorded or artifacts are regenerated from a clean code checkpoint.

## Unresolved risks

- Active-market survivorship/delisting limitation remains inherited from Stage 2 and must stay disclosed.
- Level 1 is a transparent validation baseline, not a profitability claim.
- The local binary allocation helper should not become a divergent portfolio stack in later stages; later levels should keep allocation behind the shared portfolio/risk contracts.

## Decision

REWORK

Stage 5 attempt 01 cannot pass until Level 1 artifacts are checkpoint-safe and provenance honestly identifies the source state used to generate them.

## Remediation packet for attempt 02

Assign a fresh implementation fixer with this constrained mission:

- Make required Level 1 validation artifacts and their sidecars checkpoint-safe. A narrow `.gitignore` exception is acceptable.
- Preserve Stage 2 monitoring proof exceptions.
- Add honest source-state provenance for validation artifacts. Acceptable approaches include:
  - include `git_worktree_dirty` and a deterministic `git_diff_sha256` / source-state hash in artifact sidecars and provenance columns; or
  - otherwise prove artifacts were regenerated from a clean committed source checkpoint.
- Regenerate Level 1 validation artifacts after the provenance/tracking fix.
- Add/update tests verifying Level 1 artifacts are not ignored and provenance includes either a clean commit state or an explicit dirty/source-state hash.
- Keep all outputs labeled `validation`; do not run or inspect final-test metrics.
- Rerun `uv sync --frozen`, `make lint`, `make test`, `make experiments-val`, and focused Level 1 pytest.

After remediation, assign fresh independent QA and architecture/leakage reviewers for attempt 02. The team lead will rerun decisive gates before any commit/tag.
