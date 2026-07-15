from __future__ import annotations

from .styles import Style, _default_style


class Document:
    """A PDF document under construction.

    Usage:
        doc = Document()
        doc.add_heading("Title", level=0)
        doc.add_paragraph("Body text", style=Style(...))
        doc.add_table(df, caption="Data")
        doc.add_chart(fig)
        doc.set_header("Page {page} of {total}")
        doc.render("output.pdf")
    """

    def __init__(self, page_size: str = "A4", margins: str = "32pt"):
        self._elements: list = []
        self._header: str | None = None
        self._page_size = page_size
        self._margins = margins

    def add_heading(self, text: str, level: int = 0) -> None:
        """Add a heading. level=0 → title, level=1 → h1, level=2 → h2."""
        self._elements.append(("heading", text, level))

    def add_paragraph(self, text: str, style: Style | None = None) -> None:
        """Add a body paragraph with optional Style."""
        self._elements.append(("paragraph", text, style or _default_style()))

    def add_table(self, data, caption: str | None = None, right_align_cols: list[int] | None = None) -> None:
        """Add a table. Accepts pandas DataFrame or list[list]."""
        self._elements.append(("table", data, caption, right_align_cols))

    def add_chart(
        self,
        figure,
        width: float | None = None,
        height: float | None = None,
        space_before: float = 0,
        space_after: float = 6,
        close_figure: bool = True,
    ) -> None:
        """Add a matplotlib figure as an inline vector.

        space_before / space_after: vertical spacing in points around the chart.
        close_figure: release the figure after rendering. Set to False when the
            caller needs to reuse the figure after rendering the document.
        """
        self._elements.append(
            ("chart", figure, width, height, space_before, space_after, close_figure)
        )

    def add_page_break(self) -> None:
        """Force a page break. Next content starts on a new page."""
        self._elements.append(("page_break",))

    def add_bullet(self, text: str, style: Style | None = None) -> None:
        """Add a bullet-pointed list item."""
        self._elements.append(("bullet", text, style or _default_style()))

    def set_header(self, text: str) -> None:
        """Set a running header with optional {page} and {total} placeholders."""
        self._header = text

    def render(self, path: str) -> None:
        """Render the document to a PDF file."""
        from .render import render_pdf

        render_pdf(self, path)
