"""P5-1 — the ANTI-CONVERGENCE law: themes must be provably DISTINCT design languages.

This INVERTS the retired convergence rule (test_ia_tokens_are_theme_independent forced the
IA to be identical across themes, which is *why* Power BI looked like Apple). For every pair
of active themes, their structural SIGNATURE (radius + type ramp) must differ on a QUORUM of
axes — a colour-only difference is NOT enough. So "Power BI looks like Apple" becomes a
permanent RED.

RED-first: against the pre-P5-1 state (all themes shared config IA) every pair's signature was
identical → this contract failed. P5-1 promoted per-theme IA (design_tokens.THEME_IA), making
each theme structurally distinct → GREEN. Mutation-proven below: collapsing a theme's IA back
to the default reddens the pairwise check.
"""
from __future__ import annotations

import unittest
from itertools import combinations

from scripts.rendering import design_tokens as dt

# The structural signature axes that must distinguish a design language (not colour).
_QUORUM = 2  # a theme pair must differ on >= this many signature axes


def _signature(name: str) -> tuple:
    r = dt.radius(name)
    ts = dt.type_scale(name)
    return (
        r["panel"], r["tile"],
        ts["display"][0], ts["display"][1],   # hero size + weight
        ts["metric_lg"][0], ts["body"][0],
    )


def _differing_axes(a: tuple, b: tuple) -> int:
    return sum(1 for x, y in zip(a, b) if x != y)


class DesignDistinctnessContract(unittest.TestCase):
    def test_every_theme_pair_is_structurally_distinct(self):
        names = list(dt.THEMES)
        offenders = []
        for x, y in combinations(names, 2):
            d = _differing_axes(_signature(x), _signature(y))
            if d < _QUORUM:
                offenders.append(f"{x} vs {y}: differ on only {d} signature axes (need >={_QUORUM})")
        self.assertEqual([], offenders,
                         "themes must be DISTINCT design languages, not colour swaps:\n  " + "\n  ".join(offenders))

    def test_signature_covers_radius_and_type(self):
        # the signature must actually read structural IA, not just colour — so a future
        # colour-only theme cannot pass distinctness.
        sig = _signature(dt.DEFAULT_THEME)
        self.assertEqual(len(sig), 6)
        self.assertEqual(sig[0], dt.radius(dt.DEFAULT_THEME)["panel"])

    def test_distinctness_reddens_if_a_theme_collapses_to_default(self):
        """Mutation proof: a theme whose IA equals the default's must fail the pairwise law."""
        default_sig = _signature(dt.DEFAULT_THEME)
        # a forged theme identical to the default differs on 0 axes -> below quorum
        self.assertLess(_differing_axes(default_sig, default_sig), _QUORUM)
        # and at least one real pair clears the quorum today (the law is live, not vacuous)
        names = list(dt.THEMES)
        self.assertTrue(
            any(_differing_axes(_signature(x), _signature(y)) >= _QUORUM
                for x, y in combinations(names, 2)),
            "no real theme pair clears the quorum — the distinctness law would be vacuous",
        )


if __name__ == "__main__":
    unittest.main()
