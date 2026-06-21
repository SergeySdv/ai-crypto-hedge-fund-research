# Econometric Agent Model Card

## Responsibility

Provides expected-return and conditional-volatility estimates for Level 2 comparison and ensemble scoring.

## Features

- Completed-bar return history.
- Lagged return terms for expected-return modeling.
- Conditional volatility inputs for GARCH-style risk estimates.

## Target

One-step-ahead return direction or expected-return/risk score, consumed by the orchestrator as a typed agent message.

## Fit And Retrain Schedule

Models are fit on historical train/validation windows only. Retraining cadence and model choices are frozen in `configs/validation_selected.yaml` before final-test exposure.

## Cutoffs

Fit windows and feature cutoffs are prior to each decision. Final-test execution uses the Stage 10 lock and does not select or tune after seeing 2025 outcomes.

## Validation

Validated in Stage 6 with temporal splits, robustness checks, and leakage review; included in Stage 10 lock evidence and Stage 11 final-test artifacts.

## Confidence And Abstention

Confidence reflects model fit quality and finite forecast outputs. Failed fits, stale cutoffs, NaN/inf forecasts, or invalid volatility estimates abstain safely.

## Trading Mapping

The agent emits return/risk messages only. Portfolio construction and execution remain outside the model and pass through risk controls.

## Metrics

Evaluated using predictive comparison plus after-cost portfolio metrics: net return, volatility, Sharpe, Sortino, Calmar, drawdown, turnover, and costs.

## Risks And Intended Use

Econometric assumptions can be unstable in crypto markets. This card documents a research component, not a production trading recommendation.
