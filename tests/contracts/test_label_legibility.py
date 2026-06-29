"""Red-first LABEL LEGIBILITY contract — authority: the LIVE render is the proof,
tests are the admissibility gate (owner directive). Closes the gap where a card
passed the typography/tile contracts yet still read broken on GitHub.

Policy (deliberately scoped — stated so the gate is honest, not over-claimed):
  * METRIC TILE text (the noun that labels a KPI, plus a tile's one-line caption)
    must be AUTHORED TO FIT its tile and is never machine-clipped. A glance tile
    gets a concise word, not "Public Repo C…".
  * Long-form LIST-ROW content (repository names, commit descriptions) MAY
    gracefully ellipsize — that matches GitHub's own UI and the owner did not flag
    it. So the clip check is scoped to tiles, NOT applied globally.

What these checks PROVE, on the RENDERED SVG of the real generators (driven by the
shared fixture model AND a stress fixture with long live-like strings):
  1. FITS: every caption-size string inside a metric tile is short enough that, at a
     conservative per-glyph advance for the 12px sans, it cannot reach the tile's
     right edge. Catches a label authored/grown too long for its tile.
  2. NOT CLIPPED: no tile string is machine-truncated to an ellipsis.
  3. ONE METRIC PER TILE: a caption directly under a metric value is a qualifier,
     not a second conditional metric — it carries neither a comparison operator nor
     a '%' (the tells of "N langs > 5%" jammed under "50%"). A date range stays
     legal.

Residuals (named, not hidden): (1) an SVG cannot reveal a label *silently* clipped
with NO ellipsis (a hard width-slice that drops glyphs); the codebase only ever clips
via truncate()'s "…" suffix, which check 2 catches; a future silent-clip mechanism
would need its own source-level guard. (2) The fit budget is a character COUNT proxy,
not a glyph-width metric, so an all-wide-glyph string (e.g. all-caps "MMMM%") of exactly
budget length could overflow while len() passes — inert in practice because the only
tight tile (snapshot 82px) renders a static, controlled mixed-case _TILE_LABEL set and
genuinely over-long names still bite. Palette-agnostic: ink colors import from the tokens.
"""
from __future__ import annotations

import math
import re
import tempfile
import unittest
from pathlib import Path

from scripts.core.config import SURFACE_RAISED, TEXT_BRIGHT, TEXT_DIM

# Reuse the canonical fixture-driven renderer + card registry (one source of truth
# for "render every card the way the pipeline does").
from tests.contracts.test_card_contracts import CARDS, MODEL, _render

TEXT_BRIGHT_HEX = TEXT_BRIGHT.lower()
TEXT_DIM_HEX = TEXT_DIM.lower()

_TEXT_NODE = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)
# A glass_tile's translucent base rect: the SURFACE_RAISED fill at 0.55 opacity is
# unique to metric tiles (heatmap/contribution cells fill with ramp colors, never
# SURFACE_RAISED), so this keys on tiles only.
_TILE_RECT = re.compile(
    r'<rect x="(-?[0-9.]+)" y="(-?[0-9.]+)" width="([0-9.]+)" height="([0-9.]+)"[^>]*'
    r'fill="' + re.escape(SURFACE_RAISED) + r'" fill-opacity="0.55"')
_ATTR_X = re.compile(r'\bx="(-?[0-9.]+)"')
_ATTR_Y = re.compile(r'\by="(-?[0-9.]+)"')
_ATTR_SIZE = re.compile(r'\bfont-size="([0-9.]+)"')
_ATTR_FILL = re.compile(r'\bfill="(#[0-9a-fA-F]+)"')
_ATTR_ANCHOR = re.compile(r'\btext-anchor="(\w+)"')
_NUMBER = re.compile(r"\d[\d,\.]*")
# A comparison operator or a '%' in a caption signals a second, conditional metric
# crammed under the value (e.g. "N langs > X%"). Matches raw and entity forms.
_SECOND_METRIC = re.compile(r"(?:&[lg]t;|[<>≤≥%])")

_METRIC_SIZES = {22.0, 26.0}
_CAPTION_SIZE = 12.0

# Conservative average glyph advance for the 12px sans caption — slightly above the
# real mixed-case average (~5.8px) so legible labels pass with margin while genuine
# overflow fails. Calibrated against the rendered tiles: the tightest (snapshot/badges
# 4-col) leaves 82px, where a 13-char "private repos" (82/6.0 -> budget 13) fits and a
# 14-char label does not. Deterministic integer budget => no font-metric flakiness.
_PX_PER_CHAR = 6.0


class _Node:
    __slots__ = ("x", "y", "size", "fill", "anchor", "text")

    def __init__(self, attrs: str, text: str):
        mx, my, ms, mf = (_ATTR_X.search(attrs), _ATTR_Y.search(attrs),
                          _ATTR_SIZE.search(attrs), _ATTR_FILL.search(attrs))
        ma = _ATTR_ANCHOR.search(attrs)
        self.x = float(mx.group(1)) if mx else 0.0
        self.y = float(my.group(1)) if my else 0.0
        self.size = float(ms.group(1)) if ms else 0.0
        self.fill = mf.group(1).lower() if mf else ""
        self.anchor = ma.group(1) if ma else "start"
        self.text = text


