from __future__ import annotations

from pathlib import Path

import nbformat
import pandas as pd

from crypto_hedge_fund.provenance import file_sha256
from crypto_hedge_fund.reporting import build_notebook, count_pdf_pages, load_stage12_context
from crypto_hedge_fund.reporting.notebook_display import show_frame


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


def test_show_frame_has_deterministic_notebook_representations() -> None:
    frame = pd.DataFrame([{"Metric": "Final-test lock", "Value": "abc123"}])

    first = show_frame(frame, caption="Notebook execution context")
    second = show_frame(frame, caption="Notebook execution context")

    assert first._repr_html_() == second._repr_html_()
    assert "0x" not in repr(first)
    assert "#T_" in first._repr_html_()


def test_committed_final_presentation_pdf_is_release_artifact() -> None:
    pdf_path = Path("presentation/AI Crypto Hedge Fund - Defense Deck.pdf")

    assert pdf_path.exists()
    assert count_pdf_pages(pdf_path) == 10
    assert not Path("presentation/deck.md").exists()
    assert not Path("presentation/deck.pdf").exists()
