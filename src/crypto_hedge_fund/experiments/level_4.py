"""Level 4 dynamic small-portfolio rebalancing on validation data only."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from crypto_hedge_fund.artifacts import ArtifactProvenance, BacktestArtifactWriter
from crypto_hedge_fund.clock import build_daily_research_clock
from crypto_hedge_fund.config import load_config
from crypto_hedge_fund.execution import BacktestRunResult, CostAssumptions, PanelMarketData
from crypto_hedge_fund.execution.broker import SimulatedBroker
from crypto_hedge_fund.experiments.level_3 import (
    _allocators as _level3_allocators,
)
from crypto_hedge_fund.experiments.level_3 import (
    _benchmark_with_initial_capital_baseline,
    _cost_assumptions,
    _enrich_equity,
    _historical_open_returns,
    _load_instruments,
    _load_market_frame,
    _normalize_instruments,
    _normalize_market_frame,
    _portfolio_diagnostics,
    _snapshot_for_bar,
    _trace_to_dict,
    _trim_result,
    _utc,
    _validate_trailing_12_months,
    _with_initial_capital_baseline,
    build_level_3_target_schedule,
    select_level_3_universe,
)
from crypto_hedge_fund.metrics import calculate_performance_metrics
from crypto_hedge_fund.portfolio.rebalance import DynamicRebalancePolicy
from crypto_hedge_fund.provenance import (
    canonical_config_hash,
    file_sha256,
    git_commit,
    git_diff_sha256,
    git_worktree_dirty,
)
from crypto_hedge_fund.risk import (
    PostAllocationRiskPolicy,
    PreAllocationRiskPolicy,
    resolve_risk_approval_targets,
)
from crypto_hedge_fund.types import (
    AgentContext,
    AgentSignal,
    AggregatedSignal,
    DecisionTrace,
    PortfolioProposal,
    ReasonCode,
)

LEVEL_NAME = "level_4"
RUN_LABEL = "level_4_validation_dynamic_rebalance"


@dataclass(frozen=True)
class Level4ValidationResult:
    """Paths and selected settings from a Level 4 validation run."""

    metrics: dict[str, Any]
    artifact_paths: dict[str, Path]
    figure_path: Path
    rebalance_log_path: Path
    trace_path: Path
    final_vintage_plan_path: Path | None
    selected_policy: str
    symbols: tuple[str, ...]


@dataclass(frozen=True)
class _PolicyResult:
    name: str
    schedule: pd.DataFrame
    rebalance_log: pd.DataFrame
    traces: list[DecisionTrace]
    net_result: BacktestRunResult
    gross_result: BacktestRunResult
    metrics: dict[str, Any]
    is_benchmark: bool = False


def run_level_4_validation(
    *,
    config_path: str | Path = Path("configs/default.yaml"),
    artifacts_dir: str | Path | None = None,
    market_frame: pd.DataFrame | None = None,
    instruments: pd.DataFrame | None = None,
) -> Level4ValidationResult:
    """Run validation-only Level 4 dynamic rebalancing and write artifacts."""

    config = load_config(config_path, resolve_paths=True)
    level_config = _level4_config(config)
    validation_start = _utc(level_config["validation_evaluation_start"])
    validation_end = _utc(level_config["validation_evaluation_end"])
    test_start = _utc(config["splits"]["test_start"])
    if validation_end >= test_start:
        msg = "Level 4 validation evaluation must end before final-test start"
        raise ValueError(msg)

    estimation_start = _utc(level_config["validation_estimation_start"])
    estimation_end = _utc(level_config["validation_estimation_end"])
    _validate_trailing_12_months(estimation_start, estimation_end)
    if estimation_end >= validation_start:
        msg = "Level 4 initial estimation window must end before validation starts"
        raise ValueError(msg)

    output_dir = (
        Path(artifacts_dir) if artifacts_dir is not None else Path(config["paths"]["artifacts"])
    )
    frame = (
        _load_market_frame(config, end=validation_end)
        if market_frame is None
        else _normalize_market_frame(market_frame, end=validation_end)
    )
    instruments_frame = (
        _load_instruments(config) if instruments is None else _normalize_instruments(instruments)
    )
    universe = select_level_3_universe(
        frame,
        instruments_frame,
        config=_level4_as_level3_config(config),
        estimation_start=estimation_start,
        estimation_end=estimation_end,
        cutoff_bar_start=_utc(level_config["validation_cutoff"]),
    )
    symbols = tuple(str(symbol) for symbol in universe["symbol"].tolist())
    market = PanelMarketData.from_ohlcv(frame.loc[frame["symbol"].isin(symbols)])
    cost_assumptions = _cost_assumptions(config)
    allocator = _selected_allocator(config)

    static_result = _run_static_benchmark(
        frame=frame,
        market=market,
        symbols=symbols,
        allocator=allocator,
        config=config,
        estimation_start=estimation_start,
        estimation_end=estimation_end,
        validation_start=validation_start,
        validation_end=validation_end,
        cost_assumptions=cost_assumptions,
    )
    dynamic_results: list[_PolicyResult] = []
    for policy in _policies(config):
        schedule, log, traces = build_level_4_target_schedule(
            frame=frame,
            symbols=symbols,
            allocator=allocator,
            policy=policy,
            config=config,
            initial_estimation_end=estimation_end,
            validation_start=validation_start,
            validation_end=validation_end,
        )
        net_result = _trim_result(
            SimulatedBroker(
                market,
                initial_capital=float(config["backtest"]["initial_capital_usd"]),
                cost_assumptions=cost_assumptions,
            ).run(schedule, end_time=validation_end, run_label=f"{RUN_LABEL}_{policy.name}"),
            start=validation_start,
            end=validation_end,
        )
        gross_result = _trim_result(
            SimulatedBroker(
                market,
                initial_capital=float(config["backtest"]["initial_capital_usd"]),
                cost_assumptions=CostAssumptions(fee_bps_one_way=0.0, slippage_bps_one_way=0.0),
            ).run(schedule, end_time=validation_end, run_label=f"{RUN_LABEL}_{policy.name}_gross"),
            start=validation_start,
            end=validation_end,
        )
        dynamic_results.append(
            _PolicyResult(
                name=policy.name,
                schedule=schedule,
                rebalance_log=log,
                traces=traces,
                net_result=net_result,
                gross_result=gross_result,
                metrics={},
            )
        )

    benchmark_series = static_result.net_result.equity.set_index("timestamp")["nav"]
    all_results = [static_result, *dynamic_results]
    enriched: list[_PolicyResult] = []
    for result in all_results:
        metrics = _level4_metrics(result, benchmark_nav=benchmark_series, config=config)
        metrics.update(_portfolio_diagnostics_for_schedule(result.schedule, universe, config))
        enriched.append(
            _PolicyResult(
                name=result.name,
                schedule=result.schedule,
                rebalance_log=result.rebalance_log,
                traces=result.traces,
                net_result=_enrich_equity(result.net_result, result.gross_result, benchmark_series),
                gross_result=result.gross_result,
                metrics=metrics,
                is_benchmark=result.is_benchmark,
            )
        )

    selected = _select_policy([item for item in enriched if not item.is_benchmark], config=config)
    selection_metadata = _selection_metadata(enriched, selected=selected, config=config)
    for result in enriched:
        result.metrics.update(selection_metadata)

    provenance = _provenance(
        config=config,
        symbols=symbols,
        validation_start=validation_start,
        validation_end=validation_end,
        estimation_start=estimation_start,
        estimation_end=estimation_end,
        cost_assumptions=cost_assumptions,
        selected_policy=selected.name,
    )
    artifact_paths = _write_level4_artifacts(
        enriched,
        selected_policy=selected.name,
        output_dir=output_dir,
        provenance=provenance,
    )
    figure_path = _write_equity_figure(enriched, output_dir, provenance)
    rebalance_log_path = _write_rebalance_log(
        enriched,
        selected_policy=selected.name,
        path=output_dir / "monitoring" / "level_4_rebalance_log.parquet",
        provenance=provenance,
    )
    trace_path = _write_decision_trace(
        selected=selected,
        results=enriched,
        universe=universe,
        path=output_dir / "monitoring" / "level_4_decision_trace.json",
        provenance=provenance,
        config=config,
        selection_metadata=selection_metadata,
    )
    final_plan_path = None
    if bool(level_config.get("write_final_vintage_plan", True)):
        final_plan_path = _write_final_vintage_plan(config, output_dir, provenance)

    return Level4ValidationResult(
        metrics={f"{selected.name}_{key}": value for key, value in selected.metrics.items()},
        artifact_paths=artifact_paths,
        figure_path=figure_path,
        rebalance_log_path=rebalance_log_path,
        trace_path=trace_path,
        final_vintage_plan_path=final_plan_path,
        selected_policy=selected.name,
        symbols=symbols,
    )


def build_level_4_target_schedule(
    *,
    frame: pd.DataFrame,
    symbols: tuple[str, ...],
    allocator: Any,
    policy: DynamicRebalancePolicy,
    config: dict[str, Any],
    initial_estimation_end: pd.Timestamp,
    validation_start: pd.Timestamp,
    validation_end: pd.Timestamp,
) -> tuple[pd.DataFrame, pd.DataFrame, list[DecisionTrace]]:
    """Build a dynamic target schedule from rolling causal estimates."""

    normalized = _normalize_market_frame(frame, end=validation_end)
    decision_bars = pd.date_range(
        initial_estimation_end,
        validation_end - pd.Timedelta(days=1),
        freq="D",
        tz="UTC",
    )
    if decision_bars.empty:
        msg = "Level 4 validation period leaves no executable decision bars"
        raise ValueError(msg)

    last_approved = pd.Series(dict.fromkeys(symbols, 0.0), dtype="float64")
    last_execution_time: pd.Timestamp | None = None
    previous_rebalance_time: pd.Timestamp | None = None
    previous_scores: pd.Series | None = None
    schedule_rows: list[pd.Series] = []
    log_rows: list[dict[str, object]] = []
    traces: list[DecisionTrace] = []

    for decision_bar in decision_bars:
        clock = build_daily_research_clock(decision_bar.to_pydatetime())
        execution_time = pd.Timestamp(clock.execution_time)
        rolling_start = decision_bar - pd.DateOffset(months=12) + pd.Timedelta(days=1)
        returns = _historical_open_returns(
            normalized,
            symbols=symbols,
            start=rolling_start,
            through=decision_bar,
        )
        current_weights = _drifted_current_weights(
            normalized,
            symbols=symbols,
            previous_target=last_approved,
            previous_execution_time=last_execution_time,
            decision_bar=decision_bar,
        )
        signal_series, signals, aggregated = _rolling_signals(
            normalized,
            symbols=symbols,
            returns=returns,
            decision_bar=decision_bar,
            clock_feature_cutoff=pd.Timestamp(clock.feature_cutoff),
        )
        score_change = (
            1.0
            if previous_scores is None
            else float((signal_series - previous_scores.reindex(symbols).fillna(0.0)).abs().max())
        )
        realized_vol = _portfolio_realized_volatility(returns, config)
        risk_trigger_active = realized_vol >= float(
            _level4_config(config).get("risk_rebalance_volatility_threshold_annual", 0.80)
        )
        context = AgentContext(
            clock=clock,
            symbols=symbols,
            model_fit_cutoff=pd.Timestamp(clock.feature_cutoff).to_pydatetime(),
            portfolio_nav=float(config["backtest"]["initial_capital_usd"]),
            current_weights=current_weights.to_dict(),
            health_state={
                "aggregate_score_change": score_change,
                "risk_trigger_active": risk_trigger_active,
                "realized_volatility": realized_vol if risk_trigger_active else 0.0,
            },
            metadata={
                "level": LEVEL_NAME,
                "split": "validation",
                "policy": policy.name,
                "previous_rebalance_time": previous_rebalance_time,
                "rolling_start": rolling_start.isoformat(),
                "rolling_end": decision_bar.isoformat(),
            },
        )
        snapshot = _snapshot_with_capacity(normalized, symbols, decision_bar, config)
        constraints = _pre_risk(config).constraints(list(aggregated), context, snapshot)
        proposal = allocator.allocate(signal_series, returns, constraints, current_weights)
        proposal = _proposal_with_dynamic_metadata(
            proposal,
            expected_benefit_scale=float(
                _level4_config(config).get("expected_benefit_scale", 0.002)
            ),
            signal_series=signal_series,
            risk_trigger_active=risk_trigger_active,
            realized_volatility=realized_vol,
        )
        rebalance = policy.decide(proposal, current_weights, context)
        approval = _post_risk(config).approve(proposal, rebalance, constraints, context, returns)
        executable = resolve_risk_approval_targets(approval, context)
        approved_weights = pd.Series(
            {symbol: float(executable.risky_weights.get(symbol, 0.0)) for symbol in symbols},
            dtype="float64",
        )
        should_submit = executable.action in {"approve", "cap", "cash"} and (
            rebalance.should_rebalance or executable.action == "cash"
        )
        if should_submit:
            schedule_rows.append(pd.Series(approved_weights, name=decision_bar))
            last_approved = approved_weights
            last_execution_time = execution_time
            previous_rebalance_time = pd.Timestamp(clock.decision_time)
        previous_scores = signal_series.copy()
        trace = DecisionTrace(
            clock=clock,
            signals=signals,
            aggregated_signals=aggregated,
            constraints=constraints,
            proposal=proposal,
            approval=approval,
            metadata={
                "level": LEVEL_NAME,
                "split": "validation",
                "policy": policy.name,
                "rebalance_decision": {
                    "should_rebalance": rebalance.should_rebalance,
                    "trigger_codes": list(rebalance.trigger_codes),
                    "expected_net_benefit": rebalance.expected_net_benefit,
                    "reason_codes": [code.value for code in rebalance.reason_codes],
                },
                "execution_time": execution_time.isoformat(),
                "resolved_action": executable.action,
            },
        )
        traces.append(trace)
        log_rows.append(
            _rebalance_log_row(
                policy=policy,
                decision_bar=decision_bar,
                execution_time=execution_time,
                current_weights=current_weights,
                proposal=proposal,
                rebalance=rebalance,
                approval=approval,
                approved_weights=approved_weights,
                score_change=score_change,
                realized_volatility=realized_vol,
                risk_trigger_active=risk_trigger_active,
                submitted=should_submit,
            )
        )

    if not schedule_rows:
        msg = f"Level 4 policy {policy.name} produced no executable schedule"
        raise ValueError(msg)
    schedule = pd.DataFrame(schedule_rows).sort_index(kind="mergesort")
    schedule.index = pd.DatetimeIndex(schedule.index, tz="UTC")
    return schedule, pd.DataFrame(log_rows), traces


def _run_static_benchmark(
    *,
    frame: pd.DataFrame,
    market: PanelMarketData,
    symbols: tuple[str, ...],
    allocator: Any,
    config: dict[str, Any],
    estimation_start: pd.Timestamp,
    estimation_end: pd.Timestamp,
    validation_start: pd.Timestamp,
    validation_end: pd.Timestamp,
    cost_assumptions: CostAssumptions,
) -> _PolicyResult:
    schedule, trace = build_level_3_target_schedule(
        frame=frame,
        symbols=symbols,
        allocator=allocator,
        config=_level4_as_level3_config(config),
        estimation_start=estimation_start,
        estimation_end=estimation_end,
        evaluation_start=validation_start,
        previous_weights=pd.Series(dict.fromkeys(symbols, 0.0), dtype="float64"),
    )
    net_result = _trim_result(
        SimulatedBroker(
            market,
            initial_capital=float(config["backtest"]["initial_capital_usd"]),
            cost_assumptions=cost_assumptions,
        ).run(schedule, end_time=validation_end, run_label=f"{RUN_LABEL}_static_level3"),
        start=validation_start,
        end=validation_end,
    )
    gross_result = _trim_result(
        SimulatedBroker(
            market,
            initial_capital=float(config["backtest"]["initial_capital_usd"]),
            cost_assumptions=CostAssumptions(fee_bps_one_way=0.0, slippage_bps_one_way=0.0),
        ).run(schedule, end_time=validation_end, run_label=f"{RUN_LABEL}_static_level3_gross"),
        start=validation_start,
        end=validation_end,
    )
    log = pd.DataFrame(
        [
            {
                "policy": "static_level3_benchmark",
                "decision_bar_start": estimation_end,
                "execution_time": validation_start,
                "should_rebalance": True,
                "submitted_to_broker": True,
                "trigger_codes": json.dumps(["static_initial_allocation"]),
                "skipped_reason": "",
                "before_weights": json.dumps(dict.fromkeys(symbols, 0.0)),
                "candidate_weights": json.dumps(schedule.iloc[0].to_dict(), sort_keys=True),
                "approved_weights": json.dumps(schedule.iloc[0].to_dict(), sort_keys=True),
                "approved_cash_weight": float(1.0 - schedule.iloc[0].sum()),
                "expected_turnover": float(schedule.iloc[0].sum()),
                "estimated_cost_fraction": float(
                    schedule.iloc[0].sum()
                    * (
                        float(config["backtest"]["fee_bps_one_way"])
                        + float(config["backtest"]["slippage_bps_one_way"])
                    )
                    / 10_000.0
                ),
                "max_weight_drift": float(schedule.iloc[0].max()),
                "score_change": 0.0,
                "realized_volatility": 0.0,
                "risk_trigger_active": False,
                "approval_action": trace.approval.action if trace.approval else "",
                "reason_codes": json.dumps(
                    [code.value for code in trace.approval.reason_codes] if trace.approval else []
                ),
            }
        ]
    )
    return _PolicyResult(
        name="static_level3_benchmark",
        schedule=schedule,
        rebalance_log=log,
        traces=[trace],
        net_result=net_result,
        gross_result=gross_result,
        metrics={},
        is_benchmark=True,
    )


def _level4_config(config: dict[str, Any]) -> dict[str, Any]:
    if "level_4" not in config:
        msg = "config is missing level_4"
        raise ValueError(msg)
    return dict(config["level_4"])


def _level4_as_level3_config(config: dict[str, Any]) -> dict[str, Any]:
    merged = dict(config)
    level3 = dict(config.get("level_3", {}))
    level4 = _level4_config(config)
    for key in (
        "small_size",
        "validation_cutoff",
        "validation_estimation_start",
        "validation_estimation_end",
        "validation_evaluation_start",
        "validation_evaluation_end",
        "final_cutoff",
        "final_estimation_start",
        "final_estimation_end",
        "final_evaluation_start",
        "final_evaluation_end",
        "min_estimation_days",
        "covariance_shrinkage",
        "cvar_tail_fraction",
        "cost_buffer_weight",
        "min_cash_buffer",
        "min_dollar_volume",
        "write_final_vintage_plan",
    ):
        if key in level4:
            level3[key] = level4[key]
    level3["selection_metric"] = level4.get("selection_metric", level3.get("selection_metric"))
    merged["level_3"] = level3
    portfolio = dict(config["portfolio"])
    portfolio["small_size"] = int(level4.get("small_size", portfolio["small_size"]))
    merged["portfolio"] = portfolio
    return merged


def _selected_allocator(config: dict[str, Any]) -> Any:
    allocator_name = str(_level4_config(config).get("allocator", "cvar_downside"))
    allocators = _level3_allocators(_level4_as_level3_config(config))
    if allocator_name not in allocators:
        msg = f"unsupported Level 4 allocator: {allocator_name}"
        raise ValueError(msg)
    return allocators[allocator_name]


def _policies(config: dict[str, Any]) -> list[DynamicRebalancePolicy]:
    level_config = _level4_config(config)
    cost_rate = (
        float(config["backtest"]["fee_bps_one_way"])
        + float(config["backtest"]["slippage_bps_one_way"])
    ) / 10_000.0
    policies = []
    for raw in level_config.get("policies", []):
        item = dict(raw)
        policies.append(
            DynamicRebalancePolicy(
                name=str(item["name"]),
                calendar=str(item.get("calendar", config["rebalance"]["small_calendar"])),
                drift_threshold_abs=float(
                    item.get("drift_threshold_abs", config["rebalance"]["drift_threshold_abs"])
                ),
                score_change_threshold=float(
                    item.get(
                        "score_change_threshold",
                        config["rebalance"]["score_change_threshold"],
                    )
                ),
                risk_trigger=bool(item.get("risk_trigger", config["rebalance"]["risk_trigger"])),
                min_trade_abs=float(item.get("min_trade_abs", level_config["min_trade_abs"])),
                turnover_cap=float(item.get("turnover_cap", config["portfolio"]["turnover_cap"])),
                one_way_cost_rate=cost_rate,
                min_expected_net_benefit=float(item.get("min_expected_net_benefit", -1.0)),
                require_positive_net_benefit=bool(item.get("require_positive_net_benefit", False)),
            )
        )
    if not policies:
        msg = "Level 4 requires at least one dynamic rebalance policy"
        raise ValueError(msg)
    return policies


def _pre_risk(config: dict[str, Any]) -> PreAllocationRiskPolicy:
    level_config = _level4_config(config)
    return PreAllocationRiskPolicy(
        max_gross_exposure=float(config["portfolio"]["max_gross_exposure"]),
        max_per_asset_weight=float(config["portfolio"]["small_max_weight"]),
        cost_buffer_weight=float(level_config.get("cost_buffer_weight", 0.005)),
        min_dollar_volume=float(level_config.get("min_dollar_volume", 0.0)),
        max_stale_data_days=0,
        max_model_age_days=370,
        max_agent_disagreement=float(config["risk"]["max_agent_disagreement"]),
        volatility_target=None,
        turnover_cap=float(config["portfolio"]["turnover_cap"]),
    )


def _post_risk(config: dict[str, Any]) -> PostAllocationRiskPolicy:
    level_config = _level4_config(config)
    return PostAllocationRiskPolicy(
        max_drawdown_stop=float(config["risk"]["max_drawdown_stop"]),
        high_volatility_threshold=float(config["risk"]["high_volatility_threshold_annual"]),
        min_cash_buffer=float(level_config.get("min_cash_buffer", 0.005)),
        annualization_periods=int(config["backtest"]["annualization_periods"]),
    )


def _snapshot_with_capacity(
    frame: pd.DataFrame,
    symbols: tuple[str, ...],
    decision_bar: pd.Timestamp,
    config: dict[str, Any],
) -> pd.DataFrame:
    snapshot = _snapshot_for_bar(frame, symbols=symbols, bar_start=decision_bar)
    if snapshot.empty:
        return snapshot
    lookback = int(config["liquidity"]["adv_lookback_days"])
    start = decision_bar - pd.Timedelta(days=lookback - 1)
    liquidity = frame.loc[
        (frame["bar_start_utc"] >= start)
        & (frame["bar_start_utc"] <= decision_bar)
        & (frame["symbol"].isin(symbols)),
        ["symbol", "dollar_volume"],
    ]
    adv = liquidity.groupby("symbol")["dollar_volume"].mean()
    aum = float(config["liquidity"]["assumed_aum_usd"])
    max_participation = float(config["liquidity"]["max_participation"])
    capacity_weight = (adv * max_participation / aum).clip(lower=0.0)
    snapshot["max_weight_by_liquidity"] = snapshot["symbol"].map(capacity_weight).fillna(0.0)
    return snapshot


def _rolling_signals(
    frame: pd.DataFrame,
    *,
    symbols: tuple[str, ...],
    returns: pd.DataFrame,
    decision_bar: pd.Timestamp,
    clock_feature_cutoff: pd.Timestamp,
) -> tuple[pd.Series, tuple[AgentSignal, ...], tuple[AggregatedSignal, ...]]:
    scores: dict[str, float] = {}
    signals: list[AgentSignal] = []
    aggregated: list[AggregatedSignal] = []
    for symbol in symbols:
        series = returns.get(symbol, pd.Series(dtype="float64")).dropna()
        short = float(series.tail(30).mean()) if len(series) >= 30 else 0.0
        long = float(series.tail(90).mean()) if len(series) >= 90 else short
        vol = float(series.tail(60).std(ddof=0)) if len(series) >= 2 else 0.0
        raw_score = (short + 0.5 * long) / max(vol, 1e-8)
        score = max(-1.0, min(1.0, raw_score / 5.0))
        confidence = max(0.05, min(1.0, len(series) / 365.0))
        scores[symbol] = score
        agent_signal = AgentSignal(
            symbol=symbol,
            agent="level4_rolling_signal",
            score=score,
            confidence=confidence,
            horizon_open_days=30,
            fit_cutoff=clock_feature_cutoff.to_pydatetime(),
            feature_cutoff=clock_feature_cutoff.to_pydatetime(),
            reason_codes=(ReasonCode.OK,),
            metadata={
                "decision_bar_start": decision_bar.isoformat(),
                "short_return_mean": short,
                "long_return_mean": long,
                "realized_volatility_daily": vol,
            },
        )
        signals.append(agent_signal)
        aggregated.append(
            AggregatedSignal(
                symbol=symbol,
                score=score,
                confidence=confidence,
                contributions={"level4_rolling_signal": score},
                disagreement=0.0,
                reason_codes=(ReasonCode.OK,),
            )
        )
    return pd.Series(scores, dtype="float64"), tuple(signals), tuple(aggregated)


def _proposal_with_dynamic_metadata(
    proposal: PortfolioProposal,
    *,
    expected_benefit_scale: float,
    signal_series: pd.Series,
    risk_trigger_active: bool,
    realized_volatility: float,
) -> PortfolioProposal:
    weights = pd.Series(proposal.target_weights, dtype="float64")
    expected_score = float((weights * signal_series.reindex(weights.index).fillna(0.0)).sum())
    metadata = {
        **dict(proposal.metadata),
        "expected_gross_benefit": max(0.0, expected_score) * expected_benefit_scale,
        "weighted_signal_score": expected_score,
        "risk_trigger_active": risk_trigger_active,
        "realized_volatility": realized_volatility,
    }
    return PortfolioProposal(
        decision_time=proposal.decision_time,
        target_weights=dict(proposal.target_weights),
        cash_weight=proposal.cash_weight,
        optimizer_status=proposal.optimizer_status,
        expected_turnover=proposal.expected_turnover,
        objective_value=proposal.objective_value,
        reason_codes=proposal.reason_codes,
        metadata=metadata,
    )


def _drifted_current_weights(
    frame: pd.DataFrame,
    *,
    symbols: tuple[str, ...],
    previous_target: pd.Series,
    previous_execution_time: pd.Timestamp | None,
    decision_bar: pd.Timestamp,
) -> pd.Series:
    previous = previous_target.reindex(symbols, fill_value=0.0).astype("float64")
    if previous_execution_time is None or float(previous.sum()) <= 0:
        return pd.Series(dict.fromkeys(symbols, 0.0), dtype="float64")
    start_prices = _price_series(
        frame,
        symbols=symbols,
        timestamp=previous_execution_time,
        column="open",
    )
    end_prices = _price_series(frame, symbols=symbols, timestamp=decision_bar, column="close")
    rel = (end_prices / start_prices).replace([math.inf, -math.inf], pd.NA).fillna(0.0)
    risky_values = previous * rel
    cash = max(0.0, 1.0 - float(previous.sum()))
    total = float(risky_values.sum()) + cash
    if total <= 0:
        return pd.Series(dict.fromkeys(symbols, 0.0), dtype="float64")
    return (risky_values / total).reindex(symbols, fill_value=0.0).astype("float64")


def _price_series(
    frame: pd.DataFrame,
    *,
    symbols: tuple[str, ...],
    timestamp: pd.Timestamp,
    column: str,
) -> pd.Series:
    rows = frame.loc[
        (frame["bar_start_utc"] == timestamp) & (frame["symbol"].isin(symbols)),
        ["symbol", column],
    ]
    prices = rows.set_index("symbol")[column].astype("float64").reindex(symbols)
    if prices.isna().any():
        missing = prices.index[prices.isna()].tolist()
        msg = f"missing {column} prices for Level 4 drift calculation: {missing}"
        raise ValueError(msg)
    return prices


def _portfolio_realized_volatility(returns: pd.DataFrame, config: dict[str, Any]) -> float:
    if returns.empty:
        return 0.0
    recent = returns.tail(20).dropna(how="all")
    if recent.empty:
        return 0.0
    equal = recent.mean(axis=1)
    value = float(equal.std(ddof=0) * math.sqrt(int(config["backtest"]["annualization_periods"])))
    return value if math.isfinite(value) else 0.0


def _rebalance_log_row(
    *,
    policy: DynamicRebalancePolicy,
    decision_bar: pd.Timestamp,
    execution_time: pd.Timestamp,
    current_weights: pd.Series,
    proposal: PortfolioProposal,
    rebalance: Any,
    approval: Any,
    approved_weights: pd.Series,
    score_change: float,
    realized_volatility: float,
    risk_trigger_active: bool,
    submitted: bool,
) -> dict[str, object]:
    candidate = pd.Series(proposal.target_weights, dtype="float64")
    union = current_weights.index.union(candidate.index)
    drift = (
        candidate.reindex(union, fill_value=0.0) - current_weights.reindex(union, fill_value=0.0)
    ).abs()
    skipped = ""
    if not submitted:
        skipped = "held_prior_weights"
        if ReasonCode.TURNOVER_LIMIT in rebalance.reason_codes:
            skipped = "turnover_or_cost_control"
        elif "minimum_trade_not_met" in rebalance.trigger_codes:
            skipped = "minimum_trade_not_met"
        elif "no_trigger" in rebalance.trigger_codes:
            skipped = "no_rebalance_trigger"
    return {
        "policy": policy.name,
        "decision_bar_start": decision_bar,
        "execution_time": execution_time,
        "should_rebalance": bool(rebalance.should_rebalance),
        "submitted_to_broker": submitted,
        "trigger_codes": json.dumps(list(rebalance.trigger_codes), sort_keys=True),
        "skipped_reason": skipped,
        "before_weights": json.dumps(current_weights.to_dict(), sort_keys=True),
        "candidate_weights": json.dumps(dict(proposal.target_weights), sort_keys=True),
        "approved_weights": json.dumps(approved_weights.to_dict(), sort_keys=True),
        "approved_cash_weight": float(1.0 - approved_weights.sum()),
        "expected_turnover": float(proposal.expected_turnover),
        "estimated_cost_fraction": float(proposal.expected_turnover * policy.one_way_cost_rate),
        "max_weight_drift": float(drift.max()) if not drift.empty else 0.0,
        "score_change": score_change,
        "realized_volatility": realized_volatility,
        "risk_trigger_active": risk_trigger_active,
        "approval_action": str(approval.action),
        "reason_codes": json.dumps([code.value for code in approval.reason_codes], sort_keys=True),
    }


def _level4_metrics(
    result: _PolicyResult,
    *,
    benchmark_nav: pd.Series,
    config: dict[str, Any],
) -> dict[str, Any]:
    initial_capital = float(config["backtest"]["initial_capital_usd"])
    net_equity = _with_initial_capital_baseline(result.net_result.equity, initial_capital)
    gross_equity = _with_initial_capital_baseline(result.gross_result.equity, initial_capital)
    metric_benchmark = _benchmark_for_equity(
        benchmark_nav,
        equity=net_equity,
        initial_capital=initial_capital,
    )
    net = calculate_performance_metrics(
        net_equity,
        periods_per_year=int(config["backtest"]["annualization_periods"]),
        risk_free_rate=float(config["backtest"]["risk_free_rate"]),
        weights=result.net_result.weights,
        benchmark_nav=metric_benchmark,
    )
    gross = calculate_performance_metrics(
        gross_equity,
        periods_per_year=int(config["backtest"]["annualization_periods"]),
        risk_free_rate=float(config["backtest"]["risk_free_rate"]),
        weights=result.gross_result.weights,
        benchmark_nav=metric_benchmark,
    )
    submitted = result.rebalance_log.get("submitted_to_broker", pd.Series(dtype=bool))
    skipped = result.rebalance_log.get("skipped_reason", pd.Series(dtype=str)).astype(str)
    metrics: dict[str, Any] = dict(net)
    metrics.update({f"net_{key}": value for key, value in net.items()})
    metrics.update({f"gross_{key}": value for key, value in gross.items()})
    metrics["gross_to_net_total_return_decay"] = gross["total_return"] - net["total_return"]
    metrics["rebalance_decision_count"] = float(len(result.rebalance_log))
    metrics["rebalance_submitted_count"] = float(submitted.sum()) if not submitted.empty else 0.0
    metrics["rebalance_skipped_count"] = float((skipped != "").sum()) if not skipped.empty else 0.0
    metrics["annual_turnover"] = float(net["turnover"])
    metrics["is_static_benchmark"] = result.is_benchmark
    return metrics


def _benchmark_for_equity(
    benchmark_nav: pd.Series,
    *,
    equity: pd.DataFrame,
    initial_capital: float,
) -> pd.Series:
    benchmark = _benchmark_with_initial_capital_baseline(
        benchmark_nav,
        initial_capital=initial_capital,
    )
    target_index = pd.to_datetime(equity["timestamp"], utc=True)
    aligned = benchmark.reindex(target_index).ffill().bfill()
    if aligned.isna().any() or (aligned <= 0).any():
        msg = "Level 4 benchmark could not be aligned to policy equity"
        raise ValueError(msg)
    return aligned


def _portfolio_diagnostics_for_schedule(
    schedule: pd.DataFrame,
    universe: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, float]:
    diagnostics = _portfolio_diagnostics(schedule.tail(1), universe, config)
    weights = schedule.astype("float64")
    diagnostics["average_target_risky_weight_sum"] = float(weights.sum(axis=1).mean())
    diagnostics["average_target_max_weight"] = float(weights.max(axis=1).mean())
    diagnostics["target_schedule_rows"] = float(len(schedule))
    return diagnostics


def _select_policy(results: list[_PolicyResult], *, config: dict[str, Any]) -> _PolicyResult:
    metric = str(
        _level4_config(config).get("selection_metric", config["rebalance"]["selection_metric"])
    )
    metric_name = metric if metric.startswith("net_") else f"net_{metric}"
    max_drawdown = float(config["rebalance"]["max_drawdown_constraint"])
    max_turnover = float(config["rebalance"]["annual_turnover_constraint"])
    feasible = [
        result
        for result in results
        if abs(float(result.metrics.get("net_max_drawdown", 0.0))) <= max_drawdown
        and float(result.metrics.get("annual_turnover", 0.0)) <= max_turnover
    ]
    candidates = feasible or results
    order = {result.name: idx for idx, result in enumerate(results)}
    return max(
        candidates,
        key=lambda result: (
            float(result.metrics.get(metric_name, float("-inf"))),
            -float(result.metrics.get("annual_turnover", float("inf"))),
            -order.get(result.name, 99),
        ),
    )


def _selection_metadata(
    results: list[_PolicyResult],
    *,
    selected: _PolicyResult,
    config: dict[str, Any],
) -> dict[str, object]:
    metric = str(
        _level4_config(config).get("selection_metric", config["rebalance"]["selection_metric"])
    )
    metric_name = metric if metric.startswith("net_") else f"net_{metric}"
    max_drawdown = float(config["rebalance"]["max_drawdown_constraint"])
    max_turnover = float(config["rebalance"]["annual_turnover_constraint"])
    feasible = [
        result.name
        for result in results
        if not result.is_benchmark
        and abs(float(result.metrics.get("net_max_drawdown", 0.0))) <= max_drawdown
        and float(result.metrics.get("annual_turnover", 0.0)) <= max_turnover
    ]
    return {
        "selection_metric_name": metric_name,
        "selection_drawdown_constraint": max_drawdown,
        "selection_annual_turnover_constraint": max_turnover,
        "selection_feasible_policy_count": len(feasible),
        "selection_fallback_used": len(feasible) == 0,
        "selection_tie_breaker": "max_metric_then_min_annual_turnover_then_policy_order",
        "selection_selected_policy": selected.name,
    }


def _provenance(
    *,
    config: dict[str, Any],
    symbols: tuple[str, ...],
    validation_start: pd.Timestamp,
    validation_end: pd.Timestamp,
    estimation_start: pd.Timestamp,
    estimation_end: pd.Timestamp,
    cost_assumptions: CostAssumptions,
    selected_policy: str,
) -> ArtifactProvenance:
    data_path = Path(config["paths"]["market_data"])
    return ArtifactProvenance(
        level=LEVEL_NAME,
        run_label=RUN_LABEL,
        split="validation",
        data_hash=file_sha256(data_path) if data_path.exists() else "in_memory_frame",
        config_hash=canonical_config_hash(config),
        git_commit=git_commit(),
        period_start=validation_start.date().isoformat(),
        period_end=validation_end.date().isoformat(),
        cost_assumptions={
            "fee_bps_one_way": cost_assumptions.fee_bps_one_way,
            "slippage_bps_one_way": cost_assumptions.slippage_bps_one_way,
        },
        benchmark="broker_costed_level3_static_benchmark",
        seed=int(config["project"]["seed"]),
        final_test_lock_hash=None,
        git_worktree_dirty=git_worktree_dirty(),
        git_diff_sha256=git_diff_sha256(),
        warnings=(
            "validation_only_no_final_test_metrics",
            "level4_policy_selection_uses_2024_validation_only",
            "rolling_estimates_use_completed_bars_only",
            "survivorship_bias_active_markets",
            "final_vintage_plan_has_no_2025_performance",
            f"symbols={','.join(symbols)}",
            f"initial_estimation_start={estimation_start.date().isoformat()}",
            f"initial_estimation_end={estimation_end.date().isoformat()}",
            f"selected_policy={selected_policy}",
        ),
    )


def _write_level4_artifacts(
    results: list[_PolicyResult],
    *,
    selected_policy: str,
    output_dir: Path,
    provenance: ArtifactProvenance,
) -> dict[str, Path]:
    paths = {
        "metrics": output_dir / "metrics" / "level_4.csv",
        "equity": output_dir / "equity" / "level_4.parquet",
        "weights": output_dir / "weights" / "level_4.parquet",
        "orders": output_dir / "orders" / "level_4.parquet",
        "fills": output_dir / "fills" / "level_4.parquet",
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    metadata_columns = BacktestArtifactWriter._provenance_columns(provenance)
    metric_rows: list[dict[str, object]] = []
    equity_frames: list[pd.DataFrame] = []
    weight_frames: list[pd.DataFrame] = []
    order_frames: list[pd.DataFrame] = []
    fill_frames: list[pd.DataFrame] = []
    for result in results:
        metric_rows.append(
            {
                "policy": result.name,
                "selected_for_level_4": result.name == selected_policy,
                **result.metrics,
                **metadata_columns,
            }
        )
        equity_frames.append(_tag_frame(result.net_result.equity, result.name))
        weight_frames.append(_tag_frame(result.net_result.weights, result.name))
        order_frames.append(_tag_frame(result.net_result.orders, result.name))
        fill_frames.append(_tag_frame(result.net_result.fills, result.name))
    pd.DataFrame(metric_rows).to_csv(paths["metrics"], index=False)
    for key, frames in (
        ("equity", equity_frames),
        ("weights", weight_frames),
        ("orders", order_frames),
        ("fills", fill_frames),
    ):
        frame = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        for meta_key, meta_value in metadata_columns.items():
            frame[meta_key] = meta_value
        frame.to_parquet(paths[key], index=False)
    for path in paths.values():
        _write_metadata_sidecar(path, provenance)
    return paths


def _tag_frame(frame: pd.DataFrame, policy: str) -> pd.DataFrame:
    tagged = frame.copy()
    tagged["policy"] = policy
    return tagged


def _write_equity_figure(
    results: list[_PolicyResult],
    output_dir: Path,
    provenance: ArtifactProvenance,
) -> Path:
    path = output_dir / "figures" / "level_4_equity_curve.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 5))
    for result in results:
        equity = result.net_result.equity.copy()
        equity["timestamp"] = pd.to_datetime(equity["timestamp"], utc=True)
        if equity.empty:
            continue
        base = float(equity["nav"].iloc[0])
        style = "--" if result.is_benchmark else "-"
        plt.plot(equity["timestamp"], equity["nav"] / base, linestyle=style, label=result.name)
    plt.title("Level 4 validation equity: dynamic rebalance policies")
    plt.xlabel("Validation date")
    plt.ylabel("Normalized net NAV")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    _write_metadata_sidecar(path, provenance)
    return path


def _write_rebalance_log(
    results: list[_PolicyResult],
    *,
    selected_policy: str,
    path: Path,
    provenance: ArtifactProvenance,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = []
    for result in results:
        frame = result.rebalance_log.copy()
        frame["selected_for_level_4"] = result.name == selected_policy
        frame["is_static_benchmark"] = result.is_benchmark
        frames.append(frame)
    output = pd.concat(frames, ignore_index=True)
    for key, value in BacktestArtifactWriter._provenance_columns(provenance).items():
        output[key] = value
    output.to_parquet(path, index=False)
    _write_metadata_sidecar(path, provenance)
    return path


def _write_decision_trace(
    *,
    selected: _PolicyResult,
    results: list[_PolicyResult],
    universe: pd.DataFrame,
    path: Path,
    provenance: ArtifactProvenance,
    config: dict[str, Any],
    selection_metadata: dict[str, object],
) -> Path:
    representative = selected.traces[min(len(selected.traces) - 1, 1)] if selected.traces else None
    payload = {
        "provenance": provenance.metadata(),
        "final_test_exposure": "NOT_EXPOSED",
        "portfolio_protocol": {
            "validation_vintage": (
                "same Level 3 small universe selected at 2023-12-31; rolling 12-month "
                "estimates are evaluated during 2024 only"
            ),
            "final_vintage_status": "planned_not_executed_no_2025_performance",
            "allocator": str(_level4_config(config).get("allocator", "cvar_downside")),
            "selection_diagnostics": selection_metadata,
            "policy_candidates": [result.name for result in results if not result.is_benchmark],
            "static_benchmark": "static_level3_benchmark",
            "constraints": {
                "long_only": True,
                "unlevered": True,
                "max_gross_exposure": float(config["portfolio"]["max_gross_exposure"]),
                "max_asset_weight": float(config["portfolio"]["small_max_weight"]),
                "turnover_cap": float(config["portfolio"]["turnover_cap"]),
                "min_trade_abs": float(_level4_config(config)["min_trade_abs"]),
                "capacity": {
                    "assumed_aum_usd": float(config["liquidity"]["assumed_aum_usd"]),
                    "adv_lookback_days": int(config["liquidity"]["adv_lookback_days"]),
                    "max_participation": float(config["liquidity"]["max_participation"]),
                },
            },
        },
        "universe": universe[
            [
                "symbol",
                "level_3_rank",
                "estimation_valid_days",
                "estimation_median_dollar_volume",
            ]
        ].to_dict(orient="records"),
        "policy_summary": [
            {
                "policy": result.name,
                "selected_for_level_4": result.name == selected.name,
                "is_static_benchmark": result.is_benchmark,
                "net_sharpe": result.metrics["net_sharpe"],
                "net_roi": result.metrics["net_roi"],
                "net_max_drawdown": result.metrics["net_max_drawdown"],
                "annual_turnover": result.metrics["annual_turnover"],
                "rebalance_submitted_count": result.metrics["rebalance_submitted_count"],
            }
            for result in results
        ],
        "representative_decision_trace": None
        if representative is None
        else _trace_to_dict(representative),
    }
    return _write_json_artifact(path, payload, provenance)


def _write_final_vintage_plan(
    config: dict[str, Any],
    output_dir: Path,
    provenance: ArtifactProvenance,
) -> Path:
    level_config = _level4_config(config)
    payload = {
        "provenance": provenance.metadata(),
        "status": "planned_not_executed",
        "final_test_exposure": "NOT_EXPOSED",
        "estimation_start": str(level_config["final_estimation_start"]),
        "estimation_end": str(level_config["final_estimation_end"]),
        "evaluation_period_not_run": [
            str(level_config["final_evaluation_start"]),
            str(level_config["final_evaluation_end"]),
        ],
        "selected_policy": provenance.warnings[-1].replace("selected_policy=", ""),
        "warning": "No 2025 returns, metrics, rankings, charts or fills are computed here.",
    }
    return _write_json_artifact(
        output_dir / "monitoring" / "level_4_final_vintage_plan.json",
        payload,
        provenance,
    )


def _write_json_artifact(
    path: Path,
    payload: dict[str, Any],
    provenance: ArtifactProvenance,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(payload), handle, indent=2, sort_keys=True)
        handle.write("\n")
    _write_metadata_sidecar(path, provenance)
    return path


def _write_metadata_sidecar(path: Path, provenance: ArtifactProvenance) -> None:
    sidecar = path.with_suffix(f"{path.suffix}.metadata.json")
    with sidecar.open("w", encoding="utf-8") as handle:
        json.dump(provenance.metadata(), handle, indent=2, sort_keys=True)
        handle.write("\n")


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value
