"""Shared SVG text and formatting utilities."""

from __future__ import annotations

from typing import Mapping

from scripts.core.config import LANG_COLORS, LANG_DEFAULT


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


def lang_color(lang: str | None, palette: Mapping[str, str] | None = None, default: str = LANG_DEFAULT) -> str:
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


def fmt_compact(value: int | None) -> str:
    """Format an integer to <=4 numerals, k/M-scaled (DESIGN_SPEC Part 1.8).

    Keeps <10,000 as comma-grouped digits ('8,104'); scales 10k+ to 'k' and 1M+
    to 'M' so no rendered value exceeds four numerals ('12k', '123k', '1.2M').
    """
    if value is None:
        return "n/a"
    try:
        n = int(value)
    except (TypeError, ValueError):
        return "n/a"
    a = abs(n)
    if a < 10_000:
        return f"{n:,}"
    if a < 1_000_000:
        return f"{n / 1000:.0f}k"
    return f"{n / 1_000_000:.1f}M"
