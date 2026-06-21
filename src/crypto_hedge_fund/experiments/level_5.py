"""Level 5 large-universe dynamic portfolio management on validation data only."""

from __future__ import annotations

import json
import math
import resource
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from crypto_hedge_fund.artifacts import ArtifactProvenance, BacktestArtifactWriter
from crypto_hedge_fund.clock import build_daily_research_clock
from crypto_hedge_fund.config import load_config
from crypto_hedge_fund.data.universe import (
    UniverseRules,
    eligible_universe_at,
    selected_large_universe,
)
from crypto_hedge_fund.execution import BacktestRunResult, CostAssumptions, PanelMarketData
from crypto_hedge_fund.execution.broker import SimulatedBroker
from crypto_hedge_fund.experiments.level_3 import (
    _cost_assumptions,
    _historical_open_returns,
    _load_instruments,
    _load_market_frame,
    _normalize_instruments,
    _normalize_market_frame,
    _trim_result,
    _utc,
    _with_initial_capital_baseline,
)
from crypto_hedge_fund.experiments.level_4 import _drifted_current_weights
from crypto_hedge_fund.features.level5 import Level5ScoringConfig, build_level5_score_frame
from crypto_hedge_fund.metrics import calculate_performance_metrics
from crypto_hedge_fund.portfolio import InverseVolatilityAllocator
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

LEVEL_NAME = "level_5"
RUN_LABEL = "level_5_validation_large_universe_dynamic"


@dataclass(frozen=True)
class Level5ValidationResult:
    """Paths and proof counts from a Level 5 validation run."""

    metrics: dict[str, Any]
    artifact_paths: dict[str, Path]
    figure_path: Path
    pair_count_proof_path: Path
    universe_scores_path: Path
    rebalance_log_path: Path
    decision_trace_path: Path
    health_summary_path: Path
    alerts_path: Path
    scored_count: int
    selected_count: int
    symbols: tuple[str, ...]


def run_level_5_validation(
    *,
    config_path: str | Path = Path("configs/default.yaml"),
    artifacts_dir: str | Path | None = None,
    market_frame: pd.DataFrame | None = None,
    instruments: pd.DataFrame | None = None,
    split: str = "validation",
    final_test_lock_hash: str | None = None,
) -> Level5ValidationResult:
    """Run Level 5 and write large-universe artifacts."""

    if split not in {"validation", "final_test"}:
        msg = f"unsupported Level 5 split: {split}"
        raise ValueError(msg)
    if split == "final_test" and not final_test_lock_hash:
        msg = "final_test_lock_hash is required for Level 5 final-test runs"
        raise ValueError(msg)
    started = time.perf_counter()
    config = load_config(config_path, resolve_paths=True)
    level_config = _level5_config(config)
    if split == "validation":
        decision_start = _utc(level_config["validation_decision_start"])
        decision_end = _utc(level_config["validation_decision_end"])
        validation_start = _utc(level_config["validation_evaluation_start"])
        validation_end = _utc(level_config["validation_evaluation_end"])
    else:
        validation_start = _utc(config["splits"]["test_start"])
        validation_end = _utc(config["splits"]["test_end"])
        decision_start = validation_start - pd.Timedelta(days=1)
        decision_end = validation_end - pd.Timedelta(days=1)
    test_start = _utc(config["splits"]["test_start"])
    if split == "validation" and (validation_end >= test_start or decision_end >= test_start):
        msg = "Level 5 validation must end before final-test start"
        raise ValueError(msg)
    if decision_start > decision_end:
        msg = "Level 5 decision start must be on or before decision end"
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
    market = PanelMarketData.from_ohlcv(frame)
    cost_assumptions = _cost_assumptions(config)

    schedule, score_frame, rebalance_log, traces = build_level_5_target_schedule(
        frame=frame,
        instruments=instruments_frame,
        config=config,
        decision_start=decision_start,
        decision_end=decision_end,
        split=split,
    )
    symbols = tuple(str(symbol) for symbol in schedule.columns)
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

    benchmark_nav = _benchmark_nav(frame, start=validation_start, end=validation_end, config=config)
    enriched = _enrich_equity(net_result, gross_result, benchmark_nav)
    metrics = _metrics(
        enriched,
        gross_result,
        benchmark_nav=benchmark_nav,
        score_frame=score_frame,
        rebalance_log=rebalance_log,
        config=config,
        split=split,
    )
    runtime_seconds = time.perf_counter() - started
    peak_rss_mb = _peak_rss_mb()
    metrics["runtime_seconds"] = runtime_seconds
    metrics["peak_rss_mb"] = peak_rss_mb
    provenance = _provenance(
        config=config,
        validation_start=validation_start,
        validation_end=validation_end,
        decision_start=decision_start,
        decision_end=decision_end,
        cost_assumptions=cost_assumptions,
        scored_count=int(score_frame.groupby("decision_bar_start")["symbol"].nunique().max()),
        selected_count=int(score_frame.groupby("decision_bar_start")["selected_top_k"].sum().max()),
        split=split,
        final_test_lock_hash=final_test_lock_hash,
    )

    artifact_paths = BacktestArtifactWriter(output_dir).write_run(
        enriched,
        metrics,
        provenance,
        level_name=LEVEL_NAME,
    )
    figure_path = _write_equity_figure(enriched, output_dir, provenance)
    score_path = _write_scores(score_frame, output_dir, provenance)
    rebalance_path = _write_rebalance_log(rebalance_log, output_dir, provenance)
    health_path, alerts_path = _write_health_artifacts(
        score_frame,
        rebalance_log,
        output_dir,
        provenance,
        runtime_seconds=runtime_seconds,
        peak_rss_mb=peak_rss_mb,
        config=config,
    )
    proof_path = _write_pair_count_proof(
        score_frame,
        rebalance_log,
        output_dir,
        provenance,
        runtime_seconds=runtime_seconds,
        peak_rss_mb=peak_rss_mb,
        config=config,
    )
    trace_path = _write_decision_trace(
        traces=traces,
        score_frame=score_frame,
        rebalance_log=rebalance_log,
        output_dir=output_dir,
        provenance=provenance,
        config=config,
    )

    return Level5ValidationResult(
        metrics=metrics,
        artifact_paths=artifact_paths,
        figure_path=figure_path,
        pair_count_proof_path=proof_path,
        universe_scores_path=score_path,
        rebalance_log_path=rebalance_path,
        decision_trace_path=trace_path,
        health_summary_path=health_path,
        alerts_path=alerts_path,
        scored_count=int(score_frame.groupby("decision_bar_start")["symbol"].nunique().max()),
        selected_count=int(score_frame.groupby("decision_bar_start")["selected_top_k"].sum().max()),
        symbols=symbols,
    )


