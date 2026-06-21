# Technical Agent Model Card

## Responsibility

Produces deterministic technical trend and momentum scores from completed daily bars. Used in Level 2 and as part of the large-universe scoring stack.

## Features

- Lagged returns and rolling return summaries.
- Moving-average and trend indicators.
- Volatility and drawdown context from historical bars only.
- Liquidity fields where available for large-universe prioritization.

## Target

Next-period directional or ranking signal, evaluated after costs through the shared broker/ledger.

## Fit And Retrain Schedule

Rule-based; no fitted parameters beyond validation-selected windows and thresholds frozen before final-test exposure.

## Cutoffs

Features use completed bars only. Decisions execute at the next available open under the shared execution kernel.

## Validation

Validated through Stage 6 Level 2 comparison, Stage 9 large-universe validation, Stage 10 lock, Stage 11 final-test run, and the full notebook/report evidence.

## Confidence And Abstention

Confidence is derived from signal strength and data quality. Missing, stale, non-finite, or insufficient-history inputs abstain through typed reason codes.

## Trading Mapping

The agent emits typed scores only. It cannot place orders. The orchestrator, risk gates, allocator, and broker convert approved signals into target weights and fills.

## Metrics

Primary metrics are net after fees/slippage, Sharpe, drawdown, turnover, exposure, cost, and benchmark-relative performance.

## Risks And Intended Use

Intended for educational historical research. Technical signals can overfit regime-specific trends and may decay after costs.
