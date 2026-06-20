"""CLI wrapper for the Stage 2 frozen-data validation gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from crypto_hedge_fund.data.validation import validate_data_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the included processed data bundle.")
    parser.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    args = parser.parse_args()
    result = validate_data_bundle(config_path=args.config)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
