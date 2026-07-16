"""Closed packet, provenance, and bundle validation for W4 rendered facts."""
from __future__ import annotations

import hashlib
import json

from scripts.quality.rendered_facts.codec import (
    compressed_packet_bytes, decode_packet_bytes, packet_bytes,
)

from scripts.quality.rendered_facts.geometry import (
    finite_number, nonnegative_integer, validate_box, validate_scroll,
)
from scripts.quality.rendered_facts.inventory import validate_artifact_inventory
from scripts.quality.rendered_facts.packet_types import validate_packet_types
from scripts.quality.rendered_facts.provenance import validate_provenance
from scripts.quality.rendered_facts.samples import validate_contrast_hits

from scripts.quality.rendered_facts.policy import (
    active_profiles, artifact_path, expected_density_count,
    expected_index_hydration_facts, input_hashes, load_policy, page_routes,
    provenance_path, state_plan,
)
from scripts.quality.rendered_facts.subject_identity import dom_identity_sha256, memberships

_RAW_FACT_BANNED_KEYS = frozenset({
    "pass", "fail", "ratio", "visible", "exception", "contained", "offender",
    "horizontal_overflow", "target_pass", "density_residual", "eligible",
})

def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _validate_pseudos(value: object, fields: set[str], *, label: str) -> None:
    if not isinstance(value, dict) or set(value) != {"before", "after"}:
        raise RuntimeError(f"{label}: pseudo slots drift")
    for name, row in value.items():
        if not isinstance(row, dict):
            raise RuntimeError(f"{label}/{name}: pseudo row is not an object")
        if set(row) == {"content"}:
            if row["content"] not in {"none", "normal"}:
                raise RuntimeError(f"{label}/{name}: compact pseudo is active")
        elif set(row) != fields or row["content"] in {"none", "normal"}:
            raise RuntimeError(f"{label}/{name}: pseudo row is not canonical")
def _validate_settle(value: object, *, label: str, policy: dict) -> None:
    expected = {"mechanism", "turns", "reads", "animations"}
    if not isinstance(value, dict) or set(value) != expected:
        raise RuntimeError(f"{label}: settle fields are not closed")
    spec = policy["readiness"]["settle"]
    if value["mechanism"] != spec["mechanism"] or value["turns"] != spec["turns"]:
        raise RuntimeError(f"{label}: settle mechanism/count drift")
    reads = value["reads"]
    if not isinstance(reads, list) or len(reads) != spec["turns"]:
        raise RuntimeError(f"{label}: forced-read witness count drift")
    for turn, read in enumerate(reads, start=1):
        if not isinstance(read, dict) or set(read) != {"turn", "root_display", "root_box"}:
            raise RuntimeError(f"{label}: forced-read witness fields drift")
        if read["turn"] != turn or not isinstance(read["root_display"], str):
            raise RuntimeError(f"{label}: forced-read witness order/value drift")
        validate_box(read["root_box"], label=f"{label}/turn-{turn}")
    animations = value["animations"]
    if not isinstance(animations, list):
        raise RuntimeError(f"{label}: animations are not a list")
    for animation in animations:
        if not isinstance(animation, dict) or set(animation) != {
            "id", "play_state", "pending", "current_time", "target",
        }:
            raise RuntimeError(f"{label}: animation fields drift")
        if animation["play_state"] not in {"idle", "paused", "finished"}:
            raise RuntimeError(f"{label}: animation remains {animation['play_state']!r}")
        if animation["pending"] is not False:
            raise RuntimeError(f"{label}: animation remains pending")
        if animation["current_time"] is not None:
            finite_number(animation["current_time"], label=f"{label}/animation-time")
        target = animation["target"]
        if target is not None and (
            not isinstance(target, dict) or set(target) != {"tag", "id", "class"}
            or not all(isinstance(target[key], str) for key in target)
        ):
            raise RuntimeError(f"{label}: animation target fields drift")


