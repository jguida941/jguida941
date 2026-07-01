# Apple Dark — design doctrine (Apple HIG, cited)

> Design-system profile `apple-dark` (`contracts/design_profiles/apple-dark.json`). apple-dark
> ALREADY exists as `design_tokens.THEMES['apple-dark']` (the web theme), so the profile ALIASES
> that theme (`derived_from: "theme:apple-dark"`) — no hand-typed duplicate (codex H1). Values below
> carry their `developer.apple.com` URL; UIKit/empirical numbers are marked **[derived]**.

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
