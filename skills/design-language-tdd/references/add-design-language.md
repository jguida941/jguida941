# Lane A+B — add a design language: research → cited doctrine → closed invariant set (RED-first)

The goal: turn a named design language into MEASURABLE values + testable invariants, grounded in its
real docs. This is what stops a theme from being a colour swap.

## A. Research → `docs/design-languages/<lang>.md`

1. Pull the primary source (WebSearch/WebFetch the official guidelines: developer.apple.com/design,
   learn.microsoft.com Power BI report design, m3.material.io, fluent2.microsoft.design,
   carbondesignsystem.com, …) PLUS any vendored instructions under
   `/Users/jguida941/semantic-tdd/.semantic_tdd_web/.../instructions/`.
2. Write `docs/design-languages/<lang>.md`: every doctrine clause NUMBERED with an inline source URL.
   For scale, fan out one research agent per language (a Workflow) returning a structured spec, as was
   done for the first three — capture: **density** (panel/tile padding + grid gap px + columns),
   **shape** (panel/tile radius px), **material** (flat | subtle | frosted), **typography** (display +
   body px + weight band + font note), **components** (one concrete line each for button/card/chip/
   list-row), and **charts_favored vs charts_avoided** (the structural fingerprint — e.g. Power BI
   favors tables + multi-series bars + categorical palette; Apple favors a big stat numeral + one ring
   and AVOIDS dense tables/multi-series).

## B. Derive the closed invariant set (RED-first)

For each aspect emit (1) a per-theme VALUE and (2) a CHARACTER assertion.

1. **Values → `scripts/rendering/design_tokens.py`:**
   - `THEMES[<name>]` = the 11 colour roles (run the theme-system contract: complete + WCAG-AA +
     restrained).
   - `MATERIALS[<name>]` = blur/saturate/opacity/sheen (the glass material band).
   - `THEME_IA[<name>]` = `radius` (panel/tile), `type` (a subset of the ladder, all ≥ 11px), and
     `density` (panel_pad/tile_pad/gap + a band label). The DEFAULT theme's `type`/`radius` MUST equal
     `config.py` (SVG parity anchor); other themes diverge.
   - `THEME_META[<name>]` = label + one-line blurb for the switcher.
2. **Character assertions → `tests/contracts/test_design_character.py`:** add a test that the theme
   POSITIVELY expresses its language with a doctrine cite, e.g. `assertEqual("tight", density["band"])`,
   `assertLessEqual(radius["panel"], 6)` (Power BI sharp), or a rendered-DOM signal like "Power BI is
   table-forward" (`'[data-theme="power-bi"] .lang-table' in render_dashboard()`). Each MUST be
   measurable, not taste. Judgment items (visual rhythm, "feels Apple") become a visual-receipt
   obligation, never an assertion.
3. **Distinctness is automatic:** `test_design_distinctness` already requires every theme pair to differ
   on a quorum of structural signature axes — adding a theme is picked up for free, and a converged
   theme reddens it.
4. **Prove RED first.** Before wiring the value, run the new character test and confirm it fails for the
   right reason (the theme doesn't yet express the aspect). Only then add the value to go GREEN.

## Org gate (every step)

Name the RED first; declare each new file's home in `contracts/repo_layout.json` in the SAME slice
(the structural-layout cover reddens otherwise). New test files also register in
`scripts/organization/tests_layout_contract.py` (TEST_GROUPS contracts + DESIGN_CONTRACT_GROUPS
`design_languages`). Then hand off to `references/prove-theme.md`.
