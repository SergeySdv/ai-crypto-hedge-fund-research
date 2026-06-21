# ML/Quant Audit: Models, Agents and Data Validation

Date: 2026-06-21
Auditor role: chief ML/quant engineer
Repository: `codex_crypto_hedge_fund_handoff`
Scope: verify that described models actually train and run, validate frozen data source and table formation, assess ML/agent methodology against the assignment.

## 1. Executive Conclusion

The project contains a real, reproducible ML/quant pipeline rather than only documentation:

- Level 2 trains and runs three non-trivial model families on validation data:
  - econometric AutoReg + GARCH(1,1) volatility forecast;
  - Logistic Regression classifier;
  - HistGradientBoostingClassifier;
  - agent ensemble that consumes typed model/technical signals.
- Level 5 actually scores a large universe in full mode:
  - 100 scored pairs per decision day;
  - 25 selected pairs per decision day;
  - 24 decision days in the validation run;
  - 0 invalid score rows and 0 null values in the generated score table.
- Frozen data validation is strong at the schema/hash/table level:
  - `make validate-data` passed;
  - OHLCV and instrument parquet hashes match the manifest;
  - no duplicate `(bar_start_utc, symbol)` keys;
  - no null or non-finite OHLCV values;
  - no per-symbol continuity gaps inside each listed symbol's own available date range;
  - Level 5 data proof confirms at least 100 eligible/scored pairs.

My overall audit score:

- Assignment/MVP compliance for ML and agents: **8/10**.
- Institutional ML/quant rigor: **6/10**.

Main reason for the gap: the models run correctly, but several pieces are still closer to a research assignment than a robust investment research platform. The largest gaps are provenance of the original exchange universe, limited Level 5 ML sophistication, incomplete full decision-trace persistence, and selection/documentation issues around why the Level 2 ensemble is the selected approach despite other validation rows having stronger headline metrics.

## 2. Commands Run

### 2.1 Data bundle validation

Command:

```bash
make validate-data
```

Status: **PASS**

Observed output:

```text
row_count: 158511
symbol_count: 163
min_bar_start_utc: 2021-01-01T00:00:00+00:00
max_bar_start_utc: 2025-12-31T00:00:00+00:00
eligible_count: 104
scored_count: 104
decision_cutoff_utc: 2025-07-01T00:00:00+00:00
data_sha256: 9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14
instrument_sha256: df7777139dd4106032280339818ba18179882c8e19141f374d87cb8e7bddf18b
write_policy: read_only_verify_existing_proof
```

Interpretation:

- The frozen data bundle validates against the current schema and manifest.
- The validation command is read-only after the final lock/proof stage.
- The Level 5 universe proof is sufficient for the assignment requirement of 100+ pairs.

### 2.2 Focused unit tests

Command:

```bash
uv run pytest tests/unit/test_data_layer.py \
  tests/unit/test_level2_validation.py \
  tests/unit/test_level5_validation.py \
  tests/unit/test_orchestration.py
```

Status: **PASS**

Observed result:

```text
27 passed in 24.37s
```

Coverage of this focused run:

- data validation hard gates;
- Level 2 model validation behavior;
- Level 5 scoring/monitoring behavior;
- typed agent orchestration.

### 2.3 Full validation model execution in temporary artifacts

Command: direct Python execution of:

```python
run_level_2_validation(artifacts_dir=temp_dir)
run_level_5_validation(artifacts_dir=temp_dir)
```

Status: **PASS**

Purpose:

- verify that models train and infer from the current frozen data;
- avoid overwriting committed `artifacts/`;
- inspect generated metrics, fit audit, prediction tables and score tables.

## 3. Frozen Data Source Audit

### 3.1 Declared source

From `data/README.md` and `data/manifests/ohlcv_daily_manifest.json`:

- exchange/source: Binance;
- library: CCXT;
- CCXT version in manifest: `4.5.59`;
- market type: spot;
- quote currency: USDT;
- timeframe: daily `1d`;
- requested range: 2021-01-01 through 2025-12-31;
- snapshot collection timestamp: `2026-06-20T21:50:30.099552+00:00`.

