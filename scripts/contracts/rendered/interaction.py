"""Touch-target and narrow-viewport decisions over validated rendered facts."""
from __future__ import annotations

import math

from scripts.contracts.rendered.common import (
    CLIPPING_OVERFLOW, ancestors, document_clear, effective_box, packets, visible,
)


def _inline_exception(packet: dict, state: dict, index: int) -> bool:
    node = packet["nodes"][index]
    if node["tag"] != "a" or state["elements"][index]["computed"]["display"] != "inline":
        return False
    parent = node["parent_index"]
    if parent is None:
        return False
    prose = any(row["parent_index"] == parent and row["text"].strip()
                for row in packet["text_nodes"])
    return prose and packet["nodes"][parent]["text_content"].strip() != node["text_content"].strip()


def _equivalent_target(
    packet: dict, index: int, applicable: list[int], boxes: dict[int, dict], floor: float,
) -> bool:
    href = packet["nodes"][index].get("href")
    if not href:
        return False
    return any(other != index and packet["nodes"][other].get("href") == href
               and boxes[other]["width"] >= floor and boxes[other]["height"] >= floor
               for other in applicable)


def _point_to_rect(x: float, y: float, box: dict) -> float:
    dx = max(box["left"] - x, 0, x - box["right"])
    dy = max(box["top"] - y, 0, y - box["bottom"])
    return math.hypot(dx, dy)


def _spacing_exception(
    packet: dict,
    index: int,
    applicable: list[int],
    boxes: dict[int, dict],
    floor: float,
    epsilon: float,
) -> bool:
    box = boxes[index]
    center = ((box["left"] + box["right"]) / 2, (box["top"] + box["bottom"]) / 2)
    radius = floor / 2
    for other in applicable:
        if other == index:
            continue
        other_box = boxes[other]
        if _point_to_rect(*center, other_box) < radius - epsilon:
            return False
        if other_box["width"] < floor or other_box["height"] < floor:
            other_center = ((other_box["left"] + other_box["right"]) / 2,
                            (other_box["top"] + other_box["bottom"]) / 2)
            if math.dist(center, other_center) < floor - epsilon:
                return False
    return True


def _positive_overlap(left: dict, right: dict, epsilon: float) -> bool:
    return (min(left["right"], right["right"]) - max(left["left"], right["left"])
            > epsilon and min(left["bottom"], right["bottom"])
            - max(left["top"], right["top"]) > epsilon)


def rendered_touch_targets(bundle: object, *, policy: dict, **_) -> bool:
    floor = float(policy["predicate_parameters"]["touch_minimum_css_px"])
    epsilon = 10 ** -policy["enumeration"]["css_px_precision"]
    observed_packets = packets(bundle)
    for packet in observed_packets:
        nodes = packet["nodes"]
        subjects = packet["subjects"]["interactive"]
        for state in packet["states"]:
            if not document_clear(state):
                return False
            applicable = [index for index in subjects if visible(nodes, state, index)
                          and state["elements"][index]["disabled"] is not True
                          and state["elements"][index]["computed"]["pointer_events"] != "none"]
            boxes = {index: effective_box(nodes, state, index) for index in applicable}
            if any(box is None or box["width"] <= epsilon or box["height"] <= epsilon
                   for box in boxes.values()):
                return False
            for position, index in enumerate(applicable):
                for other in applicable[position + 1:]:
                    if _positive_overlap(boxes[index], boxes[other], epsilon):
                        return False
                box = boxes[index]
                if box["width"] >= floor and box["height"] >= floor:
                    continue
                if (_inline_exception(packet, state, index)
                        or _equivalent_target(packet, index, applicable, boxes, floor)
                        or _spacing_exception(
                            packet, index, applicable, boxes, floor, epsilon)):
                    continue
                return False
            for index in subjects:
                node = nodes[index]
                if (node["tag"] == "input" and node["type"] != "hidden"
                        and state["elements"][index]["disabled"] is not True
                        and not visible(nodes, state, index)):
                    if not node["id"]:
                        return False
                    labels = [candidate for candidate in applicable
                              if nodes[candidate]["tag"] == "label"
                              and nodes[candidate]["for"] == node["id"]]
                    if not labels:
                        return False
    return bool(observed_packets)


def _matches_parent(node: dict, observed: dict, selector: str) -> bool:
    if selector.startswith("#"):
        return node["id"] == selector[1:]
    if selector.startswith("."):
        return selector[1:] in observed["class"].split()
    return False


def _inside_allowed_scroll(
    packet: dict, state: dict, index: int, rules: list[dict],
    *, viewport_width: float, tolerance: float,
) -> bool:
    nodes = packet["nodes"]
    for ancestor in list(ancestors(nodes, index))[1:]:
        node = nodes[ancestor]
        observed = state["elements"][ancestor]
        parent = node["parent_index"]
        box, scroll, style = observed["box"], observed["scroll"], observed["computed"]
        if style["overflow_x"] not in CLIPPING_OVERFLOW:
            continue
        if (style["overflow_x"] not in {"auto", "scroll"}
                or scroll["client_width"] <= 0
                or scroll["scroll_width"] <= scroll["client_width"]):
            return False
        for rule in rules:
            if (rule["class"] in observed["class"].split() and parent is not None
                    and _matches_parent(nodes[parent], state["elements"][parent], rule["parent"])
                    and box["width"] > 0 and box["left"] >= -tolerance
                    and box["right"] <= viewport_width + tolerance):
                return True
        return False
    return False


def rendered_responsive(bundle: object, *, policy: dict, **_) -> bool:
    width = policy["predicate_parameters"]["responsive_viewport_width"]
    tolerance = policy["predicate_parameters"]["rounding_tolerance_device_px"]
    observed_packets = packets(bundle)
    for packet in observed_packets:
        if packet["viewport"]["width"] != width:
            continue
        rules = policy["allowed_scroll_containers"][packet["page"]]
        for state in packet["states"]:
            if not document_clear(state):
                return False
            if any(state["document"][name]["scroll_width"] > width + tolerance
                   for name in ("root", "body")):
                return False
            if any(state["document"][name]["box"]["left"] < -tolerance
                   or state["document"][name]["box"]["right"] > width + tolerance
                   for name in ("root", "body")):
                return False
            for index, row in enumerate(state["elements"]):
                if not visible(packet["nodes"], state, index):
                    continue
                box = row["box"]
                if box["left"] >= -tolerance and box["right"] <= width + tolerance:
                    continue
                if not _inside_allowed_scroll(
                    packet, state, index, rules,
                    viewport_width=width, tolerance=tolerance,
                ):
                    return False
            for text_node, range_row in zip(packet["text_nodes"], state["text_ranges"]):
                parent = text_node["parent_index"]
                if parent is None or not visible(packet["nodes"], state, parent):
                    continue
                for rect in range_row["rects"]:
                    if rect["left"] >= -tolerance and rect["right"] <= width + tolerance:
                        continue
                    if not _inside_allowed_scroll(
                        packet, state, parent, rules,
                        viewport_width=width, tolerance=tolerance,
                    ):
                        return False
    return bool(observed_packets)
