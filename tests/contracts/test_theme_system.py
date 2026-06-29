"""Red-first THEME SYSTEM contract — authority: governed Liquid Glass material +
Power BI information-architecture separation.

The doctrine made executable: a THEME swaps COLOUR + MATERIAL only; the information
architecture (type scale, spacing, radius geometry) is theme-INDEPENDENT. So the same
layout can wear Liquid Glass, Apple, or Power BI skins and stay legible — proving the
three laws are separable, which is the whole point of the theme switcher.

Every theme must therefore be:
  1. COMPLETE   — defines every role token (a missing role = a broken swap).
  2. LEGIBLE    — primary/body ink clears WCAG AA (>=4.5:1) on its surface and raised
                  tile; dim ink clears the large-text floor (>=3.0:1).
  3. RESTRAINED — at most a handful of distinct chromatic colours across all roles
                  (one accent + the 3 semantic status hues), never a rainbow.
  4. PARITY     — the DEFAULT theme's core roles equal the SVG token source in
                  config.py, so the README SVG projection and the web :root cannot
                  drift (Law 3, token half).
And the IA tokens (type scale / spacing / radius) are identical no matter the theme.

This file imports scripts.rendering.design_tokens, which does not exist yet — so it
fails RED until the single token source is built to satisfy this contract.
"""
from __future__ import annotations

import colorsys
import re
import unittest

from scripts.core import config

# The role schema every theme must satisfy. Semantic names, never raw palette words,
# so a theme is one swap and contracts stay palette-agnostic.
REQUIRED_ROLES = (
    "ink-strong", "ink", "ink-dim",
    "surface", "surface-raised", "backdrop",
    "hairline", "accent",
    "status-success", "status-warning", "status-danger",
)
# Core roles that MUST equal the SVG source (config.py) for the default theme.
PARITY_ROLES = {
    "ink-strong": config.TEXT_BRIGHT, "ink": config.TEXT, "ink-dim": config.TEXT_DIM,
    "surface": config.SURFACE_BASE, "surface-raised": config.SURFACE_RAISED,
    "backdrop": config.SURFACE_BACKDROP, "accent": config.CYAN,
    "status-success": config.GREEN, "status-warning": config.YELLOW, "status-danger": config.RED,
}

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def _rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


