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

    def test_token_root_embedded_verbatim(self):
        from scripts.rendering.design_tokens import emit_css_root
        self.assertIn(
            emit_css_root().strip(), self.html,
            "the web :root must be design_tokens.emit_css_root() verbatim (Law 3 token parity)")

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

    def test_material_and_accessibility(self):
        for needle in ("backdrop-filter", ":focus-visible",
                       "prefers-reduced-motion", "prefers-reduced-transparency"):
            self.assertIn(needle, self.html, f"web dashboard must include {needle!r}")

    def test_colour_only_from_tokens_no_rainbow(self):
        """Restraint: the component CHROME paints from var(--token)/color-mix, never a
        pile of hand hexes (the old 9-accent tell). Hex legitimately lives in exactly
        two injected blocks — the token source (emit_css_root's :root/[data-theme])
        and the LANG_COLORS map (Linguist identity colours, data not chrome). Scrub
        both, then the remaining component CSS + HTML + JS must hold NO raw hex."""
        from scripts.rendering.design_tokens import emit_css_root
        scrubbed = self.html.replace(emit_css_root().strip(), "")
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
