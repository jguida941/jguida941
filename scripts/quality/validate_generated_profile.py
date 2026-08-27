#!/usr/bin/env python3
"""Validate generated profile files and data contracts."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from scripts.contracts import (
    DISALLOWED_README_HEADINGS,
    PROFILE_ARTIFACT_MANIFEST_PATH,
    PROFILE_GENERATION_SCHEMA,
    PUBLIC_GENERATION_JOINED_KEYS,
    REQUIRED_PROFILE_SNAPSHOT_KEYS,
    REQUIRED_README_MARKERS,
    SOURCE_KIND_VALUES,
    artifact_manifest_errors,
    expected_snapshot_metric_keys,
    missing_required_keys,
    public_snapshot_contract_errors,
)
from scripts.contracts.profile_contract import (
    METRIC_CLAIM_KEY_ATTRIBUTE,
    METRIC_CLAIM_SCOPE_ATTRIBUTE,
    METRIC_CLAIM_STATUS_ATTRIBUTE,
    METRIC_CLAIM_VALUE_ATTRIBUTE,
    PARTIAL_QUALIFICATION_CONSUMERS,
    metric_claim,
    partial_qualification_consumers,
    partial_qualification_disclosures,
)
from scripts.pipeline.profile_helpers import (
    contains_credential_material as _contains_credential_material,
)
from scripts.pipeline.render_outputs import _public_dashboard_data
from scripts.quality.metrics_svg import parse_metrics_svg


USERNAME = os.environ.get("GITHUB_USERNAME", "jguida941")
README_PATH = Path("README.md")
WORKING_SVG_PATH = Path("assets/currently_working.svg")
METRICS_SVG_PATH = Path("metrics.general.svg")
FOCUS_SVG_PATH = Path("assets/now_next_shipped.svg")
SNAPSHOT_SVG_PATH = Path("assets/raw_snapshot.svg")
CONTRIBUTION_SVG_PATH = Path("assets/contribution_calendar.svg")
PROFILE_SNAPSHOT_PATH = Path("site/data/profile_snapshot.json")
PROFILE_MANIFEST_PATH = Path(PROFILE_ARTIFACT_MANIFEST_PATH)
# Every card that repeats the CI-coverage number must carry the same claim.
CI_CLAIM_CARD_PATHS = (
    Path("assets/builder_scorecard.svg"),
    Path("assets/engineering_cadence.svg"),
)
CI_CLAIM_LABEL = "CI coverage"
EXPECTED_CARD_TITLES = {
    Path("assets/badges.svg"): "By The Numbers",
    Path("assets/builder_scorecard.svg"): "Builder Scorecard",
    Path("assets/engineering_cadence.svg"): "Engineering Cadence",
    Path("assets/contribution_calendar.svg"): "Contribution Calendar",
    Path("assets/now_next_shipped.svg"): "Current Focus",
    Path("assets/currently_working.svg"): "Currently Working On",
    Path("assets/lang_breakdown.svg"): "Language Breakdown",
    Path("assets/activity_heatmap.svg"): "When I Code",
    Path("assets/repo_spotlight.svg"): "Flagship Projects",
    Path("assets/raw_snapshot.svg"): "Raw Data Snapshot",
    Path("assets/streak_summary.svg"): "Streak Summary",
}


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _parse_int(value: object) -> int | None:
    normalized = str(value).strip().replace(",", "")
    if normalized.lower() == "n/a":
        return None
    try:
        return int(normalized)
    except ValueError:
        return None


def _rendered_metric_claim(svg_text: str, metric_key: str) -> dict[str, str] | None:
    """Read a card's machine-readable claim and the text it actually shows."""
    root = ET.fromstring(svg_text)
    for node in root.iter():
        if node.attrib.get(METRIC_CLAIM_KEY_ATTRIBUTE) != metric_key:
            continue
        return {
            "display_value": node.attrib.get(METRIC_CLAIM_VALUE_ATTRIBUTE, ""),
            "scope": node.attrib.get(METRIC_CLAIM_SCOPE_ATTRIBUTE, ""),
            "status": node.attrib.get(METRIC_CLAIM_STATUS_ATTRIBUTE, ""),
            "visible_text": " ".join(node.itertext()),
        }
    return None


def _read_manifest(errors: list[str]) -> dict | None:
    if not PROFILE_MANIFEST_PATH.exists():
        errors.append(f"{PROFILE_ARTIFACT_MANIFEST_PATH} not found")
        return None
    try:
        manifest = json.loads(PROFILE_MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        errors.append(f"{PROFILE_ARTIFACT_MANIFEST_PATH} is not valid JSON")
        return None
    if not isinstance(manifest, dict):
        errors.append(f"{PROFILE_ARTIFACT_MANIFEST_PATH} must be an object")
        return None
    return manifest


def _visible_lines(svg_text: str) -> list[str]:
    """Each visible line of a card, as a reader sees it."""
    root = ET.fromstring(svg_text)
    lines = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] != "text":
            continue
        line = " ".join(" ".join(node.itertext()).split())
        if line:
            lines.append(line)
    return lines


