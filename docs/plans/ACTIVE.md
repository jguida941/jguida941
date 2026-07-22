# ACTIVE PLAN — the universal design-compiler program (plan-of-record)

> THIS is the single plan we execute from — the durable, committed source of truth for the
> current plan and status. Every other tracked plan-shaped doc is a typed record with a lifecycle
> row in `contracts/doc_authority_policy.toml` (fail-closed; untracked drafts enter when their
> lane lands). Finished history folds into `docs/history/PLAN-LEDGER.md`. Never add a second plan doc.

## THE PRODUCT (operator-ratified 2026-07-15)

Given ANY browser-accessible website, URL/local snapshot, or design document, the system captures
its routes, regions, components, responsive layouts, interaction states, computed styles, and
assets; the user selects the aspects they like; the system compiles those selections into
provenance-bound semantic invariants, generates genuinely-failing RED tests, implements them in a
target repository, verifies the real rendered result, mutation-proves every invariant, and fails
closed wherever evidence, state coverage, or enforcement is incomplete. Approved design knowledge
becomes reusable frozen packs; user tweaks are explicit owner forks, never silent edits.

    crawl / read docs → select aspects → compile invariants → observe RED
    → implement → render + measure → mutation-prove → reusable design pack

Apple Dark, Carbon, and Liquid Glass are TEST FIXTURES proving the universal engine — not the
product. Authority ladder per aspect: official code/spec (Mode A/B) → approved measured reference
(Mode C) → owner-ratified law (Mode D); no mode = no authority; accessibility floors are
non-waivable; brand claims are always "satisfies <profile> vN — receipts attached", never "is X".

**COMPLETENESS (operator 2026-07-15): "everything that can be put in a website"** — every HTML
(DOM/semantics/attributes), CSS (every computed property, not a visual subset), and observable JS
aspect (states, hydrated DOM). The probe records the FULL computed-style+DOM+state surface; an
aspect with no vocabulary id is a coverage gap that reddens, never a silent skip. **BACKUP-BEFORE-
TRANSFORM (hard law):** a restyle NEVER overrides — it first commits a hash-pinned `pre-restyle`
restore point (git tag + frozen pack) then transforms reversibly; the O5/DEMO-B lane fails closed
without one. Slice-0 foundation: `handoff/w3c-0-design-closure.md` §8 (full W6 = its own lane).

**MODULARITY (operator law 2026-07-16): the system is a PORTABLE TOOL, never this repo's
plumbing.** This repo (site + GitHub-pages workflow) is one example target. Every engine piece
(capture, probe, vocabulary, compiler, ratchet, gates) runs on ANY repo via parameters + data
contracts — no hardcoded paths/layouts; packaging = constellation sibling pattern. Hardwiring = defect.

## PROGRAM DEFINITION-OF-DONE (acceptance demos — the project is not done before these)

- **DEMO A — design-document lane:** one design document → profile DATA → generated site →
  receipts, under gates (delivered by correction slices 5–7).
- **DEMO B — website lane (the vertical):** capture reference → approve aspects → freeze →
  fidelity-confirm → measure → promote → APPLY under byte-backup → mutation-prove → receipts.
  **Post-checkpoint selection (operator 2026-07-16): reference = `https://www.glukhovsky.com/games`;
  target = the operator's resume/portfolio site; its look transfers while the operator's content
  and labels remain. Slice 9 is readiness only; real crawl/APPLY needs post-slice-10 admission.**

## ORCHESTRATION (operator-ratified; mirrors the semantic-tdd SOP)

Continuation routing (operator 2026-07-22; AGENTS.md owns this doctrine):
**`/root` conducts, dispatches, verifies, integrates, commits, and records recovery state, but
does not design, author REDs, implement, or approve. Fable authors every bounded design and
executable RED. After one bounded Codex review/conformance gate and fresh admission, Opus builds
GREEN only in the single authoritative `w3-correction` checkout under a six-field packet and a
closed, non-overlapping write roster; Codex reviews the finished patch. Creating another Git
worktree is a hard process failure.** No artifact author approves its own work;
no slice lands without all three gates. Opus read-only fan-outs remain allowed. Findings fold
into THIS plan or its named record — never a new plan doc (conductor's live scratch record:
`scratchpad/work/CONTINUATION-PLAN.md`). Integrations stay on `w3-correction`; slice 10 is
acceptance only; `main` needs a later operator decision. SOP/receipt/effort/packet laws unchanged.
Review history is append-only across corrected/versioned artifacts. After every terminal review,
stable findings become typed `FindingToEvidenceTransition` rows and move immediately to RED,
probe, deterministic-validator, minimum-prerequisite, capability-blocker, or operator-policy
evidence. No review-of-review or broad prose revision loop is permitted. After right-reason RED,
one bounded RED-conformance check is followed immediately by a different Opus GREEN builder.

