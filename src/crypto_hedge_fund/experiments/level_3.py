"""Level 3 static portfolio validation using the shared broker stack."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from crypto_hedge_fund.artifacts import ArtifactProvenance, BacktestArtifactWriter
from crypto_hedge_fund.clock import build_daily_research_clock, ensure_utc
from crypto_hedge_fund.config import load_config
from crypto_hedge_fund.data.universe import UniverseRules, eligible_universe_at
from crypto_hedge_fund.execution import BacktestRunResult, CostAssumptions, PanelMarketData
from crypto_hedge_fund.execution.broker import SimulatedBroker
from crypto_hedge_fund.metrics import calculate_performance_metrics
from crypto_hedge_fund.portfolio import (
    AlwaysRebalancePolicy,
    CvarDownsideAllocator,
    EqualWeightAllocator,
    InverseVolatilityAllocator,
    MinimumVarianceAllocator,
)
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
    ReasonCode,
)

LEVEL_NAME = "level_3"
RUN_LABEL = "level_3_validation_static_portfolio"
METHOD_ORDER = ("equal_weight", "inverse_volatility", "minimum_variance", "cvar_downside")


@dataclass(frozen=True)
class Level3ValidationResult:
    """Paths and selected settings from a Level 3 validation run."""

    metrics: dict[str, Any]
    artifact_paths: dict[str, Path]
    figure_path: Path
    trace_path: Path
    universe_path: Path
    final_vintage_plan_path: Path | None
    selected_method: str
    symbols: tuple[str, ...]
    estimation_start: pd.Timestamp
    estimation_end: pd.Timestamp
    target_schedules: dict[str, pd.DataFrame]


@dataclass(frozen=True)
class _MethodResult:
    name: str
    schedule: pd.DataFrame
    trace: DecisionTrace
    net_result: BacktestRunResult
    gross_result: BacktestRunResult
    metrics: dict[str, Any]


def run_level_3_validation(
    *,
    config_path: str | Path = Path("configs/default.yaml"),
    artifacts_dir: str | Path | None = None,
    market_frame: pd.DataFrame | None = None,
    instruments: pd.DataFrame | None = None,
) -> Level3ValidationResult:
    """Run validation-only Level 3 and write static portfolio artifacts."""

    config = load_config(config_path, resolve_paths=True)
    level_config = dict(config.get("level_3", {}))
    validation_start = _utc(level_config["validation_evaluation_start"])
    validation_end = _utc(level_config["validation_evaluation_end"])
    test_start = _utc(config["splits"]["test_start"])
    if validation_end >= test_start:
        msg = "Level 3 validation evaluation must end before final-test start"
        raise ValueError(msg)

    estimation_start = _utc(level_config["validation_estimation_start"])
    estimation_end = _utc(level_config["validation_estimation_end"])
    _validate_trailing_12_months(estimation_start, estimation_end)
    if estimation_end >= validation_start:
        msg = "Level 3 estimation window must end before validation evaluation starts"
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
        config=config,
        estimation_start=estimation_start,
        estimation_end=estimation_end,
        cutoff_bar_start=_utc(level_config["validation_cutoff"]),
    )
    symbols = tuple(str(symbol) for symbol in universe["symbol"].tolist())
    market = PanelMarketData.from_ohlcv(frame.loc[frame["symbol"].isin(symbols)])
    cost_assumptions = _cost_assumptions(config)
    previous_weights = pd.Series(dict.fromkeys(symbols, 0.0), dtype="float64")

    methods: list[_MethodResult] = []
    for method_name, allocator in _allocators(config).items():
        schedule, trace = build_level_3_target_schedule(
            frame=frame,
            symbols=symbols,
            allocator=allocator,
            config=config,
            estimation_start=estimation_start,
            estimation_end=estimation_end,
            evaluation_start=validation_start,
            previous_weights=previous_weights,
        )
        net_result = _trim_result(
            SimulatedBroker(
                market,
                initial_capital=float(config["backtest"]["initial_capital_usd"]),
                cost_assumptions=cost_assumptions,
            ).run(schedule, end_time=validation_end, run_label=f"{RUN_LABEL}_{method_name}"),
            start=validation_start,
            end=validation_end,
        )
        gross_result = _trim_result(
            SimulatedBroker(
                market,
                initial_capital=float(config["backtest"]["initial_capital_usd"]),
                cost_assumptions=CostAssumptions(fee_bps_one_way=0.0, slippage_bps_one_way=0.0),
            ).run(schedule, end_time=validation_end, run_label=f"{RUN_LABEL}_{method_name}_gross"),
            start=validation_start,
            end=validation_end,
        )
        methods.append(
            _MethodResult(
                name=method_name,
                schedule=schedule,
                trace=trace,
                net_result=net_result,
                gross_result=gross_result,
                metrics={},
            )
        )

    benchmark_nav = next(item for item in methods if item.name == "equal_weight").net_result.equity
    benchmark_series = benchmark_nav.set_index("timestamp")["nav"]
    enriched_methods: list[_MethodResult] = []
    for method in methods:
        metrics = _combined_metrics(
            method.net_result,
            method.gross_result,
            benchmark_nav=benchmark_series,
            config=config,
        )
        metrics.update(_portfolio_diagnostics(method.schedule, universe, config))
        enriched_methods.append(
            _MethodResult(
                name=method.name,
                schedule=method.schedule,
                trace=method.trace,
                net_result=_enrich_equity(method.net_result, method.gross_result, benchmark_series),
                gross_result=method.gross_result,
                metrics=metrics,
            )
        )

    selected = _select_method(enriched_methods, config=config)
    selection_metadata = _selection_metadata(enriched_methods, selected=selected, config=config)
    for method in enriched_methods:
        method.metrics.update(selection_metadata)
    provenance = _provenance(
        config=config,
        symbols=symbols,
        estimation_start=estimation_start,
        estimation_end=estimation_end,
        validation_start=validation_start,
        validation_end=validation_end,
        cost_assumptions=cost_assumptions,
        selected_method=selected.name,
    )
    artifact_paths = _write_level3_artifacts(
        enriched_methods,
        selected_method=selected.name,
        universe=universe,
        output_dir=output_dir,
        provenance=provenance,
    )
    figure_path = _write_equity_figure(enriched_methods, output_dir, provenance)
    trace_path = _write_trace(
        selected=selected,
        methods=enriched_methods,
        universe=universe,
        path=output_dir / "monitoring" / "level_3_decision_trace.json",
        provenance=provenance,
        config=config,
        selection_metadata=selection_metadata,
    )
    universe_path = _write_universe_artifact(
        universe,
        path=output_dir / "monitoring" / "level_3_universe_selection.csv",
        provenance=provenance,
    )
    final_plan_path = None
    if bool(level_config.get("write_final_vintage_plan", True)):
        final_estimation_end = _utc(level_config["final_estimation_end"])
        final_plan_path = _write_final_vintage_plan(
            config=config,
            full_frame=_load_market_frame(config, end=final_estimation_end)
            if market_frame is None
            else _normalize_market_frame(market_frame, end=final_estimation_end),
            instruments=instruments_frame,
            output_dir=output_dir,
            provenance=provenance,
        )

    return Level3ValidationResult(
        metrics={f"{selected.name}_{key}": value for key, value in selected.metrics.items()},
        artifact_paths=artifact_paths,
        figure_path=figure_path,
        trace_path=trace_path,
        universe_path=universe_path,
        final_vintage_plan_path=final_plan_path,
        selected_method=selected.name,
        symbols=symbols,
        estimation_start=estimation_start,
        estimation_end=estimation_end,
        target_schedules={method.name: method.schedule for method in enriched_methods},
    )


def select_level_3_universe(
    frame: pd.DataFrame,
    instruments: pd.DataFrame,
    *,
    config: dict[str, Any],
    estimation_start: pd.Timestamp,
    estimation_end: pd.Timestamp,
    cutoff_bar_start: pd.Timestamp,
) -> pd.DataFrame:
    """Select 5-7 liquid assets using only the completed estimation window."""

    _validate_trailing_12_months(estimation_start, estimation_end)
    size = _small_size(config)
    if cutoff_bar_start != estimation_end:
        msg = "Level 3 cutoff bar must equal estimation window end"
        raise ValueError(msg)
    feature_cutoff = estimation_end + pd.Timedelta(days=1)
    rules = UniverseRules.from_config(config)
    eligibility = eligible_universe_at(
        frame,
        instruments,
        decision_cutoff_utc=feature_cutoff,
        rules=rules,
    )
    window = frame.loc[
        (frame["bar_start_utc"] >= estimation_start) & (frame["bar_start_utc"] <= estimation_end)
    ].copy()
    expected_days = int(pd.date_range(estimation_start, estimation_end, freq="D").size)
    coverage = (
        window.groupby("symbol")
        .agg(
            estimation_valid_days=("bar_start_utc", "nunique"),
            estimation_median_dollar_volume=("dollar_volume", "median"),
            estimation_first_bar=("bar_start_utc", "min"),
            estimation_last_bar=("bar_start_utc", "max"),
        )
        .reset_index()
    )
    coverage["has_complete_estimation_window"] = (
        coverage["estimation_valid_days"].astype(int) == expected_days
    )
    merged = eligibility.merge(coverage, on="symbol", how="left")
    merged["estimation_valid_days"] = merged["estimation_valid_days"].fillna(0).astype(int)
    merged["estimation_median_dollar_volume"] = merged["estimation_median_dollar_volume"].fillna(
        0.0
    )
    merged["eligible_for_level_3"] = merged["eligible"] & merged[
        "has_complete_estimation_window"
    ].fillna(False)
    merged["level_3_reason"] = merged["reason"]
    merged.loc[
        merged["eligible"] & ~merged["has_complete_estimation_window"].fillna(False),
        "level_3_reason",
    ] = "incomplete_12_month_estimation_window"
    merged = merged.sort_values(
        ["eligible_for_level_3", "estimation_median_dollar_volume", "symbol"],
        ascending=[False, False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    selected = merged.loc[merged["eligible_for_level_3"]].head(size).copy()
    if len(selected) != size:
        msg = f"Level 3 requires exactly {size} eligible assets, found {len(selected)}"
        raise ValueError(msg)
    selected["selected_for_level_3"] = True
    selected["level_3_rank"] = range(1, len(selected) + 1)
    selected["selection_cutoff_bar_start"] = cutoff_bar_start.isoformat()
    selected["selection_feature_cutoff"] = feature_cutoff.isoformat()
    selected["estimation_start"] = estimation_start.isoformat()
    selected["estimation_end"] = estimation_end.isoformat()
    selected["estimation_window_calendar_months"] = 12
    return selected.reset_index(drop=True)


def build_level_3_target_schedule(
    *,
    frame: pd.DataFrame,
    symbols: tuple[str, ...],
    allocator: Any,
    config: dict[str, Any],
    estimation_start: pd.Timestamp,
    estimation_end: pd.Timestamp,
    evaluation_start: pd.Timestamp,
    previous_weights: pd.Series,
) -> tuple[pd.DataFrame, DecisionTrace]:
    """Build one static risk-approved target through the shared risk interfaces."""

    normalized = _normalize_market_frame(frame, end=estimation_end)
    clock = build_daily_research_clock(estimation_end.to_pydatetime())
    if pd.Timestamp(clock.execution_time) != evaluation_start:
        msg = "Level 3 static target must execute at the first validation open"
        raise ValueError(msg)
    signals = tuple(
        AgentSignal(
            symbol=symbol,
            agent="level3_static_universe",
            score=1.0,
            confidence=1.0,
            horizon_open_days=365,
            fit_cutoff=clock.feature_cutoff,
            feature_cutoff=clock.feature_cutoff,
            reason_codes=(ReasonCode.OK,),
            metadata={"role": "static_portfolio_membership"},
        )
        for symbol in symbols
    )
    aggregated = tuple(
        AggregatedSignal(
            symbol=symbol,
            score=1.0,
            confidence=1.0,
            contributions={"level3_static_universe": 1.0},
            disagreement=0.0,
            reason_codes=(ReasonCode.OK,),
        )
        for symbol in symbols
    )
    context = AgentContext(
        clock=clock,
        symbols=symbols,
        model_fit_cutoff=clock.feature_cutoff,
        portfolio_nav=float(config["backtest"]["initial_capital_usd"]),
        current_weights=previous_weights.to_dict(),
        metadata={
            "level": LEVEL_NAME,
            "split": "validation",
            "execution_convention": "completed_bar_next_open",
            "estimation_start": estimation_start.isoformat(),
            "estimation_end": estimation_end.isoformat(),
        },
    )
    level_config = dict(config["level_3"])
    pre_risk = PreAllocationRiskPolicy(
        max_gross_exposure=float(config["portfolio"]["max_gross_exposure"]),
        max_per_asset_weight=float(config["portfolio"]["small_max_weight"]),
        cost_buffer_weight=float(level_config.get("cost_buffer_weight", 0.005)),
        min_dollar_volume=float(level_config.get("min_dollar_volume", 0.0)),
        max_stale_data_days=0,
        max_model_age_days=370,
        max_agent_disagreement=float(config["risk"]["max_agent_disagreement"]),
        volatility_target=None,
        turnover_cap=None,
    )
    constraints = pre_risk.constraints(
        list(aggregated),
        context,
        _snapshot_for_bar(normalized, symbols=symbols, bar_start=estimation_end),
    )
    returns = _historical_open_returns(
        normalized,
        symbols=symbols,
        start=estimation_start,
        through=estimation_end,
    )
    proposal = allocator.allocate(
        pd.Series(dict.fromkeys(symbols, 1.0), dtype="float64"),
        returns,
        constraints,
        previous_weights,
    )
    rebalance = AlwaysRebalancePolicy(trigger_code="static_initial_allocation").decide(
        proposal,
        previous_weights,
        context,
    )
    approval = PostAllocationRiskPolicy(
        max_drawdown_stop=float(config["risk"]["max_drawdown_stop"]),
        high_volatility_threshold=float(config["risk"]["high_volatility_threshold_annual"]),
        min_cash_buffer=float(level_config.get("min_cash_buffer", 0.005)),
        annualization_periods=int(config["backtest"]["annualization_periods"]),
    ).approve(proposal, rebalance, constraints, context, returns)
    executable = resolve_risk_approval_targets(approval, context)
    schedule = pd.DataFrame(
        [{symbol: float(executable.risky_weights.get(symbol, 0.0)) for symbol in symbols}],
        index=pd.DatetimeIndex([estimation_end], tz="UTC"),
    )
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
            "allocator": getattr(allocator, "name", type(allocator).__name__),
            "execution_time": pd.Timestamp(clock.execution_time).isoformat(),
            "resolved_action": executable.action,
            "resolved_weights": dict(executable.risky_weights),
            "resolved_cash_weight": executable.cash_weight,
            "reason_codes": [code.value for code in executable.reason_codes],
        },
    )
    return schedule, trace


def _allocators(config: dict[str, Any]) -> dict[str, Any]:
    level_config = dict(config["level_3"])
    all_allocators = {
        "equal_weight": EqualWeightAllocator(),
        "inverse_volatility": InverseVolatilityAllocator(
            min_periods=int(level_config.get("min_estimation_days", 365)) - 1
        ),
        "minimum_variance": MinimumVarianceAllocator(
            min_periods=int(level_config.get("min_estimation_days", 365)) - 1,
            shrinkage=float(level_config.get("covariance_shrinkage", 0.10)),
        ),
        "cvar_downside": CvarDownsideAllocator(
            min_periods=int(level_config.get("min_estimation_days", 365)) - 1,
            tail_fraction=float(level_config.get("cvar_tail_fraction", 0.05)),
        ),
    }
    methods = tuple(str(method) for method in level_config.get("methods", METHOD_ORDER))
    missing = sorted(set(methods).difference(all_allocators))
    if missing:
        msg = f"unsupported Level 3 allocation methods: {missing}"
        raise ValueError(msg)
    return {method: all_allocators[method] for method in methods}


def _small_size(config: dict[str, Any]) -> int:
    level_config = dict(config.get("level_3", {}))
    size = int(level_config.get("small_size", config["portfolio"]["small_size"]))
    if size < 5 or size > 7:
        msg = f"Level 3 small_size must be exactly 5-7 assets, got {size}"
        raise ValueError(msg)
    return size


def _validate_trailing_12_months(start: pd.Timestamp, end: pd.Timestamp) -> None:
    expected_start = end - pd.DateOffset(months=12) + pd.Timedelta(days=1)
    if start.normalize() != pd.Timestamp(expected_start).normalize():
        msg = f"Level 3 estimation must be exactly trailing 12 months: {start} .. {end}"
        raise ValueError(msg)


def _load_market_frame(config: dict[str, Any], *, end: pd.Timestamp) -> pd.DataFrame:
    path = Path(config["paths"]["market_data"])
    columns = [
        "bar_start_utc",
        "bar_end_utc",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "dollar_volume",
        "exchange",
        "market_type",
        "timeframe",
    ]
    frame = pd.read_parquet(
        path,
        columns=columns,
        filters=[("bar_start_utc", "<=", end.to_pydatetime())],
    )
    return _normalize_market_frame(frame, end=end)


def _load_instruments(config: dict[str, Any]) -> pd.DataFrame:
    path = Path(config["paths"]["instruments"])
    if not path.exists():
        return pd.DataFrame(columns=["symbol", "base", "quote", "market_type", "active"])
    return _normalize_instruments(pd.read_parquet(path))


def _normalize_instruments(instruments: pd.DataFrame) -> pd.DataFrame:
    source = instruments.copy()
    if source.empty:
        return pd.DataFrame(columns=["symbol", "base", "quote", "market_type", "active"])
    source["symbol"] = source["symbol"].astype(str)
    if "base" not in source.columns:
        source["base"] = source["symbol"].str.split("/", n=1).str[0]
    if "quote" not in source.columns:
        source["quote"] = source["symbol"].str.split("/", n=1).str[1]
    if "market_type" not in source.columns:
        source["market_type"] = "spot"
    if "active" not in source.columns:
        source["active"] = True
    return source


def _normalize_market_frame(frame: pd.DataFrame, *, end: pd.Timestamp) -> pd.DataFrame:
    source = frame.copy()
    if isinstance(source.index, pd.MultiIndex) and "bar_start_utc" in source.index.names:
        source = source.reset_index()
    if "bar_start_utc" not in source.columns or "symbol" not in source.columns:
        msg = "market frame must contain bar_start_utc and symbol columns"
        raise ValueError(msg)
    source["bar_start_utc"] = pd.to_datetime(source["bar_start_utc"], utc=True)
    source["bar_end_utc"] = (
        pd.to_datetime(source["bar_end_utc"], utc=True)
        if "bar_end_utc" in source.columns
        else source["bar_start_utc"] + pd.Timedelta(days=1)
    )
    source["symbol"] = source["symbol"].astype(str)
    source = source.loc[source["bar_start_utc"] <= end].copy()
    source = source.sort_values(["bar_start_utc", "symbol"], kind="mergesort").reset_index(
        drop=True
    )
    if source.duplicated(["bar_start_utc", "symbol"]).any():
        msg = "duplicate bars in Level 3 market frame"
        raise ValueError(msg)
    return source


def _snapshot_for_bar(
    frame: pd.DataFrame, *, symbols: tuple[str, ...], bar_start: pd.Timestamp
) -> pd.DataFrame:
    snapshot = frame.loc[
        (frame["bar_start_utc"] == bar_start) & (frame["symbol"].isin(symbols))
    ].copy()
    snapshot["feature_cutoff"] = snapshot["bar_end_utc"]
    return snapshot


def _historical_open_returns(
    frame: pd.DataFrame,
    *,
    symbols: tuple[str, ...],
    start: pd.Timestamp,
    through: pd.Timestamp,
) -> pd.DataFrame:
    history = frame.loc[
        (frame["bar_start_utc"] >= start)
        & (frame["bar_start_utc"] <= through)
        & (frame["symbol"].isin(symbols)),
        ["bar_start_utc", "symbol", "open"],
    ]
    pivot = history.pivot(index="bar_start_utc", columns="symbol", values="open").sort_index()
    return pivot.reindex(columns=list(symbols)).pct_change().dropna(how="all")


def _cost_assumptions(config: dict[str, Any]) -> CostAssumptions:
    return CostAssumptions(
        fee_bps_one_way=float(config["backtest"]["fee_bps_one_way"]),
        slippage_bps_one_way=float(config["backtest"]["slippage_bps_one_way"]),
    )


def _trim_result(
    result: BacktestRunResult, *, start: pd.Timestamp, end: pd.Timestamp
) -> BacktestRunResult:
    def trim(frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty or "timestamp" not in frame.columns:
            return frame.copy()
        timestamps = pd.to_datetime(frame["timestamp"], utc=True)
        return frame.loc[(timestamps >= start) & (timestamps <= end)].reset_index(drop=True)

    return BacktestRunResult(
        equity=trim(result.equity),
        weights=trim(result.weights),
        orders=trim(result.orders),
        fills=trim(result.fills),
    )


def _combined_metrics(
    net_result: BacktestRunResult,
    gross_result: BacktestRunResult,
    *,
    benchmark_nav: pd.Series,
    config: dict[str, Any],
) -> dict[str, float]:
    initial_capital = float(config["backtest"]["initial_capital_usd"])
    net_equity = _with_initial_capital_baseline(net_result.equity, initial_capital)
    gross_equity = _with_initial_capital_baseline(gross_result.equity, initial_capital)
    metric_benchmark = _benchmark_with_initial_capital_baseline(
        benchmark_nav,
        initial_capital=initial_capital,
    )
    net = calculate_performance_metrics(
        net_equity,
        periods_per_year=int(config["backtest"]["annualization_periods"]),
        risk_free_rate=float(config["backtest"]["risk_free_rate"]),
        weights=net_result.weights,
        benchmark_nav=metric_benchmark,
    )
    gross = calculate_performance_metrics(
        gross_equity,
        periods_per_year=int(config["backtest"]["annualization_periods"]),
        risk_free_rate=float(config["backtest"]["risk_free_rate"]),
        weights=gross_result.weights,
        benchmark_nav=metric_benchmark,
    )
    metrics = dict(net)
    metrics.update({f"net_{key}": value for key, value in net.items()})
    metrics.update({f"gross_{key}": value for key, value in gross.items()})
    metrics["gross_to_net_total_return_decay"] = gross["total_return"] - net["total_return"]
    return metrics


def _with_initial_capital_baseline(
    equity: pd.DataFrame,
    initial_capital: float,
) -> pd.DataFrame:
    if equity.empty:
        return equity.copy()
    source = equity.copy()
    timestamps = pd.to_datetime(source["timestamp"], utc=True)
    baseline_timestamp = timestamps.iloc[0] - pd.Timedelta(nanoseconds=1)
    baseline: dict[str, object] = {}
    for column in source.columns:
        if column == "timestamp":
            baseline[column] = baseline_timestamp
        elif column in {"cash", "nav"}:
            baseline[column] = initial_capital
        elif column == "run_label":
            baseline[column] = source[column].iloc[0]
        elif column in {
            "risky_value",
            "turnover",
            "fees",
            "slippage",
            "total_cost",
            "exposure",
            "trade_count",
        }:
            baseline[column] = 0.0
        else:
            baseline[column] = source[column].iloc[0]
    return pd.concat([pd.DataFrame([baseline]), source], ignore_index=True)


def _benchmark_with_initial_capital_baseline(
    benchmark_nav: pd.Series,
    *,
    initial_capital: float,
) -> pd.Series:
    benchmark = benchmark_nav.astype("float64").copy()
    if benchmark.empty:
        return benchmark
    index = pd.to_datetime(benchmark.index, utc=True)
    benchmark.index = index
    baseline_timestamp = index[0] - pd.Timedelta(nanoseconds=1)
    baseline = pd.Series([initial_capital], index=pd.DatetimeIndex([baseline_timestamp]))
    return pd.concat([baseline, benchmark])


def _portfolio_diagnostics(
    schedule: pd.DataFrame, universe: pd.DataFrame, config: dict[str, Any]
) -> dict[str, float]:
    target = schedule.iloc[0].astype("float64")
    nonzero = target[target > 1e-12]
    hhi = float((nonzero**2).sum())
    effective_n = float(1.0 / hhi) if hhi > 0 else 0.0
    median_dv = universe.set_index("symbol")["estimation_median_dollar_volume"].reindex(
        nonzero.index
    )
    weighted_median_liquidity = float((nonzero * median_dv).sum()) if not nonzero.empty else 0.0
    return {
        "universe_count": float(len(universe)),
        "target_risky_weight_sum": float(target.sum()),
        "target_cash_weight": float(1.0 - target.sum()),
        "target_effective_n": effective_n,
        "target_concentration_hhi": hhi,
        "target_max_weight": float(nonzero.max()) if not nonzero.empty else 0.0,
        "target_weighted_median_dollar_volume": weighted_median_liquidity,
        "assumed_aum_usd": float(config["liquidity"]["assumed_aum_usd"]),
    }


def _select_method(methods: list[_MethodResult], *, config: dict[str, Any]) -> _MethodResult:
    metric = str(config["level_3"].get("selection_metric", "net_sharpe"))
    metric_name = metric if metric.startswith("net_") else f"net_{metric}"
    max_drawdown = float(config["rebalance"]["max_drawdown_constraint"])
    feasible = [
        method
        for method in methods
        if abs(method.metrics.get("net_max_drawdown", 0.0)) <= max_drawdown
    ]
    candidates = feasible or methods
    simplicity = {name: idx for idx, name in enumerate(METHOD_ORDER)}
    return max(
        candidates,
        key=lambda method: (
            method.metrics.get(metric_name, float("-inf")),
            -method.metrics.get("net_turnover", float("inf")),
            -simplicity.get(method.name, 99),
        ),
    )


def _selection_metadata(
    methods: list[_MethodResult],
    *,
    selected: _MethodResult,
    config: dict[str, Any],
) -> dict[str, object]:
    metric = str(config["level_3"].get("selection_metric", "net_sharpe"))
    metric_name = metric if metric.startswith("net_") else f"net_{metric}"
    max_drawdown = float(config["rebalance"]["max_drawdown_constraint"])
    feasible = [
        method.name
        for method in methods
        if abs(float(method.metrics.get("net_max_drawdown", 0.0))) <= max_drawdown
    ]
    return {
        "selection_metric_name": metric_name,
        "selection_drawdown_constraint": max_drawdown,
        "selection_feasible_method_count": len(feasible),
        "selection_fallback_used": len(feasible) == 0,
        "selection_tie_breaker": "max_metric_then_min_net_turnover_then_method_order",
        "selection_selected_method": selected.name,
    }


def _enrich_equity(
    net_result: BacktestRunResult,
    gross_result: BacktestRunResult,
    benchmark_nav: pd.Series,
) -> BacktestRunResult:
    equity = net_result.equity.copy()
    timestamps = pd.to_datetime(equity["timestamp"], utc=True)
    gross = gross_result.equity.set_index("timestamp")["nav"].rename("gross_nav")
    equity = equity.set_index(timestamps)
    equity["gross_nav"] = gross.reindex(equity.index).to_numpy()
    equity["benchmark_nav"] = benchmark_nav.reindex(equity.index).to_numpy()
    equity = equity.reset_index(drop=True)
    return BacktestRunResult(
        equity=equity,
        weights=net_result.weights,
        orders=net_result.orders,
        fills=net_result.fills,
    )


def _provenance(
    *,
    config: dict[str, Any],
    symbols: tuple[str, ...],
    estimation_start: pd.Timestamp,
    estimation_end: pd.Timestamp,
    validation_start: pd.Timestamp,
    validation_end: pd.Timestamp,
    cost_assumptions: CostAssumptions,
    selected_method: str,
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
        benchmark="broker_costed_equal_weight_static_basket",
        seed=int(config["project"]["seed"]),
        final_test_lock_hash=None,
        git_worktree_dirty=git_worktree_dirty(),
        git_diff_sha256=git_diff_sha256(),
        warnings=(
            "validation_only_no_final_test_metrics",
            "survivorship_bias_active_markets",
            "static_weights_selected_on_2023_and_evaluated_in_2024",
            "final_vintage_plan_has_no_2025_performance",
            f"symbols={','.join(symbols)}",
            f"estimation_start={estimation_start.date().isoformat()}",
            f"estimation_end={estimation_end.date().isoformat()}",
            f"selected_method={selected_method}",
            "real_trading_limitations=daily_bars_no_order_book_no_custody_reconciliation",
        ),
    )


def _write_level3_artifacts(
    methods: list[_MethodResult],
    *,
    selected_method: str,
    universe: pd.DataFrame,
    output_dir: Path,
    provenance: ArtifactProvenance,
) -> dict[str, Path]:
    paths = {
        "metrics": output_dir / "metrics" / "level_3.csv",
        "equity": output_dir / "equity" / "level_3.parquet",
        "weights": output_dir / "weights" / "level_3.parquet",
        "orders": output_dir / "orders" / "level_3.parquet",
        "fills": output_dir / "fills" / "level_3.parquet",
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    metadata_columns = BacktestArtifactWriter._provenance_columns(provenance)
    metric_rows: list[dict[str, object]] = []
    equity_frames: list[pd.DataFrame] = []
    weight_frames: list[pd.DataFrame] = []
    order_frames: list[pd.DataFrame] = []
    fill_frames: list[pd.DataFrame] = []
    selected_symbols = ",".join(universe["symbol"].astype(str).tolist())
    for method in methods:
        metric_rows.append(
            {
                "method": method.name,
                "selected_for_level_3": method.name == selected_method,
                "selected_symbols": selected_symbols,
                **method.metrics,
                **metadata_columns,
            }
        )
        equity_frames.append(_tag_frame(method.net_result.equity, method.name))
        weight_frames.append(_tag_frame(method.net_result.weights, method.name))
        order_frames.append(_tag_frame(method.net_result.orders, method.name))
        fill_frames.append(_tag_frame(method.net_result.fills, method.name))
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


def _tag_frame(frame: pd.DataFrame, method: str) -> pd.DataFrame:
    tagged = frame.copy()
    tagged["method"] = method
    return tagged


def _write_equity_figure(
    methods: list[_MethodResult],
    output_dir: Path,
    provenance: ArtifactProvenance,
) -> Path:
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    path = figures_dir / "level_3_equity_curve.png"
    plt.figure(figsize=(10, 5))
    for method in methods:
        equity = method.net_result.equity.copy()
        equity["timestamp"] = pd.to_datetime(equity["timestamp"], utc=True)
        if equity.empty:
            continue
        base = float(equity["nav"].iloc[0])
        plt.plot(equity["timestamp"], equity["nav"] / base, label=method.name)
    plt.title("Level 3 validation equity: static portfolio methods")
    plt.xlabel("Validation date")
    plt.ylabel("Normalized net NAV")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    _write_metadata_sidecar(path, provenance)
    return path


def _write_universe_artifact(
    universe: pd.DataFrame,
    *,
    path: Path,
    provenance: ArtifactProvenance,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    output = universe.copy()
    for key, value in BacktestArtifactWriter._provenance_columns(provenance).items():
        output[key] = value
    output.to_csv(path, index=False)
    _write_metadata_sidecar(path, provenance)
    return path


def _write_trace(
    *,
    selected: _MethodResult,
    methods: list[_MethodResult],
    universe: pd.DataFrame,
    path: Path,
    provenance: ArtifactProvenance,
    config: dict[str, Any],
    selection_metadata: dict[str, object],
) -> Path:
    payload = {
        "provenance": provenance.metadata(),
        "portfolio_protocol": {
            "validation_vintage": (
                "select universe at 2023-12-31 using 2023 data, estimate 2023, "
                "execute first 2024 open"
            ),
            "final_vintage_status": "planned_not_executed_no_2025_performance",
            "selection_metric": str(config["level_3"].get("selection_metric", "net_sharpe")),
            "selection_diagnostics": selection_metadata,
            "methods": list(_allocators(config).keys()),
            "constraints": {
                "long_only": True,
                "unlevered": True,
                "max_gross_exposure": float(config["portfolio"]["max_gross_exposure"]),
                "max_asset_weight": float(config["portfolio"]["small_max_weight"]),
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
        "method_summary": [
            {
                "method": method.name,
                "selected_for_level_3": method.name == selected.name,
                "net_sharpe": method.metrics["net_sharpe"],
                "net_roi": method.metrics["net_roi"],
                "net_max_drawdown": method.metrics["net_max_drawdown"],
                "target_effective_n": method.metrics["target_effective_n"],
                "target_max_weight": method.metrics["target_max_weight"],
            }
            for method in methods
        ],
        "real_trading_applicability": {
            "weights_to_orders": (
                "shared broker converts approved target weights to next-open orders"
            ),
            "costs": "fees and slippage charged only on risky notional actually traded",
            "limitations": [
                "daily OHLCV bars, no order book depth or spread model",
                "active-market survivorship limitation in frozen Binance snapshot",
                "no custody, tax, exchange outage or reconciliation workflow in MVP",
                (
                    "exchange precision and minimum notional are approximated by metadata "
                    "where present"
                ),
            ],
        },
        "representative_decision_trace": _trace_to_dict(selected.trace),
    }
    return _write_json_artifact(path, payload, provenance)


def _write_final_vintage_plan(
    *,
    config: dict[str, Any],
    full_frame: pd.DataFrame,
    instruments: pd.DataFrame,
    output_dir: Path,
    provenance: ArtifactProvenance,
) -> Path:
    level_config = dict(config["level_3"])
    path = output_dir / "monitoring" / "level_3_final_vintage_plan.json"
    estimation_start = _utc(level_config["final_estimation_start"])
    estimation_end = _utc(level_config["final_estimation_end"])
    _validate_trailing_12_months(estimation_start, estimation_end)
    try:
        universe = select_level_3_universe(
            full_frame,
            instruments,
            config=config,
            estimation_start=estimation_start,
            estimation_end=estimation_end,
            cutoff_bar_start=_utc(level_config["final_cutoff"]),
        )
        symbols = tuple(str(symbol) for symbol in universe["symbol"].tolist())
        previous = pd.Series(dict.fromkeys(symbols, 0.0), dtype="float64")
        weights = {}
        for name, allocator in _allocators(config).items():
            schedule, trace = build_level_3_target_schedule(
                frame=full_frame,
                symbols=symbols,
                allocator=allocator,
                config=config,
                estimation_start=estimation_start,
                estimation_end=estimation_end,
                evaluation_start=_utc(level_config["final_evaluation_start"]),
                previous_weights=previous,
            )
            weights[name] = {
                "weights": schedule.iloc[0].to_dict(),
                "optimizer_status": (
                    trace.proposal.optimizer_status if trace.proposal else "missing"
                ),
                "approval_action": trace.approval.action if trace.approval else "missing",
            }
        payload = {
            "provenance": provenance.metadata(),
            "status": "planned_not_executed",
            "final_test_exposure": "NOT_EXPOSED",
            "estimation_start": estimation_start.isoformat(),
            "estimation_end": estimation_end.isoformat(),
            "evaluation_period_not_run": [
                str(level_config["final_evaluation_start"]),
                str(level_config["final_evaluation_end"]),
            ],
            "symbols": list(symbols),
            "weights_by_method": weights,
            "warning": "No 2025 returns, metrics, rankings, charts or fills are computed here.",
        }
    except Exception as exc:
        payload = {
            "provenance": provenance.metadata(),
            "status": "planning_failed_without_final_test_execution",
            "final_test_exposure": "NOT_EXPOSED",
            "error": str(exc),
        }
    return _write_json_artifact(path, payload, provenance)


def _write_json_artifact(
    path: Path, payload: dict[str, Any], provenance: ArtifactProvenance
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


def _trace_to_dict(trace: DecisionTrace) -> dict[str, Any]:
    return {
        "clock": {
            "bar_start": trace.clock.bar_start.isoformat(),
            "bar_end": trace.clock.bar_end.isoformat(),
            "feature_cutoff": trace.clock.feature_cutoff.isoformat(),
            "decision_time": trace.clock.decision_time.isoformat(),
            "execution_time": trace.clock.execution_time.isoformat(),
        },
        "signals": [
            {
                "symbol": signal.symbol,
                "agent": signal.agent,
                "score": signal.score,
                "confidence": signal.confidence,
                "horizon_open_days": signal.horizon_open_days,
                "fit_cutoff": signal.fit_cutoff.isoformat(),
                "feature_cutoff": signal.feature_cutoff.isoformat(),
                "reason_codes": [code.value for code in signal.reason_codes],
                "metadata": dict(signal.metadata),
            }
            for signal in trace.signals
        ],
        "aggregated_signals": [
            {
                "symbol": signal.symbol,
                "score": signal.score,
                "confidence": signal.confidence,
                "contributions": dict(signal.contributions),
                "disagreement": signal.disagreement,
                "reason_codes": [code.value for code in signal.reason_codes],
            }
            for signal in trace.aggregated_signals
        ],
        "constraints": None
        if trace.constraints is None
        else {
            "max_gross_exposure": trace.constraints.max_gross_exposure,
            "per_asset_caps": dict(trace.constraints.per_asset_caps),
            "blocked_symbols": list(trace.constraints.blocked_symbols),
            "reason_codes": [code.value for code in trace.constraints.reason_codes],
            "metadata": dict(trace.constraints.metadata),
        },
        "proposal": None
        if trace.proposal is None
        else {
            "target_weights": dict(trace.proposal.target_weights),
            "cash_weight": trace.proposal.cash_weight,
            "optimizer_status": trace.proposal.optimizer_status,
            "expected_turnover": trace.proposal.expected_turnover,
            "objective_value": trace.proposal.objective_value,
            "reason_codes": [code.value for code in trace.proposal.reason_codes],
            "metadata": dict(trace.proposal.metadata),
        },
        "approval": None
        if trace.approval is None
        else {
            "approved": trace.approval.approved,
            "approved_weights": dict(trace.approval.approved_weights),
            "cash_weight": trace.approval.cash_weight,
            "action": trace.approval.action,
            "reason_codes": [code.value for code in trace.approval.reason_codes],
            "metadata": dict(trace.approval.metadata),
        },
        "metadata": dict(trace.metadata),
    }


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


def _utc(value: Any) -> pd.Timestamp:
    return pd.Timestamp(ensure_utc(value))
