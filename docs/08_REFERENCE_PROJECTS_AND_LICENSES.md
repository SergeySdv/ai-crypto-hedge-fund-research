# 08 — Reference projects and licensing notes

Verified/reviewed on 2026-06-20. Re-check licenses before release because repositories can change.

## `denisalpino/autofin`

Repository: https://github.com/denisalpino/autofin

Useful concepts:

- financial feature engineering;
- grouped time-series splits;
- padding/barriers between temporal folds;
- data-centric experiment organization.

Do not use as a dependency or copy code. Its README currently states `All rights reserved` and says a future open license is only being considered. Some advertised execution modes are marked work in progress. Treat it as conceptual reading only.

## Freqtrade / FreqAI

Repository: https://github.com/freqtrade/freqtrade

Useful as an external reference for:

- crypto strategy lifecycle;
- exchange data and execution concepts;
- backtesting and hyperparameter workflows;
- look-ahead analysis;
- paper/live operations and protections.

License: GPL-3.0. Do not make it a core linked dependency in a proprietary/commercially sensitive fund take-home without explicit acceptance of copyleft implications. It may be mentioned as a benchmark/reference.

## skfolio

Repository: https://github.com/skfolio/skfolio

Primary recommended portfolio dependency:

- sklearn-compatible portfolio estimation;
- cross-validation/stress testing;
- mean-risk, hierarchical and robust allocation tools;
- risk management utilities.

License: BSD-3-Clause.

## Riskfolio-Lib

Repository: https://github.com/dcajasn/Riskfolio-Lib

Alternative/reference for:

- many convex risk measures;
- CVaR/drawdown/risk-parity formulations;
- portfolio constraints and risk contributions.

License: BSD-3-Clause.

Use either skfolio as the primary library or a small well-justified subset of Riskfolio-Lib. Avoid adding both merely to increase dependency count.

## CCXT

Repository: https://github.com/ccxt/ccxt

Use for public market-data ingestion and future exchange adapter abstractions.

License: MIT.

The default reproducible run must read frozen Parquet and must not depend on the exchange being online.

## QuantStats

Repository: https://github.com/ranaroussi/quantstats

Optional secondary reporting/tear-sheet library. Core metric formulas should remain transparent and unit-tested in the project.

Verify its current license and compatibility in the generated third-party license report.

## Microsoft Qlib

Repository: https://github.com/microsoft/qlib

Useful architecture reference for the research lifecycle from data and ML to portfolio/backtest. It is too large and equity-oriented to use as the take-home’s central framework.

## AI Hedge Fund

Repository: https://github.com/virattt/ai-hedge-fund

Useful reference for naming agent roles and presenting the multi-agent concept. Do not copy investment-persona prompts or make free-form LLM deliberation part of the deterministic trading path.

## General dependency policy

Preferred licenses:

- MIT;
- BSD-2-Clause/BSD-3-Clause;
- Apache-2.0;
- other permissive licenses approved after review.

Before release:

```bash
uv run pip-licenses --format=markdown > THIRD_PARTY_LICENSES.md
```

Review unknown, GPL, AGPL, Commons Clause or source-available licenses manually. A license inventory is documentation, not legal advice.

## Attribution policy

- Reimplement general mathematical ideas from primary papers/docs.
- Link to external projects in the README “References” section.
- Do not paste source code unless its license is compatible and required notices are preserved.
- Record any adapted implementation and source in comments/NOTICE.
