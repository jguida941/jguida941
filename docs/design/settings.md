# Settings — the governed control plane (doctrine)

> The design twin of the bootstrap-RED gate: **an invalid combination is unconstructable.** This is
> a governance surface, not a new design language — it composes the existing cited languages
> (`docs/design/{liquid-glass,carbon,apple-dark}.md`) and refuses combinations that belong to none.
> ONE Python decider (`scripts/quality/settings_admissibility.py`); `site/settings.html` only
> DISPLAYS the verdict (no second JS decider). `candidate_only`.

## The model

A **Customization** = a `base` design language + per-component `overrides`
(`{component: {property: value}}`). `compose(base, overrides)` builds the composed profile.

A composition is **ADMISSIBLE** iff every overridden component, **as rendered**, is a FULL valid
instance of at least one active design language — i.e. its rendered facts (1) satisfy that
language's emitted deterministic invariants for the component AND (2) match that language's declared
`fingerprint` on every facts-observable axis (radius, material, anatomy, state-mechanic, focus,
elevation). A partial property mix that is a valid instance of **no** language is **inadmissible →
unconstructable**.

- Example refusal: a card with liquid-glass's **frosted material** + Carbon's **square 0-radius** is
  neither an Apple rounded grouped list (Apple = rounded, per
  [UIKit `insetGrouped`](https://developer.apple.com/documentation/uikit/uitableview/style-swift.enum/insetgrouped))
  nor a flat Carbon Tile (Carbon = flat, per
  [Carbon tile/usage](https://carbondesignsystem.com/components/tile/usage/) "do not add a drop
  shadow to tiles") — so it is refused.
- Fingerprint coverage (why axis-completeness matters): a profile need not carry an invariant for
  every axis (e.g. liquid-glass declares no button-anatomy invariant), so admissibility ALSO checks
  the rendered facts against the source language's fingerprint — a glass capsule wearing Carbon's
  `label-left-icon-right` DOM is a valid instance of no language, even though liquid-glass has no
  anatomy invariant.

## Why the render, not just the data

The verdict routes through the REAL render → fact-gather → predicate path (the `conform` machinery),
so a degenerate/empty render fails closed (the reason the anatomy gatherer was hardened to require
positive DOM evidence). A wholesale swap is admissible only if it **actually renders** as a valid
instance — e.g. liquid-glass's frosted button cannot be transplanted onto a non-glass base, because
the frosted material is the base's capability, so those cells are honestly reported unconstructable
rather than rubber-stamped. Constants are structural, not numeric ranges, so nothing here is
`[derived]`.

## The honesty boundary

- **Deterministic (pass/fail):** admissible-space membership + `conform()` over statically-parseable
  facts (radius, material/shadow presence, mechanic, focus geometry, anatomy with positive evidence,
  card composition). An invalid combination is a genuine constructive refusal.
- **Judgment / candidate / visual-receipt (never fake-green):** whether the composed theme *renders/
  looks* right — contrast over the composed material, content-fills, responsive-no-clip — stays
  `candidate` with a visual-receipt obligation deferred to the receipt gate. The claim is "the
  composition satisfies the admissible space and conforms to profile vN," never "the theme is
  correct" and never a pixel claim from a string match.
