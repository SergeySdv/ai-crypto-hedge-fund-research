# Role / stage / attempt

Independent QA reviewer / Stage 3: Shared Panel-Native Execution Kernel / attempt 01.

## Scope

Reviewed the uncommitted Stage 3 execution-kernel implementation as a QA reviewer only. I ran the required gates, inspected the Stage 3 source, tests, artifact writer behavior, Git scope, and final-test quarantine state. I did not edit implementation code, configs, data, tests, notebooks, strategy artifacts, or production artifacts, and I did not run `make final-test`.

## Sources read

- `AGENTS.md`
- `MASTER_PROMPT_CODEX_TEAMLEAD.md`
- `docs/02_ARCHITECTURE.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/teamlead/PROJECT_STATE.md`
- `reports/teamlead/STAGE_BOARD.md`
- `reports/teamlead/REQUIREMENTS_STATUS.md`
- `reports/agent_reports/stage_02_frozen_data/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/IMPLEMENTATION_REPORT.md`

## Assumptions and decisions

- Reading Stage 2 data proof artifacts and repository status is not final-test strategy exposure; I did not inspect strategy returns, rankings, model outputs, charts, or final-test metrics.
- The required `git diff --stat` command was run exactly, but it is empty because the Stage 3 implementation files are currently untracked. Scope review therefore used `git status --short --branch --untracked-files=all` and direct file inspection.
- Artifact-writer behavior was inspected through `tests/unit/test_artifacts.py`, which writes to pytest `tmp_path`, not repository production artifacts.

## Files inspected or changed

Inspected:

- `src/crypto_hedge_fund/execution/panel.py`
- `src/crypto_hedge_fund/execution/costs.py`
- `src/crypto_hedge_fund/execution/ledger.py`
- `src/crypto_hedge_fund/execution/broker.py`
- `src/crypto_hedge_fund/metrics/performance.py`
- `src/crypto_hedge_fund/artifacts/writers.py`
- `src/crypto_hedge_fund/types.py`
- `src/crypto_hedge_fund/cli.py`
- `tests/unit/test_execution_kernel.py`
- `tests/unit/test_costs.py`
- `tests/unit/test_metrics.py`
- `tests/unit/test_artifacts.py`
- `tests/unit/test_types.py`
- `Makefile`
- `configs/default.yaml`
- `artifacts/monitoring/level_5_pair_count_proof.json`
- `artifacts/monitoring/universe_eligibility_full.csv`

Changed:

- `reports/agent_reports/stage_03_shared_engine/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/qa_uv_sync_frozen.log`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/qa_make_lint.log`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/qa_make_test.log`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/qa_pytest_stage3_unit.log`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/qa_git_diff_stat.log`
- `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/qa_git_status_short_branch_untracked.log`

## Deliverables

- Ran and logged all required commands.
- Mapped Stage 3 acceptance criteria to tests and inspected source behavior.
- Verified artifact writer behavior uses temporary test output and does not mutate production artifacts.
- Verified worker changes are in Stage 3 source/test/report/log paths only, with no configs, data, notebooks, strategy levels, final-test lock, presentation, or live-trading code added.
- Identified two rework findings before Stage 4 should build on this kernel.

## Acceptance-criteria mapping

