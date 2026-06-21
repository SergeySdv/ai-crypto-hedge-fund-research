"""Stable artifact writers for metrics, equity, weights, orders and fills."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_hedge_fund.execution.broker import BacktestRunResult
from crypto_hedge_fund.provenance import UNKNOWN

ARTIFACT_SCHEMA_VERSION = "stage3-execution-artifacts-v1"


@dataclass(frozen=True)
class ArtifactProvenance:
    """Provenance attached to every Stage 3 output artifact."""

    level: str
    run_label: str
    split: str
    data_hash: str
    config_hash: str
    git_commit: str
    period_start: str
    period_end: str
    cost_assumptions: dict[str, float]
    benchmark: str
    seed: int
    final_test_lock_hash: str | None = None
    git_worktree_dirty: bool = False
    git_diff_sha256: str = UNKNOWN
    warnings: tuple[str, ...] = ()
    created_at_utc: str = field(
        default_factory=lambda: datetime.now(UTC).replace(microsecond=0).isoformat()
    )

    def metadata(self) -> dict[str, Any]:
        """Return JSON-serializable metadata."""
        data = asdict(self)
        data["artifact_schema_version"] = ARTIFACT_SCHEMA_VERSION
        return data


class BacktestArtifactWriter:
    """Write shared execution artifacts with stable schemas and provenance."""

    def __init__(self, artifacts_dir: str | Path) -> None:
        self.artifacts_dir = Path(artifacts_dir)

    def write_run(
        self,
        result: BacktestRunResult,
        metrics: dict[str, float],
        provenance: ArtifactProvenance,
        *,
        level_name: str,
    ) -> dict[str, Path]:
        """Write metrics/equity/weights/orders/fills and return their paths."""
        paths = {
            "metrics": self.artifacts_dir / "metrics" / f"{level_name}.csv",
            "equity": self.artifacts_dir / "equity" / f"{level_name}.parquet",
            "weights": self.artifacts_dir / "weights" / f"{level_name}.parquet",
            "orders": self.artifacts_dir / "orders" / f"{level_name}.parquet",
            "fills": self.artifacts_dir / "fills" / f"{level_name}.parquet",
        }
        self.write_metrics(metrics, paths["metrics"], provenance)
        self.write_frame(result.equity, paths["equity"], provenance)
        self.write_frame(result.weights, paths["weights"], provenance)
        self.write_frame(result.orders, paths["orders"], provenance)
        self.write_frame(result.fills, paths["fills"], provenance)
        return paths

    def write_metrics(
        self,
        metrics: dict[str, float],
        path: str | Path,
        provenance: ArtifactProvenance,
    ) -> Path:
        """Write one metrics CSV row with provenance columns."""
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        row = {str(key): float(value) for key, value in metrics.items()}
        frame = pd.DataFrame([self._with_metadata(row, provenance)])
        frame.to_csv(output, index=False)
        self._write_metadata_sidecar(output, provenance)
        return output

    def write_frame(
        self,
        frame: pd.DataFrame,
        path: str | Path,
        provenance: ArtifactProvenance,
    ) -> Path:
        """Write a parquet frame with repeated provenance columns and JSON sidecar."""
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        enriched = frame.copy()
        for key, value in self._provenance_columns(provenance).items():
            enriched[key] = value
        enriched.to_parquet(output, index=False)
        self._write_metadata_sidecar(output, provenance)
        return output

    @staticmethod
    def _provenance_columns(provenance: ArtifactProvenance) -> dict[str, str | int]:
        metadata = provenance.metadata()
        cost_assumptions = metadata.pop("cost_assumptions")
        warnings = metadata.pop("warnings")
        columns = {
            f"provenance_{key}": value if value is not None else ""
            for key, value in metadata.items()
        }
        columns["provenance_cost_assumptions"] = json.dumps(cost_assumptions, sort_keys=True)
        columns["provenance_warnings"] = json.dumps(list(warnings), sort_keys=True)
        return columns

    @classmethod
    def _with_metadata(
        cls,
        row: dict[str, float],
        provenance: ArtifactProvenance,
    ) -> dict[str, object]:
        return {**row, **cls._provenance_columns(provenance)}

    @staticmethod
    def _write_metadata_sidecar(path: Path, provenance: ArtifactProvenance) -> None:
        sidecar = path.with_suffix(f"{path.suffix}.metadata.json")
        with sidecar.open("w", encoding="utf-8") as handle:
            json.dump(provenance.metadata(), handle, indent=2, sort_keys=True)
            handle.write("\n")
