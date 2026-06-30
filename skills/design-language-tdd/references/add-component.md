# Lane: add-component

Add a component (button, chip, card, kpi, input, nav, table, chart, hero, type-specimen) to the
webkit library. A component is **DATA + a render branch + only-new predicates** — never a bespoke
per-theme template. Follow the per-slice SOP in `SKILL.md`; this lane is the component-specific shape.

## What a component is, across the four seams

1. **PROFILE (data):** each profile gains a `components.<name>` block carrying the cited anatomy +
   geometry + state mechanic + focus recipe + a per-component **`fingerprint`** (the distinctness
   substrate), e.g. the button's `{radius_px, state_mechanic, focus_recipe, anatomy, material,
   elevation}`. Structural axes (e.g. Carbon `label-left-icon-right` vs `centered-capsule`) are DATA,
   not code.
2. **RENDER:** add `render_<name>(profile, variant, state) -> (html, css)` in
   `scripts/rendering/webkit/components.py`, **branching on `anatomy`** so two languages emit different
   DOM. Colour is token-only (resolved via the loader); material is single-sourced (no literals).
3. **INVARIANT:** add only the component's NEW predicates to `scripts/contracts/design_predicates.py`
   (reuse the library otherwise). Two kinds:
   - **character** (per profile): the rendered output carries the cited values AND excludes the OTHER
     languages' mechanics (a mutually-exclusive triple — e.g. carbon press is a token-swap AND not a
     filter AND not an opacity-dim).
   - **distinctness** (across profiles): the per-component `fingerprint` is pairwise-distinct on a
     QUORUM (≥3 axes). Flip the roster aspect `component-<name>` from `deferred` → `emitted` only when
     a real deterministic predicate exists.
4. **RECEIPT:** the component's `{variant × state}` cells render into the showcase matrix, each stamped
   with its `InvariantResult`; renderer-dependent rows (contrast/responsive) ship `candidate` + a PNG.

## Steps (RED-first)

1. **RED** — `tests/contracts/test_design_<name>.py` (authority `webkit`): import `render_<name>` +
   read the profiles → fails (ModuleNotFound / missing `components.<name>`). Declare its 3 homes.
2. **Doc-ground** — verify each constant against the primary doc URL in `docs/design/<lang>.md`
   FIRST; mark `[derived]` anything not literally published. Never hard-code an unverified number into
   a deterministic predicate.
3. **Implement** — add `components.<name>` to each profile + the `render_<name>` anatomy branches +
   only-new predicates.
4. **Prove** — character (cited values, mutually-exclusive mechanic) + distinctness (fingerprint
   quorum) GREEN; **mutation-prove** (collapse a signature axis — e.g. carbon radius 0→999 → reds
   character AND distinctness); capture the matrix receipt at the true viewport.
5. **Codex** on the diff (inline) → fold RED-first → commit when green + codex agrees.

## Worked example (the button, instance #1)

`components.button` carried `anatomy` (centered-capsule / label-left-icon-right), `radius_px`,
`state_mechanic` (glass-brightness / token-swap / opacity-dim), `focus_recipe`, `elevation_shadow`,
and a fingerprint. `render_button` branches on anatomy (a trailing `<svg>` sibling + `space-between`
for Carbon vs a centered label). The contract proved liquid-glass = 999 capsule + glass +
brightness-up, carbon = square + label-left/icon-right + token-swap + 2px square focus + flat, and the
two fingerprints pairwise-distinct — mutation-proven. Adding a chip next = the same shape, only the
chip's new predicates.
