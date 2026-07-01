"""P5-1 — the ANTI-CONVERGENCE law: themes must be provably DISTINCT design languages.

This INVERTS the retired convergence rule (test_ia_tokens_are_theme_independent forced the
IA to be identical across themes, which is *why* Power BI looked like Apple). For every pair
of web themes, their IA signature (radius + type ramp) must differ on a QUORUM of axes, and
for every active design-language profile, the RENDERED component fingerprints must differ on
a quorum of rendered axes. Colour-only or declared-JSON-only difference is NOT enough. So
"Power BI looks like Apple" and "two profiles render the same components" become permanent RED.

RED-first: against the pre-P5-1 state (all themes shared config IA) every pair's signature was
identical → this contract failed. P5-1 promoted per-theme IA (design_tokens.THEME_IA), making
each theme structurally distinct → GREEN. P5 pre-theme hardening then bound the design-language
signature to rendered component facts, so a model cannot claim distinctness by editing only
profile declarations.
"""
from __future__ import annotations

import unittest
from itertools import combinations

from scripts.rendering import design_tokens as dt

# The structural signature axes that must distinguish a design language (not colour).
_IA_QUORUM = 2          # a web theme pair must differ on >= this many IA axes
_RENDER_QUORUM = 3      # active profiles must differ on >= this many rendered component axes


def _web_ia_signature(name: str) -> tuple:
    r = dt.radius(name)
    ts = dt.type_scale(name)
    return (
        r["panel"], r["tile"],
        ts["display"][0], ts["display"][1],   # hero size + weight
        ts["metric_lg"][0], ts["body"][0],
    )


def _rendered_design_signature(name: str) -> dict[str, object]:
    """Flatten rendered button/chip/card fingerprints into one active-profile signature."""
    from scripts.quality.design_invariants import rendered_component_fingerprint
    sig: dict[str, object] = {}
    for component in ("button", "chip", "card"):
        for axis, value in rendered_component_fingerprint(name, component).items():
            sig[f"{component}.{axis}"] = value
    return sig


def _differing_axes(a, b) -> int:
    if isinstance(a, dict) and isinstance(b, dict):
        return sum(1 for key in set(a) | set(b) if a.get(key) != b.get(key))
    return sum(1 for x, y in zip(a, b) if x != y)


class DesignDistinctnessContract(unittest.TestCase):
    def test_every_web_theme_pair_has_distinct_ia_tokens(self):
        """Legacy web themes still need distinct IA tokens (radius/type), but this is no longer the
        whole design-language authority; rendered component facts are checked below."""
        names = list(dt.THEMES)
        offenders = []
        for x, y in combinations(names, 2):
            d = _differing_axes(_web_ia_signature(x), _web_ia_signature(y))
            if d < _IA_QUORUM:
                offenders.append(f"{x} vs {y}: differ on only {d} IA axes (need >={_IA_QUORUM})")
        self.assertEqual([], offenders,
                         "web themes must be structurally distinct, not colour swaps:\n  " + "\n  ".join(offenders))

    def test_every_active_design_language_pair_is_render_distinct(self):
        """The design-language anti-convergence gate uses rendered facts. Declared fingerprints can
        document intent, but the pairwise distinctness quorum is computed from observed output."""
        from scripts.rendering.design import loader
        names = loader.load("_index")["active_design_profiles"]
        offenders = []
        for x, y in combinations(names, 2):
            d = _differing_axes(_rendered_design_signature(x), _rendered_design_signature(y))
            if d < _RENDER_QUORUM:
                offenders.append(f"{x} vs {y}: differ on only {d} rendered axes (need >={_RENDER_QUORUM})")
        self.assertEqual([], offenders,
                         "active design languages must render distinctly:\n  " + "\n  ".join(offenders))

    def test_signature_covers_radius_and_type(self):
        # the web IA signature must actually read structural IA, not just colour — so a future
        # colour-only theme cannot pass distinctness.
        sig = _web_ia_signature(dt.DEFAULT_THEME)
        self.assertEqual(len(sig), 6)
        self.assertEqual(sig[0], dt.radius(dt.DEFAULT_THEME)["panel"])

    def test_rendered_signature_covers_components(self):
        sig = _rendered_design_signature("liquid-glass")
        self.assertIn("button.focus_recipe", sig)
        self.assertIn("chip.anatomy", sig)
        self.assertIn("card.material", sig)
        self.assertEqual(sig["button.material"], "liquid-glass")

    def test_distinctness_reddens_if_a_theme_collapses_to_default(self):
        """Mutation proof: a theme whose IA equals the default's must fail the pairwise law."""
        default_sig = _web_ia_signature(dt.DEFAULT_THEME)
        # a forged theme identical to the default differs on 0 axes -> below quorum
        self.assertLess(_differing_axes(default_sig, default_sig), _IA_QUORUM)
        # and at least one real pair clears the quorum today (the law is live, not vacuous)
        names = list(dt.THEMES)
        self.assertTrue(
            any(_differing_axes(_web_ia_signature(x), _web_ia_signature(y)) >= _IA_QUORUM
                for x, y in combinations(names, 2)),
            "no real theme pair clears the quorum — the distinctness law would be vacuous",
        )

    def test_render_distinctness_reddens_if_rendered_signatures_collapse(self):
        """Mutation proof for the newer authority: identical rendered component facts are below the
        quorum even if declarations claimed otherwise."""
        sig = _rendered_design_signature("liquid-glass")
        self.assertLess(_differing_axes(sig, sig), _RENDER_QUORUM)


if __name__ == "__main__":
    unittest.main()
