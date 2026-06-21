# Stage 14 Model Transparency And Notebook Compliance Context

Generated from the current local repository state without changing, retraining,
retuning or reselecting any frozen methodology. Final-test artifacts are already
exposed and must be treated as evidence only.

## Executive Finding

The repository contains substantive model and validation implementation in `src/`
and validation/final artifacts under `artifacts/`. The final notebook, however,
is currently a reporting notebook: it imports `load_stage12_context()` and prints
committed artifact tables. It does not visibly demonstrate feature construction,
target definition, model fitting/loading, prediction generation, validation
selection, robustness charts or backtest invocation.

This means the codebase has stronger model evidence than the notebook exposes.
Reviewer-facing compliance should be improved by surfacing the existing evidence
in the notebook and deck without changing any frozen choices after final-test
exposure.

## Key Source Files And Hashes

| Item | Path | SHA-256 |
|---|---|---|
| ML implementation | `src/crypto_hedge_fund/models/ml.py` | `4e6b43d7d8e7823573f491c684fcffbd8252fe21250890bcc0fdd01e1c55a04a` |
| Econometric implementation | `src/crypto_hedge_fund/models/econometric.py` | `0757b4715804e44af351d88c96d3dcc51e6f41dc95a796fa9f5b122772bd3c52` |
| Level 2 features/target | `src/crypto_hedge_fund/features/level2.py` | `66d4d9ddd5dfc8a0217ea679932544a0a9a2a3b84f22af3da415b31367e8b367` |
| Level 5 scoring | `src/crypto_hedge_fund/features/level5.py` | `d6a4a89380383750ab0b310f70fedd642dd96f3cdbaaf0de1839c62e50669682` |
| Validation-selected config | `configs/validation_selected.yaml` | `3f2dd08bbec595d6233852bfc94de6eae0a2cdb91d6aeec1f408afbbd10046cf` |
| Accepted final lock | `artifacts/final_test_lock.json` | `dab407601cbaf8198361e5e3d074260546ed4bbab4c4be2555248b246631308b` |
| Level 2 prediction artifact | `artifacts/monitoring/level_2_model_predictions.parquet` | `194eb028f22ce8dcf23d48c99339f2bf745918904f9459f679de292d6097f4fe` |
| Level 2 fit audit | `artifacts/monitoring/level_2_fit_audit.parquet` | `106208e23ad6202214412f6ff3de159793a5496e2cea6c7f1db95b3322451ce3` |
| Level 2 robustness | `artifacts/monitoring/level_2_robustness.json` | `d1edeb2006c5fec107189069dba3d7542a11c54653e60a1b97f59a97d2e7f12e` |
| Final Level 2 metrics | `artifacts/final_test/dab407601cba/metrics/level_2.csv` | `d45ce4a931d6d1319b1c6da7441dbc6286c980f7fc8abe50b246df037e3b65b1` |
| Final Level 5 pair proof | `artifacts/final_test/dab407601cba/monitoring/level_5_pair_count_proof.json` | `df01221bb763ebbf5c20b50158716d4130ea1dff4b233f3b76248f5708278f93` |

## Model Inventory

### `technical_sma`

- Type: deterministic SMA crossover signal agent.
- Source: `src/crypto_hedge_fund/strategies/sma.py`; Level 2 wiring in `src/crypto_hedge_fund/experiments/level_2.py`.
- Features: completed-bar close history; SMA fast/slow windows.
- Frozen Level 1 windows: fast `30`, slow `100`.
- Frozen Level 2 windows: fast `10`, slow `50`.
- Target/prediction: rule-based trend score, not fitted supervised target.
- Signal mapping: typed `AgentSignal` with score/confidence; positive score can map to risky BTC/USDT exposure through shared risk/allocator path.
- Final-test Level 2 result: `-7.94%` net return, Sharpe `-0.38`, MDD `-18.88%`.

### `econometric_ar_garch`

