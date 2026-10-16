"""Read GitHub Actions run data with the `gh` CLI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from scripts.github.gh_cli import run_json


@dataclass(frozen=True)
class WorkflowRun:
    database_id: int
    workflow_name: str
    display_title: str
    status: str
    conclusion: str
    created_at: str
    url: str


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def fetch_runs(workflow: str, limit: int = 20, branch: str | None = None) -> list[WorkflowRun]:
    cmd = [
        "gh",
        "run",
        "list",
        "--workflow",
        workflow,
        "--limit",
        str(limit),
        "--json",
        "databaseId,workflowName,displayTitle,status,conclusion,createdAt,url",
    ]
    if branch:
        cmd.extend(["--branch", branch])

    payload = run_json(cmd, default=[])
    runs: list[WorkflowRun] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        runs.append(
            WorkflowRun(
                database_id=_safe_int(item.get("databaseId", 0)),
                workflow_name=str(item.get("workflowName", workflow)),
                display_title=str(item.get("displayTitle", "")),
                status=str(item.get("status", "unknown")),
                conclusion=str(item.get("conclusion", "")),
                created_at=str(item.get("createdAt", "")),
                url=str(item.get("url", "")),
            )
        )
    return runs


@dataclass(frozen=True)
class WorkflowAudit:
    total: int
    by_state: dict[str, int]
    recent_failures: list[WorkflowRun]


def summarize_runs(runs: list[WorkflowRun], failure_limit: int = 5) -> WorkflowAudit:
    counts: dict[str, int] = {}
    failures: list[WorkflowRun] = []

    for run in runs:
        state = run.conclusion or run.status or "unknown"
        counts[state] = counts.get(state, 0) + 1
        if run.conclusion == "failure":
            failures.append(run)

    failures = sorted(failures, key=lambda item: item.created_at, reverse=True)[:failure_limit]

    return WorkflowAudit(
        total=len(runs),
        by_state=counts,
        recent_failures=failures,
    )

# One public canary: recent executions of the profile repository itself. The
# configuration/adoption metric elsewhere remains a different population.
_PROFILE_CI_CONCLUSIONS = frozenset({
    "success", "failure", "cancelled", "skipped", "timed_out",
    "neutral", "action_required", "stale", "startup_failure",
})
_PROFILE_CI_ACTIVE = frozenset({"in_progress", "queued", "pending", "requested", "waiting"})


def _utc_instant(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        return None
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _limited_label(value: object, maximum: int = 100) -> str:
    if not isinstance(value, str):
        return ""
    return "".join(char for char in value.strip() if char.isprintable())[:maximum]


def normalize_profile_ci_runs(
    rows: object, repository: str, observed_at: str, *, limit: int = 12
) -> dict:
    """Qualify a bounded Actions sample without turning missing runs into zero.

    Only public profile-repository run metadata is published: no job logs,
    credentials, run titles, or private-repository evidence. The 'available'
    claim means this query returned a structurally complete bounded sample,
    not that every workflow or every account repository was inspected.
    """
    limit = max(1, min(20, int(limit)))
    base = {
        "schema": "profile-ci-execution/v1",
        "repository": repository,
        "observed_at": observed_at,
        "sample_limit": limit,
        "scope": "Latest observed GitHub Actions runs in the public profile repository, across branches; not account-wide.",
    }
    if not isinstance(rows, list):
        return {**base, "status": "unavailable", "observed_runs": None, "runs": []}
    result: list[dict] = []
    seen: set[int] = set()
    malformed = False
    for source in rows[:limit]:
        if not isinstance(source, dict):
            malformed = True
            continue
        run_id = source.get("databaseId")
        workflow = _limited_label(source.get("workflowName"))
        created_at = _utc_instant(source.get("createdAt"))
        if type(run_id) is not int or run_id < 1 or not workflow or created_at is None or run_id in seen:
            malformed = True
            continue
        seen.add(run_id)
        state = source.get("status")
        conclusion = source.get("conclusion")
        if state == "completed":
            outcome = conclusion if isinstance(conclusion, str) and conclusion in _PROFILE_CI_CONCLUSIONS else "unknown"
        elif isinstance(state, str) and state in _PROFILE_CI_ACTIVE:
            outcome = "in_progress" if state == "in_progress" else "queued"
        else:
            outcome = "unknown"
        if outcome == "unknown":
            malformed = True
        result.append({
            "run_id": run_id,
            "workflow": workflow,
            "outcome": outcome,
            "created_at": created_at,
            "event": _limited_label(source.get("event"), 32),
            "head_branch": _limited_label(source.get("headBranch"), 80),
        })
    result.sort(key=lambda row: (row["created_at"], row["run_id"]), reverse=True)
    status = "partial" if malformed else "available" if result else "empty"
    return {**base, "status": status, "observed_runs": len(result), "runs": result}


def collect_profile_ci_runs(repository: str, limit: int = 12) -> dict:
    """Fetch only the bounded public profile repository's Actions metadata.

    GitHub CLI failure is an unavailable observation, never a zero-run claim;
    it cannot prevent unrelated profile metrics from publishing.
    """
    limit = max(1, min(20, int(limit)))
    observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    try:
        rows = run_json([
            "gh", "run", "list", "--repo", repository, "--limit", str(limit),
            "--json", "databaseId,workflowName,status,conclusion,createdAt,event,headBranch",
        ])
    except (RuntimeError, ValueError):
        rows = None
    return normalize_profile_ci_runs(rows, repository, observed_at, limit=limit)


# CI-REPO-TIMELINE-01: bounded, public-only repository execution sample.
# The README and website share this carrier. It must never describe the
# complete account or imply a sample is the population of successful runs.
def select_public_ci_repositories(repositories: object, owner: str, *, limit: int = 6) -> list[str]:
    """Pick a stable, recently pushed public workflow cohort, plus profile self.

    The caller supplies the *public* repository inventory, not a combined
    public/private list. Reject explicitly private, forked and foreign rows.
    A configured workflow is not a successful run, just a sampling criterion.
    """
    import re
    if not re.fullmatch(r"[A-Za-z0-9-]+", owner):
        return []
    eligible = []
    for repo in repositories if isinstance(repositories, list) else []:
        if not isinstance(repo, dict) or repo.get("private") is True or repo.get("fork") is True:
            continue
        name = repo.get("name")
        identity = repo.get("owner")
        if (not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", name)
                or not isinstance(identity, dict) or identity.get("login") != owner
                or name == owner or repo.get("has_ci_workflows") is not True):
            continue
        timestamp = _utc_instant(repo.get("pushed_at")) or ""
        eligible.append((timestamp, name))
    eligible.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [f"{owner}/{owner}"] + [f"{owner}/{name}" for _, name in eligible[:max(0, limit-1)]]


def normalize_public_ci_timeline(
    observations: object, owner: str, observed_at: str, *, window_days: int = 84,
    limit_per_repo: int = 20,
) -> dict:
    """A truthful time-axis view of *sampled* public GitHub Actions executions.

    One point is one valid provider run. A failed/unavailable query never adds
    success or an observed zero. Reaching the source cap makes coverage partial.
    """
    from datetime import timedelta
    instant = _utc_instant(observed_at)
    if not instant:
        raise ValueError("observed_at must be an offset-aware timestamp")
    end = datetime.fromisoformat(instant.replace("Z", "+00:00"))
    window_days = max(7, min(365, int(window_days)))
    lower = end - timedelta(days=window_days)
    limit_per_repo = max(1, min(60, int(limit_per_repo)))
    start = lower.isoformat(timespec="seconds").replace("+00:00", "Z")
    result = {"schema":"profile-ci-timeline/v1", "owner":owner,
              "observed_at":instant, "window_start":start, "window_end":instant,
              "window_days":window_days, "sample_limit_per_repo":limit_per_repo,
              "scope":"Selected public, owned repositories with observed workflow configuration, plus profile; up to 20 most recent runs per repository, not complete history.",
              "repositories":[], "observed_runs":0, "status":"unavailable"}
    if not isinstance(observations, list) or not observations:
        return result
    partial = False
    for observation in observations[:6]:
        if not isinstance(observation, dict):
            partial = True
            continue
        repo = observation.get("repository")
        if (not isinstance(repo, str) or not repo.startswith(owner + "/")
                or repo.count("/") != 1):
            partial = True
            continue
        from re import fullmatch
        if not fullmatch(r"[A-Za-z0-9_.-]{1,100}", repo.split("/", 1)[1]):
            partial = True
            continue
        raw = observation.get("runs")
        qualified = normalize_profile_ci_runs(raw, repo, instant, limit=limit_per_repo)
        samples = []
        for item in qualified["runs"]:
            moment = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
            if lower <= moment <= end:
                samples.append(item)
        truncated = isinstance(raw, list) and len(raw) >= limit_per_repo
        completeness = qualified["status"]
        if truncated and completeness == "available":
            completeness = "partial"
        if completeness in ("partial", "unavailable"):
            partial = True
        result["repositories"].append({"repository":repo, "status":completeness,
            "truncated":truncated, "observed_runs":len(samples) if raw is not None else None,
            "runs":samples})
        result["observed_runs"] += len(samples)
    if not result["repositories"]:
        return result
    if all(row["status"] == "unavailable" for row in result["repositories"]):
        return result
    result["status"] = "partial" if partial else "available"
    return result


def collect_public_ci_timeline(public_repositories: list[dict], owner: str) -> dict:
    """Bounded live GitHub Actions read. No private-repository run metadata."""
    observed = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    selected = select_public_ci_repositories(public_repositories, owner)
    observations = []
    for repo in selected:
        try:
            rows = run_json(["gh", "run", "list", "--repo", repo, "--limit", "20",
                "--json", "databaseId,workflowName,status,conclusion,createdAt,event,headBranch"])
        except (RuntimeError, ValueError):
            rows = None
        observations.append({"repository":repo,"runs":rows})
    return normalize_public_ci_timeline(observations, owner, observed)
