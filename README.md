<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://capsule-render.vercel.app/api?type=waving&height=120&color=0:1a1a2e,100:16213e&text=pdf-studio&fontSize=40&fontColor=ffffff&fontAlignY=35">
    <img alt="pdf-studio" src="https://capsule-render.vercel.app/api?type=waving&height=120&color=0:1a3c6e,100:22C55E&text=pdf-studio&fontSize=40&fontColor=ffffff&fontAlignY=35">
  </picture>
</p>

<p align="center">
  <b>Three lines of code for a PDF with a table, a chart, and a header.</b>
</p>

<p align="center">
  <a href="https://github.com/AshayK003/pdf-studio/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-AGPLv3-blue.svg" alt="License"></a>
  <a href="https://pypi.org/project/pdf-studio/"><img src="https://img.shields.io/badge/python-≥3.10-blue" alt="Python ≥3.10"></a>
  <a href="https://github.com/AshayK003/pdf-studio/actions"><img src="https://img.shields.io/badge/build-passing-brightgreen" alt="Build"></a>
</p>

---

## Why

Every Python developer hits the wall where they need a PDF with actual content — a table, a chart, a header with page numbers — and the options are:

- **ReportLab** — powerful but 300+ lines of `TableStyle` boilerplate for a simple table
- **matplotlib** — great for charts, zero for document layout
- **fpdf2/WeasyPrint** — different tradeoffs, same boilerplate problem
- **Typst** — not Python, not embeddable

**pdf-studio bridges the gap.** It's a thin wrapper around ReportLab that gives you a clean API for the 80% use case: a document with headings, paragraphs, tables, charts, and a running header — in three method calls.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Document   │ ──→ │  render.py   │ ──→ │  ReportLab  │
│  (model)    │     │  (builder)   │     │  (engine)   │
└─────────────┘     └──────────────┘     └─────────────┘
       │                     │
       ▼                     ▼
  Style / Font          SVG → PDF
  (dataclasses)         (svglib)
```

The library has three layers:

1. **Document model** (`Document`, `Style`, `Font`) — pure Python dataclasses that describe *what* goes in the PDF
2. **Render engine** (`render.py`) — converts the document model into ReportLab flowables, handles font registration, table styling, chart conversion (matplotlib SVG → vector PDF via svglib)
3. **ReportLab** — the actual PDF generation. pdf-studio is a 300-line wrapper, not a replacement.

The document is rendered in **two passes**: the first pass counts pages (for `{total}` in headers), the second pass builds the real PDF with resolved page numbers.

## Quick Start

```bash
pip install pdf-studio reportlab matplotlib pandas svglib
```

```python
from pdf_studio import Document

doc = Document()
doc.set_header("Report | Page {page} of {total}")
doc.add_heading("Q3 Results", level=0)
doc.add_paragraph("Revenue grew 12% year-over-year.")

# Charts from matplotlib (inline vector, no temp files)
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.bar(["Apr", "May", "Jun"], [100, 120, 150])
doc.add_chart(fig)

# Tables from pandas or list-of-lists
import pandas as pd
doc.add_table(pd.DataFrame({
    "City": ["Delhi", "Mumbai", "Bangalore"],
    "Revenue": [450, 620, 380],
}), caption="Q3 Revenue by City")

