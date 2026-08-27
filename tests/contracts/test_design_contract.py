"""Executable contracts for the repository's documented visual system.

Each test maps a product-level invariant from ``docs/DESIGN_AUDIT.md`` and
``docs/DESIGN_SPEC.md`` to an observable renderer or profile-model result.
The intended direction is Apple HIG restraint with Power BI information
architecture, including the numeric thresholds documented in the specification.

The guards keep colors and sizes on the shared token sources, preserve readable
text, and require public and private repository metadata to behave consistently
on surfaces that share the same repository scope.
"""
from __future__ import annotations

import copy
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]  # tests/<group>/<file>.py -> repo root
RENDERING = ROOT / "scripts" / "rendering"

# Hex colors belong in the token source (scripts/core/config.py / design_tokens),
# never hard-coded at a rendering call site.
_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
# Designated token SOURCES inside scripts/rendering/ — hex legitimately lives here
# (config.py is the SVG source; design_tokens.py is the web/theme source). Their
# values are governed by their own contracts (test_theme_system), not this scan.
_TOKEN_SOURCES = frozenset({"design_tokens.py"})
# Literal font-size attributes emitted into SVG.
_FONT = re.compile(r'font-size="([0-9.]+)"')
# Legibility floor for README SVGs downscaled into the column (DESIGN_SPEC).
MIN_FONT = 11.0

_PUBLISHED_PROFILE_PATHS = (
    "README.md",
    "metrics.general.svg",
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
)
_GOVERNED_AGGREGATE_METRICS = {
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


def _code_lines(path: Path):
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):  # skip full-line comments
            continue
        yield i, line


def _validate_snapshot_payload(payload: dict):
    from scripts.quality.validate_generated_profile import validate_profile

    with tempfile.TemporaryDirectory() as directory:
        output_root = Path(directory)
        for relative_path in _PUBLISHED_PROFILE_PATHS:
            source = ROOT / relative_path
            destination = output_root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        snapshot_path = output_root / "site/data/profile_snapshot.json"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

        original_cwd = Path.cwd()
        os.chdir(output_root)
        try:
            return validate_profile()
        finally:
            os.chdir(original_cwd)


class PublishedProfileContract(unittest.TestCase):
    def _valid_nested_payload(self):
        payload = json.loads(
            (ROOT / "site/data/profile_snapshot.json").read_text(encoding="utf-8")
        )
        payload["data_scope"] = {
            "repos_included": "public + private observed, exact",
            "activity_metric_scope": "last twelve months",
            "public_owned_repos_total": 2,
            "public_owned_forks_total": 0,
            "public_owned_nonfork_repos_total": 2,
            "private_owned_repos_total": 1,
            "private_owned_nonfork_repos_total": 1,
            "metric_scopes": {
                metric: "owned-public-private-nonfork-profile-excluded-exact"
                for metric in _GOVERNED_AGGREGATE_METRICS
            },
        }
        payload["data_quality"] = {
            "ci_status": "exact",
            "ci_note": "Current repository evidence.",
            "commits_status": "exact",
            "commits_note": "Current repository evidence.",
            "releases_status": "exact",
            "releases_note": "Current repository evidence.",
            "events_status": "exact",
            "events_note": "Current repository evidence.",
            "private_aggregate_status": "exact",
            "metric_statuses": {
                metric: "exact" for metric in _GOVERNED_AGGREGATE_METRICS
            },
        }
        return payload

    def test_public_snapshot_requires_every_nested_scope_and_quality_field(self):
        valid_payload = self._valid_nested_payload()
        valid_errors = _validate_snapshot_payload(valid_payload).errors
        self.assertFalse(
            any(
                "data_scope." in error or "data_quality." in error
                for error in valid_errors
            ),
            valid_errors,
        )

        required_paths = {
            "data_scope": (
                "repos_included",
                "activity_metric_scope",
                "public_owned_repos_total",
                "public_owned_forks_total",
                "public_owned_nonfork_repos_total",
                "private_owned_repos_total",
                "private_owned_nonfork_repos_total",
                "metric_scopes",
            ),
            "data_quality": (
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
            ),
        }
        for section, fields in required_paths.items():
            for field in fields:
                with self.subTest(missing=f"{section}.{field}"):
                    altered = copy.deepcopy(valid_payload)
                    del altered[section][field]
                    errors = _validate_snapshot_payload(altered).errors
                    expected_path = f"{section}.{field}"
                    self.assertTrue(
                        any(expected_path in error for error in errors),
                        errors,
                    )

        invalid_values = (
            ("data_scope", "public_owned_repos_total", True),
            ("data_scope", "private_owned_nonfork_repos_total", -1),
            ("data_scope", "metric_scopes", {"ci_coverage_pct": "exact"}),
            ("data_quality", "private_aggregate_status", "ok"),
            ("data_quality", "metric_statuses", {"ci_coverage_pct": "exact"}),
        )
        for section, field, value in invalid_values:
            with self.subTest(invalid=f"{section}.{field}"):
                altered = copy.deepcopy(valid_payload)
                altered[section][field] = value
                errors = _validate_snapshot_payload(altered).errors
                expected_path = f"{section}.{field}"
                self.assertTrue(
                    any(expected_path in error for error in errors),
                    errors,
                )

        with self.subTest(invalid="data_quality.token_mode"):
            altered = copy.deepcopy(valid_payload)
            altered["data_quality"]["token_mode"] = "internal"
            errors = _validate_snapshot_payload(altered).errors
            self.assertTrue(
                any("data_quality.token_mode" in error for error in errors),
                errors,
            )


