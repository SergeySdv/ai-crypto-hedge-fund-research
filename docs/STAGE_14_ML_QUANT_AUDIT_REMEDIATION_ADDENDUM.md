# Stage 14 — ML/Quant Audit Remediation Addendum

Use this file together with `STAGE_14_FINALIZATION_TEAMLEAD_PROMPT.md`.
This addendum supersedes any conflicting instruction concerning ML/quant evidence.

## Audit verdict

The repository contains real ML, econometric, agent and large-universe quant
implementations. The remaining submission risk is primarily reviewer-facing
transparency and precise claims, not missing core code.

Treat the current submission as an educational/research MVP. Do not describe it as
an institutional-grade or proven profitable trading system.

## Immutable boundaries

- Final-test state is already `EXPOSED`.
- Do not rerun `make final-test` or any final-test entry point.
- Do not retrain, retune, recalibrate or reselect using 2025 data.
- Do not change frozen features, target, model classes, thresholds, ensemble weights,
  universe rules, allocation rules, rebalance rules, risk policy or selected methods.
- Preserve all lock-covered and final-test artifacts byte-for-byte.
- Any real methodology improvement belongs to a new version and a new pretest lock.

## Confirmed implementation that must be shown accurately

### Level 2

- `technical_sma`: deterministic SMA signal.
- `econometric_ar_garch`: AutoReg expected-return forecast plus GARCH(1,1)
  volatility forecast, with the documented deterministic fallback.
- `ml_logistic`:
  `SimpleImputer(median) -> StandardScaler -> LogisticRegression`.
- `ml_hist_gradient_boosting`:
  `SimpleImputer(median) -> HistGradientBoostingClassifier`.
- `agent_ensemble`: equal frozen weights `0.25` over technical, econometric,
  logistic and HGB typed signals.

Target:

```text
label_t = 1[
    open_(t+2) / open_(t+1) - 1 > 0.002
]
```

Execution and fitting are causally aligned. The fit audit contains zero
future-label flags. ML refits monthly on an expanding window; the econometric model
refits daily using only causally available history.

### Level 5

Level 5 is a deterministic, vectorized, cross-sectional factor/ranking agent with
risk and portfolio orchestration. It is not a fitted pooled ML classifier,
regressor or ranker.

Use the exact wording:

> deterministic cross-sectional quant scoring with agent, risk and portfolio
> orchestration

Do not call Level 5 a trained ML model, deep-learning model or pooled AI model.

## P0 — required before Stage 14 can pass

### 1. Make the ML process visible in the final notebook

The notebook must visibly contain:

- exact model classes and libraries;
- the 20 causal feature names;
- exact target formula and execution horizon;
- preprocessing;
- hyperparameters;
- train, validation and frozen final periods;
- monthly ML and daily econometric refit cadence;
- fit-audit summary, including zero future-label flags;
- predictive metrics for Logistic Regression and HGB;
- econometric forecast diagnostics;
- representative typed agent contributions;
- robustness evidence already present in committed artifacts;
- validation-selection table before frozen final-test evidence;
- final-test evidence only after the validation section;
- equity, drawdown, exposure/cash, turnover and cost visualizations.

Preferred execution contract:

1. Recompute only pre-2025 validation work from included frozen data into a temporary
   or build directory, or verify the committed validation artifacts deterministically.
2. Never write to lock-covered paths.
3. Load 2025 final-test outputs as frozen evidence only.
4. State explicitly that no 2025 result was used for tuning or selection.

The notebook must not remain only a wrapper around `load_stage12_context()`.

### 2. Explain the Level 2 ensemble selection honestly

The frozen ensemble was not the maximum-Sharpe or maximum-return validation row.
Do not invent a retroactive selection score or claim that it won the leaderboard.

Use an explicit explanation similar to:

> The ensemble was frozen as the assignment-representative multi-agent candidate.
> It demonstrated typed interaction among technical, econometric and ML agents while
> retaining acceptable validation risk and turnover. It was not selected as the
> unconditional maximum-performance row, which is a limitation of the frozen
> selection protocol.

Show a validation table containing:

- approach;
- return;
- Sharpe;
- max drawdown;
- cost;
- turnover;
- selected flag;
- actual reason for selection.

Do not switch the frozen selection after seeing final-test results.

### 3. Correct ML probability language

The current classifiers emit raw `predict_proba` outputs. Calibration quality is
measured, but no Platt, sigmoid or isotonic calibration model is actually fitted.

Therefore:

- call them `raw classifier probabilities`;
- do not call them calibrated probabilities;
- explain the mismatch if configuration contains `calibration: sigmoid`;
- retain calibration as a future-version methodology improvement.

Do not add calibration to the exposed protocol.

### 4. Explain Level 5 fallback and incident evidence

Existing validation evidence reports approximately:

- optimizer fallback rate: `0.8333`;
- incident count: `20`.

Using existing logs only:

- produce per-date or per-reason counts where available;
- explain what allocator was requested and what fallback was used;
- explain whether fallback was expected by design;
- explain why system health could still be `ok`;
- state any missing reason-level evidence honestly.

Do not regenerate or retune Level 5.

