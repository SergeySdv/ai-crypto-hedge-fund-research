from datetime import UTC, datetime

import pandas as pd
import pytest

from crypto_hedge_fund.execution import (
    CostAssumptions,
    InfeasibleTradeError,
    InvalidWeightsError,
    MissingPriceError,
    PanelMarketData,
    SimulatedBroker,
)


def _panel(rows: list[tuple[str, str, float]]) -> PanelMarketData:
    frame = pd.DataFrame(
        [
            {
                "bar_start_utc": timestamp,
                "symbol": symbol,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": 1.0,
                "dollar_volume": price,
                "exchange": "fixture",
                "market_type": "spot",
                "timeframe": "1d",
            }
            for timestamp, symbol, price in rows
        ]
    )
    return PanelMarketData.from_ohlcv(frame)


def test_completed_bar_signal_fills_only_at_next_open_and_has_no_earlier_pnl() -> None:
    market = _panel(
        [
            ("2024-01-01T00:00:00+00:00", "BTC/USDT", 100.0),
            ("2024-01-02T00:00:00+00:00", "BTC/USDT", 200.0),
            ("2024-01-03T00:00:00+00:00", "BTC/USDT", 300.0),
            ("2024-01-04T00:00:00+00:00", "BTC/USDT", 600.0),
        ]
    )
    broker = SimulatedBroker(
        market,
        initial_capital=1000,
        cost_assumptions=CostAssumptions(fee_bps_one_way=0, slippage_bps_one_way=0),
    )
    result = broker.run(
        pd.DataFrame(
            [{"BTC/USDT": 0.5}],
            index=[pd.Timestamp("2024-01-01T00:00:00+00:00")],
        ),
        end_time=pd.Timestamp("2024-01-04T00:00:00+00:00"),
    )

    equity = result.equity.set_index("timestamp")
    assert equity.loc[pd.Timestamp("2024-01-01T00:00:00+00:00"), "nav"] == pytest.approx(1000)
    assert equity.loc[pd.Timestamp("2024-01-01T00:00:00+00:00"), "exposure"] == pytest.approx(0)
    assert result.fills["timestamp"].tolist() == [pd.Timestamp("2024-01-02T00:00:00+00:00")]
    assert equity.loc[pd.Timestamp("2024-01-02T00:00:00+00:00"), "nav"] == pytest.approx(1000)
    assert equity.loc[pd.Timestamp("2024-01-03T00:00:00+00:00"), "nav"] == pytest.approx(1250)
    assert equity.loc[pd.Timestamp("2024-01-04T00:00:00+00:00"), "nav"] == pytest.approx(2000)


def test_missing_next_open_price_blocks_execution_explicitly() -> None:
    market = _panel(
        [
            ("2024-01-01T00:00:00+00:00", "BTC/USDT", 100.0),
        ]
    )
    broker = SimulatedBroker(market, initial_capital=1000)

    with pytest.raises(MissingPriceError, match="execution open"):
        broker.run(
            pd.DataFrame(
                [{"BTC/USDT": 0.5}],
                index=[pd.Timestamp("2024-01-01T00:00:00+00:00")],
            )
        )


def test_invalid_and_infeasible_weights_fail_closed() -> None:
    market = _panel(
        [
            ("2024-01-01T00:00:00+00:00", "BTC/USDT", 100.0),
            ("2024-01-02T00:00:00+00:00", "BTC/USDT", 100.0),
            ("2024-01-03T00:00:00+00:00", "BTC/USDT", 100.0),
        ]
    )
    broker = SimulatedBroker(market, initial_capital=1000)

    with pytest.raises(InvalidWeightsError, match="long-only"):
        broker.run(
            pd.DataFrame(
                [{"BTC/USDT": -0.1}],
                index=[pd.Timestamp("2024-01-01T00:00:00+00:00")],
            )
        )

    with pytest.raises(InfeasibleTradeError, match="require"):
        broker.run(
            pd.DataFrame(
                [{"BTC/USDT": 1.0}],
                index=[pd.Timestamp("2024-01-01T00:00:00+00:00")],
            )
        )


