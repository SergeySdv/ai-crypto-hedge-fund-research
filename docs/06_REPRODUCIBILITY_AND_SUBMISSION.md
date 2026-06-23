# Reproducibility And Submission

## Required Environment

- Python 3.11.
- `uv`.
- No exchange credentials.
- No LLM key.
- No paid service.
- No live data download for the default final run.

## Main Verification Command

```bash
make release-verify
```

This runs:

1. `uv sync --frozen`
2. `make validate-data`
3. `make lint`
4. `make test`
5. `make notebook-full`
6. `make report`
7. `make presentation`
8. `make verify-final-lock`
9. `make pdf-page-count`
10. `git diff --exit-code`

## Stable Individual Commands

```bash
make setup
make validate-data
make lint
make test
make experiments-val
make pretest-freeze
make notebook-fast
make notebook-full
make report
make presentation
make all-fast
```

`make final-test` exists for the frozen final suite, but should not be rerun
during ordinary release review now that final-test exposure is already complete.

## Current Release Checks

The cleaned submission has been verified with:

- `make release-verify` passing;
- 113 tests passing;
- persisted full notebook outputs;
- final lock verification passing;
- 10-page `presentation/AI Crypto Hedge Fund - Defense Deck.pdf`;
- clean git tree after verification.

## Reviewer Entry Points

| Need | File or command |
| --- | --- |
| Project summary | `README.md` |
| Full narrative run | `notebooks/ai_crypto_hedge_fund.ipynb` |
| Final report | `reports/final_report.md` |
| Presentation | `presentation/AI Crypto Hedge Fund - Defense Deck.pdf` |
| Lock check | `make verify-final-lock` |
| Full release gate | `make release-verify` |

## Public Repository Reminder

This local checkout cannot prove public GitHub or GitLab visibility. The human
owner still needs to publish or verify the public repository URL, default branch,
and release/tag used for submission.