def _validate_rendered_state_witness(
    page: str, plan: dict, state: dict, nodes: list[dict]
) -> None:
    witness = state["witness"]
    expected_witness_keys = {"checked_radio_ids", "stage_displays", "active_options", "variants"}
    if set(witness) != expected_witness_keys:
        raise RuntimeError(f"{page}/{state['state_id']}: witness fields are not closed")
    if page != "studio":
        if any(witness[key] for key in expected_witness_keys):
            raise RuntimeError(f"{page}: default state unexpectedly carries Studio witnesses")
        return

    base = plan["base"]
    vector = state["elements"]
    derived_checked = [node["id"] for node, observed in zip(nodes, vector)
                       if "lang-radio" in observed["class"].split() and observed["checked"] is True]
    derived_stages = [
        {"lang": node["data"].get("data-lang"), "display": observed["computed"]["display"]}
        for node, observed in zip(nodes, vector)
        if node["tag"] == "section" and node["data"].get("data-lang")
    ]
    derived_active = [
        {"base": node["data"].get("data-base"),
         "component": node["data"].get("data-component"),
         "source": node["data"].get("data-source")}
        for node, observed in zip(nodes, vector)
        if "swap-opt" in observed["class"].split() and "active" in observed["class"].split()
    ]
    derived_variants = [
        {"variant": node["data"].get("data-variant"), "hidden": observed["hidden"],
         "display": observed["computed"]["display"]}
        for node, observed in zip(nodes, vector) if node["data"].get("data-variant")
    ]
    if witness != {
        "checked_radio_ids": derived_checked,
        "stage_displays": derived_stages,
        "active_options": derived_active,
        "variants": derived_variants,
    }:
        raise RuntimeError(f"studio/{state['state_id']}: witness does not match state vector")
    if witness["checked_radio_ids"] != [f"lang-{base}"]:
        raise RuntimeError(f"studio/{state['state_id']}: wrong selected base radio")
    stage_displays = witness["stage_displays"]
    if {row.get("lang") for row in stage_displays} != {
        row["data"].get("data-lang") for row in nodes if row["data"].get("data-lang")
        and row["tag"] == "section"
    }:
        raise RuntimeError(f"studio/{state['state_id']}: stage witness set drift")
    shown = [row["lang"] for row in stage_displays if row.get("display") != "none"]
    if shown != [base]:
        raise RuntimeError(f"studio/{state['state_id']}: expected sole displayed stage {base!r}")
    active_for_base = [row for row in witness["active_options"] if row.get("base") == base]
    if active_for_base != [{
        "base": base, "component": plan["component"], "source": plan["source"],
    }]:
        raise RuntimeError(f"studio/{state['state_id']}: wrong active swap option")

    variant_rows = witness["variants"]
    variant_names = {row["data"].get("data-variant") for row in nodes
                     if row["data"].get("data-variant")}
    if {row.get("variant") for row in variant_rows} != variant_names:
        raise RuntimeError(f"studio/{state['state_id']}: variant witness set drift")
    shown_variants = []
    for node, observed in zip(nodes, vector):
        variant = node["data"].get("data-variant")
        if variant and observed["rect_count"] > 0 and observed["computed"]["display"] != "none":
            shown_variants.append(variant)
    if shown_variants != [plan["variant"]]:
        raise RuntimeError(
            f"studio/{state['state_id']}: expected sole rendered variant {plan['variant']!r}, "
            f"observed {shown_variants!r}")
    named = {row["variant"]: row for row in variant_rows}
    expected_variant = named.get(plan["variant"])
    if not expected_variant or expected_variant["hidden"] is True:
        raise RuntimeError(f"studio/{state['state_id']}: expected variant is hidden")


