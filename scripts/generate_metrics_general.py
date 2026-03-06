"""Build `metrics.general.svg` from the profile snapshot model."""

from __future__ import annotations

from datetime import datetime, timezone

from scripts.config import BG_HIGHLIGHT, BORDER, TEXT, TEXT_BRIGHT, FONT_SANS
from scripts.card_theme import card_bg, meta_text, title_accent, title_left, title_right
from scripts.svg_utils import xml_escape, fmt_int


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


def _field(x: int, y: int, value: str, label: str) -> str:
    value_text = xml_escape(value)
    value_size = "14" if len(str(value)) > 24 else "18"
    return (
        f'<text x="{x}" y="{y}" fill="{TEXT_BRIGHT}" font-size="{value_size}" font-family="{FONT_SANS}" '
        f'font-weight="700">{value_text}</text>'
        f'<text x="{x}" y="{y + 18}" fill="{TEXT}" font-size="11" font-family="{FONT_SANS}">{xml_escape(label)}</text>'
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

    releases_text = fmt_int(int(releases)) if releases is not None else "n/a"
    prs_text = fmt_int(int(prs_merged)) if prs_merged is not None else "n/a"
    ci_text = fmt_int(int(ci_repos)) if ci_repos is not None else "n/a"
    streak_text = fmt_int(int(streak_days)) if streak_days is not None else "n/a"

    scope_text = ""
    if isinstance(data_scope, dict):
        private_scope = data_scope.get("private_owned_repos_total")
        private_scope_text = "n/a" if private_scope is None else fmt_int(int(private_scope))
        scope_text = (
            "Scope: public owned non-fork repos="
            f"{fmt_int(int(data_scope.get('public_owned_nonfork_repos_total', 0)))}"
            f" | forks={fmt_int(int(data_scope.get('public_owned_forks_total', 0)))}"
            f" | private owned={private_scope_text}"
        )

    width = 840
    height = 352
    pad = 22
    header_h = 34
    col_gap = 14
    col_w = int((width - pad * 2 - col_gap) / 2)
    row_gap = 10
    card_h = 74

    rows = []
    rows.append(card_bg(width, height))
    rows.append(title_left(xml_escape(username), x=pad, y=30))
    rows.append(title_right("Canonical CLI Metrics", width=width, pad=pad, y=30))
    rows.append(title_accent(width=width, pad=pad, y=35))
    rows.append(meta_text(f"Generated: {xml_escape(_fmt_iso_date(generated_at))}", x=pad, y=50))
    if scope_text:
        rows.append(meta_text(xml_escape(scope_text), x=pad, y=64))

    start_y = 76 if scope_text else 64
    left_x = pad
    right_x = pad + col_w + col_gap

    # Row 1
    rows.append(
        f'<rect x="{left_x}" y="{start_y}" width="{col_w}" height="{card_h}" rx="11" fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
    )
    rows.append(_field(left_x + 14, start_y + 30, fmt_int(contributions), "12mo Contributions"))
    rows.append(
        f'<rect x="{right_x}" y="{start_y}" width="{col_w}" height="{card_h}" rx="11" fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
    )
    rows.append(_field(right_x + 14, start_y + 30, fmt_int(commits), "Public Scope Commits"))

    # Row 2
    y2 = start_y + card_h + row_gap
    rows.append(
        f'<rect x="{left_x}" y="{y2}" width="{col_w}" height="{card_h}" rx="11" fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
    )
    rows.append(
        _field(
            left_x + 14,
            y2 + 30,
            f"{fmt_int(int(public_nonfork or 0))} Repositories",
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
            f"{fmt_int(int(total_stars or 0))} Stargazers",
            "Repo Stargazers (Received)",
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
            f"{fmt_int(int(public_forks or 0))} public forks | {fmt_int(private_owned)} private",
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
                f"{releases_text} Releases | {prs_text} PRs | "
                f"CI {ci_text} | Streak {streak_text}"
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
