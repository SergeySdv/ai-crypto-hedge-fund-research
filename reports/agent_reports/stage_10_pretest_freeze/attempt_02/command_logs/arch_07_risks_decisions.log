# 10 — Architecture decisions, risks and known limitations

## ADR-001 — One panel-native kernel for Levels 1–5

Decision: data, signals, weights, execution and metrics are multi-asset from the start. Level 1 is a one-symbol configuration.

Rationale:

- prevents a late rewrite when portfolio levels begin;
- guarantees comparable costs and timing;
- reduces duplicate/spaghetti code;
- scales naturally to 100+ pairs.

## ADR-002 — Transparent custom research broker/ledger

Decision: implement a small weight/order/fill simulator rather than using a large framework as the central engine.

Rationale:

- time alignment and costs can be proven with hand tests;
- portfolio weights and cash are first-class;
- notebook remains reviewable;
- avoids tying the core to restrictive/copyleft dependencies.

Limitation: it is not a full exchange matching engine.

## ADR-003 — Next-open execution after completed bars

Decision: features from daily bar `t` are available after close and orders fill no earlier than open `t+1`; holding returns are open-to-open.

Rationale: filling at the same close used to generate a signal can create an unrealistic same-close assumption.

Consequence: targets, benchmarks, order timestamps and tests must use the same clock.

## ADR-004 — Distinguish fee-bearing notional from reporting turnover

Decision:

- cost is charged on `sum(abs(delta risky weights))`;
- reporting turnover may use half-L1 including cash reconciliation.

Rationale: full rotation from asset A to asset B requires a sell and a buy, whereas cash→asset is only one fee-bearing trade.

## ADR-005 — Deterministic agents; optional LLM narration only

Decision: agents are typed analytical components with goals, state/cutoffs, confidence, abstention and orchestration. No LLM controls orders or risk.

Rationale:

- reproducibility and auditability;
- no key/cost requirement;
- clear safety boundary;
- ML/econometric agents already satisfy the AI-agent role when they actually interact.

Optional narrative output cannot affect portfolio state.

## ADR-006 — Two-stage risk gate

Decision: pre-allocation risk sets constraints and blocks unsafe inputs; post-allocation risk validates/vetoes actual candidate weights.

Rationale: portfolio volatility, concentration and turnover cannot be evaluated from signals alone.

## ADR-007 — Daily long-only unlevered spot MVP

Decision: daily bars, long-only, no leverage, cash allowed.

Rationale:

- computationally manageable for 100+ pairs;
- avoids funding/liquidation/margin modeling;
- gives a defensible historical MVP.

Limitation: “hedge fund” is conceptual; the MVP is not market-neutral and does not hedge with shorts/derivatives.

## ADR-008 — Frozen 2021–2025 study with final-test quarantine

Decision:

- train: 2021–2023;
- validation: 2024;
- final test: 2025;
- all five levels selected before a final-test lock is created;
- final suite runs only from that lock.

Rationale: avoids tuning later levels after seeing earlier final-test performance.

## ADR-009 — Exact trailing 12 months for Level 3

Decision: use a vintage-safe pattern. Select/estimate on 2023 and validate by holding in 2024; after method selection, select/estimate on 2024 and execute/hold in 2025. Each allocation uses exactly the prior 12 months.

Rationale: directly satisfies “last 12 months,” avoids choosing a validation universe with end-of-validation hindsight, and preserves OOS evaluation.

## ADR-010 — Cutoff-based small-universe popularity

Decision: select 5–7 assets mechanically by pre-test liquidity/coverage, optionally requiring BTC/ETH anchors declared in advance.

Rationale: a handpicked list based on later popularity/performance creates hindsight bias.

## ADR-011 — Hard 100+ full-mode Level 5

Decision: submission fails the Level 5 acceptance gate unless a full artifact proves at least 100 eligible and scored pairs on a rebalance date.

Rationale: the source says “at least 100”; a documented shortage is not equivalent.

## ADR-012 — Included processed data, downloader supplementary

Decision: commit/deliver compressed processed OHLCV, instrument metadata and manifest sufficient for offline notebook execution.

Rationale: “all necessary data must be included” and reproducibility on another machine.

Raw API payloads may be omitted when provenance and hashes are complete.

