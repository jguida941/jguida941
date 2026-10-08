#!/usr/bin/env python3
"""Validate generated profile files and data contracts."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
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
    contribution_trend_errors, contribution_trend_display,
    contribution_rhythm_errors, contribution_rhythm_display,
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
    Path("assets/activity_heatmap.svg"): "Contribution Rhythm",
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
            "visible_values": ["".join(child.itertext()).strip() for child in node.iter()
                               if child.tag.rsplit("}", 1)[-1] == "text"],
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
        workflow = (profile_snapshot.get("automation") or {}).get("combined") or {}
        if metric_key == "ci_coverage_pct" and workflow and workflow.get("eligible_repos") is None:
            disclosures = (
                ("the workflow field", ("workflow",)),
                ("partial status", ("partial",)),
                ("observed subtotal", ("observed subtotal",)),
                ("unknown eligible inventory", ("eligible inventory unknown",)),
            )
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
        # Artifact role and the source model govern this requirement. Renaming a
        # label or deleting a carrier must never disable semantic validation.
        if card_path.name == "builder_scorecard.svg":
            renders_gauge = bool(profile_snapshot.get("automation")) or any(
                scorecard.get(key) for key in (
                    "last_year_contributions", "active_days_last_year", "active_repos_7d",
                    "automation_workflows", "releases_30d", "primary_lang_share_pct",
                )
            ) or scorecard.get("ci_coverage_pct") is not None
        else:
            engineering = profile_snapshot.get("engineering") or {}
            renders_gauge = bool(profile_snapshot.get("automation")) or any(
                engineering.get(key) for key in (
                    "weekly_cadence", "active_days_last_year", "automation_workflows",
                    "public_repos_total", "private_repos_total",
                )
            ) or scorecard.get("ci_coverage_pct") is not None
        try:
            claim = _rendered_metric_claim(card_text, "ci_coverage_pct")
        except ET.ParseError:
            errors.append(f"{card_path} is not parsable SVG for claim comparison")
            continue
        if claim is None:
            if not renders_gauge:
                continue
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
        elif claim["display_value"] not in claim["visible_values"]:
            errors.append(
                f"{card_path} shows a CI coverage value its own claim does not declare"
            )
    return errors


def _native_path_vertical_bounds(data: str) -> tuple[float, float]:
    """Conservative bounds for the straight segments and unrotated native arcs.

    This deliberately excludes curves and SVG's arc-radius correction. The
    lower-row icons use this small grammar; unsupported paths cannot establish
    clearance from the chart. Arc bounds overestimate, rather than sample, paint.
    """
    tokens = re.findall(r"[MmLlHhVvAaZz]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", data)
    if re.sub(r"[\s,]", "", data) != "".join(tokens):
        raise ValueError("unsupported native path")
    x = y = start_x = start_y = 0.0
    lower = math.inf
    upper = -math.inf
    command = ""
    index = 0
    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
        if not command or (lower == math.inf and command not in "Mm"):
            raise ValueError("native path must start with move")
        kind = command.upper()
        if kind == "Z":
            x, y = start_x, start_y
            lower, upper = min(lower, y), max(upper, y)
            command = ""
            continue
        size = {"M": 2, "L": 2, "H": 1, "V": 1, "A": 7}[kind]
        args = [float(token) for token in tokens[index:index + size]]
        if len(args) != size or not all(math.isfinite(value) for value in args):
            raise ValueError("invalid native path coordinates")
        index += size
        previous_x, previous_y = x, y
        relative = command.islower()
        if kind in {"M", "L", "A"}:
            x, y = args[-2:]
            if relative:
                x, y = x + previous_x, y + previous_y
        elif kind == "H":
            x = args[0] + (x if relative else 0)
        else:
            y = args[0] + (y if relative else 0)
        if kind == "M":
            start_x, start_y = x, y
            command = "l" if relative else "L"
            previous_y = y
        low, high = min(previous_y, y), max(previous_y, y)
        if kind == "A":
            rx, ry, rotation, large, sweep = args[:5]
            if (rx <= 0 or ry <= 0 or rotation != 0 or large not in {0, 1} or sweep not in {0, 1}
                    or ((x - previous_x) / (2 * rx)) ** 2 + ((y - previous_y) / (2 * ry)) ** 2 > 1):
                raise ValueError("unsupported native arc")
            low, high = low - 2 * ry, high + 2 * ry
        lower, upper = min(lower, low), max(upper, high)
    if not math.isfinite(lower) or not math.isfinite(upper):
        raise ValueError("empty native path")
    return lower, upper


def _contribution_topology_errors(root: ET.Element, chart: ET.Element) -> list[str]:
    """Keep later native paint below the chart's reserved region (through y=334).

    Earlier panel effects remain valid because they paint beneath the chart.
    Later paint is limited to the native lower-row primitives and simple icon
    transforms, with conservative stroke/path/text clearance. Unknown effects
    fail closed; this is neither arbitrary SVG layout nor font measurement.
    """
    local = lambda node: node.tag.rsplit("}", 1)[-1]
    siblings = list(root)
    if chart not in siblings:
        return ["unsupported contribution painter topology"]
    position = siblings.index(chart)

    def number(node, key, default=None):
        value = float(node.get(key, default))
        if not math.isfinite(value):
            raise ValueError("nonfinite sibling geometry")
        return value

    # Geometry, not a self-reported role, establishes the native full-card base.
    def backdrop(node):
        if local(node) != "rect":
            return False
        try:
            return (number(node, "x") <= 252 and number(node, "y") <= 92
                    and number(node, "x") + number(node, "width") >= 812
                    and number(node, "y") + number(node, "height") >= 334)
        except (TypeError, ValueError):
            return False

    if not any(backdrop(node) for node in siblings[:position]):
        return ["contribution chart precedes its native backdrop"]
    paint = {"fill", "fill-opacity", "stroke", "stroke-opacity", "stroke-width", "stroke-linecap",
             "stroke-linejoin", "opacity"}
    metric = {METRIC_CLAIM_KEY_ATTRIBUTE, METRIC_CLAIM_SCOPE_ATTRIBUTE,
              METRIC_CLAIM_STATUS_ATTRIBUTE, METRIC_CLAIM_VALUE_ATTRIBUTE}
    shapes = {
        "rect": {"x", "y", "width", "height", "rx", "ry"},
        "circle": {"cx", "cy", "r", "stroke-dasharray", "transform"},
        "line": {"x1", "x2", "y1", "y2"},
        "path": {"d"},
        "text": {"x", "y", "font-size", "font-family", "font-weight", "text-anchor", "letter-spacing"},
    }

    def below(node, offset=0.0, scale=1.0, stroke=1.0, join="miter", cap="butt"):
        kind = local(node)
        if kind in {"desc", "title", "metadata", "defs", "clipPath", "linearGradient", "radialGradient"}:
            return True  # These nodes do not paint themselves.
        if set(node.attrib) - (paint | (metric | {"transform"} if kind == "g" else shapes.get(kind, set()))):
            return False
        own_stroke = number(node, "stroke-width", stroke)
        join = node.get("stroke-linejoin", join)
        cap = node.get("stroke-linecap", cap)
        if join not in {"miter", "round", "bevel"} or cap not in {"butt", "round", "square"}:
            return False
        if own_stroke < 0:
            return False
        for attribute in ("opacity", "fill-opacity", "stroke-opacity"):
            if attribute in node.attrib and not 0 <= number(node, attribute) <= 1:
                return False
        if kind == "g":
            if "transform" in node.attrib:
                # Native icon transform order is translation followed by scale.
                match = re.fullmatch(r"translate\(([-+\d.eE]+),([-+\d.eE]+)\) scale\(([-+\d.eE]+)\)", node.get("transform", ""))
                if not match:
                    return False
                x, y, factor = map(float, match.groups())
                if not all(math.isfinite(value) for value in (x, y, factor)) or not 0 < factor <= 1:
                    return False
                offset, scale = offset + scale * y, scale * factor
            return all(below(child, offset, scale, own_stroke, join, cap) for child in node)
        if kind not in shapes or list(node):
            return False
        if kind == "rect":
            top = number(node, "y")
            if number(node, "width") < 0 or number(node, "height") < 0:
                return False
        elif kind == "circle":
            radius = number(node, "r")
            if radius < 0:
                return False
            top = number(node, "cy") - radius
            if "transform" in node.attrib:
                rotation = re.fullmatch(r"rotate\(-90 ([-+\d.eE]+) ([-+\d.eE]+)\)", node.get("transform", ""))
                if not rotation or tuple(map(float, rotation.groups())) != (number(node, "cx"), number(node, "cy")):
                    return False  # Centered rotation preserves a ring's bounds.
        elif kind == "line":
            top = min(number(node, "y1"), number(node, "y2"))
        elif kind == "path":
            top, _ = _native_path_vertical_bounds(node.get("d", ""))
        else:
            size = number(node, "font-size")
            if not 0 < size <= 32:
                return False
            top = number(node, "y") - 1.5 * size
        # Default miter limit is four half-widths; round native icons need only
        # a half-width. Square caps also use the conservative larger allowance.
        margin = own_stroke * (0.5 if join == "round" and cap != "square" else 2)
        return offset + scale * (top - margin) >= 334

    try:
        if not all(below(node) for node in siblings[position + 1:]):
            return ["unsupported contribution sibling paint or chart overlap"]
    except (TypeError, ValueError, KeyError, OverflowError):
        return ["unresolved contribution sibling geometry"]
    return []


def _contribution_trend_claim_errors(profile_snapshot: dict) -> list[str]:
    """Certify the generated chart grammar, including its actual rendered effects.

    This bounded checker cannot resolve arbitrary CSS or transforms. Unsupported
    effects fail closed here while unrelated native panel/icon effects stay valid.
    """
    path = Path("assets/engineering_cadence.svg")
    engineering = profile_snapshot.get("engineering") or {}
    trend = engineering.get("contribution_trend")
    problems = contribution_trend_errors(trend)
    if problems:
        return [f"{path}: {problem}" for problem in problems]
    display = contribution_trend_display(trend)
    if engineering.get("weekly_cadence") != display["values"]:
        return [f"{path}: compatibility contribution values disagree"]
    if not path.exists():
        return [f"{path}: contribution trend artifact missing"]
    try:
        source = path.read_text(encoding="utf-8")
        root = ET.fromstring(source)
    except ET.ParseError:
        return [f"{path}: invalid contribution SVG"]
    svg_namespace = "{http://www.w3.org/2000/svg}"
    if root.tag != svg_namespace + "svg":
        return [f"{path}: contribution document must be SVG"]
    tag = lambda node: node.tag.rsplit("}", 1)[-1]
    groups = [node for node in root.iter() if node.get("data-series") == "weekly-contributions"]
    renders_body = bool(profile_snapshot.get("automation")) or any(engineering.get(key) for key in (
        "weekly_cadence", "active_days_last_year", "automation_workflows", "public_repos_total", "private_repos_total"))
    if len(groups) != 1:
        if not display["available"] and not renders_body and not groups:
            return []
        return [f"{path}: one contribution trend group required"]
    group = groups[0]
    if group.tag != svg_namespace + "g" or any(
            not node.tag.startswith(svg_namespace) for node in group.iter()):
        problems.append("contribution chart requires SVG element identities")
    problems.extend(_contribution_topology_errors(root, group))
    parents = {child: parent for parent in root.iter() for child in parent}
    ancestor = group
    while ancestor is not None:
        allowed = {"data-series"} if ancestor is group else {"width", "height", "viewBox", "version"} if ancestor is root else set()
        if set(ancestor.attrib) - allowed:
            problems.append("unsupported contribution ancestor effect")
        ancestor = parents.get(ancestor)
    if ("<?xml-stylesheet" in source or any(tag(node) in {
            "style", "script", "animate", "animateTransform", "set", "foreignObject"} for node in root.iter())):
        problems.append("unsupported contribution dynamic or stylesheet effect")
    attributes = {
        "desc": set(),
        "text": {"data-role", "x", "y", "fill", "font-size", "font-family", "font-weight", "text-anchor"},
        "line": {"x1", "x2", "y1", "y2", "stroke", "stroke-opacity", "stroke-width"},
        "polyline": {"data-role", "points", "fill", "stroke", "stroke-width"},
        "polygon": {"data-role", "points", "fill"},
        "circle": {"data-role", "cx", "cy", "r", "fill", "stroke", "stroke-width"},
        "linearGradient": {"id", "x1", "x2", "y1", "y2"},
        "stop": {"offset", "stop-color", "stop-opacity"},
    }
    for node in group.iter():
        if node is group:
            continue
        kind = tag(node)
        if kind not in attributes or set(node.attrib) - attributes.get(kind, set()):
            problems.append("unsupported contribution primitive effect")
        if list(node) and kind != "linearGradient":
            problems.append("unsupported nested contribution primitive")
        if kind == "linearGradient" and any(tag(child) != "stop" for child in node):
            problems.append("unsupported contribution gradient")
    def number(node, key, expected):
        try:
            value = float(node.get(key, ""))
            return math.isfinite(value) and abs(value - expected) <= 0.011
        except (TypeError, ValueError):
            return False
    def paint(value):
        # Generated native palettes are opaque RGB. No implicit inherited paint.
        return isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?", value) is not None
    try:
        viewport = [float(value) for value in root.get("viewBox", "").split()]
        height = float(root.get("height", ""))
        if (not number(root, "width", 840) or not math.isfinite(height) or height < 344
                or viewport != [0, 0, 840, height] or parents.get(group) is not root):
            problems.append("unsupported contribution viewport")
    except (TypeError, ValueError):
        problems.append("invalid contribution viewport")
    def geometry(node, expected):
        try:
            pairs = [tuple(map(float, pair.split(","))) for pair in node.get("points", "").split()]
            return len(pairs) == len(expected) and all(
                len(actual) == 2 and all(math.isfinite(a) and abs(a - b) <= 0.011 for a, b in zip(actual, wanted))
                for actual, wanted in zip(pairs, expected))
        except (TypeError, ValueError):
            return False
    children = list(group)
    kinds = lambda kind: [node for node in children if tag(node) == kind]
    texts = kinds("text")
    expected_text = [(display["title"], 252, 108, "start", None)]
    lines, areas, markers = kinds("polyline"), kinds("polygon"), kinds("circle")
    grids, gradients = kinds("line"), kinds("linearGradient")
    if display["available"]:
        values = display["values"]
        # Independently derive the zero scale from source values, not SVG metadata.
        step = 1
        required = max(1, (max(values) + 2) // 3)
        while step < required:
            power = 10 ** (len(str(step)) - 1)
            step = next(candidate for candidate in (2 * power, 5 * power, 10 * power) if candidate > step)
        top = 3 * step
        expected_points = [(546 if len(values) == 1 else 312 + index / (len(values) - 1) * 468,
                            272 - value / top * 112) for index, value in enumerate(values)]
        for count in (0, step, 2 * step, top):
            expected_text.append((count, 300, 272 - count / top * 112 + 4.76, "end", "y-tick"))
        if len(grids) != 4 or any(not all(number(node, key, expected) for key, expected in (
                ("x1", 312), ("x2", 780), ("y1", 272 - i * 112 / 3), ("y2", 272 - i * 112 / 3),
                ("stroke-width", 1), ("stroke-opacity", .18))) or not paint(node.get("stroke"))
                for i, node in enumerate(grids)):
            problems.append("contribution grid geometry disagrees")
        if len(values) >= 2:
            if (len(lines) != 1 or not geometry(lines[0], expected_points)
                    or lines[0].get("data-role") != "trend-line" or lines[0].get("fill") != "none"
                    or not paint(lines[0].get("stroke")) or not number(lines[0], "stroke-width", 2.5)):
                problems.append("contribution plotted values or stroke disagree")
            if (len(areas) != 1 or not geometry(areas[0], [(312, 272), *expected_points, (780, 272)])
                    or areas[0].get("data-role") != "trend-area"
                    or areas[0].get("fill") != "url(#eng-contribution-area)"):
                problems.append("contribution zero-baseline area disagrees")
            if (len(gradients) != 1 or gradients[0].get("id") != "eng-contribution-area"
                    or sum(node.get("id") == "eng-contribution-area" for node in root.iter()) != 1
                    or not all(number(gradients[0], key, value) for key, value in (("x1", 0), ("x2", 0), ("y1", 0), ("y2", 1)))):
                problems.append("contribution area gradient disagrees")
            else:
                stops = list(gradients[0])
                if len(stops) != 2 or any(node.get("offset") != offset or not paint(node.get("stop-color"))
                        or not number(node, "stop-opacity", opacity)
                        for node, offset, opacity in zip(stops, ("0%", "100%"), (.16, 0))):
                    problems.append("contribution gradient stops disagree")
        elif lines or areas or gradients:
            problems.append("singleton contribution has an invented interval")
        from scripts.core.config import BG_DARK
        if len(markers) != len(expected_points):
            problems.append("contribution weekly marker count disagrees")
        for node, (x, y), point in zip(markers, expected_points, trend["points"]):
            hollow = node.get("fill", "").lower() == BG_DARK.lower()
            if (node.get("data-role") != "week-point" or not all(number(node, key, value) for key, value in (
                    ("cx", x), ("cy", y), ("r", 3), ("stroke-width", 1.5)))
                    or not paint(node.get("fill")) or not paint(node.get("stroke"))
                    or node.get("stroke", "").lower() == BG_DARK.lower() or hollow != point["partial"]):
                problems.append("contribution weekly marker geometry or completeness disagrees")
        from datetime import date
        months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
        for index in sorted({0, (len(values) - 1) // 2, len(values) - 1}):
            day = date.fromisoformat(trend["points"][index]["week_start"])
            expected_text.append((f"{months[day.month - 1]} {day.day}", expected_points[index][0], 296, "middle", "x-tick"))
        expected_text.append((display["window"], 252, 132, "start", None))
        if ["".join(node.itertext()) for node in kinds("desc")] != [display["description"]]:
            problems.append("contribution point descriptions disagree")
    elif lines or areas or markers or grids or gradients or kinds("desc"):
        problems.append("unavailable contribution trend has quantitative geometry")
    expected_text.append((display["qualification"], 252, 320, "start", None))
    if len(texts) != len(expected_text):
        problems.append("contribution visible context count disagrees")
    for node, (content, x, y, anchor, role) in zip(texts, expected_text):
        actual = "".join(node.itertext())
        if isinstance(content, int):
            try:
                matches = float(actual.replace(",", "")) == content
            except ValueError:
                matches = False
        else:
            matches = actual == content
        if (not matches or not all(number(node, key, value) for key, value in (
                ("x", x), ("y", y), ("font-size", 14), ("font-weight", 400)))
                or node.get("text-anchor", "start") != anchor or node.get("data-role") != role
                or not paint(node.get("fill")) or not node.get("font-family")):
            problems.append("contribution visible unit/window/axis/qualification disagrees")
    return [f"{path}: {problem}" for problem in problems]


def _contribution_rhythm_claim_errors(profile_snapshot: dict) -> list[str]:
    """Verify native SVG paint, text and geometry against the published weekday model.

    The supported representation is deliberately small: native chrome followed
    by one untransformed group of text and seven linear bars. Exact topology
    prevents hidden, replaced or later-overpainted quantitative claims. This is
    not a validator for arbitrary SVGs or a font/palette certification.
    """
    from scripts.core.config import CYAN, FONT_SANS, SVG_WIDTH, TEXT, TEXT_BRIGHT, TEXT_DIM
    from scripts.rendering.components import section_header
    from scripts.rendering.glass_kit import glass_panel

    path = Path("assets/activity_heatmap.svg")
    rhythm = profile_snapshot.get("contribution_rhythm")
    problems = contribution_rhythm_errors(rhythm)
    if problems:
        return [f"{path}: {problem}" for problem in problems]
    display = contribution_rhythm_display(rhythm)
    if profile_snapshot.get("contribution_rhythm_display") != display:
        return [f"{path}: serialized contribution rhythm display disagrees"]
    if not path.exists():
        return [f"{path}: contribution rhythm missing"]
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except (ET.ParseError, OSError):
        return [f"{path}: contribution rhythm is not readable SVG"]
    namespace = "http://www.w3.org/2000/svg"
    width, height = SVG_WIDTH, 480 if display["available"] else 232
    expected_root = {"width": str(width), "height": str(height), "viewBox": f"0 0 {width} {height}",
                     "role": "img", "aria-labelledby": "rhythm-title rhythm-description"}
    if root.tag != f"{{{namespace}}}svg" or root.attrib != expected_root or (root.text or "").strip():
        return [f"{path}: unsupported contribution rhythm root/effects"]

    def signature(node):
        return (node.tag, node.attrib, node.text or "", node.tail or "",
                [signature(child) for child in node])

    children = list(root)
    if len(children) < 3:
        return [f"{path}: contribution rhythm content missing"]
    title, description = children[:2]
    expected_description = " ".join(display[key] for key in ("scope", "explanation", "coverage_summary") if display[key])
    if (title.tag != f"{{{namespace}}}title" or title.attrib != {"id": "rhythm-title"}
            or title.text != "Contribution Rhythm" or list(title) or (title.tail or "")
            or description.tag != f"{{{namespace}}}desc" or description.attrib != {"id": "rhythm-description"}
            or description.text != expected_description or list(description) or (description.tail or "")):
        problems.append("contribution rhythm accessible meaning disagrees")
    # Only the established native backdrop/header may precede the final chart.
    # Matching real paint geometry (not role metadata) rules out later overlays.
    header, _ = section_header(28, 46, "Contribution Rhythm", width=width,
                               eyebrow="Contribution calendar", pad=28)
    chrome = ET.fromstring(f'<svg xmlns="{namespace}">' + glass_panel(width, height) + header + '</svg>')
    if [signature(node) for node in children[2:-1]] != [signature(node) for node in chrome]:
        problems.append("contribution rhythm native chrome/topology disagrees")
    chart = children[-1]
    expected = ET.Element(f"{{{namespace}}}g", {"data-series": "weekday-contributions"})

    def text(parent, value, x, y, color=TEXT, anchor="start"):
        node = ET.SubElement(parent, f"{{{namespace}}}text", {
            "x": str(x), "y": str(y), "font-size": "14", "font-family": FONT_SANS,
            "fill": color, "text-anchor": anchor,
        })
        node.text = value

    text(expected, "Contributions by weekday", 28, 116, TEXT_BRIGHT)
    if display["available"]:
        text(expected, display["caption"], 28, 142, TEXT_DIM)
        maximum = max(row["contributions"] for row in rhythm["weekdays"]) or 1
        for i, row in enumerate(rhythm["weekdays"]):
            y = 178 + 34 * i
            group = ET.SubElement(expected, f"{{{namespace}}}g", {
                "data-weekday": row["weekday"], "data-contributions": str(row["contributions"]),
                "data-days-observed": str(row["days_observed"]),
            })
            text(group, row["weekday"], 28, y + 5)
            ET.SubElement(group, f"{{{namespace}}}rect", {
                "x": "92", "y": str(y - 8), "width": f'{row["contributions"] / maximum * (width - 200):.3f}',
                "height": "12", "rx": "3", "fill": CYAN,
            })
            text(group, f'{row["contributions"]:,}', width - 28, y + 5, TEXT_BRIGHT, "end")
        text(expected, display["message"], 28, 416, TEXT_DIM)
        text(expected, display["qualification"], 28, 438, TEXT_DIM)
    else:
        text(expected, "Contribution rhythm unavailable", 28, 160, TEXT_BRIGHT)
        text(expected, display["qualification"], 28, 192, TEXT_DIM)
    if signature(chart) != signature(expected):
        problems.append("contribution rhythm visible text/counts/geometry/effects disagree")
    return [f"{path}: {problem}" for problem in problems]


def _dashboard_summary_errors(payload):
    """The public model and the actual composed SVG bytes must describe one view."""
    from scripts.contracts.dashboard_summary import SCHEMA
    from scripts.rendering.generate_dashboard_summary import render_svg
    errors = []
    summary = payload.get("dashboard_summary")
    if not isinstance(summary, dict) or summary.get("schema") != SCHEMA:
        return ["public dashboard summary missing or invalid"]
    generation = payload.get("generation") or {}
    for mobile, name in ((False, "assets/dashboard_summary.svg"), (True, "assets/dashboard_summary_mobile.svg")):
        path = Path(name)
        try:
            text = path.read_text(encoding="utf-8")
            if text != render_svg(summary, mobile=mobile, generation=generation):
                errors.append(name + ": composed drawing does not match the public presentation")
        except (OSError, ValueError, TypeError, KeyError):
            errors.append(name + ": composed drawing unavailable or malformed")
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

    if readme.count("<picture>") != 1 or 'media="(max-width: 767px)"' not in readme:
        errors.append("README must mount one responsive dashboard picture")
    if "assets/now_next_shipped.svg" not in readme:
        errors.append("README does not retain legacy detail link assets/now_next_shipped.svg")
    if "assets/raw_snapshot.svg" not in readme:
        errors.append("README does not retain legacy detail link assets/raw_snapshot.svg")
    if "assets/contribution_calendar.svg" not in readme:
        errors.append("README does not retain legacy detail link assets/contribution_calendar.svg")
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
        errors.extend(_dashboard_summary_errors(profile_snapshot))
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
        errors.extend(_contribution_trend_claim_errors(profile_snapshot))
        errors.extend(_contribution_rhythm_claim_errors(profile_snapshot))

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
