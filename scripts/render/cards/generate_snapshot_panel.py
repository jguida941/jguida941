"""Build the raw snapshot panel SVG (Apple/glassmorphism) from metric rows."""

from __future__ import annotations

from math import ceil

from scripts.config import (
    BLUE,
    CYAN,
    GLASS_INSET,
    GREEN,
    ORANGE,
    RED,
    SVG_WIDTH,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
    FONT_SANS,
)
from scripts.render.card_theme import title_left
from scripts.render.glass_kit import (
    accent_ribbon,
    chip,
    chip_width,
    eyebrow_text,
    glass_panel,
    glass_tile,
    icon,
)
from scripts.render.svg_utils import xml_escape, truncate

TITLE = "Raw Data Snapshot (Python Pull)"

# Per-metric line icon (keyed by snapshot row "key"); restrained, one glyph/tile.
_KEY_ICON = {
    "last_year_contributions": "calendar",
    "public_scope_commits": "commit",
    "total_repos": "code",
    "public_forks": "fork",
    "private_owned_repos": "lock",
    "total_stars": "star",
    "languages_count": "globe",
    "prs_merged": "pr_merged",
    "releases": "release_tag",
    "ci_repos": "ci_check",
    "streak_days": "fire",
}

# Status chip icon per pipeline source.
_STATUS_ICON = {
    "CI": "ci_check",
    "Commits": "commit",
    "Releases": "release_tag",
    "Events": "workflow",
}

# Friendly status labels for chips.
_STATUS_DISPLAY = {
    "ok": "OK",
    "pass": "OK",
    "passing": "OK",
    "healthy": "OK",
    "complete": "OK",
    "partial": "Partial",
    "fallback": "Fallback",
    "degraded": "Degraded",
    "limited": "Limited",
    "empty": "None",
    "none": "None",
    "missing": "Missing",
    "unknown": "Unknown",
    "error": "Error",
    "failed": "Failed",
    "fail": "Failed",
}

def _status_color(status: str) -> str:
    normalized = str(status or "").strip().lower()
    if normalized in {"ok", "pass", "passing", "healthy", "complete", "available"}:
        return GREEN
    if normalized in {"warn", "warning", "partial", "degraded", "fallback", "limited"}:
        return ORANGE
    if normalized in {"error", "failed", "fail", "missing"}:
        return RED
    # empty / none / unknown -> calm dim
    return TEXT_DIM


def _status_display(status: str) -> str:
    normalized = str(status or "").strip().lower()
    return _STATUS_DISPLAY.get(normalized, (status or "n/a").strip().title())


