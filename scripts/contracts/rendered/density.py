"""Token-bound visible-content density decisions over rendered page facts."""
from __future__ import annotations

from scripts.contracts.rendered.common import (
    CLIPPING_OVERFLOW, ancestors, document_clear, foreground_paint_clear, intersect, packets,
    visible,
)
from scripts.contracts.rendered.values import px, rgba


def _descendant(nodes: list[dict], index: int, ancestor: int) -> bool:
    current: int | None = index
    while current is not None:
        if current == ancestor:
            return True
        current = nodes[current]["parent_index"]
    return False


def _painted_text(style: dict) -> bool:
    color = rgba(style["color"])
    fill = rgba(style["webkit_text_fill_color"])
    return (color is not None and color[3] > 0
            and fill is not None and fill[3] > 0)


def _clip_rect(
    nodes: list[dict], state: dict, parent: int, rect: dict, *, include_self: bool = True,
) -> dict | None:
    result = dict(rect)
    chain = list(ancestors(nodes, parent))
    for index in chain if include_self else chain[1:]:
        observed = state["elements"][index]
        style = observed["computed"]
        if style["clip_path"] != "none" or style["mask_image"] != "none":
            return None
        clip_x = style["overflow_x"] in CLIPPING_OVERFLOW
        clip_y = style["overflow_y"] in CLIPPING_OVERFLOW
        if not clip_x and not clip_y:
            continue
        if style["transform"] != "none":
            return None
        border_left = px(style["border_left_width"])
        border_top = px(style["border_top_width"])
        if border_left is None or border_top is None:
            return None
        clip = {"left": observed["box"]["left"] + border_left,
                "right": observed["box"]["left"] + border_left
                    + observed["scroll"]["client_width"],
                "top": observed["box"]["top"] + border_top,
                "bottom": observed["box"]["top"] + border_top
                    + observed["scroll"]["client_height"]}
        result = intersect(result, clip, x=clip_x, y=clip_y)
    return result


def _content_intervals(
    packet: dict, state: dict, child: int, surface_box: dict, epsilon: float,
) -> list[list[float]]:
    nodes, rows = packet["nodes"], state["elements"]
    intervals = []
    for text_node, range_row in zip(packet["text_nodes"], state["text_ranges"]):
        parent = text_node["parent_index"]
        if (parent is not None and _descendant(nodes, parent, child)
                and visible(nodes, state, parent)
                and foreground_paint_clear(nodes, state, parent)
                and _painted_text(rows[parent]["computed"])):
            for rect in range_row["rects"]:
                clipped = _clip_rect(nodes, state, parent, rect)
                if clipped is None:
                    continue
                clipped = intersect(clipped, surface_box)
                if clipped["width"] > epsilon and clipped["height"] > epsilon:
                    intervals.append((clipped["top"], clipped["bottom"]))
    for index, node in enumerate(nodes):
        if (not _descendant(nodes, index, child) or not visible(nodes, state, index)
                or not foreground_paint_clear(nodes, state, index)):
            continue
        style = rows[index]["computed"]
        background = rgba(style["background_color"])
        governed_prototype = "data-prototype-origin" in node["data"] and (
            background is not None and background[3] > 0
        )
        if not governed_prototype:
            continue
        clipped = _clip_rect(
            nodes, state, index, rows[index]["box"], include_self=False
        )
        if clipped is None:
            continue
        clipped = intersect(clipped, surface_box)
        if clipped["width"] > epsilon and clipped["height"] > epsilon:
            intervals.append((clipped["top"], clipped["bottom"]))
    return _merge(intervals, epsilon)


def _allowed_length(value: str, tokens: list[str], literals: list[str], root_tokens: dict) -> bool:
    return value in literals or any(value == root_tokens.get(token) for token in tokens)


def _merge(intervals: list[tuple[float, float]], epsilon: float) -> list[list[float]]:
    merged: list[list[float]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1] + epsilon:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return merged


def _max_blank_run(intervals: list[list[float]], start: float, end: float) -> float:
    gaps = [max(0.0, intervals[0][0] - start), max(0.0, end - intervals[-1][1])]
    gaps.extend(max(0.0, right[0] - left[1])
                for left, right in zip(intervals, intervals[1:]))
    return max(gaps)


