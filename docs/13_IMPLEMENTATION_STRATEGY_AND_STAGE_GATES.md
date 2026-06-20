# 13 - Implementation strategy, stage gates and Git control

## Purpose

This document turns the handoff into an operating plan for implementation. The lead agent keeps architectural ownership, delegates bounded reviews or implementation slices to subagents, and uses Git checkpoints as the source of truth for stage state, rollback and final-test quarantine.

The repository is currently a planning handoff, not an implemented Python project. Initial inventory found:

- no `pyproject.toml`, `uv.lock`, package, tests, data snapshot, notebook, presentation or Makefile yet;
- no pre-existing Git history before the baseline commit;
- docs already define the target architecture, requirements, acceptance criteria and final-test protocol;
- implementation must start from the shared panel-native kernel rather than level-specific prototypes.

## Lead operating model

The lead owns:

- architecture invariants and cross-level consistency;
- final decisions on dependencies, data source, execution clock, costs, risk sequence and artifact contracts;
- integration of subagent work;
- Git checkpoint commits and rollback decisions;
- final-test lock creation and enforcement;
- completion reporting.

Subagents may be used as experts, but they do not own final methodology. Their outputs are review inputs or bounded patches with explicit write scopes.

Recommended expert roles:

- Requirements reviewer: checks every stage against `docs/11_REQUIREMENTS_TRACEABILITY.md` and `docs/06_ACCEPTANCE_CRITERIA.md`.
- Data reviewer: validates data-source feasibility, manifest completeness and the 100+ pair proof.
- Execution reviewer: audits next-open timing, cost accounting, broker, ledger and risk veto behavior.
- Modeling reviewer: audits feature/target leakage, validation folds, econometric/ML agents and ensemble cutoffs.
- Portfolio reviewer: audits Level 3/4/5 allocation rules, optimizer fallbacks, capacity and rebalance logs.
- QA reviewer: runs or designs stage gate tests, reviews final-test quarantine and acceptance evidence.
- Presentation/notebook reviewer: checks that narrative claims match generated artifacts and actual results.

## Git control policy

Use Git as the project control plane.

Baseline:

```bash
git status --short
git log --oneline --max-count=5
```

Stage workflow:

1. Start each stage from a clean worktree.
2. Create or update files for the stage only.
3. Run the stage gate commands.
4. Commit only if the gate passes or if the commit is an explicit non-runtime planning checkpoint.
5. Tag important gates when useful.
6. If a stage fails completely, return to the last passing checkpoint commit and re-plan from there.

Rollback rules:

- Prefer `git restore --source <checkpoint> -- <paths>` for scoped rollback.
- Use `git revert <commit>` for public or shared history.
- Avoid `git reset --hard` unless the human owner explicitly requests it.
- Never rollback unrelated user changes.
- If a failed stage changed final-test methodology after exposure, do not silently recover. Follow `docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`.

Rollback or invalidate the current run if any of these happen:

- final-test metrics were inspected before `artifacts/final_test_lock.json` existed;
- any model, threshold, universe, top-K, constraint, rebalance rule or agent weight changed after final-test exposure;
- full-mode Level 5 scores fewer than 100 eligible pairs;
- same-close execution, look-ahead features, future liquidity or shuffled time split is found;
- data/config/artifact hash mismatch is detected;
- the cost model charges cash as a traded instrument or undercharges asset-to-asset rotation;
- missing or stale data silently creates returns/features;
- risk gates fail open, or signal agents can place orders or mutate the ledger;
- the notebook cannot run from clean artifacts using included data;
- `deck.pdf` exceeds 10 slides or contains claims not backed by artifacts;
- any fabricated, manually edited or unverifiable metric, chart or model output is found.

Suggested checkpoint names:

```text
stage/00-baseline-handoff
stage/01-env-skeleton
stage/02-data-layer-validates
stage/03-execution-kernel
stage/04-agents-risk-trace
stage/05-level1-validation
stage/06-level2-validation
stage/07-level3-validation
stage/08-level4-validation
stage/09-level5-validation-100pairs
stage/10-pretest-lock
stage/11-final-test-artifacts
stage/12-notebook-report-deck
stage/13-clean-clone-release
```

Suggested commit message format:

```text
stage N: short outcome
test: add regression for next-open timing
fix: correct risky-notional cost accounting
docs: record final-test lock protocol
```

## Stage gates

### Stage 0 - Planning and repository control

Scope:

- complete required doc read;
- inventory current files;
- initialize Git;
- record implementation strategy and stage gates.

Gate:

```bash
git status --short
```

Exit:

- clean baseline commit exists;
- gaps are known before implementation begins.

### Stage 1 - Environment and skeleton

Scope:

- `pyproject.toml`, `uv.lock`, `.python-version`, package skeleton, Makefile, configs and CI skeleton;
- config loading, provenance hash utilities, UTC clock helpers and typed records.

Gate:

```bash
uv sync --frozen
make lint
make test
```

Exit:

