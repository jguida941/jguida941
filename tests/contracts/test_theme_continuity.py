"""W1 (authority: page_chrome) - one selected theme governs every shipped page.

The contract closes the continuity gap across the page manifest: one frozen head bootstrap owns
URL/storage/house precedence, every page exposes every active profile's shell declarations, and
the governed navigation changes anatomy with the selected profile. Browser receipts prove the
stored choice after reload at desktop and true-mobile viewports; default-state screenshots alone
are not continuity evidence.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((ROOT / "contracts" / "page_manifest.json").read_text(encoding="utf-8"))
INDEX = json.loads(
    (ROOT / "contracts" / "design_profiles" / "_index.json").read_text(encoding="utf-8")
)
ACTIVE = tuple(INDEX["active_design_profiles"])
PAGES = {row["id"]: row["route"] for row in MANIFEST["pages"]}
VIEWPORTS = (1280, 390)


def _css_rgb(hex_color: str) -> str:
    value = hex_color.lstrip("#")
    return f"rgb({int(value[0:2], 16)}, {int(value[2:4], 16)}, {int(value[4:6], 16)})"


def _page(page: str) -> str:
    return (ROOT / PAGES[page]).read_text(encoding="utf-8")


class ThemeBootstrapContract(unittest.TestCase):
    def test_every_page_uses_the_same_bootstrap_before_theme_css(self):
        from scripts.rendering import design_tokens
        from scripts.rendering.pageshell.pageshell import theme_continuity_script_tag

        script = theme_continuity_script_tag()
        houses = {page: (design_tokens.DEFAULT_THEME if page == "index" else "apple-dark")
                  for page in PAGES}
        for page, house in houses.items():
            html = _page(page)
            self.assertEqual(html.count(script), 1, f"{page}: exactly one shared theme bootstrap")
            self.assertLess(html.index(script), html.index("<style"),
                            f"{page}: bootstrap must run before theme CSS can paint")
            root = re.search(r"<html\b[^>]*>", html, re.I)
            self.assertIsNotNone(root, f"{page}: html root missing")
            self.assertIn(f'data-house-theme="{house}"', root.group(0),
                          f"{page}: declared pre-choice house")

    def test_bootstrap_is_the_only_theme_state_machine(self):
        from scripts.pipeline.web_render import _script
        from scripts.rendering import design_tokens
        from scripts.rendering.pageshell.pageshell import theme_continuity_script_tag

        bootstrap = theme_continuity_script_tag()
        self.assertIn(json.dumps(list(ACTIVE), separators=(",", ":")), bootstrap)
        self.assertIn(json.dumps(design_tokens.THEME_STORAGE_KEY), bootstrap)
        for behavior in ("URLSearchParams", "localStorage.getItem", "localStorage.setItem",
                         "dataset.theme", "data-theme-set", "aria-pressed",
                         "data-theme-propagate", 'searchParams.set("theme", name)'):
            self.assertIn(behavior, bootstrap, f"shared bootstrap owns {behavior}")

        hydration = _script()
        for duplicate in ("dash-theme", "localStorage", "URLSearchParams", "data-theme-set",
                          "dataset.theme", "function setTheme"):
            self.assertNotIn(duplicate, hydration,
                             f"index hydration must not carry a second theme decider: {duplicate}")

    def test_all_committed_pages_embed_every_active_profile_declaration(self):
        from scripts.rendering.pageshell.pageshell import _profile_decls

        for page in PAGES:
            html = _page(page)
            for profile in ACTIVE:
                for name, value in _profile_decls(profile).items():
                    self.assertIn(f"{name}: {value};", html,
                                  f"{page}: {profile} declaration {name} must be available")

    def test_required_profile_values_have_no_fallback(self):
        from scripts.rendering.design import loader
        from scripts.rendering.pageshell.pageshell import _profile_decls

        resolved = loader.resolve_tokens("carbon")
        for path in (("radius", "panel"), ("radius", "tile"), ("font", "family")):
            broken = copy.deepcopy(resolved)
            del broken[path[0]][path[1]]
            with self.subTest(path=path), patch.object(loader, "resolve_tokens", return_value=broken):
                with self.assertRaises(KeyError, msg=f"missing required {path} must fail closed"):
                    _profile_decls("carbon")

    def test_switchable_nav_emits_each_profiles_anatomy(self):
        from scripts.rendering.webkit.components import render_switchable_nav

        links = [("home", "index.html"), ("showcase", "showcase.html")]
        html, css = render_switchable_nav("apple-dark", links, active="index.html")
        self.assertEqual(html.count("<nav "), 1, "one semantic navigation band")
        self.assertEqual(html.count("data-theme-propagate"), len(links),
                         "every governed nav destination propagates the canonical theme")
        for profile in ACTIVE:
            self.assertIn(f':root[data-theme="{profile}"] .nav-{profile}', css,
                          f"{profile}: scoped nav anatomy block missing")
        carbon = re.search(
            r':root\[data-theme="carbon"\] \.nav-carbon a\[aria-current\]\s*\{([^}]*)\}',
            css, re.S)
        apple = re.search(
            r':root\[data-theme="apple-dark"\] \.nav-apple-dark a\[aria-current\]\s*\{([^}]*)\}',
            css, re.S)
        self.assertIsNotNone(carbon)
        self.assertIsNotNone(apple)
        self.assertIn("border-bottom", carbon.group(1), "Carbon active nav is underline anatomy")
        self.assertIn("background", apple.group(1), "Apple active nav is filled capsule anatomy")

    def test_every_shipped_internal_page_link_propagates_the_theme(self):
        internal = re.compile(r'<a\b(?P<attrs>[^>]*href="[^"]+\.html[^"]*"[^>]*)>', re.I)
        for page in PAGES:
            for match in internal.finditer(_page(page)):
                self.assertIn(
                    "data-theme-propagate", match.group("attrs"),
                    f"{page}: governed internal link drops the selected theme: {match.group(0)}",
                )


class ThemeContinuityReceiptContract(unittest.TestCase):
    def test_mobile_probe_has_a_closed_scroll_container_grammar(self):
        from scripts.quality.headless_receipts import (
            DECLARED_HORIZONTAL_SCROLL_CONTAINERS,
            _theme_probe_html,
        )

        self.assertEqual(
            DECLARED_HORIZONTAL_SCROLL_CONTAINERS,
            {
                "index": (
                    {"class": "cal-wrap", "parent": "#calendar-panel"},
                    {"class": "heat-wrap", "parent": "#rhythm-panel"},
                ),
                "showcase": ({"class": "table-scroll", "parent": ".lang"},),
                "settings": ({"class": "table-scroll", "parent": ".base"},),
                "studio": (),
            },
            "adding a scroll escape requires an explicit contract change",
        )
        probe = _theme_probe_html("index", "carbon", 390)
        self.assertIn(
            "const rule = scrollRules.find((candidate) =>",
            probe,
        )
        self.assertIn("ancestor.parentElement.matches(candidate.parent)", probe)
        self.assertIn("if (declaredHere\n            && (ancestorStyle.overflowX", probe)
        self.assertNotIn("overflow-wrapper", probe,
                         "an arbitrary scrolling wrapper must not conceal overflow")

    def test_closed_runtime_matrix_is_real_and_provenanced(self):
        from scripts.quality.headless_receipts import (
            DECLARED_HORIZONTAL_SCROLL_CONTAINERS,
            THEME_CONTINUITY_KIND,
            provenance_path,
            theme_continuity_artifact,
        )
        from scripts.rendering.design import loader
        from scripts.rendering.pageshell.pageshell import _profile_decls

        for page, route in PAGES.items():
            page_hash = hashlib.sha256((ROOT / route).read_bytes()).hexdigest()
            for theme in ACTIVE:
                expected_nav = loader.load(theme)["components"]["nav"]
                expected_root = _profile_decls(theme)
                for viewport in VIEWPORTS:
                    with self.subTest(page=page, theme=theme, viewport=viewport):
                        artifact = theme_continuity_artifact(page, theme, viewport)
                        self.assertTrue(artifact.is_file(), f"missing continuity fact {artifact}")
                        data = json.loads(artifact.read_text(encoding="utf-8"))
                        self.assertEqual(data["kind"], THEME_CONTINUITY_KIND)
                        self.assertEqual(data["page"], page)
                        self.assertEqual(data["seeded_theme"], theme)
                        self.assertEqual(data["observed_theme"], theme)
                        self.assertEqual(data["viewport"]["width"], viewport)
                        self.assertEqual(data["computed_root_tokens"], expected_root)
                        self.assertEqual(data["color_scheme"], expected_root["color-scheme"])
                        self.assertEqual(data["nav"]["active_count"], 1)
                        self.assertEqual(data["nav"]["visibility"], "visible")
                        self.assertNotEqual(data["nav"]["display"], "none")
                        self.assertGreater(float(data["nav"]["opacity"]), 0)
                        self.assertIs(data["nav"]["ancestor_hidden"], False)
                        self.assertIs(data["nav"]["has_rendered_box"], True)
                        self.assertIs(data["nav"]["intersects_viewport"], True)
                        self.assertGreater(data["nav"]["box"]["width"], 0)
                        self.assertGreater(data["nav"]["box"]["height"], 0)
                        self.assertEqual(data["nav"]["radius_px"], expected_nav["radius_px"])
                        if expected_nav["anatomy"] == "underline-tabs":
                            self.assertGreaterEqual(data["nav"]["border_bottom_width_px"], 2)
                            self.assertEqual(data["nav"]["border_bottom_color"],
                                             _css_rgb(loader.resolve_tokens(theme)["color"]["accent"]))
                            self.assertEqual(data["nav"]["foreground_color"],
                                             _css_rgb(loader.resolve_tokens(theme)["color"]["ink"]))
                            self.assertEqual(data["nav"]["background_color"],
                                             "rgba(0, 0, 0, 0)")
                        else:
                            self.assertLess(data["nav"]["border_bottom_width_px"], 2)
                            colors = loader.resolve_tokens(theme)["color"]
                            self.assertEqual(data["nav"]["background_color"],
                                             _css_rgb(colors["accent"]))
                            self.assertEqual(data["nav"]["foreground_color"],
                                             _css_rgb(colors["backdrop"]))
                        if page == "index":
                            self.assertEqual(data["pressed_themes"], [theme])
                        else:
                            self.assertEqual(data["pressed_themes"], [])
                        if viewport == 390:
                            self.assertIs(data["horizontal_overflow"], False,
                                          f"{page}/{theme}: selected theme overflows at 390")
                            self.assertEqual(data["uncontained_offender_count"], 0)
                            self.assertEqual(
                                data["declared_scroll_containers"],
                                list(DECLARED_HORIZONTAL_SCROLL_CONTAINERS[page]),
                            )
                            for offender in data["offenders"]:
                                container = offender.get("scroll_container")
                                if container:
                                    self.assertIn(
                                        container["rule"],
                                        DECLARED_HORIZONTAL_SCROLL_CONTAINERS[page],
                                        f"undeclared scroll wrapper concealed {offender}",
                                    )

                        sidecar = json.loads(
                            provenance_path(artifact).read_text(encoding="utf-8"))
                        self.assertEqual(sidecar["kind"], THEME_CONTINUITY_KIND)
                        self.assertEqual(sidecar["seeded_theme"], theme)
                        self.assertEqual(sidecar["observed_theme"], theme)
                        self.assertEqual(sidecar["viewport"]["width"], viewport)
                        self.assertEqual(sidecar["page_sha256"], page_hash)
                        self.assertTrue(sidecar["chrome_version"].startswith("Google Chrome "))
                        self.assertIn("--headless=new", sidecar["command"])

    def test_state_machine_vectors_are_real_and_provenanced(self):
        from scripts.quality.headless_receipts import (
            THEME_STATE_KIND,
            provenance_path,
            theme_state_artifact,
        )

        expected = {
            "url-over-storage": {
                "inputs": {"start_page": "index", "storage": "apple-dark",
                           "url_theme": "carbon", "click_theme": None,
                           "deny_storage": False, "follow_page": None, "follow_via": None},
                "observed_theme": "carbon", "storage_value": "carbon",
                "pressed_themes": ["carbon"], "link_theme": "carbon",
            },
            "invalid-url-falls-to-storage": {
                "inputs": {"start_page": "index", "storage": "carbon",
                           "url_theme": "not-active", "click_theme": None,
                           "deny_storage": False, "follow_page": None, "follow_via": None},
                "observed_theme": "carbon", "storage_value": "carbon",
                "pressed_themes": ["carbon"], "link_theme": "carbon",
            },
            "invalid-storage-falls-to-house": {
                "inputs": {"start_page": "index", "storage": "not-active",
                           "url_theme": None, "click_theme": None,
                           "deny_storage": False, "follow_page": None, "follow_via": None},
                "observed_theme": "liquid-glass", "storage_value": "not-active",
                "pressed_themes": ["liquid-glass"], "link_theme": "liquid-glass",
            },
            "house-fallback": {
                "inputs": {"start_page": "index", "storage": None,
                           "url_theme": None, "click_theme": None,
                           "deny_storage": False, "follow_page": None, "follow_via": None},
                "observed_theme": "liquid-glass", "storage_value": None,
                "pressed_themes": ["liquid-glass"], "link_theme": "liquid-glass",
            },
            "button-persists": {
                "inputs": {"start_page": "index", "storage": None,
                           "url_theme": None, "click_theme": "carbon",
                           "deny_storage": False, "follow_page": None, "follow_via": None},
                "observed_theme": "carbon", "storage_value": "carbon",
                "pressed_themes": ["carbon"], "link_theme": "carbon",
            },
            "storage-denied-navigation": {
                "inputs": {"start_page": "index", "storage": None,
                           "url_theme": "carbon", "click_theme": None,
                           "deny_storage": True, "follow_page": "showcase", "follow_via": "nav"},
                "observed_theme": "carbon", "storage_value": "__storage_error__",
                "pressed_themes": [], "link_theme": "carbon",
            },
            "storage-denied-breadcrumb": {
                "inputs": {"start_page": "showcase", "storage": None,
                           "url_theme": "carbon", "click_theme": None,
                           "deny_storage": True, "follow_page": "index",
                           "follow_via": "breadcrumb"},
                "observed_theme": "carbon", "storage_value": "__storage_error__",
                "pressed_themes": ["carbon"], "link_theme": "carbon",
            },
        }
        for scenario, want in expected.items():
            with self.subTest(scenario=scenario):
                artifact = theme_state_artifact(scenario)
                self.assertTrue(artifact.is_file(), f"missing state-machine fact {artifact}")
                data = json.loads(artifact.read_text(encoding="utf-8"))
                self.assertEqual(data["kind"], THEME_STATE_KIND)
                self.assertEqual(data["scenario"], scenario)
                self.assertEqual(data["inputs"], want["inputs"])
                final = data["final"]
                self.assertEqual(final["observed_theme"], want["observed_theme"])
                self.assertEqual(final["storage_value"], want["storage_value"])
                self.assertEqual(final["pressed_themes"], want["pressed_themes"])
                self.assertEqual(final["propagated_link_themes"], [want["link_theme"]])
                if scenario in ("storage-denied-navigation", "storage-denied-breadcrumb"):
                    self.assertEqual(data["initial"]["observed_theme"], "carbon")
                    self.assertEqual(data["initial"]["storage_value"], "__storage_error__")
                    self.assertEqual(data["follow_page"], want["inputs"]["follow_page"])
                    self.assertIn("theme=carbon", data["followed_href"])

                sidecar = json.loads(provenance_path(artifact).read_text(encoding="utf-8"))
                self.assertEqual(sidecar["kind"], THEME_STATE_KIND)
                self.assertEqual(sidecar["scenario"], scenario)
                self.assertTrue(sidecar["chrome_version"].startswith("Google Chrome "))
                self.assertIn("--headless=new", sidecar["command"])
                start_page = want["inputs"]["start_page"]
                start_hash = hashlib.sha256((ROOT / PAGES[start_page]).read_bytes()).hexdigest()
                self.assertEqual(sidecar["page"], start_page)
                self.assertEqual(sidecar["page_sha256"], start_hash)
                follow_page = want["inputs"]["follow_page"]
                if follow_page:
                    follow_hash = hashlib.sha256(
                        (ROOT / PAGES[follow_page]).read_bytes()).hexdigest()
                    self.assertEqual(sidecar["follow_page"], follow_page)
                    self.assertEqual(sidecar["follow_page_sha256"], follow_hash)


if __name__ == "__main__":
    unittest.main()
