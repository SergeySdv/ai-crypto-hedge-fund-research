# Team Lead Decision / Stage 10 Pretest Freeze / Attempt 01

## Reports considered

- `reports/agent_reports/stage_10_pretest_freeze/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_01/ARCHITECTURE_REVIEW.md`
- Prior checkpoint decision: `reports/agent_reports/stage_09_level5_validation/attempt_03/TEAMLEAD_DECISION.md`

## Targeted diffs inspected

- `git status --short --branch --untracked-files=all`
- `git diff --stat`
- `artifacts/final_test_lock.json`
- `configs/validation_selected.yaml`
- `src/crypto_hedge_fund/pretest_lock.py`
- `src/crypto_hedge_fund/cli.py`
- `tests/unit/test_pretest_freeze.py`
- Data and Level 5 proof writers for `artifacts/monitoring/level_5_pair_count_proof.json`

## Commands independently rerun or accepted as reviewer evidence

| Command | Status | Evidence |
|---|---:|---|
| `uv sync --frozen` | PASS | Worker and QA logs. |
| `make validate-data` | PASS | Worker and QA logs. |
| `make lint` | PASS | Worker and QA logs. |
| `make test` | PASS | Worker and QA logs; QA reported 100 tests passed. |
| `make experiments-val` | PASS | Worker and QA logs; Level 5 scored 100 and selected 25. |
| `make pretest-freeze` | PASS | Worker and QA logs; lock state `LOCKED`. |
| Lock/hash/quarantine probes | PASS/REWORK | QA found current hashes coherent after its command order; architecture found the proof path can be overwritten by `make validate-data`. |

The lead did not run final Stage 10 gates because architecture review found a checkpoint-safety blocker/high issue.

## Acceptance criteria passed

- `configs/validation_selected.yaml` exists and records validation-selected methodology.
- `artifacts/final_test_lock.json` exists and records `final_test_exposure_state: LOCKED`.
- Lock records `final_test_results_inspected: false`.
- QA verified lock sidecar hash, selected-config hash and current validation artifact hashes after its command sequence.
- No final-test command was run by worker, reviewers or lead.
- Final-test state is not `EXPOSED`.

## Acceptance criteria failed

- Data validation and Level 5 validation both write `artifacts/monitoring/level_5_pair_count_proof.json`. A later `make validate-data` can overwrite the Level 5 validation proof that the lock relies on. This makes the freeze checkpoint unsafe even if the current file matches after the latest command order.
- `make final-test` hash-mismatch enforcement is only declarative. It fails closed because final-test is not implemented, but it does not yet validate lock/config/data/artifact hashes before any future final-test computation.

## Unresolved risks

- The lock currently records the Stage 9 base commit plus a dirty Stage 10 diff. This is transparent but must be handled before Stage 11; either regenerate the lock after the Stage 10 checkpoint commit or explicitly validate the recorded dirty diff/content.
- Stage 10 regenerated validation artifacts for Levels 1-5; reviewers must verify the accepted checkpoint contains the exact artifacts hashed by the final lock.
- Existing known limitations remain: active-market survivorship bias, short Level 5 validation window, BTC-normalized Level 5 benchmark and cash-heavy risk veto behavior.

## Decision

REWORK

Stage 10 attempt 01 cannot pass. The final-test quarantine was preserved, but the freeze is not robust enough for a checkpoint because proof artifacts can be overwritten after lock creation and final-test hash validation is not implemented.

## Remediation packet for attempt 02

Assign a fresh implementation fixer with this constrained mission:

- Separate the Stage 2/data-validation universe proof path from the Stage 9/10 Level 5 experiment proof path so `make validate-data` cannot overwrite the locked Level 5 validation proof.
- Preserve required Stage 2 evidence by writing the data-validation proof to a clearly named path such as `artifacts/monitoring/level_5_data_pair_count_proof.json`, while keeping `artifacts/monitoring/universe_eligibility_full.csv` and documenting any compatibility behavior.
- Ensure `artifacts/monitoring/level_5_pair_count_proof.json` is owned by the Level 5 validation experiment and contains validation split, `final_test_exposure: NOT_EXPOSED`, 100 scored pairs and selected count 25 before `make pretest-freeze`.
- Update `pretest_lock.py`, tests and artifact lists so the final lock hashes the Level 5 validation proof and, if useful, separately records the data-validation proof hash.
- Implement a lock validation function used by `make final-test` before any future final-test computation. It must verify lock sidecar hash, selected config hash, required data/config/artifact hashes and reject mismatches. It may still fail closed after validation because the actual final-test runner belongs to Stage 11.
- Add tests that mutate at least selected config or a hashed validation artifact and prove final-test/pre-final validator refuses before computation.
- Rerun/log `uv sync --frozen`, `make validate-data`, `make lint`, `make test`, `make experiments-val`, `make pretest-freeze`, a lock hash probe, and a post-`make validate-data` proof collision probe.
- Do not run final-test results, do not inspect final-test metrics, and keep final-test exposure `LOCKED` only after the corrected lock is written.

After attempt 02, assign fresh independent QA and architecture/quarantine reviewers.
