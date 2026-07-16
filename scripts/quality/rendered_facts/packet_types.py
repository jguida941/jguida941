"""Strict leaf and container domains for rendered-fact packets."""
from __future__ import annotations

from scripts.quality.rendered_facts.geometry import finite_number, nonnegative_integer


def _closed(value: object, fields: set[str], *, label: str) -> dict:
    if not isinstance(value, dict) or set(value) != fields:
        raise RuntimeError(f"{label}: fields are not closed")
    return value


def _list(value: object, *, label: str) -> list:
    if not isinstance(value, list):
        raise RuntimeError(f"{label}: expected a list")
    return value


def _string(value: object, *, label: str, nonempty: bool = False) -> str:
    if not isinstance(value, str) or (nonempty and not value):
        raise RuntimeError(f"{label}: expected {'a nonempty ' if nonempty else ''}string")
    return value


def _optional_string(value: object, *, label: str) -> None:
    if value is not None:
        _string(value, label=label)


def _bool_or_none(value: object, *, label: str) -> None:
    if value is not None and type(value) is not bool:
        raise RuntimeError(f"{label}: expected bool|null")


def _string_map(value: object, fields: list[str], *, label: str) -> None:
    row = _closed(value, set(fields), label=label)
    for key in fields:
        _string(row[key], label=f"{label}/{key}", nonempty=True)


def _pseudo_map(value: object, fields: list[str], *, label: str) -> None:
    if not isinstance(value, dict):
        raise RuntimeError(f"{label}: expected pseudo object")
    if set(value) == {"content"}:
        if value["content"] not in {"none", "normal"}:
            raise RuntimeError(f"{label}: compact pseudo is not inactive")
        return
    _string_map(value, fields, label=label)
    if value["content"] in {"none", "normal"}:
        raise RuntimeError(f"{label}: inactive pseudo is not compact")


def _settle_types(value: object, *, label: str) -> None:
    row = _closed(value, {"mechanism", "turns", "reads", "animations"}, label=label)
    _string(row["mechanism"], label=f"{label}/mechanism", nonempty=True)
    nonnegative_integer(row["turns"], label=f"{label}/turns")
    for read in _list(row["reads"], label=f"{label}/reads"):
        read = _closed(read, {"turn", "root_display", "root_box"}, label=f"{label}/read")
        nonnegative_integer(read["turn"], label=f"{label}/read/turn")
        _string(read["root_display"], label=f"{label}/read/display", nonempty=True)
    for animation in _list(row["animations"], label=f"{label}/animations"):
        animation = _closed(animation, {
            "id", "play_state", "pending", "current_time", "target",
        }, label=f"{label}/animation")
        _string(animation["id"], label=f"{label}/animation/id")
        _string(animation["play_state"], label=f"{label}/animation/state", nonempty=True)
        if type(animation["pending"]) is not bool:
            raise RuntimeError(f"{label}/animation/pending: expected bool")
        if animation["current_time"] is not None:
            finite_number(animation["current_time"], label=f"{label}/animation/time")
        if animation["target"] is not None:
            _string_map(animation["target"], ["tag", "id", "class"],
                        label=f"{label}/animation/target")


def _witness_types(value: object, *, label: str) -> None:
    row = _closed(value, {
        "checked_radio_ids", "stage_displays", "active_options", "variants",
    }, label=label)
    for item in _list(row["checked_radio_ids"], label=f"{label}/checked"):
        _string(item, label=f"{label}/checked/id", nonempty=True)
    for item in _list(row["stage_displays"], label=f"{label}/stages"):
        _string_map(item, ["lang", "display"], label=f"{label}/stage")
    for item in _list(row["active_options"], label=f"{label}/options"):
        _string_map(item, ["base", "component", "source"], label=f"{label}/option")
    for item in _list(row["variants"], label=f"{label}/variants"):
        item = _closed(item, {"variant", "hidden", "display"}, label=f"{label}/variant")
        _string(item["variant"], label=f"{label}/variant/name", nonempty=True)
        if type(item["hidden"]) is not bool:
            raise RuntimeError(f"{label}/variant/hidden: expected bool")
        _string(item["display"], label=f"{label}/variant/display", nonempty=True)


def _node_types(nodes: object) -> None:
    nullable = ("owner", "role", "href", "type", "for", "tabindex", "contenteditable")
    for position, node in enumerate(_list(nodes, label="nodes")):
        if not isinstance(node, dict):
            raise RuntimeError(f"node/{position}: expected an object")
        nonnegative_integer(node.get("index"), label=f"node/{position}/index")
        parent = node.get("parent_index")
        if parent is not None:
            nonnegative_integer(parent, label=f"node/{position}/parent")
        for key in ("tag", "id", "direct_text", "text_content"):
            _string(node.get(key), label=f"node/{position}/{key}", nonempty=key == "tag")
        for key in nullable:
            _optional_string(node.get(key), label=f"node/{position}/{key}")
        data = node.get("data")
        if not isinstance(data, dict) or any(
            not isinstance(key, str) or not key.startswith("data-")
            or not isinstance(value, str) for key, value in data.items()
        ):
            raise RuntimeError(f"node/{position}/data: expected data-* string map")


