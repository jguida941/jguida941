"""Render SVG assets, dashboard JSON, and README from computed model data."""

from __future__ import annotations

import json
from pathlib import Path

import jinja2

from scripts.collect_data import CollectedProfileData
from scripts.generate_activity_heatmap import generate as gen_heatmap
from scripts.generate_badges import generate as gen_badges
from scripts.generate_builder_scorecard import generate as gen_scorecard
from scripts.generate_contribution_panel import generate as gen_contribution_panel
from scripts.generate_currently_working import generate as gen_working
from scripts.generate_focus_board import generate as gen_focus_board
from scripts.generate_language_chart import generate as gen_lang_chart
from scripts.generate_metrics_general import generate as gen_metrics_general
from scripts.generate_repo_spotlight import generate as gen_spotlight
from scripts.generate_snapshot_panel import generate as gen_snapshot_panel
from scripts.generate_streak_summary import generate as gen_streak_summary


def ensure_output_dirs() -> None:
    Path("assets").mkdir(exist_ok=True)
    Path("site/data").mkdir(parents=True, exist_ok=True)


def generate_assets(collected: CollectedProfileData, model: dict, logger=print) -> None:
    logger("\n[8/8] Generating SVGs...")

    gen_badges(
        public_nonfork_repos=collected.repo_counts["public_owned_nonfork"],
        public_forks=collected.repo_counts["public_owned_forks"],
        private_owned_repos=collected.repo_counts["private_owned"],
        ci_count=model["snapshot"]["ci_repos"],
        last_year_contributions=collected.total_contributions,
    )
    logger("  -> assets/badges.svg")

    gen_lang_chart(collected.language_bytes)
    logger("  -> assets/lang_breakdown.svg")

    gen_working(model["recent_repos"])
    logger("  -> assets/currently_working.svg")

    gen_heatmap(collected.events)
    logger("  -> assets/activity_heatmap.svg")

    gen_contribution_panel(collected.calendar)
    logger("  -> assets/contribution_calendar.svg")

    gen_spotlight(model["spotlight_data"])
    logger("  -> assets/repo_spotlight.svg")

    gen_scorecard(model["scorecard"], tiles=model["scorecard_cards"])
    logger("  -> assets/builder_scorecard.svg")

    gen_focus_board(model["focus"])
    logger("  -> assets/now_next_shipped.svg")

    gen_streak_summary(
        calendar=collected.calendar,
        current_streak_days=model["snapshot"]["streak_days"],
        total_contributions=collected.total_contributions,
    )
    logger("  -> assets/streak_summary.svg")

    gen_snapshot_panel(
        model["snapshot_rows"],
        model["data_quality"],
        data_scope=model["data_scope"],
    )
    logger("  -> assets/raw_snapshot.svg")

    gen_metrics_general(
        username=model["dashboard_data"]["username"],
        snapshot=model["snapshot"],
        data_scope=model["data_scope"],
        generated_at=model["dashboard_data"]["generated_at"],
        output_path="metrics.general.svg",
    )
    logger("  -> metrics.general.svg")


def write_dashboard_json(model: dict, logger=print) -> None:
    output_path = Path("site/data/profile_snapshot.json")
    output_path.write_text(
        json.dumps(model["dashboard_data"], indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    logger("  -> site/data/profile_snapshot.json")


def render_readme(model: dict, logger=print) -> None:
    logger("\nRendering README.md...")

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("templates"),
        keep_trailing_newline=True,
    )
    template = env.get_template("README.md.tpl")

    cache_bust = str(model["dashboard_data"].get("generated_at", "")).replace("-", "").replace(":", "").replace("T", "").replace("Z", "")
    if not cache_bust:
        cache_bust = "latest"

    def _dedupe_links(items: list[dict], limit: int = 3) -> list[dict]:
        unique = []
        seen = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url", "")).strip()
            title = str(item.get("title", "")).strip()
            detail = str(item.get("detail", "")).strip()
            key = url or f"{title}|{detail}"
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(item)
            if len(unique) >= limit:
                break
        return unique

    featured_links = [row for row in model["repo_overview_rows"] if row.get("featured")][:6]

    readme = template.render(
        username=model["dashboard_data"]["username"],
        dashboard_url=model["dashboard_data"]["dashboard_url"],
        cache_bust=cache_bust,
        recent_created=model["recent_created"],
        focus_now=model["focus"]["now"],
        focus_next=model["focus"]["next"],
        focus_shipped=model["focus"]["shipped"],
        focus_links_now=_dedupe_links(model["focus"]["now"], 3),
        focus_links_next=_dedupe_links(model["focus"]["next"], 3),
        focus_links_shipped=_dedupe_links(model["focus"]["shipped"], 3),
        featured_links=featured_links,
        recent_releases=model["recent_releases"],
        recent_pull_requests=model["recent_pull_requests"],
        snapshot=model["snapshot"],
        snapshot_rows=model["snapshot_rows"],
        data_quality=model["data_quality"],
        scorecard=model["scorecard"],
        scorecard_cards=model["scorecard_cards"],
        data_scope=model["data_scope"],
        top_languages=model["top_languages"],
        repo_overview_rows=model["repo_overview_rows"],
        activity_feed=model["activity_feed"],
    )

    Path("README.md").write_text(readme, encoding="utf-8")
    logger("-> README.md written")
