# Team Lead Decision / Stage 4 Agents Risk / Attempt 01

## Reports considered

- `reports/agent_reports/stage_04_agents_risk/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_04_agents_risk/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/TEAMLEAD_DECISION.md`

## Targeted diffs inspected

- `src/crypto_hedge_fund/types.py`
- `src/crypto_hedge_fund/agents/orchestrator.py`
- `src/crypto_hedge_fund/agents/aggregate.py`
- `src/crypto_hedge_fund/risk/pre_allocation.py`
- `src/crypto_hedge_fund/risk/post_allocation.py`
- `tests/unit/test_agents_risk.py`
- `tests/unit/test_portfolio_allocation.py`
- `git diff --stat`
- `git status --short --branch --untracked-files=all`

## Commands independently rerun

| Command | Status | Key result |
|---|---:|---|
| `uv sync --frozen` | PASS | Audited 79 packages. |
| `make lint` | PASS | Ruff format/check passed; 50 files already formatted. |
| `make test` | PASS | 62 tests passed. |
| `uv run pytest tests/unit/test_agents_risk.py tests/unit/test_orchestration.py tests/unit/test_portfolio_allocation.py tests/unit/test_monitoring_trace.py` | PASS | 16 focused Stage 4 tests passed. |

## Acceptance criteria passed

- At least two concrete agents communicate through typed `AgentSignal` records via the orchestrator.
- Signal aggregation handles confidence weighting, abstentions, disagreement and reason-code propagation.
- Pre-allocation and post-allocation risk gates exist and are tested.
- The implementation has controlled-stop coverage for stale/missing data, NaN score, stale model cutoff, excessive disagreement, optimizer failure, invalid weights, drawdown/volatility stop, liquidity/capacity breach and reconciliation failure.
- The pre-allocation gate reserves a cash/cost buffer.
- Agents do not receive broker or ledger objects, and tests cover a mutation attempt.
- Monitoring events and decision traces are notebook-ready.
- No strategy levels, final-test lock, final-test command, notebooks, presentation, live trading or final-test metrics were introduced.
- Final-test exposure remains `NOT_EXPOSED`.

## Acceptance criteria failed

- The required controlled-stop evidence asks for `NaN/inf score`; QA found explicit NaN coverage and implementation likely covers infinity through the same `math.isfinite` branch, but there is no explicit `inf` fixture.
- Architecture review found a downstream integration hazard: `RiskApproval(approved=False, action="cash"|"prior_weights")` is a valid safe fallback record, but later execution integration could accidentally treat `approved=False` as "do nothing" unless Stage 4 provides an authoritative resolver/contract for risk actions.

## Unresolved risks

- Stage 4 allocators are foundation methods only; minimum-variance and robust portfolio methods remain later-stage work.
- Capacity checks are explicit metadata/liquidity plumbing; later Levels 4-5 must connect them to rolling ADV/AUM participation calculations.
- Stage 2 survivorship/delisting limitation and Stage 3 benchmark-labeling note remain open.

## Decision

REWORK

Stage 4 attempt 01 cannot pass yet because a required controlled-stop test is indirect and the risk-action semantics must be explicit before Stage 5 connects signals/risk/allocation to the execution kernel.

## Remediation packet for attempt 02

Assign a fresh implementation fixer with this constrained mission:

- Add an explicit `inf` score controlled-stop test, not only NaN, proving non-finite agent output becomes a safe abstention or risk-blocked result with reason codes.
- Add an authoritative utility or typed method for converting `RiskApproval` into executable target weights for later broker submission:
  - `action="approve"` or `action="cap"` returns approved risky weights plus cash;
  - `action="cash"` returns all cash / zero risky weights;
  - `action="prior_weights"` returns current context risky weights plus cash;
  - invalid or unsupported action fails closed with a reason-coded error.
- Add tests proving cash and prior-weights actions are not silently skipped when `approved=False`.
- Keep the fix within Stage 4 agent/risk/portfolio/monitoring/types/tests scope.
- Do not implement strategy levels, final-test, notebooks, presentation or live trading.
- Preserve final-test exposure state `NOT_EXPOSED`.
- Rerun `uv sync --frozen`, `make lint`, `make test`, and focused Stage 4 pytest.

After remediation, assign fresh independent QA and architecture/risk reviewers for attempt 02. The team lead will rerun decisive gates before any commit/tag.
