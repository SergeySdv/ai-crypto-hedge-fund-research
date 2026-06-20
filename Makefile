.PHONY: setup data validate-data lint test experiments-val pretest-freeze final-test notebook-fast notebook-full report presentation all-fast

setup:
	uv sync --frozen

data:
	uv run crypto-hedge-fund data

validate-data:
	uv run crypto-hedge-fund validate-data

lint:
	uv run ruff format --check .
	uv run ruff check .

test:
	uv run pytest

experiments-val:
	uv run crypto-hedge-fund experiments-val

pretest-freeze:
	uv run crypto-hedge-fund pretest-freeze

final-test:
	uv run crypto-hedge-fund final-test

notebook-fast:
	uv run crypto-hedge-fund notebook-fast

notebook-full:
	uv run crypto-hedge-fund notebook-full

report:
	uv run crypto-hedge-fund report

presentation:
	uv run crypto-hedge-fund presentation

all-fast: lint test
	uv run python -c "import crypto_hedge_fund"
