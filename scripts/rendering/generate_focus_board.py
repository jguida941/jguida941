"""Current Focus board — Now / Next / Shipped lanes (DESIGN_SPEC 3.5/3.11/Part 4).

Three uniform lane columns on the locked type ladder. Lane identity is the LABEL
(not a per-lane rainbow hue — the old CYAN/ORANGE/GREEN tell is gone); items are
uniform rows (body title + caption detail, a neutral lock for private). Glass kept.
"""

from __future__ import annotations

from scripts.core.config import SPACE, SVG_WIDTH, TEXT, TEXT_BRIGHT, TEXT_DIM
from scripts.rendering.components import empty_state, section_header, text
from scripts.rendering.glass_kit import glass_panel, glass_tile, icon
from scripts.rendering.svg_utils import truncate, xml_escape

PAD = 28
LANES = (("now", "Now"), ("next", "Next"), ("shipped", "Shipped"))
MAX_ITEMS = 3
ITEM_PITCH = 46


def _lane(focus: dict, key: str, label: str, x: float, y: float, w: float, h: float) -> str:
    pad = SPACE["md"]
    items = focus.get(key) if isinstance(focus, dict) else None
    items = [i for i in (items or []) if isinstance(i, dict)][:MAX_ITEMS]
    parts = [glass_tile(x, y, w, h)]
    # lane header: neutral label + count (no rainbow)
    parts.append(text(label.upper(), x + pad, y + 22, token="eyebrow", color=TEXT_DIM, tracking=1.2))
    parts.append(text(str(len(items)), x + w - pad, y + 23, token="caption", color=TEXT_DIM, anchor="end"))
    parts.append(
        f'<rect x="{x + pad:g}" y="{y + 32:g}" width="{w - pad * 2:g}" height="1" '
        f'fill="{TEXT_DIM}" fill-opacity="0.16"/>'
    )
    if not items:
        parts.append(text("Nothing here", x + pad, y + 60, token="caption", color=TEXT_DIM))
        return "".join(parts)
    iy = y + 56
    name_max = max(10, int((w - pad * 2) / 8))
    for item in items:
        tx = x + pad
        if item.get("is_private"):
            parts.append(icon("lock", x + pad, iy - 12, size=14, color=TEXT_DIM))
            tx = x + pad + 19
        title = truncate(str(item.get("title") or "item"), name_max)
        url = str(item.get("url") or "").strip()
        node = text(xml_escape(title), tx, iy, token="body", color=TEXT_BRIGHT)
        parts.append(f'<a href="{xml_escape(url)}">{node}</a>' if url and not item.get("is_private") else node)
        detail = truncate(str(item.get("detail") or "").strip(), name_max + 4)
        if detail:
            parts.append(text(xml_escape(detail), x + pad, iy + 16, token="caption", color=TEXT_DIM))
        iy += ITEM_PITCH
    return "".join(parts)


def generate(focus: dict, output_path: str = "assets/now_next_shipped.svg") -> str:
    width = SVG_WIDTH
    header_svg, content_top = section_header(
        PAD, 46, "Current Focus", width=width, eyebrow="Active Focus",
        right_text="now · next · shipped", pad=PAD,
    )

    has_any = isinstance(focus, dict) and any(focus.get(k) for k, _ in LANES)
    if not has_any:
        empty_header, _ = section_header(PAD, 46, "Current Focus", width=width, eyebrow="Active Focus", pad=PAD)
        height = int(content_top + 92)
        body = "".join([glass_panel(width, height), empty_header,
                        empty_state(width / 2, content_top + 48, "No focus items yet", icon_name="check")])
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                    f'viewBox="0 0 {width} {height}">{body}</svg>')
        return output_path

    gap = SPACE["md"]
    lane_w = (width - PAD * 2 - gap * 2) / 3
    lane_top = content_top + 8
    lane_h = 56 + MAX_ITEMS * ITEM_PITCH
    height = int(lane_top + lane_h + 22)
    parts = [glass_panel(width, height), header_svg]
    for i, (key, label) in enumerate(LANES):
        parts.append(_lane(focus, key, label, PAD + i * (lane_w + gap), lane_top, lane_w, lane_h))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>')
    return output_path
