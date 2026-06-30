"""P5-SKILL — the skill-structure guard for skills/design-language-tdd/.

The skill is the repeatable engine (research design language -> derive proper-style invariants ->
GENERATE the themed components/charts/layout -> prove). This RED guards its structure so it stays
a real, discoverable, portable skill (mirrors repo-surface-scout/tests/test_skill_structure shape):
a SKILL.md with `name:` + `description:` frontmatter, and the required lane references present.
candidate_only; decides no authority.
"""
from __future__ import annotations

import unittest
from pathlib import Path


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
SKILL = ROOT / "skills" / "design-language-tdd"
REQUIRED_REFERENCES = ("add-design-language.md", "prove-theme.md", "boundaries.md")


class SkillStructureContract(unittest.TestCase):
    def test_skill_md_exists_with_name_and_description_frontmatter(self):
        md = SKILL / "SKILL.md"
        self.assertTrue(md.is_file(), "skills/design-language-tdd/SKILL.md must exist")
        text = md.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---"), "SKILL.md must open with YAML frontmatter")
        head = text.split("---", 2)[1] if text.count("---") >= 2 else ""
        self.assertRegex(head, r"(?m)^name:\s*design-language-tdd\s*$", "frontmatter needs name: design-language-tdd")
        self.assertRegex(head, r"(?m)^description:\s*\S", "frontmatter needs a one-line description")

    def test_required_lane_references_present(self):
        refs = SKILL / "references"
        self.assertTrue(refs.is_dir(), "skills/design-language-tdd/references/ must exist")
        missing = [r for r in REQUIRED_REFERENCES if not (refs / r).is_file()]
        self.assertEqual([], missing, f"missing required skill references: {missing}")

    def test_honest_claim_boundary_is_stated(self):
        """The skill must carry the never-overclaim rule ('satisfies the profile', not 'is Apple')."""
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
        self.assertIn("satisfies", text)
        self.assertIn("never", text)
        self.assertIn("candidate", text)

    def test_loop_lanes_are_referenced(self):
        """SKILL.md routes to the lanes (research -> invariants -> generate -> prove)."""
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for ref in REQUIRED_REFERENCES:
            self.assertIn(ref, text, f"SKILL.md must route to references/{ref}")


if __name__ == "__main__":
    unittest.main()
