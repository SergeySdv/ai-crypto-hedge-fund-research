# Final Report - AI Crypto Hedge Fund Research MVP

## Scope and framing

This repository is an educational historical research system for an AI-agent crypto
portfolio workflow. It is not a profitability claim, not investment advice and not an
enabled live trading bot. The MVP is long-only, unlevered, spot-only, daily-bar and
USDT-cash based.

## Final-test lock and exposure

- Final-test exposure: `EXPOSED`
- Accepted lock SHA-256: `dab407601cbaf8198361e5e3d074260546ed4bbab4c4be2555248b246631308b`
- Lock path: `artifacts/final_test_lock.json`
- Final-test artifact directory: `artifacts/final_test/dab407601cba/`
- Final period: `2025-01-01` through `2025-12-31`
- Locked git commit: `394d146523445ed53c978ade1033cc7870237a8f`
- Runner git commit: `6aad82116feb26f83b7658414207e03371e07864`
- Runner source dirty during Stage 11 final suite: `True`
- Data hash: `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`
- Validation-selected config hash: `3f2dd08bbec595d6233852bfc94de6eae0a2cdb91d6aeec1f408afbbd10046cf`
- Generated final config hash: `c6c79b974e7c46f4a01781fb8e2b1a96304e1c3f639a10f38fd9a0d2b1522fc6`

The final-test suite is already exposed. Stage 12 did not rerun final-test experiments
or alter methodology; it reads committed Stage 11 artifacts.
Stage 14 Worker B made only reviewer-facing transparency edits to this notebook,
report and deck. It did not rerun `make final-test`, retune any method, or modify
the frozen lock, final-test artifacts, validation-selected config or strategy code.

## Data, execution and costs

- Timestamp convention: daily bars are UTC bar-start records; completed-bar features
  execute at the next available open.
- Cost convention: fee-bearing notional is risky-asset notional actually traded.
- One-way fee: `10.0` bps.
- One-way slippage: `5.0` bps.
- Initial capital: `$1,000,000`.
- Risk-free rate: `0.0`.

Event order is semantic, not inferred from equal-looking daily timestamps:
completed source bar at `t` -> features become available after the bar closes ->
decision/order scheduling -> execution at the next open `t+1` -> PnL begins after
execution. For the Level 2 supervised target:

```text
label_t = 1[open(t+2) / open(t+1) - 1 > threshold_return]
threshold_return = (fee_bps + slippage_bps + safety_margin_bps) / 10000 = 0.0020
```

This is not a close-to-close target and not same-bar execution.

## Level 2 model implementation transparency

The Level 2 implementation is a single BTC/USDT experiment with deterministic
technical, econometric, ML and ensemble agents sharing the same data, costs,
next-open execution, risk and ledger path.

| Component | Exact implementation |
| --- | --- |
| `technical_sma` | deterministic SMA crossover, Level 2 windows fast `10`, slow `50`; no supervised target |
| `econometric_ar_garch` | `statsmodels.tsa.ar_model.AutoReg` expected-return forecast plus GARCH(1,1) conditional volatility via `arch.arch_model` when available; deterministic educational fallback otherwise |
| `ml_logistic` | `SimpleImputer(strategy="median")` -> `StandardScaler()` -> `sklearn.linear_model.LogisticRegression(max_iter=500, random_state=seed, class_weight="balanced")` |
| `ml_hist_gradient_boosting` | `SimpleImputer(strategy="median")` -> `sklearn.ensemble.HistGradientBoostingClassifier(max_iter=60, learning_rate=0.05, max_leaf_nodes=15, random_state=seed, l2_regularization=0.01)` |
| `agent_ensemble` | deterministic aggregation over SMA, AR/GARCH, logistic and HGB typed signals; frozen component weights `0.25` each, confidence-weighted over active non-abstaining agents |

The ML feature set contains exactly these 20 causal columns:
`open_return_1d`, `close_return_1d`, `return_5d`, `return_10d`,
`return_20d`, `sma_ratio_10_50`, `ema_ratio_12_26`, `rsi_14`, `macd`,
`macd_signal`, `atr_14_norm`, `realized_vol_7`, `realized_vol_20`,
`realized_vol_60`, `range_norm`, `close_open_return`, `gap_return`,
`drawdown_60`, `volume_z_20`, `dollar_volume_z_20`.

Training cadence is monthly expanding walk-forward for both ML models and
`daily_causal` expanding refit for the econometric agent. Seeds `[7, 42, 137]`
are used as robustness evidence; the persisted trading artifacts use the primary
seed. The validation fit audit contains `2555` rows and `0` future-label flags;
the final-test fit audit contains `2548` rows and `0` future-label flags.
Invalid, stale or non-finite agent inputs fail closed through reason codes and
zero confidence rather than placing orders.

