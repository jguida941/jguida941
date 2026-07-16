"""RED for source-backed, genuinely distinct page-language compositions.

Route intent (landing/proof-report/control-plane/workbench) and design-language archetype are
independent axes. These tests reject the W3 failure where every language used one normalized DOM
and only tokens/component radii changed. The profile DATA is the closed construction input; rendered
structure and committed route templates must agree with it.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
PROFILES = ROOT / "contracts" / "design_profiles"
MANIFEST = json.loads((ROOT / "contracts" / "page_manifest.json").read_text(encoding="utf-8"))
ACTIVE = tuple(json.loads((PROFILES / "_index.json").read_text(encoding="utf-8"))["active_design_profiles"])
ROUTES = {row["id"]: row for row in MANIFEST["pages"]}

TARGETS = {
    "apple-dark": "apple-editorial-grouped",
    "carbon": "carbon-ui-shell-data-table",
    "liquid-glass": "liquid-functional-layer",
}
AXES = {
    "navigation",
    "hero-orientation",
    "hierarchy",
    "grouping",
    "data-presentation",
    "density",
    "alignment",
    "material-placement",
    "scan-path",
    "responsive-composition",
}
REQUIRED_ANATOMY = {
    "apple-dark": {"editorial-masthead", "grouped-content"},
    "carbon": {"global-header", "side-nav", "data-workspace"},
    "liquid-glass": {"functional-layer", "content-layer"},
}


def _profile(name: str) -> dict:
    return json.loads((PROFILES / f"{name}.json").read_text(encoding="utf-8"))


class _Skeleton(HTMLParser):
    """Canonical structural signature that deliberately ignores skins and copy.

    Component internals are typed placeholders so a square button versus a capsule cannot make a
    generic page template look distinct. Parent edges, semantic tags/roles, and archetype-region
    placement remain, which is the page-composition claim under test.
    """

    COMPONENT_OWNERS = {"webkit.button", "webkit.chip", "webkit.card"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool]] = []
        self.nodes: list[tuple] = []
        self._skipping = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        owner = data.get("data-dom-owner")
        if self._skipping:
            self._skipping += 1
            self.stack.append((tag, True))
            return
        if owner in self.COMPONENT_OWNERS:
            self.nodes.append((len(self.stack), "component", owner))
            self._skipping = 1
            self.stack.append((tag, True))
            return
        kept = tuple(sorted(
            (key, value or "")
            for key, value in attrs
            if key in {"role", "type", "data-arch-region", "data-page-archetype", "data-page-region"}
        ))
        self.nodes.append((len(self.stack), tag, kept))
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}:
            self.stack.append((tag, False))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if self.stack and self.stack[-1][0] == tag:
            _, skipped = self.stack.pop()
            if skipped:
                self._skipping -= 1

    def handle_endtag(self, tag: str) -> None:
        if not self.stack:
            return
        _, skipped = self.stack.pop()
        if skipped:
            self._skipping -= 1


def _skeleton(html: str) -> tuple[tuple, ...]:
    parser = _Skeleton()
    parser.feed(html)
    return tuple(parser.nodes)


class PageArchetypeDataContract(unittest.TestCase):
    def test_page_archetype_is_emitted_not_deferred(self):
        roster = json.loads((PROFILES / "design_aspect_roster.json").read_text(encoding="utf-8"))
        row = next(item for item in roster["aspects"] if item["id"] == "page-archetype")
        self.assertEqual("emitted", row["emission_status"])
        self.assertNotIn("defer_reason", row)

    def test_each_profile_has_one_closed_distinct_archetype(self):
        observed = set()
        for name in ACTIVE:
            data = _profile(name)
            arch = data["page_archetype"]
            self.assertEqual("DesignPageArchetype", arch["contract_id"], name)
            self.assertEqual(1, arch["schema_version"], name)
            self.assertEqual(TARGETS[name], arch["target_family"], name)
            self.assertEqual(f"{TARGETS[name]}.v1", arch["renderer_key"], name)
            self.assertEqual([], arch["gaps"], f"{name}: unresolved composition cannot render")
            self.assertEqual(AXES, set(arch["axes"]), f"{name}: page axes are a closed cover")
            for axis, claim in arch["axes"].items():
                self.assertTrue(claim["value_id"], f"{name}/{axis}: value missing")
                self.assertTrue(claim["clause_ids"], f"{name}/{axis}: authority missing")
                self.assertTrue(claim["refute_by"], f"{name}/{axis}: mutation handle missing")
            self.assertEqual(set(ROUTES), set(arch["routes"]), f"{name}: route cover")
            for route, route_data in arch["routes"].items():
                self.assertEqual(ROUTES[route]["archetype"], route_data["manifest_archetype"])
                self.assertTrue(route_data["region_roster"], f"{name}/{route}: no region roster")
                self.assertEqual(
                    set(route_data["region_roster"]), set(route_data["wide_order"]),
                    f"{name}/{route}: wide composition must place every region exactly once",
                )
                self.assertEqual(
                    set(route_data["region_roster"]), set(route_data["compact_order"]),
                    f"{name}/{route}: compact composition must place every region exactly once",
                )
            observed.add(arch["target_family"])
            emitted = [row for row in data["invariants"] if row.get("aspect") == "page-archetype"]
            self.assertEqual(1, len(emitted), f"{name}: exactly one page-archetype law")
            self.assertEqual("emitted", emitted[0]["emission_status"])
            self.assertEqual("deterministic", emitted[0]["determinism"])
            self.assertEqual("rendered", emitted[0]["fact_source"])
            self.assertIn("clause_id", emitted[0])
        self.assertEqual(set(TARGETS.values()), observed)


class PageArchetypeRenderContract(unittest.TestCase):
    def test_studio_mini_sites_have_distinct_normalized_structures(self):
        from scripts.rendering.webkit.archetype import render_archetype

        skeletons = {}
        for name in ACTIVE:
            html, _ = render_archetype(name)
            self.assertIn(f'data-page-archetype="{TARGETS[name]}"', html)
            for region in REQUIRED_ANATOMY[name]:
                self.assertIn(f'data-arch-region="{region}"', html, f"{name}/{region}")
            skeletons[name] = _skeleton(html)
        self.assertEqual(len(ACTIVE), len(set(skeletons.values())),
                         "component skins cannot distinguish one shared mini-site template")

    def test_dashboard_profiles_have_distinct_normalized_structures(self):
        from scripts.rendering.webkit.dashboard import render_dashboard_surface

        skeletons = {}
        for name in ACTIVE:
            html, _ = render_dashboard_surface(name)
            self.assertIn(f'data-page-archetype="{TARGETS[name]}"', html)
            for region in REQUIRED_ANATOMY[name]:
                self.assertIn(f'data-arch-region="{region}"', html, f"{name}/{region}")
            skeletons[name] = _skeleton(html)
        self.assertEqual(len(ACTIVE), len(set(skeletons.values())),
                         "dashboard construction must differ before tokens and component skins")

    def test_committed_routes_carry_inert_profile_templates_and_one_live_host(self):
        for page, row in ROUTES.items():
            html = (ROOT / row["route"]).read_text(encoding="utf-8")
            self.assertEqual(1, html.count('data-page-profile-host="site"'), page)
            for name in ACTIVE:
                pattern = (rf'<template\b[^>]*data-page-profile="{re.escape(name)}"[^>]*'
                           rf'data-page-archetype="{re.escape(TARGETS[name])}"')
                self.assertRegex(html, pattern, f"{page}/{name}: missing inert profile template")

    def test_dashboard_heading_hierarchy_is_left_stacked(self):
        from scripts.rendering.webkit.dashboard_style import dashboard_css

        css = dashboard_css()
        rule = re.search(r"\.db-section-head\s*\{([^}]*)\}", css)
        self.assertIsNotNone(rule)
        self.assertNotIn("justify-content: space-between", rule.group(1))
        self.assertTrue(
            "display: block" in rule.group(1) or "flex-direction: column" in rule.group(1),
            "eyebrow and title must form one start-aligned vertical hierarchy",
        )

    def test_site_selector_is_independent_of_vendor_button_geometry(self):
        from scripts.rendering.webkit.theme_selector import render_theme_selector

        baseline = render_theme_selector("apple-dark")
        # The local selector renderer intentionally has no profile component input. This pin makes
        # a future components.button transplant an API-level change, not silent visual drift.
        for house in ACTIVE:
            html, css = render_theme_selector(house)
            self.assertNotIn("theme-option-icon", html)
            self.assertNotIn("999px", css)
            self.assertNotIn("50px", css)
            self.assertEqual(baseline[1], css)


if __name__ == "__main__":
    unittest.main()