- Type: AutoReg expected-return forecast plus GARCH(1,1) conditional volatility.
- Libraries: `statsmodels.tsa.ar_model.AutoReg`; `arch.arch_model` when available, deterministic fallback otherwise.
- Source: `src/crypto_hedge_fund/models/econometric.py`; prediction table generation in `src/crypto_hedge_fund/experiments/level_2.py`.
- Features: historical completed-bar open returns.
- Target/proxy: one-step expected return and return/risk score; probability is `0.5 + score / 2`.
- Fit window: expanding causal history with labels observed before execution.
- Cadence: `daily_causal`.
- Validation fit audit: 365 unique econometric fit cutoffs; 0 future-label flags.
- Final-test Level 2 result: `-3.68%` net return, Sharpe `-1.41`, MDD `-4.08%`.
- Final-test predictive evidence: directional accuracy `0.510989`, coverage `1.0`.

### `ml_logistic`

- Type: supervised binary classifier.
- Library/class: `sklearn.linear_model.LogisticRegression`.
- Pipeline: `SimpleImputer(strategy="median")` -> `StandardScaler()` -> `LogisticRegression(max_iter=500, random_state=seed, class_weight="balanced")`.
- Source: `src/crypto_hedge_fund/models/ml.py`.
- Features: 20 Level 2 causal columns:
  `open_return_1d`, `close_return_1d`, `return_5d`, `return_10d`,
  `return_20d`, `sma_ratio_10_50`, `ema_ratio_12_26`, `rsi_14`,
  `macd`, `macd_signal`, `atr_14_norm`, `realized_vol_7`,
  `realized_vol_20`, `realized_vol_60`, `range_norm`,
  `close_open_return`, `gap_return`, `drawdown_60`, `volume_z_20`,
  `dollar_volume_z_20`.
- Target: `label = 1` if `open(t+2) / open(t+1) - 1 > threshold_return`.
- Threshold: `(fee_bps + slippage_bps + safety_margin_bps) / 10000`; with defaults `0.0020`.
- Horizon: one open-to-open day after next-open execution.
- Fit protocol: monthly expanding walk-forward; available rows require `label_observation_time < first_execution`.
- Seeds: `[7, 42, 137]`; persisted trading predictions use first seed and record seed-count evidence.
- Validation prediction stats: 365 rows, probability min/mean/max `0.3617 / 0.4877 / 0.6786`.
- Final-test predictive metrics: log loss `0.689481`, Brier `0.248092`, ROC-AUC `0.515371`, PR-AUC `0.501033`, calibration MAE `0.087479`, positive rate `0.445055`.
- Final-test Level 2 result: `-0.36%` net return, Sharpe `-0.60`, MDD `-0.59%`.

### `ml_hist_gradient_boosting`

- Type: supervised binary classifier.
- Library/class: `sklearn.ensemble.HistGradientBoostingClassifier`.
- Pipeline: `SimpleImputer(strategy="median")` -> `HistGradientBoostingClassifier(max_iter=60, learning_rate=0.05, max_leaf_nodes=15, random_state=seed, l2_regularization=0.01)`.
- Source: `src/crypto_hedge_fund/models/ml.py`.
- Features, target, threshold and horizon: same as `ml_logistic`.
- Fit protocol: monthly expanding walk-forward; no shuffled split.
- Validation prediction stats: 365 rows, probability min/mean/max `0.1995 / 0.4395 / 0.7855`.
- Final-test predictive metrics: log loss `0.705736`, Brier `0.255926`, ROC-AUC `0.496883`, PR-AUC `0.452545`, calibration MAE `0.079178`, positive rate `0.445055`.
- Final-test Level 2 result: `+0.02%` net return, Sharpe `+0.02`, MDD `-1.28%`.

### `agent_ensemble`

