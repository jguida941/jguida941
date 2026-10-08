"""GitHub API wrapper - facade module.

All public functions are re-exported from focused sub-modules or defined
here (domain aggregation).  Import from this module for backward
compatibility.
"""

import json
import os
import re
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests
from scripts.core.runtime_env import token_mode_from_env

# ── sub-module imports ───────────────────────────────────────────────
from scripts.core.settings import Settings  # noqa: F401
from scripts.github.github_cache import read_cache, write_cache  # noqa: F401
from scripts.github.github_transport import (  # noqa: F401
    request_with_retry,
    request_public_with_retry,
)
from scripts.github.github_graphql import (  # noqa: F401
    graphql_query,
    last_query_oauth_scopes,
    last_query_used_fallback_token,
)

# ── module-level settings (backward compat) ──────────────────────────
_settings = Settings.from_env()

CACHE_DIR: Path = _settings.cache_dir
CACHE_TTL_SECONDS: int = _settings.cache_ttl_seconds
BYPASS_CACHE: bool = _settings.bypass_cache
TOKEN: str = _settings.token
USERNAME: str = _settings.username
API: str = "https://api.github.com"
GRAPHQL: str = "https://api.github.com/graphql"


# ── thin internal wrappers (keep old call-sites identical) ───────────

def _headers():
    from scripts.github.github_transport import _auth_headers
    return _auth_headers(_settings)


def _cache_path(key: str) -> Path:
    from scripts.github.github_cache import _cache_path as _cp
    return _cp(key, _settings.cache_dir)


def _get_cached(key: str):
    return read_cache(key, _settings)


def _set_cached(key: str, data):
    write_cache(key, data, _settings)


def _request_with_retry(url, headers=None, params=None, max_retries=3):
    return request_with_retry(
        url, _settings, headers=headers, params=params, max_retries=max_retries,
    )


def _request_public_with_retry(url, params=None, max_retries=2):
    return request_public_with_retry(url, params=params, max_retries=max_retries)


def _graphql_query(query: str, variables: dict) -> dict | None:
    return graphql_query(query, variables, _settings)


# ── private helpers (domain logic, kept in facade) ───────────────────

def _profile_timezone():
    tz_name = os.environ.get("PROFILE_TIMEZONE", "America/New_York").strip() or "America/New_York"
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return timezone.utc


