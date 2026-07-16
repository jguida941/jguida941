"""Adversarial W4 controls for deterministic content-density claims."""
from __future__ import annotations

import copy
import unittest

from tests.contracts import test_rendered_fact_adversarial as shared


class RenderedFactDensityAdversarial(unittest.TestCase):
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

    def _predicate_red(self, mutate) -> None:
        from scripts.contracts import rendered_predicates
        from scripts.quality.rendered_facts.schema import validate_packet

        _, entry = self._mutant()
        mutate(entry["facts"])
        validate_packet(entry["facts"], page="index", theme=self.theme, viewport=390)
        self.assertFalse(rendered_predicates.rendered_content_density(
            [entry], policy=self.policy))

    def _reject_bundle(self, mutate) -> None:
        from scripts.quality.rendered_facts.schema import validate_packet

        _, entry = self._mutant()
        mutate(entry["facts"])
        with self.assertRaises(RuntimeError):
            validate_packet(entry["facts"], page="index", theme=self.theme, viewport=390)

    def test_internal_holes_and_hidden_content_red(self):
        def internal_hole(packet):
            state = packet["states"][0]
            selector = next(iter(packet["subjects"]["density"]))
            surface = packet["subjects"]["density"][selector][0]
            children = [index for index, node in enumerate(packet["nodes"])
                        if node["parent_index"] == surface
                        and state["elements"][index]["computed"]["position"]
                        not in {"absolute", "fixed"}]
            last = children[-1]
            surface_box = state["elements"][surface]["box"]
            shared._set_box(surface_box, left=surface_box["left"], top=surface_box["top"],
                            width=surface_box["width"], height=surface_box["height"] + 20)
            child_box = state["elements"][last]["box"]
            shared._set_box(child_box, left=child_box["left"], top=child_box["top"] + 20,
                            width=child_box["width"], height=child_box["height"])

        def hidden_content(packet):
            state = packet["states"][0]
            target = next(index for index, node in enumerate(packet["nodes"])
                          if node["id"] == "cal-total")

            def descendant(index):
                while index is not None:
                    if index == target:
                        return True
                    index = packet["nodes"][index]["parent_index"]
                return False

            for text, ranges in zip(packet["text_nodes"], state["text_ranges"]):
                if text["parent_index"] is not None and descendant(text["parent_index"]):
                    ranges["rects"] = []
            for index in range(len(packet["nodes"])):
                if descendant(index):
                    state["elements"][index]["computed"].update({
                        "background_color": "rgba(0, 0, 0, 0)", "background_image": "none",
                    })

        self._predicate_red(internal_hole)
        self._predicate_red(hidden_content)

    def test_hidden_oversized_and_blank_painted_children_red(self):
        def hidden_one_surface(packet):
            selector = next(iter(packet["subjects"]["density"]))
            subject = packet["subjects"]["density"][selector][0]
            row = packet["states"][0]["elements"][subject]
            row["hidden"] = True
            row["computed"]["display"] = "none"
            row["rect_count"] = 0
            shared._set_box(row["box"], left=0, top=0, width=0, height=0)

        def oversized_child(packet):
            state = packet["states"][0]
            selector = next(iter(packet["subjects"]["density"]))
            surface = packet["subjects"]["density"][selector][0]
            child = next(index for index, node in enumerate(packet["nodes"])
                         if node["parent_index"] == surface
                         and state["elements"][index]["computed"]["position"]
                         not in {"absolute", "fixed"})
            for index in (surface, child):
                box = state["elements"][index]["box"]
                shared._set_box(box, left=box["left"], top=box["top"], width=box["width"],
                                height=box["height"] + 500)

        def blank_painted_wrapper(packet):
            state = packet["states"][0]
            selector = next(iter(packet["subjects"]["density"]))
            surface = packet["subjects"]["density"][selector][0]
            child = next(index for index, node in enumerate(packet["nodes"])
                         if node["parent_index"] == surface)

            def descendant(index):
                while index is not None:
                    if index == child:
                        return True
                    index = packet["nodes"][index]["parent_index"]
                return False

            for text, ranges in zip(packet["text_nodes"], state["text_ranges"]):
                if text["parent_index"] is not None and descendant(text["parent_index"]):
                    ranges["rects"] = []
            for index in range(len(packet["nodes"])):
                if descendant(index):
                    state["elements"][index]["computed"].update({
                        "background_color": "rgba(0, 0, 0, 0)", "background_image": "none",
                    })
            state["elements"][child]["computed"]["background_color"] = "rgb(1, 2, 3)"

        self._predicate_red(hidden_one_surface)
        self._predicate_red(oversized_child)
        self._predicate_red(blank_painted_wrapper)

    def test_painted_text_and_effective_clipping_are_required(self):
        def transparent_text(packet):
            for row in packet["states"][0]["elements"]:
                row["computed"].update({
                    "color": "rgba(0, 0, 0, 0)",
                    "webkit_text_fill_color": "rgba(0, 0, 0, 0)",
                })

        def filtered_content(packet):
            for row in packet["states"][0]["elements"]:
                row["computed"]["filter"] = "opacity(0)"

        def clipped_surface(packet):
            selector = next(iter(packet["subjects"]["density"]))
            surface = packet["subjects"]["density"][selector][0]
            packet["states"][0]["elements"][surface]["computed"]["clip_path"] = "inset(100%)"

        def clipped_children(packet):
            state = packet["states"][0]
            selector = next(iter(packet["subjects"]["density"]))
            surface = packet["subjects"]["density"][selector][0]
            for index, node in enumerate(packet["nodes"]):
                if (node["parent_index"] == surface
                        and state["elements"][index]["computed"]["position"]
                        not in {"absolute", "fixed"}):
                    state["elements"][index]["computed"]["overflow_y"] = "hidden"
                    state["elements"][index]["scroll"]["client_height"] = 1

        def clipped_prototype_lane(packet):
            state = packet["states"][0]
            lane = next(index for index, row in enumerate(state["elements"])
                        if "db-calendar-scroll" in row["class"].split())
            state["elements"][lane]["computed"]["overflow_y"] = "hidden"
            state["elements"][lane]["scroll"]["client_height"] = 0

        def transparent_prototype_images(packet):
            state = packet["states"][0]
            lane = next(index for index, row in enumerate(state["elements"])
                        if "db-calendar-scroll" in row["class"].split())

            def below(index):
                while index is not None:
                    if index == lane:
                        return True
                    index = packet["nodes"][index]["parent_index"]
                return False

            for index, node in enumerate(packet["nodes"]):
                if below(index) and "data-prototype-origin" in node["data"]:
                    state["elements"][index]["computed"].update({
                        "background_color": "rgba(0, 0, 0, 0)",
                        "background_image": "linear-gradient(transparent, transparent)",
                    })

        for mutation in (
            transparent_text, filtered_content, clipped_surface, clipped_children,
            clipped_prototype_lane, transparent_prototype_images,
        ):
            self._predicate_red(mutation)

    def test_empty_graphic_tag_does_not_authorize_content(self):
        from scripts.quality.rendered_facts.subject_identity import dom_identity_sha256

        def empty_svg_child(packet):
            state = packet["states"][0]
            selector = next(iter(packet["subjects"]["density"]))
            surface = packet["subjects"]["density"][selector][0]
            child = next(index for index, node in enumerate(packet["nodes"])
                         if node["parent_index"] == surface
                         and state["elements"][index]["computed"]["position"]
                         not in {"absolute", "fixed"})

            def descendant(index):
                while index is not None:
                    if index == child:
                        return True
                    index = packet["nodes"][index]["parent_index"]
                return False

            packet["nodes"][child]["tag"] = "svg"
            for text, ranges in zip(packet["text_nodes"], state["text_ranges"]):
                if text["parent_index"] is not None and descendant(text["parent_index"]):
                    ranges["rects"] = []
            state["dom_identity_sha256"] = dom_identity_sha256(
                packet["nodes"], packet["text_nodes"], self.policy)

        self._predicate_red(empty_svg_child)

    def test_unknown_prototype_origin_is_rejected(self):
        from scripts.quality.rendered_facts.subject_identity import dom_identity_sha256

        def unknown_origin(packet):
            node = next(row for row in packet["nodes"]
                        if "data-prototype-origin" in row["data"])
            node["data"]["data-prototype-origin"] = "not-admitted"
            digest = dom_identity_sha256(packet["nodes"], packet["text_nodes"], self.policy)
            for state in packet["states"]:
                state["dom_identity_sha256"] = digest

        self._reject_bundle(unknown_origin)


if __name__ == "__main__":
    unittest.main()