def validate_packet(
    payload: dict, *, page: str, theme: str, viewport: int
) -> None:
    """Validate one verdict-free packet against current committed inputs and the closed policy."""
    policy = load_policy()
    expected_top = {
        "contract_id", "schema_version", "page", "route", "theme", "viewport", "inputs",
        "readiness", "nodes", "text_nodes", "subjects", "states",
    }
    if not isinstance(payload, dict) or set(payload) != expected_top:
        observed = sorted(payload) if isinstance(payload, dict) else type(payload).__name__
        raise RuntimeError(
            f"{page}/{theme}/{viewport}: packet fields are not closed: {observed!r}"
        )
    validate_packet_types(payload, policy)
    if payload.get("contract_id") != "RenderedComputedFacts" or payload.get("schema_version") != 1:
        raise RuntimeError("rendered facts contract/version mismatch")
    if (payload.get("page"), payload.get("route"), payload.get("theme")) != (
        page, page_routes()[page], theme
    ):
        raise RuntimeError("rendered facts page/theme identity mismatch")
    viewport_rows = {row["width"]: row for row in policy["matrix"]["viewports"]}
    if viewport not in viewport_rows or payload.get("viewport") != viewport_rows[viewport]:
        raise RuntimeError("rendered facts viewport mismatch")
    if payload.get("inputs") != input_hashes(page, theme):
        raise RuntimeError("rendered facts input hashes are stale or mismatched")
    banned = sorted(set(_walk_keys(payload)) & _RAW_FACT_BANNED_KEYS)
    if banned:
        raise RuntimeError(f"rendered producer emitted verdict keys: {banned}")

    readiness = payload["readiness"]
    if set(readiness) != {
        "observed_theme", "hydration_state", "fonts", "settle", "index",
    }:
        raise RuntimeError("rendered readiness fields are not closed")
    if readiness["observed_theme"] != theme or readiness["fonts"] != "ready":
        raise RuntimeError("rendered facts readiness is unproved")
    _validate_settle(readiness["settle"], label=f"{page}/readiness", policy=policy)
    if page == "index":
        expected_index = expected_index_hydration_facts()
        if readiness["hydration_state"] != "complete" or readiness["index"] != {
            key: expected_index[key]
            for key in ("sentinel_values", "prototype_origin_counts", "empty_state_hidden")
        }:
            raise RuntimeError("rendered facts index hydration witness mismatch")
    elif readiness["hydration_state"] is not None or readiness["index"] != {
        "sentinel_values": {}, "prototype_origin_counts": {}, "empty_state_hidden": {},
    }:
        raise RuntimeError(f"{page}: unexpected index readiness facts")

    nodes = payload["nodes"]
    if not isinstance(nodes, list) or not nodes:
        raise RuntimeError("rendered facts node table is empty")
    stable_fields = set(policy["stable_node_fields"])
    for index, node in enumerate(nodes):
        if not isinstance(node, dict) or set(node) != stable_fields or node.get("index") != index:
            raise RuntimeError(f"rendered node {index}: identity vector drift")
        parent = node["parent_index"]
        if parent is not None and (not isinstance(parent, int) or parent < 0 or parent >= index):
            raise RuntimeError(f"rendered node {index}: parent is not an earlier preorder index")
        if not isinstance(node["data"], dict):
            raise RuntimeError(f"rendered node {index}: data identity is not an object")
        href = node["href"]
        if href is not None and (not isinstance(href, str)
                                 or "127.0.0.1:" in href or "localhost:" in href):
            raise RuntimeError(f"rendered node {index}: href identity contains capture origin")
    admitted_origins = expected_index_hydration_facts()["prototype_origin_counts"]
    observed_origins = dict.fromkeys(admitted_origins, 0)
    for node in nodes:
        origin = node["data"].get("data-prototype-origin")
        if origin is None:
            continue
        if page != "index" or origin not in observed_origins:
            raise RuntimeError(f"{page}: unknown rendered prototype origin {origin!r}")
        observed_origins[origin] += 1
    if page == "index" and observed_origins != admitted_origins:
        raise RuntimeError("index: rendered prototype-origin counts drift")

    text_nodes = payload["text_nodes"]
    text_fields = set(policy["text_node_fields"])
    for index, row in enumerate(text_nodes):
        if not isinstance(row, dict) or set(row) != text_fields or row.get("index") != index:
            raise RuntimeError(f"rendered text node {index}: identity vector drift")
        parent = row["parent_index"]
        if parent is not None and (not isinstance(parent, int) or not 0 <= parent < len(nodes)):
            raise RuntimeError(f"rendered text node {index}: bad parent index")
    expected_dom_identity = dom_identity_sha256(nodes, text_nodes, policy)

    subjects = payload["subjects"]
    if set(subjects) != {"interactive", "contrast", "density"}:
        raise RuntimeError("rendered subject maps are not closed")
    for indices in [subjects["interactive"], *subjects["contrast"].values(),
                    *subjects["density"].values()]:
        if (not isinstance(indices, list) or len(indices) != len(set(indices))
                or any(not isinstance(i, int) or not 0 <= i < len(nodes) for i in indices)):
            raise RuntimeError("rendered subject index set is invalid")
    contrast = {row["id"]: row for row in policy["contrast_subjects"]}
    if set(subjects["contrast"]) != set(contrast):
        raise RuntimeError("rendered contrast subject cover drift")
    for subject_id, spec in contrast.items():
        if len(subjects["contrast"][subject_id]) != spec["count"]:
            raise RuntimeError(f"rendered contrast cardinality drift: {subject_id}")
    surfaces = {row["selector"]: row for row in policy["density_surfaces"][page]}
    if set(subjects["density"]) != set(surfaces):
        raise RuntimeError("rendered density subject cover drift")
    for selector, spec in surfaces.items():
        if len(subjects["density"][selector]) != expected_density_count(spec):
            raise RuntimeError(f"rendered density cardinality drift: {page}/{selector}")

    plans = state_plan(page)
    states = payload["states"]
    if [row.get("state_id") for row in states] != [row["state_id"] for row in plans]:
        raise RuntimeError(f"{page}: rendered reachable-state cover drift")
    mutable_fields = set(policy["mutable_node_fields"])
    state_vector_digests: list[str] = []
    for plan, state in zip(plans, states):
        if set(state) != {
            "state_id", "settle", "dom_identity_sha256", "witness", "document", "elements",
            "text_ranges", "contrast_hits",
        }:
            raise RuntimeError(f"{page}/{state.get('state_id')}: state fields are not closed")
        _validate_settle(
            state["settle"], label=f"{page}/{state['state_id']}", policy=policy)
        document = state["document"]
        if set(document) != {"root", "body", "root_tokens"}:
            raise RuntimeError(f"{page}/{state['state_id']}: document fields are not closed")
        for name in ("root", "body"):
            if set(document[name]) != {
                "box", "client_width", "client_height", "scroll_width", "scroll_height",
                "rect_count", "hidden", "computed", "pseudo",
            }:
                raise RuntimeError(f"{page}/{state['state_id']}: {name} fields drift")
            validate_box(document[name]["box"], label=f"{page}/{state['state_id']}/{name}")
            validate_scroll(
                {key: document[name][key] for key in (
                    "client_width", "client_height", "scroll_width", "scroll_height")},
                label=f"{page}/{state['state_id']}/{name}",
            )
            nonnegative_integer(
                document[name]["rect_count"],
                label=f"{page}/{state['state_id']}/{name}/rect-count",
            )
            if (document[name]["rect_count"] == 0
                    and (document[name]["box"]["width"] != 0
                         or document[name]["box"]["height"] != 0)):
                raise RuntimeError(f"{page}/{state['state_id']}: false {name} rect count")
            if set(document[name]["computed"]) != set(policy["computed_style_fields"]):
                raise RuntimeError(f"{page}/{state['state_id']}: {name} style fields drift")
            _validate_pseudos(
                document[name]["pseudo"], set(policy["pseudo_style_fields"]),
                label=f"{page}/{state['state_id']}/{name}",
            )
        if (document["root"]["client_width"] != payload["viewport"]["width"]
                or document["root"]["client_height"] != payload["viewport"]["height"]):
            raise RuntimeError(f"{page}/{state['state_id']}: root viewport witness drift")
        if set(document["root_tokens"]) != set(policy["root_token_fields"]):
            raise RuntimeError(f"{page}/{state['state_id']}: root token cover drift")
        vector = state["elements"]
        if len(vector) != len(nodes):
            raise RuntimeError(f"{page}/{state['state_id']}: truncated element vector")
        for index, row in enumerate(vector):
            if set(row) != mutable_fields | {"box", "rect_count", "scroll", "computed", "pseudo"}:
                raise RuntimeError(f"{page}/{state['state_id']}/{index}: mutable fields drift")
            if row["index"] != index:
                raise RuntimeError(f"{page}/{state['state_id']}/{index}: vector misalignment")
            validate_box(row["box"], label=f"{page}/{state['state_id']}/{index}")
            nonnegative_integer(
                row["rect_count"], label=f"{page}/{state['state_id']}/{index}/rect-count")
            if (row["rect_count"] == 0
                    and (row["box"]["width"] != 0 or row["box"]["height"] != 0)):
                raise RuntimeError(
                    f"{page}/{state['state_id']}/{index}: zero rect count has nonzero box")
            validate_scroll(row["scroll"], label=f"{page}/{state['state_id']}/{index}")
            if set(row["computed"]) != set(policy["computed_style_fields"]):
                raise RuntimeError(f"{page}/{state['state_id']}/{index}: style fields drift")
            _validate_pseudos(
                row["pseudo"], set(policy["pseudo_style_fields"]),
                label=f"{page}/{state['state_id']}/{index}",
            )
        if state["dom_identity_sha256"] != expected_dom_identity:
            raise RuntimeError(f"{page}/{state['state_id']}: stable DOM identity drift")
        if memberships(payload, policy, state) != subjects:
            raise RuntimeError(f"{page}/{state['state_id']}: subject selector membership drift")
        ranges = state["text_ranges"]
        if len(ranges) != len(text_nodes):
            raise RuntimeError(f"{page}/{state['state_id']}: truncated text range vector")
        for index, row in enumerate(ranges):
            if set(row) != {"index", "rects"} or row["index"] != index:
                raise RuntimeError(f"{page}/{state['state_id']}: text range misalignment")
            for rect in row["rects"]:
                validate_box(rect, label=f"{page}/{state['state_id']}/text/{index}")
        validate_contrast_hits(
            payload, state, policy, label=f"{page}/{state['state_id']}"
        )
        _validate_rendered_state_witness(page, plan, state, nodes)
        if page == "studio":
            projection = [{key: row[key] for key in ("class", "hidden", "checked", "rect_count")}
                          | {"display": row["computed"]["display"]} for row in vector]
            state_vector_digests.append(hashlib.sha256(json.dumps(
                projection, allow_nan=False, sort_keys=True, separators=(",", ":")
            ).encode()).hexdigest())
    if page == "studio" and len(state_vector_digests) != len(set(state_vector_digests)):
        raise RuntimeError("studio rendered states contain a duplicated/default-laundered vector")


