"""Build the Language Breakdown card.

Power BI information architecture (DESIGN_SPEC 3.2/3.10): the leading-language
share is promoted to the one dominant KPI, and the distribution renders as a flat
part-to-whole LanguageBar capped at <=6 languages (+ Other) with a name+value
legend. An honest empty state renders when there is no language data.
"""

from __future__ import annotations

from scripts.core.config import SVG_WIDTH
from scripts.rendering.components import empty_state, language_bar, primary_kpi, section_header
from scripts.rendering.glass_kit import glass_panel
from scripts.rendering.svg_utils import fmt_int

TITLE = "Language Breakdown"
TOP_N = 6  # <=6 languages, the rest fold into "Other" (DESIGN_SPEC 3.10)


def _human_bytes(n: float) -> str:
    """Compact, human-readable byte size (decimal units, e.g. '24.4 MB')."""
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1000:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1000.0
    return f"{n:.1f} TB"


def _segments(language_bytes: dict, total: float) -> list[tuple[str, float]]:
    ordered = sorted(language_bytes.items(), key=lambda kv: kv[1], reverse=True)
    top = ordered[:TOP_N]
    other = sum(b for _, b in ordered[TOP_N:])
    segs = [(name, b / total * 100.0) for name, b in top]
    if other > 0:
        segs.append(("Other", other / total * 100.0))
    return segs


def generate(language_bytes: dict, output_path: str = "assets/lang_breakdown.svg", top_n: int | None = None):
    _ = top_n  # capping is fixed by the design contract (<=6 + Other)
    width = SVG_WIDTH
    pad = 28
    total = sum((language_bytes or {}).values())

    header_svg, content_top = section_header(
        pad, 46, TITLE, width=width, eyebrow="Repository Composition", pad=pad
    )

    if total <= 0:
        height = int(content_top + 92)
        parts = [glass_panel(width, height), header_svg]
        parts.append(empty_state(width / 2, content_top + 48, "No language data available", icon_name="code"))
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
        )
        with open(output_path, "w") as f:
            f.write(svg)
        return output_path

    segments = _segments(language_bytes, total)
    lead_name, lead_pct = segments[0]

    # --- geometry: KPI top-left, full-width language bar + legend below ---
    bar_x = pad
    bar_w = width - pad * 2
    bar_y = content_top + 124
    bar_svg, legend_bottom = language_bar(bar_x, bar_y, bar_w, segments=segments, height=16)
    height = int(legend_bottom + 28)

    parts: list[str] = [glass_panel(width, height), header_svg]

    # PrimaryKpiCard: the leading language's share is the dominant number.
    parts.append(
        primary_kpi(
            pad,
            content_top + 58,
            value=f"{round(lead_pct)}%",
            label=lead_name,
            sublabel=f"{fmt_int(len(language_bytes))} languages · {_human_bytes(total)}",
        )
    )
    parts.append(bar_svg)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    )
    with open(output_path, "w") as f:
        f.write(svg)
    return output_path