def test_one_symbol_and_multi_symbol_use_same_engine_and_are_deterministic() -> None:
    rows = []
    for day, btc, eth in [
        ("2024-01-01T00:00:00+00:00", 100.0, 50.0),
        ("2024-01-02T00:00:00+00:00", 100.0, 50.0),
        ("2024-01-03T00:00:00+00:00", 110.0, 55.0),
        ("2024-01-04T00:00:00+00:00", 121.0, 50.0),
    ]:
        rows.append((day, "BTC/USDT", btc))
        rows.append((day, "ETH/USDT", eth))
    market = _panel(rows)
    assumptions = CostAssumptions(fee_bps_one_way=0, slippage_bps_one_way=0)
    one_symbol = pd.DataFrame(
        [{"BTC/USDT": 0.5}],
        index=[pd.Timestamp("2024-01-01T00:00:00+00:00")],
    )
    multi_symbol = pd.DataFrame(
        [{"BTC/USDT": 0.25, "ETH/USDT": 0.25}],
        index=[pd.Timestamp("2024-01-01T00:00:00+00:00")],
    )

    first = SimulatedBroker(market, initial_capital=1000, cost_assumptions=assumptions).run(
        one_symbol,
        end_time=datetime(2024, 1, 4, tzinfo=UTC),
    )
    second = SimulatedBroker(market, initial_capital=1000, cost_assumptions=assumptions).run(
        one_symbol,
        end_time=datetime(2024, 1, 4, tzinfo=UTC),
    )
    multi = SimulatedBroker(market, initial_capital=1000, cost_assumptions=assumptions).run(
        multi_symbol,
        end_time=datetime(2024, 1, 4, tzinfo=UTC),
    )

    pd.testing.assert_frame_equal(first.equity, second.equity)
    pd.testing.assert_frame_equal(first.orders, second.orders)
    assert set(multi.fills["symbol"]) == {"BTC/USDT", "ETH/USDT"}
    assert list(first.weights.columns) != ["BTC/USDT"]


def test_broker_ledger_transitions_are_consistent_across_rebalance_cases() -> None:
    rows = []
    for day in pd.date_range("2024-01-01", periods=6, tz="UTC"):
        timestamp = day.isoformat()
        rows.append((timestamp, "BTC/USDT", 100.0))
        rows.append((timestamp, "ETH/USDT", 50.0))
    market = _panel(rows)
    broker = SimulatedBroker(
        market,
        initial_capital=1000,
        cost_assumptions=CostAssumptions(fee_bps_one_way=0, slippage_bps_one_way=0),
    )
    schedule = pd.DataFrame(
        [
            {"BTC/USDT": 0.5, "ETH/USDT": 0.0},
            {"BTC/USDT": 0.5, "ETH/USDT": 0.0},
            {"BTC/USDT": 0.25, "ETH/USDT": 0.25},
            {"BTC/USDT": 0.0, "ETH/USDT": 0.5},
            {"BTC/USDT": 0.0, "ETH/USDT": 0.0},
        ],
        index=pd.date_range("2024-01-01", periods=5, tz="UTC"),
    )

    result = broker.run(schedule, end_time=pd.Timestamp("2024-01-06T00:00:00+00:00"))
    equity = result.equity.set_index("timestamp")
    weights = result.weights.set_index("timestamp")

    assert equity["nav"].tolist() == pytest.approx([1000] * 6)
    assert equity.loc[pd.Timestamp("2024-01-02T00:00:00+00:00"), "cash"] == pytest.approx(500)
    assert weights.loc[pd.Timestamp("2024-01-02T00:00:00+00:00"), "BTC/USDT"] == pytest.approx(0.5)
    assert equity.loc[pd.Timestamp("2024-01-03T00:00:00+00:00"), "trade_count"] == pytest.approx(0)
    assert weights.loc[pd.Timestamp("2024-01-04T00:00:00+00:00"), "BTC/USDT"] == pytest.approx(0.25)
    assert weights.loc[pd.Timestamp("2024-01-04T00:00:00+00:00"), "ETH/USDT"] == pytest.approx(0.25)
    assert weights.loc[pd.Timestamp("2024-01-05T00:00:00+00:00"), "BTC/USDT"] == pytest.approx(0.0)
    assert weights.loc[pd.Timestamp("2024-01-05T00:00:00+00:00"), "ETH/USDT"] == pytest.approx(0.5)
    assert equity.loc[pd.Timestamp("2024-01-06T00:00:00+00:00"), "cash"] == pytest.approx(1000)
    assert weights.loc[pd.Timestamp("2024-01-06T00:00:00+00:00"), "cash_weight"] == pytest.approx(
        1.0
    )
    assert result.orders["side"].tolist() == ["buy", "sell", "buy", "sell", "buy", "sell"]
    assert result.fills["total_cost"].sum() == pytest.approx(0.0)


def test_benchmark_series_is_price_normalized_open_to_open_not_a_broker_result() -> None:
    market = _panel(
        [
            ("2024-01-01T00:00:00+00:00", "BTC/USDT", 100.0),
            ("2024-01-02T00:00:00+00:00", "BTC/USDT", 200.0),
            ("2024-01-03T00:00:00+00:00", "BTC/USDT", 300.0),
        ]
    )

    benchmark = market.benchmark_open_to_open(
        "BTC/USDT",
        start_time=pd.Timestamp("2024-01-02T00:00:00+00:00"),
    )

    assert benchmark["timestamp"].tolist() == [
        pd.Timestamp("2024-01-02T00:00:00+00:00"),
        pd.Timestamp("2024-01-03T00:00:00+00:00"),
    ]
    assert benchmark["benchmark_nav"].tolist() == pytest.approx([1.0, 1.5])
    assert benchmark["benchmark_return"].tolist() == pytest.approx([0.0, 0.5])
    assert "fee" not in benchmark.columns
