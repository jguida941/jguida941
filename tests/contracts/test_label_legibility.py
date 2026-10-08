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
import xml.etree.ElementTree as ET
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

_SVG_NS = "{http://www.w3.org/2000/svg}"
_CARD_CONTENT_LEFT = 28.0
_CARD_CONTENT_RIGHT = 812.0
_FOOTER_GAP_MIN = 12.0
_FOOTER_GAP_MAX = 32.0
_RING_EDGE_INSET = 8.0
_RING_COPY_GAP = 12.0
_COPY_EDGE_INSET = 8.0
_HOLE_TEXT_INSET = 2.0
_ALL_OWNED_SCOPE = "owned-public-private-nonfork-profile-excluded-exact"

# Conservative average glyph advance for the 12px sans caption — slightly above the
# real mixed-case average (~5.8px) so legible labels pass with margin while genuine
# overflow fails. Calibrated against the rendered tiles: the tightest (snapshot/badges
# 4-col) leaves 82px, where a 13-char "private repos" (82/6.0 -> budget 13) fits and a
# 14-char label does not. Deterministic integer budget => no font-metric flakiness.
_PX_PER_CHAR = 6.0


def _proxy_text_width(text_value: str, font_size: float) -> float:
    """Deterministic upper-biased advance proxy for the system sans stack.

    A single average hides exactly the wide-glyph boundary this contract protects,
    while host font metrics make pixel measurement non-reproducible. These glyph
    classes deliberately run wider than ordinary Helvetica/Segoe UI advances.
    """
    em = 0.0
    for char in text_value:
        if char.isspace():
            em += 0.34
        elif char in "ilIjtfr.,:;|'!`":
            em += 0.36
        elif char in "MW@#%&":
            em += 0.96
        elif char.isdigit():
            em += 0.64
        elif char.isupper():
            em += 0.72
        elif char in "-_/+()[]":
            em += 0.46
        else:
            em += 0.62
    return em * font_size


def _first_float(raw: str | None, default: float = 0.0) -> float:
    if raw is None:
        return default
    match = re.match(r"\s*(-?[0-9]+(?:\.[0-9]+)?)", raw)
    return float(match.group(1)) if match else default


# --- ancestor-aware SVG paint state -------------------------------------------------
# A node that is display:none / visibility:hidden / aria-hidden / fully transparent is
# not proof of anything, and a node under a geometry-changing transform cannot be judged
# by its authored coordinates. Both facts inherit down the tree, so the governed footer
# and gauge validators resolve them once, from the root, instead of trusting attributes.
_STYLE_DECL = re.compile(r"([A-Za-z-]+)\s*:\s*([^;]*)")
_NUMBER_SRC = r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
_STRICT_NUMBER = re.compile(rf"^{_NUMBER_SRC}$")
# One transform function, matched from a known offset so the whole attribute must be
# consumed: a stray tail, an unmatched paren, or an illegal separator never parses.
_TRANSFORM_FN = re.compile(r"([A-Za-z]+)\s*\(\s*([^()]*?)\s*\)")
# A complete legal comma-wsp separator, required BETWEEN two functions. A dangling
# trailing separator is incomplete syntax, not a harmless identity.
_TRANSFORM_SEP = re.compile(r"\s*,\s*|\s+")
# Argument list with only legal comma-wsp separators between strict numbers.
_TRANSFORM_ARGS = re.compile(rf"{_NUMBER_SRC}(?:(?:\s*,\s*|\s+){_NUMBER_SRC})*")
# Exact SVG arity per function; anything else (including no arguments) is malformed.
_TRANSFORM_ARITY = {
    "matrix": (6,),
    "translate": (1, 2),
    "scale": (1, 2),
    "rotate": (1, 3),
    "skewx": (1,),
    "skewy": (1,),
}
_TRANSFORM_NEUTRAL = {"translate": 0.0, "rotate": 0.0, "skewx": 0.0, "skewy": 0.0, "scale": 1.0}

# SVG's own initial paint: filled black, unstroked, fully opaque. All four properties
# inherit, so a governed node's paint is resolved from its whole ancestor chain and a
# child may still override an inherited fill/stroke with its own explicit paint.
_PAINT_DEFAULTS = {
    "fill": "black",
    "stroke": "none",
    "fill-opacity": "1",
    "stroke-opacity": "1",
}
_PAINT_GOVERNED = {f"{_SVG_NS}{tag}" for tag in ("text", "tspan", "circle", "rect")}
_BLANK_PAINT = {"none", "transparent"}


def _style_map(node: ET.Element) -> dict[str, str]:
    return {
        name.strip().casefold(): value.strip()
        for name, value in _STYLE_DECL.findall(node.get("style") or "")
    }


def _declared(node: ET.Element, style: dict[str, str], name: str) -> str | None:
    """Explicitly supplied value for a presentation property (style wins over attribute)."""
    if name in style:
        return style[name]
    return node.get(name)


def _opacity_hides(raw: str | None) -> bool:
    """True when an explicitly supplied alpha paints nothing. Malformed fails closed."""
    if raw is None:
        return False
    text = raw.strip()
    if not text:
        return True
    if text.endswith("%"):
        body = text[:-1].strip()
        return True if not _STRICT_NUMBER.match(body) else float(body) <= 0.0
    if not _STRICT_NUMBER.match(text):
        return True
    return float(text) <= 0.0


def _node_hides(node: ET.Element, style: dict[str, str] | None = None) -> bool:
    """Structural non-visibility, which inherits down the whole subtree. Group opacity
    stays structural here; the fill/stroke channels are resolved separately so a child
    can still override an inherited paint property."""
    style = _style_map(node) if style is None else style
    display = _declared(node, style, "display")
    if display is not None and display.strip().casefold() == "none":
        return True
    visibility = _declared(node, style, "visibility")
    if visibility is not None and visibility.strip().casefold() in {"hidden", "collapse"}:
        return True
    aria_hidden = node.get("aria-hidden")
    if aria_hidden is not None and aria_hidden.strip().casefold() == "true":
        return True
    return _opacity_hides(_declared(node, style, "opacity"))


