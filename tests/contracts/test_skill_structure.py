"""Public distribution guard: internal authoring methods are not shipped.

The procedural skill and its reference lanes are retained in an authorized
private project. This test covers the current checked-out public tree only:
history, mirrors, downloads and other branches require separate remediation.
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class PublicAuthoringBoundaryTests(unittest.TestCase):
    def test_private_skill_not_present_in_current_public_tree(self):
        folder = ROOT / "skills" / "design-language-tdd"
        self.assertFalse(folder.exists() or folder.is_symlink(),
                         "internal authoring skill must not ship in public source")

    def test_public_plans_do_not_link_to_private_skill_files(self):
        for relative in (
            "docs/plans/ACTIVE.md",
            "docs/plans/DESIGN-SYSTEM.md",
            "docs/plans/handoff/HANDOFF.md",
            "docs/plans/handoff/d-shell-0-design.md",
        ):
            with self.subTest(relative=relative):
                content = (ROOT / relative).read_text(encoding="utf-8")
                self.assertNotIn("skills/design-language-tdd/", content)

    def test_public_agent_documentation_requires_private_authorization(self):
        content = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("access-controlled private project handoff", content)
        self.assertIn("Public runtime renderers", content)


if __name__ == "__main__":
    unittest.main()
