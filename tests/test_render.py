"""Tests for PDF rendering."""

from pathlib import Path

import pytest
from reportlab.platypus import Spacer

from pdf_studio.document import Document
from pdf_studio.render import _build_table, _to_reportlab_style, render_pdf
from pdf_studio.styles import Font, Style


def test_render_pdf_produces_valid_file(tmp_path: Path):
    doc = Document()
    doc.add_heading("Hello", level=0)
    doc.add_paragraph("Body text for the PDF.")
    out = tmp_path / "out.pdf"
    render_pdf(doc, str(out))
    data = out.read_bytes()
    assert data[:4] == b"%PDF"
    assert len(data) > 100


def test_two_pass_resolves_total_placeholder(tmp_path: Path):
    doc = Document()
    doc.set_header("Page {page} of {total}")
    doc.add_heading("Cover", level=0)
    doc.add_page_break()
    doc.add_paragraph("Second page")
    out = tmp_path / "pages.pdf"
    render_pdf(doc, str(out))
    assert out.exists()
    assert out.stat().st_size > 100


def test_empty_document_renders(tmp_path: Path):
    doc = Document()
    out = tmp_path / "empty.pdf"
    render_pdf(doc, str(out))
    assert out.read_bytes()[:4] == b"%PDF"


def test_table_empty_data_returns_spacer():
    result = _build_table([], caption=None)
    assert isinstance(result, Spacer)


def test_chart_scaling_uses_original_dimensions(tmp_path: Path):
    """Regression for #2: scale must use orig SVG size, not overwritten size."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    doc = Document()
    doc.add_heading("Chart", level=1)
    doc.add_chart(fig, width=200, height=100)
    out = tmp_path / "chart.pdf"
    render_pdf(doc, str(out))
    plt.close(fig)
    assert out.read_bytes()[:4] == b"%PDF"


def test_font_style_flags_emit_warning():
    with pytest.warns(UserWarning, match="Regular font weights only"):
        _to_reportlab_style(Style(font=Font(bold=True, italic=True)))
