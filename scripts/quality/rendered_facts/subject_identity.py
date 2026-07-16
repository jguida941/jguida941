"""Closed selector membership and stable DOM identity for rendered-fact packets."""
from __future__ import annotations

import hashlib
import json
import re


IDENTITY_DOMAIN = "RenderedDomIdentity/v1\0"
SELECTOR_LANGUAGE = "rendered-subject-selector-v1"
_IDENT = r"[a-z][a-z0-9-]*"
_ATTR = re.compile(rf"(?:href|type|for|role|tabindex|contenteditable|data-{_IDENT})$")
_TAG = re.compile(rf"{_IDENT}")
_CLASS = re.compile(rf"\.({_IDENT})")
_PRESENT = re.compile(rf"\[({_IDENT})\]")
_EQUAL = re.compile(rf'\[({_IDENT})=(?:"([a-zA-Z0-9_-]+)"|([a-zA-Z0-9_-]+))\]')
_NOT_EQUAL = re.compile(
    rf':not\(\[({_IDENT})=(?:"([a-zA-Z0-9_-]+)"|([a-zA-Z0-9_-]+))\]\)'
)


def _attribute(name: str) -> str:
    if not _ATTR.fullmatch(name):
        raise RuntimeError(f"rendered selector uses unsupported attribute {name!r}")
    return name


def compile_selector(source: str, *, lane: str) -> list[dict]:
    if not isinstance(source, str) or not source or any(char.isspace() for char in source):
        raise RuntimeError("rendered selector is empty or contains unsupported whitespace")
    compounds = []
    for part in source.split(","):
        if not part:
            raise RuntimeError("rendered selector contains an empty list member")
        offset = 0
        tag = None
        match = _TAG.match(part)
        if match:
            tag, offset = match.group(), match.end()
        classes: list[str] = []
        attributes: list[dict] = []
        while offset < len(part):
            for kind, pattern in (
                ("class", _CLASS), ("not-equals", _NOT_EQUAL),
                ("equals", _EQUAL), ("present", _PRESENT),
            ):
                match = pattern.match(part, offset)
                if not match:
                    continue
                if kind == "class":
                    classes.append(match.group(1))
                else:
                    name = _attribute(match.group(1))
                    value = None if kind == "present" else (match.group(2) or match.group(3))
                    attributes.append({"name": name, "operator": kind, "value": value})
                offset = match.end()
                break
            else:
                raise RuntimeError(f"unsupported rendered selector syntax near {part[offset:]!r}")
        compounds.append({"tag": tag, "classes": classes, "attributes": attributes})
    if lane == "contrast" and not (
        len(compounds) == 1 and compounds[0]["tag"] is None
        and len(compounds[0]["classes"]) == 1 and not compounds[0]["attributes"]
    ):
        raise RuntimeError("contrast selectors must be exactly one class")
    if lane == "density":
        row = compounds[0] if len(compounds) == 1 else {}
        attrs = row.get("attributes", [])
        if (row.get("tag") is not None or len(row.get("classes", [])) != 1
                or len(attrs) > 1 or any(
                    attr["operator"] != "present" or not attr["name"].startswith("data-")
                    for attr in attrs)):
            raise RuntimeError("density selectors must be one class plus optional data presence")
    if lane not in {"interactive", "contrast", "density"}:
        raise RuntimeError(f"unknown rendered selector lane {lane!r}")
    return compounds


def compiled_policy(policy: dict) -> dict:
    if policy["subject_identity"]["selector_language"] != SELECTOR_LANGUAGE:
        raise RuntimeError("rendered subject selector language drift")
    return {
        "interactive": compile_selector(policy["interactive_selector"], lane="interactive"),
        "contrast": {row["id"]: compile_selector(row["selector"], lane="contrast")
                     for row in policy["contrast_subjects"]},
        "density": {page: {row["selector"]: compile_selector(
            row["selector"], lane="density") for row in rows}
            for page, rows in policy["density_surfaces"].items()},
    }


def _attr_value(node: dict, name: str):
    return node["data"].get(name) if name.startswith("data-") else node.get(name)


def matches(node: dict, state_row: dict, compounds: list[dict]) -> bool:
    for compound in compounds:
        if compound["tag"] is not None and node["tag"] != compound["tag"]:
            continue
        classes = state_row["class"].split()
        if any(name not in classes for name in compound["classes"]):
            continue
        matched = True
        for attr in compound["attributes"]:
            value = _attr_value(node, attr["name"])
            if attr["operator"] == "present":
                result = value is not None
            else:
                result = value == attr["value"]
                if attr["operator"] == "not-equals":
                    result = not result
            if not result:
                matched = False
                break
        if matched:
            return True
    return False


def memberships(packet: dict, policy: dict, state: dict) -> dict:
    compiled = compiled_policy(policy)
    nodes, rows = packet["nodes"], state["elements"]

    def indices(selector):
        return [index for index, node in enumerate(nodes)
                if matches(node, rows[index], selector)]

    return {
        "interactive": indices(compiled["interactive"]),
        "contrast": {key: indices(selector)
                     for key, selector in compiled["contrast"].items()},
        "density": {key: indices(selector)
                    for key, selector in compiled["density"][packet["page"]].items()},
    }


def dom_identity_projection(nodes: list[dict], text_nodes: list[dict], policy: dict) -> list:
    node_rows = []
    for node in nodes:
        row = []
        for field in policy["stable_node_fields"]:
            value = node[field]
            row.append(sorted(value.items()) if field == "data" else value)
        node_rows.append(row)
    text_rows = [[row[field] for field in policy["text_node_fields"]] for row in text_nodes]
    return [node_rows, text_rows]


def dom_identity_sha256(nodes: list[dict], text_nodes: list[dict], policy: dict) -> str:
    projection = dom_identity_projection(nodes, text_nodes, policy)
    encoded = (IDENTITY_DOMAIN + json.dumps(
        projection, allow_nan=False, ensure_ascii=False, separators=(",", ":")
    )).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
