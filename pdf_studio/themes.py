"""Reusable visual languages for pdf-studio documents.

A Theme is the design-system-as-code: palette, typography roles, and chart
colours bundled into one object. Shipping themes turns the hardcoded brand
into a reusable asset — the actual moat over ReportLab (which makes you
configure everything) and WeasyPrint (which makes you write CSS).

All text-facing colours are WCAG-AA verified against white. `accent` is a
fill/bullet colour only (1.86:1 on white fails text AA), never used as text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Theme:
    """Brand system for a document.

    Roles (not raw colours) so charts/tables/headings stay consistent:
      foundation : deep structural colour (headings, table header)
      surface    : light card / zebra background
      body_text  : paragraph text
      muted_text : captions, KPI labels, axis ticks
      accent     : single confident highlight (fills, rules, bullets — not text)
      good / bad : semantic delta colours (KPI up/down)
      grid       : chart gridlines and table borders
      series     : ordered chart series palette
      h0/h1/h2   : heading colours by level
    """

    name: str = "cypher"
    foundation: str = "#0B1121"
    surface: str = "#F8FAFC"
    body_text: str = "#1F2937"
    muted_text: str = "#64748B"
    accent: str = "#2DD4BF"
    good: str = "#047857"
    bad: str = "#B91C1C"
    grid: str = "#E2E8F0"
    series: list[str] = field(
        default_factory=lambda: ["#1A3C6E", "#2DD4BF", "#0B1121", "#64748B", "#16A34A"]
    )
    h0: str = "#0B1121"
    h1: str = "#1A3C6E"
    h2: str = "#16213E"

    @classmethod
    def cypher(cls) -> "Theme":
        """Refined brand: navy foundation, teal accent. The default."""
        return cls(name="cypher")

    @classmethod
    def ledger(cls) -> "Theme":
        """Finance-optimized: deep-green foundation, gold semantic accent.

        Green carries growth/profit meaning (PlotSet), gold reads premium and
        pairs as a confident accent on green (FinanceAlliance). Three-part
        hierarchy: green structure, ice content, gold signal.
        """
        return cls(
            name="ledger",
            foundation="#064E3B",
            surface="#F0FDF4",
            body_text="#1F2937",
            muted_text="#6B7280",
            accent="#B45309",
            good="#047857",
            bad="#B91C1C",
            grid="#D1FAE5",
            series=["#064E3B", "#B45309", "#0F766E", "#6B7280", "#166534"],
            h0="#064E3B",
            h1="#064E3B",
            h2="#065F46",
        )

    @classmethod
    def slate(cls) -> "Theme":
        """Approachable: indigo-primary with amber accent (BethanyWorks

        'contemporary' pattern — indigo base + warm amber accent reads modern
        and warm without losing professionalism. Clearly distinct from the
        navy/teal brand theme.
        """
        return cls(
            name="slate",
            foundation="#312E81",
            surface="#EEF2FF",
            body_text="#334155",
            muted_text="#64748B",
            accent="#D97706",
            good="#047857",
            bad="#B91C1C",
            grid="#E0E7FF",
            series=["#312E81", "#D97706", "#0E7490", "#94A3B8", "#1E3A8A"],
            h0="#312E81",
            h1="#312E81",
            h2="#3730A3",
        )

    @classmethod
    def get(cls, name: Optional[str]) -> "Theme":
        """Resolve a preset by name, defaulting to cypher."""
        return {
            "cypher": cls.cypher,
            "ledger": cls.ledger,
            "slate": cls.slate,
        }.get(name or "cypher", cls.cypher)()
