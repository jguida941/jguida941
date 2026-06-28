"""Apple/glassmorphism SVG component library for profile cards.

GitHub serves README ``<img>`` SVGs through the camo proxy as raw bytes (no SVG
sanitizer), so ``<filter>`` (feGaussianBlur/feTurbulence/feDropShadow), gradients,
and ``<clipPath>`` all render in-browser. There is no DOM behind an ``<img>``, so
"frosted glass" is faked inside each card: a near-black base + blurred accent
color blobs (clipped) + a translucent frosted panel + sheen + rim + faint grain.

Constraints honored: no external fonts, no ``<script>``, no ``<foreignObject>``;
translucency uses ``fill-opacity``/``stop-opacity`` (never ``rgba()`` in fills).
"""

from __future__ import annotations

import math

from scripts.core.config import (
    BG_DARK,
    CYAN,
    FONT_SANS,
    GLASS_HAIRLINE_HEX,
    GLASS_HAIRLINE_OP,
    GLASS_HAIRLINE_STRONG_OP,
    GLASS_INSET,
    GLASS_RX,
    GLASS_SHADOW_HEX,
    GLASS_SHADOW_OP,
    GLASS_SHEEN_HEX,
    GLASS_TILE_RX,
    GLASS_TILE_SHADE_HEX,
    GRAD_BLUE_CYAN,
    GRAD_PURPLE_BLUE,
    SURFACE_BACKDROP,
    SURFACE_BASE,
    SURFACE_RAISED,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
    BLUE,
    PURPLE,
)

# Backdrop blob accent hues (subtle color that bleeds through the frosted panel).
_BLOB_HUES = (BLUE, PURPLE, CYAN)

# Near-black backdrop so blurred color blobs read as glass refraction.
_BACKDROP = SURFACE_BACKDROP


def _f(value: float) -> str:
    """Compact number formatting for SVG coordinates."""
    return f"{round(float(value), 2):g}"


# --------------------------------------------------------------------------- #
# Shared defs
# --------------------------------------------------------------------------- #
def glass_defs() -> str:
    """Return the shared ``<defs>`` block (gradients + filters) for one card.

    Each card is its own SVG file, so the fixed ``gk-`` ids never collide.
    """
    return (
        "<defs>"
        # vertical white sheen (bright top edge fading out)
        '<linearGradient id="gk-sheen" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{GLASS_SHEEN_HEX}" stop-opacity="0.20"/>'
        f'<stop offset="0.06" stop-color="{GLASS_SHEEN_HEX}" stop-opacity="0.06"/>'
        f'<stop offset="0.5" stop-color="{GLASS_SHEEN_HEX}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{GLASS_TILE_SHADE_HEX}" stop-opacity="0.10"/>'
        "</linearGradient>"
        # inner tile gradient (subtle top light -> base shade)
        '<linearGradient id="gk-tile" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{GLASS_SHEEN_HEX}" stop-opacity="0.08"/>'
        f'<stop offset="1" stop-color="{GLASS_TILE_SHADE_HEX}" stop-opacity="0.22"/>'
        "</linearGradient>"
        # top-bright hairline rim gradient (1px stroke)
        '<linearGradient id="gk-rim" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{GLASS_SHEEN_HEX}" stop-opacity="0.45"/>'
        f'<stop offset="0.4" stop-color="{GLASS_HAIRLINE_HEX}" stop-opacity="0.12"/>'
        f'<stop offset="1" stop-color="{GLASS_HAIRLINE_HEX}" stop-opacity="0.05"/>'
        "</linearGradient>"
        # drop shadow that lifts the panel off the page
        '<filter id="gk-shadow" x="-40%" y="-40%" width="180%" height="180%">'
        f'<feDropShadow dx="0" dy="10" stdDeviation="16" '
        f'flood-color="{GLASS_SHADOW_HEX}" flood-opacity="{GLASS_SHADOW_OP}"/>'
        "</filter>"
        # heavy blur for the backdrop color blobs
        '<filter id="gk-blob" x="-80%" y="-80%" width="260%" height="260%">'
        '<feGaussianBlur stdDeviation="34"/>'
        "</filter>"
        # faint frost grain
        '<filter id="gk-grain" x="0%" y="0%" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" '
        'stitchTiles="stitch" result="n"/>'
        '<feColorMatrix in="n" type="matrix" '
        'values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.04 0"/>'
        "</filter>"
        "</defs>"
    )