- Type: deterministic aggregator over typed agent outputs.
- Source: `src/crypto_hedge_fund/agents/aggregate.py`, `src/crypto_hedge_fund/agents/orchestrator.py`, Level 2 wiring in `src/crypto_hedge_fund/experiments/level_2.py`.
- Components: SMA, econometric AR/GARCH, logistic regression, HGB classifier.
- Frozen weights: equal weights `0.25` each.
- Aggregation: non-negative configured weights multiplied by agent confidence, normalized over active non-abstaining agents; disagreement recorded.
- Abstention/fail-safe: invalid/non-finite/stale outputs produce explicit reason codes and zero-confidence signals.
- Validation selection evidence: selected on 2024 validation in `artifacts/metrics/level_2.csv`, although the final notebook does not currently show the validation-selection table.
- Final-test Level 2 result: `-0.60%` net return, Sharpe `-0.52`, MDD `-1.38%`.

### Level 5 pooled/cross-sectional scoring

- Type: vectorized deterministic cross-sectional factor score, not a fitted ML model.
- Source: `src/crypto_hedge_fund/features/level5.py`; Level 5 dynamic portfolio in `src/crypto_hedge_fund/experiments/level_5.py`.
- Features: 20-day and 60-day momentum, 60-day realized volatility, 90-day drawdown, trailing mean/median dollar volume, valid-history counts.
- Score formula: z-scored momentum minus volatility penalty plus liquidity and drawdown terms, clipped to `[-1, 1]`.
- Confidence: blend of history confidence and liquidity rank.
- Selection: point-in-time universe, top `25`, max weight `0.05`, inverse-volatility allocator.
- Rebalance: weekly calendar plus drift/signal/risk triggers through shared `DynamicRebalancePolicy`.
- Final-test proof: 120 eligible/scored pairs, 25 selected, runtime `75.24s`, peak RSS `727.30 MiB`.
- Final-test result: `-28.0%` net return, Sharpe `-0.22`, MDD `-42.17%`, total costs `$110,938.85`.

## Level 2 Validation Evidence

Validation metrics from `artifacts/metrics/level_2.csv`:

| Approach | Selected | Net return | Net Sharpe | MDD | Cost | Turnover | Predictive notes |
|---|---:|---:|---:|---:|---:|---:|---|
| technical_sma | no | `+45.25%` | `1.13` | `-34.33%` | `$23,529` | `13.38` | trading-only |
| econometric_ar_garch | no | `+2.72%` | `0.59` | `-3.38%` | `$37,110` | `24.18` | directional accuracy `0.501` |
| ml_logistic | no | `+1.41%` | `1.42` | `-0.28%` | `$3,591` | `2.37` | ROC-AUC `0.542`, PR-AUC `0.545` |
| ml_hist_gradient_boosting | no | `+2.84%` | `1.35` | `-1.04%` | `$8,800` | `5.77` | ROC-AUC `0.586`, PR-AUC `0.558` |
| agent_ensemble | yes | `+2.82%` | `1.11` | `-2.30%` | `$4,019` | `2.64` | selected frozen approach |

Fit/prediction audit:

- Prediction artifact rows: `1095`.
- Fit-audit rows: `2555`.
- Refit frequencies: econometric `daily_causal`; both ML models `monthly`.
- Unique fit cutoffs: econometric `365`; each ML model `12`.
- Future-label flags: `0`.
- Train samples per model: min `1033`; max `1397` for econometric, `1368` for ML.

Robustness artifact:

- Moving block bootstrap: `1000` repetitions, block length `14`.
- Bootstrap Sharpe 95% CI for selected Level 2 validation: `[-1.049, 3.020]`.
- Circular-shift randomization: `1000` repetitions.
- Observed score/forward-return correlation: `-0.0177`.
- Two-sided p-value: `0.6823`.
- Multiple seeds recorded: `[7, 42, 137]`; first seed drives persisted trading artifacts.

## Validation Selection Context

### Level 2

The frozen selected approach is `agent_ensemble`. The validation table above shows
it did not have the highest validation net return or Sharpe; `technical_sma` was
much higher. The repository appears to have frozen the ensemble as the assignment
representative multi-agent approach, not strictly the max validation-return
approach. This should be explained explicitly to avoid the appearance of arbitrary
selection.