- package imports;
- public typed interfaces exist;
- command surface exists even if some targets are smoke implementations.

### Stage 2 - Frozen data layer

Scope:

- public downloader/freeze path;
- included processed OHLCV, instruments and manifest;
- validation command and data card;
- deterministic universe filters;
- full-mode Level 5 universe proof artifacts:
  - `artifacts/monitoring/universe_eligibility_full.csv`;
  - `artifacts/monitoring/level_5_pair_count_proof.json`.

Gate:

```bash
make validate-data
```

Exit:

- offline data validates;
- a full-mode date proves at least 100 eligible pairs;
- the proof records mode, decision date, data/config/git hashes, eligibility rules, eligible count, scored count, selected/scored symbols, exclusions with reason codes, trailing liquidity/coverage stats and runtime;
- corrupted fixtures fail loudly.

This stage is high-risk and should be closed before strategy development. If the data source cannot support 100+ pairs, change the source before continuing.

### Stage 3 - Shared execution kernel

Scope:

- panel-native broker, orders, fills, ledger, cost model, benchmarks and metrics;
- pre-trade drifted weights and next-open execution;
- artifact writers with metadata.

Gate:

```bash
make test
```

Required tests:

- completed-bar signal cannot affect same-close or prior PnL;
- cash to asset, asset to cash, asset A to asset B and no-change cost cases;
- missing next-open price blocks execution;
- invalid weights fail closed;
- one-symbol and multi-symbol runs use the same engine;
- typed agent records reject invalid score, confidence, horizon, cutoff and reason-code values.

Exit:

- no level-specific backtester is needed later.

### Stage 4 - Agents, risk and decision trace

Scope:

- typed agents and orchestrator;
- aggregator, abstentions, reason codes and disagreement;
- pre-allocation and post-allocation gates;
- fail-safe fixtures and decision traces.

Gate:

```bash
make lint
make test
```

Exit:

- at least two agents interact through typed messages;
- risk can veto before and after allocation;
- notebook-ready trace exists;
- controlled stop scenarios exist for stale data, NaN/inf score, stale model cutoff, excessive disagreement, optimizer failure, invalid weights, drawdown/volatility stop, capacity breach and reconciliation failure.

### Stages 5 to 9 - Validation-only Levels 1 to 5

Scope:

- implement each level through the shared engine;
- select parameters and policies on train/validation only;
- write validation artifacts labeled `validation`.

Gate:

```bash
make experiments-val
make test
```

Exit:

- all selected choices are reproducible and saved without using 2025 return metrics;
- Level 5 full validation proves at least 100 eligible/scored pairs before pretest freeze.

Do not run `make final-test` during these stages.

### Stage 10 - Pretest freeze

Scope:

- finalize `configs/validation_selected.yaml`;
- run lint, tests, data validation and validation experiments;
- create `artifacts/final_test_lock.json`;
- commit and optionally tag the locked state.

Gate:

```bash
make validate-data
make lint
make test
make experiments-val
make pretest-freeze
git status --short
```

Exit:

- final-test command has a lock to validate against;
- no uncommitted methodology/config change remains.

### Stage 11 - Frozen final test

Scope:

- run all five levels once from the lock;
- generate final artifacts and monitoring outputs;
- record runtime, warnings and Level 5 pair count.

Gate:

```bash
make final-test
```

Exit:

- every final artifact references the lock hash;
- no tuning follows exposure to 2025 metrics.

### Stage 12 - Notebook, report and presentation

Scope:

- execute the one final notebook from a clean artifacts directory;
- build `reports/final_report.md`;
- render `presentation/deck.pdf`;
- verify deck slide count.

Gate:

```bash
make notebook-full
make report
make presentation
```

Exit:

- notebook is committed with full outputs;
- deck has at most 10 slides;
- narrative uses actual generated results only.

### Stage 13 - Clean-clone release

Scope:

- Docker and CI if included;
- license inventory;
- clean-clone rehearsal;
- submission report.

Gate:

```bash
uv sync --frozen
make validate-data
make test
make notebook-full
make presentation
```

Exit:

- owner can publish and verify the public GitHub or GitLab URL.

## Manager checklist

At every stage, track:

- Which acceptance criteria moved from unchecked to checked?
- Which artifacts were created or regenerated?
- Which commands were run and what was the exact pass/fail state?
- Did any command touch final-test returns before the lock?
- Did a subagent identify unresolved gaps?
- Is the worktree clean after the checkpoint commit?

## Current gap summary

The largest gaps to close first are:

- no Python package, dependency lock or Makefile;
- no included data snapshot or proof of 100+ eligible pairs;
- no shared execution kernel, cost model or ledger;
- no typed agent interaction or two-stage risk gates;
- no validation experiments or final-test lock;
- no notebook, report, presentation or acceptance evidence.

The first implementation milestone should therefore be Stage 1 plus a minimal but real Stage 3 skeleton, not a standalone Level 1 notebook. A standalone Level 1 backtest would violate the shared-architecture rule and create avoidable rewrite risk.