def _calendar_window(days: int) -> tuple[datetime, datetime, str]:
    window_days = max(1, int(days))
    tz = _profile_timezone()
    now_local = datetime.now(tz)
    end_local = now_local
    start_local = (now_local - timedelta(days=window_days - 1)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return (
        start_local.astimezone(timezone.utc),
        end_local.astimezone(timezone.utc),
        now_local.date().isoformat(),
    )


def _parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


_OBSERVATION_KEYS = {
    "schema",
    "metric_id",
    "source_metric_id",
    "value",
    "status",
    "complete",
    "population_id",
    "population_signature",
    "window_start",
    "window_end",
    "observed_at",
    "source_id",
    "source_mode",
    "completion_reason",
}
_OBSERVATION_STATUSES = {"ok", "partial", "fallback", "unavailable"}
_OBSERVATION_SOURCE_MODES = {"live", "cache", "fallback", "previous_snapshot"}
_REPO_USER_COMMIT_CACHE_SCHEMA = "repo-user-commit-count/v1"
_EVENT_TYPES = {
    "PushEvent",
    "PullRequestEvent",
    "ReleaseEvent",
    "IssuesEvent",
    "PullRequestReviewEvent",
    "IssueCommentEvent",
}
_EVENT_BASE_KEYS = {
    "event_id",
    "event_type",
    "repo_full_name",
    "repo_url",
    "actor_login",
    "occurred_at",
    "is_private",
    "source_id",
    "evidence_status",
}
_EVENT_VARIANT_KEYS = {
    "PushEvent": {"commit_headlines"},
    "PullRequestEvent": {"action", "number", "title", "state", "merged", "url"},
    "ReleaseEvent": {"action", "tag_name", "url"},
    "IssuesEvent": {"action", "number", "title", "state", "url"},
    "PullRequestReviewEvent": {"action", "number", "url"},
    "IssueCommentEvent": {"action", "number", "url"},
}


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _is_nonnegative_int(value) -> bool:
    return type(value) is int and value >= 0


def _safe_summary(value, *, first_line: bool = False) -> str:
    if not isinstance(value, str):
        return ""
    text = value.splitlines()[0] if first_line else value
    text = "".join(" " if ord(char) < 32 or 127 <= ord(char) <= 159 else char for char in text)
    return " ".join(text.split())[:200]


def _valid_event_metadata_row(row, *, evidence_status: str) -> bool:
    if type(row) is not dict:
        return False
    event_type = row.get("event_type")
    variant_keys = _EVENT_VARIANT_KEYS.get(event_type)
    if variant_keys is None or set(row) != _EVENT_BASE_KEYS | variant_keys:
        return False
    event_id = row.get("event_id")
    repo_full_name = row.get("repo_full_name")
    repo_url = row.get("repo_url")
    actor_login = row.get("actor_login")
    if type(event_id) is not str or not event_id:
        return False
    if (
        type(repo_full_name) is not str
        or repo_full_name.count("/") != 1
        or any(not part for part in repo_full_name.split("/"))
    ):
        return False
    if repo_url != f"https://github.com/{repo_full_name}":
        return False
    if actor_login is not None and type(actor_login) is not str:
        return False
    if _parse_iso_datetime(row.get("occurred_at")) is None:
        return False
    if row.get("is_private") is not False:
        return False
    if row.get("source_id") != "github_rest_public_events":
        return False
    if row.get("evidence_status") != evidence_status:
        return False

    if event_type == "PushEvent":
        headlines = row.get("commit_headlines")
        if type(headlines) not in {list, tuple}:
            return False
        return all(
            type(headline) is str
            and bool(headline)
            and len(headline) <= 200
            and headline == _safe_summary(headline)
            for headline in headlines
        )

    action_sets = {
        "PullRequestEvent": {"opened", "closed", "reopened", "synchronize"},
        "ReleaseEvent": {"published", "released", "created", "edited", "deleted", "prereleased"},
        "IssuesEvent": {
            "opened", "edited", "deleted", "transferred", "pinned", "unpinned",
            "closed", "reopened", "assigned", "unassigned", "labeled", "unlabeled",
            "locked", "unlocked", "milestoned", "demilestoned",
        },
        "PullRequestReviewEvent": {"created", "edited", "dismissed"},
        "IssueCommentEvent": {"created", "edited", "deleted"},
    }
    if row.get("action") not in action_sets[event_type]:
        return False
    if event_type in {"PullRequestEvent", "IssuesEvent"}:
        if not _is_nonnegative_int(row.get("number")) or row.get("number") < 1:
            return False
        if row.get("state") not in {"open", "closed"}:
            return False
        title = row.get("title")
        if type(title) is not str or len(title) > 200 or title != _safe_summary(title):
            return False
    if event_type in {"PullRequestReviewEvent", "IssueCommentEvent"}:
        if not _is_nonnegative_int(row.get("number")) or row.get("number") < 1:
            return False
    if event_type == "PullRequestEvent" and type(row.get("merged")) is not bool:
        return False
    if event_type == "ReleaseEvent":
        tag = row.get("tag_name")
        if type(tag) is not str or len(tag) > 200 or tag != _safe_summary(tag):
            return False
    url = row.get("url")
    return type(url) is str and url.startswith(f"https://github.com/{repo_full_name}/")


def _valid_contribution_value(value) -> bool:
    if type(value) is not dict or set(value) != {"total", "days"}:
        return False
    if not _is_nonnegative_int(value.get("total")):
        return False
    days = value.get("days")
    if type(days) not in {list, tuple}:
        return False
    for day in days:
        if type(day) is not dict or set(day) != {"date", "count"}:
            return False
        try:
            datetime.strptime(day.get("date", ""), "%Y-%m-%d")
        except (TypeError, ValueError):
            return False
        if not _is_nonnegative_int(day.get("count")):
            return False
    return True


def validate_provider_observation(observation: dict) -> bool:
    """Validate the closed provider observation union.

    The accepted shapes contain only aggregate values or canonical metadata
    rows.  Raw provider payloads and open-ended extra keys are rejected before
    collection or publication can treat them as profile facts.
    """
    if type(observation) is not dict or set(observation) != _OBSERVATION_KEYS:
        return False
    if observation.get("schema") != "profile-provider-observation/v1":
        return False
    metric_id = observation.get("metric_id")
    source_metric_id = observation.get("source_metric_id")
    status = observation.get("status")
    complete = observation.get("complete")
    source_mode = observation.get("source_mode")
    reason = observation.get("completion_reason")
    if status not in _OBSERVATION_STATUSES or type(complete) is not bool:
        return False
    if source_mode not in _OBSERVATION_SOURCE_MODES:
        return False
    if type(observation.get("population_id")) is not str or not observation["population_id"]:
        return False
    signature = observation.get("population_signature")
    if signature is not None and (type(signature) is not str or not signature):
        return False
    for key in ("window_start", "window_end", "observed_at"):
        value = observation.get(key)
        if value is not None and (type(value) is not str or _parse_iso_datetime(value) is None):
            return False

    if status == "ok":
        if complete is not True:
            return False
        if source_mode == "live":
            if reason == "same_scope_cache":
                return False
        elif source_mode == "cache":
            if reason != "same_scope_cache":
                return False
        else:
            return False
    if status == "partial" and complete is not False:
        return False
    if status == "fallback" and complete is not True:
        return False
    if status == "unavailable":
        if complete is not False or observation.get("value") is not None:
            return False
        if reason not in {"unavailable", "component_unavailable"}:
            return False
        unavailable_specs = {
            "public_scope_commits": (
                "owned_public_nonfork_authored_commits",
                "owned-public-nonfork-repositories",
                "github_rest_repo_commits",
                False,
                True,
            ),
            "last_year_contributions": (
                "github_contribution_calendar_total_and_days",
                "github-contribution-calendar-visible-to-provider",
                "github_graphql_contribution_calendar",
                True,
                False,
            ),
            "releases_30d": (
                "owned_public_nonfork_releases",
                "owned-public-nonfork-repositories",
                "github_rest_repo_releases",
                True,
                True,
            ),
            "prs_merged": (
                "merged_prs_primary_visible_population",
                "owned-repositories-visible-to-primary-pr-search",
                "github_rest_merged_pr_search_primary",
                True,
                False,
            ),
            "recent_public_events": (
                "github_public_event_metadata_rows",
                "public-user-events-feed",
                "github_rest_public_events",
                False,
                True,
            ),
        }
        spec = unavailable_specs.get(metric_id)
        if spec is None:
            return False
        expected_source, expected_population, expected_source_id, needs_window, needs_signature = spec
        has_window = observation.get("window_start") is not None and observation.get("window_end") is not None
        no_window = observation.get("window_start") is None and observation.get("window_end") is None
        has_signature = type(observation.get("population_signature")) is str
        return (
            source_metric_id == expected_source
            and observation.get("population_id") == expected_population
            and observation.get("source_id") == expected_source_id
            and observation.get("source_mode") == "live"
            and (has_window if needs_window else no_window)
            and (has_signature if needs_signature else observation.get("population_signature") is None)
        )
    if observation.get("observed_at") is None:
        return False

    window_start = observation.get("window_start")
    window_end = observation.get("window_end")
    population_id = observation.get("population_id")
    source_id = observation.get("source_id")
    value = observation.get("value")

    if metric_id == "public_scope_commits":
        exact = source_metric_id == "owned_public_nonfork_authored_commits"
        fallbacks = {
            "github_total_commit_contributions": (
                "github-user-contributions-visible-to-provider",
                "github_graphql_commit_contributions",
            ),
            "github_contribution_calendar_total": (
                "github-contribution-calendar-visible-to-provider",
                "github_graphql_contribution_calendar",
            ),
        }
        if not _is_nonnegative_int(value) or window_start is not None or window_end is not None:
            return False
        if exact:
            return (
                status == "ok"
                and population_id == "owned-public-nonfork-repositories"
                and type(signature) is str
                and source_id == "github_rest_repo_commits"
                and reason in {"all_components_observed", "empty_population", "same_scope_cache"}
            )
        expected = fallbacks.get(source_metric_id)
        return (
            status == "fallback"
            and expected is not None
            and (population_id, source_id) == expected
            and signature is None
            and source_mode in {"fallback", "cache"}
            and reason == "different_metric_fallback"
        )

    if metric_id == "last_year_contributions":
        if source_metric_id == "github_contribution_calendar_total_and_days":
            return (
                status == "ok"
                and _valid_contribution_value(value)
                and population_id == "github-contribution-calendar-visible-to-provider"
                and signature is None
                and window_start is not None
                and window_end is not None
                and source_id == "github_graphql_contribution_calendar"
                and reason in {"all_components_observed", "same_scope_cache"}
            )
        return (
            source_metric_id == "previous_profile_snapshot_contributions"
            and status == "fallback"
            and _is_nonnegative_int(value)
            and population_id == "github-contribution-calendar-visible-to-provider"
            and signature is None
            and ((window_start is None and window_end is None) or (window_start is not None and window_end is not None))
            and source_id == "previous_profile_snapshot"
            and source_mode == "previous_snapshot"
            and reason == "previous_snapshot"
        )

    if metric_id == "releases_30d":
        if not _is_nonnegative_int(value) or window_start is None or window_end is None:
            return False
        if source_metric_id == "owned_public_nonfork_releases":
            return (
                status == "ok"
                and population_id == "owned-public-nonfork-repositories"
                and type(signature) is str
                and source_id == "github_rest_repo_releases"
                and reason in {"all_components_observed", "empty_population", "same_scope_cache"}
            )
        return (
            source_metric_id == "public_release_events"
            and status == "fallback"
            and population_id == "public-user-events-feed"
            and signature is None
            and source_id == "github_rest_public_events"
            and source_mode in {"fallback", "cache"}
            and reason == "different_metric_fallback"
        )

    if metric_id == "prs_merged":
        if not _is_nonnegative_int(value) or window_start is None or window_end is None or signature is not None:
            return False
        if source_metric_id == "merged_prs_primary_visible_population":
            return (
                status == "ok"
                and population_id == "owned-repositories-visible-to-primary-pr-search"
                and source_id == "github_rest_merged_pr_search_primary"
                and reason in {"all_components_observed", "same_scope_cache"}
            )
        return (
            source_metric_id == "merged_prs_public_visible_population"
            and status == "fallback"
            and population_id == "owned-public-repositories-visible-to-public-pr-search"
            and source_id == "github_rest_merged_pr_search_public"
            and source_mode in {"fallback", "cache"}
            and reason == "public_retry"
        )

    if metric_id == "recent_public_events":
        if (
            source_metric_id != "github_public_event_metadata_rows"
            or population_id != "public-user-events-feed"
            or type(signature) is not str
            or window_start is not None
            or window_end is not None
            or source_id != "github_rest_public_events"
            or type(value) not in {list, tuple}
        ):
            return False
        evidence_status = "partial" if status == "partial" else "ok"
        if not all(_valid_event_metadata_row(row, evidence_status=evidence_status) for row in value):
            return False
        if status == "partial":
            return source_mode == "live" and reason == "page_error"
        return status == "ok" and reason in {"terminal_page", "provider_cap", "same_scope_cache"}

    return False


def _validated_observation(**fields) -> dict:
    observation = {"schema": "profile-provider-observation/v1", **fields}
    if not validate_provider_observation(observation):
        raise ValueError("invalid provider observation")
    return observation


def _repo_signature(repos: list | None) -> str:
    if not repos:
        return "none"
    parts = []
    for repo in repos:
        owner = repo.get("owner", {}).get("login", USERNAME)
        name = repo.get("name", "")
        visibility = repo.get("visibility")
        if not isinstance(visibility, str):
            visibility = "private" if repo.get("private") is True else "public"
        fork = repo.get("fork") is True
        parts.append(
            f"{str(owner).casefold()}/{str(name).casefold()}:{visibility.casefold()}:{int(fork)}"
        )
    payload = "|".join(sorted(parts))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def _count_commits_from_commits_endpoint(owner: str, repo: str, use_public: bool) -> int:
    """
    Count commits authored by USERNAME using /commits?author=... with per_page=1.

    Uses the `Link` header's `rel="last"` page number as total count.
    """
    url = f"{API}/repos/{owner}/{repo}/commits"
    params = {"author": USERNAME, "per_page": 1, "page": 1}
    requester = _request_public_with_retry if use_public else _request_with_retry
    resp = requester(url, params=params)

    if resp.status_code != 200:
        return 0

    data = resp.json()
    if not isinstance(data, list) or len(data) == 0:
        return 0

    link = resp.headers.get("Link", "")
    match = re.search(r"[?&]page=(\d+)>;\s*rel=\"last\"", link)
    if match:
        return int(match.group(1))

    return len(data)


def _is_public_owned_repo(repo: dict) -> bool:
    """True when repo is publicly visible and owned by USERNAME."""
    owner_login = repo.get("owner", {}).get("login", "")
    is_owner = owner_login.lower() == USERNAME.lower()
    visibility = repo.get("visibility")
    if visibility is None:
        visibility = "private" if repo.get("private") else "public"
    return is_owner and visibility == "public"


def _validate_rest_repository_identities(repositories: list) -> None:
    """Require complete, consistent, unique REST repository identity facts."""
    if type(repositories) is not list:
        raise RuntimeError("REST repo listing is not a repository list")

    seen: set[tuple[str, str]] = set()
    for repository in repositories:
        if type(repository) is not dict:
            raise RuntimeError("REST repo listing contains a malformed row")
        name = repository.get("name")
        owner = repository.get("owner")
        owner_login = owner.get("login") if type(owner) is dict else None
        visibility = repository.get("visibility")
        private = repository.get("private")
        fork = repository.get("fork")
        if type(name) is not str or not name:
            raise RuntimeError("REST repo listing has a malformed repository name")
        if type(owner_login) is not str or not owner_login:
            raise RuntimeError("REST repo listing has a malformed repository owner")
        if visibility not in {"public", "private"}:
            raise RuntimeError("REST repo listing has an invalid visibility")
        if type(private) is not bool or private is not (visibility == "private"):
            raise RuntimeError("REST repo listing has contradictory privacy facts")
        if type(fork) is not bool:
            raise RuntimeError("REST repo listing has an invalid fork state")

        identity = (owner_login.casefold(), name.casefold())
        if identity in seen:
            raise RuntimeError("REST repo listing contains a duplicate identity")
        seen.add(identity)


def _graphql_public_identity(
    node: dict,
    *,
    include_forks: bool,
) -> tuple[str, str]:
    """Return an exact public-owned GraphQL identity or reject the row."""
    name = node.get("name")
    owner = node.get("owner")
    owner_login = owner.get("login") if type(owner) is dict else None
    visibility = node.get("visibility")
    is_private = node.get("isPrivate")
    is_fork = node.get("isFork")

    if type(name) is not str or not name:
        raise RuntimeError("GraphQL repo listing has a malformed repository name")
    if (
        type(owner_login) is not str
        or not owner_login
        or owner_login.casefold() != USERNAME.casefold()
    ):
        raise RuntimeError("GraphQL repo listing has an off-owner repository")
    if type(visibility) is not str or visibility != "PUBLIC":
        raise RuntimeError("GraphQL repo listing has non-public visibility")
    if type(is_private) is not bool or is_private is not False:
        raise RuntimeError("GraphQL repo listing has an invalid private state")
    if type(is_fork) is not bool or (not include_forks and is_fork is not False):
        raise RuntimeError("GraphQL repo listing has an invalid fork state")

    return owner_login.casefold(), name.casefold()


def _cached_graphql_public_repositories(
    payload: object,
    *,
    include_forks: bool,
) -> list[dict] | None:
    """Return rows from a complete same-scope provider cache envelope."""
    if type(payload) is not dict:
        return None
    if payload.get("schema") != "graphql-public-owned-repositories/v1":
        return None
    if payload.get("username") != USERNAME.casefold():
        return None
    if payload.get("include_forks") is not include_forks:
        return None
    if payload.get("complete") is not True:
        return None
    repositories = payload.get("repositories")
    if type(repositories) is not list:
        return None
    provider_total = payload.get("provider_total_count")
    if (
        isinstance(provider_total, bool)
        or not isinstance(provider_total, int)
        or provider_total < 0
        or provider_total != len(repositories)
    ):
        return None
    seen: set[tuple[str, str]] = set()
    for repository in repositories:
        if type(repository) is not dict:
            return None
        name = repository.get("name")
        owner = repository.get("owner")
        owner_login = owner.get("login") if type(owner) is dict else None
        visibility = repository.get("visibility")
        private = repository.get("private")
        fork = repository.get("fork")
        if type(name) is not str or not name:
            return None
        if (
            type(owner_login) is not str
            or owner_login.casefold() != USERNAME.casefold()
        ):
            return None
        if visibility != "public" or private is not False:
            return None
        if type(fork) is not bool or (not include_forks and fork is not False):
            return None
        identity = (owner_login.casefold(), name.casefold())
        if identity in seen:
            return None
        seen.add(identity)
    return repositories


def _cached_graphql_public_repos_are_valid(
    payload: object,
    *,
    include_forks: bool,
) -> bool:
    return _cached_graphql_public_repositories(
        payload,
        include_forks=include_forks,
    ) is not None


def _graphql_private_identity(node: dict) -> tuple[str, str]:
    """Return an exact private-owned non-fork identity or reject the row."""
    name = node.get("name")
    owner = node.get("owner")
    owner_login = owner.get("login") if type(owner) is dict else None
    visibility = node.get("visibility")
    is_private = node.get("isPrivate")
    is_fork = node.get("isFork")

    if type(name) is not str or not name:
        raise RuntimeError("GraphQL private repo listing has a malformed repository name")
    if (
        type(owner_login) is not str
        or not owner_login
        or owner_login.casefold() != USERNAME.casefold()
    ):
        raise RuntimeError("GraphQL private repo listing has an off-owner repository")
    if type(visibility) is not str or visibility != "PRIVATE":
        raise RuntimeError("GraphQL private repo listing has non-private visibility")
    if type(is_private) is not bool or is_private is not True:
        raise RuntimeError("GraphQL private repo listing has an invalid private state")
    if type(is_fork) is not bool or is_fork is not False:
        raise RuntimeError("GraphQL private repo listing has an invalid fork state")

    return owner_login.casefold(), name.casefold()


def _private_language_bytes(node: dict) -> dict[str, int]:
    """Normalize exact language-byte edges from a private repository row."""
    languages = node.get("languages")
    edges = languages.get("edges") if type(languages) is dict else None
    if type(edges) is not list:
        raise RuntimeError("GraphQL private repo listing has invalid language edges")

    language_bytes: dict[str, int] = {}
    for edge in edges:
        if type(edge) is not dict:
            raise RuntimeError("GraphQL private repo listing has a malformed language edge")
        language_node = edge.get("node")
        language_name = (
            language_node.get("name") if type(language_node) is dict else None
        )
        size = edge.get("size")
        if type(language_name) is not str or not language_name:
            raise RuntimeError("GraphQL private repo listing has a malformed language name")
        if type(size) is not int or size < 0:
            raise RuntimeError("GraphQL private repo listing has an invalid language size")
        if size > 0:
            language_bytes[language_name] = language_bytes.get(language_name, 0) + size
    return language_bytes


def _cached_graphql_private_repos_are_valid(repositories: object) -> bool:
    """Validate normalized private-owned non-fork rows retained in cache."""
    if type(repositories) is not list:
        return False

    seen: set[tuple[str, str]] = set()
    for repository in repositories:
        if type(repository) is not dict:
            return False
        name = repository.get("name")
        owner = repository.get("owner")
        owner_login = owner.get("login") if type(owner) is dict else None
        language_bytes = repository.get("language_bytes")
        if type(name) is not str or not name:
            return False
        if (
            type(owner_login) is not str
            or owner_login.casefold() != USERNAME.casefold()
        ):
            return False
        if repository.get("visibility") != "private":
            return False
        if repository.get("private") is not True or repository.get("fork") is not False:
            return False
        if type(repository.get("language_bytes_complete")) is not bool:
            return False
        if type(language_bytes) is not dict:
            return False
        if any(
            type(language) is not str
            or not language
            or type(size) is not int
            or size <= 0
            for language, size in language_bytes.items()
        ):
            return False
        identity = (owner_login.casefold(), name.casefold())
        if identity in seen:
            return False
        seen.add(identity)
    return True


def _declared_private_capability() -> str:
    """Return the private-repository capability promised by this run."""
    mode = token_mode_from_env()
    if TOKEN and mode == "personal_github_token":
        return "personal_github_token"
    if TOKEN and mode == "none":
        # Direct library callers may inject a transport token without declaring
        # its provenance. They may query, but their result is never reusable as
        # private-capable cached evidence.
        return "unbound_token"
    return "unavailable"


def _successful_private_capability() -> str:
    """Return the capability actually used by the latest GraphQL request."""
    declared = _declared_private_capability()
    if declared in {"personal_github_token", "unbound_token"} and not last_query_used_fallback_token():
        return declared
    return "unavailable"


def _successful_private_count_capability() -> str:
    """Return exact private-count capability proven by the last response.

    Merely authenticating with the first configured token is not evidence that
    GitHub exposed the account's complete private repository inventory.  Classic
    OAuth/PAT responses advertise ``repo`` when that full repository scope was
    actually granted; absent, restricted, or unknown scope evidence stays
    unavailable.
    """
    if _successful_private_capability() != "personal_github_token":
        return "unavailable"
    scopes = last_query_oauth_scopes()
    if scopes is None or "repo" not in scopes:
        return "unavailable"
    return "personal_github_token"


def _cached_graphql_private_repositories(
    payload: object,
    *,
    limit: int,
) -> list[dict] | None:
    """Return a complete private inventory from a same-scope cache envelope."""
    if type(payload) is not dict:
        return None
    if payload.get("schema") != "graphql-private-owned-repositories/v1":
        return None
    if payload.get("username") != USERNAME.casefold():
        return None
    if payload.get("limit") != limit:
        return None
    if payload.get("complete") is not True:
        return None
    if payload.get("private_capability") != _declared_private_capability():
        return None
    if payload.get("private_capability") != "personal_github_token":
        return None
    repositories = payload.get("repositories")
    if not _cached_graphql_private_repos_are_valid(repositories):
        return None
    provider_total = payload.get("provider_total_count")
    if (
        isinstance(provider_total, bool)
        or not isinstance(provider_total, int)
        or provider_total < 0
        or provider_total != len(repositories)
    ):
        return None
    return repositories


_OWNED_COUNT_KEYS = (
    "public_owned_total",
    "public_owned_forks",
    "public_owned_nonfork",
    "private_owned",
    "private_owned_nonfork",
)


def _owned_repo_counts_are_valid(
    counts: object,
    *,
    private_capability: str,
) -> bool:
    if type(counts) is not dict or set(counts) != set(_OWNED_COUNT_KEYS):
        return False
    public_values = [counts.get(key) for key in _OWNED_COUNT_KEYS[:3]]
    if any(type(value) is not int or value < 0 for value in public_values):
        return False
    public_total, public_forks, public_nonfork = public_values
    if public_forks + public_nonfork != public_total:
        return False

    private_total = counts.get("private_owned")
    private_nonfork = counts.get("private_owned_nonfork")
    if private_capability == "personal_github_token":
        if type(private_total) is not int or type(private_nonfork) is not int:
            return False
        if private_total < 0 or private_nonfork < 0 or private_nonfork > private_total:
            return False
    elif private_capability == "unavailable":
        if private_total is not None or private_nonfork is not None:
            return False
    else:
        return False
    return True


def _cached_owned_repo_scope_counts(payload: object) -> dict | None:
    """Return count facts only from a complete same-user/capability envelope."""
    if type(payload) is not dict:
        return None
    if payload.get("schema") != "owned-repo-scope-counts/v1":
        return None
    if payload.get("username") != USERNAME.casefold():
        return None
    if payload.get("query_scope") != "owned-public-private-counts":
        return None
    if payload.get("complete") is not True:
        return None
    private_capability = payload.get("private_capability")
    if private_capability != _declared_private_capability():
        return None
    verified_scopes = payload.get("verified_oauth_scopes")
    if private_capability == "personal_github_token":
        if (
            type(verified_scopes) is not list
            or "repo" not in verified_scopes
            or any(type(scope) is not str for scope in verified_scopes)
        ):
            return None
    elif verified_scopes not in (None, []):
        return None
    counts = payload.get("counts")
    if not _owned_repo_counts_are_valid(
        counts,
        private_capability=private_capability,
    ):
        return None
    return counts


def _owned_repo_scope_count_envelope(
    counts: dict,
    *,
    private_capability: str,
    verified_oauth_scopes: frozenset[str] | None = None,
) -> dict:
    if not _owned_repo_counts_are_valid(
        counts,
        private_capability=private_capability,
    ):
        raise RuntimeError("owned repository counts are internally inconsistent")
    envelope = {
        "schema": "owned-repo-scope-counts/v1",
        "username": USERNAME.casefold(),
        "query_scope": "owned-public-private-counts",
        "complete": True,
        "private_capability": private_capability,
        "counts": counts,
    }
    if private_capability == "personal_github_token":
        normalized_scopes = sorted(verified_oauth_scopes or ())
        if "repo" not in normalized_scopes:
            raise RuntimeError("exact private counts require verified repo scope")
        envelope["verified_oauth_scopes"] = normalized_scopes
    return envelope


def _workflow_yaml_count_from_graphql(
    workflows_dir: object,
    *,
    require_tree_typename: bool = False,
) -> int | None:
    """Return an exact workflow-YAML count, or ``None`` when not observed.

    ``None`` at the ``workflowsDir`` field means GitHub observed that the
    directory is absent. A missing field or malformed Tree payload is not the
    same evidence and remains unknown.
    """
    if not isinstance(workflows_dir, dict):
        return None
    typename = workflows_dir.get("__typename")
    if typename != "Tree" and (require_tree_typename or typename is not None):
        return None
    entries = workflows_dir.get("entries")
    if not isinstance(entries, list):
        return None

    count = 0
    seen_entries: set[tuple[str, str]] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            return None
        name = entry.get("name")
        entry_type = entry.get("type")
        if not isinstance(name, str) or not isinstance(entry_type, str):
            return None
        identity = (name, entry_type)
        if identity in seen_entries:
            return None
        seen_entries.add(identity)
        if entry_type == "blob" and name.endswith((".yml", ".yaml")):
            count += 1
    return count


def _normalize_graphql_repo(
    node: dict,
    *,
    require_workflow_tree_typename: bool = False,
) -> dict:
    owner = node.get("owner")
    owner_login = owner.get("login") if type(owner) is dict else None
    language_name = (node.get("primaryLanguage") or {}).get("name")
    visibility_value = node.get("visibility")
    visibility = (
        visibility_value.lower() if type(visibility_value) is str else None
    )
    is_fork = node.get("isFork")
    is_private = node.get("isPrivate")
    workflows_observed = "workflowsDir" in node
    workflows_dir = node.get("workflowsDir")
    if workflows_observed and workflows_dir is None:
        has_ci_workflows: bool | None = False
        workflow_file_count: int | None = 0
    elif workflows_observed:
        workflow_file_count = _workflow_yaml_count_from_graphql(
            workflows_dir,
            require_tree_typename=require_workflow_tree_typename,
        )
        has_ci_workflows = (
            workflow_file_count > 0 if workflow_file_count is not None else None
        )
    else:
        has_ci_workflows = None
        workflow_file_count = None
    language_bytes = {}
    language_bytes_complete = False
    languages = node.get("languages")
    if isinstance(languages, dict):
        edges = languages.get("edges")
        page_info = languages.get("pageInfo")
        if isinstance(edges, list):
            language_bytes_complete = (
                isinstance(page_info, dict)
                and page_info.get("hasNextPage") is False
            )
            for edge in edges:
                if not isinstance(edge, dict):
                    language_bytes_complete = False
                    continue
                lang_node = edge.get("node") or {}
                lang_name = lang_node.get("name")
                lang_size = edge.get("size")
                if not isinstance(lang_name, str) or not lang_name:
                    language_bytes_complete = False
                    continue
                try:
                    size = int(lang_size)
                except (TypeError, ValueError):
                    language_bytes_complete = False
                    size = 0
                if size > 0:
                    language_bytes[lang_name] = language_bytes.get(lang_name, 0) + size
                elif size < 0:
                    language_bytes_complete = False
    latest_commit_message = ""
    default_branch_ref = node.get("defaultBranchRef")
    if isinstance(default_branch_ref, dict):
        target = default_branch_ref.get("target")
        if isinstance(target, dict):
            message = target.get("messageHeadline") or target.get("message")
            if isinstance(message, str):
                latest_commit_message = message.strip()

    return {
        "name": node.get("name", ""),
        "fork": is_fork if type(is_fork) is bool else None,
        "private": is_private if type(is_private) is bool else None,
        "visibility": visibility,
        "description": node.get("description", ""),
        "html_url": node.get("url", ""),
        "pushed_at": node.get("pushedAt", ""),
        "created_at": node.get("createdAt", ""),
        "stargazers_count": int(node.get("stargazerCount", 0)),
        "forks_count": int(node.get("forkCount", 0)),
        "language": language_name,
        "owner": {"login": owner_login},
        "has_ci_workflows": has_ci_workflows,
        "workflow_file_count": workflow_file_count,
        "language_bytes": language_bytes,
        "language_bytes_complete": language_bytes_complete,
        "latest_commit_message": latest_commit_message,
    }


def _graphql_public_owned_repos(include_forks: bool) -> list:
    cache_key = f"graphql_public_owned_repos_{int(include_forks)}"
    cached = _get_cached(cache_key)
    cached_repositories = _cached_graphql_public_repositories(
        cached,
        include_forks=include_forks,
    )
    if cached_repositories is not None:
        return cached_repositories

    if include_forks:
        query = """
        query($login: String!, $cursor: String) {
          user(login: $login) {
            repositories(
              ownerAffiliations: OWNER
              privacy: PUBLIC
              first: 100
              after: $cursor
              orderBy: { field: CREATED_AT, direction: DESC }
            ) {
              totalCount
              pageInfo { hasNextPage endCursor }
              nodes {
                name
                isFork
                isPrivate
                visibility
                description
                url
                pushedAt
                createdAt
                stargazerCount
                forkCount
                owner { login }
                primaryLanguage { name }
                defaultBranchRef {
                  target {
                    __typename
                    ... on Commit {
                      messageHeadline
                    }
                  }
                }
                workflowsDir: object(expression: "HEAD:.github/workflows") {
                  __typename
                  ... on Tree {
                    entries { name type }
                  }
                }
                languages(first: 20, orderBy: { field: SIZE, direction: DESC }) {
                  pageInfo { hasNextPage endCursor }
                  edges {
                    size
                    node { name }
                  }
                }
              }
            }
          }
        }
        """
    else:
        query = """
        query($login: String!, $cursor: String) {
          user(login: $login) {
            repositories(
              ownerAffiliations: OWNER
              privacy: PUBLIC
              isFork: false
              first: 100
              after: $cursor
              orderBy: { field: CREATED_AT, direction: DESC }
            ) {
              totalCount
              pageInfo { hasNextPage endCursor }
              nodes {
                name
                isFork
                isPrivate
                visibility
                description
                url
                pushedAt
                createdAt
                stargazerCount
                forkCount
                owner { login }
                primaryLanguage { name }
                defaultBranchRef {
                  target {
                    __typename
                    ... on Commit {
                      messageHeadline
                    }
                  }
                }
                workflowsDir: object(expression: "HEAD:.github/workflows") {
                  __typename
                  ... on Tree {
                    entries { name type }
                  }
                }
                languages(first: 20, orderBy: { field: SIZE, direction: DESC }) {
                  pageInfo { hasNextPage endCursor }
                  edges {
                    size
                    node { name }
                  }
                }
              }
            }
          }
        }
        """

    repos = []
    cursor = None
    saw_page = False
    expected_total: int | None = None
    seen_cursors: set[str] = set()
    seen_identities: set[tuple[str, str]] = set()

    while True:
        data = _graphql_query(query, {"login": USERNAME, "cursor": cursor})
        user = (data or {}).get("user")
        repo_conn = (user or {}).get("repositories")
        if not isinstance(repo_conn, dict):
            raise RuntimeError("GraphQL repo listing unavailable")
        saw_page = True

        total_count = repo_conn.get("totalCount")
        if (
            isinstance(total_count, bool)
            or not isinstance(total_count, int)
            or total_count < 0
        ):
            raise RuntimeError("GraphQL repo listing has invalid totalCount")
        if expected_total is None:
            expected_total = total_count
        elif total_count != expected_total:
            raise RuntimeError("GraphQL repo listing totalCount changed during pagination")

        nodes = repo_conn.get("nodes")
        if not isinstance(nodes, list):
            raise RuntimeError("GraphQL repo listing has invalid nodes")
        for node in nodes:
            if not isinstance(node, dict):
                raise RuntimeError("GraphQL repo listing contains a malformed node")
            identity = _graphql_public_identity(
                node,
                include_forks=include_forks,
            )
            normalized = _normalize_graphql_repo(node)
            if identity in seen_identities:
                raise RuntimeError("GraphQL repo listing contains a duplicate or malformed identity")
            seen_identities.add(identity)
            repos.append(normalized)

        page_info = repo_conn.get("pageInfo")
        if not isinstance(page_info, dict):
            raise RuntimeError("GraphQL repo listing has invalid pageInfo")
        if not page_info.get("hasNextPage"):
            break

        next_cursor = page_info.get("endCursor")
        if not isinstance(next_cursor, str) or not next_cursor:
            raise RuntimeError("GraphQL repo listing omitted a required cursor")
        if next_cursor == cursor or next_cursor in seen_cursors:
            raise RuntimeError("GraphQL repo listing repeated a cursor")
        seen_cursors.add(next_cursor)
        cursor = next_cursor

    if not saw_page or expected_total is None or len(repos) != expected_total:
        raise RuntimeError("GraphQL repo listing cardinality disagrees with totalCount")

    _set_cached(
        cache_key,
        {
            "schema": "graphql-public-owned-repositories/v1",
            "username": USERNAME.casefold(),
            "include_forks": include_forks,
            "complete": True,
            "provider_total_count": expected_total,
            "repositories": repos,
        },
    )
    return repos


def _graphql_private_owned_repos(limit: int = 40) -> list:
    """Fetch the complete private-owned non-fork repository inventory."""
    cache_limit = int(limit)
    cache_key = f"graphql_private_owned_repos_{cache_limit}"
    cached = _get_cached(cache_key)
    cached_repositories = _cached_graphql_private_repositories(
        cached,
        limit=cache_limit,
    )
    if cached_repositories is not None:
        return cached_repositories
    if not TOKEN:
        return []
    declared_capability = _declared_private_capability()
    if declared_capability == "unavailable":
        return []

    query = """
    query($login: String!, $first: Int!, $cursor: String) {
      user(login: $login) {
        repositories(
          ownerAffiliations: OWNER
          privacy: PRIVATE
          isFork: false
          first: $first
          after: $cursor
          orderBy: { field: PUSHED_AT, direction: DESC }
        ) {
          totalCount
          pageInfo { hasNextPage endCursor }
          nodes {
            name
            isFork
            isPrivate
            visibility
            description
            url
            pushedAt
            createdAt
            stargazerCount
            forkCount
            owner { login }
            primaryLanguage { name }
            defaultBranchRef {
              target {
                __typename
                ... on Commit { messageHeadline }
              }
            }
            workflowsDir: object(expression: "HEAD:.github/workflows") {
              __typename
              ... on Tree { entries { name type } }
            }
            languages(first: 100, orderBy: { field: SIZE, direction: DESC }) {
              pageInfo { hasNextPage endCursor }
              edges {
                size
                node { name }
              }
            }
          }
        }
      }
    }
    """

    page_size = min(100, max(1, cache_limit))
    repos: list[dict] = []
    cursor: str | None = None
    expected_total: int | None = None
    seen_cursors: set[str] = set()
    seen_identities: set[tuple[str, str]] = set()
    used_fallback_token = False

    while True:
        data = _graphql_query(
            query,
            {"login": USERNAME, "first": page_size, "cursor": cursor},
        )
        if declared_capability == "personal_github_token":
            used_fallback_token = (
                used_fallback_token or last_query_used_fallback_token()
            )
        user = (data or {}).get("user")
        repo_conn = (user or {}).get("repositories")
        if type(repo_conn) is not dict:
            raise RuntimeError("GraphQL private repo listing unavailable")

        total_count = repo_conn.get("totalCount")
        if type(total_count) is not int or total_count < 0:
            raise RuntimeError("GraphQL private repo listing has invalid totalCount")
        if expected_total is None:
            expected_total = total_count
        elif total_count != expected_total:
            raise RuntimeError(
                "GraphQL private repo listing totalCount changed during pagination"
            )

        nodes = repo_conn.get("nodes")
        if type(nodes) is not list:
            raise RuntimeError("GraphQL private repo listing has invalid nodes")
        for node in nodes:
            if type(node) is not dict:
                raise RuntimeError(
                    "GraphQL private repo listing contains a malformed node"
                )
            identity = _graphql_private_identity(node)
            if identity in seen_identities:
                raise RuntimeError(
                    "GraphQL private repo listing contains a duplicate identity"
                )
            normalized = _normalize_graphql_repo(node)
            seen_identities.add(identity)
            repos.append(normalized)

        if expected_total is not None and len(repos) > expected_total:
            raise RuntimeError(
                "GraphQL private repo listing cardinality exceeds totalCount"
            )

        page_info = repo_conn.get("pageInfo")
        if type(page_info) is not dict:
            raise RuntimeError("GraphQL private repo listing has invalid pageInfo")
        has_next_page = page_info.get("hasNextPage")
        if type(has_next_page) is not bool:
            raise RuntimeError("GraphQL private repo listing has invalid page state")
        if not has_next_page:
            break

        next_cursor = page_info.get("endCursor")
        if type(next_cursor) is not str or not next_cursor:
            raise RuntimeError("GraphQL private repo listing omitted a required cursor")
        if next_cursor == cursor or next_cursor in seen_cursors:
            raise RuntimeError("GraphQL private repo listing repeated a cursor")
        seen_cursors.add(next_cursor)
        cursor = next_cursor

    if expected_total is None or len(repos) != expected_total:
        raise RuntimeError(
            "GraphQL private repo listing cardinality disagrees with totalCount"
        )

    successful_capability = (
        "unavailable" if used_fallback_token else _successful_private_capability()
    )
    if successful_capability == "unavailable":
        raise RuntimeError(
            "GraphQL private repo listing lost private-token capability"
        )
    if successful_capability == "personal_github_token":
        _set_cached(
            cache_key,
            {
                "schema": "graphql-private-owned-repositories/v1",
                "username": USERNAME.casefold(),
                "limit": cache_limit,
                "complete": True,
                "provider_total_count": expected_total,
                "private_capability": successful_capability,
                "repositories": repos,
            },
        )
    else:
        # An unbound direct-call token can provide a one-shot observation, but
        # the raw write is intentionally rejected by the cache reader above.
        _set_cached(cache_key, repos)
    return repos


def _workflow_provider_query(privacy: str) -> str:
    if privacy not in {"PUBLIC", "PRIVATE"}:
        raise ValueError(f"unsupported repository privacy {privacy!r}")
    return f"""
    query($login: String!, $cursor: String) {{
      user(login: $login) {{
        repositories(
          ownerAffiliations: OWNER
          privacy: {privacy}
          isFork: false
          first: 100
          after: $cursor
          orderBy: {{ field: CREATED_AT, direction: DESC }}
        ) {{
          totalCount
          pageInfo {{ hasNextPage endCursor }}
          nodes {{
            name
            isFork
            isPrivate
            visibility
            owner {{ login }}
            workflowsDir: object(expression: "HEAD:.github/workflows") {{
              __typename
              ... on Tree {{ entries {{ name type }} }}
            }}
          }}
        }}
      }}
    }}
    """


def _workflow_provider_result(
    repositories: list[dict],
    *,
    privacy: str,
    provider_total: int | None,
    raw_node_count: int,
    pages_fetched: int,
    enumeration_complete: bool,
    profile_row_seen: bool,
    unavailable_reason: str | None = None,
) -> dict:
    is_private = privacy == "PRIVATE"
    if provider_total is None:
        eligible_count = None
    elif enumeration_complete:
        eligible_count = len(repositories)
    elif is_private:
        eligible_count = provider_total
    else:
        # Until traversal finishes, the optional profile row and any hostile
        # unseen rows make the eligible denominator unknowable.
        eligible_count = None

    known_rows = [
        repo for repo in repositories
        if isinstance(repo.get("has_ci_workflows"), bool)
        and isinstance(repo.get("workflow_file_count"), int)
    ]
    observed_count = len(known_rows)
    if eligible_count is None:
        unknown_count = None
    else:
        unknown_count = max(0, eligible_count - observed_count)

    complete = (
        enumeration_complete
        and eligible_count is not None
        and len(repositories) == eligible_count
        and observed_count == eligible_count
        and unknown_count == 0
    )
    if complete:
        configured_count: int | None = sum(
            1 for repo in known_rows if repo["has_ci_workflows"] is True
        )
        workflow_file_count: int | None = sum(
            int(repo["workflow_file_count"]) for repo in known_rows
        )
        adoption_pct: float | None = (
            round(configured_count / eligible_count * 100, 1)
            if eligible_count
            else None
        )
    else:
        configured_count = None
        workflow_file_count = None
        adoption_pct = None

    if complete and eligible_count == 0:
        reason = "empty_population"
    elif complete:
        reason = None
    else:
        reason = unavailable_reason or (
            "unknown_repository_state"
            if enumeration_complete
            else "incomplete_enumeration"
        )

    if is_private:
        # This workflow observation needs only state rows; the separate private
        # inventory carries repository metadata to the profile model.
        safe_repositories = [
            {
                "has_ci_workflows": repo.get("has_ci_workflows"),
                "workflow_file_count": repo.get("workflow_file_count"),
            }
            for repo in repositories
        ]
    else:
        safe_repositories = list(repositories)

    scope = (
        "private owned non-fork repositories; profile repository excluded"
        if is_private
        else "public owned non-fork repositories; profile repository excluded"
    )
    return {
        "repositories": safe_repositories,
        "eligible_repository_count": eligible_count,
        "observed_repository_count": observed_count,
        "unknown_repository_count": unknown_count,
        "configured_repository_count": configured_count,
        "workflow_yaml_file_count": workflow_file_count,
        "adoption_pct": adoption_pct,
        "pages_fetched": pages_fetched,
        "raw_node_count": raw_node_count,
        "provider_total_count": provider_total,
        "complete": complete,
        "scope": scope,
        "unavailable_reason": reason,
        "profile_row_seen": profile_row_seen if not is_private else False,
    }


def _collect_workflow_provider_observation(privacy: str) -> dict:
    is_private = privacy == "PRIVATE"
    if is_private and not TOKEN:
        return _workflow_provider_result(
            [],
            privacy=privacy,
            provider_total=None,
            raw_node_count=0,
            pages_fetched=0,
            enumeration_complete=False,
            profile_row_seen=False,
            unavailable_reason="capability_unavailable",
        )

    query = _workflow_provider_query(privacy)
    cursor: str | None = None
    seen_cursors: set[str] = set()
    seen_identities: set[tuple[str, str]] = set()
    repositories: list[dict] = []
    provider_total: int | None = None
    raw_node_count = 0
    pages_fetched = 0
    profile_row_seen = False

    def partial_result(reason: str = "incomplete_enumeration") -> dict:
        return _workflow_provider_result(
            repositories,
            privacy=privacy,
            provider_total=provider_total,
            raw_node_count=raw_node_count,
            pages_fetched=pages_fetched,
            enumeration_complete=False,
            profile_row_seen=profile_row_seen,
            unavailable_reason=reason,
        )

    while True:
        try:
            data = _graphql_query(query, {"login": USERNAME, "cursor": cursor})
        except (requests.RequestException, RuntimeError):
            return partial_result()

        if not isinstance(data, dict):
            if pages_fetched:
                return partial_result("malformed_observation")
            raise RuntimeError("workflow provider returned a malformed payload")
        user = data.get("user")
        if not isinstance(user, dict):
            if pages_fetched:
                return partial_result("malformed_observation")
            raise RuntimeError("workflow provider returned a malformed user payload")
        connection = user.get("repositories")
        if not isinstance(connection, dict):
            if pages_fetched:
                return partial_result("malformed_observation")
            raise RuntimeError("workflow provider returned no repository connection")

        total_count = connection.get("totalCount")
        if (
            isinstance(total_count, bool)
            or not isinstance(total_count, int)
            or total_count < 0
        ):
            if pages_fetched:
                return partial_result("malformed_observation")
            raise RuntimeError("workflow provider returned invalid totalCount")
        if provider_total is None:
            provider_total = total_count
        elif total_count != provider_total:
            raise RuntimeError("workflow provider totalCount changed during pagination")

        nodes = connection.get("nodes")
        if not isinstance(nodes, list):
            if pages_fetched:
                return partial_result("malformed_observation")
            raise RuntimeError("workflow provider returned invalid nodes")
        pages_fetched += 1
        for node in nodes:
            raw_node_count += 1
            if not isinstance(node, dict):
                raise RuntimeError("workflow provider returned a malformed repository node")
            name = node.get("name")
            owner_login = (node.get("owner") or {}).get("login")
            visibility = node.get("visibility")
            is_fork = node.get("isFork")
            is_private_value = node.get("isPrivate")
            if not isinstance(name, str) or not name:
                raise RuntimeError("workflow provider returned a malformed repository identity")
            if not isinstance(owner_login, str) or owner_login.casefold() != USERNAME.casefold():
                raise RuntimeError("workflow provider returned an off-owner repository")
            if is_fork is not False:
                raise RuntimeError("workflow provider returned a fork or unknown fork state")
            if visibility != privacy or is_private_value is not is_private:
                raise RuntimeError("workflow provider returned a repository outside its visibility scope")

            identity = (owner_login.casefold(), name.casefold())
            if identity in seen_identities:
                raise RuntimeError("workflow provider returned a duplicate repository identity")
            seen_identities.add(identity)

            is_profile = identity == (USERNAME.casefold(), USERNAME.casefold())
            if is_profile:
                if is_private or profile_row_seen:
                    raise RuntimeError("workflow provider returned a forbidden profile repository row")
                profile_row_seen = True
                continue
            repositories.append(
                _normalize_graphql_repo(
                    node,
                    require_workflow_tree_typename=True,
                )
            )

        page_info = connection.get("pageInfo")
        if not isinstance(page_info, dict):
            if pages_fetched:
                return partial_result("malformed_observation")
            raise RuntimeError("workflow provider returned invalid pageInfo")
        has_next_page = page_info.get("hasNextPage")
        if not isinstance(has_next_page, bool):
            if pages_fetched:
                return partial_result("malformed_observation")
            raise RuntimeError("workflow provider returned invalid hasNextPage")
        if not has_next_page:
            break

        next_cursor = page_info.get("endCursor")
        if not isinstance(next_cursor, str) or not next_cursor:
            raise RuntimeError("workflow provider omitted a required cursor")
        if next_cursor == cursor or next_cursor in seen_cursors:
            raise RuntimeError("workflow provider repeated a cursor")
        seen_cursors.add(next_cursor)
        cursor = next_cursor

    if provider_total is None or raw_node_count != provider_total:
        raise RuntimeError("workflow provider cardinality disagrees with totalCount")

    return _workflow_provider_result(
        repositories,
        privacy=privacy,
        provider_total=provider_total,
        raw_node_count=raw_node_count,
        pages_fetched=pages_fetched,
        enumeration_complete=True,
        profile_row_seen=profile_row_seen,
    )


def get_public_workflow_observations() -> dict:
    """Return a complete-or-explicitly-incomplete owned-public observation."""
    return _collect_workflow_provider_observation("PUBLIC")


def get_private_workflow_observations() -> dict:
    """Return aggregate-safe owned-private workflow-configuration evidence."""
    return _collect_workflow_provider_observation("PRIVATE")


def get_private_repos(limit: int = 40) -> list:
    """Public wrapper: recently-pushed private owned repos (metadata only)."""
    try:
        return _graphql_private_owned_repos(limit=limit)
    except Exception:
        return []


# ── public API (signatures unchanged) ────────────────────────────────

def _cached_paginated_results(
    payload: object,
    *,
    endpoint: str,
    params: dict,
    per_page: int,
) -> list | None:
    """Read only a complete cache envelope bound to this REST request."""
    if type(payload) is not dict:
        return None
    if payload.get("schema") != "rest-pagination/v1":
        return None
    if payload.get("endpoint") != endpoint:
        return None
    if payload.get("params") != params:
        return None
    if payload.get("per_page") != per_page or payload.get("complete") is not True:
        return None
    pages_fetched = payload.get("pages_fetched")
    if type(pages_fetched) is not int or pages_fetched < 1:
        return None
    results = payload.get("results")
    return results if type(results) is list else None


def paginated_get(endpoint: str, params: dict | None = None, per_page: int = 100) -> list:
    """Fetch all pages from a REST endpoint."""
    request_params = dict(params or {})
    cache_key = f"paginated_{endpoint}_{json.dumps(request_params, sort_keys=True)}"
    cached = _get_cached(cache_key)
    cached_results = _cached_paginated_results(
        cached,
        endpoint=endpoint,
        params=request_params,
        per_page=per_page,
    )
    if cached_results is not None:
        return cached_results

    results = []
    p = dict(request_params)
    p["per_page"] = per_page
    page = 1

    while True:
        p["page"] = page
        url = f"{API}/{endpoint}" if not endpoint.startswith("http") else endpoint
        resp = _request_with_retry(url, params=p)
        if resp.status_code != 200:
            raise RuntimeError(
                f"REST pagination failed on page {page} with HTTP {resp.status_code}"
            )
        data = resp.json()
        if type(data) is not list:
            raise RuntimeError(f"REST pagination returned a malformed page {page}")
        if not data:
            break
        results.extend(data)
        if len(data) < per_page:
            break
        page += 1

    _set_cached(
        cache_key,
        {
            "schema": "rest-pagination/v1",
            "endpoint": endpoint,
            "params": request_params,
            "per_page": per_page,
            "complete": True,
            "pages_fetched": page,
            "results": results,
        },
    )
    return results


def get_repos(include_forks: bool = False) -> list:
    """Get public repos owned by USERNAME, optionally including forks."""
    cached_graphql = _get_cached(f"graphql_public_owned_repos_{int(include_forks)}")
    cached_repositories = _cached_graphql_public_repositories(
        cached_graphql,
        include_forks=include_forks,
    )
    if cached_repositories is not None:
        return cached_repositories

    try:
        repos = _graphql_public_owned_repos(include_forks)
        return repos
    except Exception as exc:
        print(f"  Warning: GraphQL repo listing failed; falling back to REST ({exc})")

    try:
        repos = paginated_get(
            f"users/{USERNAME}/repos",
            {"sort": "created", "direction": "desc", "type": "owner"},
        )
        _validate_rest_repository_identities(repos)
        repos = [r for r in repos if _is_public_owned_repo(r)]
        if not include_forks:
            repos = [r for r in repos if not r.get("fork")]
        return repos
    except requests.RequestException as exc:
        status = (
            exc.response.status_code
            if isinstance(exc, requests.HTTPError) and exc.response is not None
            else "network"
        )
        print(f"  Warning: REST repo listing unavailable ({status}); falling back to GraphQL")
        try:
            return _graphql_public_owned_repos(include_forks)
        except Exception as exc:
            raise RuntimeError("public repository inventory unavailable") from exc


def get_owned_repo_scope_counts() -> dict:
    """
    Return repo counts with explicit scope splits.

    Keys:
      - public_owned_total
      - public_owned_forks
      - public_owned_nonfork
      - private_owned (None when unavailable)
      - private_owned_nonfork (None when unavailable)
    """
    cache_key = "owned_repo_scope_counts"
    cached = _get_cached(cache_key)
    cached_counts = _cached_owned_repo_scope_counts(cached)
    if cached_counts is not None:
        return cached_counts

    # Prefer GraphQL totals when authenticated. This avoids pagination math drift.
    if TOKEN:
        query = """
        query($login: String!) {
          user(login: $login) {
            publicOwned: repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 1) {
              totalCount
            }
            publicOwnedForks: repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: true, first: 1) {
              totalCount
            }
            publicOwnedNonFork: repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 1) {
              totalCount
            }
            privateOwned: repositories(ownerAffiliations: OWNER, privacy: PRIVATE, first: 1) {
              totalCount
            }
            privateOwnedNonFork: repositories(ownerAffiliations: OWNER, privacy: PRIVATE, isFork: false, first: 1) {
              totalCount
            }
          }
        }
        """
        data = _graphql_query(query, {"login": USERNAME})
        user = (data or {}).get("user")
        if isinstance(user, dict):
            def connection_total(name: str) -> int | None:
                connection = user.get(name)
                total = connection.get("totalCount") if type(connection) is dict else None
                if isinstance(total, bool) or not isinstance(total, int) or total < 0:
                    return None
                return total

            public_total = connection_total("publicOwned")
            public_forks = connection_total("publicOwnedForks")
            public_nonfork = connection_total("publicOwnedNonFork")
            private_capability = _successful_private_count_capability()
            if private_capability == "personal_github_token":
                private_owned = connection_total("privateOwned")
                private_owned_nonfork = connection_total("privateOwnedNonFork")
            else:
                private_capability = "unavailable"
                private_owned = None
                private_owned_nonfork = None

            if None not in (public_total, public_forks, public_nonfork):
                counts = {
                    "public_owned_total": public_total,
                    "public_owned_forks": public_forks,
                    "public_owned_nonfork": public_nonfork,
                    "private_owned": private_owned,
                    "private_owned_nonfork": private_owned_nonfork,
                }
                if _owned_repo_counts_are_valid(
                    counts,
                    private_capability=private_capability,
                ):
                    _set_cached(
                        cache_key,
                        _owned_repo_scope_count_envelope(
                            counts,
                            private_capability=private_capability,
                            verified_oauth_scopes=(
                                last_query_oauth_scopes()
                                if private_capability == "personal_github_token"
                                else None
                            ),
                        ),
                    )
                    return counts

    # Fallback: public REST only.
    all_public = get_repos(include_forks=True)
    public_nonfork = get_repos(include_forks=False)
    public_total = len(all_public)
    public_nonfork_total = len(public_nonfork)
    counts = {
        "public_owned_total": public_total,
        "public_owned_forks": max(0, public_total - public_nonfork_total),
        "public_owned_nonfork": public_nonfork_total,
        "private_owned": None,
        "private_owned_nonfork": None,
    }
    _set_cached(
        cache_key,
        _owned_repo_scope_count_envelope(
            counts,
            private_capability="unavailable",
        ),
    )
    return counts


def get_repo_languages(owner: str, repo: str) -> dict:
    """Get language byte counts for a single repo."""
    cache_key = f"langs_{owner}_{repo}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    url = f"{API}/repos/{owner}/{repo}/languages"
    resp = _request_with_retry(url)
    data = resp.json() if resp.status_code == 200 else {}
    _set_cached(cache_key, data)
    return data


def get_all_languages(repos: list | None = None, max_workers: int = 10) -> dict:
    """Aggregate language byte counts across all repos (parallelized)."""
    if repos is None:
        repos = get_repos()

    population_facts = []
    for repo in repos:
        owner = repo.get("owner") if type(repo) is dict else None
        language_bytes = repo.get("language_bytes") if type(repo) is dict else None
        population_facts.append(
            {
                "owner": owner.get("login") if type(owner) is dict else None,
                "name": repo.get("name") if type(repo) is dict else None,
                "private": repo.get("private") if type(repo) is dict else None,
                "fork": repo.get("fork") if type(repo) is dict else None,
                "pushed_at": repo.get("pushed_at") if type(repo) is dict else None,
                "language_bytes": (
                    sorted(language_bytes.items())
                    if type(language_bytes) is dict
                    else None
                ),
                "language_bytes_complete": (
                    repo.get("language_bytes_complete")
                    if type(repo) is dict
                    else None
                ),
            }
        )
    population_signature = hashlib.sha256(
        json.dumps(
            sorted(
                population_facts,
                key=lambda fact: (
                    str(fact.get("owner") or "").casefold(),
                    str(fact.get("name") or "").casefold(),
                ),
            ),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    cache_key = "all_languages_aggregated"
    cached = _get_cached(cache_key)
    if (
        type(cached) is dict
        and cached.get("schema") == "language-aggregate/v1"
        and cached.get("username") == USERNAME.casefold()
        and cached.get("population_signature") == population_signature
        and cached.get("complete") is True
        and type(cached.get("totals")) is dict
        and all(
            type(language) is str
            and bool(language)
            and type(byte_count) is int
            and byte_count > 0
            for language, byte_count in cached["totals"].items()
        )
    ):
        return cached["totals"]

    def cache_complete_totals(totals: dict) -> None:
        _set_cached(
            cache_key,
            {
                "schema": "language-aggregate/v1",
                "username": USERNAME.casefold(),
                "population_signature": population_signature,
                "complete": True,
                "totals": totals,
            },
        )

    # Preferred path when repos were fetched from GraphQL:
    # language bytes are already embedded and require no extra API calls.
    if all(
        type(repo) is dict
        and type(repo.get("language_bytes")) is dict
        and repo.get("language_bytes_complete") is True
        for repo in repos
    ):
        totals = {}
        for repo in repos:
            language_bytes = repo.get("language_bytes") or {}
            if not isinstance(language_bytes, dict):
                continue
            for lang, bytes_ in language_bytes.items():
                try:
                    amount = int(bytes_)
                except (TypeError, ValueError):
                    amount = 0
                if amount > 0:
                    totals[lang] = totals.get(lang, 0) + amount
        cache_complete_totals(totals)
        return totals

    totals = {}

    def fetch_one(repo):
        return get_repo_languages(repo["owner"]["login"], repo["name"])

    complete = True
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fetch_one, r): r for r in repos}
        for f in as_completed(futures):
            try:
                langs = f.result()
                if type(langs) is not dict:
                    complete = False
                    continue
                for lang, bytes_ in langs.items():
                    if type(lang) is not str or not lang:
                        complete = False
                        continue
                    try:
                        amount = int(bytes_)
                    except (TypeError, ValueError):
                        complete = False
                        continue
                    if amount > 0:
                        totals[lang] = totals.get(lang, 0) + amount
                    elif amount < 0:
                        complete = False
            except Exception as exc:
                complete = False
                repo = futures[f]
                print(f"  Warning: failed to fetch languages for {repo['name']}: {exc}")

    if complete:
        cache_complete_totals(totals)
    return totals


def _canonical_public_event(raw_event: object, *, evidence_status: str) -> dict | None:
    """Return one safe metadata-only event row, or omit an unsupported row."""
    if type(raw_event) is not dict:
        return None
    event_type = raw_event.get("type")
    if event_type not in _EVENT_TYPES:
        return None
    event_id = raw_event.get("id")
    repo = raw_event.get("repo")
    repo_full_name = repo.get("name") if type(repo) is dict else None
    actor = raw_event.get("actor")
    actor_login = actor.get("login") if type(actor) is dict else None
    occurred_at = raw_event.get("created_at")
    if (
        type(event_id) is not str
        or not event_id
        or type(repo_full_name) is not str
        or repo_full_name.count("/") != 1
        or _parse_iso_datetime(occurred_at) is None
    ):
        return None
    payload = raw_event.get("payload")
    if type(payload) is not dict:
        payload = {}
    base = {
        "event_id": event_id,
        "event_type": event_type,
        "repo_full_name": repo_full_name,
        "repo_url": f"https://github.com/{repo_full_name}",
        "actor_login": actor_login if isinstance(actor_login, str) else None,
        "occurred_at": _iso_utc(_parse_iso_datetime(occurred_at)),
        "is_private": False,
        "source_id": "github_rest_public_events",
        "evidence_status": evidence_status,
    }

    if event_type == "PushEvent":
        commits = payload.get("commits")
        if type(commits) is not list:
            commits = []
        headlines = tuple(
            headline
            for commit in commits
            if type(commit) is dict
            and (headline := _safe_summary(commit.get("message"), first_line=True))
        )
        row = {**base, "commit_headlines": headlines}
    elif event_type == "PullRequestEvent":
        pull_request = payload.get("pull_request")
        if type(pull_request) is not dict:
            return None
        action = payload.get("action")
        number = pull_request.get("number")
        state = pull_request.get("state")
        title = _safe_summary(pull_request.get("title"))
        url = pull_request.get("html_url")
        if not isinstance(url, str) or not url:
            url = f"https://github.com/{repo_full_name}/pull/{number}"
        row = {
            **base,
            "action": action,
            "number": number,
            "title": title,
            "state": state,
            "merged": pull_request.get("merged") is True,
            "url": url,
        }
    elif event_type == "ReleaseEvent":
        release = payload.get("release")
        if type(release) is not dict:
            return None
        action = payload.get("action") or "published"
        tag_name = _safe_summary(release.get("tag_name"))
        url = release.get("html_url")
        if not isinstance(url, str) or not url:
            url = f"https://github.com/{repo_full_name}/releases/tag/{tag_name}"
        row = {**base, "action": action, "tag_name": tag_name, "url": url}
    elif event_type == "IssuesEvent":
        issue = payload.get("issue")
        if type(issue) is not dict:
            return None
        number = issue.get("number")
        url = issue.get("html_url")
        if not isinstance(url, str) or not url:
            url = f"https://github.com/{repo_full_name}/issues/{number}"
        row = {
            **base,
            "action": payload.get("action"),
            "number": number,
            "title": _safe_summary(issue.get("title")),
            "state": issue.get("state"),
            "url": url,
        }
    else:
        issue = payload.get("pull_request") or payload.get("issue")
        if type(issue) is not dict:
            return None
        number = issue.get("number")
        item_kind = "pull" if event_type == "PullRequestReviewEvent" else "issues"
        url = issue.get("html_url")
        if not isinstance(url, str) or not url:
            url = f"https://github.com/{repo_full_name}/{item_kind}/{number}"
        row = {
            **base,
            "action": payload.get("action"),
            "number": number,
            "url": url,
        }

    return row if _valid_event_metadata_row(row, evidence_status=evidence_status) else None


def get_events_observation(per_page: int = 100, max_pages: int = 3) -> dict:
    """Observe the bounded public-events feed without laundering partial pages."""
    page_size = max(1, min(100, int(per_page)))
    page_limit = max(1, min(3, int(max_pages)))
    query_signature = f"{USERNAME}:{page_size}:{page_limit}:300"
    cache_key = f"events_observation_v1_{page_size}_{page_limit}_{USERNAME.casefold()}"
    cached = _get_cached(cache_key)
    if (
        validate_provider_observation(cached)
        and cached.get("metric_id") == "recent_public_events"
        and cached.get("status") == "ok"
        and cached.get("complete") is True
        and cached.get("population_signature") == query_signature
    ):
        replay = dict(cached)
        replay["source_mode"] = "cache"
        replay["completion_reason"] = "same_scope_cache"
        return replay

    rows: list[dict] = []
    terminal_reason = "provider_cap"
    page_error = False
    observed_at = _iso_utc(datetime.now(timezone.utc))
    url = f"{API}/users/{USERNAME}/events/public"
    for page in range(1, page_limit + 1):
        params = {"per_page": page_size, "page": page}
        try:
            response = _request_with_retry(url, params=params)
        except requests.RequestException as exc:
            response = None
            status = exc.response.status_code if isinstance(exc, requests.HTTPError) and exc.response is not None else None
            if status in {401, 403}:
                try:
                    response = _request_public_with_retry(url, params=params)
                except requests.RequestException:
                    response = None
        if response is None or response.status_code != 200:
            page_error = True
            terminal_reason = "page_error"
            break
        try:
            payload = response.json()
        except ValueError:
            page_error = True
            terminal_reason = "page_error"
            break
        if type(payload) is not list:
            page_error = True
            terminal_reason = "page_error"
            break
        for raw_event in payload:
            row = _canonical_public_event(raw_event, evidence_status="ok")
            if row is not None:
                rows.append(row)
        if len(payload) < page_size:
            terminal_reason = "terminal_page"
            break

    if page_error:
        partial_rows = tuple({**row, "evidence_status": "partial"} for row in rows)
        return _validated_observation(
            metric_id="recent_public_events",
            source_metric_id="github_public_event_metadata_rows",
            value=partial_rows,
            status="partial",
            complete=False,
            population_id="public-user-events-feed",
            population_signature=query_signature,
            window_start=None,
            window_end=None,
            observed_at=observed_at,
            source_id="github_rest_public_events",
            source_mode="live",
            completion_reason="page_error",
        )

    observation = _validated_observation(
        metric_id="recent_public_events",
        source_metric_id="github_public_event_metadata_rows",
        value=tuple(rows),
        status="ok",
        complete=True,
        population_id="public-user-events-feed",
        population_signature=query_signature,
        window_start=None,
        window_end=None,
        observed_at=observed_at,
        source_id="github_rest_public_events",
        source_mode="live",
        completion_reason=terminal_reason,
    )
    _set_cached(cache_key, observation)
    return observation


def get_events(per_page: int = 100, max_pages: int = 3) -> list:
    """Compatibility projection of safe complete or partial event metadata rows."""
    observation = get_events_observation(per_page=per_page, max_pages=max_pages)
    value = observation.get("value")
    return list(value) if type(value) in {list, tuple} else []


def _count_repo_releases_since(owner: str, repo: str, cutoff: datetime, per_page: int = 100) -> int | None:
    cache_key = f"repo_releases_since_{owner}_{repo}_{cutoff.date().isoformat()}"
    cached = _get_cached(cache_key)
    if cached is not None:
        try:
            return int(cached)
        except (TypeError, ValueError):
            return None

    url = f"{API}/repos/{owner}/{repo}/releases"
    total = 0
    page = 1

    while True:
        params = {"per_page": per_page, "page": page}
        try:
            resp = _request_with_retry(url, params=params)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 404:
                _set_cached(cache_key, 0)
                return 0
            if status in {401, 403}:
                try:
                    resp = _request_public_with_retry(url, params=params)
                except requests.HTTPError as public_exc:
                    public_status = public_exc.response.status_code if public_exc.response is not None else None
                    if public_status == 404:
                        _set_cached(cache_key, 0)
                        return 0
                    return None
            else:
                return None

        if resp.status_code != 200:
            return None

        payload = resp.json()
        if not isinstance(payload, list):
            return None
        if not payload:
            break

        reached_older_release = False
        for release in payload:
            if not isinstance(release, dict):
                continue
            when = str(release.get("published_at") or release.get("created_at") or "")
            released_at = _parse_iso_datetime(when)
            if released_at is None:
                continue
            if released_at >= cutoff:
                total += 1
            else:
                reached_older_release = True

        if reached_older_release or len(payload) < per_page:
            break
        page += 1

    _set_cached(cache_key, total)
    return total


def get_releases_last_n_days_observation(
    repos: list | None = None,
    days: int = 30,
    max_workers: int = 8,
) -> dict:
    """Observe releases for one exact repository population and rolling window."""
    if repos is None:
        repos = get_repos(include_forks=False)
    window_days = max(1, int(days))
    start, end, window_day = _calendar_window(window_days)
    window_start = _iso_utc(start)
    window_end = _iso_utc(end)
    repo_sig = _repo_signature(repos)
    cache_key = f"releases_observation_v1_{window_days}_{window_day}_{repo_sig}"
    cached = _get_cached(cache_key)
    if (
        validate_provider_observation(cached)
        and cached.get("metric_id") == "releases_30d"
        and cached.get("source_metric_id") == "owned_public_nonfork_releases"
        and cached.get("status") == "ok"
        and cached.get("population_signature") == repo_sig
        and cached.get("window_start") == window_start
        and cached.get("window_end") == window_end
    ):
        replay = dict(cached)
        replay["source_mode"] = "cache"
        replay["completion_reason"] = "same_scope_cache"
        return replay

    if not repos:
        observation = _validated_observation(
            metric_id="releases_30d",
            source_metric_id="owned_public_nonfork_releases",
            value=0,
            status="ok",
            complete=True,
            population_id="owned-public-nonfork-repositories",
            population_signature=repo_sig,
            window_start=window_start,
            window_end=window_end,
            observed_at=_iso_utc(datetime.now(timezone.utc)),
            source_id="github_rest_repo_releases",
            source_mode="live",
            completion_reason="empty_population",
        )
        _set_cached(cache_key, observation)
        return observation

    total_known = 0
    unknown_repos = 0

    def fetch_one(repo_obj: dict) -> int | None:
        owner = repo_obj.get("owner", {}).get("login", USERNAME)
        name = repo_obj.get("name", "")
        if not name:
            return 0
        return _count_repo_releases_since(owner, name, start)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fetch_one, repo): repo for repo in repos}
        for future in as_completed(futures):
            try:
                count = future.result()
            except Exception:
                count = None
            if count is None:
                unknown_repos += 1
            else:
                total_known += int(count)

    if unknown_repos:
        print(f"  Warning: release counting unavailable for {unknown_repos} repos")
        return _validated_observation(
            metric_id="releases_30d",
            source_metric_id="owned_public_nonfork_releases",
            value=None,
            status="unavailable",
            complete=False,
            population_id="owned-public-nonfork-repositories",
            population_signature=repo_sig,
            window_start=window_start,
            window_end=window_end,
            observed_at=None,
            source_id="github_rest_repo_releases",
            source_mode="live",
            completion_reason="component_unavailable",
        )

    observation = _validated_observation(
        metric_id="releases_30d",
        source_metric_id="owned_public_nonfork_releases",
        value=total_known,
        status="ok",
        complete=True,
        population_id="owned-public-nonfork-repositories",
        population_signature=repo_sig,
        window_start=window_start,
        window_end=window_end,
        observed_at=_iso_utc(datetime.now(timezone.utc)),
        source_id="github_rest_repo_releases",
        source_mode="live",
        completion_reason="all_components_observed",
    )
    _set_cached(cache_key, observation)
    return observation


