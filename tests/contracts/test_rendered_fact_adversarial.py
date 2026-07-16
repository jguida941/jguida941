"""Adversarial W4 mutations for selector, geometry, and visible-content proof surfaces."""
from __future__ import annotations

import copy
import hashlib
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from pathlib import Path


def _root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "contracts" / "rendered_fact_policy.json").is_file():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _root()


def _rehash(entry: dict) -> None:
    from scripts.quality.rendered_facts.schema import compressed_packet_bytes, packet_bytes

    canonical = packet_bytes(entry["facts"])
    entry["provenance"]["content_sha256"] = hashlib.sha256(canonical).hexdigest()
    entry["provenance"]["artifact_sha256"] = hashlib.sha256(
        compressed_packet_bytes(entry["facts"])
    ).hexdigest()


def _set_box(box: dict, *, left: float, top: float, width: float, height: float) -> None:
    box.update({"x": left, "left": left, "right": left + width, "width": width,
                "y": top, "top": top, "bottom": top + height, "height": height})


def _active_pseudo(pseudo: dict, **overrides: str) -> None:
    row = {
        "content": '\"\"', "display": "block", "opacity": "1", "color": "rgb(0, 0, 0)",
        "background_color": "rgba(0, 0, 0, 0)", "background_image": "none",
        "filter": "none", "backdrop_filter": "none", "mix_blend_mode": "normal",
        "border_image_source": "none", "outline_width": "0px", "outline_style": "none",
        "outline_color": "rgb(0, 0, 0)", "box_shadow": "none", "clip_path": "none",
        "mask_image": "none",
    }
    for side in ("top", "right", "bottom", "left"):
        row.update({f"border_{side}_width": "0px", f"border_{side}_style": "none",
                    f"border_{side}_color": "rgb(0, 0, 0)"})
    row.update(overrides)
    pseudo.clear()
    pseudo.update(row)


