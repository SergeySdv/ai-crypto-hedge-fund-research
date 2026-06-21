# Role / stage / attempt

Implementation worker / Stage 11 Frozen Final Test / attempt 01.

## Scope

Implemented the frozen final-test runner behind `crypto-hedge-fund final-test` and `make final-test`. The runner validates the accepted Stage 10 lock before computation, derives a generated final-test config from `configs/validation_selected.yaml`, runs Levels 1-5 once with `split=final_test`, and writes lock-specific outputs under `artifacts/final_test/dab407601cba/`.

## Sources read

- `AGENTS.md`
- `docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `docs/09_CONFIG_AND_INTERFACES.md`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_02/TEAMLEAD_DECISION.md`
- `artifacts/final_test_lock.json`
- `configs/validation_selected.yaml`
- `src/crypto_hedge_fund/pretest_lock.py`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/experiments/level_1.py`
- `src/crypto_hedge_fund/experiments/level_2.py`
- `src/crypto_hedge_fund/experiments/level_3.py`
- `src/crypto_hedge_fund/experiments/level_4.py`
- `src/crypto_hedge_fund/experiments/level_5.py`
- Existing tests for Levels 1-5, pretest lock, final-test behavior, and execution kernel.

## Assumptions and decisions

- The accepted lock hash is `dab407601cbaf8198361e5e3d074260546ed4bbab4c4be2555248b246631308b`; the final-test runner refuses any other hash by default.
- Final artifacts are written to a lock-specific subtree, `artifacts/final_test/dab407601cba/`, so accepted validation artifacts remain intact for lock validation.
- `artifacts/final_test_lock.json` and `configs/validation_selected.yaml` were not modified.
- Levels 3 and 4 fail closed if the mechanically selected final small universe differs from locked final symbols.
- During the first final-test run, the shared broker failed on zero-weight Level 5 placeholder columns with missing prices. This was fixed as an implementation defect: the broker still requires prices for held symbols and nonzero target trades, but no longer requires prices for zero-weight placeholder columns.
- No model, threshold, asset list, top-K, risk limit, cost assumption, rebalance policy, benchmark, or selected method was changed based on final-test results.

## Files inspected or changed

Changed:

- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/execution/broker.py`
- `src/crypto_hedge_fund/experiments/final_test.py`
- `src/crypto_hedge_fund/experiments/level_1.py`
- `src/crypto_hedge_fund/experiments/level_2.py`
- `src/crypto_hedge_fund/experiments/level_3.py`
- `src/crypto_hedge_fund/experiments/level_4.py`
- `src/crypto_hedge_fund/experiments/level_5.py`
- `tests/unit/test_execution_kernel.py`
- `tests/unit/test_final_test.py`
- `reports/agent_reports/stage_11_final_test/attempt_01/**`

Generated final-test artifacts:

- `artifacts/final_test/dab407601cba/final_test_suite_summary.json`
- `artifacts/final_test/dab407601cba/final_test_exposure_evidence.json`
- `artifacts/final_test/dab407601cba/frozen_final_config.yaml`
- `artifacts/final_test/dab407601cba/{metrics,equity,weights,orders,fills,figures,monitoring}/...`

## Deliverables

- `make final-test` and `crypto-hedge-fund final-test` now validate the accepted lock and run the frozen final suite.
- Final-test artifacts for Levels 1-5 are generated under `artifacts/final_test/dab407601cba/`.
- All final-test metric probes show `provenance_split=final_test` and the accepted lock hash.
- `final_test_exposure_evidence.json` records generated evidence state `EXPOSED` while leaving the lock file unchanged.
- Level 5 final evidence records 120 eligible pairs, 120 scored pairs, 25 selected pairs, runtime, and peak RSS.
- Focused tests cover fail-closed lock validation before computation and final-test provenance output.
- Execution-kernel regression test covers zero-weight placeholder columns with missing prices.

## Acceptance-criteria mapping

