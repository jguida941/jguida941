"""Reusable, token-driven SVG components (Power BI IA x Apple restraint).

Every text size resolves from config.TYPE_SCALE; colors from the token source;
spacing from config.SPACE. Hierarchy is expressed via the scale + weight, not
ad-hoc sizes. See docs/DESIGN_SPEC.md (Part 3) for each component's contract.
"""
from __future__ import annotations

from scripts.core.config import (
    CYAN,
    FONT_SANS,
    GLASS_HAIRLINE_HEX,
    GLASS_TILE_SHADE_HEX,
    GREEN,
    RED,
    SPACE,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
    TYPE_SCALE,
    YELLOW,
)
from scripts.rendering.glass_kit import chip as _chip
from scripts.rendering.glass_kit import glass_tile
from scripts.rendering.glass_kit import icon as _icon
from scripts.rendering.glass_kit import progress_ring as _progress_ring
from scripts.rendering.glass_kit import sparkline as _sparkline
from scripts.rendering.svg_utils import lang_color as _lang_color
from scripts.rendering.svg_utils import truncate as _truncate
from scripts.rendering.svg_utils import xml_escape as _xml_escape


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


# Status -> (tone color, distinct icon shape). success != danger != warning
# shape, so state survives desaturation (DESIGN_SPEC 3.6 / Power BI CVD-safety).
_STATUS_TONE = {
    "success": (GREEN, "check"),
    "warning": (YELLOW, "alert"),
    "danger": (RED, "cross"),
    "neutral": (TEXT_DIM, "dot"),
}


def status_chip(x: float, y: float, *, label: str, status: str = "neutral", height: float = 22) -> str:
    """A tinted status pill: state conveyed by icon SHAPE *and* text label, never
    hue alone. DESIGN_SPEC 3.6 — hue in {success,warning,danger,neutral}."""
    color, icon_name = _STATUS_TONE.get(status, _STATUS_TONE["neutral"])
    return _chip(x, y, label, color=color, icon_name=icon_name, tone="accent", height=height)


def donut_gauge(
    cx: float,
    cy: float,
    *,
    value: float,
    max_value: float = 100.0,
    label: str | None = None,
    radius: float = 34,
    stroke: float = 8,
    color: str = CYAN,
) -> str:
    """A single value in [0, max_value] as a part-to-whole ring with a token-sized
    (>=12) center label. DESIGN_SPEC 3.9 — the only sanctioned circular chart here;
    comparisons use bars. No sublabel (progress_ring's sublabel is sub-floor)."""
    mv = float(max_value) or 1.0
    pct = max(0.0, min(100.0, float(value) / mv * 100.0))
    center = label if label is not None else f"{round(pct)}%"
    return _progress_ring(cx, cy, radius, pct, color=color, stroke=stroke, label=center, label_size=20)


def trend_panel(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    series: list[float],
    axis_label: str | None = None,
    peak_label: str | None = None,
    uid: str = "trend",
    color: str = CYAN,
) -> str:
    """A restrained continuous-time trend (DESIGN_SPEC 3.8): a sparkline with
    stroke >=1.5 and optional axis/peak labels at the caption token (>=12px)."""
    pts = [float(v) for v in (series or []) if v is not None]
    top_pad = 16 if axis_label else 0
    bot_pad = 16 if peak_label else 0
    parts: list[str] = []
    if axis_label:
        parts.append(text(axis_label, x + w, y + 10, token="caption", color=TEXT_DIM, anchor="end"))
    if pts:
        parts.append(_sparkline(pts, x, y + top_pad, w, h - top_pad - bot_pad, color=color, uid=uid))
    if peak_label:
        parts.append(text(peak_label, x + w, y + h, token="caption", color=TEXT_DIM, anchor="end"))
    return "".join(parts)


def language_bar(
    x: float,
    y: float,
    w: float,
    *,
    segments: list[tuple[str, float]],
    height: float = 14,
    legend_cols: int = 3,
    legend_row_h: float = 28,
) -> tuple[str, float]:
    """A flat part-to-whole language bar + name+value legend. DESIGN_SPEC 3.10.

    `segments` are pre-aggregated ``(name, percent)`` pairs summing to ~100, already
    capped at <=6 (+ 'Other'). Renders a flat stacked bar (one 1px hairline rim, no
    sheen gradient) using each language's identity color, then a uniform legend where
    every segment carries both a name and a percent. Returns ``(svg, legend_bottom_y)``.
    """
    parts: list[str] = [
        f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(height)}" rx="6" '
        f'fill="{GLASS_HAIRLINE_HEX}" fill-opacity="0.10"/>',
        f'<clipPath id="langbar"><rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" '
        f'height="{_n(height)}" rx="6"/></clipPath>',
        '<g clip-path="url(#langbar)">',
    ]
    cx = float(x)
    n = len(segments)
    for i, (name, pct) in enumerate(segments):
        end = x + w if i == n - 1 else cx + w * float(pct) / 100.0
        seg_w = max(0.0, end - cx)
        parts.append(
            f'<rect x="{_n(cx)}" y="{_n(y)}" width="{_n(seg_w)}" height="{_n(height)}" '
            f'fill="{_lang_color(name)}"/>'
        )
        if i < n - 1 and seg_w > 0:
            parts.append(
                f'<rect x="{_n(end - 0.75)}" y="{_n(y)}" width="1.5" height="{_n(height)}" '
                f'fill="{GLASS_TILE_SHADE_HEX}" fill-opacity="0.5"/>'
            )
        cx = end
    parts.append("</g>")
    parts.append(
        f'<rect x="{_n(x + 0.5)}" y="{_n(y + 0.5)}" width="{_n(w - 1)}" height="{_n(height - 1)}" '
        f'rx="6" fill="none" stroke="{GLASS_HAIRLINE_HEX}" stroke-opacity="0.18" stroke-width="1"/>'
    )

    legend_top = y + height + 28
    col_w = w / legend_cols
    last_row = 0
    for i, (name, pct) in enumerate(segments):
        col, row = i % legend_cols, i // legend_cols
        last_row = max(last_row, row)
        cell_x = x + col * col_w
        base = legend_top + row * legend_row_h
        parts.append(
            f'<circle cx="{_n(cell_x + 5)}" cy="{_n(base - 4)}" r="5" fill="{_lang_color(name)}"/>'
        )
        parts.append(text(_xml_escape(_truncate(name, 16)), cell_x + 18, base, token="caption", color=TEXT))
        parts.append(
            text(f"{float(pct):.1f}%", cell_x + col_w - 16, base, token="caption", color=TEXT_BRIGHT, anchor="end")
        )
    return "".join(parts), legend_top + last_row * legend_row_h


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
