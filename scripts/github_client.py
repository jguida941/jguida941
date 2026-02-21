"""GitHub API wrapper with pagination, caching, and rate-limit handling."""

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests

CACHE_DIR = Path(os.environ.get("CACHE_DIR", "/tmp/github_cache"))
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "21600"))
BYPASS_CACHE = os.environ.get("BYPASS_GITHUB_CACHE", "").lower() in {"1", "true", "yes"}
TOKEN = os.environ.get("GITHUB_TOKEN", "")
USERNAME = os.environ.get("GITHUB_USERNAME", "jguida941")
API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"


def _headers():
    h = {"Accept": "application/vnd.github+json"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h


def _cache_path(key: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe = key.replace("/", "__").replace("?", "_Q_").replace("&", "_A_")
    return CACHE_DIR / f"{safe}.json"


def _get_cached(key: str):
    if BYPASS_CACHE:
        return None

    p = _cache_path(key)
    if p.exists():
        if CACHE_TTL_SECONDS > 0:
            age_seconds = time.time() - p.stat().st_mtime
            if age_seconds > CACHE_TTL_SECONDS:
                return None
        return json.loads(p.read_text())
    return None


def _set_cached(key: str, data):
    p = _cache_path(key)
    p.write_text(json.dumps(data))


def _request_with_retry(url, headers=None, params=None, max_retries=3):
    """GET request with retry on 429/5xx."""
    for attempt in range(max_retries):
        resp = requests.get(url, headers=headers or _headers(), params=params)
        if resp.status_code == 200:
            return resp
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = int(resp.headers.get("Retry-After", 2 ** attempt))
            time.sleep(wait)
            continue
        resp.raise_for_status()
    return resp


def _request_public_with_retry(url, params=None, max_retries=2):
    """GET request without auth, for public fallback checks."""
    public_headers = {"Accept": "application/vnd.github+json"}
    for attempt in range(max_retries):
        resp = requests.get(url, headers=public_headers, params=params)
        if resp.status_code == 200:
            return resp
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = int(resp.headers.get("Retry-After", 2 ** attempt))
            time.sleep(wait)
            continue
        resp.raise_for_status()
    return resp


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
    match = re.search(r"[?&]page=(\\d+)>;\\s*rel=\"last\"", link)
    if match:
        return int(match.group(1))

    return len(data)


def paginated_get(endpoint: str, params: dict | None = None, per_page: int = 100) -> list:
    """Fetch all pages from a REST endpoint."""
    cache_key = f"paginated_{endpoint}_{json.dumps(params or {}, sort_keys=True)}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    results = []
    p = dict(params or {})
    p["per_page"] = per_page
    page = 1

    while True:
        p["page"] = page
        url = f"{API}/{endpoint}" if not endpoint.startswith("http") else endpoint
        resp = _request_with_retry(url, params=p)
        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        results.extend(data)
        if len(data) < per_page:
            break
        page += 1

    _set_cached(cache_key, results)
    return results


def _is_public_owned_repo(repo: dict) -> bool:
    """True when repo is publicly visible and owned by USERNAME."""
    owner_login = repo.get("owner", {}).get("login", "")
    is_owner = owner_login.lower() == USERNAME.lower()
    visibility = repo.get("visibility")
    if visibility is None:
        visibility = "private" if repo.get("private") else "public"
    return is_owner and visibility == "public"


def _normalize_graphql_repo(node: dict) -> dict:
    owner_login = (node.get("owner") or {}).get("login", USERNAME)
    language_name = (node.get("primaryLanguage") or {}).get("name")
    visibility = str(node.get("visibility", "PUBLIC")).lower()
    workflows_dir = node.get("workflowsDir")
    has_ci_workflows = False
    if isinstance(workflows_dir, dict):
        entries = workflows_dir.get("entries")
        has_ci_workflows = isinstance(entries, list) and len(entries) > 0
    language_bytes = {}
    languages = node.get("languages")
    if isinstance(languages, dict):
        edges = languages.get("edges")
        if isinstance(edges, list):
            for edge in edges:
                if not isinstance(edge, dict):
                    continue
                lang_node = edge.get("node") or {}
                lang_name = lang_node.get("name")
                lang_size = edge.get("size")
                if not lang_name:
                    continue
                try:
                    size = int(lang_size)
                except (TypeError, ValueError):
                    size = 0
                if size > 0:
                    language_bytes[lang_name] = language_bytes.get(lang_name, 0) + size
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
        "fork": bool(node.get("isFork")),
        "private": bool(node.get("isPrivate")),
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
        "language_bytes": language_bytes,
        "latest_commit_message": latest_commit_message,
    }


def _graphql_public_owned_repos(include_forks: bool) -> list:
    cache_key = f"graphql_public_owned_repos_{int(include_forks)}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

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
                    entries { name }
                  }
                }
                languages(first: 20, orderBy: { field: SIZE, direction: DESC }) {
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
                    entries { name }
                  }
                }
                languages(first: 20, orderBy: { field: SIZE, direction: DESC }) {
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

    while True:
        data = _graphql_query(query, {"login": USERNAME, "cursor": cursor})
        user = (data or {}).get("user")
        repo_conn = (user or {}).get("repositories")
        if not isinstance(repo_conn, dict):
            if not saw_page:
                raise RuntimeError("GraphQL repo listing unavailable")
            break
        saw_page = True

        nodes = repo_conn.get("nodes") or []
        repos.extend(_normalize_graphql_repo(node) for node in nodes if isinstance(node, dict))

        page_info = repo_conn.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break

        cursor = page_info.get("endCursor")
        if not cursor:
            break

    _set_cached(cache_key, repos)
    return repos


def get_repos(include_forks: bool = False) -> list:
    """Get public repos owned by USERNAME, optionally including forks."""
    if TOKEN:
        try:
            repos = _graphql_public_owned_repos(include_forks)
            if repos:
                return repos
        except Exception as exc:
            print(f"  Warning: GraphQL repo listing failed; falling back to REST ({exc})")

    try:
        repos = paginated_get(
            f"users/{USERNAME}/repos",
            {"sort": "created", "direction": "desc", "type": "owner"},
        )
        repos = [r for r in repos if _is_public_owned_repo(r)]
        if not include_forks:
            repos = [r for r in repos if not r.get("fork")]
        return repos
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        print(f"  Warning: REST repo listing unavailable ({status}); falling back to GraphQL")
        return _graphql_public_owned_repos(include_forks)


def _graphql_query(query: str, variables: dict) -> dict | None:
    resp = requests.post(
        GRAPHQL,
        headers=_headers(),
        json={"query": query, "variables": variables},
    )
    if resp.status_code != 200:
        return None

    payload = resp.json()
    if not isinstance(payload, dict):
        return None
    if payload.get("errors"):
        return None
    return payload.get("data")


def get_owned_repo_scope_counts() -> dict:
    """
    Return repo counts with explicit scope splits.

    Keys:
      - public_owned_total
      - public_owned_forks
      - public_owned_nonfork
      - private_owned (None when unavailable)
    """
    cache_key = "owned_repo_scope_counts"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

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
          }
        }
        """
        data = _graphql_query(query, {"login": USERNAME})
        user = (data or {}).get("user")
        if isinstance(user, dict):
            counts = {
                "public_owned_total": int(user["publicOwned"]["totalCount"]),
                "public_owned_forks": int(user["publicOwnedForks"]["totalCount"]),
                "public_owned_nonfork": int(user["publicOwnedNonFork"]["totalCount"]),
                "private_owned": int(user["privateOwned"]["totalCount"]),
            }
            _set_cached(cache_key, counts)
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
    }
    _set_cached(cache_key, counts)
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
    cache_key = "all_languages_aggregated"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    if repos is None:
        repos = get_repos()

    # Preferred path when repos were fetched from GraphQL:
    # language bytes are already embedded and require no extra API calls.
    if repos and all("language_bytes" in repo for repo in repos):
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
        _set_cached(cache_key, totals)
        return totals

    totals = {}

    def fetch_one(repo):
        return get_repo_languages(repo["owner"]["login"], repo["name"])

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fetch_one, r): r for r in repos}
        for f in as_completed(futures):
            try:
                langs = f.result()
                for lang, bytes_ in langs.items():
                    totals[lang] = totals.get(lang, 0) + bytes_
            except Exception as exc:
                repo = futures[f]
                print(f"  Warning: failed to fetch languages for {repo['name']}: {exc}")

    _set_cached(cache_key, totals)
    return totals


def get_events(per_page: int = 100, max_pages: int = 3) -> list:
    """Get recent public events (GitHub caps at 300 events / 3 pages)."""
    cache_key = f"events_{per_page}_{max_pages}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    results = []
    for page in range(1, max_pages + 1):
        url = f"{API}/users/{USERNAME}/events/public"
        try:
            resp = _request_with_retry(url, params={"per_page": per_page, "page": page})
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            if status in {401, 403}:
                # Retry public feed without auth in case token scope is restricted.
                try:
                    resp = _request_public_with_retry(url, params={"per_page": per_page, "page": page})
                except requests.HTTPError as public_exc:
                    public_status = public_exc.response.status_code if public_exc.response is not None else "unknown"
                    print(
                        "  Warning: events endpoint unavailable "
                        f"(auth={status}, public={public_status}); using partial/empty event data"
                    )
                    break
            else:
                print(f"  Warning: events endpoint unavailable ({status}); using partial/empty event data")
                break

        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        results.extend(data)
        if len(data) < per_page:
            break

    _set_cached(cache_key, results)
    return results


def get_contribution_calendar() -> dict | None:
    """Fetch contribution calendar via GraphQL."""
    cache_key = "contribution_calendar"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
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
    resp = requests.post(
        GRAPHQL,
        headers=_headers(),
        json={"query": query, "variables": {"login": USERNAME}},
    )
    if resp.status_code != 200:
        return None

    data = resp.json()
    try:
        cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        _set_cached(cache_key, cal)
        return cal
    except (KeyError, TypeError):
        return None


def get_repo_commits_last_n_weeks(owner: str, repo: str, weeks: int = 12) -> list:
    """Get weekly commit counts for last N weeks (participation stats)."""
    cache_key = f"participation_{owner}_{repo}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    url = f"{API}/repos/{owner}/{repo}/stats/participation"
    try:
        resp = _request_with_retry(url)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
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


def get_repo_user_commit_count(owner: str, repo: str) -> int:
    """Get total commits by USERNAME in a repo via contributors API."""
    cache_key = f"repo_user_commits_{owner}_{repo}_{USERNAME}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    # Primary path: contributors endpoint (fast when available).
    try:
        contributors = paginated_get(
            f"repos/{owner}/{repo}/contributors",
            {"anon": "false"},
            per_page=100,
        )
        for contributor in contributors:
            login = contributor.get("login", "")
            if login.lower() == USERNAME.lower():
                count = int(contributor.get("contributions", 0))
                _set_cached(cache_key, count)
                return count
        _set_cached(cache_key, 0)
        return 0
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status not in {401, 403, 404}:
            raise

    # Fallback path for restricted tokens: commits endpoint with author filter.
    try:
        count = _count_commits_from_commits_endpoint(owner, repo, use_public=False)
        _set_cached(cache_key, count)
        return count
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status in {401, 403}:
            try:
                count = _count_commits_from_commits_endpoint(owner, repo, use_public=True)
                _set_cached(cache_key, count)
                return count
            except requests.HTTPError:
                pass

    _set_cached(cache_key, 0)
    return 0


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


def get_total_commits(repos: list | None = None, max_workers: int = 4) -> int:
    """Count commits authored by USERNAME across the selected repos."""
    cache_key = "total_commits_owned_public_nonfork"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    if repos is None:
        repos = get_repos(include_forks=False)

    total = 0
    failures = 0

    def fetch_one(repo):
        return get_repo_user_commit_count(repo["owner"]["login"], repo["name"])

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fetch_one, r): r for r in repos}
        for f in as_completed(futures):
            repo = futures[f]
            try:
                total += int(f.result())
            except Exception as exc:
                failures += 1
                print(f"  Warning: commit count failed for {repo['name']}: {exc}")

    # If REST-based per-repo counting is broadly blocked, use GraphQL fallback.
    if repos and (total == 0 or failures >= max(1, len(repos) // 2)):
        fallback_total = get_total_commit_contributions_via_graphql()
        if fallback_total is not None:
            print("  Info: using GraphQL commit contribution fallback for total commits")
            total = fallback_total
        elif total == 0:
            # Last-resort fallback: current-year contributions.
            calendar = get_contribution_calendar()
            if isinstance(calendar, dict):
                try:
                    calendar_total = int(calendar.get("totalContributions", 0))
                except (TypeError, ValueError):
                    calendar_total = 0
                if calendar_total > 0:
                    print("  Info: using contribution-calendar fallback for total commits")
                    total = calendar_total

    _set_cached(cache_key, total)
    return total


def get_repos_with_ci(repos: list | None = None, max_workers: int = 10) -> int:
    """Count repos that have CI/CD workflows."""
    cache_key = "ci_count"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    if repos is None:
        repos = get_repos()

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


def get_repo_ci_state(owner: str, repo: str) -> bool | None:
    """
    Return CI/CD workflow presence for a single repo.

    - True: .github/workflows exists and contains files
    - False: workflows path does not exist or is empty
    - None: state could not be determined (e.g. repeated 403/401 failures)
    """
    cache_key = f"repo_ci_state_{owner}_{repo}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    url = f"{API}/repos/{owner}/{repo}/contents/.github/workflows"
    try:
        resp = _request_with_retry(url)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status == 404:
            _set_cached(cache_key, False)
            return False

        if status in {401, 403}:
            # Retry unauthenticated for public visibility.
            try:
                resp = _request_public_with_retry(url)
            except requests.HTTPError as public_exc:
                public_status = public_exc.response.status_code if public_exc.response is not None else None
                if public_status == 404:
                    _set_cached(cache_key, False)
                    return False
                # Do not cache unknown so next run can retry.
                return None
        else:
            raise

        if resp.status_code == 200:
            data = resp.json()
            result = isinstance(data, list) and len(data) > 0
            _set_cached(cache_key, result)
            return result

    if resp.status_code != 200:
        # Do not cache unknown so next run can retry.
        return None

    data = resp.json()
    result = isinstance(data, list) and len(data) > 0
    _set_cached(cache_key, result)
    return result
