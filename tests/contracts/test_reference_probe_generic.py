"""W6-P — the universal engine's generic rendered-facts probe (RED-first).

`scripts/quality/reference_intake/probe_generic.py` measures EVERY visible aspect of
ANY served page: per subject (buttons/links/landmarks/card-clusters/heading-tuples) it
captures the computed-style vector across the §3.1 aspect families
(palette / typography / spacing / geometry / radius / border / shadow / material / motion),
the DOM structure (tag / role / attributes-of-interest), and the reachable pseudo-states
(:hover / :focus / :active via forced marker classes on the served copy).

This guard runs against a COMMITTED SYNTHETIC FIXTURE (`tests/fixtures/probe_pages/sample.html`)
so CI needs no network. It asserts: the probe finds the expected subjects; every aspect family
is a non-empty computed fact; the closed packet is deterministic (two runs byte-identical); and a
forced :hover state changes the recorded hover vector. If Chrome is unavailable the probe FAILS
HONESTLY — it never fabricates facts — and this suite surfaces that as an explicit failure.
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
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "probe_pages"
FIXTURE_PAGE = "sample.html"
VIEWPORT = (1024, 768)

# the eight computed-style families the probe must measure as non-empty facts.
COMPUTED_FAMILIES = ("palette", "type", "spacing", "geometry", "radius", "border", "shadow", "material", "motion")
EXPECTED_SUBJECT_KINDS = {"button", "link", "landmark", "card-cluster", "heading-tuple"}
# one representative aspect id per family — every one must land in aspects_measured.
FAMILY_REPRESENTATIVE_IDS = {
    "palette.color", "type.font-size", "spacing.padding", "geometry.box", "radius.border-radius",
    "border.width", "shadow.box-shadow", "material.backdrop-filter", "motion.transition",
}


class ReferenceProbeGenericContract(unittest.TestCase):
    packet: dict | None = None
    packet2: dict | None = None
    chrome_error: Exception | None = None

    @classmethod
    def setUpClass(cls) -> None:
        # RED-first: this import errors until scripts/quality/reference_intake/probe_generic.py exists.
        from scripts.quality.reference_intake import probe_generic

        cls.mod = probe_generic
        cls.chrome_available = probe_generic.chrome_available()
        if not cls.chrome_available:
            return
        # two independent runs — the determinism assertion compares their canonical bytes.
        cls.packet = probe_generic.probe(FIXTURE_DIR, target=FIXTURE_PAGE, viewport=VIEWPORT)
        cls.packet2 = probe_generic.probe(FIXTURE_DIR, target=FIXTURE_PAGE, viewport=VIEWPORT)

    def _packet(self) -> dict:
        if not self.chrome_available:
            self.fail("Chrome unavailable — the probe cannot capture real rendered facts; "
                      "failing honestly rather than fabricating a packet")
        assert self.packet is not None
        return self.packet

    def _subjects_by_kind(self, kind: str) -> list[dict]:
        return [s for s in self._packet()["subjects"] if s["kind"] == kind]

    def _first(self, kind: str) -> dict:
        subjects = self._subjects_by_kind(kind)
        self.assertTrue(subjects, f"probe found no {kind!r} subject in the fixture")
        return subjects[0]

    # --- the fixture yields the heuristic subject kinds ---

    def test_finds_expected_subject_kinds(self):
        kinds = {s["kind"] for s in self._packet()["subjects"]}
        self.assertTrue(
            EXPECTED_SUBJECT_KINDS.issubset(kinds),
            f"probe missed subject kinds {sorted(EXPECTED_SUBJECT_KINDS - kinds)} (found {sorted(kinds)})",
        )
        # the fixture nav holds exactly three links; the card cluster is the .cards container.
        self.assertGreaterEqual(len(self._subjects_by_kind("link")), 3)
        self.assertGreaterEqual(len(self._subjects_by_kind("card-cluster")), 1)

    # --- the packet is a CLOSED schema, exactly the declared envelope ---

    def test_packet_is_closed_schema(self):
        packet = self._packet()
        self.assertEqual(
            {"contract_id", "schema_version", "viewport", "subjects", "aspects_measured"},
            set(packet),
            "packet must be the closed ExternalReferenceRenderedFacts envelope — no extra/missing keys",
        )
        self.assertEqual("ExternalReferenceRenderedFacts", packet["contract_id"])
        self.assertEqual(1, packet["schema_version"])
        self.assertEqual({"width": VIEWPORT[0], "height": VIEWPORT[1]}, packet["viewport"])

    # --- every aspect family is a non-empty computed fact (by construction) ---

    def test_measures_each_aspect_family_as_nonempty_facts(self):
        # the button carries every family; check each is a present, populated computed dict whose
        # facts are strings and that carries at least one real (non-empty) measured value. (A single
        # UA-unsupported longhand alias — e.g. webkit-backdrop-filter on modern Chrome — may be "".)
        button = self._first("button")
        computed = button["computed"]
        for family in COMPUTED_FAMILIES:
            self.assertIn(family, computed, f"button subject missing computed family {family!r}")
            self.assertTrue(computed[family], f"button computed family {family!r} is empty")
            values = list(computed[family].values())
            for key, value in computed[family].items():
                self.assertIsInstance(value, str, f"{family}.{key} is not a string fact")
            self.assertTrue(any(v != "" for v in values),
                            f"button computed family {family!r} recorded no non-empty fact")

    def test_specific_computed_values_are_present(self):
        button = self._first("button")
        self.assertTrue(button["computed"]["type"]["font-size"].endswith("px"))
        self.assertTrue(button["computed"]["geometry"]["width"].endswith("px"))
        self.assertNotEqual("0px", button["computed"]["radius"]["border-top-left-radius"])

    # --- MATERIAL aspect: the backdrop-filter field (the mutation-check target) ---

    def test_material_backdrop_filter_is_captured(self):
        packet = self._packet()
        button = self._first("button")
        self.assertIn(
            "backdrop-filter", button["computed"]["material"],
            "material family must carry a backdrop-filter fact (the glass/material aspect)",
        )
        self.assertIn("material.backdrop-filter", packet["aspects_measured"])
        # the fixture's glass header must yield a real (non-'none') backdrop-filter somewhere.
        glassy = [s for s in packet["subjects"]
                  if s["computed"]["material"].get("backdrop-filter", "none") != "none"]
        self.assertTrue(
            glassy, "no subject recorded a real backdrop-filter — the material aspect is not truly measured",
        )
        self.assertTrue(any("blur" in s["computed"]["material"]["backdrop-filter"] for s in glassy))

    # --- DOM structure + reachable states are captured per subject ---

    def test_structure_and_states_are_captured(self):
        link = self._first("link")
        structure = link["structure"]
        self.assertEqual("a", structure["tag"])
        self.assertEqual("link", structure["role"])
        self.assertIn("href", structure["attributes"])
        for state in ("hover", "focus", "active"):
            self.assertIn(state, link["states"], f"missing reachable state {state!r}")
            self.assertTrue(link["states"][state], f"state {state!r} vector is empty")

    # --- the §3.1 aspect vocabulary: 31 ids, all families represented ---

    def test_aspect_vocabulary_and_measured_coverage(self):
        packet = self._packet()
        self.assertEqual(31, len(self.mod.ASPECT_VOCABULARY), "the §3.1 aspect vocabulary must have 31 ids")
        self.assertEqual(len(self.mod.ASPECT_VOCABULARY), len(set(self.mod.ASPECT_VOCABULARY)))
        measured = packet["aspects_measured"]
        self.assertEqual(measured, sorted(measured), "aspects_measured must be sorted (deterministic)")
        self.assertTrue(set(measured).issubset(set(self.mod.ASPECT_VOCABULARY)))
        self.assertTrue(
            FAMILY_REPRESENTATIVE_IDS.issubset(set(measured)),
            f"aspects_measured missing family reps {sorted(FAMILY_REPRESENTATIVE_IDS - set(measured))}",
        )

    # --- determinism: two runs are byte-identical ---

    def test_two_runs_are_byte_identical(self):
        if not self.chrome_available:
            self.fail("Chrome unavailable — cannot prove determinism honestly")
        assert self.packet is not None and self.packet2 is not None
        a = self.mod.canonical_json(self.packet)
        b = self.mod.canonical_json(self.packet2)
        self.assertEqual(a, b, "two probe runs are not byte-identical — the packet is non-deterministic")
        # and the canonical form round-trips through json unchanged (sorted, closed).
        self.assertEqual(a, self.mod.canonical_json(json.loads(a)))

    # --- a forced :hover state changes the recorded hover vector ---

    def test_forced_hover_changes_the_vector(self):
        button = self._first("button")
        rest_bg = button["computed"]["palette"]["background-color"]
        hover_bg = button["states"]["hover"]["palette"]["background-color"]
        self.assertNotEqual(
            rest_bg, hover_bg,
            "forced :hover did not change the button background — pseudo-state capture is not working",
        )


if __name__ == "__main__":
    unittest.main()
