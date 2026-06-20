"""UTC clock helpers for completed-bar and next-open research semantics."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from crypto_hedge_fund.types import ResearchClock


def ensure_utc(value: date | datetime | str) -> datetime:
    """Convert a date, datetime or ISO string to a timezone-aware UTC datetime."""
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    elif isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, time.min)
    else:
        msg = f"Unsupported timestamp type: {type(value)!r}"
        raise TypeError(msg)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def build_daily_research_clock(bar_start: date | datetime | str) -> ResearchClock:
    """Build a daily next-open clock for one completed UTC bar.

    The daily bar starts at ``bar_start``. Features are available after the bar
    closes, and a completed bar at date ``t`` fills at the next daily open,
    which is the start of bar ``t+1`` in the repository's daily UTC data.
    """
    start = ensure_utc(bar_start)
    if start.time() != time.min:
        msg = f"Daily bar_start must be midnight UTC, got {start.isoformat()}"
        raise ValueError(msg)
    bar_end = start + timedelta(days=1)
    feature_cutoff = bar_end
    decision_time = feature_cutoff
    execution_time = bar_end
    return ResearchClock(
        bar_start=start,
        bar_end=bar_end,
        feature_cutoff=feature_cutoff,
        decision_time=decision_time,
        execution_time=execution_time,
    )


def validate_next_open_clock(clock: ResearchClock) -> None:
    """Raise when a research clock violates completed-bar ordering."""
    if not (
        clock.bar_start
        < clock.bar_end
        <= clock.feature_cutoff
        <= clock.decision_time
        <= clock.execution_time
    ):
        msg = (
            "Expected bar_start < bar_end <= feature_cutoff <= decision_time "
            "<= execution_time for next-open execution"
        )
        raise ValueError(msg)
