# Apple Dark — design doctrine (Apple HIG, cited)

> Design-system profile `apple-dark` (`contracts/design_profiles/apple-dark.json`). apple-dark
> ALREADY exists as `design_tokens.THEMES['apple-dark']` (the web theme), so the profile ALIASES
> that theme (`derived_from: "theme:apple-dark"`) — no hand-typed duplicate (codex H1). Values below
> carry their `developer.apple.com` URL; UIKit/empirical numbers are marked **[derived]**.

## Page chrome tokens

These tokens back the governed page shell as well as the component specimens:

| Property | Value | Source |
|---|---|---|
| Separator / hairline | `#38383a`, the dark-mode `opaqueSeparator` value; a quiet 1px separator, never pure white graph-paper chrome | https://developer.apple.com/design/human-interface-guidelines/color |
| Panel radius | `14px` **[derived]**, matching the rounded inset grouped-list container below; shell panels use the same restrained card radius, not the old uncited 26px bubbly radius | https://developer.apple.com/documentation/uikit/uitableview/style-swift.enum/insetgrouped |
| Tile radius | `12px`, aligned to `docs/DESIGN_SPEC.md` Part 0 card radius for smaller grouped surfaces | `docs/DESIGN_SPEC.md` Part 0 |

## Button (component-button)

apple-dark shares the **capsule** with liquid-glass but is a distinct COMPONENT: it is OPAQUE (not
glass), FLAT (zero shadow), and it DIMS on press instead of illuminating.

| Property | Value | Source |
|---|---|---|
| Shape | **Capsule** — `border-radius: 999px` (height/2); Apple system buttons are pill-shaped | https://developer.apple.com/design/human-interface-guidelines/buttons |
| Anatomy | **centered** label (a centered flex row; icon leading when present) — NOT Carbon's label-left/icon-right | https://developer.apple.com/design/human-interface-guidelines/buttons |
| Height (CTA) | **50px** [derived: iOS filled/CTA button] | https://developer.apple.com/design/human-interface-guidelines/buttons |
| Fill / material | **OPAQUE** (system accent `#0a84ff` filled / gray) — NOT a frosted-glass `backdrop-filter`; Liquid Glass is reserved for the functional/navigation layer, "not the content layer" | https://developer.apple.com/design/human-interface-guidelines/materials |
| Elevation | **ZERO box-shadow** — depth via material/tonal step, never a drop shadow | https://developer.apple.com/design/human-interface-guidelines/materials |
| State mechanic | **opacity-DIM press** — `opacity ~0.4` **[derived]** + `scale(0.97)` **[derived]**; the surface DIMS DOWN. NOT liquid's brightness-UP, NOT carbon's token-swap, NOT a Material ripple | https://developer.apple.com/design/human-interface-guidelines/buttons |
| Focus | **rounded system ring** following the capsule (`radius_follows: true`), accent `#0a84ff` — never a square inset | https://developer.apple.com/design/human-interface-guidelines/accessibility |
| Type | SF / `-apple-system`, Semibold 17 | https://developer.apple.com/design/human-interface-guidelines/typography |
| Motion | ~**250ms** `ease-in-out` **[derived]** | https://developer.apple.com/design/human-interface-guidelines/motion |

**Distinctness vs liquid-glass (the near-sibling — both capsules):** `material` opaque-fill (vs
liquid-glass frosted), `state_mechanic` opacity-dim (vs glass-brightness), `elevation` none (vs a
floating shadow), `focus_recipe` rounded-system-ring (vs capsule-halo) — **4 differing fingerprint
axes** — it clears the ≥3 quorum by exactly 1 (the **TIGHTEST** pair in the set, since it shares
`radius_px` + `anatomy` with liquid-glass; codex 1a-ii-B). vs carbon: radius, anatomy, mechanic,
focus, font all differ (5 axes).

## Chip / pill (component-chip)

