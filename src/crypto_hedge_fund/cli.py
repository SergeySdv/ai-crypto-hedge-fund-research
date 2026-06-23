"""Minimal command line surface for stage-gated project automation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

from crypto_hedge_fund.config import load_config
from crypto_hedge_fund.data.download import freeze_data
from crypto_hedge_fund.data.validation import (
    DataValidationError,
    generate_data_proof,
    validate_data_bundle,
)
from crypto_hedge_fund.experiments import (
    run_level_1_validation,
    run_level_2_validation,
    run_level_3_validation,
    run_level_4_validation,
    run_level_5_validation,
)
from crypto_hedge_fund.experiments.final_test import run_frozen_final_test
from crypto_hedge_fund.pretest_lock import (
    FinalTestLockValidationError,
    PretestFreezeError,
    run_pretest_freeze,
    validate_final_test_lock,
)
from crypto_hedge_fund.provenance import canonical_config_hash, file_sha256, git_commit
from crypto_hedge_fund.reporting import (
    build_notebook,
    count_pdf_pages,
    load_stage12_context,
)

PRESENTATION_PDF_PATH = Path("presentation/AI Crypto Hedge Fund - Defense Deck.pdf")


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


def _cmd_generate_data_proof(args: argparse.Namespace) -> int:
    try:
        result = generate_data_proof(config_path=args.config)
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


def _cmd_final_test(args: argparse.Namespace) -> int:
    try:
        result = run_frozen_final_test(config_path=args.config)
    except FinalTestLockValidationError as exc:
        _fail_closed(str(exc))
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _cmd_pretest_freeze(args: argparse.Namespace) -> int:
    try:
        result = run_pretest_freeze(config_path=args.config)
    except PretestFreezeError as exc:
        _fail_closed(str(exc))
    payload = {
        "validation_selected_path": str(result.validation_selected_path),
        "validation_selected_sha256": result.validation_selected_sha256,
        "final_test_lock_path": str(result.final_test_lock_path),
        "final_test_lock_sha256": result.final_test_lock_sha256,
        "metadata_path": str(result.metadata_path),
        "final_test_exposure_state": result.final_test_exposure_state,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_notebook_fast(_args: argparse.Namespace) -> int:
    path = build_notebook(smoke=True, execute=True)
    context = load_stage12_context()
    payload = {
        "mode": "FAST_SMOKE_NON_FINAL",
        "notebook_path": str(path),
        "executed": True,
        "final_test_lock_sha256": context.lock_hash,
        "level_5_counts": context.level5_counts,
        "note": "Smoke notebook is non-final; run make notebook-full for final executed outputs.",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_notebook_full(_args: argparse.Namespace) -> int:
    path = build_notebook(smoke=False, execute=True)
    notebook_stats = _notebook_stats(path)
    context = load_stage12_context()
    payload = {
        "mode": "FULL_FINAL_NOTEBOOK",
        "notebook_path": str(path),
        "executed": True,
        "execution_mode": "persisted_clean_subprocess_outputs",
        "cell_count": notebook_stats["cell_count"],
        "code_cell_count": notebook_stats["code_cell_count"],
        "executed_code_cell_count": notebook_stats["executed_code_cell_count"],
        "final_test_lock_sha256": context.lock_hash,
        "final_test_exposure": context.suite_summary["final_test_exposure"],
        "level_5_counts": context.level5_counts,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _notebook_stats(path: Path) -> dict[str, int]:
    import nbformat

    notebook = nbformat.read(path, as_version=4)
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    executed_code_cells = [
        cell
        for cell in code_cells
        if cell.execution_count is not None and bool(getattr(cell, "outputs", []))
    ]
    return {
        "cell_count": len(notebook.cells),
        "code_cell_count": len(code_cells),
        "executed_code_cell_count": len(executed_code_cells),
    }


def _cmd_report(_args: argparse.Namespace) -> int:
    path = Path("reports/final_report.md")
    if not path.exists():
        _fail_closed(f"missing final report: {path}")
    context = load_stage12_context()
    report_text = path.read_text(encoding="utf-8")
    required_markers = (
        context.lock_hash,
        "does not establish robust alpha",
        "final-test full run scored 120 pairs",
    )
    missing = [marker for marker in required_markers if marker not in report_text]
    if missing:
        _fail_closed(f"final report is missing required release markers: {missing}")
    payload = {
        "report_path": str(path),
        "verification_mode": "read_only_existing_deliverable",
        "final_test_lock_sha256": context.lock_hash,
        "final_test_exposure": context.suite_summary["final_test_exposure"],
        "level_5_counts": context.level5_counts,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_presentation(_args: argparse.Namespace) -> int:
    pdf_path = PRESENTATION_PDF_PATH
    if not pdf_path.exists():
        _fail_closed(f"missing presentation PDF: {pdf_path}")
    page_count = count_pdf_pages(pdf_path)
    if page_count > 10:
        _fail_closed(f"{pdf_path} has {page_count} pages; maximum is 10")
    context = load_stage12_context()
    payload = {
        "pdf_path": str(pdf_path),
        "verification_mode": "read_only_existing_deliverable",
        "pdf_page_count": page_count,
        "independent_pdf_page_count": count_pdf_pages(pdf_path),
        "final_test_lock_sha256": context.lock_hash,
        "level_5_counts": context.level5_counts,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_hash_file(args: argparse.Namespace) -> int:
    print(file_sha256(args.path))
    return 0


def _cmd_pdf_page_count(args: argparse.Namespace) -> int:
    page_count = count_pdf_pages(args.path)
    payload = {
        "pdf_path": str(args.path),
        "pdf_page_count": page_count,
        "maximum_allowed_pages": args.max_pages,
        "status": "pass" if page_count <= args.max_pages else "fail",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if page_count > args.max_pages:
        return 1
    return 0


def _cmd_verify_final_lock(args: argparse.Namespace) -> int:
    try:
        result = validate_final_test_lock(config_path=args.config)
    except FinalTestLockValidationError as exc:
        _fail_closed(str(exc))
    payload = {
        "final_test_lock_path": str(result.lock_path),
        "metadata_path": str(result.metadata_path),
        "final_test_lock_sha256": result.final_test_lock_sha256,
        "validation_selected_sha256": result.validation_selected_sha256,
        "validation_artifact_count": result.validation_artifact_count,
        "data_pair_count_proof_sha256": result.data_pair_count_proof_sha256,
        "final_test_exposure_state": result.final_test_exposure_state,
        "status": "pass",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _execute_notebook_read_only(path: Path) -> dict[str, int]:
    import nbformat

    root = Path(".").resolve()
    notebook = nbformat.read(path, as_version=4)
    code_cells = [cell.source for cell in notebook.cells if cell.cell_type == "code"]
    script = _notebook_execution_script(code_cells)
    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = Path(temp_dir) / "execute_notebook.py"
        script_path.write_text(script, encoding="utf-8")
        result = subprocess.run(
            [str(_project_python(root)), str(script_path)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            timeout=1200,
        )
    if result.returncode != 0:
        _fail_closed(
            "notebook read-only execution failed\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return {
        "cell_count": len(notebook.cells),
        "code_cell_count": len(code_cells),
        "executed_code_cell_count": len(code_cells),
    }


def _project_python(root: Path) -> Path:
    for relative in (".venv/bin/python3", ".venv/bin/python"):
        candidate = root / relative
        if candidate.exists():
            return candidate
    return Path(sys.executable)


def _notebook_execution_script(code_cells: list[str]) -> str:
    encoded = json.dumps(code_cells)
    return (
        "import json\n"
        "import traceback\n\n"
        f"cells = json.loads({encoded!r})\n"
        "namespace = {}\n"
        "for index, source in enumerate(cells):\n"
        '    print(f"@@CELL_START {index}@@")\n'
        "    try:\n"
        '        exec(compile(source, f"<notebook-cell-{index}>", "exec"), namespace)\n'
        "    except Exception:\n"
        "        traceback.print_exc()\n"
        "        raise\n"
        "    finally:\n"
        '        print(f"@@CELL_END {index}@@")\n'
    )


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

    pdf_page_count = subparsers.add_parser("pdf-page-count", help="Verify PDF page count.")
    pdf_page_count.add_argument("path", type=Path)
    pdf_page_count.add_argument("--max-pages", type=int, default=10)
    pdf_page_count.set_defaults(func=_cmd_pdf_page_count)

    data = subparsers.add_parser("data", help="Download/freeze configured public OHLCV data.")
    data.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    data.add_argument("--max-symbols", type=int, default=None)
    data.set_defaults(func=_cmd_data)

    validate_data = subparsers.add_parser(
        "validate-data", help="Validate included OHLCV data and universe proof."
    )
    validate_data.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    validate_data.set_defaults(func=_cmd_validate_data)

    generate_data_proof_parser = subparsers.add_parser(
        "generate-data-proof",
        help="Generate the canonical data proof before final-test lock/exposure.",
    )
    generate_data_proof_parser.add_argument(
        "--config", type=Path, default=Path("configs/default.yaml")
    )
    generate_data_proof_parser.set_defaults(func=_cmd_generate_data_proof)

    experiments_val = subparsers.add_parser(
        "experiments-val",
        help="Run validation-only experiments implemented so far.",
    )
    experiments_val.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    experiments_val.add_argument("--artifacts-dir", type=Path, default=None)
    experiments_val.set_defaults(func=_cmd_experiments_val)

    pretest_freeze = subparsers.add_parser(
        "pretest-freeze", help="Freeze validation-selected methodology before final test."
    )
    pretest_freeze.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    pretest_freeze.set_defaults(func=_cmd_pretest_freeze)

    verify_final_lock = subparsers.add_parser(
        "verify-final-lock",
        help="Validate the accepted final-test lock without running final-test.",
    )
    verify_final_lock.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    verify_final_lock.set_defaults(func=_cmd_verify_final_lock)

    notebook_fast = subparsers.add_parser(
        "notebook-fast", help="Run a clearly labeled non-final notebook smoke execution."
    )
    notebook_fast.set_defaults(func=_cmd_notebook_fast)

    notebook_full = subparsers.add_parser(
        "notebook-full", help="Build and execute the final reviewer notebook."
    )
    notebook_full.set_defaults(func=_cmd_notebook_full)

    report = subparsers.add_parser("report", help="Write reports/final_report.md.")
    report.set_defaults(func=_cmd_report)

    presentation = subparsers.add_parser(
        "presentation", help="Verify the committed final presentation PDF."
    )
    presentation.set_defaults(func=_cmd_presentation)

    final_test = subparsers.add_parser("final-test", help="Run frozen final-test suite.")
    final_test.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    final_test.set_defaults(func=_cmd_final_test)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
