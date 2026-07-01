"""P5 visual receipt producer for deferred design-language claims.

The conformance runner keeps visual/runtime rows honest by leaving them as
``candidate``. This module materializes the receipt artifacts those rows require:
contrast probes as JSON and card-fill viewport receipts as PNGs. It does not
promote a claim to ``pass``; it only turns ``receipt_status`` from pending to
present by writing the declared artifact.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

# The ONLY honest receipt kinds — each NAMES its real producer (no capability it does not have).
# `rendered-css-contrast-probe` computes sRGB contrast from the rendered component CSS (NOT a
# headless browser). `token-derived-reconstruction` is a deterministic PIL redraw of the card
# structure from the profile tokens (NOT a viewport screenshot). The real headless-render probe is
# a deferred R4 aspect (declared-deferred in the roster), never faked here.
CONTRAST_KIND = "rendered-css-contrast-probe"
CARD_KIND = "token-derived-reconstruction"
HONEST_KINDS = frozenset({CONTRAST_KIND, CARD_KIND})


def _root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "contracts" / "design_profiles").is_dir():
            return p
    raise RuntimeError("repo root not found")


def provenance_path(artifact: str) -> str:
    """The provenance sidecar path for a reconstruction artifact: `<artifact>.provenance.json`."""
    return f"{artifact}.provenance.json"


@dataclass(frozen=True)
class VisualReceipt:
    profile: str
    invariant_id: str
    aspect: str
    kind: str
    artifact: str
    law: str
    refute_by: str
    reason: str

    @property
    def component(self) -> str:
        return self.aspect.removeprefix("component-")


def _active_profiles() -> list[str]:
    idx = json.loads((_root() / "contracts" / "design_profiles" / "_index.json").read_text(encoding="utf-8"))
    return idx["active_design_profiles"]


def expected_visual_receipts() -> list[VisualReceipt]:
    """All required visual/probe artifacts, as declared by active profiles."""
    from scripts.rendering.design import loader

    out: list[VisualReceipt] = []
    for profile in _active_profiles():
        for inv in loader.load(profile).get("invariants", []):
            obligation = inv.get("receipt_obligation") or {}
            if not obligation.get("required"):
                continue
            out.append(VisualReceipt(
                profile=profile,
                invariant_id=inv["invariant_id"],
                aspect=inv["aspect"],
                kind=obligation["kind"],
                artifact=obligation["artifact"],
                law=inv.get("law", ""),
                refute_by=inv.get("refute_by", ""),
                reason=obligation.get("reason", ""),
            ))
    return out


def _signature_variant(component: dict) -> str:
    variants = component.get("variants", [])
    for variant in variants:
        if variant in ("prominent", "primary", "filled") or variant.endswith("-primary"):
            return variant
    return variants[0] if variants else "default"


def _variant(profile: str, component: str) -> str:
    from scripts.rendering.design import loader

    comp = loader.load(profile)["components"][component]
    if component == "button":
        return _signature_variant(comp)
    return comp.get("variants", ["default"])[0]


def _component_markup(profile: str, component: str) -> tuple[str, str, str]:
    from scripts.rendering.webkit.components import render_button, render_card, render_chip

    variant = _variant(profile, component)
    if component == "button":
        html, css = render_button(profile, variant, "rest")
    elif component == "chip":
        html, css = render_chip(profile, variant, "rest")
    elif component == "card":
        html, css = render_card(profile, variant, "rest")
    else:
        raise KeyError(f"unsupported component: {component}")
    return variant, html, css


def _base_rule(css: str) -> str:
    match = re.search(r"\.[\w-]+\s*\{([^}]*)\}", css)
    if not match:
        raise ValueError("rendered component CSS has no base rule")
    return match.group(1)


def _decl(css_body: str, name: str) -> str | None:
    matches = re.findall(rf"{name}:\s*([^;]+)", css_body)
    return matches[-1].strip() if matches else None


def _hex_to_rgba(value: str) -> tuple[float, float, float, float]:
    h = value.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) != 6:
        raise ValueError(f"unsupported hex colour: {value}")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (1.0,)


def _rgb_to_rgba(value: str) -> tuple[float, float, float, float]:
    nums = [p.strip() for p in re.search(r"rgba?\(([^)]+)\)", value).group(1).split(",")]
    if len(nums) == 3:
        nums.append("1")
    return float(nums[0]), float(nums[1]), float(nums[2]), float(nums[3])


def _color_srgb_to_rgba(value: str) -> tuple[float, float, float, float]:
    match = re.search(r"color\(srgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s*/\s*([\d.]+))?\)", value)
    if not match:
        raise ValueError(f"unsupported srgb colour: {value}")
    alpha = float(match.group(4)) if match.group(4) is not None else 1.0
    return float(match.group(1)) * 255, float(match.group(2)) * 255, float(match.group(3)) * 255, alpha


def _parse_color(value: str) -> tuple[float, float, float, float]:
    v = value.strip()
    if v == "transparent":
        return 0.0, 0.0, 0.0, 0.0
    if v == "white":
        return 255.0, 255.0, 255.0, 1.0
    if v == "black":
        return 0.0, 0.0, 0.0, 1.0
    if v.startswith("#"):
        return _hex_to_rgba(v)
    if v.startswith("rgb(") or v.startswith("rgba("):
        return _rgb_to_rgba(v)
    if v.startswith("color(srgb"):
        return _color_srgb_to_rgba(v)
    mix = re.search(r"color-mix\(in srgb,\s*(#[0-9a-fA-F]{3,6})\s+([\d.]+)%,\s*transparent\)", v)
    if mix:
        r, g, b, _ = _hex_to_rgba(mix.group(1))
        return r, g, b, float(mix.group(2)) / 100.0
    raise ValueError(f"unsupported colour: {value}")


def _composite(fg: tuple[float, float, float, float], bg: tuple[float, float, float, float]) -> tuple[int, int, int]:
    fr, fg_g, fb, fa = fg
    br, bg_g, bb, ba = bg
    alpha = fa + ba * (1 - fa)
    if alpha <= 0:
        return 0, 0, 0
    r = (fr * fa + br * ba * (1 - fa)) / alpha
    g = (fg_g * fa + bg_g * ba * (1 - fa)) / alpha
    b = (fb * fa + bb * ba * (1 - fa)) / alpha
    return round(r), round(g), round(b)


def _rgb_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _luminance_channel(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    l1 = 0.2126 * _luminance_channel(fg[0]) + 0.7152 * _luminance_channel(fg[1]) + 0.0722 * _luminance_channel(fg[2])
    l2 = 0.2126 * _luminance_channel(bg[0]) + 0.7152 * _luminance_channel(bg[1]) + 0.0722 * _luminance_channel(bg[2])
    light, dark = max(l1, l2), min(l1, l2)
    return (light + 0.05) / (dark + 0.05)


def contrast_receipt_payload(receipt: VisualReceipt) -> dict:
    """Deterministic probe payload from rendered component CSS.

    Browser style probes can feed the same colour fields later, but the committed
    receipt stays stable: it is derived from the renderer output and explicitly
    remains candidate-only.
    """
    from scripts.rendering.design import loader

    variant, html, css = _component_markup(receipt.profile, receipt.component)
    body = _base_rule(css)
    fg_css = _decl(body, "color")
    bg_css = _decl(body, "background")
    if not fg_css or not bg_css:
        raise ValueError(f"{receipt.profile}/{receipt.invariant_id}: missing rendered color/background")
    tokens = loader.resolve_tokens(receipt.profile).get("color", {})
    backdrop_css = tokens.get("backdrop", "#ffffff")
    backdrop = _parse_color(backdrop_css)
    fg = _composite(_parse_color(fg_css), backdrop)
    bg = _composite(_parse_color(bg_css), backdrop)
    ratio = contrast_ratio(fg, bg)
    return {
        "contract_id": "DesignVisualReceipt",
        "profile": receipt.profile,
        "invariant_id": receipt.invariant_id,
        "component": receipt.component,
        "variant": variant,
        "kind": receipt.kind,
        "status": "present",
        "authority_status": "candidate_only",
        "cannot_mark_done": True,
        "producer": "scripts/quality/visual_receipts.py",
        "probe_backend": "rendered-css-contrast",
        "law": receipt.law,
        "refute_by": receipt.refute_by,
        "rendered_html": html,
        "rendered_css": css,
        "foreground_css": fg_css,
        "background_css": bg_css,
        "backdrop_css": backdrop_css,
        "foreground": _rgb_hex(fg),
        "background": _rgb_hex(bg),
        "contrast_ratio": round(ratio, 2),
        "threshold_ratio": 4.5,
        "meets_threshold": ratio >= 4.5,
        "claim_status": "measured-candidate",
    }


def write_contrast_receipt(receipt: VisualReceipt) -> Path:
    out = _root() / receipt.artifact
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(contrast_receipt_payload(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


_CARD_ROW_COUNT = 3  # a grouped card holds N metric rows (>=2) — the anti "one box per stat" structure


def _draw_card_png(receipt: VisualReceipt, out: Path) -> None:
    """A DETERMINISTIC token-derived reconstruction of the card STRUCTURE — one container (radius
    from the profile) holding N hairline-divided rows, each with a quiet label bar + a prominent
    value bar (ink lands ACROSS the row, not floating in a giant box). Deliberately TEXT-FREE:
    PIL's default-font text rendering is non-deterministic across process invocations, which would
    make a committed, drift-guarded PNG unreliable; the row ink-bars carry the same 'content fills
    the row' evidence without a font dependency. NOT a browser render."""
    from PIL import Image, ImageDraw
    from scripts.rendering.design import loader

    tokens = loader.resolve_tokens(receipt.profile).get("color", {})
    card = loader.load(receipt.profile)["components"]["card"]
    bg = _composite(_parse_color(tokens.get("backdrop", "#ffffff")), (255, 255, 255, 1))
    surface = _composite(_parse_color(tokens.get("surface-raised", tokens.get("surface", "#ffffff"))), (*bg, 1))
    hairline = _composite(_parse_color(tokens.get("hairline", "#cccccc")), (*surface, 1))
    label = _composite(_parse_color(tokens.get("ink-dim", "#777777")), (*surface, 1))
    value = _composite(_parse_color(tokens.get("ink-strong", "#111111")), (*surface, 1))

    img = Image.new("RGB", (420, 220), bg)
    draw = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 20, 34, 400, 186
    radius = int(card.get("radius_px", 0))
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=surface, outline=hairline, width=1)
    row_h = (y1 - y0) // _CARD_ROW_COUNT
    bar_h = 8
    for idx in range(_CARD_ROW_COUNT):
        y = y0 + idx * row_h
        if idx:                                     # 1px hairline between adjacent rows
            draw.line([(x0, y), (x1, y)], fill=hairline, width=1)
        by = y + (row_h - bar_h) // 2
        draw.rectangle([x0 + 16, by, x0 + 16 + 128, by + bar_h], fill=label)   # label ink (left)
        draw.rectangle([x1 - 16 - 72, by, x1 - 16, by + bar_h], fill=value)    # value ink (right)
    img.save(out)