## ADR-013 — Robust portfolio optimization over noisy expected returns

Decision: compare equal weight, inverse volatility, shrinkage minimum variance and HRP/CVaR. Define optimizer objectives explicitly and select the submitted method on validation with risk/turnover constraints.

Rationale: crypto mean estimates are unstable; historical max-Sharpe alone is fragile.

## ADR-014 — Level 5 pooled/cross-sectional modeling

Decision: use vectorized panel features and a pooled/cross-sectional score; do not fit heavyweight GARCH/LLM pipelines for every pair every day.

Rationale: satisfies the efficiency requirement and makes 100+ pairs practical.

## ADR-015 — Actual deck PDF and one executed notebook

Decision: commit `presentation/deck.pdf` and exactly one clearly designated, fully executed final notebook.

Rationale: reviewers should not need local rendering or guess which notebook is final.

## Primary risks and mitigations

### Temporal leakage and unrealistic execution

Mitigations:

- explicit bar/feature/decision/execution timestamps;
- next-open fills;
- purging/embargo;
- no global preprocessing;
- hand-calculated regression tests.

### Final-test contamination

Mitigations:

- develop all levels on train/validation;
- pretest lock with hashes;
- one frozen final suite;
- log bug-driven reruns and prohibit performance tuning.

### Survivorship and listing bias

Risk: current active-pair downloads omit delisted assets.

Mitigations:

- point-in-time eligibility within available data;
- disclose the bias prominently;
- avoid institutional point-in-time claims;
- future historical listing/delisting source.

### Missing bars and delistings

Mitigations:

- no synthetic returns from fill;
- block orders without an execution price;
- short stale valuation window with flag;
- conservative freeze/liquidation assumption after limit;
- explicit incident log.

### Transaction-cost underestimation

Mitigations:

- correct risky-notional accounting;
- one-way fee/slippage convention;
- AUM/ADV participation cap;
- 1x/2x/3x cost stress;
- order-book/impact model listed as future work.

### Multiple testing and overfitting

Mitigations:

- bounded candidate grids;
- validation-only selection;
- block bootstrap and signal randomization;
- sensitivity and multiple seeds;
- honest negative/inconclusive conclusions.

### Non-stationarity and model decay

Mitigations:

- rolling retraining;
- regime diagnostics;
- calibration/drift monitoring;
- agent disagreement/abstention;
- volatility scaling and risk stops;
- rolling OOS quality dashboard.

### Optimization instability

Mitigations:

- shrinkage covariance;
- caps, regularization and robust baselines;
- deterministic/pinned solver where feasible;
- safe previous-weight/cash fallback;
- solver status and reason codes.

### Liquidity and capacity approximation

Risk: daily exchange volume is only a proxy; dollar volume may be approximate and order-book depth is absent.

Mitigations:

- trailing ADV/participation constraints;
- minimum notional/precision where metadata exists;
- capacity stress and clear limitations;
- future spread/depth/market-impact data.

### Misleading “AI” claims

Mitigations:

- define agent responsibility, typed interaction, confidence and abstention;
- separate predictions from risk/allocation/execution;
- display an audit trace;
- avoid anthropomorphic/autonomous claims unsupported by code.

### Operational and security risk in future live use

Future controls:

- read/trade-only API permissions with withdrawals disabled;
- secrets manager;
- idempotent order IDs and reconciliation;
- exchange/API health checks;
- human kill switch and authenticated Telegram controls;
- paper/shadow deployment before capital.

## Mandatory fail-safe demonstrations

At least controlled scenarios for:

- manifest/hash mismatch;
- stale/missing data or execution price;
- NaN/inf/extreme agent score;
- stale model cutoff;
- excessive agent disagreement;
- infeasible optimizer or invalid weights;
- drawdown/volatility hard stop;
- liquidity/capacity breach;
- ledger/weight reconciliation failure.

The system must freeze new risk, preserve the previous safe portfolio or move to cash according to policy, and emit explicit reasons.

## Result interpretation policy

- After-cost results are primary.
- A strategy losing to its benchmark remains a valid finding.
- Sharpe without uncertainty, drawdown and costs is insufficient.
- “Profitable,” “robust alpha” and “production ready” claims require direct evidence and should generally be avoided in this take-home.
- Separate historical research evidence from future production assumptions.
