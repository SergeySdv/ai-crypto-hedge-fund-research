# Experiment Protocol

## Split Discipline

The project uses train/validation work before final-test exposure. Final-test
results are frozen and reported honestly; they are not used to tune strategies.

Default final-test period:

```text
2025-01-01 through 2025-12-31
```

Level 3 uses exactly a trailing 12-month final estimation window:

```text
estimate on 2024 -> hold out-of-sample in 2025
```

## No-Leakage Rules

- Features use only completed bars.
- Decisions execute at the next available open.
- No shuffled time splits.
- No future universe membership.
- No final-test tuning of models, thresholds, assets, risk limits, benchmarks, or
  rebalance policy.
- Failed models and infeasible allocations produce explicit reason codes instead
  of silent methodological fallbacks.

## Level Protocols

### Level 1

Single-symbol BTC/USDT SMA baseline. The point is not alpha quality; it proves
that a one-symbol strategy uses the shared broker, ledger, costs, metrics, and
artifact stack.

### Level 2

BTC/USDT typed-agent ensemble:

- technical indicators;
- AutoReg expected-return model;
- GARCH(1,1) conditional volatility;
- Logistic Regression;
- HistGradientBoostingClassifier;
- regime context;
- ensemble aggregation and decision trace.

### Level 3

Static portfolio over a small selected universe. Allocation methods include:

- equal weight;
- inverse volatility;
- minimum variance with covariance shrinkage;
- robust downside/CVaR-style method.

The final estimation window is 2024, and the portfolio is evaluated out of sample
in 2025.

### Level 4

Dynamic small-universe rebalancing. The portfolio can rebalance based on calendar,
drift, signal, risk, and cost triggers. Rebalance decisions are logged.

### Level 5

Large-universe dynamic portfolio. The final run must score at least 100 eligible
pairs. Current final proof:

- eligible pairs: 120;
- scored pairs: 120;
- selected holdings: 25.

The benchmark is a broker-costed equal-weight top-K universe basket, which makes
cost and execution assumptions comparable to the strategy path.

## Result Interpretation

Net results after fees and slippage are primary. Gross results and benchmarks are
supporting diagnostics. Negative or weak final-test results are retained as valid
research outcomes rather than hidden or replaced.
