# Limitations And Attribution

## Research Limitations

- The system is a historical backtest, not a live trading system.
- The default universe is Binance spot USDT markets and may contain survivorship
  and delisting bias.
- Daily OHLCV bars cannot model intraday order book depth, queue position, spread
  dynamics, or funding/frictions outside the configured cost model.
- USDT is treated as cash with a zero risk-free rate.
- The system is long-only, unlevered, spot-only, and daily-bar based.
- Level 5 uses deterministic large-universe scoring and constrained allocation;
  it is not presented as a profitable institutional ML strategy.
- The exposed final-test results include underperforming strategies, which are
  reported as research findings.

## Safety Limitations

- No live order submission is enabled.
- Signal agents cannot place orders.
- Risk gates can block symbols, cap exposure, force cash, or reject infeasible
  portfolios.
- Any future live adapter would require separate controls for credentials,
  idempotency, reconciliation, exchange filters, partial fills, and monitoring.

## License

Project code is MIT licensed. See `LICENSE`.

Third-party dependency license details are listed in `THIRD_PARTY_LICENSES.md`.

## Reference Projects

The project may use public projects and papers as conceptual references, but does
not copy code from non-permissively licensed repositories. In particular, no code
from `denisalpino/autofin` is copied; that project is treated as a reference only
because its notice is not an open-source license.
