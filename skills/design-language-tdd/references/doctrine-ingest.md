# Lane 0 — doctrine ingest: docs/examples -> obligations

Use this lane before `add-design-language.md`. The goal is not to summarize a design system. The
goal is to compile doctrine into a candidate-only obligation packet that the repo can lower into
profile data, render branches, fact gatherers, predicates, negative tests, and receipt obligations.

Scout is evidence-only here: it proposes obligations with `authority_status: candidate_only` and
`cannot_mark_done: true`. The target repo decides by RED tests, rendered facts, and receipts.

## Required output

Write or update `docs/design/<lang>.md` with numbered doctrine clauses and an ingest packet. Each row
must be small enough to become a field, predicate, negative case, or receipt obligation.

Required row shape:

```yaml a
- claim_id: <lang>-<component-or-axis>-NN
  source: <official URL or local cite>
  doctrine_claim: <one precise design rule>
  typed axes:
    component: button|chip|card|nav|table|chart|layout|type|material
    axis: radius|material|anatomy|state_mechanic|focus_recipe|elevation|density|type|structure|motion|responsive|contrast
    value: <typed value or enum>
  determinism: deterministic|visual
  lowers_to:
    profile_field: <components.button.radius_px or null>
    render_example: <what the renderer must emit or null>
    fact: <fact gatherer key or null>
    predicate: <predicate name or null>
  negative_cases:
    - <specific forbidden substitution that must fail>
  receipt_obligation:
    required: true|false
    reason: <why static parsing cannot prove this, or why receipt is confirmation only>
  refute_by: <what evidence would invalidate this candidate obligation>
  authority_status: candidate_only
  cannot_mark_done: true
```

## Determinism split

Mark a row `deterministic` only when this repo can observe the claim from rendered HTML/CSS/facts
without taste: radius, material presence, anatomy, state mechanic, focus recipe, elevation,
chromeless rows, visible dividers, token completeness, and render-derived distinctness.

Mark a row `visual` when it needs a browser or human-visible receipt: translucent contrast, clipping,
responsive fit, content fill, animation feel, visual rhythm, density feel, and screenshot-level
polish. A visual row may guide implementation, but it cannot become a passing static predicate until
the receipt gate can observe it.

## Promotion rule

Do not promote a language because the doc exists. Promote only when deterministic rows lower into
profile fields/predicates/negative tests and pass through rendered facts, and visual rows carry a
`receipt_obligation` or remain explicit candidate-only debt.

The model may propose. The rendered, tested shape decides.