def _channel_paints(value: str, opacity: str) -> bool:
    """True when one paint channel still puts ink on the page."""
    text = value.strip().casefold()
    if not text or text in _BLANK_PAINT:
        return False
    return not _opacity_hides(opacity)


def _style_transform_changes_geometry(style: dict[str, str]) -> bool:
    """Any nonempty CSS `transform` other than `none` is geometry-unsafe for these
    static checks: the authored x/y no longer describe where the ink lands."""
    value = style.get("transform")
    if value is None:
        return False
    text = value.strip().casefold()
    return bool(text) and text != "none"


def _rotation_preserves_bounds(node: ET.Element | None, values: list[float]) -> bool:
    """True only for a well-formed rotate(angle cx cy) spun about a circle's OWN center.

    Rotating a circle about its own cx,cy maps the painted ring onto itself, so the
    authored cx/cy/r still describe the paint (this is how a progress arc is started at
    12 o'clock). Every other pivot — and every non-circle element — moves ink, so it
    stays fail-closed.
    """
    if node is None or node.tag != f"{_SVG_NS}circle" or len(values) != 3:
        return False
    center: list[float] = []
    for name in ("cx", "cy"):
        raw = node.get(name)
        if raw is None or not _STRICT_NUMBER.match(raw.strip()):
            return False
        center.append(float(raw))
    return [values[1], values[2]] == center


def _parsed_transform_list(text: str) -> list[tuple[str, list[float]]] | None:
    """A fully consumed, well-formed SVG transform-list, or None when the syntax is
    not admissible (unknown function, wrong/empty arity, loose numbers, trailing text,
    or an incomplete separator such as a dangling comma)."""
    parsed: list[tuple[str, list[float]]] = []
    position = 0
    while True:
        match = _TRANSFORM_FN.match(text, position)
        if match is None:
            return None
        key = match.group(1).casefold()
        arity = _TRANSFORM_ARITY.get(key)
        if arity is None:
            return None
        args = match.group(2)
        if not _TRANSFORM_ARGS.fullmatch(args):
            return None
        values = [float(token) for token in re.split(r"[\s,]+", args) if token]
        if len(values) not in arity:
            return None
        parsed.append((key, values))
        position = match.end()
        if position == len(text):
            return parsed
        separator = _TRANSFORM_SEP.match(text, position)
        if separator is None or separator.end() == len(text):
            # No separator at all, or one with nothing after it (a dangling comma).
            return None
        position = separator.end()


def _transform_changes_geometry(raw: str | None, node: ET.Element | None = None) -> bool:
    """True for any nonempty transform that is not provably bounds-preserving for `node`
    (fails closed; without element context only the identity is admissible)."""
    if raw is None:
        return False
    text = raw.strip()
    if not text:
        return False
    functions = _parsed_transform_list(text)
    if functions is None:
        return True
    for key, values in functions:
        if key == "matrix":
            if values != [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]:
                return True
            continue
        if key == "rotate":
            # Zero degrees preserves geometry about ANY pivot, so rotate(0) and
            # rotate(0 cx cy) are identities on any element. A real angle stays
            # admissible only as the element's sole spin about its own center.
            if values[0] == 0.0:
                continue
            if len(functions) == 1 and _rotation_preserves_bounds(node, values):
                continue
            return True
        if any(value != _TRANSFORM_NEUTRAL[key] for value in values):
            return True
    return False


def _paint_states(root: ET.Element) -> dict[ET.Element, tuple[bool, bool]]:
    """Map every element to (painted, transformed) from one ancestor-aware traversal.

    Structural non-visibility inherits down the subtree. The four paint properties
    inherit too, but the CONCLUSION does not: a governed text/tspan/circle/rect is
    painted only when a visible fill or stroke channel remains for that node, while
    its children resolve their own paint (so an explicit child fill still overrides
    an inherited fill:none).
    """
    states: dict[ET.Element, tuple[bool, bool]] = {}

    def walk(
        node: ET.Element,
        visible: bool,
        transformed: bool,
        paint: dict[str, str],
    ) -> None:
        style = _style_map(node)
        resolved = dict(paint)
        for prop in _PAINT_DEFAULTS:
            declared = _declared(node, style, prop)
            if declared is not None:
                resolved[prop] = declared
        visible = visible and not _node_hides(node, style)
        transformed = (
            transformed
            or _transform_changes_geometry(node.get("transform"), node)
            or _style_transform_changes_geometry(style)
        )
        painted = visible and (
            node.tag not in _PAINT_GOVERNED
            or _channel_paints(resolved["fill"], resolved["fill-opacity"])
            or _channel_paints(resolved["stroke"], resolved["stroke-opacity"])
        )
        states[node] = (painted, transformed)
        for child in node:
            walk(child, visible, transformed, resolved)

    walk(root, True, False, dict(_PAINT_DEFAULTS))
    return states


class _SvgLine:
    __slots__ = (
        "x",
        "y",
        "size",
        "anchor",
        "text",
        "squeezed",
        "visible",
        "transformed",
        "positioned",
    )

    def __init__(
        self,
        *,
        x: float,
        y: float,
        size: float,
        anchor: str,
        text_value: str,
        squeezed: bool,
        visible: bool = True,
        transformed: bool = False,
        positioned: bool = True,
    ):
        self.x = x
        self.y = y
        self.size = size
        self.anchor = anchor
        self.text = text_value
        self.squeezed = squeezed
        # Retained (never dropped) so footer/gauge validation can still identify a
        # semantic line that a regression hid or shoved off-card, and say so.
        self.visible = visible
        self.transformed = transformed
        # False when the authored coordinates cannot be resolved to one position.
        self.positioned = positioned