def _nodes(svg: str) -> list[_Node]:
    return [_Node(a, t) for a, t in _TEXT_NODE.findall(svg)]


def _tiles(svg: str):
    """(x, y, w, h) for every metric tile (glass_tile's translucent base rect)."""
    return [(float(a), float(b), float(c), float(d)) for a, b, c, d in _TILE_RECT.findall(svg)]


def _avail_px(n: _Node, rx: float, rw: float) -> float:
    """Horizontal room the string has inside its tile, honoring text-anchor:
    start text grows right from x; end text grows left from x; middle is symmetric."""
    if n.anchor == "end":
        return n.x - rx
    if n.anchor == "middle":
        return 2.0 * min(n.x - rx, (rx + rw) - n.x)
    return (rx + rw) - n.x


def _tile_caption_nodes(svg: str):
    """Yield (node, available_px) for every caption-size dim string that sits
    INSIDE a metric tile. Covers tile labels, tile captions, and gauge detail lines."""
    tiles = _tiles(svg)
    for n in _nodes(svg):
        if n.size != _CAPTION_SIZE or n.fill != TEXT_DIM_HEX:
            continue
        for (rx, ry, rw, rh) in tiles:
            if rx <= n.x <= rx + rw and ry <= n.y <= ry + rh:
                yield n, _avail_px(n, rx, rw)
                break


def _primary_lang_name(model: dict) -> str:
    langs = model.get("top_languages") or []
    return str(langs[0].get("name") or "") if langs and isinstance(langs[0], dict) else ""


def _render_all() -> dict[str, str]:
    out: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as d:
        for card in CARDS:
            path = str(Path(d) / f"{card}.svg")
            _render(card, path)
            out[card] = Path(path).read_text(encoding="utf-8")
    return out


def _render_stress() -> dict[str, str]:
    """Re-render the data-driven tile cards with the longest plausible live label
    (a 10-char primary language) so the FIT proof is exercised on real-length data,
    not just the short fixture string."""
    out: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as d:
        from scripts.rendering.generate_builder_scorecard import generate as bld
        from scripts.rendering.generate_engineering_cadence import generate as eng
        eng(MODEL["engineering"], output_path=str(Path(d) / "e.svg"), primary_language="JavaScript")
        out["engineering(JavaScript)"] = Path(str(Path(d) / "e.svg")).read_text(encoding="utf-8")
        bld(MODEL["scorecard"], output_path=str(Path(d) / "b.svg"),
            tiles=MODEL["scorecard_cards"], primary_language="TypeScript")
        out["scorecard(TypeScript)"] = Path(str(Path(d) / "b.svg")).read_text(encoding="utf-8")
    return out


class LabelLegibilityContract(unittest.TestCase):
    """Every shipped tile reads cleanly: labels fit, none clipped, one metric each."""

    def test_metric_tile_text_fits_its_tile(self):
        offenders = []
        for card, svg in {**_render_all(), **_render_stress()}.items():
            for n, avail in _tile_caption_nodes(svg):
                budget = math.floor(avail / _PX_PER_CHAR)
                if len(n.text) > budget:
                    offenders.append(
                        f"{card}: tile text {n.text!r} ({len(n.text)} chars) exceeds the "
                        f"~{budget}-char budget for its {avail:.0f}px tile span — author it shorter")
        self.assertEqual(
            [], offenders,
            "every metric-tile string must fit its tile width:\n  " + "\n  ".join(offenders))

    def test_metric_tile_text_not_machine_clipped(self):
        offenders = []
        for card, svg in {**_render_all(), **_render_stress()}.items():
            for n, _avail in _tile_caption_nodes(svg):
                if "…" in n.text or "..." in n.text:
                    offenders.append(f"{card}: clipped tile label {n.text!r} — author it to fit, do not truncate")
        self.assertEqual(
            [], offenders,
            "no metric-tile label may be machine-clipped to an ellipsis:\n  " + "\n  ".join(offenders))

    def test_tile_caption_is_a_qualifier_not_a_formula(self):
        """A caption directly under a metric value (same x, just below) is one
        qualifier — never a second conditional metric. A comparison operator or a
        '%' is the tell ('5 langs > 5%' under '50%'); a date range stays legal."""
        offenders = []
        for card, svg in _render_all().items():
            nodes = _nodes(svg)
            values = [n for n in nodes
                      if n.size in _METRIC_SIZES and n.fill == TEXT_BRIGHT_HEX and _NUMBER.search(n.text)]
            captions = [n for n in nodes if n.size == _CAPTION_SIZE and n.fill == TEXT_DIM_HEX]
            for v in values:
                cap = next((c for c in captions
                            if abs(c.x - v.x) < 1.5 and 0 < (c.y - v.y) <= 30), None)
                if cap is not None and _SECOND_METRIC.search(cap.text):
                    offenders.append(
                        f"{card}: tile caption {cap.text!r} crams a conditional metric under value "
                        f"{v.text!r} — a caption is one qualifier, not a formula")
        self.assertEqual(
            [], offenders,
            "a tile caption may not cram a second conditional metric under the value:\n  "
            + "\n  ".join(offenders))


if __name__ == "__main__":
    unittest.main()
