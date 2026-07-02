# D-SHELL-0 — Surface-to-law design (Fable-authored; for codex DESIGN gate)

## Reorientation (the failure being corrected)

The loop so far proved token/injection SAFETY and called pages governed. Wrong claim class: a page
can be token-only and badly designed. Operator law going forward — **if it is visible, it is
governed by the full pipeline**: observed surface → candidate law → doctrine grounding (or declared
gap) → RED → DATA → RENDER → FACTS → fail-closed PREDICATE → RECEIPT → codex adversarial review.
Screenshots are acceptance receipts inside the loop, not after-the-fact proof. Passing tests prove
only encoded predicates, never missing ones.

Pre-gate implementation (ps-main column, cited SHELL_SCALE, density consumption, 3 page-layout
predicates, hairline #38383a, radius 14/12, 315 green) is PARKED on branch `d-shell-1-pregate`.
It merges only if this design ratifies it as the D-SHELL-1 implementation; anything it missed is
re-derived from the candidate laws below.

## Observed Surface Models (evidence: committed screenshots + the 12-item file:line audit)

### index — intent: prove the builder ships; archetype: LANDING/NAVIGATION
Regions: hero/identity · KPI bento · activity viz · entry points to the design lab.
Defects: design-lab entry buried as a text line (web_render.py:248); otherwise the only page with a
real container (.wrap 980px — the layout precedent). Candidate laws: L-IDX-1 a landing page
merchandises every sibling surface with a designed entry (receipt-backed lab panel); L-IDX-2 the
frozen liquid-glass default stays (P5-ARCH) — index changes are additive panels only.

### showcase — intent: the conformance proof; archetype: PROOF/REPORT
Regions: orientation header · per-language proof section (specimen stage + verdict table) · legend.
Defects (audit #1,3,4,5,6,8): full-bleed sprawl (pageshell.py:66-68, no container); stage = black
void (showcase.py:122-124 + inline backdrop style); box-in-box (.lang re-declares panels);
body-sized section headers (3-size ramp, pageshell.py:27-30); table = flat 21-row dump — doc cite
repeated ~17×, receipt column ~90% "—", 21 identical saturated green pills, no aspect grouping
(showcase.py:_rows 75-105 ignores the aspect field).
Candidate laws: L-SHOW-1 report pages group rows by aspect with subheaders + per-group doc cite;
L-SHOW-2 PASS is quiet, FAIL/CANNOT-CERTIFY are loud (exception-first scanning); L-SHOW-3 a
specimen stage shrink-wraps its content on a visible surface (dead-space bounded; no inline raw
colour); L-SHOW-4 one chrome level per page (panels never nest chromed boxes); L-SHOW-5 empty
cells render empty, never placeholder dashes.

### settings — intent: the governed control plane; archetype: CONTROL-PLANE
Regions: orientation · the law · per-base admissibility grids.
Defects (audit #9): three stacked near-identical grids, 25 identical green pills drowning the 2
red refusals (settings.py:91-112); page bottom void.
Candidate laws: L-SET-1 a control plane leads with the DECISION (refusals visually primary,
admissible quiet); L-SET-2 repeated structure compresses (shared header/legend, tighter grids or
one matrix — fork Q3); L-SET-3 = L-SHOW-4 (no box-in-box).

### studio — intent: try the languages; archetype: COMPARISON/WORKBENCH
Regions: orientation · language tabs · swap controls · live archetype stage.
Defects: name-as-label buttons ("prominent") read as debug output (components.py:66/69 — queued
E-BTN-LABELS rider); tab/control rows overflow at 390 (audit #11); dead lower half.
Candidate laws: L-STU-1 a workbench's controls read as one instrument cluster (grouped, labeled),
the stage is the hero; L-STU-2 specimen text is real microcopy, variant ids are captions (data
labeled as data); L-STU-3 no horizontal overflow at 390 (content layer may use @media; host chrome
stays closed).

### cross-page candidate laws
L-ALL-1 one centered content column per page (measure+gutters tokens; sprawl unconstructable).
L-ALL-2 the type ramp has ≥4 cited tiers and section headers sit above body (hierarchy).
L-ALL-3 spacing rhythm: within-group < between-group < between-section, all from the cited step
set; density from the LANGUAGE'S band (THEME_IA), never a minted constant. L-ALL-4 every visual
literal traces to a token with a doctrine cite or the value doesn't ship. L-ALL-5 every page
declares intent + archetype as DATA (contracts/page_manifest.json — fork Q1) and its composition
facts must match its archetype.

## Governed aspect set (roster additions; determinism split)

Deterministic (facts from rendered HTML+CSS): **page-layout** (column/measure/gutters),
**page-type-ramp** (tier count + ordering), **page-spacing-rhythm** (step-set membership +
band provenance), **page-section-grouping** (chrome nesting depth ≤1; grouped rows; per-group
cites), **page-archetype** (page manifest declares intent/archetype; required regions present
for that archetype), **page-content-density** (dead-space bounds: stage/section fill facts).
Judgment + receipt obligation: **page-scan-path**, **page-responsive-measure** (390px no-clip —
Chrome dom-probe receipt, R4), **page-visual-receipt** (per page × language screenshot receipts
with honest provenance). page-information-architecture = the archetype+grouping pair (not a
separate predicate — fork Q2).

## RED bank (negative examples that must fail)
sprawl: shell without .ps-main column → page_has_content_column False. flat ramp: h2==body px →
tiered False. minted pad: --ps-pad ≠ density(profile) → density False. box-in-box: a chromed box
inside a chromed panel → nesting_depth fact >1 → grouping False. flat table: rows not grouped by
aspect → grouping False. loud-pass: pass pill uses solid status fill while fail is outline →
exception-first False (fact: pass/fail prominence order). dash placeholder: "—" in an empty
receipt cell → False. archetype mismatch: settings manifest says control-plane but no refusal
region rendered → False. uncited literal: any new px/hex without doc_cite → existing token gates.
overflow: dom-probe scrollWidth>clientWidth at 390 → receipt-gated fail.

## Slices after the gate
D-SHELL-1 page-layout (+type-ramp/spacing-rhythm): ratify + extend the parked branch; add roster
aspects; docs (pageshell.md §3 rewritten with citations; apple-dark.md separator/radius clauses).
D-SHELL-2 page-archetype + section-grouping: page manifest DATA; nesting-depth + grouping facts;
table grouped by aspect; quiet-pass/loud-fail; per-group cites; empty-not-dash.
D-SHELL-3 per-page recomposition: settings decision-first; studio instrument cluster; index lab
panel; stage shrink-wrap.
D-SHELL-4 visual receipt gate: Chrome-CLI page screenshots + 390 dom-probe as committed receipts
per page × language (honest kinds); receipt obligations on the judgment aspects.
Riders re-sequenced AFTER D-SHELL: E-BTN-LABELS (into D-SHELL-3), P2-RECEIPTS, switcher, themes.

## Repeatability deliverables (D-SHELL-1 slice includes)
skills/design-language-tdd/references/add-page-aspect.md — the surface-to-law loop (observe →
model → candidate law → doctrine/gap → RED → data/render/facts/predicate → receipt → codex).
Repo AGENTS.md — the two-plan protocol: Fable designs/reviews/commits; codex gates (DESIGN-VERDICT/
VERDICT/ADVERSARIAL-VERDICT lines) + codex build agents (workspace-write, never commit).

## Open forks for the DESIGN gate (answer each)
Q1 page manifest home: contracts/page_manifest.json (new contract, 3-registry) vs a `pages` block
inside _index.json? Q2 IA aspect: separate predicate or the archetype+grouping conjunction?
Q3 settings compression: three per-base grids kept (tests reference data-base sections) with
shared header + refusal-first styling, or one combined matrix (bigger test churn)? Q4 does the
parked d-shell-1-pregate branch merge as-is as D-SHELL-1's core (then extended), or re-implement
from scratch? Q5 aspect granularity: 6 deterministic roster aspects as listed, or fold
type-ramp/spacing into page-layout to keep the roster tighter?

## ADDENDUM — round-1 DESIGN gate folds (all four must-fixes accepted; forks ratified)

MF1 — PER-SLICE RECEIPT RULE (binding on every D-SHELL slice): any slice that changes visible
layout commits, BEFORE merge: (a) Chrome-CLI screenshots of every changed page at 1280 width,
(b) the 390px dom-probe overflow receipt for every changed page, both with honest provenance
sidecars (kind: chrome-headless-screenshot / chrome-headless-dom-probe, exact command + version).
D-SHELL-4 only GENERALIZES this into roster receipt-obligations; it is never the first receipt.

MF2 — page_manifest schema (defined now, implemented in D-SHELL-2):
contracts/page_manifest.json = { "contract_id": "PageManifest", "pages": [ {
  "id": "settings", "route": "site/settings.html",
  "render_source": "scripts/rendering/settings/settings.py::render_settings",
  "intent": "<one sentence>", "archetype": "control-plane" | "landing" | "proof-report" | "workbench",
  "required_regions": ["orientation", "law", "control-groups", ...],   // per-archetype region ids
  "region_aliases": { "control-groups": ["ps-panel[data-base]"] },     // optional selector hints
  "receipt_obligations": [ {"kind": "chrome-headless-screenshot", ...}, {"kind": "chrome-headless-dom-probe", "viewport": 390} ]
} ] }
Fail-closed law: a generated page absent from the manifest reddens; a manifest page whose
required_regions are not all present in the render reddens; an archetype value outside the closed
enum reddens. 3-registry home declaration in the same slice.

MF3 — roster keeps SIX separate deterministic aspects (page-layout, page-type-ramp,
page-spacing-rhythm, page-section-grouping, page-archetype, page-content-density) + the three
judgment/receipt aspects (page-scan-path, page-responsive-measure, page-visual-receipt). Separate
failure names; separate RED bank entries; separate receipts.

MF4 — d-shell-1-pregate is a REUSABLE CORE only: its ps-main/type-tier/density/hairline/radius
work is re-derived into the ratified aspect roster + docs + RED bank + MF1 receipt flow on a fresh
slice branch; never merged as-is.

Forks ratified: Q1 contracts/page_manifest.json · Q2 IA = archetype+grouping conjunction ·
Q3 settings keeps three per-base grids (shared header/legend, refusal-first styling; matrix
compression deferred until the predicate surface is stable) · Q4 extend the parked branch after
revision · Q5 six deterministic aspects.

Focused re-review ask: confirm the four folds close your must-fixes with no new hole, and that
D-SHELL-1 may proceed to a codex BUILD brief on this basis.
DESIGN-VERDICT required: APPROVE or REVISE (numbered).