def _text_types(rows: object) -> None:
    for position, row in enumerate(_list(rows, label="text-nodes")):
        row = _closed(row, {"index", "parent_index", "child_index", "text"},
                      label=f"text/{position}")
        nonnegative_integer(row["index"], label=f"text/{position}/index")
        for key in ("parent_index", "child_index"):
            if row[key] is not None:
                nonnegative_integer(row[key], label=f"text/{position}/{key}")
        _string(row["text"], label=f"text/{position}/text", nonempty=True)


def _state_types(states: object, policy: dict) -> None:
    mutable = set(policy["mutable_node_fields"])
    for state_position, state in enumerate(_list(states, label="states")):
        if not isinstance(state, dict):
            raise RuntimeError(f"state/{state_position}: expected an object")
        _string(state.get("state_id"), label=f"state/{state_position}/id", nonempty=True)
        _string(state.get("dom_identity_sha256"), label=f"state/{state_position}/dom-hash",
                nonempty=True)
        _settle_types(state.get("settle"), label=f"state/{state_position}/settle")
        _witness_types(state.get("witness"), label=f"state/{state_position}/witness")
        document = _closed(state.get("document"), {"root", "body", "root_tokens"},
                           label=f"state/{state_position}/document")
        for name in ("root", "body"):
            geometry = _closed(document[name], {
                "box", "client_width", "client_height", "scroll_width", "scroll_height",
                "rect_count", "hidden", "computed", "pseudo",
            }, label=f"state/{state_position}/document/{name}")
            for key in ("client_width", "client_height", "scroll_width", "scroll_height"):
                nonnegative_integer(
                    geometry[key], label=f"state/{state_position}/document/{name}/{key}")
            nonnegative_integer(
                geometry["rect_count"], label=f"state/{state_position}/document/{name}/rects")
            if type(geometry["hidden"]) is not bool:
                raise RuntimeError(f"state/{state_position}/document/{name}/hidden")
            _string_map(geometry["computed"], policy["computed_style_fields"],
                        label=f"state/{state_position}/document/{name}/computed")
            pseudo = _closed(geometry["pseudo"], {"before", "after"},
                             label=f"state/{state_position}/document/{name}/pseudo")
            for pseudo_name in ("before", "after"):
                _pseudo_map(pseudo[pseudo_name], policy["pseudo_style_fields"],
                            label=f"state/{state_position}/document/{name}/{pseudo_name}")
        tokens = document.get("root_tokens")
        _string_map(tokens, policy["root_token_fields"],
                    label=f"state/{state_position}/tokens")
        for element_position, element in enumerate(_list(
                state.get("elements"), label=f"state/{state_position}/elements")):
            if not isinstance(element, dict):
                raise RuntimeError(f"state/{state_position}/element/{element_position}: object")
            nonnegative_integer(element.get("index"),
                                label=f"state/{state_position}/element/{element_position}/index")
            nonnegative_integer(element.get("rect_count"),
                                label=f"state/{state_position}/element/{element_position}/rects")
            _string(element.get("class"),
                    label=f"state/{state_position}/element/{element_position}/class")
            if type(element.get("hidden")) is not bool:
                raise RuntimeError(f"state/{state_position}/element/{element_position}/hidden")
            for key in ("checked", "disabled"):
                _bool_or_none(element.get(key),
                              label=f"state/{state_position}/element/{element_position}/{key}")
            for key in mutable - {"index", "class", "hidden", "checked", "disabled"}:
                _optional_string(element.get(key),
                                 label=f"state/{state_position}/element/{element_position}/{key}")
            _string_map(element.get("computed"), policy["computed_style_fields"],
                        label=f"state/{state_position}/element/{element_position}/computed")
            pseudo = element.get("pseudo")
            if not isinstance(pseudo, dict):
                raise RuntimeError(f"state/{state_position}/element/{element_position}/pseudo")
            for name in ("before", "after"):
                _pseudo_map(pseudo.get(name), policy["pseudo_style_fields"],
                            label=f"state/{state_position}/element/{element_position}/{name}")
        for range_position, range_row in enumerate(_list(
                state.get("text_ranges"), label=f"state/{state_position}/ranges")):
            range_row = _closed(range_row, {"index", "rects"},
                                label=f"state/{state_position}/range/{range_position}")
            nonnegative_integer(range_row["index"],
                                label=f"state/{state_position}/range/{range_position}/index")
            _list(range_row["rects"], label=f"state/{state_position}/range/{range_position}/rects")
        hits = _closed(state.get("contrast_hits"), {
            row["id"] for row in policy["contrast_subjects"]
        }, label=f"state/{state_position}/contrast-hits")
        for subject_id, subject_rows in hits.items():
            for subject_row in _list(
                    subject_rows, label=f"state/{state_position}/contrast-hits/{subject_id}"):
                subject_row = _closed(subject_row, {"subject_index", "samples"},
                                      label=f"state/{state_position}/contrast-hit")
                nonnegative_integer(subject_row["subject_index"],
                                    label=f"state/{state_position}/contrast-subject")
                for sample in _list(subject_row["samples"], label="contrast-samples"):
                    sample = _closed(sample, {"x", "y", "top_index", "visual_top_index"},
                                     label="contrast-sample")
                    finite_number(sample["x"], label="contrast-sample/x")
                    finite_number(sample["y"], label="contrast-sample/y")
                    if (type(sample["top_index"]) is not int
                            or sample["top_index"] < -1):
                        raise RuntimeError("contrast-sample/top-index")
                    if (type(sample["visual_top_index"]) is not int
                            or sample["visual_top_index"] < -1):
                        raise RuntimeError("contrast-sample/visual-top-index")


