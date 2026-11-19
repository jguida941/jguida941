"""Collect profile data from GitHub APIs."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.github import github_client as gh
from scripts.github.activity_observations import collect_activity_observations
from scripts.github.actions_audit import collect_profile_ci_runs, collect_public_ci_timeline
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
    activity_observations: dict[str, Any] = field(default_factory=dict)
    inventory_evidence: dict[str, Any] = field(default_factory=dict)
    collection_started_at: str | None = None
    ci_execution_observation: dict[str, Any] = field(default_factory=dict)
    ci_timeline_observation: dict[str, Any] = field(default_factory=dict)


def _repository_locator(row: dict[str, Any]) -> str:
    """Validate provider locators before they become request paths or identities."""
    if not isinstance(row, dict):
        raise ValueError("repository identity requires an object")
    owner = row.get("owner")
    login = owner.get("login") if isinstance(owner, dict) else None
    name = row.get("name")
    if any(not isinstance(part, str) or part in (".", "..")
           or not re.fullmatch(r"[A-Za-z0-9_.-]+", part) for part in (login, name)):
        raise ValueError("repository identity requires a valid owner and name")
    locator = f"{login}/{name}"
    full_name = row.get("full_name")
    if full_name is not None and (not isinstance(full_name, str)
                                  or full_name.casefold() != locator.casefold()):
        raise ValueError("repository identity conflicts with its full_name")
    return locator


def _positive_repository_id(row: dict[str, Any]) -> int | None:
    identity = row.get("id")
    return identity if type(identity) is int and identity > 0 else None


def _collect_repository_inventory(public: list[dict[str, Any]],
                                  private: list[dict[str, Any]],
                                  counts: dict[str, int | None]) -> dict[str, Any]:
    """Resolve one explicitly scoped inventory; locators are aliases, not owners.

    Preferred GraphQL discovery omits stable IDs. A fresh REST repository read
    supplies both that identity and its current owner, including after transfers.
    The configured organization is a target-owned scope, never membership search.
    Personal metrics below are projections of this inventory, not union counts.
    """
    owners = sorted({gh.USERNAME.casefold(), "semverity-labs"})
    observations = [*public, *private]
    issues: list[dict[str, str]] = []
    personal_public_sources = [_repository_locator(row).casefold() for row in public
                              if row.get("private") is False and row.get("fork") is False]
    public_count = counts.get("public_owned_nonfork")
    personal_public_complete = type(public_count) is int and public_count == len(personal_public_sources)
    for count, rows in ((counts.get("public_owned_total"), public),
                        (counts.get("private_owned_nonfork"), private)):
        if type(count) is not int or count != len(rows):
            issues.append({"owner": gh.USERNAME, "reason": "personal_discovery_incomplete"})
    try:
        organization = gh.paginated_get("orgs/semverity-labs/repos", {"type": "all"}, fresh=True)
        if not isinstance(organization, list):
            raise ValueError("organization repository discovery is not a list")
        observations.extend(organization)
        # A completed page walk enumerates repositories this credential can see.
        # The list-only provider supplies no proof of full organization visibility.
        issues.append({"owner": "semverity-labs", "reason": "organization_coverage_unknown"})
    except (RuntimeError, ValueError, gh.requests.RequestException):
        issues.append({"owner": "semverity-labs", "reason": "organization_unavailable"})

    resolved: dict[str, dict[str, Any] | None] = {}
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    current_locators: dict[str, int | None] = {}
    for observed in sorted(observations, key=lambda row: _repository_locator(row).casefold()):
        source_locator = _repository_locator(observed)
        if source_locator.split("/")[0].casefold() not in owners:
            raise ValueError("repository discovery owner is outside the selected scope")
        source_key = source_locator.casefold()
        if source_key not in resolved:
            try:
                response = gh._request_with_retry(f"{gh.API}/repos/{source_locator}")
                payload = response.json() if response.status_code == 200 else None
                if not isinstance(payload, dict):
                    payload = None
            except (RuntimeError, ValueError, gh.requests.RequestException):
                payload = None
            resolved[source_key] = payload
        payload = resolved[source_key]
        if payload is None:
            issues.append({"locator": source_locator, "reason": "current_metadata_unavailable"})
            if source_key in personal_public_sources:
                personal_public_complete = False
            continue
        locator = _repository_locator(payload)
        if locator.split("/")[0].casefold() not in owners:
            # A transfer outside the explicitly selected owners leaves the inventory.
            issues.append({"locator": source_locator, "reason": "current_owner_outside_scope"})
            continue
        identity = _positive_repository_id(payload)
        prior_id = _positive_repository_id(observed)
        if prior_id is not None and identity is not None and prior_id != identity:
            raise ValueError("repository identity mismatch at a reused or conflicting locator")
        try:
            gh._validate_rest_repository_identities([payload])
        except RuntimeError as exc:
            raise ValueError("repository current identity is inconsistent: " + str(exc)) from exc
        current = dict(payload)
        # Only enrich the same current locator. Transfer aliases cannot overwrite
        # fresh metadata with stale language, workflow, or commit observations.
        if source_key == locator.casefold():
            for field in ("language_bytes", "language_bytes_complete", "has_ci_workflows",
                          "workflow_file_count", "latest_commit_message"):
                if field in observed:
                    current.setdefault(field, observed[field])
        current["full_name"] = locator
        current["html_url"] = f"https://github.com/{locator}"
        current["identity_qualification"] = "provider_id" if identity else "locator_only"
        if identity is None:
            current.pop("id", None)
            issues.append({"locator": locator, "reason": "stable_id_unavailable"})
            if source_key in personal_public_sources:
                personal_public_complete = False
        key = ("github", str(identity)) if identity else ("locator", locator.casefold())
        if locator.casefold() in current_locators and current_locators[locator.casefold()] != identity:
            raise ValueError("conflicting repository identities share a current locator")
        current_locators[locator.casefold()] = identity
        previous = rows.get(key)
        if previous is not None:
            if (previous["full_name"].casefold(), previous["private"], previous["fork"]) != (
                    locator.casefold(), payload["private"], payload["fork"]):
                raise ValueError("conflicting current repository owner, locator or visibility")
            previous["aliases"] = sorted(set(previous["aliases"]) | {source_locator}, key=str.casefold)
            # A legacy alias may sort first. Later current-locator enrichment
            # still belongs to this same repository and must not disappear.
            if source_key == locator.casefold():
                for field in ("language_bytes", "language_bytes_complete", "has_ci_workflows",
                              "workflow_file_count", "latest_commit_message"):
                    if field in current:
                        previous.setdefault(field, current[field])
        else:
            current["aliases"] = [source_locator]
            rows[key] = current
    inventory = sorted(rows.values(), key=lambda row: row["full_name"].casefold())
    return {"schema": "profile-repository-inventory/v1", "owners": owners,
            "status": ("partial" if inventory else "unavailable") if issues else "ok",
            "complete": not issues, "rows": inventory, "issues": issues,
            "personal_public_complete": personal_public_complete,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "identity_basis": "canonical_rest_repository_id_with_qualified_locator_fallback"}


def collect_profile_data(logger=print) -> CollectedProfileData:
    collection_started_at = datetime.now(timezone.utc).isoformat()
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
    contribution_observation = gh.get_default_contribution_calendar_observation()
    profile_contributions_observation = gh.profile_contributions_from_calendar(contribution_observation)
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
            logger("  n/a GitHub contributions (calendar unavailable for this run)")
    else:
        logger(f"  {total_contributions} GitHub contributions")

    # Collect private-owned non-fork repository metadata for the same profile
    # surfaces and aggregate families as public repository metadata.
    private_repos = gh.get_private_repos()
    if private_repos:
        logger(f"  {len(private_repos)} private non-fork repos observed for profile metrics")

    # Selection gets fresh discovery hints; other metrics retain their own caches.
    activity_observed_at = datetime.now(timezone.utc)
    try:
        activity_repos = gh.get_repos(include_forks=False, fresh=True)
        activity_all_public = gh.get_repos(include_forks=True, fresh=True)
        activity_private = gh.get_private_repos(fresh=True)
        activity_counts = gh.get_owned_repo_scope_counts(fresh=True)
        inventory_fresh = True
    except (RuntimeError, ValueError):
        activity_repos, activity_private, activity_counts = repos, private_repos, repo_counts
        activity_all_public = all_repos
        inventory_fresh = False
    inventory_evidence = {
        "fresh": inventory_fresh, "observed_at": datetime.now(timezone.utc).isoformat(),
        "counts": dict(activity_counts), "public_repos": activity_repos,
        "all_public_repos": activity_all_public,
        "personal_public_complete": True,
    }
    activity_observations = collect_activity_observations(
        activity_repos, activity_private, activity_counts,
        observed_at=activity_observed_at, inventory_fresh=inventory_fresh,
    )

    # This is a separate, bounded execution sample for this public profile repo.
    # It is not inferred from account-wide workflow configuration counts.
    from scripts.core.config import USERNAME
    ci_execution_observation = collect_profile_ci_runs(f"{USERNAME}/{USERNAME}")
    # Resolve the same admitted personal and organization metadata used by
    # the private source. This CI-only inventory does not change other metrics.
    ci_repository_inventory = _collect_repository_inventory(
        activity_all_public, activity_private, activity_counts)
    ci_timeline_observation = collect_public_ci_timeline(
        repos, USERNAME, repository_inventory=ci_repository_inventory)

    return CollectedProfileData(
        inventory_evidence=inventory_evidence,
        collection_started_at=collection_started_at,
        activity_observations=activity_observations,
        ci_execution_observation=ci_execution_observation,
        ci_timeline_observation=ci_timeline_observation,
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
            "github_profile_contributions": profile_contributions_observation,
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
        **{key: value[key] for key in ("calendar_start", "calendar_end") if key in value},
        "weeks": [
            {"contributionDays": sorted(weeks[key], key=lambda row: row["date"])}
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
