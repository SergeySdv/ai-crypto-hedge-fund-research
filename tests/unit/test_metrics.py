import pandas as pd
import pytest

from crypto_hedge_fund.metrics import calculate_performance_metrics


def test_performance_metrics_cover_return_risk_turnover_exposure_and_trades() -> None:
    equity = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=4, tz="UTC"),
            "nav": [100.0, 110.0, 105.0, 120.0],
            "turnover": [0.0, 0.5, 0.0, 0.2],
            "fees": [0.0, 1.0, 0.0, 0.5],
            "slippage": [0.0, 0.5, 0.0, 0.25],
            "total_cost": [0.0, 1.5, 0.0, 0.75],
            "exposure": [0.0, 0.5, 0.5, 0.7],
            "trade_count": [0, 1, 0, 2],
        }
    )
    weights = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=4, tz="UTC"),
            "cash_weight": [1.0, 0.5, 0.5, 0.3],
            "BTC/USDT": [0.0, 0.5, 0.4, 0.5],
            "ETH/USDT": [0.0, 0.0, 0.1, 0.2],
        }
    )
    benchmark_nav = pd.Series(
        [100.0, 105.0, 104.0, 112.0],
        index=equity.index,
        dtype="float64",
    )

    metrics = calculate_performance_metrics(
        equity,
        periods_per_year=365,
        weights=weights,
        benchmark_nav=benchmark_nav,
    )

    assert metrics["total_return"] == pytest.approx(0.2)
    assert metrics["roi"] == pytest.approx(0.2)
    assert metrics["downside_deviation"] > 0
    assert metrics["max_drawdown"] < 0
    assert metrics["drawdown_duration"] >= 1
    assert metrics["var_95"] > 0
    assert metrics["cvar_95"] >= metrics["var_95"]
    assert metrics["turnover"] == pytest.approx(0.7)
    assert metrics["average_exposure"] == pytest.approx(0.425)
    assert metrics["average_cash_exposure"] == pytest.approx(0.575)
    assert metrics["trade_count"] == pytest.approx(3)
    assert metrics["fees"] == pytest.approx(1.5)
    assert metrics["slippage"] == pytest.approx(0.75)
    assert metrics["total_cost"] == pytest.approx(2.25)
    assert metrics["average_concentration_hhi"] > 0
    assert metrics["average_effective_n"] > 0
    assert metrics["average_risky_weight_contribution_btc_usdt"] > 0
    assert metrics["average_risky_weight_contribution_eth_usdt"] > 0
    assert metrics["benchmark_total_return"] == pytest.approx(0.12)
    assert metrics["excess_total_return"] == pytest.approx(0.08)
    assert {"cagr", "volatility", "sharpe", "sortino", "calmar", "tracking_error"}.issubset(metrics)


def test_metrics_reject_missing_nav() -> None:
    with pytest.raises(ValueError, match="nav"):
        calculate_performance_metrics(pd.DataFrame({"equity": [1.0, 2.0]}))
