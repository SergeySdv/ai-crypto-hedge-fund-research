# Role / stage / attempt

Independent QA reviewer / Stage 11 Frozen Final Test / attempt 01.

## Scope

Reviewed the Stage 11 final-test implementation and existing final-test artifacts after final-test exposure. I did not rerun `make final-test` and did not edit source, tests, configs, lock files, validation artifacts, or final-test artifacts.

## Sources read

- `AGENTS.md`
- Required governance docs in AGENTS order, including `docs/06_ACCEPTANCE_CRITERIA.md` and `docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_02/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_11_final_test/attempt_01/IMPLEMENTATION_REPORT.md`
- Worker command logs, especially `make_final_test.log` and `make_final_test_after_broker_fix.log`
- `artifacts/final_test/dab407601cba/final_test_suite_summary.json`
- `artifacts/final_test/dab407601cba/final_test_exposure_evidence.json`
- `artifacts/final_test/dab407601cba/monitoring/level_5_pair_count_proof.json`
- `src/crypto_hedge_fund/experiments/final_test.py`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/execution/broker.py`
- `tests/unit/test_final_test.py`
- `tests/unit/test_execution_kernel.py`
- `.gitignore`

## Assumptions and decisions

- Accepted pretest lock hash is `dab407601cbaf8198361e5e3d074260546ed4bbab4c4be2555248b246631308b`.
- Final-test results are exposed, so I treated all source/config/methodology changes as frozen except documented correctness review.
- I treated the generated final-test evidence files as the exposure record. The lock metadata still validates as `LOCKED`, which is consistent with the worker design of not mutating the accepted Stage 10 lock.
- I classified ignored final artifacts as a delivery/checkpoint visibility risk, not as a computation/provenance failure.

## Files inspected or changed

Inspected: the sources listed above, worker logs/status files, final artifacts, `.gitignore`, and diffs for the Stage 11 runner/broker/level plumbing.

Changed by QA only:

- `reports/agent_reports/stage_11_final_test/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_11_final_test/attempt_01/command_logs/qa_*`

## Deliverables

- Independent QA report at this path.
- QA command logs and status files under `reports/agent_reports/stage_11_final_test/attempt_01/command_logs/qa_*`.

## Acceptance-criteria mapping

- No final-test rerun: PASS. I did not run `make final-test` or `crypto-hedge-fund final-test`.
- Worker final-test logs inspected: PASS. Initial run exited 2 on the broker placeholder missing-price defect; after-fix run exited 0.
- Non-final verification commands: PASS. `uv sync --frozen`, `make lint`, `make test`, and focused final-test/broker pytest passed.
- Direct lock validation: PASS. Accepted hash validated, 47 validation artifacts checked, lock metadata state reported `LOCKED`.
- Final metric provenance: PASS. Every `artifacts/final_test/dab407601cba/metrics/level_<n>.csv` has `provenance_split=final_test` and the accepted lock hash.
- Level 5 pair proof: PASS. Proof has `split=final_test`, `final_test_exposure=EXPOSED`, nested provenance lock hash, `eligible_count=120`, `scored_count=120`, and `selected_count=25`.
- Broker post-exposure fix: PASS_WITH_NOTES. The diff removes zero-weight placeholder symbols before price lookup while preserving missing-price failure for held symbols and nonzero target trades. Focused regression tests pass.
- Final artifact Git visibility: PASS_WITH_RISK. Artifacts exist and pass provenance checks on disk, but `artifacts/final_test/dab407601cba/**` is Git-ignored and currently not tracked.
- Failed-run contamination risk: PASS_WITH_NOTES. The failed run ended before suite summary/exposure evidence and before Level 5 artifacts; current artifact timestamps are after the failed log and match the successful rerun. No extra stale final-test files were found beyond the current lock-specific output tree.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `command_logs/qa_uv_sync_frozen.log` |
| `make lint` | 0 | `command_logs/qa_make_lint.log` |
| `make test` | 0 | `command_logs/qa_make_test.log` |
| `uv run pytest -q tests/unit/test_final_test.py tests/unit/test_execution_kernel.py` | 0 | `command_logs/qa_focused_final_test_and_broker_pytest.log` |
| Direct lock validation probe | 0 | `command_logs/qa_direct_lock_validation_probe.log` |
| Initial artifact provenance probe | 1 | `command_logs/qa_artifact_provenance_probe.log`; probe expected a top-level Level 5 proof lock key |
| Corrected artifact provenance probe | 0 | `command_logs/qa_artifact_provenance_probe_corrected.log` |
| Git artifact visibility probe | 0 | `command_logs/qa_git_artifact_visibility_probe.log` |
| Final artifact inventory/timestamp probe | 0 | `command_logs/qa_final_artifact_inventory_timestamps.log` |
| Worker final-test log audit | 0 | `command_logs/qa_worker_final_test_log_audit.log` |

## Test and artifact evidence

- `uv sync --frozen`: audited 79 packages.
- `make lint`: Ruff format check reported 77 files already formatted; Ruff check passed.
- `make test`: 106 tests passed in 30.63s.
- Focused pytest: 9 tests passed, including final-test runner tests and broker execution-kernel tests.
- Direct lock probe: `final_test_lock_sha256=dab407601cbaf8198361e5e3d074260546ed4bbab4c4be2555248b246631308b`, `validation_artifact_count=47`, `final_test_exposure_state=LOCKED`.
- Final suite summary/evidence: `split=final_test`, `final_test_exposure=EXPOSED`, output directory `artifacts/final_test/dab407601cba/`.
- Level 5 proof: 120 eligible, 120 scored, 25 selected; proof provenance contains the accepted final-test lock hash.
- Worker failed-run log: initial `make final-test` exited 2 with `MissingPriceError` for zero-weight placeholder/new-listing symbols.
- Worker successful-run log: after broker fix, `make final-test` exited 0 and printed the final suite output paths.
- Artifact timestamps: current Level 1-5 artifacts are dated after the initial failed log and align with the successful after-fix run.

## Findings by severity

- BLOCKER
  - None.

- HIGH
  - None.

- MEDIUM
  - Final-test artifacts are Git-ignored and untracked. `git status --ignored` reports `!! artifacts/final_test/dab407601cba/**`, and `git ls-files artifacts/final_test/dab407601cba` returns no tracked files. The artifacts are valid on disk, but a normal checkpoint/public submission will omit them unless the team lead force-adds them or adjusts ignore rules before checkpointing.

- LOW
  - The first `make final-test` produced partial final-test artifacts before failing in Level 5. Current artifacts were regenerated by the successful after-fix run and pass provenance checks, so I do not see a cleanup blocker.
  - The broker fix happened after final-test exposure and must remain disclosed. Based on the diff and tests, it is a correctness fix for zero-weight placeholder symbols, not a retuning or methodology change.
  - My first artifact provenance probe failed because it expected the Level 5 proof lock hash at the top level; the proof stores it under `provenance.final_test_lock_hash`. The corrected probe passed.

## Unresolved risks and limitations

- Final artifacts must be made visible to Git before a Stage 11 checkpoint or public submission. This is a delivery risk, not an artifact-content failure.
- Existing methodology limitations remain from prior stages: active-market survivorship/delisting bias, daily-bar liquidity proxies without order-book depth, and BTC-normalized Level 5 benchmark.
- I did not run notebook, report, presentation, clean-clone, or final-test commands because they are outside this QA scope or forbidden for this exposed final-test review.

## Recommendation

PASS_WITH_NOTES

No computation/provenance blocker was found, and the post-exposure broker fix does not leave a QA blocker. Before checkpoint/public submission, the team lead must handle `artifacts/final_test/dab407601cba/**` Git visibility so required final-test artifacts are actually delivered.
