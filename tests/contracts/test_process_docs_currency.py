"""Process-docs currency guard (operator-directed): SKILL.md + AGENTS.md must teach the LIVE
process, or an AI agent cannot drive the system. Mirrors the kernel docs-currency law.

Conductor-authored RED: it fails today because `skills/design-language-tdd/` is stale (teaches a
6-step loop, a non-functional two-arg bootstrap example, "headless proof deferred", and omits the
build-lane routing / Mode C reference lane / failure-ratchet / convergence law). An Opus lane
refreshes the skill + adds `contracts/process_docs_currency_policy.toml` to make this data-driven
and green. Until then this reddens for the right reason.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "skills" / "design-language-tdd"
AGENTS = ROOT / "AGENTS.md"

# Stale claims that must NOT survive anywhere in the skill (each is superseded by the live SOP).
STALE_TOKENS = [
    "self-demonstrating design system",   # the product is the universal compiler, not this
    "headless proof is deferred",         # MF1 Chrome-headless is binding now
    "deferred R4 aspect",                 # same
]
# The two-arg bootstrap form is non-functional (gate() returns admit=False without --expect).
BOOTSTRAP_TWO_ARG = re.compile(r'bootstrap_red_ref\s+"[^"]+"\s+"[^"]+"\s*(?:`|$|\n)')

# Live-process concepts the skill MUST teach (name, or a SOP-POINTER to AGENTS.md).
REQUIRED_CONCEPTS = [
    "13-step",                 # the full slice ritual
    "DESIGN-VERDICT",          # the three-gate cadence
    "ADVERSARIAL-VERDICT",
    "build lane",              # Opus-builds / Codex-reviews routing
    "Mode C",                  # the reference-capture lane
    "convergence",             # the review convergence law
    "MF1",                     # binding Chrome-headless receipts
]


def _skill_text() -> str:
    parts = []
    for md in sorted(SKILL_DIR.rglob("*.md")):
        parts.append(md.read_text(encoding="utf-8"))
    return "\n".join(parts)


class ProcessDocsCurrency(unittest.TestCase):
    def test_skill_dir_exists(self):
        self.assertTrue(SKILL_DIR.is_dir(), "the design-language-tdd skill must exist")

    def test_no_stale_tokens_in_skill(self):
        text = _skill_text().lower()
        found = [t for t in STALE_TOKENS if t.lower() in text]
        self.assertEqual(found, [], f"skill still teaches superseded claims: {found}")

    def test_no_nonfunctional_two_arg_bootstrap_example(self):
        text = _skill_text()
        hits = BOOTSTRAP_TWO_ARG.findall(text)
        # a two-arg bootstrap example with no --expect nearby is the non-functional form
        offenders = [h for h in hits if "--expect" not in text[text.find(h):text.find(h) + 200]]
        self.assertEqual(offenders, [], "skill prints the non-functional two-arg bootstrap command")

    def test_skill_teaches_live_process(self):
        text = _skill_text()
        missing = [c for c in REQUIRED_CONCEPTS if c.lower() not in text.lower()]
        self.assertEqual(missing, [], f"skill omits live-process concepts (or SOP-POINTERs): {missing}")

    def test_skill_routes_to_plan_of_record_and_sop(self):
        text = _skill_text()
        self.assertIn("docs/plans/ACTIVE.md", text, "skill must route to the plan-of-record")
        self.assertIn("AGENTS.md", text, "skill must route to the SOP (AGENTS.md)")


if __name__ == "__main__":
    unittest.main()
