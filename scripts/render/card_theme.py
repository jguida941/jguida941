"""Simple style helpers for SVG profile cards."""

from __future__ import annotations

from scripts.config import BLUE, BORDER, BG_CARD, CYAN, FONT_SANS, ORANGE, TEXT, TEXT_BRIGHT

TITLE_Y = 29
TITLE_SIZE = 16
SUBTITLE_SIZE = 11
LABEL_SIZE = 11
VALUE_SIZE = 18


def card_bg(width: int | float, height: int | float, rx: int = 14) -> str:
    return (
        f'<rect width="{width}" height="{height}" rx="{rx}" '
        f'fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>'
    )


def title_left(text: str, *, x: int | float = 20, y: int | float = TITLE_Y, size: int = TITLE_SIZE) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{TEXT_BRIGHT}" font-size="{size}" '
        f'font-family="{FONT_SANS}" font-weight="700">{text}</text>'
    )


def title_right(
    text: str,
    *,
    width: int | float,
    pad: int | float = 20,
    y: int | float = TITLE_Y,
    size: int = SUBTITLE_SIZE,
) -> str:
    return (
        f'<text x="{width - pad}" y="{y}" fill="{TEXT}" font-size="{size}" '
        f'font-family="{FONT_SANS}" text-anchor="end">{text}</text>'
    )


def label_text(text: str, *, x: int | float, y: int | float) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{TEXT}" font-size="{LABEL_SIZE}" '
        f'font-family="{FONT_SANS}">{text}</text>'
    )


def meta_text(text: str, *, x: int | float, y: int | float, color: str = TEXT, size: int = 10) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
        f'font-family="{FONT_SANS}">{text}</text>'
    )


def title_accent(
    *,
    width: int | float,
    pad: int | float = 20,
    y: int | float = 34,
    height: int | float = 3,
    gap: int | float = 6,
) -> str:
    seg_w = (width - pad * 2 - gap * 2) / 3
    x1 = pad
    x2 = x1 + seg_w + gap
    x3 = x2 + seg_w + gap
    return (
        f'<rect x="{x1}" y="{y}" width="{seg_w}" height="{height}" rx="2" fill="{BLUE}" />'
        f'<rect x="{x2}" y="{y}" width="{seg_w}" height="{height}" rx="2" fill="{CYAN}" />'
        f'<rect x="{x3}" y="{y}" width="{seg_w}" height="{height}" rx="2" fill="{ORANGE}" />'
    )
