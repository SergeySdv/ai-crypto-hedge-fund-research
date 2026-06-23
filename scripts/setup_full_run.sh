#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is not installed or not on PATH."
  echo "Install it from https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

if ! command -v make >/dev/null 2>&1; then
  echo "ERROR: make is not installed or not on PATH."
  exit 1
fi

echo "Repository: $ROOT_DIR"
echo "Installing locked Python environment..."
uv sync --frozen

echo "Checking Python version inside the project environment..."
uv run python - <<'PY'
import sys

if sys.version_info[:2] != (3, 11):
    raise SystemExit(f"ERROR: expected Python 3.11, got {sys.version.split()[0]}")
print(f"Python OK: {sys.version.split()[0]}")
PY

echo "Running full release verification..."
make release-verify

echo
echo "Full run complete. Main outputs:"
echo "- notebooks/ai_crypto_hedge_fund.ipynb"
echo "- reports/final_report.md"
echo "- presentation/AI Crypto Hedge Fund - Defense Deck.pdf"
echo "- artifacts/final_test/c33b5eb396f6/"
