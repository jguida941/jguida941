"""Reusable, token-driven SVG components (Power BI IA x Apple restraint).

Every text size resolves from config.TYPE_SCALE; colors from the token source;
spacing from config.SPACE. Hierarchy is expressed via the scale + weight, not
ad-hoc sizes. See docs/DESIGN_SPEC.md (Part 3) for each component's contract.
"""
from __future__ import annotations

from scripts.core.config import (
    FONT_SANS,
    GLASS_HAIRLINE_HEX,
    SPACE,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
    TYPE_SCALE,
)
from scripts.rendering.glass_kit import glass_tile
from scripts.rendering.glass_kit import icon as _icon


def _n(v: float) -> str:
    return f"{round(float(v), 2):g}"


def text(
    content: str,
    x: float,
    y: float,
    *,
    token: str = "body",
    color: str = TEXT,
    anchor: str = "start",
    tracking: float | None = None,
) -> str:
    """A text node whose size/weight come from the type scale (no off-scale sizes)."""
    size, weight = TYPE_SCALE[token]
    lt = f' letter-spacing="{tracking}"' if tracking else ""
    an = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return (
        f'<text x="{_n(x)}" y="{_n(y)}" fill="{color}" font-size="{size}" '
        f'font-family="{FONT_SANS}" font-weight="{weight}"{lt}{an}>{content}</text>'
    )


def section_header(
    x: float,
    y: float,
    title: str,
    *,
    width: float,
    eyebrow: str | None = None,
    right_text: str | None = None,
    pad: float = 24,
) -> tuple[str, float]:
    """Eyebrow + single title + optional right meta + a 1px hairline divider.

    Returns (svg, content_top_y). Replaces the per-card gradient ribbon with a
    quiet hairline (DESIGN_SPEC 3.5). The title is the card's single <text> title.
    """
    parts: list[str] = []
    ty = y
    if eyebrow:
        parts.append(text(eyebrow.upper(), x, ty, token="eyebrow", color=TEXT_DIM, tracking=1.2))
        ty += 18
    parts.append(text(title, x, ty + 6, token="title", color=TEXT_BRIGHT))
    if right_text:
        parts.append(
            text(right_text, x + width - pad * 2, ty + 4, token="caption", color=TEXT_DIM, anchor="end")
        )
    hy = ty + 18
    parts.append(
        f'<rect x="{_n(x)}" y="{_n(hy)}" width="{_n(width - pad * 2)}" height="1" '
        f'fill="{GLASS_HAIRLINE_HEX}" fill-opacity="0.14"/>'
    )
    return "".join(parts), hy + 1


def primary_kpi(
    x: float,
    y: float,
    *,
    value: str,
    label: str,
    sublabel: str | None = None,
) -> str:
    """The one dominant KPI (display size, top-left). DESIGN_SPEC 3.2.

    `y` is the value's text baseline. Exactly one of these per metric surface; its
    value is the largest text on the card (enforced by the hierarchy contract).
    """
    parts = [text(value, x, y, token="display", color=TEXT_BRIGHT)]
    parts.append(text(label, x, y + 24, token="body", color=TEXT))
    if sublabel:
        parts.append(text(sublabel, x, y + 42, token="caption", color=TEXT_DIM))
    return "".join(parts)


def metric_tile(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    value: str,
    label: str,
    icon_name: str | None = None,
    caption: str | None = None,
    value_token: str = "metric",
) -> str:
    """A secondary metric cell: neutral icon + value + label (+ optional caption).

    DESIGN_SPEC 3.3/3.4. Value uses a smaller scale token than `primary_kpi` so the
    KPI always dominates; icon is neutral (tertiary ink) — color is reserved for
    status, not decoration. The optional third-line `caption` (e.g. a date range)
    rides at the caption token without scattering raw <text> at call sites.
    """
    pad = SPACE["lg"]
    parts = [glass_tile(x, y, w, h)]
    if icon_name:
        parts.append(_icon(icon_name, x + pad, y + 13, size=15, color=TEXT_DIM))
    if caption:
        vy = y + h - 40
        parts.append(text(value, x + pad, vy, token=value_token, color=TEXT_BRIGHT))
        parts.append(text(label, x + pad, vy + 16, token="caption", color=TEXT_DIM))
        parts.append(text(caption, x + pad, vy + 31, token="caption", color=TEXT_DIM))
    else:
        vy = y + h - 24
        parts.append(text(value, x + pad, vy, token=value_token, color=TEXT_BRIGHT))
        parts.append(text(label, x + pad, vy + 15, token="caption", color=TEXT_DIM))
    return "".join(parts)


def empty_state(cx: float, cy: float, message: str, *, icon_name: str | None = None) -> str:
    """A centered, honest empty state — explanatory text, never fabricated numbers.

    DESIGN_SPEC 3.13. Caller renders this iff the data count is zero.
    """
    parts = []
    ty = cy
    if icon_name:
        parts.append(_icon(icon_name, cx - 11, cy - 26, size=22, color=TEXT_DIM))
        ty = cy + 6
    parts.append(text(message, cx, ty, token="body", color=TEXT_DIM, anchor="middle"))
    return "".join(parts)
