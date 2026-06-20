from datetime import UTC, datetime, timedelta

import pytest

from crypto_hedge_fund.clock import build_daily_research_clock, ensure_utc, validate_next_open_clock
from crypto_hedge_fund.types import ResearchClock


def test_ensure_utc_normalizes_supported_inputs() -> None:
    assert ensure_utc("2024-01-01").tzinfo == UTC
    assert ensure_utc(datetime(2024, 1, 1, tzinfo=UTC)) == datetime(2024, 1, 1, tzinfo=UTC)


def test_daily_research_clock_enforces_next_open_ordering() -> None:
    clock = build_daily_research_clock("2024-01-01")

    assert clock.bar_start == datetime(2024, 1, 1, tzinfo=UTC)
    assert clock.bar_end == datetime(2024, 1, 2, tzinfo=UTC)
    assert clock.feature_cutoff < clock.decision_time < clock.execution_time
    validate_next_open_clock(clock)


def test_research_clock_rejects_same_close_execution() -> None:
    bar_start = datetime(2024, 1, 1, tzinfo=UTC)

    with pytest.raises(ValueError, match="ResearchClock requires"):
        ResearchClock(
            bar_start=bar_start,
            bar_end=bar_start + timedelta(days=1),
            feature_cutoff=bar_start + timedelta(days=1),
            decision_time=bar_start + timedelta(days=1),
            execution_time=bar_start + timedelta(days=1),
        )


def test_daily_research_clock_requires_midnight_start() -> None:
    with pytest.raises(ValueError, match="midnight UTC"):
        build_daily_research_clock("2024-01-01T12:00:00+00:00")
