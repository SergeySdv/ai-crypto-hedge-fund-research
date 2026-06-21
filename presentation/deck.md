---
marp: true
title: AI Crypto Hedge Fund Research MVP
paginate: true
---

# Hedge Fund Model
## Mandate and investment universe

- Educational, historical AI-assisted crypto research MVP.
- Long-only, unlevered daily spot USDT universe; cash is explicit.
- Strategy sleeves: technical, econometric, ML and cross-sectional scoring.
- Future: multi-CEX automation, but no live order submission is enabled.

---

# Hedge Fund Model
## AI/ML and agent interaction

- Classical indicators are transparent baseline signals.
- Logistic regression, gradient boosting, AutoReg/GARCH and deterministic cross-sectional scoring agents are used.
- Agents emit score, confidence, horizon, cutoffs and reason codes.
- Aggregation proposes exposure; deterministic risk can veto or move to cash.

---

# Risk Management
## Taxonomy and metrics

- Market, drawdown/tail, concentration/correlation and liquidity/capacity risk.
- Model, data and operational failures are tracked separately from returns.
- Metrics include volatility, VaR/CVaR, drawdown, exposure, turnover and costs.
- Level 5 health status: `ok`.

---

# Risk Management
## AI support and deterministic controls

- GARCH/realized volatility and regime state inform risk budgets.
- Pre-allocation risk blocks stale, illiquid or invalid inputs.
- Post-allocation risk validates weights, turnover, concentration and cash.
- Fail-safes include volatility cash approval, invalid feature alerts and reconciliation checks.

---

# Portfolio Management
## Theory and "optimal" portfolio

- MPT and minimum variance give transparent objectives but face estimation error.
- Equal weight and inverse volatility remain robust baselines.
- CVaR/downside methods address tail risk directly.
- Submitted methods were selected on validation, not on final-test returns.

---

# Portfolio Management
## Static, dynamic and large universe

- Level 3: 5-7 assets, exactly prior 12-month estimation, static OOS hold.
- Level 4: calendar/drift/signal/risk rebalance policy.
- Level 5: point-in-time 100+ universe, top-K 25, capacity and turnover controls.
- Target weights become next-open simulated orders through one shared broker.

---

# System Architecture
## End-to-end block diagram

```text
Frozen OHLCV -> quality gate -> causal features -> signal agents
  -> orchestrator -> pre-risk -> allocator -> rebalance controller
  -> post-risk -> order generator -> simulated broker -> ledger
  -> metrics, monitoring, notebook and deck
```

Future CEX adapters are disabled; simulator artifacts are the submitted evidence.

---

# System Architecture
## Interactions, monitoring and roadmap

1. Completed daily bar creates features.
2. Agents emit typed proposals with cutoffs and confidence.
3. Risk and portfolio layers approve, cap or reject.
4. Orders fill at next open; ledger writes gross/net metrics.
5. Monitoring records freshness, drift, disagreement, incidents and runtime.

---

# Technical Evidence
## Frozen protocol and Level 5 count

- Train: 2021-2023; validation: 2024; final test: 2025.
- Accepted final lock: `dab407601cbaf8198361e5e3d074260546ed4bbab4c4be2555248b246631308b`.
- Final-test exposure: `EXPOSED`.
- Level 5 final count: 120 eligible, 120 scored, 25 selected.
- Runtime: 75.2s; peak RSS: 727.3 MiB.

---

# Results and Limitations
## Net final-test evidence

| Level | Selected | Net return | Sharpe | MDD |
| --- | --- | --- | --- | --- |
| Level 1 | SMA baseline | -7.4% | -0.17 | -18.5% |
| Level 2 | agent_ensemble | -0.6% | -0.52 | -1.4% |
| Level 3 | cvar_downside | -18.0% | -0.02 | -45.2% |
| Level 4 | calendar_monthly | -4.1% | -0.88 | -9.1% |
| Level 5 | large_universe_dynamic | -28.0% | -0.22 | -42.2% |

Limitations: active-market survivorship/delisting bias, daily-bar liquidity proxy,
short late-December 2024 Level 5 validation proof window, cash-heavy risk behavior,
BTC-normalized Level 5 benchmark and dirty Stage 11 runner provenance. Results did
not establish robust alpha.
