# 12 — Final-test freeze, clean-run protocol and submission checklist

## Purpose

The final test is evidence, not a development dashboard. All five levels must be designed and selected before final-test metrics are viewed.

## Stage A — development without final-test access

Allowed:

- synthetic fixtures;
- train period;
- validation period;
- rolling validation folds;
- structural tests that do not reveal test returns;
- checking that test dates exist and schemas are valid.

Not allowed:

- selecting a parameter because 2025 Sharpe improved;
- replacing assets because 2025 performance was poor;
- changing top-K, costs, universe filters or rebalance rules after reading test outcomes;
- comparing many final-test variants and reporting the best.

## Stage B — pretest freeze

Create a command such as:

```bash
make pretest-freeze
```

It must:

1. verify lint/tests/data validation and train/validation experiments;
2. resolve the effective full configuration;
3. record selected strategies, models, thresholds, agent weights, portfolio methods and rebalance rules;
4. record data SHA-256, git commit and dependency lock hash;
5. write `artifacts/final_test_lock.json`;
6. fail if there are uncommitted methodology/config changes, unless an explicit documented override is used.

Suggested lock structure:

```json
{
  "created_at_utc": "...",
  "git_commit": "...",
  "uv_lock_sha256": "...",
  "data_sha256": "...",
  "config_sha256": "...",
  "test_period": ["2025-01-01", "2025-12-31"],
  "selected": {
    "level_1": {},
    "level_2": {},
    "level_3": {},
    "level_4": {},
    "level_5": {}
  }
}
```

## Stage C — one frozen final-test suite

```bash
make final-test
```

Requirements:

- runs Levels 1–5 from the same lock;
- refuses a mismatched data/config hash;
- writes all results under a lock-specific artifact directory or embeds the lock hash in metadata;
- never performs hyperparameter search on test data;
- generates gross and net performance/risk metrics and benchmarks;
- records exact runtime and any warnings.

## Stage D — notebook and presentation

The notebook and deck consume the frozen final artifacts. They may re-run the same frozen calculation for reproducibility, but they may not change the locked choices.

Commit:

```text
notebooks/ai_crypto_hedge_fund.ipynb   # executed full mode
presentation/deck.md
presentation/deck.pdf
reports/final_report.md
artifacts/final_test_lock.json
```

## Clean-clone release rehearsal

From a new directory/machine:

```bash
git clone <PUBLIC_URL>
cd <REPOSITORY>
uv sync --frozen
make validate-data
make test
make notebook-full
make presentation
```

Then verify:

- no API key or live network request is required for the notebook;
- deleting `artifacts/` and rerunning recreates headline outputs;
- the notebook uses included frozen data;
- Level 5 full output proves at least 100 pairs;
- `deck.pdf` is at most 10 slides;
- all paths are repository-relative;
- no secrets or local absolute paths are present.

## Public repository requirement

Codex may prepare the repository but may not have permission to publish it. The human owner must confirm:

- GitHub/GitLab repository is public;
- default branch contains the final commit;
- README shows exact commands and expected runtime;
- notebook and presentation render in the web UI or are downloadable;
- release/tag points to the submitted commit.

## Bug discovered after test exposure

A correctness bug may be fixed, but record:

- bug description;
- affected files and metrics;
- why the fix is methodological rather than performance-driven;
- old and new lock hashes;
- whether claims are downgraded due to test exposure.

Do not silently relabel post-test tuning as a bug fix.
