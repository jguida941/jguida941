"""W4 rendered-facts RED: Chrome facts become a closed conformance input.

The producer owns observation only. This contract closes its page/theme/viewport matrix and raw
schema; the predicate library alone decides contrast, target size, containment, and density.
"""
from __future__ import annotations

import ast
import copy
import gzip
import hashlib
import importlib
import io
import json
import unittest
from pathlib import Path
from unittest import mock


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "contracts" / "repo_layout.json").is_file():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
ADMITTED_POLICY_SHA256 = "edc8e01d7b6f61a2211d6fcfab58acf3f0e177c2ca47ca4092dd52d2f368c2c9"


def _canonical_gzip(raw: bytes, *, compresslevel: int = 9) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(
        filename="", mode="wb", compresslevel=compresslevel, fileobj=output, mtime=0
    ) as archive:
        archive.write(raw)
    return output.getvalue()


def _rehash(entry: dict) -> None:
    from scripts.quality.rendered_facts.schema import compressed_packet_bytes, packet_bytes

    canonical = packet_bytes(entry["facts"])
    entry["provenance"]["content_sha256"] = hashlib.sha256(canonical).hexdigest()
    entry["provenance"]["artifact_sha256"] = hashlib.sha256(
        compressed_packet_bytes(entry["facts"])
    ).hexdigest()


def _imports(source: str) -> set[str]:
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def _group(group_id: str) -> dict:
    layout = json.loads((ROOT / "contracts" / "repo_layout.json").read_text(encoding="utf-8"))
    groups = layout["structural_layout"]["source_layout"]["groups"]
    return next(group for group in groups if group["id"] == group_id)


def _rendered_group() -> dict:
    return _group("rendered-facts")


