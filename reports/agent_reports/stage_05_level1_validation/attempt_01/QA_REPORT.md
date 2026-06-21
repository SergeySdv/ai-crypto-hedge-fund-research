# Role / stage / attempt

Independent QA reviewer / Stage 5: Level 1 validation / attempt 01.

## Scope

Report-only QA for the validation-only Level 1 implementation. I reran the required command gates, inspected generated Level 1 artifacts and provenance, reviewed source/test evidence for shared-engine use and final-test quarantine, and wrote only this report plus `qa_*.log` command logs.

No implementation files, commits, tags, final-test commands, notebooks, presentation files or live-trading paths were touched.

## Sources read

- `AGENTS.md`
- `MASTER_PROMPT_CODEX_TEAMLEAD.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `docs/13_IMPLEMENTATION_STRATEGY_AND_STAGE_GATES.md`
- `reports/agent_reports/stage_03_shared_engine/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_04_agents_risk/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/IMPLEMENTATION_REPORT.md`

Additional inspected evidence:

- `src/crypto_hedge_fund/experiments/level_1.py`
- `src/crypto_hedge_fund/strategies/sma.py`
- `tests/unit/test_level1_validation.py`
- `tests/unit/test_experiments_validation.py`
- Generated `artifacts/` Level 1 files and sidecar metadata

## Assumptions and decisions

- The QA target is Stage 5 Level 1 only; Levels 2-5, pretest freeze, final-test execution, notebook and presentation are out of scope.
- `make final-test` is forbidden for this stage and was not run.
- Validation artifact metrics may be inspected because final-test exposure is declared `NOT_EXPOSED`.
- The uncommitted/untracked Stage 5 implementation state is expected for this attempt, but it affects artifact git provenance until the team-lead checkpoint is committed and rerun.

## Files inspected or changed

Inspected:

- Required source documents listed above
- `src/crypto_hedge_fund/experiments/level_1.py`
- `src/crypto_hedge_fund/strategies/sma.py`
- `tests/unit/test_level1_validation.py`
- `tests/unit/test_experiments_validation.py`
- Fresh Level 1 artifacts under `artifacts/metrics`, `artifacts/equity`, `artifacts/weights`, `artifacts/orders`, `artifacts/fills`, `artifacts/figures`, and `artifacts/monitoring`

Changed:

- `reports/agent_reports/stage_05_level1_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_uv_sync_frozen.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_make_lint.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_make_test.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_make_experiments_val.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_focused_level1_pytest.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_artifact_inspection.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_source_test_evidence.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_artifact_file_inventory.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_git_diff_stat.log`
- `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_git_status_short_branch_untracked.log`

## Deliverables

- Independent QA command logs for all required commands.
- Artifact inspection log proving required Level 1 files, metric/provenance fields, timestamp ranges, sidecars and hashes.
- Source/test evidence log for shared broker/risk path and final-test quarantine.
- This QA report.

## Acceptance-criteria mapping

- Shared Stage 3 broker/ledger/cost/metrics/artifact stack: PASS. `level_1.py` uses `SimulatedBroker`, `calculate_performance_metrics`, `BacktestArtifactWriter`, and Stage 4 risk/orchestration records; focused tests monkeypatch and verify `SimulatedBroker.run`.
- Completed-bar signal executes at next open: PASS. Source builds daily clocks from completed bars, schedules target rows by decision bar, and tests assert feature cutoff equals bar end and execution is at/after cutoff.
- Train/validation only, no final-test metrics: PASS. `make experiments-val` reported `"split": "validation"` and `"final_test_exposure": "NOT_EXPOSED"`; tests assert no `final_test_lock.json` is created and 2025 fixture rows are ignored.
- Included frozen data offline: PASS for Level 1 validation rerun. `make experiments-val` used local configured data and wrote artifacts without external credentials or downloads.
- Net after costs primary, gross/net and benchmark evidence present: PASS. Metrics include primary net/unprefixed fields, `net_*`, `gross_*`, fee/slippage/total-cost fields and broker-costed buy-and-hold benchmark fields.
- Artifacts labeled validation and include provenance: PASS with note. Artifacts and sidecars include split, period, data/config/git hashes, cost assumptions, benchmark, seed, validation warnings and null final-test lock hash. See MEDIUM note on uncommitted-code provenance.
- Required Level 1 artifacts created: PASS. Metrics, equity, weights, orders, fills and `level_1_equity_curve.png` exist.
- Tests prove shared engine/risk path and no final-test exposure: PASS. Focused tests cover shared broker use, validation-only CLI output, no lock creation, 2025-row exclusion and next-open/feature-cutoff behavior.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_uv_sync_frozen.log` |
| `make lint` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_make_lint.log` |
| `make test` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_make_test.log` |
| `make experiments-val` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_make_experiments_val.log` |
| `uv run pytest tests/unit/test_level1_validation.py tests/unit/test_experiments_validation.py` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_focused_level1_pytest.log` |
| Artifact inspection command | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_artifact_inspection.log` |
| Source/test evidence grep | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_source_test_evidence.log` |
| Artifact inventory | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_artifact_file_inventory.log` |
| `git diff --stat` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_git_diff_stat.log` |
| `git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_05_level1_validation/attempt_01/command_logs/qa_git_status_short_branch_untracked.log` |

