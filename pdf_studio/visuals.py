"""Pre-styled chart builders for data-analysis PDFs.

Each function returns a matplotlib Figure styled with the pdf-studio brand
palette (navy + teal) so charts match document typography without the caller
configuring matplotlib. Built on matplotlib only, no new dependencies.

These are intentionally thin: they wrap a single matplotlib call with brand
defaults. Compose them with Document.add_chart (or the Document.add_*_chart
convenience methods) to place them in a PDF.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from .themes import Theme


def _theme_or(theme: Optional[Theme]) -> Theme:
    return theme or Theme.cypher()


def _base_style(fig, ax, title=None, theme: Optional[Theme] = None):
    """Apply brand chrome: white canvas, no top/right spine, subtle grid."""
    theme = _theme_or(theme)
    series = theme.series
    navy = theme.foundation
    grid = theme.grid
    slate = theme.muted_text
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    if title:
        ax.set_title(title, color=navy, fontsize=12, fontweight="bold", pad=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(grid)
    ax.spines["bottom"].set_color(grid)
    ax.tick_params(colors=slate, labelsize=9)
    ax.grid(axis="y", color=grid, linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    return ax


def bar_chart(labels, values, title=None, horizontal=False, theme: Optional[Theme] = None):
    """Single-series bar chart. Vertical by default, optional horizontal."""
    theme = _theme_or(theme)
    fig, ax = plt.subplots(figsize=(6.3, 3.2), dpi=150)
    color = theme.series[0]
    if horizontal:
        bars = ax.barh(labels, values, color=color, zorder=3)
        ax.bar_label(bars, padding=4, color=theme.foundation, fontsize=9, fontweight="bold")
        ax.set_axisbelow(True)
        ax.grid(axis="x", color=theme.grid, linewidth=0.6, zorder=0)
        ax.grid(axis="y", visible=False)
    else:
        bars = ax.bar(labels, values, color=color, zorder=3, width=0.62)
        ax.bar_label(bars, padding=3, color=theme.foundation, fontsize=9, fontweight="bold")
    _base_style(fig, ax, title, theme)
    fig.tight_layout()
    return fig


def line_chart(x, series, title=None, theme: Optional[Theme] = None):
    """Multi-series line chart. series: dict[name -> list[float]]."""
    theme = _theme_or(theme)
    fig, ax = plt.subplots(figsize=(6.3, 3.2), dpi=150)
    for i, (name, y) in enumerate(series.items()):
        color = theme.series[i % len(theme.series)]
        ax.plot(
            x, y, marker="o", markersize=4, linewidth=2, color=color, label=name, zorder=3
        )
    _base_style(fig, ax, title, theme)
    if len(series) > 1:
        ax.legend(
            frameon=False, fontsize=9, labelcolor=theme.muted_text, loc="best"
        )
    fig.tight_layout()
    return fig


def donut_chart(labels, values, title=None, theme: Optional[Theme] = None):
    """Composition donut. Slice colours cycle the theme series palette.

    Legend is placed to the right of the donut to avoid overlap.
    Figure is wider (5.2 x 4.2) to accommodate external legend without compression.
    """
    theme = _theme_or(theme)
    fig, ax = plt.subplots(figsize=(5.2, 4.2), dpi=150)  # wider for external legend
    colors = [theme.series[i % len(theme.series)] for i in range(len(values))]
    wedges, _texts, autotexts = ax.pie(
        values,
        colors=colors,
        startangle=90,
        counterclock=False,
        autopct=lambda p: f"{p:.0f}%",
        pctdistance=0.68,  # move % labels closer to center
        wedgeprops=dict(width=0.38, edgecolor="white", linewidth=2),
    )
    # Adaptive % label color: white on dark slices, dark on light slices
    for t, wedge_color in zip(autotexts, colors):
        wc = wedge_color.lstrip('#')
        r, g, b = int(wc[0:2], 16)/255, int(wc[2:4], 16)/255, int(wc[4:6], 16)/255
        lum = 0.2126*r + 0.7152*g + 0.0722*b
        t.set_color("white" if lum < 0.5 else "#1a1a1a")
        t.set_fontsize(9)
        t.set_fontweight("bold")
    # Legend OUTSIDE to the right (not inside the donut hole)
    ax.legend(
        wedges,
        labels,
        frameon=False,
        fontsize=8,
        labelcolor=theme.muted_text,
        loc="center left",
        bbox_to_anchor=(1.05, 0.5),  # outside right
    )
    if title:
        ax.set_title(title, color=theme.foundation, fontsize=12, fontweight="bold", pad=12)
    fig.patch.set_facecolor("white")
    fig.tight_layout(pad=0.5)
    return fig


def heatmap(matrix, labels, title=None, diverging=True, theme: Optional[Theme] = None):
    """Matrix heatmap. diverging=True centres colour at 0 (for correlations)."""
    theme = _theme_or(theme)
    fig, ax = plt.subplots(figsize=(4.8, 4.2), dpi=150)
    if diverging:
        cmap = LinearSegmentedColormap.from_list(
            "brand_div", [theme.bad, "#FFFFFF", theme.foundation]
        )
        vmin, vmax = -1, 1
    else:
        cmap = LinearSegmentedColormap.from_list(
            "brand_seq", [theme.surface, theme.accent, theme.foundation]
        )
        vmin = vmax = None
    im = ax.imshow(matrix, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8, color=theme.muted_text)
    ax.set_yticklabels(labels, fontsize=8, color=theme.muted_text)
    for i in range(len(labels)):
        for j in range(len(labels)):
            val = matrix[i][j]
            txt_color = "white" if abs(val) > 0.5 else theme.foundation
            ax.text(
                j, i, f"{val:.2f}", ha="center", va="center",
                fontsize=8, color=txt_color, fontweight="bold",
            )
    if title:
        ax.set_title(title, color=theme.foundation, fontsize=12, fontweight="bold", pad=10)
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    return fig
