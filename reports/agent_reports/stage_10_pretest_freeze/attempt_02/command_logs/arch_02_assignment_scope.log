# 01 — Assignment, scope and delivery contract

## Objective

Design and implement an MVP for an AI-agent-based cryptocurrency fund that combines data collection, signal generation, econometrics, machine learning, portfolio construction, risk management, historical execution/backtesting, monitoring and future execution interfaces.

The conceptual presentation and technical implementation must tell the same story. Every core module shown in the presentation must either exist in the MVP or be explicitly labeled as future work.

## Part 1 — mandatory conceptual presentation

Deliver a professional presentation with **at most 10 slides**. The assignment recommends 2–3 slides per required section; within the 10-slide limit, target about two slides for each section:

1. Hedge Fund Model.
2. Risk Management.
3. Portfolio Management.
4. System Architecture and module interactions.

The deck must:

- integrate cryptocurrencies and AI-driven trading bots;
- explain classical technical indicators and applicable ML categories;
- define the role and limits of AI in trade decisions;
- explain how multiple agents/models interact;
- identify risk metrics and high-volatility controls;
- discuss volatility and liquidity estimation;
- discuss portfolio theories, objectives, metrics and rebalancing;
- show a block diagram containing data collection, signal agents, order execution, monitoring, risk and portfolio management;
- justify choices with clear rationale;
- remain clear, clean and not text-heavy.

Required artifacts:

```text
presentation/deck.md
presentation/deck.pdf
```

The PDF, not only the Markdown source, is part of the submission.

## Part 2 — mandatory technical deliverable

Create a working public GitHub/GitLab project that is:

- modular and documented;
- reproducible on another machine;
- managed by `uv` or equivalent lock-based tooling;
- supplied with all data required for the default run;
- evaluated out of sample with both performance and risk metrics;
- validated and tested;
- presented through one final self-contained, reproducible and executed `.ipynb` notebook;
- structured according to the five Part 2 levels.

“Self-contained notebook” means the notebook is the single end-to-end narrative and execution entry point. It may import the repository package, but it must not depend on hidden notebook state, live downloads, private keys, uncommitted local files or previously fabricated results.

## Five technical levels

### Level 1 — baseline on one cryptocurrency

- Default pair: BTC/USDT.
- Implement a simple moving-average strategy.
- Compare with BTC buy-and-hold.
- Report ROI/total return, Sharpe and drawdown plus other useful metrics.
- Explain how the strategy evolves into an AI agent with typed output, state/confidence and risk interaction.

### Level 2 — econometrics, ML and AI agents on one cryptocurrency

On the same pair, implement and compare under identical data, execution, cost and sizing assumptions:

- technical strategy/agent;
- classical econometric time-series model for expected return;
- econometric volatility model;
- classical ML model(s);
- interacting multi-agent ensemble/orchestrator.

Explicitly answer:

- feature data;
- target variable;
- training, validation and test protocol;
- retraining frequency;
- predictive, trading, performance and risk metrics and why they are used;
- how random-chance/overfitting explanations are tested.

### Level 3 — static portfolio of 5–7 cryptocurrencies

- Select 5–7 popular/liquid coins using information available at the estimation cutoff.
- Use the **last 12 months of historical data** to estimate a static portfolio.
- Freeze weights and evaluate them out of sample.
- Calculate the risk/performance/liquidity/concentration metrics introduced in Part 1.
- Define and solve at least one explicit constrained “optimal portfolio” objective, while comparing robust baselines.
- Explain translation to real trading: target weights to orders, costs, liquidity, minimum notional/precision, custody and execution limitations.

Default frozen interpretation:

```text
estimation: 2024-01-01 through 2024-12-31
execution: first valid open in 2025
evaluation: 2025 out of sample
```

For method validation, use a prior vintage: select/estimate with 2023 data and evaluate in 2024. Do not backtest 2024 using a universe selected with end-of-2024 information.

### Level 4 — small portfolio with adaptive dynamic rebalancing

- Build on the same 5–7 asset portfolio and shared engine.
- Implement time-based, weight-drift, signal-change and/or risk-triggered logic.
- Use rolling historical estimates without future information.
- Predefine a cost-aware validation criterion for selecting the most effective policy.
- Freeze the chosen policy before final-test evaluation.
- Report turnover, costs, changing weights and risk through time.

### Level 5 — large portfolio/universe with dynamic rebalancing

- Handle and score **at least 100 pairs in an actual full run**.
- Use point-in-time pair eligibility and liquidity/data-quality filters.
- Prioritize agent signals using expected net alpha, confidence, risk and liquidity.
- Apply dynamic portfolio allocation and risk controls.
- Make agent/regime changes part of the rebalance intent while deterministic risk retains veto authority.
- Monitor system health beyond trading KPIs.
- Track long-term quality and model/system decay.
- Demonstrate fail-safe stop signals for unexpected agent/system behavior.
- Show runtime/scalability evidence and avoid one heavyweight model/LLM call per pair per bar.

The system may score 100+ pairs while holding a smaller top-K. It does not need to hold every pair simultaneously.

## Out-of-sample and reproducibility contract

- Use chronological train, validation and final-test periods.
- Never shuffle time-series splits.
- Fit preprocessing and models only on historical data.
- Select all choices on train/validation.
- Quarantine the final test until all five levels are implemented and frozen.
- Include transaction costs and consistent benchmarks.
- Include both performance and risk metrics for every strategy comparison.
- Include frozen data, manifest, hashes, package lock and seeds.
- Run the notebook from a clean kernel and empty artifacts directory.

## Project future explicitly mentioned in the assignment

Document as future interfaces/roadmap, not required MVP implementation:

- automated trading across multiple centralized exchanges through APIs;
- Telegram controls/statistics/manual intervention;
- news feeds and sentiment analysis.

## Requirement-to-artifact map

| Requirement | Repository evidence |
|---|---|
| Professional concept presentation | `presentation/deck.md`, `presentation/deck.pdf` |
| Four conceptual sections | deck slide map and `docs/07_PRESENTATION_OUTLINE.md` |
| System architecture | `docs/architecture.md`, Mermaid diagrams and deck |
| Public reproducible project | README, public URL, `pyproject.toml`, `uv.lock`, CI, Docker |
| Included data | frozen Parquet, instruments metadata and manifest |
| Single final notebook | `notebooks/ai_crypto_hedge_fund.ipynb` |
| Data preparation | `src/.../data/` plus notebook section |
| Model validation | `src/.../validation/`, model cards and notebook |
| Backtesting | shared execution/broker/ledger modules |
| Visualization/explanation | artifacts, notebook and final report |
| Agent interaction | orchestrator, typed records and decision trace |
| Levels 1–5 | experiment modules and exact notebook chapters |
| Long-term monitoring/fail-safes | monitoring artifacts and demonstrated scenarios |
| Final-test integrity | `artifacts/final_test_lock.json` |
| Code quality | tests, Ruff, CI, typed APIs and docs |

## Out of scope for the required MVP

- enabled live order submission;
- leverage, futures, options and shorting;
- Telegram implementation;
- news/sentiment ingestion;
- deep reinforcement learning;
- paid LLM/data services;
- distributed microservices.

## Success standard

A reviewer can clone the public repository and run, without API keys:

```bash
uv sync --frozen
make validate-data
make test
make notebook-full
make presentation
```

The run uses included frozen real data, recreates the headline artifacts, proves a 100+ pair Level 5 run and yields a rendered deck of at most 10 slides.