## Test and artifact evidence

- `uv sync --frozen`: audited 79 packages.
- `make lint`: Ruff format check and Ruff check passed.
- `make test`: 70 tests passed.
- Focused Level 1 pytest: 4 tests passed.
- `make experiments-val`: wrote Level 1 validation artifacts and reported selected SMA fast `30`, slow `100`, net ROI `1.186110921467134`, net Sharpe `1.9535370402802261`, net max drawdown `-0.20027161004621163`, split `validation`, final-test exposure `NOT_EXPOSED`.
- Required artifacts exist:
  - `artifacts/metrics/level_1.csv`
  - `artifacts/equity/level_1.parquet`
  - `artifacts/weights/level_1.parquet`
  - `artifacts/orders/level_1.parquet`
  - `artifacts/fills/level_1.parquet`
  - `artifacts/figures/level_1_equity_curve.png`
- Metrics file has 106 columns including ROI, CAGR, volatility, Sharpe, Sortino, Calmar, max drawdown, drawdown duration, turnover, exposure, trade count, fees, slippage, total cost, benchmark return/CAGR/volatility, tracking error and information ratio, with net and gross prefixed variants.
- Artifact timestamp ranges are validation-only: equity/weights/orders/fills are bounded from `2024-01-01 00:00:00+00:00` through `2024-12-31 00:00:00+00:00`.
- Sidecar metadata records split `validation`, period `2024-01-01` to `2024-12-31`, data hash `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`, config hash `0ac673b154e14619aeb516523913f3ff479e688b67a25c247fee1cef810bd2e1`, git commit `40d748b27a284ce3c8efa7c0b7204a5608b3904b`, benchmark `broker_costed_buy_and_hold`, seed `42`, cost assumptions `10.0` bps fee and `5.0` bps slippage, and `final_test_lock_hash: null`.
- Decision trace exists at `artifacts/monitoring/level_1_decision_trace.json`, with typed SMA signal, aggregate signal, constraints, proposal, approval and resolved target action.
- Artifact inventory contains Level 1 artifacts and prior Stage 2 universe proof artifacts only; no final-test metrics artifacts were observed.

## Findings by severity

- BLOCKER: None.
- HIGH: None.
- MEDIUM: Artifact git provenance currently records base commit `40d748b27a284ce3c8efa7c0b7204a5608b3904b`, while Stage 5 implementation files are still uncommitted/untracked or modified. This is acceptable for a pre-checkpoint QA attempt, but the team-lead gate should commit/checkpoint and rerun artifacts so the recorded git hash identifies the actual Level 1 implementation state.
- LOW: Active-market survivorship/delisting limitation remains inherited from Stage 2 and is disclosed in artifact warnings. It must stay visible in later reports/notebook.
- LOW: `git diff --stat` only reports tracked changes (`configs/default.yaml`, `configs/fast.yaml`, `src/crypto_hedge_fund/cli.py`); the fuller implementation scope is visible only through `git status --untracked-files=all` because new Stage 5 files are untracked at this attempt.

## Unresolved risks and limitations

- Final-test exposure remains `NOT_EXPOSED`; later stages must preserve quarantine until all five levels are implemented and the pretest lock exists.
- Level 1 SMA window selection is validation-based and suitable for this stage, but broader robustness checks belong to later validation/freeze stages.
- Stage 4 accepted daily-boundary convention remains in effect: the representative trace has `decision_time == execution_time == next open` at the UTC daily boundary.
- Levels 2-5, pretest freeze, final test, notebook, report and presentation remain out of scope and incomplete.

## Recommendation

PASS_WITH_NOTES

Level 1 can proceed to team-lead gate rerun. Only the team lead can pass the stage.
