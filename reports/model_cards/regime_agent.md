# Regime Agent Model Card

## Responsibility

Provides data-quality, volatility, and market-regime context used by the orchestrator and risk layer to adjust or block trading.

## Features

- Rolling volatility and drawdown context.
- Stale/missing data indicators.
- Liquidity and capacity proxies.
- Health and alert inputs from monitoring artifacts.

## Target

Regime state and risk flags rather than a standalone return forecast.

## Fit And Retrain Schedule

Mostly deterministic rules with validation-selected thresholds frozen before final-test exposure.

## Cutoffs

Regime inputs are based on completed bars and current validation/final-test lock metadata only.

## Validation

Stage 4 controlled-stop tests cover stale/missing data, invalid scores, stale cutoffs, disagreement, optimizer failure, invalid weights, drawdown/volatility stops, liquidity/capacity breach, and reconciliation failure.

## Confidence And Abstention

Confidence reflects quality and completeness of regime inputs. Severe quality or risk failures produce explicit stop reason codes.

## Trading Mapping

The regime agent cannot trade. It can cause abstention, exposure caps, cash moves, or kill-switch behavior through typed risk decisions.

## Metrics

Evaluated through monitoring events, alerts, health summaries, stop counts, exposure, turnover, drawdown, volatility, and final portfolio outcomes.

## Risks And Intended Use

Regime rules can be conservative and cash-heavy. They are intended to make failure modes explicit in a research backtest.
