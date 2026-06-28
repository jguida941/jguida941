"""Shared SVG text and formatting utilities."""

from __future__ import annotations

from typing import Mapping

from scripts.config import LANG_COLORS


def xml_escape(value: object, *, quote: bool = True) -> str:
    """Escape text for safe embedding in SVG/XML."""
    text = str(value)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    if quote:
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#39;")
    return text


def truncate(text: str, max_len: int, suffix: str = "...") -> str:
    """Truncate text to max_len, appending suffix if shortened."""
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


def lang_color(lang: str | None, palette: Mapping[str, str] | None = None, default: str = "#8b8b8b") -> str:
    """Return the display color for a programming language."""
    if lang is None:
        return default
    colors = palette if palette is not None else LANG_COLORS
    return colors.get(lang, default)


def fmt_int(value: int | None) -> str:
    """Format an integer with comma separators, or 'n/a' if None."""
    if value is None:
        return "n/a"
    return f"{int(value):,}"