doc.render("report.pdf")   # ✅ 3 methods, one file
```

That's it. Three methods and one `render()` call produces a multi-page PDF with a running header, a chart, and a styled table.

## API

### `Document`

| Method | Parameters | Description |
|---|---|---|
| `add_heading(text, level=0)` | `level`: 0=title, 1=h1, 2=h2 | Add a heading |
| `add_paragraph(text, style=None)` | `style`: optional `Style` | Add body text |
| `add_table(data, caption=None)` | `data`: DataFrame or `list[list]` | Add a styled table with alternating rows |
| `add_chart(figure, width=None, height=None)` | matplotlib `Figure` | Convert chart to inline vector PDF |
| `add_bullet(text, style=None)` | — | Add a bullet-pointed item |
| `add_page_break()` | — | Force a new page |
| `set_header(text)` | supports `{page}` and `{total}` | Running header on every page |
| `render(path)` | file path | Build the PDF file |

### `Style`

| Field | Default | Description |
|---|---|---|
| `font` | `Font()` | Font specification |
| `leading` | `1.4` | Line-height multiplier |
| `alignment` | `"left"` | One of: `left`, `center`, `right`, `justify` |
| `space_before` | `0` | Points before paragraph |
| `space_after` | `6` | Points after paragraph |

### `Font`

| Field | Default | Description |
|---|---|---|
| `family` | `"Inter"` | One of bundled fonts or your own TTF name |
| `size` | `11` | Point size |
| `bold` | `False` | Style flag (uses regular weight in v0.1.0) |
| `italic` | `False` | Style flag (uses regular weight in v0.1.0) |
| `color` | `"#1a1a1a"` | Hex color string |

## Bundled Fonts

Three open-source fonts ship with the library — zero system font dependencies:

- **Inter** (sans-serif, body text)
- **Lora** (serif, headings / long-form reading)
- **JetBrains Mono** (monospace, code / data)

v0.1.0 bundles **Regular** weight only. Bold/italic flags use the same regular font. Add weight-specific `.ttf` files to `pdf_studio/fonts/` and update `_BUILTIN_FONTS` in `render.py` for real bold/italic rendering.

## Dependencies

| Package | Required | Why |
|---|---|---|
| `reportlab` | ✅ | PDF generation engine |
| `matplotlib` | ❌ | Charts (only needed if you use `add_chart()`) |
| `pandas` | ❌ | Tables from DataFrames (only needed if you pass DataFrames) |
| `svglib` | ❌ | SVG→PDF conversion (only needed if you use `add_chart()`) |

Core dependency is **one package**: `reportlab`. Chart and DataFrame features are optional.

## Setup

### Install from PyPI

```bash
pip install pdf-studio
```

### Install from source

```bash
git clone https://github.com/AshayK003/pdf-studio.git
cd pdf-studio
pip install -e .
```

For development (includes test deps):

```bash
pip install -e ".[dev]"
```

### Verify installation

```bash
python _demo.py
# ✅ pdf-studio v0.1.0 smoke test passed
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pdf_studio

# Run specific test file
pytest tests/test_render.py -v
```

Tests use pytest with standard Python temp directories. No external services, no network calls, no fixtures beyond what `pytest` provides. 12 tests, ~2.5s runtime.

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'reportlab'` | Missing dependency | `pip install reportlab` |
| `ModuleNotFoundError: No module named 'svglib'` | Need chart support | `pip install svglib` |
| Chart renders at wrong size / always 1.0 scale | Using patched `render.py` before PR #4 | Update to latest master — the bug was that `drawing.width` was overwritten before the scale ratio was computed |
| `font not found: Inter` | Font file missing | Reinstall with `pip install -e .` — bundled fonts are in `pdf_studio/fonts/` |
| `pdf_studio` not found after `pip install -e .` | Build backend needs setuptools | `pip install setuptools` |

## Production Notes

- pdf-studio is a **library**, not a service. It generates PDFs synchronously on the calling thread. For high-throughput PDF generation, wrap calls in a thread pool.
- The two-pass render is intentional: `{total}` in headers needs the final page count. If you don't use `{total}`, the first pass still runs (minor overhead, ~50ms on a 10-page doc).
- Thread-safe within a single `Document` instance. Concurrent calls to `render()` on the same doc are not safe (it mutates internal state).
- ReportLab is C-extended where it matters (PDF serialization) and pure Python for layout. Expect ~100ms for a 5-page document on modern hardware.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

High-level principles:

- **One change per PR.** Small, focused diffs are easier to review and less likely to conflict.
- **Tests required.** Every new feature or bug fix includes tests. `pytest` must pass.
- **Keep it simple.** This is a 300-line library with 3 bundled fonts. Adding a dependency or a new abstraction needs a strong justification — the library's value is its simplicity.
- **Backend-optional.** Chart/matplotlib features use lazy imports. Don't make them hard requirements.

## License

AGPL v3 — see [LICENSE](LICENSE). Free to use, share, and modify. If you build a closed-source application on top of it, you must release your changes under AGPL as well.
