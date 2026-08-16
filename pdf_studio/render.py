"""PDF rendering engine for pdf-studio.

Converts the Document model into ReportLab flowables and builds the final PDF.
"""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from threading import Lock

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.styles import ParagraphStyle

from .styles import Font, Style

# Bundled font name → (filename, bold, italic). Registering each weight/style
# as its own named font lets us resolve bold/italic to a real TTF instead of
# silently rendering regular weight. Add new fonts here when bundled.
_BUILTIN_FONTS: dict[str, tuple[str, bool, bool]] = {
    "Inter": ("Inter-Regular.ttf", False, False),
    "Inter-Bold": ("Inter-Bold.ttf", True, False),
    "Lora": ("Lora-Regular.ttf", False, False),
    "Lora-Bold": ("Lora-Bold.ttf", True, False),
    "Lora-Italic": ("Lora-Italic.ttf", False, True),
    "JetBrainsMono": ("JetBrainsMono-Regular.ttf", False, False),
    "JetBrainsMono-Bold": ("JetBrainsMono-Bold.ttf", True, False),
}

_FONTS_REGISTERED = False  # global flag for one-time font registration
_FONT_REGISTRATION_LOCK = Lock()


def _register_fonts() -> None:
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return

    with _FONT_REGISTRATION_LOCK:
        if _FONTS_REGISTERED:
            return

        from reportlab.lib.fonts import addMapping
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        fonts_dir = Path(__file__).parent / "fonts"

        for registered_name, (filename, _bold, _italic) in _BUILTIN_FONTS.items():
            ttf_path = fonts_dir / filename
            if not ttf_path.exists():
                continue
            pdfmetrics.registerFont(TTFont(registered_name, str(ttf_path)))

        # Map family + weight/style combos so inline <b>/<i> tags resolve.
        addMapping("Inter", 0, 0, "Inter")
        addMapping("Inter", 1, 0, "Inter-Bold")
        addMapping("Inter", 0, 1, "Inter")
        addMapping("Inter", 1, 1, "Inter-Bold")
        addMapping("Lora", 0, 0, "Lora")
        addMapping("Lora", 1, 0, "Lora-Bold")
        addMapping("Lora", 0, 1, "Lora-Italic")
        addMapping("Lora", 1, 1, "Lora-Bold")
        addMapping("JetBrainsMono", 0, 0, "JetBrainsMono")
        addMapping("JetBrainsMono", 1, 0, "JetBrainsMono-Bold")
        addMapping("JetBrainsMono", 0, 1, "JetBrainsMono")
        addMapping("JetBrainsMono", 1, 1, "JetBrainsMono-Bold")

        _FONTS_REGISTERED = True


def _resolve_font_name(family: str, bold: bool, italic: bool) -> str:
    """Map a base family + style flags to a registered font name."""
    fam = family or "Inter"
    if fam == "Inter":
        return "Inter-Bold" if bold else "Inter"
    if fam == "Lora":
        # No bundled Lora-BoldItalic; bold wins over italic.
        if bold:
            return "Lora-Bold"
        if italic:
            return "Lora-Italic"
        return "Lora"
    if fam == "JetBrainsMono":
        return "JetBrainsMono-Bold" if bold else "JetBrainsMono"
    return fam  # caller-supplied custom TTF name


def _to_reportlab_style(style: Style) -> ParagraphStyle:
    """Convert our Style dataclass to a ReportLab ParagraphStyle."""
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

    align_map = {
        "left": TA_LEFT,
        "center": TA_CENTER,
        "right": TA_RIGHT,
        "justify": TA_JUSTIFY,
    }
    font = style.font or Font()
    # Real bold/italic weights are bundled; resolve to the right TTF.
    font_name = _resolve_font_name(font.family, font.bold, font.italic)

    return ParagraphStyle(
        "UserStyle",
        fontName=font_name,
        fontSize=font.size,
        leading=font.size * style.leading,
        alignment=align_map.get(style.alignment, TA_LEFT),
        spaceBefore=style.space_before,
        spaceAfter=style.space_after,
        textColor=_parse_color(font.color),
    )


def _heading_style(level: int, theme) -> ParagraphStyle:
    """Return a ReportLab ParagraphStyle sized by heading level.

    Brand display hierarchy: Lora Bold with a navy palette and tight leading.
    Colours come from the active Theme. Levels 1–2 get a teal hairline rule
    (added in _build_story).
    """
    sizes = {0: 24, 1: 18, 2: 14, 3: 12}
    colors_by_level = {
        0: theme.h0,
        1: theme.h1,
        2: theme.h2,
        3: theme.body_text,
    }
    size = sizes.get(level, 12)
    color = colors_by_level.get(level, theme.body_text)
    return ParagraphStyle(
        f"Heading{level}",
        fontName="Lora-Bold",
        fontSize=size,
        leading=size * 1.15,
        spaceBefore=16 if level else 4,
        spaceAfter=10,
        textColor=HexColor(color),
    )


