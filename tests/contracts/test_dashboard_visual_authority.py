"""REDs for W3's visible regression and missing design authority."""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


class DashboardVisualAuthorityContract(unittest.TestCase):
    def test_all_documents_reset_the_user_agent_body_inset(self):
        reset = "html, body { height: 100%; margin: 0; }"
        border_box = "*, *::before, *::after { box-sizing: border-box; }"
        for page in ("index", "showcase", "studio", "settings"):
            html = (ROOT / "site" / f"{page}.html").read_text(encoding="utf-8")
            self.assertIn(reset, html, page)
            self.assertIn(border_box, html, page)

    def test_home_orientation_is_integrated_and_not_self_breadcrumbed(self):
        from scripts.pipeline.web_render import render_dashboard

        html = render_dashboard("liquid-glass")
        hero = re.search(r'<section[^>]*data-dashboard-section="hero".*?</section>', html, re.S)
        self.assertIsNotNone(hero)
        self.assertEqual(1, len(re.findall(r"<h1\b", html)))
        self.assertIn('id="hero-name"', hero.group(0))
        self.assertIn('id="hero-tag"', hero.group(0))
        self.assertNotIn('class="ps-crumbs"', html)
        self.assertNotIn('class="ps-title"', html)

    def test_content_surfaces_reject_raw_hairlines_and_liquid_blur(self):
        from scripts.rendering.webkit.dashboard import render_dashboard_surface

        _, css = render_dashboard_surface("liquid-glass")
        section = re.search(r"\.db-section\s*\{([^}]*)\}", css)
        self.assertIsNotNone(section)
        self.assertNotIn("border: 1px solid var(--hairline)", section.group(1))
        for selector in (".db-section", ".card-liquid-glass-dashboard-score",
                         ".card-liquid-glass-dashboard-snapshot"):
            rule = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
            self.assertIsNotNone(rule, selector)
            self.assertNotIn("backdrop-filter", rule.group(1), selector)

    def test_selector_is_not_a_generic_button_transplant(self):
        from scripts.rendering.webkit.theme_selector import render_theme_selector

        html, css = render_theme_selector("carbon")
        self.assertIn('role="radiogroup"', html)
        self.assertEqual(3, html.count('role="radio"'))
        self.assertEqual(1, html.count('aria-checked="true"'))
        self.assertNotIn("theme-option-icon", html)
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr))", css)
        self.assertNotIn("button-hover-background", css)

    def test_every_page_exposes_exactly_one_selected_theme_selector(self):
        for page in ("index", "showcase", "studio", "settings"):
            html = (ROOT / "site" / f"{page}.html").read_text(encoding="utf-8")
            controls = re.findall(
                r'<(?:div|fieldset)\b[^>]*\bdata-theme-selector="site"[^>]*>.*?</(?:div|fieldset)>',
                html,
                re.S,
            )
            self.assertEqual(1, len(controls), page)
            self.assertEqual(1, controls[0].count('aria-checked="true"'), page)

    def test_visible_dashboard_literals_cannot_be_unresolved(self):
        contract = json.loads((ROOT / "contracts/dashboard_surface.json").read_text(encoding="utf-8"))
        provenance = contract["css_policy"]["provenance"]
        self.assertIn(provenance["source_mode"], {
            "official-code", "official-spec", "measured-reference", "owner-ratified",
        })
        self.assertNotEqual("consistency-only", provenance["exactness"])
        self.assertEqual("approved", provenance["ratification_status"])

    def test_showcase_pass_claims_expose_their_authority(self):
        html = (ROOT / "site/showcase.html").read_text(encoding="utf-8")
        pass_rows = re.findall(r'<tr[^>]*data-status="pass".*?</tr>', html, re.S)
        self.assertTrue(pass_rows)
        for row in pass_rows:
            self.assertRegex(row, r'data-clause-id="[^"]+"')
            self.assertRegex(row, r'data-authority="(?:official-code|official-docs|approved-reference|owner-ratified)"')
            self.assertRegex(row, r'data-source-mode="(?:official-code|official-spec|measured-reference|owner-ratified)"')
            self.assertRegex(row, r'data-exactness="(?:source-exact|specification-exact|measurement-exact|perceptual)"')


if __name__ == "__main__":
    unittest.main()
