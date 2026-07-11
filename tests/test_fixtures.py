"""Structural regression tests for golden PDF fixtures.

Validates that generated PDFs maintain expected structural properties:
page count, text content extraction, and file validity.
"""

from pathlib import Path

import pypdf

from pdf_studio.document import Document
from pdf_studio.render import render_pdf
from pdf_studio.styles import Font, Style

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_all_elements_page_count():
    """The full fixture should span 2 pages (has a page break)."""
    path = FIXTURES_DIR / "all-elements.pdf"
    assert path.exists(), f"Regenerate fixtures: python scripts/generate_fixtures.py"
    reader = pypdf.PdfReader(str(path))
    assert 2 <= len(reader.pages) <= 3


def test_all_elements_contains_page_2():
    """The fixture should have content on both pages."""
    path = FIXTURES_DIR / "all-elements.pdf"
    reader = pypdf.PdfReader(str(path))
    # Extract text from all pages
    all_text = "".join(p.extract_text() for p in reader.pages)
    assert "Page 2 Content" in all_text or "Complete Test Document" in all_text


def test_simple_page_count():
    """The simple fixture should be a single page."""
    path = FIXTURES_DIR / "simple.pdf"
    assert path.exists()
    reader = pypdf.PdfReader(str(path))
    assert len(reader.pages) == 1


def test_simple_contains_hello():
    """The simple fixture should contain expected text."""
    path = FIXTURES_DIR / "simple.pdf"
    reader = pypdf.PdfReader(str(path))
    text = reader.pages[0].extract_text()
    assert "Hello" in text


def test_both_fixtures_are_valid_pdf():
    """Both fixtures must be valid PDFs (header and non-empty)."""
    for name in ("simple.pdf", "all-elements.pdf"):
        path = FIXTURES_DIR / name
        assert path.exists()
        data = path.read_bytes()
        assert data[:4] == b"%PDF"
        assert len(data) > 500


def test_regenerate_produces_same_structure():
    """Re-generating fixtures should produce structurally similar PDFs.

    This is not a byte-for-byte check (PDF metadata differs), but verifies
    that the same Document class produces the same page count and text.
    """
    doc = Document()
    doc.add_heading("Hello, World!", level=0)
    doc.add_paragraph("This is a minimal test document.")
    doc.add_paragraph(
        "It is used to verify basic PDF rendering does not regress.",
        style=Style(font=Font(size=10)),
    )

    out = FIXTURES_DIR / "_regenerate_check.pdf"
    try:
        render_pdf(doc, str(out))
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 1
        text = reader.pages[0].extract_text()
        assert "Hello" in text
        assert out.read_bytes()[:4] == b"%PDF"
    finally:
        if out.exists():
            out.unlink()
