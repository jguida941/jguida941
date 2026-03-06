"""Generate a themed raw snapshot panel SVG from metric rows."""

from __future__ import annotations

from math import ceil

from scripts.config import (
    BG_CARD,
    BG_HIGHLIGHT,
    BLUE,
    CYAN,
    GREEN,
    ORANGE,
    RED,
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


def _status_color(status: str) -> str:
    normalized = str(status or "").strip().lower()
    if normalized in {"ok", "pass", "passing", "healthy", "complete"}:
        return GREEN
    if normalized in {"warn", "warning", "partial", "degraded"}:
        return ORANGE
    if normalized in {"error", "failed", "fail", "missing", "unknown"}:
        return RED
    return BLUE


def generate(
    snapshot_rows: list,
    data_quality: dict,
    data_scope: dict | None = None,
    output_path: str = "assets/raw_snapshot.svg",
) -> str:
    pad = 20
    cols = 2
    col_gap = 14
    row_gap = 10
    tile_h = 62
    tile_w = (SVG_WIDTH - pad * 2 - col_gap) / cols
    row_count = max(1, ceil(max(len(snapshot_rows), 1) / cols))
    content_top = 30
    body_h = row_count * tile_h + (row_count - 1) * row_gap

    ci_status = _esc(data_quality.get("ci_status", "unknown")) if isinstance(data_quality, dict) else "unknown"
    commits_status = (
        _esc(data_quality.get("commits_status", "unknown")) if isinstance(data_quality, dict) else "unknown"
    )
    events_status = _esc(data_quality.get("events_status", "unknown")) if isinstance(data_quality, dict) else "unknown"
    ci_note = _esc(data_quality.get("ci_note", "")) if isinstance(data_quality, dict) else ""
    commits_note = _esc(data_quality.get("commits_note", "")) if isinstance(data_quality, dict) else ""

    quality_notes = [note for note in (ci_note, commits_note) if note]
    quality_note = _truncate(" | ".join(quality_notes), 112)

    scope_note = ""
    if isinstance(data_scope, dict):
        private_owned = data_scope.get("private_owned_repos_total")
        private_text = str(private_owned) if private_owned is not None else "n/a"
        scope_note = (
            "Scope: public owned non-forks="
            f"{data_scope.get('public_owned_nonfork_repos_total', 'n/a')} | forks="
            f"{data_scope.get('public_owned_forks_total', 'n/a')} | private owned={private_text}"
        )
        scope_note = _truncate(_esc(scope_note), 118)

    status_y = content_top + body_h + 14
    chip_gap = 12
    chip_w = (SVG_WIDTH - pad * 2 - chip_gap * 2) / 3
    notes_y = status_y + 46
    notes: list[tuple[str, str]] = []
    if scope_note:
        notes.append((scope_note, TEXT_DIM))
    if quality_note:
        notes.append((quality_note, CYAN))
    if not notes:
        notes.append(("Data pulled from the canonical profile CLI snapshot.", TEXT_DIM))
    svg_h = notes_y + max(28, len(notes) * 14 + 10)

    parts = []
    parts.append(
        f'<text x="{pad}" y="20" fill="{TEXT_DIM}" font-size="10" '
        f'font-family="{FONT_SANS}">Python pull from GitHub API</text>'
    )

    for idx, row in enumerate(snapshot_rows or []):
        col = idx % cols
        row_idx = idx // cols
        x = pad + col * (tile_w + col_gap)
        y = content_top + row_idx * (tile_h + row_gap)

        label = _truncate(_esc(row.get("label", "Metric")), 52)
        value = _esc(row.get("display_value", "n/a"))
        value_font = "24" if len(value) <= 8 else "20" if len(value) <= 16 else "16"
        accent = BLUE if idx % 2 == 0 else CYAN

        parts.append(
            f'<rect x="{x}" y="{y}" width="{tile_w}" height="{tile_h}" rx="11" '
            f'fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
        )
        parts.append(
            f'<rect x="{x + 9}" y="{y + 10}" width="4" height="{tile_h - 20}" rx="2" fill="{accent}"/>'
        )
        parts.append(
            f'<text x="{x + 20}" y="{y + 24}" fill="{TEXT_DIM}" font-size="11" '
            f'font-family="{FONT_SANS}">{label}</text>'
        )
        parts.append(
            f'<text x="{x + 20}" y="{y + 49}" fill="{TEXT_BRIGHT}" font-size="{value_font}" '
            f'font-family="{FONT_SANS}" font-weight="700">{value}</text>'
        )

    chips = [
        ("CI", ci_status),
        ("Commits", commits_status),
        ("Events", events_status),
    ]
    for idx, (label, status) in enumerate(chips):
        x = pad + idx * (chip_w + chip_gap)
        color = _status_color(status)
        parts.append(
            f'<rect x="{x}" y="{status_y}" width="{chip_w}" height="30" rx="10" '
            f'fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
        )
        parts.append(
            f'<circle cx="{x + 14}" cy="{status_y + 15}" r="4" fill="{color}"/>'
        )
        parts.append(
            f'<text x="{x + 24}" y="{status_y + 19}" fill="{TEXT}" font-size="11" '
            f'font-family="{FONT_SANS}" font-weight="600">{_esc(label)}: {_truncate(_esc(status), 20)}</text>'
        )

    for idx, (line, color) in enumerate(notes):
        y = notes_y + idx * 14
        parts.append(
            f'<text x="{pad}" y="{y}" fill="{color}" font-size="10" font-family="{FONT_SANS}">{line}</text>'
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" '
        f'viewBox="0 0 {SVG_WIDTH} {svg_h}">'
        f'<rect width="{SVG_WIDTH}" height="{svg_h}" rx="14" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>'
        f'{"".join(parts)}'
        f"</svg>"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path
