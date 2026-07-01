# Carbon — design doctrine (IBM Carbon Design System v11, cited)

> Design-system profile `carbon` (`contracts/design_profiles/carbon.json`). Carbon is IBM's
> open-source system; it ships its OWN role map, so the profile carries literal Carbon token
> values (`derived_from: null`). The public web `THEMES` bridge projects those profile-owned
> values because Carbon is an active design profile. Every value below carries its
> `carbondesignsystem.com` URL; UIKit/empirical anchors are marked **[derived]**.

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

## Tag / chip (component-chip)

The Carbon **Tag** is the system's ONE rounded control — proof the *component*, not just the
theme, carries shape: the Tag radius is a fixed **16px token** while the button radius is **0**.

| Property | Value | Source |
|---|---|---|
| Corner radius | **16px** fixed token (`border-radius` in the Tag SCSS; on the 18/24/32px heights it clamps to a pill, but it is a *fixed token*, NOT a dynamic capsule) | https://carbondesignsystem.com/components/tag/style/ |
| Heights | **sm 18 / md 24 (default) / lg 32px** | https://carbondesignsystem.com/components/tag/style/ |
| Inline padding | **`$spacing-03` = 8px** (lg `$spacing-04` 12px) **[derived from @carbon/styles tag SCSS]** | https://carbondesignsystem.com/components/tag/usage/ |
| Material | **flat — no blur, no shadow**; fill from component tokens (light: step-20 bg / step-70 text) | https://carbondesignsystem.com/components/tag/style/ · https://carbondesignsystem.com/elements/color/tokens/ |
| Anatomy | **dismissible**: optional leading 16px icon → label → **trailing `×` close button** (`label-dismiss`) | https://carbondesignsystem.com/components/tag/usage/ |
| Type | **IBM Plex Sans `label-01` = 12px / lh 16px / weight 400**, **sentence case** (Carbon never uppercases tags) | https://carbondesignsystem.com/elements/typography/type-sets/ |
| State mechanic | **background token-swap** (hover token, e.g. `$tag-hover-gray`) — NO filter / opacity | https://carbondesignsystem.com/components/tag/style/ |
| Focus | **`outline: 2px solid $focus` + `outline-offset: 1px`** — an OUTLINE, distinct from the button's `inset` square ring | https://carbondesignsystem.com/components/tag/style/ |

**Distinctness vs the Apple pills:** the fixed 16px token reads pill-like but is framed as
*fixed-token-vs-dynamic-capsule*; the load-bearing separators are the **dismissible `×` anatomy**,
**token-swap** state, **2px outline** focus (vs a halo/ring), and **IBM Plex** (vs SF) — four solid
axes independent of radius.

## Card / grouped metrics (component-card)

Carbon's answer to a multi-metric surface is a **flat, square Tile / structured list**, NOT a
rounded Apple grouped list and NOT one floating box per number.

| Property | Value | Source |
|---|---|---|
| Container radius | **0 (square)** — Carbon's brand signature; the Tile has no rounded corners | https://carbondesignsystem.com/components/tile/style/ |
| Elevation | **NONE — literal:** *"Do not add a drop shadow to tiles... Tiles reside on the same plane as the page background layer and do not have elevation."* | https://carbondesignsystem.com/components/tile/usage/ |
| Composition | **ONE shared container** — structured list = *"column header + data row"*; rows are content, not individual boxes | https://carbondesignsystem.com/components/structured-list/usage/ |
| Row divider | full-bleed **1px `$border-subtle`** gridline between rows | https://carbondesignsystem.com/components/data-table/style/ · https://carbondesignsystem.com/elements/color/tokens/ |
| Row anatomy | label/header cell + value/data cell on one line (horizontal), left-aligned | https://carbondesignsystem.com/components/structured-list/usage/ |
| Type | IBM Plex Sans; header `heading-compact-01` 14px semibold, value `body-compact-01` 14px regular | https://carbondesignsystem.com/components/data-table/style/ |
| Row height | structured list default **48px**, condensed 32px; padding `$spacing-05` 16px **[derived]** | https://carbondesignsystem.com/components/structured-list/style/ |

**The deterministic invariants** assert: single container (rows carry no independent chrome),
≥2 rows, 1px divider, horizontal row axis, `material_flat` (no blur AND no shadow), radius 0. The
**"content fills the Tile / no dead space"** law is JUDGMENT — a static parser sees declared boxes,
not rendered ink, so it ships `candidate` + a visual receipt, never a fake-green number.
