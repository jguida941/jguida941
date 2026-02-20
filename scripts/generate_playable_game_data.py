"""Generate JSON data consumed by the playable Developer Quest mini-game."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.config import LEVEL_XP_BASE, LEVEL_XP_SCALE


def _calc_level(total_xp: int) -> tuple[int, int, int]:
    """Return (level, xp_into_level, xp_needed_for_next)."""
    level = 1
    xp_remaining = max(0, total_xp)

    while True:
        needed = int(LEVEL_XP_BASE * (LEVEL_XP_SCALE ** (level - 1)))
        if xp_remaining < needed:
            return level, xp_remaining, needed
        xp_remaining -= needed
        level += 1


def _class_name(lang_count: int, top_lang: str) -> str:
    if lang_count >= 8:
        return "Polyglot Architect"
    if lang_count >= 5:
        return "Full-Stack Mage"
    if top_lang == "Python":
        return "Python Sorcerer"
    if top_lang == "Java":
        return "Java Knight"
    if top_lang in ("C++", "C", "Rust"):
        return "Systems Warlock"
    return "Code Wanderer"


def _title(stars: int) -> str:
    if stars >= 100:
        return "Open Source Legend"
    if stars >= 50:
        return "Community Champion"
    if stars >= 20:
        return "Rising Maintainer"
    if stars >= 5:
        return "Apprentice Builder"
    return "New Adventurer"


def generate(
    username: str,
    total_commits: int,
    total_repos: int,
    total_stars: int,
    language_data: dict[str, int],
    prs_merged: int,
    releases: int,
    ci_pipelines: int,
    streak_days: int,
    total_contributions: int,
    featured_repos: list[dict],
    contributions: list[dict],
    data_scope: dict | None = None,
    output_path: str = "game/data.json",
) -> str:
    total_xp = total_commits + total_repos * 5 + total_stars * 10 + prs_merged * 3
    level, xp_current, xp_next = _calc_level(total_xp)

    sorted_langs = sorted(language_data.items(), key=lambda x: x[1], reverse=True)
    lang_total = sum(language_data.values())
    top_lang = sorted_langs[0][0] if sorted_langs else "Unknown"

    top_languages = []
    for lang, byte_count in sorted_langs[:8]:
        percent = (byte_count / lang_total * 100) if lang_total > 0 else 0
        top_languages.append(
            {
                "name": lang,
                "bytes": int(byte_count),
                "percent": round(percent, 1),
            }
        )

    payload = {
        "username": username,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile_url": f"https://github.com/{username}",
        "stats": {
            "total_commits": int(total_commits),
            "total_repos": int(total_repos),
            "total_stars": int(total_stars),
            "languages_count": len([item for item in language_data.values() if item > 0]),
            "prs_merged": int(prs_merged),
            "releases": int(releases),
            "ci_pipelines": int(ci_pipelines),
            "streak_days": int(streak_days),
            "total_contributions": int(total_contributions),
        },
        "derived": {
            "level": int(level),
            "class_name": _class_name(len(sorted_langs), top_lang),
            "title": _title(total_stars),
            "total_xp": int(total_xp),
            "xp_current": int(xp_current),
            "xp_next": int(xp_next),
        },
        "top_languages": top_languages,
        "featured_repos": [
            {
                "name": repo.get("name", "unknown"),
                "stars": int(repo.get("stars", 0)),
                "language": repo.get("language"),
                "weekly_commits": [int(x) for x in repo.get("weekly_commits", [])][:12],
                "has_ci": bool(repo.get("has_ci", False)),
            }
            for repo in featured_repos
        ],
        "recent_activity": [
            {
                "repo": item.get("repo", ""),
                "url": item.get("url", ""),
                "time_ago": item.get("time_ago", ""),
            }
            for item in contributions[:10]
        ],
        "data_scope": data_scope or {"repos_included": "public + owned + non-fork"},
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    return str(out)
