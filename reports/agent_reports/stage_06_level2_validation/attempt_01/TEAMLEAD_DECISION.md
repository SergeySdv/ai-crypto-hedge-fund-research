# Team Lead Decision / Stage 6 Level 2 Validation / Attempt 01

## Reports considered

- `reports/agent_reports/stage_06_level2_validation/attempt_01/IMPLEMENTATION_REPORT.md`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/QA_REPORT.md`
- `reports/agent_reports/stage_06_level2_validation/attempt_01/ARCHITECTURE_REVIEW.md`
- Stage 5 checkpoint decision: `reports/agent_reports/stage_05_level1_validation/attempt_02/TEAMLEAD_DECISION.md`

## Targeted diffs inspected

- `git status --short --branch --untracked-files=all`
- `git check-ignore` probes for Level 2 required artifacts
- Stage 6 implementation and review reports
- Worker/reviewer evidence for:
  - `src/crypto_hedge_fund/features/level2.py`
  - `src/crypto_hedge_fund/models/econometric.py`
  - `src/crypto_hedge_fund/models/ml.py`
  - `src/crypto_hedge_fund/agents/level2.py`
  - `src/crypto_hedge_fund/experiments/level_2.py`
  - `tests/unit/test_level2_validation.py`
  - `artifacts/**/level_2*`

## Commands independently rerun or accepted as reviewer evidence

Reviewer evidence shows:

| Command | Status | Evidence |
|---|---:|---|
| `uv sync --frozen` | PASS | Worker, QA and architecture logs. |
| `make lint` | PASS | Worker and QA logs. |
| `make test` | PASS | Worker and QA logs; 75 tests passed. |
| `make experiments-val` | PASS | Worker and QA logs; validation-only and `NOT_EXPOSED`. |
| `uv run pytest tests/unit/test_level2_validation.py` | PASS | Worker, QA and architecture logs; 4 tests passed. |
| Artifact/provenance probes | PASS/REWORK evidence | Artifacts exist and are validation-only, but are ignored by Git. |
| Final-test quarantine scan | PASS | No final-test exposure found. |

The lead did not perform a final gate rerun because independent review found an unresolved HIGH issue. A full lead rerun will be performed after remediation.

## Acceptance criteria passed

- Level 2 implementation exists for BTC/USDT using technical, econometric, Logistic Regression, HistGradientBoosting and ensemble approaches.
- Worker and reviewers found validation-only artifacts, no future-label audit flags and no final-test exposure.
- Existing tests pass and focused Level 2 tests validate feature/target alignment and artifact evidence.
- The implementation appears to use the shared orchestrator/risk/broker path rather than a standalone backtester.
- Validation results honestly report that buy-and-hold outperformed Level 2 approaches.

## Acceptance criteria failed

- Required Level 2 artifacts are physically present but ignored by `.gitignore`, so the stage evidence is not checkpoint-safe through normal Git staging.
- Econometric refit cadence is inconsistent in the current evidence: architecture review found forecasts are causally refit daily while config/trace wording implies monthly expanding refit. The implementation and documentation/artifacts must describe the actual cadence consistently.

## Unresolved risks

- `make experiments-val` regenerates Level 1 artifacts together with Level 2. This needs a repeatable policy before later multi-level validation checkpoints.
- Multiple-seed robustness is currently limited: the trading artifacts are generated from the primary seed while robustness reports additional validation checks.
- Active-market survivorship/delisting limitation from Stage 2 remains accepted and must stay disclosed.

## Decision

REWORK

Stage 6 attempt 01 cannot pass while the required Level 2 artifacts are ignored and methodology wording is inconsistent.

## Remediation packet for attempt 02

Assign a fresh implementation fixer with this constrained mission:

- Add narrow `.gitignore` exceptions so all required Level 2 artifacts and metadata sidecars are checkpoint-safe without broadly committing unrelated generated artifacts.
- Reconcile the econometric refit cadence across code, config, trace, metrics, robustness artifacts and reports. Either make the econometric model follow the documented monthly expanding cadence or explicitly document that econometric forecasts are daily causal refits while ML uses monthly expanding refits.
- Add or adjust tests/artifact checks proving the chosen cadence is recorded consistently and does not introduce look-ahead.
- Preserve the existing validation-only Level 2 implementation and do not tune based on results.
- Preserve final-test state `NOT_EXPOSED`; do not run `make final-test` or inspect final-test returns, rankings, charts or final model outputs.
- Rerun `uv sync --frozen`, `make lint`, `make test`, `make experiments-val`, `uv run pytest tests/unit/test_level2_validation.py`, and a Git ignore/artifact visibility probe.

After remediation, assign fresh independent QA and modeling/leakage reviewers for attempt 02. The team lead will rerun decisive gates and inspect artifacts before any commit/tag.
