# Team Lead Decision / Stage 3 Shared Engine / Attempt 01

## Reports considered

- `reports/agent_reports/stage_03_shared_engine/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/ARCHITECTURE_REVIEW.md`
- Stage 2 checkpoint decision: `reports/agent_reports/stage_02_frozen_data/attempt_02/TEAMLEAD_DECISION.md`

## Targeted diffs inspected

- `git status --short --branch --untracked-files=all`
- Stage 3 report files and reviewer command logs.
- Worker/reviewer summaries for:
  - `src/crypto_hedge_fund/execution/**`
  - `src/crypto_hedge_fund/metrics/**`
  - `src/crypto_hedge_fund/artifacts/**`
  - `tests/unit/test_execution_kernel.py`
  - `tests/unit/test_costs.py`
  - `tests/unit/test_metrics.py`
  - `tests/unit/test_artifacts.py`

## Commands independently rerun or accepted as reviewer evidence

Reviewer evidence shows:

| Command | Status | Evidence |
|---|---:|---|
| `uv sync --frozen` | PASS | Worker, QA, and architecture logs. |
| `make lint` | PASS | Worker and QA logs. |
| `make test` | PASS | Worker, QA, and architecture logs; 39 tests passed. |
| `uv run pytest tests/unit/test_execution_kernel.py tests/unit/test_costs.py tests/unit/test_metrics.py tests/unit/test_artifacts.py` | PASS | Worker and QA logs; 13 tests passed. |
| `uv run pytest tests/unit/test_execution_kernel.py tests/unit/test_costs.py` | PASS | Architecture log; 10 tests passed. |
| Focused timing and ledger probes | PASS/REWORK evidence | Architecture logs identified the timing mismatch and ledger-transition coverage gap. |

The lead did not perform a final gate rerun because independent review found unresolved HIGH issues. A full lead rerun will be performed only after remediation.

## Acceptance criteria passed

- A panel-native broker/ledger/cost implementation exists and is exercised by tests.
- Core cost cases are implemented and tested: cash-to-asset, asset-to-cash, asset rotation, partial rebalance, and no-change deltas.
- Cash is not charged as a fee-bearing instrument.
- Missing next-open prices and invalid weights fail closed.
- One-symbol and multi-symbol schedules use the same broker path.
- Artifact writer tests verify provenance columns and sidecar metadata.
- No strategy levels, final-test metrics, live trading, notebook, report, or presentation were introduced.
- Final-test exposure remains `NOT_EXPOSED`.

## Acceptance criteria failed

- Clock semantics conflict with the governing docs. The Stage 3 implementation fills a signal from `2024-01-01` at `2024-01-03` open, while `docs/04_EXPERIMENT_PROTOCOL.md` specifies execution at `open(t+1)`, i.e. `2024-01-02`.
- The shared metrics surface is incomplete for documented portfolio/risk needs: VaR/CVaR, explicit downside deviation, cash, concentration/effective-N, risk-contribution, and benchmark-relative coverage are missing or untested.
- Mandatory typed-record negative tests are incomplete for invalid confidence, horizon, cutoff ordering, and reason-code values.
- Broker-level ledger transition probes are not yet automated regression tests.
- Benchmark behavior is not yet proven to use shared broker/cost conventions.

## Unresolved risks

- Fully invested risky targets with nonzero costs fail closed unless an allocator/risk layer reserves a transaction-cost cash buffer. This is acceptable execution-layer behavior, but Stage 4 must account for it before submitting target weights to the broker.
- Stage 2 active-market survivorship/delisting limitation remains accepted and must stay disclosed.

## Decision

REWORK

Stage 3 attempt 01 cannot pass because independent QA and architecture reviews found unresolved HIGH findings.

## Remediation packet for attempt 02

Assign a fresh implementation fixer with this constrained mission:

- Align clock semantics to the governing protocol: a completed bar at date `t` must execute at the next available open of bar `t+1`, not `t+2`.
- Update execution tests so a `2024-01-01` completed-bar decision fills at `2024-01-02` open and cannot affect the `2024-01-01` close or earlier state.
- Preserve explicit fail-closed behavior for missing `open(t+1)` prices.
- Complete the shared metrics surface or clearly scoped Stage 3 equivalent for VaR, CVaR, explicit downside deviation, cash exposure, concentration/effective-N, risk contribution, and benchmark-relative metrics; add tests.
- Add typed-record negative tests for invalid score, confidence, horizon, cutoff ordering, and reason-code values.
- Convert architecture reviewer ledger transition probes into automated regression tests covering cash-to-asset, no-change, partial rebalance, asset rotation, and liquidation ledger state consistency.
- Add or adjust benchmark tests so benchmark behavior is traceable to the same timing/cost conventions, or document precisely why only price-normalized benchmark series belongs in Stage 3.
- Do not implement strategy levels, agents, final-test, notebooks, presentation, or live trading.
- Preserve final-test state `NOT_EXPOSED`; do not run `make final-test` or inspect strategy returns, rankings, charts, or model results.
- Rerun `uv sync --frozen`, `make lint`, `make test`, and focused Stage 3 pytest commands.

After remediation, assign fresh independent QA and architecture/execution-accounting reviewers for attempt 02. The team lead will rerun decisive gates and inspect artifacts before any commit/tag.
