"""Single design-token source — role-named, theme-able, shared by both projections.

This is the one place the design system's *semantics* live. The README SVG cards read
their colours from config.py (the default theme's raw values, kept identical here by a
parity contract); the web dashboard reads `emit_css_root()`. A THEME swaps colour +
material ONLY — the information architecture (type scale, spacing, radius) is constant,
sourced from config, so the same layout can wear any skin and stay legible. That
separation is the doctrine the web theme switcher shows off:

    IA = Power BI (constant)   x   Material = governed Liquid Glass (per-theme)

Adding a theme is one entry in THEMES (+ MATERIALS); the theme-system contract proves
it is complete, legible (WCAG AA), and restrained before it can ship.
"""
from __future__ import annotations

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

# Each theme maps EXACTLY the role schema to a hex value. The default theme's core
# roles equal config.py so the SVG and web default cannot drift (Law 3, token half).
THEMES: dict[str, dict[str, str]] = {
    # Governed Liquid Glass — the shipped Tokyo-Night dark glass (== config.py).
    "liquid-glass": {
        "ink-strong": config.TEXT_BRIGHT, "ink": config.TEXT, "ink-dim": config.TEXT_DIM,
        "surface": config.SURFACE_BASE, "surface-raised": config.SURFACE_RAISED,
        "backdrop": config.SURFACE_BACKDROP, "hairline": config.GLASS_HAIRLINE_HEX,
        "accent": config.CYAN,
        "status-success": config.GREEN, "status-warning": config.YELLOW, "status-danger": config.RED,
    },
    # Apple system dark — neutral near-black surfaces, one vivid system-blue accent,
    # heavier frost. SF-style restraint: colour only where it carries meaning.
    "apple-dark": {
        "ink-strong": "#f5f5f7", "ink": "#c7c7cc", "ink-dim": "#98989d",
        "surface": "#1c1c1e", "surface-raised": "#2c2c2e",
        "backdrop": "#000000", "hairline": "#ffffff",
        "accent": "#0a84ff",
        "status-success": "#30d158", "status-warning": "#ff9f0a", "status-danger": "#ff453a",
    },
    # Power BI dark — analytical slate, the Power BI blue accent, flatter material
    # (data-ink forward). Same IA, different material — proving the axes are separable.
    "power-bi": {
        "ink-strong": "#ffffff", "ink": "#d9dde3", "ink-dim": "#9aa0ab",
        "surface": "#20242b", "surface-raised": "#2b303a",
        "backdrop": "#14171c", "hairline": "#ffffff",
        "accent": "#2899f5",
        "status-success": "#1aab8a", "status-warning": "#f2c811", "status-danger": "#e0626d",
    },
}

# Material (governed glass) per theme — the blur/opacity/sheen that make the surface
# read as frosted glass. NOT a colour role (kept out of THEMES so the role schema stays
# exact); this is the "Material = Liquid Glass (governed)" axis varying per skin.
MATERIALS: dict[str, dict[str, float]] = {
    "liquid-glass": {"blur": 22, "saturate": 160, "surface_opacity": 0.55, "raised_opacity": 0.55, "sheen": 0.07},
    "apple-dark":   {"blur": 30, "saturate": 180, "surface_opacity": 0.60, "raised_opacity": 0.50, "sheen": 0.10},
    "power-bi":     {"blur": 6,  "saturate": 120, "surface_opacity": 0.92, "raised_opacity": 0.85, "sheen": 0.03},
}

# Human metadata for the theme switcher UI (label + one-line doctrine blurb).
THEME_META: dict[str, dict[str, str]] = {
    "liquid-glass": {"label": "Liquid Glass", "blurb": "Apple frosted glass · Tokyo Night"},
    "apple-dark":   {"label": "Apple Dark", "blurb": "System dark · one vivid accent"},
    "power-bi":     {"label": "Power BI", "blurb": "Analytical slate · flat data-ink"},
}


def roles() -> tuple[str, ...]:
    return ROLES


def theme(name: str | None = None) -> dict[str, str]:
    return dict(THEMES[name or DEFAULT_THEME])


def material(name: str | None = None) -> dict[str, float]:
    return dict(MATERIALS[name or DEFAULT_THEME])


# --- IA tokens (theme-INDEPENDENT) — one source: config.py ----------------------
def type_scale() -> dict[str, tuple[int, int]]:
    return {k: tuple(v) for k, v in config.TYPE_SCALE.items()}


def space() -> dict[str, int]:
    return dict(config.SPACE)


def radius() -> dict[str, int]:
    return {"panel": config.GLASS_RX, "tile": config.GLASS_TILE_RX}


# --- CSS emission ----------------------------------------------------------------
def _role_vars(name: str, indent: str = "  ") -> str:
    roles_map = THEMES[name]
    mat = MATERIALS[name]
    lines = [f"{indent}--{role}: {roles_map[role]};" for role in ROLES]
    lines.append(f"{indent}--glass-blur: {mat['blur']:g}px;")
    lines.append(f"{indent}--glass-saturate: {mat['saturate']:g}%;")
    lines.append(f"{indent}--surface-opacity: {mat['surface_opacity']:g};")
    lines.append(f"{indent}--raised-opacity: {mat['raised_opacity']:g};")
    lines.append(f"{indent}--sheen-opacity: {mat['sheen']:g};")
    return "\n".join(lines)


def _ia_vars(indent: str = "  ") -> str:
    r = radius()
    lines = [f"{indent}--radius-panel: {r['panel']}px;", f"{indent}--radius-tile: {r['tile']}px;"]
    for key, (size, weight) in type_scale().items():
        lines.append(f"{indent}--type-{key}: {size}px;")
        lines.append(f"{indent}--type-{key}-weight: {weight};")
    for key, val in space().items():
        lines.append(f"{indent}--space-{key}: {val}px;")
    lines.append(f"{indent}--font-sans: {config.FONT_SANS};")
    return "\n".join(lines)


def emit_css_root() -> str:
    """The web :root carries the DEFAULT theme's roles + the theme-independent IA
    vars; each other theme gets a [data-theme="name"] override block (colour/material
    only). Theme switching is a single attribute on <html>."""
    blocks = [":root {\n" + _role_vars(DEFAULT_THEME) + "\n" + _ia_vars() + "\n}"]
    for name in THEMES:
        if name == DEFAULT_THEME:
            continue
        blocks.append(f'[data-theme="{name}"] {{\n' + _role_vars(name) + "\n}")
    return "\n\n".join(blocks) + "\n"
