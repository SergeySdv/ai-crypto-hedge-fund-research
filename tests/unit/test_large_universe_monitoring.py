from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from crypto_hedge_fund.config import find_repo_root
from crypto_hedge_fund.experiments.level_5 import run_level_5_validation


def _config(tmp_path: Path) -> Path:
    root = find_repo_root()
    config = yaml.safe_load((root / "configs/default.yaml").read_text(encoding="utf-8"))
    config["paths"]["market_data"] = str(root / config["paths"]["market_data"])
    config["paths"]["instruments"] = str(root / config["paths"]["instruments"])
    config["paths"]["manifest"] = str(root / config["paths"]["manifest"])
    config["paths"]["artifacts"] = str(tmp_path / "artifacts")
    config["final_test"]["lock_path"] = str(tmp_path / "artifacts" / "final_test_lock.json")
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


def test_large_universe_monitoring_health_alerts_and_proof_fields(tmp_path: Path) -> None:
    result = run_level_5_validation(config_path=_config(tmp_path))
    health = pd.read_csv(result.health_summary_path)
    alerts = pd.read_parquet(result.alerts_path)
    proof = json.loads(result.pair_count_proof_path.read_text(encoding="utf-8"))

    assert health["level"].iloc[0] == "level_5"
    assert health["scored_count_max"].iloc[0] >= 100
    assert health["runtime_seconds"].iloc[0] > 0.0
    assert health["peak_rss_mb"].iloc[0] > 0.0
    assert health["peak_rss_unit"].iloc[0] == "MiB"
    assert health["final_test_exposure"].iloc[0] == "NOT_EXPOSED"
    assert {
        "level5_data",
        "level5_methodology",
        "level5_long_term_quality",
        "level5_fail_safe",
    }.issubset(set(alerts["component"]))
    assert "feature_drift_abs_mean" in health.columns
    assert "optimizer_fallback_rate" in health.columns
    assert "fail_safe_scenarios_demonstrated" in health.columns
    assert proof["runtime_seconds"] > 0.0
    assert proof["peak_rss_mb"] > 0.0
    assert proof["peak_rss_unit"] == "MiB"
    assert "full_universe_exclusion_reason_counts" in proof
    assert "filters" in proof
    assert proof["coverage_stats"]["valid_history_days_min"] >= 240
    assert proof["liquidity_stats"]["max_weight_by_liquidity_min"] >= 0.0
