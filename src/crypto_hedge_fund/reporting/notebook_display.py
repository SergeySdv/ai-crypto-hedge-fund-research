"""Compact notebook display helpers for the reviewer-facing report."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

LABELS = {
    "level": "Level",
    "selected_result": "Selected",
    "approach": "Approach",
    "method": "Method",
    "policy": "Policy",
    "net_total_return": "Net",
    "gross_total_return": "Gross",
    "gross_to_net_total_return_decay": "Cost drag",
    "net_benchmark_total_return": "Bench",
    "net_sharpe": "Sharpe",
    "net_max_drawdown": "MDD",
    "net_turnover": "Turn",
    "net_total_cost": "Cost",
    "net_average_cash_exposure": "Avg cash",
    "net_trade_count": "Trades",
    "eligible_count": "Eligible",
    "scored_count": "Scored",
    "selected_count": "Holdings",
    "runtime_seconds": "Runtime",
    "peak_rss_mb": "Peak RSS",
    "predictive_roc_auc": "ROC-AUC",
    "predictive_pr_auc": "PR-AUC",
    "predictive_log_loss": "Log loss",
    "predictive_brier_score": "Brier",
    "predictive_directional_accuracy": "Dir acc",
    "selected_for_level_1": "Selected",
    "selected_for_level_2": "Selected",
    "selected_for_level_3": "Selected",
    "selected_for_level_4": "Selected",
    "selected_for_level_5": "Selected",
    "agent": "Agent",
    "score": "Score",
    "confidence": "Conf",
    "fit_cutoff": "Fit",
    "reason_codes": "Action",
}
PCT_COLUMNS = {
    "net_total_return",
    "gross_total_return",
    "gross_to_net_total_return_decay",
    "net_benchmark_total_return",
    "net_max_drawdown",
    "net_turnover",
    "net_average_cash_exposure",
    "turnover_cap",
    "max_weight",
    "coverage_rate_min",
    "optimizer_fallback_rate",
    "cost_decay_proxy",
    "abstention_rate",
    "agent_disagreement_rate",
}
USD_COLUMNS = {"net_total_cost", "fee_bearing_notional", "total_cost", "fees", "slippage"}
FLOAT_COLUMNS = {
    "net_sharpe",
    "predictive_roc_auc",
    "predictive_pr_auc",
    "predictive_log_loss",
    "predictive_brier_score",
    "predictive_directional_accuracy",
}
VALUE_ALIASES = {
    "technical_sma": "SMA",
    "econometric_ar_garch": "AR/GARCH",
    "ml_logistic": "Logistic",
    "ml_hist_gradient_boosting": "HGB",
    "agent_ensemble": "Ensemble",
    "equal_weight": "Equal weight",
    "inverse_volatility": "Inv vol",
    "minimum_variance": "Min var",
    "cvar_downside": "CVaR",
    "static_level3_benchmark": "Static",
    "calendar_monthly": "Calendar",
    "drift_monthly": "Drift",
    "signal_risk_monthly": "Signal/risk",
    "large_universe_dynamic": "Large universe",
}


class DeterministicNotebookTable:
    """Notebook display object with stable HTML and plain-text representations."""

    def __init__(self, html: str, label: str) -> None:
        self._html = html
        self._label = label

    def _repr_html_(self) -> str:
        return self._html

    def __repr__(self) -> str:
        return f"DeterministicNotebookTable({self._label})"


def configure_notebook_display() -> None:
    """Set conservative display defaults without relying on external CSS."""

    pd.set_option("display.max_columns", 8)
    pd.set_option("display.max_rows", 18)
    pd.set_option("display.width", 100)
    plt.rcParams.update(
        {
            "figure.figsize": (7.4, 3.4),
            "figure.dpi": 120,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
        }
    )


def short_hash(value: object, *, head: int = 12, tail: int = 6) -> str:
    text = str(value)
    return text if len(text) <= head + tail + 3 else text[:head] + "..." + text[-tail:]


def compact_date(value: object) -> str:
    text = str(value)
    if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
        return text[:10]
    return text


def compact_list(value: object, *, max_items: int = 5) -> str:
    if isinstance(value, str):
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            parsed = value
    else:
        parsed = value
    if not isinstance(parsed, list | tuple):
        return str(value)
    shown = [str(item) for item in parsed[:max_items]]
    suffix = "" if len(parsed) <= max_items else f", +{len(parsed) - max_items}"
    return ", ".join(shown) + suffix


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
    if column in FLOAT_COLUMNS:
        return f"{float(value):.3f}"
    if column in {"fit_cutoff", "feature_cutoff", "bar_start_utc", "execution_time"}:
        return compact_date(value)
    if column == "reason_codes":
        return compact_list(value, max_items=3)
    if isinstance(value, float):
        return f"{value:.3f}"
    text = str(value)
    if column in {"approach", "method", "policy", "selected_result"}:
        text = VALUE_ALIASES.get(text, text)
    return text if len(text) <= 46 else text[:43] + "..."


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


def _stable_table_uuid(frame: pd.DataFrame, caption: str | None) -> str:
    payload = {
        "caption": caption or "",
        "columns": [str(column) for column in frame.columns],
        "index": [str(index) for index in frame.index],
        "shape": list(frame.shape),
        "values": frame.astype(str).to_dict(orient="split")["data"],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:10]


def show_frame(frame: pd.DataFrame, *, caption: str | None = None) -> Any:
    """Return compact deterministic table output for notebook/PDF rendering."""

    styler = frame.style.hide(axis="index")
    if caption:
        styler = styler.set_caption(caption)
    html = (
        styler.set_table_attributes(
            'style="font-size:9pt; width:100%; border-collapse:collapse; table-layout:fixed"'
        )
        .set_uuid(_stable_table_uuid(frame, caption))
        .set_properties(
            **{
                "text-align": "center",
                "white-space": "normal",
                "overflow-wrap": "anywhere",
                "padding": "3px 5px",
            }
        )
        .set_table_styles(
            [
                {
                    "selector": "caption",
                    "props": "caption-side:top; text-align:left; font-weight:600",
                },
                {
                    "selector": "th",
                    "props": "text-align:center; border-bottom:1px solid #d1d5db",
                },
                {
                    "selector": "td",
                    "props": "text-align:center; border-bottom:1px solid #e5e7eb",
                },
            ]
        )
        .to_html()
    )
    label = caption or f"{frame.shape[0]}x{frame.shape[1]}"
    return DeterministicNotebookTable(html, repr(label))


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


def reproducibility_frame(ctx: Any) -> pd.DataFrame:
    summary = ctx.suite_summary
    lock = ctx.lock
    return key_value_frame(
        [
            ("Python", "3.11"),
            ("Package manager", "uv with committed uv.lock"),
            ("Final-test period", "2025-01-01 to 2025-12-31"),
            ("Train/validation", "2021-2023 train, 2024 validation"),
            ("Final-test lock", short_hash(ctx.lock_hash)),
            ("Data SHA-256", short_hash(summary["data_sha256"])),
            ("Validation config", short_hash(summary["validation_selected_sha256"])),
            ("Locked commit", short_hash(summary["locked_git_commit"])),
            ("Runner commit", short_hash(summary["git_commit"])),
            ("Base tag", lock["git"]["base_tag"]),
            ("Public URL", "not configured in this checkout; owner must publish/verify"),
        ]
    )


def data_card_frame(ctx: Any) -> pd.DataFrame:
    data = pd.read_parquet("data/processed/ohlcv_daily.parquet")
    instruments = pd.read_parquet("data/processed/instruments.parquet")
    ohlcv_nulls = int(data[["open", "high", "low", "close", "volume"]].isna().sum().sum())
    duplicates = int(data.duplicated(["bar_start_utc", "symbol"]).sum())
    period = (
        f"{compact_date(data['bar_start_utc'].min())} "
        f"to {compact_date(data['bar_start_utc'].max())}"
    )
    return key_value_frame(
        [
            ("Source", "Binance spot USDT via CCXT snapshot"),
            ("Timeframe", "1d OHLCV, UTC bar-start semantics"),
            ("Period", period),
            ("Rows", f"{len(data):,}"),
            ("Symbols", f"{instruments['symbol'].nunique():,}"),
            ("Duplicate symbol-days", duplicates),
            ("Null OHLCV fields", ohlcv_nulls),
            ("Known limitation", "active-market survivorship/delisting bias"),
        ]
    )


def notebook_scope_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Section": "Data validation",
                "Behavior": "read-only verification from committed data/artifacts",
            },
            {
                "Section": "Model specification",
                "Behavior": "read from source config and frozen lock",
            },
            {
                "Section": "2024 validation",
                "Behavior": "loaded as pre-exposure validation artifacts",
            },
            {"Section": "2025 final results", "Behavior": "loaded as frozen final-test evidence"},
            {"Section": "Final test", "Behavior": "never rerun by this notebook"},
        ]
    )


def lock_lineage_frame(ctx: Any) -> pd.DataFrame:
    summary = ctx.suite_summary
    lock = ctx.lock
    pre_exposure = (
        f"results_inspected={lock['final_test_results_inspected']}; "
        f"state={lock['final_test_exposure_state']}"
    )
    return pd.DataFrame(
        [
            {
                "Field": "Current release source of truth",
                "Value": short_hash(ctx.lock_hash),
            },
            {
                "Field": "Lock role",
                "Value": "pretest/final methodology lock for this committed release",
            },
            {
                "Field": "Pre-exposure statement",
                "Value": pre_exposure,
            },
            {
                "Field": "Locked commit",
                "Value": short_hash(summary["locked_git_commit"]),
            },
            {
                "Field": "Runner commit",
                "Value": short_hash(summary["git_commit"]),
            },
            {
                "Field": "Final artifacts reference",
                "Value": "all committed final-test metadata in c33b5eb396f6 references this lock",
            },
            {
                "Field": "Earlier external audit reference",
                "Value": "dab407... is not a committed release lock in this checkout",
            },
        ]
    )


def benchmark_frame(ctx: Any) -> pd.DataFrame:
    labels = {
        "levels_1_2": "Levels 1-2",
        "level_3": "Level 3",
        "level_4": "Level 4",
        "level_5": "Level 5",
    }
    return pd.DataFrame(
        [
            {"Scope": labels.get(scope, scope), "Benchmark definition": definition}
            for scope, definition in ctx.lock["benchmarks"].items()
        ]
    )


def benchmark_reconciliation_frame(ctx: Any) -> pd.DataFrame:
    level5_final = ctx.metrics["level_5"].iloc[0]
    level5_validation = ctx.validation_metrics["level_5"].iloc[0]
    btc_final = ctx.metrics["level_1"].iloc[0]
    return pd.DataFrame(
        [
            {
                "Benchmark": "Level 5 frozen final",
                "Return": format_cell(
                    level5_final["net_benchmark_total_return"], "net_benchmark_total_return"
                ),
                "Status": "locked in c33 final-test lock",
                "Definition": level5_final["provenance_benchmark"],
            },
            {
                "Benchmark": "BTC buy-and-hold final",
                "Return": format_cell(
                    btc_final["net_benchmark_total_return"], "net_benchmark_total_return"
                ),
                "Status": "diagnostic comparator only",
                "Definition": btc_final["provenance_benchmark"],
            },
            {
                "Benchmark": "Level 5 validation feasibility",
                "Return": format_cell(
                    level5_validation["net_benchmark_total_return"], "net_benchmark_total_return"
                ),
                "Status": "short Dec-2024 validation diagnostic",
                "Definition": level5_validation["provenance_benchmark"],
            },
        ]
    )


def model_spec_frame(ctx: Any) -> pd.DataFrame:
    level2 = ctx.lock["selected"]["level_2"]
    return pd.DataFrame(
        [
            {
                "Model": "SMA",
                "Preprocessing": "completed close history",
                "Parameters": "10/50 in Level 2; 30/100 in Level 1",
                "Refit": "rule-based",
            },
            {
                "Model": "AutoReg/GARCH",
                "Preprocessing": "open returns",
                "Parameters": "AutoReg + GARCH(1,1)",
                "Refit": level2["econometric_refit"],
            },
            {
                "Model": "Logistic Regression",
                "Preprocessing": "median imputer + StandardScaler",
                "Parameters": "max_iter=500; class_weight=balanced",
                "Refit": f"{level2['ml_retrain']} expanding",
            },
            {
                "Model": "HistGradientBoosting",
                "Preprocessing": "median imputer",
                "Parameters": "60 iter; LR 0.05; 15 leaves; L2 0.01",
                "Refit": f"{level2['ml_retrain']} expanding",
            },
        ]
    )


def target_features_frame(ctx: Any) -> pd.DataFrame:
    fee_bps = ctx.cost_assumptions["fee_bps_one_way"]
    slippage_bps = ctx.cost_assumptions["slippage_bps_one_way"]
    safety_bps = ctx.lock["selected"]["level_2"]["safety_margin_bps"]
    threshold = (fee_bps + slippage_bps + safety_bps) / 10_000
    return key_value_frame(
        [
            ("Target", f"1[open(t+2) / open(t+1) - 1 > {threshold:.4f}]"),
            (
                "Threshold formula",
                (
                    f"({fee_bps:.0f} fee bps + {slippage_bps:.0f} slippage bps "
                    f"+ {safety_bps:.0f} safety bps) / 10000"
                ),
            ),
            (
                "Feature groups",
                "returns, momentum, trend, RSI/MACD, ATR/range, vol, drawdown, volume",
            ),
            ("Causal clock", "completed daily bars; decisions execute at next open"),
            ("ML retraining", ctx.lock["selected"]["level_2"]["ml_retrain"]),
            ("Econometric refit", ctx.lock["selected"]["level_2"]["econometric_refit"]),
            (
                "Agent weights",
                json.dumps(ctx.lock["selected"]["level_2"]["agent_weights"], sort_keys=True),
            ),
        ]
    )


def leakage_evidence_frame(ctx: Any) -> pd.DataFrame:
    audit = pd.read_parquet(ctx.final_dir / "monitoring/level_2_fit_audit.parquet")
    predictions = pd.read_parquet(ctx.final_dir / "monitoring/level_2_model_predictions.parquet")
    return key_value_frame(
        [
            ("Fit-audit rows", f"{len(audit):,}"),
            ("Prediction rows", f"{len(predictions):,}"),
            ("Future-label flags", int(audit["used_future_labels"].sum())),
            ("Audit status", ", ".join(sorted(audit["status"].dropna().unique()))),
            ("ML refit", ", ".join(sorted(audit["refit_frequency"].dropna().unique()))),
            ("Feature cutoff example", compact_date(predictions["feature_cutoff"].iloc[0])),
            ("Fit cutoff example", compact_date(predictions["fit_cutoff"].iloc[0])),
        ]
    )


def candidate_results_frame(ctx: Any, level: str, *, split: str) -> pd.DataFrame:
    source = ctx.validation_metrics if split == "validation" else ctx.metrics
    frame = source[level]
    selector = f"selected_for_{level}"
    columns = [
        "approach",
        "method",
        "policy",
        selector,
        "net_total_return",
        "net_sharpe",
        "net_max_drawdown",
    ]
    if level != "level_3":
        columns.extend(["net_turnover", "net_total_cost"])
    return compact_frame(frame, columns, max_rows=8)


def selected_validation_final_frame(ctx: Any) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for level in ("level_1", "level_2", "level_3", "level_4", "level_5"):
        for split, source in (("Validation", ctx.validation_metrics), ("Final", ctx.metrics)):
            frame = source[level]
            selector = f"selected_for_{level}"
            row = (
                frame[frame[selector].astype(bool)].iloc[0] if selector in frame else frame.iloc[0]
            )
            rows.append(
                {
                    "Level": level.replace("_", " ").title(),
                    "Split": split,
                    "Selected": _selected_name(level, row),
                    "Net": format_cell(row["net_total_return"], "net_total_return"),
                    "Bench": format_cell(
                        row["net_benchmark_total_return"], "net_benchmark_total_return"
                    ),
                    "Sharpe": format_cell(row["net_sharpe"], "net_sharpe"),
                    "MDD": format_cell(row["net_max_drawdown"], "net_max_drawdown"),
                }
            )
    return pd.DataFrame(rows)


def predictive_metrics_frame(ctx: Any) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for split, source in (("Validation", ctx.validation_metrics), ("Final", ctx.metrics)):
        frame = source["level_2"]
        for approach in ("ml_logistic", "ml_hist_gradient_boosting"):
            row = frame[frame["approach"] == approach].iloc[0]
            rows.append(
                {
                    "Model": "Logistic" if approach == "ml_logistic" else "HGB",
                    "Split": split,
                    "ROC-AUC": format_cell(row["predictive_roc_auc"], "predictive_roc_auc"),
                    "PR-AUC": format_cell(row["predictive_pr_auc"], "predictive_pr_auc"),
                    "Log loss": format_cell(row["predictive_log_loss"], "predictive_log_loss"),
                    "Brier": format_cell(row["predictive_brier_score"], "predictive_brier_score"),
                }
            )
    return pd.DataFrame(rows)


def robustness_frame(ctx: Any) -> pd.DataFrame:
    rows = []
    sources = [
        ("Validation", "used before freeze", "artifacts/monitoring/level_2_robustness.json"),
        (
            "Final",
            "post-hoc diagnostic only",
            str(ctx.final_dir / "monitoring/level_2_robustness.json"),
        ),
    ]
    for split, role, path_text in sources:
        path = Path(path_text)
        payload = json.loads(path.read_text(encoding="utf-8"))
        provenance = payload["provenance"]
        robust = payload["robustness"]
        bootstrap = robust["block_bootstrap"]
        randomization = robust["circular_shift_randomization"]
        cost = robust["cost_sensitivity"]
        sharpe_ci = f"{bootstrap['sharpe_ci_95'][0]:.2f} to {bootstrap['sharpe_ci_95'][1]:.2f}"
        rows.append(
            {
                "Split": split,
                "Role": role,
                "Period": f"{provenance['period_start']} to {provenance['period_end']}",
                "Sharpe 95% CI": sharpe_ci,
                "Shift p": f"{randomization['two_sided_p_value']:.3f}",
                "Corr": f"{randomization['observed_score_forward_return_correlation']:.4f}",
                "Net ROI": format_cell(cost["1x_recorded_net_roi"], "net_total_return"),
            }
        )
    return pd.DataFrame(rows)


def selection_rationale_frame(ctx: Any) -> pd.DataFrame:
    level4 = ctx.lock["selected"]["level_4"]
    constraints = level4["selection_constraints"]
    return pd.DataFrame(
        [
            {
                "Level": "1",
                "Frozen selection": "SMA 30/100 BTC",
                "Rationale": "validation net Sharpe among SMA grid; typed SignalAgent wrapper",
            },
            {
                "Level": "2",
                "Frozen selection": "Ensemble",
                "Rationale": "multi-agent candidate; acceptable risk, not max-performance row",
            },
            {
                "Level": "3",
                "Frozen selection": ctx.lock["selected"]["level_3"]["selected_method"],
                "Rationale": "maximum validation net Sharpe in static portfolio candidates",
            },
            {
                "Level": "4",
                "Frozen selection": level4["selected_policy"],
                "Rationale": (
                    f"validation selected under MDD <= {constraints['max_drawdown']:.0%}, "
                    f"turnover <= {constraints['annual_turnover']:.1f}"
                ),
            },
            {
                "Level": "5",
                "Frozen selection": "top-25 inv-vol universe",
                "Rationale": "cross-sectional scoring; validates >=100 pairs and fail-safes",
            },
        ]
    )


def level1_agent_evolution_frame(ctx: Any) -> pd.DataFrame:
    selected = ctx.lock["selected"]["level_1"]
    return key_value_frame(
        [
            (
                "Rule",
                (
                    f"{selected['symbol']} SMA fast={selected['fast_window']}, "
                    f"slow={selected['slow_window']}"
                ),
            ),
            ("Execution", "completed close signal; next-open broker execution"),
            (
                "Agent evolution",
                "SMA rule -> typed SignalAgent -> score/confidence -> ensemble input",
            ),
            ("Risk layer", "pre/post risk controls decide final exposure and can move to cash"),
        ]
    )


def level3_assets_frame(ctx: Any) -> pd.DataFrame:
    level3 = ctx.lock["selected"]["level_3"]
    method = level3["selected_method"]
    weights = level3["final_weights_by_method"][method]["weights"]
    rows = [
        {"Symbol": symbol, "Weight": f"{weight:.1%}"}
        for symbol, weight in sorted(weights.items(), key=lambda item: item[1], reverse=True)
    ]
    cash_rounding = max(0.0, 1.0 - sum(float(weight) for weight in weights.values()))
    if cash_rounding > 1e-6:
        rows.append({"Symbol": "Cash/rounding", "Weight": f"{cash_rounding:.1%}"})
    return pd.DataFrame(rows)


def level3_method_frame(ctx: Any) -> pd.DataFrame:
    level3 = ctx.lock["selected"]["level_3"]
    return key_value_frame(
        [
            ("Final assets", ", ".join(level3["final_symbols"])),
            ("Estimation window", "2024-01-01 to 2024-12-31"),
            ("Candidate methods", ", ".join(level3["candidate_methods"])),
            ("Selected method", level3["selected_method"]),
            ("Objective", "validation net Sharpe; risk/cost metrics reported net of fees/slippage"),
            (
                "Trading application",
                "target weights -> risk approval -> next-open orders/fills -> ledger",
            ),
        ]
    )


def level4_policy_frame(ctx: Any) -> pd.DataFrame:
    rows = []
    for policy in ctx.lock["selected"]["level_4"]["candidate_policies"]:
        drift = float(policy["drift_threshold_abs"])
        score = float(policy["score_change_threshold"])
        rows.append(
            {
                "Policy": VALUE_ALIASES.get(policy["name"], policy["name"]),
                "Calendar": policy["calendar"],
                "Drift": "disabled" if drift >= 1.0 else format_cell(drift, "turnover_cap"),
                "Score trigger": "disabled" if score >= 1.0 else format_cell(score, "turnover_cap"),
                "Risk trigger": "yes" if policy["risk_trigger"] else "no",
            }
        )
    return pd.DataFrame(rows)


def level5_mechanics_frame(ctx: Any) -> pd.DataFrame:
    level5 = ctx.lock["selected"]["level_5"]
    filters = level5["filters"]
    return pd.DataFrame(
        [
            {
                "Question": "Pair selection",
                "Implementation": (
                    f"{filters['quote_currency']} spot; history/liquidity filters; "
                    "excludes stable/fiat bases"
                ),
            },
            {
                "Question": "Signal priority",
                "Implementation": "deterministic cross-sectional factor score",
            },
            {
                "Question": "Factors",
                "Implementation": "20/60-day momentum, vol, drawdown, liquidity penalties",
            },
            {
                "Question": "Portfolio",
                "Implementation": (
                    f"top {level5['top_k']}; max {level5['max_weight']:.0%}; "
                    f"{level5['allocator']} allocation"
                ),
            },
            {
                "Question": "Rebalance",
                "Implementation": (
                    f"{level5['rebalance_calendar']} plus drift/signal/risk; "
                    f"score trigger {level5['score_change_threshold']:.0%}"
                ),
            },
            {
                "Question": "Risk",
                "Implementation": "pre/post gates, cash approval, caps, turnover checks",
            },
            {
                "Question": "Monitoring",
                "Implementation": "runtime, RSS, incidents, fallback, nulls, pair counts",
            },
            {
                "Question": "Fail-safe",
                "Implementation": "abstain, retain weights, move to cash, kill switch evidence",
            },
            {
                "Question": "Long-term quality",
                "Implementation": (
                    "freshness, coverage, feature drift, calibration, disagreement, "
                    "rolling Sharpe/drawdown, cost drift, universe churn"
                ),
            },
        ]
    )


def level5_diagnostics_frame(ctx: Any) -> pd.DataFrame:
    metric = ctx.metrics["level_5"].iloc[0]
    equity = pd.read_parquet(ctx.final_dir / "equity/level_5.parquet")
    fee_bps = ctx.cost_assumptions["fee_bps_one_way"]
    fee_bearing_notional = equity["fees"].sum() / (fee_bps / 10_000)
    initial_capital = ctx.cost_assumptions["initial_capital_usd"]
    return key_value_frame(
        [
            ("Gross return", format_cell(metric["gross_total_return"], "gross_total_return")),
            (
                "Return drag from costs",
                (
                    format_cell(
                        metric["gross_to_net_total_return_decay"],
                        "gross_to_net_total_return_decay",
                    )
                    + " gross-to-net"
                ),
            ),
            ("Net return", format_cell(metric["net_total_return"], "net_total_return")),
            (
                "Benchmark",
                format_cell(metric["net_benchmark_total_return"], "net_benchmark_total_return"),
            ),
            ("Rebalance decisions", int(ctx.health_summary.iloc[0]["submitted_rebalances"])),
            ("Fills", f"{int(metric['net_trade_count']):,}"),
            ("Fee-bearing notional", format_cell(fee_bearing_notional, "fee_bearing_notional")),
            ("Total cost", format_cell(metric["net_total_cost"], "net_total_cost")),
            ("Cost as % initial AUM", f"{metric['net_total_cost'] / initial_capital:.1%}"),
            (
                "Average cash",
                format_cell(metric["net_average_cash_exposure"], "net_average_cash_exposure"),
            ),
        ]
    )


def monitoring_incident_frame(ctx: Any) -> pd.DataFrame:
    health = ctx.health_summary.iloc[0]
    alerts = pd.read_parquet(ctx.final_dir / "monitoring/alerts.parquet")
    critical_count = int((alerts["severity"].str.lower() == "critical").sum())
    warning_count = int((alerts["severity"].str.lower() == "warning").sum())
    info_count = int((alerts["severity"].str.lower() == "info").sum())
    return key_value_frame(
        [
            ("System status", health["system_status"]),
            ("Status meaning", "operational pipeline health, not investment performance"),
            ("Recorded monitoring events", int(health["incident_count"])),
            ("Critical alerts", critical_count),
            ("Warning alert rows", warning_count),
            ("Info alert rows", info_count),
            ("Invalid data count", int(health["data_quality_invalid_count"])),
            ("Invalid model count", int(health["model_quality_invalid_count"])),
            (
                "Optimizer fallback rate",
                format_cell(health["optimizer_fallback_rate"], "optimizer_fallback_rate")
                + " final-test rate",
            ),
            ("Abstention rate", format_cell(health["abstention_rate"], "abstention_rate")),
            (
                "Fail-safe evidence",
                compact_list(health["fail_safe_scenarios_demonstrated"], max_items=4),
            ),
        ]
    )


def commands_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Step": "Setup", "Command": "uv sync --frozen"},
            {"Step": "Data", "Command": "make validate-data"},
            {"Step": "Quality", "Command": "make lint && make test"},
            {"Step": "Notebook", "Command": "make notebook-full"},
            {"Step": "Deck", "Command": "make presentation"},
            {"Step": "Release", "Command": "make release-verify"},
            {"Step": "Do not rerun", "Command": "make final-test after exposure"},
        ]
    )


def trace_frame(trace_rows: list[dict[str, object]]) -> pd.DataFrame:
    trace = pd.DataFrame(trace_rows).copy()
    trace["fit_cutoff"] = trace["fit_cutoff"].map(compact_date)
    trace["reason_codes"] = trace["reason_codes"].map(lambda item: compact_list(item, max_items=2))
    return compact_frame(
        trace, ["agent", "score", "confidence", "fit_cutoff", "reason_codes"], max_rows=8
    )


def plot_return_overview(ctx: Any) -> plt.Figure:
    frame = ctx.selected_metrics.copy()
    labels = frame["level"].str.replace("_", " ").str.title()
    x = range(len(frame))
    width = 0.36
    fig, ax = plt.subplots(figsize=(7.4, 3.1))
    ax.bar(
        [item - width / 2 for item in x], frame["net_total_return"] * 100, width, label="Strategy"
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
    ax.set_title("Frozen final-test net return")
    ax.legend(loc="best")
    fig.tight_layout()
    return fig


def plot_selected_nav(ctx: Any) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
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
        ax.plot(nav["timestamp"], nav["nav"] / nav["nav"].iloc[0], label=label, linewidth=1.2)
    ax.axhline(1.0, color="#111827", linewidth=0.8)
    ax.set_title("Selected strategies: normalized NAV")
    ax.set_ylabel("NAV / initial NAV")
    ax.set_xlabel("")
    ax.legend(loc="best", ncols=2)
    fig.autofmt_xdate(rotation=0)
    fig.tight_layout()
    return fig


def plot_predictive_auc(ctx: Any) -> plt.Figure:
    validation = ctx.validation_metrics["level_2"]
    final = ctx.metrics["level_2"]
    rows = []
    for approach, label in (("ml_logistic", "Logistic"), ("ml_hist_gradient_boosting", "HGB")):
        rows.append(
            {
                "Model": label,
                "Validation": validation.loc[
                    validation["approach"] == approach, "predictive_roc_auc"
                ].iloc[0],
                "Final": final.loc[final["approach"] == approach, "predictive_roc_auc"].iloc[0],
            }
        )
    frame = pd.DataFrame(rows)
    x = range(len(frame))
    width = 0.34
    fig, ax = plt.subplots(figsize=(5.8, 2.8))
    ax.bar([item - width / 2 for item in x], frame["Validation"], width, label="Validation")
    ax.bar([item + width / 2 for item in x], frame["Final"], width, label="Final")
    ax.axhline(0.5, color="#111827", linewidth=0.8, linestyle="--")
    ax.set_xticks(list(x), frame["Model"])
    ax.set_ylim(0.45, 0.62)
    ax.set_ylabel("ROC-AUC")
    ax.set_title("Predictive validation did not generalize")
    ax.legend(loc="best")
    fig.tight_layout()
    return fig


def plot_selected_drawdowns(ctx: Any) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    for row in ctx.selected_metrics.itertuples(index=False):
        equity = pd.read_parquet(ctx.final_dir / "equity" / (row.level + ".parquet"))
        for candidate in ("approach", "method", "policy"):
            if candidate in equity.columns and hasattr(row, candidate):
                equity = equity[equity[candidate] == getattr(row, candidate)]
                break
        if equity.empty:
            continue
        equity = equity.sort_values("timestamp").drop_duplicates("timestamp")
        nav = equity["nav"] / equity["nav"].iloc[0]
        drawdown = nav / nav.cummax() - 1
        ax.plot(
            equity["timestamp"],
            drawdown * 100,
            label=row.level.replace("_", " ").title(),
            linewidth=1.1,
        )
    ax.set_title("Selected strategies: final-test drawdowns")
    ax.set_ylabel("Drawdown, %")
    ax.set_xlabel("")
    ax.legend(loc="lower left", ncols=2)
    fig.autofmt_xdate(rotation=0)
    fig.tight_layout()
    return fig


def plot_level5_cost_decomposition(ctx: Any) -> plt.Figure:
    row = ctx.metrics["level_5"].iloc[0]
    labels = ["Gross", "Cost drag", "Net", "Benchmark"]
    values = [
        row["gross_total_return"] * 100,
        -row["gross_to_net_total_return_decay"] * 100,
        row["net_total_return"] * 100,
        row["net_benchmark_total_return"] * 100,
    ]
    colors = ["#2563eb", "#dc2626", "#111827", "#6b7280"]
    fig, ax = plt.subplots(figsize=(6.2, 2.8))
    ax.bar(labels, values, color=colors)
    ax.axhline(0, color="#111827", linewidth=0.8)
    ax.set_ylabel("% initial AUM")
    ax.set_title("Level 5 economics: gross performance and cost drag")
    fig.tight_layout()
    return fig


def _selected_name(level: str, row: pd.Series) -> str:
    if level == "level_1":
        return "SMA 30/100"
    for column in ("approach", "method", "policy"):
        if column in row:
            return VALUE_ALIASES.get(str(row[column]), str(row[column]))
    return VALUE_ALIASES["large_universe_dynamic"]
