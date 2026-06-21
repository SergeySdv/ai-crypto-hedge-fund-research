# 00 — Global plan, assignment audit and architecture invariants

## Why this document exists

The source assignment is short, but its requirements are coupled across all five implementation levels. Implementing the levels as five independent mini-projects is likely to produce the wrong architecture, duplicate logic, contaminate the final test, or fail the 100+ pair requirement.

This document is the first file Codex must read. It records the full-task interpretation and the decisions that must be made before implementation begins.

## Audit result

The seven-page assignment has no hidden appendix or extra rubric beyond the visible text. However, several requirements have important cross-level implications that are easy to miss:

1. Part 1 and Part 2 must present one coherent system, not a theoretical deck plus unrelated code.
2. Every technical level must use out-of-sample evaluation and report both performance and risk metrics.
3. Level 3 explicitly says **5–7 popular coins using the last 12 months of historical data**.
4. Level 5 requires **at least 100 pairs**, dynamic rebalancing, monitoring beyond trading KPIs, long-term quality tracking, and fail-safe stop signals.
5. The final deliverable is one self-contained reproducible notebook, but the code must also be modular and non-spaghetti. Therefore, the notebook is the orchestrating narrative while reusable logic stays in `src/`.
6. All required data must be included with the project; the final notebook cannot depend on a live exchange download.
7. The presentation must be at most 10 slides, cover all four conceptual sections, justify choices, and remain visually clean.
8. “AI agents” must visibly interact. Merely renaming ordinary functions to `Agent` is not sufficient evidence of an agent-based system.
9. The architecture diagram must include data collection, signal agents, order execution, monitoring, risk management and portfolio management, with interactions explained.
10. The future multi-exchange, Telegram, news and sentiment ideas should be supported by interfaces and roadmap, but must not distract from the historical MVP.

See `11_REQUIREMENTS_TRACEABILITY.md` for a line-by-line requirement map.

## One architecture for all five levels

The implementation must be panel-native and portfolio-native from the first commit.

- Level 1 is the same multi-asset engine with a universe of one symbol.
- Level 2 is the same engine with several signal agents but still one symbol.
- Level 3 activates multi-asset allocation with fixed weights.
- Level 4 activates the rebalance controller and rolling estimates.
- Level 5 activates the point-in-time universe, cross-sectional scoring, capacity controls and system monitoring.

Do **not** build a single-asset backtester and later replace it with a different portfolio backtester. Do **not** create separate time conventions, cost logic or metric implementations per level.

### Shared core that must exist before Level 1

```text
MarketPanel + instrument metadata
        ↓
Causal feature pipeline
        ↓
Typed signal/agent messages
        ↓
Pre-allocation risk constraints
        ↓
Portfolio allocator
        ↓
Rebalance controller
        ↓
Post-allocation risk validation
        ↓
Order generation → simulated broker → fills
        ↓
Portfolio ledger
        ↓
Metrics, audit log and monitoring
```

## Non-negotiable global invariants

### 1. Panel-native data model

Use long-form data keyed by `(bar_start_utc, symbol)` plus instrument metadata. All APIs accept one or many symbols without changing semantics. A one-symbol DataFrame is a valid subset of the same panel.

### 2. Causal execution convention

Primary convention:

1. A daily bar is labeled by its UTC start time.
2. Features are available only after that bar closes.
3. A decision made after close `t` is executed at the next available open `t+1`.
4. The new position earns the subsequent open-to-open holding return.
5. Costs are charged on actual risky-asset notional traded at execution.

This is safer than assuming a trade can be filled at the same close used to calculate the signal. A close-to-close approximation may be shown only as a clearly labeled sensitivity check.

### 3. Two-stage risk control

Portfolio-level risk cannot be checked only before allocation. Use:

- **Pre-allocation risk gate:** data freshness, blocked assets, gross/per-asset/liquidity limits and current kill-switch state.
- **Post-allocation risk gate:** validates the candidate portfolio’s volatility, concentration, turnover, feasibility and all hard limits; it can cap, reject or move to cash.

Risk has veto power in both stages.

### 4. Actual agent interaction

Agents must have:

- a responsibility and lifecycle;
- historical fit cutoff and feature cutoff;
- typed input context;
- typed output with score, confidence, horizon and reason codes;
- ability to abstain or fail safely;
- an orchestrator/aggregator that resolves conflicts;
- a decision trace showing how several agent outputs produced a final action.

An external LLM is not required. The ML and econometric components are AI/analytical agents; optional LLM narration must never alter trades.

### 5. Final-test quarantine

Do not inspect 2025 test results while implementing Levels 1–5.

Workflow:

