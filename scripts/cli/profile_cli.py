#!/usr/bin/env python3
"""CLI for profile generation, checks, triage, and diagnostics."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


@dataclass(frozen=True)
class CommandResult:
    exit_code: int
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


def _print_validation_result(result) -> None:
    if result.errors:
        print("Profile validation failed:")
        for err in result.errors:
            print(f"  - {err}")
    else:
        print("Profile validation passed")

    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")


def _report_publication_decision(result: object) -> str:
    """Print the decision this generation reached, without inferring readiness."""
    decision = result.get("publication_decision") if isinstance(result, dict) else None
    if decision is None:
        return ""
    described = decision.describe() if hasattr(decision, "describe") else str(decision)
    print(f"Publication decision: {described}")
    return str(getattr(decision, "state", decision))


def _run_live_profile_generation() -> str:
    from scripts.core.config import USERNAME
    from scripts.pipeline.profile_pipeline import run_profile_pipeline

    print("=== GitHub Profile README Builder ===")
    print(f"User: {USERNAME}")
    result = run_profile_pipeline(logger=print)
    state = _report_publication_decision(result)
    print("\nDone!")
    return state


def _cmd_build(args: argparse.Namespace) -> CommandResult:
    state = _run_live_profile_generation()
    return CommandResult(exit_code=0, extra={"step": "build", "publication_state": state})


def _cmd_validate(args: argparse.Namespace) -> CommandResult:
    from scripts.quality.validate_generated_profile import validate_profile

    result = validate_profile()
    _print_validation_result(result)
    return CommandResult(
        exit_code=0 if result.ok else 1,
        warnings=list(result.warnings),
        errors=list(result.errors),
        extra={"step": "validate"},
    )


def _cmd_generate_profile(args: argparse.Namespace) -> CommandResult:
    from scripts.pipeline.profile_pipeline import run_profile_pipeline_from_fixture
    from scripts.quality.validate_generated_profile import validate_profile

    if args.fixture:
        print("=== GitHub Profile README Builder (fixture mode) ===")
        print(f"Fixture: {args.fixture}")
        generated = run_profile_pipeline_from_fixture(args.fixture, logger=print)
        publication_state = _report_publication_decision(generated)
        print("\nDone!")
    else:
        publication_state = _run_live_profile_generation()

    warnings: list[str] = []
    errors: list[str] = []
    rc = 0
    if args.validate:
        result = validate_profile()
        _print_validation_result(result)
        warnings = list(result.warnings)
        errors = list(result.errors)
        rc = 0 if result.ok else 1

    return CommandResult(
        exit_code=rc,
        warnings=warnings,
        errors=errors,
        extra={
            "step": "generate_profile",
            "validated": bool(args.validate),
            "fixture": args.fixture,
            "publication_state": publication_state,
        },
    )


def _cmd_publication_status(args: argparse.Namespace) -> CommandResult:
    """Report the one publication decision for the stored artifact set on disk.

    The subject is the stored set: its own manifest, payload bytes, and recorded
    quality facts. No provider is queried and no candidate hold from another run
    is copied onto it.
    """
    import json

    from scripts.contracts import PROFILE_ARTIFACT_MANIFEST_PATH
    from scripts.pipeline.profile_pipeline import (
        evaluate_profile_publication,
        stored_publication_subject,
    )
    from scripts.quality.validate_generated_profile import (
        PROFILE_SNAPSHOT_PATH,
        validate_profile,
    )

    def read_json(path: Path) -> dict:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    validation = validate_profile()
    _print_validation_result(validation)
    decision = evaluate_profile_publication(
        stored_publication_subject(
            read_json(Path(PROFILE_ARTIFACT_MANIFEST_PATH)),
            read_json(PROFILE_SNAPSHOT_PATH),
            artifact_errors=tuple(validation.errors),
        )
    )
    print(f"Publication decision: {decision.describe()}")

    publish = decision.allows_canonical_publication
    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as handle:
            handle.write(f"publish={'true' if publish else 'false'}\n")
            handle.write(f"state={decision.state}\n")
            handle.write(f"reasons={','.join(decision.reasons)}\n")

    invalid = decision.state == "ERROR_INVALID_ARTIFACT_SET"
    rc = 1 if invalid or (args.require_ready and not publish) else 0
    return CommandResult(
        exit_code=rc,
        warnings=list(validation.warnings),
        errors=list(validation.errors) if invalid else [],
        extra={
            "step": "publication_status",
            "state": decision.state,
            "reasons": list(decision.reasons),
            "publish": publish,
            "require_ready": bool(args.require_ready),
        },
    )


def _cmd_check_metrics(args: argparse.Namespace) -> CommandResult:
    from scripts.quality.metrics_svg import parse_metrics_svg, check_metrics

    svg_path = Path(args.path)
    if not svg_path.exists():
        message = f"{svg_path} not found"
        print(message)
        return CommandResult(exit_code=1, errors=[message], extra={"step": "check_metrics"})

    snapshot = parse_metrics_svg(svg_path)
    result = check_metrics(
        snapshot,
        require_repositories=not args.allow_missing_repositories,
        stargazers_min=args.stargazers_min,
        releases_min=args.releases_min,
    )

    print(
        "metrics.general.svg values: "
        f"repositories={snapshot.repositories}, "
        f"stargazers={snapshot.stargazers}, "
        f"releases={snapshot.releases}"
    )
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")
    if result.failures:
        print("Checks failed:")
        for failure in result.failures:
            print(f"  - {failure}")
        return CommandResult(
            exit_code=1,
            warnings=list(result.warnings),
            errors=list(result.failures),
            extra={"step": "check_metrics"},
        )
    print("Checks passed")
    return CommandResult(
        exit_code=0,
        warnings=list(result.warnings),
        extra={"step": "check_metrics"},
    )


def _cmd_audit_runs(args: argparse.Namespace) -> CommandResult:
    from scripts.github import actions_audit

    try:
        runs = actions_audit.fetch_runs(
            workflow=args.workflow,
            limit=args.limit,
            branch=args.branch,
        )
    except Exception as exc:
        message = f"Failed to read GitHub Actions runs: {exc}"
        print(message)
        return CommandResult(exit_code=1, errors=[message], extra={"step": "audit_runs"})

    summary = actions_audit.summarize_runs(runs, failure_limit=args.failure_limit)

    print(f"Workflow: {args.workflow}")
    print(f"Total runs checked: {summary.total}")
    print("State counts:")
    for state, count in sorted(summary.by_state.items(), key=lambda item: item[0]):
        print(f"  - {state}: {count}")

    if summary.recent_failures:
        print("Recent failures:")
        for run in summary.recent_failures:
            print(
                f"  - {run.created_at} | {run.display_title} | "
                f"id={run.database_id} | {run.url}"
            )
    else:
        print("No failed runs in the selected range")

    return CommandResult(
        exit_code=0,
        extra={
            "step": "audit_runs",
            "workflow": args.workflow,
            "total_runs": summary.total,
            "state_counts": summary.by_state,
        },
    )


def _cmd_branch_protection(args: argparse.Namespace) -> CommandResult:
    from scripts.github import branch_protection

    repo = args.repo or os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not repo:
        message = "Repository is required. Pass --repo <owner/repo> or set GITHUB_REPOSITORY."
        print(message)
        return CommandResult(exit_code=1, errors=[message], extra={"step": "branch_protection"})

    required_checks = list(args.require or branch_protection.DEFAULT_REQUIRED_CHECKS)

    try:
        audit = branch_protection.audit_required_checks(
            repo=repo,
            branch=args.branch,
            required_checks=required_checks,
        )
    except Exception as exc:
        message = f"Failed to audit branch protection: {exc}"
        print(message)
        return CommandResult(
            exit_code=1,
            errors=[message],
            extra={"step": "branch_protection", "repo": repo},
        )

    print(f"Branch protection audit for {repo}@{args.branch}")
    print(f"Required checks: {', '.join(audit.required_checks) if audit.required_checks else '(none)'}")
    print(f"Configured checks: {', '.join(audit.configured_checks) if audit.configured_checks else '(none)'}")
    if audit.missing_checks:
        print(f"Missing checks: {', '.join(audit.missing_checks)}")
    else:
        print("Missing checks: none")

    if args.apply and audit.missing_checks:
        try:
            branch_protection.apply_required_checks(
                repo=repo,
                branch=args.branch,
                required_checks=audit.required_checks,
                strict=not args.no_strict,
            )
        except Exception as exc:
            message = f"Failed to apply required checks: {exc}"
            print(message)
            return CommandResult(
                exit_code=1,
                errors=[message],
                extra={"step": "branch_protection", "repo": repo, "branch": args.branch},
            )

        audit = branch_protection.audit_required_checks(
            repo=repo,
            branch=args.branch,
            required_checks=required_checks,
        )
        if audit.missing_checks:
            print(f"Still missing checks after apply: {', '.join(audit.missing_checks)}")
        else:
            print("Required checks applied successfully.")

    should_fail = bool(audit.missing_checks) and bool(args.fail_on_missing)
    if should_fail:
        return CommandResult(
            exit_code=1,
            errors=[f"missing required checks: {', '.join(audit.missing_checks)}"],
            extra={
                "step": "branch_protection",
                "repo": repo,
                "branch": args.branch,
                "missing_checks": audit.missing_checks,
            },
        )

    return CommandResult(
        exit_code=0,
        extra={
            "step": "branch_protection",
            "repo": repo,
            "branch": args.branch,
            "missing_checks": audit.missing_checks,
            "applied": bool(args.apply),
        },
    )


def _cmd_triage(args: argparse.Namespace) -> CommandResult:
    from scripts.quality import triage

    report = triage.build_triage_report(
        workflow=args.workflow,
        run_limit=args.limit,
        branch=args.branch,
    )
    triage.write_triage_report(report, args.output)

    print(f"Triage report written: {args.output}")
    print("Findings by severity:")
    for severity, count in sorted(
        report.get("summary", {}).get("by_severity", {}).items(),
        key=lambda item: item[0],
    ):
        print(f"  - {severity}: {count}")

    fail_on = (args.fail_on or "").lower()
    should_fail = fail_on != "none" and triage.has_severity_at_or_above(report, fail_on)
    if should_fail:
        print(f"Triage failed because finding severity >= {fail_on}")
        return CommandResult(
            exit_code=1,
            errors=[f"triage severity threshold reached: {fail_on}"],
            extra={"step": "triage", "output": args.output},
        )

    return CommandResult(exit_code=0, extra={"step": "triage", "output": args.output})


def _cmd_triage_summary(args: argparse.Namespace) -> CommandResult:
    from scripts.quality import triage

    input_path = Path(args.input)
    if not input_path.exists():
        message = f"{args.input} not found"
        print(message)
        return CommandResult(exit_code=1, errors=[message], extra={"step": "triage_summary"})

    try:
        report = triage.read_triage_report(args.input)
    except Exception as exc:
        message = f"Failed to read triage report: {exc}"
        print(message)
        return CommandResult(exit_code=1, errors=[message], extra={"step": "triage_summary"})

    ranked = triage.ranked_open_findings(
        report,
        min_severity=args.min_severity,
        limit=args.limit,
    )

    print(f"Triage summary from: {args.input}")
    if not ranked:
        print("No open findings at or above the selected severity.")
        return CommandResult(
            exit_code=0,
            extra={"step": "triage_summary", "input": args.input, "count": 0},
        )

    for idx, finding in enumerate(ranked, start=1):
        severity = finding.get("severity", "unknown")
        finding_id = finding.get("finding_id", "unknown")
        confidence = finding.get("confidence", 0)
        fix_hint = finding.get("fix_hint", "")
        print(f"{idx}. [{severity}] {finding_id} (confidence={confidence})")
        if fix_hint:
            print(f"   fix: {fix_hint}")

    return CommandResult(
        exit_code=0,
        extra={
            "step": "triage_summary",
            "input": args.input,
            "count": len(ranked),
            "min_severity": args.min_severity,
        },
    )


def _doctor_has_failure_at_or_above(report: dict[str, Any], threshold: str) -> bool:
    from scripts.quality.severity import is_at_or_above

    for check in report.get("checks", []):
        if check.get("ok"):
            continue
        if is_at_or_above(str(check.get("severity", "info")), threshold):
            return True
    return False


def _cmd_doctor(args: argparse.Namespace) -> CommandResult:
    from scripts.quality.diagnostics import doctor_checks
    import json

    report = doctor_checks()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"Doctor report written: {args.output}")
    for check in report.get("checks", []):
        status = "OK" if check.get("ok") else "FAIL"
        print(f"  - {check.get('name')}: {status} ({check.get('detail')})")

    fail_on = (args.fail_on or "").lower()
    should_fail = fail_on != "none" and _doctor_has_failure_at_or_above(report, fail_on)
    if should_fail:
        return CommandResult(
            exit_code=1,
            errors=[f"doctor severity threshold reached: {fail_on}"],
            extra={"step": "doctor", "output": args.output},
        )

    return CommandResult(exit_code=0, extra={"step": "doctor", "output": args.output})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="profile-cli",
        description="Profile pipeline CLI for build, checks, triage, and diagnostics.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_cmd = subparsers.add_parser("build", help="Generate README, SVGs, and JSON snapshot.")
    build_cmd.set_defaults(func=_cmd_build)

    validate_cmd = subparsers.add_parser("validate", help="Validate generated profile outputs.")
    validate_cmd.set_defaults(func=_cmd_validate)

    generate_cmd = subparsers.add_parser(
        "generate-profile",
        help="Run full generation and optionally validation in one command.",
    )
    generate_cmd.add_argument(
        "--validate",
        action="store_true",
        help="Run validation after build.",
    )
    generate_cmd.add_argument(
        "--fixture",
        default=None,
        help="Path to collected-data JSON fixture. Skips live GitHub API calls.",
    )
    generate_cmd.set_defaults(func=_cmd_generate_profile)

    publication_cmd = subparsers.add_parser(
        "publication-status",
        help="Report the publication decision for the stored profile artifact set.",
    )
    publication_cmd.add_argument(
        "--github-output",
        default=None,
        help="Append publish/state/reasons to this GitHub Actions output file.",
    )
    publication_cmd.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit non-zero unless the stored artifact set is READY to publish.",
    )
    publication_cmd.set_defaults(func=_cmd_publication_status)

    metrics_cmd = subparsers.add_parser(
        "check-metrics",
        aliases=["sanity-check-metrics"],
        help="Run checks on metrics.general.svg values.",
    )
    metrics_cmd.add_argument(
        "--path",
        default="metrics.general.svg",
        help="Path to metrics SVG file.",
    )
    metrics_cmd.add_argument(
        "--allow-missing-repositories",
        action="store_true",
        help="Do not fail when repository count is missing.",
    )
    metrics_cmd.add_argument(
        "--stargazers-min",
        type=int,
        default=None,
        help="Fail if stargazers is below this value.",
    )
    metrics_cmd.add_argument(
        "--releases-min",
        type=int,
        default=None,
        help="Fail if releases is below this value.",
    )
    metrics_cmd.set_defaults(func=_cmd_check_metrics)

    audit_cmd = subparsers.add_parser(
        "audit-runs",
        help="Show recent GitHub Actions run status for a workflow.",
    )
    audit_cmd.add_argument(
        "--workflow",
        required=True,
        help="Workflow name, for example: Generate Metrics",
    )
    audit_cmd.add_argument(
        "--limit",
        type=int,
        default=20,
        help="How many runs to read.",
    )
    audit_cmd.add_argument(
        "--branch",
        default=None,
        help="Optional branch filter.",
    )
    audit_cmd.add_argument(
        "--failure-limit",
        type=int,
        default=5,
        help="How many recent failures to print.",
    )
    audit_cmd.set_defaults(func=_cmd_audit_runs)

    protection_cmd = subparsers.add_parser(
        "branch-protection",
        help="Audit or apply required status checks for a branch.",
    )
    protection_cmd.add_argument(
        "--repo",
        default=None,
        help="Repository in owner/repo format. Defaults to GITHUB_REPOSITORY when set.",
    )
    protection_cmd.add_argument(
        "--branch",
        default="main",
        help="Branch name to audit or update.",
    )
    protection_cmd.add_argument(
        "--require",
        action="append",
        help="Required check name. Pass multiple times for multiple checks.",
    )
    protection_cmd.add_argument(
        "--apply",
        action="store_true",
        help="Apply missing checks using `gh api`.",
    )
    protection_cmd.add_argument(
        "--no-strict",
        action="store_true",
        help="Do not require branch to be up to date before merging.",
    )
    protection_cmd.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit non-zero when required checks are missing.",
    )
    protection_cmd.set_defaults(func=_cmd_branch_protection)

    triage_cmd = subparsers.add_parser(
        "triage",
        help="Build machine-friendly triage report from contracts, metrics, and run status.",
    )
    triage_cmd.add_argument(
        "--workflow",
        default="Generate Metrics",
        help="Workflow name for run health audit.",
    )
    triage_cmd.add_argument(
        "--limit",
        type=int,
        default=20,
        help="How many workflow runs to inspect.",
    )
    triage_cmd.add_argument(
        "--branch",
        default=None,
        help="Optional branch filter for run audit.",
    )
    triage_cmd.add_argument(
        "--output",
        default="site/data/triage_report.json",
        help="Where to write triage report JSON.",
    )
    triage_cmd.add_argument(
        "--fail-on",
        default="none",
        choices=["none", "low", "medium", "high", "critical"],
        help="Fail command if finding severity is at or above this level.",
    )
    triage_cmd.set_defaults(func=_cmd_triage)

    triage_summary_cmd = subparsers.add_parser(
        "triage-summary",
        help="Print ordered fix plan from triage report JSON.",
    )
    triage_summary_cmd.add_argument(
        "--input",
        default="site/data/triage_report.json",
        help="Path to triage report JSON.",
    )
    triage_summary_cmd.add_argument(
        "--min-severity",
        default="low",
        choices=["low", "medium", "high", "critical"],
        help="Only include findings at or above this severity.",
    )
    triage_summary_cmd.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Max findings to print.",
    )
    triage_summary_cmd.set_defaults(func=_cmd_triage_summary)

    doctor_cmd = subparsers.add_parser(
        "doctor",
        help="Run local environment checks and write doctor report.",
    )
    doctor_cmd.add_argument(
        "--output",
        default="site/data/doctor_report.json",
        help="Where to write doctor report JSON.",
    )
    doctor_cmd.add_argument(
        "--fail-on",
        default="none",
        choices=["none", "low", "medium", "high", "critical"],
        help="Fail command if doctor failures are at or above this level.",
    )
    doctor_cmd.set_defaults(func=_cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    from scripts.quality.diagnostics import write_run_diagnostics

    os.chdir(ROOT)
    parser = build_parser()
    args = parser.parse_args(argv)
    result: CommandResult = args.func(args)
    write_run_diagnostics(
        command=str(args.command),
        exit_code=result.exit_code,
        warnings=result.warnings,
        errors=result.errors,
        extra=result.extra,
    )
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
