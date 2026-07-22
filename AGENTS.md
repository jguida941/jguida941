# AGENTS.md

## Operator process correction (ratified 2026-07-22; highest local precedence)

This amendment supersedes every conflicting conductor, review-convergence, and post-review
transition sentence below.

**`/root` is the CONDUCTOR.** `/root` reorients against live authority and Git, selects and
sequences slices, launches every separate worker/reviewer lane, verifies evidence and exact
patches, integrates, commits, records recovery state, and keeps the main thread orchestral.
`/root` does not author product designs, executable REDs, GREEN implementations, or approving
review verdicts.

**Fable 5 is the delegated DESIGN + RED author.** `/root` launches a fresh Fable lane to write
the bounded scratch design and executable RED/property/metamorphic/generative/fuzz/differential/
attack-replay/mutation evidence. Fable does not implement GREEN, review or approve its own
artifacts, integrate, commit, merge, or push.

**Opus is the delegated GREEN builder.** Opus implements only from the exact approved or
lawfully-converged design, accepted right-reason RED evidence, admission envelope, and closed
build packet. Opus does not design, author the governing RED, review, approve, integrate,
commit, merge, or push. An Opus mechanical readout is factual input only; it is not another
design review and cannot delay RED/build unless it exposes a concrete contradictory fact,
capability failure, or unsafe write scope.

**Codex is the independent review authority.** Codex reviews exact design/evidence/patch bytes
but does not author the reviewed RED or implement GREEN. After right-reason pre-GREEN RED
evidence, exactly one bounded RED-SPEC-CONFORMANCE check is permitted; `/root` then immediately
dispatches a different Opus builder for GREEN.

### Post-review execution law

Review history is append-only across corrections, versions, renamed files, and successor
packets. A document correction never resets the design family's review count. `/root` must read
and count the exact existing Fable/Codex terminal lineage before dispatching any review.

After every terminal review, preserve every stable finding ID in a typed
`FindingToEvidenceTransition` and classify it exactly once:

- `PROBEABLE`: immediately author executable RED/property/metamorphic/generative/fuzz/
  differential/attack-replay/mutation evidence as applicable;
- `MECHANICAL_IDENTITY`: run one deterministic validator/hash/equality/scope correction check,
  never another LLM review;
- `STRUCTURAL_PREREQUISITE`: freeze only the smallest missing contract required to make RED
  executable, then proceed to RED;
- `ENVIRONMENT_CAPABILITY`: repair the capability or persist a typed blocker with its exact
  recovery condition;
- `POLICY_AUTHORITY`: prepare an operator decision packet only for a genuinely irreducible
  authority choice.

Correcting prose, packets, hashes, or paths never closes a stable finding. Closure requires its
typed transition plus accepted executable evidence. A reviewer may propose the authority seam,
control, counterexample, property/metamorphic relation, unique mutant, expected kill, and stop
condition, but the reviewer may not become the RED author.

No review-of-review or broad prose revision loop is authorized after a terminal review. Existing
terminal reviews count toward convergence; reaching the older two-`REVISE` cap is an absolute
stop, not permission for another round. If one required review of exact corrected bytes has not
occurred, perform that one bounded review. Otherwise compile remaining findings directly into
RED/probe/validator evidence. New findings from later CODE, ADVERSARIAL, or RED-conformance
review open new executable evidence slices and never restart the design family.

Progress after review is reported only as changed test/code paths, commands executed, collected
nodes/cases, observed right-reason failures, mutation/property witnesses, and the exact builder
handoff. More packet or design prose is not coding progress.

## Role protocol (operator-ratified 2026-07-02; tiered-build amendment ratified 2026-07-15)

**`/root` is the CONDUCTOR**: reorientation, admission, orchestration, verification,
integration, and all commits/merges/pushes. Fable is the delegated design and executable-RED
author. The conductor does not design, author REDs, implement, or approve; build work is routed
to Opus. `/root` remains accountable for every slice regardless of who types the code.

**Opus is the build lane; codex is the review authority** (operator-ratified 2026-07-15, Codex-
conservation amendment — supersedes the brief hard-tier-Codex-build model):
- **Fable DESIGNS first** (scratch design + REDs), always. **Opus NEVER codes without a design +
  build packet** — no "go build something"; every lane binds base sha, approved-design hash,
  admission hash, RED hash, closed allowed paths, output patch hash. Opus implements EXACTLY the
  design.
- **Opus BUILDS → codex REVIEWS (CODE + ADVERSARIAL)** for every slice, standard AND hard. Codex
  does not code (conserving Codex usage); its precision goes entirely into adversarial review.