def _parse_color(hex_str: str) -> Color:
    """Parse a hex colour string like '#1a1a1a' into a ReportLab Color object."""
    if re.fullmatch(r"#[0-9a-fA-F]{6}", hex_str) is None:
        raise ValueError(f"Invalid hex color: {hex_str!r}")

    try:
        return HexColor(hex_str)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid hex color: {hex_str!r}") from exc


def _build_table(data, caption: str | None, right_align_cols: list[int] | None = None, theme=None, available_width=None):
    """Convert data (DataFrame or list[list]) into a ReportLab Table flowable.

    Cell text is wrapped in Paragraphs so long content wraps instead of
    overflowing or clipping the cell. Header row uses the theme foundation with
    an accent rule; body rows use zebra striping in the theme surface.
    """
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    # duck-type DataFrame without importing pandas
    if hasattr(data, "iloc"):
        header = list(data.columns)
        rows = data.values.tolist()
        data = [header] + rows

    # data is now list[list]
    if not data:
        return Spacer(1, 6)

    col_count = max(len(row) for row in data) if data else 0
    if available_width is None:
        available = 6.3 * inch  # A4 minus 1in margins ≈ 6.3in
    else:
        available = available_width
    col_widths = [available / col_count] * col_count if col_count else None

    header_style = ParagraphStyle(
        "TH",
        fontName="Inter-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=TA_LEFT,
    )
    body_style = ParagraphStyle(
        "TD",
        fontName="Inter",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor(theme.body_text),
        alignment=TA_LEFT,
    )
    body_right = ParagraphStyle("TD-R", parent=body_style, alignment=TA_RIGHT)

    def make_cell(text, row_idx, col_idx):
        if row_idx == 0:
            return Paragraph(str(text), header_style)
        if right_align_cols and col_idx in right_align_cols:
            return Paragraph(str(text), body_right)
        return Paragraph(str(text), body_style)

    wrapped = [
        [make_cell(cell, r, c) for c, cell in enumerate(row)]
        for r, row in enumerate(data)
    ]

    t = Table(wrapped, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(theme.foundation)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, colors.HexColor(theme.accent)),
        ("GRID", (0, 1), (-1, -1), 0.5, colors.HexColor(theme.grid)),
    ]
    # Right-align specified numeric columns (data rows only)
    if right_align_cols:
        for col_idx in right_align_cols:
            style_cmds.append(("ALIGN", (col_idx, 1), (col_idx, -1), "RIGHT"))
    # Alternating row colors (skip header row)
    for i in range(1, len(data)):
        bg = colors.HexColor(theme.surface) if i % 2 == 0 else colors.white
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))

    # Add color swatches in the Preview column (col 2) for data rows
    # Check if column 2 contains hex colors and set background accordingly
    for i in range(1, len(data)):
        if len(data[i]) > 2:
            cell_val = str(data[i][2]).strip()
            if cell_val.startswith("#") and len(cell_val) == 7:
                try:
                    style_cmds.append(("BACKGROUND", (2, i), (2, i), colors.HexColor(cell_val)))
                except (ValueError, AttributeError):
                    pass

    t.setStyle(TableStyle(style_cmds))

    if caption:
        cap_style = _to_reportlab_style(
            Style(
                font=Font("Inter", 9, italic=True, color=theme.muted_text),
                space_before=10,
                space_after=6,
                alignment="center",
            )
        )
        return [Paragraph(caption, cap_style), t]

    return t


