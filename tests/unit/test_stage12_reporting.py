from __future__ import annotations

from pathlib import Path

import nbformat

from crypto_hedge_fund.provenance import file_sha256
from crypto_hedge_fund.reporting import build_notebook, build_presentation, load_stage12_context
from crypto_hedge_fund.reporting.builders import _split_slides


def test_stage12_context_validates_accepted_final_artifacts() -> None:
    context = load_stage12_context()

    assert context.lock_hash == file_sha256(Path("artifacts/final_test_lock.json"))
    assert context.final_dir == Path("artifacts/final_test", context.lock_hash[:12]).resolve()
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
    expected_deck_path = Path("presentation/deck.md")
    expected_pdf_path = Path("presentation/deck.pdf")
    original_deck = expected_deck_path.read_bytes() if expected_deck_path.exists() else None
    original_pdf = expected_pdf_path.read_bytes() if expected_pdf_path.exists() else None
    try:
        deck_path, pdf_path, page_count = build_presentation()
        generated_deck = deck_path.read_text(encoding="utf-8")
    finally:
        if original_deck is None:
            expected_deck_path.unlink(missing_ok=True)
        else:
            expected_deck_path.write_bytes(original_deck)
        if original_pdf is None:
            expected_pdf_path.unlink(missing_ok=True)
        else:
            expected_pdf_path.write_bytes(original_pdf)

    assert deck_path.exists()
    assert pdf_path.exists()
    assert "short late-December 2024 Level 5 validation proof window" in generated_deck
    assert len(_split_slides(generated_deck)) == 10
    assert page_count <= 10
