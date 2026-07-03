from __future__ import annotations

from pathlib import Path

from .styles import Style, Font

# ponytail: simple name→filename mapping for bundled fonts.
# Add new fonts here when bundled.
_BUILTIN_FONTS: dict[str, str] = {
    "Inter": "Inter-Regular.ttf",
    "Lora": "Lora-Regular.ttf",
    "JetBrainsMono": "JetBrainsMono-Regular.ttf",
}

_FONTS_REGISTERED = False  # ponytail: global flag; lru_cache if invalidation needed


def _register_fonts() -> None:
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.fonts import addMapping

    fonts_dir = Path(__file__).parent / "fonts"

    for family, filename in _BUILTIN_FONTS.items():
        ttf_path = fonts_dir / filename
        if not ttf_path.exists():
            continue
        # Register regular variant under the family name
        font = TTFont(family, str(ttf_path))
        pdfmetrics.registerFont(font)
        # Tell ps2tt about this font family
        addMapping(family, 0, 0, family)  # normal
        addMapping(family, 1, 0, family)  # bold (same font for now)

    _FONTS_REGISTERED = True


def _to_reportlab_style(style: Style) -> "ParagraphStyle":
    """Convert our Style dataclass to a ReportLab ParagraphStyle."""
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.lib.styles import ParagraphStyle

    align_map = {
        "left": TA_LEFT,
        "center": TA_CENTER,
        "right": TA_RIGHT,
        "justify": TA_JUSTIFY,
    }
    font = style.font or Font()
    # ponytail: v0.1.0 bundles Regular variants only. bold/italic use same
    # regular font. Add variant TTF files when someone needs real bold/italic.
    font_name = font.family

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


def _heading_style(level: int) -> "ParagraphStyle":
    """Return a ReportLab ParagraphStyle sized by heading level."""
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import ParagraphStyle

    sizes = {0: 24, 1: 18, 2: 14}
    font_name = "Inter"
    size = sizes.get(level, 12)
    return ParagraphStyle(
        f"Heading{level}",
        fontName=font_name,
        fontSize=size,
        leading=size * 1.2,
        spaceBefore=14,
        spaceAfter=14,
        textColor=HexColor("#1a1a1a"),
    )


def _parse_color(hex_str: str) -> "Color":
    """Parse a hex colour string like '#1a1a1a' into a ReportLab Color object."""
    from reportlab.lib.colors import HexColor

    return HexColor(hex_str)


def _build_table(data, caption: str | None, right_align_cols: list[int] | None = None):
    """Convert data (DataFrame or list[list]) into a ReportLab Table flowable."""
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import Table, TableStyle, Paragraph

    # ponytail: duck-type DataFrame without importing pandas
    if hasattr(data, "iloc"):
        header = list(data.columns)
        rows = data.values.tolist()
        data = [header] + rows

    # data is now list[list]
    if not data:
        from reportlab.platypus import Spacer

        return Spacer(1, 6)

    # Smart column widths: proportional to content
    col_count = max(len(row) for row in data) if data else 0
    available = 6.3 * inch  # A4 minus 1in margins ≈ 6.3in
    if col_count > 0:
        col_width = available / col_count
        col_widths = [col_width] * col_count
    else:
        col_widths = None

    t = Table(
        data,
        colWidths=col_widths,
        repeatRows=1,  # repeat header on page split
    )

    # Build alternating-row style
    style_cmds = [
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Inter"),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d2d2d")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
    ]
    # Right-align specified numeric columns (data rows only)
    if right_align_cols:
        for col_idx in right_align_cols:
            style_cmds.append(("ALIGN", (col_idx, 1), (col_idx, -1), "RIGHT"))
    # Alternating row colors (skip header row)
    for i in range(1, len(data)):
        bg = colors.HexColor("#f5f5f5") if i % 2 == 0 else colors.white
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))

    t.setStyle(TableStyle(style_cmds))

    if caption:
        from reportlab.platypus import Paragraph as P, Spacer

        cap_style = _to_reportlab_style(Style(font=Font("Inter", 9, italic=True), space_before=12, space_after=4))
        return [P(caption, cap_style), t]

    return t


