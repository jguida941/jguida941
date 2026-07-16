"""Fail-closed containment proof for paint that can escape a border box."""
from __future__ import annotations

from scripts.contracts.rendered.values import pseudo_paints, px, rgba


_CLIPPING_OVERFLOW = {"auto", "clip", "hidden", "scroll"}
_PAINT_CONTAINMENT = {"paint", "content", "strict"}


def _outline_paints(style: dict) -> bool:
    width = px(style["outline_width"])
    color = rgba(style["outline_color"])
    return (width is None or (width > 0
        and style["outline_style"] not in {"none", "hidden"}
        and (color is None or color[3] > 0)))


def escape_capable(row: dict) -> bool:
    """Return whether observed ink may extend outside ``row['box']``."""
    style = row["computed"]
    text_stroke = px(style["webkit_text_stroke_width"])
    return (style["box_shadow"] != "none" or style["filter"] != "none"
            or style["text_shadow"] != "none" or _outline_paints(style)
            or text_stroke is None or text_stroke > 0
            or style["border_image_source"] != "none"
            or any(pseudo_paints(pseudo) for pseudo in row["pseudo"].values()))


def _outside(box: dict, x: float, y: float, margin: float = 0) -> tuple[bool, bool]:
    return (x < box["left"] - margin or x > box["right"] + margin,
            y < box["top"] - margin or y > box["bottom"] + margin)


def paint_boundary_excludes(
    nodes: list[dict], state: dict, index: int, x: float, y: float,
) -> bool:
    """Prove an ancestor clips an effect-bearing descendant away from a sample."""
    ancestor = nodes[index]["parent_index"]
    while ancestor is not None:
        row = state["elements"][ancestor]
        style = row["computed"]
        margin = px(style["overflow_clip_margin"])
        if margin is not None and margin >= 0:
            outside_x, outside_y = _outside(row["box"], x, y, margin)
            containment = set(style["contain"].split())
            if containment & _PAINT_CONTAINMENT and (outside_x or outside_y):
                return True
            if (style["overflow_x"] in _CLIPPING_OVERFLOW and outside_x
                    or style["overflow_y"] in _CLIPPING_OVERFLOW and outside_y):
                return True
        ancestor = nodes[ancestor]["parent_index"]
    return False
