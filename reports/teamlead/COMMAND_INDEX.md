# Command Index

Updated: 2026-06-21

## Required Status Commands Run For This Documentation Pass

| Command | Status | Key Result |
|---|---:|---|
| `git status --short --branch --untracked-files=all` | PASS | Branch `main`; Stage 2 changes uncommitted; owner prompt untracked. |
| `git log --oneline --decorate --max-count=5` | PASS | `HEAD` is `7df063f` tagged `stage/01-env-skeleton`. |
| `git tag --list 'stage/*'` | PASS | `stage/00-baseline-handoff`, `stage/00-strategy-gates`, `stage/01-env-skeleton`. |

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

## Not Yet Run For Later Gates

- `make experiments-val`
- `make pretest-freeze`
- `make final-test`
- `make notebook-fast`
- `make notebook-full`
- `make report`
- `make presentation`