def _partial_qualification_errors(profile_snapshot: dict) -> list[str]:
    """A retained partial value must name its own partial basis where it is shown.

    Published status vocabulary is not disclosure to a reader looking at a card,
    so every registered consumer of a partial family must carry that field's
    qualification on one visible line. The proof is semantic and independent of the
    rendered wording: the line has to name the field, its partial status, and each
    meaning the retained number owes. A card that degrades its qualifier to a bare
    word therefore fails here even though it still renders the registered string.
    """
    errors: list[str] = []
    statuses = (profile_snapshot.get("data_quality") or {}).get("metric_statuses") or {}
    for metric_key in sorted(PARTIAL_QUALIFICATION_CONSUMERS):
        if statuses.get(metric_key) != "partial":
            continue
        disclosures = partial_qualification_disclosures(metric_key)
        if not disclosures:
            continue
        for relative_path in partial_qualification_consumers(metric_key):
            consumer = Path(relative_path)
            if not consumer.exists():
                continue
            try:
                lines = _visible_lines(consumer.read_text(encoding="utf-8"))
            except ET.ParseError:
                errors.append(
                    f"{relative_path} is not parsable SVG for {metric_key} "
                    "partial-qualification review"
                )
                continue
            if not any(
                all(
                    any(phrase in line.casefold() for phrase in phrases)
                    for _meaning, phrases in disclosures
                )
                for line in lines
            ):
                errors.append(
                    f"{relative_path} shows {metric_key} without one visible line "
                    "disclosing its partial basis: a reader needs "
                    + ", ".join(meaning for meaning, _phrases in disclosures)
                    + " together on that line"
                )
    return errors


def _ci_coverage_claim_errors(profile_snapshot: dict) -> list[str]:
    """One CI-coverage claim: identical value, scope, and status on every surface.

    Equal file hashes cannot satisfy this law; a card whose bytes are internally
    consistent can still repeat a percentage from a different population, so the
    published claim is compared semantically against each card.
    """
    errors: list[str] = []
    scorecard = profile_snapshot.get("scorecard") or {}
    scopes = (profile_snapshot.get("data_scope") or {}).get("metric_scopes") or {}
    statuses = (profile_snapshot.get("data_quality") or {}).get("metric_statuses") or {}
    published = metric_claim(
        "ci_coverage_pct",
        value=scorecard.get("ci_coverage_pct"),
        scope=scopes.get("ci_coverage_pct"),
        status=statuses.get("ci_coverage_pct"),
    )

    for card_path in CI_CLAIM_CARD_PATHS:
        if not card_path.exists():
            continue
        card_text = card_path.read_text(encoding="utf-8")
        if CI_CLAIM_LABEL not in card_text:
            # An honest empty card repeats no CI number, so it makes no claim.
            continue
        try:
            claim = _rendered_metric_claim(card_text, "ci_coverage_pct")
        except ET.ParseError:
            errors.append(f"{card_path} is not parsable SVG for claim comparison")
            continue
        if claim is None:
            errors.append(
                f"{card_path} repeats CI coverage without a machine-readable claim "
                "naming its value, population scope, and completeness status"
            )
            continue
        observed = {key: claim[key] for key in ("display_value", "scope", "status")}
        expected = {key: published[key] for key in ("display_value", "scope", "status")}
        if observed != expected:
            errors.append(
                f"{card_path} CI coverage claim {observed} does not match the "
                f"published claim {expected}"
            )
        elif claim["display_value"] not in claim["visible_text"]:
            errors.append(
                f"{card_path} shows a CI coverage value its own claim does not declare"
            )
    return errors


