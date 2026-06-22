"""Compact notebook display helpers for the reviewer-facing report."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

LABELS = {
    "level": "Level",
    "selected_result": "Selected",
    "approach": "Approach",
    "method": "Method",
    "policy": "Policy",
    "net_total_return": "Net return",
    "net_benchmark_total_return": "Benchmark",
    "net_sharpe": "Sharpe",
    "net_max_drawdown": "Max DD",
    "net_turnover": "Turnover",
    "net_total_cost": "Costs",
    "eligible_count": "Eligible",
    "scored_count": "Scored",
    "selected_count": "Selected count",
    "runtime_seconds": "Runtime",
    "peak_rss_mb": "Peak RSS",
}
PCT_COLUMNS = {
    "net_total_return",
    "net_benchmark_total_return",
    "net_max_drawdown",
    "net_turnover",
}
USD_COLUMNS = {"net_total_cost"}


def configure_notebook_display() -> None:
    """Set conservative display defaults without custom notebook CSS."""

    pd.set_option("display.max_columns", 10)
    pd.set_option("display.max_rows", 20)
    pd.set_option("display.width", 120)
    plt.rcParams.update(
        {
            "figure.figsize": (8.5, 4.2),
            "figure.dpi": 120,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
        }
    )


def short_hash(value: object) -> str:
    text = str(value)
    return text if len(text) <= 24 else text[:16] + "..." + text[-8:]


def format_cell(value: Any, column: str) -> str:
    try:
        if pd.isna(value):
            return "n/a"
    except (TypeError, ValueError):
        pass
    if isinstance(value, bool):
        return "yes" if value else "no"
    if column in PCT_COLUMNS:
        return f"{float(value):.1%}"
    if column in USD_COLUMNS:
        return f"${float(value):,.0f}"
    if column == "runtime_seconds":
        return f"{float(value):.1f}s"
    if column == "peak_rss_mb":
        return f"{float(value):.0f} MiB"
    if isinstance(value, float):
        return f"{value:.3f}"
    text = str(value)
    return text if len(text) <= 70 else text[:67] + "..."


def compact_frame(
    frame: pd.DataFrame,
    columns: list[str],
    *,
    max_rows: int = 12,
) -> pd.DataFrame:
    available = [column for column in columns if column in frame.columns]
    shown = frame.loc[:, available].head(max_rows).copy()
    for column in shown.columns:
        shown[column] = shown[column].map(lambda value, col=column: format_cell(value, col))
    return shown.rename(columns={column: LABELS.get(column, column) for column in shown.columns})


def key_value_frame(items: list[tuple[str, object]]) -> pd.DataFrame:
    return pd.DataFrame([{"Metric": key, "Value": value} for key, value in items])


def selected_summary_frame(ctx: Any) -> pd.DataFrame:
    return compact_frame(
        ctx.selected_metrics,
        [
            "level",
            "selected_result",
            "net_total_return",
            "net_benchmark_total_return",
            "net_sharpe",
            "net_max_drawdown",
            "net_total_cost",
        ],
    )


def plot_return_overview(ctx: Any) -> plt.Figure:
    frame = ctx.selected_metrics.copy()
    labels = frame["level"].str.replace("_", " ").str.title()
    x = range(len(frame))
    width = 0.36
    fig, ax = plt.subplots(figsize=(8.2, 3.8))
    ax.bar(
        [item - width / 2 for item in x],
        frame["net_total_return"] * 100,
        width,
        label="Strategy",
    )
    ax.bar(
        [item + width / 2 for item in x],
        frame["net_benchmark_total_return"] * 100,
        width,
        label="Benchmark",
    )
    ax.axhline(0, color="#111827", linewidth=0.8)
    ax.set_xticks(list(x), labels, rotation=0)
    ax.set_ylabel("Net return, %")
    ax.set_title("Final-test net return by level")
    ax.legend(loc="best")
    fig.tight_layout()
    return fig


def plot_selected_nav(ctx: Any) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8.2, 4.0))
    for row in ctx.selected_metrics.itertuples(index=False):
        path = ctx.final_dir / "equity" / (row.level + ".parquet")
        equity = pd.read_parquet(path)
        selector = None
        for candidate in ("approach", "method", "policy"):
            if candidate in equity.columns and hasattr(row, candidate):
                selector = candidate
                break
        if selector is not None:
            equity = equity[equity[selector] == getattr(row, selector)]
        if equity.empty:
            continue
        nav = equity.sort_values("timestamp").drop_duplicates("timestamp")
        label = row.level.replace("_", " ").title()
        ax.plot(nav["timestamp"], nav["nav"] / nav["nav"].iloc[0], label=label, linewidth=1.5)
    ax.axhline(1.0, color="#111827", linewidth=0.8)
    ax.set_title("Selected strategies: normalized NAV")
    ax.set_ylabel("NAV / initial NAV")
    ax.set_xlabel("")
    ax.legend(loc="best", ncols=2)
    fig.autofmt_xdate(rotation=0)
    fig.tight_layout()
    return fig
