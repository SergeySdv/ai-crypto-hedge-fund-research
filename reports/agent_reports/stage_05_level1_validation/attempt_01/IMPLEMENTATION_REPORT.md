# Role / stage / attempt

Implementation worker / Stage 5: Level 1 validation / attempt 01.

## Scope

Implemented validation-only Level 1: BTC/USDT SMA crossover baseline through the shared Stage 3 broker/ledger/metrics/artifact stack and the Stage 4 typed signal, orchestration, risk approval and risk-action resolution path.

No final-test command was run. No 2025 final-test metrics, returns, rankings, charts or model outputs were inspected or created.

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
- `reports/agent_reports/stage_03_shared_engine/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_04_agents_risk/attempt_02/TEAMLEAD_DECISION.md`

## Assumptions and decisions

- Level 1 evaluates only the configured validation period, `2024-01-01` through `2024-12-31`.
- The first validation fill may come from the completed `2023-12-31` bar, executing at the `2024-01-01` open, then artifacts are trimmed to validation timestamps only.
- SMA windows are selected from the configured bounded grid using validation net Sharpe. Default selected pair from the full included data run: fast `30`, slow `100`.
- Buy-and-hold is broker-costed through `SimulatedBroker`, not just price-normalized, with the same validation clock and cost assumptions.
- Gross metrics are produced from the same approved target schedule with zero fees/slippage; net metrics are primary and also retained under unprefixed metric names.
- Pre-risk reserves configured cash/cost buffer and post-risk approval is resolved through `resolve_risk_approval_targets(...)` before target weights are passed to the broker.

## Files inspected or changed

Inspected existing implementation:

- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/config.py`
- `src/crypto_hedge_fund/clock.py`
- `src/crypto_hedge_fund/types.py`
- `src/crypto_hedge_fund/execution/**`
- `src/crypto_hedge_fund/agents/**`
- `src/crypto_hedge_fund/risk/**`
- `src/crypto_hedge_fund/portfolio/**`
- `src/crypto_hedge_fund/metrics/performance.py`
- `src/crypto_hedge_fund/artifacts/writers.py`
- relevant existing unit tests under `tests/unit/`

Changed or created:

- `src/crypto_hedge_fund/strategies/__init__.py`
- `src/crypto_hedge_fund/strategies/sma.py`
- `src/crypto_hedge_fund/experiments/__init__.py`
- `src/crypto_hedge_fund/experiments/level_1.py`
- `src/crypto_hedge_fund/cli.py`
- `configs/default.yaml`
- `configs/fast.yaml`
- `tests/unit/test_level1_validation.py`
- `tests/unit/test_experiments_validation.py`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/*`
- this report

Generated validation artifacts:

- `artifacts/metrics/level_1.csv`
- `artifacts/equity/level_1.parquet`
- `artifacts/weights/level_1.parquet`
- `artifacts/orders/level_1.parquet`
- `artifacts/fills/level_1.parquet`
- `artifacts/figures/level_1_equity_curve.png`
- `artifacts/monitoring/level_1_decision_trace.json`
- metadata sidecars emitted by the existing Stage 3 artifact writer

## Deliverables

- `crypto-hedge-fund experiments-val` and `make experiments-val` now run Level 1 validation.
- SMA crossover baseline emits typed `AgentSignal` records through `TypedAgentOrchestrator`.
- Daily target weights pass through pre-allocation risk, binary cash/asset allocation, rebalance decision, post-allocation risk, and `resolve_risk_approval_targets(...)`.
- Shared `SimulatedBroker` executes the selected schedule at next opens.
- Net/gross metrics and broker-costed buy-and-hold benchmark are written to Level 1 artifacts.
- Decision trace JSON shows representative signal, aggregate, constraints, proposal, approval and resolved target action.
- Equity curve PNG is generated from actual validation output.
- Tests cover shared broker use, next-open timing, validation-only filtering, provenance and CLI wiring.

## Acceptance-criteria mapping

- Level 1 BTC/USDT SMA baseline: implemented in `src/crypto_hedge_fund/strategies/sma.py` and `src/crypto_hedge_fund/experiments/level_1.py`.
- Shared architecture, not standalone backtester: execution uses `SimulatedBroker`, Stage 4 orchestrator/risk records and Stage 3 artifact writer.
- Completed-bar, next-open timing: target schedule indexes completed bars; fills occur at the next UTC open; focused tests assert this behavior.
- Validation-only split: runner refuses `validation_end >= test_start`, filters market rows to `<= validation_end`, and artifacts span `2024-01-01` to `2024-12-31`.
- Gross and net reporting: metric row contains primary net fields plus `net_*` and `gross_*` fields.
- Buy-and-hold benchmark: benchmark is broker-costed and included in benchmark-relative metrics.
- Provenance: artifact metadata includes split, period, data hash, config hash, git commit, costs, benchmark, seed and warnings.
- Final-test quarantine: no `final-test` command run, no final-test lock created, and output payload states `NOT_EXPOSED`.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/make_test.log` |
| `make experiments-val` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/make_experiments_val.log` |
| `uv run pytest tests/unit/test_level1_validation.py tests/unit/test_experiments_validation.py` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/focused_level1_pytest.log` |
| `git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/git_status_short_branch_untracked.log` |

Additional evidence command:

| Command | Exit status | Evidence/log |
|---|---:|---|
| Artifact evidence probe | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/artifact_evidence.log` |

## Test and artifact evidence

- Full test suite: 70 passed.
- Focused Level 1 tests: 4 passed.
- `make experiments-val` selected SMA fast `30`, slow `100`.
- Full validation metrics from `artifact_evidence.log`:
  - net ROI: `1.186110921467134`
  - net Sharpe: `1.953537040280226`
  - net maximum drawdown: `-0.2002716100462116`
  - net total cost: `10770.857678522843`
  - gross ROI: `1.1991902392661182`
  - benchmark total return: `1.1903213194638522`
- Artifact timestamp bounds:
  - equity: `2024-01-01 00:00:00+00:00` to `2024-12-31 00:00:00+00:00`, 366 rows.
  - weights: `2024-01-01 00:00:00+00:00` to `2024-12-31 00:00:00+00:00`, 366 rows.
  - fills: `2024-01-01 00:00:00+00:00` to `2024-12-31 00:00:00+00:00`, 262 rows.
- Provenance:
  - split: `validation`
  - period: `2024-01-01` to `2024-12-31`
  - benchmark: `broker_costed_buy_and_hold`
  - git commit recorded: `40d748b27a284ce3c8efa7c0b7204a5608b3904b`
  - data hash: `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`
  - config hash: `0ac673b154e14619aeb516523913f3ff479e688b67a25c247fee1cef810bd2e1`
  - final-test lock hash: `None`
- Artifact hashes are recorded in `artifact_evidence.log`.
- Decision trace representative signal agent is `sma_crossover`; representative approval action is `approve`.

## Findings by severity

- BLOCKER: None.
- HIGH: None.
- MEDIUM: Active Binance/CCXT survivorship and delisting limitation remains inherited from Stage 2 and must stay disclosed later.
- LOW: Level 1 currently selects only from SMA fast/slow windows. Broader sensitivity/bootstrap checks are later validation-stage work, not part of this Stage 5 Level 1 slice.

## Unresolved risks and limitations

- Final-test exposure remains `NOT_EXPOSED`; later stages must continue quarantine until the pretest lock exists.
- Level 1 is a transparent baseline only; performance should not be interpreted as alpha or profitability evidence.
- Stage 5 implements Level 1 only. Levels 2-5, notebook, presentation, pretest lock and final-test suite remain future stages.
- The daily research clock still uses the accepted Stage 4 equality convention at the daily boundary: `decision_time == execution_time == next open`.

## Recommendation

PASS_WITH_NOTES
