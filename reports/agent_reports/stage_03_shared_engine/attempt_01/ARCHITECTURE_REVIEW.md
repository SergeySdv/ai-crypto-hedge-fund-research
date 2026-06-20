# Role / stage / attempt

Independent execution/accounting specialist and architecture reviewer / Stage 3: Shared Panel-Native Execution Kernel / attempt 01.

## Scope

Reviewed the uncommitted Stage 3 execution kernel for next-open timing, ledger state transitions, risky-notional transaction-cost accounting, fail-closed behavior, panel-native behavior, artifact provenance, final-test quarantine, and suitability as the common Levels 1-5 accounting foundation.

No implementation code, tests, configs, data, notebooks, presentation files, or artifacts were edited.

## Sources read

- `AGENTS.md`
- `MASTER_PROMPT_CODEX_TEAMLEAD.md`
- `docs/00_GLOBAL_PLAN_AND_AUDIT.md`
- `docs/11_REQUIREMENTS_TRACEABILITY.md`
- `docs/01_ASSIGNMENT_AND_SCOPE.md`
- `docs/02_ARCHITECTURE.md`
- `docs/03_REPOSITORY_LAYOUT.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `docs/05_IMPLEMENTATION_PLAN.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`
- `docs/07_PRESENTATION_OUTLINE.md`
- `docs/10_RISKS_AND_DECISIONS.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/teamlead/PROJECT_STATE.md`
- `reports/teamlead/STAGE_BOARD.md`
- `reports/teamlead/RISK_REGISTER.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/IMPLEMENTATION_REPORT.md`

## Assumptions and decisions

- I treated the repository documents as binding where implementation and tests disagree.
- I did not run `make final-test` and did not inspect strategy/model/portfolio performance. Final-test exposure remains `NOT_EXPOSED`.
- I classified the current clock issue as HIGH, not BLOCKER, because it is conservative against look-ahead but conflicts with the documented `open(t+1)` protocol and must be resolved before targets/models are built.
- `git diff --stat` was empty because Stage 3 files are untracked; `git status --short --branch --untracked-files=all` is the useful change inventory.

## Files inspected or changed

Inspected:

- `src/crypto_hedge_fund/clock.py`
- `src/crypto_hedge_fund/types.py`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/execution/__init__.py`
- `src/crypto_hedge_fund/execution/panel.py`
- `src/crypto_hedge_fund/execution/costs.py`
- `src/crypto_hedge_fund/execution/ledger.py`
- `src/crypto_hedge_fund/execution/broker.py`
- `src/crypto_hedge_fund/metrics/performance.py`
- `src/crypto_hedge_fund/artifacts/writers.py`
- `tests/unit/test_clock.py`
- `tests/unit/test_types.py`
- `tests/unit/test_execution_kernel.py`
- `tests/unit/test_costs.py`
- `tests/unit/test_metrics.py`
- `tests/unit/test_artifacts.py`
- `configs/default.yaml`
- `Makefile`

Changed:

- `reports/agent_reports/stage_03_shared_engine/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/arch_*.log`

## Deliverables

- Independent architecture/accounting review report.
- Fresh command logs for required commands.
- Focused timing probe log showing actual signal-bar to fill timestamp behavior.
- Focused ledger transition probe log covering cash to asset, no-change, partial rebalance, asset A to asset B, and asset to cash transitions.

## Acceptance-criteria mapping

