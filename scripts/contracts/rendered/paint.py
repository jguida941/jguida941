"""Spatial paint-stack decisions for rendered contrast predicates."""
from __future__ import annotations

from scripts.contracts.rendered.common import ancestors, document_clear
from scripts.contracts.rendered.effects import escape_capable, paint_boundary_excludes
from scripts.contracts.rendered.values import composite, number, px, rgba


_GRAPHIC_TAGS = {
    "canvas", "circle", "ellipse", "embed", "foreignobject", "g", "iframe", "image",
    "img", "line", "object", "path", "polygon", "polyline", "rect", "svg", "text",
    "textpath", "use", "video",
}
_ESCAPING_GRAPHIC_TAGS = _GRAPHIC_TAGS - {
    "canvas", "embed", "iframe", "img", "object", "svg", "video",
}


def _contains(box: dict, x: float, y: float) -> bool:
    return box["left"] <= x <= box["right"] and box["top"] <= y <= box["bottom"]


def _descendant(nodes: list[dict], index: int, ancestor: int) -> bool:
    return ancestor in ancestors(nodes, index)


def _paint_layout_present(nodes: list[dict], state: dict, index: int) -> bool:
    if not document_clear(state):
        return False
    if state["elements"][index]["computed"]["visibility"] in {"hidden", "collapse"}:
        return False
    for ancestor in ancestors(nodes, index):
        row = state["elements"][ancestor]
        style = row["computed"]
        opacity = number(style["opacity"])
        if (style["display"] == "none"
                or style["content_visibility"] == "hidden"
                or opacity is None or opacity <= 0):
            return False
    return True


def _foreign_text_paints(
    packet: dict, state: dict, subject: int, samples: list[dict],
) -> bool:
    for text, ranges in zip(packet["text_nodes"], state["text_ranges"]):
        parent = text["parent_index"]
        if (parent is None or _descendant(packet["nodes"], parent, subject)
                or not _paint_layout_present(packet["nodes"], state, parent)):
            continue
        style = state["elements"][parent]["computed"]
        fill = rgba(style["webkit_text_fill_color"])
        if fill is None or fill[3] <= 0:
            continue
        if any(_contains(rect, sample["x"], sample["y"])
               for rect in ranges["rects"] for sample in samples):
            return True
    return False


def _foreign_paints(
    packet: dict, state: dict, subject: int, lineage: set[int], samples: list[dict],
) -> bool:
    if _foreign_text_paints(packet, state, subject, samples):
        return True
    for index, (node, row) in enumerate(zip(packet["nodes"], state["elements"])):
        if index in lineage or not _paint_layout_present(packet["nodes"], state, index):
            continue
        style = row["computed"]
        background = rgba(style["background_color"])
        borders = [px(style[f"border_{side}_width"])
                   for side in ("top", "right", "bottom", "left")]
        can_escape = escape_capable(row) or node["tag"] in _ESCAPING_GRAPHIC_TAGS
        if can_escape and any(
            _contains(row["box"], sample["x"], sample["y"])
            or not paint_boundary_excludes(
                packet["nodes"], state, index, sample["x"], sample["y"]
            ) for sample in samples
        ):
            return True
        painted = (background is None or background[3] > 0
                or style["background_image"] != "none"
                or style["backdrop_filter"] != "none"
                or style["mix_blend_mode"] != "normal"
                or any(width is None or width > 0 for width in borders)
                or node["tag"] in _GRAPHIC_TAGS
                )
        if painted and any(_contains(row["box"], sample["x"], sample["y"])
                           for sample in samples):
            return True
    return False


def _spatially_closed(packet: dict, state: dict, index: int, samples: list[dict]) -> bool:
    lineage = list(ancestors(packet["nodes"], index))
    element_rows = [state["elements"][ancestor] for ancestor in lineage]
    document_rows = [state["document"]["body"], state["document"]["root"]]
    if any(not _contains(row["box"], sample["x"], sample["y"])
           for sample in samples for row in element_rows + document_rows):
        return False
    return not _foreign_paints(packet, state, index, set(lineage), samples)


def paint_background(
    packet: dict, state: dict, index: int, samples: list[dict],
) -> tuple | None:
    nodes = packet["nodes"]
    chain = list(ancestors(nodes, index))
    document_rows = [state["document"]["body"], state["document"]["root"]]
    rows = [state["elements"][ancestor] for ancestor in chain] + document_rows
    if not _spatially_closed(packet, state, index, samples):
        return None
    for row in rows:
        style = row["computed"]
        if (style["background_image"] != "none" or escape_capable(row)
                or style["backdrop_filter"] != "none"
                or style["mix_blend_mode"] != "normal" or style["transform"] != "none"
                or style["clip_path"] != "none" or style["mask_image"] != "none"
                or style["background_clip"] != "border-box"
                ):
            return None
    layers = []
    for row in rows:
        layer = rgba(row["computed"]["background_color"])
        if layer is None:
            return None
        layers.append(layer)
        if layer[3] == 1:
            break
    if not layers or layers[-1][3] != 1:
        return None
    result = layers[-1]
    for layer in reversed(layers[:-1]):
        result = composite(layer, result)
        if result is None:
            return None
    return result