def validate_profile() -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not README_PATH.exists():
        errors.append("README.md not found")
        return ValidationResult(errors=tuple(errors), warnings=tuple(warnings))

    readme = README_PATH.read_text(encoding="utf-8")
    if _contains_credential_material(readme):
        errors.append("README contains credential-shaped material")

    for marker in REQUIRED_README_MARKERS:
        if marker not in readme:
            errors.append(f"README missing required marker: {marker}")

    for heading in DISALLOWED_README_HEADINGS:
        if heading in readme:
            errors.append(f"README should not contain duplicate heading: {heading}")

    if "assets/now_next_shipped.svg" not in readme:
        errors.append("README does not embed assets/now_next_shipped.svg")
    if "assets/raw_snapshot.svg" not in readme:
        errors.append("README does not embed assets/raw_snapshot.svg")
    if "assets/contribution_calendar.svg" not in readme:
        errors.append("README does not embed assets/contribution_calendar.svg")
    if "site/data/profile_snapshot.json" not in readme:
        errors.append("README does not link site/data/profile_snapshot.json")

    if not FOCUS_SVG_PATH.exists():
        errors.append("assets/now_next_shipped.svg not found")
    if not SNAPSHOT_SVG_PATH.exists():
        errors.append("assets/raw_snapshot.svg not found")
    if not CONTRIBUTION_SVG_PATH.exists():
        errors.append("assets/contribution_calendar.svg not found")

    for svg_path, title in EXPECTED_CARD_TITLES.items():
        if not svg_path.exists():
            errors.append(f"{svg_path} not found")
            continue
        svg_text = svg_path.read_text(encoding="utf-8")
        if _contains_credential_material(svg_text):
            errors.append(f"{svg_path} contains credential-shaped material")
        title_hits = len(re.findall(rf">{re.escape(title)}</text>", svg_text))
        if title_hits != 1:
            errors.append(
                f"{svg_path} should contain exactly one in-image title '{title}' (found {title_hits})"
            )

    profile_snapshot: dict = {}
    if PROFILE_SNAPSHOT_PATH.exists():
        try:
            profile_snapshot = json.loads(PROFILE_SNAPSHOT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("site/data/profile_snapshot.json is not valid JSON")
            profile_snapshot = {}
    else:
        errors.append("site/data/profile_snapshot.json not found")

    if profile_snapshot:
        try:
            if _public_dashboard_data(profile_snapshot) != profile_snapshot:
                errors.append(
                    "site/data/profile_snapshot.json contains non-publishable fields or values"
                )
        except (TypeError, ValueError):
            errors.append("site/data/profile_snapshot.json exceeds the safe publication boundary")

        missing_keys = missing_required_keys(profile_snapshot, REQUIRED_PROFILE_SNAPSHOT_KEYS)
        if missing_keys:
            errors.append(
                "site/data/profile_snapshot.json missing keys: " + ", ".join(missing_keys)
            )

        # The published nested scope/quality contract, field by field. A snapshot
        # that predates it is not silently accepted as current.
        for message in public_snapshot_contract_errors(profile_snapshot):
            errors.append(f"site/data/profile_snapshot.json {message}")

        snapshot_username = str(profile_snapshot.get("username", "")).strip()
        if snapshot_username and snapshot_username != USERNAME:
            warnings.append("site/data/profile_snapshot.json username does not match GITHUB_USERNAME")

        snapshot = profile_snapshot.get("snapshot", {})
        if not isinstance(snapshot, dict):
            errors.append("site/data/profile_snapshot.json snapshot must be an object")
            snapshot = {}

        snapshot_rows = profile_snapshot.get("snapshot_rows", [])
        if not isinstance(snapshot_rows, list):
            errors.append("site/data/profile_snapshot.json snapshot_rows must be an array")
            snapshot_rows = []

        expected_snapshot_keys = expected_snapshot_metric_keys()
        row_keys = {
            row.get("key")
            for row in snapshot_rows
            if isinstance(row, dict) and isinstance(row.get("key"), str)
        }
        missing_snapshot_rows = sorted(expected_snapshot_keys - row_keys)
        if missing_snapshot_rows:
            errors.append(
                "site/data/profile_snapshot.json snapshot_rows missing metric keys: "
                + ", ".join(missing_snapshot_rows)
            )

        missing_snapshot_values = sorted(key for key in expected_snapshot_keys if key not in snapshot)
        if missing_snapshot_values:
            errors.append(
                "site/data/profile_snapshot.json snapshot missing metric keys: "
                + ", ".join(missing_snapshot_values)
            )

        snapshot_cards = profile_snapshot.get("snapshot_cards", [])
        if not isinstance(snapshot_cards, list):
            errors.append("site/data/profile_snapshot.json snapshot_cards must be an array")
        else:
            card_keys = {
                card.get("key")
                for card in snapshot_cards
                if isinstance(card, dict) and isinstance(card.get("key"), str)
            }
            missing_card_keys = sorted(expected_snapshot_keys - card_keys)
            if missing_card_keys:
                errors.append(
                    "site/data/profile_snapshot.json snapshot_cards missing keys: "
                    + ", ".join(missing_card_keys)
                )

        focus = profile_snapshot.get("focus", {})
        if not isinstance(focus, dict):
            errors.append("site/data/profile_snapshot.json focus must be an object")
        else:
            for lane in ("now", "next", "shipped"):
                lane_items = focus.get(lane)
                if not isinstance(lane_items, list):
                    errors.append(f"site/data/profile_snapshot.json focus.{lane} must be an array")

        if not isinstance(profile_snapshot.get("scorecard", {}), dict):
            errors.append("site/data/profile_snapshot.json scorecard must be an object")
        if not isinstance(profile_snapshot.get("data_scope", {}), dict):
            errors.append("site/data/profile_snapshot.json data_scope must be an object")
        if not isinstance(profile_snapshot.get("data_quality", {}), dict):
            errors.append("site/data/profile_snapshot.json data_quality must be an object")
        if not isinstance(profile_snapshot.get("activity_feed", []), list):
            errors.append("site/data/profile_snapshot.json activity_feed must be an array")
        if not isinstance(profile_snapshot.get("repo_language_matrix", []), list):
            errors.append("site/data/profile_snapshot.json repo_language_matrix must be an array")
        if not isinstance(profile_snapshot.get("recent_created", []), list):
            errors.append("site/data/profile_snapshot.json recent_created must be an array")

        if "generation" in profile_snapshot:
            generation = profile_snapshot.get("generation")
            if not isinstance(generation, dict):
                errors.append("site/data/profile_snapshot.json generation must be an object")
            else:
                if generation.get("schema") != PROFILE_GENERATION_SCHEMA:
                    errors.append(
                        "site/data/profile_snapshot.json generation.schema must be "
                        + PROFILE_GENERATION_SCHEMA
                    )
                if generation.get("source_kind") not in SOURCE_KIND_VALUES:
                    errors.append(
                        "site/data/profile_snapshot.json generation.source_kind must name "
                        "a known generation source"
                    )

        errors.extend(_partial_qualification_errors(profile_snapshot))
        errors.extend(_ci_coverage_claim_errors(profile_snapshot))

        stars_value = _parse_int(snapshot.get("total_stars"))
        if stars_value is None:
            warnings.append("Snapshot total_stars is missing or non-numeric")

        releases_value = _parse_int(snapshot.get("releases"))
        releases_status = str(profile_snapshot.get("data_quality", {}).get("releases_status", "")).strip().lower()
        if releases_value is None and releases_status not in {"unavailable", "events_fallback", "partial", "fallback"}:
            warnings.append("Snapshot releases is missing or non-numeric")

        if METRICS_SVG_PATH.exists():
            metrics_svg_text = METRICS_SVG_PATH.read_text(encoding="utf-8")
            if _contains_credential_material(metrics_svg_text):
                errors.append("metrics.general.svg contains credential-shaped material")
            metrics = parse_metrics_svg(METRICS_SVG_PATH)
            metrics_repositories = metrics.repositories
            metrics_releases = metrics.releases
            metrics_stargazers = metrics.stargazers

            if metrics_repositories is None:
                warnings.append("metrics.general.svg missing Repositories metric")
            if metrics_releases is None:
                warnings.append("metrics.general.svg missing Releases metric")
            if metrics_stargazers is None:
                warnings.append("metrics.general.svg missing Stargazers metric")

            if (
                stars_value is not None
                and stars_value > 0
                and metrics_stargazers is not None
                and metrics_stargazers == 0
            ):
                warnings.append(
                    "metrics.general.svg reports 0 Stargazers while snapshot reports non-zero Total Stars"
                )

            if (
                releases_value is not None
                and releases_value > 0
                and metrics_releases is not None
                and metrics_releases == 0
            ):
                warnings.append(
                    "metrics.general.svg reports 0 Releases while snapshot reports non-zero recent releases"
                )
        else:
            warnings.append("metrics.general.svg not found")

    # The external manifest is recomputed, never trusted: every payload length,
    # digest, and the aggregate set digest are derived from the bytes on disk, and
    # the generator source, execution, and effective render identities are
    # recomputed in this venue so stale output cannot pass as current.
    manifest = _read_manifest(errors)
    if manifest is not None:
        errors.extend(artifact_manifest_errors(manifest))
        generation = profile_snapshot.get("generation")
        if isinstance(generation, dict):
            # Both copies describe one generation; every duplicated field is joined,
            # not just the key, so the two records cannot disagree about origin.
            for field in PUBLIC_GENERATION_JOINED_KEYS:
                if generation.get(field) != manifest.get(field):
                    errors.append(
                        f"site/data/profile_snapshot.json generation.{field} does not "
                        "match the sealed artifact manifest generation identity"
                    )

    if WORKING_SVG_PATH.exists():
        working_svg = WORKING_SVG_PATH.read_text(encoding="utf-8")
        placeholder_hits = working_svg.count("latest commit message unavailable")
        if placeholder_hits >= 3:
            warnings.append(f"Currently working card has {placeholder_hits} placeholder commit messages")
    else:
        warnings.append("assets/currently_working.svg not found")

    return ValidationResult(errors=tuple(errors), warnings=tuple(warnings))


def _finish(result: ValidationResult) -> None:
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


def main() -> int:
    os.chdir(ROOT)
    result = validate_profile()
    _finish(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
