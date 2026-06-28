"""Build `metrics.general.svg` — the hero banner for the profile README.

Power BI information architecture (DESIGN_SPEC): one dominant KPI top-left
(12-month contributions at `display` size), a supporting grid of secondary
engineering metrics, and a scope/provenance footer. The footer carries the three
totals as a single text node ("67 Repositories", "78 Stargazers", "0 Releases")
so the metrics validator (scripts/quality/metrics_svg.py) reads them back.
"""

from __future__ import annotations

from datetime import datetime, timezone

from scripts.core.config import SVG_WIDTH, SPACE, TEXT_DIM
from scripts.rendering.components import metric_tile, primary_kpi, section_header, text
from scripts.rendering.glass_kit import glass_panel
from scripts.rendering.svg_utils import fmt_int, truncate, xml_escape


def _fmt_iso_date(iso_value: str | None) -> str:
    if not iso_value:
        return "unknown"
    try:
        dt = datetime.fromisoformat(str(iso_value).replace("Z", "+00:00"))
    except ValueError:
        return xml_escape(str(iso_value))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def generate(
    *,
    username: str,
    snapshot: dict,
    data_scope: dict | None = None,
    generated_at: str | None = None,
    output_path: str = "metrics.general.svg",
) -> str:
    contributions = _int(snapshot.get("last_year_contributions"))
    commits = _int(snapshot.get("public_scope_commits"))
    total_repos = _int(snapshot.get("total_repos"))
    private_owned = _int(snapshot.get("private_owned_repos"))
    total_stars = _int(snapshot.get("total_stars"))
    languages_count = _int(snapshot.get("languages_count"))
    prs_merged = _int(snapshot.get("prs_merged"))
    releases = _int(snapshot.get("releases"))
    ci_repos = _int(snapshot.get("ci_repos"))
    streak_days = _int(snapshot.get("streak_days"))

    width = SVG_WIDTH
    height = 326
    pad = 28
    name = xml_escape(truncate(str(username), 28))
    generated = xml_escape(_fmt_iso_date(generated_at))

    parts: list[str] = [glass_panel(width, height)]

    # --- header: eyebrow + single title + "Updated <date>" + hairline ----------
    header_svg, content_top = section_header(
        pad,
        46,
        name,
        width=width,
        eyebrow="Developer Analytics · Backend",
        right_text=f"Updated {generated}",
        pad=pad,
    )
    parts.append(header_svg)

    # --- PrimaryKpiCard (the one dominant metric, top-left) ---------------------
    kpi_y = content_top + 58
    parts.append(
        primary_kpi(
            pad,
            kpi_y,
            value=fmt_int(contributions),
            label="contributions",
            sublabel="last 12 months",
        )
    )
    # vertical hairline separating the KPI from the supporting grid
    kpi_w = 244
    parts.append(
        f'<rect x="{pad + kpi_w:g}" y="{content_top + 6:g}" width="1" '
        f'height="150" fill="{TEXT_DIM}" fill-opacity="0.16"/>'
    )

    # --- supporting grid: 6 secondary engineering metrics (3 x 2) --------------
    grid_x = pad + kpi_w + SPACE["xl"]
    cols, gap = 3, SPACE["md"]
    col_w = (width - pad - grid_x - gap * (cols - 1)) / cols
    tile_h, row_gap = 66, SPACE["md"]
    secondary = [
        ("commit", fmt_int(commits), "commits"),
        ("lock", fmt_int(private_owned), "private repos"),
        ("pr_merged", fmt_int(prs_merged), "PRs merged"),
        ("globe", fmt_int(languages_count), "languages"),
        ("workflow", fmt_int(ci_repos), "CI pipelines"),
        ("fire", fmt_int(streak_days), "day streak"),
    ]
    for i, (icon_name, value, label) in enumerate(secondary):
        col, row = i % cols, i // cols
        x = grid_x + col * (col_w + gap)
        y = content_top + row * (tile_h + row_gap)
        parts.append(
            metric_tile(x, y, col_w, tile_h, value=value, label=label, icon_name=icon_name)
        )

    # --- scope / provenance footer (single text node; carries the 3 totals the
    #     metrics validator reads back: "<n> Repositories/Stargazers/Releases") --
    scope_bits = "public · owned · non-fork" if not (
        isinstance(data_scope, dict) and data_scope.get("repos_included")
    ) else xml_escape(str(data_scope["repos_included"]))
    footer = (
        f"{fmt_int(total_repos)} Repositories · {fmt_int(total_stars)} Stargazers · "
        f"{fmt_int(releases)} Releases · {scope_bits} · last 12 months"
    )
    parts.append(text(footer, pad, height - 18, token="caption", color=TEXT_DIM))

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(svg)
    return output_path