| Criterion | Status | Evidence |
|---|---|---|
| Same completed-bar close cannot fill same close or earlier | Verified | `SimulatedBroker.run` maps each schedule bar through `build_daily_research_clock` before execution (`src/crypto_hedge_fund/execution/broker.py:103`-`108`). Test expects a `2024-01-01` signal to fill on `2024-01-03`, with no earlier PnL (`tests/unit/test_execution_kernel.py:38`-`64`). Probe confirms the same behavior in `arch_timing_probe.log`. |
| Next available open is the only fill basis | Refuted / needs decision | The broker does fill at an open price (`src/crypto_hedge_fund/execution/panel.py:88`-`115`), but the current clock sets `execution_time = bar_start + 2 days` (`src/crypto_hedge_fund/clock.py:38`-`42`). The written protocol says `execution_time_t = open of bar t+1` (`docs/04_EXPERIMENT_PROTOCOL.md:55`-`56`) and global plan says next available open `t+1` (`docs/00_GLOBAL_PLAN_AND_AUDIT.md:74`). |
| Ledger cash/holdings/equity internally consistent across transition cases | Verified by probe, partially by tests | The broker updates holdings and cash only inside `_execute_rebalance` from fills (`src/crypto_hedge_fund/execution/broker.py:218`-`305`) and records equity/weights afterward (`src/crypto_hedge_fund/execution/broker.py:183`-`209`). `arch_ledger_transition_probe.log` shows NAV, cash, risky value, weights, orders, and fills for required transition cases. |
| Cost model charges risky notional exactly and does not charge cash | Verified | Cost model computes `gross_fraction = sum(abs(target - pretrade))`, cash only for reporting turnover, fees/slippage only on risky notional (`src/crypto_hedge_fund/execution/costs.py:128`-`135`). Tests cover cash-to-asset, asset-to-cash, asset rotation, partial rebalance, no-change, and invalid weights (`tests/unit/test_costs.py:20`-`68`). |
| Missing price fails closed | Verified | `PanelMarketData.open_prices` raises `MissingPriceError` when requested execution/valuation opens are missing or invalid (`src/crypto_hedge_fund/execution/panel.py:100`-`115`). Test covers missing next-open execution price (`tests/unit/test_execution_kernel.py:67`-`82`). |
| Invalid weights fail closed | Verified | Target schedules are finite, long-only, duplicate-free, and unlevered (`src/crypto_hedge_fund/execution/broker.py:47`-`72`; `src/crypto_hedge_fund/execution/costs.py:70`-`90`). Tests cover negative and unfundable weights (`tests/unit/test_execution_kernel.py:85`-`109`). |
| Panel-native path handles one and many symbols | Verified | `PanelMarketData` normalizes long-form `(bar_start_utc, symbol)` data (`src/crypto_hedge_fund/execution/panel.py:45`-`76`), and the same `SimulatedBroker` handles one and multi-symbol schedules. Test covers deterministic one-symbol and multi-symbol runs (`tests/unit/test_execution_kernel.py:112`-`149`). |
| Deterministic outputs and artifact provenance | Verified | Deterministic repeat tested with DataFrame equality (`tests/unit/test_execution_kernel.py:133`-`147`). Artifacts carry provenance columns and JSON sidecars (`src/crypto_hedge_fund/artifacts/writers.py:18`-`43`, `52`-`73`, `90`-`104`; `tests/unit/test_artifacts.py:9`-`56`). |
| Implementation does not access final-test metrics | Verified | No final-test command was run. `make final-test` is still fail-closed until a lock and later runner exist (`src/crypto_hedge_fund/cli.py:71`-`84`). Grep found only config/date guards and no strategy result access in Stage 3 source. |
| No live trading | Verified | Stage 3 implements only `SimulatedBroker`; no live execution adapter is present in `src/crypto_hedge_fund/execution/`. |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/arch_uv_sync_frozen.log` |
| `make test` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/arch_make_test.log` |
| `uv run pytest tests/unit/test_execution_kernel.py tests/unit/test_costs.py` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/arch_pytest_execution_costs.log` |
| `git diff --stat` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/arch_git_diff_stat.log` |
| `git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/arch_git_status_short_branch_untracked.log` |
| Timing probe | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/arch_timing_probe.log` |
| Ledger transition probe | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/arch_ledger_transition_probe.log` |
| Code-path search | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/arch_code_path_search.log` |

## Test and artifact evidence

- `make test`: 39 tests passed.
- Targeted execution/cost pytest: 10 tests passed.
- `arch_timing_probe.log`: `2024-01-01` bar has `bar_end` and documented `open(t+1)` at `2024-01-02T00:00:00+00:00`, but current clock and fill timestamp are `2024-01-03T00:00:00+00:00`.
- `arch_ledger_transition_probe.log`: with zero costs and flat prices, NAV stays at 1000 through cash-to-asset, no-change, partial rebalance, rotation, and liquidation; weights and order/fill notionals reconcile.
- No repository artifacts were generated outside the allowed command-log files and this report.

## Findings by severity

- BLOCKER
  - None found.

- HIGH
  - Clock semantics conflict with the documented next-open protocol. The implementation is conservative and prevents same-close fills, but it does not execute at the documented `open(t+1)` for a completed bar. `build_daily_research_clock("2024-01-01")` returns `execution_time=2024-01-03T00:00:00+00:00`, while `docs/04_EXPERIMENT_PROTOCOL.md` specifies `execution_time_t = open of bar t+1`. This needs a team-lead decision and code/docs/test realignment before Stage 4, because Level 2 targets and Level 3/4/5 rebalance windows must match the execution kernel exactly.

- MEDIUM
  - Fully invested risky targets with nonzero costs fail closed as `InfeasibleTradeError` rather than being netted down automatically. This is acceptable as a fail-closed execution-layer behavior, but Stage 4 risk/allocator integration must explicitly reserve a cost cash buffer or cap approved weights before sending them to the broker.
  - Broker-level tests do not yet encode all ledger transition cases as automated assertions. The focused probe verifies current behavior, and cost tests cover deltas, but a regression test should be added so cash-to-asset, asset-to-cash, A-to-B, partial rebalance, and no-change ledger states remain protected.

- LOW
  - `reports/teamlead/PROJECT_STATE.md` and `reports/teamlead/STAGE_BOARD.md` still show Stage 3 as `NOT_STARTED`, while uncommitted Stage 3 implementation and reports exist. This is a management-document lag, not an execution-kernel defect.
  - `git diff --stat` is empty because Stage 3 implementation files are untracked. Reviewers must rely on `git status --short --branch --untracked-files=all` until the stage is added to Git.

## Unresolved risks and limitations

- No pre/post risk gates are implemented in Stage 3; later stages must connect risk approvals to broker inputs without allowing signals or weights to mutate ledger state directly.
- Precision, minimum notional, participation/capacity, stale valuation windows, and partial fills remain future-stage work.
- Metrics are a basic deterministic layer. Benchmark-relative analytics, statistical uncertainty, prediction metrics, and monitoring metrics are still future-stage work.
- Active-market survivorship/delisting bias from Stage 2 remains unchanged and must stay disclosed.
- The timing convention must be resolved before any feature/target/model implementation depends on it.

## Recommendation

REWORK

The accounting core is close and the tests pass, but Stage 3 should not be accepted into Stage 4 until the clock semantics are reconciled with the documented `open(t+1)` next-open protocol or the governing docs are explicitly changed to the current stricter `open(t+2)` convention. This decision affects every later target, benchmark, rebalance timestamp, and artifact label.
