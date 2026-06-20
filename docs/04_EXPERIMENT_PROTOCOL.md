# 04 — Data, execution and experiment protocol

## 1. Frozen research dataset

Default study:

- one spot exchange for the primary frozen snapshot;
- quote currency: USDT;
- timeframe: daily;
- requested history: `2021-01-01` through `2025-12-31` where available;
- timezone and bar boundary: UTC;
- format: compressed long-form Parquet;
- key: `(bar_start_utc, symbol)`.

Required bar columns:

```text
bar_start_utc, bar_end_utc, symbol,
open, high, low, close, volume, dollar_volume,
exchange, market_type, timeframe
```

`dollar_volume = close * volume` may be used as an approximation and must be labeled as such.

Required instrument metadata is described in `03_REPOSITORY_LAYOUT.md`. Store the actual processed dataset, metadata and manifest in the submitted project so the default notebook can run offline.

Manifest fields include collection timestamp, adapter/library version, request parameters, actual date coverage, row/symbol counts, source, schema version and SHA-256 hashes.

### Source fallback

If the preferred exchange cannot produce the required 100+ pair full dataset:

1. keep the same adapter interface;
2. select one alternative CEX spot source for the entire primary snapshot;
3. do not silently mix exchanges;
4. update provenance and documentation;
5. keep searching until the hard Level 5 requirement can be demonstrated.

A limitation note is not a substitute for the required 100+ pair run.

## 2. Timestamp and execution convention

Exchange daily candles are commonly timestamped by bar start. Therefore:

- `bar_start_utc=t` is not the decision time;
- the bar completes at `bar_end_utc`;
- all features using that bar become available only at/after `bar_end_utc`;
- decisions execute at the next available bar open;
- positions earn the following open-to-open holding return.

For symbol `s`:

```text
feature_cutoff_t = bar_end_t
decision_time_t >= feature_cutoff_t
execution_time_t = open of bar t+1
holding_return_t = open_(t+2) / open_(t+1) - 1
```

For static or infrequent weights, the engine applies the same clock and lets holdings drift between executions.

A same-close fill using the close that created the signal is forbidden in primary results. A close-to-close convention may appear only as a labeled sensitivity check.

## 3. Universe rules

### General exclusions

Exclude deterministically:

- stablecoin/stablecoin and fiat-like bases;
- leveraged token suffixes (`UP`, `DOWN`, `BULL`, `BEAR`, etc.);
- non-spot instruments;
- impossible OHLC data;
- insufficient historical coverage;
- low trailing liquidity;
- stale or currently untradable symbols.

### Level 3 small universe

At the estimation cutoff:

1. require 12 complete prior months of valid data;
2. rank eligible assets by trailing 12-month median dollar volume or another predeclared liquidity statistic;
3. select 5–7 popular/liquid pairs without using test-period information;
4. freeze and log the selected list before test execution.

BTC and ETH may be required anchors if this rule is declared in advance; remaining assets must be selected mechanically. Avoid choosing a list based on knowledge of later winners.

### Level 5 point-in-time universe

At each rebalance date:

1. use only bars and metadata available at the decision cutoff;
2. require at least 365 prior valid bars, preferably 730 for fitted models;
3. rank by trailing 90-day median dollar volume;
4. select at least 100 eligible pairs where the full run is claimed;
5. score all selected pairs;
6. allow holdings in a smaller constrained top-K.

Downloading only currently active pairs creates survivorship bias. Document it. Do not claim a true institutional point-in-time universe without delisted-symbol history.

## 4. Data validation and missing-data policy

Automated checks:

- UTC-aware timestamps and valid bar start/end relationship;
- unique `(bar_start_utc, symbol)` key;
- sorted rows;
- finite numeric values;
- `low <= min(open, close) <= max(open, close) <= high`;
- positive prices and non-negative volume;
- no duplicate bars;
- date bounds and coverage reports;
- first/last bar per symbol;
- data and metadata hash match manifest;
- proof of at least one full-mode Level 5 date with 100+ eligible pairs.

Never forward-fill OHLCV for features or returns.

Trading/valuation policy:

- no order without a valid next-open execution price;
- a symbol missing the execution bar is blocked from new trading;
- an existing holding may be marked using the last valid price only for a short configured stale window, with a stale flag;
- after the stale limit, activate a documented freeze or conservative liquidation assumption and record it;
- do not hide delisting or stale-price effects.

## 5. Chronological splits and final-test quarantine

Default split:

| Split | Dates | Purpose |
|---|---|---|
| Train | 2021-01-01 — 2023-12-31 | fitting, preprocessing and bounded research |
| Validation | 2024-01-01 — 2024-12-31 | selecting all hyperparameters, methods and policies |
| Final test | 2025-01-01 — 2025-12-31 | frozen OOS evaluation only |

Within train/validation:

