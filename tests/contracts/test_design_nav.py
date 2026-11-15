"""P5-BOARD B-1b (authority: nav) — the governed nav component connects every page.

`render_nav(profile, links, active)` is a webkit component like button/chip/card: per-language
ANATOMY from `components.nav` profile DATA (carbon: flat square tabs, 2px active underline;
apple-dark/liquid-glass: capsule pills, accent-filled active), token-only colour, and the active
page marked `aria-current="page"`. Every site page carries the band (`.site-nav`) linking the
other three surfaces — the operator's "no way to connect stuff" fix, governed. candidate_only.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path


def _root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "contracts" / "design_profiles").is_dir():
            return p
    raise RuntimeError("repo root not found")


ROOT = _root()
_LINKS = [("home", "index.html"), ("showcase", "showcase.html"),
          ("studio", "studio.html"), ("settings", "settings.html")]


def _active():
    from scripts.rendering.design import loader
    return loader.load("_index")["active_design_profiles"]


class NavContract(unittest.TestCase):
    def test_render_nav_builds_a_tokenonly_band_with_active_marker(self):
        from scripts.rendering.webkit.components import render_nav
        for name in _active():
            html, css = render_nav(name, _LINKS, active="index.html")
            self.assertIn('class="site-nav', html, f"{name}: the band container")
            self.assertEqual(html.count("<a "), len(_LINKS), f"{name}: every surface linked")
            self.assertIn('aria-current="page"', html, f"{name}: the active page is marked")
            self.assertNotRegex(css, r"#[0-9a-fA-F]{3,8}\b",
                                f"{name}: nav CSS must be token-only (no raw hex)")

    def test_nav_anatomy_differs_by_language(self):
        """Carbon is square with an underline active; the capsule languages are pills with a
        filled active — a real anatomy branch, not a colour swap (profile DATA decides)."""
        from scripts.rendering.webkit.components import render_nav
        _, carbon = render_nav("carbon", _LINKS, active="index.html")
        _, apple = render_nav("apple-dark", _LINKS, active="index.html")
        self.assertIn("border-radius: 0", carbon.replace("0px", "0"), "carbon nav is square")
        self.assertRegex(apple, r"border-radius:\s*999px", "apple nav is capsule pills")
        self.assertNotEqual(carbon, apple)

    def test_conform_emits_passing_nav_rows(self):
        from scripts.quality.design_invariants import conform
        for name in _active():
            rows = [r for r in conform(name) if r["aspect"] == "component-nav"]
            self.assertEqual(len(rows), 1, f"{name}: one emitted nav invariant")
            self.assertEqual(rows[0]["status"], "pass", f"{name}: {rows[0]['invariant_id']}")

    def test_every_shipped_page_carries_the_band_linking_its_siblings(self):
        """Committed bytes primary (the manifest law's idiom): each page's .site-nav links the
        other three surfaces and marks itself aria-current."""
        for page, route in (("index", "site/index.html"), ("showcase", "site/showcase.html"),
                            ("settings", "site/settings.html"), ("studio", "site/studio.html")):
            b = (ROOT / route).read_text(encoding="utf-8")
            self.assertIn('class="site-nav', b, f"{page}: nav band missing")
            band = re.search(r'<nav class="site-nav.*?</nav>', b, re.S).group(0)
            self.assertIn('aria-current="page"', band, f"{page}: active marker")
            for _, href in _LINKS:
                if href != f"{page}.html":
                    self.assertIn(href, band, f"{page}: must link {href}")


class SingleSiteNavigationTests(unittest.TestCase):
    def assert_single_navigation(self, html, page):
        from html.parser import HTMLParser
        class Links(HTMLParser):
            def __init__(self):
                super().__init__();self.stack=[];self.links=[];self.bands=0
            def handle_starttag(self, tag, attrs):
                attrs=dict(attrs)
                band=tag=="nav" and "site-nav" in attrs.get("class","").split()
                if band:self.bands+=1
                if tag=="a" and attrs.get("href") in dict(_LINKS).values():
                    self.links.append((attrs,any(x[1] for x in self.stack)))
                if tag not in ("img","meta","link","input","br","hr"):
                    self.stack.append((tag,band))
            def handle_endtag(self, tag):
                for i in range(len(self.stack)-1,-1,-1):
                    if self.stack[i][0]==tag:self.stack=self.stack[:i];break
        seen=Links();seen.feed(html)
        self.assertEqual(1,seen.bands,page+": one primary navigation band")
        self.assertEqual(4,len(seen.links),page+": remove duplicate peer-navigation links")
        self.assertTrue(all(inside for _,inside in seen.links),page+": all peer links belong to the top band")
        self.assertEqual([page+".html"],[attrs["href"] for attrs,_ in seen.links if attrs.get("aria-current")=="page"])

    def test_all_four_rendered_pages_have_one_navigation_owner(self):
        from scripts.pipeline.web_render import render_dashboard
        from scripts.rendering.showcase.showcase import render_showcase
        from scripts.contracts.page_manifest import committed_receipts
        from scripts.rendering.studio.studio import render_studio
        from scripts.rendering.settings.settings import render_settings
        for page,render in (("index",render_dashboard),("showcase",lambda: render_showcase(committed_receipts(ROOT))),("studio",render_studio),("settings",render_settings)):
            with self.subTest(page=page):self.assert_single_navigation(render(),page)

    def test_duplicate_peer_row_is_rejected_and_real_breadcrumbs_remain_supported(self):
        from scripts.pipeline.web_render import render_dashboard
        from scripts.rendering.pageshell.pageshell import render_page_shell
        with self.assertRaises(AssertionError):
            self.assert_single_navigation(render_dashboard()+'<p><a href="settings.html">settings</a></p>',"index")
        html,_=render_page_shell("apple-dark",title="Nested detail",intro="",breadcrumbs=[("Parent","parent.html")])
        self.assertIn('<a href="parent.html">Parent</a>',html)

if __name__ == "__main__":
    unittest.main()