The source is appropriate for an offline educational/research assignment. It is not sufficient for institutional live execution research because it lacks order book depth, bid/ask spread history, exchange outage data and delisted market reconstruction.

### 3.2 Data tables verified

`data/processed/ohlcv_daily.parquet`:

```text
shape: (158511, 12)
columns:
bar_start_utc, bar_end_utc, symbol,
open, high, low, close, volume, dollar_volume,
exchange, market_type, timeframe
```

`data/processed/instruments.parquet`:

```text
shape: (163, 16)
columns:
symbol, base, quote, exchange, market_type, active,
first_bar_start_utc, last_bar_start_utc,
bar_count, expected_bar_count, missing_bar_count, coverage_ratio,
min_amount, min_cost, precision_amount, precision_price
```

Manifest:

```text
manifest row_count: 158511
manifest symbol_count: 163
requested_symbol_count: 180
actual stored symbols: 163
requested_symbol_exclusions: absent / length 0
download_failures: absent / length 0
```

### 3.3 Table integrity results

Observed checks:

```text
symbols: 163
duplicates on (bar_start_utc, symbol): 0
OHLCV nulls: 0 in all required columns
numeric non-finite values: 0 in open/high/low/close/volume/dollar_volume
bar_start min/max: 2021-01-01 to 2025-12-31 UTC
bar_end min/max: 2021-01-02 to 2026-01-01 UTC
coverage missing total from instruments: 0
minimum coverage_ratio: 1.0
symbols with full 2021-2025 coverage: 40
symbols with at least 365 bars: 115
```

Assessment:

- The parquet tables are internally consistent.
- `bar_end_utc = bar_start_utc + 1 day` is enforced by validation.
- OHLC sanity is enforced by validation.
- Hashes match manifest.
- The processed data is suitable for the project's historical backtest pipeline.

### 3.4 Universe proof

`artifacts/monitoring/level_5_data_pair_count_proof.json` and `universe_eligibility_full.csv` verify:

```text
eligible_count: 104
scored_count: 104
required_min_pairs: 100
large_universe_size: 120
decision_cutoff_utc: 2025-07-01T00:00:00+00:00
```

Eligibility table:

```text
shape: (163, 11)
reason counts:
eligible: 104
insufficient_history: 34
no_completed_bars_by_cutoff: 22
stable_or_fiat_base: 3
selected_for_scoring: 104
```

Assessment:

- The proof satisfies the Level 5 requirement of at least 100 eligible/scored pairs.
- The rules are deterministic and point-in-time with respect to completed bars at the cutoff.
- Ranking by trailing median dollar volume is transparent.

### 3.5 Data-source concerns

Finding D1: current universe selection has survivorship bias.

Evidence:

- Downloader selects currently active Binance spot USDT markets.
- `data/README.md` explicitly states that delisted/renamed markets are not reconstructed point-in-time.

Impact:

- Backtest universe is cleaner than what a real historical investor would have faced.
- Returns/risk may be biased upward or downward depending on omitted delistings and market churn.

Recommendation:

- Add `survivorship_bias=true` prominently to all model cards and final report sections.
- For a stronger version, store point-in-time exchange listings or a daily universe membership table.

Finding D2: 180 requested symbols versus 163 stored symbols is not fully reason-coded in the current manifest.

Evidence:

- manifest has `requested_symbol_count=180`;
- manifest has `symbol_count=163`;
- manifest has no `requested_symbol_exclusions` and no `download_failures`;
- `data/README.md` documents this as a provenance limitation of the snapshot.

Impact:

- The table is valid, but source lineage is incomplete for the 17 no-row requested candidates.

Recommendation:

- Re-freeze data only if protocol allows, or add a non-mutating provenance note to `reports/data_card.md`.
- Future freezes should persist zero-row symbols as `no_ohlcv_rows_returned`; the current downloader code already supports this field.

## 4. Level 2 Model Audit

### 4.1 Models implemented