def png_tile_digest(path: Path, grid: int = 6) -> list:
    """Per-tile per-channel mean over a `grid`×`grid` tiling — a SPATIAL summary (codex): a layout
    change that preserves the GLOBAL mean (e.g. a bar moved left<->right) still shifts specific
    tiles, so the drift guard reddens. Decoded-pixel means (not file bytes) stay portable across
    PIL/zlib builds; a small per-tile tolerance absorbs any sub-pixel AA jitter."""
    from PIL import Image, ImageStat
    with Image.open(path) as img:
        rgb = img.convert("RGB")
        w, h = rgb.size
        tiles = []
        for gy in range(grid):
            for gx in range(grid):
                box = (gx * w // grid, gy * h // grid, (gx + 1) * w // grid, (gy + 1) * h // grid)
                tiles.append([round(v, 2) for v in ImageStat.Stat(rgb.crop(box)).mean])
    return tiles


def png_summary(path: Path) -> dict:
    from PIL import Image, ImageStat

    with Image.open(path) as img:
        rgb = img.convert("RGB")
        stat = ImageStat.Stat(rgb)
        extrema = rgb.getextrema()
    nonblank = any(lo != hi for lo, hi in extrema)
    return {
        "format": img.format or "PNG",
        "width": rgb.width,
        "height": rgb.height,
        "mean": [round(v, 2) for v in stat.mean],
        "nonblank": nonblank,
    }


def _card_provenance_payload(receipt: VisualReceipt) -> dict:
    return {
        "contract_id": "DesignReceiptProvenance",
        "profile": receipt.profile,
        "invariant_id": receipt.invariant_id,
        "artifact": receipt.artifact,
        "kind": receipt.kind,
        "probe_backend": "pil-reconstruction",
        "producer": "scripts/quality/visual_receipts.py",
        "authority_status": "candidate_only",
        "cannot_mark_done": True,
        "claim_status": "reconstruction-candidate",
        "note": ("a deterministic token-derived PIL redraw of the card structure (radius, rows, "
                 "hairlines) from the profile tokens; NOT a browser render. The real headless-render "
                 "probe is a deferred R4 aspect, authored live-wired RED-first when it lands."),
    }


def write_card_provenance(receipt: VisualReceipt) -> Path:
    out = _root() / provenance_path(receipt.artifact)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_card_provenance_payload(receipt), indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    return out


def write_card_receipt(receipt: VisualReceipt) -> Path:
    out = _root() / receipt.artifact
    out.parent.mkdir(parents=True, exist_ok=True)
    _draw_card_png(receipt, out)
    summary = png_summary(out)
    if not summary["nonblank"] or summary["width"] <= 0 or summary["height"] <= 0:
        raise RuntimeError(f"{receipt.artifact}: generated PNG is blank/invalid")
    write_card_provenance(receipt)   # every reconstruction carries its honest provenance sidecar
    return out


def write_visual_receipt(receipt: VisualReceipt) -> Path:
    if receipt.kind == CONTRAST_KIND:
        return write_contrast_receipt(receipt)
    if receipt.kind == CARD_KIND:
        return write_card_receipt(receipt)
    raise KeyError(f"unsupported receipt kind: {receipt.kind}")


def write_all_visual_receipts() -> list[Path]:
    return [write_visual_receipt(receipt) for receipt in expected_visual_receipts()]


def main() -> None:
    for path in write_all_visual_receipts():
        print(path.relative_to(_root()))


if __name__ == "__main__":
    main()
