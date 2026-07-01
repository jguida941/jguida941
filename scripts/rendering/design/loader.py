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


def _injected_group(derived_from) -> tuple[str | None, dict]:
    """The (alias-namespace, DTCG group) a profile derives from — built from the ONE source
    (`scripts.core.config` via `design_tokens`). `derived_from: "config"` injects `config`
    (liquid-glass == config, the SVG-parity anchor); `derived_from: "theme:<name>"` injects
    `theme` from `design_tokens.THEMES[<name>]` so a profile that mirrors an existing web theme
    (e.g. apple-dark) ALIASES it instead of hand-typing a duplicate (codex H1). A self-contained
    `derived_from: null` profile (e.g. carbon, which owns its palette) injects nothing."""
    from scripts.core import config
    from scripts.rendering import design_tokens as dt

    if derived_from == "config":
        return "config", {
            "color": dt.theme("liquid-glass"),        # role -> hex, == config (SVG-parity anchor)
            "radius": dt.radius("liquid-glass"),       # {panel, tile} == GLASS_RX / GLASS_TILE_RX
            "font": {"family": config.FONT_SANS},
        }
    if isinstance(derived_from, str) and derived_from.startswith("theme:"):
        theme = derived_from.split(":", 1)[1]
        if theme not in dt.THEMES:  # fail LOUD, not silent (codex 1a-ii-B #4)
            raise KeyError(f"derived_from 'theme:{theme}' — no such theme in design_tokens.THEMES")
        return "theme", {
            "color": dt.theme(theme),                  # role -> hex, == THEMES[theme] (single source)
            "radius": dt.radius(theme),
            # NOTE: THEMES carries no per-theme font, so `{theme.font.family}` resolves to
            # config.FONT_SANS (config-derived, not theme-derived). A future theme: profile needing
            # its OWN font must add a font source; the alias name does not imply per-theme fonts.
            "font": {"family": config.FONT_SANS},
        }
    return None, {}


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
    ns, grp = _injected_group(prof.get("derived_from"))
    if ns:
        groups[ns] = grp
    return _resolve_group(prof.get("tokens", {}), groups)