def build_level_5_target_schedule(
    *,
    frame: pd.DataFrame,
    instruments: pd.DataFrame,
    config: dict[str, Any],
    decision_start: pd.Timestamp,
    decision_end: pd.Timestamp,
    split: str = "validation",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[DecisionTrace]]:
    """Build dynamic large-universe targets from point-in-time scores."""

    normalized = _normalize_market_frame(frame, end=decision_end + pd.Timedelta(days=1))
    rules = _universe_rules(config)
    scoring_config = _scoring_config(config)
    policy = _rebalance_policy(config)
    allocator = _allocator(config)
    minimum_full_scored = int(_level5_config(config)["min_scored_pairs_full"])
    mode = str(config.get("project", {}).get("mode", "full"))
    decision_bars = pd.date_range(decision_start, decision_end, freq="D", tz="UTC")

    all_symbols: set[str] = set()
    last_approved = pd.Series(dtype="float64")
    last_execution_time: pd.Timestamp | None = None
    previous_rebalance_time: pd.Timestamp | None = None
    previous_scores: pd.Series | None = None
    rows: list[pd.Series] = []
    score_frames: list[pd.DataFrame] = []
    log_rows: list[dict[str, object]] = []
    traces: list[DecisionTrace] = []

    for decision_bar in decision_bars:
        clock = build_daily_research_clock(decision_bar.to_pydatetime())
        feature_cutoff = pd.Timestamp(clock.feature_cutoff)
        eligibility = eligible_universe_at(
            normalized,
            instruments,
            decision_cutoff_utc=feature_cutoff,
            rules=rules,
        )
        universe = selected_large_universe(eligibility, rules=rules)
        if mode == "full" and len(universe) < minimum_full_scored:
            msg = (
                f"Level 5 full mode scored {len(universe)} pairs at "
                f"{feature_cutoff.isoformat()}, below required {minimum_full_scored}"
            )
            raise ValueError(msg)

        score_frame = build_level5_score_frame(
            normalized,
            universe,
            decision_bar=decision_bar,
            feature_cutoff=feature_cutoff,
            config=scoring_config,
        )
        score_frame = _mark_top_k_and_capacity(score_frame, normalized, decision_bar, config)
        symbols = tuple(score_frame["symbol"].astype(str).tolist())
        all_symbols.update(symbols)
        current_weights = _current_weights(
            normalized,
            symbols=symbols,
            previous_target=last_approved,
            previous_execution_time=last_execution_time,
            decision_bar=decision_bar,
        )
        score_series = _allocation_scores(score_frame, config)
        returns = _historical_open_returns(
            normalized,
            symbols=symbols,
            start=decision_bar
            - pd.Timedelta(days=int(_level5_config(config)["scoring_lookback_days"])),
            through=decision_bar,
        )
        signals, aggregated = _signals_from_scores(score_frame, clock)
        score_change = (
            1.0
            if previous_scores is None
            else float((score_series - previous_scores.reindex(symbols).fillna(0.0)).abs().max())
        )
        realized_volatility = _realized_volatility(returns, config)
        risk_trigger_active = realized_volatility >= float(
            _level5_config(config)["risk_rebalance_volatility_threshold_annual"]
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
                "realized_volatility": realized_volatility if risk_trigger_active else 0.0,
                "kill_switch": bool(_level5_config(config).get("kill_switch", False)),
            },
            metadata={
                "level": LEVEL_NAME,
                "split": split,
                "previous_rebalance_time": previous_rebalance_time,
                "eligible_count": len(universe),
                "scored_count": int(score_frame["scored"].sum()),
            },
        )
        snapshot = _snapshot_with_capacity(normalized, symbols, decision_bar, config)
        constraints = _pre_risk(config).constraints(list(aggregated), context, snapshot)
        proposal = allocator.allocate(score_series, returns, constraints, current_weights)
        proposal = _proposal_with_metadata(
            proposal,
            score_series=score_series,
            risk_trigger_active=risk_trigger_active,
            realized_volatility=realized_volatility,
            score_frame=score_frame,
            config=config,
        )
        rebalance = policy.decide(proposal, current_weights, context)
        approval = _post_risk(config).approve(proposal, rebalance, constraints, context, returns)
        executable = resolve_risk_approval_targets(approval, context)
        approved = pd.Series(
            {symbol: float(executable.risky_weights.get(symbol, 0.0)) for symbol in all_symbols},
            dtype="float64",
        )
        should_submit = executable.action in {"approve", "cap", "cash"} and (
            rebalance.should_rebalance or executable.action == "cash"
        )
        if should_submit:
            rows.append(approved.rename(decision_bar))
            last_approved = approved
            last_execution_time = pd.Timestamp(clock.execution_time)
            previous_rebalance_time = pd.Timestamp(clock.decision_time)
        score_frame["blocked_by_pre_risk"] = score_frame["symbol"].isin(constraints.blocked_symbols)
        score_frame["per_asset_cap"] = score_frame["symbol"].map(constraints.per_asset_caps)
        score_frame["approved_weight"] = score_frame["symbol"].map(approved).fillna(0.0)
        score_frames.append(score_frame)
        log_rows.append(
            _rebalance_log_row(
                decision_bar=decision_bar,
                execution_time=pd.Timestamp(clock.execution_time),
                score_frame=score_frame,
                current_weights=current_weights,
                proposal=proposal,
                rebalance=rebalance,
                approval=approval,
                approved=approved,
                submitted=should_submit,
                score_change=score_change,
                realized_volatility=realized_volatility,
                risk_trigger_active=risk_trigger_active,
                eligibility=eligibility,
            )
        )
        traces.append(
            DecisionTrace(
                clock=clock,
                signals=signals,
                aggregated_signals=aggregated,
                constraints=constraints,
                proposal=proposal,
                approval=approval,
                metadata={
                    "level": LEVEL_NAME,
                    "split": "validation",
                    "execution_time": pd.Timestamp(clock.execution_time).isoformat(),
                    "rebalance_decision": {
                        "should_rebalance": rebalance.should_rebalance,
                        "trigger_codes": list(rebalance.trigger_codes),
                        "reason_codes": [code.value for code in rebalance.reason_codes],
                    },
                    "resolved_action": executable.action,
                },
            )
        )
        previous_scores = score_series.copy()

    if not rows:
        msg = "Level 5 produced no executable schedule"
        raise ValueError(msg)
    schedule = pd.DataFrame(rows).sort_index(kind="mergesort").fillna(0.0)
    schedule.index = pd.DatetimeIndex(schedule.index, tz="UTC")
    return schedule, pd.concat(score_frames, ignore_index=True), pd.DataFrame(log_rows), traces