# --------------------------------------------------------------------------- #
# Panels & tiles
# --------------------------------------------------------------------------- #
def glass_panel(
    width: float,
    height: float,
    *,
    rx: int = GLASS_RX,
    inset: int = GLASS_INSET,
    base: str = SURFACE_BASE,
    blobs: tuple[str, ...] = _BLOB_HUES,
    include_defs: bool = True,
) -> str:
    """Full frosted-glass card background. Drop-in replacement for ``card_bg``.

    Draws: drop shadow + dark base, blurred accent blobs (clipped), frosted
    translucent panel, top sheen, faint grain, 1px top-bright rim, specular line.
    Keeps everything inside ``inset`` so the shadow never clips the viewBox.
    """
    x = inset
    y = inset
    w = width - inset * 2
    h = height - inset * 2
    clip = "gk-clip"

    parts: list[str] = []
    if include_defs:
        parts.append(glass_defs())
    # clip blobs to the card shape
    parts.append(
        f'<clipPath id="{clip}"><rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" '
        f'height="{_f(h)}" rx="{rx}"/></clipPath>'
    )
    # dark base + lift shadow
    parts.append(
        f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" rx="{rx}" '
        f'fill="{_BACKDROP}" filter="url(#gk-shadow)"/>'
    )
    # blurred color blobs (the thing the glass "refracts")
    blob_layer = [f'<g clip-path="url(#{clip})" filter="url(#gk-blob)">']
    hues = list(blobs) if blobs else []
    if hues:
        positions = [
            (x + w * 0.08, y + h * 0.10, max(h, 120) * 0.62, 0.30),
            (x + w * 0.96, y + h * 0.96, max(h, 120) * 0.70, 0.26),
            (x + w * 0.62, y - h * 0.08, max(h, 120) * 0.45, 0.20),
        ]
        for i, (cx, cy, r, op) in enumerate(positions):
            hue = hues[i % len(hues)]
            # Ellipse (not circle) so cards with a "no <circle>" contract stay clean.
            blob_layer.append(
                f'<ellipse cx="{_f(cx)}" cy="{_f(cy)}" rx="{_f(r)}" ry="{_f(r * 0.82)}" '
                f'fill="{hue}" fill-opacity="{op}"/>'
            )
    blob_layer.append("</g>")
    parts.append("".join(blob_layer))
    # frosted translucent panel (lets blob color bleed through, keeps text legible)
    parts.append(
        f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" rx="{rx}" '
        f'fill="{base}" fill-opacity="0.74"/>'
    )
    # top sheen + faint grain (grain clipped to card)
    parts.append(
        f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" rx="{rx}" '
        f'fill="url(#gk-sheen)"/>'
    )
    parts.append(
        f'<g clip-path="url(#{clip})"><rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" '
        f'height="{_f(h)}" filter="url(#gk-grain)"/></g>'
    )
    # 1px top-bright rim
    parts.append(
        f'<rect x="{_f(x + 0.5)}" y="{_f(y + 0.5)}" width="{_f(w - 1)}" '
        f'height="{_f(h - 1)}" rx="{rx}" fill="none" stroke="url(#gk-rim)" '
        f'stroke-width="1"/>'
    )
    # specular top line (brightest at center)
    parts.append(
        f'<rect x="{_f(x + rx)}" y="{_f(y + 1.5)}" width="{_f(w - rx * 2)}" '
        f'height="1" fill="{GLASS_SHEEN_HEX}" fill-opacity="0.0"/>'
    )
    return "".join(parts)


