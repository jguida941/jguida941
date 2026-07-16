"""Deterministic contrast hit-sample geometry and closed packet validation."""
from __future__ import annotations

import math


def _descendant(nodes: list[dict], index: int, ancestor: int) -> bool:
    current: int | None = index
    while current is not None:
        if current == ancestor:
            return True
        current = nodes[current]["parent_index"]
    return False


def _axis(start: float, end: float, step: float) -> list[float]:
    if end <= start:
        return []
    values = []
    value = start + min(step / 2, (end - start) / 2)
    while value < end:
        values.append(value)
        value += step
    center = (start + end) / 2
    if not any(abs(value - center) < 0.01 for value in values):
        values.append(center)
    return sorted(values)


def _quantize(value: float, precision: int) -> float:
    scale = 10 ** precision
    return math.floor(value * scale + 0.5) / scale


def expected_points(
    packet: dict, state: dict, subject_index: int, *, step: float, precision: int,
) -> list[tuple[float, float]]:
    points = []
    for text_node, range_row in zip(packet["text_nodes"], state["text_ranges"]):
        parent = text_node["parent_index"]
        if parent is None or not _descendant(packet["nodes"], parent, subject_index):
            continue
        for rect in range_row["rects"]:
            for x in _axis(rect["left"], rect["right"], step):
                for y in _axis(rect["top"], rect["bottom"], step):
                    points.append((_quantize(x, precision), _quantize(y, precision)))
    return points


def validate_contrast_hits(packet: dict, state: dict, policy: dict, *, label: str) -> None:
    hits = state["contrast_hits"]
    expected_ids = [row["id"] for row in policy["contrast_subjects"]]
    if list(hits) != sorted(expected_ids):
        raise RuntimeError(f"{label}: contrast hit subjects are not canonical")
    step = policy["predicate_parameters"]["contrast_hit_grid_css_px"]
    precision = policy["enumeration"]["css_px_precision"]
    for subject_id in sorted(expected_ids):
        rows = hits[subject_id]
        indices = packet["subjects"]["contrast"][subject_id]
        if [row["subject_index"] for row in rows] != indices:
            raise RuntimeError(f"{label}/{subject_id}: contrast hit subject drift")
        for row in rows:
            expected = expected_points(
                packet, state, row["subject_index"], step=step, precision=precision)
            observed = [(sample["x"], sample["y"]) for sample in row["samples"]]
            if not expected or observed != expected:
                raise RuntimeError(f"{label}/{subject_id}: contrast sample geometry drift")
            if any(
                sample[field] >= len(packet["nodes"])
                for sample in row["samples"]
                for field in ("top_index", "visual_top_index")
            ):
                raise RuntimeError(f"{label}/{subject_id}: contrast hit index drift")
