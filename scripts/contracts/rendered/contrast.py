"""Deterministic WCAG contrast decisions over validated rendered facts."""
from __future__ import annotations

from scripts.contracts.rendered.common import ancestors, document_clear, packets, visible
from scripts.contracts.rendered.paint import paint_background
from scripts.contracts.rendered.values import composite, luminance, number, px, rgba


def _fully_opaque(nodes: list[dict], state: dict, index: int) -> bool:
    return all(number(state["elements"][ancestor]["computed"]["opacity"]) == 1
               for ancestor in ancestors(nodes, index))


def _qualifies_as_large(style: dict, policy: dict) -> bool:
    parameters = policy["predicate_parameters"]
    font_size = px(style["font_size"])
    font_weight = number(style["font_weight"])
    if font_size is None or font_weight is None:
        return False
    return (font_size + 1e-9 >= parameters["large_text_minimum_css_px"]
            or (font_size + 1e-9 >= parameters["large_bold_text_minimum_css_px"]
                and font_weight >= parameters["large_bold_text_minimum_weight"]))


def _samples(packet: dict, state: dict, subject_id: str, index: int) -> list[dict] | None:
    rows = [row for row in state["contrast_hits"][subject_id]
            if row["subject_index"] == index]
    if len(rows) != 1 or not rows[0]["samples"]:
        return None
    samples = rows[0]["samples"]
    return samples if all(
        sample["top_index"] == index and sample["visual_top_index"] == index
        for sample in samples
    ) else None


def rendered_contrast(bundle: object, *, policy: dict, **_) -> bool:
    specs = {row["id"]: row for row in policy["contrast_subjects"]}
    observed_packets = packets(bundle)
    for packet in observed_packets:
        nodes = packet["nodes"]
        for state in packet["states"]:
            if not document_clear(state):
                return False
            for subject_id, spec in specs.items():
                indices = packet["subjects"]["contrast"].get(subject_id, [])
                if len(indices) != spec["count"]:
                    return False
                for index in indices:
                    samples = _samples(packet, state, subject_id, index)
                    if not visible(nodes, state, index) or samples is None:
                        return False
                    style = state["elements"][index]["computed"]
                    if (not _fully_opaque(nodes, state, index)
                            or style["text_shadow"] != "none"
                            or px(style["webkit_text_stroke_width"]) != 0
                            or style["background_clip"] == "text"):
                        return False
                    if spec["classification"] == "large" and not _qualifies_as_large(
                        style, policy
                    ):
                        return False
                    background = paint_background(packet, state, index, samples)
                    foreground = rgba(style["color"])
                    fill = rgba(style["webkit_text_fill_color"])
                    if (background is None or foreground is None or fill != foreground
                            or foreground[3] != 1 or fill[3] != 1):
                        return False
                    foreground = composite(foreground, background)
                    if foreground is None:
                        return False
                    light, dark = sorted(
                        (luminance(foreground), luminance(background)), reverse=True)
                    if (light + 0.05) / (dark + 0.05) + 1e-9 < spec["minimum_ratio"]:
                        return False
    return bool(observed_packets)