def get_releases_last_n_days(
    repos: list | None = None,
    days: int = 30,
    max_workers: int = 8,
) -> int | None:
    """Exact-only compatibility projection of the release observation."""
    observation = get_releases_last_n_days_observation(
        repos=repos,
        days=days,
        max_workers=max_workers,
    )
    return observation["value"] if observation.get("status") == "ok" else None


def _get_recent_release_cache(days: int, exclude_signature: str) -> int | None:
    """Return a recent cached release count for the same day window when available."""
    prefix = f"releases_last_{days}_"
    candidates: list[tuple[float, Path]] = []
    try:
        for path in CACHE_DIR.glob(f"{prefix}*.json"):
            if path.stem.endswith(exclude_signature):
                continue
            candidates.append((path.stat().st_mtime, path))
    except OSError:
        return None

    for _mtime, path in sorted(candidates, key=lambda item: item[0], reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(payload, dict):
            total = payload.get("total")
        else:
            total = payload
        try:
            return int(total)
        except (TypeError, ValueError):
            continue
    return None


def get_merged_prs_last_n_days_observation(days: int = 365) -> dict:
    """Observe merged pull requests without collapsing public retry scope."""
    window_days = max(1, int(days))
    start, end, window_day = _calendar_window(window_days)
    since = start.date().isoformat()
    window_start = _iso_utc(start)
    window_end = _iso_utc(end)
    cache_key = f"merged_prs_observation_v1_{window_days}_{window_day}"
    cached = _get_cached(cache_key)
    if (
        validate_provider_observation(cached)
        and cached.get("metric_id") == "prs_merged"
        and cached.get("window_start") == window_start
        and cached.get("window_end") == window_end
        and cached.get("status") in {"ok", "fallback"}
    ):
        replay = dict(cached)
        replay["source_mode"] = "cache"
        if replay.get("status") == "ok":
            replay["completion_reason"] = "same_scope_cache"
        return replay

    query = f"author:{USERNAME} user:{USERNAME} is:pr is:merged merged:>={since}"
    params = {"q": query, "per_page": 1}
    url = f"{API}/search/issues"

    def _fetch_total(use_public: bool) -> int | None:
        requester = _request_public_with_retry if use_public else _request_with_retry
        try:
            resp = requester(url, params=params)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status in {401, 403, 422}:
                return None
            raise
        except requests.RequestException:
            return None

        if resp.status_code != 200:
            return None
        try:
            payload = resp.json()
        except ValueError:
            return None
        if not isinstance(payload, dict):
            return None
        try:
            return int(payload.get("total_count", 0))
        except (TypeError, ValueError):
            return None

    total = _fetch_total(use_public=False)
    if total is not None:
        observation = _validated_observation(
            metric_id="prs_merged",
            source_metric_id="merged_prs_primary_visible_population",
            value=total,
            status="ok",
            complete=True,
            population_id="owned-repositories-visible-to-primary-pr-search",
            population_signature=None,
            window_start=window_start,
            window_end=window_end,
            observed_at=_iso_utc(datetime.now(timezone.utc)),
            source_id="github_rest_merged_pr_search_primary",
            source_mode="live",
            completion_reason="all_components_observed",
        )
        _set_cached(cache_key, observation)
        return observation

    public_total = _fetch_total(use_public=True) if TOKEN else None
    if public_total is not None:
        observation = _validated_observation(
            metric_id="prs_merged",
            source_metric_id="merged_prs_public_visible_population",
            value=public_total,
            status="fallback",
            complete=True,
            population_id="owned-public-repositories-visible-to-public-pr-search",
            population_signature=None,
            window_start=window_start,
            window_end=window_end,
            observed_at=_iso_utc(datetime.now(timezone.utc)),
            source_id="github_rest_merged_pr_search_public",
            source_mode="fallback",
            completion_reason="public_retry",
        )
        _set_cached(cache_key, observation)
        return observation

    return _validated_observation(
        metric_id="prs_merged",
        source_metric_id="merged_prs_primary_visible_population",
        value=None,
        status="unavailable",
        complete=False,
        population_id="owned-repositories-visible-to-primary-pr-search",
        population_signature=None,
        window_start=window_start,
        window_end=window_end,
        observed_at=None,
        source_id="github_rest_merged_pr_search_primary",
        source_mode="live",
        completion_reason="unavailable",
    )


def get_merged_prs_last_n_days(days: int = 365) -> int | None:
    """Exact-only compatibility projection of the merged-PR observation."""
    observation = get_merged_prs_last_n_days_observation(days=days)
    return observation["value"] if observation.get("status") == "ok" else None


def _get_recent_merged_pr_cache(window_days: int, exclude_day: str) -> int | None:
    """Return the most recent cached merged PR total for the same window when available."""
    prefix = f"merged_prs_last_{window_days}_"
    candidates: list[tuple[str, Path]] = []
    try:
        for path in CACHE_DIR.glob(f"{prefix}*.json"):
            day = path.stem.replace(prefix, "", 1)
            if day == exclude_day:
                continue
            candidates.append((day, path))
    except OSError:
        return None

    for _day, path in sorted(candidates, key=lambda item: item[0], reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(payload, dict):
            total = payload.get("total")
        else:
            total = payload
        try:
            return int(total)
        except (TypeError, ValueError):
            continue
    return None


def _contribution_value_from_calendar(calendar: object) -> dict | None:
    if type(calendar) is not dict:
        return None
    total = calendar.get("totalContributions")
    if not _is_nonnegative_int(total):
        return None
    weeks = calendar.get("weeks")
    if type(weeks) is not list:
        return None
    days: list[dict] = []
    for week in weeks:
        if type(week) is not dict or type(week.get("contributionDays")) is not list:
            return None
        for day in week["contributionDays"]:
            if type(day) is not dict:
                return None
            day_value = {"date": day.get("date"), "count": day.get("contributionCount")}
            if not _valid_contribution_value({"total": total, "days": (day_value,)}):
                return None
            days.append(day_value)
    return {"total": total, "days": tuple(days)}


def _calendar_from_contribution_value(value: object) -> dict | None:
    if not _valid_contribution_value(value):
        return None
    grouped: dict[tuple[int, int], list[dict]] = {}
    for day in value["days"]:
        parsed = datetime.strptime(day["date"], "%Y-%m-%d")
        iso_year, iso_week, _weekday = parsed.isocalendar()
        grouped.setdefault((iso_year, iso_week), []).append(
            {
                "date": day["date"],
                "contributionCount": day["count"],
                "weekday": parsed.weekday(),
            }
        )
    return {
        "totalContributions": value["total"],
        "weeks": [
            {"contributionDays": grouped[key]}
            for key in sorted(grouped)
        ],
    }


def get_contribution_calendar_observation(days: int = 365) -> dict:
    """Observe the current contribution calendar with its exact source window."""
    start, end, window_day = _calendar_window(days)
    tz_name = os.environ.get("PROFILE_TIMEZONE", "America/New_York").strip() or "America/New_York"
    window_start = _iso_utc(start)
    window_end = _iso_utc(end)
    cache_key = f"contribution_calendar_observation_v1_{days}_{tz_name}_{window_day}"
    cached = _get_cached(cache_key)
    if (
        validate_provider_observation(cached)
        and cached.get("metric_id") == "last_year_contributions"
        and cached.get("source_metric_id") == "github_contribution_calendar_total_and_days"
        and cached.get("status") == "ok"
        and cached.get("window_start") == window_start
        and cached.get("window_end") == window_end
    ):
        replay = dict(cached)
        replay["source_mode"] = "cache"
        replay["completion_reason"] = "same_scope_cache"
        return replay

    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                weekday
              }
            }
          }
        }
      }
    }
    """
    data = _graphql_query(
        query,
        {
            "login": USERNAME,
            "from": start.isoformat().replace("+00:00", "Z"),
            "to": end.isoformat().replace("+00:00", "Z"),
        },
    )
    if not isinstance(data, dict):
        return _validated_observation(
            metric_id="last_year_contributions",
            source_metric_id="github_contribution_calendar_total_and_days",
            value=None,
            status="unavailable",
            complete=False,
            population_id="github-contribution-calendar-visible-to-provider",
            population_signature=None,
            window_start=window_start,
            window_end=window_end,
            observed_at=None,
            source_id="github_graphql_contribution_calendar",
            source_mode="live",
            completion_reason="unavailable",
        )

    try:
        cal = data["user"]["contributionsCollection"]["contributionCalendar"]
        value = _contribution_value_from_calendar(cal)
    except (KeyError, TypeError):
        value = None
    if value is None:
        return _validated_observation(
            metric_id="last_year_contributions",
            source_metric_id="github_contribution_calendar_total_and_days",
            value=None,
            status="unavailable",
            complete=False,
            population_id="github-contribution-calendar-visible-to-provider",
            population_signature=None,
            window_start=window_start,
            window_end=window_end,
            observed_at=None,
            source_id="github_graphql_contribution_calendar",
            source_mode="live",
            completion_reason="unavailable",
        )
    observation = _validated_observation(
        metric_id="last_year_contributions",
        source_metric_id="github_contribution_calendar_total_and_days",
        value=value,
        status="ok",
        complete=True,
        population_id="github-contribution-calendar-visible-to-provider",
        population_signature=None,
        window_start=window_start,
        window_end=window_end,
        observed_at=_iso_utc(datetime.now(timezone.utc)),
        source_id="github_graphql_contribution_calendar",
        source_mode="live",
        completion_reason="all_components_observed",
    )
    _set_cached(cache_key, observation)
    return observation


def get_contribution_calendar(days: int = 365) -> dict | None:
    """Exact-only compatibility projection of the contribution observation."""
    observation = get_contribution_calendar_observation(days=days)
    if observation.get("status") != "ok":
        return None
    return _calendar_from_contribution_value(observation.get("value"))


def get_repo_commits_last_n_weeks(owner: str, repo: str, weeks: int = 12) -> list:
    """Get weekly commit counts for last N weeks (participation stats)."""
    cache_key = f"participation_{owner}_{repo}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    url = f"{API}/repos/{owner}/{repo}/stats/participation"
    try:
        resp = _request_with_retry(url)
    except requests.RequestException as exc:
        status = (
            exc.response.status_code
            if isinstance(exc, requests.HTTPError) and exc.response is not None
            else "network"
        )
        # This endpoint is not always accessible for every repo/token context.
        print(f"  Warning: participation stats unavailable for {owner}/{repo} ({status}); using zeros")
        return [0] * weeks

    if resp.status_code != 200:
        # GitHub can return 202 while stats are being generated.
        return [0] * weeks

    data = resp.json()
    owner_commits = data.get("owner", [])[-weeks:]
    if not isinstance(owner_commits, list):
        return [0] * weeks

    _set_cached(cache_key, owner_commits)
    return owner_commits


class _ObservedCommitCount(int):
    """Integer component result carrying its source observation identity."""

    def __new__(
        cls,
        value: int,
        *,
        observed_at: str,
        source_mode: str,
    ):
        instance = super().__new__(cls, value)
        instance.observed_at = observed_at
        instance.source_mode = source_mode
        return instance


def _validated_repo_user_commit_cache(cached) -> _ObservedCommitCount | None:
    if (
        type(cached) is not dict
        or set(cached) != {"schema", "count", "observed_at"}
        or cached.get("schema") != _REPO_USER_COMMIT_CACHE_SCHEMA
        or not _is_nonnegative_int(cached.get("count"))
        or type(cached.get("observed_at")) is not str
        or _parse_iso_datetime(cached.get("observed_at")) is None
    ):
        return None
    return _ObservedCommitCount(
        cached["count"],
        observed_at=cached["observed_at"],
        source_mode="cache",
    )


def get_repo_user_commit_count(owner: str, repo: str) -> int | None:
    """
    Get total commits by USERNAME in a repo.

    Returns:
      - int: a concrete commit count
      - None: the count could not be determined for this repo in this run
    """
    cache_key = f"repo_user_commits_v2_{owner}_{repo}_{USERNAME}"
    cached_count = _validated_repo_user_commit_cache(_get_cached(cache_key))
    if cached_count is not None:
        return cached_count

    def _cache_and_return(value: int | None) -> int | None:
        if not _is_nonnegative_int(value):
            return None
        observed_at = _iso_utc(datetime.now(timezone.utc))
        _set_cached(
            cache_key,
            {
                "schema": _REPO_USER_COMMIT_CACHE_SCHEMA,
                "count": value,
                "observed_at": observed_at,
            },
        )
        return _ObservedCommitCount(
            value,
            observed_at=observed_at,
            source_mode="live",
        )

    try:
        contributors = paginated_get(
            f"repos/{owner}/{repo}/contributors",
            {"anon": "false"},
            per_page=100,
        )
        if contributors:
            for contributor in contributors:
                login = contributor.get("login", "")
                if login.lower() == USERNAME.lower():
                    count = int(contributor.get("contributions", 0))
                    return _cache_and_return(count)
            return _cache_and_return(0)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status not in {401, 403, 404}:
            raise

    # Fallback path for restricted/empty contributors responses:
    # commits endpoint filtered by author.
    try:
        count = _count_commits_from_commits_endpoint(owner, repo, use_public=False)
        return _cache_and_return(count)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status == 409:
            return _cache_and_return(0)
        if status not in {401, 403, 404}:
            raise

    try:
        count = _count_commits_from_commits_endpoint(owner, repo, use_public=True)
        return _cache_and_return(count)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status == 409:
            return _cache_and_return(0)
        if status in {401, 403, 404}:
            return None
        raise


def get_total_commit_contributions_via_graphql() -> int | None:
    """Fallback total commit metric using GraphQL contributionsCollection."""
    cache_key = "total_commit_contributions_graphql_all_time"
    cached = _get_cached(cache_key)
    if cached is not None:
        return int(cached)

    if not TOKEN:
        return None

    created_query = """
    query($login: String!) {
      user(login: $login) {
        createdAt
      }
    }
    """
    created_data = _graphql_query(created_query, {"login": USERNAME})
    try:
        created_at = created_data["user"]["createdAt"]
        start_year = datetime.fromisoformat(created_at.replace("Z", "+00:00")).year
    except (TypeError, KeyError, ValueError, AttributeError):
        start_year = 2008

    current_year = datetime.now(timezone.utc).year
    year_query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
        }
      }
    }
    """
    total = 0
    saw_value = False
    for year in range(start_year, current_year + 1):
        data = _graphql_query(
            year_query,
            {
                "login": USERNAME,
                "from": f"{year}-01-01T00:00:00Z",
                "to": f"{year}-12-31T23:59:59Z",
            },
        )
        try:
            year_total = int(data["user"]["contributionsCollection"]["totalCommitContributions"])
            total += year_total
            saw_value = True
        except (TypeError, KeyError, ValueError):
            continue

    if not saw_value:
        return None

    _set_cached(cache_key, total)
    return total


