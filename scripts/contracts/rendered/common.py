"""Shared visibility and rectangular geometry over validated browser facts."""
from __future__ import annotations

from scripts.contracts.rendered.effects import escape_capable
from scripts.contracts.rendered.values import number, px


CLIPPING_OVERFLOW = {"auto", "clip", "hidden", "scroll"}


def packets(bundle: object) -> list[dict]:
    if not isinstance(bundle, list) or not bundle:
        return []
    rows = []
    for entry in bundle:
        if not isinstance(entry, dict) or not isinstance(entry.get("facts"), dict):
            return []
        rows.append(entry["facts"])
    return rows


def ancestors(nodes: list[dict], index: int):
    current: int | None = index
    seen = set()
    while current is not None and current not in seen:
        seen.add(current)
        yield current
        current = nodes[current]["parent_index"]


def document_clear(state: dict) -> bool:
    for name in ("root", "body"):
        row = state["document"][name]
        style = row["computed"]
        if (row["rect_count"] <= 0
                or row["box"]["width"] <= 0 or row["box"]["height"] <= 0
                or style["display"] == "none"
                or style["visibility"] in {"hidden", "collapse"}
                or style["content_visibility"] == "hidden"
                or style["overflow_x"] in CLIPPING_OVERFLOW
                or style["overflow_y"] in CLIPPING_OVERFLOW
                or number(style["opacity"]) != 1
                or escape_capable(row)
                or style["backdrop_filter"] != "none"
                or style["mix_blend_mode"] != "normal"
                or style["clip_path"] != "none" or style["mask_image"] != "none"
                ):
            return False
    return True


def visible(nodes: list[dict], state: dict, index: int) -> bool:
    if not document_clear(state):
        return False
    rows = state["elements"]
    row = rows[index]
    if row["rect_count"] <= 0 or row["box"]["width"] <= 0 or row["box"]["height"] <= 0:
        return False
    if row["computed"]["visibility"] in {"hidden", "collapse"}:
        return False
    for ancestor in ancestors(nodes, index):
        observed = rows[ancestor]
        style = observed["computed"]
        opacity = number(style["opacity"])
        if (style["display"] == "none"
                or style["content_visibility"] == "hidden"
                or opacity is None or opacity <= 0):
            return False
    return True


def foreground_paint_clear(nodes: list[dict], state: dict, index: int) -> bool:
    for ancestor in ancestors(nodes, index):
        style = state["elements"][ancestor]["computed"]
        if (style["filter"] != "none" or style["mix_blend_mode"] != "normal"
                or style["clip_path"] != "none" or style["mask_image"] != "none"):
            return False
    return True


def intersect(left: dict, right: dict, *, x: bool = True, y: bool = True) -> dict:
    x1 = max(left["left"], right["left"]) if x else left["left"]
    x2 = min(left["right"], right["right"]) if x else left["right"]
    y1 = max(left["top"], right["top"]) if y else left["top"]
    y2 = min(left["bottom"], right["bottom"]) if y else left["bottom"]
    return {"left": x1, "right": x2, "top": y1, "bottom": y2,
            "width": max(0.0, x2 - x1), "height": max(0.0, y2 - y1)}


def effective_box(nodes: list[dict], state: dict, index: int) -> dict | None:
    observed = state["elements"][index]
    style = observed["computed"]
    if style.get("clip_path", "none") != "none" or style.get("mask_image", "none") != "none":
        return None
    result = dict(observed["box"])
    for ancestor in list(ancestors(nodes, index))[1:]:
        parent = state["elements"][ancestor]
        parent_style = parent["computed"]
        if parent_style.get("clip_path", "none") != "none" or parent_style.get(
            "mask_image", "none") != "none":
            return None
        clip_x = parent_style["overflow_x"] in CLIPPING_OVERFLOW
        clip_y = parent_style["overflow_y"] in CLIPPING_OVERFLOW
        if not clip_x and not clip_y:
            continue
        if parent_style["transform"] != "none":
            return None
        border_left = px(parent_style["border_left_width"])
        border_top = px(parent_style["border_top_width"])
        if border_left is None or border_top is None:
            return None
        clip = {
            "left": parent["box"]["left"] + border_left,
            "right": parent["box"]["left"] + border_left + parent["scroll"]["client_width"],
            "top": parent["box"]["top"] + border_top,
            "bottom": parent["box"]["top"] + border_top + parent["scroll"]["client_height"],
        }
        result = intersect(result, clip, x=clip_x, y=clip_y)
    return result
