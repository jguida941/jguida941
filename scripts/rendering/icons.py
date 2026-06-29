"""Vendored Lucide icon set (https://lucide.dev) — canonical 24x24 line geometry.

Lucide is ISC-licensed (Copyright (c) 2024 Lucide Contributors). Each entry below
is the inner geometry of a canonical Lucide icon (geometry attributes only); the
stroke attributes are applied uniformly by `render()` so every icon reads as ONE
system: a single 24-grid, round caps/joins, one muted color, and a constant ~1.5px
ON-SCREEN stroke (`stroke-width = 36 / renderPx`) that matches the label weight and
survives GitHub's column downscaling.

This replaces the old hand-drawn `glass_kit._ICONS` (which mixed fill/stroke glyphs
at inconsistent weights — the "AI look" the icon contract reds out).
"""
from __future__ import annotations

from scripts.core.config import TEXT


def _f(value: float) -> str:
    return f"{round(float(value), 3):g}"


# name -> inner Lucide geometry (paths/lines/circles/rects/polylines/polygons).
LUCIDE: dict[str, str] = {
    "commit": '<circle cx="12" cy="12" r="3"/><line x1="3" x2="9" y1="12" y2="12"/><line x1="15" x2="21" y1="12" y2="12"/>',
    "branch": '<line x1="6" x2="6" y1="3" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>',
    "fork": '<circle cx="12" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><path d="M18 9v2c0 .6-.4 1-1 1H7c-.6 0-1-.4-1-1V9"/><path d="M12 12v3"/>',
    "pr_merged": '<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><line x1="6" x2="6" y1="9" y2="21"/>',
    "lock": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "workflow": '<rect width="8" height="8" x="3" y="3" rx="2"/><path d="M7 11v4a2 2 0 0 0 2 2h4"/><rect width="8" height="8" x="13" y="13" rx="2"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "code": '<path d="m16 18 6-6-6-6"/><path d="m8 6-6 6 6 6"/>',
    "fire": '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
    "calendar": '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
    "calendar_check": '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/><path d="m9 16 2 2 4-4"/>',
    "star": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    "release_tag": '<path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    "trend_up": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    "trend_down": '<polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "ci_check": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "cross": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "rocket": '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>',
    "test": '<path d="M10 2v7.31"/><path d="M14 9.3V1.99"/><path d="M8.5 2h7"/><path d="M14 9.3a6.5 6.5 0 1 1-4 0"/><path d="M5.52 16h12.96"/>',
}

# Aliases so existing semantic call-site keys keep working unchanged.
LUCIDE["release"] = LUCIDE["release_tag"]


def render(name: str, x: float, y: float, *, size: float = 16, color: str = TEXT, opacity: float = 1.0) -> str:
    """Render a Lucide icon translated/scaled to (x, y). Round caps; one muted color;
    constant ~1.5px on-screen stroke (stroke-width = 36/renderPx)."""
    # Filled dots keep their fill (language identity / neutral status dot).
    if name in ("lang_dot", "dot"):
        r = (size / 2.0) if name == "lang_dot" else (size * 0.3)
        op = f' opacity="{opacity:g}"' if opacity < 1.0 else ""
        return f'<circle cx="{_f(x + size / 2)}" cy="{_f(y + size / 2)}" r="{_f(r)}" fill="{color}"{op}/>'
    body = LUCIDE.get(name)
    if not body:
        return ""
    scale = size / 24.0
    stroke_w = 36.0 / float(size)  # -> on-screen stroke = stroke_w * scale = 1.5px
    op = f' opacity="{opacity:g}"' if opacity < 1.0 else ""
    return (
        f'<g transform="translate({_f(x)},{_f(y)}) scale({_f(scale)})" fill="none" '
        f'stroke="{color}" stroke-width="{_f(stroke_w)}" stroke-linecap="round" '
        f'stroke-linejoin="round"{op}>{body}</g>'
    )
