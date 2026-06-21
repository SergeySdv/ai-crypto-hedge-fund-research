# 11 — Source requirement traceability matrix

This matrix is the reviewer-facing proof that every explicit instruction and guiding question from the assignment has an implementation or presentation home. “Guiding question” does not always require a separate feature, but it requires an explicit answer and rationale.

## Part 0 — overall objective and future vision

| ID | Source requirement | Required evidence |
|---|---|---|
| O-01 | Concept, technical design and MVP of an AI-agent crypto trading and risk system | README, architecture, notebook, source package |
| O-02 | Part 1 and Part 2 closely integrated into one coherent vision | Same agents/risk/portfolio methods in deck and code; concept-to-code table in notebook |
| O-03 | Future automation across multiple centralized exchanges via APIs | Market-data and execution protocols; roadmap only, no live orders |
| O-04 | Future Telegram interface for stats/manual close/parameter adjustment | Slide 10 roadmap and future architecture notes |
| O-05 | Future news feeds and sentiment analysis | Slide 10 roadmap; optional interface note, not required implementation |

## Part 1 — presentation

| ID | Source requirement/question | Required evidence |
|---|---|---|
| P-01 | Professional presentation, maximum 10 slides | `presentation/deck.pdf`; automated/manual slide-count check |
| P-02 | Recommended 2–3 slides per section | Target two slides each for fund model, risk, portfolio and architecture; remaining two integrate validation/results |
| P-03 | Cover Hedge Fund Model | Slides 1–2 |
| P-04 | Can classical technical indicators be used? | Explain causal indicators as weak/transparent signals and baseline, not guaranteed alpha |
| P-05 | Which ML algorithms are applicable? | Supervised classification/regression/ranking, unsupervised regimes/anomaly detection; RL/NLP as future with rationale |
| P-06 | Role of AI in trade decisions and which agents | AI proposes scores/confidence; deterministic risk and execution retain authority |
| P-07 | How multiple agents/models interact | Typed messages, normalization/calibration, aggregator, abstention, risk veto and audit trace |
| P-08 | Cover Risk Management | Slides 3–4 |
| P-09 | Which risk metrics? | Volatility, drawdown, VaR/CVaR, concentration, correlation, turnover, liquidity/capacity, exposure |
| P-10 | AI mitigation in high volatility | GARCH/regime forecast → volatility scaling/cash; hard limits remain deterministic |
| P-11 | Volatility and liquidity estimation methods | Realized/GARCH/EWMA vol; trailing dollar volume/ADV/Amihud proxy; order-book depth/spread as future |
| P-12 | Cover Portfolio Management and existing theories/core principles | Slides 5–6: MPT/mean-variance, diversification, risk parity, HRP, CVaR, estimation error |
| P-13 | What is an optimal portfolio? | State objective and constraints; distinguish mathematical optimum from validation-selected robust method |
| P-14 | Metrics guiding optimization | Expected return, covariance, CVaR, drawdown proxy, turnover/cost, concentration and liquidity |
| P-15 | How portfolio is managed/rebalanced over time | Static, calendar, drift, signal and risk-triggered policies |
| P-16 | Cover System Architecture | Slides 7–8 |
| P-17 | Block diagram includes data collection | Explicit module and adapter |
| P-18 | Includes AI signal agents | Explicit modules |
| P-19 | Includes order execution | “Execution layer: simulator now, CEX adapter future” |
| P-20 | Includes monitoring | Operational, data, model, portfolio and execution monitoring |
| P-21 | Includes risk management | Pre-allocation and post-allocation risk gates |
| P-22 | Includes portfolio management | Allocator and rebalance controller |
| P-23 | Interactions clearly described | Arrows plus numbered decision sequence |
| P-24 | All four sections addressed | Deck checklist |
| P-25 | Theoretical depth | Core principles/formulas plus limitations and rationale, not just library names |
| P-26 | Every design choice justified | “Choice / reason / limitation” callouts or speaker notes |
| P-27 | Clear, clean, not text-heavy | Diagrams, tables and generated charts; no dense paragraphs |

## Part 2 — global technical requirements

| ID | Source requirement | Required evidence |
|---|---|---|
| T-01 | Working codebase covering all five levels | `src/`, tests, experiments and final notebook |
| T-02 | Backtest on out-of-sample data not used in training | Frozen train/validation/test protocol and pretest lock |
| T-03 | Train/test split recommended | Stronger train/validation/final-test split with purging/embargo |
| T-04 | Every evaluation includes performance and risk metrics | Per-approach tables contain both metric classes |
| T-05 | Tests reproducible | Frozen data, lockfile, seeds, config/data/git hashes |
| T-06 | Public GitHub or GitLab repository | Final submission checklist includes public URL and clean-clone verification |
| T-07 | Modular code | `src/` boundaries, typed interfaces and tests |
| T-08 | `poetry` or `uv` expected | `uv`, `pyproject.toml`, committed `uv.lock` |
| T-09 | Docker is a plus | Dockerfile and documented command, implemented after core |
| T-10 | All necessary data included in project | Frozen Parquet + instrument metadata + manifest physically delivered |
| T-11 | One self-contained reproducible `.ipynb` | One executed notebook that runs cleanly and regenerates artifacts |
| T-12 | Structured according to Part 2 | Exact notebook headings for Levels 1–5 in assignment order |
| T-13 | Data preparation | Notebook section and source modules |
| T-14 | Model validation | Notebook section, walk-forward splitter and tests |
| T-15 | Strategy backtesting | Shared broker/ledger used by all levels |
| T-16 | Result visualization and explanation | Saved figures plus per-level interpretation |
| T-17 | Code quality, architecture and documentation matter | lint, tests, docs, diagrams, ADRs and CI |
| T-18 | Spaghetti code penalized | Single shared engine; no duplicate level-specific backtest logic |

