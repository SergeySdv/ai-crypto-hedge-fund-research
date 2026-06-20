"""Next-open simulated broker and portfolio ledger."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from crypto_hedge_fund.clock import build_daily_research_clock
from crypto_hedge_fund.execution.costs import (
    CostAssumptions,
    WeightDeltaCostModel,
    validate_target_risky_weights,
)
from crypto_hedge_fund.execution.panel import MissingPriceError, PanelMarketData
from crypto_hedge_fund.types import ReasonCode


class InvalidWeightsError(ValueError):
    """Raised when a target-weight schedule is invalid."""


class InfeasibleTradeError(ValueError):
    """Raised when valid weights cannot be funded without leverage."""


@dataclass(frozen=True)
class BacktestRunResult:
    """In-memory execution artifacts produced by the shared broker."""

    equity: pd.DataFrame
    weights: pd.DataFrame
    orders: pd.DataFrame
    fills: pd.DataFrame


def _validate_initial_capital(value: float) -> float:
    capital = float(value)
    if not math.isfinite(capital) or capital <= 0:
        msg = "initial_capital must be finite and positive"
        raise ValueError(msg)
    return capital


def _normalize_schedule(target_weights: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(target_weights, pd.DataFrame):
        msg = "target_weights must be a pandas DataFrame"
        raise TypeError(msg)
    if target_weights.empty:
        msg = "target_weights must not be empty"
        raise InvalidWeightsError(msg)
    schedule = target_weights.copy()
    if "bar_start_utc" in schedule.columns:
        schedule["bar_start_utc"] = pd.to_datetime(schedule["bar_start_utc"], utc=True)
        schedule = schedule.set_index("bar_start_utc")
    schedule.index = pd.to_datetime(schedule.index, utc=True)
    if schedule.index.has_duplicates:
        msg = "target_weights contains duplicate decision bars"
        raise InvalidWeightsError(msg)
    schedule.columns = schedule.columns.astype(str)
    schedule = schedule.sort_index(kind="mergesort").astype("float64")
    if not schedule.map(math.isfinite).all().all():
        msg = "target_weights must contain only finite values"
        raise InvalidWeightsError(msg)
    for timestamp, row in schedule.iterrows():
        try:
            validate_target_risky_weights(row, label=f"target_weights[{timestamp.isoformat()}]")
        except ValueError as exc:
            raise InvalidWeightsError(str(exc)) from exc
    return schedule


class SimulatedBroker:
    """Panel-native long-only broker that fills approved weights at next opens."""

    def __init__(
        self,
        market_data: PanelMarketData,
        *,
        initial_capital: float = 1_000_000.0,
        cost_assumptions: CostAssumptions | None = None,
    ) -> None:
        self.market_data = market_data
        self.initial_capital = _validate_initial_capital(initial_capital)
        self.cost_assumptions = cost_assumptions or CostAssumptions()
        self.cost_model = WeightDeltaCostModel(self.cost_assumptions)

    def run(
        self,
        target_weights: pd.DataFrame,
        *,
        end_time: datetime | pd.Timestamp | None = None,
        run_label: str = "stage3_kernel",
    ) -> BacktestRunResult:
        """Execute a target-weight schedule using completed-bar, next-open timing.

        The schedule index identifies the completed signal bar start. For a daily
        bar, the broker uses :func:`build_daily_research_clock`, so no fill can
        occur at the signal bar close or any earlier open.
        """
        schedule = _normalize_schedule(target_weights)
        execution_schedule: dict[pd.Timestamp, pd.Series] = {}
        for bar_start, row in schedule.iterrows():
            clock = build_daily_research_clock(bar_start.to_pydatetime())
            execution_schedule[pd.Timestamp(clock.execution_time)] = row

        start_time = min(schedule.index.min(), min(execution_schedule))
        final_time = (
            pd.Timestamp(end_time).tz_convert("UTC")
            if end_time is not None
            else max(execution_schedule)
        )
        all_open_times = self.market_data.open_times
        missing_execution_times = sorted(set(execution_schedule).difference(set(all_open_times)))
        if missing_execution_times:
            first_missing = missing_execution_times[0]
            msg = f"missing execution open at {first_missing.isoformat()}"
            raise MissingPriceError(msg)
        open_times = all_open_times[(all_open_times >= start_time) & (all_open_times <= final_time)]
        if open_times.empty:
            msg = "market data contains no opens covering the target-weight schedule"
            raise MissingPriceError(msg)

        holdings = pd.Series(dtype="float64")
        cash = self.initial_capital
        equity_rows: list[dict[str, object]] = []
        weight_rows: list[dict[str, object]] = []
        order_rows: list[dict[str, object]] = []
        fill_rows: list[dict[str, object]] = []
        order_number = 0

        for timestamp in open_times:
            active_symbols = sorted(
                set(holdings[holdings.abs() > 1e-15].index)
                | set(execution_schedule.get(timestamp, pd.Series(dtype="float64")).index)
            )
            prices = self.market_data.open_prices(timestamp, active_symbols, reason="valuation")
            nav_before = self._nav(cash, holdings, prices)
            turnover = 0.0
            fees = 0.0
            slippage = 0.0
            trade_count = 0

            if timestamp in execution_schedule:
                target = execution_schedule[timestamp].copy()
                symbols = target.index.union(holdings.index)
                target = target.reindex(symbols, fill_value=0.0)
                holdings = holdings.reindex(symbols, fill_value=0.0)
                prices = self.market_data.open_prices(timestamp, symbols, reason="execution")
                current_values = holdings * prices
                nav_before = self._nav(cash, holdings, prices)
                pretrade_weights = current_values / nav_before
                costs = self.cost_model.estimate_from_weight_deltas(
                    target,
                    pretrade_weights,
                    nav_before,
                )
                turnover = costs.reporting_turnover
                (
                    cash,
                    holdings,
                    new_order_rows,
                    new_fill_rows,
                    trade_count,
                    fees,
                    slippage,
                    order_number,
                ) = self._execute_rebalance(
                    cash=cash,
                    holdings=holdings,
                    prices=prices,
                    target=target,
                    nav=nav_before,
                    timestamp=timestamp,
                    order_number=order_number,
                    run_label=run_label,
                )
                order_rows.extend(new_order_rows)
                fill_rows.extend(new_fill_rows)

            prices = self.market_data.open_prices(timestamp, holdings.index, reason="valuation")
            nav_after = self._nav(cash, holdings, prices)
            risky_value = float((holdings * prices).sum())
            exposure = risky_value / nav_after if nav_after > 0 else 0.0
            equity_rows.append(
                {
                    "timestamp": timestamp,
                    "cash": cash,
                    "risky_value": risky_value,
                    "nav": nav_after,
                    "turnover": turnover,
                    "fees": fees,
                    "slippage": slippage,
                    "total_cost": fees + slippage,
                    "exposure": exposure,
                    "trade_count": trade_count,
                    "run_label": run_label,
                }
            )
            weight_row: dict[str, object] = {
                "timestamp": timestamp,
                "cash_weight": cash / nav_after,
                "run_label": run_label,
            }
            for symbol in holdings.index:
                weight_row[symbol] = (holdings[symbol] * prices[symbol]) / nav_after
            weight_rows.append(weight_row)

        return BacktestRunResult(
            equity=pd.DataFrame(equity_rows),
            weights=pd.DataFrame(weight_rows).fillna(0.0),
            orders=pd.DataFrame(order_rows, columns=self._order_columns()),
            fills=pd.DataFrame(fill_rows, columns=self._fill_columns()),
        )

    def _execute_rebalance(
        self,
        *,
        cash: float,
        holdings: pd.Series,
        prices: pd.Series,
        target: pd.Series,
        nav: float,
        timestamp: pd.Timestamp,
        order_number: int,
        run_label: str,
    ) -> tuple[
        float,
        pd.Series,
        list[dict[str, object]],
        list[dict[str, object]],
        int,
        float,
        float,
        int,
    ]:
        current_values = holdings * prices
        target_values = target * nav
        delta_values = target_values - current_values
        rows: list[dict[str, object]] = []
        fills: list[dict[str, object]] = []
        fees = 0.0
        slippage = 0.0
        trade_count = 0

        for symbol, delta in delta_values[delta_values < -1e-10].items():
            notional = float(-delta)
            order_number += 1
            fee = notional * self.cost_assumptions.fee_rate
            slip = notional * self.cost_assumptions.slippage_rate
            quantity = notional / float(prices[symbol])
            holdings[symbol] -= quantity
            cash += notional - fee - slip
            fees += fee
            slippage += slip
            trade_count += 1
            order_id = f"{run_label}-{order_number:06d}"
            rows.append(
                self._order_row(order_id, symbol, "sell", timestamp, notional, prices[symbol])
            )
            fills.append(
                self._fill_row(
                    order_id, symbol, "sell", timestamp, quantity, prices[symbol], fee, slip
                )
            )

        buy_deltas = delta_values[delta_values > 1e-10]
        required_cash = float(
            sum(delta * (1.0 + self.cost_assumptions.total_rate) for delta in buy_deltas)
        )
        if required_cash > cash + 1e-8:
            msg = (
                f"target weights require {required_cash:.10f} cash including costs, "
                f"but only {cash:.10f} is available"
            )
            raise InfeasibleTradeError(msg)

        for symbol, delta in buy_deltas.items():
            notional = float(delta)
            order_number += 1
            fee = notional * self.cost_assumptions.fee_rate
            slip = notional * self.cost_assumptions.slippage_rate
            quantity = notional / float(prices[symbol])
            holdings[symbol] += quantity
            cash -= notional + fee + slip
            fees += fee
            slippage += slip
            trade_count += 1
            order_id = f"{run_label}-{order_number:06d}"
            rows.append(
                self._order_row(order_id, symbol, "buy", timestamp, notional, prices[symbol])
            )
            fills.append(
                self._fill_row(
                    order_id, symbol, "buy", timestamp, quantity, prices[symbol], fee, slip
                )
            )

        if cash < -1e-8:
            msg = f"ledger cash became negative after execution: {cash}"
            raise InfeasibleTradeError(msg)
        holdings[holdings.abs() < 1e-14] = 0.0
        return cash, holdings, rows, fills, trade_count, fees, slippage, order_number

    @staticmethod
    def _nav(cash: float, holdings: pd.Series, prices: pd.Series) -> float:
        live_holdings = holdings[holdings.abs() > 1e-15]
        aligned_prices = prices.reindex(live_holdings.index)
        if aligned_prices.isna().any():
            missing = aligned_prices.index[aligned_prices.isna()].tolist()
            msg = f"missing valuation prices for holdings: {missing}"
            raise MissingPriceError(msg)
        nav = float(cash + (live_holdings * aligned_prices).sum())
        if not math.isfinite(nav) or nav <= 0:
            msg = f"ledger NAV must remain finite and positive, got {nav}"
            raise InfeasibleTradeError(msg)
        return nav

    @staticmethod
    def _order_columns() -> list[str]:
        return [
            "order_id",
            "timestamp",
            "symbol",
            "side",
            "target_notional",
            "reference_price",
            "reason_code",
            "run_label",
        ]

    @staticmethod
    def _fill_columns() -> list[str]:
        return [
            "order_id",
            "timestamp",
            "symbol",
            "side",
            "quantity",
            "fill_price",
            "fee",
            "slippage",
            "total_cost",
            "status",
            "reason_code",
            "run_label",
        ]

    @staticmethod
    def _order_row(
        order_id: str,
        symbol: str,
        side: str,
        timestamp: pd.Timestamp,
        notional: float,
        price: float,
    ) -> dict[str, object]:
        return {
            "order_id": order_id,
            "timestamp": timestamp,
            "symbol": symbol,
            "side": side,
            "target_notional": notional,
            "reference_price": float(price),
            "reason_code": ReasonCode.OK.value,
            "run_label": order_id.rsplit("-", maxsplit=1)[0],
        }

    @staticmethod
    def _fill_row(
        order_id: str,
        symbol: str,
        side: str,
        timestamp: pd.Timestamp,
        quantity: float,
        price: float,
        fee: float,
        slippage: float,
    ) -> dict[str, object]:
        return {
            "order_id": order_id,
            "timestamp": timestamp,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "fill_price": float(price),
            "fee": fee,
            "slippage": slippage,
            "total_cost": fee + slippage,
            "status": "filled",
            "reason_code": ReasonCode.OK.value,
            "run_label": order_id.rsplit("-", maxsplit=1)[0],
        }
