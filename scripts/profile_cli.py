#!/usr/bin/env python3
"""CLI for profile generation, checks, triage, and diagnostics."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


def _set_diag(args: argparse.Namespace, *, warnings=None, errors=None, extra=None) -> None:
    args._diag = {
        "warnings": list(warnings or []),
        "errors": list(errors or []),
        "extra": extra or {},
    }


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


def _run_live_profile_generation() -> None:
    from scripts.config import USERNAME
    from scripts.profile_pipeline import run_profile_pipeline

    print("=== GitHub Profile README Builder ===")
    print(f"User: {USERNAME}")
    run_profile_pipeline(logger=print)
    print("\nDone!")


def _cmd_build(args: argparse.Namespace) -> int:
    _run_live_profile_generation()
    _set_diag(args, extra={"step": "build"})
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    from scripts.validate_generated_profile import validate_profile

    result = validate_profile()
    _print_validation_result(result)
    _set_diag(
        args,
        warnings=list(result.warnings),
        errors=list(result.errors),
        extra={"step": "validate"},
    )
    return 0 if result.ok else 1


def _cmd_generate_profile(args: argparse.Namespace) -> int:
    from scripts.profile_pipeline import run_profile_pipeline_from_fixture
    from scripts.validate_generated_profile import validate_profile

    if args.fixture:
        print("=== GitHub Profile README Builder (fixture mode) ===")
        print(f"Fixture: {args.fixture}")
        run_profile_pipeline_from_fixture(args.fixture, logger=print)
        print("\nDone!")
    else:
        _run_live_profile_generation()

    warnings: list[str] = []
    errors: list[str] = []
    rc = 0
    if args.validate:
        result = validate_profile()
        _print_validation_result(result)
        warnings = list(result.warnings)
        errors = list(result.errors)
        rc = 0 if result.ok else 1

    _set_diag(
        args,
        warnings=warnings,
        errors=errors,
        extra={
            "step": "generate_profile",
            "validated": bool(args.validate),
            "fixture": args.fixture,
        },
    )
    return rc


def _cmd_check_metrics(args: argparse.Namespace) -> int:
    from scripts.metrics_svg import parse_metrics_svg, check_metrics

    svg_path = Path(args.path)
    if not svg_path.exists():
        message = f"{svg_path} not found"
        print(message)
        _set_diag(args, errors=[message], extra={"step": "check_metrics"})
        return 1

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
        _set_diag(
            args,
            warnings=list(result.warnings),
            errors=list(result.failures),
            extra={"step": "check_metrics"},
        )
        return 1
    print("Checks passed")
    _set_diag(
        args,
        warnings=list(result.warnings),
        extra={"step": "check_metrics"},
    )
    return 0


def _cmd_audit_runs(args: argparse.Namespace) -> int:
    from scripts import actions_audit

    try:
        runs = actions_audit.fetch_runs(
            workflow=args.workflow,
            limit=args.limit,
            branch=args.branch,
        )
    except Exception as exc:
        message = f"Failed to read GitHub Actions runs: {exc}"
        print(message)
        _set_diag(args, errors=[message], extra={"step": "audit_runs"})
        return 1

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

    _set_diag(
        args,
        extra={
            "step": "audit_runs",
            "workflow": args.workflow,
            "total_runs": summary.total,
            "state_counts": summary.by_state,
        },
    )
    return 0


def _cmd_branch_protection(args: argparse.Namespace) -> int:
    from scripts import branch_protection

    repo = args.repo or os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not repo:
        message = "Repository is required. Pass --repo <owner/repo> or set GITHUB_REPOSITORY."
        print(message)
        _set_diag(args, errors=[message], extra={"step": "branch_protection"})
        return 1

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
        _set_diag(args, errors=[message], extra={"step": "branch_protection", "repo": repo})
        return 1

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
            _set_diag(
                args,
                errors=[message],
                extra={"step": "branch_protection", "repo": repo, "branch": args.branch},
            )
            return 1

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
        _set_diag(
            args,
            errors=[f"missing required checks: {', '.join(audit.missing_checks)}"],
            extra={
                "step": "branch_protection",
                "repo": repo,
                "branch": args.branch,
                "missing_checks": audit.missing_checks,
            },
        )
        return 1

    _set_diag(
        args,
        extra={
            "step": "branch_protection",
            "repo": repo,
            "branch": args.branch,
            "missing_checks": audit.missing_checks,
            "applied": bool(args.apply),
        },
    )
    return 0


def _cmd_triage(args: argparse.Namespace) -> int:
    from scripts import triage

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
        _set_diag(
            args,
            errors=[f"triage severity threshold reached: {fail_on}"],
            extra={"step": "triage", "output": args.output},
        )
        return 1

    _set_diag(args, extra={"step": "triage", "output": args.output})
    return 0


def _cmd_triage_summary(args: argparse.Namespace) -> int:
    from scripts import triage

    input_path = Path(args.input)
    if not input_path.exists():
        message = f"{args.input} not found"
        print(message)
        _set_diag(args, errors=[message], extra={"step": "triage_summary"})
        return 1

    try:
        report = triage.read_triage_report(args.input)
    except Exception as exc:
        message = f"Failed to read triage report: {exc}"
        print(message)
        _set_diag(args, errors=[message], extra={"step": "triage_summary"})
        return 1

    ranked = triage.ranked_open_findings(
        report,
        min_severity=args.min_severity,
        limit=args.limit,
    )

    print(f"Triage summary from: {args.input}")
    if not ranked:
        print("No open findings at or above the selected severity.")
        _set_diag(args, extra={"step": "triage_summary", "input": args.input, "count": 0})
        return 0

    for idx, finding in enumerate(ranked, start=1):
        severity = finding.get("severity", "unknown")
        finding_id = finding.get("finding_id", "unknown")
        confidence = finding.get("confidence", 0)
        fix_hint = finding.get("fix_hint", "")
        print(f"{idx}. [{severity}] {finding_id} (confidence={confidence})")
        if fix_hint:
            print(f"   fix: {fix_hint}")

    _set_diag(
        args,
        extra={
            "step": "triage_summary",
            "input": args.input,
            "count": len(ranked),
            "min_severity": args.min_severity,
        },
    )
    return 0


def _doctor_has_failure_at_or_above(report: dict[str, Any], threshold: str) -> bool:
    from scripts.severity import is_at_or_above

    for check in report.get("checks", []):
        if check.get("ok"):
            continue
        if is_at_or_above(str(check.get("severity", "info")), threshold):
            return True
    return False


def _cmd_doctor(args: argparse.Namespace) -> int:
    from scripts.diagnostics import doctor_checks
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
        _set_diag(
            args,
            errors=[f"doctor severity threshold reached: {fail_on}"],
            extra={"step": "doctor", "output": args.output},
        )
        return 1

    _set_diag(args, extra={"step": "doctor", "output": args.output})
    return 0


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
    from scripts.diagnostics import write_run_diagnostics

    parser = build_parser()
    args = parser.parse_args(argv)
    exit_code = int(args.func(args))
    diag = getattr(args, "_diag", {"warnings": [], "errors": [], "extra": {}})
    write_run_diagnostics(
        command=str(args.command),
        exit_code=exit_code,
        warnings=diag.get("warnings", []),
        errors=diag.get("errors", []),
        extra=diag.get("extra", {}),
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
