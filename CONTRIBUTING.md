# Contributing to pdf-studio

Thanks for your interest in contributing. This document covers the practical details.

## Getting Started

```bash
git clone https://github.com/AshayK003/pdf-studio.git
cd pdf-studio
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
pip install -e ".[dev]"
```

Verify everything works:

```bash
python _demo.py              # generates example.pdf
pytest                        # 12 tests, all pass
```

## Development Workflow

1. Create a branch from `master`: `git checkout -b feature/my-change`
2. Make your changes
3. Add or update tests
4. Run `pytest` — all tests must pass
5. Commit and push
6. Open a pull request

## What to Work On

Check [open issues](https://github.com/AshayK003/pdf-studio/issues) for planned work. Good first contributions:

- Add pytest test suite (see issue #1)
- Fix chart scaling bug (see issue #2)
- Fix table column widths (see issue #3)
- Add support for custom fonts
- Add page numbering options

## Code Conventions

### Python

- Follow existing style in the file you're editing
- Keep imports sorted: stdlib, third-party, local
- Type hints are encouraged but not required
- Document public API methods with docstrings

### Architecture

- `Document` class is the main entry point
- `Style` and `Font` dataclasses configure appearance
- `render.py` handles ReportLab PDF generation
- Bundled fonts live in `pdf_studio/fonts/`

### Testing

- Test files go in `tests/`
- Name tests `test_<module>.py`
- Use `pytest` fixtures
- Write behavior-focused tests, not implementation tests

## Commit Messages

Use short imperative descriptions:

```
add test coverage for Document API
fix chart scaling with original SVG dimensions
update table column width calculation
add support for custom TTF fonts
```

## Pull Requests

- Keep PRs focused — one change per PR (target ≤200 lines changed)
- Include a description of what changed and why
- Reference related issues
- Small PRs get reviewed and merged faster. Split large features into sequential PRs.

## Troubleshooting

### Font bold/italic not rendering

If a font's bold or italic style appears the same as the regular style, the font file likely doesn't include that weight variant.

**Cause:** The PDF library falls back to the nearest available weight when the requested one isn't in the font file.

**Fix:** Register a font that has the weight you need. For bundled fonts:

- **Inter** (bundled) — supports Regular, Bold, Italic, Bold Italic
- **Lora** (bundled) — supports Regular, Bold, Italic, Bold Italic
- **JetBrains Mono** (bundled) — supports Regular, Bold, Italic, Bold Italic

Example:

```python
from pdf_studio import Font
bold_font = Font("Inter", size=12, weight="bold")  # works with bundled Inter
```

For custom fonts, verify the TTF/OTF file includes the `bold` and `italic` tables (check with `fc-query` or font book).

### Questions?

Open an issue or start a discussion on GitHub.
