"""Positive guard: the README glassmorphism must survive (authority: owner directive #1).

A previous attempt to "go flat/light" was rejected — the owner wants the glass kept.
The design contracts mostly forbid AI-look decoration; this is the COUNTERWEIGHT that
asserts the glass IS still there, so no future "de-AI" pass can quietly flatten the
cards. Rendered cards must still contain the frosted-glass primitives (a Gaussian-blur
backdrop + the sheen + the rim) that `glass_kit.glass_panel` bakes into every SVG.

GREEN today; reddens the moment a card stops baking its glass.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


def _hero(out: str) -> str:
    from scripts.rendering.generate_metrics_general import generate

    generate(username="jguida941", snapshot={
        "last_year_contributions": 8104, "public_scope_commits": 4264, "total_repos": 67,
        "private_owned_repos": 146, "total_stars": 78, "languages_count": 24,
        "prs_merged": 35, "releases": 0, "ci_repos": 16, "streak_days": 2,
    }, generated_at="2026-06-28T00:00:00Z", output_path=out)
    return Path(out).read_text(encoding="utf-8")


def _badges(out: str) -> str:
    from scripts.rendering.generate_badges import generate

    generate(output_path=out, public_nonfork_repos=42, public_forks=8,
             private_owned_repos=146, ci_count=16, last_year_contributions=8104)
    return Path(out).read_text(encoding="utf-8")


class GlassPreservedContract(unittest.TestCase):
    """The frosted-glass look the owner asked to keep must remain baked into the SVG."""

    GLASS_MARKERS = ("feGaussianBlur", "gk-sheen", "gk-rim")

    def _cards(self, d: str):
        return {"hero": _hero(str(Path(d) / "hero.svg")), "badges": _badges(str(Path(d) / "badges.svg"))}

    def test_cards_keep_the_frosted_glass(self):
        with tempfile.TemporaryDirectory() as d:
            cards = self._cards(d)
        offenders = []
        for name, svg in cards.items():
            for marker in self.GLASS_MARKERS:
                if marker not in svg:
                    offenders.append(f"{name}: lost glass primitive '{marker}' (card was flattened)")
        self.assertEqual(
            [], offenders,
            "README cards must keep the baked glassmorphism (owner directive — do NOT flatten):\n  "
            + "\n  ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
