"""Adversarial W4 controls for deterministic paint and contrast claims."""
from __future__ import annotations

import copy
import unittest

from tests.contracts import test_rendered_fact_adversarial as shared


class RenderedFactPaintAdversarial(unittest.TestCase):
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

    def _mutant(self) -> tuple[list[dict], dict]:
        bundle = list(self.bundle)
        position = next(index for index, entry in enumerate(bundle)
                        if entry["facts"]["page"] == "index"
                        and entry["facts"]["viewport"]["width"] == 390)
        bundle[position] = copy.deepcopy(bundle[position])
        return bundle, bundle[position]

    def _contrast_value(self, mutate) -> bool:
        from scripts.contracts.rendered_predicates import rendered_contrast
        from scripts.quality.rendered_facts.schema import validate_packet

        _, entry = self._mutant()
        mutate(entry["facts"])
        validate_packet(entry["facts"], page="index", theme=self.theme, viewport=390)
        return rendered_contrast([entry], policy=self.policy)

    def _red(self, mutate) -> None:
        self.assertFalse(self._contrast_value(mutate))

    def _all_red(self, mutate) -> None:
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

    def test_pseudo_and_sampled_top_layer_occlusion_red(self):
        def painted_empty_pseudo(packet):
            subject = packet["subjects"]["contrast"]["shell-title"][0]
            pseudo = packet["states"][0]["elements"][subject]["pseudo"]["before"]
            shared._active_pseudo(pseudo, background_color="rgb(0, 0, 0)")

        def foreign_hit(packet):
            state = packet["states"][0]
            subject = packet["subjects"]["contrast"]["shell-title"][0]
            hit = state["contrast_hits"]["shell-title"][0]["samples"][0]
            hit["top_index"] = next(index for index in range(len(packet["nodes"]))
                                    if index != subject)

        self._red(painted_empty_pseudo)
        self._red(foreign_hit)

    def test_empty_pseudo_strokes_and_regular_subject_effects_red(self):
        required = {
            "border_top_width", "border_top_style", "border_top_color",
            "border_right_width", "border_right_style", "border_right_color",
            "border_bottom_width", "border_bottom_style", "border_bottom_color",
            "border_left_width", "border_left_style", "border_left_color",
            "border_image_source", "outline_width", "outline_style", "outline_color",
            "box_shadow", "clip_path", "mask_image", "visibility",
        }
        self.assertLessEqual(required, set(self.policy["pseudo_style_fields"]))
        self.assertLessEqual({
            "box_shadow", "border_image_source", "border_image_outset",
            "outline_width", "outline_style", "outline_color", "outline_offset",
            "webkit_text_stroke_width", "webkit_text_stroke_color",
        }, set(self.policy["computed_style_fields"]))

        def subject_shadow(packet):
            subject = packet["subjects"]["contrast"]["shell-title"][0]
            shared._active_pseudo(
                packet["states"][0]["elements"][subject]["pseudo"]["before"],
                box_shadow="inset 0 0 0 8px rgb(0, 0, 0)",
            )

        def subject_effects(packet):
            subject = packet["subjects"]["contrast"]["shell-title"][0]
            packet["states"][0]["elements"][subject]["computed"].update({
                "box_shadow": "inset 0 0 0 20px rgb(0, 0, 0)",
                "webkit_text_stroke_width": "2px",
                "webkit_text_stroke_color": "rgb(0, 0, 0)",
            })

        def lineage_clip(packet):
            subject = packet["subjects"]["contrast"]["shell-title"][0]
            parent = packet["nodes"][subject]["parent_index"]
            packet["states"][0]["elements"][parent]["computed"].update({
                "clip_path": "inset(0 50% 0 0)", "mask_image": "linear-gradient(#0008,#0008)",
            })

        def lineage_border_image(packet):
            subject = packet["subjects"]["contrast"]["shell-title"][0]
            parent = packet["nodes"][subject]["parent_index"]
            packet["states"][0]["elements"][parent]["computed"].update({
                "border_image_source": "linear-gradient(red, red)",
                "border_image_outset": "100",
            })

        for mutation in (subject_shadow, subject_effects, lineage_clip, lineage_border_image):
            self._red(mutation)

        def root_effects(packet):
            root = packet["states"][0]["document"]["root"]
            root["computed"]["box_shadow"] = "inset 0 0 0 20px rgb(0, 0, 0)"
            shared._active_pseudo(
                root["pseudo"]["after"], border_top_width="4px",
                border_top_style="solid", border_top_color="rgb(0, 0, 0)",
            )

        self._all_red(root_effects)

    def test_visible_pseudo_on_hidden_host_cannot_escape_contrast_cover(self):
        def hidden_host_visible_pseudo(packet):
            state = packet["states"][0]
            subject = packet["subjects"]["contrast"]["shell-title"][0]
            lineage = set()
            current = subject
            while current is not None:
                lineage.add(current)
                current = packet["nodes"][current]["parent_index"]
            target = next(index for index in packet["subjects"]["interactive"]
                          if index not in lineage)
            state["elements"][target]["computed"]["visibility"] = "hidden"
            shared._active_pseudo(
                state["elements"][target]["pseudo"]["before"],
                background_color="rgb(0, 0, 0)",
            )
            current = packet["nodes"][target]["parent_index"]
            while current is not None:
                state["elements"][current]["computed"].update({
                    "contain": "none", "overflow_x": "visible", "overflow_y": "visible",
                })
                current = packet["nodes"][current]["parent_index"]

        self._red(hidden_host_visible_pseudo)

    def test_pointerless_visual_occlusion_red(self):
        def pointerless_overlay(packet):
            state = packet["states"][0]
            subject = packet["subjects"]["contrast"]["shell-title"][0]
            sample = state["contrast_hits"]["shell-title"][0]["samples"][0]
            overlay = next(index for index in range(len(packet["nodes"]))
                           if index != subject)
            observed = state["elements"][overlay]
            shared._set_box(observed["box"], left=sample["x"] - 2,
                            top=sample["y"] - 2, width=4, height=4)
            observed["computed"].update({
                "position": "fixed", "pointer_events": "none",
                "background_color": "rgb(0, 0, 0)",
            })
            sample["visual_top_index"] = overlay

        self._red(pointerless_overlay)

    def test_spatial_ancestor_and_foreign_underlay_are_closed(self):
        def absent_ancestor(packet):
            state = packet["states"][0]
            subject = packet["subjects"]["contrast"]["shell-title"][0]
            parent = packet["nodes"][subject]["parent_index"]
            shared._set_box(state["elements"][parent]["box"], left=-100, top=-100,
                            width=1, height=1)

        def painted_underlay(packet):
            state = packet["states"][0]
            subject = packet["subjects"]["contrast"]["shell-title"][0]
            lineage = set()
            current = subject
            while current is not None:
                lineage.add(current)
                current = packet["nodes"][current]["parent_index"]
            foreign = next(index for index in range(len(packet["nodes"]))
                           if index not in lineage)
            subject_box = state["elements"][subject]["box"]
            shared._set_box(state["elements"][foreign]["box"],
                            left=subject_box["left"], top=subject_box["top"],
                            width=subject_box["width"], height=subject_box["height"])
            state["elements"][foreign]["computed"].update({
                "position": "fixed", "background_color": "rgb(0, 0, 0)",
            })

        def hidden_attribute_overridden(packet):
            state = packet["states"][0]
            subject = packet["subjects"]["contrast"]["shell-title"][0]
            sample = state["contrast_hits"]["shell-title"][0]["samples"][0]
            foreign = next(index for index in range(len(packet["nodes"]))
                           if index != subject)
            row = state["elements"][foreign]
            row["hidden"] = True
            shared._set_box(row["box"], left=sample["x"] - 2, top=sample["y"] - 2,
                            width=4, height=4)
            row["computed"].update({
                "display": "block", "visibility": "visible",
                "background_color": "rgb(0, 0, 0)",
            })

        self._red(absent_ancestor)
        self._red(painted_underlay)
        self._red(hidden_attribute_overridden)

    def test_escape_paint_requires_an_excluding_ancestor_boundary(self):
        required = {
            "contain", "overflow_clip_margin", "outline_width", "outline_style",
            "outline_color", "outline_offset", "border_image_source", "border_image_outset",
        }
        self.assertLessEqual(required, set(self.policy["computed_style_fields"]))

        def effect(packet, kind: str, *, boundary: str = "paint"):
            state = packet["states"][0]
            target = next(index for index, row in enumerate(state["elements"])
                          if "db-score-ring" in row["class"].split())
            wrapper = next(index for index, row in enumerate(state["elements"])
                           if "db-dashboard" in row["class"].split())
            state["elements"][wrapper]["computed"]["contain"] = boundary
            style = state["elements"][target]["computed"]
            if kind == "shadow":
                style["box_shadow"] = "0 0 40px 20px rgb(0, 0, 0)"
            elif kind == "outline":
                style.update({"outline_width": "40px", "outline_style": "solid",
                              "outline_color": "rgb(0, 0, 0)", "outline_offset": "20px"})
            elif kind == "filter":
                style["filter"] = "blur(40px)"
            elif kind == "pseudo":
                shared._active_pseudo(
                    state["elements"][target]["pseudo"]["before"],
                    background_color="rgb(0, 0, 0)",
                )

        for kind in ("shadow", "outline", "filter", "pseudo"):
            with self.subTest(kind=kind, boundary="paint"):
                self.assertTrue(self._contrast_value(
                    lambda packet, kind=kind: effect(packet, kind)))
            with self.subTest(kind=kind, boundary="none"):
                self._red(lambda packet, kind=kind: effect(packet, kind, boundary="none"))

        def unknown_margin(packet):
            effect(packet, "shadow")
            state = packet["states"][0]
            wrapper = next(index for index, row in enumerate(state["elements"])
                           if "db-dashboard" in row["class"].split())
            state["elements"][wrapper]["computed"]["overflow_clip_margin"] = "unknown"

        self._red(unknown_margin)

        def zero_box_shadow(packet):
            effect(packet, "shadow", boundary="none")
            state = packet["states"][0]
            target = next(index for index, row in enumerate(state["elements"])
                          if "db-score-ring" in row["class"].split())
            shared._set_box(state["elements"][target]["box"], left=200, top=400,
                            width=0, height=0)

        self._red(zero_box_shadow)

    def test_svg_ink_requires_its_own_overflow_boundary(self):
        from scripts.contracts.rendered.effects import paint_boundary_excludes

        def svg_overflow(packet, value: str):
            state = packet["states"][0]
            line = next(index for index, node in enumerate(packet["nodes"])
                        if node["tag"] == "line")
            ancestor = packet["nodes"][line]["parent_index"]
            while ancestor is not None and packet["nodes"][ancestor]["tag"] != "svg":
                ancestor = packet["nodes"][ancestor]["parent_index"]
            self.assertIsNotNone(ancestor)
            state["elements"][ancestor]["computed"].update({
                "overflow_x": value, "overflow_y": value,
                "overflow_clip_margin": "0px",
            })
            current = packet["nodes"][ancestor]["parent_index"]
            while current is not None:
                state["elements"][current]["computed"].update({
                    "contain": "none", "overflow_x": "visible", "overflow_y": "visible",
                })
                current = packet["nodes"][current]["parent_index"]
            return line, ancestor

        _, entry = self._mutant()
        packet = entry["facts"]
        line, svg = svg_overflow(packet, "hidden")
        sample = packet["states"][0]["contrast_hits"]["shell-title"][0]["samples"][0]
        self.assertTrue(paint_boundary_excludes(
            packet["nodes"], packet["states"][0], line, sample["x"], sample["y"]))
        packet["states"][0]["elements"][svg]["computed"].update({
            "overflow_x": "visible", "overflow_y": "visible",
        })
        self.assertFalse(paint_boundary_excludes(
            packet["nodes"], packet["states"][0], line, sample["x"], sample["y"]))
        self._red(lambda packet: svg_overflow(packet, "visible"))

    def test_foreign_text_range_cannot_escape_a_narrow_origin_box(self):
        def escaped_text(packet):
            state = packet["states"][0]
            sample = state["contrast_hits"]["shell-title"][0]["samples"][0]
            contrast = {index for rows in packet["subjects"]["contrast"].values()
                        for index in rows}
            text_index = next(index for index, row in enumerate(packet["text_nodes"])
                              if row["parent_index"] not in contrast
                              and state["text_ranges"][index]["rects"])
            parent = packet["text_nodes"][text_index]["parent_index"]
            shared._set_box(state["elements"][parent]["box"], left=sample["x"] + 20,
                            top=sample["y"], width=1, height=1)
            shared._set_box(state["text_ranges"][text_index]["rects"][0],
                            left=sample["x"] - 1, top=sample["y"] - 1,
                            width=2, height=2)

        self._red(escaped_text)


if __name__ == "__main__":
    unittest.main()
