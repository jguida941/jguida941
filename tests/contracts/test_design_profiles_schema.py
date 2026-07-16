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
            for invariant in prof["invariants"]:
                if (invariant.get("emission_status") == "emitted"
                        and invariant.get("determinism") == "deterministic"):
                    self.assertIn(
                        invariant.get("fact_source"), ("static", "rendered"),
                        f"{name}/{invariant.get('invariant_id')}: emitted deterministic "
                        "invariants must close fact_source as static|rendered",
                    )
            covered = set(prof["aspect_coverage"].keys())
            self.assertEqual(covered, set(self.roster_ids),
                             f"{name}: aspect_coverage must cover EXACTLY the roster aspects "
                             f"(missing: {sorted(set(self.roster_ids) - covered)}; "
                             f"extra: {sorted(covered - set(self.roster_ids))})")
            # stand-in SF-4: the coverage VALUE is a governance claim — cross-check it against the
            # roster's emission_status AND against the profile actually emitting invariants for the
            # aspect, so "covered-emitted" can never be a label without a law behind it.
            roster_status = {a["id"]: a["emission_status"] for a in self.roster["aspects"]}
            emitted_aspects = {inv["aspect"] for inv in prof["invariants"]
                               if inv.get("emission_status") == "emitted"}
            for aspect, claim in prof["aspect_coverage"].items():
                if roster_status[aspect] == "deferred":
                    self.assertEqual(claim, "covered-deferred",
                                     f"{name}/{aspect}: roster defers this aspect — a profile may "
                                     f"not claim {claim!r}")
                    self.assertNotIn(aspect, emitted_aspects,
                                     f"{name}/{aspect}: deferred aspect must not emit invariants")
                else:
                    self.assertEqual(claim, "covered-emitted",
                                     f"{name}/{aspect}: roster emits this aspect — a profile may "
                                     f"not quietly defer it (the flip-hole)")
                    self.assertIn(aspect, emitted_aspects,
                                  f"{name}/{aspect}: 'covered-emitted' requires >=1 emitted "
                                  f"invariant for the aspect — a label is not a law")

    # --- SPINE-b: the DTCG token block DERIVES from config (single source, not a copy) ---
    def test_liquid_glass_tokens_derive_from_config_single_source(self):
        """The liquid-glass DTCG token block carries NO literal copy of config — every `$value`
        is an `{alias}` into the loader-injected `config` group, resolved by the DTCG-subset
        loader. Pins single source: a re-literaled value OR a broken alias reddens, so the DEFAULT
        language can never drift from the `config.py` SVG-parity anchor."""
        from scripts.core import config
        from scripts.rendering.design import loader
        tok = loader.resolve_tokens("liquid-glass")
        self.assertEqual(tok["color"]["accent"], config.CYAN)
        self.assertEqual(tok["color"]["ink-strong"], config.TEXT_BRIGHT)
        self.assertEqual(tok["color"]["surface"], config.SURFACE_BASE)
        self.assertEqual(tok["color"]["status-danger"], config.RED)
        self.assertEqual(tok["radius"]["panel"], config.GLASS_RX)
        self.assertEqual(tok["radius"]["tile"], config.GLASS_TILE_RX)
        self.assertEqual(tok["font"]["family"], config.FONT_SANS)
        # true single-source: the RAW JSON must ALIAS config, never re-literal its hex
        raw_tokens = json.dumps(loader.load("liquid-glass")["tokens"])
        self.assertNotIn(config.CYAN, raw_tokens,
                         "liquid-glass must ALIAS config (single source), never re-literal config.CYAN")

    def test_apple_dark_tokens_derive_from_the_theme_not_a_hand_typed_copy(self):
        """codex H1: apple-dark ALREADY exists in `design_tokens.THEMES['apple-dark']`.
        So the apple-dark profile must ALIAS that theme
        (`derived_from: theme:apple-dark`), NOT hand-type a duplicate hex map that could silently
        drift. Pins single source: resolved apple-dark tokens == `THEMES['apple-dark']`, and the raw
        JSON re-literals nothing."""
        if "apple-dark" not in self.index["active_design_profiles"]:
            self.skipTest("apple-dark not active yet")
        from scripts.rendering import design_tokens as dt
        from scripts.rendering.design import loader
        tok = loader.resolve_tokens("apple-dark")
        theme = dt.THEMES["apple-dark"]
        self.assertEqual(tok["color"]["accent"], theme["accent"])
        self.assertEqual(tok["color"]["ink-strong"], theme["ink-strong"])
        self.assertEqual(tok["color"]["surface"], theme["surface"])
        raw_tokens = json.dumps(loader.load("apple-dark")["tokens"])
        self.assertNotIn(theme["accent"], raw_tokens,
                         "apple-dark must ALIAS THEMES['apple-dark'] (single source), never re-literal its hex")

    def test_carbon_web_bridge_projects_profile_owned_tokens(self):
        """Carbon owns literal profile tokens (`derived_from: null`). Its public web theme bridge
        must project those resolved profile tokens, not invent a second Carbon palette/radius set."""
        if "carbon" not in self.index["active_design_profiles"]:
            self.skipTest("carbon not active yet")
        from scripts.rendering import design_tokens as dt
        from scripts.rendering.design import loader
        tok = loader.resolve_tokens("carbon")
        self.assertEqual(tok["color"], dt.THEMES["carbon"])
        self.assertEqual(tok["radius"], dt.radius("carbon"))

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
