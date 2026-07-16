# ACTIVE PLAN — the universal design-compiler program (plan-of-record)

> THIS is the single plan we execute from — the durable, committed source of truth for the
> current plan and status. Every other plan-shaped doc is a typed record with a lifecycle row in
> `contracts/doc_authority_policy.toml` (fail-closed via `tests/contracts/test_doc_authority.py`);
> finished history folds into `docs/history/PLAN-LEDGER.md`. Never add a second plan doc.

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
without one. Detail: `handoff/w6-reference-capture-design.md`.

**MODULARITY (operator law 2026-07-16): the system is a PORTABLE TOOL, never this repo's
plumbing.** This repo (site + GitHub-pages workflow) is one example target. Every engine piece
(capture, probe, vocabulary, compiler, ratchet, gates) runs on ANY repo via parameters + data
contracts — no hardcoded paths/layouts; packaging = constellation sibling pattern. Hardwiring = defect.

## PROGRAM DEFINITION-OF-DONE (acceptance demos — the project is not done before these)

- **DEMO A — design-document lane:** one design document → profile DATA → generated site →
  receipts, under gates (delivered by correction slices 5–7).
- **DEMO B — website lane (the vertical):** capture reference → approve aspects → freeze →
  fidelity-confirm → measure → promote → APPLY under byte-backup → mutation-prove → receipts
  (slice 9's acceptance; automated crawl/gallery = W6, after slice 10). **Operator 2026-07-16:
  reference = `https://www.glukhovsky.com/games`; target = the operator's resume/portfolio site;
  the look matches the reference, content/labels stay the operator's; byte backup precedes any change.**

## ORCHESTRATION (operator-ratified; mirrors the semantic-tdd SOP)

Fable (conductor) owns reorientation, slice designs, REDs, integration, and commits — and does
not implement. Build routing (AGENTS.md owns this doctrine; Codex-conservation model 2026-07-15):
**Fable designs first → Opus builds EXACTLY the design (never without a design + packet) → Codex
adversarially reviews (CODE + ADVERSARIAL).** Codex does not code — its budget goes to reviews.
Author-never-approves. A design too vague for Opus to implement faithfully is a design defect the
DESIGN gate rejects. Codex gates EVERY slice three ways (`DESIGN-VERDICT` on the scratch design,
`VERDICT` + `ADVERSARIAL-VERDICT` on the finished patch) — no slice lands without all three.
Opus read-only fan-outs always; build lanes under the AGENTS.md build-packet (isolated worktree,
never commit; Fable verifies and integrates). Anything found in any review folds into THIS plan
or its named design record — never a new plan document.
Review-effort policy: the FIRST review round on an artifact runs at max/ultra effort; repeat
rounds on the same artifact run at xhigh — never spend ultra on re-reviews (reviews only).
Convergence cap (lesson of the 13-round slice-0 gate): after TWO REVISE rounds on one artifact,
remaining findings convert to executable REDs/probe scripts and move to the build phase — codex
then reviews code and test output, never prose re-descriptions; empirical domains (git, browser
behavior) are settled by scripts with hostile-case tests from the first round.

## STATUS

- **W3 visible-design correction** — gate record `handoff/w3-visual-regression-correction.md`;
  clean-context baseline 75/7F/9E (102/39F/13E was the dirty-tree diagnostic). **Slice-0 design
  `handoff/w3c-0-design-closure.md` = DESIGN-VERDICT: APPROVE (r13; rev 14 on disk); §16 statuses
  corrected 2026-07-16 — value rows PENDING real operator ratification.** Landing after
  re-ratification (text-only: plain-diff review → commit). T0 consolidation STAGED, uncommitted —
  lands with slice 0 (`doc_authority_policy.toml` + `test_doc_authority.py` + this plan).
- **Correction slices** (branch `w3-correction`; per slice: design → DESIGN gate → RED + admission
  → Opus build → suite + mutations + MF1 receipts → CODE + ADVERSARIAL → Fable commit; merge only
  after 10). Slice 0 = design closure + T0 + AGENTS amendment (**text-only — no receipts; lands
  via plain-diff review, NOT the hermetic binary-patch tool, which is slice-1+**). 1 admission/
  source foundation + `dashboard-pre-w3.v2` + slice_patch + ratchet hardening · 2 coverage +
  fail-closed render admission · 3 mount lifecycle + receipt authenticity · 4 component substrate
  · 5 Apple · 6 Carbon · 7 Liquid · 8 integrated 12+12+24 evidence + divergence · 9 manual
  reference lane — **DEMO B** · 10 integrated review + merge. Slice map detail: the handoff.
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
  pipeline (the promoted DEMO rides slice 9); integration into `main` follows the correction
  merge but the engine builds and demos in parallel. Durable design:
  `handoff/w6-reference-capture-design.md`.
- **K-series kit + odinproject:** GOVERNANCE only — NO design imposed, NO reference chosen, NO
  pixel changed; the site is *prepared* for restyle, not restyled. LANDED: O0 harness (`bad950a`),
  O1-tokenize (`e593d28`, value-preserving colors→tokens — the restyle prerequisite, not a new
  palette), O2-receipts (`037d3e2`, Chrome MF1 governance; 0 overflow@390). All
  correctness/hygiene/measurement invariants, NOT design. **O5 restyle (pick a doc OR crawl a
  reference → invariants that CHANGE the look) is DEMO B — not done, never without the owner
  choosing the reference.** Kit K0–K3 after slice 9.
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