class PublishedMetricClaimContract(unittest.TestCase):
    def test_ci_coverage_claim_is_identical_across_json_and_cards(self):
        import xml.etree.ElementTree as ET

        from scripts.pipeline.compute_metrics import compute_profile_model
        from scripts.pipeline.render_outputs import ensure_output_dirs, generate_assets
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests

        collected = AccuracyTests()._collected()
        first_public = copy.deepcopy(collected.repos[1])
        first_public.update(
            {
                "name": "public-automated",
                "has_ci_workflows": True,
                "workflow_file_count": 1,
            }
        )
        second_public = copy.deepcopy(collected.repos[2])
        second_public.update(
            {
                "name": "public-manual",
                "has_ci_workflows": False,
                "workflow_file_count": 0,
            }
        )
        private_repository = copy.deepcopy(collected.private_repos[0])
        private_repository.update(
            {
                "name": "private-manual",
                "has_ci_workflows": False,
                "workflow_file_count": 0,
            }
        )
        collected = replace(
            collected,
            repo_counts={
                "public_owned_total": 2,
                "public_owned_forks": 0,
                "public_owned_nonfork": 2,
                "private_owned": 1,
                "private_owned_nonfork": 1,
            },
            repos=[first_public, second_public],
            all_repos=[first_public, second_public],
            private_repos=[private_repository],
            events=[],
        )
        model = compute_profile_model(
            collected,
            logger=lambda *_args, **_kwargs: None,
            allow_network_calls=False,
        )
        expected_scope = model["data_scope"]["metric_scopes"]["ci_coverage_pct"]
        expected_status = model["data_quality"]["metric_statuses"]["ci_coverage_pct"]
        self.assertAlmostEqual(100 / 3, model["scorecard"]["ci_coverage_pct"])
        self.assertEqual(1, model["engineering"]["automation_repos"])
        self.assertEqual(3, model["engineering"]["automation_eligible_repos"])

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            original_cwd = Path.cwd()
            os.chdir(output_root)
            try:
                ensure_output_dirs()
                generate_assets(
                    collected,
                    model,
                    logger=lambda *_args, **_kwargs: None,
                )
            finally:
                os.chdir(original_cwd)
            rendered = {
                "builder": (output_root / "assets/builder_scorecard.svg").read_text(
                    encoding="utf-8"
                ),
                "cadence": (output_root / "assets/engineering_cadence.svg").read_text(
                    encoding="utf-8"
                ),
            }

        def find_claim(svg_text):
            root = ET.fromstring(svg_text)
            for node in root.iter():
                if node.attrib.get("data-metric-key") == "ci_coverage_pct":
                    return {
                        "display_value": node.attrib.get("data-metric-display-value"),
                        "scope": node.attrib.get("data-metric-scope"),
                        "status": node.attrib.get("data-metric-status"),
                        "visible_text": " ".join(node.itertext()),
                    }
            return None

        for surface, svg_text in rendered.items():
            with self.subTest(surface=surface, assertion="visible all-owned value"):
                self.assertIn("33%", svg_text)
            with self.subTest(surface=surface, assertion="machine-readable claim"):
                self.assertEqual(
                    {
                        "display_value": "33%",
                        "scope": expected_scope,
                        "status": expected_status,
                        "visible_text": unittest.mock.ANY,
                    },
                    find_claim(svg_text),
                )
            claim = find_claim(svg_text)
            if claim is not None:
                with self.subTest(surface=surface, assertion="visible value matches claim"):
                    self.assertIn(claim["display_value"], claim["visible_text"])


class DesignTokenContract(unittest.TestCase):
    def test_no_raw_hex_in_rendering_code(self):
        offenders = []
        for path in sorted(RENDERING.glob("*.py")):
            if path.name in _TOKEN_SOURCES:
                continue
            for lineno, line in _code_lines(path):
                for hexval in _HEX.findall(line):
                    offenders.append(f"{path.relative_to(ROOT)}:{lineno}  {hexval}")
        self.assertEqual(
            [],
            offenders,
            "Raw hex colors must resolve from the design-token source, not be "
            "hard-coded in rendering code:\n  " + "\n  ".join(offenders),
        )


class FontLegibilityContract(unittest.TestCase):
    # The sparse-label heatmap, contribution view, and progress-ring sublabel all
    # share this 11px legibility floor (DESIGN_SPEC 3.8/3.15/3.17).
    def test_no_font_size_below_floor(self):
        offenders = []
        for path in sorted(RENDERING.glob("*.py")):
            text = path.read_text(encoding="utf-8")
            for match in _FONT.finditer(text):
                if float(match.group(1)) < MIN_FONT:
                    offenders.append(f"{path.name}: font-size={match.group(1)}")
        self.assertEqual(
            [],
            offenders,
            f"Rendered text must stay >= {MIN_FONT}px so README cards read when "
            "downscaled:\n  " + "\n  ".join(offenders),
        )


class HierarchyContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.3: one dominant KPI per metric surface, strictly larger
    than every secondary value (Power BI 'size = emphasis')."""

    def _render_hero(self, out: str) -> str:
        from scripts.rendering.generate_metrics_general import generate

        snapshot = {
            "last_year_contributions": 8104,
            "public_scope_commits": 4264,
            "total_repos": 67,
            "private_owned_repos": 146,
            "total_stars": 78,
            "languages_count": 24,
            "prs_merged": 35,
            "releases": 0,
            "ci_repos": 16,
            "streak_days": 2,
        }
        generate(
            username="jguida941",
            snapshot=snapshot,
            generated_at="2026-06-28T00:00:00Z",
            output_path=out,
        )
        return Path(out).read_text(encoding="utf-8")

    def test_hero_has_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render_hero(str(Path(d) / "hero.svg"))
        sizes = [float(m) for m in re.findall(r'font-size="([0-9.]+)"', svg)]
        self.assertTrue(sizes, "hero emitted no text")
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "hero must promote one KPI to display size")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI value")
        second = max(s for s in sizes if s < top)
        self.assertLess(second, top, "KPI must be strictly larger than every secondary value")


_TEXT_NODE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)


def _text_contents(svg: str) -> str:
    return " ".join(_TEXT_NODE.findall(svg))


def _provider_dashboard_data(*, exact: bool) -> dict:
    from scripts.pipeline.compute_metrics import compute_profile_model
    from tests.contracts.test_data_semantics import GeneratedCardTruthTests

    collected = GeneratedCardTruthTests._aggregate_observation_fixture(exact=exact)
    model = compute_profile_model(
        collected,
        logger=lambda *_args, **_kwargs: None,
        allow_network_calls=False,
    )
    data = json.loads(json.dumps(model["dashboard_data"]))
    # These unrelated collections stay empty so the test exercises the Raw Snapshot
    # hydration route without depending on repository, calendar, or rhythm content.
    data["top_languages"] = []
    data["featured_repo_facts"] = []
    data["focus"] = {}
    data["contribution_calendar"] = None
    data["activity_rhythm"] = None
    return data


def _hydrate_web_dashboard(data: dict) -> dict:
    """Execute the emitted dashboard hydration program against a small DOM."""
    from scripts.pipeline.web_render import render_dashboard

    html = render_dashboard()
    programs = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, re.S)
    program = next((source for source in programs if "fetch(DATA_URL" in source), None)
    if program is None:
        raise AssertionError("dashboard output has no hydration program")
    runtime_match = re.search(
        r"\bconst RUNTIME = (\{.*?\});\s*const PROTOTYPES",
        program,
        re.S,
    )
    if runtime_match is None:
        raise AssertionError("dashboard output has no runtime contract")
    runtime = json.loads(runtime_match.group(1))

    def dataset_name(attribute: str) -> str:
        words = attribute.removeprefix("data-").split("-")
        return words[0] + "".join(word.title() for word in words[1:])

    static_nodes = []
    routed_attributes = {
        "data-bind",
        "data-dashboard-hydration",
        "data-empty-state",
        "data-focus-items",
        "data-snapshot-key",
    }
    for tag in re.findall(r"<(?!/|!)[^>]+>", html):
        attributes = dict(
            re.findall(r'([A-Za-z_:][A-Za-z0-9_:.-]*)="([^"]*)"', tag)
        )
        if "id" not in attributes and not routed_attributes.intersection(attributes):
            continue
        static_nodes.append(
            {
                "id": attributes.get("id"),
                "dataset": {
                    dataset_name(name): value
                    for name, value in attributes.items()
                    if name.startswith("data-")
                },
            }
        )

    node = shutil.which("node")
    if node is None:
        raise AssertionError("the web product test requires the CI Node runtime")

    harness = (
        "const TEST_DATA = "
        + json.dumps(data, sort_keys=True, separators=(",", ":"))
        + ";\nconst TEST_RUNTIME = "
        + json.dumps(runtime, sort_keys=True, separators=(",", ":"))
        + ";\nconst TEST_STATIC_NODES = "
        + json.dumps(static_nodes, sort_keys=True, separators=(",", ":"))
        + ";\n"
        + r"""
