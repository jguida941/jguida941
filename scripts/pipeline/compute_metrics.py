"""Build the profile metrics and dashboard model from collected data."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from scripts.github import github_client as gh
from scripts.pipeline.collect_data import CollectedProfileData
from scripts.core.config import (
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
from scripts.contracts import (
    DataQuality,
    DataScope,
    Snapshot,
    ScorecardCard,
    SnapshotRow,
    activity_timezone_name,
    profile_timezone_name,
)
from scripts.contracts.profile_contract import (
    SCORECARD_METRICS, SNAPSHOT_METRICS, automation_display, format_metric_value,
    CONTRIBUTION_WEEKDAYS, contribution_rhythm_unavailable, contribution_rhythm_display,
)
from scripts.pipeline.profile_helpers import (
    activity_label,
    ci_text,
    has_ci_workflow,
    is_bot_actor,
    is_self_repo,
    safe_commit_headline,
    time_ago,
)


_ALL_OWNED_NONFORK_AGGREGATE_SCOPE = (
    "owned-public-private-nonfork-profile-excluded-exact"
)
_INCOMPLETE_OWNED_NONFORK_SCOPE = (
    "owned-public-private-nonfork-profile-excluded-partial-observation"
)
_UNAVAILABLE_OWNED_NONFORK_SCOPE = (
    "owned-public-private-nonfork-profile-excluded-unavailable"
)


def _validated_metric_observations(
    collected: CollectedProfileData,
) -> dict[str, dict[str, Any]]:
    observations = getattr(collected, "metric_observations", {})
    if not isinstance(observations, dict):
        return {}
    return {
        metric_id: dict(observation)
        for metric_id, observation in observations.items()
        if metric_id in {
            "public_scope_commits",
            "last_year_contributions",
            "releases_30d",
            "prs_merged",
            "recent_public_events",
        }
        and isinstance(observation, dict)
        and observation.get("metric_id") == metric_id
        and gh.validate_provider_observation(observation)
    }


def _observation_provenance(observation: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in observation.items() if key != "value"}


def _non_exact_carrier(observation: dict[str, Any]) -> dict[str, Any] | None:
    value = observation.get("value")
    if observation.get("status") not in {"partial", "fallback"}:
        return None
    if type(value) is not int or value < 0:
        return None
    return {
        "schema": "profile-nonexact-metric/v1",
        **{
            key: observation.get(key)
            for key in (
                "metric_id",
                "source_metric_id",
                "value",
                "status",
                "population_id",
                "population_signature",
                "window_start",
                "window_end",
                "observed_at",
                "source_id",
                "source_mode",
                "completion_reason",
            )
        },
    }


def _event_type(event: dict[str, Any]) -> str:
    return str(event.get("event_type") or event.get("type") or "")


def _event_repo_name(event: dict[str, Any]) -> str:
    canonical = event.get("repo_full_name")
    if isinstance(canonical, str):
        return canonical
    repo = event.get("repo")
    return str(repo.get("name") or "") if isinstance(repo, dict) else ""


def _event_created_at(event: dict[str, Any]) -> str:
    return str(event.get("occurred_at") or event.get("created_at") or "")


def _event_actor_login(event: dict[str, Any]) -> str | None:
    canonical = event.get("actor_login")
    if canonical is None and isinstance(event.get("actor"), dict):
        canonical = event["actor"].get("login")
    return canonical if isinstance(canonical, str) else None


def _event_payload(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload")
    if isinstance(payload, dict):
        return payload
    event_type = _event_type(event)
    if event_type == "PushEvent":
        return {
            "commits": [
                {"message": headline}
                for headline in event.get("commit_headlines", ())
                if isinstance(headline, str)
            ]
        }
    if event_type == "PullRequestEvent":
        return {
            "action": event.get("action"),
            "pull_request": {
                "merged": event.get("merged") is True,
                "state": event.get("state"),
                "number": event.get("number"),
                "title": event.get("title"),
                "html_url": event.get("url"),
            },
        }
    if event_type == "ReleaseEvent":
        return {
            "action": event.get("action"),
            "release": {
                "tag_name": event.get("tag_name"),
                "html_url": event.get("url"),
            },
        }
    return {"action": event.get("action")}


def _event_push_headline(event: dict[str, Any]) -> str:
    commits = _event_payload(event).get("commits", ())
    if not isinstance(commits, (list, tuple)):
        return ""
    for commit in reversed(commits):
        if not isinstance(commit, dict):
            continue
        headline = safe_commit_headline(commit.get("message"))
        if headline:
            return headline
    return ""


def _zone(name: str) -> Any:
    """Resolve an already-validated effective zone name to a tzinfo."""
    if name == "UTC":
        return timezone.utc
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        return timezone.utc


def _profile_today() -> date:
    """Today's date in the profile timezone (so streaks aren't off-by-one in UTC)."""
    return datetime.now(_zone(profile_timezone_name())).date()


def _parse_calendar_day_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _compute_current_streak_days(
    calendar: dict | None, now_utc: datetime, today_local: date | None = None
) -> int:
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

    today_ref = today_local if today_local is not None else now_utc.date()
    streak = 0
    for day in reversed(all_days):
        day_dt = _parse_calendar_day_date(str(day.get("date", "")))
        if day_dt is not None and day_dt.date() > today_ref:
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


def _owner_login(repository: dict[str, Any]) -> str:
    owner = repository.get("owner")
    login = owner.get("login") if isinstance(owner, dict) else None
    return str(login).strip() if isinstance(login, str) and login.strip() else USERNAME


def _row_identity(repository: dict[str, Any]) -> tuple[str, str]:
    """The normalized (owner, repository) pair that distinguishes two rows.

    Repository name alone is not an identity: the same name under two owners is
    two repositories, and two rows for one owner/name pair are one repository.
    """
    return (
        _owner_login(repository).casefold(),
        str(repository.get("name", "")).strip().casefold(),
    )


def _admitted_identity(repository: dict[str, Any], population: str) -> tuple[str, str]:
    owner = repository.get("owner")
    login = owner.get("login") if isinstance(owner, dict) else None
    name = repository.get("name")
    if not isinstance(login, str) or not login.strip():
        raise ValueError(
            f"repository in {population} is missing a non-empty owner login"
        )
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"repository in {population} is missing a non-empty name")
    return login.strip().casefold(), name.strip().casefold()


def admit_repository_population(collected: CollectedProfileData) -> None:
    """Reject a population that cannot be an exact set of distinct repositories.

    Matching a declared count is necessary but never sufficient: two rows for one
    normalized owner/name pair double-count one repository on every aggregate and
    collapse it on every row surface, so admission fails before any computation
    or output write. Equal names under different owners stay distinct.
    """
    populations = (
        ("repos", collected.repos),
        ("private_repos", collected.private_repos),
        ("all_repos", collected.all_repos),
    )
    for population, rows in populations:
        seen: set[tuple[str, str]] = set()
        for repository in rows:
            if not isinstance(repository, dict):
                raise ValueError(f"repository in {population} must be an object")
            identity = _admitted_identity(repository, population)
            if identity in seen:
                raise ValueError(
                    f"duplicate repository identity {identity[0]}/{identity[1]} in {population}"
                )
            seen.add(identity)

    def nonfork_identities(rows: list[dict[str, Any]], population: str) -> set[tuple[str, str]]:
        return {
            _admitted_identity(repository, population)
            for repository in rows
            if isinstance(repository, dict) and repository.get("fork") is not True
        }

    shared = nonfork_identities(collected.repos, "repos") & nonfork_identities(
        collected.private_repos, "private_repos"
    )
    if shared:
        owner, name = sorted(shared)[0]
        raise ValueError(
            f"duplicate repository identity {owner}/{name} in both the public and "
            "private non-fork populations"
        )


def _build_recent_repos(
    repos: list[dict],
    seven_days_ago: datetime,
    latest_push_message_by_repo: dict[str, str],
    allow_network_calls: bool,
    private_repos: list[dict] | None = None,
) -> tuple[list[dict], dict[tuple[str, str], str]]:
    recent_repos = []
    recent_commit_message_by_repo: dict[tuple[str, str], str] = {}
    seen = set()
    candidates = list(repos) + list(private_repos or [])
    for repo in sorted(candidates, key=lambda item: item.get("pushed_at", ""), reverse=True):
        name = repo.get("name", "")
        # Never surface the profile repo itself (the hourly bot commit).
        if not name or is_self_repo(name):
            continue
        pushed = repo.get("pushed_at", "")
        if not pushed:
            continue
        try:
            pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        except (AttributeError, ValueError):
            continue
        if pushed_dt < seven_days_ago:
            break
        identity = _row_identity(repo)
        if identity in seen:
            continue
        seen.add(identity)

        last_msg = safe_commit_headline(repo.get("latest_commit_message"))
        if not last_msg and allow_network_calls:
            try:
                commits_data = gh.paginated_get(
                    f"repos/{_owner_login(repo)}/{name}/commits",
                    {"per_page": 1},
                    per_page=1,
                )
                if commits_data:
                    last_msg = safe_commit_headline(
                        commits_data[0].get("commit", {}).get("message")
                    )
            except Exception:
                pass
        if not last_msg:
            full_name = f"{_owner_login(repo)}/{name}"
            last_msg = safe_commit_headline(
                latest_push_message_by_repo.get(full_name)
            )
        if not last_msg:
            last_msg = "recent push detected"

        if last_msg:
            recent_commit_message_by_repo[identity] = last_msg
        recent_repos.append(
            {
                "name": name,
                "html_url": repo.get("html_url", ""),
                "language": repo.get("language"),
                "pushed_at": pushed,
                "last_commit_msg": last_msg,
                "is_private": repo.get("private") is True,
            }
        )
    return recent_repos, recent_commit_message_by_repo


def _build_ci_quality(
    repos: list[dict],
    *,
    allow_network_calls: bool,
) -> dict[tuple[str, str], bool | None]:
    repo_ci_lookup: dict[tuple[str, str], bool | None] = {}
    for repo in repos:
        name = repo.get("name", "")
        if not name or is_self_repo(name):
            continue
        repo_ci_lookup[_row_identity(repo)] = has_ci_workflow(
            repo, allow_network_calls=allow_network_calls
        )

    return repo_ci_lookup


def _build_repo_overview_rows(
    repos: list[dict],
    recent_commit_message_by_repo: dict[tuple[str, str], str],
    latest_push_message_by_repo: dict[str, str],
    repo_ci_lookup: dict[tuple[str, str], bool | None],
) -> tuple[list[dict], list[dict]]:
    sorted_repos_by_push = sorted(repos, key=lambda item: item.get("pushed_at", ""), reverse=True)
    repo_by_identity = {
        _row_identity(repo): repo for repo in repos if repo.get("name")
    }
    featured_set = set(FEATURED_REPOS)

    def build_repo_row(repo: dict) -> dict:
        owner_login = _owner_login(repo)
        name = repo.get("name", "")
        full_name = f"{owner_login}/{name}" if name else ""
        identity = _row_identity(repo)
        pushed_raw = repo.get("pushed_at", "") or ""
        pushed_date = pushed_raw[:10] if pushed_raw else ""
        commit_msg = safe_commit_headline(repo.get("latest_commit_message"))
        if not commit_msg and name:
            commit_msg = safe_commit_headline(
                recent_commit_message_by_repo.get(identity, "")
            )
        if not commit_msg and full_name:
            commit_msg = safe_commit_headline(
                latest_push_message_by_repo.get(full_name, "")
            )
        if not commit_msg:
            commit_msg = "recent push detected"

        ci_state = repo_ci_lookup.get(identity)
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
            "is_private": repo.get("private") is True,
            "featured": name in featured_set,
        }

    ordered_identities: list[tuple[str, str]] = []
    for featured_name in FEATURED_REPOS:
        for identity, repo in repo_by_identity.items():
            if repo.get("name") == featured_name and identity not in ordered_identities:
                ordered_identities.append(identity)
    for repo in sorted_repos_by_push:
        repo_name = repo.get("name", "")
        if is_self_repo(repo_name):
            continue
        identity = _row_identity(repo)
        if repo_name and identity not in ordered_identities:
            ordered_identities.append(identity)
        if len(ordered_identities) >= 18:
            break

    repo_overview_rows = [
        build_repo_row(repo_by_identity[identity])
        for identity in ordered_identities
        if identity in repo_by_identity
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
    owned_repo_prefix = f"{username}/".casefold()

    contributions = []
    seen_contrib = set()
    for event in events:
        event_type = _event_type(event)
        if event_type not in contribution_event_types:
            continue
        repo_name = _event_repo_name(event)
        if not repo_name.casefold().startswith(owned_repo_prefix):
            continue
        # Drop the profile repo itself and automation-actor events.
        if is_self_repo(None, repo_name):
            continue
        if is_bot_actor(_event_actor_login(event)):
            continue
        created_at = _event_created_at(event)
        push_headline = _event_push_headline(event) if event_type == "PushEvent" else ""
        canonical_push = (
            event_type == "PushEvent"
            and event.get("evidence_status") in {"ok", "partial"}
        )
        contribution_identity = (
            ("push", repo_name.casefold(), created_at, push_headline)
            if canonical_push
            else ("legacy_push", repo_name.casefold())
            if event_type == "PushEvent"
            else ("other", repo_name.casefold())
        )
        if contribution_identity in seen_contrib:
            continue
        seen_contrib.add(contribution_identity)
        contribution = {
            "repo": repo_name,
            "url": f"https://github.com/{repo_name}",
            "activity": activity_label(event_type),
            "time_ago": time_ago(created_at),
            "created_at": created_at,
            "is_private": False,
            "observation_source": "event",
        }
        if event_type == "PushEvent":
            contribution["_push_identity_headline"] = push_headline
            contribution["_push_identity_scope"] = (
                "observation" if canonical_push else "repository"
            )
        contributions.append(contribution)
        if len(contributions) >= 10:
            break

    if not contributions:
        for repo in recent_repos[:10]:
            full_name = f"{username}/{repo['name']}"
            headline = safe_commit_headline(repo.get("last_commit_msg")) or "push"
            contributions.append(
                {
                    "repo": full_name,
                    "url": repo.get("html_url", f"https://github.com/{full_name}"),
                    "activity": "push",
                    "time_ago": time_ago(repo.get("pushed_at", "")),
                    "created_at": repo.get("pushed_at", ""),
                    "is_private": bool(repo.get("is_private")),
                    "observation_source": "repository push metadata",
                    "_push_identity_headline": headline,
                }
            )

    release_list = []
    for event in events:
        if _event_type(event) != "ReleaseEvent":
            continue
        payload = _event_payload(event)
        release = payload.get("release", {})
        repo_name = _event_repo_name(event)
        if is_self_repo(None, repo_name):
            continue
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
                "time_ago": time_ago(_event_created_at(event)),
                "created_at": _event_created_at(event),
            }
        )
        if len(release_list) >= 5:
            break

    pr_list = []
    for event in events:
        if _event_type(event) != "PullRequestEvent":
            continue
        pr = _event_payload(event).get("pull_request", {})
        repo_name = _event_repo_name(event)
        if is_self_repo(None, repo_name):
            continue
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
                "time_ago": time_ago(_event_created_at(event)),
                "created_at": _event_created_at(event),
            }
        )
        if len(pr_list) >= 5:
            break

    repo_row_by_full_name = {
        row["full_name"]: row for row in repo_overview_rows if row.get("full_name")
    }

    # "Now" = actual most-recent pushes (public + private, self-repo excluded),
    # never the featured-ordered overview — this is what's genuinely in flight.
    focus_now = []
    for repo in recent_repos[:3]:
        lang = repo.get("language") or "code"
        detail = f"{lang} · pushed {time_ago(repo.get('pushed_at', ''))}"
        focus_now.append(
            {
                "title": repo["name"],
                "detail": detail,
                "url": repo.get("html_url", ""),
                "is_private": bool(repo.get("is_private")),
            }
        )
    if not focus_now:
        for entry in contributions[:3]:
            repo_short = entry["repo"].split("/")[-1] if entry.get("repo") else "repo"
            focus_now.append(
                {
                    "title": repo_short,
                    "detail": f"{entry['activity']} · {entry['time_ago']}",
                    "url": entry["url"],
                }
            )

    # "Next" is sourced ONLY from real open PRs. No fabricated "Next pass:" items —
    # an empty lane is honest when there is nothing queued.
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
        # Fall back to recent pushes with a publishable commit headline, excluding
        # only repositories already shown in "Now".
        now_titles = {item.get("title") for item in focus_now}
        for repo in recent_repos[:8]:
            if repo["name"] in now_titles:
                continue
            msg = repo.get("last_commit_msg", "")
            if not msg or msg == "recent push detected":
                continue
            if len(msg) > 58:
                msg = msg[:55] + "..."
            focus_shipped.append(
                {
                    "title": msg,
                    "detail": f"{repo['name']} · {time_ago(repo.get('pushed_at', ''))}",
                    "url": repo.get("html_url", ""),
                    "is_private": bool(repo.get("is_private")),
                }
            )
            if len(focus_shipped) >= 3:
                break

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
        activity = contrib["activity"]
        title = (
            contrib.get("_push_identity_headline") or activity
            if activity == "push"
            else activity
        )
        activity_feed.append(
            {
                "kind": "activity",
                "title": title,
                "url": contrib["url"],
                "repo": contrib["repo"],
                "repo_url": contrib["url"],
                "state": activity.upper(),
                "time_ago": contrib["time_ago"],
                "created_at": contrib["created_at"],
                "is_private": bool(contrib.get("is_private")),
                "observation_source": contrib.get(
                    "observation_source", "event"
                ),
                "_push_identity_headline": contrib.get(
                    "_push_identity_headline", ""
                ),
                "_push_identity_scope": contrib.get(
                    "_push_identity_scope", "observation"
                ),
            }
        )
    event_push_identities = {
        (
            str(item.get("repo", "")).casefold(),
            item.get("created_at", ""),
            item.get("_push_identity_headline", ""),
        )
        for item in activity_feed
        if item.get("state") == "PUSH"
        and item.get("observation_source") == "event"
        and item.get("_push_identity_scope") == "observation"
    }
    legacy_event_push_repositories = {
        str(item.get("repo", "")).casefold()
        for item in activity_feed
        if item.get("state") == "PUSH"
        and item.get("observation_source") == "event"
        and item.get("_push_identity_scope") == "repository"
    }
    for repo in recent_repos:
        repo_name = f"{username}/{repo.get('name', '')}"
        headline = safe_commit_headline(repo.get("last_commit_msg")) or "push"
        push_identity = (
            repo_name.casefold(),
            repo.get("pushed_at", ""),
            headline,
        )
        if (
            not repo.get("name")
            or repo_name.casefold() in legacy_event_push_repositories
            or push_identity in event_push_identities
        ):
            continue
        activity_feed.append(
            {
                "kind": "activity",
                "title": headline,
                "url": repo.get("html_url", ""),
                "repo": repo_name,
                "repo_url": repo.get("html_url", ""),
                "state": "PUSH",
                "time_ago": time_ago(repo.get("pushed_at", "")),
                "created_at": repo.get("pushed_at", ""),
                "is_private": bool(repo.get("is_private")),
                "observation_source": "repository push metadata",
                "_push_identity_headline": headline,
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
                "is_private": repo.get("private") is True,
                "observation_source": "repository creation metadata",
            }
        )

    activity_feed = sorted(
        activity_feed,
        key=lambda item: (
            item.get("created_at", ""),
            item.get("observation_source") == "event",
        ),
        reverse=True,
    )
    deduped_feed = []
    seen_feed = set()
    for item in activity_feed:
        if item.get("state") == "PUSH":
            signature = (
                "push",
                str(item.get("repo", "")).casefold(),
                item.get("created_at", ""),
                item.get("_push_identity_headline", ""),
            )
        else:
            signature = (
                item.get("kind", ""),
                item.get("title", ""),
                item.get("repo", ""),
                item.get("created_at", ""),
            )
        if signature in seen_feed:
            continue
        seen_feed.add(signature)
        item.pop("_push_identity_headline", None)
        item.pop("_push_identity_scope", None)
        deduped_feed.append(item)
    return deduped_feed[:18]


def _build_language_stats(
    repos: list[dict[str, Any]],
    language_bytes: dict[str, int],
) -> tuple[list[dict[str, Any]], int, int]:
    """Return (top_languages, lang_count, total_language_bytes)."""
    total_language_bytes = sum(bytes_ for bytes_ in language_bytes.values() if bytes_ > 0)
    lang_count = len([lang for lang, bytes_ in language_bytes.items() if bytes_ > 0])

    top_languages: list[dict[str, Any]] = []
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
    return top_languages, lang_count, total_language_bytes


def _private_aggregate_quality(
    repo_counts: dict[str, int | None],
    private_repos: list[dict[str, Any]],
) -> str:
    """Classify whether the private non-fork inventory is complete."""
    expected = repo_counts.get("private_owned_nonfork")
    if type(expected) is not int or expected < 0:
        return "unavailable"
    if len(private_repos) != expected:
        return "partial"
    return "exact"


def _inventory_quality(
    expected: object,
    repositories: list[dict[str, Any]],
) -> str:
    if type(expected) is not int or expected < 0:
        return "unavailable"
    if len(repositories) != expected:
        return "partial"
    return "exact"


def _has_valid_push_fact(repository: dict[str, Any]) -> bool:
    pushed_at = repository.get("pushed_at")
    if not isinstance(pushed_at, str) or not pushed_at:
        return False
    try:
        datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _has_valid_automation_fact(repository: dict[str, Any]) -> bool:
    workflow_state = repository.get("has_ci_workflows")
    workflow_count = repository.get("workflow_file_count")
    return (
        isinstance(workflow_state, bool)
        and not isinstance(workflow_count, bool)
        and isinstance(workflow_count, int)
        and workflow_count >= 0
        and workflow_state is (workflow_count > 0)
    )


def _build_automation_summary(
    repo_counts: dict[str, int | None],
    public_repos: list[dict[str, Any]],
    private_repos: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Workflow configuration at observed HEAD, from valid paired facts only.

    Inventory completeness and workflow observation completeness are independent.
    Missing inventory never supplies an adoption denominator. Unknown workflow
    pairs never contribute to either the repository or file subtotal.
    """
    def finish(observed, eligible, known, configured, files, inventory):
        empty = inventory == "exact" and eligible == 0
        status = ("exact" if inventory == "exact" and known == observed
                  else "partial" if known else "unavailable")
        return {
            "observed_eligible_repos": observed,
            "eligible_repos": eligible,
            "observed_workflow_repos": known,
            "unknown_workflow_repos": observed - known,
            "configured_repos": configured if known or empty else None,
            "workflow_files": files if known or empty else None,
            "adoption_pct": configured / eligible * 100 if eligible and known else None,
            "inventory_status": inventory,
            "status": status,
        }

    def partition(repositories, expected):
        nonfork = [repo for repo in repositories if repo.get("fork") is not True]
        inventory = _inventory_quality(expected, nonfork)
        eligible = [repo for repo in nonfork if not is_self_repo(repo.get("name"))]
        valid = [repo for repo in eligible if _has_valid_automation_fact(repo)]
        return finish(
            len(eligible), len(eligible) if inventory == "exact" else None,
            len(valid), sum(repo["has_ci_workflows"] is True for repo in valid),
            sum(repo["workflow_file_count"] for repo in valid), inventory,
        )

    public = partition(public_repos, repo_counts.get("public_owned_nonfork"))
    private = partition(private_repos, repo_counts.get("private_owned_nonfork"))
    rows = (public, private)
    inventory = ("exact" if all(row["inventory_status"] == "exact" for row in rows)
                 else "unavailable" if all(row["inventory_status"] == "unavailable" for row in rows)
                 else "partial")
    combined = finish(
        sum(row["observed_eligible_repos"] for row in rows),
        sum(row["eligible_repos"] for row in rows) if inventory == "exact" else None,
        sum(row["observed_workflow_repos"] for row in rows),
        sum(row["configured_repos"] for row in rows if row["configured_repos"] is not None),
        sum(row["workflow_files"] for row in rows if row["workflow_files"] is not None),
        inventory,
    )
    return {"public": public, "private": private, "combined": combined}


