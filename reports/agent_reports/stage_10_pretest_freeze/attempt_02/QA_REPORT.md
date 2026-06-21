# Role / stage / attempt

Independent QA reviewer / Stage 10 - Pretest Freeze / attempt 02.

## Scope

Independently verified the attempt 02 remediation for the Stage 10 pretest freeze. Focus was limited to closing the attempt 01 proof-collision and final-test-lock enforcement findings, rerunning required Stage 10 gates, validating hash coherence, and checking final-test quarantine without inspecting final-test performance results.

I did not run `make final-test`, did not commit or tag, and did not inspect final-test returns, metrics, rankings, charts, orders, fills, or model results.

## Sources read

- `AGENTS.md`
- `docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`
- `docs/06_ACCEPTANCE_CRITERIA.md`
- `docs/04_EXPERIMENT_PROTOCOL.md`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_01/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_02/IMPLEMENTATION_REPORT.md`
- `configs/validation_selected.yaml`
- `artifacts/final_test_lock.json`
- `src/crypto_hedge_fund/pretest_lock.py`
- `src/crypto_hedge_fund/cli.py`
- `src/crypto_hedge_fund/data/validation.py`
- `tests/unit/test_pretest_freeze.py`
- `tests/unit/test_data_layer.py`

## Assumptions and decisions

- Treated Stage 10 as a freeze/quarantine review, not a final-test execution review.
- Treated structural 2025 data coverage proof from `make validate-data` as allowed because it does not expose strategy performance.
- Used direct package probes and temp-copy mutation probes instead of `make final-test`.
- Treated command-generated validation artifact and lock rewrites as expected side effects of the required QA commands; I made no manual source/config/data/artifact edits.
- Disregarded two preliminary proof-probe logging mistakes and relied on corrected `v3` plus post-lock probes, both passing.

## Files inspected or changed

Inspected the mandatory sources listed above, current Git status, proof artifacts, lock metadata, command logs, and filename-only final-artifact scan output.

Changed:

- `reports/agent_reports/stage_10_pretest_freeze/attempt_02/QA_REPORT.md`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_02/command_logs/qa_*`

Command side effects regenerated validation artifacts, `configs/validation_selected.yaml`, `artifacts/final_test_lock.json`, and `artifacts/final_test_lock.json.metadata.json` as required by the QA command list.

## Deliverables

- QA report: `reports/agent_reports/stage_10_pretest_freeze/attempt_02/QA_REPORT.md`
- QA logs/status files: `reports/agent_reports/stage_10_pretest_freeze/attempt_02/command_logs/qa_*`

## Acceptance-criteria mapping

- `make validate-data` writes `artifacts/monitoring/level_5_data_pair_count_proof.json`: PASS. Log reports proof path exactly and `scored_count=104`.
- `make validate-data` does not overwrite `artifacts/monitoring/level_5_pair_count_proof.json`: PASS. Post-lock SHA stayed `ccdf3bf817c50e5001c2af1baeb1dfe9c0b44208800c023c66eac54bc21cc925`.
- `level_5_pair_count_proof.json` remains Level 5 validation proof: PASS. Probe shows `split=validation`, `final_test_exposure=NOT_EXPOSED`, `scored_count=100`, `selected_count=25`.
- `artifacts/final_test_lock.json` is `LOCKED` and coherent: PASS. Lock validator reports `LOCKED`, sidecar hash match, 47 validation artifact hashes, and data proof hash match.
- Mutated selected config refused before computation: PASS. Temp-copy probe raises `validation-selected config hash mismatch`.
- Mutated locked validation artifact refused before computation: PASS. Temp-copy probe raises `Validation artifact hash mismatch` for `level_5_pair_count_proof.json`.
- Required Stage 10 commands pass: PASS. See command table.
- No final-test performance artifacts/results produced or inspected: PASS_WITH_NOTES. Filename scan found `unexpected_final_or_test_named_files_count=0`; I did not open final-test result content. The known Level 3/4 final vintage plan files remain planned-not-executed artifacts, not result outputs.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `uv sync --frozen` | 0 | `command_logs/qa_uv_sync_frozen.log`, `command_logs/qa_uv_sync_frozen.status` |
| `make validate-data` | 0 | `command_logs/qa_make_validate_data.log`, `command_logs/qa_make_validate_data.status` |
| Initial proof-collision probe before `make validate-data` | 0 | `command_logs/qa_proof_collision_probe_before_v3.log`, `command_logs/qa_proof_collision_probe_before_v3.status` |
| Proof-collision `make validate-data` rerun | 0 | `command_logs/qa_proof_collision_make_validate_data.log`, `command_logs/qa_proof_collision_make_validate_data.status` |
| Proof-collision comparison | 0 | `command_logs/qa_proof_collision_probe.log`, `command_logs/qa_proof_collision_probe.status` |
| `make lint` | 0 | `command_logs/qa_make_lint.log`, `command_logs/qa_make_lint.status` |
| `make test` | 0 | `command_logs/qa_make_test.log`, `command_logs/qa_make_test.status` |
| `make experiments-val` | 0 | `command_logs/qa_make_experiments_val.log`, `command_logs/qa_make_experiments_val.status` |
| `make pretest-freeze` | 0 | `command_logs/qa_make_pretest_freeze.log`, `command_logs/qa_make_pretest_freeze.status` |
| `uv run pytest -vv tests/unit/test_pretest_freeze.py` | 0 | `command_logs/qa_focused_pretest_final_lock_pytest.log`, `command_logs/qa_focused_pretest_final_lock_pytest.status` |
| Direct lock validation probe | 0 | `command_logs/qa_lock_validation_probe.log`, `command_logs/qa_lock_validation_probe.status` |
| Temp-copy lock mutation probe | 0 | `command_logs/qa_lock_mutation_probe.log`, `command_logs/qa_lock_mutation_probe.status` |
| Post-lock proof-collision `make validate-data` rerun | 0 | `command_logs/qa_postlock_proof_collision_make_validate_data.log`, `command_logs/qa_postlock_proof_collision_make_validate_data.status` |
| Post-lock proof-collision comparison and lock validation | 0 | `command_logs/qa_postlock_proof_collision_probe.log`, `command_logs/qa_postlock_proof_collision_probe.status` |
| Artifact evidence probe | 0 | `command_logs/qa_artifact_evidence_probe.log`, `command_logs/qa_artifact_evidence_probe.status` |
| Final-artifact filename scan | 0 | `command_logs/qa_final_artifact_name_scan.log`, `command_logs/qa_final_artifact_name_scan.status` |