- rolling or expanding windows;
- no random shuffle;
- purge samples whose forward labels overlap a later fold;
- embargo at least equal to prediction horizon;
- refit preprocessing in each fold;
- keep searches bounded and documented.

Before any test returns are read, write `artifacts/final_test_lock.json` containing the selected choices and data/config/git hashes. Implement all five levels and create this lock first; then run the final suite together.

## 6. Features

Core causal features:

- lagged returns over 1/5/10/20 days;
- rolling mean/std and downside deviation;
- SMA/EMA ratios;
- RSI(14), MACD components and normalized ATR;
- realized volatility over 7/20/60 days;
- high-low, close-open and gap/range features;
- distance from rolling peak and rolling drawdown;
- trailing volume/dollar-volume z-scores and liquidity proxies;
- cross-sectional momentum, volatility and liquidity ranks for Level 5.

Rules:

- no centered windows;
- no backward fill;
- no global full-history normalization;
- learned transformations fit only on historical training windows;
- target columns are structurally excluded from feature inputs;
- cross-sectional features use the point-in-time eligible set only.

## 7. Targets and trading mapping

### Level 2 single-pair target

Primary classification target aligns with next-open execution:

```text
execution_open_t = open of bar t+1
future_open_t = open of bar t+2
forward_return_t = future_open_t / execution_open_t - 1
label_t = 1 if forward_return_t > estimated_trading_threshold else 0
```

The threshold reflects expected one-way entry/exit costs for the chosen holding convention plus a safety margin. Keep raw forward return for economic evaluation.

Map every model to the same target exposure scale for fair comparison, e.g. `[0, 1]` risky weight with cash as residual. Any volatility scaling is shared or explicitly separated as a risk overlay.

### Level 5 cross-sectional target

Default horizon: 5 open-to-open days, aligned with the execution delay.

```text
target_(t,s) = forward 5-day return after next-open execution
```

Overlapping labels require purging/embargo. Prefer one pooled/cross-sectional model rather than 100+ heavyweight independent models.

## 8. Models and agent interaction

### Technical strategy/agent

- SMA fast/slow crossover;
- small candidate grid;
- windows chosen on validation only;
- emits score/confidence and can abstain during insufficient warm-up.

### Econometric Agent

- AutoReg or ARIMA-family model for expected return;
- GARCH(1,1) for conditional volatility;
- refit monthly or on a validation-selected cadence;
- score can be forecast return divided by forecast volatility;
- failed fit returns neutral/abstain plus reason code, not stale optimistic output.

### ML Agent

Required classical models:

- Logistic Regression with scaling inside a pipeline;
- HistGradientBoostingClassifier or equivalent tree-based model.

Predictive metrics:

- log loss;
- Brier score;
- ROC-AUC and PR-AUC;
- calibration error/curve;
- precision/recall at the trading threshold.

These do not replace after-cost performance/risk metrics.

### Regime Agent

Uses causal realized/GARCH volatility and optional trend features to identify risk-on, risk-off or high-volatility states. It may reduce risk budget or confidence, but hard controls remain deterministic.

### Orchestrator and ensemble

- call agents with the same context/cutoffs;
- validate outputs and handle abstentions;
- normalize scores to a documented scale;
- non-negative ensemble weights sum to one;
- choose weights and thresholds on validation only;
- log contributions, disagreement and final aggregate score;
- no free-form LLM output can alter the decision.

The notebook must show at least one full interaction trace.

## 9. Portfolio experiments

### Level 3 — static 5–7 asset portfolio

Use vintage-safe validation and exactly the immediately preceding 12 months for every static allocation:

```text
validation vintage:
  select universe at 2023-12-31 using 2023 information
  estimate weights from 2023-01-01 .. 2023-12-31
  hold/evaluate candidate methods during 2024

final frozen vintage:
  select universe at 2024-12-31 using 2024 information
  estimate weights from 2024-01-01 .. 2024-12-31
  execute at the next valid open in 2025
  evaluate during 2025
```

Do not evaluate 2024 with a universe chosen using end-of-2024 popularity/liquidity.

Compare:

- equal weight;
- inverse volatility;
- minimum variance with shrinkage covariance;
- one robust method such as HRP or CVaR.

Define “optimal” in advance. Recommended interpretation:

1. each mathematical optimizer has an explicit objective and constraints;
2. the submitted portfolio method is selected on validation by a predeclared utility such as net Sharpe subject to maximum drawdown/concentration constraints;
3. ties favor lower turnover and simpler/robust methods;
4. final-test performance never selects the winner.

Show the efficient-risk trade-off and risk contributions where appropriate.

### Level 4 — dynamic small portfolio

Keep each vintage’s Level 3 universe fixed to isolate rebalancing effects. Select the validation universe at `2023-12-31` for the 2024 policy comparison; after the rule is frozen, select the final universe at `2024-12-31` for 2025. Use rolling historical estimates, normally a trailing 12-month window.