### Level 3

Validation metrics from `artifacts/metrics/level_3.csv`:

| Method | Selected | Net return | Net Sharpe | MDD | Cost |
|---|---:|---:|---:|---:|---:|
| equal_weight | no | `+128.15%` | `1.68` | `-36.33%` | `$1,492.50` |
| inverse_volatility | no | `+121.84%` | `1.67` | `-35.16%` | `$1,492.50` |
| minimum_variance | no | `+111.35%` | `1.65` | `-32.80%` | `$1,492.50` |
| cvar_downside | yes | `+126.10%` | `1.70` | `-34.71%` | `$1,492.50` |

Selection logic in code: max validation `net_sharpe`, subject to drawdown
constraint, then lower turnover and method order. This supports frozen
`cvar_downside` despite poorer final-test performance than minimum variance.

### Level 4

Validation metrics from `artifacts/metrics/level_4.csv`:

| Policy | Selected | Net return | Net Sharpe | MDD | Cost | Turnover |
|---|---:|---:|---:|---:|---:|---:|
| static_level3_benchmark | no | `+126.10%` | `1.70` | `-34.71%` | `$1,492.50` | `0.995` |
| calendar_monthly | yes | `+3.35%` | `0.48` | `-6.55%` | `$2,762.71` | `1.82` |
| drift_monthly | no | `+55.08%` | `1.51` | `-22.84%` | `$13,040.41` | `9.32` |
| signal_risk_monthly | no | `+55.08%` | `1.51` | `-22.84%` | `$13,040.41` | `9.32` |

Selection logic in code: dynamic policy max validation `net_sharpe` subject to
max drawdown `0.25` and annual turnover `6.0`; tie-breaker lower turnover then
policy order. `drift_monthly` and `signal_risk_monthly` violate the turnover
constraint, supporting `calendar_monthly`.

### Level 5

Frozen policy: full mode, point-in-time 120/100 scored universe, top 25, max
weight 5%, inverse-volatility allocation, weekly calendar and score-change
rebalance threshold `0.10`. This is a deterministic factor scoring policy. There
is no fitted Level 5 classifier/regressor in the current implementation.

## Final-Test Context

Final metrics from `artifacts/final_test/dab407601cba/`:

| Level | Selected result | Net return | Net Sharpe | MDD | Total costs | Benchmark |
|---|---|---:|---:|---:|---:|---:|
| 1 | SMA baseline | `-7.44%` | `-0.17` | `-18.47%` | `$8,906` | `-5.42%` |
| 2 | agent_ensemble | `-0.60%` | `-0.52` | `-1.38%` | `$1,600` | `-5.42%` |
| 3 | cvar_downside | `-17.98%` | `-0.02` | `-45.24%` | `$1,492` | `-25.41%` |
| 4 | calendar_monthly | `-4.05%` | `-0.88` | `-9.13%` | `$3,584` | `-9.33%` |
| 5 | large_universe_dynamic | `-27.99%` | `-0.22` | `-42.17%` | `$110,939` | `-5.44%` |

Important final-test comparisons that must not be used for re-selection:

- Level 2 HGB final-test net return was `+0.02%`, better than selected ensemble `-0.60%`.
- Level 3 minimum variance final-test net return was `+0.90%`, better than selected `cvar_downside`.
- Level 4 drift/signal policies final-test net return was `+3.85%`, better than selected `calendar_monthly`.

These are not methodology-change reasons after final exposure. They are evidence
that the validation-selected policies did not generalize cleanly and should be
explained as such.

## Level 5 Economics Diagnosis

Final-test Level 5 diagnostics:

- Eligible/scored max: `120`.
- Selected max: `25`.
- Submitted rebalances: `364`.
- Fills: `8727`.
- Fee-bearing order notional: about `$73.96M` on `$1M` initial AUM.
- Total transaction costs: `$110,938.85`.
- Reported turnover metric: `49.24`.
- Rebalance expected-turnover sum: `91.63`.
- Approval actions: `312` approve, `52` cash, `1` prior weights.
- Full-cash days: `52 / 365`.
- Average risky exposure: `85.35%`.
- Average cash weight: `14.65%`.
- Average nonzero risky holdings: `21.44`; max `25`.
- Non-cash effective N average: about `23.41`.

Interpretation: the main economic failure is not lack of pair-count scalability or
extreme concentration. The policy scored 100+ pairs and usually held a diversified
top-K basket, but signal changes triggered very frequent turnover. Costs consumed
about 11.1% of initial capital, while the gross Level 5 return was already negative
at `-18.62%`; net fell to `-27.99%`.

## Notebook Compliance Findings

Notebook structure:

- File: `notebooks/ai_crypto_hedge_fund.ipynb`.
- Cells: `24` total; `11` code; `13` markdown.
- Outputs: all code-cell outputs are text streams.
- The only package execution entry point used is `load_stage12_context()`.

Notebook does not contain:

- `fit(`.
- `predict_proba`.
- `LogisticRegression`.
- `HistGradientBoostingClassifier`.
- `build_level2_feature_frame`.
- `walk_forward_ml_predictions`.
- `matplotlib` or image display.

Notebook currently shows:

- selected final-test rows;
- hashes and lock context;
- Level 5 counts and health summary;
- representative agent trace table;
- per-level artifact metrics tables.

Notebook currently does not visibly show:

- exact Level 2 features and target formula in executable form;
- representative model fitting or verified frozen model loading;
- ML predictive metrics table as a dedicated diagnostic section;
- validation-selection tables explaining frozen choices before 2025 exposure;
- robustness table/chart beyond text narrative;
- equity/drawdown/turnover/cost visualizations;
- Level 5 cost/turnover/cash/utilization diagnosis.

## Existing Evidence That Should Be Surfaced In Notebook

- Source-level features and target: `src/crypto_hedge_fund/features/level2.py`.
- Source-level ML model config: `src/crypto_hedge_fund/models/ml.py`.
- Source-level econometric config: `src/crypto_hedge_fund/models/econometric.py`.
- Fit audit: `artifacts/monitoring/level_2_fit_audit.parquet`.
- Predictions: `artifacts/monitoring/level_2_model_predictions.parquet`.
- Robustness: `artifacts/monitoring/level_2_robustness.json`.
- Validation metrics: `artifacts/metrics/level_2.csv`, `level_3.csv`, `level_4.csv`, `level_5.csv`.
- Final metrics: `artifacts/final_test/dab407601cba/metrics/*.csv`.
- L5 pair proof: `artifacts/final_test/dab407601cba/monitoring/level_5_pair_count_proof.json`.
- L5 scores/logs: `artifacts/final_test/dab407601cba/monitoring/level_5_universe_scores.parquet`, `level_5_rebalance_log.parquet`.

## Suggested Stage 14 Report Sections

1. State final-test quarantine: no methodology changes after exposed final test.
2. Present exact model inventory table from this context.
3. Show Level 2 feature list and target formula.
4. Show fit-audit leakage proof and retraining cadence.
5. Show ML predictive metrics separately from trading metrics.
6. Show validation-selection tables for Levels 2-5.
7. Show final-test tables only after validation evidence.
8. Explain why selected methods underperformed alternatives on final test without reselecting.
9. Add L5 economics diagnosis: turnover, costs, cash days, exposure, capacity.
10. Declare notebook compliance gap: existing notebook is artifact-reporting, not currently self-contained technical demonstration.

## Commands Used For This Context

- `rg --files` inventory.
- `sed`/`rg` source inspection.
- `uv run python` read-only artifact summaries.
- `shasum -a 256` for source/artifact hashes.

No test, validation, notebook, presentation, training or final-test command was
run during this context-gathering step.
