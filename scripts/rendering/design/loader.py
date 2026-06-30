"""P5-PROFILE-SPINE-b — the DTCG-subset profile loader (the thin VIEW; never the source).

A design profile's token block is W3C Design Tokens Format Module (DTCG, 2025.10) DATA:
`{ "$type": ..., "<token>": { "$value": ... } }`. The loader resolves it. For a
`derived_from: "config"` profile it injects a synthetic `config` token group built from
`scripts.core.config` via `design_tokens` (the EXISTING config-derivation, which is the
SVG-parity anchor) and resolves `{alias}` references — so the profile carries NO literal copy
of config values (single source). A re-literaled value or a broken alias makes the
derived-parity test (test_design_profiles_schema) redden.

Conservative subset (codex): `{group.token}` curly-brace alias resolution + typed leaves +
nested groups. `$ref` JSON-Pointer sub-addressing and chained-alias edge cases are DEFERRED.
candidate_only; decides no authority.
"""
from __future__ import annotations

import json
from pathlib import Path


def _profiles_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "contracts" / "design_profiles").is_dir():
            return parent / "contracts" / "design_profiles"
    raise RuntimeError("contracts/design_profiles not found")


def _config_token_group() -> dict:
    """The `config` DTCG group injected for `derived_from: config` profiles — pulled from
    `design_tokens` (which derives from `scripts.core.config`), so there is ONE source."""
    from scripts.core import config
    from scripts.rendering import design_tokens as dt

    return {
        "color": dt.theme("liquid-glass"),        # role -> hex, == config (SVG-parity anchor)
        "radius": dt.radius("liquid-glass"),       # {panel, tile} == GLASS_RX / GLASS_TILE_RX
        "font": {"family": config.FONT_SANS},
    }


def load(name: str) -> dict:
    """Read a profile / roster / index JSON verbatim (no resolution)."""
    return json.loads((_profiles_dir() / f"{name}.json").read_text(encoding="utf-8"))


def _resolve_value(value, groups: dict):
    """Resolve a single DTCG `$value`: a `{group.token...}` alias dereferences into `groups`;
    anything else is a literal."""
    if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
        node = groups
        for part in value[1:-1].split("."):
            node = node[part]
        return node
    return value


def _resolve_group(node: dict, groups: dict) -> dict:
    """Walk a DTCG group: skip `$`-prefixed metadata; a leaf has `$value`; else recurse."""
    out: dict = {}
    for key, child in node.items():
        if key.startswith("$"):
            continue
        if isinstance(child, dict) and "$value" in child:
            out[key] = _resolve_value(child["$value"], groups)
        elif isinstance(child, dict):
            out[key] = _resolve_group(child, groups)
    return out


def resolve_tokens(name: str) -> dict:
    """Load `<name>.json` and return its resolved token tree (aliases dereferenced)."""
    prof = load(name)
    groups: dict = {}
    if prof.get("derived_from") == "config":
        groups["config"] = _config_token_group()
    return _resolve_group(prof.get("tokens", {}), groups)
