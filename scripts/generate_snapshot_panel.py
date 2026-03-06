"""Generate a themed raw snapshot panel SVG from metric rows."""

from __future__ import annotations

from math import ceil

from scripts.config import (
    BG_CARD,
    BG_DARK,
    BG_HIGHLIGHT,
    CYAN,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
    BORDER,
    SVG_WIDTH,
    FONT_SANS,
)


def _esc(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _truncate(value: str, max_len: int) -> str:
    text = (value or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def generate(
    snapshot_rows: list,
    data_quality: dict,
    data_scope: dict | None = None,
    output_path: str = "assets/raw_snapshot.svg",
) -> str:
    pad = 20
    gap = 12
    header_h = 44
    cols = 2
    tile_h = 46
    tile_w = (SVG_WIDTH - pad * 2 - gap) / cols
    rows = max(1, ceil(max(len(snapshot_rows), 1) / cols))
    body_h = rows * tile_h + (rows - 1) * 8
    footer_h = 68
    svg_h = header_h + body_h + footer_h + pad

    parts = []
    parts.append(
        f'<rect x="0" y="0" width="{SVG_WIDTH}" height="{header_h}" rx="14" fill="{BG_DARK}"/>'
    )
    parts.append(
        f'<text x="{pad}" y="29" fill="{TEXT_BRIGHT}" font-size="16" '
        f'font-family="{FONT_SANS}" font-weight="700">Raw Data Snapshot</text>'
    )
    parts.append(
        f'<text x="{SVG_WIDTH - pad}" y="29" fill="{TEXT_DIM}" font-size="11" '
        f'font-family="{FONT_SANS}" text-anchor="end">Python pull from GitHub API</text>'
    )

    for idx, row in enumerate(snapshot_rows or []):
        col = idx % cols
        r = idx // cols
        x = pad + col * (tile_w + gap)
        y = header_h + r * (tile_h + 8)

        label = _truncate(_esc(row.get("label", "Metric")), 42)
        value = _esc(row.get("display_value", "n/a"))

        parts.append(
            f'<rect x="{x}" y="{y}" width="{tile_w}" height="{tile_h}" rx="10" '
            f'fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x + 12}" y="{y + 19}" fill="{TEXT_DIM}" font-size="10" '
            f'font-family="{FONT_SANS}">{label}</text>'
        )
        parts.append(
            f'<text x="{x + 12}" y="{y + 36}" fill="{TEXT_BRIGHT}" font-size="14" '
            f'font-family="{FONT_SANS}" font-weight="700">{value}</text>'
        )

    ci_status = _esc(data_quality.get("ci_status", "unknown")) if isinstance(data_quality, dict) else "unknown"
    commits_status = (
        _esc(data_quality.get("commits_status", "unknown")) if isinstance(data_quality, dict) else "unknown"
    )
    events_status = _esc(data_quality.get("events_status", "unknown")) if isinstance(data_quality, dict) else "unknown"
    ci_note = _esc(data_quality.get("ci_note", "")) if isinstance(data_quality, dict) else ""
    commits_note = _esc(data_quality.get("commits_note", "")) if isinstance(data_quality, dict) else ""
    quality_notes = [note for note in (ci_note, commits_note) if note]
    quality_note = _truncate(" | ".join(quality_notes), 90)
    scope_note = ""
    if isinstance(data_scope, dict):
        private_owned = data_scope.get("private_owned_repos_total")
        private_text = str(private_owned) if private_owned is not None else "n/a"
        scope_note = (
            "Scope: public owned non-forks="
            f"{data_scope.get('public_owned_nonfork_repos_total', 'n/a')} | forks="
            f"{data_scope.get('public_owned_forks_total', 'n/a')} | private owned={private_text}"
        )
        scope_note = _truncate(_esc(scope_note), 100)

    footer_y = header_h + body_h + 18
    parts.append(
        f'<text x="{pad}" y="{footer_y}" fill="{TEXT}" font-size="11" font-family="{FONT_SANS}">'
        f'Data quality · CI: {ci_status} · Commits: {commits_status} · Events: {events_status}</text>'
    )
    if scope_note:
        parts.append(
            f'<text x="{pad}" y="{footer_y + 16}" fill="{TEXT_DIM}" font-size="10" '
            f'font-family="{FONT_SANS}">{scope_note}</text>'
        )
    if quality_note:
        ci_note_y = footer_y + (32 if scope_note else 16)
        parts.append(
            f'<text x="{pad}" y="{ci_note_y}" fill="{CYAN}" font-size="10" '
            f'font-family="{FONT_SANS}">{quality_note}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" viewBox="0 0 {SVG_WIDTH} {svg_h}">
  <rect width="{SVG_WIDTH}" height="{svg_h}" rx="14" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>
  {''.join(parts)}
</svg>'''

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path
