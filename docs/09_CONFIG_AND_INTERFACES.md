# 09 — Configuration and typed interfaces

## Example full configuration

Create `configs/default.yaml` with equivalent semantics:

```yaml
project:
  name: ai-crypto-hedge-fund
  seed: 42
  timezone: UTC
  mode: full

paths:
  market_data: data/processed/ohlcv_daily.parquet
  instruments: data/processed/instruments.parquet
  manifest: data/manifests/ohlcv_daily_manifest.json
  artifacts: artifacts

data:
  exchange: binance
  market_type: spot
  quote_currency: USDT
  timeframe: 1d
  start: '2021-01-01'
  end: '2025-12-31'
  min_history_days: 365
  preferred_history_days: 730
  large_universe_size: 120
  liquidity_lookback_days: 90
  small_portfolio_lookback_days: 365
  stable_bases: [USDT, USDC, FDUSD, TUSD, DAI, USDP, EUR, GBP]

clock:
  bar_timestamp_semantics: start
  decision_after_bar_close: true
  execution: next_open
  holding_return: open_to_open
  max_stale_valuation_days: 2

splits:
  train_start: '2021-01-01'
  train_end: '2023-12-31'
  validation_start: '2024-01-01'
  validation_end: '2024-12-31'
  test_start: '2025-01-01'
  test_end: '2025-12-31'
  embargo_days: 5

backtest:
  initial_capital_usd: 1000000
  annualization_periods: 365
  risk_free_rate: 0.0
  fee_bps_one_way: 10.0
  slippage_bps_one_way: 5.0
  allow_short: false
  allow_leverage: false
  allow_cash: true

level_1:
  symbol: BTC/USDT
  fast_windows: [10, 20, 30]
  slow_windows: [50, 100, 150]

level_2:
  prediction_horizon_open_days: 1
  retrain_candidates: [weekly, monthly, quarterly]
  default_retrain: monthly
  calibration: sigmoid
  ensemble_weight_grid_step: 0.1
  safety_margin_bps: 5.0

portfolio:
  small_size: 7
  small_selection: trailing_liquidity
  small_selection_cutoff: '2024-12-31'
  small_estimation_start: '2024-01-01'
  small_estimation_end: '2024-12-31'
  small_max_weight: 0.30
  large_max_weight: 0.05
  large_top_k: 25
  volatility_target_annual: 0.35
  max_gross_exposure: 1.0
  turnover_cap: 0.35
  solver: deterministic_supported_solver

rebalance:
  calendar: weekly
  small_calendar: monthly
  drift_threshold_abs: 0.05
  score_change_threshold: 0.15
  risk_trigger: true
  selection_metric: net_sharpe
  max_drawdown_constraint: 0.25
  annual_turnover_constraint: 6.0
  tie_breaker: lower_turnover_then_simpler

liquidity:
  assumed_aum_usd: 1000000
  adv_lookback_days: 20
  max_participation: 0.01
  enforce_min_notional_if_available: true

risk:
  max_drawdown_stop: 0.20
  high_volatility_threshold_annual: 0.80
  max_agent_disagreement: 0.75
  min_effective_holdings: 5
  post_allocation_validation: true

statistics:
  bootstrap_repetitions: 1000
  permutation_repetitions: 1000
  block_length_days: 14
  random_seeds: [7, 42, 137]

final_test:
  require_lock: true
  lock_path: artifacts/final_test_lock.json
  refuse_hash_mismatch: true
```

`configs/fast.yaml` may reduce symbols, repetitions and model iterations for CI, but it must not change timing, leakage protection, cost formulas or weight/risk invariants. Fast mode is never the evidence for the final 100+ pair claim.

## Core enums and records

Use frozen dataclasses or Pydantic v2 models with runtime validation.

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping


