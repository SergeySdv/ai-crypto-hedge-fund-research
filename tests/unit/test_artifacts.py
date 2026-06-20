import json

import pandas as pd

from crypto_hedge_fund.artifacts import ArtifactProvenance, BacktestArtifactWriter
from crypto_hedge_fund.execution.broker import BacktestRunResult


def test_artifact_writers_add_provenance_and_stable_schema(tmp_path) -> None:
    result = BacktestRunResult(
        equity=pd.DataFrame(
            {"timestamp": pd.date_range("2024-01-01", periods=1, tz="UTC"), "nav": [1.0]}
        ),
        weights=pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=1, tz="UTC"),
                "cash_weight": [1.0],
            }
        ),
        orders=pd.DataFrame({"order_id": ["o1"], "symbol": ["BTC/USDT"]}),
        fills=pd.DataFrame({"order_id": ["o1"], "symbol": ["BTC/USDT"], "fee": [1.0]}),
    )
    provenance = ArtifactProvenance(
        level="level_1",
        run_label="validation",
        split="validation",
        data_hash="datahash",
        config_hash="confighash",
        git_commit="gitsha",
        period_start="2024-01-01",
        period_end="2024-12-31",
        cost_assumptions={"fee_bps_one_way": 10.0, "slippage_bps_one_way": 5.0},
        benchmark="buy_and_hold",
        seed=42,
        warnings=("survivorship_bias_active_markets",),
        created_at_utc="2026-01-01T00:00:00+00:00",
    )

    paths = BacktestArtifactWriter(tmp_path).write_run(
        result,
        {"total_return": 0.1, "sharpe": 1.0},
        provenance,
        level_name="level_1",
    )

    metrics = pd.read_csv(paths["metrics"])
    equity = pd.read_parquet(paths["equity"])
    assert metrics.loc[0, "provenance_data_hash"] == "datahash"
    assert metrics.loc[0, "provenance_artifact_schema_version"] == "stage3-execution-artifacts-v1"
    assert equity.loc[0, "provenance_run_label"] == "validation"
    assert set(paths) == {"metrics", "equity", "weights", "orders", "fills"}

    sidecar = paths["equity"].with_suffix(".parquet.metadata.json")
    metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    assert metadata["artifact_schema_version"] == "stage3-execution-artifacts-v1"
    assert metadata["warnings"] == ["survivorship_bias_active_markets"]