def load_bundle(theme: str, entries: list[dict] | None = None) -> list[dict]:
    """Load or validate the exact page x viewport bundle for one active profile.

    Injected mutation bundles use the same packet and provenance validation as committed artifacts.
    """
    if theme not in active_profiles():
        raise KeyError(f"unknown active theme {theme!r}")
    policy = load_policy()
    expected = [(page, row["width"]) for page in page_routes()
                for row in policy["matrix"]["viewports"]]
    if entries is None:
        validate_artifact_inventory()
        entries = []
        for page, viewport in expected:
            artifact = artifact_path(page, theme, viewport)
            encoded = artifact.read_bytes()
            entries.append({
                "facts": decode_packet_bytes(encoded),
                "provenance": json.loads(provenance_path(artifact).read_text(encoding="utf-8")),
                "_artifact_bytes": encoded,
            })
    if not isinstance(entries, list) or len(entries) != len(expected):
        raise RuntimeError(f"{theme}: rendered fact bundle must contain exactly {len(expected)} cells")
    observed: list[tuple[str, int]] = []
    for entry in entries:
        if (not isinstance(entry, dict)
                or set(entry) not in ({"facts", "provenance"},
                                      {"facts", "provenance", "_artifact_bytes"})):
            raise RuntimeError(f"{theme}: rendered fact bundle entry shape drift")
        payload = entry["facts"]
        page = payload.get("page")
        viewport = (payload.get("viewport") or {}).get("width")
        observed.append((page, viewport))
        if (page, viewport) not in expected:
            raise RuntimeError(f"{theme}: unknown rendered fact cell {(page, viewport)!r}")
        validate_packet(payload, page=page, theme=theme, viewport=viewport)
        validate_provenance(
            payload,
            entry["provenance"],
            page=page,
            theme=theme,
            viewport=viewport,
            artifact_bytes=entry.get("_artifact_bytes"),
        )
    if observed != expected:
        raise RuntimeError(f"{theme}: rendered fact cells are missing, duplicated, or out of order")
    return [{"facts": entry["facts"], "provenance": entry["provenance"]}
            for entry in entries]