def _level5_config(config: dict[str, Any]) -> dict[str, Any]:
    if "level_5" not in config:
        msg = "config is missing level_5"
        raise ValueError(msg)
    return dict(config["level_5"])


def _universe_rules(config: dict[str, Any]) -> UniverseRules:
    base = UniverseRules.from_config(config)
    level_config = _level5_config(config)
    return replace(
        base,
        min_history_days=int(level_config.get("universe_min_history_days", base.min_history_days)),
        preferred_history_days=int(
            level_config.get("universe_preferred_history_days", base.preferred_history_days)
        ),
        min_trailing_valid_days=int(
            level_config.get("universe_min_trailing_valid_days", base.min_trailing_valid_days or 1)
        ),
        min_median_dollar_volume=float(level_config.get("min_dollar_volume", 0.0)),
    )


def _scoring_config(config: dict[str, Any]) -> Level5ScoringConfig:
    item = _level5_config(config)
    return Level5ScoringConfig(
        scoring_lookback_days=int(item["scoring_lookback_days"]),
        momentum_short_days=int(item["momentum_short_days"]),
        momentum_long_days=int(item["momentum_long_days"]),
        volatility_days=int(item["volatility_days"]),
        drawdown_days=int(item["drawdown_days"]),
        horizon_open_days=int(item["horizon_open_days"]),
    )


def _allocator(config: dict[str, Any]) -> InverseVolatilityAllocator:
    name = str(_level5_config(config).get("allocator", "inverse_volatility"))
    if name != "inverse_volatility":
        msg = f"unsupported Level 5 allocator: {name}"
        raise ValueError(msg)
    return InverseVolatilityAllocator(min_periods=20)


def _rebalance_policy(config: dict[str, Any]) -> DynamicRebalancePolicy:
    level_config = _level5_config(config)
    cost_rate = (
        float(config["backtest"]["fee_bps_one_way"])
        + float(config["backtest"]["slippage_bps_one_way"])
    ) / 10_000.0
    return DynamicRebalancePolicy(
        name="level5_large_universe_dynamic",
        calendar=str(level_config["rebalance_calendar"]),
        drift_threshold_abs=float(config["rebalance"]["drift_threshold_abs"]),
        score_change_threshold=float(level_config["score_change_threshold"]),
        risk_trigger=True,
        min_trade_abs=float(level_config["min_trade_abs"]),
        turnover_cap=float(level_config["turnover_cap"]),
        one_way_cost_rate=cost_rate,
    )


def _pre_risk(config: dict[str, Any]) -> PreAllocationRiskPolicy:
    level_config = _level5_config(config)
    return PreAllocationRiskPolicy(
        max_gross_exposure=float(config["portfolio"]["max_gross_exposure"]),
        max_per_asset_weight=float(level_config["max_weight"]),
        cost_buffer_weight=float(level_config["cost_buffer_weight"]),
        min_dollar_volume=float(level_config["min_dollar_volume"]),
        max_stale_data_days=0,
        max_model_age_days=1,
        max_agent_disagreement=float(config["risk"]["max_agent_disagreement"]),
        volatility_target=None,
        turnover_cap=float(level_config["turnover_cap"]),
    )


def _post_risk(config: dict[str, Any]) -> PostAllocationRiskPolicy:
    return PostAllocationRiskPolicy(
        max_drawdown_stop=float(config["risk"]["max_drawdown_stop"]),
        high_volatility_threshold=float(config["risk"]["high_volatility_threshold_annual"]),
        min_cash_buffer=float(_level5_config(config)["min_cash_buffer"]),
        annualization_periods=int(config["backtest"]["annualization_periods"]),
    )