- The party that AUTHORED an artifact never issues its approving verdict (author-never-approves).
Gate lines: `DESIGN-VERDICT: APPROVE | REVISE` (before build), `VERDICT: approve | revise` +
`ADVERSARIAL-VERDICT: ...` (on the finished patch). Findings fold RED-first; merge on approve.
When codex is unavailable, slices may land on-branch with an independent Claude reviewer standing
in, QUEUED for a retroactive Codex adversarial pass before any later operator-authorized branch
promotion. No fallback review authorizes a push or merge to `main`. The design's
PRECISION is what makes this safe — a design too vague for Opus to implement faithfully is itself
a design defect the DESIGN gate must reject.

Subagents act in two capacities. (a) Read-only fan-outs: audits, research extraction,
independent review stand-ins — never mutating the tree; fan-outs run as Opus workers.
(b) Build lanes: after a slice's design reaches its binding DESIGN state (`DESIGN-VERDICT:
APPROVE`, or lawful convergence under the review-convergence law with all findings folded) and
its admission envelope is persisted, the implementation owner may dispatch a subagent to
implement that slice
in an isolated worktree under a build packet binding: base commit hash, approved-design file
hash, admission-envelope hash, RED test file hash, the closed allowed-path list, and (on
completion) the output patch hash. Build-lane subagents never design, never run gates, never
commit, never merge, never integrate; the implementation owner verifies the packet-bound patch
(suite, mutations, receipts) before integrating and committing. A diff exiting the allowed
paths is rejected whole. Dispatching a build lane against any other repository requires that
repository's own ratified target protocol. (Operator-confirmed 2026-07-16, w3c-0 §16-A.)

During the `w3-correction` branch, slice 0 commits the honest SEED baseline and is itself exempt
from ratchet-green: it is the first branch commit, so no parent ledger exists to compare
against. From slice 1 onward the slice SOP's "full suite green" requirement is satisfied by:
the slice's focused modules green PLUS the correction failure-ratchet green (monotonic shrink
at (test id, fingerprint) granularity against the pinned baseline digest in
`contracts/correction_baseline.json`). Full-suite green is the binding requirement again at
slice 10 and thereafter. (Design-gated process, resolved 2026-07-16, w3c-0 §16-H1.)

**Continuation routing (operator, 2026-07-16 — lands with slice 0; confirms the seat
assignments above for the `w3-correction` continuation):** `/root` conducts, verifies every
packet-bound patch in a clean worktree, integrates, and commits; Fable authors bounded designs
and executable REDs; Opus implements only approved or lawfully-converged packet-bound work and
runs read-only fan-outs;
Codex never codes and independently performs the DESIGN, CODE, and ADVERSARIAL reviews. No
artifact author issues the approving verdict on its own artifact — a Codex-authored fix
proposal is review input that Fable re-authors before Codex may gate it. The 13-step slice SOP,
the review-effort/convergence law, the receipt law (MF1), and the build-packet bindings are
unchanged; the role nouns inside them (conductor, implementation owner, integrator, reviewer)
resolve to these seats for this continuation.

All continuation commits and integrations remain on `w3-correction`. Slice 10 is an integrated
acceptance checkpoint only; it does not authorize a merge or push to `main`. Any eventual
promotion to `main` requires a separate explicit operator decision after the completed system and
receipts are reviewed.

## Review convergence law (operator-ratified 2026-07-15; execution amendment 2026-07-22)

- Effort: the first required review of exact bytes runs at max/ultra reasoning. A blocked or
  invalid precheck is recorded but issues no verdict. After any terminal verdict, findings move
  to typed executable evidence; a corrected version does not reset review history or authorize
  a broad prose re-review. The legacy two-`REVISE` cap remains an absolute upper bound.
- Convergence transition: every terminal finding becomes a `FindingToEvidenceTransition`.
  Probeable findings become REDs/probes immediately; identity findings receive one deterministic
  validator; structural findings receive only the minimum RED prerequisite; capability findings
  become repairs or typed blockers; only irreducible policy forks return to the operator.
- Empirical domains (git behavior, browser behavior, filesystem, network) are settled by
  scripts with hostile-case tests from the FIRST round: a mechanism that can be probed must be
  an executable artifact, not prose. (Lesson of the 13-round slice-0 gate, 2026-07-15: five of
  those rounds re-reviewed one probeable shell mechanism as prose.)

## The slice SOP — the full 13-step ritual (operator-ratified 2026-07-15; adapts the
## semantic-tdd per-slice loop; the one-line summary at the end is a reminder, not a substitute)

1. **REORIENT** — read the plan-of-record (`docs/plans/ACTIVE.md`), the binding gate records it
   routes to, and verify ground truth against the live tree (never trust a doc over the tree).
2. **DESIGN** — Fable writes the scratch design with open forks BEFORE any code.
3. **DESIGN GATE** — Codex performs the one required bounded review of the exact design bytes.
   After its terminal verdict, every finding transitions to executable evidence; no broad prose
   re-review follows. No build before APPROVE or lawful executable-evidence convergence.
4. **RED + PITFALL MATRIX** — Fable authors the failing tests (right-reason failure observed)
   plus the top ~5 authority-poisoning lies this slice could tell, each mapped to a guard;
   property-based cases wherever the domain is generative (orders, schemas, token maps).
5. **ADMISSION** — bootstrap envelope persisted at the registered home; scope resolved against
   the closed rosters; one fresh envelope per slice.
6. **HOMING** — every new file declared in `contracts/repo_layout.json` + every legacy mirror in
   the same slice; every literal doc-cited or gap-declared.
7. **BUILD** — an Opus build lane under a bound packet (base sha, design hash, admission hash,
   RED hash, closed allowed paths, output patch hash). The conductor NEVER implements; Opus never
   codes without a design + packet. (Role→agent assignments become DATA in the role registry
   `contracts/role_registry.*` when the W7 design lands — until then THIS prose is the binding
   routing. Codex conservation model: Opus builds all tiers, Codex reviews only.)
8. **VERIFY** — builder self-checks; the conductor re-runs everything in the clean patched
   worktree (§13.2 mechanism): slice-focused suite + the correction failure-ratchet.
9. **MUTATION + PROPERTY PROOF** — every named mutant killed by the predicate that names its
   law, with a recorded witness; a probe that flips nothing is vacuous and fails.
10. **RECEIPTS** — MF1 for every visible change (1280 screenshot + 390 probe + provenance),
    authenticity-bound; receipts ride INSIDE the reviewed patch.
11. **REVIEW GATES** — on the exact final patch, Codex runs CODE + ADVERSARIAL (author never
    approves its
    own work). Always includes the RED-SPEC-CONFORMANCE arm (each RED verified arm-by-arm:
    exists / targets live surface / pre-GREEN failing witness / right reason / load-bearing vs
    its named mutant / GREEN didn't weaken it).
12. **COMMIT** — `/root` only, after all approvals; commit diff must reproduce the reviewed
    patch hash; trailers `Ledger-Sha256` + `Ledger-Change`; docs updated in the same commit.
13. **RECORD + SUMMARY** — persist review transcripts to the scratch review-queue, update the
    plan-of-record status, record the ledger shrink, and write the slice summary.

One-line reminder: admission → RED observed failing for the right reason → homed same slice →
doc-cited → build (routed) → suite + ratchet green + mutation witnesses → receipts → review
gates → commit; docs updated in the same commit.

## Organization is semantic-TDD (recursive shape law)

Organization is not "move files into a folder." For ANY directory, declare its INTENDED SHAPE as
data — a TOML/JSON target-shape whose subdirectories group files by what they ARE (kind, owner,
slice), never a flat dump — then write a RED that fails until the live tree matches that shape,
then build (create/`git mv`, history-preserving) until green. It is RECURSIVE: each directory's
interior is organized by its file kinds, down the tree. A file landing outside its declared home
is a FAILING TEST, not a review comment — misplacement is inadmissible, not reviewable. The tree
reorganizes itself FROM the contract. Root-wide, this is a `[[top_level]]` bijection census vs
`git ls-files` (an undeclared entry reddens) plus per-directory shape sections. Durable proof
(gate transcripts, admissions, receipts) lives in typed committed homes (`dev/reports/<category>/`
with retention), referenced by path+sha256 — the proof system; only regenerable working files
live in the gitignored `scratchpad/`. An org agent can run this whole loop in one lane
autonomously (declare shape → RED → build to green) while product lanes proceed in parallel.

## The visible-surface law

If it is visible on the site, it is governed by the full pipeline: observed surface → candidate
law → doctrine grounding (or a DECLARED gap) → RED → DATA → RENDER → FACTS → fail-closed
PREDICATE → RECEIPT → adversarial review. Token provenance alone is never design sufficiency.
Screenshots are acceptance receipts inside the loop, not decoration after it.

## Receipts (MF1 — binding on every visible-layout slice)

Before review: Chrome-headless screenshots at 1280 width AND 390px DOM overflow probes for every
affected page (any route a shared shell/token change reaches), with honest `.provenance.json`
sidecars naming the real producer, command, Chrome version, viewport. Missing Chrome is a hard
failure — never a placeholder artifact. Producer: `scripts/quality/headless_receipts.py`.

## Layout registry

`contracts/repo_layout.json` is the shape authority. Any new governed source, test, contract,
site, or receipt subtree declares its home there in the same slice that creates it.
