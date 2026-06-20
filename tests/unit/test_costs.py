import pandas as pd
import pytest

from crypto_hedge_fund.execution.costs import (
    CostAssumptions,
    InvalidWeightsError,
    WeightDeltaCostModel,
)


def _cost(target: dict[str, float], pretrade: dict[str, float]) -> float:
    model = WeightDeltaCostModel(CostAssumptions(fee_bps_one_way=10, slippage_bps_one_way=5))
    return model.estimate_from_weight_deltas(
        pd.Series(target, dtype="float64"),
        pd.Series(pretrade, dtype="float64"),
        1_000_000,
    ).total_cost


def test_cash_to_asset_charges_one_risky_trade_and_no_cash_instrument() -> None:
    breakdown = WeightDeltaCostModel(
        CostAssumptions(fee_bps_one_way=10, slippage_bps_one_way=5)
    ).estimate_from_weight_deltas(
        pd.Series({"BTC/USDT": 1.0}),
        pd.Series({"BTC/USDT": 0.0}),
        1_000_000,
    )

    assert breakdown.gross_traded_notional_fraction == pytest.approx(1.0)
    assert breakdown.reporting_turnover == pytest.approx(1.0)
    assert breakdown.total_cost == pytest.approx(1_500.0)


def test_asset_to_cash_charges_one_risky_trade() -> None:
    assert _cost({"BTC/USDT": 0.0}, {"BTC/USDT": 1.0}) == pytest.approx(1_500.0)


def test_asset_to_asset_rotation_charges_sell_plus_buy_risky_notional() -> None:
    assert _cost({"ETH/USDT": 1.0}, {"BTC/USDT": 1.0}) == pytest.approx(3_000.0)


def test_partial_rebalance_charges_absolute_risky_deltas() -> None:
    assert _cost(
        {"BTC/USDT": 0.5, "ETH/USDT": 0.5},
        {"BTC/USDT": 0.6, "ETH/USDT": 0.4},
    ) == pytest.approx(300.0)


def test_no_change_has_zero_cost_and_turnover() -> None:
    breakdown = WeightDeltaCostModel().estimate_from_weight_deltas(
        pd.Series({"BTC/USDT": 0.5}),
        pd.Series({"BTC/USDT": 0.5}),
        1000,
    )

    assert breakdown.gross_traded_notional == 0
    assert breakdown.reporting_turnover == 0
    assert breakdown.total_cost == 0


def test_invalid_weights_fail_closed() -> None:
    model = WeightDeltaCostModel()

    with pytest.raises(InvalidWeightsError, match="long-only"):
        model.estimate_from_weight_deltas(pd.Series({"BTC/USDT": -0.1}), pd.Series(), 1000)

    with pytest.raises(InvalidWeightsError, match="budget"):
        model.estimate_from_weight_deltas(pd.Series({"BTC/USDT": 1.1}), pd.Series(), 1000)
