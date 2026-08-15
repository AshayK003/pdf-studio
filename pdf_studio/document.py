from __future__ import annotations

from .styles import Style, _default_style
from .themes import Theme


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

    def __init__(
        self,
        page_size: str = "A4",
        margins: str = "32pt",
        theme: Theme | str | None = None,
    ):
        self._elements: list = []
        self._header: str | None = None
        self._page_size = page_size
        self._margins = margins
        self.theme = Theme.get(theme) if isinstance(theme, (str, type(None))) else theme

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

    def add_kpi_row(self, cards: list[dict]) -> None:
        """Add a row of KPI summary cards (label + value, optional delta).

        cards: list of {"label": str, "value": str, "delta": str (optional)}.
        Rendered as a brand-styled table so figures stay crisp at any zoom.
        """
        self._elements.append(("kpi_row", cards))

    def add_bar_chart(
        self, labels, values, title=None, horizontal=False,
        space_after: float = 6,
    ) -> None:
        """Add a brand-styled bar chart (single series)."""
        from .visuals import bar_chart

        fig = bar_chart(labels, values, title=title, horizontal=horizontal, theme=self.theme)
        self.add_chart(fig, space_after=space_after)

    def add_line_chart(self, x, series, title=None, space_after: float = 6) -> None:
        """Add a brand-styled multi-series line chart."""
        from .visuals import line_chart

        fig = line_chart(x, series, title=title, theme=self.theme)
        self.add_chart(fig, space_after=space_after)

    def add_donut_chart(self, labels, values, title=None, space_after: float = 6) -> None:
        """Add a brand-styled composition donut."""
        from .visuals import donut_chart

        fig = donut_chart(labels, values, title=title, theme=self.theme)
        self.add_chart(fig, space_after=space_after)

    def add_heatmap(
        self, matrix, labels, title=None, diverging=True, space_after: float = 6
    ) -> None:
        """Add a brand-styled matrix heatmap (e.g. correlation)."""
        from .visuals import heatmap

        fig = heatmap(matrix, labels, title=title, diverging=diverging, theme=self.theme)
        self.add_chart(fig, space_after=space_after)

    def add_chart_row(self, figures: list, space_after: float = 6) -> None:
        """Add up to two charts side by side to save vertical space.

        figures: list of matplotlib Figure objects (1 or 2). Two charts share
        one row at half-width each; a single figure still renders full width.
        """
        self._elements.append(("chart_row", figures, space_after))

    def add_bullet(self, text: str, style: Style | None = None) -> None:
        self._elements.append(("bullet", text, style or _default_style()))

    def set_header(self, text: str) -> None:
        """Set a running header with optional {page} and {total} placeholders."""
        self._header = text

    def render(self, path: str) -> None:
        """Render the document to a PDF file."""
        from .render import render_pdf

        render_pdf(self, path)

    @classmethod
    def from_template(cls, name: str, data, **kwargs) -> "Document":
        """Build a document from a named template + data in one call.

        Templates map structured data onto the existing element API, so a
        non-designer gets a fully styled report (theme, KPIs, table, charts)
        without configuring any colour or font. This is the category
        differentiator: declarative data → brand-consistent PDF.

        Available templates: "financial_statement".
        """
        from .templates import build

        return build(name, data, **kwargs)
