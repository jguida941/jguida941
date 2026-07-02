"""D-SHELL-2 (authority: page_manifest) — every page declares WHAT IT IS, fail-closed.

The manifest (contracts/page_manifest.json) is the DATA half of the page-archetype law: page id →
intent → archetype (CLOSED enum) → required regions. This contract checks the COMMITTED page bytes
as primary (gate MF-C: committed bytes are what ship; rendered==committed is held per page by the
four named drift guards — test_showcase_coverage / test_settings_composition / test_studio /
test_web_dashboard). The roster's `page-archetype` aspect stays DEFERRED with this file named as
its enforcement home (gate Q1 fallback: a site-scoped fact surfaced per profile would fake
per-language proof). candidate_only.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


def _root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "contracts" / "page_manifest.json").is_file():
            return p
    raise RuntimeError("repo root not found")


ROOT = _root()


def _manifest() -> dict:
    return json.loads((ROOT / "contracts" / "page_manifest.json").read_text(encoding="utf-8"))


def _region_present(alias: str, page_bytes: str) -> bool:
    """The CLOSED alias grammar (gate SF-3): '.class-token' -> a class attribute carrying the
    token; '[data-attr]' -> the attribute appears. ANYTHING else raises (fail-closed)."""
    if re.fullmatch(r"\.[\w-]+", alias):
        return bool(re.search(rf'class="[^"]*\b{re.escape(alias[1:])}\b', page_bytes))
    if re.fullmatch(r"\[data-[\w-]+\]", alias):
        return f'{alias[1:-1]}=' in page_bytes
    raise ValueError(f"unparseable region alias {alias!r} — allowed: '.class-token' | '[data-attr]'")


class PageManifestContract(unittest.TestCase):
    def test_manifest_covers_exactly_the_shipped_pages_both_directions(self):
        """Closed cover: manifest ids == the receipts page allowlist == headless_receipts routes ==
        the site html allowlist (three-way parity, gate SF-3a). A page shipped without declaring
        what it IS — or declared without shipping — reddens."""
        from scripts.quality.headless_receipts import PAGE_ROUTES
        man = _manifest()
        ids = [p["id"] for p in man["pages"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate page ids")
        layout = json.loads((ROOT / "contracts" / "repo_layout.json").read_text(encoding="utf-8"))
        allow = layout["structural_layout"]["receipts_layout"]["page_allowlist"]
        self.assertEqual(set(ids), set(allow), "manifest ids != receipts page_allowlist")
        self.assertEqual(set(ids), set(PAGE_ROUTES), "manifest ids != headless_receipts.PAGE_ROUTES")
        for p in man["pages"]:
            self.assertEqual(p["route"], PAGE_ROUTES[p["id"]], f"{p['id']}: route parity")

    def test_every_page_declares_a_valid_archetype_and_intent(self):
        man = _manifest()
        enum = man["archetypes"]
        self.assertEqual(set(enum), {"landing", "proof-report", "control-plane", "workbench"},
                         "the archetype enum is CLOSED (ratified MF2)")
        for p in man["pages"]:
            self.assertIn(p["archetype"], enum, f"{p['id']}: archetype outside the closed enum")
            self.assertTrue(p["intent"].strip(), f"{p['id']}: intent must be a real sentence")
            self.assertTrue(p["required_regions"], f"{p['id']}: an archetype requires regions")

    def test_required_regions_are_present_in_the_committed_page_bytes(self):
        """The archetype's regions exist in what SHIPS (committed bytes primary, gate MF-C).
        Fail-closed: a missing page file or an alias-less region reddens."""
        for p in _manifest()["pages"]:
            page = ROOT / p["route"]
            self.assertTrue(page.is_file(), f"{p['id']}: committed page missing")
            page_bytes = page.read_text(encoding="utf-8")
            for region in p["required_regions"]:
                alias = p["region_aliases"].get(region)
                self.assertTrue(alias, f"{p['id']}/{region}: region without an alias (fail-closed)")
                self.assertTrue(_region_present(alias, page_bytes),
                                f"{p['id']}: required region {region!r} ({alias}) not in shipped bytes")

    def test_bogus_archetype_and_missing_region_redden(self):
        """Negative vectors (in-memory): the enum refuses an invented archetype; a region whose
        alias is absent from the html fails; an off-grammar alias raises."""
        enum = _manifest()["archetypes"]
        self.assertNotIn("hero-carousel", enum, "an invented archetype must not be admissible")
        self.assertFalse(_region_present(".not-there", '<div class="wrap">x</div>'))
        with self.assertRaises(ValueError):
            _region_present("div > .fancy:hover", "<div/>")

    def test_receipt_obligations_match_the_mf1_law(self):
        """Every page owes the two MF1 receipt kinds at the ratified viewports — and the committed
        receipts exist (produced + byte-pinned; deep validation lives in
        test_visual_receipt_provenance)."""
        from scripts.quality.headless_receipts import dom_probe_artifact, screenshot_artifact
        for p in _manifest()["pages"]:
            kinds = {(o["kind"], o["viewport"]) for o in p["receipt_obligations"]}
            self.assertEqual(kinds, {("chrome-headless-screenshot", 1280),
                                     ("chrome-headless-dom-probe", 390)},
                             f"{p['id']}: receipt obligations must match the MF1 law")
            self.assertTrue(screenshot_artifact(p["id"]).is_file(), f"{p['id']}: screenshot owed")
            self.assertTrue(dom_probe_artifact(p["id"]).is_file(), f"{p['id']}: dom probe owed")


if __name__ == "__main__":
    unittest.main()
