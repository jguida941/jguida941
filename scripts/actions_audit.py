"""Read GitHub Actions run data with the `gh` CLI."""

from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess


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

    try:
        result = subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("GitHub CLI not found. Install `gh` to use workflow run audit.") from exc
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or str(exc)).strip()
        raise RuntimeError(message) from exc

    try:
        payload = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise RuntimeError("Could not parse JSON output from `gh run list`") from exc
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
