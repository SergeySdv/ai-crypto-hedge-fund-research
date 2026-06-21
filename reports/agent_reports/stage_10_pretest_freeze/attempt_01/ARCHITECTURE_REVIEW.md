# Role / stage / attempt

Independent architecture/quarantine reviewer / Stage 10 - Pretest freeze / attempt 01.

## Scope

Audited whether the Stage 10 lock freezes methodology and preserves final-test quarantine before Stage 11. Focus areas were requirements coverage, final-test lock semantics, selected methodology completeness, dirty-worktree policy, current validation artifact coherence, and whether the regenerated validation artifacts should be accepted into the checkpoint.

I did not run `make final-test`, inspect final-test strategy performance, commit, tag, or edit implementation/config/test/trading-artifact files.

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
- `reports/agent_reports/stage_09_level5_validation/attempt_03/TEAMLEAD_DECISION.md`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_01/IMPLEMENTATION_REPORT.md`
- `configs/validation_selected.yaml`
- `artifacts/final_test_lock.json`
- `src/crypto_hedge_fund/pretest_lock.py`
- `tests/unit/test_pretest_freeze.py`
- Supporting command-path files: `Makefile`, `src/crypto_hedge_fund/cli.py`, `configs/default.yaml`, data/universe proof writers found by `rg`.

## Assumptions and decisions

- I treated Stage 10 as a pretest lock review, not a final-test-runner review or profitability review.
- I treated validation artifact hashes in `artifacts/final_test_lock.json` as part of the frozen checkpoint contract because they are explicitly recorded under `hashes.validation_artifact_hashes`.
- I treated structural 2025 data coverage checks as allowed only when they do not expose strategy performance, rankings, final-test returns, orders, fills, or tuning metrics.
- I considered `make final-test` fail-closed today because it refuses to run after finding a lock. However, that is not the same as implemented hash-mismatch validation for Stage 11.

## Files inspected or changed

Inspected:

- The mandatory sources above.
- Current Git status and Stage 10 diffs.
- Current lock, selected config, lock sidecar and validation artifact hashes.
- Current Level 1-5 metrics provenance fields.
- Current `final-test` CLI path and pretest lock helper/test coverage.
- Current `level_5_pair_count_proof.json` content and diff.

Changed:

- `reports/agent_reports/stage_10_pretest_freeze/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_01/command_logs/arch_*.log`
- `reports/agent_reports/stage_10_pretest_freeze/attempt_01/command_logs/arch_*.status`

## Deliverables

- This architecture/quarantine review report.
- Read-only review logs under `reports/agent_reports/stage_10_pretest_freeze/attempt_01/command_logs/`.

## Acceptance-criteria mapping

- Lock exists and state transition is represented: PASS. `configs/validation_selected.yaml` records `NOT_EXPOSED` before lock; `artifacts/final_test_lock.json` records `LOCKED`; `final_test_results_inspected` is `false`.
- Required selected choices: PASS_WITH_NOTES. The lock records selected Levels 1-5 methodology, costs, seeds, periods, benchmarks and hashes. Some global risk/liquidity/long-only constraints are frozen indirectly through the hashed `configs/validation_selected.yaml`, not expanded directly in the JSON lock.
- Models/agent choices: PASS. Level 2 freezes ensemble approach, model list, retraining/refit cadence, calibration, thresholds and equal agent weights summing to 1.0.
- Assets/universe rules: PASS. Level 3 freezes validation/final symbols and exact trailing-12-month windows; Level 5 freezes universe filters, required 100 scored pairs, selected symbols, top-K and allocator.
- Portfolio constraints/rebalance policy: PASS_WITH_NOTES. Level 4 selected policy and selection constraints are recorded; Level 5 top-K, max weight and turnover cap are recorded. Broader risk/liquidity settings are in the hashed selected config.
- Data/config/code/dependency hashes: PASS_WITH_NOTES. Data, instruments, manifest, `uv.lock`, `pyproject.toml`, default config and selected-config hashes are present. The lock uses base commit `394d146523445ed53c978ade1033cc7870237a8f` plus dirty paths/diff hash, so the eventual checkpoint commit will not equal the lock's `git.commit` unless the lock is regenerated after checkpointing.
- Artifact hash coherence: FAIL. One recorded validation artifact hash no longer matches the current worktree.
- Dirty-worktree policy: PASS_WITH_NOTES. `make pretest-freeze` refuses forbidden dirty methodology/config paths in the focused unit test, but allows broad `artifacts/` changes and selected Stage 10 helper/test/CLI changes.
- Final-test quarantine: PASS_WITH_NOTES. I found no final-test strategy performance artifacts or metrics. The current `level_5_pair_count_proof.json` is a 2025 data-validation/universe proof, not strategy performance, but its path collision with the validation Level 5 proof breaks lock coherence.
- Final-test hash mismatch enforcement: HIGH RISK. The lock declares `final_test_command_must_refuse_hash_mismatch: true`, but the current `final-test` command only refuses all locked runs as not-yet-implemented and does not validate hashes.

## Commands executed

| Command | Exit status | Evidence/log |
|---|---:|---|
| `git status --short --branch --untracked-files=all` plus `git diff --name-only` | 0 | `command_logs/arch_git_status.log` |
| Lock/config/artifact hash and provenance probe | 0 | `command_logs/arch_lock_probe.log` |
| Final-test command/guard source scan | 0 | `command_logs/arch_final_test_guard_probe.log` |
| `uv run pytest -p no:cacheprovider tests/unit/test_pretest_freeze.py` | 0 | `command_logs/arch_pytest_pretest_freeze.log` |
| Quarantine/artifact string scan | 0 | `command_logs/arch_quarantine_artifact_scan.log` |
| Pair-count proof mismatch probe | 0 | `command_logs/arch_pair_proof_hash_mismatch.log` |
| Universe/proof writer and Stage 10 diff source scan | 0 | terminal output only; used to identify the path collision root cause |

Focused test result: `tests/unit/test_pretest_freeze.py` passed, 2 tests in 0.18s.

## Test and artifact evidence

- Lock hash: `733fa797c08deec65eae347c122d9b046af87cb0243a39d0449e00ea6060a3bc`; sidecar matches.
- Selected-config file hash: `2a7a756ea89c363bade1e89b5bfcdaec8c66a02bfad92cbf0a10816db0473d99`; lock matches.
- Lock records periods: train `2021-01-01` to `2023-12-31`, validation `2024-01-01` to `2024-12-31`, final test `2025-01-01` to `2025-12-31`.
- Lock records Level 5 validation window: `2024-12-08` to `2024-12-31`.
- Lock records 47 validation artifact hashes. Current worktree has 0 missing hashed artifacts and 1 mismatched hashed artifact.
- Mismatched artifact: `artifacts/monitoring/level_5_pair_count_proof.json`.
- Lock expected hash for that file: `35cbbeceb8f11b4574b72537b3585b15265a29ef1b6617b03d5841469a31beb5`.
- Current hash for that file: `af35649b0e832d141f20fedf737ec50b18acc1c30ebb18387e014dcc6699ffef`.
- Current Level 1-5 metrics are still `provenance_split=validation`, have blank `provenance_final_test_lock_hash`, and include `validation_only_no_final_test_metrics`.
- Current `level_5_pair_count_proof.json` is not the Level 5 validation proof expected by the lock. Its diff shows a data-validation proof with `decision_cutoff_utc: 2025-07-01T00:00:00+00:00`, `eligible_count: 104`, and no `final_test_exposure: NOT_EXPOSED` marker, replacing the validation proof that had Level 5 decision dates in December 2024 and `scored_count: 100`.
- The source scan shows both `src/crypto_hedge_fund/data/validation.py` and `src/crypto_hedge_fund/experiments/level_5.py` write `artifacts/monitoring/level_5_pair_count_proof.json`, creating a path collision between data-validation proof and Level 5 validation proof.

## Findings by severity

### BLOCKER

- B-001: The current validation artifact set is not coherent with `artifacts/final_test_lock.json`. The lock records `artifacts/monitoring/level_5_pair_count_proof.json` hash `35cbbe...`, but the current file hashes to `af3564...`. The current file is a data-validation universe proof at a 2025-07-01 cutoff, not the Level 5 validation proof used by the lock. This means the regenerated validation artifacts should not be accepted into the Stage 10 checkpoint as-is. Restore the intended Level 5 validation proof or rerun in a deterministic order that writes validation artifacts last, then rerun `make pretest-freeze`. Longer term, separate the data-validation universe proof path from the Level 5 experiment pair-count proof path.

### HIGH

- H-001: Hash-mismatch enforcement for `make final-test` is not implemented yet. The lock declares that the final-test command must refuse mismatched hashes, but `src/crypto_hedge_fund/cli.py` currently only checks that the lock exists and then fails closed because the final-test runner is reserved for a later stage. This preserves quarantine today, but it does not prove Stage 11 will reject changed data/config/code/selected methodology after the lock. Add a lock validation function and tests that mutate config/data/selected config/lock hash inputs and verify refusal before any final-test computation.

### MEDIUM

- M-001: The lock's `git.commit` is the Stage 9 base commit while Stage 10 is dirty and includes the lock helper, CLI change, tests, `.gitignore`, selected config, lock and regenerated artifacts. The lock records dirty paths and a diff hash, which is transparent, but a later team-lead checkpoint commit will not match `git.commit`. Before Stage 11, either regenerate the lock after the Stage 10 checkpoint commit or make the final-test validator explicitly accept and verify the recorded dirty diff/content hashes.
- M-002: `run_pretest_freeze` allows all `artifacts/` dirty paths. It then checks required validation artifacts, which is useful, but broad artifact allowance can hide unrelated generated outputs or stale proof collisions. Tighten this to the exact validation artifact allowlist plus lock outputs, and keep data-validation proof artifacts on distinct paths.
- M-003: The JSON lock freezes some global risk/liquidity/long-only constraints only indirectly through `validation_selected_sha256`. This is acceptable for cryptographic reproducibility if Stage 11 validates that file, but reviewer-facing completeness would improve if the lock duplicated the risk, liquidity, exposure and cash/leverage/short flags directly.

### LOW

- L-001: `src/crypto_hedge_fund/pretest_lock.py` includes `src/crypto_hedge_fund/provenance.py` in allowed dirty paths even though provenance hashing affects lock semantics. If this remains intentional, document why it is operational-only and include focused test coverage.
- L-002: The lock records Level 5 benchmark as `price_normalized_btc_open_to_open`, matching the Stage 9 known limitation. This is not a quarantine failure, but it remains weaker than the protocol-preferred equal-weight eligible/top-K benchmark and must be disclosed or corrected before final narrative claims.

## Regenerated validation artifact decision

Do not accept the current regenerated validation artifacts into the Stage 10 checkpoint as-is.

The Level 1-5 metrics remain validation-only and the lock captures most intended choices, but the `level_5_pair_count_proof.json` path collision makes the current artifact tree inconsistent with the lock. Restoring prior accepted artifacts alone is not sufficient unless the restored file hash matches the lock and `make pretest-freeze` remains reproducible. The safer checkpoint sequence is:

1. Ensure `make validate-data` writes its 2025 data/universe proof to a data-validation-specific path.
2. Rerun `make experiments-val` so the Level 5 validation proof is the experiment proof with `final_test_exposure=NOT_EXPOSED`.
3. Rerun `make pretest-freeze`.
4. Re-probe that every hash in `hashes.validation_artifact_hashes` matches the worktree before checkpointing.

## Final-test quarantine assessment

No final-test strategy results were run or inspected in this review. Current validation metrics are labeled `validation`, have no final-test lock hash, and include validation-only warnings. The current 2025 data-validation proof does not contain strategy performance, but because it overwrote the Level 5 validation proof path it is a checkpoint integrity blocker.

The final-test state transition is semantically correct in the lock: `NOT_EXPOSED` before lock, `LOCKED` after lock, and no `EXPOSED` state observed. The implementation must not proceed to Stage 11 until the artifact hash mismatch is fixed and final-test hash validation is implemented or explicitly completed as the first Stage 11 gate before any final-test computation.

## Unresolved risks and limitations

- Stage 11 final-test runner is not implemented and was not run.
- I did not rerun full `make validate-data`, `make lint`, `make test`, `make experiments-val`, or `make pretest-freeze`; this review used focused probes and the implementation report's logged command claims.
- Active Binance/CCXT survivorship and delisting bias remains inherited project risk.
- Level 5 validation remains a short late-December 2024 proof window and should not be framed as broad alpha evidence.

## Recommendation

DO_NOT_ACCEPT_AS_CHECKPOINT

Stage 10 attempt 01 preserves final-test quarantine in the sense that no final-test strategy metrics were exposed, and it contains most of the right lock fields. It is not checkpoint-safe because the current artifact tree no longer matches the lock and the future final-test hash-mismatch validator is not implemented.