def _has_valid_language_fact(
    repository: dict[str, Any],
    *,
    completeness_markers_present: bool,
) -> bool:
    language_bytes = repository.get("language_bytes")
    language_shape_is_valid = isinstance(language_bytes, dict) and all(
        isinstance(language, str)
        and bool(language)
        and not isinstance(byte_count, bool)
        and isinstance(byte_count, int)
        and byte_count > 0
        for language, byte_count in language_bytes.items()
    )
    if not language_shape_is_valid:
        return False
    if completeness_markers_present:
        return repository.get("language_bytes_complete") is True
    return True


def _metric_family_statuses(
    repo_counts: dict[str, int | None],
    public_repos: list[dict[str, Any]],
    private_repos: list[dict[str, Any]],
) -> dict[str, str]:
    """Classify each value from the facts that actually contributed to it."""
    public_inventory_status = _inventory_quality(
        repo_counts.get("public_owned_nonfork"), public_repos
    )
    private_inventory_status = _inventory_quality(
        repo_counts.get("private_owned_nonfork"), private_repos
    )
    inventory_is_exact = (
        public_inventory_status == "exact"
        and private_inventory_status == "exact"
    )
    repositories = [
        repository
        for repository in [*public_repos, *private_repos]
        if not is_self_repo(repository.get("name"))
    ]
    language_markers_present = any(
        "language_bytes_complete" in repository for repository in repositories
    )
    validators = {
        "push": _has_valid_push_fact,
        "language": lambda repository: _has_valid_language_fact(
            repository,
            completeness_markers_present=language_markers_present,
        ),
    }
    statuses: dict[str, str] = {}
    for family, validator in validators.items():
        valid_fact_count = sum(
            1 for repository in repositories if validator(repository)
        )
        if not repositories:
            statuses[family] = "exact" if inventory_is_exact else "unavailable"
        elif inventory_is_exact and valid_fact_count == len(repositories):
            statuses[family] = "exact"
        elif valid_fact_count:
            statuses[family] = "partial"
        else:
            statuses[family] = "unavailable"
    return statuses


