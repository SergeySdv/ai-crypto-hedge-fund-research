# ML Agent Model Card

## Responsibility

Runs classical machine-learning classifiers for Level 2 validation and ensemble comparison, including Logistic Regression and HistGradientBoosting-style tree boosting.

## Features

- Lagged return, trend, volatility, and liquidity features.
- Features are computed from completed bars and passed through temporal train/validation protocols.

## Target

Forward directional label or probability used as a typed score and confidence input to the orchestrator.

## Fit And Retrain Schedule

Training uses temporal splits only. Hyperparameters, selected model family, seeds, and ensemble weights are frozen before final-test exposure.

## Cutoffs

Feature and label construction avoids shuffled splits and future bars. Predictions at a decision time use only data available before the next-open execution.

## Validation

Stage 6 validates temporal train/validation behavior, robustness checks, multiple seeds where applicable, and leakage controls. Stage 10 locks the selected method before Stage 11.

## Confidence And Abstention

Confidence is based on raw classifier probabilities or normalized score outputs. Calibration error is measured for diagnostics, but no Platt, sigmoid, or isotonic calibration model is fitted in the frozen protocol. Invalid confidence, stale model cutoff, NaN/inf output, or excessive disagreement triggers abstention or risk stop.

## Trading Mapping

The ML agent emits typed messages only. The orchestrator aggregates messages; risk gates and allocation control any target portfolio.

## Metrics

Reported with predictive checks and after-cost trading metrics, with net metrics primary.

## Risks And Intended Use

ML classifiers may overfit noisy daily crypto data. The repository reports negative and inconclusive outcomes honestly and is for reproducible research only.
