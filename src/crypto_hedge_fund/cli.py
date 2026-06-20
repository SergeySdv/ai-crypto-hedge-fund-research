"""Minimal command line surface for stage-gated project automation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn

from crypto_hedge_fund.config import load_config
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

    for command in (
        "data",
        "validate-data",
        "experiments-val",
        "pretest-freeze",
        "notebook-fast",
        "notebook-full",
        "report",
        "presentation",
    ):
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
