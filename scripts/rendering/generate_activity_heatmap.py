"""Contribution-calendar weekday distribution at the stable activity SVG URL."""
from scripts.contracts.profile_contract import contribution_rhythm_display
from scripts.core.config import CYAN, FONT_SANS, SVG_WIDTH, TEXT, TEXT_BRIGHT, TEXT_DIM
from scripts.rendering.components import section_header
from scripts.rendering.glass_kit import glass_panel
from scripts.rendering.svg_utils import xml_escape


def _text(value, x, y, *, fill=TEXT, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="14" font-family="{FONT_SANS}" '
            f'fill="{fill}" text-anchor="{anchor}">{xml_escape(value)}</text>')


def generate(rhythm: dict | None, output_path: str = "assets/activity_heatmap.svg"):
    display = contribution_rhythm_display(rhythm)
    available = display["available"]
    description = " ".join(display[key] for key in ("scope", "explanation", "coverage_summary") if display[key])
    width, height = SVG_WIDTH, 480 if available else 232
    header, _ = section_header(28, 46, display["title"], width=width, eyebrow="Contribution calendar", pad=28)
    parts = [f'<title id="rhythm-title">{display["title"]}</title>',
             f'<desc id="rhythm-description">{xml_escape(description)}</desc>',
             glass_panel(width, height), header,
             '<g data-series="weekday-contributions">',
             _text(display["subtitle"], 28, 116, fill=TEXT_BRIGHT)]
    if available:
        parts.append(_text(display["caption"], 28, 142, fill=TEXT_DIM))
        maximum = max((row["contributions"] for row in display["rows"]), default=0) or 1
        # Common zero origin; absent contributions draw a true zero-width bar.
        for i, row in enumerate(display["rows"]):
            y = 178 + i * 34
            bar_width = row["contributions"] / maximum * (width - 200)
            parts.extend([
                f'<g data-weekday="{row["weekday"]}" data-contributions="{row["contributions"]}" data-days-observed="{row["days_observed"]}">',
                _text(row["weekday"], 28, y + 5),
                f'<rect x="92" y="{y - 8}" width="{bar_width:.3f}" height="12" rx="3" fill="{CYAN}"/>',
                _text(row["count_text"], width - 28, y + 5, fill=TEXT_BRIGHT, anchor="end"),
                '</g>',
            ])
        parts.append(_text(display["message"], 28, 416, fill=TEXT_DIM))
        parts.append(_text(display["qualification"], 28, 438, fill=TEXT_DIM))
    else:
        parts.append(_text(display["message"], 28, 160, fill=TEXT_BRIGHT))
        parts.append(_text(display["qualification"], 28, 192, fill=TEXT_DIM))
    parts.append('</g>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="rhythm-title rhythm-description">'
           + "".join(parts) + '</svg>')
    with open(output_path, "w") as handle:
        handle.write(svg)
    return output_path
