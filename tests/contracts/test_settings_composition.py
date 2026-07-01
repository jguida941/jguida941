"""P5-SETTINGS (authority: settings) — the governed control plane.

`compose(base, overrides)` + `is_admissible()` (scripts/quality/settings_admissibility.py) are the
ONE Python decision source. An INVALID combination — a partial property mix that is a valid instance
of NO active design language — is UNCONSTRUCTABLE (the design twin of the bootstrap-RED gate).
`render_settings()` -> `site/settings.html` only DISPLAYS the decision; it carries no second (JS)
verdict. candidate_only.
"""
from __future__ import annotations

import copy
import unittest
from pathlib import Path


def _repo_root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "scripts").is_dir() and (p / "site").is_dir():
            return p
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
SETTINGS = ROOT / "site" / "settings.html"


class SettingsCompositionContract(unittest.TestCase):
    def test_invalid_combination_is_unconstructable(self):
        """A Frankenstein card — liquid-glass frosted material + Carbon's square 0-radius — conforms
        to NO active language (neither an Apple rounded grouped list nor a Carbon flat Tile), so the
        gate refuses it. Mutation-provable (widen the admissible logic and it would slip through)."""
        from scripts.quality.settings_admissibility import is_admissible
        self.assertFalse(
            is_admissible("liquid-glass", {"card": {"material": "liquid-glass", "radius_px": 0}}),
            "a frosted square-0 card is a valid instance of no design language -> unconstructable")

    def test_partial_override_on_an_uncovered_axis_is_rejected(self):
        """codex settings #5: an override on an axis NOT covered by an emitted invariant
        (liquid-glass declares no button-anatomy invariant) still cannot slip — admissibility checks
        the composed button's RENDERED facts against the full fingerprint of the language it claims
        to be. A glass capsule wearing Carbon's label-left-icon-right DOM is a valid instance of NO
        language -> unconstructable."""
        from scripts.quality.settings_admissibility import is_admissible
        self.assertFalse(
            is_admissible("liquid-glass", {"button": {"anatomy": "label-left-icon-right"}}),
            "a glass capsule with Carbon's anatomy is a Frankenstein on an uncovered axis")

    def test_admissible_wholesale_swap_composes_and_conforms(self):
        """Swapping Carbon's WHOLE card into a liquid-glass base is admissible — the composed card is
        a real Carbon instance (it satisfies Carbon's full card invariant set as rendered)."""
        from scripts.quality.settings_admissibility import is_admissible, matching_languages
        from scripts.rendering.design import loader
        carbon_card = copy.deepcopy(loader.load("carbon")["components"]["card"])
        self.assertTrue(is_admissible("liquid-glass", {"card": carbon_card}),
                        "Carbon's whole card in a liquid-glass base is admissible")
        self.assertIn("carbon", matching_languages("liquid-glass", {"card": carbon_card}, "card"))

    def test_admissible_space_is_computed_not_rubber_stamped(self):
        """The pre-baked space is COMPUTED from the real render (not asserted True): every cell
        marked admissible re-verifies as a full valid language instance. (Honest: a swap that cannot
        render validly is excluded, so the space is a genuine computation, not a rubber stamp.)"""
        from scripts.quality.settings_admissibility import admissible_space, is_admissible
        from scripts.rendering.design import loader
        space = admissible_space()
        self.assertTrue(space, "the admissible space is non-empty")
        for cell in space:
            if cell["admissible"]:
                spec = copy.deepcopy(loader.load(cell["source"])["components"][cell["component"]])
                self.assertTrue(is_admissible(cell["base"], {cell["component"]: spec}),
                                f"admissible cell must re-verify against the render: {cell}")

    def test_settings_page_is_generated_and_has_no_second_verdict_source(self):
        """codex must-fix #2 — ONE Python decider: site/settings.html DISPLAYS the admissibility that
        Python computes and carries NO verdict logic of its own (no <script>). Drift-guarded."""
        from scripts.rendering.settings.settings import render_settings
        self.assertTrue(SETTINGS.is_file(), "site/settings.html must be generated + committed")
        self.assertEqual(SETTINGS.read_text(encoding="utf-8"), render_settings(),
                         "settings drift — regenerate via scripts.rendering.settings.settings.write_settings")
        self.assertNotIn("<script", SETTINGS.read_text(encoding="utf-8"),
                         "the settings page carries no JS verdict source (Python is the ONE decider)")


if __name__ == "__main__":
    unittest.main()