def _authored_coordinate(raw: str | None, default: float) -> tuple[float, bool]:
    """(value, trustworthy) for one authored x/y/dx/dy. A coordinate LIST — or any
    value that is not a single strict number — is not one authored position for these
    static checks, so it fails closed instead of silently using its first number."""
    if raw is None:
        return default, True
    text = raw.strip()
    if not _STRICT_NUMBER.match(text):
        return default, False
    return float(text), True


def _text_node_state(
    node: ET.Element,
    inherited: dict,
    cursor: dict[str, float],
) -> dict:
    """Resolve one text/tspan node's authored position (honoring dx/dy), type and
    squeeze state, advancing the shared document-order cursor."""
    positioned = inherited["positioned"]
    x, x_ok = _authored_coordinate(node.get("x"), cursor["x"])
    dx, dx_ok = _authored_coordinate(node.get("dx"), 0.0)
    y, y_ok = _authored_coordinate(node.get("y"), cursor["y"])
    dy, dy_ok = _authored_coordinate(node.get("dy"), 0.0)
    cursor["x"] = x + dx
    cursor["y"] = y + dy
    return {
        "x": cursor["x"],
        "y": cursor["y"],
        "size": _first_float(node.get("font-size"), inherited["size"]),
        "anchor": node.get("text-anchor", inherited["anchor"]),
        "squeezed": (
            inherited["squeezed"]
            or "textLength" in node.attrib
            or "lengthAdjust" in node.attrib
        ),
        "positioned": positioned and x_ok and dx_ok and y_ok and dy_ok,
    }


def _text_lines(
    container: ET.Element,
    states: dict[ET.Element, tuple[bool, bool]],
) -> list[_SvgLine]:
    """Every nonempty text segment under `container`, descendant-aware: a nested tspan
    keeps its OWN coordinates, type, paint and transform state instead of being
    promoted into its visible parent."""
    lines: list[_SvgLine] = []

    def emit(state: dict, content: str, owner: ET.Element) -> None:
        visible, transformed = states.get(owner, (True, False))
        lines.append(
            _SvgLine(
                x=state["x"],
                y=state["y"],
                size=state["size"],
                anchor=state["anchor"],
                text_value=content,
                squeezed=state["squeezed"],
                visible=visible,
                transformed=transformed,
                positioned=state["positioned"],
            )
        )

    def visit(node: ET.Element, inherited: dict, cursor: dict[str, float]) -> None:
        state = _text_node_state(node, inherited, cursor)
        direct = (node.text or "").strip()
        if direct:
            emit(state, direct, node)
        for child in node:
            if child.tag == f"{_SVG_NS}tspan":
                visit(child, state, cursor)
            tail = (child.tail or "").strip()
            if tail:
                emit({**state, "x": cursor["x"], "y": cursor["y"]}, tail, node)

    root_state = {
        "x": 0.0,
        "y": 0.0,
        "size": 0.0,
        "anchor": "start",
        "squeezed": False,
        "positioned": True,
    }
    for text_node in container.iter(f"{_SVG_NS}text"):
        visit(text_node, root_state, {"x": 0.0, "y": 0.0})
    return lines


def _positioned_text_lines(svg: str) -> tuple[ET.Element, list[_SvgLine]]:
    """Return text lines with ancestor-aware paint state, including nested tspans."""
    root = ET.fromstring(svg)
    return root, _text_lines(root, _paint_states(root))


def _exact_total_count(text_value: str, total: str) -> int:
    """Occurrences of a COMPLETE numeric+label total token. '154 Repositories' does not
    satisfy '54 Repositories', and '11 Releases' does not satisfy '1 Releases'."""
    pattern = rf"(?<![0-9A-Za-z_.,]){re.escape(total)}(?![0-9A-Za-z_])"
    return len(re.findall(pattern, text_value))


def _line_horizontal_bounds(line: _SvgLine) -> tuple[float, float]:
    width = _proxy_text_width(line.text, line.size)
    if line.anchor == "end":
        return line.x - width, line.x
    if line.anchor == "middle":
        return line.x - width / 2.0, line.x + width / 2.0
    return line.x, line.x + width