## Validation selection before final-test evidence

The frozen choices were made before final-test exposure. Better final-test
alternatives observed afterward are not eligible for reselection.

| Level | Validation evidence and frozen selection |
| --- | --- |
| 1 | SMA baseline parameters were frozen on validation as the transparent single-asset baseline. |
| 2 | `agent_ensemble` was frozen as the assignment-representative multi-agent candidate. It was **not** the maximum validation-return or maximum validation-Sharpe row: validation `technical_sma` had higher net return, and `ml_logistic` had higher Sharpe. |
| 3 | `cvar_downside` had the highest validation net Sharpe (`1.70`) under the drawdown/turnover selection rule. |
| 4 | `calendar_monthly` was selected because higher-return drift/signal policies violated the turnover constraint (`9.32` vs limit `6.0`). |
| 5 | `large_universe_dynamic` is a deterministic cross-sectional scoring policy: point-in-time 100+ universe, top 25, max 5% weight, inverse-volatility allocation, weekly calendar plus drift/signal/risk triggers. It is not a fitted Level 5 classifier or regressor. |

## Level 2 robustness and predictive evidence

The existing robustness artifact is validation-only and statistically
inconclusive. It does not establish robust alpha:

- Moving-block bootstrap: `1000` repetitions, block length `14`, selected
  validation Sharpe 95% CI `[-1.049, 3.020]`.
- Circular-shift randomization: `1000` repetitions, observed score/forward-return
  correlation `-0.0177`, two-sided p-value `0.6823`.
- Multiple ML seeds recorded: `[7, 42, 137]`; first seed drives persisted trading
  artifacts.

Predictive metrics are reported separately from trading metrics. On the final
test, logistic regression had ROC-AUC `0.515` and PR-AUC `0.501`; HGB had
ROC-AUC `0.497` and PR-AUC `0.453`. The Level 2 ensemble reduced downside
relative to BTC in 2025, but the evidence does not prove forecasting skill.

## Final-test selected results

| Level | Selected result | Net return | Net Sharpe | Max drawdown | Total costs | Benchmark |
| --- | --- | --- | --- | --- | --- | --- |
| Level 1 | SMA baseline | -7.4% | -0.17 | -18.5% | $8,906 | -5.4% |
| Level 2 | agent_ensemble | -0.6% | -0.52 | -1.4% | $1,600 | -5.4% |
| Level 3 | cvar_downside | -18.0% | -0.02 | -45.2% | $1,492 | -25.4% |
| Level 4 | calendar_monthly | -4.1% | -0.88 | -9.1% | $3,584 | -9.3% |
| Level 5 | large_universe_dynamic | -28.0% | -0.22 | -42.2% | $110,939 | -5.4% |

Net after fees and slippage is primary. Several selected strategies underperformed
their benchmark in the exposed final year; those are research findings, not failures
to be hidden.

Final-test alternatives that happened to perform better remain post-exposure
diagnostics only. In particular, Level 2 HGB returned `+0.02%` net versus the
selected ensemble's `-0.60%`; Level 3 minimum variance returned `+0.90%` net
versus selected `cvar_downside`; and Level 4 drift/signal policies returned
`+3.85%` net versus selected `calendar_monthly`. These comparisons show that the
validation-selected choices did not generalize cleanly.

## Level 5 proof

- Eligible pairs: `120`
- Scored pairs: `120`
- Selected holdings: `25`
- Runtime: `75.2` seconds.
- Peak RSS: `727.3` MiB.
- Proof artifact: `artifacts/final_test/dab407601cba/monitoring/level_5_pair_count_proof.json`

Level 5 is best read as a scalability and portfolio-control demonstration, not
as a profitable large-universe strategy. It scored a deterministic factor blend
using 20/60-day momentum, 60-day realized volatility, 90-day drawdown, trailing
dollar-volume liquidity and valid-history counts. The score is clipped to
`[-1, 1]`; no Level 5 fitted ML model is present.

Economic diagnosis from frozen 2025 artifacts:

- Submitted rebalances: `364`; fills: `8727`.
- Fee-bearing order notional: about `$73.96M` on `$1M` initial AUM.
- Total transaction costs: `$110,939`; reported turnover: `49.24`.
- Gross Level 5 return was already negative (`-18.62%`); net return fell to
  `-27.99%`.
- Approval actions: `312` approve, `52` cash, `1` prior weights.
- Optimizer/risk fallback evidence: validation health summary records
  `optimizer_fallback_rate=0.8333` with `20` incidents; final-test health
  summary records `optimizer_fallback_rate=0.1452` with `53` incidents. In
  this artifact schema the field is the share of rebalance decisions whose
  post-allocation approval action was not `approve`, not proof of a numerical
  optimizer crash. The requested Level 5 allocator was `inverse_volatility`;
  fallback actions were explicit risk/rebalance controls: validation moved
  `20` of `24` decisions to cash under `volatility_limit`, while final test
  moved `52` decisions to cash and held prior weights once.