class FakeNode {
  constructor(id, dataset) {
    this.id = id || null;
    this.dataset = Object.assign({}, dataset || {});
    this.textContent = "";
    this.hidden = false;
    this.title = "";
    this.href = "";
    this.children = [];
    this.style = {values: {}, setProperty(name, value) { this.values[name] = String(value); }};
  }
  append(node) { this.children.push(node); }
  replaceChildren(...nodes) { this.children = nodes; }
  cloneNode(deep) {
    const copy = new FakeNode(this.id, this.dataset);
    copy.textContent = this.textContent;
    copy.hidden = this.hidden;
    copy.title = this.title;
    copy.href = this.href;
    if (deep) copy.children = this.children.map((child) => child.cloneNode(true));
    return copy;
  }
  querySelectorAll(selector) {
    if (selector !== "[data-field]") return [];
    const found = [];
    const visit = (node) => {
      node.children.forEach((child) => {
        if (child.dataset.field) found.push(child);
        visit(child);
      });
    };
    visit(this);
    return found;
  }
}

const staticNodes = TEST_STATIC_NODES.map(
  (entry) => new FakeNode(entry.id, entry.dataset));
const byId = new Map(staticNodes.filter((entry) => entry.id)
  .map((entry) => [entry.id, entry]));

function prototypeRoot(policy) {
  const fields = Array.isArray(policy.unit.fields) ? policy.unit.fields : [];
  const rootField = fields.includes("root") ? "root" : (fields[0] || null);
  const dataset = {domOwner: policy.unit.owner, prototypeOrigin: policy.id};
  if (rootField) dataset.field = rootField;
  const root = new FakeNode(null, dataset);
  fields.filter((field) => field !== rootField).forEach((field) => {
    root.append(new FakeNode(null, {domOwner: policy.unit.owner, field}));
  });
  return root;
}

const templates = new Map(TEST_RUNTIME.prototypes.map((policy) => [
  policy.id,
  {content: {firstElementChild: prototypeRoot(policy)}},
]));
for (const policy of TEST_RUNTIME.prototypes) {
  if (policy.target === "focus") continue;
  const target = byId.get(policy.target);
  if (target && !target.dataset.domOwner) target.dataset.domOwner = policy.target_owner;
}

const dataName = (name) => name.split("-").map(
  (part, index) => index ? part.charAt(0).toUpperCase() + part.slice(1) : part).join("");
function matchesDataSelector(node, selector) {
  const match = /^\[data-([a-z0-9-]+)(?:="([^"]*)")?\]$/.exec(selector);
  if (!match) return false;
  const value = node.dataset[dataName(match[1])];
  return match[2] === undefined ? value !== undefined : value === match[2];
}

globalThis.location = {href: "https://example.test/index.html"};
globalThis.document = {
  getElementById(id) { return byId.get(id) || null; },
  querySelectorAll(selector) {
    return staticNodes.filter((entry) => matchesDataSelector(entry, selector));
  },
  querySelector(selector) {
    const template = /^template\[data-prototype="([^"]+)"\]$/.exec(selector);
    if (template) return templates.get(template[1]) || null;
    return this.querySelectorAll(selector)[0] || null;
  },
};
globalThis.fetch = () => Promise.resolve({json: () => Promise.resolve(TEST_DATA)});
"""
        + program
        + r"""

