# 07 — Presentation outline (maximum 10 slides)

Create `presentation/deck.md` in Marp-compatible Markdown and render `presentation/deck.pdf`. Verify the PDF contains no more than 10 slides.

The source recommends 2–3 slides per conceptual section. Within the 10-slide cap, use two slides for each of the four required sections, then two integrated evidence/roadmap slides.

## Slide 1 — Hedge Fund Model: mandate and investment universe

Answer:

- What is the fund trying to do?
- Why a long-only, unlevered spot MVP?
- Which markets/time horizons are in scope?
- How are cash and capacity treated?

Content:

- risk-first AI-assisted crypto portfolio;
- daily spot USDT universe;
- strategy sleeves: technical, econometric and ML/cross-sectional;
- research MVP now, live multi-CEX automation later.

Visual: compact investment-process pipeline.

## Slide 2 — Hedge Fund Model: AI/ML and agent interaction

Answer the assignment’s AI questions directly:

- classical indicators are transparent baseline signals;
- supervised classification/regression/ranking are core ML choices;
- regime clustering/anomaly detection are useful support tools;
- RL and NLP/sentiment are future/optional due data and validation complexity;
- AI produces scored proposals/confidence, not unchecked orders.

Show:

- Technical, Econometric, ML and Regime Agents;
- typed outputs, abstention and aggregator;
- risk veto and audit trail.

Visual: agent responsibility/interaction matrix.

## Slide 3 — Risk Management: risk taxonomy and metrics

Cover:

- market/volatility risk;
- drawdown/tail risk;
- concentration/correlation risk;
- liquidity/capacity and transaction-cost risk;
- model/data/operational risk.

Metrics:

- volatility, VaR/CVaR, maximum drawdown/duration;
- exposure, concentration/effective N and risk contributions;
- turnover, costs, ADV participation and stale-data/model-health metrics.

Visual: risk taxonomy or dashboard mock-up.

## Slide 4 — Risk Management: AI support and deterministic controls

Explain:

- GARCH/realized volatility and Regime Agent anticipate high-volatility periods;
- volatility scaling, cash and lower risk budgets mitigate exposure;
- pre-allocation and post-allocation risk gates;
- drawdown/volatility/data/model/optimizer kill switches;
- AI may warn or propose, but hard controls remain deterministic.

Visual: two-stage risk funnel and fail-safe sequence.

## Slide 5 — Portfolio Management: theory and “optimal” portfolio

Discuss core principles:

- diversification and Modern Portfolio Theory;
- mean-variance and estimation error;
- inverse volatility/risk parity;
- HRP and CVaR/tail-risk alternatives;
- why historical maximum Sharpe is not automatically a robust optimum.

Define the chosen optimization objective and constraints.

Visual: small comparison table or efficient-risk frontier schematic.

## Slide 6 — Portfolio Management: static, dynamic and large-universe implementation

Show the progression:

- Level 3: 5–7 assets, prior 12 months, static OOS weights;
- Level 4: calendar/drift/signal/risk rebalance selected on validation;
- Level 5: point-in-time 100+ pair universe, top-K, capacity and turnover controls.

Use actual generated weight/risk/cost chart. Explain how target weights become executable orders and what remains simplified.

## Slide 7 — System Architecture: end-to-end block diagram

Must visibly include:

- data collection and frozen storage;
- data quality and causal features;
- AI signal agents and orchestrator;
- pre-risk, portfolio allocator, rebalance controller and post-risk;
- order generation/execution simulator;
- ledger, monitoring and audit artifacts.

Label future CEX adapter separately from the implemented simulator.

## Slide 8 — System Architecture: interactions, monitoring and future operation

Show a numbered decision sequence from completed bar to fill/no-fill.

Monitoring beyond trading KPIs:

- freshness/coverage;
- drift/calibration and agent disagreement;
- optimizer/order failures;
- runtime/artifact health;
- long-term rolling stability and incidents.

Future roadmap in a small callout: multi-CEX, reconciliation, Telegram and news/sentiment.

## Slide 9 — Technical implementation and validation evidence

Summarize all five levels and the experimental protocol:

- included frozen data;
- train 2021–2023, validation 2024, frozen test 2025;
- final-test lock;
- next-open execution;
- fees/slippage and consistent benchmarks;
- bootstrap/randomization/sensitivity checks;
- full Level 5 pair count and runtime.

Visual: timeline plus maturity staircase.

## Slide 10 — Results, limitations and conclusion

Use actual final artifacts only:

- compact gross/net return-risk-cost table;
- benchmark comparison and uncertainty;
- note negative/inconclusive results honestly;
- key limitations: survivorship, daily bars, exchange-only liquidity proxy, USDT cash assumption and simplified fills;
- production next steps.

Do not claim “production ready,” guaranteed alpha or robust profitability without evidence.

## Deck quality checklist

- exactly 10 or fewer PDF pages/slides;
- all four required sections identifiable;
- every core claim supported by code/artifact or labeled future;
- readable fonts and minimal paragraphs;
- no placeholder metrics;
- architecture arrows/interactions explicit;
- actual charts exported at suitable resolution;
- financial disclaimer and limitations visible.