class RenderedFactAdversarial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.quality.rendered_facts.policy import active_profiles, load_policy
        from scripts.quality.rendered_facts.schema import load_bundle

        cls.theme = active_profiles()[0]
        cls.policy = load_policy()
        cls.bundle = load_bundle(cls.theme)

    @classmethod
    def tearDownClass(cls):
        del cls.bundle

    def _mutant(self, *, page: str = "index", viewport: int = 390) -> tuple[list[dict], dict]:
        bundle = list(self.bundle)
        position = next(index for index, entry in enumerate(bundle)
                        if entry["facts"]["page"] == page
                        and entry["facts"]["viewport"]["width"] == viewport)
        bundle[position] = copy.deepcopy(bundle[position])
        return bundle, bundle[position]

    def _reject_bundle(self, mutate, *, page: str = "index") -> None:
        from scripts.quality.rendered_facts.schema import validate_packet

        _, entry = self._mutant(page=page)
        mutate(entry["facts"])
        with self.assertRaises(RuntimeError):
            validate_packet(
                entry["facts"], page=page, theme=self.theme,
                viewport=entry["facts"]["viewport"]["width"],
            )

    def _predicate_red(self, name: str, mutate) -> None:
        from scripts.contracts import rendered_predicates
        from scripts.quality.rendered_facts.schema import validate_packet

        _, entry = self._mutant()
        mutate(entry["facts"])
        validate_packet(entry["facts"], page="index", theme=self.theme, viewport=390)
        self.assertFalse(getattr(rendered_predicates, name)([entry], policy=self.policy))

    def _all_predicates_red(self, mutate) -> None:
        from scripts.contracts import rendered_predicates
        from scripts.quality.rendered_facts.schema import validate_packet

        _, entry = self._mutant()
        mutate(entry["facts"])
        validate_packet(entry["facts"], page="index", theme=self.theme, viewport=390)
        for name in (
            "rendered_contrast", "rendered_touch_targets",
            "rendered_responsive", "rendered_content_density",
        ):
            with self.subTest(predicate=name):
                self.assertFalse(getattr(rendered_predicates, name)(
                    [entry], policy=self.policy))

    def test_closed_selector_language_accepts_only_the_governed_dsl(self):
        from scripts.quality.rendered_facts.subject_identity import (
            compile_selector, compiled_policy,
        )

        compiled_policy(self.policy)
        rejected = [
            "main > button", "main button", "#save", "button:hover", ":not(.quiet)",
            "[role^=button]", "[role=button i]", "[role='button']", ".bad\\:class", "button,",
        ]
        for selector in rejected:
            with self.subTest(selector=selector), self.assertRaises(RuntimeError):
                compile_selector(selector, lane="interactive")

    def test_subject_membership_and_state_dom_identity_cannot_be_rebound(self):
        def interactive_swap(packet):
            indices = packet["subjects"]["interactive"]
            replacement = next(index for index in range(len(packet["nodes"]))
                               if index not in indices)
            indices[0] = replacement

        def contrast_swap(packet):
            packet["subjects"]["contrast"]["shell-title"] = list(
                packet["subjects"]["contrast"]["shell-intro"])

        def density_swap(packet):
            selector = next(iter(packet["subjects"]["density"]))
            indices = packet["subjects"]["density"][selector]
            replacement = next(index for index in range(len(packet["nodes"]))
                               if index not in indices)
            indices[0] = replacement

        def state_class_drift(packet):
            index = packet["subjects"]["contrast"]["shell-title"][0]
            row = packet["states"][0]["elements"][index]
            row["class"] = " ".join(
                name for name in row["class"].split() if name != "ps-title")

        def dom_drift(packet):
            packet["states"][0]["dom_identity_sha256"] = "0" * 64

        for label, mutation in (
            ("interactive", interactive_swap), ("contrast", contrast_swap),
            ("density", density_swap), ("state class", state_class_drift),
            ("DOM digest", dom_drift),
        ):
            with self.subTest(mutation=label):
                self._reject_bundle(mutation)

    def test_numeric_and_leaf_domains_reject_fake_geometry(self):
        from scripts.quality.rendered_facts.schema import validate_packet

        base = next(entry["facts"] for entry in self.bundle
                    if entry["facts"]["page"] == "index"
                    and entry["facts"]["viewport"]["width"] == 390)

        def element(packet):
            return packet["states"][0]["elements"][0]

        mutations = (
            ("bool width", lambda packet: element(packet)["box"].__setitem__("width", True)),
            ("nonfinite x", lambda packet: element(packet)["box"].__setitem__("x", float("nan"))),
            ("inconsistent right", lambda packet: element(packet)["box"].__setitem__(
                "right", element(packet)["box"]["right"] + 10)),
            ("negative width", lambda packet: element(packet)["box"].__setitem__("width", -1)),
            ("bool scroll", lambda packet: element(packet)["scroll"].__setitem__(
                "client_width", True)),
            ("bool DPR", lambda packet: packet["viewport"].__setitem__(
                "device_scale_factor", True)),
            ("numeric style", lambda packet: element(packet)["computed"].__setitem__(
                "opacity", 1)),
            ("nonbool hidden", lambda packet: element(packet).__setitem__("hidden", 1)),
            ("false rect count", lambda packet: element(packet).__setitem__("rect_count", 0)),
        )
        for label, mutation in mutations:
            payload = copy.deepcopy(base)
            mutation(payload)
            with self.subTest(mutation=label), self.assertRaises((RuntimeError, ValueError)):
                validate_packet(payload, page="index", theme=self.theme, viewport=390)

    def test_touch_geometry_rejects_large_neighbor_and_clipping_laundering(self):
        def near_large_neighbor(packet):
            state = packet["states"][0]
            buttons = [index for index in packet["subjects"]["interactive"]
                       if packet["nodes"][index]["tag"] == "button"]
            first, second = buttons[:2]
            _set_box(state["elements"][first]["box"], left=95, top=95, width=10, height=10)
            _set_box(state["elements"][second]["box"], left=111, top=80, width=100, height=44)

        def clipped_target(packet):
            state = packet["states"][0]
            target = next(index for index in packet["subjects"]["interactive"]
                          if packet["nodes"][index]["tag"] == "button")
            parent = packet["nodes"][target]["parent_index"]
            observed = state["elements"][parent]
            observed["computed"]["overflow_x"] = "hidden"
            observed["computed"]["overflow_y"] = "hidden"
            observed["scroll"]["client_width"] = 1
            observed["scroll"]["client_height"] = 1
            _set_box(observed["box"], left=observed["box"]["left"],
                     top=observed["box"]["top"], width=1, height=1)

        self._predicate_red("rendered_touch_targets", near_large_neighbor)
        self._predicate_red("rendered_touch_targets", clipped_target)

    def test_css_hidden_input_requires_a_governed_visible_label(self):
        from scripts.quality.rendered_facts.subject_identity import dom_identity_sha256

        def idless_hidden_input(packet):
            state = packet["states"][0]
            index = next(index for index in packet["subjects"]["interactive"]
                         if packet["nodes"][index]["tag"] == "button")
            node = packet["nodes"][index]
            node.update({"tag": "input", "type": "text", "id": "", "href": ""})
            observed = state["elements"][index]
            observed.update({"hidden": True, "rect_count": 0})
            observed["computed"]["display"] = "none"
            _set_box(observed["box"], left=0, top=0, width=0, height=0)
            digest = dom_identity_sha256(packet["nodes"], packet["text_nodes"], self.policy)
            for candidate in packet["states"]:
                candidate["dom_identity_sha256"] = digest

        self._predicate_red("rendered_touch_targets", idless_hidden_input)

    def test_touch_rejects_an_unmeasured_pseudo_target(self):
        def zero_box_pseudo_target(packet):
            state = packet["states"][0]
            index = next(index for index in packet["subjects"]["interactive"]
                         if packet["nodes"][index]["tag"] == "button")
            observed = state["elements"][index]
            observed["rect_count"] = 0
            _set_box(observed["box"], left=100, top=100, width=0, height=0)
            _active_pseudo(
                observed["pseudo"]["before"], background_color="rgb(0, 0, 0)")

        self._predicate_red("rendered_touch_targets", zero_box_pseudo_target)

    def test_touch_intersects_target_geometry_with_the_viewport(self):
        def viewport_sliver(packet):
            state = packet["states"][0]
            buttons = [index for index in packet["subjects"]["interactive"]
                       if packet["nodes"][index]["tag"] == "button"]
            first, second = buttons[:2]
            top = state["elements"][first]["box"]["top"]
            _set_box(state["elements"][first]["box"], left=389, top=top,
                     width=100, height=44)
            _set_box(state["elements"][second]["box"], left=364, top=top,
                     width=24, height=44)

        self._predicate_red("rendered_touch_targets", viewport_sliver)

    def test_opaque_contrast_scope_rejects_translucent_foreground(self):
        def translucent_title(packet):
            subject = packet["subjects"]["contrast"]["shell-title"][0]
            packet["states"][0]["elements"][subject]["computed"].update({
                "color": "rgba(255, 255, 255, 0.5)",
                "webkit_text_fill_color": "rgba(255, 255, 255, 0.5)",
            })

        self._predicate_red("rendered_contrast", translucent_title)

    def test_same_action_targets_cannot_overlap_or_skip_spacing(self):
        def overlapping_same_href(packet):
            groups = {}
            for index in packet["subjects"]["interactive"]:
                href = packet["nodes"][index]["href"]
                if href:
                    groups.setdefault(href, []).append(index)
            first, second = next(indices for indices in groups.values() if len(indices) == 2)
            state = packet["states"][0]
            _set_box(state["elements"][first]["box"], left=100, top=100,
                     width=5, height=5)
            _set_box(state["elements"][second]["box"], left=100, top=100,
                     width=5, height=5)

        self._predicate_red("rendered_touch_targets", overlapping_same_href)

    def test_document_roots_close_global_visibility_and_paint(self):
        from scripts.contracts.rendered.common import document_clear

        expected = {
            "box", "client_width", "client_height", "scroll_width", "scroll_height",
            "rect_count", "hidden", "computed", "pseudo",
        }
        for entry in self.bundle:
            for state in entry["facts"]["states"]:
                for name in ("root", "body"):
                    self.assertEqual(set(state["document"][name]), expected)

        _, entry = self._mutant()
        state = entry["facts"]["states"][0]
        state["document"]["root"]["hidden"] = True
        self.assertTrue(
            document_clear(state),
            "a raw hidden attribute is not rendered-hidden when computed CSS overrides it",
        )

        mutations = (
            ("body opacity", "body", "opacity", "0"),
            ("root filter", "root", "filter", "blur(2px)"),
            ("body clipping", "body", "clip_path", "inset(0 0 100% 0)"),
        )
        for label, root_name, field, value in mutations:
            def mutate(packet, root_name=root_name, field=field, value=value):
                packet["states"][0]["document"][root_name]["computed"][field] = value
            with self.subTest(mutation=label):
                self._all_predicates_red(mutate)

    def test_document_overflow_clipping_cannot_launder_visibility(self):
        def clipped_body(packet):
            body = packet["states"][0]["document"]["body"]
            body["computed"]["overflow_y"] = "hidden"
            body["client_height"] = 1
            _set_box(body["box"], left=body["box"]["left"], top=body["box"]["top"],
                     width=body["box"]["width"], height=1)

        self._all_predicates_red(clipped_body)

    def test_css_visibility_overrides_cannot_launder_offscreen_content(self):
        def overridden_hidden_attribute(packet):
            state = packet["states"][0]
            subject = packet["subjects"]["contrast"]["shell-title"][0]
            row = state["elements"][subject]
            row["hidden"] = True
            row["computed"].update({"display": "block", "visibility": "visible"})
            _set_box(row["box"], left=500, top=row["box"]["top"], width=100,
                     height=row["box"]["height"])

        self._predicate_red("rendered_responsive", overridden_hidden_attribute)

    def test_document_bounds_and_nearest_scroll_ancestor_are_closed(self):
        def shifted_root(packet):
            box = packet["states"][0]["document"]["root"]["box"]
            _set_box(box, left=-50, top=box["top"], width=390, height=box["height"])

        def unapproved_inner_scroller(packet):
            state = packet["states"][0]
            grid = next(index for index, row in enumerate(state["elements"])
                        if "db-calendar-grid" in row["class"].split())
            observed = state["elements"][grid]
            observed["computed"]["overflow_x"] = "auto"
            observed["scroll"]["client_width"] = max(1, observed["scroll"]["client_width"])
            observed["scroll"]["scroll_width"] = observed["scroll"]["client_width"] + 100

        def unapproved_inner_clip(packet):
            state = packet["states"][0]
            grid = next(index for index, row in enumerate(state["elements"])
                        if "db-calendar-grid" in row["class"].split())
            state["elements"][grid]["computed"]["overflow_x"] = "hidden"

        self._predicate_red("rendered_responsive", shifted_root)
        self._predicate_red("rendered_responsive", unapproved_inner_scroller)
        self._predicate_red("rendered_responsive", unapproved_inner_clip)

    def test_responsive_requires_a_horizontal_escape_paint_boundary(self):
        def unbounded_shadow(packet):
            state = packet["states"][0]
            target = next(index for index, row in enumerate(state["elements"])
                          if "db-score-ring" in row["class"].split())
            state["elements"][target]["computed"]["box_shadow"] = (
                "0 0 500px 500px rgb(0, 0, 0)")
            current = packet["nodes"][target]["parent_index"]
            while current is not None:
                state["elements"][current]["computed"].update({
                    "contain": "none", "overflow_x": "visible", "overflow_y": "visible",
                })
                current = packet["nodes"][current]["parent_index"]

        self._predicate_red("rendered_responsive", unbounded_shadow)

    def test_capture_inputs_name_runtime_and_dashboard_authorities(self):
        from scripts.quality.rendered_facts.policy import digest, input_hashes

        inputs = input_hashes("index", self.theme)
        self.assertEqual(
            inputs["headless_runtime_sha256"], digest("scripts/quality/headless_receipts.py"))
        self.assertEqual(
            inputs["dashboard_surface_sha256"], digest("contracts/dashboard_surface.json"))
        self.assertEqual(
            inputs["rendered_doctrine_sha256"], digest("docs/design/pageshell.md"))
        self.assertEqual(
            inputs["settings_admissibility_sha256"],
            digest("scripts/quality/settings_admissibility.py"),
        )
        self.assertEqual(
            inputs["state_authority_sha256"],
            digest("scripts/quality/rendered_facts/state_authority.py"),
        )
        self.assertIsNone(input_hashes("showcase", self.theme)["dashboard_surface_sha256"])

        def stale_runtime(packet):
            packet["inputs"]["headless_runtime_sha256"] = "0" * 64

        def stale_dashboard(packet):
            packet["inputs"]["dashboard_surface_sha256"] = "0" * 64

        self._reject_bundle(stale_runtime)
        self._reject_bundle(stale_dashboard)

    def test_physical_artifact_inventory_is_closed(self):
        from scripts.quality.rendered_facts import inventory
        from scripts.quality.rendered_facts.inventory import (
            expected_artifact_inventory, validate_artifact_inventory,
        )

        expected = expected_artifact_inventory()
        self.assertEqual(len(expected), 48)
        validate_artifact_inventory(expected)
        with self.assertRaises(RuntimeError):
            validate_artifact_inventory(
                expected | {"assets/receipts/pages/index/rendered-facts-old-theme-999.json.gz"})
        with self.assertRaises(RuntimeError):
            validate_artifact_inventory(set(sorted(expected)[1:]))

        with TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            pages = temporary_root / "assets" / "receipts" / "pages"
            for page in inventory.page_routes():
                (pages / page).mkdir(parents=True)
            nested = pages / "index" / "nested" / "rendered-facts-rogue.json.gz"
            unknown = pages / "unknown" / "rendered-facts-rogue.json.gz"
            staged = pages / "index" / ".rendered-facts-rogue.json.gz.dead.tmp"
            nested.parent.mkdir(parents=True)
            unknown.parent.mkdir(parents=True)
            nested.write_bytes(b"rogue")
            unknown.write_bytes(b"rogue")
            staged.write_bytes(b"interrupted")
            with mock.patch.object(inventory, "root", return_value=temporary_root):
                observed = inventory.observed_artifact_inventory()
            self.assertIn(nested.relative_to(temporary_root).as_posix(), observed)
            self.assertIn(unknown.relative_to(temporary_root).as_posix(), observed)
            self.assertIn(staged.relative_to(temporary_root).as_posix(), observed)

if __name__ == "__main__":
    unittest.main()