def _build_chart(figure, width: float | None = None, height: float | None = None):
    """Convert a matplotlib figure into an inline vector PDF flowable."""
    from io import BytesIO

    # ponytail: SVG via BytesIO → svg2rlg. No temp files.
    svg_io = BytesIO()
    figure.savefig(svg_io, format="svg", bbox_inches="tight")
    svg_io.seek(0)

    from reportlab.graphics import renderPDF
    from svglib.svglib import svg2rlg

    drawing = svg2rlg(svg_io)
    aspect = drawing.width / drawing.height if drawing.height else 1.0

    if width is None:
        width = 6.3 * 72  # ~6.3 inches in points
    if height is None:
        height = width / aspect if aspect else width * 0.6

    drawing.width = width
    drawing.height = height
    drawing.scale(width / drawing.width, height / drawing.height)

    return drawing


def _header_footer_callback(doc, header_text: str | None):
    """Return an onPage callback that draws the header on each page."""

    def callback(canvas, page_doc):
        if header_text:
            text = header_text.replace("{page}", str(canvas._pageNumber))
            text = text.replace("{total}", str(page_doc.page))
            canvas.saveState()
            canvas.setFont("Inter", 9)
            canvas.drawCentredString(page_doc.width / 2.0, page_doc.height + 14, text)
            canvas.restoreState()

    return callback


def _build_story(pdf_doc) -> list:
    """Build the list of ReportLab flowables from document elements."""
    from reportlab.platypus import Paragraph, PageBreak, Spacer
    from reportlab.platypus import ListFlowable, ListItem
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle

    story = []
    for el in pdf_doc._elements:
        etype = el[0]
        if etype == "chart":
            _, figure, width, height, space_before, space_after = el
            item = _build_chart(figure, width, height)
            if item is not None:
                if space_before:
                    story.append(Spacer(1, space_before))
                story.append(item)
                if space_after:
                    story.append(Spacer(1, space_after))
        elif etype == "heading":
            _, text, level = el
            story.append(Paragraph(str(text), _heading_style(level)))
        elif etype == "paragraph":
            _, text, style = el
            story.append(Paragraph(text, _to_reportlab_style(style)))
        elif etype == "table":
            _, data, caption, right_align_cols = el
            item = _build_table(data, caption, right_align_cols)
            if isinstance(item, list):
                story.extend(item)
            else:
                story.append(item)
        elif etype == "page_break":
            story.append(PageBreak())
        elif etype == "bullet":
            _, text, style = el
            rs = _to_reportlab_style(style)
            p = Paragraph(text, rs)
            story.append(ListFlowable(
                [ListItem(p, bulletColor=colors.HexColor("#1a1a1a"))],
                bulletType="bullet",
                start=None,
                bulletFontSize=rs.fontSize * 0.7,
                leftIndent=14,
                spaceBefore=3,
                spaceAfter=3,
            ))
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

    # First pass: build story and count pages
    from io import BytesIO

    buf = BytesIO()
    tmp_template = SimpleDocTemplate(buf, **template_kw)
    tmp_template.build(_build_story(pdf_doc))
    total_pages = tmp_template.page if hasattr(tmp_template, "page") else 1
    buf.close()

    # Second pass: resolve {total} header and render to real path
    header_text = pdf_doc._header
    if header_text and "{total}" in header_text:
        header_text = header_text.replace("{total}", str(total_pages))

    doc_template = SimpleDocTemplate(path, **template_kw)
    doc_template.build(
        _build_story(pdf_doc),
        onFirstPage=_header_footer_callback(doc_template, header_text),
        onLaterPages=_header_footer_callback(doc_template, header_text),
    )