def _mark_top_k_and_capacity(
    score_frame: pd.DataFrame,
    frame: pd.DataFrame,
    decision_bar: pd.Timestamp,
    config: dict[str, Any],
) -> pd.DataFrame:
    output = score_frame.copy()
    top_k = int(_level5_config(config).get("top_k", config["portfolio"]["large_top_k"]))
    ordered = output.sort_values(["score", "confidence", "symbol"], ascending=[False, False, True])
    selected = set(ordered.head(top_k)["symbol"].astype(str))
    output["selected_top_k"] = output["symbol"].astype(str).isin(selected)
    capacity = _capacity_weights(frame, tuple(output["symbol"].astype(str)), decision_bar, config)
    output["max_weight_by_liquidity"] = output["symbol"].map(capacity).fillna(0.0)
    output["configured_max_weight"] = float(_level5_config(config)["max_weight"])
    output["capacity_notional_usd"] = output["max_weight_by_liquidity"] * float(
        config["liquidity"]["assumed_aum_usd"]
    )
    return output


def _allocation_scores(score_frame: pd.DataFrame, config: dict[str, Any]) -> pd.Series:
    scores = score_frame.set_index("symbol")["score"].astype("float64")
    scores.loc[~score_frame.set_index("symbol")["selected_top_k"]] = 0.0
    return scores * score_frame.set_index("symbol")["confidence"].astype("float64")


def _signals_from_scores(
    score_frame: pd.DataFrame,
    clock: Any,
) -> tuple[tuple[AgentSignal, ...], tuple[AggregatedSignal, ...]]:
    signals: list[AgentSignal] = []
    aggregated: list[AggregatedSignal] = []
    for row in score_frame.itertuples(index=False):
        reason = ReasonCode(str(row.reason_codes))
        signal = AgentSignal(
            symbol=str(row.symbol),
            agent="level5_cross_sectional_ranker",
            score=float(row.score),
            confidence=float(row.confidence),
            horizon_open_days=int(row.horizon_open_days),
            fit_cutoff=clock.feature_cutoff,
            feature_cutoff=clock.feature_cutoff,
            reason_codes=(reason,),
            metadata={
                "selected_top_k": bool(row.selected_top_k),
                "data_quality_flag": str(row.data_quality_flag),
                "trailing_median_dollar_volume": float(row.trailing_median_dollar_volume),
            },
        )
        signals.append(signal)
        aggregated.append(
            AggregatedSignal(
                symbol=str(row.symbol),
                score=float(row.score),
                confidence=float(row.confidence),
                contributions={"level5_cross_sectional_ranker": float(row.score)},
                disagreement=0.0,
                reason_codes=(reason,),
            )
        )
    return tuple(signals), tuple(aggregated)


def _snapshot_with_capacity(
    frame: pd.DataFrame,
    symbols: tuple[str, ...],
    decision_bar: pd.Timestamp,
    config: dict[str, Any],
) -> pd.DataFrame:
    snapshot = frame.loc[
        (frame["bar_start_utc"] == decision_bar) & (frame["symbol"].isin(symbols))
    ].copy()
    snapshot["feature_cutoff"] = snapshot["bar_end_utc"]
    capacity = _capacity_weights(frame, symbols, decision_bar, config)
    snapshot["max_weight_by_liquidity"] = snapshot["symbol"].map(capacity).fillna(0.0)
    return snapshot


def _capacity_weights(
    frame: pd.DataFrame,
    symbols: tuple[str, ...],
    decision_bar: pd.Timestamp,
    config: dict[str, Any],
) -> pd.Series:
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
    return (adv * max_participation / aum).clip(lower=0.0)


def _current_weights(
    frame: pd.DataFrame,
    *,
    symbols: tuple[str, ...],
    previous_target: pd.Series,
    previous_execution_time: pd.Timestamp | None,
    decision_bar: pd.Timestamp,
) -> pd.Series:
    if previous_target.empty or float(previous_target.sum()) <= 0:
        return pd.Series(dict.fromkeys(symbols, 0.0), dtype="float64")
    held = tuple(str(symbol) for symbol, weight in previous_target.items() if float(weight) > 1e-12)
    if not held:
        return pd.Series(dict.fromkeys(symbols, 0.0), dtype="float64")
    drifted = _drifted_current_weights(
        frame,
        symbols=held,
        previous_target=previous_target.reindex(held, fill_value=0.0),
        previous_execution_time=previous_execution_time,
        decision_bar=decision_bar,
    )
    return drifted.reindex(symbols, fill_value=0.0).astype("float64")


