"""Declarative report templates — data in, brand-consistent PDF out.

A template maps a structured dataset onto the Document element API. The caller
never touches a colour or font: theme + layout are encoded once, here.

Add a template by registering a builder in _REGISTRY and documenting it in the
from_template docstring. Builders return a fully populated Document.
"""

from __future__ import annotations

from typing import Callable

from .document import Document


def _financial_statement(data, theme=None) -> Document:
    """Build a one-page portfolio/financial statement.

    data: dict with keys
        title           : str
        subtitle        : str (optional)
        kpis            : list[dict]  (label, value, delta?)
        table           : list[list] or DataFrame  (rows of holdings/metrics)
        table_caption   : str (optional)
        right_align_cols: list[int] (optional)
        composition     : (labels, values) tuple (optional) -> donut
    """
    doc = Document(theme=theme)
    doc.add_heading(data.get("title", "Statement"), level=0)
    if data.get("subtitle"):
        doc.add_paragraph(data["subtitle"])
    if data.get("kpis"):
        doc.add_kpi_row(data["kpis"])
    if "composition" in data and data["composition"]:
        labels, values = data["composition"]
        doc.add_donut_chart(labels, values, title="Allocation")
    if data.get("table") is not None:
        doc.add_table(
            data["table"],
            caption=data.get("table_caption"),
            right_align_cols=data.get("right_align_cols"),
        )
    return doc


_REGISTRY: dict[str, Callable] = {
    "financial_statement": _financial_statement,
}


def build(name: str, data, **kwargs) -> Document:
    """Dispatch to a registered template builder."""
    if name not in _REGISTRY:
        raise ValueError(
            f"Unknown template '{name}'. Available: {', '.join(_REGISTRY)}"
        )
    # Theme may be passed positionally via kwargs from from_template.
    return _REGISTRY[name](data, **kwargs)
