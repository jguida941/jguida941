"""P5-RECEIPT-PROVENANCE (authority: receipts) — a receipt may not overclaim its producer.

The visual-receipt gate must not wear a pixel-truth label it did not earn: the card "content-fills"
artifact is a TOKEN-DERIVED RECONSTRUCTION (a deterministic PIL redraw from the profile's tokens), NOT
a browser screenshot; the contrast artifact is a RENDERED-CSS contrast measurement, NOT a headless
browser probe. Each `receipt_obligation.kind` must name the ACTUAL producer, carry a provenance
sidecar, be reproducible (producer-drift guarded), and the PNGs must be governed by the closed cover.
Rows stay `candidate` throughout — this strips a proxy label, it never promotes a verdict.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path


def _repo_root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "scripts").is_dir() and (p / "contracts").is_dir():
            return p
    raise RuntimeError("repo root not found")


ROOT = _repo_root()


def _active() -> list[str]:
    idx = json.loads((ROOT / "contracts" / "design_profiles" / "_index.json").read_text(encoding="utf-8"))
    return idx["active_design_profiles"]


def _obligations():
    from scripts.rendering.design import loader
    for name in _active():
        for inv in loader.load(name).get("invariants", []):
            ob = inv.get("receipt_obligation") or {}
            if ob.get("required"):
                yield name, inv, ob


class ReceiptProvenanceContract(unittest.TestCase):
    def test_obligation_kinds_name_their_actual_producer(self):
        """No obligation may claim a capability its producer lacks: the reconstruction kind must not
        say 'screenshot'; the css-contrast kind must not say 'headless'. Every kind is in the honest
        allowlist (single-sourced from the producer module)."""
        from scripts.quality.visual_receipts import CARD_KIND, CONTRAST_KIND, HONEST_KINDS
        for name, inv, ob in _obligations():
            kind = ob.get("kind")
            self.assertIn(kind, HONEST_KINDS, f"{name}/{inv['invariant_id']}: kind {kind!r} not honest")
            text = " ".join([kind or "", ob.get("reason", ""), inv.get("refute_by", "")]).lower()
            if kind == CARD_KIND:
                self.assertNotIn("screenshot", text,
                                 f"{name}/{inv['invariant_id']}: a PIL reconstruction must not claim 'screenshot'")
            if kind == CONTRAST_KIND:
                self.assertNotIn("headless", text,
                                 f"{name}/{inv['invariant_id']}: a CSS-parse contrast must not claim 'headless'")

    def test_card_reconstruction_carries_an_honest_provenance_sidecar(self):
        """Each card PNG has a `<artifact>.provenance.json` sidecar declaring the real producer +
        candidate-only honesty fields — so the artifact cannot silently claim more than a redraw."""
        from scripts.quality.visual_receipts import CARD_KIND, provenance_path
        for name, inv, ob in _obligations():
            if ob.get("kind") != CARD_KIND:
                continue
            side = ROOT / provenance_path(ob["artifact"])
            self.assertTrue(side.is_file(), f"{name}/{inv['invariant_id']}: missing provenance sidecar {side}")
            data = json.loads(side.read_text(encoding="utf-8"))
            self.assertEqual(data["probe_backend"], "pil-reconstruction")
            self.assertEqual(data["authority_status"], "candidate_only")
            self.assertIs(data["cannot_mark_done"], True)
            self.assertEqual(data["producer"], "scripts/quality/visual_receipts.py")
            self.assertNotIn("screenshot", json.dumps(data).lower())

    def test_card_png_matches_its_producer_regenerated(self):
        """Producer-drift guard: regenerating the PNG must reproduce the committed one (structural
        summary — dims + per-channel mean + nonblank). Editing the producer without recommitting
        reddens here (the old format/dims/nonblank check stayed green — the pre-slice gap)."""
        import tempfile
        from scripts.quality.visual_receipts import (
            CARD_KIND, _draw_card_png, expected_visual_receipts, png_summary, png_tile_digest)
        for receipt in expected_visual_receipts():
            if receipt.kind != CARD_KIND:
                continue
            committed = ROOT / receipt.artifact
            self.assertTrue(committed.is_file(), f"{receipt.artifact}: missing committed PNG")
            with tempfile.TemporaryDirectory() as tmp:
                regen = Path(tmp) / "regen.png"
                _draw_card_png(receipt, regen)
                c, g = png_summary(committed), png_summary(regen)
                self.assertEqual((c["format"], c["width"], c["height"], c["nonblank"]),
                                 (g["format"], g["width"], g["height"], g["nonblank"]),
                                 f"{receipt.artifact}: PNG structure drift — regenerate via scripts.quality.visual_receipts")
                # SPATIAL tile digest (codex): a per-tile compare so a layout change that preserves
                # the global mean still reddens; small tolerance absorbs any cross-env AA jitter.
                ct, gt = png_tile_digest(committed), png_tile_digest(regen)
                self.assertEqual(len(ct), len(gt), f"{receipt.artifact}: tile grid mismatch")
                for i, (ctile, gtile) in enumerate(zip(ct, gt)):
                    for ch, (cm, gm) in enumerate(zip(ctile, gtile)):
                        self.assertAlmostEqual(cm, gm, delta=0.5,
                                               msg=f"{receipt.artifact}: tile {i} ch {ch} drift {cm} vs {gm} — regenerate")

    def test_every_committed_png_is_under_a_known_profile_or_page_dir(self):
        """Closed cover over PNG receipts: component PNGs live under a known profile; MF1 page
        screenshots live under the declared pages subtree."""
        from scripts.quality.headless_receipts import PAGE_ROUTES
        known = set(_active())
        idx = json.loads((ROOT / "contracts" / "design_profiles" / "_index.json").read_text(encoding="utf-8"))
        known |= set(idx.get("reserved_design_profiles", []))
        pngs = list((ROOT / "assets" / "receipts").glob("**/*.png"))
        self.assertTrue(pngs, "there must be committed PNG receipts to govern")
        for png in pngs:
            parts = png.relative_to(ROOT / "assets" / "receipts").parts
            if parts[0] == "pages":
                self.assertIn(parts[1], PAGE_ROUTES, f"{png}: PNG under an unknown page receipt dir")
            else:
                self.assertIn(parts[0], known, f"{png}: PNG under an unknown profile dir")
        # anti-tautology: a rogue-profile dir is NOT known
        self.assertNotIn("rogue-profile", known)
        self.assertNotIn("rogue-page", PAGE_ROUTES)

    def test_committed_headless_page_receipts_are_real_and_provenanced(self):
        """MF1: committed page receipts are real Chrome-headless artifacts. This test reads only
        committed files: screenshots are nonempty PNGs, sidecars name the honest kind/command, the
        probes MEASURED the viewport they claim (stand-in MF-1: a bare --window-size=390 silently
        measures at Chrome's ~500 minimum — the iframe probe must report client_width == 390), the
        sidecar pins the exact page bytes it captured (stand-in SF-2: a stale or hand-authored
        receipt reddens), and the design pages report no horizontal overflow at true 390."""
        import hashlib
        from scripts.quality.headless_receipts import (
            DESIGN_PAGES,
            DOM_PROBE_KIND,
            PAGE_ROUTES,
            SCREENSHOT_KIND,
            dom_probe_artifact,
            provenance_path,
            screenshot_artifact,
        )
        from scripts.quality.visual_receipts import png_summary

        for page in PAGE_ROUTES:
            screenshot = screenshot_artifact(page)
            self.assertTrue(screenshot.is_file(), f"{page}: missing page screenshot receipt")
            summary = png_summary(screenshot)
            self.assertEqual(summary["format"], "PNG", f"{page}: screenshot must be a PNG")
            self.assertGreater(summary["width"], 0, f"{page}: screenshot width")
            self.assertGreater(summary["height"], 0, f"{page}: screenshot height")
            self.assertTrue(summary["nonblank"], f"{page}: screenshot must be nonblank")

            page_sha = hashlib.sha256(
                (ROOT / PAGE_ROUTES[page]).read_bytes()).hexdigest()
            screenshot_sidecar = json.loads(provenance_path(screenshot).read_text(encoding="utf-8"))
            self.assertEqual(screenshot_sidecar["kind"], SCREENSHOT_KIND)
            self.assertIn("--headless=new", screenshot_sidecar["command"])
            self.assertTrue(screenshot_sidecar["chrome_version"].startswith("Google Chrome "))
            self.assertEqual(screenshot_sidecar["viewport"]["width"], 1280)
            self.assertEqual(screenshot_sidecar["page_sha256"], page_sha,
                             f"{page}: screenshot receipt is stale — reproduce via headless_receipts")

            probe = dom_probe_artifact(page)
            self.assertTrue(probe.is_file(), f"{page}: missing DOM probe receipt")
            data = json.loads(probe.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], DOM_PROBE_KIND)
            self.assertEqual(data["viewport"]["width"], 390)
            self.assertEqual(data["client_width"], 390,
                             f"{page}: the probe must MEASURE 390, not merely claim it")
            probe_sidecar = json.loads(provenance_path(probe).read_text(encoding="utf-8"))
            self.assertEqual(probe_sidecar["kind"], DOM_PROBE_KIND)
            self.assertIn("--headless=new", probe_sidecar["command"])
            self.assertEqual(probe_sidecar["page_sha256"], page_sha,
                             f"{page}: probe receipt is stale — reproduce via headless_receipts")
            if page in DESIGN_PAGES:
                self.assertIs(data["horizontal_overflow"], False,
                              f"{page}: 390px DOM probe overflowed: {data.get('offenders')}")


if __name__ == "__main__":
    unittest.main()
