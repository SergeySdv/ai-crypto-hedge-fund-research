"""Level 2 validation runner for one-pair econometric, ML and agent ensemble models."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from crypto_hedge_fund.agents import (
    PredictionTableSignalAgent,
    SignalAggregator,
    TypedAgentOrchestrator,
)
from crypto_hedge_fund.artifacts import ArtifactProvenance, BacktestArtifactWriter
from crypto_hedge_fund.clock import build_daily_research_clock, ensure_utc
from crypto_hedge_fund.config import load_config
from crypto_hedge_fund.execution import BacktestRunResult, CostAssumptions, PanelMarketData
from crypto_hedge_fund.execution.broker import SimulatedBroker
from crypto_hedge_fund.features import LEVEL2_FEATURE_COLUMNS, build_level2_feature_frame
from crypto_hedge_fund.metrics import calculate_performance_metrics
from crypto_hedge_fund.models import fit_econometric_forecast, walk_forward_ml_predictions
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

LEVEL_NAME = "level_2"
RUN_LABEL = "level_2_validation_agent_ensemble"
APPROACHES = (
    "technical_sma",
    "econometric_ar_garch",
    "ml_logistic",
    "ml_hist_gradient_boosting",
    "agent_ensemble",
)


@dataclass(frozen=True)
class Level2ValidationResult:
    """Paths and summary settings from the Level 2 validation run."""

    metrics: dict[str, float]
    artifact_paths: dict[str, Path]
    figure_path: Path
    trace_path: Path
    robustness_path: Path
    selected_approach: str
    feature_columns: tuple[str, ...]
    prediction_paths: dict[str, Path]


@dataclass(frozen=True)
class _ApproachResult:
    name: str
    schedule: pd.DataFrame
    traces: tuple[DecisionTrace, ...]
    net_result: BacktestRunResult
    gross_result: BacktestRunResult
    metrics: dict[str, float]


class _RiskScaledSingleAssetAllocator:
    name = "level2_risk_scaled_single_asset"

    def __init__(self, *, max_weight: float, min_confidence: float) -> None:
        self.max_weight = float(max_weight)
        self.min_confidence = float(min_confidence)

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
            confidence = float(previous_weights.attrs.get(f"confidence:{symbol}", 1.0))
            if (
                score > 0
                and confidence >= self.min_confidence
                and symbol not in constraints.blocked_symbols
                and constraints.per_asset_caps.get(symbol, 0.0) > 0
            ):
                raw_weight = min(1.0, max(0.0, float(score) * confidence)) * self.max_weight
                weights[symbol] = min(
                    raw_weight,
                    constraints.max_gross_exposure,
                    constraints.per_asset_caps.get(symbol, 0.0),
                )
        target = pd.Series(weights, dtype="float64")
        previous = previous_weights.astype("float64").reindex(target.index, fill_value=0.0)
        expected_turnover = (
            float((target - previous).abs().sum())
            if not target.empty
            else float(previous_weights.abs().sum())
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
            metadata={"allocator": self.name, "min_confidence": self.min_confidence},
        )


def run_level_2_validation(
    *,
    config_path: str | Path = Path("configs/default.yaml"),
    artifacts_dir: str | Path | None = None,
    market_frame: pd.DataFrame | None = None,
    split: str = "validation",
    final_test_lock_hash: str | None = None,
) -> Level2ValidationResult:
    """Run Level 2 and write required comparison artifacts."""

    if split not in {"validation", "final_test"}:
        msg = f"unsupported Level 2 split: {split}"
        raise ValueError(msg)
    if split == "final_test" and not final_test_lock_hash:
        msg = "final_test_lock_hash is required for Level 2 final-test runs"
        raise ValueError(msg)
    config = load_config(config_path, resolve_paths=True)
    level_config = dict(config.get("level_2", {}))
    cadence = _level2_cadence(config)
    symbol = str(level_config.get("symbol", config["level_1"]["symbol"]))
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
    train_start = pd.Timestamp(ensure_utc(config["splits"]["train_start"]))
    test_start = pd.Timestamp(ensure_utc(config["splits"]["test_start"]))
    if split == "validation" and validation_end >= test_start:
        msg = "validation_end must be before test_start for validation-only Level 2"
        raise ValueError(msg)

    output_dir = (
        Path(artifacts_dir) if artifacts_dir is not None else Path(config["paths"]["artifacts"])
    )
    frame = (
        _load_symbol_frame(config, symbol=symbol, validation_end=validation_end)
        if market_frame is None
        else _normalize_market_frame(market_frame, symbol=symbol, end=validation_end)
    )
    threshold_return = _target_threshold(config)
    features = build_level2_feature_frame(
        frame,
        symbol=symbol,
        horizon_open_days=int(level_config.get("prediction_horizon_open_days", 1)),
        threshold_return=threshold_return,
    )
    validation_mask = (features["execution_time"] >= validation_start) & (
        features["execution_time"] <= validation_end
    )
    if not bool(validation_mask.any()):
        msg = "Level 2 validation feature frame has no validation decisions"
        raise ValueError(msg)

    seeds = tuple(int(seed) for seed in config["statistics"]["random_seeds"])
    ml_outputs = walk_forward_ml_predictions(
        features,
        feature_columns=LEVEL2_FEATURE_COLUMNS,
        validation_mask=validation_mask,
        seeds=seeds,
        min_train_samples=int(level_config.get("min_train_samples", 120)),
        refit_frequency=cadence["ml_refit_frequency"],
    )
    econometric_predictions = _econometric_predictions(
        features,
        validation_mask=validation_mask,
        refit_frequency=cadence["econometric_refit_frequency"],
    )
    prediction_tables = {
        "econometric_ar_garch": econometric_predictions,
        **{output.model_name: output.predictions for output in ml_outputs},
    }
    predictive_metrics = {output.model_name: output.predictive_metrics for output in ml_outputs}
    predictive_metrics["econometric_ar_garch"] = _directional_prediction_metrics(
        econometric_predictions
    )

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

    approaches: list[_ApproachResult] = []
    for approach_name, agents, weights in _approach_agents(
        config=config,
        symbol=symbol,
        prediction_tables=prediction_tables,
    ):
        schedule, traces = build_level_2_target_schedule(
            frame=frame,
            features=features,
            symbol=symbol,
            agents=agents,
            agent_weights=weights,
            config=config,
            approach_name=approach_name,
            split=split,
        )
        net_result = _trim_result(
            SimulatedBroker(
                market,
                initial_capital=float(config["backtest"]["initial_capital_usd"]),
                cost_assumptions=cost_assumptions,
            ).run(schedule, end_time=validation_end, run_label=f"{RUN_LABEL}_{approach_name}"),
            start=validation_start,
            end=validation_end,
        )
        gross_result = _trim_result(
            SimulatedBroker(
                market,
                initial_capital=float(config["backtest"]["initial_capital_usd"]),
                cost_assumptions=CostAssumptions(fee_bps_one_way=0.0, slippage_bps_one_way=0.0),
            ).run(
                schedule, end_time=validation_end, run_label=f"{RUN_LABEL}_{approach_name}_gross"
            ),
            start=validation_start,
            end=validation_end,
        )
        metrics = _combined_metrics(
            net_result,
            gross_result,
            benchmark_nav=benchmark_nav,
            config=config,
        )
        if approach_name in predictive_metrics:
            metrics.update(
                {
                    f"predictive_{key}": value
                    for key, value in predictive_metrics[approach_name].items()
                }
            )
        approaches.append(
            _ApproachResult(
                name=approach_name,
                schedule=schedule,
                traces=traces,
                net_result=net_result,
                gross_result=gross_result,
                metrics=metrics,
            )
        )

    selected = next(item for item in approaches if item.name == "agent_ensemble")
    provenance = _provenance(
        config=config,
        symbol=symbol,
        train_start=train_start,
        validation_start=validation_start,
        validation_end=validation_end,
        cost_assumptions=cost_assumptions,
        threshold_return=threshold_return,
        selected_approach=selected.name,
        cadence=cadence,
        split=split,
        final_test_lock_hash=final_test_lock_hash,
    )
    artifact_paths = _write_level2_artifacts(
        approaches,
        output_dir=output_dir,
        provenance=provenance,
    )
    figure_path = _write_equity_figure(approaches, output_dir, provenance)
    trace_path = _write_trace(
        traces=selected.traces,
        path=output_dir / "monitoring" / "level_2_decision_trace.json",
        provenance=provenance,
        predictive_metrics=predictive_metrics,
        feature_columns=LEVEL2_FEATURE_COLUMNS,
        cadence=cadence,
    )
    robustness = _robustness_checks(
        selected=selected,
        features=features.loc[validation_mask].copy(),
        config=config,
        cadence=cadence,
    )
    robustness_path = _write_json_artifact(
        output_dir / "monitoring" / "level_2_robustness.json",
        {"provenance": provenance.metadata(), "robustness": robustness},
    )
    prediction_paths = _write_prediction_artifacts(
        output_dir,
        provenance=provenance,
        prediction_tables=prediction_tables,
        ml_outputs=ml_outputs,
        cadence=cadence,
    )
    return Level2ValidationResult(
        metrics={f"{selected.name}_{key}": value for key, value in selected.metrics.items()},
        artifact_paths=artifact_paths,
        figure_path=figure_path,
        trace_path=trace_path,
        robustness_path=robustness_path,
        selected_approach=selected.name,
        feature_columns=LEVEL2_FEATURE_COLUMNS,
        prediction_paths=prediction_paths,
    )


def build_level_2_target_schedule(
    *,
    frame: pd.DataFrame,
    features: pd.DataFrame,
    symbol: str,
    agents: tuple[Any, ...],
    agent_weights: dict[str, float],
    config: dict[str, Any],
    approach_name: str,
    split: str = "validation",
) -> tuple[pd.DataFrame, tuple[DecisionTrace, ...]]:
    """Create risk-approved target weights through the Stage 4 orchestrator path."""

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
    orchestrator = TypedAgentOrchestrator(
        agents,
        aggregator=SignalAggregator(
            agent_weights=agent_weights,
            disagreement_threshold=float(config["risk"]["max_agent_disagreement"]),
        ),
    )
    level_config = dict(config.get("level_2", {}))
    pre_risk = PreAllocationRiskPolicy(
        max_gross_exposure=float(config["portfolio"]["max_gross_exposure"]),
        max_per_asset_weight=float(level_config.get("max_weight", 1.0)),
        cost_buffer_weight=float(level_config.get("cost_buffer_weight", 0.005)),
        min_dollar_volume=float(level_config.get("min_dollar_volume", 0.0)),
        max_stale_data_days=0,
        max_model_age_days=int(level_config.get("max_model_age_days", 60)),
        max_agent_disagreement=float(config["risk"]["max_agent_disagreement"]),
        volatility_target=None,
        turnover_cap=None,
    )
    allocator = _RiskScaledSingleAssetAllocator(
        max_weight=float(level_config.get("max_weight", 1.0)),
        min_confidence=float(level_config.get("min_confidence", 0.0)),
    )
    rebalance_policy = AlwaysRebalancePolicy(trigger_code=approach_name)
    post_risk = PostAllocationRiskPolicy(
        max_drawdown_stop=float(config["risk"]["max_drawdown_stop"]),
        high_volatility_threshold=float(config["risk"]["high_volatility_threshold_annual"]),
        min_cash_buffer=float(level_config.get("min_cash_buffer", 0.005)),
        annualization_periods=int(config["backtest"]["annualization_periods"]),
    )

    rows: list[dict[str, float]] = []
    index: list[pd.Timestamp] = []
    traces: list[DecisionTrace] = []
    current_weights = pd.Series({symbol: 0.0}, dtype="float64")
    feature_rows = features.loc[
        (features["bar_start_utc"] >= first_decision_bar)
        & (features["execution_time"] >= validation_start)
        & (features["execution_time"] <= validation_end)
    ]
    feature_by_bar = {
        pd.Timestamp(row.bar_start_utc): row for row in feature_rows.itertuples(index=False)
    }
    for bar_start, feature_row in feature_by_bar.items():
        clock = build_daily_research_clock(bar_start.to_pydatetime())
        execution_time = pd.Timestamp(clock.execution_time)
        history = normalized.loc[normalized["bar_start_utc"] <= bar_start].set_index(
            "bar_start_utc"
        )
        model_fit_cutoff = _minimum_fit_cutoff(agents, bar_start, fallback=clock.feature_cutoff)
        context = AgentContext(
            clock=clock,
            symbols=(symbol,),
            model_fit_cutoff=pd.Timestamp(model_fit_cutoff).to_pydatetime(),
            portfolio_nav=float(config["backtest"]["initial_capital_usd"]),
            current_weights=current_weights.to_dict(),
            health_state={
                "realized_volatility": float(getattr(feature_row, "realized_vol_20", 0.0))
            },
            metadata={
                "level": LEVEL_NAME,
                "split": split,
                "approach": approach_name,
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
        confidence_by_symbol = {
            f"confidence:{signal.symbol}": signal.confidence for signal in run.aggregated_signals
        }
        current_weights.attrs.update(confidence_by_symbol)
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
                    "approach": approach_name,
                    "execution_time": execution_time.isoformat(),
                    "resolved_action": executable.action,
                    "resolved_weights": dict(executable.risky_weights),
                    "resolved_cash_weight": executable.cash_weight,
                    "forward_return": float(feature_row.forward_return),
                },
            )
        )

    if not rows:
        msg = f"Level 2 {approach_name} produced no executable target-weight rows"
        raise ValueError(msg)
    return pd.DataFrame(rows, index=pd.DatetimeIndex(index, tz="UTC")), tuple(traces)


def _approach_agents(
    *,
    config: dict[str, Any],
    symbol: str,
    prediction_tables: dict[str, pd.DataFrame],
) -> list[tuple[str, tuple[Any, ...], dict[str, float]]]:
    level_config = dict(config.get("level_2", {}))
    technical = SMACrossoverSignalAgent(
        fast_window=int(level_config.get("technical_fast_window", 10)),
        slow_window=int(level_config.get("technical_slow_window", 50)),
    )
    econometric = PredictionTableSignalAgent(
        "econometric_ar_garch", prediction_tables["econometric_ar_garch"]
    )
    logistic = PredictionTableSignalAgent("ml_logistic", prediction_tables["ml_logistic"])
    hgb = PredictionTableSignalAgent(
        "ml_hist_gradient_boosting", prediction_tables["ml_hist_gradient_boosting"]
    )
    del symbol
    ensemble_weights = {
        "sma_crossover": float(level_config.get("technical_weight", 0.25)),
        "econometric_ar_garch": float(level_config.get("econometric_weight", 0.25)),
        "ml_logistic": float(level_config.get("logistic_weight", 0.25)),
        "ml_hist_gradient_boosting": float(level_config.get("hgb_weight", 0.25)),
    }
    return [
        ("technical_sma", (technical,), {"sma_crossover": 1.0}),
        ("econometric_ar_garch", (econometric,), {"econometric_ar_garch": 1.0}),
        ("ml_logistic", (logistic,), {"ml_logistic": 1.0}),
        ("ml_hist_gradient_boosting", (hgb,), {"ml_hist_gradient_boosting": 1.0}),
        ("agent_ensemble", (technical, econometric, logistic, hgb), ensemble_weights),
    ]


def _minimum_fit_cutoff(
    agents: tuple[Any, ...],
    bar_start: pd.Timestamp,
    *,
    fallback: pd.Timestamp,
) -> pd.Timestamp:
    cutoffs: list[pd.Timestamp] = []
    for agent in agents:
        table = getattr(agent, "predictions", None)
        if isinstance(table, pd.DataFrame) and not table.empty:
            normalized = table.copy()
            normalized["bar_start_utc"] = pd.to_datetime(normalized["bar_start_utc"], utc=True)
            rows = normalized.loc[normalized["bar_start_utc"] == bar_start]
            if not rows.empty and pd.notna(rows.iloc[-1].get("fit_cutoff")):
                cutoffs.append(pd.Timestamp(rows.iloc[-1]["fit_cutoff"]))
    return min(cutoffs) if cutoffs else fallback


def _econometric_predictions(
    features: pd.DataFrame,
    *,
    validation_mask: pd.Series,
    refit_frequency: str,
) -> pd.DataFrame:
    if refit_frequency not in {"daily", "daily_causal", "daily_expanding_validation"}:
        msg = f"unsupported econometric refit frequency: {refit_frequency}"
        raise ValueError(msg)
    rows: list[dict[str, object]] = []
    validation_rows = features.loc[validation_mask].copy()
    open_returns = features.set_index("bar_start_utc")["open_return_1d"]
    for row in validation_rows.itertuples(index=False):
        execution_time = pd.Timestamp(row.execution_time)
        available = features.loc[features["label_observation_time"] < execution_time]
        history = open_returns.reindex(available["bar_start_utc"]).dropna()
        forecast = fit_econometric_forecast(history)
        if forecast.status == "ok" and forecast.volatility > 0:
            risk_adjusted = forecast.expected_return / max(forecast.volatility, 1e-8)
            score = float(np.tanh(risk_adjusted * 3.0))
            confidence = float(min(1.0, abs(risk_adjusted) * 4.0))
            status = "ok"
        else:
            score = 0.0
            confidence = 0.0
            status = "abstain"
        rows.append(
            {
                "bar_start_utc": pd.Timestamp(row.bar_start_utc),
                "execution_time": execution_time,
                "feature_cutoff": pd.Timestamp(row.feature_cutoff),
                "fit_cutoff": pd.Timestamp(available["label_observation_time"].max())
                if not available.empty
                else pd.NaT,
                "probability": 0.5 + score / 2.0,
                "score": score,
                "confidence": confidence,
                "expected_return": forecast.expected_return,
                "forecast_volatility": forecast.volatility,
                "target_label": int(row.target_label),
                "forward_return": float(row.forward_return),
                "method": forecast.method,
                "status": status,
                "reason": forecast.reason,
                "refit_frequency": "daily_causal",
                "train_samples": len(history),
                "used_future_labels": bool(
                    not available.empty
                    and (available["label_observation_time"] >= execution_time).any()
                ),
            }
        )
    return pd.DataFrame(rows)


def _directional_prediction_metrics(predictions: pd.DataFrame) -> dict[str, float]:
    if predictions.empty:
        return {"directional_accuracy": 0.0, "coverage": 0.0}
    active = predictions.loc[predictions["status"] == "ok"].copy()
    if active.empty:
        return {"directional_accuracy": 0.0, "coverage": 0.0}
    predicted = active["expected_return"] > 0
    actual = active["forward_return"] > active.get("target_threshold_return", 0.0)
    return {
        "directional_accuracy": float((predicted == actual).mean()),
        "coverage": float(len(active) / len(predictions)),
        "mean_forecast_volatility": float(active["forecast_volatility"].mean()),
    }


def _level2_cadence(config: dict[str, Any]) -> dict[str, str]:
    level_config = dict(config.get("level_2", {}))
    ml_refit = str(
        level_config.get(
            "ml_default_retrain",
            level_config.get("default_retrain", "monthly"),
        )
    )
    econometric_refit = str(level_config.get("econometric_refit", "daily_causal"))
    return {
        "ml_refit_frequency": ml_refit,
        "econometric_refit_frequency": econometric_refit,
    }


def _target_threshold(config: dict[str, Any]) -> float:
    one_way_bps = float(config["backtest"]["fee_bps_one_way"]) + float(
        config["backtest"]["slippage_bps_one_way"]
    )
    safety_bps = float(config.get("level_2", {}).get("safety_margin_bps", 5.0))
    return (one_way_bps + safety_bps) / 10_000.0


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
    source["bar_end_utc"] = (
        pd.to_datetime(source["bar_end_utc"], utc=True)
        if "bar_end_utc" in source.columns
        else source["bar_start_utc"] + pd.Timedelta(days=1)
    )
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
    level_config = dict(config.get("level_2", {}))
    max_weight = min(
        float(config["portfolio"]["max_gross_exposure"]),
        float(level_config.get("max_weight", 1.0)),
        1.0 - float(level_config.get("cost_buffer_weight", 0.005)),
    )
    schedule = pd.DataFrame(
        [{symbol: max_weight}], index=pd.DatetimeIndex([decision_bar], tz="UTC")
    )
    result = SimulatedBroker(
        market,
        initial_capital=float(config["backtest"]["initial_capital_usd"]),
        cost_assumptions=cost_assumptions,
    ).run(schedule, end_time=validation_end, run_label="level_2_buy_and_hold")
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


def _provenance(
    *,
    config: dict[str, Any],
    symbol: str,
    train_start: pd.Timestamp,
    validation_start: pd.Timestamp,
    validation_end: pd.Timestamp,
    cost_assumptions: CostAssumptions,
    threshold_return: float,
    selected_approach: str,
    cadence: dict[str, str],
    split: str = "validation",
    final_test_lock_hash: str | None = None,
) -> ArtifactProvenance:
    data_path = Path(config["paths"]["market_data"])
    return ArtifactProvenance(
        level=LEVEL_NAME,
        run_label=RUN_LABEL if split == "validation" else "level_2_final_test_agent_ensemble",
        split=split,
        data_hash=file_sha256(data_path) if data_path.exists() else "in_memory_frame",
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
            "model_selection_validation_only",
            f"symbol={symbol}",
            f"train_start={train_start.date().isoformat()}",
            f"target_threshold_return={threshold_return:.8f}",
            f"selected_approach={selected_approach}",
            f"ml_refit_frequency={cadence['ml_refit_frequency']}",
            f"econometric_refit_frequency={cadence['econometric_refit_frequency']}",
        ),
    )


def _write_level2_artifacts(
    approaches: list[_ApproachResult],
    *,
    output_dir: Path,
    provenance: ArtifactProvenance,
) -> dict[str, Path]:
    paths = {
        "metrics": output_dir / "metrics" / "level_2.csv",
        "equity": output_dir / "equity" / "level_2.parquet",
        "weights": output_dir / "weights" / "level_2.parquet",
        "orders": output_dir / "orders" / "level_2.parquet",
        "fills": output_dir / "fills" / "level_2.parquet",
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    metric_rows: list[dict[str, object]] = []
    equity_frames: list[pd.DataFrame] = []
    weight_frames: list[pd.DataFrame] = []
    order_frames: list[pd.DataFrame] = []
    fill_frames: list[pd.DataFrame] = []
    metadata_columns = BacktestArtifactWriter._provenance_columns(provenance)
    for approach in approaches:
        metric_rows.append(
            {
                "approach": approach.name,
                "selected_for_level_2": approach.name == "agent_ensemble",
                **approach.metrics,
                **metadata_columns,
            }
        )
        equity_frames.append(_tag_frame(approach.net_result.equity, approach.name))
        weight_frames.append(_tag_frame(approach.net_result.weights, approach.name))
        order_frames.append(_tag_frame(approach.net_result.orders, approach.name))
        fill_frames.append(_tag_frame(approach.net_result.fills, approach.name))
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


def _tag_frame(frame: pd.DataFrame, approach: str) -> pd.DataFrame:
    tagged = frame.copy()
    tagged["approach"] = approach
    return tagged


def _write_equity_figure(
    approaches: list[_ApproachResult],
    output_dir: Path,
    provenance: ArtifactProvenance,
) -> Path:
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    path = figures_dir / "level_2_equity_curve.png"
    plt.figure(figsize=(10, 5))
    for approach in approaches:
        equity = approach.net_result.equity.copy()
        equity["timestamp"] = pd.to_datetime(equity["timestamp"], utc=True)
        if equity.empty:
            continue
        base = float(equity["nav"].iloc[0])
        plt.plot(equity["timestamp"], equity["nav"] / base, label=approach.name)
    plt.title("Level 2 validation equity: agents and ensemble")
    plt.xlabel("Validation date")
    plt.ylabel("Normalized net NAV")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    _write_metadata_sidecar(path, provenance)
    return path


def _write_trace(
    *,
    traces: tuple[DecisionTrace, ...],
    path: Path,
    provenance: ArtifactProvenance,
    predictive_metrics: dict[str, dict[str, float]],
    feature_columns: tuple[str, ...],
    cadence: dict[str, str],
) -> Path:
    representative = next(
        (
            trace
            for trace in traces
            if len(trace.signals) >= 4 and any(signal.confidence > 0 for signal in trace.signals)
        ),
        traces[0],
    )
    payload = {
        "provenance": provenance.metadata(),
        "feature_definition": {
            "feature_set": "level2_daily_causal_v1",
            "columns": list(feature_columns),
            "target": "forward_return = open(t+2) / open(t+1) - 1; label above cost threshold",
            "split_protocol": (
                "expanding walk-forward; labels only when observation time is before execution"
            ),
            "cadence": {
                "ml_refit_frequency": cadence["ml_refit_frequency"],
                "econometric_refit_frequency": cadence["econometric_refit_frequency"],
                "econometric_note": (
                    "AutoReg/GARCH forecasts are refit for each validation decision using "
                    "only labels observed before that execution time"
                ),
            },
        },
        "predictive_metrics": predictive_metrics,
        "representative_decision_trace": _trace_to_dict(representative),
    }
    return _write_json_artifact(path, payload)


def _robustness_checks(
    *,
    selected: _ApproachResult,
    features: pd.DataFrame,
    config: dict[str, Any],
    cadence: dict[str, str],
) -> dict[str, Any]:
    returns = selected.net_result.equity["nav"].astype("float64").pct_change().dropna()
    repetitions = int(config["statistics"]["bootstrap_repetitions"])
    permutation_repetitions = int(config["statistics"]["permutation_repetitions"])
    block_length = int(config["statistics"]["block_length_days"])
    rng = np.random.default_rng(int(config["project"]["seed"]))
    boot_means = []
    boot_sharpes = []
    values = returns.to_numpy()
    if len(values) > 0:
        for _ in range(repetitions):
            sample = _moving_block_sample(values, block_length=block_length, rng=rng)
            boot_means.append(float(np.mean(sample)))
            boot_sharpes.append(_sharpe(sample))
    observed_score_return_corr = _score_return_correlation(selected.traces, features)
    shifted = []
    returns_by_bar = features.set_index("bar_start_utc")["forward_return"].to_numpy()
    scores = np.array(
        [
            trace.aggregated_signals[0].score if trace.aggregated_signals else 0.0
            for trace in selected.traces
        ],
        dtype="float64",
    )
    n = min(len(scores), len(returns_by_bar))
    if n > 2:
        for _ in range(permutation_repetitions):
            shift = int(rng.integers(1, n))
            shifted.append(float(np.corrcoef(scores[:n], np.roll(returns_by_bar[:n], shift))[0, 1]))
    cost_stress = {
        "1x_recorded_net_roi": float(selected.metrics["net_roi"]),
        "gross_to_net_total_return_decay": float(
            selected.metrics["gross_to_net_total_return_decay"]
        ),
        "reported_as_validation_only": 1.0,
    }
    return {
        "block_bootstrap": {
            "repetitions": repetitions,
            "block_length_days": block_length,
            "mean_return_ci_95": _percentiles(boot_means),
            "sharpe_ci_95": _percentiles(boot_sharpes),
        },
        "circular_shift_randomization": {
            "repetitions": permutation_repetitions,
            "observed_score_forward_return_correlation": observed_score_return_corr,
            "two_sided_p_value": _two_sided_p_value(observed_score_return_corr, shifted),
        },
        "multiple_seeds": {
            "seeds": [int(seed) for seed in config["statistics"]["random_seeds"]],
            "purpose": (
                "ML walk-forward fitting repeated across configured seeds; first seed drives "
                "trading artifacts"
            ),
        },
        "cost_sensitivity": cost_stress,
        "cadence": cadence,
    }


def _moving_block_sample(
    values: np.ndarray, *, block_length: int, rng: np.random.Generator
) -> np.ndarray:
    if len(values) == 0:
        return values
    block = max(1, min(block_length, len(values)))
    samples: list[float] = []
    while len(samples) < len(values):
        start = int(rng.integers(0, len(values)))
        for offset in range(block):
            samples.append(float(values[(start + offset) % len(values)]))
            if len(samples) >= len(values):
                break
    return np.array(samples, dtype="float64")


def _sharpe(values: np.ndarray) -> float:
    std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    return float(np.mean(values) / std * np.sqrt(365.0)) if std > 0 else 0.0


def _percentiles(values: list[float]) -> list[float]:
    if not values:
        return [0.0, 0.0]
    low, high = np.percentile(np.array(values, dtype="float64"), [2.5, 97.5])
    return [float(low), float(high)]


def _score_return_correlation(traces: tuple[DecisionTrace, ...], features: pd.DataFrame) -> float:
    by_bar = features.set_index("bar_start_utc")["forward_return"]
    scores = []
    returns = []
    for trace in traces:
        bar_start = pd.Timestamp(trace.clock.bar_start)
        if bar_start in by_bar.index and trace.aggregated_signals:
            scores.append(float(trace.aggregated_signals[0].score))
            returns.append(float(by_bar.loc[bar_start]))
    if len(scores) < 3 or np.std(scores) <= 0 or np.std(returns) <= 0:
        return 0.0
    return float(np.corrcoef(scores, returns)[0, 1])


def _two_sided_p_value(observed: float, shifted: list[float]) -> float:
    if not shifted:
        return 1.0
    extreme = sum(abs(value) >= abs(observed) for value in shifted)
    return float((extreme + 1) / (len(shifted) + 1))


def _write_prediction_artifacts(
    output_dir: Path,
    *,
    provenance: ArtifactProvenance,
    prediction_tables: dict[str, pd.DataFrame],
    ml_outputs: list[Any],
    cadence: dict[str, str],
) -> dict[str, Path]:
    monitoring = output_dir / "monitoring"
    monitoring.mkdir(parents=True, exist_ok=True)
    predictions_path = monitoring / "level_2_model_predictions.parquet"
    audit_path = monitoring / "level_2_fit_audit.parquet"
    prediction_frames: list[pd.DataFrame] = []
    for model, table in prediction_tables.items():
        tagged = _tag_frame(table, model)
        if "refit_frequency" not in tagged.columns or tagged["refit_frequency"].isna().any():
            frequency = (
                cadence["ml_refit_frequency"]
                if model.startswith("ml_")
                else cadence["econometric_refit_frequency"]
            )
            tagged["refit_frequency"] = tagged.get("refit_frequency", frequency)
            tagged["refit_frequency"] = tagged["refit_frequency"].fillna(frequency)
        prediction_frames.append(tagged)
    predictions = pd.concat(prediction_frames, ignore_index=True)
    audits = [output.fit_audit for output in ml_outputs]
    audits.append(
        prediction_tables["econometric_ar_garch"][
            [
                "bar_start_utc",
                "execution_time",
                "fit_cutoff",
                "train_samples",
                "used_future_labels",
                "status",
                "refit_frequency",
            ]
        ].assign(model="econometric_ar_garch", seed=0)
    )
    prediction_columns = BacktestArtifactWriter._provenance_columns(provenance)
    for key, value in prediction_columns.items():
        predictions[key] = value
    predictions.to_parquet(predictions_path, index=False)
    pd.concat(audits, ignore_index=True).to_parquet(audit_path, index=False)
    _write_metadata_sidecar(predictions_path, provenance)
    _write_metadata_sidecar(audit_path, provenance)
    return {"predictions": predictions_path, "fit_audit": audit_path}


def _write_json_artifact(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
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
        "events": [
            {
                "component": event.component,
                "severity": event.severity,
                "reason_codes": [code.value for code in event.reason_codes],
                "message": event.message,
                "metadata": dict(event.metadata),
            }
            for event in trace.events
        ],
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
