"""Red-first WEB DASHBOARD contract — authority: cross-projection parity (Law 3) +
governed Liquid Glass material + a11y. The web dashboard is the second projection of
the one analytics contract and must be GENERATED, never hand-written, so it can't drift
back into a bespoke 1458-line page.

Proves, against the committed site/index.html:
  1. GENERATED — committed bytes == web_render.render_dashboard() (a drift guard: hand
     edits redden; the page can only change by changing the generator + regenerating).
  2. TOKEN PARITY (Law 3, token half) — the page embeds design_tokens.emit_css_root()
     verbatim, so the web :root and the SVG cards share one token source.
  3. PROJECTION PARITY (Law 3) — the web binds the same shared-snapshot metric keys the
     README SVG cards read (hero KPI + the core metrics), driven by the same JSON.
  4. MATERIAL + A11Y — real backdrop-filter glass, a visible-focus ring, reduced-motion
     and reduced-transparency fallbacks (governed material, accessible).
  5. RESTRAINT — colour comes only from token vars (no rainbow of hand-authored hexes
     like the old 9-accent page).
  6. PRIVACY + STATIC-SAFE — never leaks token mode / credentials; no external scripts
     (GitHub Pages safe); the theme switcher offers every theme.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
INDEX = ROOT / "site" / "index.html"


class WebDashboardContract(unittest.TestCase):
    def setUp(self):
        self.html = INDEX.read_text(encoding="utf-8")

    def test_index_is_generated_not_handwritten(self):
        from scripts.pipeline.web_render import render_dashboard
        self.assertEqual(
            self.html, render_dashboard(),
            "site/index.html is GENERATED — regenerate via scripts.pipeline.web_render and "
            "commit; it must never be hand-edited (run: python -m scripts.pipeline.web_render)")

    def test_pageshell_consumes_the_one_declaration_projection_without_a_second_root(self):
        from scripts.rendering import design_tokens
        from scripts.rendering.pageshell.pageshell import _profile_decls

        for profile in design_tokens.ACTIVE_THEME_NAMES:
            self.assertEqual(_profile_decls(profile), design_tokens.css_declarations(profile))
            for name, value in design_tokens.css_declarations(profile).items():
                self.assertIn(f"{name}: {value};", self.html)
        self.assertEqual(self.html.count("--glass-blur: 22px;"), 1,
                         "index ships pageshell's projection once, not a duplicate legacy root")

    def test_binds_shared_snapshot_metric_keys(self):
        """The web reads the SAME shared-snapshot keys the README SVG cards do."""
        required = (
            "last_year_contributions",  # the hero KPI (shared with the SVG hero)
            "total_repos", "total_stars", "public_scope_commits",
            "ci_coverage_pct", "primary_lang_share_pct", "active_days_last_year",
        )
        missing = [k for k in required if k not in self.html]
        self.assertEqual([], missing, f"web projection must bind shared metric keys; missing: {missing}")

    def test_renders_calendar_and_rhythm_sections(self):
        """The web projection covers the same surfaces as the README, including the
        contribution calendar + activity heatmap (hidden until their data hydrates)."""
        for needle in ('id="calendar-panel"', 'id="rhythm-panel"',
                       "contribution_calendar", "activity_rhythm",
                       "Contribution Calendar", "When I Code"):
            self.assertIn(needle, self.html, f"web dashboard missing {needle!r}")

    def test_status_conveyed_by_shape_not_hue_alone(self):
        """DESIGN_SPEC 3.6 / 10 (and the README status_chip): pipeline status must read
        by icon-SHAPE AND label, never hue alone — so a desaturated/colour-blind viewer
        still distinguishes OK from failure. The colour belongs in a small glyph, not a
        saturated full-hue pill (the old 'green button' AI tell)."""
        html = self.html
        prototype = re.search(
            r'<template[^>]*data-prototype="pipeline-status".*?</template>', html, re.S)
        self.assertIsNotNone(prototype, "pipeline status must have one governed static prototype")
        for field in ("ok-icon", "warn-icon", "bad-icon"):
            self.assertIn(f'data-field="{field}"', prototype.group(0))
        shapes = re.findall(r'<(?:path|polygon)[^>]*(?:d|points)="([^"]+)"', prototype.group(0))
        self.assertGreaterEqual(len(set(shapes)), 3, "status states require distinct Lucide geometry")
        # restraint: the chip LABEL stays neutral ink — colour lives in the glyph, not a
        # full-hue text/pill. So .chip.<state> must NOT repaint the label colour.
        for state in ("ok", "warn", "bad"):
            rule = re.search(r'\.db-status\[data-status="' + state + r'"\]\s*\{([^}]*)\}', html)
            if rule:
                self.assertNotRegex(
                    rule.group(1), r"(^|;)\s*color\s*:",
                    f".chip.{state} must not paint the label a status hue — status reads by shape")

    def test_material_and_accessibility(self):
        for needle in ("backdrop-filter", ":focus-visible",
                       "prefers-reduced-motion", "prefers-reduced-transparency"):
            self.assertIn(needle, self.html, f"web dashboard must include {needle!r}")

    def test_responsive_mobile_and_touch_targets(self):
        """Mobile is a first-class design rule (Apple HIG / WCAG 2.5.5), and renders differ on
        Safari: the page must carry (1) a PHONE breakpoint (<=480px), (2) >=44px touch targets on
        interactive controls, (3) a scrollable heatmap wrapper so the dense matrix doesn't distort
        on a narrow screen, and (4) the -webkit- material prefix so frosted glass works on Safari."""
        html = self.html
        self.assertRegex(html, r"@media[^{]*max-width:\s*4[0-8]\dpx", "needs a phone breakpoint (<=480px)")
        self.assertIn("-webkit-backdrop-filter", html, "Safari needs the -webkit-backdrop-filter prefix")
        self.assertIn("min-height: 44px", html, "interactive controls need >=44px touch targets (Apple/WCAG)")
        self.assertRegex(html, r"\.db-rhythm-scroll\s*\{[^}]*overflow-x:\s*auto",
                         "the heatmap must scroll on a narrow screen, not squish/distort")

    def test_colour_only_from_tokens_no_rainbow(self):
        """Restraint: the component CHROME paints from var(--token)/color-mix, never a
        pile of hand hexes (the old 9-accent tell). Hex legitimately lives in exactly
        two injected blocks — the token source (emit_css_root's :root/[data-theme])
        and the LANG_COLORS map (Linguist identity colours, data not chrome). Scrub
        both, then the remaining component CSS + HTML + JS must hold NO raw hex."""
        from scripts.rendering import design_tokens
        scrubbed = self.html
        for profile in design_tokens.ACTIVE_THEME_NAMES:
            for value in design_tokens.css_declarations(profile).values():
                if re.fullmatch(r"#[0-9a-fA-F]{3,8}", value):
                    scrubbed = scrubbed.replace(value, "")
        scrubbed = re.sub(r"const LANG_COLORS = \{.*?\};", "", scrubbed, flags=re.S)
        stray = sorted(set(re.findall(r"#[0-9a-fA-F]{3,8}\b", scrubbed)))
        self.assertEqual([], stray, f"component chrome must paint from token vars, not raw hex: {stray}")

    def test_never_leaks_private_signals(self):
        for banned in ("token_mode", "ghp_", "github_pat_", "Bearer "):
            self.assertNotIn(banned, self.html, f"web dashboard must never contain {banned!r}")

    def test_static_pages_safe_and_offers_every_theme(self):
        from scripts.rendering.design_tokens import THEME_META, THEMES
        self.assertNotIn("<script src=", self.html, "no external scripts (GitHub Pages static-safe)")
        for name in THEMES:
            self.assertIn(f'data-theme-set="{name}"', self.html, f"theme switcher missing {name}")
            self.assertIn(THEME_META[name]["label"], self.html, f"switcher missing label for {name}")


if __name__ == "__main__":
    unittest.main()
