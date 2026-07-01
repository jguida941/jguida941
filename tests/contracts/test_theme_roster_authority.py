"""P5-THEME-ROSTER — one public theme roster authority.

The canonical public site is `site/index.html` with one theme selector. It must expose
exactly the active design profiles from `contracts/design_profiles/_index.json` — no
reserved profile may leak into the public switcher, and no active profile may be proved
by conformance while missing from the public surface.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "contracts").is_dir():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
INDEX = ROOT / "contracts" / "design_profiles" / "_index.json"
PUBLIC_SITE = ROOT / "site" / "index.html"


def _profile_index() -> dict:
    return json.loads(INDEX.read_text(encoding="utf-8"))


class ThemeRosterAuthorityContract(unittest.TestCase):
    def test_web_theme_bridge_matches_active_design_profiles(self):
        """`design_tokens.py` is only a public-web projection bridge; its keyspace is not an
        independent roster."""
        from scripts.rendering import design_tokens as dt

        active = _profile_index()["active_design_profiles"]
        for label, mapping in (
            ("THEMES", dt.THEMES),
            ("THEME_META", dt.THEME_META),
            ("MATERIALS", dt.MATERIALS),
            ("THEME_IA", dt.THEME_IA),
        ):
            self.assertEqual(
                active,
                list(mapping),
                f"{label} must be ordered exactly like active_design_profiles",
            )

    def test_public_dashboard_offers_exactly_active_design_profiles(self):
        active = sorted(_profile_index()["active_design_profiles"])
        html = PUBLIC_SITE.read_text(encoding="utf-8")
        rendered = sorted(set(re.findall(r'data-theme-set="([^"]+)"', html)))
        self.assertEqual(
            active,
            rendered,
            "site/index.html must expose exactly active design profiles in the public switcher",
        )

    def test_reserved_profiles_are_not_public_theme_options(self):
        index = _profile_index()
        html = PUBLIC_SITE.read_text(encoding="utf-8")
        public_options = set(re.findall(r'data-theme-set="([^"]+)"', html))
        leaked = sorted(set(index["reserved_design_profiles"]) & public_options)
        self.assertEqual([], leaked, f"reserved profiles leaked into public switcher: {leaked}")

    def test_active_public_themes_resolve_web_bridge_tokens(self):
        from scripts.rendering import design_tokens as dt

        for name in _profile_index()["active_design_profiles"]:
            self.assertEqual(set(dt.roles()), set(dt.theme(name)), f"{name}: incomplete role bridge")
            self.assertIn("blur", dt.material(name), f"{name}: missing material bridge")
            self.assertIn("panel", dt.radius(name), f"{name}: missing radius bridge")


if __name__ == "__main__":
    unittest.main()
