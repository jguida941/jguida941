# Lane A+B — add a design language: doctrine obligations → profile → closed invariant set

The goal: turn a named design language into MEASURABLE values + testable invariants, grounded in its
real docs. This is what stops a theme from being a colour swap or a model taste claim.

## A. Ingest doctrine → `docs/design/<lang>.md`

1. Read `doctrine-ingest.md` first. Do not write prose-only doctrine. Produce candidate-only rows with
   typed axes, negative cases, `refute_by`, and `receipt_obligation`.
2. Pull primary sources (official guidelines such as developer.apple.com/design, m3.material.io,
   fluent2.microsoft.design, carbondesignsystem.com, polaris.shopify.com, atlassian.design, etc.) plus
   any local/vendored instructions the target provides.
3. Write `docs/design/<lang>.md`: every doctrine clause numbered with an inline source URL and an
   ingest packet row. Capture deterministic axes such as **shape**, **material**, **typography**,
   **component anatomy**, **state mechanic**, **focus recipe**, **elevation**, **card/list structure**,
   and **forbidden substitutions**. Capture visual/candidate axes such as responsive fit, translucent
   contrast, content fill, motion feel, and visual rhythm as receipt obligations, not static greens.

## B. Derive the closed invariant set (RED-first)

For each deterministic obligation emit a typed value and a red-now/green-after assertion. For each
visual obligation emit candidate-only receipt debt.

1. **Profile values → `contracts/design_profiles/<lang>.json`:**
   - DTCG token groups and aliases.
   - `components.<name>` blocks for every emitted component axis.
   - `components.<name>.fingerprint` as documentation of the intended axes.
   - `invariants[]` rows for every deterministic obligation, and explicit deferred/candidate rows for
     visual obligations.
2. **Token bridge when needed → `scripts/rendering/design_tokens.py`:** only for legacy web theme
   roles/IA still used by the scorecard projection (`THEMES`, `MATERIALS`, `THEME_IA`, `THEME_META`).
   Do not treat token declarations as the authority for active design-language distinctness.
3. **Character assertions → `tests/contracts/test_design_character.py` and component contracts:** add
   tests that POSITIVELY express the doctrine with measurable evidence. Every assertion must cite the
   doctrine row it lowers from. Judgment items become visual-receipt obligations, never assertions.
4. **Render-derived distinctness:** `test_design_distinctness` and per-component contracts compare
   rendered fingerprints from `rendered_component_fingerprint()`. Declared fingerprints must match
   rendered facts, but cannot self-certify distinctness. If render output converges, the new theme is
   invalid even if the JSON says it differs.
5. **Prove RED first.** Before wiring the value, run the new character/distinctness test and confirm it
   fails for the right reason. Only then add profile/render/predicate code to go GREEN.

## Org gate (every step)

Name the RED first; declare each new file's home in `contracts/repo_layout.json` in the SAME slice
(the structural-layout cover reddens otherwise). New test files also register in
`scripts/organization/tests_layout_contract.py` (TEST_GROUPS contracts + DESIGN_CONTRACT_GROUPS
`design_languages`). Then hand off to `references/prove-theme.md`.

## Lifecycle authority

Slice lifecycle, role seats, review gates, and commit authority are governed by `AGENTS.md`
(operator process correction 2026-07-22); this lane carries only the design-language method.
