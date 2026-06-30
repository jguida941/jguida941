---
name: design-language-tdd
description: Turn a named design language (Apple HIG, Power BI, Material, Fluent, a brand guide, ...) into a CLOSED set of red-first, mutation-proven design invariants, then GENERATE the themed components/charts/layout that satisfy them and prove it with receipts. Use when adding or governing a design-language theme — each run produces a complete, structurally distinct themed website from the same data, not a colour swap. Honest claim only: "satisfies the <language> profile vN — here are the receipts", never "is Apple".
---

# design-language-tdd — the repeatable design-language engine

This skill is the engine behind the multi-theme design system. Run it with a design language and it
does the full loop: **research the docs → derive that language's proper-style invariants → generate
the components, charts, layout, and density that satisfy them → prove it.** Run it per language and
each pass produces an **entire distinct website** from the same data. The same engine generalizes to
"build X to a researched design law" — it is not theme-specific.

It exists because "make it look like Apple / Power BI" is a CLAIM, not a fact. A model can hallucinate
design compliance as easily as code. So every adjective ("clean", "Apple-like", "dense", "professional")
must resolve to evidence → an invariant → a passing test → a receipt. The skill never trusts the
adjective; it forces the UI to PROVE it.

## Non-negotiable boundaries (read `references/boundaries.md`)

- **Honest claim, always:** "satisfies the `<language>` profile vN across <aspects> — here are the
  receipts." NEVER "is Apple" / "100% Apple". Every profile is `candidate_only` + `cannot_mark_done`.
- **Org gate (this repo's rule):** you may not add/move a file without first naming the failing RED,
  and a shape/reorg task's RED must be the target-shape contract (`tests/contracts/test_structural_layout.py`).
  Declare every new file's home in `contracts/repo_layout.json` in the SAME slice. (Run
  `python -m scripts.organization.bootstrap_red_ref "<task>" "<red>"` to check.)
- **Determinism split — never a fake RED:** a deterministic invariant (observable from the rendered
  DOM/CSS/SVG without taste) compiles to a red-now/green-after predicate; a judgment invariant becomes
  a review anchor + a visual-receipt obligation. Never assert taste.
- **The kernel decides, this gathers:** emit verdict-free claims; semantic-tdd's Rust kernel
  (`preflight.rs` / `placement_law.rs`) is the eventual authority. This repo PROVES its own conformance.

## The loop (lanes A→D)

**A — research → cited doctrine.** `references/add-design-language.md`. Pull the language's primary
docs (web + any vendored instructions) into `docs/design-languages/<lang>.md`, every claim numbered +
sourced. Output measurable values: density (panel/tile padding + grid gap px), shape (radius), material
(flat/frosted), type (display/body px + weight), component anatomy (button/card/chip/list), and the
charts it FAVORS vs AVOIDS (e.g. Power BI → tables + multi-series bars; Apple → big stat + one ring,
no dense table).

**B — derive the closed invariant set (RED-first).** `references/add-design-language.md`. Walk the
closed aspect roster and emit, for each aspect, an invariant: a per-theme value in
`scripts/rendering/design_tokens.py THEME_IA` (+ a profile entry as the model grows) AND a CHARACTER
assertion that POSITIVELY expresses the language ("Power BI must be dense/flat/table-forward"; "Apple
must be airy/large/rounded/stat-forward"). Prove each predicate fails RED for the right reason first.

**C — generate the themed anatomy.** Make the theme render its proper style: per-theme tokens (colour
+ material + type + radius), density routed through `--pad-*`/`--gap-*`, and the per-theme chart/
component selection (CSS-gated on `[data-theme="<name>"]`, or the `THEME_SPEC` chart-variant map) so
the SAME data draws a DIFFERENT chart/layout. The character invariant from B *forbids the same boxes*,
so generation must produce different ones.

**D — prove.** `references/prove-theme.md`. GREEN on both surfaces (SVG + web), `test_design_character`
(expresses its language) + `test_design_distinctness` (differs from every other theme) pass, MUTATION-
PROVE each predicate (revert the theme's value → a test must fail), capture visual receipts per
breakpoint, then CODEX review folds any disagreement back RED-first. Emit the honest receipt.

## Workflow routing

| You want to… | Read |
|---|---|
| add a new design language / theme | `references/add-design-language.md` (lanes A+B) |
| prove a theme + receipts + codex | `references/prove-theme.md` (lane D) |
| understand the boundaries / honest claim / org gate | `references/boundaries.md` |

## Required end state (per design language)

Complete closed invariant set (every roster aspect emitted or declared-deferred) · the DEFAULT theme's
IA still equals `config.py` (SVG parity anchor) · `test_design_character` + `test_design_distinctness`
green · every predicate mutation-proven · a `docs/design-languages/<lang>.md` doctrine doc with cited
clauses · visual receipts · codex agrees · the honest receipt recorded. Then "add Material / Fluent /
Stripe / a brand guide" = run this skill again = another complete, distinct website.