def get_total_commits_observation(
    repos: list | None = None,
    max_workers: int = 4,
    use_global_fallback: bool = False,
) -> dict:
    """Observe exact per-repository commits and retain broader fallbacks by identity."""
    if repos is None:
        repos = get_repos(include_forks=False)
    repo_sig = _repo_signature(repos)
    cache_key = (
        "total_commits_observation_v1_owned_public_nonfork_"
        f"{repo_sig}_{int(use_global_fallback)}"
    )
    cached = _get_cached(cache_key)
    if (
        validate_provider_observation(cached)
        and cached.get("metric_id") == "public_scope_commits"
        and (
            cached.get("population_signature") == repo_sig
            if cached.get("status") == "ok"
            else cached.get("population_signature") is None
        )
    ):
        replay = dict(cached)
        replay["source_mode"] = "cache"
        if replay.get("status") == "ok":
            replay["completion_reason"] = "same_scope_cache"
        return replay

    total_known = 0
    unknown = 0
    failures = 0
    component_observation_times: list[datetime] = []
    used_component_cache = False

    def fetch_one(repo):
        return get_repo_user_commit_count(repo["owner"]["login"], repo["name"])

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fetch_one, r): r for r in repos}
        for f in as_completed(futures):
            repo = futures[f]
            try:
                count = f.result()
                if count is None:
                    unknown += 1
                else:
                    total_known += int(count)
                    component_observed_at = getattr(count, "observed_at", None)
                    parsed_component_time = (
                        _parse_iso_datetime(component_observed_at)
                        if isinstance(component_observed_at, str)
                        else None
                    )
                    if parsed_component_time is not None:
                        component_observation_times.append(parsed_component_time)
                    if getattr(count, "source_mode", None) == "cache":
                        used_component_cache = True
            except Exception as exc:
                failures += 1
                print(f"  Warning: commit count failed for {repo['name']}: {exc}")

    total: int | None
    if not repos:
        total = 0
    elif unknown > 0 or failures > 0:
        total = None
    else:
        total = total_known

    aggregate_time = datetime.now(timezone.utc)
    observed_at = _iso_utc(
        min([aggregate_time, *component_observation_times])
        if component_observation_times
        else aggregate_time
    )
    if total is not None:
        source_mode = "cache" if used_component_cache else "live"
        completion_reason = (
            "empty_population"
            if not repos
            else "same_scope_cache"
            if used_component_cache
            else "all_components_observed"
        )
        observation = _validated_observation(
            metric_id="public_scope_commits",
            source_metric_id="owned_public_nonfork_authored_commits",
            value=total,
            status="ok",
            complete=True,
            population_id="owned-public-nonfork-repositories",
            population_signature=repo_sig,
            window_start=None,
            window_end=None,
            observed_at=observed_at,
            source_id="github_rest_repo_commits",
            source_mode=source_mode,
            completion_reason=completion_reason,
        )
        _set_cached(cache_key, observation)
        return observation

    # Broader sources remain useful typed evidence, but never become the exact
    # owned-public-nonfork compatibility result.
    if use_global_fallback and repos and total is None:
        fallback_total = get_total_commit_contributions_via_graphql()
        if fallback_total is not None:
            print("  Info: using GraphQL commit contribution fallback for total commits")
            observation = _validated_observation(
                metric_id="public_scope_commits",
                source_metric_id="github_total_commit_contributions",
                value=int(fallback_total),
                status="fallback",
                complete=True,
                population_id="github-user-contributions-visible-to-provider",
                population_signature=None,
                window_start=None,
                window_end=None,
                observed_at=observed_at,
                source_id="github_graphql_commit_contributions",
                source_mode="fallback",
                completion_reason="different_metric_fallback",
            )
            _set_cached(cache_key, observation)
            return observation

        calendar = get_contribution_calendar()
        if isinstance(calendar, dict):
            calendar_total = calendar.get("totalContributions")
            if _is_nonnegative_int(calendar_total):
                print("  Info: using contribution-calendar fallback for total commits")
                observation = _validated_observation(
                    metric_id="public_scope_commits",
                    source_metric_id="github_contribution_calendar_total",
                    value=calendar_total,
                    status="fallback",
                    complete=True,
                    population_id="github-contribution-calendar-visible-to-provider",
                    population_signature=None,
                    window_start=None,
                    window_end=None,
                    observed_at=observed_at,
                    source_id="github_graphql_contribution_calendar",
                    source_mode="fallback",
                    completion_reason="different_metric_fallback",
                )
                _set_cached(cache_key, observation)
                return observation

    return _validated_observation(
        metric_id="public_scope_commits",
        source_metric_id="owned_public_nonfork_authored_commits",
        value=None,
        status="unavailable",
        complete=False,
        population_id="owned-public-nonfork-repositories",
        population_signature=repo_sig,
        window_start=None,
        window_end=None,
        observed_at=None,
        source_id="github_rest_repo_commits",
        source_mode="live",
        completion_reason="component_unavailable",
    )


