"""Build the Engineering Cadence analytics card (Apple/glass style).

Showcase analytics card: weekly contribution cadence sparkline, CI coverage
ring, public/private repo split, and headline automation/language stats — all
laid out inside a single frosted ``glass_panel``.
"""

from __future__ import annotations

from scripts.config import (
    CYAN,
    FONT_SANS,
    GLASS_HAIRLINE_HEX,
    GLASS_INSET,
    SVG_WIDTH,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
)
from scripts.render.card_theme import title_left
from scripts.render.glass_kit import (
    accent_ribbon,
    eyebrow_text,
    glass_panel,
    glass_tile,
    icon,
    progress_bar,
    progress_ring,
    sparkline,
)
from scripts.render.svg_utils import fmt_int


def _f(value: float) -> str:
    return f"{round(float(value), 2):g}"


def _text(
    x: float,
    y: float,
    text: str,
    *,
    size: float = 11,
    color: str = TEXT,
    weight: int = 400,
    anchor: str = "start",
    spacing: float | None = None,
) -> str:
    ls = f' letter-spacing="{_f(spacing)}"' if spacing is not None else ""
    anc = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return (
        f'<text x="{_f(x)}" y="{_f(y)}" fill="{color}" font-size="{_f(size)}" '
        f'font-family="{FONT_SANS}" font-weight="{weight}"{anc}{ls}>{text}</text>'
    )


def _pct_label(value: float) -> str:
    """Compact percent label: 49.6 -> '49.6%', 50.0 -> '50%'."""
    return f"{round(float(value), 1):g}%"


