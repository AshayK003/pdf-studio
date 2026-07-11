"""Generate golden PDF fixtures for structural regression testing.

Usage:
    python scripts/generate_fixtures.py

Output:
    tests/fixtures/all-elements.pdf  - document with every element type
    tests/fixtures/simple.pdf        - minimal document (heading + paragraph)
"""

from pathlib import Path

from pdf_studio.document import Document
from pdf_studio.render import render_pdf
from pdf_studio.styles import Font, Style

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def generate_all_elements() -> None:
    """Generate a PDF that exercises every element type."""
    doc = Document()
    doc.set_header("Page {page} of {total}")
    doc.add_heading("Complete Test Document", level=0)
    doc.add_paragraph(
        "This document exercises every element type for structural regression testing."
    )
    doc.add_heading("Headings", level=1)
    doc.add_heading("Level 2 Heading", level=2)
    doc.add_heading("Level 3 Heading", level=3)

    doc.add_heading("Paragraphs", level=1)
    doc.add_paragraph("Default paragraph with standard styling.")
    doc.add_paragraph("Right-aligned paragraph.", style=Style(alignment="right"))

    doc.add_heading("Tables", level=1)
    doc.add_table(
        [["Name", "Value"], ["Alpha", 100], ["Beta", 200], ["Gamma", 300]],
        caption="Sample Table",
    )

    doc.add_heading("Bullets", level=1)
    doc.add_bullet("First bullet item")
    doc.add_bullet("Second bullet item")
    doc.add_bullet("Third bullet item")

    doc.add_page_break()
    doc.add_heading("Page 2 Content", level=1)
    doc.add_paragraph("This content should appear on a new page.")

    out_path = FIXTURES_DIR / "all-elements.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    render_pdf(doc, str(out_path))
    print(f"Generated {out_path}")


def generate_simple() -> None:
    """Generate a minimal PDF with just a heading and paragraph."""
    doc = Document()
    doc.add_heading("Hello, World!", level=0)
    doc.add_paragraph("This is a minimal test document.")
    doc.add_paragraph(
        "It is used to verify basic PDF rendering does not regress.",
        style=Style(font=Font(size=10)),
    )

    out_path = FIXTURES_DIR / "simple.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    render_pdf(doc, str(out_path))
    print(f"Generated {out_path}")


if __name__ == "__main__":
    generate_all_elements()
    generate_simple()
    print("Done.")
