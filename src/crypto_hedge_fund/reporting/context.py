"""Load and validate committed Stage 11 artifacts for Stage 12 reporting."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_hedge_fund.provenance import file_sha256

ACCEPTED_FINAL_TEST_LOCK_SHA256: str | None = None
FINAL_TEST_ARTIFACT_DIR = Path("artifacts/final_test")
LEVELS = tuple(f"level_{number}" for number in range(1, 6))


class Stage12ArtifactError(RuntimeError):
    """Raised when final reporting inputs are missing or inconsistent."""


@dataclass(frozen=True)
class Stage12Context:
    """Validated view of final-test and validation artifacts used by reports."""

    repo_root: Path
    final_dir: Path
    lock_hash: str
    lock: dict[str, Any]
    suite_summary: dict[str, Any]
    exposure_evidence: dict[str, Any]
    metrics: dict[str, pd.DataFrame]
    selected_metrics: pd.DataFrame
    level5_pair_count_proof: dict[str, Any]
    health_summary: pd.DataFrame
    traces: dict[str, dict[str, Any]]
    validation_metrics: dict[str, pd.DataFrame]

    @property
    def level5_counts(self) -> dict[str, Any]:
        return dict(self.suite_summary["level_5_counts"])

    @property
    def final_period(self) -> tuple[str, str]:
        start, end = self.suite_summary["period"]
        return str(start), str(end)

    @property
    def cost_assumptions(self) -> dict[str, Any]:
        return dict(self.suite_summary["cost_assumptions"])


def load_stage12_context(repo_root: Path | str = Path(".")) -> Stage12Context:
    """Load committed final-test artifacts and fail if the accepted lock is absent."""

    root = Path(repo_root).resolve()
    lock_path = root / "artifacts/final_test_lock.json"
    if not lock_path.exists():
        raise Stage12ArtifactError("missing final-test lock: artifacts/final_test_lock.json")
    lock_hash = file_sha256(lock_path)
    if ACCEPTED_FINAL_TEST_LOCK_SHA256 is not None and lock_hash != ACCEPTED_FINAL_TEST_LOCK_SHA256:
        raise Stage12ArtifactError(
            "final-test lock hash mismatch: "
            f"expected {ACCEPTED_FINAL_TEST_LOCK_SHA256}, got {lock_hash}"
        )

    final_dir = root / FINAL_TEST_ARTIFACT_DIR / lock_hash[:12]
    summary_path = final_dir / "final_test_suite_summary.json"
    exposure_path = final_dir / "final_test_exposure_evidence.json"
    proof_path = final_dir / "monitoring/level_5_pair_count_proof.json"
    health_path = final_dir / "monitoring/health_summary.csv"

    required = [lock_path, summary_path, exposure_path, proof_path, health_path]
    required.extend(final_dir / "metrics" / f"{level}.csv" for level in LEVELS)
    required.extend(final_dir / "monitoring" / f"{level}_decision_trace.json" for level in LEVELS)
    missing = [path for path in required if not path.exists()]
    if missing:
        missing_display = ", ".join(str(path.relative_to(root)) for path in missing)
        raise Stage12ArtifactError(f"missing required Stage 12 input artifacts: {missing_display}")

    lock = _read_json(lock_path)
    summary = _read_json(summary_path)
    exposure = _read_json(exposure_path)
    proof = _read_json(proof_path)
    health = pd.read_csv(health_path)
    metrics = {level: pd.read_csv(final_dir / "metrics" / f"{level}.csv") for level in LEVELS}
    traces = {
        level: _read_json(final_dir / "monitoring" / f"{level}_decision_trace.json")
        for level in LEVELS
    }
    validation_metrics = _load_validation_metrics(root)

    _validate_summary(summary=summary, exposure=exposure, proof=proof, lock_hash=lock_hash)

    return Stage12Context(
        repo_root=root,
        final_dir=final_dir,
        lock_hash=lock_hash,
        lock=lock,
        suite_summary=summary,
        exposure_evidence=exposure,
        metrics=metrics,
        selected_metrics=_selected_metric_rows(metrics),
        level5_pair_count_proof=proof,
        health_summary=health,
        traces=traces,
        validation_metrics=validation_metrics,
    )


def metric_label(level: str, row: pd.Series) -> str:
    if level == "level_1":
        return "SMA baseline"
    if level == "level_2":
        return str(row.get("approach", "agent_ensemble"))
    if level == "level_3":
        return str(row.get("method", "static_portfolio"))
    if level == "level_4":
        return str(row.get("policy", "dynamic_rebalance"))
    return "large_universe_dynamic"


def format_percent(value: object, digits: int = 1) -> str:
    number = _to_float(value)
    return "n/a" if number is None else f"{number * 100:.{digits}f}%"


def format_float(value: object, digits: int = 2) -> str:
    number = _to_float(value)
    return "n/a" if number is None else f"{number:.{digits}f}"


def format_usd(value: object) -> str:
    number = _to_float(value)
    return "n/a" if number is None else f"${number:,.0f}"


def markdown_table(rows: list[dict[str, object]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join([header, separator, *body])


def selected_rows_for_markdown(context: Stage12Context) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for _, row in context.selected_metrics.iterrows():
        level = str(row["level"])
        rows.append(
            {
                "Level": level.replace("_", " ").title(),
                "Selected result": str(row["selected_result"]),
                "Net return": format_percent(row.get("net_total_return")),
                "Net Sharpe": format_float(row.get("net_sharpe")),
                "Max drawdown": format_percent(row.get("net_max_drawdown")),
                "Total costs": format_usd(row.get("net_total_cost")),
                "Benchmark": format_percent(row.get("net_benchmark_total_return")),
            }
        )
    return rows


def representative_trace_rows(context: Stage12Context) -> list[dict[str, object]]:
    trace = context.traces["level_2"]["representative_decision_trace"]
    clock = trace["clock"]
    rows: list[dict[str, object]] = []
    for signal in trace["signals"]:
        rows.append(
            {
                "agent": signal["agent"],
                "symbol": signal["symbol"],
                "score": format_float(signal["score"], digits=3),
                "confidence": format_float(signal["confidence"], digits=3),
                "fit_cutoff": signal["fit_cutoff"],
                "feature_cutoff": signal["feature_cutoff"],
                "reason_codes": ",".join(signal["reason_codes"]),
            }
        )
    aggregate = trace["aggregated_signals"][0]
    rows.append(
        {
            "agent": "aggregator",
            "symbol": aggregate["symbol"],
            "score": format_float(aggregate["score"], digits=3),
            "confidence": format_float(aggregate["confidence"], digits=3),
            "fit_cutoff": clock["bar_start"],
            "feature_cutoff": clock["feature_cutoff"],
            "reason_codes": ",".join(aggregate["reason_codes"]),
        }
    )
    approval = trace["approval"]
    rows.append(
        {
            "agent": "post_risk",
            "symbol": "portfolio",
            "score": approval["action"],
            "confidence": f"cash={format_percent(approval['cash_weight'])}",
            "fit_cutoff": clock["decision_time"],
            "feature_cutoff": clock["execution_time"],
            "reason_codes": ",".join(approval["reason_codes"]),
        }
    )
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise Stage12ArtifactError(f"expected JSON object in {path}")
    return payload


def _validate_summary(
    *,
    summary: dict[str, Any],
    exposure: dict[str, Any],
    proof: dict[str, Any],
    lock_hash: str,
) -> None:
    if summary.get("final_test_exposure") != "EXPOSED":
        raise Stage12ArtifactError("final-test summary is not marked EXPOSED")
    if exposure.get("final_test_exposure") != "EXPOSED":
        raise Stage12ArtifactError("final-test exposure evidence is not marked EXPOSED")
    if summary.get("final_test_lock_sha256") != lock_hash:
        raise Stage12ArtifactError("summary final-test lock hash does not match lock file")
    counts = summary.get("level_5_counts", {})
    expected = {"eligible_count": 120, "scored_count": 120, "selected_count": 25}
    for key, expected_value in expected.items():
        if counts.get(key) != expected_value:
            raise Stage12ArtifactError(
                f"unexpected Level 5 {key}: expected {expected_value}, got {counts.get(key)}"
            )
    proof_counts = {
        "eligible_count": 120,
        "scored_count": 120,
        "selected_count": 25,
    }
    for key, expected_value in proof_counts.items():
        if proof.get(key) != expected_value:
            raise Stage12ArtifactError(
                f"unexpected Level 5 proof {key}: expected {expected_value}, got {proof.get(key)}"
            )


def _selected_metric_rows(metrics: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for level, frame in metrics.items():
        row = _selected_row(level, frame)
        row_dict = row.to_dict()
        row_dict["level"] = level
        row_dict["selected_result"] = metric_label(level, row)
        rows.append(row_dict)
    return pd.DataFrame(rows)


def _selected_row(level: str, frame: pd.DataFrame) -> pd.Series:
    if frame.empty:
        raise Stage12ArtifactError(f"{level} metrics are empty")
    flag = f"selected_for_{level}"
    if flag in frame.columns:
        selected = frame[frame[flag].astype(bool)]
        if len(selected) != 1:
            raise Stage12ArtifactError(f"{level} must have exactly one selected metrics row")
        return selected.iloc[0]
    return frame.iloc[0]


def _load_validation_metrics(root: Path) -> dict[str, pd.DataFrame]:
    metrics_dir = root / "artifacts/metrics"
    frames: dict[str, pd.DataFrame] = {}
    for level in LEVELS:
        path = metrics_dir / f"{level}.csv"
        if path.exists():
            frames[level] = pd.read_csv(path)
    return frames


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(number):
        return None
    return number