Candidate triggers:

- monthly calendar;
- absolute weight drift above 5 percentage points;
- material change in agent scores/target weights;
- volatility/risk-state trigger;
- combined OR rule.

Predeclare validation selection, for example:

```text
utility = net Sharpe
subject to max_drawdown <= threshold
and annual_turnover <= threshold
```

Tie-breaker: lower costs/turnover, then simpler policy. Freeze the selected rule before final test.

### Level 5 — dynamic 100+ pair system

Default design:

- weekly decision schedule plus risk/agent-trigger override;
- trailing 90-day point-in-time liquidity filter;
- at least 100 eligible/scored pairs in the full run;
- pooled cross-sectional score;
- priority based on expected net alpha, confidence, forecast risk and liquidity;
- top 20–30 positive net scores eligible for holdings;
- per-asset cap around 3–5%;
- cash allowed;
- volatility scaling, capacity and turnover limits;
- dynamic rebalance intent from schedule, signal change, drift or risk state.

A defensible priority score is:

```text
priority = expected_return_after_cost
           * confidence
           / max(forecast_volatility, epsilon)
           * liquidity_penalty
```

Document the exact normalization and avoid pretending it is uniquely optimal.

## 10. Cost, turnover and capacity

Base scenario, configurable:

- exchange fee: 10 bps one way;
- fixed slippage: 5 bps one way;
- stress tests: 1x, 2x and 3x cost assumptions.

At execution, using risky weights only for fee-bearing trades:

```text
delta_i = target_i - pretrade_i
gross_traded_notional_fraction = sum_i(abs(delta_i))
fixed_cost_fraction = gross_traded_notional_fraction
                      * (fee_bps + slippage_bps) / 10_000
```

Reporting turnover may include cash reconciliation:

```text
turnover = 0.5 * (
    sum_i(abs(delta_i)) + abs(delta_cash)
)
```

Examples that must be unit-tested:

- cash → asset: one unit of fee-bearing notional;
- asset → cash: one unit;
- asset A → asset B: two units;
- no change: zero.

For Level 5 include capacity diagnostics:

- assumed AUM, default USD 1,000,000;
- trailing 20-day average dollar volume;
- maximum participation, default 1%;
- reject/cap changes above capacity;
- optionally show a square-root impact scenario separately.

## 11. Performance, risk and system metrics

Every strategy/approach table includes both performance and risk measures.

Trading/performance:

- total return/ROI;
- CAGR;
- annualized volatility using 365 periods;
- Sharpe and Sortino;
- Calmar;
- maximum drawdown and duration;
- hit rate and exposure;
- turnover, number of trades/rebalances and total costs.

Risk/portfolio:

- historical VaR/CVaR 95%;
- downside deviation;
- gross/net exposure and cash;
- concentration HHI and effective holdings;
- risk contributions/correlation diagnostics;
- liquidity/capacity utilization.

System quality:

- data freshness/coverage;
- feature/prediction drift;
- calibration decay;
- agent disagreement/abstention/failure rate;
- optimizer fallback rate;
- rejected order/reconciliation count;
- runtime/memory;
- artifact/hash freshness;
- rolling OOS stability and gross-to-net degradation;
- kill-switch incidents.

## 12. Benchmarks

- single-asset levels: BTC buy-and-hold using the same execution/evaluation window;
- Level 3: static equal-weight buy-and-hold basket;
- Level 4: frozen Level 3 static portfolio and a simple calendar rebalance;
- Level 5: equal-weight eligible universe or equal-weight top-K using the same point-in-time selection and costs;
- cash at the configured risk-free rate, default zero.

Benchmarks must use the same timestamps, tradability rules and cost conventions.

## 13. Statistical validation

At minimum:

- moving-block bootstrap confidence intervals for average return and Sharpe;
- circular-shift/permutation test breaking signal-return alignment while preserving return structure better than row shuffle;
- multiple seeds for stochastic models;
- parameter sensitivity around chosen SMA, model and rebalance settings;
- results by market regime;
- gross-to-net/cost stress analysis.

Optional strengthening:

- probabilistic/deflated Sharpe or multiple-testing adjustment;
- placebo targets or lagged-signal tests.

Full mode: at least 1,000 bootstrap/permutation repetitions where practical. Fast mode: 100–200, clearly non-final.

Do not claim statistically significant alpha without after-cost evidence. Negative or inconclusive findings are valid.

## 14. Required charts/tables

- data coverage and universe count;
- price with signals/positions;
- gross/net equity vs benchmark;
- drawdown and rolling volatility/Sharpe;
- ML calibration/prediction diagnostics;
- agent contribution/disagreement example;
- static and dynamic portfolio weights;
- turnover and costs;
- risk contribution/concentration;
- Level 5 liquidity/capacity and system-health alerts;
- cross-level OOS summary with identical period/cost labels.
