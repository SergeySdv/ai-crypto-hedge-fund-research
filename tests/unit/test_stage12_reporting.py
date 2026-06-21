from __future__ import annotations

from pathlib import Path

import nbformat

from crypto_hedge_fund.reporting import build_notebook, build_presentation, load_stage12_context
from crypto_hedge_fund.reporting.builders import _split_slides


def test_stage12_context_validates_accepted_final_artifacts() -> None:
    context = load_stage12_context()

    assert context.lock_hash == "dab407601cbaf8198361e5e3d074260546ed4bbab4c4be2555248b246631308b"
    assert context.suite_summary["final_test_exposure"] == "EXPOSED"
    assert context.level5_counts["eligible_count"] == 120
    assert context.level5_counts["scored_count"] == 120
    assert context.level5_counts["selected_count"] == 25
    assert len(context.selected_metrics) == 5


def test_notebook_builder_contains_required_level_headings() -> None:
    notebook_path = Path("notebooks/ai_crypto_hedge_fund.ipynb")
    original_notebook = notebook_path.read_bytes() if notebook_path.exists() else None
    try:
        generated_notebook_path = build_notebook(repo_root=".", smoke=True, execute=False)
        notebook = nbformat.read(generated_notebook_path, as_version=4)
    finally:
        if original_notebook is None:
            notebook_path.unlink(missing_ok=True)
        else:
            notebook_path.write_bytes(original_notebook)
    markdown = "\n".join(cell.source for cell in notebook.cells if cell.cell_type == "markdown")

    assert "Level 1 \u2014 Baseline Strategy for a Single Cryptocurrency." in markdown
    assert "Level 2 \u2014 Adding AI Agents, Econometrics and ML." in markdown
    assert "Level 3 \u2014 Portfolio Management on Historical Data" in markdown
    assert "Level 4 \u2014 Dynamic Portfolio Rebalancing." in markdown
    assert "Level 5 \u2014 Portfolio Expansion to 100+ Pairs." in markdown
    assert "FAST SMOKE - NON-FINAL CHECK" in markdown


def test_presentation_builder_writes_ten_or_fewer_slides() -> None:
    deck_path, pdf_path, page_count = build_presentation()

    assert deck_path.exists()
    assert pdf_path.exists()
    assert "short late-December 2024 Level 5 validation proof window" in deck_path.read_text(
        encoding="utf-8"
    )
    assert len(_split_slides(deck_path.read_text(encoding="utf-8"))) == 10
    assert page_count <= 10