def _proposal_with_metadata(
    proposal: PortfolioProposal,
    *,
    score_series: pd.Series,
    risk_trigger_active: bool,
    realized_volatility: float,
    score_frame: pd.DataFrame,
    config: dict[str, Any],
) -> PortfolioProposal:
    weights = pd.Series(proposal.target_weights, dtype="float64")
    expected_score = float((weights * score_series.reindex(weights.index).fillna(0.0)).sum())
    cap = float(_level5_config(config)["max_weight"])
    capacity_breaches = [
        str(symbol)
        for symbol, weight in weights.items()
        if weight > cap + 1e-12
        or weight
        > float(score_frame.set_index("symbol")["max_weight_by_liquidity"].get(symbol, 0.0)) + 1e-12
    ]
    metadata = {
        **dict(proposal.metadata),
        "expected_gross_benefit": max(0.0, expected_score)
        * float(_level5_config(config)["expected_benefit_scale"]),
        "weighted_signal_score": expected_score,
        "risk_trigger_active": risk_trigger_active,
        "realized_volatility": realized_volatility,
        "capacity_breach_symbols": capacity_breaches,
        "capacity_breach": bool(capacity_breaches),
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


def _rebalance_log_row(
    *,
    decision_bar: pd.Timestamp,
    execution_time: pd.Timestamp,
    score_frame: pd.DataFrame,
    current_weights: pd.Series,
    proposal: PortfolioProposal,
    rebalance: Any,
    approval: Any,
    approved: pd.Series,
    submitted: bool,
    score_change: float,
    realized_volatility: float,
    risk_trigger_active: bool,
    eligibility: pd.DataFrame,
) -> dict[str, object]:
    exclusion_counts = (
        eligibility.loc[~eligibility["eligible"], "reason"].value_counts().sort_index().to_dict()
    )
    return {
        "policy": "level5_large_universe_dynamic",
        "decision_bar_start": decision_bar,
        "execution_time": execution_time,
        "eligible_count": len(score_frame),
        "scored_count": int(score_frame["scored"].sum()),
        "selected_count": int(score_frame["selected_top_k"].sum()),
        "approved_nonzero_count": int((approved > 1e-12).sum()),
        "should_rebalance": bool(rebalance.should_rebalance),
        "submitted_to_broker": bool(submitted),
        "trigger_codes": json.dumps(list(rebalance.trigger_codes), sort_keys=True),
        "skipped_reason": "" if submitted else _skipped_reason(rebalance),
        "before_weight_sum": float(current_weights.sum()),
        "candidate_weight_sum": float(sum(proposal.target_weights.values())),
        "approved_weight_sum": float(approved.sum()),
        "approved_cash_weight": float(1.0 - approved.sum()),
        "max_approved_weight": float(approved.max()) if not approved.empty else 0.0,
        "expected_turnover": float(proposal.expected_turnover),
        "score_change": score_change,
        "realized_volatility": realized_volatility,
        "risk_trigger_active": risk_trigger_active,
        "approval_action": str(approval.action),
        "reason_codes": json.dumps([code.value for code in approval.reason_codes], sort_keys=True),
        "total_instrument_count": len(eligibility),
        "excluded_count": int((~eligibility["eligible"]).sum()),
        "exclusion_counts": json.dumps(exclusion_counts, sort_keys=True),
    }


def _skipped_reason(rebalance: Any) -> str:
    if ReasonCode.TURNOVER_LIMIT in rebalance.reason_codes:
        return "turnover_or_cost_control"
    if "minimum_trade_not_met" in rebalance.trigger_codes:
        return "minimum_trade_not_met"
    if "no_trigger" in rebalance.trigger_codes:
        return "no_rebalance_trigger"
    return "held_prior_weights"


def _realized_volatility(returns: pd.DataFrame, config: dict[str, Any]) -> float:
    if returns.empty:
        return 0.0
    recent = returns.tail(20).dropna(how="all")
    if recent.empty:
        return 0.0
    equal = recent.mean(axis=1)
    value = float(equal.std(ddof=0) * math.sqrt(int(config["backtest"]["annualization_periods"])))
    return value if math.isfinite(value) else 0.0


def _benchmark_nav(
    frame: pd.DataFrame,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    config: dict[str, Any],
) -> pd.Series:
    initial_capital = float(config["backtest"]["initial_capital_usd"])
    symbol = str(config["level_1"]["symbol"]) if "level_1" in config else "BTC/USDT"
    rows = frame.loc[
        (frame["symbol"] == symbol)
        & (frame["bar_start_utc"] >= start)
        & (frame["bar_start_utc"] <= end),
        ["bar_start_utc", "open"],
    ].sort_values("bar_start_utc", kind="mergesort")
    if rows.empty:
        first_symbol = str(frame["symbol"].iloc[0])
        rows = frame.loc[
            (frame["symbol"] == first_symbol)
            & (frame["bar_start_utc"] >= start)
            & (frame["bar_start_utc"] <= end),
            ["bar_start_utc", "open"],
        ].sort_values("bar_start_utc", kind="mergesort")
    nav = rows.set_index("bar_start_utc")["open"].astype("float64")
    return nav / float(nav.iloc[0]) * initial_capital


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
    equity["benchmark_nav"] = benchmark_nav.reindex(equity.index).ffill().bfill().to_numpy()
    equity = equity.reset_index(drop=True)
    return BacktestRunResult(
        equity=equity,
        weights=net_result.weights,
        orders=net_result.orders,
        fills=net_result.fills,
    )


def _metrics(
    net_result: BacktestRunResult,
    gross_result: BacktestRunResult,
    *,
    benchmark_nav: pd.Series,
    score_frame: pd.DataFrame,
    rebalance_log: pd.DataFrame,
    config: dict[str, Any],
    split: str = "validation",
) -> dict[str, Any]:
    initial_capital = float(config["backtest"]["initial_capital_usd"])
    net_equity = _with_initial_capital_baseline(net_result.equity, initial_capital)
    gross_equity = _with_initial_capital_baseline(gross_result.equity, initial_capital)
    baseline_time = pd.to_datetime(net_equity["timestamp"], utc=True).iloc[0]
    benchmark = pd.concat(
        [pd.Series([initial_capital], index=[baseline_time]), benchmark_nav]
    ).sort_index()
    net = calculate_performance_metrics(
        net_equity,
        periods_per_year=int(config["backtest"]["annualization_periods"]),
        risk_free_rate=float(config["backtest"]["risk_free_rate"]),
        weights=net_result.weights,
        benchmark_nav=benchmark,
    )
    gross = calculate_performance_metrics(
        gross_equity,
        periods_per_year=int(config["backtest"]["annualization_periods"]),
        risk_free_rate=float(config["backtest"]["risk_free_rate"]),
        weights=gross_result.weights,
        benchmark_nav=benchmark,
    )
    metrics: dict[str, Any] = dict(net)
    metrics.update({f"net_{key}": value for key, value in net.items()})
    metrics.update({f"gross_{key}": value for key, value in gross.items()})
    metrics["gross_to_net_total_return_decay"] = gross["total_return"] - net["total_return"]
    metrics["eligible_count_max"] = float(score_frame.groupby("decision_bar_start").size().max())
    metrics["scored_count_max"] = float(
        score_frame.groupby("decision_bar_start")["scored"].sum().max()
    )
    metrics["selected_count_max"] = float(
        score_frame.groupby("decision_bar_start")["selected_top_k"].sum().max()
    )
    metrics["approved_nonzero_count_max"] = float(rebalance_log["approved_nonzero_count"].max())
    metrics["rebalance_decision_count"] = float(len(rebalance_log))
    metrics["rebalance_submitted_count"] = float(rebalance_log["submitted_to_broker"].sum())
    metrics["final_test_exposure_flag"] = float(split == "final_test")
    return metrics


def _provenance(
    *,
    config: dict[str, Any],
    validation_start: pd.Timestamp,
    validation_end: pd.Timestamp,
    decision_start: pd.Timestamp,
    decision_end: pd.Timestamp,
    cost_assumptions: CostAssumptions,
    scored_count: int,
    selected_count: int,
    split: str = "validation",
    final_test_lock_hash: str | None = None,
) -> ArtifactProvenance:
    data_path = Path(config["paths"]["market_data"])
    return ArtifactProvenance(
        level=LEVEL_NAME,
        run_label=RUN_LABEL if split == "validation" else "level_5_final_test_large_universe",
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
        benchmark="price_normalized_btc_open_to_open",
        seed=int(config["project"]["seed"]),
        final_test_lock_hash=final_test_lock_hash,
        git_worktree_dirty=git_worktree_dirty(),
        git_diff_sha256=git_diff_sha256(),
        warnings=(
            "validation_only_no_final_test_metrics"
            if split == "validation"
            else "final_test_exposure_EXPOSED_frozen_lock",
            "survivorship_bias_active_markets",
            "level5_uses_late_2024_validation_window_for_100_pair_feasibility"
            if split == "validation"
            else "level5_full_2025_final_test_100_pair_scoring",
            "universe_min_history_days_240_for_new_listings",
            "daily_bars_adv_proxy_capacity_no_order_book_depth",
            f"decision_start={decision_start.date().isoformat()}",
            f"decision_end={decision_end.date().isoformat()}",
            f"scored_count={scored_count}",
            f"selected_count={selected_count}",
        ),
    )


def _write_equity_figure(
    result: BacktestRunResult,
    output_dir: Path,
    provenance: ArtifactProvenance,
) -> Path:
    path = output_dir / "figures" / "level_5_equity_curve.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    equity = result.equity.copy()
    equity["timestamp"] = pd.to_datetime(equity["timestamp"], utc=True)
    plt.figure(figsize=(10, 5))
    base = float(equity["nav"].iloc[0])
    plt.plot(equity["timestamp"], equity["nav"] / base, label="Level 5 net NAV")
    plt.plot(equity["timestamp"], equity["gross_nav"] / base, label="Level 5 gross NAV")
    plt.plot(equity["timestamp"], equity["benchmark_nav"] / base, linestyle="--", label="BTC")
    plt.title("Level 5 validation equity: 100-pair dynamic universe")
    plt.xlabel("Validation date")
    plt.ylabel("Normalized NAV")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    _write_metadata_sidecar(path, provenance)
    return path


def _write_scores(
    score_frame: pd.DataFrame, output_dir: Path, provenance: ArtifactProvenance
) -> Path:
    path = output_dir / "monitoring" / "level_5_universe_scores.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    output = score_frame.copy()
    for key, value in BacktestArtifactWriter._provenance_columns(provenance).items():
        output[key] = value
    output.to_parquet(path, index=False)
    _write_metadata_sidecar(path, provenance)
    return path


def _write_rebalance_log(
    rebalance_log: pd.DataFrame,
    output_dir: Path,
    provenance: ArtifactProvenance,
) -> Path:
    path = output_dir / "monitoring" / "level_5_rebalance_log.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    output = rebalance_log.copy()
    for key, value in BacktestArtifactWriter._provenance_columns(provenance).items():
        output[key] = value
    output.to_parquet(path, index=False)
    _write_metadata_sidecar(path, provenance)
    return path


def _write_health_artifacts(
    score_frame: pd.DataFrame,
    rebalance_log: pd.DataFrame,
    output_dir: Path,
    provenance: ArtifactProvenance,
    *,
    runtime_seconds: float,
    peak_rss_mb: float,
    config: dict[str, Any],
) -> tuple[Path, Path]:
    summary_path = output_dir / "monitoring" / "health_summary.csv"
    alerts_path = output_dir / "monitoring" / "alerts.parquet"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    invalid_count = int((score_frame["reason_codes"] != ReasonCode.OK.value).sum())
    summary = pd.DataFrame(
        [
            {
                "level": LEVEL_NAME,
                "split": provenance.split,
                "mode": str(config["project"]["mode"]),
                "system_status": "warning" if invalid_count else "ok",
                "eligible_count_min": int(score_frame.groupby("decision_bar_start").size().min()),
                "eligible_count_max": int(score_frame.groupby("decision_bar_start").size().max()),
                "scored_count_min": int(
                    score_frame.groupby("decision_bar_start")["scored"].sum().min()
                ),
                "scored_count_max": int(
                    score_frame.groupby("decision_bar_start")["scored"].sum().max()
                ),
                "selected_count_max": int(
                    score_frame.groupby("decision_bar_start")["selected_top_k"].sum().max()
                ),
                "submitted_rebalances": int(rebalance_log["submitted_to_broker"].sum()),
                "data_quality_invalid_count": invalid_count,
                "model_quality_invalid_count": invalid_count,
                "runtime_seconds": runtime_seconds,
                "peak_rss_mb": peak_rss_mb,
                "peak_rss_unit": "MiB",
                "final_test_exposure": "NOT_EXPOSED"
                if provenance.split == "validation"
                else "EXPOSED",
                "coverage_rate_min": float(
                    score_frame.groupby("decision_bar_start")["trailing_valid_days"].min().min()
                    / max(1, int(_level5_config(config)["scoring_lookback_days"]))
                ),
                "feature_drift_abs_mean": float(
                    score_frame.groupby("decision_bar_start")["score"].mean().diff().abs().mean()
                    or 0.0
                ),
                "prediction_drift_abs_mean": float(
                    score_frame.groupby("decision_bar_start")["confidence"]
                    .mean()
                    .diff()
                    .abs()
                    .mean()
                    or 0.0
                ),
                "calibration_decay_proxy": float(
                    score_frame.groupby("decision_bar_start")["confidence"].std(ddof=0).mean()
                    or 0.0
                ),
                "agent_disagreement_rate": 0.0,
                "abstention_rate": float(invalid_count / max(1, len(score_frame))),
                "optimizer_fallback_rate": float(
                    (rebalance_log["approval_action"] != "approve").mean()
                ),
                "cost_decay_proxy": float(
                    rebalance_log["expected_turnover"].mean()
                    * (
                        float(config["backtest"]["fee_bps_one_way"])
                        + float(config["backtest"]["slippage_bps_one_way"])
                    )
                    / 10_000.0
                ),
                "incident_count": int((rebalance_log["approval_action"] != "approve").sum()),
                "fail_safe_scenarios_demonstrated": json.dumps(
                    [
                        "kill_switch_cash_schedule_unit_test",
                        "volatility_limit_cash_approval",
                        "invalid_feature_alert_path",
                        "weight_reconciliation_post_risk",
                    ],
                    sort_keys=True,
                ),
                "kill_switch_unit_test_evidence": (
                    "tests/unit/test_level5_validation.py::"
                    "test_level5_kill_switch_scores_but_moves_schedule_to_cash"
                ),
            }
        ]
    )
    for key, value in BacktestArtifactWriter._provenance_columns(provenance).items():
        summary[key] = value
    summary.to_csv(summary_path, index=False)
    alerts = pd.DataFrame(
        [
            {
                "timestamp": provenance.created_at_utc,
                "component": "level5_data",
                "severity": "warning",
                "reason_codes": ReasonCode.INVALID_DATA.value,
                "message": "Some eligible symbols had invalid scoring features."
                if invalid_count
                else "No invalid scoring features detected.",
                "count": invalid_count,
            },
            {
                "timestamp": provenance.created_at_utc,
                "component": "level5_methodology",
                "severity": "warning",
                "reason_codes": ReasonCode.OK.value,
                "message": "Validation-only late-2024 100-pair feasibility window; no final test."
                if provenance.split == "validation"
                else "Frozen final-test suite exposed once from accepted lock.",
                "count": 1,
            },
            {
                "timestamp": provenance.created_at_utc,
                "component": "level5_long_term_quality",
                "severity": "info",
                "reason_codes": ReasonCode.OK.value,
                "message": (
                    "Tracks score drift, confidence drift, calibration proxy, "
                    "fallback rate, cost decay proxy and incidents."
                ),
                "count": int((rebalance_log["approval_action"] != "approve").sum()),
            },
            {
                "timestamp": provenance.created_at_utc,
                "component": "level5_fail_safe",
                "severity": "info",
                "reason_codes": ReasonCode.DRAWDOWN_STOP.value,
                "message": (
                    "Fail-safe evidence includes kill-switch unit test and validation "
                    "risk approvals that moved to cash."
                ),
                "count": int((rebalance_log["approval_action"] == "cash").sum()),
            },
        ]
    )
    for key, value in BacktestArtifactWriter._provenance_columns(provenance).items():
        alerts[key] = value
    alerts.to_parquet(alerts_path, index=False)
    _write_metadata_sidecar(summary_path, provenance)
    _write_metadata_sidecar(alerts_path, provenance)
    return summary_path, alerts_path


def _write_pair_count_proof(
    score_frame: pd.DataFrame,
    rebalance_log: pd.DataFrame,
    output_dir: Path,
    provenance: ArtifactProvenance,
    *,
    runtime_seconds: float,
    peak_rss_mb: float,
    config: dict[str, Any],
) -> Path:
    path = output_dir / "monitoring" / "level_5_pair_count_proof.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    grouped = score_frame.groupby("decision_bar_start")
    proof_date = grouped["symbol"].nunique().idxmax()
    proof_scores = score_frame.loc[score_frame["decision_bar_start"] == proof_date].copy()
    rules = _universe_rules(config)
    payload = {
        "provenance": provenance.metadata(),
        "mode": str(config["project"]["mode"]),
        "split": provenance.split,
        "final_test_exposure": "NOT_EXPOSED" if provenance.split == "validation" else "EXPOSED",
        "validation_decision_date": pd.Timestamp(proof_date).isoformat()
        if provenance.split == "validation"
        else None,
        "final_test_decision_date": pd.Timestamp(proof_date).isoformat()
        if provenance.split == "final_test"
        else None,
        "decision_dates": [pd.Timestamp(item).isoformat() for item in grouped.size().index],
        "required_min_pairs": int(_level5_config(config)["min_scored_pairs_full"]),
        "eligible_count": len(proof_scores),
        "scored_count": int(proof_scores["scored"].sum()),
        "selected_count": int(proof_scores["selected_top_k"].sum()),
        "approved_nonzero_count_max": int(rebalance_log["approved_nonzero_count"].max()),
        "symbols": proof_scores["symbol"].astype(str).tolist(),
        "selected_symbols": proof_scores.loc[proof_scores["selected_top_k"], "symbol"]
        .astype(str)
        .tolist(),
        "exclusion_reason_counts": proof_scores["reason_codes"].value_counts().to_dict(),
        "eligibility_rules": {
            "quote_currency": rules.quote_currency,
            "min_history_days": rules.min_history_days,
            "preferred_history_days": rules.preferred_history_days,
            "liquidity_lookback_days": rules.liquidity_lookback_days,
            "min_trailing_valid_days": rules.min_trailing_valid_days,
            "large_universe_size": rules.large_universe_size,
        },
        "coverage_stats": {
            "valid_history_days_min": int(proof_scores["valid_history_days"].min()),
            "valid_history_days_median": float(proof_scores["valid_history_days"].median()),
            "trailing_valid_days_min": int(proof_scores["trailing_valid_days"].min()),
        },
        "liquidity_stats": {
            "trailing_median_dollar_volume_min": float(
                proof_scores["trailing_median_dollar_volume"].min()
            ),
            "trailing_median_dollar_volume_median": float(
                proof_scores["trailing_median_dollar_volume"].median()
            ),
            "max_weight_by_liquidity_min": float(proof_scores["max_weight_by_liquidity"].min()),
        },
        "runtime_seconds": runtime_seconds,
        "peak_rss_mb": peak_rss_mb,
        "peak_rss_unit": "MiB",
        "scores_artifact": "artifacts/monitoring/level_5_universe_scores.parquet",
        "rebalance_log_artifact": "artifacts/monitoring/level_5_rebalance_log.parquet",
        "filters": {
            "point_in_time_cutoff": "feature_cutoff",
            "rank_metric": "trailing_90_day_median_dollar_volume",
            "quote_currency": rules.quote_currency,
            "excluded_statuses": [
                "wrong_quote_currency",
                "non_spot",
                "inactive",
                "stable_or_fiat_base",
                "leveraged_token_suffix",
                "insufficient_history",
                "insufficient_trailing_liquidity_window",
                "low_liquidity",
                "no_completed_bars_by_cutoff",
            ],
        },
        "full_universe_exclusion_reason_counts": json.loads(
            str(
                rebalance_log.loc[
                    rebalance_log["decision_bar_start"] == proof_date, "exclusion_counts"
                ].iloc[0]
            )
        ),
        "full_universe_excluded_count": int(
            rebalance_log.loc[
                rebalance_log["decision_bar_start"] == proof_date, "excluded_count"
            ].iloc[0]
        ),
    }
    return _write_json_artifact(path, payload, provenance)


def _write_decision_trace(
    *,
    traces: list[DecisionTrace],
    score_frame: pd.DataFrame,
    rebalance_log: pd.DataFrame,
    output_dir: Path,
    provenance: ArtifactProvenance,
    config: dict[str, Any],
) -> Path:
    path = output_dir / "monitoring" / "level_5_decision_trace.json"
    representative = traces[0]
    selected_scores = score_frame.loc[
        score_frame["decision_bar_start"] == score_frame["decision_bar_start"].min()
    ].copy()
    payload = {
        "provenance": provenance.metadata(),
        "final_test_exposure": "NOT_EXPOSED" if provenance.split == "validation" else "EXPOSED",
        "portfolio_protocol": {
            "validation_only": provenance.split == "validation",
            "point_in_time_universe": True,
            "completed_bar_next_open_execution": True,
            "allocator": str(_level5_config(config)["allocator"]),
            "top_k": int(_level5_config(config)["top_k"]),
            "max_weight": float(_level5_config(config)["max_weight"]),
            "capacity": {
                "assumed_aum_usd": float(config["liquidity"]["assumed_aum_usd"]),
                "adv_lookback_days": int(config["liquidity"]["adv_lookback_days"]),
                "max_participation": float(config["liquidity"]["max_participation"]),
            },
        },
        "rebalance_summary": rebalance_log.to_dict(orient="records"),
        "representative_scores": selected_scores.head(30).to_dict(orient="records"),
        "representative_decision": {
            "bar_start": representative.clock.bar_start.isoformat(),
            "feature_cutoff": representative.clock.feature_cutoff.isoformat(),
            "decision_time": representative.clock.decision_time.isoformat(),
            "execution_time": representative.clock.execution_time.isoformat(),
            "signal_count": len(representative.signals),
            "aggregated_signal_count": len(representative.aggregated_signals),
            "blocked_count": 0
            if representative.constraints is None
            else len(representative.constraints.blocked_symbols),
            "proposal_status": None
            if representative.proposal is None
            else representative.proposal.optimizer_status,
            "approval_action": None
            if representative.approval is None
            else representative.approval.action,
            "approval_reason_codes": []
            if representative.approval is None
            else [code.value for code in representative.approval.reason_codes],
        },
    }
    return _write_json_artifact(path, payload, provenance)


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
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _peak_rss_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return float(usage / (1024.0 * 1024.0))
    return float(usage / 1024.0)
