# Role / stage / attempt

Independent portfolio/risk specialist and architecture reviewer / Stage 8 - Level 4 dynamic portfolio rebalancing / attempt 01.

## Scope

Reviewed Level 4 dynamic rebalancing methodology, risk/turnover/cost controls, shared architecture compatibility, validation-only policy selection, artifact disclosure and final-test quarantine. This is not a global stage-completion declaration.

## Sources read

- `AGENTS.md`
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
- `reports/teamlead/REQUIREMENTS_STATUS.md`
- `reports/teamlead/RISK_REGISTER.md`
- `reports/agent_reports/stage_07_level3_validation/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_08_level4_validation/attempt_01/IMPLEMENTATION_REPORT.md`

## Assumptions and decisions

- The teamlead management files still show Stage 8 as `NOT_STARTED`; I treat those as stale process state because the Stage 8 attempt files and artifacts exist.
- Negative validation performance versus the static Level 3 benchmark is acceptable research evidence if disclosed and not tuned away.
- `drift_monthly` and `signal_risk_monthly` having identical validation metrics is not pass-blocking because the code, tests and rebalance log prove separate signal/risk triggers exist; the identical metrics result from controls producing the same submitted schedule.
- The max-weight control is implemented as a target/post-allocation cap, not a continuous mark-to-market holding cap. That is acceptable for this attempt if disclosed before notebook/report/deck claims.
- Final-test state remains `NOT_EXPOSED`; no final-test command or 2025 return artifact was inspected.

## Files inspected or changed

Inspected:

- `src/crypto_hedge_fund/experiments/level_4.py`
- `src/crypto_hedge_fund/portfolio/rebalance.py`
- `src/crypto_hedge_fund/risk/pre_allocation.py`
- `src/crypto_hedge_fund/risk/post_allocation.py`
- `src/crypto_hedge_fund/cli.py`
- `configs/default.yaml`
- `configs/fast.yaml`
- `tests/unit/test_level4_validation.py`
- `tests/unit/test_portfolio_rebalance.py`
- Level 4 artifacts under `artifacts/metrics`, `artifacts/equity`, `artifacts/weights`, `artifacts/orders`, `artifacts/fills`, `artifacts/figures`, and `artifacts/monitoring`

Changed:

- `reports/agent_reports/stage_08_level4_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/arch_*`

## Deliverables

- Independent architecture/risk review with logged evidence.
- Focused pytest run for Level 4 validation and rebalance policy behavior.
- Artifact probes covering selected policy, benchmark comparison, turnover feasibility, trigger rows, caps, costs, sidecar provenance and final-test quarantine.

## Acceptance-criteria mapping

