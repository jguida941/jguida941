---
name: design-language-tdd
description: 'Add or govern a design language in the self-demonstrating design system by following the one data-flow — PROFILE (DATA) → RENDER (webkit) → INVARIANT (conform) → RECEIPT — RED-first. Use when adding a theme, a component, or an aspect contract. Each pass is data + only-new predicates that PROVE the result against cited docs, never a colour swap. Honest claim only: "satisfies the LANGUAGE profile vN — here are the receipts", never "is Apple".'
---

# design-language-tdd — the repeatable, self-proving engine

The design system has ONE data-flow, and everything (a theme, a component, an aspect) is added by
running it RED-first: **PROFILE (DATA) → RENDER (webkit) → INVARIANT (conform/predicate) → RECEIPT.**
The full architecture is `docs/plans/DESIGN-SYSTEM.md`; this skill is the disciplined loop for
extending it. It exists because "make it look like Apple / Carbon" is a CLAIM — a model hallucinates
design compliance as easily as code — so every adjective ("clean", "Apple-like", "dense") must resolve
to a cited value → a typed axis → a predicate or receipt obligation → rendered facts. The skill never
trusts the adjective; it makes the artifact PROVE it, and the showcase RENDERS that proof.

## The data-flow (the four seams)

- **PROFILE (data):** a design profile is DATA — `contracts/design_profiles/<lang>.json` in the W3C
  **DTCG** format (`$value`/`$type`/`{alias}`); the loader (`scripts/rendering/design/loader.py`) is a
  thin VIEW. The DEFAULT (liquid-glass) is `derived_from: config` — it ALIASES into `config.py` with no
  literal copy (single source / the SVG-parity anchor). Component anatomy + the distinctness fingerprint
  live at the profile TOP-LEVEL.
- **RENDER (webkit):** `scripts/rendering/webkit/components.py::render_<component>(profile, variant,
  state)` reads the DATA and emits HTML+CSS, branching on the per-profile **anatomy** so STRUCTURE
  differs (Carbon label-left/icon-right DOM vs a centered capsule), not just tokens.
- **INVARIANT (conform / decide):** `conform()` walks the profile's `invariants[]`; deterministic rows
  dispatch to the closed predicate library and DECIDE pass/fail from the rendered facts; judgment rows
  (e.g. contrast over translucent glass) demote to `candidate` — a review anchor + visual receipt,
  **never a fake pass** (ACT/axe `passed`/`failed`/`cantTell`).
- **RECEIPT:** the `[InvariantResult]` serialized to `assets/receipts/<lang>/` + visual receipts; the
  showcase + settings READ them to stamp each cell. The proof IS the product.

## Doctrine ingest comes first

Before adding a language, read `references/doctrine-ingest.md`. The scout/research pass is a
doctrine-to-contract compiler front-end: it emits candidate-only obligations, not authority. Its
output must include typed axes, negative cases, `refute_by`, and `receipt_obligation` rows that can
lower into profile fields, render examples, facts, predicates, and receipts. A design doc plus JSON
profile is not enough; the rendered artifact must satisfy the doctrine-derived obligations.

## Non-negotiable boundaries (read `references/boundaries.md`)

- **Honest claim, always:** "satisfies the `<language>` profile vN — here are the receipts." NEVER "is
  Apple". Every profile is `candidate_only` + `cannot_mark_done`. Mark empirical numbers `[derived]`.
- **Enforcement is LOCAL:** there is NO Rust kernel in this repo — pytest contracts + visual receipts
  are the only authority. (The kernel/relay is the SIBLING repos'; we mirror the discipline, not a
  phantom adjudicator.)
- **Determinism split — never a fake RED/green:** static-parseable facts (radius, anatomy, shadow,
  focus, elevation, token-only colour, contrast over a known opaque background) → deterministic
  predicate; renderer-dependent facts (contrast over blur, responsive-no-clip, motion feel) → candidate
  + visual receipt behind a declared headless-probe slice. Never claim deterministic-green you can't
  compute browserless.

## The per-slice method (domain steps only)

Slice lifecycle, role seats, review gates, and commit authority are governed by `AGENTS.md`
(operator process correction 2026-07-22); this skill owns no lifecycle and mints no verdict.

1. **Name the RED first** — the failing contract. A shape/move task's RED is `test_structural_layout`.
   (`python -m scripts.organization.bootstrap_red_ref "<task>" "<red>"`.)
2. **Declare every new file's home in the SAME slice** — `contracts/repo_layout.json` (source/test/
   site/design_profiles) AND a test's THREE places: `repo_layout test_layout.contracts`,
   `tests_layout_contract TEST_GROUPS.contracts`, AND a `DESIGN_CONTRACT_GROUPS` authority.
3. **Doc-ground** — cite every magic value to a primary doc URL in `docs/design/<lang>.md`.
4. **Implement** — DATA (+ only-new predicates / only-new render branches).
5. **Prove** — GREEN; **mutation-prove** each predicate (revert the cited value → it reddens); materialize
   each declared `receipt_obligation` via `scripts/quality/visual_receipts.py` — a DETERMINISTIC
   token-derived reconstruction (PIL) or rendered-CSS measurement whose `kind` NAMES its real producer,
   NOT a browser screenshot. The true headless/viewport probe is a deferred R4 aspect; never label a
   reconstruction as a screenshot.
6. **Gates** — the independent codex review and the commit run under `AGENTS.md`'s slice SOP and
   role seats; fold review disagreements RED-first.

## Lanes (workflow routing)

| You want to… | Read |
|---|---|
| turn docs/examples/screenshots into typed obligations before implementation | `references/doctrine-ingest.md` |
| add a new design language / theme (profile JSON + doctrine + character/distinctness) | `references/add-design-language.md` |
| add a component (a `components.<name>` block + a render branch + only-new predicates) | `references/add-component.md` |
| add or split a governed page aspect from rendered surface evidence | `references/add-page-aspect.md` |
| prove a theme/component + receipts + codex | `references/prove-theme.md` |
| the boundaries / honest claim / determinism split / org gate | `references/boundaries.md` |

## Required end state

A new theme = a `contracts/design_profiles/<lang>.json` (DTCG, every roster aspect emitted or
declared-deferred) + a cited `docs/design/<lang>.md` + usually zero new predicates; the distinctness
fingerprint pairwise-distinct from every other profile; every predicate mutation-proven; visual
receipts; **codex agrees**; the honest receipt recorded. Then "add Material / Fluent / Stripe" = run
this loop = another genuinely distinct, proven component set — DATA + only-new predicates, not a reskin.