def _lum(hex_color: str) -> float:
    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in _rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(fg: str, bg: str) -> float:
    a, b = _lum(fg), _lum(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def _is_chromatic(hex_color: str) -> bool:
    r, g, b = _rgb(hex_color)
    _, s, v = colorsys.rgb_to_hsv(r, g, b)
    return s >= 0.20 and v >= 0.15  # saturated and not near-black


def _hue_bucket(hex_color: str) -> int:
    r, g, b = _rgb(hex_color)
    h, _, _ = colorsys.rgb_to_hsv(r, g, b)
    return round(h * 12) % 12  # 12 coarse hue buckets


class ThemeSystemContract(unittest.TestCase):
    def setUp(self):
        from scripts.rendering import design_tokens as dt
        self.dt = dt
        self.themes = dt.THEMES

    def test_at_least_three_named_themes(self):
        self.assertGreaterEqual(len(self.themes), 3,
                                "the switcher needs >=3 themes to show the doctrine off")
        self.assertIn(self.dt.DEFAULT_THEME, self.themes)

    def test_every_theme_defines_every_role_with_valid_hex(self):
        offenders = []
        for name, roles in self.themes.items():
            for role in REQUIRED_ROLES:
                val = roles.get(role)
                if val is None:
                    offenders.append(f"{name}: missing role {role!r}")
                elif not _HEX.match(str(val)):
                    offenders.append(f"{name}.{role} = {val!r} is not a 6-digit hex")
        self.assertEqual([], offenders, "every theme must define every role as hex:\n  " + "\n  ".join(offenders))

    def test_default_theme_matches_svg_token_source(self):
        """Law 3 (token half): the README SVG and the web default must share values."""
        roles = self.dt.theme(self.dt.DEFAULT_THEME)
        offenders = [
            f"{role}: theme {roles.get(role)} != config {expected}"
            for role, expected in PARITY_ROLES.items()
            if str(roles.get(role, "")).lower() != expected.lower()
        ]
        self.assertEqual([], offenders, "default theme must equal the SVG token source:\n  " + "\n  ".join(offenders))

    def test_every_theme_is_legible_AA(self):
        offenders = []
        for name, roles in self.themes.items():
            # primary/body ink AND the secondary ink-dim/accent are checked on BOTH
            # surfaces (tiles/rows render ink-dim on surface-raised, not just surface).
            for surf in ("surface", "surface-raised"):
                bg = roles[surf]
                if _contrast(roles["ink-strong"], bg) < 4.5:
                    offenders.append(f"{name}: ink-strong on {surf} = {_contrast(roles['ink-strong'], bg):.2f} (<4.5)")
                if _contrast(roles["ink"], bg) < 4.5:
                    offenders.append(f"{name}: ink on {surf} = {_contrast(roles['ink'], bg):.2f} (<4.5)")
                if _contrast(roles["ink-dim"], bg) < 3.0:
                    offenders.append(f"{name}: ink-dim on {surf} = {_contrast(roles['ink-dim'], bg):.2f} (<3.0)")
                if _contrast(roles["accent"], bg) < 3.0:
                    offenders.append(f"{name}: accent on {surf} = {_contrast(roles['accent'], bg):.2f} (<3.0)")
        self.assertEqual([], offenders, "every theme must clear WCAG AA:\n  " + "\n  ".join(offenders))

    def test_every_theme_is_restrained(self):
        """Restraint, the way the old 9-accent web violated it: (1) a theme defines
        EXACTLY the role schema — no sneaking in accent-2/accent-3 decorative roles;
        (2) the whole palette stays within a small set of chromatic hue families (the
        surface/ink tint family + one accent + the 3 semantic status hues)."""
        offenders = []
        for name, roles in self.themes.items():
            if set(roles) != set(REQUIRED_ROLES):
                extra = set(roles) - set(REQUIRED_ROLES)
                offenders.append(f"{name}: extra/decorative roles {sorted(extra)} beyond the schema")
            chromatic = {role: roles[role] for role in roles
                         if role in REQUIRED_ROLES and _is_chromatic(roles[role])}
            buckets = {_hue_bucket(v) for v in chromatic.values()}
            if len(buckets) > 5:
                offenders.append(f"{name}: {len(buckets)} chromatic hue families {sorted(chromatic)} — rainbow")
        self.assertEqual([], offenders, "themes must be restrained (one accent, no rainbow):\n  " + "\n  ".join(offenders))

    def test_ia_is_complete_and_bounded(self):
        """P5 (convergence RETIRED): IA is now PER-THEME — a theme is a full design
        language, not a colour swap — but BOUNDED. The DEFAULT theme's IA equals config
        (the SVG parity + portability anchor); every theme defines the complete type
        ladder, every size stays >= the 11px floor, and radii stay within a sane range.
        That themes actually DIFFER is proven separately (test_design_distinctness)."""
        # DEFAULT == config (the anchor)
        self.assertEqual(self.dt.type_scale(self.dt.DEFAULT_THEME), dict(config.TYPE_SCALE))
        dr = self.dt.radius(self.dt.DEFAULT_THEME)
        self.assertEqual((dr["panel"], dr["tile"]), (config.GLASS_RX, config.GLASS_TILE_RX))
        # every theme: complete ladder, legible floor, bounded radii
        for name in self.themes:
            ts = self.dt.type_scale(name)
            self.assertEqual(set(ts), set(config.TYPE_SCALE), f"{name}: incomplete type ladder")
            for tok, (size, _w) in ts.items():
                self.assertGreaterEqual(size, 11, f"{name}.{tok}={size} below the 11px floor")
            r = self.dt.radius(name)
            for k in ("panel", "tile"):
                self.assertTrue(2 <= r[k] <= 40, f"{name}.radius.{k}={r[k]} out of bounds")

    def test_emit_css_root_carries_every_role_and_theme(self):
        css = self.dt.emit_css_root()
        # :root defines the default role vars
        for role in REQUIRED_ROLES:
            self.assertIn(f"--{role}:", css, f":root missing --{role}")
        # each non-default theme gets a [data-theme="x"] override block
        for name in self.themes:
            if name == self.dt.DEFAULT_THEME:
                continue
            self.assertIn(f'[data-theme="{name}"]', css, f"missing [data-theme=\"{name}\"] block")
        # the IA radius/type are also exposed as vars (shared geometry)
        self.assertIn("--radius-panel:", css)
        self.assertIn("--radius-tile:", css)


if __name__ == "__main__":
    unittest.main()
