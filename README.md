# AI Crypto Hedge Fund

Educational research repository for a historical, reproducible crypto trading-system assignment.
It is not a profitability claim and does not enable live trading.

Stage 1 contains the environment skeleton, configuration surface, UTC research clock helpers,
provenance hashing, and frozen typed contracts shared by all later strategy levels.

## Setup

```bash
uv sync --frozen
make lint
make test
```

The repository uses Python 3.11, a `src/` package layout, Ruff, pytest, and `uv.lock`.

## Current Command Surface

All stable commands from `AGENTS.md` exist in the `Makefile`. Stage 1 intentionally fails
later-stage commands closed with explicit messages until data, experiments, final-test lock,
notebook, report, and presentation artifacts are implemented.

`make final-test` refuses to run without `artifacts/final_test_lock.json`.

## Research Conventions

- Daily UTC spot bars.
- Completed-bar features only.
- Decisions execute under a next-open convention.
- Long-only, unlevered, explicit-cash portfolio contracts.
- Signal, risk, portfolio, rebalance, execution, and ledger boundaries remain separate.

## License

MIT. See `LICENSE`.
