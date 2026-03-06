"""Generate `metrics.general.svg` from the canonical profile snapshot model."""

from __future__ import annotations

from datetime import datetime, timezone

from scripts.config import BG_CARD, BG_DARK, BG_HIGHLIGHT, BORDER, TEXT, TEXT_BRIGHT, TEXT_DIM, FONT_SANS


def _esc(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _fmt_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    return f"{int(value):,}"


def _fmt_iso_date(iso_value: str | None) -> str:
    if not iso_value:
        return "unknown"
    try:
        dt = datetime.fromisoformat(str(iso_value).replace("Z", "+00:00"))
    except ValueError:
        return _esc(str(iso_value))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _field(x: int, y: int, value: str, label: str) -> str:
    value_text = _esc(value)
    value_size = "14" if len(str(value)) > 24 else "18"
    return (
        f'<text x="{x}" y="{y}" fill="{TEXT_BRIGHT}" font-size="{value_size}" font-family="{FONT_SANS}" '
        f'font-weight="700">{value_text}</text>'
        f'<text x="{x}" y="{y + 18}" fill="{TEXT}" font-size="11" font-family="{FONT_SANS}">{_esc(label)}</text>'
    )


def generate(
    *,
    username: str,
    snapshot: dict,
    data_scope: dict | None = None,
    generated_at: str | None = None,
    output_path: str = "metrics.general.svg",
) -> str:
    public_nonfork = snapshot.get("total_repos")
    public_forks = snapshot.get("public_forks")
    private_owned = snapshot.get("private_owned_repos")
    total_stars = snapshot.get("total_stars")
    releases = snapshot.get("releases")
    contributions = snapshot.get("last_year_contributions")
    commits = snapshot.get("public_scope_commits")
    prs_merged = snapshot.get("prs_merged")
    streak_days = snapshot.get("streak_days")
    ci_repos = snapshot.get("ci_repos")

    scope_text = ""
    if isinstance(data_scope, dict):
        private_scope = data_scope.get("private_owned_repos_total")
        private_scope_text = "n/a" if private_scope is None else _fmt_int(int(private_scope))
        scope_text = (
            "Scope: public owned non-fork repos="
            f"{_fmt_int(int(data_scope.get('public_owned_nonfork_repos_total', 0)))}"
            f" | forks={_fmt_int(int(data_scope.get('public_owned_forks_total', 0)))}"
            f" | private owned={private_scope_text}"
        )

    width = 840
    height = 352
    pad = 22
    header_h = 54
    col_gap = 14
    col_w = int((width - pad * 2 - col_gap) / 2)
    row_gap = 10
    card_h = 74

    rows = []
    rows.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="14" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>'
    )
    rows.append(
        f'<rect x="0" y="0" width="{width}" height="{header_h}" rx="14" fill="{BG_DARK}"/>'
    )
    rows.append(
        f'<text x="{pad}" y="33" fill="{TEXT_BRIGHT}" font-size="20" font-family="{FONT_SANS}" font-weight="700">{_esc(username)}</text>'
    )
    rows.append(
        f'<text x="{width - pad}" y="33" fill="{TEXT_DIM}" font-size="11" font-family="{FONT_SANS}" text-anchor="end">'
        f"Canonical CLI Metrics</text>"
    )
    rows.append(
        f'<text x="{pad}" y="{header_h + 18}" fill="{TEXT_DIM}" font-size="10" font-family="{FONT_SANS}">'
        f"Generated: {_esc(_fmt_iso_date(generated_at))}</text>"
    )
    if scope_text:
        rows.append(
            f'<text x="{pad}" y="{header_h + 34}" fill="{TEXT_DIM}" font-size="10" font-family="{FONT_SANS}">{_esc(scope_text)}</text>'
        )

    start_y = header_h + 48
    left_x = pad
    right_x = pad + col_w + col_gap

    # Row 1
    rows.append(
        f'<rect x="{left_x}" y="{start_y}" width="{col_w}" height="{card_h}" rx="11" fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
    )
    rows.append(_field(left_x + 14, start_y + 30, _fmt_int(contributions), "12mo Contributions"))
    rows.append(
        f'<rect x="{right_x}" y="{start_y}" width="{col_w}" height="{card_h}" rx="11" fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
    )
    rows.append(_field(right_x + 14, start_y + 30, _fmt_int(commits), "Public Scope Commits"))

    # Row 2
    y2 = start_y + card_h + row_gap
    rows.append(
        f'<rect x="{left_x}" y="{y2}" width="{col_w}" height="{card_h}" rx="11" fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
    )
    rows.append(
        _field(
            left_x + 14,
            y2 + 30,
            f"{_fmt_int(int(public_nonfork or 0))} Repositories",
            "Public Non-Fork Repos",
        )
    )
    rows.append(
        f'<rect x="{right_x}" y="{y2}" width="{col_w}" height="{card_h}" rx="11" fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
    )
    rows.append(
        _field(
            right_x + 14,
            y2 + 30,
            f"{_fmt_int(int(total_stars or 0))} Stargazers",
            "Total Stars",
        )
    )

    # Row 3
    y3 = y2 + card_h + row_gap
    rows.append(
        f'<rect x="{left_x}" y="{y3}" width="{col_w}" height="{card_h}" rx="11" fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
    )
    rows.append(
        _field(
            left_x + 14,
            y3 + 30,
            f"{_fmt_int(int(public_forks or 0))} public forks | {_fmt_int(private_owned)} private",
            "Repository Scope",
        )
    )
    rows.append(
        f'<rect x="{right_x}" y="{y3}" width="{col_w}" height="{card_h}" rx="11" fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
    )
    rows.append(
        _field(
            right_x + 14,
            y3 + 30,
            (
                f"{_fmt_int(int(releases or 0))} Releases | {_fmt_int(int(prs_merged or 0))} PRs | "
                f"CI {_fmt_int(int(ci_repos or 0))} | Streak {_fmt_int(int(streak_days or 0))}"
            ),
            "Recent Delivery",
        )
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{"".join(rows)}</svg>'
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(svg)
    return output_path
