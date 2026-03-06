"""Simple style helpers for SVG profile cards."""

from __future__ import annotations

from scripts.config import BORDER, BG_CARD, FONT_SANS, TEXT, TEXT_BRIGHT, TEXT_DIM

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
        f'<text x="{width - pad}" y="{y}" fill="{TEXT_DIM}" font-size="{size}" '
        f'font-family="{FONT_SANS}" text-anchor="end">{text}</text>'
    )


def label_text(text: str, *, x: int | float, y: int | float) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{TEXT}" font-size="{LABEL_SIZE}" '
        f'font-family="{FONT_SANS}">{text}</text>'
    )


def meta_text(text: str, *, x: int | float, y: int | float, color: str = TEXT_DIM, size: int = 10) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
        f'font-family="{FONT_SANS}">{text}</text>'
    )