Preliminary logging mistakes:

- `qa_proof_collision_probe_before.status` exited `1` due to using system Python without the package import path.
- `qa_proof_collision_probe_before_v2.status` exited `0` but had a shell quoting error that made the SHA capture invalid.
- Corrected evidence is `qa_proof_collision_probe_before_v3.*` and the post-lock probe files above.

## Test and artifact evidence

- `make validate-data`: 158,511 rows, 163 symbols, data SHA `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`, instrument SHA `df7777139dd4106032280339818ba18179882c8e19141f374d87cb8e7bddf18b`, proof path `artifacts/monitoring/level_5_data_pair_count_proof.json`, `eligible_count=104`, `scored_count=104`.
- `make lint`: Ruff format check and Ruff lint passed.
- `make test`: 103 tests passed in 30.57s.
- Focused lock tests: 5 tests passed in 0.33s.
- `make experiments-val`: validation split, Level 5 `scored_count=100`, `selected_count=25`.
- `make pretest-freeze`: wrote `artifacts/final_test_lock.json`, lock SHA `2b8ea386cb71ba593c034d9751fe02e85f2013356690e5e6af20558b8ec1577f`, selected config SHA `5bdfe153511175a1004fc68413e176c7bae1bf1141fae72504616796554eab55`, exposure state `LOCKED`.
- Direct lock validation: sidecar hash matches, `validation_artifact_count=47`, data proof SHA `801554301f071a4846db2d1d1717e078c85fe8ce1c6c8574b53df6f639ebf28f`.
- Level 5 validation proof: SHA `ccdf3bf817c50e5001c2af1baeb1dfe9c0b44208800c023c66eac54bc21cc925`, `split=validation`, `final_test_exposure=NOT_EXPOSED`, `scored_count=100`, `selected_count=25`.
- Data-validation proof: SHA `801554301f071a4846db2d1d1717e078c85fe8ce1c6c8574b53df6f639ebf28f`, `proof_owner=data_validation`, `generated_by=make validate-data`, `scored_count=104`.
- Post-lock proof-collision probe: Level 5 validation proof unchanged, data proof unchanged, data proof matches lock, lock validation after `make validate-data` passed.
- Level 1-5 metric provenance fields remain `provenance_split=validation` and empty `provenance_final_test_lock_hash`.
- Final-artifact filename scan: `unexpected_final_or_test_named_files_count=0`.

## Findings by severity

- BLOCKER
  - None found for the attempt 02 QA scope.

- HIGH
  - None found for the attempt 02 QA scope.

- MEDIUM
  - The lock still records a dirty Stage 10 worktree at the Stage 9 base commit. This is transparent in the lock and not a proof-collision failure, but before Stage 11 the team lead should either accept this exact dirty-state evidence or regenerate the lock after the Stage 10 checkpoint commit.

- LOW
  - The pretest dirty allowlist remains broad for `artifacts/` and `reports/`. The current lock validates exact artifact hashes, which mitigates the Stage 10 freeze risk, but a narrower allowlist would make future reviews cleaner.
  - QA probe logs include two preliminary proof-probe mistakes before the corrected probes. They did not affect source/config/data/artifact state.

## Unresolved risks and limitations

- This report does not declare Stage 10 globally passed; team lead acceptance is still required.
- `make final-test` was not run by instruction. The final-test runner itself remains Stage 11 work; this review verified the pre-computation lock validator directly.
- Existing methodology limitations remain: active Binance/CCXT survivorship and delisting bias, daily-bar liquidity proxies instead of order-book depth, short Level 5 validation proof window, and BTC-normalized Level 5 benchmark disclosure risk.
- I did not perform a clean-clone rehearsal, full notebook run, final report generation, or presentation rendering in this Stage 10 QA pass.

## Recommendation

PASS_WITH_NOTES

Attempt 02 closes the attempt 01 proof-collision and declarative-only lock-enforcement findings for QA scope. Do not treat this as a global Stage 10 pass until the team lead reviews and accepts the dirty checkpoint state.