def get_total_commits(
    repos: list | None = None,
    max_workers: int = 4,
    use_global_fallback: bool = False,
) -> int | None:
    """Exact-only compatibility projection of the public commit observation."""
    observation = get_total_commits_observation(
        repos=repos,
        max_workers=max_workers,
        use_global_fallback=use_global_fallback,
    )
    return observation["value"] if observation.get("status") == "ok" else None


def get_repos_with_ci(repos: list | None = None, max_workers: int = 10) -> int:
    """Count repos that have CI/CD workflows."""
    if repos is None:
        repos = get_repos()
    cache_key = f"ci_count_{_repo_signature(repos)}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    if repos and all("has_ci_workflows" in repo for repo in repos):
        count = sum(1 for repo in repos if bool(repo.get("has_ci_workflows")))
        _set_cached(cache_key, count)
        return count

    count = 0

    def check_ci(repo):
        owner = repo["owner"]["login"]
        name = repo["name"]
        per_repo_cache_key = f"repo_ci_state_{owner}_{name}"
        cached_state = _get_cached(per_repo_cache_key)
        if cached_state is not None:
            return bool(cached_state)

        url = f"{API}/repos/{owner}/{name}/contents/.github/workflows"
        try:
            resp = _request_with_retry(url)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            # 404 means the folder does not exist (normal for repos without Actions).
            if status == 404:
                _set_cached(per_repo_cache_key, False)
                return False
            # 401/403 can occur from token scope restrictions. Retry without auth.
            if status in {401, 403}:
                try:
                    resp = _request_public_with_retry(url)
                except requests.HTTPError as public_exc:
                    public_status = public_exc.response.status_code if public_exc.response is not None else None
                    if public_status == 404:
                        _set_cached(per_repo_cache_key, False)
                        return False
                    return None
            else:
                raise

        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                _set_cached(per_repo_cache_key, True)
                return True
            _set_cached(per_repo_cache_key, False)
            return False
        return False

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(check_ci, r) for r in repos]
        for f in as_completed(futures):
            try:
                result = f.result()
                if result is True:
                    count += 1
            except Exception as exc:
                print(f"  Warning: CI check failed: {exc}")

    _set_cached(cache_key, count)
    return count


