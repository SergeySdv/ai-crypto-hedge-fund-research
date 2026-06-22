.PHONY: setup data generate-data-proof validate-data lint test experiments-val pretest-freeze final-test notebook-fast notebook-full report presentation verify-final-lock pdf-page-count release-verify all-fast

setup:
	uv sync --frozen

data:
	uv run crypto-hedge-fund data

generate-data-proof:
	uv run crypto-hedge-fund generate-data-proof

validate-data:
	uv run crypto-hedge-fund validate-data

lint:
	uv run ruff format --check .
	uv run ruff check .
	uv run python -m compileall -q src tests
	uv run python scripts/check_file_size.py
	uv run radon cc src -nc

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

verify-final-lock:
	uv run crypto-hedge-fund verify-final-lock

pdf-page-count:
	uv run crypto-hedge-fund pdf-page-count presentation/deck.pdf --max-pages 10

release-verify:
	uv sync --frozen
	$(MAKE) validate-data
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) notebook-full
	$(MAKE) report
	$(MAKE) presentation
	$(MAKE) verify-final-lock
	$(MAKE) pdf-page-count
	git diff --exit-code

all-fast: lint test
	uv run python -c "import crypto_hedge_fund"