- Dynamic policy implementation: PASS. `calendar_monthly`, `drift_monthly`, and `signal_risk_monthly` are configured and implemented via `DynamicRebalancePolicy`.
- Trigger coverage: PASS. Code/tests cover calendar, drift, signal and risk triggers; artifact log shows calendar, drift, signal and risk trigger rows.
- Turnover/cost/min-trade controls: PASS. Policy gates skip minimum trades and turnover breaches; selection excludes dynamic candidates above the annual turnover constraint.
- Max weight/liquidity/capacity controls: PASS_WITH_NOTES. Submitted target weights are capped and liquidity-derived capacity caps feed pre-risk constraints, but actual drifted holdings can exceed the 30% target cap between accepted trades.
- Shared architecture: PASS. Level 4 reuses Level 3 universe/allocator foundations, `PreAllocationRiskPolicy`, `PostAllocationRiskPolicy`, `resolve_risk_approval_targets`, `SimulatedBroker`, metrics and artifact writers.
- Validation-only selection: PASS. Sidecars and traces are `validation`, `2024-01-01` to `2024-12-31`, with `final_test_lock_hash: null`.
- Static comparison honesty: PASS. The static benchmark is reported and not eligible for dynamic policy selection; dynamic underperformance is visible in metrics and trace summary.
- Final-test quarantine: PASS. `artifacts/final_test_lock.json` is absent; trace and final-vintage plan state `NOT_EXPOSED` and no 2025 performance is computed.
- Level 5 compatibility: PASS_WITH_NOTES. The policy abstraction, rebalance log and shared risk/broker path are compatible with Level 5, but Level 5 should tighten/explicitly define continuous cap handling if max holding caps are hard limits.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `git diff --stat` | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/arch_git_diff_stat.log` |
| `git status --short --branch --untracked-files=all` | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/arch_git_status.log` |
| `sed` inspections of Level 4 source/rebalance/config/tests/risk/CLI | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/arch_level4_py_*.log`, `arch_rebalance_py.log`, `arch_test_*.log`, `arch_config_*.log`, `arch_pre_allocation_py.log`, `arch_post_allocation_py.log`, `arch_cli_experiments_val.log` |
| `rg` inspections for Level 4/risk/capacity surfaces | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/arch_rg_level4_surfaces.log`, `arch_rg_risk_capacity_tests.log` |
| `uv run pytest tests/unit/test_level4_validation.py tests/unit/test_portfolio_rebalance.py` | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/arch_pytest_level4_rebalance.log` |
| Level 4 artifact probe | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/arch_artifact_probe.log` |
| Level 4 weight-cap probe | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/arch_weight_cap_probe.log` |
| Level 4 selected target/weights/orders probe | 0 | `reports/agent_reports/stage_08_level4_validation/attempt_01/command_logs/arch_selected_target_cap_probe.log`, `arch_weights_orders_probe.log` |

## Test and artifact evidence

- Focused pytest: 9 passed.
- Metrics policies: `static_level3_benchmark`, `calendar_monthly`, `drift_monthly`, `signal_risk_monthly`.
- Selected Level 4 policy: `calendar_monthly`, not the static benchmark.
- Selected metrics: net total return `0.033511`, net Sharpe `0.475263`, max drawdown `-0.065519`, annual turnover `1.820453`.
- Static benchmark metrics: net total return `1.260970`, net Sharpe `1.696379`, max drawdown `-0.347085`, annual turnover `0.995000`.
- Turnover feasibility: `calendar_monthly` is feasible under the `6.0` annual turnover constraint; `drift_monthly` and `signal_risk_monthly` both have turnover `9.316548` and are infeasible.
- Drift/signal metrics: `drift_monthly` and `signal_risk_monthly` are identical on net return, Sharpe, drawdown, turnover and submitted count.
- Rebalance log: 1099 rows; submitted counts are static `1`, calendar `50`, drift `70`, signal/risk `70`.
- Trigger rows: `calendar_monthly` 602, `weight_drift` 628, `signal_change` 3, `risk_trigger` 18; risk-trigger active rows 54.
- Controls: `turnover_cap_exceeded` appears in 886 trigger rows; `minimum_trade_not_met` appears in 32 rows.
- Submitted selected candidate and approved weights have max weight `0.30` and zero over-30% submitted rows.
- Actual weight timeline can drift above target caps: selected `calendar_monthly` max actual weight `0.345222`; drift/signal candidates max actual weight `0.666810`.
- Artifact sidecars for metrics, rebalance log, weights, orders, fills and traces are `split=validation`, period `2024-01-01` to `2024-12-31`, `final_test_lock_hash=null`.
- `artifacts/final_test_lock.json` does not exist. Decision trace and final-vintage plan report `NOT_EXPOSED`.

## Findings by severity

- BLOCKER: None.
- HIGH: None.
- MEDIUM: Dynamic policies underperform the static Level 3 benchmark in validation, with selected `calendar_monthly` net total return `3.35%` versus static `126.10%`. This is acceptable only if downstream notebook/report/deck preserve it as negative research evidence and do not imply Level 4 improves returns.
- MEDIUM: Max-weight enforcement is a target/post-allocation cap, not a continuous holding cap. Submitted selected targets are capped at 30%, but drifted actual weights reached `34.52%` for the selected policy and `66.68%` for rejected dynamic candidates. This should be disclosed and tightened before Level 5 if max weight is intended as a hard live holding limit.
- MEDIUM: `drift_monthly` and `signal_risk_monthly` produced identical validation metrics and submitted counts. This is not a methodology blocker because separate trigger rows exist, but the final narrative should explain that signal/risk triggers did not add incremental executed rebalances after turnover/risk controls.
- LOW: Capacity/liquidity is based on trailing daily dollar-volume participation, not order-book depth or intraday liquidity.
- LOW: Active Binance/CCXT survivorship and delisting bias remains inherited from prior stages.
- LOW: Stage management docs are stale for Stage 8 status and should be updated by the teamlead if this attempt is accepted.

## Unresolved risks and limitations

- Final-test remains unrun and must stay quarantined until Levels 1-5 are implemented and pretest-locked.
- The dynamic selected policy is feasible by turnover constraint but economically worse than static on 2024 validation.
- Actual holdings can drift beyond target caps between rebalances; the current implementation logs this but does not force an immediate cap-reduction trade when turnover/risk controls veto the candidate.
- `make experiments-val` still appears to regenerate earlier-level artifacts as a side effect, per worker report and existing project risk register.
- Daily OHLCV, ADV capacity proxies and simplified fills remain research approximations.

## Recommendation

PASS_WITH_NOTES

Stage 8 attempt 01 satisfies Level 4 architecture and validation-selection requirements without final-test exposure. The worker notes are acceptable limitations rather than pass-blocking issues, provided downstream reporting explicitly states that dynamic rebalancing underperformed the static benchmark and that current max-weight controls apply to submitted targets, not continuously drifted holdings.
