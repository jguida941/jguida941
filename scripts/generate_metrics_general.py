"""Build `metrics.general.svg` from the profile snapshot model.

This is the hero banner for the profile README: a frosted-glass card whose
single title is the GitHub username, with an eyebrow caption, a generated/scope
line, two status chips, and a balanced grid of glass stat tiles.

Three of those tiles intentionally render the metric as a *single* text node with
the number and word adjacent ("67 Repositories", "78 Stargazers", "0 Releases")
so the metrics validator (scripts/metrics_svg.py) can read them back.
"""

from __future__ import annotations

from datetime import datetime, timezone

from scripts.config import BLUE, CYAN, FONT_SANS, TEXT, TEXT_BRIGHT, TEXT_DIM
from scripts.card_theme import title_left
from scripts.glass_kit import (
    accent_ribbon,
    chip,
    chip_width,
    eyebrow_text,
    glass_panel,
    glass_tile,
    icon,
)
from scripts.svg_utils import fmt_int, truncate, xml_escape


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


def _stat_tile(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    icon_name: str,
    value: str,
    caption: str,
    accent: str,
    value_size: int,
) -> str:
    """One frosted stat cell: accent icon, big bold value, dim caption."""
    pad_x = 16
    return "".join(
        [
            glass_tile(x, y, w, h),
            icon(icon_name, x + pad_x, y + 15, size=16, color=accent),
            (
                f'<text x="{x + pad_x:g}" y="{y + 60:g}" fill="{TEXT_BRIGHT}" '
                f'font-size="{value_size}" font-family="{FONT_SANS}" '
                f'font-weight="700">{value}</text>'
            ),
            (
                f'<text x="{x + pad_x:g}" y="{y + 80:g}" fill="{TEXT_DIM}" '
                f'font-size="10.5" font-family="{FONT_SANS}" '
                f'letter-spacing="0.2">{caption}</text>'
            ),
        ]
    )


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

    # --- geometry ----------------------------------------------------------
    width = 840
    height = 384
    pad = 30
    right = width - pad

    cols = 4
    col_gap = 14
    tile_w = (width - pad * 2 - col_gap * (cols - 1)) / cols
    tile_h = 92
    row_gap = 14
    row1_y = 162
    row2_y = row1_y + tile_h + row_gap  # 268 -> bottom 360, panel inner bottom 372

    def col_x(i: int) -> float:
        return pad + i * (tile_w + col_gap)

    # --- header copy -------------------------------------------------------
    name = xml_escape(truncate(str(username), 28))
    generated = xml_escape(_fmt_iso_date(generated_at))
    if isinstance(data_scope, dict) and data_scope.get("repos_included"):
        scope = xml_escape(
            f"Scope: {data_scope['repos_included']} repositories "
            f"· contributions over the last 12 months"
        )
    else:
        scope = "Scope: public, owned, non-fork repositories · last 12 months"

    parts: list[str] = []
    # 1) frosted card background (emits its own defs)
    parts.append(glass_panel(width, height))

    # 2) header: eyebrow + username title (the single bold title node) + meta
    parts.append(eyebrow_text("GITHUB PROFILE · BACKEND ENGINEERING", x=pad, y=48))
    parts.append(title_left(name, x=pad, y=88, size=33))
    parts.append(
        f'<text x="{pad}" y="111" fill="{TEXT}" font-size="11.5" '
        f'font-family="{FONT_SANS}">Generated {generated}</text>'
    )
    parts.append(
        f'<text x="{pad}" y="129" fill="{TEXT_DIM}" font-size="10.5" '
        f'font-family="{FONT_SANS}">{scope}</text>'
    )

    # 3) status chips, stacked + right-aligned with the header
    streak_text = f"{fmt_int(streak_days)}-day streak"
    ci_text = f"{fmt_int(ci_repos)} CI pipelines"
    cw_streak = chip_width(streak_text, size=11, icon=True)
    cw_ci = chip_width(ci_text, size=11, icon=True)
    parts.append(
        chip(right - cw_streak, 50, streak_text, color=CYAN, icon_name="fire", height=24)
    )
    parts.append(
        chip(right - cw_ci, 82, ci_text, color=BLUE, icon_name="ci_check", height=24)
    )

    # 4) one calm gradient divider between header and stat grid
    parts.append(accent_ribbon(width, pad=pad, y=147, h=2))

    # 5a) primary row: the big headline numbers
    primary = [
        ("fire", fmt_int(contributions), "contributions · 12 mo"),
        ("commit", fmt_int(commits), "public-scope commits"),
        ("lock", fmt_int(private_owned), "private repositories"),
        ("pr_merged", fmt_int(prs_merged), "pull requests merged"),
    ]
    for i, (icon_name, value, caption) in enumerate(primary):
        parts.append(
            _stat_tile(
                col_x(i),
                row1_y,
                tile_w,
                tile_h,
                icon_name=icon_name,
                value=value,
                caption=caption,
                accent=BLUE,
                value_size=26,
            )
        )

    # 5b) secondary row: "<N> Word" metrics (validator reads these three back)
    secondary = [
        ("code", f"{fmt_int(total_repos)} Repositories", "public · non-fork"),
        ("star", f"{fmt_int(total_stars)} Stargazers", "received across repos"),
        ("release_tag", f"{fmt_int(releases)} Releases", "tagged + published"),
        ("globe", f"{fmt_int(languages_count)} Languages", "used in public code"),
    ]
    for i, (icon_name, value, caption) in enumerate(secondary):
        parts.append(
            _stat_tile(
                col_x(i),
                row2_y,
                tile_w,
                tile_h,
                icon_name=icon_name,
                value=value,
                caption=caption,
                accent=CYAN,
                value_size=19,
            )
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(svg)
    return output_path