def glass_tile(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    rx: int = GLASS_TILE_RX,
    accent: str | None = None,
    accent_w: float | None = None,
    base: str = SURFACE_RAISED,
) -> str:
    """Inner metric tile. Lighter frosted lift over the panel (no per-tile filter)."""
    parts = [
        # base fill (translucent so the panel/backdrop shows faintly through)
        f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" rx="{rx}" '
        f'fill="{base}" fill-opacity="0.55"/>',
        # tile sheen gradient
        f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" rx="{rx}" '
        f'fill="url(#gk-tile)"/>',
        # hairline border
        f'<rect x="{_f(x + 0.5)}" y="{_f(y + 0.5)}" width="{_f(w - 1)}" '
        f'height="{_f(h - 1)}" rx="{rx}" fill="none" stroke="{GLASS_HAIRLINE_HEX}" '
        f'stroke-opacity="{GLASS_HAIRLINE_OP}" stroke-width="1"/>',
        # top inner highlight
        f'<rect x="{_f(x + rx * 0.5)}" y="{_f(y + 1)}" width="{_f(w - rx)}" height="1" '
        f'rx="0.5" fill="{GLASS_SHEEN_HEX}" fill-opacity="0.14"/>',
    ]
    # NOTE: the per-tile colored accent bar was removed — Apple uses one accent per
    # context, not a stripe on every tile (a common "AI look" tell). `accent`/`accent_w`
    # are kept for back-compat but intentionally no longer rendered.
    _ = (accent, accent_w)
    return "".join(parts)


def accent_ribbon(
    width: float,
    *,
    pad: float = 20,
    y: float = 36,
    h: float = 3,
    grad: tuple[str, str] = GRAD_BLUE_CYAN,
    uid: str = "gk-ribbon",
) -> str:
    """One calm gradient ribbon (replaces the repeated tri-color underline)."""
    seg = width - pad * 2
    return (
        f'<linearGradient id="{uid}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{grad[0]}" stop-opacity="0.95"/>'
        f'<stop offset="0.55" stop-color="{grad[1]}" stop-opacity="0.85"/>'
        f'<stop offset="1" stop-color="{grad[1]}" stop-opacity="0"/>'
        f"</linearGradient>"
        f'<rect x="{_f(pad)}" y="{_f(y)}" width="{_f(seg)}" height="{_f(h)}" '
        f'rx="{_f(h / 2)}" fill="url(#{uid})"/>'
    )


def eyebrow_text(text: str, *, x: float, y: float, color: str = TEXT_DIM, size: int = 10) -> str:
    """Small, tracked, uppercase caption (Apple eyebrow style)."""
    return (
        f'<text x="{_f(x)}" y="{_f(y)}" fill="{color}" font-size="{size}" '
        f'font-family="{FONT_SANS}" font-weight="600" letter-spacing="1.2" '
        f'text-transform="uppercase">{text}</text>'
    )


# --------------------------------------------------------------------------- #
# Data viz primitives
# --------------------------------------------------------------------------- #
def sparkline(
    points: list[float],
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    color: str = CYAN,
    fill: bool = True,
    width: float = 1.8,
    uid: str | None = None,
) -> str:
    """A glowing sparkline with optional gradient area fill + end dot."""
    pts = [float(p) for p in points if p is not None]
    if not pts:
        return ""
    if len(pts) == 1:
        pts = [pts[0], pts[0]]
    lo, hi = min(pts), max(pts)
    rng = (hi - lo) or 1.0
    n = len(pts)
    step = w / (n - 1)
    coords = [(x + i * step, y + h - (p - lo) / rng * h) for i, p in enumerate(pts)]
    poly = " ".join(f"{_f(px)},{_f(py)}" for px, py in coords)
    parts: list[str] = []
    if fill:
        gid = uid or f"spk{int(x)}-{int(y)}"
        area = f"{_f(x)},{_f(y + h)} {poly} {_f(x + (n - 1) * step)},{_f(y + h)}"
        parts.append(
            f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{color}" stop-opacity="0.30"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/>'
            f"</linearGradient>"
            f'<polygon points="{area}" fill="url(#{gid})"/>'
        )
    parts.append(
        f'<polyline points="{poly}" fill="none" stroke="{color}" '
        f'stroke-width="{_f(width)}" stroke-linecap="round" stroke-linejoin="round"/>'
    )
    ex, ey = coords[-1]
    parts.append(f'<circle cx="{_f(ex)}" cy="{_f(ey)}" r="{_f(width + 1.3)}" fill="{color}"/>')
    return "".join(parts)