def _footer_layout_errors(
    svg: str,
    totals: tuple[str, str, str],
    expected_scope_lines: tuple[str, ...] = (),
) -> list[str]:
    root, lines = _positioned_text_lines(svg)
    tiles = _tiles(svg)
    if not tiles:
        return ["metrics.general: no metric grid found"]
    grid_bottom = max(y + h for _x, y, _w, h in tiles)
    footer = [line for line in lines if line.y > grid_bottom + 8]
    if not footer:
        return ["metrics.general: no footer text found below the metric grid"]

    errors: list[str] = []
    distinct_baselines = sorted({line.y for line in footer})
    if len(distinct_baselines) < 2:
        errors.append("longest public+private footer is still one line; it must wrap semantically")

    for total in totals:
        count = sum(_exact_total_count(line.text, total) for line in footer)
        if count != 1:
            errors.append(f"footer must preserve readable total {total!r} exactly once (found {count})")

    # A scope line is a complete semantic claim about a population, so it is proved by
    # equality: a broadened or suffixed variant names a different population.
    for expected in expected_scope_lines:
        matches = sum(1 for line in footer if line.text == expected)
        if matches != 1:
            errors.append(
                f"footer must carry the complete scope line {expected!r} exactly once "
                f"(found {matches}); a broadened or suffixed variant is a different claim"
            )

    footer_text = " ".join(line.text for line in footer).casefold()
    for term in ("languages", "public", "private"):
        if term not in footer_text:
            errors.append(f"footer lost the visible {term!r} scope meaning")

    height = _first_float(root.get("height"))
    for line in footer:
        if not line.visible:
            errors.append(
                f"footer line {line.text!r} paints no visible fill or stroke (hidden, "
                "transparent, or fill:none); a semantic footer line must stay visible "
                "to carry its meaning"
            )
        if line.transformed:
            # Reporting beats trusting: the authored x/y no longer describe the paint.
            errors.append(
                f"footer line {line.text!r} carries a geometry-changing transform, so its "
                "painted bounds are not the authored content bounds (off-card paint is possible)"
            )
        elif not line.positioned:
            errors.append(
                f"footer line {line.text!r} declares a coordinate list this static check "
                "cannot resolve, so its painted position and bounds are unproven"
            )
        else:
            left, right = _line_horizontal_bounds(line)
            if left < _CARD_CONTENT_LEFT - 0.01 or right > _CARD_CONTENT_RIGHT + 0.01:
                errors.append(
                    f"footer line {line.text!r} paints x={left:.1f}..{right:.1f}; "
                    f"content bounds are {_CARD_CONTENT_LEFT:.0f}..{_CARD_CONTENT_RIGHT:.0f}"
                )
            if line.y - line.size < 12 or line.y + line.size * 0.25 > height - 12:
                errors.append(f"footer line {line.text!r} paints outside the panel's vertical content bounds")
        if line.squeezed:
            errors.append(f"footer line {line.text!r} uses textLength/lengthAdjust instead of wrapping")
        if "…" in line.text or "..." in line.text:
            errors.append(f"footer line {line.text!r} is clipped instead of preserving its meaning")

    first_ink_top = min(line.y - line.size for line in footer)
    grid_to_footer = first_ink_top - grid_bottom
    if not (_FOOTER_GAP_MIN <= grid_to_footer <= _FOOTER_GAP_MAX):
        errors.append(
            f"metric grid to first footer ink is {grid_to_footer:.1f}px; "
            f"expected {_FOOTER_GAP_MIN:.0f}..{_FOOTER_GAP_MAX:.0f}px"
        )

    ordered = sorted(footer, key=lambda line: line.y)
    for previous, current in zip(ordered, ordered[1:]):
        if abs(current.y - previous.y) < 0.01:
            # Segments of one visual line (nested tspans) share a baseline by design.
            continue
        previous_bottom = previous.y + previous.size * 0.25
        current_top = current.y - current.size
        if current_top < previous_bottom:
            errors.append(
                f"footer lines {previous.text!r} and {current.text!r} overlap vertically"
            )
    return errors


_CONTROL_PUBLIC_SCOPE = "Repositories/stars/releases: public owned non-forks"
_CONTROL_LANGUAGE_SCOPE = (
    "Languages: public + private owned non-forks; profile excluded; exact · last 12 months"
)
_CONTROL_SCOPE_LINES = (_CONTROL_PUBLIC_SCOPE, _CONTROL_LANGUAGE_SCOPE)


def _nearest_valid_footer_control(
    *,
    totals_text: str = "54 Repositories · 57 Stargazers",
    totals_suffix: str = " · 1 Releases",
    first_line_attrs: str = "",
    line_attrs: str = "",
    group_attrs: str | None = None,
    scope_suffix: str = "",
) -> str:
    """The nearest-valid footer, optionally perturbed one authored fact at a time."""
    body = (
        f'<text x="28" y="257" font-size="12"{line_attrs}{first_line_attrs}>'
        f'{totals_text}{totals_suffix}</text>'
        f'<text x="28" y="275" font-size="12"{line_attrs}>{_CONTROL_PUBLIC_SCOPE}{scope_suffix}</text>'
        f'<text x="28" y="293" font-size="12"{line_attrs}>{_CONTROL_LANGUAGE_SCOPE}{scope_suffix}</text>'
    )
    if group_attrs is not None:
        body = f"<g {group_attrs}>{body}</g>"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="840" height="312" viewBox="0 0 840 312">'
        f'<rect x="296" y="161" width="164" height="66" fill="{SURFACE_RAISED}" fill-opacity="0.55"/>'
        f'{body}</svg>'
    )


def _reports(errors: list[str], markers: tuple[str, ...]) -> bool:
    """True when some error names one of these meanings (wording stays free)."""
    return any(marker in error.casefold() for error in errors for marker in markers)


def _render_live_footer() -> str:
    from scripts.rendering.generate_metrics_general import generate

    snapshot = {
        "last_year_contributions": 11740,
        "public_scope_commits": 7140,
        "total_repos": 54,
        "private_owned_repos": 198,
        "total_stars": 57,
        "languages_count": 32,
        "prs_merged": 52,
        "releases": 1,
        "ci_repos": 53,
        "streak_days": 62,
    }
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "metrics.general.svg"
        generate(
            username="jguida941",
            snapshot=snapshot,
            data_scope={"metric_scopes": {"languages_count": _ALL_OWNED_SCOPE}},
            generated_at="2026-08-27T09:04:00Z",
            output_path=str(output),
        )
        return output.read_text(encoding="utf-8")


