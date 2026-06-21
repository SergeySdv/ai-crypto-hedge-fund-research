# Ensemble Orchestrator Model Card

## Responsibility

Aggregates typed technical, econometric, ML, and regime messages into validated portfolio intent for Levels 2, 4, and 5.

## Features

Consumes agent outputs with score, confidence, horizon, fit cutoff, feature cutoff, and reason codes. It does not compute raw market features directly.

## Target

Consensus ranking or allocation intent passed to pre-allocation risk, portfolio allocation, post-allocation risk, and the shared broker.

## Fit And Retrain Schedule

Aggregation rules, disagreement thresholds, confidence handling, top-K selection, risk limits, and rebalance policy are selected on validation data and frozen in the Stage 10 lock.

## Cutoffs

The orchestrator rejects stale model cutoffs, invalid horizons, invalid confidence, and inconsistent decision/execution timestamps.

## Validation

Stage 4 validates typed agent communication, disagreement/abstention handling, fail-safe states, and decision trace. Stages 8-11 validate dynamic rebalancing, large-universe scoring, pretest lock, and frozen final-test execution.

## Confidence And Abstention

Confidence is aggregated conservatively. Excessive disagreement, missing agents, invalid scores, optimizer failure, or risk breaches produce explicit abstention, cash, cap, or block actions.

## Trading Mapping

The orchestrator emits portfolio intent only. Orders and fills are created by the shared next-open broker after risk and allocation checks.

## Metrics

Evaluated with final net performance, drawdown, turnover, costs, exposure, selected/eligible/scored counts, monitoring alerts, health summaries, runtime, and memory evidence.

## Risks And Intended Use

Aggregation can hide weak individual models and may still underperform after costs. The final-test results are frozen evidence for the assignment, not a live-trading claim.