function visibleText(node) {
  return [node.textContent, ...node.children.map(visibleText)]
    .filter((value) => String(value).trim())
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}
setTimeout(() => {
  const labels = [];
  for (const target of byId.values()) {
    for (const child of target.children) {
      const value = visibleText(child);
      if (value) labels.push(value);
    }
  }
  const snapshot = Object.fromEntries(staticNodes
    .filter((entry) => entry.dataset.snapshotKey)
    .map((entry) => [entry.dataset.snapshotKey, entry.textContent]));
  const bindings = Object.fromEntries(staticNodes
    .filter((entry) => entry.dataset.bind)
    .map((entry) => [entry.dataset.bind, entry.textContent]));
  const hydration = staticNodes.find(
    (entry) => entry.dataset.dashboardHydration !== undefined);
  process.stdout.write(JSON.stringify({
    hydration: hydration ? hydration.dataset.dashboardHydration : null,
    labels,
    snapshot,
    bindings,
  }));
}, 0);
"""
    )
    completed = subprocess.run(
        [node, "-"],
        input=harness,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "dashboard hydration program did not execute:\n" + completed.stderr
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            "dashboard hydration program returned no readable result:\n"
            + completed.stdout
            + completed.stderr
        ) from exc


def _provider_evidence(labels: list[str], *terms: str) -> str:
    return " ".join(
        label for label in labels if any(term in label.casefold() for term in terms)
    ).casefold()


class WebRawSnapshotTruthContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fallback_data = _provider_dashboard_data(exact=False)
        cls.exact_data = _provider_dashboard_data(exact=True)
        cls.fallback_route = _hydrate_web_dashboard(cls.fallback_data)
        cls.exact_route = _hydrate_web_dashboard(cls.exact_data)

        other_pr_population = copy.deepcopy(cls.fallback_data)
        pr_carrier = other_pr_population["data_quality"]["non_exact_metrics"][
            "prs_merged"
        ]
        pr_carrier["source_metric_id"] = "merged_prs_primary_visible_population"
        pr_carrier["population_id"] = (
            "owned-repositories-visible-to-primary-pr-search"
        )
        cls.other_pr_population_route = _hydrate_web_dashboard(other_pr_population)

        current_contribution_source = copy.deepcopy(cls.fallback_data)
        contribution_carrier = current_contribution_source["data_quality"][
            "non_exact_metrics"
        ]["last_year_contributions"]
        contribution_carrier.update(
            {
                "source_metric_id": "github_contribution_calendar_total_and_days",
                "source_id": "github_graphql_contribution_calendar",
                "source_mode": "fallback",
                "completion_reason": "provider_error",
                "observed_at": current_contribution_source["generated_at"],
            }
        )
        cls.current_contribution_source_route = _hydrate_web_dashboard(
            current_contribution_source
        )

    def test_web_raw_snapshot_qualifies_public_pr_fallback(self):
        route = self.fallback_route
        self.assertEqual("complete", route["hydration"])
        self.assertEqual("n/a", route["snapshot"]["prs_merged"])
        self.assertEqual(
            23,
            self.fallback_data["data_quality"]["non_exact_metrics"]
            ["prs_merged"]["value"],
        )
        evidence = _provider_evidence(
            route["labels"], "prs", "pull request", "pull-request"
        )
        other_population_evidence = _provider_evidence(
            self.other_pr_population_route["labels"],
            "prs",
            "pull request",
            "pull-request",
        )
        self.assertNotIn("public", other_population_evidence)
        self.assertIn("fallback", evidence)
        self.assertIn("public", evidence)
        self.assertIn("fallback", other_population_evidence)

    def test_web_raw_snapshot_qualifies_previous_contributions(self):
        route = self.fallback_route
        self.assertEqual("complete", route["hydration"])
        self.assertEqual(
            777,
            self.fallback_data["data_quality"]["non_exact_metrics"]
            ["last_year_contributions"]["value"],
        )
        evidence = _provider_evidence(route["labels"], "contribution")
        current_source_evidence = _provider_evidence(
            self.current_contribution_source_route["labels"], "contribution"
        )
        self.assertNotIn("previous", current_source_evidence)
        self.assertNotIn("noncurrent", current_source_evidence)
        self.assertIn("fallback", evidence)
        self.assertTrue(
            "previous" in evidence or "noncurrent" in evidence,
            "previous contribution evidence must remain visibly noncurrent",
        )
        self.assertIn("fallback", current_source_evidence)

    def test_web_raw_snapshot_keeps_current_pr_zero_exact(self):
        route = self.exact_route
        self.assertEqual("complete", route["hydration"])
        self.assertEqual("0", route["snapshot"]["prs_merged"])
        evidence = _provider_evidence(
            route["labels"], "prs", "pull request", "pull-request"
        )
        self.assertIn("ok", evidence)
        self.assertNotIn("fallback", evidence)
        self.assertNotIn("public scope", evidence)

    def test_web_raw_snapshot_keeps_current_contribution_zero_exact(self):
        route = self.exact_route
        self.assertEqual("complete", route["hydration"])
        self.assertEqual("0", route["bindings"]["snapshot.last_year_contributions"])
        evidence = _provider_evidence(route["labels"], "contribution")
        self.assertIn("ok", evidence)
        self.assertNotIn("fallback", evidence)
        self.assertNotIn("previous", evidence)
        self.assertNotIn("noncurrent", evidence)


class ByTheNumbersContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.3/3.15/Part 1.8: the "By The Numbers" card promotes one
    dominant KPI (12-month contributions) at display size, demotes the rest to
    secondary metric tiles on the type scale, drops the decorative gradient
    ribbon, scales numbers to <=4 numerals, and renders an honest empty state."""

    SCALE = {46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0}

    def _render(self, out: str, **overrides) -> str:
        from scripts.rendering.generate_badges import generate

        params = dict(
            public_nonfork_repos=42,
            public_forks=8,
            private_owned_repos=146,
            ci_count=16,
            last_year_contributions=8104,
        )
        params.update(overrides)
        generate(output_path=out, **params)
        return Path(out).read_text(encoding="utf-8")

    def _sizes(self, svg: str):
        return [float(m) for m in _FONT.findall(svg)]

    def test_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "badges.svg"))
        sizes = self._sizes(svg)
        self.assertTrue(sizes, "card emitted no text")
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "needs one display-size KPI (contributions)")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI value")
        second = max(s for s in sizes if s < top)
        self.assertLessEqual(second, 26, "secondary values must be metric-scale, below the KPI")

    def test_sizes_on_scale_and_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "badges.svg"))
        for s in self._sizes(svg):
            self.assertIn(s, self.SCALE, f"off-scale font-size {s}")
            self.assertGreaterEqual(s, 11.0, f"sub-floor font-size {s}")

    def test_no_gradient_ribbon(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "badges.svg"))
        self.assertNotIn("url(#bn-accent)", svg, "decorative gradient ribbon must be gone")

    def test_numbers_scaled_to_four_numerals(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(
                str(Path(d) / "badges.svg"),
                last_year_contributions=123456,
                ci_count=98765,
            )
        self.assertIsNone(
            re.search(r"\d{5,}", _text_contents(svg)),
            "values must be k/M scaled to <=4 numerals",
        )

    def test_empty_state_when_no_data(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(
                str(Path(d) / "badges.svg"),
                public_nonfork_repos=None,
                public_forks=None,
                private_owned_repos=None,
                ci_count=None,
                last_year_contributions=None,
            )
        texts = _TEXT_NODE.findall(svg)
        self.assertLessEqual(
            len(texts), 3, "empty card should be header + one explanatory line, not metric tiles"
        )
        self.assertIsNone(
            re.search(r"\d", _text_contents(svg)), "empty state must not fabricate numbers"
        )


class StreakSummaryContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.3/Part 1.2/Part 4: Streak Summary promotes Current Streak
    to one dominant display KPI, left-aligned (not a centered triptych), demotes
    Total/Longest to secondary tiles, and drops the orange gradient ribbon + the
    decorative orange hero number for neutral ink (emphasis via size, not hue)."""

    SCALE = {46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0}

    def _calendar(self, days_back: int = 14, count: int = 3):
        from datetime import datetime, timezone, timedelta

        today = datetime.now(timezone.utc).date()
        days = [
            {"date": str(today - timedelta(days=i)), "contributionCount": count}
            for i in range(days_back)
        ]
        return {"weeks": [{"contributionDays": days}]}

    def _render(self, out: str, *, calendar=None, current=12, total=1843) -> str:
        from scripts.rendering.generate_streak_summary import generate

        generate(
            calendar=self._calendar() if calendar is None else calendar,
            current_streak_days=current,
            total_contributions=total,
            output_path=out,
        )
        return Path(out).read_text(encoding="utf-8")

    def _sizes(self, svg: str):
        return [float(m) for m in _FONT.findall(svg)]

    def test_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "streak.svg"))
        sizes = self._sizes(svg)
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "current streak must be the display KPI")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI value")
        self.assertLessEqual(max(s for s in sizes if s < top), 26, "secondaries below the KPI")

    def test_sizes_on_scale_and_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "streak.svg"))
        for s in self._sizes(svg):
            self.assertIn(s, self.SCALE, f"off-scale font-size {s}")
            self.assertGreaterEqual(s, 11.0, f"sub-floor font-size {s}")

    def test_kpi_left_aligned(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "streak.svg"))
        # the display-size KPI node must not be centered (top-left reading path)
        kpi = re.search(r'<text[^>]*font-size="46"[^>]*>', svg)
        self.assertIsNotNone(kpi, "no display KPI node")
        self.assertNotIn('text-anchor="middle"', kpi.group(0), "KPI must be left-aligned")

    def test_no_orange_accent(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "streak.svg"))
        self.assertNotIn("#ff9e64", svg, "orange gradient ribbon / hero hue must be gone")

    def test_empty_state_when_no_calendar(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "streak.svg"), calendar={"weeks": []}, current=0, total=None)
        texts = _TEXT_NODE.findall(svg)
        self.assertLessEqual(len(texts), 3, "empty card = header + one explanatory line")
        self.assertIsNone(re.search(r"\d", _text_contents(svg)), "empty state must not fabricate numbers")


class SnapshotPanelContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.3/3.6/Part 1.7: the Raw Data Snapshot promotes one KPI,
    curates to <=4 secondary tiles (not an 11-row dump), drops the gradient
    ribbon, and renders pipeline status by distinct icon SHAPE + label."""

    SCALE = {46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0}
    CHECK = "M20 6 9 17l-5-5"      # success icon path (Lucide 'check')
    CROSS = "M18 6 6 18"            # danger icon path (Lucide 'x' / 'cross')

    def _rows(self):
        return [
            {"key": "last_year_contributions", "label": "12-Month Contributions", "display_value": "8,104"},
            {"key": "public_scope_commits", "label": "Public Commits", "display_value": "4,264"},
            {"key": "total_repos", "label": "Repositories", "display_value": "67"},
            {"key": "private_owned_repos", "label": "Private Repos", "display_value": "146"},
            {"key": "total_stars", "label": "Stargazers", "display_value": "78"},
            {"key": "languages_count", "label": "Languages", "display_value": "24"},
        ]

    def _render(self, out: str, *, rows=None, quality=None) -> str:
        from scripts.rendering.generate_snapshot_panel import generate

        generate(
            self._rows() if rows is None else rows,
            quality
            if quality is not None
            else {"ci_status": "ok", "commits_status": "ok", "releases_status": "error", "events_status": "partial"},
            output_path=out,
        )
        return Path(out).read_text(encoding="utf-8")

    def _sizes(self, svg):
        return [float(m) for m in _FONT.findall(svg)]

    def test_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "snap.svg"))
        sizes = self._sizes(svg)
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "needs one display KPI")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI")
        self.assertLessEqual(max(s for s in sizes if s < top), 26, "secondaries below KPI")

    def test_sizes_on_scale_and_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "snap.svg"))
        for s in self._sizes(svg):
            self.assertIn(s, self.SCALE, f"off-scale font-size {s}")
            self.assertGreaterEqual(s, 11.0, f"sub-floor font-size {s}")

    def test_no_gradient_ribbon(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "snap.svg"))
        self.assertNotIn("gk-ribbon", svg, "gradient ribbon must be replaced by a hairline")

    def test_secondary_tiles_curated(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "snap.svg"))
        # secondary metric tile values render at the metric token (22)
        self.assertLessEqual(svg.count('font-size="22"'), 4, "cap at <=4 curated secondary tiles")

    def test_status_by_distinct_icon_shape(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "snap.svg"))
        self.assertIn(self.CHECK, svg, "success status must use the check shape")
        self.assertIn(self.CROSS, svg, "danger status must use a distinct (cross) shape")

    def test_empty_state(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "snap.svg"), rows=[], quality={})
        texts = _TEXT_NODE.findall(svg)
        self.assertLessEqual(len(texts), 3, "empty snapshot = header + one explanatory line")
        self.assertIsNone(re.search(r"\d", _text_contents(svg)), "empty state must not fabricate numbers")


class BuilderScorecardContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.3/3.9/Part 4: the Builder Scorecard promotes contributions
    to one display KPI, demotes the rest to uniform secondary tiles, renders CI
    coverage as a token-labeled donut gauge (the one sanctioned circular chart),
    and drops the rainbow accents + gradient ribbon."""

    SCALE = {46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0}

    def _scorecard(self):
        return {
            "last_year_contributions": 8104,
            "active_days_last_year": 287,
            "active_repos_7d": 5,
            "ci_coverage_pct": 82,
            "automation_workflows": 16,
            "releases_30d": 3,
            "primary_lang_share_pct": 61.4,
            "median_days_since_push": 4,
        }

    def _render(self, out: str, *, scorecard=None) -> str:
        from scripts.rendering.generate_builder_scorecard import generate

        generate(self._scorecard() if scorecard is None else scorecard, output_path=out)
        return Path(out).read_text(encoding="utf-8")

    def _sizes(self, svg):
        return [float(m) for m in _FONT.findall(svg)]

    def test_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "score.svg"))
        sizes = self._sizes(svg)
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "needs one display KPI (contributions)")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI")
        self.assertLessEqual(max(s for s in sizes if s < top), 26, "secondaries below KPI")

    def test_sizes_on_scale_and_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "score.svg"))
        for s in self._sizes(svg):
            self.assertIn(s, self.SCALE, f"off-scale font-size {s}")
            self.assertGreaterEqual(s, 11.0, f"sub-floor font-size {s}")

    def test_no_gradient_ribbon(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "score.svg"))
        self.assertNotIn("gk-ribbon", svg, "gradient ribbon must be replaced by a hairline")

    def test_ci_coverage_is_labeled_gauge(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "score.svg"))
        # gauge center label rides at a scale token (20) and shows a percent in [0,100]
        self.assertRegex(
            svg, r'<text[^>]*font-size="20"[^>]*>[^<]*%</text>',
            "CI coverage must render as a >=12px labeled gauge",
        )

    def test_empty_state(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "score.svg"), scorecard={})
        texts = _TEXT_NODE.findall(svg)
        self.assertLessEqual(len(texts), 3, "empty scorecard = header + one explanatory line")
        self.assertIsNone(re.search(r"\d", _text_contents(svg)), "empty state must not fabricate numbers")


class LanguageBreakdownContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.10/Part 4: Language Breakdown promotes the leading-language
    share as the one display KPI, renders a flat part-to-whole LanguageBar capped at
    <=6 (+Other) with a name+value legend, and drops the glossy sheen gradient."""

    SCALE = {46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0}

    def _bytes(self):
        return {
            "Python": 600000, "TypeScript": 250000, "Rust": 120000, "Go": 60000,
            "C": 30000, "Shell": 15000, "HTML": 9000, "CSS": 5000,
        }

    def _render(self, out: str, *, language_bytes=None) -> str:
        from scripts.rendering.generate_language_chart import generate

        generate(self._bytes() if language_bytes is None else language_bytes, output_path=out)
        return Path(out).read_text(encoding="utf-8")

    def _sizes(self, svg):
        return [float(m) for m in _FONT.findall(svg)]

    def test_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "lang.svg"))
        sizes = self._sizes(svg)
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "needs one display KPI (leading-language share)")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI")
        self.assertLessEqual(max(s for s in sizes if s < top), 26, "secondaries below KPI")

    def test_sizes_on_scale_and_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "lang.svg"))
        for s in self._sizes(svg):
            self.assertIn(s, self.SCALE, f"off-scale font-size {s}")
            self.assertGreaterEqual(s, 11.0, f"sub-floor font-size {s}")

    def test_no_sheen_gradient(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "lang.svg"))
        self.assertNotIn("Sheen", svg, "the glossy bar sheen gradient must be removed (flat fill)")

    def test_segments_capped_with_other(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "lang.svg"))
        # legend renders one dot per segment; cap at <=6 languages + Other
        self.assertLessEqual(svg.count("<circle"), 7, "cap visible segments at <=6 (+Other)")
        self.assertIn(">Other</text>", svg, "languages beyond the cap fold into 'Other'")

    def test_segment_has_name_and_value(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "lang.svg"))
        self.assertIn(">Python</text>", svg, "each segment shows its language name")
        self.assertRegex(svg, r">[0-9]+(\.[0-9]+)?%</text>", "each segment shows its percent value")

    def test_empty_state(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "lang.svg"), language_bytes={})
        self.assertIsNone(
            re.search(r"\d", _text_contents(svg)), "empty state must not fabricate numbers"
        )