class ReasonCode(StrEnum):
    OK = "ok"
    ABSTAIN = "abstain"
    WARMUP = "warmup"
    STALE_DATA = "stale_data"
    MISSING_EXECUTION_PRICE = "missing_execution_price"
    INVALID_DATA = "invalid_data"
    LOW_LIQUIDITY = "low_liquidity"
    CAPACITY_LIMIT = "capacity_limit"
    VOLATILITY_LIMIT = "volatility_limit"
    DRAWDOWN_STOP = "drawdown_stop"
    TURNOVER_LIMIT = "turnover_limit"
    CONCENTRATION_LIMIT = "concentration_limit"
    AGENT_DISAGREEMENT = "agent_disagreement"
    MODEL_FAILURE = "model_failure"
    STALE_MODEL = "stale_model"
    OPTIMIZER_FAILURE = "optimizer_failure"
    WEIGHT_RECONCILIATION_FAILURE = "weight_reconciliation_failure"
    DRIFT_ALERT = "drift_alert"
    HASH_MISMATCH = "hash_mismatch"


@dataclass(frozen=True)
class ResearchClock:
    bar_start: datetime
    bar_end: datetime
    feature_cutoff: datetime
    decision_time: datetime
    execution_time: datetime


@dataclass(frozen=True)
class AgentContext:
    clock: ResearchClock
    symbols: tuple[str, ...]
    model_fit_cutoff: datetime
    portfolio_nav: float
    current_weights: Mapping[str, float]
    health_state: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentSignal:
    symbol: str
    agent: str
    score: float          # normally [-1, 1]
    confidence: float     # [0, 1]
    horizon_open_days: int
    fit_cutoff: datetime
    feature_cutoff: datetime
    reason_codes: tuple[ReasonCode, ...] = (ReasonCode.OK,)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AggregatedSignal:
    symbol: str
    score: float
    confidence: float
    contributions: Mapping[str, float]
    disagreement: float
    reason_codes: tuple[ReasonCode, ...]


