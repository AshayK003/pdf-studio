"""Tests for pdf_studio.Document API."""

from pdf_studio.document import Document
from pdf_studio.styles import Style, Font


def test_add_heading_stores_element():
    doc = Document()
    doc.add_heading("Title", level=0)
    assert doc._elements[0] == ("heading", "Title", 0)


def test_add_paragraph_default_and_custom_style():
    doc = Document()
    doc.add_paragraph("hello")
    assert doc._elements[0][0] == "paragraph"
    assert doc._elements[0][1] == "hello"
    assert isinstance(doc._elements[0][2], Style)

    custom = Style(font=Font(size=14), alignment="center")
    doc.add_paragraph("world", style=custom)
    assert doc._elements[1][2] is custom


def test_add_table_list_and_dataframe():
    doc = Document()
    doc.add_table([["a", "b"], [1, 2]], caption="T")
    assert doc._elements[0][0] == "table"
    assert doc._elements[0][2] == "T"

    try:
        import pandas as pd
    except ImportError:
        return
    df = pd.DataFrame({"x": [1], "y": [2]})
    doc.add_table(df)
    assert doc._elements[1][0] == "table"


def test_add_chart_page_break_bullet_header():
    doc = Document()

    class FakeFig:
        pass

    doc.add_chart(FakeFig(), width=100, height=50)
    assert doc._elements[0][0] == "chart"
    assert doc._elements[0][2] == 100

    doc.add_page_break()
    assert doc._elements[1] == ("page_break",)

    doc.add_bullet("item")
    assert doc._elements[2][0] == "bullet"
    assert doc._elements[2][1] == "item"

    doc.set_header("Page {page} of {total}")
    assert doc._header == "Page {page} of {total}"