- Lock validates before computation: PASS, direct lock probes exit 0 before and after final-test.
- Mismatched lock refuses before computation: PASS, `tests/unit/test_final_test.py`.
- Same locked methodology: PASS_WITH_NOTES, generated final config is derived from accepted lock/selected config; no retuning after final exposure.
- All five levels run once as final suite: PASS after broker defect fix, `make_final_test_after_broker_fix.log`.
- Outputs labeled `final_test` with lock/data/config/git/seed provenance: PASS, `artifact_provenance_probe.log`.
- Level 5 100+ pair proof: PASS, 120 eligible/scored and 25 selected.
- Final-test exposure becomes `EXPOSED` in generated evidence: PASS.
- No live downloads, exchange credentials, private APIs, or LLM keys: PASS.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `command_logs/uv_sync_frozen.log` |
| `make lint` | 2 | `command_logs/make_lint.log` formatting-only failure before Ruff format |
| `make lint` rerun | 0 | `command_logs/make_lint_rerun.log` |
| `make test` | 0 | `command_logs/make_test.log` |
| `uv run pytest -q tests/unit/test_final_test.py` | 0 | `command_logs/focused_final_test_pytest.log` |
| Direct lock validation probe | 0 | `command_logs/direct_lock_validation_probe.log` |
| `make final-test` initial | 2 | `command_logs/make_final_test.log` broker zero-weight placeholder price defect |
| `make lint` after broker fix | 2 | `command_logs/make_lint_after_broker_fix.log` formatting-only failure |
| `make lint` after broker fix rerun | 0 | `command_logs/make_lint_after_broker_fix_rerun.log` |
| `make test` after broker fix | 0 | `command_logs/make_test_after_broker_fix.log` |
| `uv run pytest -q tests/unit/test_final_test.py tests/unit/test_execution_kernel.py` | 0 | `command_logs/focused_final_test_and_broker_pytest_after_fix.log` |
| `make final-test` after broker fix | 0 | `command_logs/make_final_test_after_broker_fix.log` |
| Artifact/provenance probe | 0 | `command_logs/artifact_provenance_probe.log` |
| Post-final lock validation probe | 0 | `command_logs/post_final_lock_validation_probe.log` |
| `git status --short --branch --untracked-files=all` | 0 | `command_logs/git_status_short_branch_untracked.log` |
| Final `git status --short --branch --untracked-files=all` | 0 | `command_logs/git_status_short_branch_untracked_final.log` |

## Test and artifact evidence

- Accepted lock hash: `dab407601cbaf8198361e5e3d074260546ed4bbab4c4be2555248b246631308b`.
- Direct lock validation: `final_test_exposure_state=LOCKED`, 47 validation artifacts validated.
- Final suite output directory: `artifacts/final_test/dab407601cba/`.
- Suite summary: `artifacts/final_test/dab407601cba/final_test_suite_summary.json`.
- Exposure evidence: `artifacts/final_test/dab407601cba/final_test_exposure_evidence.json`.
- All level metric files report `split_labels=["final_test"]`.
- All level metric files report the accepted final-test lock hash.
- Level 5 proof: `eligible_count=120`, `scored_count=120`, `selected_count=25`, `runtime_seconds=75.24468995799543`, `peak_rss_mb=727.296875`.

## Findings by severity

- BLOCKER: None remaining.
- HIGH: Initial `make final-test` failed on a shared broker implementation defect. The broker required prices for zero-weight placeholder symbols in the schedule. Fixed by only pricing held symbols and nonzero target symbols; missing prices for actual trades/holdings still fail closed.
- MEDIUM: `artifacts/final_test/**` is currently ignored by `.gitignore`. Final artifacts exist on disk, but packaging for commit/review will need either ignore-rule adjustment or explicit force-add by the owner/team lead.
- LOW: Initial lint failures were formatting-only after edits and were resolved with Ruff format.

## Unresolved risks and limitations

- The broker fix touched `src/crypto_hedge_fund/execution/broker.py`, which was outside the narrow Stage 11 write-scope list, because the implementation defect blocked final-test execution without changing methodology.
- Final artifacts are generated but ignored by current `.gitignore`.
- Existing methodology limitations remain: active-market survivorship/delisting bias, daily-bar liquidity proxies, no order-book depth, and BTC-normalized Level 5 benchmark.
- This report does not claim public submission completion; the human owner/team lead still needs to decide stage acceptance and publication packaging.

## Recommendation

PASS_WITH_NOTES