def _aggregate_language_bytes(
    public_repos: list[dict[str, Any]],
    private_repos: list[dict[str, Any]],
    *,
    fallback_public_language_bytes: dict[str, int],
) -> dict[str, int]:
    """Aggregate every valid observed fact in the self-excluded population."""
    public_population = [
        repository
        for repository in public_repos
        if not is_self_repo(repository.get("name"))
    ]
    private_population = [
        repository
        for repository in private_repos
        if not is_self_repo(repository.get("name"))
    ]
    repositories = [*public_population, *private_population]
    language_markers_present = any(
        "language_bytes_complete" in repository for repository in repositories
    )
    combined: dict[str, int] = {}
    valid_public_facts = 0
    public_row_ids = {id(repository) for repository in public_population}
    for repository in repositories:
        if not _has_valid_language_fact(
            repository,
            completeness_markers_present=language_markers_present,
        ):
            continue
        if id(repository) in public_row_ids:
            valid_public_facts += 1
        language_bytes = repository.get("language_bytes", {})
        for language, byte_count in language_bytes.items():
            combined[language] = combined.get(language, 0) + byte_count

    # REST fallback rows do not carry per-repository byte maps. Preserve their
    # known aggregate as a qualified observation when there is no row-level
    # public numerator to double-count.
    if public_population and valid_public_facts == 0:
        for language, byte_count in fallback_public_language_bytes.items():
            if (
                type(language) is str
                and language
                and type(byte_count) is int
                and byte_count > 0
            ):
                combined[language] = combined.get(language, 0) + byte_count
    return combined


