# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2026-08-16

### Changed
- **License: AGPL v3 → MIT.** The library is now permissively licensed — free to use, modify, and distribute, including in closed-source and commercial projects with no copyleft obligations.

## [0.1.2] - 2026-08-15

### Added
- **portfolio_risk template** for NSE Portfolio Risk Scanner

### Fixed
- **Restored `build()` function** in templates.py for template dispatch

## [0.1.1] - 2026-08-15

### Added
- **PyPI publish** as `pdf-studio-py` v0.1.1
- **Input validation** on all Document methods (heading, paragraph, table) with clear error messages
- **Graceful svglib error** - `add_chart()` now raises clear `RuntimeError` with install instruction if svglib missing
- **Two-pass rendering optimization** - skips first pass when `{total}` placeholder not in header
- **Table column width respects custom page size/margins** - no longer hardcoded A4 assumption
- **Declarative templates** - `Document.from_template("financial_statement", data)` for one-call reports
- **Three research-backed themes** - cypher (navy/teal), ledger (green/gold), slate (indigo/amber) - all WCAG-AA verified
- **Convenience chart methods** - `add_bar_chart()`, `add_line_chart()`, `add_donut_chart()`, `add_heatmap()`
- **KPI summary cards** - `add_kpi_row()` with green/red deltas
- **Chart row layout** - `add_chart_row()` for side-by-side charts
- **Bundled fonts** - Inter (Regular, Bold), Lora (Regular, Bold, Italic), JetBrains Mono (Regular, Bold) with real TTF weights
- **`__version__` attribute** - accessible via `pdf_studio.__version__`
- **Dev extras** - `pip install "pdf-studio-py[dev]"` includes pytest, ruff, matplotlib, pandas, svglib
- **Full documentation** - README, CONTRIBUTING, ARCHITECTURE, LICENSE (AGPL v3)
- **Theme showcase** - 9-page PDF demonstrating all features across all themes

### Fixed
- **Chart scaling** - preserves original SVG dimensions (no more 1.0 scale bug)
- **Donut chart layout** - wider figure (5.2×4.2) with external legend, adaptive % label contrast
- **Two-pass rendering** - now only runs when `{total}` placeholder is actually used
- **Table column widths** - now respect custom page size and margins

### Changed
- **Package name** - published as `pdf-studio-py` on PyPI (import remains `import pdf_studio`)
- **Theme presets** - darker `muted_text` for WCAG-AA legend contrast across all themes
- **README install command** - optional deps now marked as optional
- **pyproject.toml** - added `readme`, `optional-dependencies.dev`, project URLs

### Security
- No hardcoded secrets
- Input validation on all public methods
- Graceful degradation for missing optional dependencies

## [0.1.0] - 2026-08-15

### Initial Release
- Core PDF generation with ReportLab
- Document model with headings, paragraphs, tables, charts
- Theme system with 3 presets
- Declarative template for financial statements
- Two-pass rendering for headers with page numbers
- Vector chart rendering (matplotlib → SVG → PDF)
- 39 tests passing

---

**Full diff:** https://github.com/AshayK003/pdf-studio/compare/v0.1.0...v0.1.1