An Apple pill on an **OPAQUE system fill** — the deliberate contrast to liquid-glass's translucency
(HIG reserves Liquid Glass for the floating layer; the content layer uses standard/opaque
materials). Chip px are **[derived]** (Apple publishes no chip metric).

| Property | Value | Source |
|---|---|---|
| Radius | **capsule** (radius = ½ height) — rendered 999px | https://developer.apple.com/design/human-interface-guidelines/ |
| Material | **opaque system fill** on an elevated dark surface — **no blur** (the glass contrast) | https://developer.apple.com/design/human-interface-guidelines/dark-mode · https://developer.apple.com/design/human-interface-guidelines/color |
| Anatomy | **centered label**, optional leading SF Symbol; no dismiss × | https://developer.apple.com/design/human-interface-guidelines/ |
| Type | **SF, sentence case**, never ALL-CAPS | https://developer.apple.com/design/human-interface-guidelines/typography |
| State mechanic | **opacity-dim** press (matches the apple-dark button) **[derived]** | https://developer.apple.com/design/human-interface-guidelines/buttons |
| Focus | **rounded system ring** (halo infers the capsule contour) | https://developer.apple.com/design/human-interface-guidelines/accessibility |

**Distinctness vs liquid-glass (near-sibling, both Apple capsules):** the load-bearing wall is
**material** (opaque-fill vs frosted glass), reinforced by **state** (opacity-dim vs glass-brightness),
**focus** (rounded ring vs capsule-halo), and **elevation** (none vs floating) — **4 fingerprint
axes**, the same honest basis as the button (radius + anatomy shared; material is the one strongly
doc-grounded axis, the others [derived] but consistently rendered). vs carbon: radius-token,
anatomy (× dismiss), state, focus, font all differ.

## Card / grouped metrics (component-card)

The Apple **inset grouped list** on an OPAQUE dark surface — the deliberate material contrast to
liquid-glass. Same grouped composition (ONE rounded container, chrome-less hairline-divided rows),
no frosted blur.

| Property | Value | Source |
|---|---|---|
| Composition | **ONE container, chrome-less rows** — LITERAL `insetGrouped` (rows are section content) | https://developer.apple.com/documentation/uikit/uitableview/style-swift.enum/insetgrouped |
| Material | **OPAQUE** elevated dark surface — NO blur (the wall vs liquid-glass); grouped background is a solid system fill | https://developer.apple.com/design/human-interface-guidelines/dark-mode · https://developer.apple.com/design/human-interface-guidelines/color |
| Container | rounded + inset (literal); radius ~14px **[derived]** | https://developer.apple.com/documentation/uikit/uitableview/style-swift.enum/insetgrouped |
| Divider | separator lines between rows (literal); ~1px **[derived]** | https://developer.apple.com/design/human-interface-guidelines/layout |
| Hierarchy | from TYPE — `label`/`secondaryLabel` vibrancy, not per-stat boxes (literal) | https://developer.apple.com/design/human-interface-guidelines/materials |

**Distinctness vs liquid-glass (the honest wall):** BOTH are rounded, hairline-divided Apple
grouped lists — radius and divider are **shared, not distinguishing**. The ONE honest deterministic
separator is **material**: `material_opaque` (no backdrop-filter) here vs `material_glass` there.
Per the research, we do NOT invent a second axis to pad a quorum. vs carbon: the SHAPE wall
(rounded vs square radius 0) + gridline-vs-hairline character. **"Content fills the card"** is
JUDGMENT → `candidate` + visual receipt, never fake-green.

## Shared dashboard realization

W3 makes the public dashboard a governed pageshell surface instead of a separate bespoke theme
implementation. Selecting Apple Dark activates its opaque page roles, rounded navigation/switcher
anatomy, and the opaque branches of the two grouped `webkit.card` readouts. The dashboard emitter
owns only data layout and typed hydration slots; profile literals remain in the design profile and
flow through the canonical declaration projection. This preserves the material distinction from
Liquid Glass on the same real content surface.
