"""Build the "By The Numbers" totals card.

Power BI information architecture (DESIGN_SPEC 3.2/3.3): one dominant KPI
(12-month contributions) at display size, top-left, with the remaining profile
totals demoted to a row of secondary metric tiles with neutral monochrome icons.
Numbers are k/M-scaled to <=4 numerals; an honest empty state renders when there
is no data at all.
"""

from __future__ import annotations

from scripts.core.config import SVG_WIDTH, SPACE, TEXT_DIM
from scripts.rendering.components import empty_state, metric_tile, primary_kpi, section_header
from scripts.rendering.glass_kit import glass_panel
from scripts.rendering.svg_utils import fmt_compact


def _empty(value: object) -> bool:
    return value is None or value == 0


def generate(
    public_nonfork_repos: int,
    public_forks: int,
    private_owned_repos: int | None,
    ci_count: int | None,
    last_year_contributions: int | None,
    output_path: str = "assets/badges.svg",
):
    width = SVG_WIDTH
    pad = 28

    header_svg, content_top = section_header(
        pad,
        46,
        "By The Numbers",
        width=width,
        eyebrow="GitHub · Profile Totals",
        pad=pad,
    )

    secondary = [
        ("code", fmt_compact(public_nonfork_repos), "public repos"),
        ("fork", fmt_compact(public_forks), "forks"),
        ("lock", fmt_compact(private_owned_repos), "private repos"),
        ("workflow", fmt_compact(ci_count), "CI pipelines"),
    ]

    # Honest empty state: nothing to show -> one explanatory line, no fabricated tiles.
    if all(
        _empty(v)
        for v in (
            last_year_contributions,
            public_nonfork_repos,
            public_forks,
            private_owned_repos,
            ci_count,
        )
    ):
        height = int(content_top + 92)
        parts = [glass_panel(width, height), header_svg]
        parts.append(
            empty_state(
                width / 2,
                content_top + 48,
                "No profile metrics available yet",
                icon_name="code",
            )
        )
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
        )
        with open(output_path, "w") as f:
            f.write(svg)
        return output_path

    height = int(content_top + 124)
    parts = [glass_panel(width, height), header_svg]

    # PrimaryKpiCard: the one dominant metric, top-left.
    kpi_y = content_top + 58
    parts.append(
        primary_kpi(
            pad,
            kpi_y,
            value=fmt_compact(last_year_contributions),
            label="contributions",
            sublabel="last 12 months",
        )
    )
    kpi_w = 244
    parts.append(
        f'<rect x="{pad + kpi_w:g}" y="{content_top + 6:g}" width="1" '
        f'height="84" fill="{TEXT_DIM}" fill-opacity="0.16"/>'
    )

    # Supporting row of four secondary metric tiles (neutral icons).
    grid_x = pad + kpi_w + SPACE["xl"]
    cols, gap = 4, SPACE["md"]
    col_w = (width - pad - grid_x - gap * (cols - 1)) / cols
    tile_h = 66
    tile_y = content_top + 26
    for i, (icon_name, value, label) in enumerate(secondary):
        x = grid_x + i * (col_w + gap)
        parts.append(
            metric_tile(x, tile_y, col_w, tile_h, value=value, label=label, icon_name=icon_name)
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    )
    with open(output_path, "w") as f:
        f.write(svg)
    return output_path