def generate(engineering: dict, output_path: str = "assets/engineering_cadence.svg") -> str:
    data = engineering or {}

    cadence = [float(v) for v in (data.get("weekly_cadence") or []) if v is not None]
    active_days = int(data.get("active_days_last_year") or 0)
    workflows = int(data.get("automation_workflows") or 0)
    automation_repos = int(data.get("automation_repos") or 0)
    primary_share = float(data.get("primary_lang_share_pct") or 0.0)
    langs_over_5 = int(data.get("languages_over_5pct") or 0)
    public_total = int(data.get("public_repos_total") or 0)
    public_nonfork = int(data.get("public_nonfork_repos") or 0)
    private_total = data.get("private_repos_total")
    private_total = int(private_total) if private_total is not None else None

    ci_pct = automation_repos / max(public_nonfork, 1) * 100.0
    repo_known = public_total + (private_total or 0)
    public_share = (public_total / repo_known * 100.0) if repo_known else 0.0

    # ---- Geometry -------------------------------------------------------- #
    inset = GLASS_INSET
    pad = 30                       # content padding from the SVG edge
    content_w = SVG_WIDTH - pad * 2
    gap = 16

    row1_y = 80
    row1_h = 124
    left_w = 478
    right_w = content_w - left_w - gap          # 286
    cad_x = pad
    ring_x = pad + left_w + gap

    row2_y = row1_y + row1_h + 12               # 216
    row2_h = 80
    tile_w = (content_w - gap * 2) / 3
    rep_x = pad
    pipe_x = pad + tile_w + gap
    lang_x = pad + (tile_w + gap) * 2

    height = row2_y + row2_h + 12 + inset        # bottom pad + shadow inset

    parts: list[str] = [glass_panel(SVG_WIDTH, height)]

    # ---- Header ---------------------------------------------------------- #
    parts.append(eyebrow_text("WORKFLOW ANALYTICS", x=pad, y=34))
    parts.append(title_left("Engineering Cadence", x=pad, y=56, size=18))
    parts.append(
        _text(
            SVG_WIDTH - pad,
            56,
            "automation-first · last 12 months",
            size=11,
            color=TEXT_DIM,
            anchor="end",
        )
    )
    parts.append(accent_ribbon(SVG_WIDTH, pad=pad, y=66, h=2.5))

    # ---- Tile 1: weekly cadence (hero stat + sparkline) ------------------ #
    parts.append(glass_tile(cad_x, row1_y, left_w, row1_h))
    ix = cad_x + 16
    parts.append(icon("trend_up", ix, row1_y + 14, size=12, color=CYAN))
    parts.append(eyebrow_text("WEEKLY CADENCE", x=ix + 17, y=row1_y + 24))
    parts.append(
        _text(
            cad_x + left_w - 16,
            row1_y + 24,
            "12 weeks",
            size=10,
            color=TEXT_DIM,
            anchor="end",
            spacing=0.4,
        )
    )
    # hero number (active days)
    parts.append(
        _text(cad_x + 16, row1_y + 78, fmt_int(active_days), size=34, color=TEXT_BRIGHT, weight=700)
    )
    parts.append(_text(cad_x + 16, row1_y + 96, "active days", size=11, color=TEXT, weight=600))
    parts.append(_text(cad_x + 16, row1_y + 110, "last 12 months", size=10, color=TEXT_DIM))
    # divider between hero and chart
    div_x = cad_x + 150
    parts.append(
        f'<rect x="{_f(div_x)}" y="{_f(row1_y + 22)}" width="1" '
        f'height="{_f(row1_h - 40)}" rx="0.5" fill="{GLASS_HAIRLINE_HEX}" fill-opacity="0.16"/>'
    )
    # sparkline
    if cadence:
        spk_x = div_x + 18
        spk_w = (cad_x + left_w - 16) - spk_x
        parts.append(sparkline(cadence, spk_x, row1_y + 40, spk_w, 56, color=CYAN, uid="eng-spark"))
        peak = max(cadence)
        parts.append(
            _text(
                cad_x + left_w - 16,
                row1_y + 112,
                f"peak {fmt_int(int(peak))} / wk",
                size=9.5,
                color=TEXT_DIM,
                anchor="end",
            )
        )

    # ---- Tile 2: CI coverage ring --------------------------------------- #
    parts.append(glass_tile(ring_x, row1_y, right_w, row1_h))
    rix = ring_x + 16
    parts.append(icon("ci_check", rix, row1_y + 13, size=13, color=CYAN))
    parts.append(eyebrow_text("CI COVERAGE", x=rix + 18, y=row1_y + 24))
    parts.append(
        progress_ring(
            ring_x + right_w / 2,
            row1_y + 64,
            36,
            ci_pct,
            color=CYAN,
            stroke=8,
            label=f"{round(ci_pct)}%",
            label_size=19,
            sublabel="CI",
        )
    )
    parts.append(
        _text(
            ring_x + right_w / 2,
            row1_y + 114,
            f"{fmt_int(automation_repos)} / {fmt_int(public_nonfork)} repos automated",
            size=10,
            color=TEXT_DIM,
            anchor="middle",
        )
    )

    # ---- Tile 3: repositories split ------------------------------------- #
    parts.append(glass_tile(rep_x, row2_y, tile_w, row2_h))
    parts.append(icon("globe", rep_x + 14, row2_y + 11, size=12, color=TEXT_DIM))
    parts.append(eyebrow_text("REPOSITORIES", x=rep_x + 31, y=row2_y + 21))
    private_str = fmt_int(private_total)  # 'n/a' when None
    half = rep_x + tile_w / 2 + 4
    parts.append(_text(rep_x + 14, row2_y + 48, fmt_int(public_total), size=20, color=CYAN, weight=700))
    parts.append(_text(rep_x + 14, row2_y + 62, "public", size=9.5, color=TEXT_DIM, spacing=0.3))
    parts.append(_text(half, row2_y + 48, private_str, size=20, color=TEXT_BRIGHT, weight=700))
    parts.append(_text(half, row2_y + 62, "private", size=9.5, color=TEXT_DIM, spacing=0.3))
    bar_w = tile_w - 28
    bar_pct = public_share if private_total is not None else 100.0
    parts.append(progress_bar(rep_x + 14, row2_y + 68, bar_w, 5, bar_pct, color=CYAN, track_op=0.18))

    # ---- Tile 4: CI pipelines ------------------------------------------- #
    parts.append(glass_tile(pipe_x, row2_y, tile_w, row2_h))
    parts.append(icon("workflow", pipe_x + 14, row2_y + 11, size=12, color=CYAN))
    parts.append(eyebrow_text("CI PIPELINES", x=pipe_x + 31, y=row2_y + 21))
    parts.append(_text(pipe_x + 14, row2_y + 51, fmt_int(workflows), size=26, color=TEXT_BRIGHT, weight=700))
    parts.append(
        _text(
            pipe_x + 14,
            row2_y + 68,
            f"workflows · {fmt_int(automation_repos)} repos",
            size=10,
            color=TEXT_DIM,
        )
    )

    # ---- Tile 5: language mix ------------------------------------------- #
    parts.append(glass_tile(lang_x, row2_y, tile_w, row2_h))
    parts.append(icon("code", lang_x + 14, row2_y + 11, size=12, color=TEXT_DIM))
    parts.append(eyebrow_text("LANGUAGE MIX", x=lang_x + 31, y=row2_y + 21))
    parts.append(_text(lang_x + 14, row2_y + 46, _pct_label(primary_share), size=22, color=TEXT_BRIGHT, weight=700))
    parts.append(
        _text(
            lang_x + 14,
            row2_y + 61,
            f"primary lang · {fmt_int(langs_over_5)} over 5%",
            size=10,
            color=TEXT_DIM,
        )
    )
    lbar_w = tile_w - 28
    parts.append(progress_bar(lang_x + 14, row2_y + 68, lbar_w, 5, primary_share, color=CYAN, track_op=0.18))

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{height}" '
        f'viewBox="0 0 {SVG_WIDTH} {height}">'
        f'{"".join(parts)}'
        f"</svg>"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path
