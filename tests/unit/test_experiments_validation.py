from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from crypto_hedge_fund.cli import main


def _write_cli_fixture(tmp_path: Path) -> Path:
    rows = []
    for idx, timestamp in enumerate(pd.date_range("2023-12-25", "2024-01-05", tz="UTC")):
        price = 100.0 + idx
        rows.append(
            {
                "bar_start_utc": timestamp,
                "bar_end_utc": timestamp + pd.Timedelta(days=1),
                "symbol": "BTC/USDT",
                "open": price,
                "high": price + 1,
                "low": price - 1,
                "close": price,
                "volume": 1000.0,
                "dollar_volume": price * 1000.0,
                "exchange": "fixture",
                "market_type": "spot",
                "timeframe": "1d",
            }
        )
    market_path = tmp_path / "ohlcv.parquet"
    pd.DataFrame(rows).to_parquet(market_path, index=False)
    artifacts_dir = tmp_path / "artifacts"
    config = {
        "project": {"name": "test", "seed": 42, "timezone": "UTC", "mode": "test"},
        "paths": {
            "market_data": str(market_path),
            "instruments": str(tmp_path / "instruments.parquet"),
            "manifest": str(tmp_path / "manifest.json"),
            "artifacts": str(artifacts_dir),
        },
        "splits": {
            "validation_start": "2024-01-01",
            "validation_end": "2024-01-05",
            "test_start": "2025-01-01",
            "test_end": "2025-12-31",
        },
        "backtest": {
            "initial_capital_usd": 1000.0,
            "annualization_periods": 365,
            "risk_free_rate": 0.0,
            "fee_bps_one_way": 10.0,
            "slippage_bps_one_way": 5.0,
        },
        "level_1": {
            "symbol": "BTC/USDT",
            "fast_windows": [2],
            "slow_windows": [3],
            "selection_metric": "net_sharpe",
            "max_weight": 1.0,
            "cost_buffer_weight": 0.005,
            "min_cash_buffer": 0.005,
            "min_dollar_volume": 0.0,
        },
        "portfolio": {"max_gross_exposure": 1.0},
        "risk": {
            "max_drawdown_stop": 0.20,
            "high_volatility_threshold_annual": 0.80,
            "max_agent_disagreement": 0.75,
        },
        "final_test": {
            "require_lock": True,
            "lock_path": str(artifacts_dir / "final_test_lock.json"),
            "refuse_hash_mismatch": True,
        },
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path


def test_experiments_val_cli_runs_level1_validation_only(tmp_path: Path, capsys) -> None:
    config_path = _write_cli_fixture(tmp_path)
    artifacts_dir = tmp_path / "custom_artifacts"

    status = main(
        [
            "experiments-val",
            "--config",
            str(config_path),
            "--artifacts-dir",
            str(artifacts_dir),
        ]
    )

    captured = capsys.readouterr()
    assert status == 0
    assert '"split": "validation"' in captured.out
    assert '"final_test_exposure": "NOT_EXPOSED"' in captured.out
    assert (artifacts_dir / "metrics" / "level_1.csv").exists()
    assert not (artifacts_dir / "final_test_lock.json").exists()