- Full-cash days: `52`; average risky exposure `85.35%`; average cash weight
  `14.65%`; average nonzero risky holdings `21.44`.

The failure mode was not inability to handle 100+ pairs or extreme concentration.
Frequent score changes and rebalances created large costs while gross performance
was also negative.

## Agent interaction trace

The notebook displays a readable Level 2 trace from agent outputs to aggregate signal,
portfolio proposal and risk approval. The committed trace shows SMA, econometric,
logistic-regression and gradient-boosting agents emitting typed scores/confidence with
cutoffs and reason codes. The aggregate signal was negative for BTC/USDT on the shown
decision, so the approved portfolio was cash with reason code `ok`.

## Monitoring and fail-safes

The final Level 5 health summary reports system status
`ok`, eligible/scored count ranges
`100`-`120`,
and `53` monitoring incidents.
Demonstrated fail-safe scenarios include
`["kill_switch_cash_schedule_unit_test", "volatility_limit_cash_approval", "invalid_feature_alert_path", "weight_reconciliation_post_risk"]`.

## Artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| artifacts/final_test_lock.json | dab407601cbaf8198361e5e3d074260546ed4bbab4c4be2555248b246631308b |
| artifacts/final_test/dab407601cba/final_test_suite_summary.json | 759e6051f243f5ef2bb5aacaeaa7c5f1a5158f153d71b05cd3ad9cd49d0adf1e |
| artifacts/final_test/dab407601cba/monitoring/level_5_pair_count_proof.json | df01221bb763ebbf5c20b50158716d4130ea1dff4b233f3b76248f5708278f93 |
| artifacts/final_test/dab407601cba/monitoring/health_summary.csv | 995eaf5b4107b7580cbd5773d30571c1532646086423f3c18302ec6db4602e5f |
| artifacts/final_test/dab407601cba/metrics/level_1.csv | b9085ec8cac78d2c0d1e25d71d07f74b095cf2a72409f04d597a100901d92886 |
| artifacts/final_test/dab407601cba/metrics/level_2.csv | d45ce4a931d6d1319b1c6da7441dbc6286c980f7fc8abe50b246df037e3b65b1 |
| artifacts/final_test/dab407601cba/metrics/level_3.csv | c0ec6ccceb579f7ff54dc392bd203be82061986428e930be8e4f3eeac44b2672 |
| artifacts/final_test/dab407601cba/metrics/level_4.csv | 065e8f4244fe1ccfccc8955351b0de21be82ee4865fe053fb72f54d8703a74e6 |
| artifacts/final_test/dab407601cba/metrics/level_5.csv | 86a11b90ba78398132ba4e91fe19eab9be509f2dae6ade6ee8e034d515f18495 |

## Command evidence

The Stage 12 implementation report contains exact command logs for the required
verification commands. Reviewer-facing commands are:

```bash
uv sync --frozen
make lint
make test
make notebook-fast
make notebook-full
make report
make presentation
```

After the pretest/final lock exists, `make validate-data` preserves the
lock-covered `artifacts/monitoring/level_5_data_pair_count_proof.json` hash and
writes fresh post-lock data-validation candidates only to ignored
`artifacts/monitoring/data_validation_*_latest.*` files. `make notebook-full`
executes the reviewer narrative over committed frozen final artifacts; it does
not rerun `make final-test`, because final-test results are already exposed.

## Known limitations

- Active Binance/CCXT market snapshot introduces survivorship and delisting bias.
- Daily-bar volume is a liquidity/capacity proxy; no order-book depth or spread model
  is included.
- Level 5 validation 100-pair evidence has a short late-December 2024 validation
  window, though the final-test full run scored 120 pairs.
- Risk behavior can be cash-heavy under volatility and turnover constraints.
- Level 5 benchmark is BTC-normalized, not a fully investable equal-weight dynamic
  benchmark.
- Stage 11 final artifacts record dirty runner-source provenance because the frozen
  final suite was run before committing the runner implementation and broker defect fix.
- Stage 11 final-test summary/evidence JSON files are preserved byte-for-byte,
  including historical local runner paths as provenance strings. Stage 14 provides
  a separate portable repo-relative view at
  `reports/stage_14/final_test_suite_summary_portable.json`; clean-clone release
  commands do not depend on the preserved local paths.

## Publication reminder

The human owner must publish or verify the public GitHub/GitLab URL; this agent cannot
confirm repository visibility outside the local checkout.
