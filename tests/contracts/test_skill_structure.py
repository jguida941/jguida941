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
REQUIRED_REFERENCES = (
    "doctrine-ingest.md",
    "add-design-language.md",
    "add-component.md",
    "add-page-aspect.md",
    "prove-theme.md",
    "boundaries.md",
)


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

    def test_doctrine_ingest_lane_emits_obligations_not_vibes(self):
        """The design-language skill must encode the owner's core architecture: Scout is a
        doctrine-to-contract compiler front-end. It emits typed axes, negative cases, refutation
        handles, and visual receipt obligations; it does not merely summarize design docs."""
        text = (SKILL / "references" / "doctrine-ingest.md").read_text(encoding="utf-8")
        low = text.lower()
        for token in (
            "typed axes",
            "negative_cases",
            "refute_by",
            "receipt_obligation",
            "candidate_only",
            "cannot_mark_done",
            "deterministic",
            "visual",
        ):
            self.assertIn(token, low, f"doctrine-ingest.md must require {token}")
        self.assertIn("docs/design/<lang>.md", text, "doctrine docs live under docs/design/, not a stale path")

    def test_skill_references_current_design_doc_path(self):
        """The repo's doctrine docs live in docs/design/*.md; stale docs/design-languages paths would
        send future theme slices to the wrong home."""
        for path in [SKILL / "SKILL.md", *(SKILL / "references").glob("*.md")]:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("docs/design-languages", text, f"{path.name}: stale doctrine-doc path")

    def test_skill_codifies_the_current_architecture_and_is_honest(self):
        """The skill must reflect the ACTUAL system (docs/plans/DESIGN-SYSTEM.md): the
        PROFILE(data)->RENDER->INVARIANT->RECEIPT data-flow, profile-as-DATA, and the per-slice
        SOP I actually run (RED -> declare homes -> doc-ground -> implement -> mutation -> codex).
        And it must be HONEST: enforcement here is LOCAL pytest + receipts — there is NO Rust
        kernel in this repo, so the skill must not claim a kernel 'decides' locally (that framing
        was retired by the architecture + best-practice reviews)."""
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        low = text.lower()
        for seam in ("profile", "render", "invariant", "receipt", "conform"):
            self.assertIn(seam, low, f"SKILL.md must name the {seam!r} seam of the data-flow")
        self.assertIn("design_profiles", low, "SKILL.md must reflect profile-as-DATA (contracts/design_profiles)")
        self.assertIn("codex", low, "the per-slice loop must include a codex review")
        self.assertNotRegex(text, r"kernel\s+(decides|is the (eventual )?authority)",
                            "drop the 'kernel decides' framing — enforcement here is LOCAL pytest + receipts")


if __name__ == "__main__":
    unittest.main()