class RenderedFactsRed(unittest.TestCase):
    def test_closed_policy_and_matrix_api_exist(self):
        policy_path = ROOT / "contracts" / "rendered_fact_policy.json"
        self.assertTrue(policy_path.is_file(), "W4 RED: rendered fact policy has not landed")
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        self.assertEqual(policy.get("contract_id"), "RenderedFactPolicy")

        from scripts.quality import headless_receipts

        self.assertTrue(
            hasattr(headless_receipts, "rendered_facts_artifact"),
            "W4 RED: rendered-facts artifact matrix API has not landed",
        )
        self.assertTrue(
            hasattr(headless_receipts, "write_all_rendered_facts"),
            "W4 RED: rendered-facts Chrome producer has not landed",
        )

    def test_policy_closes_the_exact_matrix_and_verdict_free_fields(self):
        policy = json.loads((ROOT / "contracts" / "rendered_fact_policy.json").read_text(
            encoding="utf-8"))
        manifest = json.loads((ROOT / "contracts" / "page_manifest.json").read_text(
            encoding="utf-8"))
        profiles = json.loads((ROOT / "contracts" / "design_profiles" / "_index.json").read_text(
            encoding="utf-8"))
        self.assertEqual([row["width"] for row in policy["matrix"]["viewports"]], [1280, 390])
        self.assertEqual(policy["matrix"]["page_source"], "contracts/page_manifest.json#/pages")
        self.assertEqual(
            policy["matrix"]["profile_source"],
            "contracts/design_profiles/_index.json#/active_design_profiles",
        )
        self.assertEqual(len(manifest["pages"]), 4)
        self.assertEqual(len(profiles["active_design_profiles"]), 3)
        self.assertEqual(policy["readiness"]["settle"]["mechanism"],
                         "forced-style-layout-task-turn")
        self.assertEqual(policy["readiness"]["settle"]["turns"], 2)
        encoding = policy["artifact_encoding"]
        self.assertEqual((encoding["extension"], encoding["compression"], encoding["members"]),
                         (".json.gz", "gzip", 1))
        self.assertEqual((encoding["filename"], encoding["mtime"]), ("", 0))
        self.assertEqual(
            (encoding["compresslevel"], encoding["header_flags"],
             encoding["header_xfl"], encoding["header_os"]),
            (9, 0, 2, 255),
        )
        self.assertGreaterEqual(encoding["max_uncompressed_bytes"], 40 * 1024 * 1024)
        self.assertEqual(policy["density_surfaces"]["studio"][0]["visible_count"], 1)
        self.assertEqual(
            policy["enumeration"]["same_origin_href_encoding"],
            "path-query-fragment",
        )

    def test_every_predicate_affecting_policy_value_is_independently_pinned(self):
        from scripts.quality.rendered_facts.doctrine import (
            ADMITTED_POLICY_SHA256 as CODE_PIN,
            policy_doctrine_sha256,
            validate_policy_doctrine,
        )

        policy = json.loads((ROOT / "contracts" / "rendered_fact_policy.json").read_text(
            encoding="utf-8"))
        self.assertEqual(CODE_PIN, ADMITTED_POLICY_SHA256)
        self.assertEqual(policy_doctrine_sha256(policy), ADMITTED_POLICY_SHA256)
        validate_policy_doctrine(policy)
        mutations = (
            lambda row: row["predicate_parameters"].__setitem__(
                "touch_minimum_css_px", 1),
            lambda row: row["predicate_parameters"].__setitem__(
                "rounding_tolerance_device_px", 999),
            lambda row: row["contrast_subjects"][0].__setitem__("minimum_ratio", 1),
            lambda row: row["allowed_scroll_containers"]["index"].clear(),
            lambda row: row["density_surfaces"]["index"][0].__setitem__(
                "allowed_gap_values", ["normal", "999px"]),
            lambda row: row.__setitem__("interactive_selector", "a[href]"),
        )
        for mutation in mutations:
            candidate = copy.deepcopy(policy)
            mutation(candidate)
            with self.subTest(mutation=mutation), self.assertRaises(RuntimeError):
                validate_policy_doctrine(candidate)

    def test_deterministic_gzip_envelope_is_single_member_and_canonical(self):
        from scripts.quality.rendered_facts.schema import (
            compressed_packet_bytes,
            decode_packet_bytes,
        )

        payload = {"z": [3, 2, 1], "a": {"truth": True}}
        first = compressed_packet_bytes(payload)
        second = compressed_packet_bytes(payload)
        self.assertEqual(first, second)
        self.assertEqual(first[:10], b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff")
        self.assertEqual(decode_packet_bytes(first), payload)

    def test_decoder_rejects_ambiguous_truncated_noncanonical_and_oversized_inputs(self):
        from scripts.quality.rendered_facts import codec, schema

        payload = {"sample": "x" * 128}
        encoded = schema.compressed_packet_bytes(payload)
        malformed = {
            "concatenated member": encoded + encoded,
            "trailing bytes": encoded + b"tail",
            "truncated member": encoded[:-1],
            "noncanonical JSON": _canonical_gzip(json.dumps(payload).encode("utf-8")),
            "wrong compression level": _canonical_gzip(
                json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n",
                compresslevel=1,
            ),
            "nonmaximum compression": _canonical_gzip(
                json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n",
                compresslevel=6,
            ),
        }
        for label, artifact in malformed.items():
            with self.subTest(label=label), self.assertRaises(RuntimeError):
                schema.decode_packet_bytes(artifact)

        policy = copy.deepcopy(schema.load_policy())
        policy["artifact_encoding"]["max_uncompressed_bytes"] = 8
        with mock.patch.object(codec, "load_policy", return_value=policy):
            with self.assertRaisesRegex(RuntimeError, "uncompressed-byte cap"):
                schema.decode_packet_bytes(encoded)

    def test_policy_state_plan_is_the_exact_admissible_studio_space(self):
        from scripts.quality.rendered_facts import policy as rendered_policy
        from scripts.quality.rendered_facts.policy import active_profiles, state_plan
        from scripts.quality.settings_admissibility import admissible_space

        expected = []
        rows = admissible_space()
        for base in active_profiles():
            expected.append({
                "state_id": f"base:{base}", "base": base, "component": "button",
                "source": base, "variant": f"{base}-base",
            })
            for row in rows:
                if row["base"] != base or row["source"] == base or row["admissible"] is not True:
                    continue
                expected.append({
                    "state_id": f"base:{base}|swap:{row['component']}:{row['source']}",
                    "base": base, "component": row["component"], "source": row["source"],
                    "variant": f"{base}-{row['component']}-{row['source']}",
                })
        self.assertEqual(state_plan("studio"), expected)
        self.assertEqual(len(expected), 19)

        forged = copy.deepcopy(rendered_policy.load_policy())
        forged["state_plan"]["studio"]["states"] = forged["state_plan"]["studio"]["states"][:-1]
        with mock.patch.object(rendered_policy, "load_policy", return_value=forged):
            with self.assertRaisesRegex(RuntimeError, "admissible-space authority"):
                state_plan("studio")

    def test_semantic_package_respects_manifest_line_and_import_boundaries(self):
        group = _rendered_group()
        package = ROOT / "scripts" / group["target_dir"]
        module_policy = group["module_policy"]
        names = ["__init__.py", *group["members"]]
        self.assertEqual(set(names), set(module_policy["max_lines"]))
        for name in names:
            path = package / name
            source = path.read_text(encoding="utf-8")
            self.assertLessEqual(len(source.splitlines()), module_policy["max_lines"][name], name)
            observed = _imports(source)
            allowed = set(module_policy["allowed_internal_imports"][name])
            internal = {item for item in observed
                        if item.startswith("scripts.quality.rendered_facts")}
            self.assertEqual(set(), internal - allowed, f"{name}: unexpected internal edge")
            for prefix in module_policy["forbidden_import_prefixes"]:
                self.assertFalse(any(item == prefix or item.startswith(prefix + ".")
                                     for item in observed), f"{name}: forbidden edge {prefix}")

        facade = ROOT / "scripts" / module_policy["facade"]["path"]
        source = facade.read_text(encoding="utf-8")
        imports = {item for item in _imports(source)
                   if item.startswith("scripts.quality.rendered_facts")}
        self.assertEqual(imports, set(module_policy["facade"]["allowed_imports"]))
        functions = {node.name for node in ast.parse(source).body
                     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertTrue(set(module_policy["facade"]["exports"]) <= functions)

    def test_import_boundary_guard_has_a_negative_control(self):
        forged = _imports("from scripts.quality.design_invariants import conform\n")
        forbidden = _rendered_group()["module_policy"]["forbidden_import_prefixes"]
        self.assertTrue(any(item == prefix or item.startswith(prefix + ".")
                            for item in forged for prefix in forbidden))

    def test_rendered_predicates_are_a_bounded_semantic_package(self):
        group = _group("rendered-predicates")
        package = ROOT / "scripts" / group["target_dir"]
        module_policy = group["module_policy"]
        prefix = "scripts.contracts.rendered"
        for name in ["__init__.py", *group["members"]]:
            source = (package / name).read_text(encoding="utf-8")
            self.assertLessEqual(len(source.splitlines()), module_policy["max_lines"][name])
            internal = {item for item in _imports(source) if item.startswith(prefix)}
            self.assertEqual(
                internal - set(module_policy["allowed_internal_imports"][name]), set(), name)
        facade_policy = module_policy["facade"]
        facade = ROOT / "scripts" / facade_policy["path"]
        imports = {item for item in _imports(facade.read_text(encoding="utf-8"))
                   if item.startswith(prefix)}
        self.assertEqual(imports, set(facade_policy["allowed_imports"]))
        module = importlib.import_module("scripts.contracts.rendered_predicates")
        self.assertEqual(set(module.__all__), set(facade_policy["exports"]))


class RenderedFactsBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.quality.rendered_facts.policy import active_profiles
        from scripts.quality.rendered_facts.schema import load_bundle

        cls.theme = active_profiles()[0]
        cls.bundle = load_bundle(cls.theme)

    @classmethod
    def tearDownClass(cls):
        del cls.bundle

    def _mutant(self, *, page: str = "index", viewport: int = 390) -> tuple[list[dict], dict]:
        mutant = list(self.bundle)
        position = next(index for index, entry in enumerate(mutant)
                        if entry["facts"]["page"] == page
                        and entry["facts"]["viewport"]["width"] == viewport)
        mutant[position] = copy.deepcopy(mutant[position])
        return mutant, mutant[position]

    def test_committed_bundle_and_promoted_predicates_are_green(self):
        from scripts.contracts import rendered_predicates
        from scripts.quality.rendered_facts.policy import load_policy

        policy = load_policy()
        self.assertEqual(len(self.bundle), 8)
        self.assertEqual(sum(len(entry["facts"]["states"])
                             for entry in self.bundle), 44)
        for name in (
            "rendered_contrast",
            "rendered_touch_targets",
            "rendered_responsive",
            "rendered_content_density",
        ):
            with self.subTest(predicate=name):
                self.assertTrue(getattr(rendered_predicates, name)(self.bundle, policy=policy))

    def test_schema_matrix_state_and_provenance_mutations_red(self):
        from scripts.quality.rendered_facts.schema import load_bundle

        with self.assertRaisesRegex(RuntimeError, "exactly 8 cells"):
            load_bundle(self.theme, self.bundle[:-1])

        mutations = []
        mutant, entry = self._mutant()
        entry["facts"]["unknown"] = True
        _rehash(entry)
        mutations.append(("closed packet", mutant))

        mutant, entry = self._mutant()
        href_node = next(node for node in entry["facts"]["nodes"] if node["href"])
        href_node["href"] = "http://127.0.0.1:9999/site/index.html"
        _rehash(entry)
        mutations.append(("capture-origin-free identity", mutant))

        mutant, entry = self._mutant()
        entry["facts"]["states"][0]["elements"].pop()
        _rehash(entry)
        mutations.append(("full element vector", mutant))

        mutant, entry = self._mutant(page="studio")
        entry["facts"]["states"].pop()
        _rehash(entry)
        mutations.append(("reachable Studio states", mutant))

        mutant, entry = self._mutant()
        entry["facts"]["states"][0]["settle"]["animations"].append({
            "id": "mutation", "play_state": "running", "pending": False,
            "current_time": 1, "target": None,
        })
        _rehash(entry)
        mutations.append(("settled animations", mutant))

        mutant, entry = self._mutant()
        entry["provenance"]["content_sha256"] = "0" * 64
        mutations.append(("canonical content hash", mutant))

        for label, candidate in mutations:
            with self.subTest(label=label), self.assertRaises(RuntimeError):
                load_bundle(self.theme, candidate)

    def test_forged_gzip_runtime_and_fake_chrome_command_red(self):
        from scripts.quality.rendered_facts.schema import load_bundle, packet_bytes

        mutant, entry = self._mutant()
        forged = bytearray(_canonical_gzip(packet_bytes(entry["facts"]), compresslevel=1))
        forged[8] = 2
        entry["_artifact_bytes"] = bytes(forged)
        entry["provenance"]["artifact_sha256"] = hashlib.sha256(forged).hexdigest()
        entry["provenance"]["python_version"] = "forged"
        entry["provenance"]["zlib_version"] = "forged"
        entry["provenance"]["zlib_runtime_version"] = "forged"
        with self.assertRaises(RuntimeError):
            load_bundle(self.theme, mutant)

        mutant, entry = self._mutant()
        entry["provenance"]["command"] = ["fake", "--headless=new", "--dump-dom"]
        entry["provenance"]["chrome_version"] = "Google Chrome fake"
        with self.assertRaises(RuntimeError):
            load_bundle(self.theme, mutant)

        mutant, entry = self._mutant()
        entry["provenance"]["chrome_version"] = "Google Chrome 1.2.3.4"
        with self.assertRaises(RuntimeError):
            load_bundle(self.theme, mutant)

    def test_each_promoted_predicate_has_a_negative_control(self):
        from scripts.contracts import rendered_predicates
        from scripts.quality.rendered_facts.policy import load_policy
        from scripts.quality.rendered_facts.schema import validate_packet

        policy = load_policy()
        cases = []

        mutant, entry = self._mutant()
        packet = entry["facts"]
        subject = packet["subjects"]["contrast"]["shell-intro"][0]
        packet["states"][0]["elements"][subject]["computed"]["color"] = "rgba(0, 0, 0, 0)"
        cases.append(("contrast ratio", "rendered_contrast", mutant, entry))

        mutant, entry = self._mutant()
        packet = entry["facts"]
        subject = packet["subjects"]["contrast"]["shell-title"][0]
        packet["states"][0]["elements"][subject]["computed"]["font_size"] = "10px"
        cases.append(("large-text qualification", "rendered_contrast", mutant, entry))

        mutant, entry = self._mutant()
        packet = entry["facts"]
        subject = packet["subjects"]["contrast"]["shell-intro"][0]
        packet["states"][0]["elements"][subject]["computed"]["opacity"] = "0.1"
        cases.append(("paint opacity", "rendered_contrast", mutant, entry))

        mutant, entry = self._mutant()
        packet = entry["facts"]
        buttons = [index for index in packet["subjects"]["interactive"]
                   if packet["nodes"][index]["tag"] == "button"]
        first, second = buttons[:2]
        first_box = packet["states"][0]["elements"][first]["box"]
        second_box = packet["states"][0]["elements"][second]["box"]
        center_x = (second_box["left"] + second_box["right"]) / 2
        center_y = (second_box["top"] + second_box["bottom"]) / 2
        first_box.update({"x": center_x - 5, "left": center_x - 5,
                          "right": center_x + 5, "width": 10,
                          "y": center_y - 5, "top": center_y - 5,
                          "bottom": center_y + 5, "height": 10})
        cases.append(("undersized overlapping target", "rendered_touch_targets", mutant, entry))

        mutant, entry = self._mutant()
        packet = entry["facts"]
        subject = packet["subjects"]["contrast"]["shell-title"][0]
        box = packet["states"][0]["elements"][subject]["box"]
        box.update({"x": 450, "left": 450, "right": 550, "width": 100})
        cases.append(("offscreen element", "rendered_responsive", mutant, entry))

        mutant, entry = self._mutant()
        packet = entry["facts"]
        state = packet["states"][0]
        wrapper = next(index for index, row in enumerate(state["elements"])
                       if "db-calendar-scroll" in row["class"].split())
        descendant = next(index for index, node in enumerate(packet["nodes"])
                          if node["parent_index"] == wrapper)
        state["elements"][descendant]["box"].update(
            {"x": 450, "left": 450, "right": 550, "width": 100}
        )
        state["elements"][wrapper]["computed"]["overflow_x"] = "visible"
        state["elements"][wrapper]["box"].update(
            {"x": 0, "left": 0, "right": 0, "width": 0}
        )
        cases.append(("forged scroll exception", "rendered_responsive", mutant, entry))

        mutant, entry = self._mutant()
        packet = entry["facts"]
        contrast_subjects = {
            index for indices in packet["subjects"]["contrast"].values() for index in indices
        }

        def under(index, ancestor):
            while index is not None:
                if index == ancestor:
                    return True
                index = packet["nodes"][index]["parent_index"]
            return False

        text_index = next(
            index for index, row in enumerate(packet["text_nodes"])
            if row["parent_index"] is not None
            and packet["states"][0]["text_ranges"][index]["rects"]
            and not any(under(row["parent_index"], subject)
                        for subject in contrast_subjects)
        )
        packet["states"][0]["text_ranges"][text_index]["rects"][0].update(
            {"x": 450, "left": 450, "right": 550, "width": 100}
        )
        cases.append(("offscreen text range", "rendered_responsive", mutant, entry))

        mutant, entry = self._mutant()
        packet = entry["facts"]
        selector = next(iter(packet["subjects"]["density"]))
        subject = packet["subjects"]["density"][selector][0]
        packet["states"][0]["elements"][subject]["computed"]["padding_top"] = "999px"
        cases.append(("invented density padding", "rendered_content_density", mutant, entry))

        mutant, entry = self._mutant()
        packet = entry["facts"]
        selector = next(iter(packet["subjects"]["density"]))
        for subject in packet["subjects"]["density"][selector]:
            row = packet["states"][0]["elements"][subject]
            row["hidden"] = True
            row["computed"]["display"] = "none"
            row["rect_count"] = 0
            row["box"].update({
                "x": 0, "y": 0, "left": 0, "top": 0, "right": 0,
                "bottom": 0, "width": 0, "height": 0,
            })
        cases.append(("hidden density surface", "rendered_content_density", mutant, entry))

        for label, name, candidate, entry in cases:
            validate_packet(entry["facts"], page="index", theme=self.theme, viewport=390)
            with self.subTest(predicate=name, mutation=label):
                self.assertFalse(getattr(rendered_predicates, name)([entry], policy=policy))


if __name__ == "__main__":
    unittest.main()
