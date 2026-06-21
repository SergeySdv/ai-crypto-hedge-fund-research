"""Level 1 validation runner using the shared agent, risk and broker stack."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from crypto_hedge_fund.agents import SignalAggregator, TypedAgentOrchestrator
from crypto_hedge_fund.artifacts import ArtifactProvenance, BacktestArtifactWriter
from crypto_hedge_fund.clock import build_daily_research_clock, ensure_utc
from crypto_hedge_fund.config import load_config
from crypto_hedge_fund.execution import BacktestRunResult, CostAssumptions, PanelMarketData
from crypto_hedge_fund.execution.broker import SimulatedBroker
from crypto_hedge_fund.metrics import calculate_performance_metrics
from crypto_hedge_fund.portfolio.rebalance import AlwaysRebalancePolicy
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
from crypto_hedge_fund.strategies import SMACrossoverSignalAgent
from crypto_hedge_fund.types import (
    AgentContext,
    AggregatedSignal,
    DecisionTrace,
    PortfolioProposal,
    ReasonCode,
    RiskConstraints,
)

LEVEL_NAME = "level_1"
RUN_LABEL = "level_1_validation_sma"


@dataclass(frozen=True)
class Level1ValidationResult:
    """Paths and selected settings from a Level 1 validation run."""

    metrics: dict[str, float]
    artifact_paths: dict[str, Path]
    figure_path: Path
    trace_path: Path
    selected_fast_window: int
    selected_slow_window: int
    target_schedule: pd.DataFrame


@dataclass(frozen=True)
class _CandidateResult:
    fast_window: int
    slow_window: int
    schedule: pd.DataFrame
    traces: tuple[DecisionTrace, ...]
    net_result: BacktestRunResult
    gross_result: BacktestRunResult
    metrics: dict[str, float]


class _BinarySignalAllocator:
    name = "level1_binary_cash_or_asset"

    def allocate(
        self,
        signals: pd.Series,
        historical_returns: pd.DataFrame,
        constraints: RiskConstraints,
        previous_weights: pd.Series,
    ) -> PortfolioProposal:
        del historical_returns
        clean = signals.astype("float64").replace([math.inf, -math.inf], math.nan).dropna()
        weights: dict[str, float] = {}
        for symbol, score in clean.items():
            symbol = str(symbol)
            if (
                score > 0
                and symbol not in constraints.blocked_symbols
                and constraints.per_asset_caps.get(symbol, 0.0) > 0
            ):
                weights[symbol] = min(
                    constraints.max_gross_exposure,
                    constraints.per_asset_caps.get(symbol, 0.0),
                )
        previous = previous_weights.astype("float64").reindex(weights, fill_value=0.0)
        target = pd.Series(weights, dtype="float64")
        expected_turnover = (
            float((target - previous).abs().sum())
            if not target.empty
            else float(previous.abs().sum())
        )
        risky_sum = sum(weights.values())
        return PortfolioProposal(
            decision_time=constraints.decision_time,
            target_weights=weights,
            cash_weight=1.0 - risky_sum,
            optimizer_status="ok",
            expected_turnover=expected_turnover,
            objective_value=None,
            reason_codes=(ReasonCode.OK,),
            metadata={"allocator": self.name},
        )


def run_level_1_validation(
    *,
    config_path: str | Path = Path("configs/default.yaml"),
    artifacts_dir: str | Path | None = None,
    market_frame: pd.DataFrame | None = None,
    split: str = "validation",
    final_test_lock_hash: str | None = None,
) -> Level1ValidationResult:
    """Run Level 1 and write required artifacts for validation or frozen final test."""
    if split not in {"validation", "final_test"}:
        msg = f"unsupported Level 1 split: {split}"
        raise ValueError(msg)
    if split == "final_test" and not final_test_lock_hash:
        msg = "final_test_lock_hash is required for Level 1 final-test runs"
        raise ValueError(msg)
    config = load_config(config_path, resolve_paths=True)
    symbol = str(config["level_1"]["symbol"])
    validation_start = pd.Timestamp(
        ensure_utc(
            config["splits"]["validation_start"]
            if split == "validation"
            else config["splits"]["test_start"]
        )
    )
    validation_end = pd.Timestamp(
        ensure_utc(
            config["splits"]["validation_end"]
            if split == "validation"
            else config["splits"]["test_end"]
        )
    )
    test_start = pd.Timestamp(ensure_utc(config["splits"]["test_start"]))
    if split == "validation" and validation_end >= test_start:
        msg = "validation_end must be before test_start for validation-only Level 1"
        raise ValueError(msg)

    output_dir = (
        Path(artifacts_dir) if artifacts_dir is not None else Path(config["paths"]["artifacts"])
    )
    frame = (
        _load_symbol_frame(config, symbol=symbol, validation_end=validation_end)
        if market_frame is None
        else _normalize_market_frame(market_frame, symbol=symbol, end=validation_end)
    )
    if frame.empty:
        msg = f"No validation-safe OHLCV rows found for {symbol}"
        raise ValueError(msg)

    market = PanelMarketData.from_ohlcv(frame)
    cost_assumptions = _cost_assumptions(config)
    benchmark = _run_buy_and_hold_benchmark(
        market,
        symbol=symbol,
        decision_bar=validation_start - pd.Timedelta(days=1),
        validation_start=validation_start,
        validation_end=validation_end,
        config=config,
        cost_assumptions=cost_assumptions,
    )
    benchmark_nav = benchmark.equity.set_index("timestamp")["nav"]

    candidates: list[_CandidateResult] = []
    for fast_window, slow_window in _candidate_windows(config):
        schedule, traces = build_level_1_target_schedule(
            frame=frame,
            symbol=symbol,
            fast_window=fast_window,
            slow_window=slow_window,
            config=config,
            split=split,
        )
        net_result = _trim_result(
            SimulatedBroker(
                market,
                initial_capital=float(config["backtest"]["initial_capital_usd"]),
                cost_assumptions=cost_assumptions,
            ).run(schedule, end_time=validation_end, run_label=RUN_LABEL),
            start=validation_start,
            end=validation_end,
        )
        gross_result = _trim_result(
            SimulatedBroker(
                market,
                initial_capital=float(config["backtest"]["initial_capital_usd"]),
                cost_assumptions=CostAssumptions(fee_bps_one_way=0.0, slippage_bps_one_way=0.0),
            ).run(schedule, end_time=validation_end, run_label=f"{RUN_LABEL}_gross"),
            start=validation_start,
            end=validation_end,
        )
        metrics = _combined_metrics(
            net_result,
            gross_result,
            benchmark_nav=benchmark_nav,
            config=config,
        )
        candidates.append(
            _CandidateResult(
                fast_window=fast_window,
                slow_window=slow_window,
                schedule=schedule,
                traces=traces,
                net_result=net_result,
                gross_result=gross_result,
                metrics=metrics,
            )
        )

    selected = _select_candidate(
        candidates, metric=str(config["level_1"].get("selection_metric", "net_sharpe"))
    )
    enriched_result = _enrich_equity(selected.net_result, selected.gross_result, benchmark)
    final_metrics = {
        **selected.metrics,
        "selected_fast_window": float(selected.fast_window),
        "selected_slow_window": float(selected.slow_window),
        "candidate_count": float(len(candidates)),
    }
    provenance = _provenance(
        config=config,
        symbol=symbol,
        validation_start=validation_start,
        validation_end=validation_end,
        cost_assumptions=cost_assumptions,
        selected=selected,
        split=split,
        final_test_lock_hash=final_test_lock_hash,
    )
    writer = BacktestArtifactWriter(output_dir)
    artifact_paths = writer.write_run(
        enriched_result,
        final_metrics,
        provenance,
        level_name=LEVEL_NAME,
    )
    figure_path = _write_equity_figure(enriched_result.equity, output_dir, provenance)
    trace_path = _write_trace(
        traces=selected.traces,
        path=output_dir / "monitoring" / "level_1_decision_trace.json",
        provenance=provenance,
        candidates=candidates,
        selected=selected,
    )
    return Level1ValidationResult(
        metrics=final_metrics,
        artifact_paths=artifact_paths,
        figure_path=figure_path,
        trace_path=trace_path,
        selected_fast_window=selected.fast_window,
        selected_slow_window=selected.slow_window,
        target_schedule=selected.schedule,
    )


def build_level_1_target_schedule(
    *,
    frame: pd.DataFrame,
    symbol: str,
    fast_window: int,
    slow_window: int,
    config: dict[str, Any],
    split: str = "validation",
) -> tuple[pd.DataFrame, tuple[DecisionTrace, ...]]:
    """Create risk-approved target weights from SMA signals."""
    period_start_key = "validation_start" if split == "validation" else "test_start"
    period_end_key = "validation_end" if split == "validation" else "test_end"
    normalized = _normalize_market_frame(
        frame,
        symbol=symbol,
        end=pd.Timestamp(ensure_utc(config["splits"][period_end_key])),
    )
    validation_start = pd.Timestamp(ensure_utc(config["splits"][period_start_key]))
    validation_end = pd.Timestamp(ensure_utc(config["splits"][period_end_key]))
    first_decision_bar = validation_start - pd.Timedelta(days=1)
    agent = SMACrossoverSignalAgent(fast_window=fast_window, slow_window=slow_window)
    orchestrator = TypedAgentOrchestrator(
        [agent],
        aggregator=SignalAggregator(
            agent_weights={agent.name: 1.0},
            disagreement_threshold=float(config["risk"]["max_agent_disagreement"]),
        ),
    )
    pre_risk = PreAllocationRiskPolicy(
        max_gross_exposure=float(config["portfolio"]["max_gross_exposure"]),
        max_per_asset_weight=float(config["level_1"].get("max_weight", 1.0)),
        cost_buffer_weight=float(config["level_1"].get("cost_buffer_weight", 0.005)),
        min_dollar_volume=float(config["level_1"].get("min_dollar_volume", 0.0)),
        max_stale_data_days=0,
        max_model_age_days=3650,
        max_agent_disagreement=float(config["risk"]["max_agent_disagreement"]),
        volatility_target=None,
        turnover_cap=None,
    )
    allocator = _BinarySignalAllocator()
    rebalance_policy = AlwaysRebalancePolicy(trigger_code="sma_signal")
    post_risk = PostAllocationRiskPolicy(
        max_drawdown_stop=float(config["risk"]["max_drawdown_stop"]),
        high_volatility_threshold=float(config["risk"]["high_volatility_threshold_annual"]),
        min_cash_buffer=float(config["level_1"].get("min_cash_buffer", 0.005)),
        annualization_periods=int(config["backtest"]["annualization_periods"]),
    )

    rows: list[dict[str, float]] = []
    index: list[pd.Timestamp] = []
    traces: list[DecisionTrace] = []
    current_weights = pd.Series({symbol: 0.0}, dtype="float64")

    decision_bars = normalized.loc[
        (normalized["bar_start_utc"] >= first_decision_bar)
        & (normalized["bar_start_utc"] < validation_end)
    ]
    for bar in decision_bars.itertuples(index=False):
        bar_start = pd.Timestamp(bar.bar_start_utc)
        clock = build_daily_research_clock(bar_start.to_pydatetime())
        execution_time = pd.Timestamp(clock.execution_time)
        if execution_time < validation_start or execution_time > validation_end:
            continue
        history = normalized.loc[normalized["bar_start_utc"] <= bar_start].set_index(
            "bar_start_utc"
        )
        context = AgentContext(
            clock=clock,
            symbols=(symbol,),
            model_fit_cutoff=clock.feature_cutoff,
            portfolio_nav=float(config["backtest"]["initial_capital_usd"]),
            current_weights=current_weights.to_dict(),
            metadata={
                "level": LEVEL_NAME,
                "split": split,
                "execution_convention": "completed_bar_next_open",
            },
        )
        run = orchestrator.run(history, context)
        constraints = pre_risk.constraints(
            list(run.aggregated_signals),
            context,
            _snapshot_for_bar(normalized, symbol=symbol, bar_start=bar_start),
        )
        signal_series = pd.Series(
            {signal.symbol: signal.score for signal in run.aggregated_signals},
            dtype="float64",
        )
        returns = _historical_open_returns(normalized, through=bar_start)
        proposal = allocator.allocate(signal_series, returns, constraints, current_weights)
        rebalance = rebalance_policy.decide(proposal, current_weights, context)
        approval = post_risk.approve(proposal, rebalance, constraints, context, returns)
        executable = resolve_risk_approval_targets(approval, context)
        target = pd.Series(executable.risky_weights, dtype="float64").reindex(
            [symbol], fill_value=0.0
        )
        rows.append({symbol: float(target.get(symbol, 0.0))})
        index.append(bar_start)
        current_weights = target
        traces.append(
            DecisionTrace(
                clock=clock,
                signals=run.signals,
                aggregated_signals=run.aggregated_signals,
                constraints=constraints,
                proposal=proposal,
                approval=approval,
                events=run.events,
                metadata={
                    "level": LEVEL_NAME,
                    "split": split,
                    "execution_time": execution_time.isoformat(),
                    "resolved_action": executable.action,
                    "resolved_weights": dict(executable.risky_weights),
                    "resolved_cash_weight": executable.cash_weight,
                },
            )
        )

    if not rows:
        msg = "Level 1 validation produced no executable target-weight rows"
        raise ValueError(msg)
    return pd.DataFrame(rows, index=pd.DatetimeIndex(index, tz="UTC")), tuple(traces)


def _candidate_windows(config: dict[str, Any]) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    for fast in config["level_1"]["fast_windows"]:
        for slow in config["level_1"]["slow_windows"]:
            fast_window = int(fast)
            slow_window = int(slow)
            if fast_window < slow_window:
                pairs.append((fast_window, slow_window))
    if not pairs:
        msg = "level_1 fast_windows/slow_windows contain no valid fast < slow pairs"
        raise ValueError(msg)
    return pairs


def _load_symbol_frame(
    config: dict[str, Any],
    *,
    symbol: str,
    validation_end: pd.Timestamp,
) -> pd.DataFrame:
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
        filters=[
            ("symbol", "==", symbol),
            ("bar_start_utc", "<=", validation_end.to_pydatetime()),
        ],
    )
    return _normalize_market_frame(frame, symbol=symbol, end=validation_end)


def _normalize_market_frame(
    frame: pd.DataFrame,
    *,
    symbol: str,
    end: pd.Timestamp,
) -> pd.DataFrame:
    source = frame.copy()
    if isinstance(source.index, pd.MultiIndex) and "bar_start_utc" in source.index.names:
        source = source.reset_index()
    if "bar_start_utc" not in source.columns or "symbol" not in source.columns:
        msg = "market frame must contain bar_start_utc and symbol columns"
        raise ValueError(msg)
    source["bar_start_utc"] = pd.to_datetime(source["bar_start_utc"], utc=True)
    if "bar_end_utc" not in source.columns:
        source["bar_end_utc"] = source["bar_start_utc"] + pd.Timedelta(days=1)
    else:
        source["bar_end_utc"] = pd.to_datetime(source["bar_end_utc"], utc=True)
    source["symbol"] = source["symbol"].astype(str)
    source = source.loc[(source["symbol"] == symbol) & (source["bar_start_utc"] <= end)]
    source = source.sort_values("bar_start_utc", kind="mergesort").reset_index(drop=True)
    if source["bar_start_utc"].duplicated().any():
        msg = f"duplicate bars for {symbol}"
        raise ValueError(msg)
    return source


def _snapshot_for_bar(frame: pd.DataFrame, *, symbol: str, bar_start: pd.Timestamp) -> pd.DataFrame:
    row = frame.loc[frame["bar_start_utc"] == bar_start]
    if row.empty:
        return pd.DataFrame()
    snapshot = row.tail(1).copy()
    snapshot["feature_cutoff"] = snapshot["bar_end_utc"]
    snapshot["symbol"] = symbol
    return snapshot


def _historical_open_returns(frame: pd.DataFrame, *, through: pd.Timestamp) -> pd.DataFrame:
    history = frame.loc[frame["bar_start_utc"] <= through, ["bar_start_utc", "symbol", "open"]]
    pivot = history.pivot(index="bar_start_utc", columns="symbol", values="open").sort_index()
    return pivot.pct_change().dropna(how="all")


def _cost_assumptions(config: dict[str, Any]) -> CostAssumptions:
    return CostAssumptions(
        fee_bps_one_way=float(config["backtest"]["fee_bps_one_way"]),
        slippage_bps_one_way=float(config["backtest"]["slippage_bps_one_way"]),
    )


def _run_buy_and_hold_benchmark(
    market: PanelMarketData,
    *,
    symbol: str,
    decision_bar: pd.Timestamp,
    validation_start: pd.Timestamp,
    validation_end: pd.Timestamp,
    config: dict[str, Any],
    cost_assumptions: CostAssumptions,
) -> BacktestRunResult:
    max_weight = min(
        float(config["portfolio"]["max_gross_exposure"]),
        float(config["level_1"].get("max_weight", 1.0)),
        1.0 - float(config["level_1"].get("cost_buffer_weight", 0.005)),
    )
    schedule = pd.DataFrame(
        [{symbol: max_weight}], index=pd.DatetimeIndex([decision_bar], tz="UTC")
    )
    result = SimulatedBroker(
        market,
        initial_capital=float(config["backtest"]["initial_capital_usd"]),
        cost_assumptions=cost_assumptions,
    ).run(schedule, end_time=validation_end, run_label="level_1_buy_and_hold")
    return _trim_result(result, start=validation_start, end=validation_end)


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
    net = calculate_performance_metrics(
        net_result.equity,
        periods_per_year=int(config["backtest"]["annualization_periods"]),
        risk_free_rate=float(config["backtest"]["risk_free_rate"]),
        weights=net_result.weights,
        benchmark_nav=benchmark_nav,
    )
    gross = calculate_performance_metrics(
        gross_result.equity,
        periods_per_year=int(config["backtest"]["annualization_periods"]),
        risk_free_rate=float(config["backtest"]["risk_free_rate"]),
        weights=gross_result.weights,
        benchmark_nav=benchmark_nav,
    )
    metrics = dict(net)
    metrics.update({f"net_{key}": value for key, value in net.items()})
    metrics.update({f"gross_{key}": value for key, value in gross.items()})
    metrics["gross_to_net_total_return_decay"] = gross["total_return"] - net["total_return"]
    return metrics


def _select_candidate(candidates: list[_CandidateResult], *, metric: str) -> _CandidateResult:
    if not candidates:
        msg = "No Level 1 candidates were evaluated"
        raise ValueError(msg)
    metric_name = metric if metric.startswith("net_") else f"net_{metric}"
    return max(
        candidates,
        key=lambda candidate: (
            candidate.metrics.get(metric_name, float("-inf")),
            candidate.metrics.get("net_total_return", float("-inf")),
            -candidate.metrics.get("net_turnover", float("inf")),
            -candidate.fast_window,
            -candidate.slow_window,
        ),
    )


def _enrich_equity(
    net_result: BacktestRunResult,
    gross_result: BacktestRunResult,
    benchmark_result: BacktestRunResult,
) -> BacktestRunResult:
    equity = net_result.equity.copy()
    timestamps = pd.to_datetime(equity["timestamp"], utc=True)
    gross = gross_result.equity.set_index("timestamp")["nav"].rename("gross_nav")
    benchmark = benchmark_result.equity.set_index("timestamp")["nav"].rename("benchmark_nav")
    equity = equity.set_index(timestamps)
    equity["gross_nav"] = gross.reindex(equity.index).to_numpy()
    equity["benchmark_nav"] = benchmark.reindex(equity.index).to_numpy()
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
    symbol: str,
    validation_start: pd.Timestamp,
    validation_end: pd.Timestamp,
    cost_assumptions: CostAssumptions,
    selected: _CandidateResult,
    split: str = "validation",
    final_test_lock_hash: str | None = None,
) -> ArtifactProvenance:
    data_path = Path(config["paths"]["market_data"])
    data_hash = (
        file_sha256(data_path) if data_path.exists() else _frame_hash(selected.net_result.equity)
    )
    return ArtifactProvenance(
        level=LEVEL_NAME,
        run_label=RUN_LABEL if split == "validation" else "level_1_final_test_sma",
        split=split,
        data_hash=data_hash,
        config_hash=canonical_config_hash(config),
        git_commit=git_commit(),
        period_start=validation_start.date().isoformat(),
        period_end=validation_end.date().isoformat(),
        cost_assumptions={
            "fee_bps_one_way": cost_assumptions.fee_bps_one_way,
            "slippage_bps_one_way": cost_assumptions.slippage_bps_one_way,
        },
        benchmark="broker_costed_buy_and_hold",
        seed=int(config["project"]["seed"]),
        final_test_lock_hash=final_test_lock_hash,
        git_worktree_dirty=git_worktree_dirty(),
        git_diff_sha256=git_diff_sha256(),
        warnings=(
            "validation_only_no_final_test_metrics"
            if split == "validation"
            else "final_test_exposure_EXPOSED_frozen_lock",
            "survivorship_bias_active_markets",
            f"symbol={symbol}",
            f"sma_fast={selected.fast_window}",
            f"sma_slow={selected.slow_window}",
        ),
    )


def _frame_hash(frame: pd.DataFrame) -> str:
    digest = pd.util.hash_pandas_object(frame, index=True).sum()
    return f"frame-{int(digest):x}"


def _write_equity_figure(
    equity: pd.DataFrame,
    artifacts_dir: Path,
    provenance: ArtifactProvenance,
) -> Path:
    figures_dir = artifacts_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    path = figures_dir / "level_1_equity_curve.png"
    plot_frame = equity.copy()
    plot_frame["timestamp"] = pd.to_datetime(plot_frame["timestamp"], utc=True)
    initial_net = float(plot_frame["nav"].iloc[0])
    initial_gross = float(plot_frame["gross_nav"].iloc[0])
    initial_benchmark = float(plot_frame["benchmark_nav"].iloc[0])
    plt.figure(figsize=(10, 5))
    plt.plot(plot_frame["timestamp"], plot_frame["nav"] / initial_net, label="SMA net")
    plt.plot(
        plot_frame["timestamp"],
        plot_frame["gross_nav"] / initial_gross,
        label="SMA gross",
        linestyle="--",
    )
    plt.plot(
        plot_frame["timestamp"],
        plot_frame["benchmark_nav"] / initial_benchmark,
        label="Buy and hold net",
        alpha=0.8,
    )
    plt.title("Level 1 validation equity: SMA crossover vs buy-and-hold")
    plt.xlabel("Validation date")
    plt.ylabel("Normalized NAV")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    metadata_path = path.with_suffix(".png.metadata.json")
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(provenance.metadata(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


def _write_trace(
    *,
    traces: tuple[DecisionTrace, ...],
    path: Path,
    provenance: ArtifactProvenance,
    candidates: list[_CandidateResult],
    selected: _CandidateResult,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    representative = next(
        (
            trace
            for trace in traces
            if trace.aggregated_signals and trace.aggregated_signals[0].score > 0
        ),
        traces[0],
    )
    payload = {
        "provenance": provenance.metadata(),
        "selection": {
            "selected_fast_window": selected.fast_window,
            "selected_slow_window": selected.slow_window,
            "selection_metric": "net_sharpe",
            "candidate_count": len(candidates),
            "candidates": [
                {
                    "fast_window": candidate.fast_window,
                    "slow_window": candidate.slow_window,
                    "net_sharpe": candidate.metrics["net_sharpe"],
                    "net_roi": candidate.metrics["net_roi"],
                    "net_max_drawdown": candidate.metrics["net_max_drawdown"],
                }
                for candidate in candidates
            ],
        },
        "representative_decision_trace": _trace_to_dict(representative),
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


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
        "aggregated_signals": [_aggregate_to_dict(signal) for signal in trace.aggregated_signals],
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


def _aggregate_to_dict(signal: AggregatedSignal) -> dict[str, Any]:
    return {
        "symbol": signal.symbol,
        "score": signal.score,
        "confidence": signal.confidence,
        "contributions": dict(signal.contributions),
        "disagreement": signal.disagreement,
        "reason_codes": [code.value for code in signal.reason_codes],
    }
