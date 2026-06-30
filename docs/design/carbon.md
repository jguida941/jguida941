# Carbon — design doctrine (IBM Carbon Design System v11, cited)

> Design-system profile `carbon` (`contracts/design_profiles/carbon.json`). Carbon is IBM's
> open-source system; it ships its OWN role map (no entry in the repo's web `THEMES`), so the
> profile carries literal Carbon token values (`derived_from: null`). Every value below carries
> its `carbondesignsystem.com` URL; UIKit/empirical anchors are marked **[derived]**.

## Button (component-button)

The Carbon button is the loudest contrast to the Apple capsules — it is **square, flat, and
asymmetric**, the opposite of a centered frosted pill.

| Property | Value | Source |
|---|---|---|
| Corner radius | **0px** on the button (Carbon's signature; the ONLY rounded control is the Tag) | https://carbondesignsystem.com/components/button/style/ · https://carbondesignsystem.com/elements/themes/overview/ |
| Anatomy | **label pinned hard-LEFT (16px), trailing icon pinned hard-RIGHT** in a ~64px gutter — a `space-between` row, NOT a centered label | https://carbondesignsystem.com/components/button/usage/ |
| Height (default/lg) | **48px** | https://carbondesignsystem.com/components/button/style/ |
| Padding | **16px** leading / **64px** trailing (icon gutter); 0 vertical beyond the 48px box | https://carbondesignsystem.com/components/button/style/ |
| Type | **IBM Plex Sans**, body-compact-01 **14px / weight 400** (Carbon emphasizes in 600 elsewhere, but button text is Regular 400, NOT 600) | https://carbondesignsystem.com/guidelines/typography/overview/ |
| State mechanic | **token SWAP** — hover/active change the discrete background token (`$button-primary` #0f62fe → `$button-primary-hover` #0353e9 → `$button-primary-active` #002d9c) with **NO** translucent `::after` state-layer, NO transform, NO opacity fade (the anti-Material tell) | https://carbondesignsystem.com/components/button/style/ · https://carbondesignsystem.com/elements/color/tokens/ |
| Focus | **2px square focus ring** (`inset` box-shadow, `$focus` #0f62fe + a `$background` inset) — the radius stays 0 | https://carbondesignsystem.com/components/button/style/ |
| Elevation | **flat — zero box-shadow** | https://carbondesignsystem.com/components/button/style/ |
| Motion | **70ms**, `productive` standard easing `cubic-bezier(0.2, 0, 0.38, 0.9)` **[derived: read from @carbon/styles motion tokens; easing not published as a literal on the button page]** | https://carbondesignsystem.com/elements/motion/overview/ |

**Distinctness vs the Apple capsules:** radius 0 (vs 999 capsule), `label-left-icon-right` DOM
(vs centered), token-swap press (vs glass-brightness / opacity-dim), 2px **square** focus (vs a
rounded halo/ring), flat zero-shadow, IBM Plex 400 (vs SF 600). The `distinctness_fingerprint`
over `{radius, state_mechanic, focus_recipe, anatomy, elevation}` forbids any convergence.