| Criterion | QA result | Evidence |
|---|---:|---|
| Completed-bar signals cannot affect same-close or earlier PnL | PASS | `tests/unit/test_execution_kernel.py:38` asserts no NAV change on Jan 1 or Jan 2 and fill only on Jan 3 for a Jan 1 completed-bar signal. |
| Next-open broker execution exists and is tested | PASS | `SimulatedBroker.run` maps schedule bars through `build_daily_research_clock`; explicit test evidence at `tests/unit/test_execution_kernel.py:60-64`. |
| Cash→asset, asset→cash, asset A→asset B, partial rebalance, no-change costs tested | PASS | `tests/unit/test_costs.py:20`, `:34`, `:38`, `:42`, `:49`. |
| No charge for cash as instrument | PASS | `tests/unit/test_costs.py:20-31`; `WeightDeltaCostModel` computes fees from risky deltas only. |
| Missing next-open price fails/blocks explicitly | PASS | `tests/unit/test_execution_kernel.py:67-82`; source raises `MissingPriceError`. |
| Invalid weights fail closed | PASS | `tests/unit/test_execution_kernel.py:85-109`; `tests/unit/test_costs.py:61-68`. |
| One-symbol and multi-symbol configs use same engine | PASS | `tests/unit/test_execution_kernel.py:112-145` runs one- and two-symbol schedules through `SimulatedBroker`. |
| Deterministic repeatability | PASS | `tests/unit/test_execution_kernel.py` compares repeated equity and order frames in the same engine test. |
| Required metrics exist | REWORK | Current metrics output covers return/CAGR/volatility/Sharpe/Sortino/Calmar/drawdown/turnover/costs, but does not expose required `VaR/CVaR`, explicit `downside_deviation`, cash, concentration/effective N/risk contribution metrics from `docs/02_ARCHITECTURE.md:243-252`. Source returns only the keys at `src/crypto_hedge_fund/metrics/performance.py:76-100`; test asserts only the narrower set at `tests/unit/test_metrics.py:23-31`. |
| Artifacts carry provenance | PASS_WITH_NOTES | `tests/unit/test_artifacts.py` verifies metrics CSV, parquet provenance columns, and sidecar JSON using `tmp_path`. Provenance includes data/config/git hashes, split, period, costs, benchmark, seed, warnings, and optional lock hash. Later stages should add full final-lock/uv-lock metadata if required. |
| Final-test quarantine preserved | PASS | I did not run `make final-test`; artifact sweep found only Stage 2 monitoring proof files under `artifacts/`; `src/crypto_hedge_fund/cli.py` still fails closed without `artifacts/final_test_lock.json`. |
| Mandatory typed-agent negative tests | REWORK | `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md:191-198` requires tests for invalid score, confidence, horizon, cutoff, and reason-code values. `tests/unit/test_types.py:28-53` tests only valid construction and invalid score for `AgentSignal`; confidence, horizon, fit/feature cutoff ordering, and invalid reason code are implemented but not covered by the mandatory tests. |

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/qa_uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/qa_make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/qa_make_test.log` |
| `uv run pytest tests/unit/test_execution_kernel.py tests/unit/test_costs.py tests/unit/test_metrics.py tests/unit/test_artifacts.py` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/qa_pytest_stage3_unit.log` |
| `git diff --stat` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/qa_git_diff_stat.log` |
| `git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_03_shared_engine/attempt_01/command_logs/qa_git_status_short_branch_untracked.log` |

## Test and artifact evidence

- `make test` passed: 39 tests collected and passed, including Stage 3 execution, costs, metrics, artifacts, and prior data/type tests.
- Focused Stage 3 pytest passed: 13 tests collected and passed across execution kernel, costs, metrics, and artifact writer tests.
- `make lint` passed: Ruff format check reported 34 files already formatted and Ruff check reported all checks passed.
- Artifact writer test writes only under pytest `tmp_path` and verifies metrics CSV, parquet artifact provenance columns, and JSON sidecar metadata.
- Repository artifact sweep found no strategy metrics/equity/weights/orders/fills/figures files; only Stage 2 monitoring proof files are present.
- `git status --short --branch --untracked-files=all` shows Stage 3 implementation files are untracked under `src/crypto_hedge_fund/execution/`, `src/crypto_hedge_fund/metrics/`, `src/crypto_hedge_fund/artifacts/`, `tests/unit/`, and Stage 3 report/log paths.

## Findings by severity

- BLOCKER: None.

- HIGH: Shared metrics layer is incomplete against the documented required metric surface. `docs/02_ARCHITECTURE.md:243-252` requires VaR/CVaR, downside deviation, cash, concentration/effective N/risk contributions, and benchmark-relative metrics as part of the shared metrics layer. `calculate_performance_metrics` currently returns only the narrower set at `src/crypto_hedge_fund/metrics/performance.py:76-100`, and `tests/unit/test_metrics.py:23-31` does not test the missing metrics. Future levels would either lack required metrics or reimplement metrics outside the shared kernel.

- HIGH: Mandatory typed-record negative tests are incomplete. Stage 3 gate requires tests that typed agent records reject invalid score, confidence, horizon, cutoff, and reason-code values (`docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md:191-198`). Existing `tests/unit/test_types.py:28-53` only tests invalid score for `AgentSignal`. The implementation appears to validate the omitted cases in `src/crypto_hedge_fund/types.py`, but the mandated regression coverage is not present.

- MEDIUM: Benchmark support is not yet proven to use the same broker/cost path. Stage 3 scope includes benchmarks and metrics, and acceptance criteria require benchmarks to use the same clock, tradability, and costs. The current visible benchmark helper is raw open-to-open price normalization in `PanelMarketData.benchmark_open_to_open`; I did not find a test proving benchmark execution through the broker with costs. This should be tightened before benchmark artifacts become user-facing.

- LOW: `git diff --stat` is empty because all Stage 3 implementation files are untracked. This is not an implementation defect, but reviewers and the team lead must rely on `git status --untracked-files=all` until the Stage 3 changes are staged or committed.

## Unresolved risks and limitations

- Stage 3 intentionally does not implement agents, orchestrator, pre/post risk gates, portfolio optimization, strategy levels, notebooks, final report, or presentation.
- Precision, minimum notional, participation/capacity, stale valuation windows, partial fills, and rejected-order modeling remain future-stage work.
- A fully invested target can be valid by weights but infeasible once costs are included; the broker fails closed. Stage 4 risk/allocation should reserve a cost buffer or cap target risky exposure before execution.
- Binance active-market survivorship/delisting limitation from Stage 2 remains unchanged and must stay visible later.

## Recommendation

REWORK

The core next-open broker, ledger, risky-notional cost accounting, missing-price fail-closed behavior, invalid-weight checks, deterministic panel execution, and artifact writer tests pass. Rework should be limited to completing the shared metric surface and adding the missing mandatory typed-record negative tests, with a benchmark-through-shared-cost-path test if the benchmark helper remains part of Stage 3.