## Level 1 — baseline

| ID | Requirement | Required evidence |
|---|---|---|
| L1-01 | One pair such as BTC/USDT | Default BTC/USDT experiment |
| L1-02 | Simple moving-average strategy | SMA fast/slow agent |
| L1-03 | ROI, Sharpe and Drawdown | Required metrics table |
| L1-04 | Other useful metrics | CAGR, volatility, Sortino, Calmar, turnover, costs, hit rate and drawdown duration |
| L1-05 | Explain evolution into AI agent | Typed signal output, confidence, state, risk gate and orchestrator mapping |

## Level 2 — econometrics, ML and agents

| ID | Requirement/question | Required evidence |
|---|---|---|
| L2-01 | Integrate AI agents, econometric time-series models and ML models | Technical, Econometric, ML and Regime agents plus aggregator |
| L2-02 | Single pair | Same BTC/USDT panel slice |
| L2-03 | Compare different approaches | Same OOS period, execution, costs, sizing and benchmark for all |
| L2-04 | What data are features? | Feature table and leakage notes |
| L2-05 | What is target variable? | Cost-aware next-open forward return/classification target |
| L2-06 | How trained/tested? | Purged walk-forward train/validation and frozen final test |
| L2-07 | Retraining frequency? | Validation-selected or justified monthly cadence plus sensitivity |
| L2-08 | Which comparison metrics and why? | Predictive metrics separated from after-cost performance/risk metrics |
| L2-09 | Verify results not random chance | Block bootstrap, circular shift/permutation, sensitivity and multiple seeds |

## Level 3 — static portfolio

| ID | Requirement | Required evidence |
|---|---|---|
| L3-01 | Add 5–7 popular coins | Cutoff-based top-liquid universe of 5–7, frozen and logged |
| L3-02 | Static portfolio management | One allocation executed once and held OOS |
| L3-03 | Based on last 12 months | Exact trailing 12-month estimation window before test |
| L3-04 | Calculate metrics defined in Part 1 | Performance, risk, concentration, liquidity and cost metrics |
| L3-05 | Find optimal portfolio | Explicit constrained objective and frozen selected method; compare robust baselines |
| L3-06 | Explain real-trading application | Orders from weights, min notional/lot size, liquidity, fees, custody and reconciliation limitations |

## Level 4 — dynamic portfolio rebalancing

| ID | Requirement/question | Required evidence |
|---|---|---|
| L4-01 | Adapt to changing market conditions | Rolling estimates and regime/risk state |
| L4-02 | Describe time, deviation and signal logic | Calendar, drift, signal-change and risk triggers |
| L4-03 | Select the most effective strategy | Predeclared validation utility using net performance, risk and turnover; frozen before test |

## Level 5 — 100+ pairs

| ID | Requirement/question | Required evidence |
|---|---|---|
| L5-01 | Handle at least 100 pairs | Full-mode artifact showing >=100 eligible and scored pairs on a rebalance date |
| L5-02 | Operate efficiently | Vectorized panel features, pooled/cross-sectional model, caching and runtime/memory report |
| L5-03 | Select trading pairs | Point-in-time coverage, spot status, trailing liquidity and data-quality eligibility |
| L5-04 | Prioritize agent signals | Net-alpha/confidence/risk/liquidity priority score and top-K selection |
| L5-05 | Risk management and metrics | Risk Agent, hard limits, exposure/vol/CVaR/concentration/liquidity/capacity |
| L5-06 | AI-driven dynamic rebalancing | Agent score/regime change contributes to rebalance intent; deterministic risk approves or rejects |
| L5-07 | Monitoring beyond trading KPIs | Data freshness, coverage, drift, calibration, disagreement, failures, runtime and artifact freshness |
| L5-08 | Track long-term system quality | Rolling OOS stability, model decay, calibration, cost ratio, incidents and champion/challenger notes |
| L5-09 | Fail-safe stop signals | Demonstrated stale-data, invalid-signal, drawdown/volatility, optimizer and reconciliation stop scenarios |

## Submission proof

Before submission, attach or display:

- public repository URL;
- clean-clone command transcript;
- executed final notebook;
- rendered `deck.pdf` with slide count;
- data/config/git hashes;
- final-test lock;
- full-mode Level 5 universe count;
- limitations and any skipped checks.