def progress_bar(
    x: float,
    y: float,
    w: float,
    h: float,
    pct: float,
    *,
    color: str = CYAN,
    track_op: float = 0.14,
    rx: float | None = None,
) -> str:
    """Rounded progress/track bar."""
    rad = h / 2 if rx is None else rx
    p = max(0.0, min(100.0, float(pct)))
    fill_w = max(0.0, w * p / 100.0)
    parts = [
        f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" rx="{_f(rad)}" '
        f'fill="{GLASS_HAIRLINE_HEX}" fill-opacity="{track_op}"/>'
    ]
    if fill_w > 0:
        parts.append(
            f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(fill_w)}" height="{_f(h)}" '
            f'rx="{_f(rad)}" fill="{color}"/>'
        )
    return "".join(parts)


def progress_ring(
    cx: float,
    cy: float,
    r: float,
    pct: float,
    *,
    color: str = CYAN,
    stroke: float = 7,
    track_op: float = 0.16,
    label: str | None = None,
    label_size: int = 15,
    label_color: str = TEXT_BRIGHT,
    sublabel: str | None = None,
) -> str:
    """A donut/ring progress meter with optional centered label."""
    p = max(0.0, min(100.0, float(pct)))
    circ = 2 * math.pi * r
    dash = circ * p / 100.0
    gap = circ - dash
    parts = [
        f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r)}" fill="none" '
        f'stroke="{GLASS_HAIRLINE_HEX}" stroke-opacity="{track_op}" stroke-width="{_f(stroke)}"/>',
        f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r)}" fill="none" stroke="{color}" '
        f'stroke-width="{_f(stroke)}" stroke-linecap="round" '
        f'stroke-dasharray="{_f(dash)} {_f(gap)}" transform="rotate(-90 {_f(cx)} {_f(cy)})"/>',
    ]
    if label is not None:
        dy = -2 if sublabel else 5
        parts.append(
            f'<text x="{_f(cx)}" y="{_f(cy + dy)}" fill="{label_color}" '
            f'font-size="{label_size}" font-family="{FONT_SANS}" font-weight="700" '
            f'text-anchor="middle">{label}</text>'
        )
        if sublabel:
            parts.append(
                f'<text x="{_f(cx)}" y="{_f(cy + 13)}" fill="{TEXT_DIM}" font-size="8.5" '
                f'font-family="{FONT_SANS}" text-anchor="middle" '
                f'letter-spacing="0.5">{sublabel}</text>'
            )
    return "".join(parts)


def chip_width(text: str, *, size: int = 11, icon: bool = False) -> float:
    """Estimate chip width for layout."""
    return len(text) * size * 0.62 + 22 + (15 if icon else 0)


def chip(
    x: float,
    y: float,
    text: str,
    *,
    color: str = CYAN,
    icon_name: str | None = None,
    filled: bool = False,  # back-compat, unused
    tone: str = "neutral",
    size: int = 11,
    height: float = 22,
    width: float | None = None,
) -> str:
    """An Apple-style tag: a soft FILL, no stroke (fill OR label, never both).

    tone="neutral" -> grey fill + secondary text (the workhorse, Recipe A).
    tone="accent"  -> low-opacity hue fill + same hue text/icon (Recipe B; use at
    most once per card). Color lives only on the fill+text, never a 1px outline.
    """
    _ = filled
    w = width if width is not None else chip_width(text, size=size, icon=bool(icon_name))
    rad = 7  # small concentric radius, not a full pill
    icon_sz = 12
    text_x = x + 10 + (icon_sz + 3 if icon_name else 0)
    if tone == "accent":
        fill, fill_op, fg = color, 0.14, color
    else:
        fill, fill_op, fg = TEXT_DIM, 0.16, TEXT
    parts = [
        f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(height)}" '
        f'rx="{rad}" fill="{fill}" fill-opacity="{fill_op}"/>'
    ]
    if icon_name:
        parts.append(icon(icon_name, x + 9, y + (height - icon_sz) / 2, size=icon_sz, color=fg))
    parts.append(
        f'<text x="{_f(text_x)}" y="{_f(y + height / 2 + size * 0.34)}" fill="{fg}" '
        f'font-size="{size}" font-family="{FONT_SANS}" font-weight="500">{text}</text>'
    )
    return "".join(parts)