def _unknown_repo_workflow_observation(reason: str) -> dict:
    return {
        "observed": False,
        "has_actions_config": None,
        "workflow_yaml_file_count": None,
        "unavailable_reason": reason,
    }


_REST_WORKFLOW_CACHE_SCHEMA_VERSION = 1
_REST_WORKFLOW_QUERY_ID = "github_rest_default_branch_workflows_v1"
_REST_WORKFLOW_OBSERVATION_KEYS = frozenset(
    {
        "observed",
        "has_actions_config",
        "workflow_yaml_file_count",
        "unavailable_reason",
    }
)
_REST_WORKFLOW_UNKNOWN_REASONS = frozenset(
    {"capability_unavailable", "malformed_observation"}
)
_REST_WORKFLOW_PUBLIC_POPULATION = "public_owned_nonfork_profile_excluded"
_REST_WORKFLOW_UNRESOLVED_POPULATION = "owned_repository_visibility_unresolved"


def _rest_workflow_cache_key(
    owner: str,
    repository: str,
    *,
    population: str = _REST_WORKFLOW_UNRESOLVED_POPULATION,
) -> str:
    if population not in {
        _REST_WORKFLOW_PUBLIC_POPULATION,
        _REST_WORKFLOW_UNRESOLVED_POPULATION,
    }:
        raise ValueError(f"unsupported REST workflow population {population!r}")
    bindings = (
        "provider=github",
        "transport=rest",
        f"query_id={_REST_WORKFLOW_QUERY_ID}",
        f"population_id={population}",
        f"scope={population}",
        "observation_kind=repository_workflow_configuration",
        f"owner={owner}",
        f"repository={repository}",
    )
    return (
        f"repo_actions_workflow_observation_v{_REST_WORKFLOW_CACHE_SCHEMA_VERSION}|"
        + "|".join(bindings)
    )