### 5. Handle the effective-N metric defect transparently

The existing `average_effective_n` calculation can become misleading for cash-heavy
rows because risky weights are not normalized inside the risky sleeve.

Do not rewrite frozen metrics.

Instead:

- mark the existing field as known-invalid or potentially misleading;
- calculate a separate derived diagnostic from existing frozen weights:

```text
risky_effective_n =
    1 / sum((w_i / sum_risky)^2), when sum_risky > epsilon
    0, otherwise
```

- also report average cash exposure separately;
- clearly label the corrected value as a post-hoc presentation diagnostic not used
  for selection or final-test decisions;
- remove unsupported effective-N claims from the deck.

### 6. Make data provenance limitations prominent

Document without re-freezing data:

- active-market survivorship bias;
- no historical delisted/renamed-market reconstruction;
- no bid/ask spread, order-book depth or outage history;
- 180 requested candidates versus 163 stored symbols;
- missing reason-level provenance for the 17 zero-row candidates;
- daily `close * volume` as a liquidity proxy.

Do not modify the frozen data bundle or manifest in Stage 14.

## P1 — submission-safe where possible

### Decision traces

Surface at least one complete representative trace in the notebook:

```text
agent signals
-> confidence-weighted aggregation
-> pre-allocation risk
-> portfolio proposal
-> post-allocation approval/veto
-> order intent
```

Full historical JSONL/parquet trace persistence is desirable but is not required if
it would require rerunning or mutating frozen final-test artifacts. Document the
current representative-trace limitation.

### Prediction-table schema

Document that nullable model-specific fields are expected because econometric and
classifier rows populate different columns. Add a field-applicability table or
model-card note. Do not present the null count as missing predictions.

### Panel-agent safety

`PredictionTableSignalAgent` currently selects by date and is safe for the frozen
single-symbol Level 2 use, but unsafe for future panel reuse unless it also filters
by symbol. Record this as a known limitation. Patch only if independent review
proves no frozen path or result changes; otherwise defer to the next version.

### Model cards and final report

Update them with:

- exact classes and hyperparameters;
- features and target;
- fit cadence;
- fit-audit counts;
- predictive and trading metrics;
- robustness result;
- known failure modes;
- final-test exposure warning;
- statement that results are not a profitability claim.

## Existing statistical evidence

Surface, do not rerun or redesign:

- moving block bootstrap: 1000 repetitions;
- block length: 14;
- selected Level 2 validation Sharpe 95% CI approximately `[-1.049, 3.020]`;
- circular-shift randomization: 1000 repetitions;
- p-value approximately `0.6823`;
- seeds `[7, 42, 137]`, with the primary seed used for persisted trading artifacts.

Required conclusion:

> Statistical evidence is inconclusive and does not establish persistent alpha.

Do not use these diagnostics to retroactively change the selected approach.

## Explicitly deferred to a new methodology version

Do not implement these inside the current exposed submission:

- validation-selected ensemble weights;
- fitted probability calibration;
- pooled Level 5 ML classifier/regressor/ranker;
- reusable purged/embargo splitter if it changes current experiment behavior;
- broader Level 5 selection window;
- hard effective-N, CVaR, correlation-cluster or marginal-risk controls;
- changes to Level 5 turnover, top-K, allocator or rebalance policy;
- replacement of selected Level 2, 3, 4 or 5 methods.

List them as future work requiring a new pretest freeze and a new untouched final
period.

## Required reviewer-facing positioning

Use:

- educational historical research MVP;
- real causal ML/econometrics at Level 2;
- typed agents propose scores and confidence;
- deterministic risk and execution retain control;
- Level 5 proves 100+ pair scalability, not profitable alpha;
- mixed/negative final-test results are reported honestly;
- main value is reproducibility, leakage control, architecture and auditability.

Avoid:

- production-ready hedge fund;
- profitable AI bot;
- calibrated probabilities;
- trained Level 5 ML model;
- statistically proven alpha.

## Independent review gates

Use separate reviewers for:

1. ML/quant claims and causal alignment.
2. Notebook compliance with the original assignment.
3. Frozen-artifact and release reproducibility.

A reviewer must return `BLOCKED` if any of the following remains:

- notebook still hides the real ML process;
- Level 5 is described as trained ML;
- ensemble selection is presented as metric-optimal;
- raw probabilities are called calibrated;
- effective N is reported without the defect disclosure;
- fallback/incident rates are omitted;
- final lock changes;
- a final-test entry point is executed;
- documented release commands dirty the worktree.

## Stage 14 completion checks

Run without invoking final test:

```bash
uv sync --frozen
make validate-data
make lint
make test
make notebook-full
make presentation
# direct final-lock validation
# PDF page count <= 10
git diff --exit-code
git status --porcelain
```

Stage 14 passes only when:

- all commands pass;
- `make validate-data` remains read-only;
- final lock remains valid;
- frozen final-test artifacts are byte-identical;
- notebook and deck contain accurate ML/quant evidence;
- the deck remains at most 10 pages;
- the worktree is clean;
- independent reviewers return PASS;
- no final-test rerun occurred.

Commit and tag only after all gates pass:

```text
stage/14-release-hardening
```
