# Stage 11 Final-Test Incident Record

## Scope

This document records the Stage 11 final-test incident without changing or deleting
the original logs. It is a release/provenance note, not a methodology update.

## Provenance

- Accepted final-test lock hash:
  `dab407601cbaf8198361e5e3d074260546ed4bbab4c4be2555248b246631308b`.
- Lock file: `artifacts/final_test_lock.json`.
- Locked commit recorded inside the lock and frozen final summary:
  `394d146523445ed53c978ade1033cc7870237a8f`.
- Final-test runner commit recorded by frozen Stage 11 artifacts:
  `6aad82116feb26f83b7658414207e03371e07864`.
- Accepted Stage 11 checkpoint tag: `stage/11-final-test`, commit
  `33e5008fc5614ba500999b0ef8e41c641f723cee`.
- Frozen final-test artifact directory:
  `artifacts/final_test/dab407601cba/`.

## First Failed Attempt

The first Stage 11 `make final-test` attempt failed with exit status `2`.
The original log is:

```text
reports/agent_reports/stage_11_final_test/attempt_01/command_logs/make_final_test.log
```

The failure occurred during Level 5 before the final suite summary and exposure
evidence were written. The exception was:

```text
crypto_hedge_fund.execution.panel.MissingPriceError:
missing valuation open at 2025-01-01T00:00:00+00:00
```

The missing symbols listed in the log were newly listed or otherwise unavailable
at that execution timestamp, including `AIXBT/USDT`, `ANIME/USDT`, `BERA/USDT`,
`KAITO/USDT`, `TRUMP/USDT`, `VIRTUAL/USDT`, and others.

## Output Exposure Status

Evidence from the Stage 11 worker and independent reviews says the failed run
likely materialized partial Level 1-4 final artifacts before Level 5 failed,
because the final runner executes levels sequentially. The failed command log did
not print final-suite metrics and did not write:

- `artifacts/final_test/dab407601cba/final_test_suite_summary.json`
- `artifacts/final_test/dab407601cba/final_test_exposure_evidence.json`

Whether any human inspected partial Level 1-4 performance outputs before the fix
cannot be proven from the committed logs. The independent reviewers found no
evidence that partial outputs were used to tune methodology.

## Defect

The exact defect was in the shared simulated broker. At each execution timestamp,
the broker required valuation prices for every symbol appearing in the target
schedule, including symbols with target weight exactly zero. Level 5 schedules
can contain zero-weight placeholder columns for symbols that are not held and not
being traded. Those placeholders should not require a next-open price.

The fix excluded zero-weight target symbols from the active-symbol price lookup
while preserving fail-closed behavior for:

- existing nonzero holdings;
- nonzero target trades;
- missing execution prices for actual orders.

The source diff used to review the fix is preserved at:

```text
reports/agent_reports/stage_11_final_test/attempt_01/command_logs/arch_diff_broker_fix.log
```

The regression test added for the defect was:

```text
tests/unit/test_execution_kernel.py::test_zero_weight_placeholder_symbol_does_not_require_missing_price
```

## Classification

The change was classified as an implementation-defect fix rather than
performance tuning because it changed only broker treatment of zero-weight
placeholder symbols. Existing missing-price fail-closed behavior remained in
force for held symbols and nonzero targets. The Stage 11 reports state that no
model, threshold, feature, target, asset list, universe rule, top-K setting, risk
limit, rebalance rule, selected method, benchmark, or transaction-cost assumption
was changed after exposure.

## Dirty Runner Provenance

The accepted Stage 10 lock records `394d1465...` as the locked commit. The
frozen Stage 11 final artifacts record `git_commit=6aad821...` and dirty runner
source provenance because the final-test runner implementation and broker fix
were uncommitted when the successful frozen suite ran. This is disclosed in:

- `reports/teamlead/PROJECT_STATE.md`
- `reports/teamlead/RISK_REGISTER.md`
- `reports/agent_reports/stage_11_final_test/attempt_01/TEAMLEAD_DECISION.md`
- `artifacts/final_test/dab407601cba/final_test_suite_summary.json`

The final-test lock was not mutated to absorb this runner state.

## Review Conclusion

Independent Stage 11 QA and architecture/quarantine review both accepted the fix
with notes. Their conclusion was that the broker change did not require rollback
or methodology rework, provided the incident and dirty-runner provenance remained
disclosed:

- `reports/agent_reports/stage_11_final_test/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_11_final_test/attempt_01/ARCHITECTURE_REVIEW.md`
- `reports/agent_reports/stage_11_final_test/attempt_01/TEAMLEAD_DECISION.md`

## Unknowns

- It cannot be proven from committed logs whether any person inspected partial
  Level 1-4 performance outputs produced before the first run failed.
- It cannot be proven from committed logs that no transient local files existed
  outside the repository during the failed run.

No original Stage 11 logs were rewritten for this incident record.