def generate(
    snapshot_rows: list,
    data_quality: dict,
    data_scope: dict | None = None,
    output_path: str = "assets/raw_snapshot.svg",
) -> str:
    inset = GLASS_INSET
    pad = 30
    cols = 2
    col_gap = 16
    row_gap = 12
    tile_h = 66
    tile_w = (SVG_WIDTH - pad * 2 - col_gap) / cols

    rows = list(snapshot_rows or [])
    row_count = max(1, ceil(max(len(rows), 1) / cols))
    content_top = 94
    body_h = row_count * tile_h + (row_count - 1) * row_gap

    quality = data_quality if isinstance(data_quality, dict) else {}
    ci_status = str(quality.get("ci_status", "unknown"))
    commits_status = str(quality.get("commits_status", "unknown"))
    releases_status = str(quality.get("releases_status", "unknown"))
    events_status = str(quality.get("events_status", "unknown"))
    token_mode = str(quality.get("token_mode", "") or "")

    ci_note = str(quality.get("ci_note", "") or "")
    commits_note = str(quality.get("commits_note", "") or "")
    releases_note = str(quality.get("releases_note", "") or "")
    quality_notes = [n for n in (ci_note, commits_note, releases_note) if n]
    quality_note = truncate(" · ".join(quality_notes), 150)

    scope_note = ""
    if isinstance(data_scope, dict):
        private_owned = data_scope.get("private_owned_repos_total")
        private_text = str(private_owned) if private_owned is not None else "n/a"
        scope_note = (
            "Public owned non-forks "
            f"{data_scope.get('public_owned_nonfork_repos_total', 'n/a')}  ·  forks "
            f"{data_scope.get('public_owned_forks_total', 'n/a')}  ·  private owned {private_text}"
        )
        scope_note = truncate(scope_note, 130)

    # --- vertical layout (status chips + notes below the grid) ---
    chips_label_y = content_top + body_h + 30
    chips_y = chips_label_y + 12
    chip_h = 26

    notes: list[tuple[str, str]] = []
    if scope_note:
        notes.append((scope_note, TEXT))
    if quality_note:
        notes.append((quality_note, TEXT_DIM))
    if not notes:
        notes.append(("Data pulled from the canonical profile CLI snapshot.", TEXT))

    notes_top = chips_y + chip_h + 30
    note_line_h = 17
    notes_bottom = notes_top + (len(notes) - 1) * note_line_h
    svg_h = notes_bottom + 24  # baseline -> panel bottom (12) + inset margin (12)

    # --- build SVG body ---
    parts: list[str] = [glass_panel(SVG_WIDTH, svg_h)]

    # Header: eyebrow caption + single title node + accent ribbon.
    parts.append(eyebrow_text("CANONICAL CLI SNAPSHOT", x=pad, y=36))
    parts.append(title_left(TITLE, x=pad, y=58, size=17))
    parts.append(accent_ribbon(SVG_WIDTH, pad=pad, y=70))

    # NOTE: token_mode is internal diagnostic state — never surface it on the
    # public profile (it was previously rendered as a "Personal token" chip).
    _ = token_mode

    # Metric grid: 2-col glass tiles, label + big display value.
    n_rows = len(rows)
    for idx, row in enumerate(rows):
        col = idx % cols
        row_idx = idx // cols
        # An odd final tile spans the full width so there's no empty quadrant.
        is_lonely_last = idx == n_rows - 1 and col == 0 and n_rows % cols == 1
        w = (SVG_WIDTH - pad * 2) if is_lonely_last else tile_w
        x = pad + col * (tile_w + col_gap)
        y = content_top + row_idx * (tile_h + row_gap)

        key = str(row.get("key", "") or "")
        label = truncate(xml_escape(row.get("label", "Metric")), 44)
        value = xml_escape(row.get("display_value", "n/a"))
        vlen = len(str(row.get("display_value", "n/a")))
        value_font = 25 if vlen <= 7 else 20 if vlen <= 14 else 16
        ic = _KEY_ICON.get(key, "code")

        parts.append(glass_tile(x, y, w, tile_h))
        if is_lonely_last:
            # Full-width summary bar: label left (v-centered), big number right.
            parts.append(icon(ic, x + 18, y + tile_h / 2 - 7, size=14, color=CYAN))
            parts.append(
                f'<text x="{x + 40}" y="{y + tile_h / 2 + 4}" fill="{TEXT}" font-size="11.5" '
                f'font-family="{FONT_SANS}" font-weight="500">{label}</text>'
            )
            parts.append(
                f'<text x="{x + w - 22}" y="{y + tile_h / 2 + value_font * 0.34}" '
                f'fill="{TEXT_BRIGHT}" font-size="{value_font}" font-family="{FONT_SANS}" '
                f'font-weight="700" text-anchor="end">{value}</text>'
            )
            continue
        parts.append(icon(ic, x + 18, y + 14, size=14, color=CYAN))
        parts.append(
            f'<text x="{x + 40}" y="{y + 25}" fill="{TEXT}" font-size="11.5" '
            f'font-family="{FONT_SANS}" font-weight="500">{label}</text>'
        )
        parts.append(
            f'<text x="{x + 18}" y="{y + 53}" fill="{TEXT_BRIGHT}" font-size="{value_font}" '
            f'font-family="{FONT_SANS}" font-weight="700">{value}</text>'
        )

    # Pipeline status section.
    parts.append(eyebrow_text("PIPELINE STATUS", x=pad, y=chips_label_y))

    status_rows = [
        ("CI", ci_status),
        ("Commits", commits_status),
        ("Releases", releases_status),
        ("Events", events_status),
    ]
    chip_gap = 12
    cx = pad
    for label, status in status_rows:
        disp = _status_display(status)
        color = _status_color(status)
        text = f"{label}  {disp}"
        cw = chip_width(text, icon=True)
        # wrap if a chip would overflow the content width
        if cx + cw > SVG_WIDTH - pad and cx > pad:
            cx = pad  # (single row expected; guard only)
        parts.append(
            chip(
                cx,
                chips_y,
                text,
                color=color,
                icon_name=_STATUS_ICON.get(label),
                filled=True,
                height=chip_h,
            )
        )
        cx += cw + chip_gap

    # Note / scope line(s).
    for i, (line, color) in enumerate(notes):
        y = notes_top + i * note_line_h
        parts.append(
            f'<text x="{pad}" y="{y}" fill="{color}" font-size="10.5" '
            f'font-family="{FONT_SANS}" letter-spacing="0.2">{xml_escape(line)}</text>'
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" '
        f'viewBox="0 0 {SVG_WIDTH} {svg_h}">'
        f"{''.join(parts)}"
        f"</svg>"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path