def _compact_gauge_errors(svg: str) -> list[str]:
    root = ET.fromstring(svg)
    states = _paint_states(root)
    group = next(
        (
            node
            for node in root.iter()
            if node.attrib.get("data-metric-key") == "ci_coverage_pct"
        ),
        None,
    )
    if group is None:
        return ["missing ci_coverage_pct claim group"]

    tile = next(
        (
            node
            for node in group.iter(f"{_SVG_NS}rect")
            if node.get("fill") == SURFACE_RAISED and node.get("fill-opacity") == "0.55"
        ),
        None,
    )
    circles = list(group.iter(f"{_SVG_NS}circle"))
    if tile is None or len(circles) < 2:
        return ["compact CI tile must contain one tile and a two-circle painted ring"]

    tx = _first_float(tile.get("x"))
    ty = _first_float(tile.get("y"))
    tw = _first_float(tile.get("width"))
    th = _first_float(tile.get("height"))

    errors: list[str] = []
    tile_visible, tile_transformed = states.get(tile, (True, False))
    if not tile_visible or tile_transformed:
        # Without a trustworthy tile rect there is no frame to judge ring or copy by.
        return [
            "the compact CI tile rect is hidden or carries a geometry-changing transform, "
            "so its authored x/y/width/height cannot govern the ring and copy"
        ]
    if len(circles) != 2:
        errors.append(
            f"claim group paints {len(circles)} ring circles; a compact gauge is exactly two "
            "concentric circles — an extra ring paints outside the governed geometry"
        )
    painted: list[ET.Element] = []
    for circle in circles:
        visible, transformed = states.get(circle, (True, False))
        if not visible:
            errors.append(
                "a gauge ring circle paints no visible fill or stroke (hidden, transparent, "
                "or an unstroked fill:none ring); the painted ring must be visible"
            )
            continue
        if transformed:
            errors.append(
                "a gauge ring circle carries a geometry-changing transform, so its painted "
                "ring bounds cannot be checked against the tile"
            )
            continue
        painted.append(circle)
    if len(painted) != 2:
        errors.append(
            f"compact CI tile paints {len(painted)} visible untransformed ring circles; "
            "the governed ring is exactly two"
        )
    if not painted:
        return errors
    for attribute in ("cx", "cy", "r", "stroke-width"):
        values = {round(_first_float(node.get(attribute)), 4) for node in painted}
        if len(values) > 1:
            errors.append(
                f"gauge ring circles disagree on {attribute} ({sorted(values)}); a track and its "
                "progress arc must be concentric and equally weighted"
            )

    ring = max(painted, key=lambda node: _first_float(node.get("stroke-width")))
    cx = _first_float(ring.get("cx"))
    cy = _first_float(ring.get("cy"))
    radius = _first_float(ring.get("r"))
    stroke = _first_float(ring.get("stroke-width"))
    ring_right = cx + radius + stroke / 2.0

    for index, circle in enumerate(painted, start=1):
        node_cx = _first_float(circle.get("cx"))
        node_cy = _first_float(circle.get("cy"))
        node_radius = _first_float(circle.get("r")) + _first_float(circle.get("stroke-width")) / 2.0
        margins = {
            "left": (node_cx - node_radius) - tx,
            "right": tx + tw - (node_cx + node_radius),
            "top": (node_cy - node_radius) - ty,
            "bottom": ty + th - (node_cy + node_radius),
        }
        for side, margin in margins.items():
            if margin < _RING_EDGE_INSET - 0.01:
                errors.append(
                    f"painted ring #{index} {side} margin is {margin:.1f}px; "
                    f"needs >= {_RING_EDGE_INSET:.0f}px inside the tile bounds"
                )

    # One descendant-aware extractor decides what the reader can read here too, so a
    # hidden nested tspan can never be promoted into its visible parent.
    text_nodes = _text_lines(group, states)
    centered = [
        line for line in text_nodes if line.anchor == "middle" and abs(line.x - cx) < 0.01
    ]
    if len(centered) > 1:
        errors.append(
            f"painted ring holds {len(centered)} centered labels; exactly one value label is governed"
        )
    center = centered[0] if centered else None
    if center is None:
        errors.append("painted ring is missing its centered value label")
    elif not center.visible:
        errors.append(
            f"center label {center.text!r} paints no visible fill or stroke (hidden, "
            "transparent, or fill:none); the ring's value must stay visible"
        )
    elif center.transformed:
        errors.append(
            f"center label {center.text!r} carries a geometry-changing transform, so its "
            "centered position inside the ring hole is not trustworthy"
        )
    elif not center.positioned:
        errors.append(
            f"center label {center.text!r} declares a coordinate list this static check "
            "cannot resolve, so its position inside the ring hole is unproven"
        )
    else:
        if not _NUMBER.search(center.text):
            errors.append(f"center label {center.text!r} does not read as the ring's value")
        if center.size < 12:
            errors.append(f"center label {center.text!r} is below the 12px legibility floor")
        hole_half = radius - stroke / 2.0 - _HOLE_TEXT_INSET
        hole_width = 2.0 * hole_half
        label_width = _proxy_text_width(center.text, center.size)
        if label_width > hole_width + 0.01:
            errors.append(
                f"center label {center.text!r} needs ~{label_width:.1f}px but the guarded ring hole is "
                f"{hole_width:.1f}px"
            )
        ink_top = center.y - center.size
        ink_bottom = center.y + center.size * 0.25
        if ink_top < cy - hole_half - 0.01 or ink_bottom > cy + hole_half + 0.01:
            errors.append(
                f"center label {center.text!r} paints ink y={ink_top:.1f}..{ink_bottom:.1f}; "
                f"the guarded ring hole spans {cy - hole_half:.1f}..{cy + hole_half:.1f}"
            )

    copy_lines = [line for line in text_nodes if line is not center]
    if not copy_lines:
        errors.append("compact CI tile is missing its explanatory copy column")
    elif len(copy_lines) != 2:
        errors.append(
            f"compact CI copy column paints {len(copy_lines)} lines; the governed column is "
            "exactly two (subject line + detail line)"
        )
    if copy_lines and not any(
        "coverage" in line.text.casefold() or "repo adoption" in line.text.casefold()
        or re.search(r"\bci\b", line.text, re.I)
        for line in copy_lines
    ):
        errors.append("compact CI copy column never names its CI coverage subject")
    for line in copy_lines:
        if not line.visible:
            errors.append(
                f"copy {line.text!r} paints no visible fill or stroke (hidden, transparent, "
                "or fill:none); the CI copy column must stay visible"
            )
            continue
        if line.transformed:
            errors.append(
                f"copy {line.text!r} carries a geometry-changing transform, so its painted "
                "bounds inside the tile cannot be trusted"
            )
            continue
        if not line.positioned:
            errors.append(
                f"copy {line.text!r} declares a coordinate list this static check cannot "
                "resolve, so its painted position inside the tile is unproven"
            )
            continue
        left, right = _line_horizontal_bounds(line)
        gap = left - ring_right
        if gap < _RING_COPY_GAP - 0.01:
            errors.append(
                f"copy {line.text!r} begins {gap:.1f}px after ring paint; needs >= {_RING_COPY_GAP:.0f}px"
            )
        if right > tx + tw - _COPY_EDGE_INSET + 0.01:
            errors.append(
                f"copy {line.text!r} paints through x={right:.1f}; tile copy limit is "
                f"{tx + tw - _COPY_EDGE_INSET:.1f}"
            )
        if line.y - line.size < ty + _COPY_EDGE_INSET or line.y + line.size * 0.25 > ty + th - _COPY_EDGE_INSET:
            errors.append(f"copy {line.text!r} does not fit the tile's vertical content bounds")
    return errors


