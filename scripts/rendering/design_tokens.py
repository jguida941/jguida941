"""Web token bridge for the active design-profile roster.

The roster authority is `contracts/design_profiles/_index.json` (`active_design_profiles`).
This module is the legacy web projection bridge: it exposes the active roster as CSS
variables for `site/index.html`, while profile JSON remains the design-language source.

Adding a public theme means adding an active design profile and then adding its web bridge
projection here in the same slice. A reserved profile may not appear in these maps; the
theme-roster authority contract fails import if this bridge drifts from the active roster.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.core import config

# Role schema — semantic names only (never raw palette words), so a theme is one swap
# and every contract stays palette-agnostic.
ROLES = (
    "ink-strong", "ink", "ink-dim",
    "surface", "surface-raised", "backdrop",
    "hairline", "accent",
    "status-success", "status-warning", "status-danger",
)

DEFAULT_THEME = "liquid-glass"
THEME_STORAGE_KEY = "dash-theme"

def _profiles_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "contracts" / "design_profiles"
        if candidate.is_dir():
            return candidate
    raise RuntimeError("contracts/design_profiles not found")


def _active_design_profiles() -> tuple[str, ...]:
    index = json.loads((_profiles_dir() / "_index.json").read_text(encoding="utf-8"))
    return tuple(index["active_design_profiles"])


ACTIVE_THEME_NAMES = _active_design_profiles()


def _literal_profile_tokens(profile: str, group: str) -> dict:
    """Read literal DTCG `$value` leaves for self-owned profile token groups.

    Carbon owns its profile palette (`derived_from: null`), so the web bridge imports
    the profile literals instead of retyping a duplicate palette in Python.
    """
    prof = json.loads((_profiles_dir() / f"{profile}.json").read_text(encoding="utf-8"))
    values = {}
    for key, leaf in prof["tokens"][group].items():
        if key.startswith("$"):
            continue
        values[key] = leaf["$value"]
    return values


def _active_bridge_map(kind: str, rows: dict[str, dict]) -> dict[str, dict]:
    active = set(ACTIVE_THEME_NAMES)
    declared = set(rows)
    missing = sorted(active - declared)
    extra = sorted(declared - active)
    if missing or extra:
        raise KeyError(
            f"{kind} must match active_design_profiles exactly; "
            f"missing={missing}, extra={extra}"
        )
    return {name: rows[name] for name in ACTIVE_THEME_NAMES}


# Each theme maps EXACTLY the role schema to a hex value. The default theme's core
# roles equal config.py so the SVG and web default cannot drift (Law 3, token half).
THEMES: dict[str, dict[str, str]] = _active_bridge_map("THEMES", {
    # Governed Liquid Glass — the shipped Tokyo-Night dark glass (== config.py).
    "liquid-glass": {
        "ink-strong": config.TEXT_BRIGHT, "ink": config.TEXT, "ink-dim": config.TEXT_DIM,
        "surface": config.SURFACE_BASE, "surface-raised": config.SURFACE_RAISED,
        "backdrop": config.SURFACE_BACKDROP, "hairline": config.GLASS_HAIRLINE_HEX,
        "accent": config.CYAN,
        "status-success": config.GREEN, "status-warning": config.YELLOW, "status-danger": config.RED,
    },
    # IBM Carbon — profile-owned literal DTCG tokens projected into the public web bridge.
    "carbon": _literal_profile_tokens("carbon", "color"),
    # Apple system dark — neutral near-black surfaces, one vivid system-blue accent,
    # heavier frost. SF-style restraint: colour only where it carries meaning.
    "apple-dark": {
        "ink-strong": "#f5f5f7", "ink": "#c7c7cc", "ink-dim": "#98989d",
        "surface": "#1c1c1e", "surface-raised": "#2c2c2e",
        # hairline = HIG opaqueSeparator (dark) — a SUBTLE separator, never pure white at 100%
        # (design-audit #2: #ffffff read as graph-paper; no doctrine clause supported it)
        "backdrop": "#000000", "hairline": "#38383a",
        "accent": "#0a84ff",
        "status-success": "#30d158", "status-warning": "#ff9f0a", "status-danger": "#ff453a",
    },
})

# Material (governed glass) per theme — the blur/opacity/sheen that make the surface
# read as frosted glass. NOT a colour role (kept out of THEMES so the role schema stays
# exact); this is the "Material = Liquid Glass (governed)" axis varying per skin.
MATERIALS: dict[str, dict[str, float]] = _active_bridge_map("MATERIALS", {
    "liquid-glass": {"blur": 22, "saturate": 160, "surface_opacity": 0.55, "raised_opacity": 0.55, "sheen": 0.07},
    "carbon":       {"blur": 0,  "saturate": 100, "surface_opacity": 1.00, "raised_opacity": 1.00, "sheen": 0.00},
    "apple-dark":   {"blur": 30, "saturate": 180, "surface_opacity": 0.60, "raised_opacity": 0.50, "sheen": 0.10},
})

# Human metadata for the theme switcher UI (label + one-line doctrine blurb).
THEME_META: dict[str, dict[str, str]] = _active_bridge_map("THEME_META", {
    "liquid-glass": {"label": "Liquid Glass", "blurb": "Apple frosted glass · Tokyo Night"},
    "carbon":       {"label": "Carbon", "blurb": "IBM Carbon · flat structured UI"},
    "apple-dark":   {"label": "Apple Dark", "blurb": "System dark · one vivid accent"},
})

# Native control/chrome mode is part of the selected language, not page-local decoration.
# Carbon's shipped white (g10) theme is light; the two dark profiles declare dark surfaces.
# Sources: docs/design/carbon.md, docs/design/apple-dark.md, docs/design/liquid-glass.md.
COLOR_SCHEMES: dict[str, str] = _active_bridge_map("COLOR_SCHEMES", {
    "liquid-glass": "dark",
    "carbon": "light",
    "apple-dark": "dark",
})

# Per-theme INFORMATION ARCHITECTURE — radius + type overrides (over the config defaults).
# This is what makes each theme a different *website*, not a colour swap: Apple is
# rounder + larger, Carbon is square/structured/compact. The DEFAULT theme MUST equal config
# (SVG parity). `radius` keys: panel, tile. `type` overrides a subset of the type ladder
# {token: (size, weight)} — anything omitted inherits config.TYPE_SCALE. All sizes stay
# >= the 11px legibility floor. (Density/motion/charts are added in later P5 slices.)
# `density` (web only — the SVG cards don't use CSS padding; doesn't affect SVG parity)
# carries the per-theme spacing band that makes the BOXES different, not just the paint:
# panel_pad / tile_pad / gap (px) + a band label, grounded in each design language's docs
# (Apple HIG Layout: airy 32/24 padding, 24 gap, few large cards; Carbon: compact
# structured-list rhythm; Liquid Glass: the medium anchor).
THEME_IA: dict[str, dict] = _active_bridge_map("THEME_IA", {
    "liquid-glass": {  # type/radius == config (the anchor); medium density
        "radius": {"panel": config.GLASS_RX, "tile": config.GLASS_TILE_RX},
        "type": {},
        "density": {"band": "medium", "panel_pad": 28, "tile_pad": 14, "gap": 20, "tile_min": 280},
        # motion (docs/design/motion.md §2): the medium anchor, [derived]
        "motion": {"fast": 120, "base": 200, "slow": 400,
                   "ease-standard": "ease-in-out", "ease-enter": "ease-out", "ease-exit": "ease-in"},
    },
    "carbon": {  # IBM Carbon — square surfaces, compact spacing, restrained body scale
        "radius": _literal_profile_tokens("carbon", "radius"),
        "type": {"display": (40, 600), "metric_lg": (24, 600), "title": (18, 600), "body": (14, 400)},
        "density": {"band": "compact", "panel_pad": 20, "tile_pad": 12, "gap": 12, "tile_min": 180},
        # motion: Carbon Motion productive tokens fast-01/fast-02/moderate-02 + productive easings
        "motion": {"fast": 70, "base": 110, "slow": 240,
                   "ease-standard": "cubic-bezier(0.2, 0, 0.38, 0.9)",
                   "ease-enter": "cubic-bezier(0, 0, 0.38, 0.9)",
                   "ease-exit": "cubic-bezier(0.2, 0, 1, 0.9)"},
    },
    "apple-dark": {  # Apple HIG — generous radius + large display type + AIRY space, few large cards
        # panel 14 == the profile's own cited card radius (apple-dark.md "~14"); tile 12 ==
        # DESIGN_SPEC Part 0 card radius. 26/18 were uncited "bubbly" inflation (design-audit #5).
        "radius": {"panel": 14, "tile": 12},
        "type": {"display": (54, 600), "metric_lg": (30, 600), "title": (22, 600)},
        "density": {"band": "airy", "panel_pad": 32, "tile_pad": 24, "gap": 24, "tile_min": 380},
        # motion (motion.md §2): fluid, [derived] from the ~0.3s platform transition convention
        "motion": {"fast": 150, "base": 300, "slow": 500,
                   "ease-standard": "ease-out", "ease-enter": "ease-out", "ease-exit": "ease-in"},
    },
})

_DENSITY_DEFAULT = {"band": "medium", "panel_pad": 28, "tile_pad": 14, "gap": 20, "tile_min": 280}


def density(name: str | None = None) -> dict:
    return {**_DENSITY_DEFAULT, **THEME_IA.get(name or DEFAULT_THEME, {}).get("density", {})}


def roles() -> tuple[str, ...]:
    return ROLES


def theme(name: str | None = None) -> dict[str, str]:
    return dict(THEMES[name or DEFAULT_THEME])


def material(name: str | None = None) -> dict[str, float]:
    return dict(MATERIALS[name or DEFAULT_THEME])


def color_scheme(name: str | None = None) -> str:
    return COLOR_SCHEMES[name or DEFAULT_THEME]


# --- IA tokens (now PER-THEME: config defaults + the theme's THEME_IA overrides) ----
def type_scale(name: str | None = None) -> dict[str, tuple[int, int]]:
    base = {k: tuple(v) for k, v in config.TYPE_SCALE.items()}
    base.update({k: tuple(v) for k, v in THEME_IA.get(name or DEFAULT_THEME, {}).get("type", {}).items()})
    return base


def space(name: str | None = None) -> dict[str, int]:
    return dict(config.SPACE)  # density/spacing diverges in a later P5 slice


def radius(name: str | None = None) -> dict[str, int]:
    default = {"panel": config.GLASS_RX, "tile": config.GLASS_TILE_RX}
    default.update(THEME_IA.get(name or DEFAULT_THEME, {}).get("radius", {}))
    return default


# --- CSS emission ----------------------------------------------------------------
def css_declarations(name: str) -> dict[str, str]:
    """Return the one ordered profile-to-CSS declaration projection."""
    from scripts.rendering.design import loader

    if name not in ACTIVE_THEME_NAMES:
        raise KeyError(f"theme {name!r} is not active")
    resolved = loader.resolve_tokens(name)
    roles_map = resolved["color"]
    mat = MATERIALS[name]
    r = resolved["radius"]
    d = density(name)
    declarations: dict[str, str] = {f"--{role}": roles_map[role] for role in ROLES}
    declarations.update({
        "--glass-blur": f"{mat['blur']:g}px",
        "--glass-saturate": f"{mat['saturate']:g}%",
        "--surface-opacity": f"{mat['surface_opacity']:g}",
        "--raised-opacity": f"{mat['raised_opacity']:g}",
        "--sheen-opacity": f"{mat['sheen']:g}",
        "color-scheme": color_scheme(name),
        "--radius-panel": f"{r['panel']}px",
        "--radius-tile": f"{r['tile']}px",
        "--pad-panel": f"{d['panel_pad']}px",
        "--ps-pad": f"{d['panel_pad']}px",
        "--pad-tile": f"{d['tile_pad']}px",
        "--gap-grid": f"{d['gap']}px",
    })
    for key, (size, weight) in type_scale(name).items():
        declarations[f"--type-{key}"] = f"{size}px"
        declarations[f"--type-{key}-weight"] = str(weight)
    for key, val in space(name).items():
        declarations[f"--space-{key}"] = f"{val}px"
    motion = THEME_IA.get(name, {}).get("motion", {})
    if motion:
        for key in ("fast", "base", "slow"):
            declarations[f"--motion-{key}"] = f"{motion[key]}ms"
        for key in ("standard", "enter", "exit"):
            declarations[f"--ease-{key}"] = motion["ease-" + key]
    button = loader.load(name)["components"]["button"]
    declarations["--motion-switcher"] = f"{button['transition_ms']}ms"
    declarations["--ease-switcher"] = button["easing"]
    declarations["--button-hover-background"] = button.get("hover_css", {}).get(
        "background-color", "transparent"
    )
    declarations["--button-active-background"] = button.get("active_css", {}).get(
        "background-color", "transparent"
    )
    declarations["--font-sans"] = resolved["font"]["family"]
    return declarations


def _declaration_lines(name: str, indent: str = "  ") -> str:
    return "\n".join(f"{indent}{key}: {value};" for key, value in css_declarations(name).items())


def emit_css_root() -> str:
    """The web :root carries the DEFAULT theme's full axis (roles + material + IA); each
    other theme gets a [data-theme="name"] block carrying its OWN full axis (colour +
    material + per-theme radius/type), so flipping the theme reflows the whole page —
    not just its palette. Theme switching is a single attribute on <html>."""
    blocks = [":root {\n" + _declaration_lines(DEFAULT_THEME) + "\n}"]
    for name in THEMES:
        if name == DEFAULT_THEME:
            continue
        blocks.append(f'[data-theme="{name}"] {{\n' + _declaration_lines(name) + "\n}")
    return "\n\n".join(blocks) + "\n"
