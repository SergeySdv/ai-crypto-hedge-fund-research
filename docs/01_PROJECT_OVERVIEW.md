# Project Overview

## Purpose

AI Crypto Hedge Fund is an educational research system for historical crypto
portfolio experiments. It is not investment advice, not a profitability claim, and
not an enabled live trading bot.

The default submission is:

- Python 3.11 with `uv`, `pyproject.toml`, and a committed `uv.lock`.
- Offline and reproducible from included frozen data.
- Long-only, unlevered, spot-only, daily-bar, USDT-cash based.
- Built as one shared panel-native engine, not five independent scripts.
- Evaluated with net results after configured fees and slippage.

## The Five Levels

Each assignment level is a configuration of the same architecture.

| Level | Main question | Main evidence |
| --- | --- | --- |
| 1 | Can a single-symbol baseline run through the real engine? | BTC/USDT SMA baseline, orders, fills, ledger, metrics |
| 2 | Can typed agents generate auditable signals? | Technical, econometric, ML, regime, and ensemble traces |
| 3 | Can static portfolio methods be selected without final-test leakage? | 5-7 asset portfolio selected using prior 12-month estimation |
| 4 | Can the small portfolio rebalance dynamically? | Calendar, drift, signal, risk, and cost-aware rebalance log |
| 5 | Can the system scale to a large universe? | 120 eligible/scored final-test pairs, top-K constrained portfolio |

## Core Idea

The engine follows a strict sequence:

```text
completed market data
  -> causal features
  -> typed agent proposals
  -> pre-allocation risk constraints
  -> portfolio allocation
  -> rebalance decision
  -> post-allocation risk approval
  -> next-open simulated execution
  -> ledger, costs, metrics, monitoring, artifacts
```

No signal agent can place an order. Only broker fills update the ledger. The same
broker, ledger, cost model, risk gates, metrics, and artifact writers are used for
every level.

## Where To Start In The Repository

| Path | Role |
| --- | --- |
| `README.md` | concise release-facing summary and command list |
| `notebooks/ai_crypto_hedge_fund.ipynb` | executed end-to-end narrative notebook |
| `src/crypto_hedge_fund/` | reusable package code |
| `configs/default.yaml` | frozen default experiment configuration |
| `data/processed/` | included daily OHLCV and instrument snapshot |
| `artifacts/final_test_lock.json` | frozen final-test lock |
| `artifacts/final_test/c33b5eb396f6/` | accepted final-test artifacts |
| `reports/final_report.md` | final written report |
| `presentation/deck.pdf` | 10-page presentation |

## Safety Boundary

The codebase includes only the offline research/simulation path for the default
run. Live exchange order submission is out of scope. Any future live adapter would
need explicit credentials, exchange permissions, reconciliation, and operational
safety controls that are not enabled in this submission.
