"""GitHub API wrapper with pagination, caching, and rate-limit handling."""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

CACHE_DIR = Path(os.environ.get("CACHE_DIR", "/tmp/github_cache"))
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
    p = _cache_path(key)
    if p.exists():
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


def get_repos(include_forks=False) -> list:
    """Get all repos for the user."""
    repos = paginated_get(f"users/{USERNAME}/repos", {"sort": "created", "direction": "desc"})
    if not include_forks:
        repos = [r for r in repos if not r.get("fork")]
    return repos


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
        resp = _request_with_retry(url, params={"per_page": per_page, "page": page})
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
    resp = _request_with_retry(url)
    if resp.status_code == 200:
        data = resp.json()
        owner_commits = data.get("owner", [])[-weeks:]
        _set_cached(cache_key, owner_commits)
        return owner_commits
    return [0] * weeks


def get_total_commits() -> int:
    """Estimate total commits using the search API."""
    cache_key = "total_commits"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    url = f"{API}/search/commits"
    params = {"q": f"author:{USERNAME}", "per_page": 1}
    resp = _request_with_retry(url, headers=_headers(), params=params)
    if resp.status_code == 200:
        count = resp.json().get("total_count", 0)
        _set_cached(cache_key, count)
        return count
    return 0


def get_repos_with_ci(repos: list | None = None, max_workers: int = 10) -> int:
    """Count repos that have CI/CD workflows."""
    cache_key = "ci_count"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    if repos is None:
        repos = get_repos()

    count = 0

    def check_ci(repo):
        url = f"{API}/repos/{repo['owner']['login']}/{repo['name']}/contents/.github/workflows"
        resp = _request_with_retry(url)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                return True
        return False

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(check_ci, r) for r in repos]
        for f in as_completed(futures):
            try:
                if f.result():
                    count += 1
            except Exception as exc:
                print(f"  Warning: CI check failed: {exc}")

    _set_cached(cache_key, count)
    return count
