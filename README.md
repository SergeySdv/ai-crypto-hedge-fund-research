# AI Crypto Hedge Fund

Educational research repository for a historical, reproducible crypto trading-system assignment.
It is not a profitability claim and does not enable live trading.

Stage 2 contains the environment skeleton plus the frozen data layer: included Binance
daily spot OHLCV, instrument metadata, manifest hash validation, deterministic universe
filters, and the full-mode 100+ pair eligibility proof.

## Setup

```bash
uv sync --frozen
make validate-data
make lint
make test
```

The repository uses Python 3.11, a `src/` package layout, Ruff, pytest, and `uv.lock`.

## Current Command Surface

All stable commands from `AGENTS.md` exist in the `Makefile`. Stage 2 implements:

```bash
make data           # re-freezes the configured public CCXT/Binance snapshot
make validate-data  # validates included files, manifest hashes, and 100+ pair proof
```

Later-stage experiment, final-test lock, notebook, report, and presentation commands still
fail closed until their implementation stages.

`make final-test` refuses to run without `artifacts/final_test_lock.json`.

## Included Data

The default offline data bundle is:

- `data/processed/ohlcv_daily.parquet`
- `data/processed/instruments.parquet`
- `data/manifests/ohlcv_daily_manifest.json`

Current Stage 2 snapshot: Binance spot, USDT quote, daily bars, 2021-01-01 through
2025-12-31 UTC where available, 158,511 rows across 163 symbols.

`make validate-data` currently proves 104 eligible/scored full-mode Level 5 pairs at
decision cutoff `2025-07-01T00:00:00+00:00`. The snapshot is selected from currently
active Binance markets, so survivorship/delisting bias is documented in `data/README.md`
and `reports/data_card.md`.

## Research Conventions

- Daily UTC spot bars.
- Completed-bar features only.
- Decisions execute under a next-open convention.
- Long-only, unlevered, explicit-cash portfolio contracts.
- Signal, risk, portfolio, rebalance, execution, and ledger boundaries remain separate.

## License

MIT. See `LICENSE`.
