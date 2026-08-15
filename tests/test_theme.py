"""Tests for the Theme system and declarative templates (the pdf-studio moat)."""

from pathlib import Path

from pdf_studio.document import Document
from pdf_studio.themes import Theme
from pdf_studio.templates import build

TMP = Path("C:/Users/Ashay/AppData/Local/Temp")


def test_presets_are_distinct():
    a, b, c = Theme.cypher(), Theme.ledger(), Theme.slate()
    assert a.name == "cypher" and b.name == "ledger" and c.name == "slate"
    # Each preset carries a different foundation/accent pair.
    assert a.foundation != b.foundation != c.foundation
    assert a.accent != b.accent != c.accent


def test_get_resolves_name_and_default():
    assert Theme.get("ledger").name == "ledger"
    assert Theme.get("slate").name == "slate"
    assert Theme.get(None).name == "cypher"  # default
    assert Theme.get("unknown").name == "cypher"  # fallback


def test_document_accepts_theme_string():
    doc = Document(theme="ledger")
    assert doc.theme.name == "ledger"


def test_document_accepts_theme_object():
    doc = Document(theme=Theme.slate())
    assert doc.theme.name == "slate"


def test_document_default_theme_is_cypher():
    doc = Document()
    assert doc.theme.name == "cypher"


def test_financial_template_renders():
    data = {
        "title": "Q3 Portfolio",
        "subtitle": "Generated from template",
        "kpis": [
            {"label": "AUM", "value": "₹1.2L", "delta": "+4.1%"},
            {"label": "Returns", "value": "18.3%", "delta": "-1.2%"},
        ],
        "composition": (["Equity", "Cash", "ETF"], [60, 25, 15]),
        "table": [
            ["Holding", "Qty", "Value"],
            ["VEDL", "50", "₹4,500"],
            ["ITC", "20", "₹5,200"],
        ],
        "right_align_cols": [1, 2],
        "table_caption": "Positions",
    }
    doc = Document.from_template("financial_statement", data)
    out = TMP / "test_financial_template.pdf"
    doc.render(str(out))
    assert out.exists() and out.stat().st_size > 1000


def test_unknown_template_raises():
    try:
        build("nope", {})
        assert False, "expected ValueError"
    except ValueError:
        pass
