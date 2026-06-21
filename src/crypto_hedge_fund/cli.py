"""Minimal command line surface for stage-gated project automation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn

from crypto_hedge_fund.config import load_config
from crypto_hedge_fund.data.download import freeze_data
from crypto_hedge_fund.data.validation import DataValidationError, validate_data_bundle
from crypto_hedge_fund.experiments import (
    run_level_1_validation,
    run_level_2_validation,
    run_level_3_validation,
    run_level_4_validation,
    run_level_5_validation,
)
from crypto_hedge_fund.provenance import canonical_config_hash, file_sha256, git_commit


def _fail_closed(message: str) -> NoReturn:
    print(f"FAIL CLOSED: {message}", file=sys.stderr)
    raise SystemExit(2)


def _cmd_config_hash(args: argparse.Namespace) -> int:
    config = load_config(
        overlay_path=Path("configs/fast.yaml") if args.fast else None,
        resolve_paths=False,
    )
    print(canonical_config_hash(config))
    return 0


def _cmd_status(_args: argparse.Namespace) -> int:
    payload = {
        "package": "crypto_hedge_fund",
        "git_commit": git_commit(),
        "default_config_hash": canonical_config_hash(load_config(resolve_paths=False)),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_data(args: argparse.Namespace) -> int:
    manifest = freeze_data(config_path=args.config, max_symbols=args.max_symbols)
    payload = {
        "exchange": manifest["source"]["exchange"],
        "row_count": manifest["row_count"],
        "symbol_count": manifest["symbol_count"],
        "min_bar_start_utc": manifest["actual_min_bar_start_utc"],
        "max_bar_start_utc": manifest["actual_max_bar_start_utc"],
        "file_sha256": manifest["file_sha256"],
        "instrument_sha256": manifest["instrument_sha256"],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_validate_data(args: argparse.Namespace) -> int:
    try:
        result = validate_data_bundle(config_path=args.config)
    except DataValidationError as exc:
        _fail_closed(str(exc))
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _cmd_experiments_val(args: argparse.Namespace) -> int:
    effective_config = load_config(args.config, resolve_paths=True)
    level1 = run_level_1_validation(
        config_path=args.config,
        artifacts_dir=args.artifacts_dir,
    )
    level2 = (
        run_level_2_validation(
            config_path=args.config,
            artifacts_dir=args.artifacts_dir,
        )
        if "level_2" in effective_config
        else None
    )
    level3 = (
        run_level_3_validation(
            config_path=args.config,
            artifacts_dir=args.artifacts_dir,
        )
        if "level_3" in effective_config
        else None
    )
    level4 = (
        run_level_4_validation(
            config_path=args.config,
            artifacts_dir=args.artifacts_dir,
        )
        if "level_4" in effective_config
        else None
    )
    level5 = (
        run_level_5_validation(
            config_path=args.config,
            artifacts_dir=args.artifacts_dir,
        )
        if "level_5" in effective_config
        else None
    )
    payload = {
        "levels": [
            "level_1",
            *([] if level2 is None else ["level_2"]),
            *([] if level3 is None else ["level_3"]),
            *([] if level4 is None else ["level_4"]),
            *([] if level5 is None else ["level_5"]),
        ],
        "split": "validation",
        "metrics_path": str(level1.artifact_paths["metrics"]),
        "equity_path": str(level1.artifact_paths["equity"]),
        "weights_path": str(level1.artifact_paths["weights"]),
        "orders_path": str(level1.artifact_paths["orders"]),
        "fills_path": str(level1.artifact_paths["fills"]),
        "figure_path": str(level1.figure_path),
        "trace_path": str(level1.trace_path),
        "selected_fast_window": level1.selected_fast_window,
        "selected_slow_window": level1.selected_slow_window,
        "net_roi": level1.metrics["net_roi"],
        "net_sharpe": level1.metrics["net_sharpe"],
        "net_max_drawdown": level1.metrics["net_max_drawdown"],
        "level_1": {
            "selected_fast_window": level1.selected_fast_window,
            "selected_slow_window": level1.selected_slow_window,
            "metrics_path": str(level1.artifact_paths["metrics"]),
            "equity_path": str(level1.artifact_paths["equity"]),
            "weights_path": str(level1.artifact_paths["weights"]),
            "orders_path": str(level1.artifact_paths["orders"]),
            "fills_path": str(level1.artifact_paths["fills"]),
            "figure_path": str(level1.figure_path),
            "trace_path": str(level1.trace_path),
            "net_roi": level1.metrics["net_roi"],
            "net_sharpe": level1.metrics["net_sharpe"],
            "net_max_drawdown": level1.metrics["net_max_drawdown"],
        },
        "level_2": None
        if level2 is None
        else {
            "selected_approach": level2.selected_approach,
            "metrics_path": str(level2.artifact_paths["metrics"]),
            "equity_path": str(level2.artifact_paths["equity"]),
            "weights_path": str(level2.artifact_paths["weights"]),
            "orders_path": str(level2.artifact_paths["orders"]),
            "fills_path": str(level2.artifact_paths["fills"]),
            "figure_path": str(level2.figure_path),
            "trace_path": str(level2.trace_path),
            "robustness_path": str(level2.robustness_path),
        },
        "level_3": None
        if level3 is None
        else {
            "selected_method": level3.selected_method,
            "symbols": list(level3.symbols),
            "estimation_start": level3.estimation_start.isoformat(),
            "estimation_end": level3.estimation_end.isoformat(),
            "metrics_path": str(level3.artifact_paths["metrics"]),
            "equity_path": str(level3.artifact_paths["equity"]),
            "weights_path": str(level3.artifact_paths["weights"]),
            "orders_path": str(level3.artifact_paths["orders"]),
            "fills_path": str(level3.artifact_paths["fills"]),
            "figure_path": str(level3.figure_path),
            "trace_path": str(level3.trace_path),
            "universe_path": str(level3.universe_path),
            "final_vintage_plan_path": None
            if level3.final_vintage_plan_path is None
            else str(level3.final_vintage_plan_path),
        },
        "level_4": None
        if level4 is None
        else {
            "selected_policy": level4.selected_policy,
            "symbols": list(level4.symbols),
            "metrics_path": str(level4.artifact_paths["metrics"]),
            "equity_path": str(level4.artifact_paths["equity"]),
            "weights_path": str(level4.artifact_paths["weights"]),
            "orders_path": str(level4.artifact_paths["orders"]),
            "fills_path": str(level4.artifact_paths["fills"]),
            "figure_path": str(level4.figure_path),
            "trace_path": str(level4.trace_path),
            "rebalance_log_path": str(level4.rebalance_log_path),
            "final_vintage_plan_path": None
            if level4.final_vintage_plan_path is None
            else str(level4.final_vintage_plan_path),
        },
        "level_5": None
        if level5 is None
        else {
            "scored_count": level5.scored_count,
            "selected_count": level5.selected_count,
            "metrics_path": str(level5.artifact_paths["metrics"]),
            "equity_path": str(level5.artifact_paths["equity"]),
            "weights_path": str(level5.artifact_paths["weights"]),
            "orders_path": str(level5.artifact_paths["orders"]),
            "fills_path": str(level5.artifact_paths["fills"]),
            "figure_path": str(level5.figure_path),
            "pair_count_proof_path": str(level5.pair_count_proof_path),
            "universe_scores_path": str(level5.universe_scores_path),
            "rebalance_log_path": str(level5.rebalance_log_path),
            "decision_trace_path": str(level5.decision_trace_path),
            "health_summary_path": str(level5.health_summary_path),
            "alerts_path": str(level5.alerts_path),
        },
        "final_test_exposure": "NOT_EXPOSED",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_future_stage(args: argparse.Namespace) -> NoReturn:
    _fail_closed(
        f"`{args.command}` is reserved for a later stage and is not implemented in Stage 1."
    )


def _cmd_final_test(args: argparse.Namespace) -> NoReturn:
    config = load_config(resolve_paths=True)
    lock_path = Path(config["final_test"]["lock_path"])
    if not lock_path.is_absolute():
        lock_path = Path.cwd() / lock_path
    if not lock_path.exists():
        _fail_closed(
            "`make final-test` requires artifacts/final_test_lock.json. "
            "Run the validation-only stages and pretest freeze first."
        )
    _fail_closed(
        f"`{args.command}` found lock {lock_path} but the frozen final-test runner "
        "is not implemented until later stages."
    )


def _cmd_hash_file(args: argparse.Namespace) -> int:
    print(file_sha256(args.path))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="crypto-hedge-fund")
    subparsers = parser.add_subparsers(dest="command", required=True)

    config_hash = subparsers.add_parser("config-hash", help="Print the effective config hash.")
    config_hash.add_argument("--fast", action="store_true", help="Apply configs/fast.yaml overlay.")
    config_hash.set_defaults(func=_cmd_config_hash)

    status = subparsers.add_parser("status", help="Print Stage 1 package provenance.")
    status.set_defaults(func=_cmd_status)

    hash_file = subparsers.add_parser("hash-file", help="Print a file SHA-256 digest.")
    hash_file.add_argument("path", type=Path)
    hash_file.set_defaults(func=_cmd_hash_file)

    data = subparsers.add_parser("data", help="Download/freeze configured public OHLCV data.")
    data.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    data.add_argument("--max-symbols", type=int, default=None)
    data.set_defaults(func=_cmd_data)

    validate_data = subparsers.add_parser(
        "validate-data", help="Validate included OHLCV data and universe proof."
    )
    validate_data.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    validate_data.set_defaults(func=_cmd_validate_data)

    experiments_val = subparsers.add_parser(
        "experiments-val",
        help="Run validation-only experiments implemented so far.",
    )
    experiments_val.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    experiments_val.add_argument("--artifacts-dir", type=Path, default=None)
    experiments_val.set_defaults(func=_cmd_experiments_val)

    for command in ("pretest-freeze", "notebook-fast", "notebook-full", "report", "presentation"):
        future = subparsers.add_parser(command, help="Later-stage command placeholder.")
        future.set_defaults(func=_cmd_future_stage)

    final_test = subparsers.add_parser("final-test", help="Run frozen final-test suite.")
    final_test.set_defaults(func=_cmd_final_test)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