@dataclass(frozen=True)
class RiskConstraints:
    decision_time: datetime
    max_gross_exposure: float
    per_asset_caps: Mapping[str, float]
    blocked_symbols: tuple[str, ...]
    volatility_target: float | None
    turnover_cap: float | None
    reason_codes: tuple[ReasonCode, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PortfolioProposal:
    decision_time: datetime
    target_weights: Mapping[str, float]
    cash_weight: float
    optimizer_status: str
    expected_turnover: float
    objective_value: float | None
    reason_codes: tuple[ReasonCode, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RebalanceDecision:
    decision_time: datetime
    should_rebalance: bool
    trigger_codes: tuple[str, ...]
    expected_net_benefit: float | None
    reason_codes: tuple[ReasonCode, ...]


@dataclass(frozen=True)
class RiskApproval:
    approved: bool
    approved_weights: Mapping[str, float]
    cash_weight: float
    action: str            # approve, cap, prior_weights, cash, reject
    reason_codes: tuple[ReasonCode, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OrderIntent:
    order_id: str
    symbol: str
    side: str
    execution_time: datetime
    target_notional: float
    reference_price: float
    reason_codes: tuple[ReasonCode, ...]


@dataclass(frozen=True)
class Fill:
    order_id: str
    symbol: str
    side: str
    fill_time: datetime
    quantity: float
    fill_price: float
    fee: float
    slippage_cost: float
    status: str
    reason_codes: tuple[ReasonCode, ...]


@dataclass(frozen=True)
class BacktestResult:
    experiment: str
    split: str
    equity_curve_path: str
    weights_path: str
    orders_path: str
    fills_path: str
    metrics: Mapping[str, float]
    data_hash: str
    config_hash: str
    git_commit: str
    final_test_lock_hash: str | None
```

Validate all timestamps, ranges, finite values, score/confidence ranges, side/status values and weight sums at construction or boundary functions.

## Protocols

```python
from typing import Protocol, Sequence
import pandas as pd


class MarketDataAdapter(Protocol):
    def fetch_ohlcv(self, symbols: Sequence[str], start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        ...


class SignalAgent(Protocol):
    name: str

    def fit(self, frame: pd.DataFrame, *, fit_cutoff: pd.Timestamp) -> None:
        ...

    def predict(self, frame: pd.DataFrame, context: AgentContext) -> list[AgentSignal]:
        ...


class AgentOrchestrator(Protocol):
    def run(self, frame: pd.DataFrame, context: AgentContext) -> list[AggregatedSignal]:
        ...


class PreAllocationRiskGate(Protocol):
    def constraints(
        self,
        signals: list[AggregatedSignal],
        context: AgentContext,
        market_snapshot: pd.DataFrame,
    ) -> RiskConstraints:
        ...


class PortfolioAllocator(Protocol):
    name: str

    def allocate(
        self,
        signals: pd.Series,
        historical_returns: pd.DataFrame,
        constraints: RiskConstraints,
        previous_weights: pd.Series,
    ) -> PortfolioProposal:
        ...


class RebalancePolicy(Protocol):
    def decide(
        self,
        proposal: PortfolioProposal,
        current_weights: pd.Series,
        context: AgentContext,
    ) -> RebalanceDecision:
        ...


class PostAllocationRiskGate(Protocol):
    def approve(
        self,
        proposal: PortfolioProposal,
        rebalance: RebalanceDecision,
        constraints: RiskConstraints,
        context: AgentContext,
        historical_returns: pd.DataFrame,
    ) -> RiskApproval:
        ...


class Broker(Protocol):
    def execute(
        self,
        orders: list[OrderIntent],
        market_snapshot: pd.DataFrame,
    ) -> list[Fill]:
        ...
```

## Weight and execution invariants

For every approved portfolio:

```text
all weights finite
0 <= risky weight <= applicable cap
0 <= cash weight <= 1
sum(risky weights) + cash weight == 1 within tolerance
no short positions
no leverage
blocked symbols have zero weight
execution_time > feature_cutoff
no fill without valid execution price
```

If capital is intentionally unallocated, it is explicit cash.

## Cost interface and invariants

The cost model takes orders/fills or risky-weight deltas, not cash as a fee-bearing asset.

```python
class CostModel(Protocol):
    def estimate_from_weight_deltas(
        self,
        target_risky_weights: pd.Series,
        pretrade_risky_weights: pd.Series,
        market_snapshot: pd.DataFrame,
        nav: float,
    ) -> float:
        ...
```

Required unit examples are specified in `04_EXPERIMENT_PROTOCOL.md`.

## Experiment API

Notebook-facing APIs must be simple and side-effect-controlled:

```python
result = run_level_2(
    config=config,
    market_data=market_data,
    instruments=instruments,
    split="validation",   # or "test" only with final lock
    artifacts_dir=Path("artifacts"),
)
```

No experiment depends on notebook globals. Test mode validates the final-test lock before computing results.

## Final-test lock API

```python
lock = create_final_test_lock(
    selected_config=selected_config,
    data_manifest=manifest,
    git_commit=git_commit,
    uv_lock_path=Path("uv.lock"),
)

validate_final_test_lock(lock, selected_config, manifest, git_commit)
```

## Artifact metadata

Every result file must include or reference:

```json
{
  "experiment": "level_2_ensemble",
  "split": "test",
  "created_at_utc": "...",
  "data_hash": "...",
  "config_hash": "...",
  "git_commit": "...",
  "uv_lock_hash": "...",
  "final_test_lock_hash": "...",
  "train_period": ["2021-01-01", "2023-12-31"],
  "validation_period": ["2024-01-01", "2024-12-31"],
  "test_period": ["2025-01-01", "2025-12-31"],
  "execution_convention": "next_open_open_to_open",
  "fee_bps_one_way": 10.0,
  "slippage_bps_one_way": 5.0,
  "seed": 42,
  "eligible_symbol_count": 0,
  "warnings": []
}
```
