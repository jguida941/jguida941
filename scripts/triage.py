"""Build a machine-friendly triage report for profile pipeline health."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from scripts import actions_audit
from scripts.contracts import REQUIRED_PROFILE_SNAPSHOT_KEYS, missing_required_keys
from scripts.runtime_env import token_mode_from_env
from scripts.metrics_svg import parse_metrics_svg
from scripts.severity import SEVERITY_ORDER
from scripts.severity import any_at_or_above
from scripts.validate_generated_profile import validate_profile


def _finding(
    *,
    finding_id: str,
    severity: str,
    status: str,
    evidence: list[str],
    likely_cause: str,
    fix_hint: str,
    confidence: float,
) -> dict[str, Any]:
    return {
        "finding_id": finding_id,
        "severity": severity,
        "status": status,
        "evidence": evidence,
        "likely_cause": likely_cause,
        "fix_hint": fix_hint,
        "confidence": confidence,
    }


def _load_snapshot(path: str = "site/data/profile_snapshot.json") -> dict[str, Any] | None:
    snapshot_path = Path(path)
    if not snapshot_path.exists():
        return None
    try:
        return json.loads(snapshot_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def build_triage_report(
    *,
    workflow: str = "Generate Metrics",
    run_limit: int = 20,
    branch: str | None = None,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    validation = validate_profile()
    if validation.errors:
        findings.append(
            _finding(
                finding_id="validation-errors",
                severity="critical",
                status="open",
                evidence=list(validation.errors),
                likely_cause="Generated files do not meet required contract checks.",
                fix_hint="Run `profile-cli generate-profile --validate` and fix listed errors.",
                confidence=0.98,
            )
        )
    if validation.warnings:
        findings.append(
            _finding(
                finding_id="validation-warnings",
                severity="medium",
                status="open",
                evidence=list(validation.warnings),
                likely_cause="Some quality checks returned warning-level drift.",
                fix_hint="Review warnings and decide if any should move to hard-fail rules.",
                confidence=0.85,
            )
        )

    snapshot = _load_snapshot()
    if snapshot is None:
        findings.append(
            _finding(
                finding_id="snapshot-missing",
                severity="critical",
                status="open",
                evidence=["site/data/profile_snapshot.json missing or invalid JSON"],
                likely_cause="Build step did not finish or output file was corrupted.",
                fix_hint="Run `profile-cli generate-profile --validate` and check write permissions.",
                confidence=0.99,
            )
        )
    else:
        missing_keys = missing_required_keys(snapshot, REQUIRED_PROFILE_SNAPSHOT_KEYS)
        if missing_keys:
            findings.append(
                _finding(
                    finding_id="snapshot-contract-missing-keys",
                    severity="critical",
                    status="open",
                    evidence=missing_keys,
                    likely_cause="Code writing snapshot JSON drifted from contract.",
                    fix_hint="Update pipeline writer or contract expectations to match.",
                    confidence=0.97,
                )
            )

        data_quality = snapshot.get("data_quality", {})
        if isinstance(data_quality, dict):
            ci_status = str(data_quality.get("ci_status", "unknown"))
            if ci_status in {"unavailable", "partial"}:
                findings.append(
                    _finding(
                        finding_id="ci-coverage-not-reliable",
                        severity="medium",
                        status="open",
                        evidence=[str(data_quality.get("ci_note", "CI status not reliable"))],
                        likely_cause="API scope/token limits made CI workflow detection incomplete.",
                        fix_hint="Use token mode with enough repo read scope or keep this metric as n/a.",
                        confidence=0.82,
                    )
                )

        snapshot_values = snapshot.get("snapshot", {})
        if isinstance(snapshot_values, dict):
            stars = snapshot_values.get("total_stars")
            releases = snapshot_values.get("releases")
            if Path("metrics.general.svg").exists():
                metrics = parse_metrics_svg("metrics.general.svg")
                if isinstance(stars, int) and stars > 0 and metrics.stargazers == 0:
                    findings.append(
                        _finding(
                            finding_id="metrics-svg-stargazer-drift",
                            severity="medium",
                            status="open",
                            evidence=[
                                f"snapshot total_stars={stars}",
                                f"metrics.general.svg stargazers={metrics.stargazers}",
                            ],
                            likely_cause="Third-party metrics card output differs from canonical API snapshot.",
                            fix_hint="Treat snapshot JSON as source of truth and keep card mismatch as warning.",
                            confidence=0.9,
                        )
                    )
                if isinstance(releases, int) and releases > 0 and metrics.releases == 0:
                    findings.append(
                        _finding(
                            finding_id="metrics-svg-release-drift",
                            severity="medium",
                            status="open",
                            evidence=[
                                f"snapshot releases={releases}",
                                f"metrics.general.svg releases={metrics.releases}",
                            ],
                            likely_cause="Third-party metrics card output differs from canonical API snapshot.",
                            fix_hint="Treat snapshot JSON as source of truth and keep card mismatch as warning.",
                            confidence=0.9,
                        )
                    )

    token_mode = token_mode_from_env()
    if token_mode == "none":
        findings.append(
            _finding(
                finding_id="token-missing",
                severity="high",
                status="open",
                evidence=["No GitHub token found in environment"],
                likely_cause="Workflow or local env does not provide auth token.",
                fix_hint="Set GITHUB_TOKEN or PERSONAL_GITHUB_TOKEN before running pipeline commands.",
                confidence=0.95,
            )
        )

    run_error = None
    run_audit = None
    try:
        runs = actions_audit.fetch_runs(workflow=workflow, limit=run_limit, branch=branch)
        run_audit = actions_audit.summarize_runs(runs, failure_limit=5)
        failure_count = run_audit.by_state.get("failure", 0)
        if failure_count >= 3:
            findings.append(
                _finding(
                    finding_id="workflow-failure-pattern",
                    severity="high",
                    status="open",
                    evidence=[
                        f"{failure_count} failures in last {run_audit.total} runs for workflow '{workflow}'"
                    ],
                    likely_cause="Repeated pipeline gate failure or unstable external dependency.",
                    fix_hint="Open recent failed run logs and address highest-frequency failure first.",
                    confidence=0.88,
                )
            )
    except Exception as exc:
        run_error = str(exc)
        findings.append(
            _finding(
                finding_id="workflow-run-audit-unavailable",
                severity="low",
                status="open",
                evidence=[run_error],
                likely_cause="Could not query GitHub Actions runs from current environment.",
                fix_hint="Check network access and gh auth settings.",
                confidence=0.7,
            )
        )

    by_severity: dict[str, int] = {}
    for finding in findings:
        severity = finding["severity"]
        by_severity[severity] = by_severity.get(severity, 0) + 1

    return {
        "schema": {
            "name": "profile_triage_report",
            "version": "1.0.0",
        },
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "workflow": workflow,
        "run_limit": run_limit,
        "token_mode": token_mode,
        "inputs": {
            "snapshot_path": "site/data/profile_snapshot.json",
            "metrics_svg_path": "metrics.general.svg",
            "workflow_name": workflow,
        },
        "summary": {
            "total_findings": len(findings),
            "by_severity": by_severity,
        },
        "run_audit": {
            "error": run_error,
            "total": None if run_audit is None else run_audit.total,
            "by_state": {} if run_audit is None else run_audit.by_state,
            "recent_failures": [] if run_audit is None else [run.__dict__ for run in run_audit.recent_failures],
        },
        "findings": findings,
    }


def write_triage_report(report: dict[str, Any], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def has_severity_at_or_above(report: dict[str, Any], threshold: str) -> bool:
    findings = report.get("findings", [])
    if not isinstance(findings, list):
        return False
    return any_at_or_above(findings, threshold)


def read_triage_report(input_path: str) -> dict[str, Any]:
    path = Path(input_path)
    return json.loads(path.read_text(encoding="utf-8"))


def ranked_open_findings(
    report: dict[str, Any],
    *,
    min_severity: str = "low",
    limit: int = 10,
) -> list[dict[str, Any]]:
    findings = report.get("findings", [])
    if not isinstance(findings, list):
        return []

    threshold_value = SEVERITY_ORDER.get(min_severity.lower(), 1)
    filtered = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        if str(finding.get("status", "open")).lower() != "open":
            continue
        severity = str(finding.get("severity", "info")).lower()
        severity_value = SEVERITY_ORDER.get(severity, -1)
        if severity_value < threshold_value:
            continue
        confidence = finding.get("confidence", 0.0)
        try:
            confidence_value = float(confidence)
        except (TypeError, ValueError):
            confidence_value = 0.0
        filtered.append(
            (
                -severity_value,
                -confidence_value,
                str(finding.get("finding_id", "")),
                finding,
            )
        )

    filtered.sort(key=lambda row: (row[0], row[1], row[2]))
    return [row[3] for row in filtered[: max(limit, 0)]]