Code paths:

- `src/crypto_hedge_fund/models/econometric.py`
- `src/crypto_hedge_fund/models/ml.py`
- `src/crypto_hedge_fund/experiments/level_2.py`
- `src/crypto_hedge_fund/features/level2.py`

Implemented model families:

- `econometric_ar_garch`:
  - AutoReg expected-return forecast;
  - `arch` GARCH(1,1) volatility forecast when available;
  - deterministic educational GARCH-style fallback otherwise.
- `ml_logistic`:
  - median imputer;
  - standard scaler;
  - Logistic Regression with `class_weight="balanced"`.
- `ml_hist_gradient_boosting`:
  - median imputer;
  - HistGradientBoostingClassifier.
- `agent_ensemble`:
  - typed signal agents and weighted aggregator.

### 4.2 Causal feature and label alignment

Level 2 features use completed daily bars and create a next-open target:

- `feature_cutoff = bar_end_utc`;
- `execution_time = bar_start_utc + 1 day`;
- target return is next-open to following-open;
- `label_observation_time = future_open_time`;
- walk-forward fit uses only rows where `label_observation_time < first_execution`.

This is the correct design for preventing same-close leakage.

### 4.3 Actual validation run results

Generated in a temporary artifact directory with `run_level_2_validation`.

Metrics rows:

```text
approaches:
technical_sma,
econometric_ar_garch,
ml_logistic,
ml_hist_gradient_boosting,
agent_ensemble
```

Selected approach:

```text
agent_ensemble
```

Fit audit:

```text
shape: (2555, 9)
status counts:
econometric_ar_garch ok: 365
ml_hist_gradient_boosting ok: 1095
ml_logistic ok: 1095
used_future_labels: 0
train_samples min/max: 1033 / 1397
```

Prediction table:

```text
shape: (1095, 35)
status counts:
econometric_ar_garch ok: 365
ml_hist_gradient_boosting ok: 365
ml_logistic ok: 365
probability range: 0.19953805853524 to 0.7855463967602443
```

Important nuance:

- Prediction table null total was `4380`.
- This is not evidence of broken predictions by itself because econometric rows and classifier rows have different applicable fields. For example, econometric rows use `expected_return`/`forecast_volatility`, while classifier rows use predictive probabilities. Still, a schema-level field applicability map should be documented to avoid confusing reviewers.

### 4.4 Level 2 validation metrics observed

Key validation rows:

```text
technical_sma:
  net_total_return: 0.4524921162
  net_sharpe: 1.1327180990
  net_max_drawdown: -0.3432799138
  net_total_cost: 23529.3701586

econometric_ar_garch:
  net_total_return: 0.0271820157
  net_sharpe: 0.5880966725
  net_max_drawdown: -0.0337827758
  net_total_cost: 37109.6731273

ml_logistic:
  net_total_return: 0.0140775439
  net_sharpe: 1.4152216101
  net_max_drawdown: -0.0027705367
  net_total_cost: 3590.5934956
  predictive_log_loss: 0.6887904714
  predictive_brier_score: 0.2478340826
  predictive_roc_auc: 0.5424866101
  predictive_pr_auc: 0.5446302637
  predictive_calibration_mae: 0.0307911307

ml_hist_gradient_boosting:
  net_total_return: 0.0283782215
  net_sharpe: 1.3534302463
  net_max_drawdown: -0.0104493750
  net_total_cost: 8799.8165205
  predictive_log_loss: 0.6899573892
  predictive_brier_score: 0.2478783863
  predictive_roc_auc: 0.5855449239
  predictive_pr_auc: 0.5579688157
  predictive_calibration_mae: 0.0548504231

agent_ensemble:
  selected_for_level_2: true
  net_total_return: 0.0281738520
  net_sharpe: 1.1103129407
  net_max_drawdown: -0.0229513844
  net_total_cost: 4019.2476422
```

Assessment:

- Logistic Regression and HGB both genuinely train and infer.
- Predictive signal is weak but non-random enough for an educational baseline:
  - Logistic ROC-AUC around 0.542;
  - HGB ROC-AUC around 0.586.