def _rest_workflow_cache_populations(
    owner: str,
    repository: str,
) -> tuple[str, ...]:
    if (
        owner.casefold() == USERNAME.casefold()
        and repository.casefold() != USERNAME.casefold()
    ):
        return (
            _REST_WORKFLOW_PUBLIC_POPULATION,
            _REST_WORKFLOW_UNRESOLVED_POPULATION,
        )
    return (_REST_WORKFLOW_UNRESOLVED_POPULATION,)


def _validated_rest_workflow_observation(value: object) -> dict | None:
    if not isinstance(value, dict) or set(value) != _REST_WORKFLOW_OBSERVATION_KEYS:
        return None
    observed = value.get("observed")
    configured = value.get("has_actions_config")
    file_count = value.get("workflow_yaml_file_count")
    reason = value.get("unavailable_reason")
    if type(observed) is not bool:
        return None
    if observed:
        if type(configured) is not bool or type(file_count) is not int:
            return None
        if file_count < 0 or configured is not (file_count > 0) or reason is not None:
            return None
    elif (
        configured is not None
        or file_count is not None
        or reason not in _REST_WORKFLOW_UNKNOWN_REASONS
    ):
        return None
    return dict(value)


def _rest_workflow_registry(
    owner: str,
    *,
    public_visibility_established: bool,
) -> tuple[str, dict, str]:
    if public_visibility_established:
        population = _REST_WORKFLOW_PUBLIC_POPULATION
        registry = {
            "kind": "provider",
            "registry_id": "github_actions_public_provider_v1",
            "query_id": _REST_WORKFLOW_QUERY_ID,
            "population_id": population,
            "owner": owner,
            "visibility_policy": "public",
            "fork_policy": "nonfork",
            "profile_row_policy": "owned_public_optional_single_self_excluded",
        }
        auth_capability = "public_visibility_established"
    else:
        population = _REST_WORKFLOW_UNRESOLVED_POPULATION
        registry = {
            "kind": "provider",
            "registry_id": "github_actions_authenticated_resource_provider_v1",
            "query_id": _REST_WORKFLOW_QUERY_ID,
            "population_id": population,
            "owner": owner,
            "visibility_policy": "authenticated_visible",
            "fork_policy": "unresolved",
            "profile_row_policy": "unresolved",
        }
        auth_capability = "authenticated_resource_observed"
    return population, registry, auth_capability


