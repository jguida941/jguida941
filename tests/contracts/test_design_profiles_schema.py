"""P5-PROFILE-SPINE (authority: design_profiles) — the design-profile DATA closed cover.

A design profile is DATA (scout `design_profiles.json` style): `contracts/design_profiles/
_index.json` (the active/reserved roster), `design_aspect_roster.json` (the CLOSED COVER of
aspects every active profile must address), and one `<lang>.json` per profile. This guard pins
the DATA itself BEFORE any render — the tokens-first discipline (USWDS/Polaris): an active
profile that omits a roster aspect, or a roster/profile drift between the index and the files
on disk, reddens, exactly like an undeclared file.

SPINE-a scope: the index/roster shape + index<->files parity + per-profile ENVELOPE +
aspect-coverage set-equality. The DTCG token block ($value/$type/{alias}) + the loader +
the derived-parity (liquid-glass tokens == config.py) land in SPINE-b. candidate_only.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
PROFILES = ROOT / "contracts" / "design_profiles"


def _load(name: str) -> dict:
    return json.loads((PROFILES / name).read_text(encoding="utf-8"))


class DesignProfileSpineContract(unittest.TestCase):
    def setUp(self):
        self.index = _load("_index.json")
        self.roster = _load("design_aspect_roster.json")
        self.roster_ids = [a["id"] for a in self.roster["aspects"]]

    # --- the index: a clean active/reserved roster (scout pattern) ---
    def test_index_active_and_reserved_are_disjoint_and_active_nonempty(self):
        active = self.index["active_design_profiles"]
        reserved = self.index["reserved_design_profiles"]
        self.assertEqual(self.index.get("contract_id"), "DesignProfileIndex")
        self.assertTrue(active, "at least one active design profile is required")
        self.assertEqual([], sorted(set(active) & set(reserved)),
                         "a profile cannot be both active and reserved")
        for bucket in (active, reserved):
            self.assertEqual(len(bucket), len(set(bucket)), "duplicate profile in the index")

    # --- the aspect roster: a CLOSED COVER, deferred reasons honest ---
    def test_aspect_roster_is_closed_and_deferrals_are_justified(self):
        self.assertEqual(self.roster.get("contract_id"), "DesignAspectRoster")
        self.assertEqual(len(self.roster_ids), len(set(self.roster_ids)), "duplicate aspect id")
        for aspect in self.roster["aspects"]:
            self.assertIn(aspect["emission_status"], ("emitted", "deferred"),
                          f"{aspect['id']}: emission_status must be emitted|deferred")
            if aspect["emission_status"] == "deferred":
                self.assertTrue(aspect.get("defer_reason"),
                                f"{aspect['id']}: a deferred aspect must carry a defer_reason")

    # --- index <-> files parity (both drift directions) ---
    def test_index_active_matches_profile_files_on_disk(self):
        on_disk = {p.stem for p in PROFILES.glob("*.json")
                   if p.name not in ("_index.json", "design_aspect_roster.json")}
        self.assertEqual(set(self.index["active_design_profiles"]), on_disk,
                         "index.active_design_profiles must equal the <lang>.json profile files on disk "
                         "(add the profile + index it in the same slice; reserved profiles have no file yet)")

    # --- every active profile: honest envelope + CLOSED aspect cover ---
    def test_every_active_profile_validates_envelope_and_covers_all_aspects(self):
        for name in self.index["active_design_profiles"]:
            prof = _load(f"{name}.json")
            self.assertEqual(prof.get("contract_id"), "DesignLanguageProfile", f"{name}: wrong contract_id")
            self.assertEqual(prof.get("profile"), name, f"{name}: profile field must equal the filename stem")
            self.assertEqual(prof.get("authority_status"), "candidate_only", f"{name}: must be candidate_only")
            self.assertIs(prof.get("cannot_mark_done"), True, f"{name}: cannot_mark_done must be true")
            self.assertTrue(prof.get("derived_from") is not None or prof.get("derived_from") is None)  # field present
            self.assertIn("derived_from", prof, f"{name}: must declare derived_from (\"config\"|null)")
            self.assertTrue(prof.get("doctrine_doc"), f"{name}: must cite a doctrine_doc")
            covered = set(prof["aspect_coverage"].keys())
            self.assertEqual(covered, set(self.roster_ids),
                             f"{name}: aspect_coverage must cover EXACTLY the roster aspects "
                             f"(missing: {sorted(set(self.roster_ids) - covered)}; "
                             f"extra: {sorted(covered - set(self.roster_ids))})")

    # --- anti-tautology: the cover CAN redden (a coverage gap is caught) ---
    def test_aspect_cover_fires_on_a_gap(self):
        roster = set(self.roster_ids)
        full = {a: "covered-deferred" for a in roster}
        self.assertEqual(set(full.keys()), roster, "a full cover is green")
        gap = dict(full); gap.pop(sorted(roster)[0])
        self.assertNotEqual(set(gap.keys()), roster, "a profile missing one aspect must redden the cover")
        extra = dict(full); extra["bogus-aspect"] = "covered-deferred"
        self.assertNotEqual(set(extra.keys()), roster, "an undeclared aspect must redden the cover")


if __name__ == "__main__":
    unittest.main()
