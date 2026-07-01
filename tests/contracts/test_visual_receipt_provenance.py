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

    def test_every_committed_png_is_under_a_known_profile_dir(self):
        """Closed cover over the PNG receipts (debt c): every assets/receipts/**/*.png lives under a
        KNOWN design profile; a rogue-profile PNG would redden (anti-tautology below)."""
        known = set(_active())
        idx = json.loads((ROOT / "contracts" / "design_profiles" / "_index.json").read_text(encoding="utf-8"))
        known |= set(idx.get("reserved_design_profiles", []))
        pngs = list((ROOT / "assets" / "receipts").glob("**/*.png"))
        self.assertTrue(pngs, "there must be committed PNG receipts to govern")
        for png in pngs:
            self.assertIn(png.parent.name, known, f"{png}: PNG under an unknown profile dir")
        # anti-tautology: a rogue-profile dir is NOT known
        self.assertNotIn("rogue-profile", known)


if __name__ == "__main__":
    unittest.main()
