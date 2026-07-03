from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Font:
    """A font specification.

    family: Inter, Lora, or JetBrains Mono (bundled). Supply your own TTF name too.
    size: point size.
    bold, italic: style flags.
    color: hex string like "#1a1a1a".
    """

    family: str = "Inter"
    size: float = 11
    bold: bool = False
    italic: bool = False
    color: str = "#1a1a1a"


@dataclass
class Style:
    """A paragraph or heading style.

    font: Font specification.
    leading: line-height multiplier (1.4 = 140% of font size).
    alignment: "left", "center", "right", or "justify".
    space_before / space_after: spacing in points.
    """

    font: Font | None = None
    leading: float = 1.4
    alignment: str = "left"
    space_before: float = 0
    space_after: float = 6


def _default_style() -> Style:
    return Style(font=Font())