def _density_surface(packet: dict, state: dict, index: int, spec: dict, policy: dict) -> bool:
    nodes, rows = packet["nodes"], state["elements"]
    if not visible(nodes, state, index) or not foreground_paint_clear(nodes, state, index):
        return False
    epsilon = 10 ** -policy["enumeration"]["css_px_precision"]
    tolerance = policy["predicate_parameters"]["rounding_tolerance_device_px"]
    observed = rows[index]
    style, tokens = observed["computed"], state["document"]["root_tokens"]
    for side, token in spec["padding_tokens"].items():
        if style[f"padding_{side}"] != tokens.get(token):
            return False
    allowed_gaps = set(spec["allowed_gap_values"])
    allowed_gaps.update(tokens.get(token) for token in spec.get("allowed_gap_tokens", []))
    if style["row_gap"] not in allowed_gaps or style["column_gap"] not in allowed_gaps:
        return False
    children = [child for child, node in enumerate(nodes)
                if node["parent_index"] == index and visible(nodes, state, child)
                and rows[child]["computed"]["position"] not in {"absolute", "fixed"}]
    if not children:
        return False
    margin_tokens = spec["allowed_child_block_margin_tokens"]
    margin_literals = spec["allowed_child_block_margin_literals"]
    border_top, border_bottom = px(style["border_top_width"]), px(style["border_bottom_width"])
    padding_top, padding_bottom = px(style["padding_top"]), px(style["padding_bottom"])
    if None in (border_top, border_bottom, padding_top, padding_bottom):
        return False
    content_top = observed["box"]["top"] + border_top + padding_top
    content_bottom = observed["box"]["bottom"] - border_bottom - padding_bottom
    content_box = {"left": observed["box"]["left"], "right": observed["box"]["right"],
                   "top": content_top, "bottom": content_bottom}
    intervals = []
    for child in children:
        child_style = rows[child]["computed"]
        if not all(_allowed_length(
            child_style[f"margin_{side}"], margin_tokens, margin_literals, tokens
        ) for side in ("top", "bottom")):
            return False
        margin_top = px(child_style["margin_top"])
        margin_bottom = px(child_style["margin_bottom"])
        if margin_top is None or margin_bottom is None:
            return False
        start = rows[child]["box"]["top"] - margin_top
        end = rows[child]["box"]["bottom"] + margin_bottom
        if start < content_top - epsilon or end > content_bottom + epsilon:
            return False
        content_intervals = _content_intervals(
            packet, state, child, content_box, epsilon)
        child_top = max(rows[child]["box"]["top"], content_top)
        child_bottom = min(rows[child]["box"]["bottom"], content_bottom)
        if (not content_intervals or _max_blank_run(
                content_intervals, child_top, child_bottom
        ) > policy["predicate_parameters"]["density_max_child_blank_run_css_px"] + epsilon):
            return False
        intervals.append((max(start, content_top), min(end, content_bottom)))
    merged = _merge(intervals, epsilon)
    row_gap = 0.0 if style["row_gap"] in {"normal", "0px"} else px(style["row_gap"])
    if row_gap is None:
        return False
    residual = max(0.0, merged[0][0] - content_top)
    residual += max(0.0, content_bottom - merged[-1][1])
    residual += sum(max(0.0, right[0] - left[1] - row_gap)
                    for left, right in zip(merged, merged[1:]))
    return residual <= tolerance + epsilon


def rendered_content_density(bundle: object, *, policy: dict, **_) -> bool:
    observed_packets = packets(bundle)
    for packet in observed_packets:
        surfaces = {row["selector"]: row for row in policy["density_surfaces"][packet["page"]]}
        for state in packet["states"]:
            if not document_clear(state):
                return False
            for selector, spec in surfaces.items():
                indices = packet["subjects"]["density"].get(selector, [])
                visible_indices = [index for index in indices
                                   if visible(packet["nodes"], state, index)]
                expected_visible = spec.get("visible_count", len(indices))
                if len(visible_indices) != expected_visible or not visible_indices:
                    return False
                if any(not _density_surface(packet, state, index, spec, policy)
                       for index in visible_indices):
                    return False
    return bool(observed_packets)