## STATUS

- **W3 visible-design correction** — gate record `handoff/w3-visual-regression-correction.md`;
  clean-context baseline 75/7F/9E (102/39F/13E was the dirty-tree diagnostic). **Slice-0 design
  `handoff/w3c-0-design-closure.md` rev 16 (2026-07-16; rev15 combined max review REVISE;
  r2 xhigh REVISE folded — converged; §16: A + H1 resolved, B–G/H2 pending).** Slice 0 lands
  text-only as first branch commit only after CODE + ADVERSARIAL approve the exact landing patch;
  org L1/L2 intake follows. T0 lands with slice 0 (doc law + plan).
- **Correction slices** (development branch `w3-correction`; design → DESIGN gate → RED + admission
  → isolated, packet-bound Opus build → `/root` verification + Codex CODE/ADVERSARIAL → `/root` commit;
  every integration stays on this branch). Slice 0 = design closure + T0 + AGENTS amendment
  (**text-only — no receipts; lands via plain-diff review, NOT the hermetic binary-patch tool, which is slice-1+**). 1 admission/
  source foundation + `dashboard-pre-w3.v2` + slice_patch + ratchet hardening · 2 coverage +
  fail-closed render admission · 3 mount lifecycle + receipt authenticity · 4 component substrate
  · 5 Apple · 6 Carbon · 7 Liquid · 8 integrated 12+12+24 evidence + divergence · 9 fixture/manual
  reference readiness only · 10 clean reviewed `w3-correction` checkpoint; real crawl/APPLY is later.
- **W6 — the universal capture ENGINE (ACTIVE parallel workstream — this IS the product).**
  Reframed 2026-07-15: the FOUNDATION is design-approved in slice 0 (§8 reference-lane schemas:
  candidate/approval/pack/promotion; §3.1 the closed 31-id aspect vocabulary — the COMPLETENESS
  mechanism; §3.2 the closed coverage join). It BUILDS NOW on its own branch, parallel to the
  fixture-correction, and never widens repo-surface-scout's on-disk `web_surface_probe` (schema
  pins `scout_fetch_executed: false`). Engine lanes (each design→gate→build→review): **W6-P
  generic probe** (every aspect of any served page — the rendered-facts engine without
  `data-dom-owner` sentinels); **W6-C capture pipeline** (dump-dom → localize → freeze →
  serve-locally → probe; boundary checks; rights + custody; restore points); **W6-K reference-
  lane contracts + validators** (§8 schemas as closed contracts). Promotion reuses the correction
  pipeline. Through slice 9, only fixtures/local snapshots exercise it; live requests/target writes
  wait for fresh post-checkpoint admission. W6 integration targets `w3-correction`; `main` is
  separately operator-gated. Foundation: `handoff/w3c-0-design-closure.md` §8; full W6 own lane.
- **K-series kit + odinproject:** GOVERNANCE only — NO design imposed, NO reference chosen, NO
  pixel changed; the site is *prepared* for restyle, not restyled. LANDED: O0 harness (`bad950a`),
  O1-tokenize (`e593d28`, value-preserving colors→tokens — the restyle prerequisite, not a new
  palette), O2-receipts (`037d3e2`, Chrome MF1 governance; 0 overflow@390). All
  correctness/hygiene/measurement invariants, NOT design. **O5 keeps the selected reference/target,
  but no real crawl or target mutation occurs through slice 9. Real crawl/portfolio APPLY starts
  only after the clean slice-10 checkpoint under fresh admission.** Kit K0–K3 stay post-correction.
- **P5 remainder** (org meta-gate, P5-DATA sweep, P5-PATTERN, themes 4–10): after the correction; ledger.
- **Kernel honesty:** enforcement is pytest contracts + receipts + Codex review; no Rust kernel
  runs here ("kernel decides" is historical — ledger). semantic-tdd is the portability destination;
  this repo is registered there as a kernel-free adopter (reentry: `handoff/HANDOFF.md`).

## VERIFICATION (every slice)

Focused 17-module command + full `unittest discover` green by slice 10; every named mutant
reddens the predicate that names its law (witnessed, non-vacuous); MF1 receipts for every visible
change (1280 screenshot + 390 probe + provenance); Codex DESIGN + CODE + ADVERSARIAL per slice;
`test_doc_authority` green (one plan, lifecycled records, caps); docs updated in the same commit.

## POINTERS

Architecture seam: `docs/plans/DESIGN-SYSTEM.md` · doctrine: `docs/design/*.md` · skill:
`skills/design-language-tdd/` · history/doctrine ledger: `docs/history/PLAN-LEDGER.md` · reentry:
`handoff/HANDOFF.md` · review transcripts: `scratchpad/work/codex-*.md`.
