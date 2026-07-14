"""W3 - the public dashboard is a governed pageshell/webkit composition.

The RED closes the migration itself: content parity, direct primitive lineage, closed DATA/CSS,
and prototype-derived hydration. Rendered pixel facts remain W4's explicit handoff.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import re
import unittest
from collections import Counter
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "contracts" / "dashboard_surface.json"
MODULE_PATH = ROOT / "scripts" / "rendering" / "webkit" / "dashboard.py"

EXPECTED_SECTIONS = (
    "hero", "scorecard", "calendar", "languages", "rhythm", "flagship", "focus", "snapshot",
)
EXPECTED_IDS = (
    "hero-name", "hero-tag", "updated", "ci-ring", "lang-name", "calendar-panel",
    "cal-total", "cal", "cal-months", "cal-scale", "lang-count", "langbar", "langlegend",
    "rhythm-panel", "rhythm-meta", "heat-days", "heat-grid", "heat-hours", "event-mix",
    "flagship", "focus", "snap-tiles", "pipeline",
)
EXPECTED_BINDINGS = (
    ("hero-contributions", "snapshot.last_year_contributions", None, None),
    ("hero-active-days", "scorecard.active_days_last_year", None, None),
    ("hero-repos", "snapshot.total_repos", None, None),
    ("hero-stars", "snapshot.total_stars", None, None),
    ("ci-coverage", "scorecard.ci_coverage_pct", "%", 0),
    ("score-active-days", "scorecard.active_days_last_year", None, None),
    ("score-active-repos", "scorecard.active_repos_7d", None, None),
    ("score-workflows", "scorecard.automation_workflows", None, None),
    ("score-releases", "scorecard.releases_30d", None, None),
    ("score-language-share", "scorecard.primary_lang_share_pct", "%", 0),
    ("score-last-push", "scorecard.days_since_last_push", "d", 0),
)
RETIRED_CLASSES = frozenset({
    "bento", "cal", "cal-foot", "cal-scale", "cal-swatches", "cal-wrap", "chip", "chips",
    "eyebrow", "hairline", "heat", "heat-days", "heat-grid", "heat-hours", "heat-wrap", "hero",
    "item", "kpi", "kpi-label", "kpi-value", "lane", "lanes", "lang-bars", "langbar",
    "langlegend", "ldot", "live", "lockico", "m", "meta", "mgroup", "mix", "ml", "mrow",
    "ms", "mt", "mv", "nm", "num", "panel", "pc", "ring", "ring-row", "row", "rows",
    "rrow", "section-head", "section-meta", "stat", "stats", "swatch", "switcher", "title",
    "topline", "v", "wrap",
})
BANNED_RUNTIME = (
    "innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "createElement(",
    "createElementNS(", "createTextNode(", "new Image(", "new Audio(", "new Option(",
    "className", "classList", "setAttribute(", "removeAttribute(", "toggleAttribute(",
    "appendChild(", "insertBefore(", ".prepend(", ".before(", ".after(", ".replaceWith(",
)
EXPECTED_CSS_SHA256 = "6bf0a2d1afa9cd9373ec5133d7270e927326b299c1c9d6f70814ab7ddb574acb"
EXPECTED_SCRIPT_SHA256 = "cf7cad9eea603b41d9f06828021ebeb5fb7c288c194b74344250b573cdd09fb3"
EXPECTED_LOCAL_LITERAL_MANIFEST_SHA256 = "de176991a500c32bbdb949dbcf902bb2c38e72627dc383ffe35f777b1911f7c8"
EXPECTED_COPY_KEYS = frozenset({
    "breadcrumb_home", "calendar_eyebrow", "calendar_label", "calendar_less", "calendar_more",
    "calendar_title", "ci_detail", "ci_label", "flagship_empty", "flagship_eyebrow", "flagship_title",
    "focus_empty", "focus_eyebrow", "focus_next", "focus_now", "focus_shipped", "focus_title",
    "footer_link", "footer_prefix", "hero_active_days", "hero_eyebrow", "hero_intro",
    "hero_kpi_label", "hero_public_repos", "hero_stars", "hero_title", "languages_eyebrow",
    "languages_title", "live_prefix", "load_error", "pipeline_ci", "pipeline_commits",
    "pipeline_events", "pipeline_releases", "pipeline_title", "rhythm_eyebrow", "rhythm_label",
    "rhythm_title", "score_active_days", "score_active_days_detail", "score_active_repos",
    "score_active_repos_detail", "score_language_detail", "score_last_push",
    "score_last_push_detail", "score_primary_language", "score_releases",
    "score_releases_detail", "score_workflows", "score_workflows_detail", "scorecard_eyebrow",
    "scorecard_title", "snapshot_ci", "snapshot_commits", "snapshot_eyebrow",
    "snapshot_private", "snapshot_prs", "snapshot_repos", "snapshot_stars", "snapshot_title",
    "status_ok",
})
EXPECTED_PROTOTYPE_PINS = {
    "calendar-cell": ("cal", 377, "calendar"),
    "calendar-scale": ("cal-scale", 5, "calendar-scale"),
    "event-mix": ("event-mix", 12, "event-mix"),
    "focus-item": ("focus", 9, "focus"),
    "heat-cell": ("heat-grid", 168, "heat"),
    "heat-day": ("heat-days", 7, "heat-days"),
    "heat-hour": ("heat-hours", 5, "heat-hours"),
    "language-legend": ("langlegend", 6, "languages"),
    "language-segment": ("langbar", 6, "languages"),
    "pipeline-status": ("pipeline", 4, "pipeline"),
    "repository": ("flagship", 5, "repositories"),
}


class _SurfaceParser(HTMLParser):
    _VOID = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
                       "meta", "param", "source", "track", "wbr"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.templates: dict[str, dict] = {}
        self.targets: dict[str, tuple[str, str | None, bool]] = {}
        self.errors: list[str] = []
        self.current: str | None = None
        self.depth = 0

    def handle_starttag(self, tag, attrs):  # noqa: ANN001 - parser callback
        data = dict(attrs)
        if tag == "template" and "data-prototype" in data:
            if self.current is not None:
                self.errors.append("nested prototype template")
            self.current = data["data-prototype"]
            if self.current in self.templates:
                self.errors.append("duplicate prototype template")
            self.templates[self.current] = {"nodes": [], "roots": 0, "owner": data.get("data-dom-owner")}
            self.depth = 0
            return
        if "id" in data:
            self.targets[data["id"]] = (tag, data.get("data-dom-owner"), self.current is not None)
        if self.current is None:
            return
        if tag == "template":
            self.errors.append("nested anonymous template")
        if self.depth == 0:
            self.templates[self.current]["roots"] += 1
        canonical_attrs = sorted((name, value or "") for name, value in attrs)
        self.templates[self.current]["nodes"].append((tag, canonical_attrs, self.depth))
        classes = (data.get("class") or "").split()
        if classes and data.get("data-dom-owner") != "webkit.dashboard":
            self.errors.append(f"{self.current}: class-bearing {tag} lacks dashboard owner")
        if any(name == "style" or name.lower().startswith("on") for name, _ in attrs):
            self.errors.append(f"{self.current}: active/style attribute")
        if "id" in data or tag in {"script", "iframe", "object", "embed"}:
            self.errors.append(f"{self.current}: forbidden prototype element")
        if tag not in self._VOID:
            self.depth += 1

    def handle_startendtag(self, tag, attrs):  # noqa: ANN001 - parser callback
        self.handle_starttag(tag, attrs)
        if self.current is not None and tag not in self._VOID:
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.current is not None and data.strip():
            self.errors.append(f"{self.current}: prototype contains undeclared literal text")

    def handle_endtag(self, tag):  # noqa: ANN001 - parser callback
        if tag == "template" and self.current is not None and self.depth == 0:
            self.current = None
            return
        if self.current is not None and tag not in self._VOID:
            self.depth -= 1


def _tree_digest(nodes: list) -> str:
    payload = json.dumps(nodes, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def _prototype_errors(contract: dict, html: str) -> list[str]:
    errors: list[str] = []
    parser = _SurfaceParser()
    parser.feed(html)
    errors.extend(parser.errors)
    rows = contract.get("prototypes", [])
    if rows != sorted(rows, key=lambda row: row.get("id", "")):
        errors.append("prototype rows not canonical")
    if set(parser.templates) != {row.get("id") for row in rows}:
        errors.append("template roster drift")
    for row in rows:
        expected_keys = {"id", "target", "target_owner", "target_tag", "insertion", "budget_group",
                         "max_clones", "bound", "unit", "writes"}
        if set(row) != expected_keys:
            errors.append(f"{row.get('id')}: prototype keys not closed")
            continue
        pin = EXPECTED_PROTOTYPE_PINS.get(row["id"])
        if pin != (row["target"], row["max_clones"], row["budget_group"]):
            errors.append(f"{row['id']}: independent prototype pin drift")
        if type(row["max_clones"]) is not int or row["max_clones"] <= 0:
            errors.append(f"{row['id']}: invalid clone cap")
        if row["insertion"] not in {"replace-children", "append-field"}:
            errors.append(f"{row['id']}: invalid insertion mode")
        target = parser.targets.get(row["target"])
        if target != (row["target_tag"], row["target_owner"], False):
            errors.append(f"{row['id']}: target mismatch/nested target")
        template = parser.templates.get(row["id"])
        if not template:
            continue
        if template["owner"] != "webkit.dashboard" or template["roots"] != 1:
            errors.append(f"{row['id']}: template owner/root mismatch")
        fields = sorted({dict(attrs).get("data-field") for _, attrs, _ in template["nodes"]
                         if dict(attrs).get("data-field")})
        if fields != row["unit"]["fields"]:
            errors.append(f"{row['id']}: field roster mismatch")
        if len(template["nodes"]) != row["unit"]["element_count"]:
            errors.append(f"{row['id']}: element count mismatch")
        if _tree_digest(template["nodes"]) != row["unit"]["tree_sha256"]:
            errors.append(f"{row['id']}: unit tree hash mismatch")
        writes = row["writes"]
        if writes != sorted(writes, key=lambda item: (item["field"], item["sink"], item["name"] or "")):
            errors.append(f"{row['id']}: writes not canonical")
        if any(write["field"] not in fields for write in writes):
            errors.append(f"{row['id']}: write references unknown field")
    return errors


def _runtime_source_errors(source: str, contract: dict) -> list[str]:
    errors: list[str] = []
    expected_hash = contract.get("grammar_hashes", {}).get("script_sha256")
    if hashlib.sha256(source.encode()).hexdigest() != expected_hash:
        errors.append("runtime program is outside the single admitted grammar hash")
    for banned in BANNED_RUNTIME + ("importNode", "adoptNode", "DOMParser", "createContextualFragment",
                                    "attachShadow", "customElements", "adoptedStyleSheets", "insertRule",
                                    "replaceSync", "cssText", "eval(", "new Function"):
        if banned in source:
            errors.append(f"banned runtime API {banned}")
    if source.count(".cloneNode(true)") != 1 or source.count("function appendClone(") != 1:
        errors.append("clone engine is not singular")
    if source.count(".cloneNode(") != 1:
        errors.append("alternate/shallow clone site")
    if source.count("target.append(node)") != 1:
        errors.append("prototype append site is not singular")
    if source.count(".append(") != 1:
        errors.append("undeclared append site")
    if source.count(".replaceChildren(") != 2:
        errors.append("undeclared replace-children site")
    if source.count(".style.setProperty(") != 3 or source.count(".style.") != 3:
        errors.append("custom property writers drifted")
    dataset_assignments = re.findall(
        r"(?:\w+|\([^\n]+\))\.dataset(?:\[[^\]]+\]|\.[A-Za-z_$][\w$]*)\s*=", source
    )
    if len(dataset_assignments) != 2 or source.count(".dataset[") != 2:
        errors.append("dataset writers drifted")
    for sink, count in ((".textContent =", 4), (".hidden =", 2), (".title =", 1),
                        (".href =", 1)):
        if source.count(sink) != count:
            errors.append(f"typed sink count drifted: {sink}")
    if re.search(r"\.(?:id|src|srcdoc|onclick|onload|onerror|value)\s*=", source):
        errors.append("undeclared direct attribute write")
    declared = {(row["id"], row["target"]) for row in contract["prototypes"]}
    used = set(re.findall(r'appendClone\(["\']([^"\']+)["\'],\s*["\']([^"\']+)["\']', source))
    if used != declared:
        errors.append("appendClone call roster drift")
    return errors


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _html() -> str:
    from scripts.pipeline.web_render import render_dashboard
    return render_dashboard()


def _classes(html: str) -> list[str]:
    return [token for raw in re.findall(r'\bclass="([^"]*)"', html) for token in raw.split()]


def _literal_manifest_hash(rows: list[dict]) -> str:
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


class DashboardMigrationRedPresence(unittest.TestCase):
    def test_w3_contract_and_emitter_exist(self):
        self.assertTrue(CONTRACT_PATH.is_file(),
                        "W3 RED: contracts/dashboard_surface.json has not landed")
        self.assertTrue(MODULE_PATH.is_file(),
                        "W3 RED: scripts/rendering/webkit/dashboard.py has not landed")


@unittest.skipUnless(CONTRACT_PATH.is_file() and MODULE_PATH.is_file(),
                     "W3 RED target DATA/emitter not implemented")
class DashboardSurfaceContract(unittest.TestCase):
    def test_closed_contract_identity_and_content_rosters(self):
        contract = _contract()
        self.assertEqual(
            set(contract),
            {"contract_id", "schema_version", "authority_status", "cannot_mark_done", "purpose",
             "document", "sections", "ids", "bindings", "copy", "limits", "status",
             "intensity", "geometry", "data_colors", "custom_properties", "prototypes",
             "hydration_writes", "runtime_policy", "css_policy", "grammar_hashes"},
        )
        self.assertEqual(contract["contract_id"], "GovernedDashboardSurface")
        self.assertEqual(contract["schema_version"], 1)
        self.assertEqual(contract["authority_status"], "candidate_only")
        self.assertIs(contract["cannot_mark_done"], True)
        self.assertEqual(tuple(row["id"] for row in contract["sections"]), EXPECTED_SECTIONS)
        self.assertEqual(tuple(contract["ids"]), EXPECTED_IDS)
        actual_bindings = tuple(
            (row["slot"], row["path"], row["suffix"], row["round"])
            for row in contract["bindings"]
        )
        self.assertEqual(actual_bindings, EXPECTED_BINDINGS)
        self.assertEqual(set(contract["copy"]), EXPECTED_COPY_KEYS)
        self.assertEqual(len(contract["copy"]), len(set(contract["copy"].values())))
        self.assertTrue(all(isinstance(value, str) and value.strip()
                            for value in contract["copy"].values()))

    def test_index_is_pageshell_with_one_real_hydratable_h1_and_intro(self):
        html = _html()
        self.assertEqual(html.count("<h1"), 1)
        self.assertRegex(html, r'<h1 class="ps-title" data-dom-owner="pageshell" id="hero-name">')
        self.assertRegex(html, r'<p class="ps-intro" data-dom-owner="pageshell" id="hero-tag">')
        self.assertIn('class="ps-main" data-dom-owner="pageshell"', html)
        self.assertNotIn('class="wrap"', html)

    def test_exact_sections_ids_bindings_and_retired_debt_absence(self):
        html = _html()
        self.assertEqual(tuple(re.findall(r'data-dashboard-section="([^"]+)"', html)),
                         EXPECTED_SECTIONS)
        self.assertEqual(tuple(re.findall(r'\bid="([^"]+)"', html)), EXPECTED_IDS)
        bindings = []
        for tag in re.findall(r'<[^>]+\bdata-bind="[^"]+"[^>]*>', html):
            def attr(name):
                match = re.search(rf'\b{name}="([^"]*)"', tag)
                return match.group(1) if match else None
            bindings.append((attr("data-slot"), attr("data-bind"), attr("data-suffix"),
                             int(attr("data-round")) if attr("data-round") is not None else None))
        self.assertEqual(tuple(bindings), EXPECTED_BINDINGS)
        self.assertEqual([], sorted(RETIRED_CLASSES & set(_classes(html))))

    def test_dashboard_calls_real_card_component_and_switcher_has_facts(self):
        from scripts.contracts.design_predicates import (card_hairline_divided, card_multi_row,
                                                         card_rows_inline, card_single_container,
                                                         switcher_profile_governed)
        from scripts.rendering.webkit.dashboard import render_dashboard_surface
        from scripts.rendering.webkit.design_render_adapter import card_facts, switcher_facts

        html, css = render_dashboard_surface("liquid-glass")
        groups = re.findall(r'(<div class="card-[^"]* card-group".*?</div>\s*</div>)', html, re.S)
        self.assertEqual(len(groups), 2, "scorecard + snapshot must be direct grouped-card instances")
        for group in groups:
            facts = card_facts(group, css)
            self.assertTrue(card_single_container(facts))
            self.assertTrue(card_multi_row(facts))
            self.assertTrue(card_hairline_divided(facts))
            self.assertTrue(card_rows_inline(facts))
        facts = switcher_facts(_html(), css)
        self.assertTrue(switcher_profile_governed(facts))
        from scripts.rendering.design import loader
        for profile in loader.load("_index")["active_design_profiles"]:
            button = loader.load(profile)["components"]["button"]
            self.assertEqual(
                facts["profiles"][profile],
                {
                    "height_px": button["height_px"],
                    "radius_px": button["radius_px"],
                    "anatomy": button["anatomy"],
                    "state_mechanic": button["state_mechanic"],
                    "focus_recipe": button["focus_recipe"],
                    "hover_nonempty": True,
                    "active_nonempty": True,
                    "focus_nonempty": True,
                    "state_css": button["switcher_css"],
                },
            )

    def test_metric_label_hydration_preserves_card_icon_and_detail(self):
        html = _html()
        self.assertNotRegex(html, r'<span class="card-label"[^>]*\bid="lang-name"')
        self.assertRegex(
            html,
            r'<span class="card-label"[^>]*><svg[^>]*class="card-icon".*?'
            r'<span[^>]*\bid="lang-name"[^>]*>primary language</span>'
            r'<span class="card-detail"[^>]*>share of code</span></span>',
        )

    def test_empty_data_states_and_hydration_completion_are_governed(self):
        from scripts.pipeline.web_render import _script
        from scripts.rendering.webkit.dashboard import (
            empty_state_hidden,
            render_dashboard_surface,
        )

        html, _ = render_dashboard_surface("liquid-glass")
        self.assertEqual(
            set(re.findall(r'data-empty-state="([^"]+)"', html)),
            {"flagship", "focus-now", "focus-next", "focus-shipped"},
        )
        self.assertEqual(
            len(re.findall(r'<p class="db-empty"[^>]*\bhidden\b[^>]*data-empty-state=', html)),
            4,
            "pending hydration must not make an unproved no-data claim",
        )
        self.assertTrue(empty_state_hidden("pending"))
        self.assertTrue(empty_state_hidden("error"))
        self.assertFalse(empty_state_hidden("complete", item_count=0))
        self.assertTrue(empty_state_hidden("complete", item_count=1))
        self.assertIn('data-dashboard-hydration="pending"', html)
        source = _script()
        self.assertIn("staticSelectorHidden", source)
        self.assertGreaterEqual(source.count("hideAllEmptyStates();"), 2)
        self.assertIn("setEmptyStateForSuccess", source)
        self.assertIn("Number(itemCount) > 0", source)
        self.assertIn('staticDataEnum("[data-dashboard-hydration]", "dashboardHydration", "complete")', source)
        self.assertIn('staticDataEnum("[data-dashboard-hydration]", "dashboardHydration", "error")', source)

    def test_hydration_is_prototype_only_and_contract_closed(self):
        from scripts.pipeline.web_render import _script
        source = _script()
        self.assertEqual([], _runtime_source_errors(source, _contract()))
        self.assertNotRegex(source, r"['\"]\s*<[A-Za-z]", "no HTML tag templates in JavaScript")
        self.assertEqual([], _prototype_errors(_contract(), _html()))

    def test_headless_receipt_fails_closed_on_incomplete_or_wrong_hydration(self):
        from scripts.quality.headless_receipts import (
            _expected_index_hydration_facts,
            _probe_html,
            _validate_index_hydration_facts,
            dom_probe_artifact,
        )

        expected = _expected_index_hydration_facts()
        data = json.loads(dom_probe_artifact("index").read_text(encoding="utf-8"))
        _validate_index_hydration_facts(data, expected)
        self.assertEqual(data["hydration_state"], "complete")
        self.assertEqual(data["readiness"]["outcome"], "ready")
        self.assertEqual(data["sentinel_values"], expected["sentinel_values"])
        self.assertEqual(data["prototype_origin_counts"], expected["prototype_origin_counts"])
        self.assertEqual(data["empty_state_hidden"], expected["empty_state_hidden"])

        probe_source = _probe_html("index", "/site/index.html", 390, 1000)
        self.assertIn('hydrationState === "pending"', probe_source)
        self.assertIn('"prototype_origin_counts"', probe_source)
        self.assertIn('"sentinel_values"', probe_source)
        self.assertIn('"offenders": offenders,', probe_source)
        self.assertNotIn("offenders.slice", probe_source)
        for outcome in ("hydration-error", "hydration-timeout", "hydration-marker-missing"):
            self.assertIn(outcome, probe_source)
        self.assertNotIn("window.setTimeout(probe, 800)", probe_source)

        for field, wrong in (
            ("hydration_state", "error"),
            ("sentinel_values", {**expected["sentinel_values"], "hero-contributions": "—"}),
            ("prototype_origin_counts", {
                **expected["prototype_origin_counts"], "repository": 0,
            }),
            ("empty_state_hidden", {
                **expected["empty_state_hidden"], "focus-next": True,
            }),
        ):
            mutant = deepcopy(data)
            mutant[field] = wrong
            with self.assertRaises(RuntimeError, msg=f"receipt must reject wrong {field}"):
                _validate_index_hydration_facts(mutant, expected)
        mutant = deepcopy(data)
        mutant["prototype_origin_counts"]["rogue"] = 1
        with self.assertRaises(RuntimeError):
            _validate_index_hydration_facts(mutant, expected)

    def test_css_and_script_grammars_are_independently_pinned_and_literal_closed(self):
        from scripts.pipeline.web_render import _script
        from scripts.rendering.webkit.dashboard import _dashboard_css, render_dashboard_surface
        from scripts.rendering.webkit.design_render_adapter import css_numeric_occurrences

        _, css = render_dashboard_surface("liquid-glass")
        hashes = _contract()["grammar_hashes"]
        self.assertEqual(hashes, {"css_sha256": EXPECTED_CSS_SHA256,
                                  "script_sha256": EXPECTED_SCRIPT_SHA256})
        self.assertEqual(hashlib.sha256(css.encode()).hexdigest(), hashes["css_sha256"])
        self.assertEqual(hashlib.sha256(_script().encode()).hexdigest(), hashes["script_sha256"])
        self.assertNotRegex(css, r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(")
        self.assertNotIn("box-shadow", css)
        local_css = _dashboard_css()
        policy = _contract()["css_policy"]
        rows = css_numeric_occurrences(local_css)
        self.assertEqual(policy["scope"],
                         "scripts/rendering/webkit/dashboard.py::_dashboard_css")
        self.assertEqual(_literal_manifest_hash(rows), EXPECTED_LOCAL_LITERAL_MANIFEST_SHA256)
        self.assertEqual(policy["occurrence_manifest_sha256"],
                         EXPECTED_LOCAL_LITERAL_MANIFEST_SHA256)
        self.assertEqual(sum(row["count"] for row in rows), policy["occurrence_count"])
        self.assertEqual(sorted({row["value"] for row in rows}), policy["literal_vocabulary"])
        self.assertEqual(sorted(set(re.findall(r"var\((--[\w-]+)", local_css))),
                         policy["variable_refs"])
        self.assertEqual(sorted(set(re.findall(
            r"(?<![-\w])([A-Za-z][\w-]*)\(", local_css))), policy["function_roster"])
        self.assertEqual(sorted(set(re.findall(
            r"\b(?:transparent|currentColor)\b", local_css, re.I))),
            policy["color_keywords"])
        self.assertNotRegex(local_css, r"var\([^),]+,")
        self.assertNotRegex(local_css, r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(")
        provenance = policy["provenance"]
        self.assertEqual(
            provenance,
            {
                "authority_status": "declared-unresolved",
                "exactness": "consistency-only",
                "gap_id": "W5-dashboard-literal-provenance",
                "ratification_status": "unratified",
                "source_mode": None,
                "source_ref": (
                    "docs/plans/handoff/w3-index-migration-design.md"
                    "#d-w3-lit-1-dashboard-literal-gap"
                ),
            },
        )
        source_path, _, anchor = provenance["source_ref"].partition("#")
        source = (ROOT / source_path).read_text(encoding="utf-8")
        self.assertIn(anchor, re.sub(r"[^a-z0-9]+", "-", source.lower()))
        for literal in policy["literal_vocabulary"]:
            self.assertIn(f"`{literal}`", source)

    def test_default_theme_is_threaded_and_no_fragment_pins_default(self):
        from scripts.rendering.design import loader
        from scripts.rendering.webkit import dashboard
        from scripts.rendering.webkit.components import render_theme_switcher
        from scripts.pipeline.web_render import render_dashboard

        self.assertNotIn("DEFAULT_THEME", inspect.getsource(dashboard))
        self.assertNotIn("DEFAULT_THEME", inspect.getsource(render_theme_switcher))
        for profile in loader.load("_index")["active_design_profiles"]:
            html = render_dashboard(profile)
            self.assertIn(f'data-house-theme="{profile}"', html)
            self.assertIn(f'class="ps-{profile}"', html)
            self.assertIn(
                f':root:not([data-theme]) .theme-switcher[data-switcher-house="{profile}"]', html
            )
            self.assertIn(f':root:not([data-theme]) .card-{profile}-dashboard-score', html)

    def test_w2_debt_is_fully_resolved_but_retained_as_history(self):
        cover = json.loads((ROOT / "contracts" / "dom_cover.json").read_text(encoding="utf-8"))
        debt = cover["pages"]["index"]["debt"]
        self.assertTrue(debt, "W2 debt history must not be deleted")
        self.assertTrue(all(row["resolved_count"] == row["baseline_count"] for row in debt))
        prototype_cover = cover["coverage"].get("runtime_prototype_cover", {})
        self.assertEqual(set(prototype_cover), {"index-hydration"})
        self.assertEqual(
            {row["id"] for row in prototype_cover["index-hydration"]["prototypes"]},
            {row["id"] for row in _contract()["prototypes"]},
        )

    def test_negative_contract_and_source_mutations_are_observable(self):
        from scripts.pipeline.web_render import _script
        from scripts.rendering.webkit.dashboard import _dashboard_css
        from scripts.rendering.webkit.design_render_adapter import css_numeric_occurrences

        contract = _contract()
        malformed = deepcopy(contract)
        malformed["prototypes"][0]["max_clones"] = True
        self.assertTrue(_prototype_errors(malformed, _html()))
        malformed = deepcopy(contract)
        malformed["prototypes"][0]["writes"][0]["field"] = "invented"
        self.assertTrue(_prototype_errors(malformed, _html()))
        malformed_html = _html().replace('data-prototype="calendar-cell"',
                                         'data-prototype="calendar-cell"><template', 1)
        self.assertTrue(_prototype_errors(contract, malformed_html))
        literal_template_text = _html().replace(
            'data-prototype="calendar-cell"><i',
            'data-prototype="calendar-cell">ROGUE<i',
            1,
        )
        self.assertTrue(_prototype_errors(contract, literal_template_text))
        self.assertTrue(_runtime_source_errors(_script() + "\nconst x = node.cloneNode(true);", contract))
        self.assertTrue(_runtime_source_errors(_script().replace(
            "target.append(node);", "target.append(node); target.append(node);"), contract))
        for mutation in (
            "\nconst shallow = node.cloneNode(false);",
            "\nconst text = document.createTextNode('rogue');",
            "\nconst element = document['createElement']('div');",
            "\nconst element2 = document['create' + 'Element']('div');",
            "\nconst element3 = document?.createElement?.('div');",
            "\nconst element4 = Reflect.get(document, 'create' + 'Element')('div');",
            "\nconst ce = document.createElement; ce.call(document, 'div');",
            "\nnode['append'](document.body);",
            "\nElement.prototype.append.call(document.body, node);",
            "\nnode.innerText = 'rogue';",
            "\nnode.style['color'] = 'red';",
            "\nnode['inner' + 'HTML'] = '<b>rogue</b>';",
            "\nnode['\\u0069nnerHTML'] = '<b>rogue</b>';",
            "\nconst textNode = new Text('rogue');",
            "\ndocument.body.insertAdjacentText('beforeend', 'rogue');",
            "\nReflect.set(node, 'textContent', 'rogue');",
            "\nconst image = new Image();",
            "\nnode.style.color = 'red';",
            "\nnode.dataset.rogue = 'yes';",
            "\nnode.setAttribute('id', 'rogue');",
            "\ndocument.body.replaceChildren();",
        ):
            errors = _runtime_source_errors(_script() + mutation, contract)
            self.assertIn("runtime program is outside the single admitted grammar hash", errors,
                          mutation)
        self.assertIn(
            "runtime program is outside the single admitted grammar hash",
            _runtime_source_errors(_script().replace("\n", "\n ", 1), contract),
            "even whitespace drift is outside the frozen singleton program",
        )

        from scripts.contracts.design_predicates import switcher_profile_governed
        from scripts.rendering.webkit.components import render_theme_switcher
        from scripts.rendering.webkit.design_render_adapter import switcher_facts
        switcher_html, switcher_css = render_theme_switcher("liquid-glass")
        from scripts.rendering.design import loader
        for profile in loader.load("_index")["active_design_profiles"]:
            prefix = f':root[data-theme="{profile}"] .theme-switcher .theme-option'
            for state in (":hover", ":active", ":focus-visible",
                          '[aria-pressed="true"]', ":disabled"):
                mutant = switcher_css.replace(
                    f"{prefix}{state} {{", f"{prefix}{state} {{ z-index: 987;", 1)
                self.assertFalse(
                    switcher_profile_governed(switcher_facts(switcher_html, mutant)),
                    f"{profile}/{state}: declaration drift must red",
                )

        local_css = _dashboard_css()
        for mutant in (
            local_css.replace("gap: 7px", "gap: 8px", 1),
            local_css.replace("min-width: 460px", "min-width: 560px", 1),
            local_css.replace("38%", "58%", 1),
            local_css.replace("stroke-width: 1.6", "stroke-width: 2", 1),
            local_css.replace("max-width: 480px", "max-width: 760px", 1),
            local_css + "\n.db-dashboard { gap: 7px; }",
            local_css.replace("7px", "1rem", 1),
        ):
            self.assertNotEqual(
                _literal_manifest_hash(css_numeric_occurrences(mutant)),
                EXPECTED_LOCAL_LITERAL_MANIFEST_SHA256,
            )
        for mutant in (
            local_css + "\n.db-dashboard { color: rgb(1, 2, 3); }",
            local_css + "\n.db-dashboard { color: #fff; }",
            local_css + "\n.db-dashboard { gap: var(--rogue, 7px); }",
        ):
            self.assertTrue(
                re.search(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(|var\([^),]+,", mutant)
                or sorted(set(re.findall(r"var\((--[\w-]+)", mutant)))
                != _contract()["css_policy"]["variable_refs"]
            )


if __name__ == "__main__":
    unittest.main()
