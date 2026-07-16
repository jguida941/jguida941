"""Closed CSS numeric, color, and generated-paint value helpers."""
from __future__ import annotations

import math
import re


_COLOR = re.compile(
    r"rgba?\(\s*([\d.]+)[, ]+([\d.]+)[, ]+([\d.]+)(?:\s*[,/]\s*([\d.]+))?\s*\)"
)
_SRGB = re.compile(
    r"color\(srgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s*/\s*([\d.]+))?\)"
)


def number(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def px(value: object) -> float | None:
    text = str(value).strip()
    return number(text[:-2]) if text.endswith("px") else None


def rgba(value: object) -> tuple[float, float, float, float] | None:
    text = str(value).strip()
    match = _SRGB.fullmatch(text)
    if match:
        red, green, blue = (number(match.group(index)) for index in range(1, 4))
        alpha = number(match.group(4)) if match.group(4) is not None else 1.0
        if None in (red, green, blue, alpha) or not all(
            0 <= channel <= 1 for channel in (red, green, blue, alpha)
        ):
            return None
        return red, green, blue, alpha
    match = _COLOR.fullmatch(text)
    if not match:
        return None
    red, green, blue = (number(match.group(index)) for index in range(1, 4))
    alpha = number(match.group(4)) if match.group(4) is not None else 1.0
    if None in (red, green, blue, alpha):
        return None
    if not all(0 <= channel <= 255 for channel in (red, green, blue)) or not 0 <= alpha <= 1:
        return None
    return red / 255, green / 255, blue / 255, alpha


def composite(front: tuple, back: tuple) -> tuple | None:
    alpha = front[3] + back[3] * (1 - front[3])
    if alpha <= 0:
        return None
    rgb = tuple(
        (front[index] * front[3] + back[index] * back[3] * (1 - front[3])) / alpha
        for index in range(3)
    )
    return (*rgb, alpha)


def luminance(color: tuple) -> float:
    channels = [channel / 12.92 if channel <= 0.04045
                else ((channel + 0.055) / 1.055) ** 2.4 for channel in color[:3]]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def pseudo_paints(pseudo: dict) -> bool:
    content = pseudo["content"]
    if content in {"none", "normal"}:
        return False
    opacity = number(pseudo["opacity"])
    if opacity is None:
        return True
    if pseudo["display"] == "none" or opacity <= 0:
        return False
    if content not in {'""', "''"}:
        return True
    background = rgba(pseudo["background_color"])
    strokes = []
    for side in ("top", "right", "bottom", "left"):
        width = px(pseudo[f"border_{side}_width"])
        color = rgba(pseudo[f"border_{side}_color"])
        strokes.append(width is None or (width > 0
            and pseudo[f"border_{side}_style"] not in {"none", "hidden"}
            and (color is None or color[3] > 0)))
    outline_width = px(pseudo["outline_width"])
    outline_color = rgba(pseudo["outline_color"])
    outline = (outline_width is None or (outline_width > 0
        and pseudo["outline_style"] not in {"none", "hidden"}
        and (outline_color is None or outline_color[3] > 0)))
    return (background is None or background[3] > 0
            or pseudo["background_image"] != "none"
            or pseudo["filter"] != "none" or pseudo["backdrop_filter"] != "none"
            or pseudo["mix_blend_mode"] != "normal" or any(strokes) or outline
            or pseudo["border_image_source"] != "none"
            or pseudo["box_shadow"] != "none")