def validate_packet_types(payload: dict, policy: dict) -> None:
    if type(payload.get("schema_version")) is not int:
        raise RuntimeError("rendered facts schema_version must be an integer")
    for key in ("contract_id", "page", "route", "theme"):
        _string(payload.get(key), label=key, nonempty=True)
    viewport = _closed(payload.get("viewport"), {
        "width", "height", "device_scale_factor",
    }, label="viewport")
    for key in ("width", "height"):
        if nonnegative_integer(viewport[key], label=f"viewport/{key}") == 0:
            raise RuntimeError(f"viewport/{key}: must be positive")
    if finite_number(viewport["device_scale_factor"], label="viewport/dpr") <= 0:
        raise RuntimeError("viewport/dpr: must be positive")
    inputs = payload.get("inputs")
    if not isinstance(inputs, dict) or any(
        value is not None and (
            not isinstance(value, str) or len(value) != 64
            or any(char not in "0123456789abcdef" for char in value)
        ) for value in inputs.values()
    ):
        raise RuntimeError("inputs: expected sha256|null map")
    readiness = _closed(payload.get("readiness"), {
        "observed_theme", "hydration_state", "fonts", "settle", "index",
    }, label="readiness")
    _string(readiness["observed_theme"], label="readiness/theme", nonempty=True)
    _optional_string(readiness["hydration_state"], label="readiness/hydration")
    _string(readiness["fonts"], label="readiness/fonts", nonempty=True)
    _settle_types(readiness["settle"], label="readiness/settle")
    index = _closed(readiness["index"], {
        "sentinel_values", "prototype_origin_counts", "empty_state_hidden",
    }, label="readiness/index")
    if (not isinstance(index["sentinel_values"], dict)
            or any(not isinstance(value, str) for value in index["sentinel_values"].values())):
        raise RuntimeError("readiness/index/sentinels: expected string map")
    if (not isinstance(index["prototype_origin_counts"], dict)
            or any(nonnegative_integer(value, label="readiness/index/count") < 0
                   for value in index["prototype_origin_counts"].values())):
        raise RuntimeError("readiness/index/counts: expected nonnegative integer map")
    if (not isinstance(index["empty_state_hidden"], dict)
            or any(type(value) is not bool for value in index["empty_state_hidden"].values())):
        raise RuntimeError("readiness/index/empty: expected bool map")
    _node_types(payload.get("nodes"))
    _text_types(payload.get("text_nodes"))
    subjects = _closed(payload.get("subjects"), {
        "interactive", "contrast", "density",
    }, label="subjects")
    contrast = _closed(subjects["contrast"], {
        row["id"] for row in policy["contrast_subjects"]}, label="subjects/contrast")
    page = payload.get("page")
    density_fields = {row["selector"] for row in policy["density_surfaces"].get(page, [])}
    density = _closed(subjects["density"], density_fields, label="subjects/density")
    for label, indices in [("interactive", subjects["interactive"]), *(
        (f"contrast/{key}", value) for key, value in contrast.items()), *(
        (f"density/{key}", value) for key, value in density.items())]:
        for index in _list(indices, label=f"subjects/{label}"):
            nonnegative_integer(index, label=f"subjects/{label}/index")
    _state_types(payload.get("states"), policy)