def _nearest_valid_gauge_control(
    width: float,
    height: float,
    detail: str,
    *,
    track_paint: str | None = None,
    tile_attrs: str = "",
    center_content: str = "100%",
    center_y: float | None = None,
    copy_attrs: str = "",
) -> str:
    x, y = 10.0, 10.0
    cx, cy = x + 33.0, y + height / 2.0
    radius, stroke = 21.5, 4.0
    copy_x = x + 69.0
    track = (
        f'fill="none" stroke="#555" stroke-width="{stroke:g}"'
        if track_paint is None
        else track_paint
    )
    label_y = cy + 5.0 if center_y is None else center_y
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width + 20:g}" height="{height + 20:g}">'
        '<g data-metric-key="ci_coverage_pct">'
        f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" fill="{SURFACE_RAISED}" fill-opacity="0.55"{tile_attrs}/>'
        f'<circle cx="{cx:g}" cy="{cy:g}" r="{radius:g}" {track}/>'
        f'<circle cx="{cx:g}" cy="{cy:g}" r="{radius:g}" fill="none" stroke="#fff" stroke-width="{stroke:g}"/>'
        f'<text x="{cx:g}" y="{label_y:g}" font-size="12" text-anchor="middle">{center_content}</text>'
        f'<text x="{copy_x:g}" y="{cy - 2:g}" font-size="12"{copy_attrs}>CI coverage</text>'
        f'<text x="{copy_x:g}" y="{cy + 14:g}" font-size="12">{detail}</text>'
        '</g></svg>'
    )