def _build_kpi_row(cards: list[dict], theme=None):
    """Render a row of KPI summary cards as a styled table.

    Each card: {"label": str, "value": str, "delta": str (optional, green/red)}.
    A multi-column table keeps text vector-crisp at any zoom (unlike rasterized
    chart labels). Returns a Table flowable.
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    if not cards:
        return Spacer(1, 6)

    label_style = ParagraphStyle(
        "KPIL", fontName="Inter", fontSize=8, leading=10,
        textColor=colors.HexColor(theme.muted_text), alignment=1,
    )
    value_style = ParagraphStyle(
        "KPIV", fontName="Inter-Bold", fontSize=18, leading=20,
        textColor=colors.HexColor(theme.foundation), alignment=1,
    )
    delta_style_up = ParagraphStyle(
        "KPIDU", fontName="Inter-Bold", fontSize=8, leading=10,
        textColor=colors.HexColor(theme.good), alignment=1,
    )
    delta_style_down = ParagraphStyle(
        "KPIDD", fontName="Inter-Bold", fontSize=8, leading=10,
        textColor=colors.HexColor(theme.bad), alignment=1,
    )

    rows = []
    for c in cards:
        label = Paragraph(str(c.get("label", "")), label_style)
        value = Paragraph(str(c.get("value", "")), value_style)
        delta = c.get("delta")
        if delta is None:
            delta_cell = Paragraph("", label_style)
        elif str(delta).startswith("-"):
            delta_cell = Paragraph(str(delta), delta_style_down)
        else:
            delta_cell = Paragraph(str(delta), delta_style_up)
        rows.append([label, value, delta_cell])

    # transpose: each card becomes a column of [label, value, delta]
    data = list(map(list, zip(*rows)))
    n = len(cards)
    col_widths = [6.3 * inch / n] * n

    t = Table(data, colWidths=col_widths)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(theme.surface)),
        ("LINEBEFORE", (1, 0), (-1, -1), 0.5, colors.HexColor(theme.grid)),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(theme.grid)),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t


def _build_chart(
    figure,
    width: float | None = None,
    height: float | None = None,
    close_figure: bool = True,
):
    """Convert a matplotlib figure into an inline vector PDF flowable."""

    # SVG via BytesIO → svg2rlg. No temp files.
    svg_io = BytesIO()
    try:
        figure.savefig(svg_io, format="svg", bbox_inches="tight")
    finally:
        if close_figure:
            from matplotlib import pyplot as plt

            plt.close(figure)
    svg_io.seek(0)

    from svglib.svglib import svg2rlg

    drawing = svg2rlg(svg_io)
    aspect = drawing.width / drawing.height if drawing.height else 1.0

    if width is None:
        width = 6.3 * 72  # ~6.3 inches in points
    if height is None:
        height = width / aspect if aspect else width * 0.6

    # Save original SVG dimensions before overwriting — otherwise the scale
    # factor becomes width/width = 1.0 and charts never resize.
    orig_width = drawing.width
    orig_height = drawing.height

    # Tall/square figures (donut, heatmap) look bloated at full width and
    # refuse to pack two-per-page. Cap their rendered width so they stay
    # proportional and leave room for a neighbour. Wide figures keep full width.
    AVAILABLE = 6.3 * 72
    width = min(width, AVAILABLE)
    # Donut charts are now wider (aspect ~1.24) to accommodate external legend.
    # Don't cap at 4.6in — allow up to 5.5in for these.
    if aspect >= 1.1 and aspect <= 1.35 and width > 5.5 * 72:
        width = 5.5 * 72
    elif aspect < 1.3 and width > 4.6 * 72:
        width = 4.6 * 72

    drawing.width = width
    drawing.height = height
    if orig_width and orig_height:
        drawing.scale(width / orig_width, height / orig_height)

        # Centre charts narrower than the content frame so they read as
        # intentional rather than leaving a gap on the right.
        if drawing is not None:
            drawing.hAlign = "CENTER"

        return drawing


def _build_chart_row(figures: list, space_after: float = 0):
    """Lay out up to two charts in a single row to conserve vertical space."""
    from reportlab.lib.units import inch
    from reportlab.platypus import Spacer, Table, TableStyle

    if not figures:
        return Spacer(1, 6)
    cells = []
    for fig in figures[:2]:
        item = _build_chart(fig, width=(6.3 * 72) / len(figures[:2]), close_figure=True)
        if item is not None:
            cells.append(item)
    if not cells:
        return Spacer(1, 6)
    if len(cells) == 1:
        return cells[0]
    row = Table([[cells[0], cells[1]]], colWidths=[3.05 * inch, 3.05 * inch])
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                             ("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
    return row


def _header_footer_callback(doc, header_text: str | None):
    """Return an onPage callback that draws the header on each page."""

    def callback(canvas, page_doc):
        if header_text:
            text = header_text.replace("{page}", str(canvas.getPageNumber()))
            text = text.replace("{total}", str(page_doc.page))
            canvas.saveState()
            canvas.setFont("Inter", 9)
            # Position in the top margin, above the content frame
            header_y = page_doc.height + page_doc.topMargin - 14
            canvas.drawCentredString(page_doc.width / 2.0, header_y, text)
            canvas.restoreState()

    return callback


def _build_story(pdf_doc) -> list:
    """Build the list of ReportLab flowables from document elements."""
    from reportlab.lib import colors
    from reportlab.platypus import (
        HRFlowable,
        ListFlowable,
        ListItem,
        PageBreak,
        Paragraph,
        Spacer,
    )

    theme = pdf_doc.theme
    story = []
    for el in pdf_doc._elements:
        etype = el[0]
        if etype == "chart":
            _, figure, width, height, space_before, space_after, close_figure = el
            item = _build_chart(figure, width, height, close_figure)
            if item is not None:
                if space_before:
                    story.append(Spacer(1, space_before))
                story.append(item)
                if space_after:
                    story.append(Spacer(1, space_after))
        elif etype == "heading":
            _, text, level = el
            story.append(Paragraph(str(text), _heading_style(level, theme)))
            # Hairline rule under section headings (h1/h2)
            if level in (1, 2):
                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.6,
                        color=colors.HexColor(theme.accent),
                        spaceBefore=0,
                        spaceAfter=10,
                    )
                )
        elif etype == "paragraph":
            _, text, style = el
            story.append(Paragraph(text, _to_reportlab_style(style)))
        elif etype == "table":
                    _, data, caption, right_align_cols = el
                    # Calculate available width based on page size and margins
                    from reportlab.lib.pagesizes import A4, letter
                    from reportlab.lib.units import inch
                    page_size_map = {"A4": A4, "letter": letter}
                    ps = page_size_map.get(pdf_doc._page_size, A4)
                    margins = pdf_doc._margins
                    if isinstance(margins, str) and margins.endswith("in"):
                        margin_pts = float(margins.replace("in", "")) * inch
                    elif isinstance(margins, str) and margins.endswith("pt"):
                        margin_pts = float(margins.replace("pt", ""))
                    else:
                        margin_pts = inch
                    available_width = ps[0] - 2 * margin_pts
                    item = _build_table(data, caption, right_align_cols, theme, available_width)
                    if isinstance(item, list):
                        story.extend(item)
                    else:
                        story.append(item)
        elif etype == "page_break":
            story.append(PageBreak())
        elif etype == "chart_row":
            _, figures, space_after = el
            item = _build_chart_row(figures, space_after)
            if space_after:
                story.append(Spacer(1, space_after))
            if item is not None:
                story.append(item)
        elif etype == "kpi_row":
            _, cards = el
            story.append(_build_kpi_row(cards, theme))
        elif etype == "bullet":
            _, text, style = el
            rs = _to_reportlab_style(style)
            p = Paragraph(text, rs)
            story.append(
                ListFlowable(
                    [ListItem(p, bulletColor=colors.HexColor(theme.accent))],
                    bulletType="bullet",
                    bulletColor=colors.HexColor(theme.accent),
                    bulletFontSize=rs.fontSize * 0.7,
                    leftIndent=14,
                    spaceBefore=3,
                    spaceAfter=3,
                )
            )
    return story


def render_pdf(pdf_doc, path: str) -> None:
    """Render a Document to a PDF file using ReportLab."""
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate

    _register_fonts()

    page_size_map = {"A4": A4, "letter": letter}
    ps = page_size_map.get(pdf_doc._page_size, A4)

    margins = pdf_doc._margins
    if isinstance(margins, str) and margins.endswith("in"):
        margin_pts = float(margins.replace("in", "")) * inch
    elif isinstance(margins, str) and margins.endswith("pt"):
        margin_pts = float(margins.replace("pt", ""))
    else:
        margin_pts = inch

    template_kw = dict(
        pagesize=ps,
        leftMargin=margin_pts,
        rightMargin=margin_pts,
        topMargin=margin_pts + 30,  # extra space for header
        bottomMargin=margin_pts,
    )

    header_text = pdf_doc._header
    needs_total = header_text and "{total}" in header_text

    if needs_total:
        # First pass: build story and count pages
        from io import BytesIO

        buf = BytesIO()
        tmp_template = SimpleDocTemplate(buf, **template_kw)
        tmp_template.build(_build_story(pdf_doc))
        total_pages = tmp_template.page if hasattr(tmp_template, "page") else 1
        buf.close()

        header_text = header_text.replace("{total}", str(total_pages))

    # Second pass: resolve {total} header and render to real path
    doc_template = SimpleDocTemplate(path, **template_kw)
    doc_template.build(
        _build_story(pdf_doc),
        onFirstPage=_header_footer_callback(doc_template, header_text),
        onLaterPages=_header_footer_callback(doc_template, header_text),
    )