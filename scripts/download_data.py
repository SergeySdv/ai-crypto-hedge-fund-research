"""CLI wrapper for downloading/freezing the public OHLCV snapshot."""

from __future__ import annotations

from crypto_hedge_fund.data.download import main

if __name__ == "__main__":
    raise SystemExit(main())