def _render_compact_gauge_cases() -> dict[str, str]:
    from scripts.contracts.profile_contract import metric_claim
    from scripts.rendering.generate_builder_scorecard import generate as builder
    from scripts.rendering.generate_engineering_cadence import generate as cadence

    scorecard = dict(MODEL["scorecard"])
    engineering = dict(MODEL["engineering"])
    engineering.update(
        {
            "automation_repos": 53,
            "automation_eligible_repos": 251,
            "automation_workflows": 164,
            "public_repos_total": 55,
            "public_nonfork_repos": 54,
            "private_repos_total": 198,
            "private_nonfork_repos": 197,
        }
    )
    cases: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as directory:
        for label, value in (("live", 21.115537848605577), ("boundary", 100.0)):
            claim = metric_claim(
                "ci_coverage_pct",
                value=value,
                scope=_ALL_OWNED_SCOPE,
                status="exact",
            )
            score = dict(scorecard)
            score["ci_coverage_pct"] = value
            score_path = Path(directory) / f"score-{label}.svg"
            automation = {"combined": {
                "configured_repos": 53,
                "eligible_repos": 53 if label == "boundary" else 251,
                "workflow_files": 164, "adoption_pct": value,
                "status": "exact", "unknown_workflow_repos": 0,
            }}
            builder(score, output_path=str(score_path), ci_claim=claim, automation=automation)
            cases[f"builder-{label}"] = score_path.read_text(encoding="utf-8")

            eng = dict(engineering)
            if label == "boundary":
                eng["automation_eligible_repos"] = 53
            cadence_path = Path(directory) / f"cadence-{label}.svg"
            cadence(eng, output_path=str(cadence_path), ci_claim=claim, automation=automation)
            cases[f"cadence-{label}"] = cadence_path.read_text(encoding="utf-8")
    return cases


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

    def test_metrics_general_footer_control_accepts_semantic_wrapping(self):
        self.assertEqual(
            [],
            _footer_layout_errors(
                _nearest_valid_footer_control(),
                ("54 Repositories", "57 Stargazers", "1 Releases"),
                expected_scope_lines=_CONTROL_SCOPE_LINES,
            ),
        )

    def test_metrics_general_footer_fits_and_conserves_live_totals(self):
        self.assertEqual(
            [],
            _footer_layout_errors(
                _render_live_footer(),
                ("54 Repositories", "57 Stargazers", "1 Releases"),
                expected_scope_lines=(
                    "Repositories/Stargazers/Releases: public-owned-nonfork",
                    f"Languages: {_ALL_OWNED_SCOPE}",
                ),
            ),
            "the longest live public+private footer must wrap, fit, and conserve its totals",
        )

    def test_footer_rejects_unpainted_displaced_and_broadened_semantic_lines(self):
        """One table per observed way a footer line can read broken yet pass before."""
        totals = ("54 Repositories", "57 Stargazers", "1 Releases")
        cases = (
            ("direct fill:none", {"first_line_attrs": ' fill="none"'}, ("visible", "paints no")),
            ("style fill:none", {"first_line_attrs": ' style="fill:none"'}, ("visible", "paints no")),
            ("inherited fill:none", {"group_attrs": 'fill="none"'}, ("visible", "paints no")),
            (
                "hidden nested tspan",
                {"totals_suffix": '<tspan><tspan display="none"> · 1 Releases</tspan></tspan>'},
                ("visible", "paints no"),
            ),
            (
                "hidden direct tspan",
                {"totals_suffix": '<tspan display="none"> · 1 Releases</tspan>'},
                ("visible", "paints no"),
            ),
            ("dx paints off-card", {"first_line_attrs": ' dx="900"'}, ("bounds",)),
            ("dy paints off-card", {"first_line_attrs": ' dy="900"'}, ("bounds", "position")),
            (
                "css style transform",
                {"first_line_attrs": ' style="transform:translate(0px,0px)"'},
                ("transform",),
            ),
            ("coordinate list", {"first_line_attrs": ' dx="28 40"'}, ("position", "bounds")),
            ("broadened scope lines", {"scope_suffix": "-broadened"}, ("scope",)),
            (
                "totals swallowed by larger numbers",
                {
                    "totals_text": "154 Repositories · 157 Stargazers",
                    "totals_suffix": " · 11 Releases",
                },
                ("total",),
            ),
        )
        for name, control_kwargs, markers in cases:
            with self.subTest(case=name):
                errors = _footer_layout_errors(
                    _nearest_valid_footer_control(**control_kwargs),
                    totals,
                    expected_scope_lines=_CONTROL_SCOPE_LINES,
                )
                self.assertTrue(
                    _reports(errors, markers),
                    f"footer case {name!r} survived without a {markers} error: {errors}",
                )

    def test_footer_controls_stay_admissible_under_valid_paint_and_position(self):
        """The nearest legal neighbours of those cases must NOT be rejected."""
        totals = ("54 Repositories", "57 Stargazers", "1 Releases")
        controls = (
            (
                "explicit fill overrides inherited none",
                {"group_attrs": 'fill="none"', "line_attrs": ' fill="#d0d7de"'},
            ),
            ("stroke-only paint", {"line_attrs": ' fill="none" stroke="#d0d7de"'}),
            (
                "visible nested tspan",
                {"totals_suffix": '<tspan><tspan> · 1 Releases</tspan></tspan>'},
            ),
            ("declared identity dx/dy", {"first_line_attrs": ' dx="0" dy="0"'}),
            ("css transform none", {"first_line_attrs": ' style="transform:none"'}),
        )
        for name, control_kwargs in controls:
            with self.subTest(control=name):
                self.assertEqual(
                    [],
                    _footer_layout_errors(
                        _nearest_valid_footer_control(**control_kwargs),
                        totals,
                        expected_scope_lines=_CONTROL_SCOPE_LINES,
                    ),
                    f"footer control {name!r} must remain admissible",
                )

    def test_compact_gauge_rejects_unpainted_rings_and_displaced_ink(self):
        cases = (
            (
                "unstroked ring",
                {"track_paint": 'fill="none" stroke="none" stroke-width="4"'},
                ("ring", "circle"),
            ),
            (
                "zero stroke-opacity ring",
                {"track_paint": 'fill="none" stroke="#555" stroke-opacity="0" stroke-width="4"'},
                ("ring", "circle"),
            ),
            (
                "hidden nested center tspan",
                {"center_content": '<tspan><tspan display="none">100%</tspan></tspan>'},
                ("center",),
            ),
            ("center below the ring hole", {"center_y": 999.0}, ("hole",)),
            ("copy dx leaves the tile", {"copy_attrs": ' dx="900"'}, ("copy",)),
            ("copy dy leaves the tile", {"copy_attrs": ' dy="900"'}, ("copy",)),
            (
                "transformed tile rect",
                {"tile_attrs": ' transform="translate(900 0)"'},
                ("tile",),
            ),
        )
        for name, control_kwargs, markers in cases:
            with self.subTest(case=name):
                errors = _compact_gauge_errors(
                    _nearest_valid_gauge_control(164, 66, "observed", **control_kwargs)
                )
                self.assertTrue(
                    _reports(errors, markers),
                    f"gauge case {name!r} survived without a {markers} error: {errors}",
                )

    def test_compact_gauge_controls_stay_admissible_under_valid_paint_and_position(self):
        controls = (
            (
                "style fill:none with a real stroke",
                {"track_paint": 'style="fill:none" stroke="#555" stroke-width="4"'},
            ),
            ("visible nested center tspan", {"center_content": "<tspan><tspan>100%</tspan></tspan>"}),
            ("identity tile transform", {"tile_attrs": ' transform="translate(0 0)"'}),
            ("declared identity copy dx/dy", {"copy_attrs": ' dx="0" dy="0"'}),
        )
        for name, control_kwargs in controls:
            with self.subTest(control=name):
                self.assertEqual(
                    [],
                    _compact_gauge_errors(
                        _nearest_valid_gauge_control(164, 66, "observed", **control_kwargs)
                    ),
                    f"gauge control {name!r} must remain admissible",
                )

    def test_compact_ci_gauge_controls_accept_nearest_valid_geometry(self):
        controls = {
            "builder": _nearest_valid_gauge_control(164, 66, "observed"),
            "cadence": _nearest_valid_gauge_control(187, 84, "53 automated"),
        }
        offenders = []
        for card, svg in controls.items():
            offenders.extend(f"{card}: {error}" for error in _compact_gauge_errors(svg))
        self.assertEqual([], offenders, "nearest-valid compact gauge controls must remain admissible")

    def test_footer_rejects_all_semantic_lines_with_zero_opacity(self):
        control = _render_live_footer()
        totals = ("54 Repositories", "57 Stargazers", "1 Releases")
        self.assertEqual([], _footer_layout_errors(control, totals))
        selected = []

        def hide_semantic_line(match):
            attrs, body = match.groups()
            if any(
                marker in body
                for marker in (
                    "54 Repositories",
                    "Repositories/Stargazers/Releases:",
                    "Languages:",
                )
            ):
                selected.append(body)
                return f'<text{attrs} opacity="0.0">{body}</text>'
            return match.group(0)

        mutant = _TEXT_NODE.sub(hide_semantic_line, control)
        self.assertEqual(3, len(selected), "mutant must hide all three semantic footer lines")
        errors = _footer_layout_errors(mutant, totals)
        self.assertTrue(
            any("visible" in error.casefold() or "opacity" in error.casefold() for error in errors),
            f"fully transparent footer mutant survived without a visibility error: {errors}",
        )

    def test_footer_rejects_semantic_lines_translated_off_card(self):
        control = _render_live_footer()
        totals = ("54 Repositories", "57 Stargazers", "1 Releases")
        self.assertEqual([], _footer_layout_errors(control, totals))
        selected = []

        def translate_semantic_line(match):
            attrs, body = match.groups()
            if any(
                marker in body
                for marker in (
                    "54 Repositories",
                    "Repositories/Stargazers/Releases:",
                    "Languages:",
                )
            ):
                selected.append(body)
                return f'<text{attrs} transform="translate(900 0)">{body}</text>'
            return match.group(0)

        mutant = _TEXT_NODE.sub(translate_semantic_line, control)
        self.assertEqual(3, len(selected), "mutant must translate all three footer lines")
        errors = _footer_layout_errors(mutant, totals)
        self.assertTrue(
            any(
                marker in error.casefold()
                for error in errors
                for marker in ("transform", "off-card", "bounds")
            ),
            f"off-card transformed footer mutant survived without a geometry error: {errors}",
        )

    def test_compact_gauge_rejects_transparent_center_percentage(self):
        control = _render_compact_gauge_cases()["builder-live"]
        self.assertEqual([], _compact_gauge_errors(control))
        selected = []

        def hide_center_percentage(match):
            attrs, body = match.groups()
            if 'text-anchor="middle"' in attrs and "%" in body:
                selected.append(body)
                return f'<text{attrs} opacity="0.0">{body}</text>'
            return match.group(0)

        mutant = _TEXT_NODE.sub(hide_center_percentage, control)
        self.assertEqual(["21%"], selected, "mutant must hide the one centered live percentage")
        errors = _compact_gauge_errors(mutant)
        self.assertTrue(
            any(
                "center" in error.casefold()
                and ("visible" in error.casefold() or "opacity" in error.casefold())
                for error in errors
            ),
            f"transparent center-percentage mutant survived without a visibility error: {errors}",
        )

    def test_footer_rejects_malformed_identity_transform_syntax(self):
        """Incomplete transform syntax must not be read as a harmless identity."""
        control = _nearest_valid_footer_control()
        totals = ("54 Repositories", "57 Stargazers", "1 Releases")
        self.assertEqual([], _footer_layout_errors(control, totals))
        opening = '<text x="28" y="257" font-size="12">'
        self.assertIn(opening, control)
        for transform in (
            "translate()",
            "rotate(0 0)",
            "translate(0) trailing-garbage",
            "translate(0),",
        ):
            with self.subTest(transform=transform):
                candidate = control.replace(
                    opening,
                    f'<text x="28" y="257" font-size="12" transform="{transform}">',
                    1,
                )
                errors = _footer_layout_errors(candidate, totals)
                self.assertTrue(
                    any(
                        marker in error.casefold()
                        for error in errors
                        for marker in ("transform", "bounds")
                    ),
                    f"malformed transform {transform!r} was accepted as an identity: {errors}",
                )
        for transform in ("rotate(0)", "rotate(0 999 999)", "translate(0, 0)"):
            with self.subTest(identity=transform):
                candidate = control.replace(
                    opening,
                    f'<text x="28" y="257" font-size="12" transform="{transform}">',
                    1,
                )
                self.assertEqual(
                    [],
                    _footer_layout_errors(candidate, totals),
                    f"identity transform {transform!r} preserves geometry and must be accepted",
                )

    def test_compact_gauge_rejects_extra_out_of_bounds_ring(self):
        control = _render_compact_gauge_cases()["builder-live"]
        self.assertEqual([], _compact_gauge_errors(control))
        group_start = control.index('<g data-metric-key="ci_coverage_pct"')
        insertion = control.index("<text", group_start)
        extra_ring = (
            '<circle cx="999" cy="116" r="21.5" fill="none" '
            'stroke="#ffffff" stroke-width="3"/>'
        )
        mutant = control[:insertion] + extra_ring + control[insertion:]
        root = ET.fromstring(mutant)
        claim_group = next(
            node
            for node in root.iter()
            if node.attrib.get("data-metric-key") == "ci_coverage_pct"
        )
        self.assertEqual(
            3,
            len(list(claim_group.iter(f"{_SVG_NS}circle"))),
            "mutant must add exactly one third painted ring",
        )
        errors = _compact_gauge_errors(mutant)
        self.assertTrue(
            any(
                ("ring" in error.casefold() or "circle" in error.casefold())
                and any(
                    marker in error.casefold()
                    for marker in ("bounds", "outside", "margin", "extra")
                )
                for error in errors
            ),
            f"third out-of-bounds ring mutant survived without a ring-geometry error: {errors}",
        )

    def test_compact_ci_gauges_fit_ring_label_and_copy(self):
        cases = _render_compact_gauge_cases()
        self.assertIn("21%", " ".join(line.text for line in _positioned_text_lines(cases["builder-live"])[1]))
        cadence_live_text = " ".join(
            line.text for line in _positioned_text_lines(cases["cadence-live"])[1]
        ).casefold()
        self.assertIn("53/251 repos", cadence_live_text)
        self.assertIn("repo adoption", cadence_live_text)
        self.assertIn(
            "100%",
            " ".join(line.text for line in _positioned_text_lines(cases["builder-boundary"])[1]),
        )

        offenders = []
        for card, svg in cases.items():
            offenders.extend(f"{card}: {error}" for error in _compact_gauge_errors(svg))
        self.assertEqual(
            [],
            offenders,
            "compact CI rings, labels, and copy columns must remain separated at live and boundary values",
        )

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
