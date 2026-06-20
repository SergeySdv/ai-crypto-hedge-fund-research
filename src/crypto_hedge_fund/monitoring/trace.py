"""Notebook-ready decision trace and monitoring event helpers."""

from __future__ import annotations

import pandas as pd

from crypto_hedge_fund.types import (
    DecisionTrace,
    MonitoringEvent,
    PortfolioProposal,
    RiskApproval,
    RiskConstraints,
)


def events_to_frame(events: tuple[MonitoringEvent, ...] | list[MonitoringEvent]) -> pd.DataFrame:
    """Convert monitoring events to a tabular artifact surface."""
    rows = [
        {
            "timestamp": event.timestamp,
            "component": event.component,
            "severity": event.severity,
            "reason_codes": ",".join(code.value for code in event.reason_codes),
            "message": event.message,
            **{f"metadata_{key}": value for key, value in event.metadata.items()},
        }
        for event in events
    ]
    return pd.DataFrame(rows)


def merge_decision_trace(
    trace: DecisionTrace,
    *,
    constraints: RiskConstraints | None = None,
    proposal: PortfolioProposal | None = None,
    approval: RiskApproval | None = None,
    events: tuple[MonitoringEvent, ...] = (),
) -> DecisionTrace:
    """Return a new immutable trace with later risk/allocation decisions attached."""
    return DecisionTrace(
        clock=trace.clock,
        signals=trace.signals,
        aggregated_signals=trace.aggregated_signals,
        constraints=constraints if constraints is not None else trace.constraints,
        proposal=proposal if proposal is not None else trace.proposal,
        approval=approval if approval is not None else trace.approval,
        events=(*trace.events, *events),
        metadata=trace.metadata,
    )


def trace_to_frame(trace: DecisionTrace) -> pd.DataFrame:
    """Flatten one decision trace into per-symbol rows for notebooks/reports."""
    aggregate_by_symbol = {signal.symbol: signal for signal in trace.aggregated_signals}
    symbols = sorted(
        set(aggregate_by_symbol)
        | set(trace.constraints.per_asset_caps if trace.constraints else ())
        | set(trace.proposal.target_weights if trace.proposal else ())
        | set(trace.approval.approved_weights if trace.approval else ())
    )
    rows: list[dict[str, object]] = []
    for symbol in symbols:
        aggregate = aggregate_by_symbol.get(symbol)
        row: dict[str, object] = {
            "bar_start": trace.clock.bar_start,
            "feature_cutoff": trace.clock.feature_cutoff,
            "decision_time": trace.clock.decision_time,
            "execution_time": trace.clock.execution_time,
            "symbol": symbol,
            "aggregate_score": aggregate.score if aggregate else None,
            "aggregate_confidence": aggregate.confidence if aggregate else None,
            "disagreement": aggregate.disagreement if aggregate else None,
            "aggregate_reason_codes": ",".join(code.value for code in aggregate.reason_codes)
            if aggregate
            else None,
            "blocked": symbol in trace.constraints.blocked_symbols if trace.constraints else None,
            "per_asset_cap": trace.constraints.per_asset_caps.get(symbol)
            if trace.constraints
            else None,
            "candidate_weight": trace.proposal.target_weights.get(symbol)
            if trace.proposal
            else None,
            "approved_weight": trace.approval.approved_weights.get(symbol)
            if trace.approval
            else None,
            "approval_action": trace.approval.action if trace.approval else None,
            "approval_reason_codes": ",".join(code.value for code in trace.approval.reason_codes)
            if trace.approval
            else None,
        }
        for signal in trace.signals:
            if signal.symbol == symbol:
                prefix = f"agent_{signal.agent}"
                row[f"{prefix}_score"] = signal.score
                row[f"{prefix}_confidence"] = signal.confidence
                row[f"{prefix}_reason_codes"] = ",".join(code.value for code in signal.reason_codes)
        rows.append(row)
    return pd.DataFrame(rows)
