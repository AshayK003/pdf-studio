# pdf-studio Architecture

## High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Document                               │
│  (model: elements list, header, page_size, margins, theme)  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     render.py                               │
│  (builder: font registration, table styling, chart SVG→PDF) │
└──────────────────────────┬──────────────────────────────────┘
                           │
               ┌───────────┼───────────┐
               ▼           ▼           ▼
       ┌─────────────┐ ┌───────────┐ ┌─────────┐
       │  ReportLab  │ │ matplotlib │ │ svglib  │
       │  (engine)   │ │ (charts)   │ │(SVG→PDF)│
       └─────────────┘ └───────────┘ └─────────┘
```

## Module Structure

| Module | Responsibility | Key Exports |
|--------|---------------|-------------|
| `document.py` | Document model, builder API, template dispatch | `Document`, `Style`, `Font`, `Theme` |
| `render.py` | ReportLab flowable construction, two-pass rendering | `render_pdf`, `_build_table`, `_build_chart`, `_build_story` |
| `visuals.py` | Pre-styled matplotlib chart builders | `bar_chart`, `line_chart`, `donut_chart`, `heatmap` |
| `templates.py` | Declarative template registry | `build`, `_REGISTRY` |
| `themes.py` | Visual language definitions | `Theme` dataclass, presets |
| `styles.py` | Style/Font dataclasses | `Style`, `Font`, `_default_style` |

## Data Flow

```
Document (user API)
    │
    ├── add_heading() ───┐
    ├── add_paragraph()  │
    ├── add_table()      ├──→ Document._elements (list of tuples)
    ├── add_chart()      │
    ├── add_kpi_row()    │
    ├── add_bullet()     │
    └── set_header() ────┘
                           │
                           ▼
                  render_pdf(document, path)
                           │
                           ▼
                  _build_story(pdf_doc)  →  list of ReportLab flowables
                           │
                           ▼
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    _build_table()  _build_chart()   _build_kpi_row()
           │               │               │
           ▼               ▼               ▼
      ReportLab       SVG → PDF       ReportLab
        Table        (svglib)         Table
           │               │               │
           └───────────────┼───────────────┘
                           ▼
              SimpleDocTemplate.build(story)
                           │
                           ▼
                      output.pdf
```

## Two-Pass Rendering

The document is rendered in **two passes**:

1. **First pass** — Build story into a `BytesIO` buffer using a temporary `SimpleDocTemplate`. This counts pages so `{total}` placeholder in headers can be resolved.
2. **Second pass** — Replace `{total}` with actual page count, then render to the final file path with `onFirstPage`/`onLaterPage` callbacks for headers.

## Theme System

The `Theme` dataclass (in `themes.py`) defines a complete visual language:

- **Roles** (not raw colours): `foundation`, `surface`, `body_text`, `muted_text`, `accent`, `good`, `bad`, `grid`, `series`, `h0/h1/h2`
- **3 presets**: `cypher` (navy/teal), `ledger` (green/gold), `slate` (indigo/amber)
- All foundations pass WCAG-AA on white (≥4.5:1)
- `accent` is fill/bullet only — never used as text

Theme is passed through `Document.theme` → `render.py` → all `_build_*` functions → chart builders in `visuals.py`.

## Font System

Three open-source fonts bundled as real TTF files (no synthetic bold/italic):

| Font | Weights | Use Case |
|------|---------|----------|
| Inter | Regular, Bold | Body text, UI |
| Lora | Regular, Bold, Italic | Headings, long-form |
| JetBrains Mono | Regular, Bold | Code, data, tables |

Font registration uses double-checked locking for thread safety (`_register_fonts()`).

Style resolution (`_resolve_font_name`) maps `Font(family, bold, italic)` → registered TTF name.

## Chart Pipeline

```
matplotlib Figure
    │
    ▼
savefig(format="svg") → BytesIO
    │
    ▼
svglib.svg2rlg() → ReportLab Drawing
    │
    ▼
_scale() using original SVG dimensions
    │
    ▼
ReportLab flowable (vector, crisp at any zoom)
```

Chart builders in `visuals.py` accept optional `Theme` and use `theme.series` for colours.

## Template System

`templates.py` provides a registry for declarative reports:

- `build(name, data, **kwargs)` → dispatches to template builder
- `financial_statement` — the built-in template (title, subtitle, KPIs, donut, table)
- `Document.from_template(name, data)` — class method for one-call usage

## Dependencies

| Package | Required | Purpose |
|---------|----------|---------|
| `reportlab` | ✅ | PDF generation engine |
| `matplotlib` | Optional | Charts (`add_chart()`, convenience methods) |
| `pandas` | Optional | DataFrame → table conversion |
| `svglib` | Optional | SVG → PDF conversion for charts |

Core dependency: **only `reportlab`**. Optional deps use lazy imports.

## Testing

- Framework: `pytest`
- Location: `tests/`
- 39 tests covering: rendering, tables, charts, fonts, themes, templates
- No external services, no network calls
- Run: `pytest` or `pytest --cov=pdf_studio`

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Two-pass rendering | Required for `{total}` header placeholder |
| SVG → PDF for charts | Vector output stays crisp at any zoom; no rasterization |
| Dataclasses for Style/Font/Theme | Type-safe, IDE-friendly, immutable by default |
| Lazy imports for optional deps | Core library works with only `reportlab` |
| Real TTF weights (no synthetic) | Professional typography, no fallback surprises |
| Theme roles (not raw colours) | Consistent recoloring across all elements |
| Template registry (not hardcoded) | Extensible for user-defined report types |