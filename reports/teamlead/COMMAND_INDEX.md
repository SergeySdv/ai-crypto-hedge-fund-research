# Command Index

Updated: 2026-06-21

## Required Status Commands Run For This Documentation Pass

| Command | Status | Key Result |
|---|---:|---|
| `git status --short --branch --untracked-files=all` | PASS | Branch `main`; Stage 3 changes uncommitted before checkpoint. |
| `git log --oneline --decorate --max-count=10` | PASS | `HEAD` is `d51a3e9` tagged `stage/02-frozen-data` before Stage 3 checkpoint. |
| `git tag --list 'stage/*'` | PASS | Tags through `stage/02-frozen-data` before Stage 3 checkpoint. |

## Stage 1 Verified Commands

Evidence: `reports/agent_reports/stage_01_validation.md`.

| Command | Status |
|---|---:|
| `uv sync --frozen` | PASS |
| `make lint` | PASS |
| `make test` | PASS |
| `uv run python -c "import crypto_hedge_fund"` | PASS |
| `make final-test` | PASS as fail-closed guard; exited nonzero because no final-test lock exists |

## Stage 2 Verified Commands

Evidence: `reports/agent_reports/stage_02_frozen_data/attempt_02/TEAMLEAD_DECISION.md`.

| Command | Status | Key Result |
|---|---:|---:|
| `uv sync --frozen` | PASS | Audited 79 packages. |
| `make lint` | PASS | Ruff format/check passed. |
| `make test` | PASS | 26 tests passed. |
| `make validate-data` | PASS | 158,511 rows; 163 symbols; 104 eligible/scored pairs. |
| `uv run python scripts/validate_data.py` | PASS | Same offline validation result. |
| Proof JSON/CSV consistency probe | PASS | JSON and CSV agree on 104 eligible/scored pairs. |
| `git check-ignore` proof-artifact checks | PASS | Required proof artifacts are not ignored. |

## Stage 3 Verified Commands

Evidence: `reports/agent_reports/stage_03_shared_engine/attempt_02/TEAMLEAD_DECISION.md`.

| Command | Status | Key Result |
|---|---:|---:|
| `uv sync --frozen` | PASS | Audited 79 packages. |
| `make lint` | PASS | Ruff format/check passed; 34 files already formatted. |
| `make test` | PASS | 46 tests passed. |
| `uv run pytest tests/unit/test_clock.py tests/unit/test_types.py tests/unit/test_execution_kernel.py tests/unit/test_costs.py tests/unit/test_metrics.py tests/unit/test_artifacts.py` | PASS | 29 focused Stage 3 tests passed. |
| Artifact scan | PASS | Only Stage 2 monitoring proof artifacts present; no strategy/final-test metrics created. |

## Stage 4 Verified Commands

Evidence: `reports/agent_reports/stage_04_agents_risk/attempt_02/TEAMLEAD_DECISION.md`.

| Command | Status | Key Result |
|---|---:|---:|
| `uv sync --frozen` | PASS | Audited 79 packages. |
| `make lint` | PASS | Ruff format/check passed; 50 files already formatted. |
| `make test` | PASS | 66 tests passed. |
| `uv run pytest tests/unit/test_agents_risk.py tests/unit/test_orchestration.py tests/unit/test_portfolio_allocation.py tests/unit/test_monitoring_trace.py` | PASS | 20 focused Stage 4 tests passed. |
| Artifact scan | PASS | Only Stage 2 monitoring proof artifacts present; no strategy/final-test metrics created. |

## Stage 5 Verified Commands

Evidence: `reports/agent_reports/stage_05_level1_validation/attempt_02/TEAMLEAD_DECISION.md`.

| Command | Status | Key Result |
|---|---:|---:|
| `uv sync --frozen` | PASS | Audited 79 packages. |
| `make lint` | PASS | Ruff format/check passed; 56 files already formatted. |
| `make test` | PASS | 71 tests passed. |
| `make experiments-val` | PASS | Generated Level 1 validation artifacts; final-test exposure `NOT_EXPOSED`. |
| `uv run pytest tests/unit/test_level1_validation.py tests/unit/test_experiments_validation.py` | PASS | 5 focused tests passed. |
| Level 1 artifact/provenance inspection | PASS | Artifacts are validation-labeled, checkpoint-safe and include source-state provenance. |

## Not Yet Run For Later Gates

- `make experiments-val`
- `make pretest-freeze`
- `make final-test`
- `make notebook-fast`
- `make notebook-full`
- `make report`
- `make presentation`