def _validate_rest_workflow_cache_envelope(
    value: object,
    *,
    owner: str,
    repository: str,
    expected_population: str,
) -> dict | None:
    top_keys = {
        "schema_version",
        "metric_id",
        "observation_kind",
        "observation_id",
        "observation_episode_id",
        "episode_started_at",
        "episode_ended_at",
        "population_id",
        "scope",
        "owner",
        "repository",
        "query_registry",
        "observed_at",
        "component_provenance",
        "observation",
    }
    if not isinstance(value, dict) or set(value) != top_keys:
        return None
    schema_version = value.get("schema_version")
    if (
        type(schema_version) is not int
        or schema_version != _REST_WORKFLOW_CACHE_SCHEMA_VERSION
    ):
        return None
    if value.get("metric_id") != "github_actions_configuration":
        return None
    if value.get("observation_kind") != "repository_workflow_configuration":
        return None
    if value.get("owner") != owner or value.get("repository") != repository:
        return None

    observation_id = value.get("observation_id")
    episode_id = value.get("observation_episode_id")
    if not isinstance(observation_id, str) or not observation_id:
        return None
    if not isinstance(episode_id, str) or not episode_id:
        return None

    registry = value.get("query_registry")
    if not isinstance(registry, dict):
        return None
    if expected_population not in {
        _REST_WORKFLOW_PUBLIC_POPULATION,
        _REST_WORKFLOW_UNRESOLVED_POPULATION,
    }:
        return None
    public_visibility_established = (
        expected_population == _REST_WORKFLOW_PUBLIC_POPULATION
    )
    population, expected_registry, auth_capability = _rest_workflow_registry(
        owner,
        public_visibility_established=public_visibility_established,
    )
    if (
        population != expected_population
        or value.get("population_id") != expected_population
        or value.get("scope") != expected_population
    ):
        return None
    if (
        public_visibility_established
        and owner.casefold() == USERNAME.casefold()
        and repository.casefold() == USERNAME.casefold()
    ):
        return None
    if registry != expected_registry:
        return None

    observation = _validated_rest_workflow_observation(value.get("observation"))
    if observation is None:
        return None
    if (
        not public_visibility_established
        and observation["observed"] is True
        and observation["has_actions_config"] is False
        and observation["workflow_yaml_file_count"] == 0
    ):
        # An authenticated resource response may establish an empty directory,
        # but a cached zero without the response cannot distinguish it from an
        # ambiguous 404. Revalidate that state unless public visibility is bound.
        return None

    provenance = value.get("component_provenance")
    if not isinstance(provenance, list) or len(provenance) != 1:
        return None
    component = provenance[0]
    component_keys = {
        "component_id",
        "observation_id",
        "query_id",
        "fetched_at",
        "observed_at",
        "source",
        "cache",
    }
    if not isinstance(component, dict) or set(component) != component_keys:
        return None
    if component.get("component_id") != "repository-workflow-configuration":
        return None
    if component.get("observation_id") != observation_id:
        return None
    if component.get("query_id") != _REST_WORKFLOW_QUERY_ID:
        return None

    source = component.get("source")
    expected_source = {
        "provider": "github",
        "transport": "rest",
        "owner": owner,
        "auth_capability": auth_capability,
    }
    if source != expected_source:
        return None
    cache = component.get("cache")
    cache_keys = {
        "source_mode",
        "payload_version",
        "cached_at",
        "derived_valid_until",
    }
    if not isinstance(cache, dict) or set(cache) != cache_keys:
        return None
    if cache.get("source_mode") != "cache":
        return None
    payload_version = cache.get("payload_version")
    if (
        type(payload_version) is not int
        or payload_version != _REST_WORKFLOW_CACHE_SCHEMA_VERSION
    ):
        return None

    timestamp_values = {
        "episode_started_at": value.get("episode_started_at"),
        "episode_ended_at": value.get("episode_ended_at"),
        "observed_at": value.get("observed_at"),
        "fetched_at": component.get("fetched_at"),
        "component_observed_at": component.get("observed_at"),
        "cached_at": cache.get("cached_at"),
        "derived_valid_until": cache.get("derived_valid_until"),
    }
    parsed = {
        key: _parse_iso_datetime(raw) if isinstance(raw, str) else None
        for key, raw in timestamp_values.items()
    }
    if any(stamp is None for stamp in parsed.values()):
        return None
    observed_at = parsed["observed_at"]
    if not (
        parsed["episode_started_at"]
        <= observed_at
        <= parsed["episode_ended_at"]
    ):
        return None
    if parsed["fetched_at"] != observed_at or parsed["component_observed_at"] != observed_at:
        return None
    cached_at = parsed["cached_at"]
    valid_until = parsed["derived_valid_until"]
    now = datetime.now(timezone.utc)
    future_limit = now + timedelta(minutes=5)
    ttl = timedelta(seconds=max(1, int(CACHE_TTL_SECONDS)))
    if observed_at > future_limit or cached_at > future_limit:
        return None
    if cached_at < observed_at or valid_until != observed_at + ttl:
        return None
    if now > valid_until:
        return None
    return observation


def _cache_rest_workflow_observation(
    _cache_key: str,
    *,
    owner: str,
    repository: str,
    observation: dict,
    public_visibility_established: bool,
) -> None:
    observed_at = datetime.now(timezone.utc).replace(microsecond=0)
    observed_stamp = observed_at.isoformat().replace("+00:00", "Z")
    valid_until = observed_at + timedelta(seconds=max(1, int(CACHE_TTL_SECONDS)))
    valid_until_stamp = valid_until.isoformat().replace("+00:00", "Z")
    digest = hashlib.sha256(
        f"{owner}\0{repository}\0{observed_stamp}".encode("utf-8")
    ).hexdigest()[:24]
    observation_id = f"rest-workflows-{digest}"
    episode_id = f"rest-workflows-episode-{digest}"
    population, registry, auth_capability = _rest_workflow_registry(
        owner,
        public_visibility_established=public_visibility_established,
    )
    envelope = {
        "schema_version": _REST_WORKFLOW_CACHE_SCHEMA_VERSION,
        "metric_id": "github_actions_configuration",
        "observation_kind": "repository_workflow_configuration",
        "observation_id": observation_id,
        "observation_episode_id": episode_id,
        "episode_started_at": observed_stamp,
        "episode_ended_at": observed_stamp,
        "population_id": population,
        "scope": population,
        "owner": owner,
        "repository": repository,
        "query_registry": registry,
        "observed_at": observed_stamp,
        "component_provenance": [
            {
                "component_id": "repository-workflow-configuration",
                "observation_id": observation_id,
                "query_id": _REST_WORKFLOW_QUERY_ID,
                "fetched_at": observed_stamp,
                "observed_at": observed_stamp,
                "source": {
                    "provider": "github",
                    "transport": "rest",
                    "owner": owner,
                    "auth_capability": auth_capability,
                },
                "cache": {
                    "source_mode": "cache",
                    "payload_version": _REST_WORKFLOW_CACHE_SCHEMA_VERSION,
                    "cached_at": observed_stamp,
                    "derived_valid_until": valid_until_stamp,
                },
            }
        ],
        "observation": observation,
    }
    cache_key = _rest_workflow_cache_key(
        owner,
        repository,
        population=population,
    )
    _set_cached(cache_key, envelope)


def _owned_public_visibility_is_established(owner: str, repository: str) -> bool:
    if type(owner) is not str or not owner:
        return False
    if type(repository) is not str or not repository:
        return False
    if owner.casefold() != USERNAME.casefold():
        return False
    if repository.casefold() == USERNAME.casefold():
        return False
    try:
        repositories = get_repos(include_forks=False)
    except Exception:
        return False
    if not isinstance(repositories, list):
        return False
    for candidate in repositories:
        if type(candidate) is not dict:
            continue
        name = candidate.get("name")
        candidate_owner = candidate.get("owner")
        visibility = candidate.get("visibility")
        private = candidate.get("private")
        fork = candidate.get("fork")
        if type(name) is not str or not name:
            continue
        if type(candidate_owner) is not dict:
            continue
        candidate_owner_login = candidate_owner.get("login")
        if (
            type(candidate_owner_login) is str
            and candidate_owner_login.casefold() == owner.casefold()
            and name.casefold() == repository.casefold()
            and type(visibility) is str
            and visibility == "public"
            and type(private) is bool
            and private is False
            and type(fork) is bool
            and fork is False
        ):
            return True
    return False


def _observed_absent_workflow_directory() -> dict:
    return {
        "observed": True,
        "has_actions_config": False,
        "workflow_yaml_file_count": 0,
        "unavailable_reason": None,
    }


def get_repo_workflow_observation(owner: str, repo: str) -> dict:
    """Observe default-branch Actions configuration through the REST API.

    This reports configuration presence and a lowercase workflow-YAML file
    count. Capability failures stay unknown; they never become an exact zero.
    """
    candidate_populations = _rest_workflow_cache_populations(owner, repo)
    for population in candidate_populations:
        cache_key = _rest_workflow_cache_key(
            owner,
            repo,
            population=population,
        )
        cached = _get_cached(cache_key)
        cached_observation = _validate_rest_workflow_cache_envelope(
            cached,
            owner=owner,
            repository=repo,
            expected_population=population,
        )
        if cached_observation is not None:
            return cached_observation

    cache_key = _rest_workflow_cache_key(owner, repo)

    url = f"{API}/repos/{owner}/{repo}/contents/.github/workflows"
    try:
        response = _request_with_retry(url)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status == 404:
            if not _owned_public_visibility_is_established(owner, repo):
                return _unknown_repo_workflow_observation("capability_unavailable")
            result = _observed_absent_workflow_directory()
            _cache_rest_workflow_observation(
                cache_key,
                owner=owner,
                repository=repo,
                observation=result,
                public_visibility_established=True,
            )
            return result
        if status not in {401, 403}:
            return _unknown_repo_workflow_observation("capability_unavailable")
        try:
            response = _request_public_with_retry(url)
        except requests.HTTPError as public_exc:
            public_status = (
                public_exc.response.status_code
                if public_exc.response is not None
                else None
            )
            if public_status == 404:
                if not _owned_public_visibility_is_established(owner, repo):
                    return _unknown_repo_workflow_observation("capability_unavailable")
                result = _observed_absent_workflow_directory()
                _cache_rest_workflow_observation(
                    cache_key,
                    owner=owner,
                    repository=repo,
                    observation=result,
                    public_visibility_established=True,
                )
                return result
            return _unknown_repo_workflow_observation("capability_unavailable")
        except requests.RequestException:
            return _unknown_repo_workflow_observation("capability_unavailable")
    except requests.RequestException:
        return _unknown_repo_workflow_observation("capability_unavailable")

    if response.status_code == 404:
        if not _owned_public_visibility_is_established(owner, repo):
            return _unknown_repo_workflow_observation("capability_unavailable")
        result = _observed_absent_workflow_directory()
        _cache_rest_workflow_observation(
            cache_key,
            owner=owner,
            repository=repo,
            observation=result,
            public_visibility_established=True,
        )
        return result
    if response.status_code != 200:
        return _unknown_repo_workflow_observation("capability_unavailable")

    try:
        entries = response.json()
    except (TypeError, ValueError):
        return _unknown_repo_workflow_observation("malformed_observation")
    if not isinstance(entries, list):
        return _unknown_repo_workflow_observation("malformed_observation")

    workflow_file_count = 0
    for entry in entries:
        if not isinstance(entry, dict):
            return _unknown_repo_workflow_observation("malformed_observation")
        name = entry.get("name")
        entry_type = entry.get("type")
        if not isinstance(name, str) or not isinstance(entry_type, str):
            return _unknown_repo_workflow_observation("malformed_observation")
        if entry_type == "file" and name.endswith((".yml", ".yaml")):
            workflow_file_count += 1

    result = {
        "observed": True,
        "has_actions_config": workflow_file_count > 0,
        "workflow_yaml_file_count": workflow_file_count,
        "unavailable_reason": None,
    }
    _cache_rest_workflow_observation(
        cache_key,
        owner=owner,
        repository=repo,
        observation=result,
        public_visibility_established=False,
    )
    return result


def get_repo_ci_state(owner: str, repo: str) -> bool | None:
    """Backward-compatible boolean projection of workflow observation."""
    observation = get_repo_workflow_observation(owner, repo)
    value = observation.get("has_actions_config")
    return value if isinstance(value, bool) else None
