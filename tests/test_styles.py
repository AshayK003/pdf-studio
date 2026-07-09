"""Tests for pdf_studio styles dataclasses."""

from pdf_studio.styles import Font, Style, _default_style


def test_font_defaults():
    f = Font()
    assert f.family == "Inter"
    assert f.size == 11
    assert f.bold is False
    assert f.italic is False
    assert f.color == "#1a1a1a"


def test_style_defaults():
    s = Style()
    assert s.leading == 1.4
    assert s.alignment == "left"
    assert s.space_before == 0
    assert s.space_after == 6


def test_default_style_returns_valid_style():
    s = _default_style()
    assert isinstance(s, Style)
    assert isinstance(s.font, Font)
    assert s.font.family == "Inter"
