"""Frozen typed records and protocols shared by all strategy levels."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Protocol

import pandas as pd

WEIGHT_TOLERANCE = 1e-8


class ReasonCode(StrEnum):
    """Shared reason codes for signals, risk controls and execution outcomes."""

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
    KILL_SWITCH = "kill_switch"
    TURNOVER_LIMIT = "turnover_limit"
    CONCENTRATION_LIMIT = "concentration_limit"
    AGENT_DISAGREEMENT = "agent_disagreement"
    MODEL_FAILURE = "model_failure"
    STALE_MODEL = "stale_model"
    OPTIMIZER_FAILURE = "optimizer_failure"
    WEIGHT_RECONCILIATION_FAILURE = "weight_reconciliation_failure"
    RECONCILIATION_FAILURE = "reconciliation_failure"
    DRIFT_ALERT = "drift_alert"
    HASH_MISMATCH = "hash_mismatch"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class FillStatus(StrEnum):
    FILLED = "filled"
    PARTIAL = "partial"
    REJECTED = "rejected"


class RiskAction(StrEnum):
    APPROVE = "approve"
    CAP = "cap"
    PRIOR_WEIGHTS = "prior_weights"
    CASH = "cash"
    REJECT = "reject"


class EventSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


def _as_utc(value: datetime, *, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        msg = f"{field_name} must be a datetime"
        raise TypeError(msg)
    if value.tzinfo is None:
        msg = f"{field_name} must be timezone-aware UTC"
        raise ValueError(msg)
    converted = value.astimezone(UTC)
    if converted != value:
        msg = f"{field_name} must already be normalized to UTC"
        raise ValueError(msg)
    return converted


def _finite(value: float | int, *, field_name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        msg = f"{field_name} must be finite"
        raise ValueError(msg)
    return number


def _range(value: float | int, *, field_name: str, low: float, high: float) -> float:
    number = _finite(value, field_name=field_name)
    if not low <= number <= high:
        msg = f"{field_name} must be in [{low}, {high}], got {number}"
        raise ValueError(msg)
    return number


def _positive(value: float | int, *, field_name: str) -> float:
    number = _finite(value, field_name=field_name)
    if number <= 0:
        msg = f"{field_name} must be positive"
        raise ValueError(msg)
    return number


def _non_negative(value: float | int, *, field_name: str) -> float:
    number = _finite(value, field_name=field_name)
    if number < 0:
        msg = f"{field_name} must be non-negative"
        raise ValueError(msg)
    return number


def _freeze_mapping(mapping: Mapping[str, Any], *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(mapping, Mapping):
        msg = f"{field_name} must be a mapping"
        raise TypeError(msg)
    return MappingProxyType(dict(mapping))


def _reason_tuple(reason_codes: Sequence[ReasonCode | str]) -> tuple[ReasonCode, ...]:
    if not reason_codes:
        msg = "reason_codes must not be empty"
        raise ValueError(msg)
    return tuple(
        code if isinstance(code, ReasonCode) else ReasonCode(code) for code in reason_codes
    )


def _validated_weights(
    weights: Mapping[str, float],
    *,
    cash_weight: float,
    field_name: str,
) -> Mapping[str, float]:
    if not isinstance(weights, Mapping):
        msg = f"{field_name} must be a mapping"
        raise TypeError(msg)
    validated = {
        str(symbol): _non_negative(weight, field_name=f"{field_name}[{symbol}]")
        for symbol, weight in weights.items()
    }
    cash = _range(cash_weight, field_name="cash_weight", low=0.0, high=1.0)
    total = sum(validated.values()) + cash
    if abs(total - 1.0) > WEIGHT_TOLERANCE:
        msg = f"{field_name} plus cash_weight must sum to 1.0, got {total}"
        raise ValueError(msg)
    return MappingProxyType(validated)


@dataclass(frozen=True)
class ResearchClock:
    """Explicit UTC timestamps for one completed-bar decision."""

    bar_start: datetime
    bar_end: datetime
    feature_cutoff: datetime
    decision_time: datetime
    execution_time: datetime

    def __post_init__(self) -> None:
        for name in ("bar_start", "bar_end", "feature_cutoff", "decision_time", "execution_time"):
            object.__setattr__(self, name, _as_utc(getattr(self, name), field_name=name))
        if not (
            self.bar_start
            < self.bar_end
            <= self.feature_cutoff
            <= self.decision_time
            <= self.execution_time
        ):
            msg = (
                "ResearchClock requires bar_start < bar_end <= feature_cutoff "
                "<= decision_time <= execution_time"
            )
            raise ValueError(msg)


@dataclass(frozen=True)
class AgentContext:
    clock: ResearchClock
    symbols: tuple[str, ...]
    model_fit_cutoff: datetime
    portfolio_nav: float
    current_weights: Mapping[str, float]
    health_state: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.symbols:
            msg = "symbols must not be empty"
            raise ValueError(msg)
        object.__setattr__(self, "symbols", tuple(str(symbol) for symbol in self.symbols))
        model_fit_cutoff = _as_utc(self.model_fit_cutoff, field_name="model_fit_cutoff")
        if model_fit_cutoff > self.clock.feature_cutoff:
            msg = "model_fit_cutoff cannot be after feature_cutoff"
            raise ValueError(msg)
        object.__setattr__(self, "model_fit_cutoff", model_fit_cutoff)
        object.__setattr__(
            self, "portfolio_nav", _positive(self.portfolio_nav, field_name="portfolio_nav")
        )
        current_weights = {
            str(symbol): _non_negative(weight, field_name=f"current_weights[{symbol}]")
            for symbol, weight in self.current_weights.items()
        }
        object.__setattr__(self, "current_weights", MappingProxyType(current_weights))
        object.__setattr__(
            self, "health_state", _freeze_mapping(self.health_state, field_name="health_state")
        )
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata, field_name="metadata"))


@dataclass(frozen=True)
class AgentSignal:
    symbol: str
    agent: str
    score: float
    confidence: float
    horizon_open_days: int
    fit_cutoff: datetime
    feature_cutoff: datetime
    reason_codes: tuple[ReasonCode, ...] = (ReasonCode.OK,)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.symbol or not self.agent:
            msg = "symbol and agent must be non-empty"
            raise ValueError(msg)
        object.__setattr__(
            self, "score", _range(self.score, field_name="score", low=-1.0, high=1.0)
        )
        object.__setattr__(
            self,
            "confidence",
            _range(self.confidence, field_name="confidence", low=0.0, high=1.0),
        )
        if self.horizon_open_days <= 0:
            msg = "horizon_open_days must be positive"
            raise ValueError(msg)
        fit_cutoff = _as_utc(self.fit_cutoff, field_name="fit_cutoff")
        feature_cutoff = _as_utc(self.feature_cutoff, field_name="feature_cutoff")
        if fit_cutoff > feature_cutoff:
            msg = "fit_cutoff cannot be after feature_cutoff"
            raise ValueError(msg)
        object.__setattr__(self, "fit_cutoff", fit_cutoff)
        object.__setattr__(self, "feature_cutoff", feature_cutoff)
        object.__setattr__(self, "reason_codes", _reason_tuple(self.reason_codes))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata, field_name="metadata"))


@dataclass(frozen=True)
class AggregatedSignal:
    symbol: str
    score: float
    confidence: float
    contributions: Mapping[str, float]
    disagreement: float
    reason_codes: tuple[ReasonCode, ...]

    def __post_init__(self) -> None:
        if not self.symbol:
            msg = "symbol must be non-empty"
            raise ValueError(msg)
        object.__setattr__(
            self, "score", _range(self.score, field_name="score", low=-1.0, high=1.0)
        )
        object.__setattr__(
            self,
            "confidence",
            _range(self.confidence, field_name="confidence", low=0.0, high=1.0),
        )
        object.__setattr__(
            self,
            "disagreement",
            _range(self.disagreement, field_name="disagreement", low=0.0, high=1.0),
        )
        contributions = {
            str(agent): _finite(value, field_name=f"contributions[{agent}]")
            for agent, value in self.contributions.items()
        }
        object.__setattr__(self, "contributions", MappingProxyType(contributions))
        object.__setattr__(self, "reason_codes", _reason_tuple(self.reason_codes))


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

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "decision_time", _as_utc(self.decision_time, field_name="decision_time")
        )
        object.__setattr__(
            self,
            "max_gross_exposure",
            _range(self.max_gross_exposure, field_name="max_gross_exposure", low=0.0, high=1.0),
        )
        caps = {
            str(symbol): _range(cap, field_name=f"per_asset_caps[{symbol}]", low=0.0, high=1.0)
            for symbol, cap in self.per_asset_caps.items()
        }
        object.__setattr__(self, "per_asset_caps", MappingProxyType(caps))
        object.__setattr__(
            self, "blocked_symbols", tuple(str(symbol) for symbol in self.blocked_symbols)
        )
        if self.volatility_target is not None:
            object.__setattr__(
                self,
                "volatility_target",
                _positive(self.volatility_target, field_name="volatility_target"),
            )
        if self.turnover_cap is not None:
            object.__setattr__(
                self,
                "turnover_cap",
                _range(self.turnover_cap, field_name="turnover_cap", low=0.0, high=1.0),
            )
        object.__setattr__(self, "reason_codes", _reason_tuple(self.reason_codes))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata, field_name="metadata"))


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

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "decision_time", _as_utc(self.decision_time, field_name="decision_time")
        )
        object.__setattr__(
            self,
            "target_weights",
            _validated_weights(
                self.target_weights,
                cash_weight=self.cash_weight,
                field_name="target_weights",
            ),
        )
        object.__setattr__(
            self,
            "cash_weight",
            _range(self.cash_weight, field_name="cash_weight", low=0.0, high=1.0),
        )
        if not self.optimizer_status:
            msg = "optimizer_status must be non-empty"
            raise ValueError(msg)
        object.__setattr__(
            self,
            "expected_turnover",
            _range(self.expected_turnover, field_name="expected_turnover", low=0.0, high=2.0),
        )
        if self.objective_value is not None:
            object.__setattr__(
                self, "objective_value", _finite(self.objective_value, field_name="objective_value")
            )
        object.__setattr__(self, "reason_codes", _reason_tuple(self.reason_codes))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata, field_name="metadata"))


@dataclass(frozen=True)
class RebalanceDecision:
    decision_time: datetime
    should_rebalance: bool
    trigger_codes: tuple[str, ...]
    expected_net_benefit: float | None
    reason_codes: tuple[ReasonCode, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "decision_time", _as_utc(self.decision_time, field_name="decision_time")
        )
        object.__setattr__(self, "trigger_codes", tuple(str(code) for code in self.trigger_codes))
        if self.expected_net_benefit is not None:
            object.__setattr__(
                self,
                "expected_net_benefit",
                _finite(self.expected_net_benefit, field_name="expected_net_benefit"),
            )
        object.__setattr__(self, "reason_codes", _reason_tuple(self.reason_codes))


@dataclass(frozen=True)
class RiskApproval:
    approved: bool
    approved_weights: Mapping[str, float]
    cash_weight: float
    action: str
    reason_codes: tuple[ReasonCode, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "approved_weights",
            _validated_weights(
                self.approved_weights,
                cash_weight=self.cash_weight,
                field_name="approved_weights",
            ),
        )
        object.__setattr__(
            self,
            "cash_weight",
            _range(self.cash_weight, field_name="cash_weight", low=0.0, high=1.0),
        )
        RiskAction(self.action)
        object.__setattr__(self, "reason_codes", _reason_tuple(self.reason_codes))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata, field_name="metadata"))


@dataclass(frozen=True)
class ExecutableTargetWeights:
    """Risk-resolved target weights ready for later order-intent generation."""

    risky_weights: Mapping[str, float]
    cash_weight: float
    action: str
    reason_codes: tuple[ReasonCode, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "risky_weights",
            _validated_weights(
                self.risky_weights,
                cash_weight=self.cash_weight,
                field_name="risky_weights",
            ),
        )
        object.__setattr__(
            self,
            "cash_weight",
            _range(self.cash_weight, field_name="cash_weight", low=0.0, high=1.0),
        )
        RiskAction(self.action)
        object.__setattr__(self, "reason_codes", _reason_tuple(self.reason_codes))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata, field_name="metadata"))


@dataclass(frozen=True)
class MonitoringEvent:
    """Reason-coded event suitable for health summaries and notebook traces."""

    timestamp: datetime
    component: str
    severity: str
    reason_codes: tuple[ReasonCode, ...]
    message: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", _as_utc(self.timestamp, field_name="timestamp"))
        if not self.component or not self.message:
            msg = "component and message must be non-empty"
            raise ValueError(msg)
        EventSeverity(self.severity)
        object.__setattr__(self, "reason_codes", _reason_tuple(self.reason_codes))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata, field_name="metadata"))


@dataclass(frozen=True)
class DecisionTrace:
    """Auditable record from agent outputs through risk approval."""

    clock: ResearchClock
    signals: tuple[AgentSignal, ...]
    aggregated_signals: tuple[AggregatedSignal, ...]
    constraints: RiskConstraints | None
    proposal: PortfolioProposal | None
    approval: RiskApproval | None
    events: tuple[MonitoringEvent, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "signals", tuple(self.signals))
        object.__setattr__(self, "aggregated_signals", tuple(self.aggregated_signals))
        object.__setattr__(self, "events", tuple(self.events))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata, field_name="metadata"))


@dataclass(frozen=True)
class OrderIntent:
    order_id: str
    symbol: str
    side: str
    execution_time: datetime
    target_notional: float
    reference_price: float
    reason_codes: tuple[ReasonCode, ...]

    def __post_init__(self) -> None:
        if not self.order_id or not self.symbol:
            msg = "order_id and symbol must be non-empty"
            raise ValueError(msg)
        OrderSide(self.side)
        object.__setattr__(
            self, "execution_time", _as_utc(self.execution_time, field_name="execution_time")
        )
        object.__setattr__(
            self,
            "target_notional",
            _non_negative(self.target_notional, field_name="target_notional"),
        )
        object.__setattr__(
            self, "reference_price", _positive(self.reference_price, field_name="reference_price")
        )
        object.__setattr__(self, "reason_codes", _reason_tuple(self.reason_codes))


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

    def __post_init__(self) -> None:
        if not self.order_id or not self.symbol:
            msg = "order_id and symbol must be non-empty"
            raise ValueError(msg)
        OrderSide(self.side)
        FillStatus(self.status)
        object.__setattr__(self, "fill_time", _as_utc(self.fill_time, field_name="fill_time"))
        object.__setattr__(self, "quantity", _non_negative(self.quantity, field_name="quantity"))
        object.__setattr__(self, "fill_price", _positive(self.fill_price, field_name="fill_price"))
        object.__setattr__(self, "fee", _non_negative(self.fee, field_name="fee"))
        object.__setattr__(
            self, "slippage_cost", _non_negative(self.slippage_cost, field_name="slippage_cost")
        )
        object.__setattr__(self, "reason_codes", _reason_tuple(self.reason_codes))


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

    def __post_init__(self) -> None:
        for name in (
            "experiment",
            "split",
            "equity_curve_path",
            "orders_path",
            "fills_path",
            "data_hash",
            "config_hash",
            "git_commit",
        ):
            if not getattr(self, name):
                msg = f"{name} must be non-empty"
                raise ValueError(msg)
        metrics = {
            str(key): _finite(value, field_name=f"metrics[{key}]")
            for key, value in self.metrics.items()
        }
        object.__setattr__(self, "metrics", MappingProxyType(metrics))


class MarketDataAdapter(Protocol):
    def fetch_ohlcv(
        self,
        symbols: Sequence[str],
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> pd.DataFrame: ...


class SignalAgent(Protocol):
    name: str

    def fit(self, frame: pd.DataFrame, *, fit_cutoff: pd.Timestamp) -> None: ...

    def predict(self, frame: pd.DataFrame, context: AgentContext) -> list[AgentSignal]: ...


class AgentOrchestrator(Protocol):
    def run(self, frame: pd.DataFrame, context: AgentContext) -> list[AggregatedSignal]: ...


class PreAllocationRiskGate(Protocol):
    def constraints(
        self,
        signals: list[AggregatedSignal],
        context: AgentContext,
        market_snapshot: pd.DataFrame,
    ) -> RiskConstraints: ...


class PortfolioAllocator(Protocol):
    name: str

    def allocate(
        self,
        signals: pd.Series,
        historical_returns: pd.DataFrame,
        constraints: RiskConstraints,
        previous_weights: pd.Series,
    ) -> PortfolioProposal: ...


class RebalancePolicy(Protocol):
    def decide(
        self,
        proposal: PortfolioProposal,
        current_weights: pd.Series,
        context: AgentContext,
    ) -> RebalanceDecision: ...


class PostAllocationRiskGate(Protocol):
    def approve(
        self,
        proposal: PortfolioProposal,
        rebalance: RebalanceDecision,
        constraints: RiskConstraints,
        context: AgentContext,
        historical_returns: pd.DataFrame,
    ) -> RiskApproval: ...


class Broker(Protocol):
    def execute(
        self,
        orders: list[OrderIntent],
        market_snapshot: pd.DataFrame,
    ) -> list[Fill]: ...


class CostModel(Protocol):
    def estimate_from_weight_deltas(
        self,
        target_risky_weights: pd.Series,
        pretrade_risky_weights: pd.Series,
        market_snapshot_or_nav: pd.DataFrame | float,
        nav: float | None = None,
    ) -> Any: ...
