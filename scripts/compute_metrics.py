"""Compute profile metrics and dashboard model from collected data."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from scripts import github_client as gh
from scripts.collect_data import CollectedProfileData
from scripts.config import (
    USERNAME,
    FEATURED_REPOS,
    BG_DARK,
    BG_CARD,
    BG_HIGHLIGHT,
    BLUE,
    CYAN,
    GREEN,
    ORANGE,
    RED,
    YELLOW,
    TEXT,
    TEXT_DIM,
    TEXT_BRIGHT,
    BORDER,
)
from scripts.profile_contract import SCORECARD_METRICS, SNAPSHOT_METRICS, format_metric_value
from scripts.profile_helpers import activity_label, ci_text, has_ci_workflow, time_ago


def _parse_calendar_day_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _compute_current_streak_days(calendar: dict | None, now_utc: datetime) -> int:
    if not isinstance(calendar, dict):
        return 0

    all_days: list[dict] = []
    for week in calendar.get("weeks", []):
        days = week.get("contributionDays", []) if isinstance(week, dict) else []
        if not isinstance(days, list):
            continue
        for day in days:
            if isinstance(day, dict):
                all_days.append(day)

    if not all_days:
        return 0

    today_utc = now_utc.date()
    streak = 0
    for day in reversed(all_days):
        day_dt = _parse_calendar_day_date(str(day.get("date", "")))
        if day_dt is not None and day_dt.date() > today_utc:
            continue
        try:
            count = int(day.get("contributionCount", 0))
        except (TypeError, ValueError):
            count = 0
        if count > 0:
            streak += 1
            continue
        break

    return streak


def _build_recent_repos(
    repos: list[dict],
    seven_days_ago: datetime,
    latest_push_message_by_repo: dict[str, str],
    allow_network_calls: bool,
) -> tuple[list[dict], dict[str, str]]:
    recent_repos = []
    recent_commit_message_by_repo: dict[str, str] = {}
    seen = set()
    for repo in sorted(repos, key=lambda item: item.get("pushed_at", ""), reverse=True):
        pushed = repo.get("pushed_at", "")
        if not pushed:
            continue
        pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        if pushed_dt < seven_days_ago:
            break
        if repo["name"] in seen:
            continue
        seen.add(repo["name"])

        last_msg = (repo.get("latest_commit_message") or "").split("\n")[0].strip()
        if not last_msg and allow_network_calls:
            try:
                commits_data = gh.paginated_get(
                    f"repos/{repo['owner']['login']}/{repo['name']}/commits",
                    {"per_page": 1},
                    per_page=1,
                )
                if commits_data:
                    last_msg = commits_data[0].get("commit", {}).get("message", "").split("\n")[0].strip()
            except Exception:
                pass
        if not last_msg:
            full_name = f"{repo['owner']['login']}/{repo['name']}"
            last_msg = latest_push_message_by_repo.get(full_name, "")
        if not last_msg:
            last_msg = "recent push detected"

        recent_commit_message_by_repo[repo["name"]] = last_msg
        recent_repos.append(
            {
                "name": repo["name"],
                "html_url": repo.get("html_url", ""),
                "language": repo.get("language"),
                "pushed_at": pushed,
                "last_commit_msg": last_msg,
            }
        )
    return recent_repos, recent_commit_message_by_repo


def _build_ci_quality(
    repos: list[dict],
    *,
    allow_network_calls: bool,
) -> tuple[dict[str, bool | None], dict[str, Any]]:
    repo_ci_lookup: dict[str, bool | None] = {}
    for repo in repos:
        name = repo.get("name", "")
        if not name:
            continue
        repo_ci_lookup[name] = has_ci_workflow(repo, allow_network_calls=allow_network_calls)

    ci_total_repos = len(repo_ci_lookup)
    ci_unknown_count = sum(1 for state in repo_ci_lookup.values() if state is None)
    ci_true_count = sum(1 for state in repo_ci_lookup.values() if state is True)
    ci_known_count = ci_total_repos - ci_unknown_count

    if ci_total_repos == 0:
        ci_status = "empty"
        ci_note = "No repositories in scope."
        ci_count_effective = 0
        ci_coverage_pct = 0.0
    elif ci_unknown_count == 0:
        ci_status = "ok"
        ci_note = "CI workflow detection complete."
        ci_count_effective = ci_true_count
        ci_coverage_pct = (ci_true_count / ci_total_repos * 100) if ci_total_repos else 0.0
    elif ci_known_count == 0:
        ci_status = "unavailable"
        ci_note = "CI workflow detection unavailable for this run; shown as n/a."
        ci_count_effective = None
        ci_coverage_pct = None
    else:
        ci_status = "partial"
        ci_note = (
            "CI workflow detection partial for this run; unknown repos shown as n/a "
            f"({ci_unknown_count}/{ci_total_repos})."
        )
        ci_count_effective = None
        ci_coverage_pct = None

    return repo_ci_lookup, {
        "ci_status": ci_status,
        "ci_note": ci_note,
        "ci_count_effective": ci_count_effective,
        "ci_coverage_pct": ci_coverage_pct,
    }


def _build_repo_overview_rows(
    repos: list[dict],
    recent_commit_message_by_repo: dict[str, str],
    latest_push_message_by_repo: dict[str, str],
    repo_ci_lookup: dict[str, bool | None],
) -> tuple[list[dict], list[dict]]:
    sorted_repos_by_push = sorted(repos, key=lambda item: item.get("pushed_at", ""), reverse=True)
    repo_by_name = {repo.get("name", ""): repo for repo in repos if repo.get("name")}
    featured_set = set(FEATURED_REPOS)

    def build_repo_row(repo: dict) -> dict:
        owner_login = repo.get("owner", {}).get("login", USERNAME)
        name = repo.get("name", "")
        full_name = f"{owner_login}/{name}" if name else ""
        pushed_raw = repo.get("pushed_at", "") or ""
        pushed_date = pushed_raw[:10] if pushed_raw else ""
        commit_msg = (repo.get("latest_commit_message") or "").split("\n")[0].strip()
        if not commit_msg and name:
            commit_msg = recent_commit_message_by_repo.get(name, "")
        if not commit_msg and full_name:
            commit_msg = latest_push_message_by_repo.get(full_name, "")
        if not commit_msg:
            commit_msg = "recent push detected"

        ci_state = repo_ci_lookup.get(name)
        return {
            "name": name,
            "full_name": full_name,
            "url": repo.get("html_url", ""),
            "language": repo.get("language") or "n/a",
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "ci": ci_text(ci_state),
            "pushed_at": pushed_date,
            "pushed_at_raw": pushed_raw,
            "pushed_ago": time_ago(pushed_raw) if pushed_raw else "unknown",
            "created_at": (repo.get("created_at") or "")[:10],
            "last_commit_msg": commit_msg,
            "featured": name in featured_set,
        }

    ordered_repo_names = []
    for featured_name in FEATURED_REPOS:
        if featured_name in repo_by_name and featured_name not in ordered_repo_names:
            ordered_repo_names.append(featured_name)
    for repo in sorted_repos_by_push:
        repo_name = repo.get("name", "")
        if repo_name and repo_name not in ordered_repo_names:
            ordered_repo_names.append(repo_name)
        if len(ordered_repo_names) >= 18:
            break

    repo_overview_rows = [
        build_repo_row(repo_by_name[name]) for name in ordered_repo_names if name in repo_by_name
    ]
    featured_repo_facts = [row for row in repo_overview_rows if row.get("featured")]
    return repo_overview_rows, featured_repo_facts


def _build_recent_activity(
    events: list[dict],
    recent_repos: list[dict],
    repo_overview_rows: list[dict],
    username: str,
) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict], list[dict]]:
    contribution_event_types = {
        "PushEvent",
        "PullRequestEvent",
        "PullRequestReviewEvent",
        "ReleaseEvent",
        "IssuesEvent",
        "IssueCommentEvent",
        "CreateEvent",
        "DeleteEvent",
    }
    owned_repo_prefix = f"{username}/"

    contributions = []
    seen_contrib = set()
    for event in events:
        if event.get("type") not in contribution_event_types:
            continue
        repo_name = event.get("repo", {}).get("name", "")
        if not repo_name.startswith(owned_repo_prefix):
            continue
        if repo_name in seen_contrib:
            continue
        seen_contrib.add(repo_name)
        contributions.append(
            {
                "repo": repo_name,
                "url": f"https://github.com/{repo_name}",
                "activity": activity_label(event.get("type", "")),
                "time_ago": time_ago(event.get("created_at", "")),
                "created_at": event.get("created_at", ""),
            }
        )
        if len(contributions) >= 10:
            break

    if not contributions:
        for repo in recent_repos[:10]:
            full_name = f"{username}/{repo['name']}"
            contributions.append(
                {
                    "repo": full_name,
                    "url": repo.get("html_url", f"https://github.com/{full_name}"),
                    "activity": "push",
                    "time_ago": time_ago(repo.get("pushed_at", "")),
                    "created_at": repo.get("pushed_at", ""),
                }
            )

    release_list = []
    for event in events:
        if event.get("type") != "ReleaseEvent":
            continue
        payload = event.get("payload", {})
        release = payload.get("release", {})
        repo_name = event.get("repo", {}).get("name", "")
        release_tag = (release.get("tag_name") or "").strip() or "unknown"
        release_url = (release.get("html_url") or "").strip()
        if not release_url and repo_name and release_tag != "unknown":
            release_url = f"https://github.com/{repo_name}/releases/tag/{release_tag}"
        release_list.append(
            {
                "repo": repo_name,
                "repo_url": f"https://github.com/{repo_name}",
                "tag": release_tag,
                "url": release_url,
                "time_ago": time_ago(event.get("created_at", "")),
                "created_at": event.get("created_at", ""),
            }
        )
        if len(release_list) >= 5:
            break

    pr_list = []
    for event in events:
        if event.get("type") != "PullRequestEvent":
            continue
        pr = event.get("payload", {}).get("pull_request", {})
        repo_name = event.get("repo", {}).get("name", "")
        state = pr.get("state", "open").upper()
        if pr.get("merged"):
            state = "MERGED"
        pr_number = pr.get("number")
        pr_title = (pr.get("title") or "").strip()
        if not pr_title:
            pr_title = f"PR #{pr_number}" if pr_number else "pull request"
        pr_url = (pr.get("html_url") or "").strip()
        if not pr_url and repo_name and pr_number:
            pr_url = f"https://github.com/{repo_name}/pull/{pr_number}"
        if not pr_url and repo_name:
            pr_url = f"https://github.com/{repo_name}/pulls"
        pr_list.append(
            {
                "title": pr_title,
                "url": pr_url,
                "repo": repo_name,
                "repo_url": f"https://github.com/{repo_name}",
                "state": state,
                "time_ago": time_ago(event.get("created_at", "")),
                "created_at": event.get("created_at", ""),
            }
        )
        if len(pr_list) >= 5:
            break

    repo_row_by_full_name = {
        row["full_name"]: row for row in repo_overview_rows if row.get("full_name")
    }

    focus_now = []
    for entry in contributions[:3]:
        repo_short = entry["repo"].split("/")[-1] if entry.get("repo") else "repo"
        repo_ctx = repo_row_by_full_name.get(entry.get("repo", ""))
        detail_bits = [entry["activity"], entry["time_ago"]]
        if repo_ctx:
            detail_bits.append(f"★{repo_ctx['stars']}")
            if repo_ctx.get("language") and repo_ctx["language"] != "n/a":
                detail_bits.append(repo_ctx["language"])
        focus_now.append(
            {
                "title": repo_short,
                "detail": " · ".join(detail_bits),
                "url": entry["url"],
            }
        )
    if not focus_now:
        for row in repo_overview_rows[:3]:
            focus_now.append(
                {
                    "title": row["name"],
                    "detail": f"{row['language']} · {row['pushed_ago']} · ★{row['stars']}",
                    "url": row["url"],
                }
            )

    focus_next = []
    open_prs = [pr for pr in pr_list if pr.get("state") == "OPEN"]
    for pr in open_prs[:3]:
        repo_short = pr["repo"].split("/")[-1] if pr.get("repo") else "repo"
        focus_next.append(
            {
                "title": pr["title"],
                "detail": f"{repo_short} · open · {pr['time_ago']}",
                "url": pr["url"],
            }
        )
    if not focus_next:
        candidate_rows = [row for row in repo_overview_rows if row.get("ci") != "yes"] or repo_overview_rows
        for row in candidate_rows[:3]:
            ci_detail = row["ci"] if row["ci"] in {"yes", "no"} else "unavailable"
            focus_next.append(
                {
                    "title": f"Next pass: {row['name']}",
                    "detail": f"CI {ci_detail} · ★{row['stars']} · pushed {row['pushed_at'] or 'n/a'}",
                    "url": row["url"],
                }
            )

    focus_shipped = []
    for rel in release_list[:3]:
        repo_short = rel["repo"].split("/")[-1] if rel.get("repo") else "repo"
        focus_shipped.append(
            {
                "title": rel["tag"],
                "detail": f"{repo_short} · {rel['time_ago']}",
                "url": rel["url"] or rel["repo_url"],
            }
        )
    if not focus_shipped:
        merged_prs = [pr for pr in pr_list if pr.get("state") == "MERGED"]
        for pr in merged_prs[:3]:
            repo_short = pr["repo"].split("/")[-1] if pr.get("repo") else "repo"
            focus_shipped.append(
                {
                    "title": pr["title"],
                    "detail": f"{repo_short} · merged · {pr['time_ago']}",
                    "url": pr["url"],
                }
            )
    if not focus_shipped:
        for repo in recent_repos[:3]:
            msg = repo.get("last_commit_msg", "")
            if len(msg) > 58:
                msg = msg[:55] + "..."
            focus_shipped.append(
                {
                    "title": msg or repo["name"],
                    "detail": f"{repo['name']} · pushed {time_ago(repo.get('pushed_at', ''))}",
                    "url": repo.get("html_url", f"https://github.com/{username}/{repo['name']}"),
                }
            )

    return (
        contributions,
        release_list,
        pr_list,
        focus_now,
        focus_next,
        focus_shipped,
        repo_row_by_full_name,
    )


def _build_activity_feed(
    release_list: list[dict],
    pr_list: list[dict],
    contributions: list[dict],
    recent_created: list[dict],
    recent_repos: list[dict],
    username: str,
) -> list[dict]:
    activity_feed = []
    for rel in release_list:
        activity_feed.append(
            {
                "kind": "release",
                "title": rel["tag"],
                "url": rel["url"] or rel["repo_url"],
                "repo": rel["repo"],
                "repo_url": rel["repo_url"],
                "state": "RELEASED",
                "time_ago": rel["time_ago"],
                "created_at": rel["created_at"],
            }
        )
    for pr in pr_list:
        activity_feed.append(
            {
                "kind": "pull request",
                "title": pr["title"],
                "url": pr["url"],
                "repo": pr["repo"],
                "repo_url": pr["repo_url"],
                "state": pr["state"],
                "time_ago": pr["time_ago"],
                "created_at": pr["created_at"],
            }
        )
    for contrib in contributions:
        activity_feed.append(
            {
                "kind": "activity",
                "title": contrib["activity"],
                "url": contrib["url"],
                "repo": contrib["repo"],
                "repo_url": contrib["url"],
                "state": contrib["activity"].upper(),
                "time_ago": contrib["time_ago"],
                "created_at": contrib["created_at"],
            }
        )
    for repo in recent_created[:3]:
        repo_name = f"{username}/{repo.get('name', '')}"
        activity_feed.append(
            {
                "kind": "created",
                "title": repo.get("name", "repository"),
                "url": repo.get("html_url", ""),
                "repo": repo_name,
                "repo_url": repo.get("html_url", ""),
                "state": "CREATED",
                "time_ago": time_ago(repo.get("created_at", "")),
                "created_at": repo.get("created_at", ""),
            }
        )
    if not activity_feed:
        for repo in recent_repos[:10]:
            repo_name = f"{username}/{repo.get('name', '')}"
            activity_feed.append(
                {
                    "kind": "activity",
                    "title": repo.get("last_commit_msg", "push"),
                    "url": repo.get("html_url", ""),
                    "repo": repo_name,
                    "repo_url": repo.get("html_url", ""),
                    "state": "PUSH",
                    "time_ago": time_ago(repo.get("pushed_at", "")),
                    "created_at": repo.get("pushed_at", ""),
                }
            )

    activity_feed = sorted(activity_feed, key=lambda item: item.get("created_at", ""), reverse=True)
    deduped_feed = []
    seen_feed = set()
    for item in activity_feed:
        signature = (
            item.get("kind", ""),
            item.get("title", ""),
            item.get("repo", ""),
            item.get("created_at", ""),
        )
        if signature in seen_feed:
            continue
        seen_feed.add(signature)
        deduped_feed.append(item)
    return deduped_feed[:18]


def compute_profile_model(
    collected: CollectedProfileData,
    logger=print,
    *,
    allow_network_calls: bool = True,
) -> dict[str, Any]:
    repos = collected.repos
    events = collected.events
    language_bytes = collected.language_bytes
    calendar = collected.calendar
    repo_counts = collected.repo_counts

    now_utc = datetime.now(timezone.utc)
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    total_language_bytes = sum(bytes_ for bytes_ in language_bytes.values() if bytes_ > 0)
    lang_count = len([lang for lang, bytes_ in language_bytes.items() if bytes_ > 0])

    top_languages = []
    for lang, byte_count in sorted(language_bytes.items(), key=lambda item: item[1], reverse=True)[:12]:
        if byte_count <= 0:
            continue
        pct = (byte_count / total_language_bytes * 100) if total_language_bytes else 0
        top_languages.append(
            {
                "name": lang,
                "bytes": byte_count,
                "percent": round(pct, 2),
            }
        )

    prs_merged_from_events = sum(
        1
        for event in events
        if event.get("type") == "PullRequestEvent"
        and event.get("payload", {}).get("action") == "closed"
        and event.get("payload", {}).get("pull_request", {}).get("merged")
    )
    prs_merged = prs_merged_from_events
    if allow_network_calls:
        merged_pr_total = gh.get_merged_prs_last_n_days(days=365)
        if merged_pr_total is not None:
            prs_merged = merged_pr_total
    releases = sum(1 for event in events if event.get("type") == "ReleaseEvent")

    release_event_times = []
    for event in events:
        if event.get("type") != "ReleaseEvent":
            continue
        created_at = event.get("created_at", "")
        if not created_at:
            continue
        try:
            release_event_times.append(datetime.fromisoformat(created_at.replace("Z", "+00:00")))
        except ValueError:
            continue
    releases_30d = sum(1 for ts in release_event_times if (now_utc - ts).days < 30)
    if allow_network_calls:
        release_total_via_api = gh.get_releases_last_n_days(repos, days=30)
        if release_total_via_api is not None:
            releases_30d = release_total_via_api
    avg_release_gap_days = 0.0
    if len(release_event_times) >= 2:
        sorted_times = sorted(release_event_times, reverse=True)
        gaps = []
        for idx in range(len(sorted_times) - 1):
            gaps.append((sorted_times[idx] - sorted_times[idx + 1]).total_seconds() / 86400.0)
        avg_release_gap_days = sum(gaps) / len(gaps)

    seven_days_ago = now_utc - timedelta(days=7)
    active_repos_7d = 0
    for repo in repos:
        pushed = repo.get("pushed_at", "")
        if not pushed:
            continue
        try:
            pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        except ValueError:
            continue
        if pushed_dt >= seven_days_ago:
            active_repos_7d += 1

    repo_ci_lookup, ci_quality = _build_ci_quality(
        repos,
        allow_network_calls=allow_network_calls,
    )
    ci_count_effective = ci_quality["ci_count_effective"]
    ci_coverage_pct = ci_quality["ci_coverage_pct"]

    public_scope_commits = collected.public_scope_commits
    if not repos:
        commits_status = "empty"
        commits_note = "No repositories in scope."
    elif public_scope_commits is None:
        commits_status = "unavailable"
        commits_note = "Public-scope commit aggregation unavailable for this run; shown as n/a."
    else:
        commits_status = "ok"
        commits_note = "Public-scope commit aggregation complete."

    stars_per_public_repo = (total_stars / len(repos)) if repos else 0.0

    streak_days = _compute_current_streak_days(calendar, now_utc)

    recent_repos, recent_commit_message_by_repo = _build_recent_repos(
        repos,
        seven_days_ago,
        collected.latest_push_message_by_repo,
        allow_network_calls,
    )

    spotlight_data = []
    for repo_name in FEATURED_REPOS:
        repo = next((item for item in collected.all_repos if item["name"] == repo_name), None)
        if not repo:
            continue
        weekly = []
        if allow_network_calls:
            weekly = gh.get_repo_commits_last_n_weeks(repo["owner"]["login"], repo["name"])
        has_ci = has_ci_workflow(repo, allow_network_calls=allow_network_calls)
        spotlight_data.append(
            {
                "name": repo["name"],
                "description": repo.get("description", ""),
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "html_url": repo.get("html_url", ""),
                "pushed_at": (repo.get("pushed_at") or "")[:10],
                "weekly_commits": weekly,
                "has_ci": has_ci,
            }
        )

    scorecard = {
        "releases_30d": releases_30d,
        "active_repos_7d": active_repos_7d,
        "avg_release_gap_days": avg_release_gap_days,
        "stars_per_public_repo": stars_per_public_repo,
        "ci_coverage_pct": ci_coverage_pct,
        "last_year_contributions": collected.total_contributions,
    }
    accent_colors = {
        "BLUE": BLUE,
        "CYAN": CYAN,
        "GREEN": GREEN,
        "ORANGE": ORANGE,
    }
    scorecard_cards = []
    for definition in SCORECARD_METRICS:
        value = scorecard.get(definition["key"], 0)
        scorecard_cards.append(
            {
                "key": definition["key"],
                "label": definition["label"],
                "detail": definition["detail"],
                "value": value,
                "display_value": format_metric_value(value, definition),
                "accent": accent_colors.get(definition.get("accent", "CYAN"), CYAN),
            }
        )

    repo_overview_rows, featured_repo_facts = _build_repo_overview_rows(
        repos,
        recent_commit_message_by_repo,
        collected.latest_push_message_by_repo,
        repo_ci_lookup,
    )

    data_scope = {
        "repos_included": "public + owned + non-fork",
        "activity_metric_scope": "GitHub contributionCalendar.totalContributions (last 12 months)",
        "public_owned_repos_total": repo_counts["public_owned_total"],
        "public_owned_forks_total": repo_counts["public_owned_forks"],
        "public_owned_nonfork_repos_total": repo_counts["public_owned_nonfork"],
        "private_owned_repos_total": repo_counts["private_owned"],
    }

    snapshot = {
        "last_year_contributions": collected.total_contributions,
        "public_scope_commits": public_scope_commits,
        "total_repos": repo_counts["public_owned_nonfork"],
        "public_forks": repo_counts["public_owned_forks"],
        "private_owned_repos": repo_counts["private_owned"],
        "total_stars": total_stars,
        "languages_count": lang_count,
        "prs_merged": prs_merged,
        "releases": releases,
        "ci_repos": ci_count_effective,
        "streak_days": streak_days,
    }

    snapshot_rows = []
    for definition in SNAPSHOT_METRICS:
        key = definition["key"]
        value = snapshot.get(key)
        snapshot_rows.append(
            {
                "key": key,
                "label": definition["label"],
                "dashboard_label": definition["dashboard_label"],
                "value": value,
                "display_value": format_metric_value(value, definition),
            }
        )
    snapshot_cards = [
        {
            "key": row["key"],
            "label": row["dashboard_label"],
            "value": row["value"],
            "display_value": row["display_value"],
        }
        for row in snapshot_rows
    ]

    recent_created = sorted(repos, key=lambda item: item.get("created_at", ""), reverse=True)[:10]

    (
        contributions,
        release_list,
        pr_list,
        focus_now,
        focus_next,
        focus_shipped,
        _repo_row_by_full_name,
    ) = _build_recent_activity(events, recent_repos, repo_overview_rows, USERNAME)

    activity_feed = _build_activity_feed(
        release_list,
        pr_list,
        contributions,
        recent_created,
        recent_repos,
        USERNAME,
    )

    events_status = "ok" if events else "limited"
    events_note = (
        "Public events feed available."
        if events
        else "No recent public events returned in this run; focus/feed use repo push fallbacks."
    )
    data_quality = {
        "ci_status": ci_quality["ci_status"],
        "ci_note": ci_quality["ci_note"],
        "commits_status": commits_status,
        "commits_note": commits_note,
        "events_status": events_status,
        "events_note": events_note,
    }

    theme = {
        "bg_main": BG_DARK,
        "bg_panel": BG_CARD,
        "bg_panel_strong": BG_HIGHLIGHT,
        "text_main": TEXT_BRIGHT,
        "text_soft": TEXT,
        "text_dim": TEXT_DIM,
        "line": BORDER,
        "accent_cyan": CYAN,
        "accent_gold": YELLOW,
        "accent_mint": GREEN,
        "accent_pink": RED,
        "accent_orange": ORANGE,
        "accent_blue": BLUE,
    }

    dashboard_data = {
        "generated_at": now_utc.isoformat().replace("+00:00", "Z"),
        "username": USERNAME,
        "dashboard_url": f"https://{USERNAME}.github.io/{USERNAME}/",
        "theme": theme,
        "snapshot": snapshot,
        "snapshot_rows": snapshot_rows,
        "snapshot_cards": snapshot_cards,
        "data_quality": data_quality,
        "scorecard": scorecard,
        "scorecard_cards": scorecard_cards,
        "data_scope": data_scope,
        "featured_repo_facts": featured_repo_facts,
        "top_languages": top_languages,
        "repo_language_matrix": repo_overview_rows,
        "recent_created": recent_created,
        "focus": {
            "now": focus_now,
            "next": focus_next,
            "shipped": focus_shipped,
        },
        "activity_feed": activity_feed,
        "recent_releases": release_list,
        "recent_pull_requests": pr_list,
    }

    return {
        "now_utc": now_utc,
        "lang_count": lang_count,
        "snapshot": snapshot,
        "snapshot_rows": snapshot_rows,
        "snapshot_cards": snapshot_cards,
        "scorecard": scorecard,
        "scorecard_cards": scorecard_cards,
        "data_scope": data_scope,
        "data_quality": data_quality,
        "featured_repo_facts": featured_repo_facts,
        "top_languages": top_languages,
        "repo_overview_rows": repo_overview_rows,
        "recent_created": recent_created,
        "focus": {
            "now": focus_now,
            "next": focus_next,
            "shipped": focus_shipped,
        },
        "activity_feed": activity_feed,
        "recent_releases": release_list,
        "recent_pull_requests": pr_list,
        "dashboard_data": dashboard_data,
        "recent_repos": recent_repos,
        "spotlight_data": spotlight_data,
        "token_mode": collected.token_mode,
        "cache_mode": collected.cache_mode,
    }