- HGB has better directional ranking than Logistic but worse calibration MAE.
- The ensemble is defensible as an agent-demonstration choice, but not as the strongest pure validation metric choice.

### 4.5 Level 2 findings

Finding M1: models train and run correctly.

Severity: pass/positive finding.

Evidence:

- all fit statuses `ok`;
- 0 future-label flags;
- prediction rows exist for all three model families;
- tests passed.

Finding M2: selected Level 2 ensemble needs stronger justification.

Severity: P1.

Evidence:

- `agent_ensemble` is selected;
- `ml_logistic` has higher validation net Sharpe than `agent_ensemble`;
- `technical_sma` has much higher validation total return but much larger drawdown;
- `ml_hist_gradient_boosting` has similar return and higher Sharpe than ensemble in this run.

Impact:

- A reviewer may interpret the selected ensemble as chosen for narrative/agent requirement rather than a fully specified validation selection rule.

Recommendation:

- Add a frozen selection rationale table:
  - primary metric;
  - risk veto thresholds;
  - tie-breakers;
  - reason for preferring ensemble despite lower Sharpe than standalone ML.
- If the assignment requires agent interaction, state explicitly that Level 2 selected model optimizes both methodology coverage and validation acceptability, not pure performance.

Finding M3: probability calibration is measured, but not a full calibration procedure.

Severity: P2.

Evidence:

- `predictive_calibration_mae` is computed;
- no explicit Platt/isotonic calibration model is fitted in `models/ml.py`.

Impact:

- Probability values should not be described as calibrated probabilities.

Recommendation:

- Either rename to raw classifier probability, or add walk-forward calibration using only historical validation folds.

Finding M4: prediction table has mixed-model nullable columns.

Severity: P2.

Evidence:

- prediction table has 1095 rows and 4380 null cells.

Impact:

- The table is valid but needs a schema note because different model families populate different fields.

Recommendation:

- Add a `field_applicability` section to model cards or artifact metadata.
- Optionally split `level_2_model_predictions.parquet` into common columns plus model-specific extension columns.

## 5. Level 5 Model/Scoring Audit

### 5.1 What Level 5 actually is

Level 5 is not a trained ML classifier/regressor. It is a deterministic cross-sectional scoring model plus agent/risk/portfolio machinery.

Code paths:

- `src/crypto_hedge_fund/features/level5.py`
- `src/crypto_hedge_fund/experiments/level_5.py`
- `src/crypto_hedge_fund/data/universe.py`
- `src/crypto_hedge_fund/portfolio/allocators.py`
- `src/crypto_hedge_fund/risk/pre_allocation.py`
- `src/crypto_hedge_fund/risk/post_allocation.py`

Scoring inputs:

- short momentum;
- long momentum;
- realized volatility;
- drawdown;
- trailing dollar-volume liquidity;
- valid history days;
- trailing valid days.

Score formula:

- z-scored momentum;
- volatility penalty;
- liquidity contribution;
- drawdown contribution;
- clipped final score in `[-1, 1]`;
- confidence from history coverage and liquidity rank.

This is a transparent quant ranking model, not classical supervised ML.

### 5.2 Actual validation run results

Generated in a temporary artifact directory with `run_level_5_validation`.

Counts:

```text
scored_count: 100
selected_count: 25
score table shape: (2400, 42)
decision days: 24
scored per decision min/max: 100 / 100
selected per decision min/max: 25 / 25
invalid score rows: 0
score table null total: 0
rebalance log shape: (24, 42)
```

Metrics:

```text
net_total_return: -0.1857549573
net_sharpe: -4.2393336418
net_max_drawdown: -0.1880493759
net_total_cost: 5216.4296529
gross_total_return: -0.1808232884
gross_sharpe: -4.1243356616
runtime_seconds: 4.8815145
peak_rss_mb: 537.25
```

Health summary:

```text
system_status: ok
eligible_count_min/max: 100 / 100
scored_count_min/max: 100 / 100
selected_count_max: 25
submitted_rebalances: 24
data_quality_invalid_count: 0
model_quality_invalid_count: 0
coverage_rate_min: 1.0
optimizer_fallback_rate: 0.8333333333
incident_count: 20
final_test_exposure: NOT_EXPOSED
```

Assessment:

- Level 5 satisfies the hard 100-pair operational requirement.
- The table formation is good: no nulls, no invalid rows, stable 100 rows per decision date.
- Performance is poor on this validation window, but the assignment does not require profitability.
- High `optimizer_fallback_rate` and `incident_count` are significant for quant review and should be explained in the final narrative.

### 5.3 Level 5 findings

Finding L5-1: large-universe scoring runs correctly.

Severity: pass/positive finding.

Evidence:

- score table `(2400, 42)`;
- 24 decision days;
- exactly 100 scored pairs per day;
- exactly 25 selected pairs per day;
- 0 invalid score rows;
- 0 null cells.

Finding L5-2: Level 5 should not be marketed as supervised ML.

Severity: P1.

Evidence:

- score is deterministic feature/ranking logic;
- no Level 5 fit object, training labels or supervised model audit exists.

Impact:

- Overclaiming "AI/ML" at Level 5 would be misleading.

Recommendation:

- Describe Level 5 as "cross-sectional quant scoring with agent/risk orchestration".
- If stronger ML is needed later, add a pooled cross-sectional supervised model trained on pre-2025 data with purged walk-forward validation.

Finding L5-3: high optimizer fallback rate needs explanation.

Severity: P1.

Evidence:

- `optimizer_fallback_rate: 0.8333333333`.

Impact:

- If the allocator frequently falls back, the realized strategy may differ from the intended optimizer.

Recommendation:

- Add per-date fallback reasons and allocator status to the report.
- Add thresholds that make fallback rate a warning/failure depending on methodology.
- Consider making inverse-volatility the explicit primary allocator if fallback is expected and acceptable.

Finding L5-4: validation window is short.

Severity: P1.

Evidence:

- Level 5 validation decision period: 2024-12-07 to 2024-12-30;
- evaluation period: 2024-12-08 to 2024-12-31.

Impact:

- 24 days is enough for mechanical feasibility but weak for statistical evidence.

Recommendation:

- Keep current window as assignment feasibility proof.
- Add a secondary non-selection diagnostic over more historical periods, clearly marked as not used for final-test selection if final lock is already in place.

## 6. Agent Architecture Audit

### 6.1 Positive findings

The project has real typed agent interactions:

- signal agents emit typed `AgentSignal`-like structures;
- orchestrator aggregates signals;
- proposals go through pre-allocation and post-allocation risk;
- agents cannot directly place orders;
- risk policies can block or move portfolios to cash;
- artifacts include representative decision traces and model cards.

This satisfies the assignment's "actual agent interaction" requirement better than a renamed function pipeline.

### 6.2 Trace persistence limitation

Finding A1: decision traces are representative/summary-oriented, not complete daily trace logs.

Severity: P2.

Observed structures:

`artifacts/monitoring/level_2_decision_trace.json`:

```text
feature_definition
predictive_metrics
provenance
representative_decision_trace
```

`artifacts/monitoring/level_5_decision_trace.json`:

```text
final_test_exposure
portfolio_protocol
provenance
rebalance_summary
representative_decision
representative_scores
```

Impact:

- A reviewer can inspect representative logic, but cannot easily replay every daily agent decision from trace alone.

Recommendation:

- Add `artifacts/monitoring/level_<n>_decision_trace.parquet` or JSONL:
  - one row per decision date and symbol/agent;
  - signal score;
  - confidence;
  - reason codes;
  - pre-risk constraints;
  - proposal;
  - post-risk approval/veto.

## 7. Data Table Formation Audit

### 7.1 OHLCV table

Status: **valid**.

Strong points:

- long-form panel is appropriate;
- timestamp semantics are explicit;
- sorted keys are enforced;
- duplicates are rejected;
- no forward/backward filling;
- `dollar_volume = close * volume` is explicitly labeled as approximation.

Limitations:

- no bid/ask spread;
- no order book depth;
- no exchange outage information;
- active-market survivorship bias;
- 17 requested symbols are not reason-coded in current manifest.

### 7.2 Instruments table

Status: **valid**.

Strong points:

- contains exchange, market type, active flag and precision/limit metadata;
- coverage values reconcile with OHLCV data;
- symbol metadata is unique;
- no missing metadata for symbols present in OHLCV.

Limitations:

- `active` is current metadata, not point-in-time metadata;
- delisting/renaming history is absent.

### 7.3 Level 2 model tables

Status: **valid but schema documentation should improve**.

Strong points:

- fit audit explicitly records `fit_cutoff`, `train_samples`, `used_future_labels`, `status`;
- prediction table includes provenance columns;
- all model families produced validation predictions.

Limitations:

- mixed model-family fields create expected nulls;
- representative trace is not a complete decision log.

### 7.4 Level 5 score tables

Status: **valid**.

Strong points:

- no nulls;
- 100 scored rows per decision day;
- top-K selection is explicit;
- per-asset caps and approved weights are included;
- provenance columns are embedded.

Limitations:

- deterministic score is not trained ML;
- fallback/incident fields need more reviewer-facing explanation.

## 8. Highest-Priority Improvements

### P0: Do not overclaim Level 5 ML

Current Level 5 is a deterministic quant scoring model. Keep that wording precise.

Concrete fix:

- update `reports/final_report.md`, model cards and notebook text to say:
  - "cross-sectional scoring";
  - "agent/risk orchestration";
  - not "trained ML model" for Level 5.

### P0: Add a selection-rationale table for Level 2

The selected ensemble is not the top row by every validation metric.

Concrete fix:

- add a table showing:
  - approach;
  - net return;
  - net Sharpe;
  - max drawdown;
  - costs;
  - chosen/not chosen;
  - reason.

### P1: Improve data provenance for requested symbols

The current manifest has 180 requested symbols and 163 stored symbols, but does not persist the 17 no-row candidates.

Concrete fix:

- in documentation now: explicitly state the limitation;
- in next data freeze: persist `requested_symbol_exclusions`.

### P1: Persist full decision traces

Representative traces are not enough for a serious audit trail.

Concrete fix:

- write full trace JSONL/parquet per level;
- preserve representative JSON as human-readable summary.

### P1: Add actual calibration or weaken wording

The project measures calibration error but does not calibrate probabilities.

Concrete fix:

- either call outputs "raw model probabilities";
- or add walk-forward Platt/isotonic calibration trained only on prior periods.

### P1: Explain Level 5 fallback/incident rates

`optimizer_fallback_rate=0.8333` and `incident_count=20` need reviewer-facing details.

Concrete fix:

- add per-date reason counts;
- document whether fallback is expected by design;
- fail validation if fallback exceeds a threshold and is not explicitly selected as methodology.

### P2: Extend Level 5 validation diagnostics

Current Level 5 validation window is short.

Concrete fix:

- add non-selection robustness diagnostics over earlier historical windows;
- keep final selection frozen and clearly mark diagnostics as post-selection health checks.

## 9. Final Auditor Opinion

The project is materially compliant with the assignment from a machine-learning, agent and data-engineering standpoint:

- models are implemented and actually train/run;
- data validation is not superficial;
- Level 5 really handles 100+ pairs in full mode;
- agent interaction is typed and connected to risk/portfolio execution;
- artifacts are reproducible and provenance-rich.

The main remaining work is not to "make the code real" because it already is. The main work is to raise the auditability and institutional clarity:

- be exact about what is ML versus deterministic scoring;
- document model selection decisions more defensibly;
- improve original universe provenance;
- persist full decision traces;
- make calibration and optimizer fallback behavior explicit.

Until these are addressed, I would accept the repository as a strong educational/research assignment submission, but I would not present it as institutional-grade ML trading research.