def metadata(
    x: float,
    y: float,
    text: str,
    *,
    icon_name: str | None = None,
    color: str = TEXT,
    icon_color: str | None = None,
    size: int = 12,
    icon_size: int = 13,
) -> str:
    """Inline metadata (Apple App-Store style): optional leading symbol + secondary
    text, NO container. For recency/measurements joined with ' · ' separators."""
    parts = []
    tx = x
    if icon_name:
        parts.append(icon(icon_name, x, y - icon_size + 2.5, size=icon_size, color=icon_color or color))
        tx = x + icon_size + 5
    parts.append(
        f'<text x="{_f(tx)}" y="{_f(y)}" fill="{color}" font-size="{size}" '
        f'font-family="{FONT_SANS}" font-weight="400">{text}</text>'
    )
    return "".join(parts)


# --------------------------------------------------------------------------- #
# Icons (SF-Symbols-like line set, 24x24 grid, scaled)
# --------------------------------------------------------------------------- #
# Each entry: (mode, body) where mode is "stroke" or "fill" or "mixed".
_ICONS: dict[str, tuple[str, str]] = {
    "star": ("fill", '<path d="M12 17.3 18.2 21l-1.6-7 5.4-4.7-7.2-.6L12 2 9.2 8.7 2 9.3l5.5 4.7L5.8 21z"/>'),
    "fork": (
        "mixed",
        '<circle cx="6" cy="5" r="2.4" fill="C"/><circle cx="18" cy="5" r="2.4" fill="C"/>'
        '<circle cx="12" cy="19" r="2.4" fill="C"/>'
        '<path d="M6 7.4V10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7.4M12 12v4.6" '
        'fill="none" stroke="C" stroke-width="2" stroke-linecap="round"/>',
    ),
    "commit": (
        "stroke",
        '<circle cx="12" cy="12" r="3.4"/><path d="M2 12h5.2M16.8 12H22"/>',
    ),
    "branch": (
        "mixed",
        '<circle cx="6" cy="6" r="2.4" fill="none" stroke="C" stroke-width="2"/>'
        '<circle cx="6" cy="18" r="2.4" fill="none" stroke="C" stroke-width="2"/>'
        '<circle cx="18" cy="8" r="2.4" fill="none" stroke="C" stroke-width="2"/>'
        '<path d="M6 8.4v7.2M6 12h7a3 3 0 0 0 3-3v-.6" fill="none" stroke="C" '
        'stroke-width="2" stroke-linecap="round"/>',
    ),
    "lock": (
        "mixed",
        '<rect x="5" y="10.5" width="14" height="9.5" rx="2.2" fill="C"/>'
        '<path d="M8 10.5V8a4 4 0 0 1 8 0v2.5" fill="none" stroke="C" stroke-width="2"/>',
    ),
    "ci_check": (
        "stroke",
        '<circle cx="12" cy="12" r="9"/><path d="M8 12.4l2.6 2.6L16.4 9"/>',
    ),
    "rocket": (
        "mixed",
        '<path d="M12 2c2.6 2 4 5.2 4 8.4 0 1.6-.5 3.1-1.4 4.4h-5.2C8.5 13.5 8 12 8 10.4 8 7.2 9.4 4 12 2z" '
        'fill="C"/><circle cx="12" cy="9" r="1.7" fill="B"/>'
        '<path d="M9.4 16.4l-1.4 3.6 3.2-1.6M14.6 16.4l1.4 3.6-3.2-1.6" '
        'fill="none" stroke="C" stroke-width="1.6" stroke-linejoin="round"/>',
    ),
    "fire": (
        "fill",
        '<path d="M12.5 2c.6 2.8 3.5 4 3.5 7.5a4 4 0 0 1-8 .3c0-1.4.5-2.4 1.2-3.2.1 1 .7 1.7 1.5 1.8'
        '-.7-2.3.6-4.6 1.8-6.4z"/>',
    ),
    "clock": (
        "stroke",
        '<circle cx="12" cy="12" r="9"/><path d="M12 7v5.2l3.4 1.8"/>',
    ),
    "trend_up": (
        "stroke",
        '<path d="M3 17l6.5-6.5 3.5 3.5L21 6"/><path d="M15.5 6H21v5.5"/>',
    ),
    "trend_down": (
        "stroke",
        '<path d="M3 7l6.5 6.5 3.5-3.5L21 18"/><path d="M15.5 18H21v-5.5"/>',
    ),
    "pr_merged": (
        "stroke",
        '<circle cx="7" cy="6" r="2.4"/><circle cx="7" cy="18" r="2.4"/><circle cx="18" cy="14" r="2.4"/>'
        '<path d="M7 8.4v7.2M7 9a8 8 0 0 0 8.6 7"/>',
    ),
    "release_tag": (
        "mixed",
        '<path d="M3.5 11.5V4.5a1 1 0 0 1 1-1h7l8.5 8.5a1.4 1.4 0 0 1 0 2l-6.5 6.5a1.4 1.4 0 0 1-2 0'
        'l-8-8z" fill="none" stroke="C" stroke-width="2" stroke-linejoin="round"/>'
        '<circle cx="7.5" cy="7.5" r="1.5" fill="C"/>',
    ),
    "workflow": (
        "fill",
        '<path d="M13 2L4 14h6.5L9 22l9.5-12.5H12L13 2z"/>',
    ),
    "test": (
        "stroke",
        '<path d="M9 3h6M10 3v6L5.2 18.4A1.2 1.2 0 0 0 6.3 20h11.4a1.2 1.2 0 0 0 1.1-1.6L14 9V3"/>'
        '<path d="M7.5 14.5h9"/>',
    ),
    "code": ("stroke", '<path d="M9 8l-4 4 4 4M15 8l4 4-4 4"/>'),
    "globe": ("stroke", '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.4 2.6 15.6 0 18M12 3c-2.6 2.4-2.6 15.6 0 18"/>'),
    "calendar": (
        "stroke",
        '<rect x="3.5" y="5" width="17" height="15.5" rx="2.2"/><path d="M3.5 9.5h17M8 3v4M16 3v4"/>',
    ),
}


def icon(name: str, x: float, y: float, *, size: float = 14, color: str = TEXT, opacity: float = 1.0) -> str:
    """Render a 24x24-grid icon translated/scaled to (x, y) at the given size."""
    if name == "lang_dot":
        r = size / 2
        return f'<circle cx="{_f(x + r)}" cy="{_f(y + r)}" r="{_f(r)}" fill="{color}"/>'
    entry = _ICONS.get(name)
    if not entry:
        return ""
    mode, body = entry
    # "B" = backdrop placeholder (token), "C" = the icon color. Replace B first so a
    # color hex can never collide with the backdrop marker.
    body = body.replace("B", SURFACE_BACKDROP).replace("C", color)
    scale = size / 24.0
    op = f' opacity="{opacity}"' if opacity < 1.0 else ""
    if mode == "stroke":
        attrs = (
            f'fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"'
        )
    elif mode == "fill":
        attrs = f'fill="{color}"'
    else:  # mixed: each shape carries its own attrs
        attrs = ""
    return (
        f'<g transform="translate({_f(x)},{_f(y)}) scale({_f(scale)})" {attrs}{op}>'
        f"{body}</g>"
    )