1. Implement and debug on fixtures, train data and validation data.
2. Select every model, threshold, ensemble weight, universe rule, portfolio constraint and rebalance policy.
3. Create `artifacts/final_test_lock.json` containing the git commit, data hash, config hash and frozen choices.
4. Run all five final tests together only after the lock exists.
5. Re-running identical frozen code is allowed. Changing methodology after viewing test results is not.
6. Bug fixes after test exposure must be logged; they may not introduce performance-driven tuning.

This corrects a common mistake: evaluating each level on the final test before later levels and architecture are frozen.

### 6. Exact Level 3 interpretation

Use the **immediately preceding 12 months** as the estimation window for the static portfolio. With the default frozen study:

- estimation window: `2024-01-01` through `2024-12-31`;
- weights frozen at the cutoff;
- execution: first valid open in 2025;
- out-of-sample holding/evaluation: 2025.

The 5–7 asset universe must be selected using information available at the cutoff, preferably trailing liquidity and coverage rather than hindsight-based manual popularity.

For method/policy validation, use a prior vintage rather than backtesting 2024 with a universe selected at the end of 2024:

- select the validation universe and estimate static weights using data through `2023-12-31`;
- evaluate candidate portfolio methods/rebalance rules during 2024;
- after selection is frozen, select the final universe and refit final weights using data through `2024-12-31`;
- evaluate only in 2025.

### 7. Hard 100+ pair requirement

Level 5 is not complete unless a full-mode rebalance actually handles and scores at least 100 eligible pairs. “The source did not have enough pairs” is a limitation, not completion. Change the frozen source, date coverage or eligible exchange before submission if needed.

Fast CI mode may use fewer symbols, but final committed results and the full executed notebook must prove the 100+ pair run.

### 8. Data physically delivered

The default processed dataset, instrument metadata and manifest must be present in the submitted project and sufficient for an offline run after checkout. A downloader is supplementary.

Preferred files:

```text
data/processed/ohlcv_daily.parquet
data/processed/instruments.parquet
data/manifests/ohlcv_daily_manifest.json
```

Daily OHLCV for roughly 120–200 pairs is normally small enough when compressed. Raw exchange responses may be omitted if the processed snapshot, provenance and hashes are complete.

### 9. Presentation is an actual deliverable

Create both source and rendered output:

```text
presentation/deck.md
presentation/deck.pdf
```

The rendered deck must contain at most 10 slides. Aim for roughly two slides per required conceptual section, with implementation evidence embedded into those sections.

### 10. Single notebook means a clean end-to-end entry point

The single final notebook must:

- use the same package code as CLI/tests;
- validate the included data;
- regenerate or validate all headline artifacts from an empty `artifacts/` directory;
- execute top-to-bottom in a clean kernel;
- contain headings matching Levels 1–5;
- show actual results and explanations, not only links to files;
- be committed in fully executed form for review.

Do not create multiple competing “final” notebooks.

## Cross-level dependency map

| Shared capability | L1 | L2 | L3 | L4 | L5 |
|---|:---:|:---:|:---:|:---:|:---:|
| Panel data and causal clock | ✓ | ✓ | ✓ | ✓ | ✓ |
| Same broker, costs and ledger | ✓ | ✓ | ✓ | ✓ | ✓ |
| Technical signals | ✓ | ✓ | optional | optional | ✓ |
| Econometric/ML agents |  | ✓ | optional | optional | ✓/pooled |
| Portfolio allocator | cash/asset | cash/asset | ✓ | ✓ | ✓ |
| Rebalance controller | signal change | signal change | one initial allocation | ✓ | ✓ |
| Pre/post risk gates | minimal | ✓ | ✓ | ✓ | ✓ |
| Point-in-time universe | fixed 1 | fixed 1 | cutoff-selected 5–7 | same 5–7 | dynamic 100+ |
| Monitoring/fail-safes | basic | model health | portfolio health | rebalance health | full system health |

## Architecture decisions that must be frozen before coding strategies

1. Timestamp semantics and next-open execution.
2. Return, cost and turnover formulas.
3. Missing-bar and delisting behavior.
4. Data schema and instrument metadata.
5. Agent message contracts and orchestration.
6. Pre/post risk sequence.
7. Portfolio weight and cash invariants.
8. Train/validation/final-test periods.
9. Artifact naming and provenance hashes.
10. Full-mode versus fast-mode guarantees.

## What remains intentionally future work

- private exchange credentials and real orders;
- multi-exchange smart order routing;
- leverage, derivatives and shorting;
- Telegram controls;
- news/sentiment ingestion;
- deep reinforcement learning;
- distributed microservices.

The architecture should expose adapters for future market data and execution, but the submitted default must remain a deterministic historical research system.
