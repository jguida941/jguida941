"""Collect profile data from GitHub APIs."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.github import github_client as gh
from scripts.core.runtime_env import cache_mode_from_env, token_mode_from_env


def detect_token_mode() -> str:
    return token_mode_from_env()


def detect_cache_mode() -> dict[str, object]:
    return cache_mode_from_env()


@dataclass(frozen=True)
class CollectedProfileData:
    repo_counts: dict[str, int | None]
    repos: list[dict[str, Any]]
    all_repos: list[dict[str, Any]]
    language_bytes: dict[str, int]
    events: list[dict[str, Any]]
    latest_push_message_by_repo: dict[str, str]
    public_scope_commits: int | None
    ci_count_probe: int
    calendar: dict[str, Any] | None
    total_contributions: int | None
    token_mode: str
    cache_mode: dict[str, Any]
    private_repos: list[dict[str, Any]] = field(default_factory=list)
    metric_observations: dict[str, dict[str, Any]] = field(default_factory=dict)


def collect_profile_data(logger=print) -> CollectedProfileData:
    logger("\n[1/7] Fetching repo scope counts...")
    repo_counts = gh.get_owned_repo_scope_counts()
    # Older cache entries predate the non-fork private scope. Its absence is
    # unknown evidence, never permission to substitute the all-private count.
    repo_counts.setdefault("private_owned_nonfork", None)
    logger(
        "  Scope totals:"
        f" public non-fork={repo_counts['public_owned_nonfork']},"
        f" public forks={repo_counts['public_owned_forks']},"
        f" public total={repo_counts['public_owned_total']},"
        f" private owned={repo_counts['private_owned'] if repo_counts['private_owned'] is not None else 'n/a'},"
        " private non-fork="
        f"{repo_counts['private_owned_nonfork'] if repo_counts['private_owned_nonfork'] is not None else 'n/a'}"
    )

    logger("[2/7] Fetching repos...")
    repos = gh.get_repos(include_forks=False)
    all_repos = gh.get_repos(include_forks=True)
    # Keep scope counts and fetched repo lists consistent when the scope endpoint degrades.
    if repos and int(repo_counts.get("public_owned_nonfork", 0) or 0) == 0:
        repo_counts["public_owned_nonfork"] = len(repos)
    if all_repos and int(repo_counts.get("public_owned_total", 0) or 0) == 0:
        repo_counts["public_owned_total"] = len(all_repos)
    if repo_counts.get("public_owned_total") is not None and repo_counts.get("public_owned_nonfork") is not None:
        repo_counts["public_owned_forks"] = max(
            0,
            int(repo_counts["public_owned_total"]) - int(repo_counts["public_owned_nonfork"]),
        )
    previous_snapshot = _read_previous_snapshot()
    if repo_counts.get("private_owned") is None:
        previous_private = _prev_int(previous_snapshot, "private_owned_repos")
        if previous_private is not None:
            repo_counts["private_owned"] = previous_private
    logger(
        f"  Found {len(repos)} public non-fork repos "
        f"({len(all_repos)} public owned total, {repo_counts['public_owned_forks']} forks)"
    )

    logger("[3/7] Fetching language data...")
    language_bytes = gh.get_all_languages(repos)
    lang_count = len([lang for lang, bytes_ in language_bytes.items() if bytes_ > 0])
    logger(f"  {lang_count} languages across all repos")

    logger("[4/7] Fetching events...")
    events_observation = gh.get_events_observation()
    events_value = events_observation.get("value")
    events = list(events_value) if isinstance(events_value, (list, tuple)) else []
    logger(f"  {len(events)} recent events")

    latest_push_message_by_repo: dict[str, str] = {}
    for event in events:
        event_type = event.get("event_type", event.get("type"))
        if event_type != "PushEvent":
            continue
        repo_full_name = event.get("repo_full_name")
        if not repo_full_name:
            repo_full_name = event.get("repo", {}).get("name", "")
        if not repo_full_name or repo_full_name in latest_push_message_by_repo:
            continue
        headlines = event.get("commit_headlines")
        if isinstance(headlines, (list, tuple)):
            message = str(headlines[-1]).strip() if headlines else ""
        else:
            commits = event.get("payload", {}).get("commits", [])
            message = (
                commits[-1].get("message", "").split("\n")[0].strip()
                if commits
                else ""
            )
        if message:
            latest_push_message_by_repo[repo_full_name] = message

    logger("[5/7] Fetching public repo commit count...")
    commits_observation = gh.get_total_commits_observation(
        repos,
        use_global_fallback=True,
    )
    public_scope_commits = (
        commits_observation.get("value")
        if commits_observation.get("status") == "ok"
        else None
    )
    if public_scope_commits is None:
        logger("  n/a exact public-scope commits (non-exact evidence retained separately)")
    else:
        logger(f"  {public_scope_commits} public-scope commits")

    releases_observation = gh.get_releases_last_n_days_observation(repos, days=30)
    releases_observation = _release_events_fallback_observation(
        releases_observation,
        events_observation,
        events,
    )
    prs_observation = gh.get_merged_prs_last_n_days_observation(days=365)

    logger("[6/7] Counting CI/CD pipelines...")
    ci_count_probe = gh.get_repos_with_ci(repos)
    logger(f"  Probe found {ci_count_probe} repos with CI/CD")

    logger("[7/7] Fetching contribution calendar...")
    contribution_observation = gh.get_contribution_calendar_observation()
    contribution_value = contribution_observation.get("value")
    calendar = _calendar_from_observation_value(contribution_value)
    total_contributions = (
        contribution_value.get("total")
        if contribution_observation.get("status") == "ok"
        and isinstance(contribution_value, dict)
        else None
    )
    if total_contributions is None:
        previous_contribution = _previous_contribution_observation(previous_snapshot)
        if previous_contribution is not None:
            contribution_observation = previous_contribution
            total_contributions = previous_contribution["value"]
            logger(f"  retained previous contribution observation: {total_contributions}")
        else:
            logger("  n/a contributions in the last 12 months (calendar unavailable for this run)")
    else:
        logger(f"  {total_contributions} contributions in the last 12 months")

    # Collect private-owned non-fork repository metadata for the same profile
    # surfaces and aggregate families as public repository metadata.
    private_repos = gh.get_private_repos()
    if private_repos:
        logger(f"  {len(private_repos)} private non-fork repos observed for profile metrics")

    return CollectedProfileData(
        repo_counts=repo_counts,
        repos=repos,
        all_repos=all_repos,
        language_bytes=language_bytes,
        events=events,
        latest_push_message_by_repo=latest_push_message_by_repo,
        public_scope_commits=public_scope_commits,
        ci_count_probe=ci_count_probe,
        calendar=calendar,
        total_contributions=total_contributions,
        token_mode=detect_token_mode(),
        cache_mode=detect_cache_mode(),
        private_repos=private_repos,
        metric_observations={
            "public_scope_commits": commits_observation,
            "last_year_contributions": contribution_observation,
            "releases_30d": releases_observation,
            "prs_merged": prs_observation,
            "recent_public_events": events_observation,
        },
    )


def _read_previous_snapshot() -> dict[str, Any] | None:
    """Return the most-trustworthy complete previous profile payload.

    Reads ``site/data/profile_snapshot.json`` from both the working tree and
    ``git show HEAD:...`` so a degraded run can preserve last-known-good
    user-specific metrics instead of regressing them to zero/n-a.
    """
    snapshot_path = Path("site/data/profile_snapshot.json")
    payloads: list[dict[str, Any]] = []
    if snapshot_path.exists():
        try:
            loaded = json.loads(snapshot_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                payloads.append(loaded)
        except (OSError, ValueError):
            pass

    try:
        result = subprocess.run(
            ["git", "show", "HEAD:site/data/profile_snapshot.json"],
            check=True,
            text=True,
            capture_output=True,
        )
        loaded = json.loads(result.stdout)
        if isinstance(loaded, dict):
            payloads.append(loaded)
    except (OSError, ValueError, subprocess.CalledProcessError):
        pass

    for payload in payloads:
        if isinstance(payload.get("snapshot"), dict):
            return payload
    return None


def _prev_int(snapshot: dict[str, Any] | None, key: str) -> int | None:
    """Return a non-negative int from a previous snapshot dict, else None."""
    if not isinstance(snapshot, dict):
        return None
    snapshot_values = snapshot.get("snapshot")
    if isinstance(snapshot_values, dict):
        snapshot = snapshot_values
    try:
        parsed = int(snapshot.get(key))
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _read_previous_private_owned_count() -> int | None:
    """Back-compat: last known private-owned repo count from snapshot output."""
    return _prev_int(_read_previous_snapshot(), "private_owned_repos")


def _calendar_from_observation_value(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict) or not isinstance(value.get("days"), (list, tuple)):
        return None
    weeks: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for day in value["days"]:
        if not isinstance(day, dict):
            return None
        try:
            parsed = datetime.strptime(day["date"], "%Y-%m-%d")
            count = int(day["count"])
        except (KeyError, TypeError, ValueError):
            return None
        if count < 0:
            return None
        iso_year, iso_week, _ = parsed.isocalendar()
        weeks.setdefault((iso_year, iso_week), []).append(
            {
                "date": day["date"],
                "contributionCount": count,
                "weekday": parsed.weekday(),
            }
        )
    try:
        total = int(value["total"])
    except (KeyError, TypeError, ValueError):
        return None
    if total < 0:
        return None
    return {
        "totalContributions": total,
        "weeks": [
            {"contributionDays": weeks[key]}
            for key in sorted(weeks)
        ],
    }


def _parseable_iso(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return value


def _previous_contribution_observation(
    previous_payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    value = _prev_int(previous_payload, "last_year_contributions")
    if value is None or not isinstance(previous_payload, dict):
        return None
    previous_provenance = (
        previous_payload.get("data_quality", {})
        .get("metric_provenance", {})
        .get("last_year_contributions", {})
    )
    if not isinstance(previous_provenance, dict):
        previous_provenance = {}
    observed_at = _parseable_iso(previous_provenance.get("observed_at"))
    if observed_at is None:
        observed_at = _parseable_iso(previous_payload.get("generated_at"))
    if observed_at is None:
        return None
    window_start = _parseable_iso(previous_provenance.get("window_start"))
    window_end = _parseable_iso(previous_provenance.get("window_end"))
    if (window_start is None) != (window_end is None):
        window_start = None
        window_end = None
    observation = {
        "schema": "profile-provider-observation/v1",
        "metric_id": "last_year_contributions",
        "source_metric_id": "previous_profile_snapshot_contributions",
        "value": value,
        "status": "fallback",
        "complete": True,
        "population_id": "github-contribution-calendar-visible-to-provider",
        "population_signature": None,
        "window_start": window_start,
        "window_end": window_end,
        "observed_at": observed_at,
        "source_id": "previous_profile_snapshot",
        "source_mode": "previous_snapshot",
        "completion_reason": "previous_snapshot",
    }
    return observation if gh.validate_provider_observation(observation) else None


def _release_events_fallback_observation(
    release_observation: dict[str, Any],
    events_observation: dict[str, Any],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    if release_observation.get("status") == "ok":
        return release_observation
    if events_observation.get("status") != "ok":
        return release_observation
    window_start = release_observation.get("window_start")
    window_end = release_observation.get("window_end")
    observed_at = events_observation.get("observed_at")
    if not all(isinstance(value, str) for value in (window_start, window_end, observed_at)):
        return release_observation
    try:
        start = datetime.fromisoformat(window_start.replace("Z", "+00:00"))
        end = datetime.fromisoformat(window_end.replace("Z", "+00:00"))
    except ValueError:
        return release_observation
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    total = 0
    for event in events:
        event_type = event.get("event_type", event.get("type"))
        if event_type != "ReleaseEvent":
            continue
        occurred_at = event.get("occurred_at", event.get("created_at"))
        if not isinstance(occurred_at, str):
            continue
        try:
            occurred = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        if occurred.tzinfo is None:
            occurred = occurred.replace(tzinfo=timezone.utc)
        if start <= occurred <= end:
            total += 1
    fallback = {
        "schema": "profile-provider-observation/v1",
        "metric_id": "releases_30d",
        "source_metric_id": "public_release_events",
        "value": total,
        "status": "fallback",
        "complete": True,
        "population_id": "public-user-events-feed",
        "population_signature": None,
        "window_start": window_start,
        "window_end": window_end,
        "observed_at": observed_at,
        "source_id": "github_rest_public_events",
        "source_mode": "fallback",
        "completion_reason": "different_metric_fallback",
    }
    return fallback if gh.validate_provider_observation(fallback) else release_observation