class ProfileMetricScopeContract(unittest.TestCase):
    ALL_OWNED = "owned-public-private-nonfork-profile-excluded-exact"
    PUSH_METRICS = ("active_repos_7d", "days_since_last_push")
    AUTOMATION_METRICS = ("automation_repos", "automation_workflows")
    AUTOMATION_SURFACE_METRICS = AUTOMATION_METRICS + (
        "ci_coverage_pct",
        "ci_repos",
    )
    LANGUAGE_METRICS = (
        "top_languages",
        "primary_lang_share_pct",
        "languages_over_5pct",
    )
    LANGUAGE_SURFACE_METRICS = LANGUAGE_METRICS + ("languages_count",)

    def _model(
        self,
        *,
        public_repo_name="pub1",
        public_updates=None,
        omit_private_language_marker=False,
        **private_updates,
    ):
        from scripts.pipeline.compute_metrics import compute_profile_model
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests

        collected = AccuracyTests()._collected()
        public_repos = copy.deepcopy(collected.repos)
        for repository in public_repos:
            repository["language_bytes_complete"] = True
            if repository.get("name") == public_repo_name and public_updates:
                repository.update(public_updates)
        private_repo = copy.deepcopy(collected.private_repos[0])
        private_repo["language_bytes_complete"] = True
        private_repo.update(private_updates)
        if omit_private_language_marker:
            private_repo.pop("language_bytes_complete", None)
        collected = replace(
            collected,
            repos=public_repos,
            all_repos=copy.deepcopy(public_repos),
            private_repos=[private_repo],
        )
        return compute_profile_model(
            collected,
            logger=lambda *_args, **_kwargs: None,
            allow_network_calls=False,
        )

    def _truth(self, model):
        statuses = model["data_quality"].get("metric_statuses")
        self.assertIsInstance(
            statuses,
            dict,
            "each private-aware metric needs an explicit completeness status",
        )
        return statuses, model["data_scope"]["metric_scopes"]

    def _assert_exact_all_owned(self, statuses, scopes, metrics):
        for metric in metrics:
            with self.subTest(metric=metric):
                self.assertEqual("exact", statuses.get(metric))
                self.assertEqual(self.ALL_OWNED, scopes.get(metric))

    def _assert_not_exact_all_owned(self, statuses, scopes, metrics):
        for metric in metrics:
            with self.subTest(metric=metric):
                self.assertNotEqual("exact", statuses.get(metric))
                self.assertNotEqual(self.ALL_OWNED, scopes.get(metric))

    def test_complete_private_facts_are_exact_for_each_metric_family(self):
        model = self._model()
        statuses, scopes = self._truth(model)
        metrics = self.PUSH_METRICS + self.AUTOMATION_METRICS + self.LANGUAGE_METRICS
        self._assert_exact_all_owned(statuses, scopes, metrics)
        language_bytes = {row["name"]: row["bytes"] for row in model["top_languages"]}
        self.assertEqual(1000, language_bytes["Rust"])

    def test_missing_private_push_facts_only_degrade_push_metrics(self):
        model = self._model(pushed_at="")
        statuses, scopes = self._truth(model)
        self._assert_not_exact_all_owned(statuses, scopes, self.PUSH_METRICS)
        self._assert_exact_all_owned(
            statuses,
            scopes,
            self.AUTOMATION_METRICS + self.LANGUAGE_METRICS,
        )

    def test_unknown_private_workflow_facts_only_degrade_automation_metrics(self):
        model = self._model(has_ci_workflows=None, workflow_file_count=None)
        statuses, scopes = self._truth(model)
        self._assert_not_exact_all_owned(statuses, scopes, self.AUTOMATION_METRICS)
        self._assert_exact_all_owned(
            statuses,
            scopes,
            self.PUSH_METRICS + self.LANGUAGE_METRICS,
        )

    def test_incomplete_private_language_facts_only_degrade_language_metrics(self):
        model = self._model(language_bytes_complete=False)
        statuses, scopes = self._truth(model)
        self._assert_not_exact_all_owned(statuses, scopes, self.LANGUAGE_METRICS)
        self._assert_exact_all_owned(
            statuses,
            scopes,
            self.PUSH_METRICS + self.AUTOMATION_METRICS,
        )

    def test_missing_public_push_facts_only_degrade_push_metrics(self):
        model = self._model(public_updates={"pushed_at": ""})
        statuses, scopes = self._truth(model)
        self._assert_not_exact_all_owned(statuses, scopes, self.PUSH_METRICS)
        self._assert_exact_all_owned(
            statuses,
            scopes,
            self.AUTOMATION_METRICS + self.LANGUAGE_METRICS,
        )

    def test_unknown_public_workflow_facts_only_degrade_automation_metrics(self):
        model = self._model(
            public_updates={
                "has_ci_workflows": None,
                "workflow_file_count": None,
            }
        )
        statuses, scopes = self._truth(model)
        self._assert_not_exact_all_owned(
            statuses,
            scopes,
            self.AUTOMATION_SURFACE_METRICS,
        )
        self._assert_exact_all_owned(
            statuses,
            scopes,
            self.PUSH_METRICS + self.LANGUAGE_METRICS,
        )

    def test_incomplete_public_language_facts_only_degrade_language_metrics(self):
        model = self._model(public_updates={"language_bytes_complete": False})
        statuses, scopes = self._truth(model)
        self._assert_not_exact_all_owned(
            statuses,
            scopes,
            self.LANGUAGE_SURFACE_METRICS,
        )
        self._assert_exact_all_owned(
            statuses,
            scopes,
            self.PUSH_METRICS + self.AUTOMATION_METRICS,
        )

    def test_private_language_completeness_marker_is_required_for_exactness(self):
        missing = self._model(omit_private_language_marker=True)
        complete = self._model(language_bytes_complete=True)
        missing_statuses, missing_scopes = self._truth(missing)
        complete_statuses, complete_scopes = self._truth(complete)

        self._assert_not_exact_all_owned(
            missing_statuses,
            missing_scopes,
            self.LANGUAGE_METRICS,
        )
        self._assert_exact_all_owned(
            complete_statuses,
            complete_scopes,
            self.LANGUAGE_METRICS,
        )

    def test_exposed_aggregate_metrics_have_explicit_status_and_scope(self):
        model = self._model()
        statuses, scopes = self._truth(model)
        self._assert_exact_all_owned(
            statuses,
            scopes,
            ("ci_coverage_pct", "ci_repos", "languages_count"),
        )

    def test_scorecard_and_engineering_automation_share_one_population(self):
        model = self._model(
            public_repo_name="jguida941",
            public_updates={
                "has_ci_workflows": False,
                "workflow_file_count": 0,
            },
        )
        engineering = model["engineering"]
        eligible = engineering["automation_eligible_repos"]
        expected_percentage = (
            engineering["automation_repos"] / eligible * 100 if eligible else 0.0
        )

        self.assertEqual(
            engineering["automation_repos"],
            model["snapshot"]["ci_repos"],
        )
        self.assertAlmostEqual(
            expected_percentage,
            model["scorecard"]["ci_coverage_pct"],
        )
        statuses, scopes = self._truth(model)
        self._assert_exact_all_owned(
            statuses,
            scopes,
            self.AUTOMATION_SURFACE_METRICS,
        )


class EngineeringCadenceContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.8/3.9/Part 4: Engineering Cadence promotes active days to
    one display KPI, renders the weekly cadence as a TrendPanel (stroke >=1.5) and
    CI coverage as a labeled DonutGauge, on the type scale, with no gradient ribbon."""

    SCALE = {46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0}

    def _data(self):
        return {
            "weekly_cadence": [2, 5, 3, 8, 4, 6, 9, 5, 7, 4, 6, 8],
            "active_days_last_year": 287,
            "automation_workflows": 16,
            "automation_repos": 12,
            "primary_lang_share_pct": 61.4,
            "languages_over_5pct": 4,
            "public_repos_total": 42,
            "public_nonfork_repos": 30,
            "private_repos_total": 146,
        }

    def _render(self, out: str, *, data=None) -> str:
        from scripts.rendering.generate_engineering_cadence import generate

        generate(self._data() if data is None else data, output_path=out)
        return Path(out).read_text(encoding="utf-8")

    def _sizes(self, svg):
        return [float(m) for m in _FONT.findall(svg)]

    def test_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "eng.svg"))
        sizes = self._sizes(svg)
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "needs one display KPI (active days)")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI")
        self.assertLessEqual(max(s for s in sizes if s < top), 26, "secondaries below KPI")

    def test_sizes_on_scale_and_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "eng.svg"))
        for s in self._sizes(svg):
            self.assertIn(s, self.SCALE, f"off-scale font-size {s}")
            self.assertGreaterEqual(s, 11.0, f"sub-floor font-size {s}")

    def test_no_gradient_ribbon(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "eng.svg"))
        self.assertNotIn("gk-ribbon", svg, "gradient ribbon must be replaced by a hairline")

    def test_trend_stroke_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "eng.svg"))
        strokes = re.findall(r'<polyline[^>]*stroke-width="([0-9.]+)"', svg)
        self.assertTrue(strokes, "weekly cadence must render a trend polyline")
        self.assertTrue(all(float(s) >= 1.5 for s in strokes), "trend stroke must be >=1.5px")

    def test_ci_coverage_is_labeled_gauge(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "eng.svg"))
        self.assertRegex(
            svg, r'<text[^>]*font-size="20"[^>]*>[^<]*%</text>',
            "CI coverage must render as a >=12px labeled gauge",
        )

    def test_ci_coverage_uses_the_same_repository_scope_for_both_terms(self):
        from scripts.rendering import generate_engineering_cadence as cadence

        def gauge_value(data):
            captured = []

            def capture(*_args, **kwargs):
                captured.append(kwargs["value"])
                return "<g/>"

            import tempfile

            with tempfile.TemporaryDirectory() as directory, patch.object(
                cadence, "_gauge_cell", side_effect=capture
            ):
                cadence.generate(data, output_path=str(Path(directory) / "eng.svg"))
            return captured[0]

        all_owned = {
            **self._data(),
            "automation_repos": 3,
            "public_nonfork_repos": 1,
            "private_nonfork_repos": 2,
            "private_repos_total": 2,
        }
        public_only = {
            **self._data(),
            "automation_repos": 1,
            "public_nonfork_repos": 1,
            "private_nonfork_repos": 0,
            "private_repos_total": 0,
        }

        observed = (gauge_value(all_owned), gauge_value(public_only))
        self.assertEqual((100.0, 100.0), observed)

    def test_empty_state(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "eng.svg"), data={})
        self.assertIsNone(
            re.search(r"\d", _text_contents(svg)), "empty state must not fabricate numbers"
        )


class CurrentlyWorkingContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.11/3.12/Part 4: Currently Working On promotes the active-
    repo count to one display KPI, lists repos as uniform rows (language by dot AND
    label), drops the gradient ribbon, and renders an honest empty state."""

    SCALE = {46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0}

    def _repos(self):
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)

        def iso(h):
            return (now - timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")

        return [
            {"name": "ci-cd-hub", "language": "Python", "pushed_at": iso(3),
             "last_commit_msg": "add deploy gate", "is_private": False,
             "html_url": "https://github.com/x/ci-cd-hub"},
            {"name": "voiceterm", "language": "Rust", "pushed_at": iso(20),
             "last_commit_msg": "fix audio buffer", "is_private": False,
             "html_url": "https://github.com/x/voiceterm"},
            {"name": "secret-svc", "language": "Go", "pushed_at": iso(50), "is_private": True},
        ]

    def _render(self, out: str, *, repos=None) -> str:
        from scripts.rendering.generate_currently_working import generate

        generate(self._repos() if repos is None else repos, output_path=out)
        return Path(out).read_text(encoding="utf-8")

    def _sizes(self, svg):
        return [float(m) for m in _FONT.findall(svg)]

    def test_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "cw.svg"))
        sizes = self._sizes(svg)
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "needs one display KPI (active repo count)")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI")
        self.assertLessEqual(max(s for s in sizes if s < top), 26, "secondaries below KPI")

    def test_sizes_on_scale_and_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "cw.svg"))
        for s in self._sizes(svg):
            self.assertIn(s, self.SCALE, f"off-scale font-size {s}")
            self.assertGreaterEqual(s, 11.0, f"sub-floor font-size {s}")

    def test_no_gradient_ribbon(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "cw.svg"))
        self.assertNotIn("gk-ribbon", svg, "gradient ribbon must be replaced by a hairline")

    def test_language_color_independence(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "cw.svg"))
        self.assertIn(">Python</text>", svg, "language must be shown by label, not hue alone")
        self.assertGreaterEqual(svg.count("<circle"), 1, "each row carries a language dot")

    def test_public_and_private_repository_urls_render_as_svg_anchors(self):
        import tempfile
        import xml.etree.ElementTree as ET

        repos = self._repos()
        repos[-1]["html_url"] = "https://github.com/x/secret-svc"
        focus = {
            "now": [
                {
                    "title": repo["name"],
                    "detail": f"{repo['language']} · pushed recently",
                    "url": repo["html_url"],
                    "is_private": repo["is_private"],
                }
                for repo in (repos[0], repos[-1])
            ],
            "next": [],
            "shipped": [],
        }

        from scripts.rendering.generate_focus_board import generate as generate_focus

        with tempfile.TemporaryDirectory() as directory:
            working_output = Path(directory) / "currently-working.svg"
            focus_output = Path(directory) / "focus.svg"
            self._render(str(working_output), repos=repos)
            generate_focus(focus, output_path=str(focus_output))

            for surface, output in (
                ("currently-working", working_output),
                ("focus", focus_output),
            ):
                with self.subTest(surface=surface):
                    root = ET.fromstring(output.read_text(encoding="utf-8"))
                    hrefs = {
                        node.attrib.get("href")
                        for node in root.iter()
                        if node.tag.endswith("a")
                    }
                    self.assertIn(
                        repos[0]["html_url"],
                        hrefs,
                        "the public repository is the control for link rendering",
                    )
                    self.assertIn(
                        repos[-1]["html_url"],
                        hrefs,
                        "repository visibility must not discard an authorized metadata URL",
                    )

    def test_empty_state(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "cw.svg"), repos=[])
        self.assertIsNone(
            re.search(r"\d", _text_contents(svg)), "empty state must not fabricate numbers"
        )


if __name__ == "__main__":
    unittest.main()
