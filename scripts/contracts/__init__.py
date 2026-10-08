"""Shared required keys, publication contracts, and README checks."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Literal, TypedDict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from scripts.contracts.profile_contract import SNAPSHOT_METRICS
from scripts.core.config import USERNAME


# ---------------------------------------------------------------------------
# Typed contracts for key data shapes
# ---------------------------------------------------------------------------


class Snapshot(TypedDict):
    last_year_contributions: int | None
    public_scope_commits: int | None
    total_repos: int
    public_forks: int
    private_owned_repos: int | None
    total_stars: int
    languages_count: int
    prs_merged: int | None
    releases: int | None
    ci_repos: int | None
    streak_days: int


class DataQuality(TypedDict):
    ci_status: str
    ci_note: str
    commits_status: str
    commits_note: str
    releases_status: str
    releases_note: str
    prs_status: str
    prs_note: str
    contributions_status: str
    contributions_note: str
    events_status: str
    events_note: str
    token_mode: str
    private_aggregate_status: str
    metric_statuses: dict[str, str]
    metric_provenance: dict[str, dict[str, Any]]
    non_exact_metrics: dict[str, dict[str, Any]]
    publication_hold_reasons: tuple[str, ...]


class ContributionDay(TypedDict):
    date: str
    count: int


class ContributionCalendarValue(TypedDict):
    total: int
    days: tuple[ContributionDay, ...]


class ProviderObservation(TypedDict):
    """Closed provider fact envelope shared by collection and projection.

    The runtime validator in ``scripts.github.github_client`` discriminates the
    value shape by ``metric_id``.  Keeping the envelope here gives collectors a
    single typed carrier without allowing raw provider response bodies into the
    profile model.
    """

    schema: Literal["profile-provider-observation/v1"]
    metric_id: str
    source_metric_id: str
    value: int | ContributionCalendarValue | tuple[dict[str, Any], ...] | None
    status: Literal["ok", "partial", "fallback", "unavailable"]
    complete: bool
    population_id: str
    population_signature: str | None
    window_start: str | None
    window_end: str | None
    observed_at: str | None
    source_id: str
    source_mode: Literal["live", "cache", "fallback", "previous_snapshot"]
    completion_reason: str


class NonExactMetricValue(TypedDict):
    schema: Literal["profile-nonexact-metric/v1"]
    metric_id: str
    source_metric_id: str
    value: int
    status: Literal["partial", "fallback"]
    population_id: str
    population_signature: str | None
    window_start: str | None
    window_end: str | None
    observed_at: str
    source_id: str
    source_mode: Literal["live", "cache", "fallback", "previous_snapshot"]
    completion_reason: str


class DataScope(TypedDict):
    repos_included: str
    activity_metric_scope: str
    public_owned_repos_total: int
    public_owned_forks_total: int
    public_owned_nonfork_repos_total: int
    private_owned_repos_total: int | None
    private_owned_nonfork_repos_total: int | None
    metric_scopes: dict[str, str]


class FocusItem(TypedDict):
    title: str
    detail: str
    url: str


class FocusLanes(TypedDict):
    now: list[FocusItem]
    next: list[FocusItem]
    shipped: list[FocusItem]


class ScorecardCard(TypedDict):
    key: str
    label: str
    detail: str
    value: object
    display_value: str
    accent: str


class SnapshotRow(TypedDict):
    key: str
    label: str
    dashboard_label: str
    value: object
    display_value: str


REQUIRED_README_MARKERS = (
    "assets/dashboard_summary.svg",
    "assets/dashboard_summary_mobile.svg",
    "<picture>",
    "metrics.general.svg",
    "assets/streak_summary.svg",
    "assets/badges.svg",
    "assets/builder_scorecard.svg",
    "assets/engineering_cadence.svg",
    "assets/contribution_calendar.svg",
    "assets/now_next_shipped.svg",
    "assets/currently_working.svg",
    "assets/lang_breakdown.svg",
    "assets/activity_heatmap.svg",
    "assets/repo_spotlight.svg",
    "assets/raw_snapshot.svg",
    "### Deep Dive Data",
    "site/data/profile_snapshot.json",
)


DISALLOWED_README_HEADINGS = (
    "### By The Numbers",
    "### Builder Scorecard",
    "### Contribution Calendar",
    "### Current Focus",
    "### Currently Working On",
    "### Language Breakdown",
    "### Raw Data Snapshot",
)


REQUIRED_PROFILE_SNAPSHOT_KEYS = {
    "generated_at",
    "username",
    "dashboard_url",
    "generation",
    "snapshot",
    "snapshot_rows",
    "snapshot_cards",
    "scorecard",
    "scorecard_cards",
    "data_scope",
    "data_quality",
    "focus",
    "top_languages",
    "repo_language_matrix",
    "activity_feed",
    "recent_created",
}


def expected_snapshot_metric_keys() -> set[str]:
    return {entry["key"] for entry in SNAPSHOT_METRICS}


def missing_required_keys(payload: dict[str, Any], required_keys: set[str]) -> list[str]:
    return sorted(key for key in required_keys if key not in payload)


# ---------------------------------------------------------------------------
# Public runtime contract for the published snapshot
# ---------------------------------------------------------------------------

# Every aggregate whose scope and completeness are published for the same owned
# repository population. A missing, extra, or renamed key is a contract error.
GOVERNED_AGGREGATE_METRIC_KEYS = frozenset(
    {
        "active_repos_7d",
        "automation_repos",
        "automation_workflows",
        "ci_coverage_pct",
        "ci_repos",
        "days_since_last_push",
        "languages_count",
        "languages_over_5pct",
        "primary_lang_share_pct",
        "top_languages",
    }
)

REQUIRED_PUBLIC_DATA_SCOPE_KEYS = (
    "repos_included",
    "activity_metric_scope",
    "public_owned_repos_total",
    "public_owned_forks_total",
    "public_owned_nonfork_repos_total",
    "private_owned_repos_total",
    "private_owned_nonfork_repos_total",
    "metric_scopes",
)
REQUIRED_PUBLIC_DATA_QUALITY_KEYS = (
    "ci_status",
    "ci_note",
    "commits_status",
    "commits_note",
    "releases_status",
    "releases_note",
    "events_status",
    "events_note",
    "private_aggregate_status",
    "metric_statuses",
)
# The internal authentication posture is diagnostics; it is never published.
FORBIDDEN_PUBLIC_DATA_QUALITY_KEYS = ("token_mode",)

# Population counts that may legitimately be absent (never observed) rather than
# zero. Every other published count is a real non-negative integer.
NULLABLE_PUBLIC_SCOPE_COUNT_KEYS = (
    "private_owned_repos_total",
    "private_owned_nonfork_repos_total",
)
PUBLIC_SCOPE_COUNT_KEYS = (
    "public_owned_repos_total",
    "public_owned_forks_total",
    "public_owned_nonfork_repos_total",
    *NULLABLE_PUBLIC_SCOPE_COUNT_KEYS,
)

# Closed vocabularies. Completeness values describe how much of a population was
# observed; source statuses describe one provider observation. They are not
# interchangeable, so a provider status may never stand in for completeness.
COMPLETENESS_VALUES = frozenset({"exact", "partial", "unavailable"})
SOURCE_STATUS_VALUES = frozenset(
    {
        "exact",
        "ok",
        "partial",
        "fallback",
        "unavailable",
        "empty",
        "limited",
        "events_fallback",
    }
)
CONTRIBUTION_CURRENTNESS_VALUES = frozenset({"current", "noncurrent"})
# The one origin that asserts live provider observation, and therefore the one
# that owes a clean generator-source census before it may produce artifacts.
LIVE_SOURCE_KIND = "github-api"
FIXTURE_SOURCE_KIND = "fixture"
SOURCE_KIND_VALUES = frozenset({LIVE_SOURCE_KIND, FIXTURE_SOURCE_KIND})

PUBLICATION_DECISION_STATES = (
    "READY",
    "HOLD_NONLIVE_SOURCE",
    "HOLD_INCOMPLETE_PRIVATE_EVIDENCE",
    "HOLD_NONCURRENT_CONTRIBUTIONS",
    "ERROR_INVALID_ARTIFACT_SET",
)
# Displayed-state precedence when several holds coexist. Every reason is kept.
PUBLICATION_HOLD_PRECEDENCE = (
    "HOLD_NONLIVE_SOURCE",
    "HOLD_INCOMPLETE_PRIVATE_EVIDENCE",
    "HOLD_NONCURRENT_CONTRIBUTIONS",
)
PUBLICATION_HOLD_REASONS = (
    "NONLIVE_SOURCE",
    "INCOMPLETE_PRIVATE_EVIDENCE",
    "NONCURRENT_CONTRIBUTIONS",
)


def _is_count(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def _is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _mapping_errors(
    section: str,
    field: str,
    value: object,
    *,
    allowed_values: frozenset[str] | None,
) -> list[str]:
    path = f"{section}.{field}"
    if not isinstance(value, dict):
        return [f"{path} must be an object keyed by the governed metric keys"]
    observed = set(value)
    missing = sorted(GOVERNED_AGGREGATE_METRIC_KEYS - observed)
    unexpected = sorted(observed - GOVERNED_AGGREGATE_METRIC_KEYS)
    errors: list[str] = []
    if missing:
        errors.append(f"{path} is missing metric keys: " + ", ".join(missing))
    if unexpected:
        errors.append(f"{path} carries unknown metric keys: " + ", ".join(unexpected))
    for metric in sorted(observed & GOVERNED_AGGREGATE_METRIC_KEYS):
        entry = value[metric]
        if not _is_text(entry):
            errors.append(f"{path} value for {metric} must be a non-empty string")
        elif allowed_values is not None and entry not in allowed_values:
            errors.append(
                f"{path} value for {metric} must be one of: "
                + ", ".join(sorted(allowed_values))
            )
    return errors


def _automation_contract_errors(payload: dict[str, Any]) -> list[str]:
    """Check the aggregate summary and every compatibility projection.

    Legacy snapshots may omit this additive summary. When supplied, all three
    partitions and their projections are required and internally consistent.
    """
    import math
    from scripts.contracts.profile_contract import automation_display, format_metric_value

    if "automation" not in payload:
        return []
    errors = []
    summary = payload["automation"]
    names = {"public", "private", "combined"}
    if type(summary) is not dict or set(summary) != names:
        return ["automation must contain public, private and combined partitions"]
    counts = ("observed_eligible_repos", "observed_workflow_repos", "unknown_workflow_repos")
    nullable = ("eligible_repos", "configured_repos", "workflow_files")
    fields = {*counts, *nullable, "adoption_pct", "inventory_status", "status"}
    for name in sorted(names):
        row = summary[name]
        path = "automation." + name
        if type(row) is not dict or set(row) != fields:
            errors.append(path + " has an invalid field roster")
            continue
        if (any(not _is_count(row[key]) for key in counts)
                or any(row[key] is not None and not _is_count(row[key]) for key in nullable)
                or row["inventory_status"] not in COMPLETENESS_VALUES
                or row["status"] not in COMPLETENESS_VALUES):
            errors.append(path + " has invalid counts or statuses")
            continue
        observed, known, unknown = (row[key] for key in counts)
        eligible, configured, files = (row[key] for key in nullable)
        exact_inventory = row["inventory_status"] == "exact"
        expected_status = ("exact" if exact_inventory and known == observed
                           else "partial" if known else "unavailable")
        if known + unknown != observed or (eligible != observed if exact_inventory else eligible is not None):
            errors.append(path + " inventory and observation counts disagree")
        if row["status"] != expected_status:
            errors.append(path + " status disagrees with its evidence")
        if known or exact_inventory and eligible == 0:
            if configured is None or files is None or configured > known or files < configured or (configured == 0 and files != 0):
                errors.append(path + " configuration counts disagree")
        elif configured is not None or files is not None:
            errors.append(path + " unavailable observations must have null counts")
        ratio = row["adoption_pct"]
        expected_ratio = configured / eligible * 100 if eligible and known and configured is not None else None
        if expected_ratio is None:
            if ratio is not None:
                errors.append(path + " adoption must be null without a known denominator and observation")
        elif (type(ratio) not in (int, float) or not math.isfinite(ratio)
              or not math.isclose(ratio, expected_ratio, rel_tol=1e-12, abs_tol=1e-12)):
            errors.append(path + " adoption disagrees with configured/eligible repositories")
    if errors:
        return errors
    public, private, combined = (summary[key] for key in ("public", "private", "combined"))
    inventory = ("exact" if public["inventory_status"] == private["inventory_status"] == "exact"
                 else "unavailable" if public["inventory_status"] == private["inventory_status"] == "unavailable"
                 else "partial")
    if combined["inventory_status"] != inventory:
        errors.append("automation.combined inventory disagrees with its partitions")
    for key in counts + nullable:
        values = [row[key] for row in (public, private)]
        expected = (sum(values) if inventory == "exact" else None) if key == "eligible_repos" else (
            sum(value for value in values if value is not None)
            if any(value is not None for value in values) else None
        )
        # An exact-empty sibling contributes no observation to an unavailable row.
        if key in ("configured_repos", "workflow_files") and combined["status"] == "unavailable":
            expected = None
        if combined[key] != expected:
            errors.append("automation.combined." + key + " disagrees with its partitions")
    for section, key, field in (
        ("snapshot", "ci_repos", "configured_repos"),
        ("engineering", "automation_repos", "configured_repos"),
        ("engineering", "automation_workflows", "workflow_files"),
        ("engineering", "automation_eligible_repos", "eligible_repos"),
        ("scorecard", "automation_workflows", "workflow_files"),
        ("scorecard", "ci_coverage_pct", "adoption_pct"),
    ):
        projection = payload.get(section)
        if not isinstance(projection, dict) or key not in projection or projection[key] != combined[field]:
            errors.append(section + "." + key + " disagrees with automation.combined." + field)
    statuses = (payload.get("data_quality") or {}).get("metric_statuses") or {}
    scopes = (payload.get("data_scope") or {}).get("metric_scopes") or {}
    expected_scope = "owned-public-private-nonfork-profile-excluded-" + {
        "exact": "exact", "partial": "partial-observation", "unavailable": "unavailable",
    }[combined["status"]]
    for key in ("ci_repos", "automation_repos", "automation_workflows", "ci_coverage_pct"):
        if statuses.get(key) != combined["status"]:
            errors.append("data_quality.metric_statuses." + key + " disagrees with automation")
        if scopes.get(key) != expected_scope:
            errors.append("data_scope.metric_scopes." + key + " disagrees with automation")
    for collection in ("snapshot_rows", "snapshot_cards"):
        rows = [row for row in payload.get(collection, []) if isinstance(row, dict) and row.get("key") == "ci_repos"]
        if (len(rows) != 1 or rows[0].get("value") != combined["configured_repos"]
                or rows[0].get("display_value") != format_metric_value(combined["configured_repos"], {"format": "int_or_na"})):
            errors.append(collection + " workflow repository projection disagrees with automation")
    if payload.get("automation_display") != automation_display(summary):
        errors.append("automation_display disagrees with automation")
    return errors


def public_snapshot_contract_errors(payload: dict[str, Any]) -> list[str]:
    """Return path-qualified errors for the published scope/quality contract."""
    errors: list[str] = []

    data_scope = payload.get("data_scope")
    if not isinstance(data_scope, dict):
        errors.append("data_scope must be an object")
        data_scope = {}
    data_quality = payload.get("data_quality")
    if not isinstance(data_quality, dict):
        errors.append("data_quality must be an object")
        data_quality = {}

    for field in REQUIRED_PUBLIC_DATA_SCOPE_KEYS:
        if field not in data_scope:
            errors.append(f"data_scope.{field} is missing")
    for field in REQUIRED_PUBLIC_DATA_QUALITY_KEYS:
        if field not in data_quality:
            errors.append(f"data_quality.{field} is missing")

    for field in ("repos_included", "activity_metric_scope"):
        if field in data_scope and not _is_text(data_scope[field]):
            errors.append(f"data_scope.{field} must be a non-empty string")

    for field in PUBLIC_SCOPE_COUNT_KEYS:
        if field not in data_scope:
            continue
        value = data_scope[field]
        if value is None and field in NULLABLE_PUBLIC_SCOPE_COUNT_KEYS:
            continue
        if not _is_count(value):
            errors.append(
                f"data_scope.{field} must be a non-negative integer count"
                + (" or null" if field in NULLABLE_PUBLIC_SCOPE_COUNT_KEYS else "")
            )

    if "metric_scopes" in data_scope:
        errors.extend(
            _mapping_errors(
                "data_scope", "metric_scopes", data_scope["metric_scopes"], allowed_values=None
            )
        )

    for field in ("ci_status", "commits_status", "releases_status", "events_status"):
        if field in data_quality and data_quality[field] not in SOURCE_STATUS_VALUES:
            errors.append(
                f"data_quality.{field} must be one of: " + ", ".join(sorted(SOURCE_STATUS_VALUES))
            )
    for field in ("ci_note", "commits_note", "releases_note", "events_note"):
        if field in data_quality and not _is_text(data_quality[field]):
            errors.append(f"data_quality.{field} must be a non-empty string")

    if "private_aggregate_status" in data_quality:
        if data_quality["private_aggregate_status"] not in COMPLETENESS_VALUES:
            errors.append(
                "data_quality.private_aggregate_status must be one of: "
                + ", ".join(sorted(COMPLETENESS_VALUES))
            )

    if "metric_statuses" in data_quality:
        errors.extend(
            _mapping_errors(
                "data_quality",
                "metric_statuses",
                data_quality["metric_statuses"],
                allowed_values=COMPLETENESS_VALUES,
            )
        )

    for field in FORBIDDEN_PUBLIC_DATA_QUALITY_KEYS:
        if field in data_quality:
            errors.append(
                f"data_quality.{field} is internal diagnostics and is never published"
            )

    errors.extend(_automation_contract_errors(payload))
    return errors


# ---------------------------------------------------------------------------
# Artifact set identity
# ---------------------------------------------------------------------------

PROFILE_ARTIFACT_MANIFEST_SCHEMA = "profile-artifact-manifest/v1"
PROFILE_GENERATION_SCHEMA = "profile-artifact-generation/v1"

# The exact canonical payload set. Generation writes these first, then seals them
# in the external manifest below; no upload or commit may use a wildcard.
PROFILE_PAYLOAD_PATHS = (
    "assets/dashboard_summary.svg",
    "assets/dashboard_summary_mobile.svg",
    "README.md",
    "assets/activity_heatmap.svg",
    "assets/badges.svg",
    "assets/builder_scorecard.svg",
    "assets/contribution_calendar.svg",
    "assets/currently_working.svg",
    "assets/engineering_cadence.svg",
    "assets/lang_breakdown.svg",
    "assets/now_next_shipped.svg",
    "assets/raw_snapshot.svg",
    "assets/repo_spotlight.svg",
    "assets/streak_summary.svg",
    "metrics.general.svg",
    "site/data/profile_snapshot.json",
)
PROFILE_ARTIFACT_MANIFEST_PATH = "site/data/profile_artifact_manifest.json"
# The exact roster every generated-artifact upload and auto-commit enumerates.
PROFILE_ARTIFACT_PATHS = PROFILE_PAYLOAD_PATHS + (PROFILE_ARTIFACT_MANIFEST_PATH,)

# Generator inputs whose bytes decide the rendered output. This roster is itself
# inside the fingerprinted source, so changing it changes the source digest.
GENERATOR_SOURCE_ROOTS = (
    "scripts/contracts",
    "scripts/core",
    "scripts/github",
    "scripts/pipeline",
    "scripts/rendering",
)
GENERATOR_SOURCE_FILES = (
    "assets/profile-avatar.jpg",
    "pyproject.toml",
    "requirements.txt",
    "scripts/quality/metrics_svg.py",
    "scripts/quality/validate_generated_profile.py",
)
GENERATOR_TEMPLATE_PATH = "templates/README.md.tpl"
GENERATOR_SOURCE_SUFFIX = ".py"

PROFILE_TIMEZONE_DEFAULT = "America/New_York"

SOURCE_ROOT = Path(__file__).resolve().parents[2]


class ProfileGenerationIdentityError(RuntimeError):
    """A generation input could not be identified deterministically."""


def canonical_json(value: object) -> str:
    """The one canonical serialization used by every digest in this contract."""
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def canonical_digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ProfileGenerationIdentityError(
            f"generator input {path} could not be read: {exc}"
        ) from exc


def _template_source_path() -> Path:
    """The README template the renderer actually loads for this run."""
    local = Path(GENERATOR_TEMPLATE_PATH)
    if local.is_file():
        return local
    return SOURCE_ROOT / GENERATOR_TEMPLATE_PATH


def generator_source_records() -> list[list[object]]:
    """The sorted logical-path/length/digest stream over every generator input."""
    records: dict[str, list[object]] = {}

    def record(logical_path: str, payload: bytes) -> None:
        records[logical_path] = [
            logical_path,
            len(payload),
            hashlib.sha256(payload).hexdigest(),
        ]

    for root in GENERATOR_SOURCE_ROOTS:
        base = SOURCE_ROOT / root
        if not base.is_dir():
            raise ProfileGenerationIdentityError(f"generator source root {root} is missing")
        for path in sorted(base.rglob(f"*{GENERATOR_SOURCE_SUFFIX}")):
            if "__pycache__" in path.parts or not path.is_file():
                continue
            record(path.relative_to(SOURCE_ROOT).as_posix(), _read_bytes(path))

    for relative_path in GENERATOR_SOURCE_FILES:
        path = SOURCE_ROOT / relative_path
        if not path.is_file():
            raise ProfileGenerationIdentityError(f"generator input {relative_path} is missing")
        record(relative_path, _read_bytes(path))

    record(GENERATOR_TEMPLATE_PATH, _read_bytes(_template_source_path()))
    return [records[key] for key in sorted(records)]


def generator_source_digest() -> str:
    return canonical_digest(generator_source_records())


_REQUIREMENT_PATTERN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*(.*)$")
_PYTHON_VERSION_MARKER = re.compile(
    r"^python_version\s*(<=|>=|==|!=|<|>)\s*['\"]([0-9]+(?:\.[0-9]+)*)['\"]$"
)


def normalized_distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip()).lower()


def _version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def _marker_applies(marker: str) -> bool:
    match = _PYTHON_VERSION_MARKER.match(marker.strip())
    if match is None:
        raise ProfileGenerationIdentityError(
            f"unsupported dependency environment marker: {marker.strip()}"
        )
    operator, declared = match.group(1), _version_tuple(match.group(2))
    current = sys.version_info[: len(declared)]
    comparisons = {
        "<": current < declared,
        "<=": current <= declared,
        ">": current > declared,
        ">=": current >= declared,
        "==": current == declared,
        "!=": current != declared,
    }
    return comparisons[operator]


def _declared_requirements(entries: list[str]) -> dict[str, str]:
    """Map each active requirement to the distribution spelling it declares."""
    declared: dict[str, str] = {}
    for entry in entries:
        requirement = entry.split("#", 1)[0].strip()
        if not requirement:
            continue
        requirement, _, marker = requirement.partition(";")
        requirement = requirement.strip()
        if marker.strip() and not _marker_applies(marker):
            continue
        match = _REQUIREMENT_PATTERN.match(requirement)
        if match is None:
            raise ProfileGenerationIdentityError(
                f"unparsable runtime dependency: {requirement}"
            )
        declared.setdefault(normalized_distribution_name(match.group(1)), match.group(1))
    return declared


def _project_dependencies() -> list[str]:
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
        import tomli as tomllib

    project = tomllib.loads((SOURCE_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = project.get("project", {}).get("dependencies", [])
    return [str(entry) for entry in dependencies]


def runtime_dependency_names() -> dict[str, str]:
    """Every runtime dependency this Python actually needs, declared spellings."""
    declared = _declared_requirements(
        (SOURCE_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    )
    for name, spelling in _declared_requirements(_project_dependencies()).items():
        declared.setdefault(name, spelling)
    return declared


def resolve_execution_identity() -> dict[str, Any]:
    """The exact interpreter and installed dependency versions that render output."""
    packages: dict[str, str] = {}
    for name, spelling in sorted(runtime_dependency_names().items()):
        for candidate in (spelling, name):
            try:
                packages[name] = metadata.version(candidate)
                break
            except metadata.PackageNotFoundError:
                continue
        else:
            raise ProfileGenerationIdentityError(
                f"installed version for runtime dependency {name} is unavailable"
            )
    return {
        "python_implementation": sys.implementation.name,
        "python_version": (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        ),
        "packages": packages,
    }


def _validated_timezone_name(raw: object, default: str) -> str:
    name = str(raw or "").strip() or default
    if name == "UTC":
        return name
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        return "UTC"
    return name


def profile_timezone_name() -> str:
    """The effective streak/profile zone after the product default is applied."""
    return _validated_timezone_name(os.environ.get("PROFILE_TIMEZONE"), PROFILE_TIMEZONE_DEFAULT)


def activity_timezone_name() -> str:
    """The effective activity-rhythm zone after the product default is applied."""
    return _validated_timezone_name(
        os.environ.get("PROFILE_ACTIVITY_TZ"), PROFILE_TIMEZONE_DEFAULT
    )


def resolve_render_config(source_kind: str) -> dict[str, str]:
    """The closed set of effective values that change rendered output."""
    if source_kind not in SOURCE_KIND_VALUES:
        raise ProfileGenerationIdentityError(f"unknown generation source kind: {source_kind}")
    return {
        "username": str(USERNAME).strip(),
        "profile_timezone": profile_timezone_name(),
        "activity_timezone": activity_timezone_name(),
        "source_kind": source_kind,
    }


def _git(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(SOURCE_ROOT), *arguments],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def resolve_generator_revision() -> str:
    """The checked-out commit that loaded this generator."""
    try:
        completed = _git("rev-parse", "HEAD")
    except (OSError, subprocess.SubprocessError) as exc:
        raise ProfileGenerationIdentityError(
            f"generator revision could not be resolved: {exc}"
        ) from exc
    revision = completed.stdout.strip()
    if completed.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ProfileGenerationIdentityError(
            "generator revision could not be resolved to a 40-hex commit"
        )
    return revision


def dirty_generator_source_paths() -> tuple[str, ...]:
    """Staged, unstaged, and untracked generator inputs. Outputs are excluded."""
    pathspecs = [
        *GENERATOR_SOURCE_ROOTS,
        *GENERATOR_SOURCE_FILES,
        GENERATOR_TEMPLATE_PATH,
    ]
    try:
        completed = _git("status", "--porcelain", "--untracked-files=normal", "--", *pathspecs)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ProfileGenerationIdentityError(
            f"generator source state could not be enumerated: {exc}"
        ) from exc
    if completed.returncode != 0:
        raise ProfileGenerationIdentityError(
            "generator source state could not be enumerated"
        )
    return tuple(
        line[3:].strip()
        for line in completed.stdout.splitlines()
        if line.strip()
    )


# The exact declared inputs of the pre-render identity. The render key is their
# canonical digest and nothing else, so a reader can recompute it from a manifest
# alone; changing any one input without changing the key is a contradiction.
GENERATION_IDENTITY_INPUT_KEYS = (
    "schema",
    "source_kind",
    "generated_at",
    "generator_revision",
    "generator_source_digest",
    "execution_identity",
    "render_config",
    "claim_input_digest",
)
# Every generation field the snapshot payload duplicates from the manifest. Both
# copies describe one generation, so both are joined before a set is accepted.
PUBLIC_GENERATION_JOINED_KEYS = (
    "source_kind",
    "generated_at",
    "generator_revision",
    "generator_source_digest",
    "claim_input_digest",
    "render_key",
)


def render_key_for(record: dict[str, Any]) -> str:
    """Recompute the render key from exactly the declared identity inputs."""
    missing = [key for key in GENERATION_IDENTITY_INPUT_KEYS if key not in record]
    if missing:
        raise ProfileGenerationIdentityError(
            "generation identity is missing declared inputs: " + ", ".join(missing)
        )
    return canonical_digest(
        {key: record[key] for key in GENERATION_IDENTITY_INPUT_KEYS}
    )


def build_generation_identity(
    *,
    source_kind: str,
    generated_at: str,
    claim_input_digest: str,
) -> dict[str, Any]:
    """The full pre-render identity. It contains no generated output bytes."""
    identity = {
        "schema": PROFILE_ARTIFACT_MANIFEST_SCHEMA,
        "source_kind": source_kind,
        "generated_at": generated_at,
        "generator_revision": resolve_generator_revision(),
        "generator_source_digest": generator_source_digest(),
        "execution_identity": resolve_execution_identity(),
        "render_config": resolve_render_config(source_kind),
        "claim_input_digest": claim_input_digest,
    }
    identity["render_key"] = render_key_for(identity)
    return identity


def public_generation_record(identity: dict[str, Any]) -> dict[str, Any]:
    """The origin binding published inside the snapshot payload itself."""
    record = {key: identity[key] for key in PUBLIC_GENERATION_JOINED_KEYS}
    record["schema"] = PROFILE_GENERATION_SCHEMA
    return record


def artifact_payload_records(root: Path | str = ".") -> list[dict[str, Any]]:
    """Path, length, and digest for each canonical payload, in canonical order."""
    base = Path(root)
    records: list[dict[str, Any]] = []
    for relative_path in sorted(PROFILE_PAYLOAD_PATHS):
        payload = _read_bytes(base / relative_path)
        records.append(
            {
                "path": relative_path,
                "byte_length": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return records


def build_artifact_manifest(
    identity: dict[str, Any],
    *,
    root: Path | str = ".",
) -> dict[str, Any]:
    """Seal the exact payload bytes. The manifest never hashes itself."""
    records = artifact_payload_records(root)
    return {
        "schema": PROFILE_ARTIFACT_MANIFEST_SCHEMA,
        "render_key": identity["render_key"],
        "source_kind": identity["source_kind"],
        "generated_at": identity["generated_at"],
        "generator_revision": identity["generator_revision"],
        "generator_source_digest": identity["generator_source_digest"],
        "execution_identity": identity["execution_identity"],
        "render_config": identity["render_config"],
        "claim_input_digest": identity["claim_input_digest"],
        "files": records,
        "artifact_set_digest": canonical_digest(records),
    }


def artifact_manifest_errors(
    manifest: object,
    *,
    root: Path | str = ".",
) -> list[str]:
    """Recompute every byte, digest, and identity the manifest claims."""
    label = PROFILE_ARTIFACT_MANIFEST_PATH
    if not isinstance(manifest, dict):
        return [f"{label} must be an object"]

    errors: list[str] = []
    if manifest.get("schema") != PROFILE_ARTIFACT_MANIFEST_SCHEMA:
        errors.append(f"{label} schema must be {PROFILE_ARTIFACT_MANIFEST_SCHEMA}")
    if manifest.get("source_kind") not in SOURCE_KIND_VALUES:
        errors.append(f"{label} source_kind must name a known generation source")
    for field in ("render_key", "generator_source_digest", "claim_input_digest"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(manifest.get(field, ""))):
            errors.append(f"{label} {field} must be a sha256 digest")
    if not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("generator_revision", ""))):
        errors.append(f"{label} generator_revision must be a 40-hex commit")

    # The key is recomputed from the identity the manifest itself declares. A
    # recorded commit that is absent from local history stays valid while that one
    # identity remains internally consistent; a changed input does not.
    try:
        declared_render_key = render_key_for(manifest)
    except ProfileGenerationIdentityError as exc:
        errors.append(f"{label} render_key cannot be recomputed: {exc}")
    else:
        if manifest.get("render_key") != declared_render_key:
            errors.append(
                f"{label} render_key does not match the identity inputs it declares"
            )

    recorded = manifest.get("files")
    if not isinstance(recorded, list):
        return errors + [f"{label} files must be the exact payload sequence"]

    try:
        observed = artifact_payload_records(root)
    except ProfileGenerationIdentityError as exc:
        return errors + [f"{label} payload bytes are unreadable: {exc}"]

    recorded_paths = [
        entry.get("path") for entry in recorded if isinstance(entry, dict)
    ]
    if recorded_paths != [entry["path"] for entry in observed]:
        errors.append(f"{label} files must list the exact canonical payload roster")
    else:
        for entry, actual in zip(recorded, observed):
            if entry.get("byte_length") != actual["byte_length"] or entry.get(
                "sha256"
            ) != actual["sha256"]:
                errors.append(
                    f"{actual['path']} bytes changed after the manifest recorded them "
                    f"(recorded sha256 {entry.get('sha256')}, observed {actual['sha256']})"
                )
    if manifest.get("artifact_set_digest") != canonical_digest(recorded):
        errors.append(f"{label} artifact_set_digest does not match its own file records")

    try:
        current_source_digest = generator_source_digest()
        current_execution = resolve_execution_identity()
        current_render_config = resolve_render_config(
            str(manifest.get("source_kind", "github-api"))
            if manifest.get("source_kind") in SOURCE_KIND_VALUES
            else "github-api"
        )
    except (ProfileGenerationIdentityError, OSError, ValueError) as exc:
        return errors + [f"{label} generator identity is unverifiable: {exc}"]

    if manifest.get("generator_source_digest") != current_source_digest:
        errors.append(
            f"{label} was produced by different generator bytes; regenerate the artifact set"
        )
    if manifest.get("execution_identity") != current_execution:
        errors.append(
            f"{label} was produced by a different interpreter or dependency set"
        )
    if manifest.get("render_config") != current_render_config:
        errors.append(
            f"{label} was produced by a different effective render configuration"
        )
    return errors