def _build_pr_and_release_stats(
    events: list[dict[str, Any]],
    repos: list[dict[str, Any]],
    now_utc: datetime,
    *,
    allow_network_calls: bool,
    observations: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return exact PR/release scalars plus their metric-specific quality."""
    observations = observations or {}
    prs_observation = observations.get("prs_merged")
    if prs_observation is not None:
        prs_merged = (
            prs_observation.get("value")
            if prs_observation.get("status") == "ok"
            else None
        )
        prs_status = str(prs_observation.get("status"))
        prs_note = (
            "Merged pull-request observation complete for the primary provider population."
            if prs_status == "ok"
            else "Merged pull-request value retained as non-exact provider evidence."
        )
    else:
        prs_merged = None
        prs_status = "unavailable"
        prs_note = "Merged pull-request observation unavailable for this run."

    release_event_times: list[datetime] = []
    for event in events:
        if _event_type(event) != "ReleaseEvent":
            continue
        created_at = _event_created_at(event)
        if not created_at:
            continue
        try:
            release_event_times.append(datetime.fromisoformat(created_at.replace("Z", "+00:00")))
        except ValueError:
            continue

    releases_from_events_30d = sum(1 for ts in release_event_times if (now_utc - ts).days < 30)
    release_observation = observations.get("releases_30d")
    if release_observation is not None:
        releases_30d = (
            release_observation.get("value")
            if release_observation.get("status") == "ok"
            else None
        )
        releases_status = str(release_observation.get("status"))
        releases_note = (
            "Release aggregation complete for the current repository population."
            if releases_status == "ok"
            else "Release value retained as non-exact provider evidence."
        )
    else:
        releases_30d = releases_from_events_30d
        releases_status = "events_fallback"
        releases_note = "Release count derived from events feed fallback (offline or fixture mode)."
    if release_observation is None and allow_network_calls:
        release_total_via_api = gh.get_releases_last_n_days(repos, days=30)
        if release_total_via_api is None:
            releases_30d = releases_from_events_30d
            releases_status = "fallback"
            releases_note = "Release API count unavailable for this run; using events fallback."
        else:
            releases_30d = release_total_via_api
            releases_status = "ok"
            releases_note = "Release aggregation complete."
    avg_release_gap_days = 0.0
    if len(release_event_times) >= 2:
        sorted_times = sorted(release_event_times, reverse=True)
        gaps = []
        for idx in range(len(sorted_times) - 1):
            gaps.append((sorted_times[idx] - sorted_times[idx + 1]).total_seconds() / 86400.0)
        avg_release_gap_days = sum(gaps) / len(gaps)

    return {
        "prs_merged": prs_merged,
        "prs_status": prs_status,
        "prs_note": prs_note,
        "releases_30d": releases_30d,
        "releases_status": releases_status,
        "releases_note": releases_note,
        "avg_release_gap_days": avg_release_gap_days,
    }


def _build_commit_stats(
    collected: CollectedProfileData,
    repos: list[dict[str, Any]],
    *,
    allow_network_calls: bool,
    observation: dict[str, Any] | None = None,
) -> tuple[int | None, str, str]:
    """Return (public_scope_commits, commits_status, commits_note)."""
    if observation is not None:
        status = str(observation.get("status"))
        if status == "ok":
            return (
                observation.get("value"),
                "ok",
                "Public-scope commit aggregation complete.",
            )
        if status == "fallback":
            return (
                None,
                "fallback",
                "Public-scope commit aggregation unavailable; a broader aggregate is retained as non-exact evidence.",
            )
        return None, status, "Public-scope commit aggregation unavailable for this run."

    return None, "unavailable", "Public-scope commit observation unavailable for this run."


def _contribution_observation_bounds(
    collected: CollectedProfileData, days: dict[date, int],
) -> tuple[datetime, datetime] | None:
    """Only a matching native observation can certify coverage of dated values."""
    observation = _validated_metric_observations(collected).get("last_year_contributions")
    if not observation or observation.get("status") != "ok" or observation.get("complete") is not True:
        return None
    if (observation.get("source_metric_id") != "github_contribution_calendar_total_and_days"
            or observation.get("source_id") != "github_graphql_contribution_calendar"):
        return None
    rows = observation["value"]["days"]
    native = {date.fromisoformat(row["date"]): row["count"] for row in rows}
    if len(native) != len(rows) or native != days:
        return None
    try:
        bounds = [datetime.fromisoformat(observation[key].replace("Z", "+00:00"))
                  for key in ("window_start", "window_end", "observed_at")]
    except (TypeError, ValueError, AttributeError):
        return None
    if any(value.tzinfo is None or value.utcoffset() is None for value in bounds):
        return None
    start, end, observed = [value.astimezone(timezone.utc) for value in bounds]
    cutoff = min(end, observed)
    return (start, cutoff) if start <= cutoff else None


def _build_contribution_rhythm(collected: CollectedProfileData) -> dict[str, Any]:
    """Sum the full dated calendar, retaining observation uncertainty explicitly."""
    unavailable = contribution_rhythm_unavailable()
    calendar = collected.calendar
    if not isinstance(calendar, dict):
        return unavailable
    days: dict[date, int] = {}
    try:
        weeks = calendar.get("weeks")
        if not isinstance(weeks, list):
            raise ValueError("invalid weeks")
        for week in weeks:
            rows = week.get("contributionDays") if isinstance(week, dict) else None
            if not isinstance(rows, list):
                raise ValueError("invalid days")
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError("invalid day")
                label, count = row.get("date"), row.get("contributionCount")
                day = date.fromisoformat(label)
                if day.isoformat() != label or type(count) is not int or count < 0 or day in days:
                    raise ValueError("invalid dated count")
                days[day] = count
        if not days:
            return contribution_rhythm_unavailable("no_dated_days")
        ordered = sorted(days)
        total = calendar.get("totalContributions")
        if (type(total) is not int or total < 0 or total != sum(days.values())
                or (ordered[-1] - ordered[0]).days + 1 != len(ordered)):
            raise ValueError("inconsistent calendar")
    except (TypeError, ValueError):
        return contribution_rhythm_unavailable("invalid_calendar")

    # Inspect the original carrier as well as its validated form: malformed or
    # stale supplied metadata must not disappear into the raw-data-only state.
    observations = getattr(collected, "metric_observations", {})
    if not isinstance(observations, dict):
        return contribution_rhythm_unavailable("observation_unavailable")
    bounds = None
    if "last_year_contributions" in observations:
        observation = _validated_metric_observations(collected).get("last_year_contributions")
        try:
            bounds = _contribution_observation_bounds(collected, days)
        except (KeyError, TypeError, ValueError):
            return contribution_rhythm_unavailable("observation_unavailable")
        if (not observation or not bounds or observation["value"]["total"] != total
                or not bounds[0].date() <= ordered[0] <= ordered[-1] <= bounds[1].date()):
            return contribution_rhythm_unavailable("observation_unavailable")
        end = datetime.fromisoformat(observation["window_end"].replace("Z", "+00:00")).astimezone(timezone.utc)
        observed = datetime.fromisoformat(observation["observed_at"].replace("Z", "+00:00")).astimezone(timezone.utc)
        if observed < end:
            return contribution_rhythm_unavailable("observation_unavailable")
    buckets = [{"weekday": name, "contributions": 0, "days_observed": 0}
               for name in CONTRIBUTION_WEEKDAYS]
    for day, count in days.items():
        buckets[day.weekday()]["contributions"] += count
        buckets[day.weekday()]["days_observed"] += 1
    return {
        **unavailable, "status": "available", "reason": "dated_calendar",
        "completeness": "known" if bounds else "unknown",
        "window_start": ordered[0].isoformat(), "window_end": ordered[-1].isoformat(),
        "days_observed": len(days), "total": total, "weekdays": buckets,
        "last_day_in_progress": bounds[1].date() <= ordered[-1] if bounds else None,
    }


def _build_contribution_trend(collected: CollectedProfileData) -> dict[str, Any]:
    """Preserve GitHub's UTC date labels; never rebucket them by viewer timezone.

    Raw dated values can outlive their observation metadata. They remain useful,
    but generation time cannot establish that their weeks are complete.
    """
    unavailable = {
        "status": "unavailable", "unit": "contributions", "bucket": "iso_week",
        "week_start_day": "Monday", "timezone": "UTC", "completeness": "unknown",
        "window_start": None, "window_end": None, "points": [],
        "reason": "calendar_unavailable",
    }
    calendar = collected.calendar
    if not isinstance(calendar, dict):
        return unavailable
    days: dict[date, int] = {}
    try:
        weeks = calendar.get("weeks")
        if not isinstance(weeks, list):
            raise ValueError("invalid weeks")
        for week in weeks:
            rows = week.get("contributionDays") if isinstance(week, dict) else None
            if not isinstance(rows, list):
                raise ValueError("invalid days")
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError("invalid day")
                label, count = row.get("date"), row.get("contributionCount")
                day = date.fromisoformat(label)
                if day.isoformat() != label or type(count) is not int or count < 0 or day in days:
                    raise ValueError("invalid dated count")
                days[day] = count
        if not days:
            return {**unavailable, "reason": "no_dated_days"}
        ordered = sorted(days)
        if (ordered[-1] - ordered[0]).days + 1 != len(ordered):
            raise ValueError("missing date")
    except (TypeError, ValueError):
        return {**unavailable, "reason": "invalid_calendar"}

    bounds = _contribution_observation_bounds(collected, days)
    if bounds and not (bounds[0].date() <= ordered[0] <= ordered[-1] <= bounds[1].date()):
        return {**unavailable, "reason": "invalid_calendar"}
    buckets: dict[date, list[date]] = {}
    for day in ordered:
        monday = day - timedelta(days=day.weekday())
        buckets.setdefault(monday, []).append(day)
    points = []
    for monday, observed_days in list(buckets.items())[-12:]:
        start = datetime.combine(monday, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=7)
        partial = (len(observed_days) != 7 or bounds is None
                   or bounds[0] > start or bounds[1] < end)
        points.append({
            "week_start": monday.isoformat(), "week_end": (monday + timedelta(days=6)).isoformat(),
            "observed_start": observed_days[0].isoformat(), "observed_end": observed_days[-1].isoformat(),
            "days_observed": len(observed_days), "contributions": sum(days[day] for day in observed_days),
            "partial": partial,
        })
    return {
        **unavailable, "status": "available", "reason": "dated_calendar",
        "completeness": "known" if bounds else "unknown", "points": points,
        "window_start": points[0]["observed_start"], "window_end": points[-1]["observed_end"],
    }


def _build_engineering_metrics(
    collected: CollectedProfileData,
    push_repos: list[dict[str, Any]],
    top_languages: list[dict[str, Any]],
    now_utc: datetime,
    *,
    automation: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Backend-developer analytics derived from already-fetched data."""
    calendar = collected.calendar if isinstance(collected.calendar, dict) else {}
    weeks = calendar.get("weeks", []) if isinstance(calendar, dict) else []

    active_days = 0
    for week in weeks:
        days = week.get("contributionDays", []) if isinstance(week, dict) else []
        for day in days:
            try:
                if int(day.get("contributionCount", 0)) > 0:
                    active_days += 1
            except (TypeError, ValueError):
                continue

    contribution_trend = _build_contribution_trend(collected)
    weekly_cadence = [point["contributions"] for point in contribution_trend["points"]]

    automation = automation or _build_automation_summary(
        collected.repo_counts, getattr(collected, "repos", push_repos), collected.private_repos
    )
    workflow = automation["combined"]

    primary_lang_share_pct = float(top_languages[0]["percent"]) if top_languages else 0.0
    languages_over_5pct = sum(1 for lang in top_languages if float(lang.get("percent", 0)) >= 5.0)

    gaps: list[int] = []
    for r in push_repos:
        if is_self_repo(r.get("name")):
            continue
        pushed = r.get("pushed_at", "")
        if not pushed:
            continue
        try:
            pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        except ValueError:
            continue
        gaps.append((now_utc - pushed_dt).days)
    gaps.sort()
    if gaps:
        mid = len(gaps) // 2
        median_days_since_push = float(
            gaps[mid] if len(gaps) % 2 else (gaps[mid - 1] + gaps[mid]) / 2
        )
    else:
        median_days_since_push = 0.0
    # The FRESHEST repo's age = the user's true "last push". gaps is sorted ascending, so
    # gaps[0] is the minimum. The median across all (incl. archived) repos reads as staleness
    # and is dishonest as a "since last push" figure; this is the honest one (P5-DATA).
    days_since_last_push = float(gaps[0]) if gaps else 0.0

    counts = collected.repo_counts
    private_count = counts.get("private_owned")
    private_nonfork_count = counts.get("private_owned_nonfork")
    return {
        "active_days_last_year": active_days,
        "weekly_cadence": weekly_cadence,
        "contribution_trend": contribution_trend,
        "automation_workflows": workflow["workflow_files"],
        "automation_repos": workflow["configured_repos"],
        "primary_lang_share_pct": round(primary_lang_share_pct, 1),
        "languages_over_5pct": languages_over_5pct,
        "median_days_since_push": round(median_days_since_push, 1),
        "days_since_last_push": round(days_since_last_push, 1),
        "public_repos_total": int(counts.get("public_owned_total", 0) or 0),
        "public_nonfork_repos": int(counts.get("public_owned_nonfork", 0) or 0),
        "private_repos_total": int(private_count) if isinstance(private_count, int) else None,
        "private_nonfork_repos": (
            int(private_nonfork_count)
            if isinstance(private_nonfork_count, int)
            else None
        ),
        "automation_eligible_repos": workflow["eligible_repos"],
        "recent_private_count": len(collected.private_repos),
    }


def _build_snapshot_dict(
    collected: CollectedProfileData,
    repo_counts: dict[str, int | None],
    total_stars: int,
    lang_count: int | None,
    prs_merged: int | None,
    releases_30d: int | None,
    ci_count_effective: int | None,
    streak_days: int,
    public_scope_commits: int | None,
    last_year_contributions: int | None = None,
) -> Snapshot:
    """Assemble the snapshot dict."""
    return {
        "last_year_contributions": last_year_contributions,
        "public_scope_commits": public_scope_commits,
        "total_repos": repo_counts["public_owned_nonfork"],
        "public_forks": repo_counts["public_owned_forks"],
        "private_owned_repos": repo_counts["private_owned"],
        "total_stars": total_stars,
        "languages_count": lang_count,
        "prs_merged": prs_merged,
        "releases": releases_30d,
        "ci_repos": ci_count_effective,
        "streak_days": streak_days,
    }


def _build_scorecard_cards(
    scorecard: dict[str, Any],
    accent_colors: dict[str, str],
) -> list[ScorecardCard]:
    """Build the scorecard_cards list from scorecard values and accent colour map."""
    scorecard_cards: list[ScorecardCard] = []
    for definition in SCORECARD_METRICS:
        value = scorecard.get(
            definition["key"],
            None if definition.get("format") == "int_or_na" else 0,
        )
        scorecard_cards.append(
            {
                "key": definition["key"],
                "label": definition["label"],
                "detail": definition["detail"],
                "value": value,
                "display_value": format_metric_value(value, definition),
                "accent": accent_colors.get(definition.get("accent", "CYAN"), accent_colors.get("CYAN", CYAN)),
            }
        )
    return scorecard_cards


# --- Public activity aggregations for the web dashboard -------------------------
# COUNTS ONLY. The published profile_snapshot.json must stay name+metadata (never
# contents), so these reduce events/calendar to numbers — no repo names, URLs, or
# payloads ever reach the public JSON.
_WEB_EVENT_LABELS = {
    "PushEvent": "push", "PullRequestEvent": "pull request",
    "PullRequestReviewEvent": "pr review", "IssuesEvent": "issue",
    "IssueCommentEvent": "comment", "ReleaseEvent": "release", "CreateEvent": "create",
}


def _activity_timezone() -> tuple[Any, str]:
    name = activity_timezone_name()
    return _zone(name), name.rsplit("/", 1)[-1].replace("_", " ")


def _safe_iso_date(value: Any) -> str:
    """Return value iff it is a clean YYYY-MM-DD date, else '' — so no arbitrary
    string can ride into the public JSON via the calendar's only text field."""
    s = str(value or "")
    if len(s) == 10:
        try:
            date.fromisoformat(s)
            return s
        except ValueError:
            pass
    return ""


def _safe_count(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _public_contribution_calendar(calendar: Any) -> dict | None:
    """Trim the contribution calendar to date+count per day for the web grid.
    Every field is normalized (date validated, count coerced to a non-negative int)
    so the public JSON carries numbers + clean dates only."""
    if not isinstance(calendar, dict):
        return None
    weeks_out: list[list[dict]] = []
    for wk in calendar.get("weeks") or []:
        if not isinstance(wk, dict):
            continue
        days = [
            {"date": iso, "count": _safe_count(d.get("contributionCount"))}
            for d in (wk.get("contributionDays") or [])
            if isinstance(d, dict) and (iso := _safe_iso_date(d.get("date")))
        ]
        if days:
            weeks_out.append(days)
    if not weeks_out:
        return None
    try:
        total = int(calendar.get("totalContributions", 0) or 0)
    except (TypeError, ValueError):
        total = 0
    return {"total": total, "weeks": weeks_out}


def _activity_rhythm(events: list) -> dict | None:
    """Aggregate public events into a 7x24 weekday-hour matrix + event-type mix.
    Counts ONLY — no repo names/URLs/payloads reach the published JSON."""
    from collections import Counter

    tz, tz_label = _activity_timezone()
    matrix = [[0] * 24 for _ in range(7)]
    mix: Counter = Counter()
    total = 0
    for ev in events or []:
        if not isinstance(ev, dict):
            continue
        label = _WEB_EVENT_LABELS.get(_event_type(ev))
        ts = _event_created_at(ev)
        if not label or not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(tz)
        except ValueError:
            continue
        matrix[dt.weekday()][dt.hour] += 1
        mix[label] += 1
        total += 1
    if total == 0:
        return None
    return {"matrix": matrix, "event_mix": dict(mix.most_common(6)), "total": total, "timezone": tz_label}


def _build_dashboard_payload(
    *,
    now_utc: datetime,
    username: str,
    theme: dict[str, str],
    snapshot: Snapshot,
    snapshot_rows: list[SnapshotRow],
    snapshot_cards: list[dict[str, Any]],
    data_quality: DataQuality,
    scorecard: dict[str, Any],
    scorecard_cards: list[ScorecardCard],
    data_scope: DataScope,
    featured_repo_facts: list[dict[str, Any]],
    top_languages: list[dict[str, Any]],
    repo_overview_rows: list[dict[str, Any]],
    recent_created: list[dict[str, Any]],
    focus_now: list[dict[str, Any]],
    focus_next: list[dict[str, Any]],
    focus_shipped: list[dict[str, Any]],
    activity_feed: list[dict[str, Any]],
    release_list: list[dict[str, Any]],
    pr_list: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assemble the dashboard_data payload."""
    return {
        "generated_at": now_utc.isoformat().replace("+00:00", "Z"),
        "username": username,
        "dashboard_url": f"https://{username}.github.io/{username}/",
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


def compute_profile_model(
    collected: CollectedProfileData,
    logger=print,
    *,
    allow_network_calls: bool = True,
) -> dict[str, Any]:  # returns a dict matching the ProfileModel shape
    metric_observations = _validated_metric_observations(collected)
    repos = collected.repos
    events_observation = metric_observations.get("recent_public_events")
    observed_events = events_observation.get("value") if events_observation else None
    events = (
        list(observed_events)
        if isinstance(observed_events, (list, tuple))
        else collected.events
    )
    contribution_observation = metric_observations.get("last_year_contributions")
    if contribution_observation and contribution_observation.get("status") == "ok":
        contribution_value = contribution_observation.get("value")
        exact_contributions = (
            contribution_value.get("total")
            if isinstance(contribution_value, dict)
            else None
        )
        calendar = collected.calendar
    elif contribution_observation:
        exact_contributions = None
        calendar = None
    else:
        exact_contributions = collected.total_contributions
        calendar = collected.calendar
    repo_counts = collected.repo_counts

    public_nonfork_repos = [
        repo
        for repo in repos
        if isinstance(repo, dict) and repo.get("fork") is not True
    ]
    private_nonfork_repos = [
        repo
        for repo in collected.private_repos
        if isinstance(repo, dict) and repo.get("fork") is not True
    ]
    private_aggregate_status = _private_aggregate_quality(
        repo_counts,
        private_nonfork_repos,
    )
    family_statuses = _metric_family_statuses(
        repo_counts,
        public_nonfork_repos,
        private_nonfork_repos,
    )
    push_repos = [
        repository
        for repository in [*public_nonfork_repos, *private_nonfork_repos]
        if not is_self_repo(repository.get("name"))
    ]
    automation = _build_automation_summary(
        repo_counts, public_nonfork_repos, private_nonfork_repos
    )
    workflow = automation["combined"]
    family_statuses["automation"] = workflow["status"]
    workflow_display = automation_display(automation)
    language_bytes = _aggregate_language_bytes(
        public_nonfork_repos,
        private_nonfork_repos,
        fallback_public_language_bytes=collected.language_bytes,
    )

    now_utc = datetime.now(timezone.utc)
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)

    # --- language stats ---
    top_languages, lang_count, _total_language_bytes = _build_language_stats(repos, language_bytes)

    # --- PR & release stats ---
    pr_release = _build_pr_and_release_stats(
        events,
        repos,
        now_utc,
        allow_network_calls=allow_network_calls,
        observations=metric_observations,
    )
    prs_merged = pr_release["prs_merged"]
    prs_status = pr_release["prs_status"]
    prs_note = pr_release["prs_note"]
    releases_30d = pr_release["releases_30d"]
    releases_status = pr_release["releases_status"]
    releases_note = pr_release["releases_note"]
    avg_release_gap_days = pr_release["avg_release_gap_days"]

    # --- active repos (7d) ---
    seven_days_ago = now_utc - timedelta(days=7)
    active_repos_7d = 0
    for repo in push_repos:
        if is_self_repo(repo.get("name")):
            continue
        pushed = repo.get("pushed_at", "")
        if not pushed:
            continue
        try:
            pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        except ValueError:
            continue
        if pushed_dt >= seven_days_ago:
            active_repos_7d += 1

    # Aggregate values use retained paired facts; per-repo fallback is separate.
    repo_ci_lookup = _build_ci_quality(push_repos, allow_network_calls=allow_network_calls)
    ci_count_effective = workflow["configured_repos"]
    ci_coverage_pct = workflow["adoption_pct"]
    ci_quality = {
        "ci_status": "empty" if workflow["eligible_repos"] == 0 else {
            "exact": "ok", "partial": "partial", "unavailable": "unavailable",
        }[workflow["status"]],
        "ci_note": workflow_display["combined"]["qualification"],
    }

    # --- commit stats ---
    public_scope_commits, commits_status, commits_note = _build_commit_stats(
        collected,
        repos,
        allow_network_calls=allow_network_calls,
        observation=metric_observations.get("public_scope_commits"),
    )

    stars_per_public_repo = (total_stars / len(repos)) if repos else 0.0
    streak_days = _compute_current_streak_days(calendar, now_utc, _profile_today())

    # --- recent repos ---
    recent_repos, recent_commit_message_by_repo = _build_recent_repos(
        repos,
        seven_days_ago,
        collected.latest_push_message_by_repo,
        allow_network_calls,
        private_repos=collected.private_repos,
    )

    # --- spotlight ---
    spotlight_data = []
    for repo_name in FEATURED_REPOS:
        repo = next((item for item in collected.all_repos if item["name"] == repo_name), None)
        if not repo:
            continue
        weekly = []
        if allow_network_calls:
            weekly = gh.get_repo_commits_last_n_weeks(repo["owner"]["login"], repo["name"])
        has_ci = has_ci_workflow(repo, allow_network_calls=allow_network_calls)
        pushed_raw = repo.get("pushed_at") or ""
        status = "active"
        if pushed_raw:
            try:
                pushed_dt = datetime.fromisoformat(pushed_raw.replace("Z", "+00:00"))
                status = "active" if (now_utc - pushed_dt).days <= 30 else "maintained"
            except ValueError:
                status = "active"
        spotlight_data.append(
            {
                "name": repo["name"],
                "description": repo.get("description", ""),
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "html_url": repo.get("html_url", ""),
                "pushed_at": pushed_raw[:10],
                "pushed_ago": time_ago(pushed_raw) if pushed_raw else "",
                "status": status,
                "weekly_commits": weekly,
                "has_ci": has_ci,
            }
        )

    # --- scorecard ---
    engineering = _build_engineering_metrics(
        collected,
        push_repos,
        top_languages,
        now_utc,
        automation=automation,
    )
    if family_statuses["push"] == "unavailable":
        active_repos_7d = None
        engineering["median_days_since_push"] = None
        engineering["days_since_last_push"] = None
    if family_statuses["language"] == "unavailable":
        engineering["primary_lang_share_pct"] = None
        engineering["languages_over_5pct"] = None
    scorecard = {
        "releases_30d": releases_30d,
        "active_repos_7d": active_repos_7d,
        "avg_release_gap_days": avg_release_gap_days,
        "stars_per_public_repo": stars_per_public_repo,
        "ci_coverage_pct": ci_coverage_pct,
        "last_year_contributions": exact_contributions,
        "active_days_last_year": engineering["active_days_last_year"],
        "automation_workflows": engineering["automation_workflows"],
        "primary_lang_share_pct": engineering["primary_lang_share_pct"],
        "median_days_since_push": engineering["median_days_since_push"],
        "days_since_last_push": engineering["days_since_last_push"],
    }
    accent_colors = {
        "BLUE": BLUE,
        "CYAN": CYAN,
        "GREEN": GREEN,
        "ORANGE": ORANGE,
    }
    scorecard_cards = _build_scorecard_cards(scorecard, accent_colors)

    # --- repo overview ---
    repo_overview_rows, featured_repo_facts = _build_repo_overview_rows(
        push_repos,
        recent_commit_message_by_repo,
        collected.latest_push_message_by_repo,
        repo_ci_lookup,
    )

    # --- data scope ---
    public_inventory_status = _inventory_quality(
        repo_counts.get("public_owned_nonfork"), public_nonfork_repos
    )
    observed_public = any(
        not is_self_repo(repository.get("name"))
        for repository in public_nonfork_repos
    )
    observed_private = any(
        not is_self_repo(repository.get("name"))
        for repository in private_nonfork_repos
    )
    if not observed_public and not observed_private:
        if public_inventory_status == "exact" and private_aggregate_status == "exact":
            repos_included = "public + private observed, exact empty"
        else:
            repos_included = "repository observation unavailable"
    elif observed_public and observed_private:
        if public_inventory_status == "exact" and private_aggregate_status == "exact":
            repos_included = "public + private observed, exact"
        else:
            repos_included = "public + private observed, partial"
    elif observed_public:
        if private_aggregate_status == "exact":
            repos_included = "public observed, private exact empty"
        elif private_aggregate_status == "unavailable":
            repos_included = "public observed, private unavailable"
        else:
            repos_included = "public observed, private partial"
    else:
        public_observation = {
            "exact": "exact empty",
            "partial": "partial",
            "unavailable": "unavailable",
        }[public_inventory_status]
        repos_included = f"private observed, public {public_observation}"

    data_scope: DataScope = {
        "repos_included": repos_included,
        "activity_metric_scope": "GitHub contributionCalendar.totalContributions (last 12 months)",
        "public_owned_repos_total": repo_counts["public_owned_total"],
        "public_owned_forks_total": repo_counts["public_owned_forks"],
        "public_owned_nonfork_repos_total": repo_counts["public_owned_nonfork"],
        "private_owned_repos_total": repo_counts["private_owned"],
        "private_owned_nonfork_repos_total": repo_counts.get("private_owned_nonfork"),
    }
    metric_families = {
        "active_repos_7d": "push",
        "days_since_last_push": "push",
        "automation_repos": "automation",
        "automation_workflows": "automation",
        "ci_coverage_pct": "automation",
        "ci_repos": "automation",
        "top_languages": "language",
        "primary_lang_share_pct": "language",
        "languages_over_5pct": "language",
        "languages_count": "language",
    }
    metric_statuses = {
        metric: family_statuses[family]
        for metric, family in metric_families.items()
    }
    scope_by_status = {
        "exact": _ALL_OWNED_NONFORK_AGGREGATE_SCOPE,
        "partial": _INCOMPLETE_OWNED_NONFORK_SCOPE,
        "unavailable": _UNAVAILABLE_OWNED_NONFORK_SCOPE,
    }
    data_scope["metric_scopes"] = {
        metric: scope_by_status[metric_statuses[metric]]
        for metric in metric_families
    }

    # --- snapshot ---
    snapshot: Snapshot = _build_snapshot_dict(
        collected,
        repo_counts,
        total_stars,
        lang_count if family_statuses["language"] != "unavailable" else None,
        prs_merged, releases_30d, ci_count_effective, streak_days,
        public_scope_commits,
        exact_contributions,
    )

    # --- snapshot rows & cards ---
    snapshot_rows: list[SnapshotRow] = []
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

    # --- recent activity & focus ---
    recent_created = []
    for r in sorted(
        [
            r
            for r in [*public_nonfork_repos, *private_nonfork_repos]
            if not is_self_repo(r.get("name"))
        ],
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )[:10]:
        rr = dict(r)
        rr["latest_commit_message"] = safe_commit_headline(
            rr.get("latest_commit_message")
        )
        recent_created.append(rr)

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

    # --- data quality ---
    if events_observation is not None:
        events_status = str(events_observation.get("status"))
        events_note = (
            "Public event metadata observation complete."
            if events_status == "ok"
            else "Public event metadata is partial; repository push metadata remains merged."
        )
    else:
        events_status = "ok" if events else "limited"
        events_note = (
            "Public events feed available."
            if events
            else "No recent public events returned in this run; focus/feed use repo push fallbacks."
        )

    if contribution_observation is not None:
        contributions_status = str(contribution_observation.get("status"))
        contributions_note = (
            "Contribution calendar observation is current and complete."
            if contributions_status == "ok"
            else "Contribution total is retained from noncurrent evidence."
        )
    elif exact_contributions is not None:
        contributions_status = "ok"
        contributions_note = "Contribution total available from the collected profile data."
    else:
        contributions_status = "unavailable"
        contributions_note = "Contribution total unavailable for this run."

    metric_provenance = {
        metric_id: _observation_provenance(observation)
        for metric_id, observation in metric_observations.items()
    }
    non_exact_metrics = {}
    for metric_id, observation in metric_observations.items():
        carrier = _non_exact_carrier(observation)
        if carrier is not None:
            non_exact_metrics[metric_id] = carrier
    publication_hold_reasons = (
        ("NONCURRENT_CONTRIBUTIONS",)
        if contribution_observation is not None
        and contribution_observation.get("status") != "ok"
        else ()
    )
    data_quality: DataQuality = {
        "ci_status": ci_quality["ci_status"],
        "ci_note": ci_quality["ci_note"],
        "commits_status": commits_status,
        "commits_note": commits_note,
        "releases_status": releases_status,
        "releases_note": releases_note,
        "prs_status": prs_status,
        "prs_note": prs_note,
        "contributions_status": contributions_status,
        "contributions_note": contributions_note,
        "events_status": events_status,
        "events_note": events_note,
        "private_aggregate_status": private_aggregate_status,
        "metric_statuses": metric_statuses,
        "metric_provenance": metric_provenance,
        "non_exact_metrics": non_exact_metrics,
        "publication_hold_reasons": publication_hold_reasons,
        # Coarse auth state only — the precise token mode is internal diagnostics
        # and must never appear on the public profile / published snapshot.
        "token_mode": (
            "authenticated"
            if collected.token_mode not in {"none", "unauthenticated", ""}
            else "unauthenticated"
        ),
    }

    # --- theme ---
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

    # --- dashboard payload ---
    dashboard_data = _build_dashboard_payload(
        now_utc=now_utc,
        username=USERNAME,
        theme=theme,
        snapshot=snapshot,
        snapshot_rows=snapshot_rows,
        snapshot_cards=snapshot_cards,
        data_quality=data_quality,
        scorecard=scorecard,
        scorecard_cards=scorecard_cards,
        data_scope=data_scope,
        featured_repo_facts=featured_repo_facts,
        top_languages=top_languages,
        repo_overview_rows=repo_overview_rows,
        recent_created=recent_created,
        focus_now=focus_now,
        focus_next=focus_next,
        focus_shipped=focus_shipped,
        activity_feed=activity_feed,
        release_list=release_list,
        pr_list=pr_list,
    )
    dashboard_data["engineering"] = engineering
    dashboard_data["automation"] = automation
    dashboard_data["automation_display"] = workflow_display
    calendar_public = _public_contribution_calendar(calendar)
    if calendar_public:
        dashboard_data["contribution_calendar"] = calendar_public
    rhythm = _build_contribution_rhythm(collected)
    dashboard_data["contribution_rhythm"] = rhythm
    dashboard_data["contribution_rhythm_display"] = contribution_rhythm_display(rhythm)

    return {
        "now_utc": now_utc,
        "contribution_rhythm": rhythm,
        "automation": automation,
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
        "language_bytes": language_bytes,
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
        "engineering": engineering,
        "token_mode": collected.token_mode,
        "cache_mode": collected.cache_mode,
        "publication_hold_reasons": publication_hold_reasons,
    }
