# AGENTS.md

## Role protocol (operator-ratified 2026-07-02; tiered-build amendment 2026-07-15;
## single-conductor amendment — A13 — operator-ratified 2026-07-18)

**`/root` (the operator's conductor session) is the SOLE CONDUCTOR**: reorientation, dispatch
control, currentness/hash checks, model/tool integrity enforcement, verification in clean
worktrees, integration of approved patches, ALL commits/merges, and lifecycle recording. The
conductor NEVER designs, authors REDs, implements, or issues review verdicts. The conductor is
accountable for every slice regardless of who types the code.

**Fresh exact `claude-fable-5` sessions at MAX effort are the AUTHOR lane**: slice designs (a
scratch design doc with open forks BEFORE any code), pitfall matrices, executable REDs, admission
envelopes, build-packet specifications, review-finding folds, and hard-proof interpretation.
Writing RED test code is authoring, not GREEN implementation. Fable never conducts, never
implements GREEN, never commits, never integrates, and never approves its own artifact.

**Fresh exact `claude-opus-4-8` sessions are the BUILD lane for EVERY implementation tier —
difficulty never changes the builder seat.** Opus NEVER codes without a design + build packet —
no "go build something"; every lane binds base sha, approved-design hash, admission hash, RED
hash, closed allowed paths, output patch hash. Opus implements EXACTLY the design and never
designs, authors REDs, reviews, commits, merges, integrates, or pushes. Opus read-only fan-outs
remain allowed.

**Fresh separate Codex sessions are the REVIEW authority**: the DESIGN verdict before any build,
and the exact-final CODE + ADVERSARIAL verdicts on the finished patch. Review effort (operator
amendment 2026-07-19): every review dispatched after the grandfathered A13/A14 r1 design review
runs at operator-ratified XHIGH — first, repeat/delta, CODE, and ADVERSARIAL rounds alike; no
review runs at MAX, ultra, or HIGH. (That r1 review alone was already running at MAX when XHIGH
was ratified and was allowed to close; it is history, never a template.) Codex never conducts,
never designs, never authors REDs, never implements, never integrates, never commits, never
merges, never pushes; its precision goes entirely into adversarial review. `/root` is never a
reviewer. The party that AUTHORED an artifact never issues its approving verdict
(author-never-approves).
Gate lines: `DESIGN-VERDICT: APPROVE | REVISE` (before build), `VERDICT: approve | revise` +
`ADVERSARIAL-VERDICT: ...` (on the finished patch). Findings fold RED-first; merge on approve.
When codex is unavailable, slices may land on-branch with an independent Claude reviewer standing
in at the same XHIGH review effort, QUEUED for a retroactive Codex adversarial pass before any
later operator-authorized branch promotion. No fallback review authorizes a push or merge to
`main`. The design's PRECISION is what makes this safe — a design too vague for Opus to implement
faithfully is itself a design defect the DESIGN gate must reject.

**Dispatch integrity (A13):** every Claude worker dispatch is a fresh one-shot session pinned to
its exact model, with no fallback, no resume, and no mixed-model artifact. One-shot means a fresh
non-resumed session, not one response. `/root` imposes no wall-clock deadline, token/turn/response
budget, or brevity target on an authoring event — accuracy and completeness control, and a
provider per-response output limit never authorizes an effort downgrade or acceptance of a partial
artifact; Fable authoring always runs at MAX effort. `/root` live-monitors every dispatch and
structurally rescans the exact closed JSONL transcript after it ends (answering-model check on
every assistant record, tool-name check against the dispatch's allowed set, no-resume check). An
answering model other than the pinned one, or a forbidden tool call, invalidates the COMPLETE
worker output and requires a fresh relaunch from the last accepted immutable pins. One JGUIDA
worker lane runs at a time. A worker failure stops that lane only; a conductor-identity failure
freezes all orchestration. Work splits at natural gate boundaries (design → DESIGN gate →
RED/packet → build → final gates) rather than combining gated phases.

Subagents act in two capacities. (a) Read-only fan-outs: audits, research extraction, bounded
read-only inspection and evidence extraction — never mutating the tree and never issuing any
review verdict; fan-outs run as Opus workers. Review stand-ins are never Opus: under the
codex-unavailable fallback the stand-in is a separate fresh independent Claude reviewer lane at
XHIGH review effort, and approving DESIGN, CODE, and ADVERSARIAL review authority remains
separate Codex (A13 capacity resolution, operator-ratified 2026-07-19).
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

**Continuation routing (operator, 2026-07-18 — A13; supersedes the 2026-07-16 seat assignments;
the role nouns in the SOP (conductor, implementation owner, integrator, reviewer) resolve to
these seats):** `/root` conducts — dispatches, enforces model/tool integrity, verifies every
packet-bound patch in a clean worktree, integrates, and commits on `w3-correction`. Fresh MAX
`claude-fable-5` events author designs, REDs, pitfall matrices, admissions, packet
specifications, and review folds; a Codex-authored fix proposal is review input that a fresh
Fable event re-authors before Codex may gate it. Fresh `claude-opus-4-8` events implement only
approved, packet-bound work. Fresh separate Codex sessions issue the DESIGN, CODE, and
ADVERSARIAL verdicts and never code. No artifact author issues the approving verdict on its own
artifact. Seat text in earlier gate/design records is historical; THIS section is the binding
routing. The receipt law (MF1) and the build-packet bindings are unchanged; the slice SOP's
step 3 and the review-effort/convergence law are amended by the 2026-07-19 XHIGH review-effort
amendment recorded in their own sections.

All continuation commits and integrations remain on `w3-correction`. Slice 10 is an integrated
acceptance checkpoint only; it does not authorize a merge or push to `main`. Any eventual
promotion to `main` requires a separate explicit operator decision after the completed system and
receipts are reviewed.

## Review convergence law (operator-ratified 2026-07-15; review-effort amendment 2026-07-19)

- Effort (operator amendment 2026-07-19; supersedes the 2026-07-15 first-round ladder and the
  never-landed candidate HIGH rule): every review dispatched after the grandfathered A13/A14 r1
  design review runs at operator-ratified XHIGH — first, repeat/delta, CODE, and ADVERSARIAL
  rounds alike; no review runs at MAX, ultra, or HIGH. Invalidated worker attempts are not review
  rounds and do not advance the convergence counter. Fable authoring dispatches always run at MAX
  effort with no conductor-imposed budgets.
- Convergence cap: after TWO `REVISE` rounds on the same artifact, all remaining and future
  findings on it convert to executable REDs/probe scripts and move to the build phase — the
  reviewer then reviews code and test output, never prose re-descriptions of a mechanism.
- Empirical domains (git behavior, browser behavior, filesystem, network) are settled by
  scripts with hostile-case tests from the FIRST round: a mechanism that can be probed must be
  an executable artifact, not prose. (Lesson of the 13-round slice-0 gate, 2026-07-15: five of
  those rounds re-reviewed one probeable shell mechanism as prose.)

## Cross-repository exchange (A14 — operator-ratified 2026-07-18)

Exchange between this repository and any other (semantic-tdd, its constellation siblings, or any
future repository) is IMMUTABLE, CONSUMER-PULL, and CANDIDATE-ONLY. Neither repository ever
writes into the other, and neither mints the other's authority: a producer publishes immutable,
hash-pinned candidate artifacts in its own tree; a consumer pulls, re-verifies, and admits them
under its own laws. Every exchange edge is recorded in
`contracts/orchestration_exchange_policy.json` and pins ALL of: producer repository, producer
commit and tree, artifact path + sha256 digest, contract/schema version, proof receipts and
review receipts (path + sha256), candidate status, a consumer-pull direction, and a per-edge
staleness rule. ANY change to an upstream pin invalidates every downstream admission, packet,
proof, and review derived from it until re-admitted from fresh pins. No cross-repository write
grant exists; dispatching a build lane against any other repository requires that repository's
own ratified target protocol (§ above). The typed actor/session/model/tool/capability/scope
registry remains W7's surface; the policy record pins only the bootstrap seat/exchange laws and
evidence hashes.

## Evidence law (A13 bootstrap — operator-ratified 2026-07-18)

Session transcripts (JSONLs), untracked drafts, and external review banks are EVIDENCE, never
plan authority. Classification follows the event's actual CWD/repository, never the folder a
file was stored in; a Semantic-TDD-CWD session is Semantic-TDD evidence and can never authorize
JGUIDA work. Raw evidence bytes stay local (untracked scratch or outside the repo); tracked
bytes carry only sha256 hashes, classifications, and relevant findings —
`contracts/orchestration_exchange_policy.json` is the durable record, enforced by
`tests/contracts/test_orchestration_exchange.py`. Content authored after an in-session
answering-model transition is non-authoritative and is never reused. An unavailable artifact's
digest is recorded exactly as supplied (abbreviated if supplied abbreviated), marked UNVERIFIED,
and gates nothing; missing digest bytes are never invented.

## The slice SOP — the full 13-step ritual (operator-ratified 2026-07-15; adapts the
## semantic-tdd per-slice loop; the one-line summary at the end is a reminder, not a substitute)

1. **REORIENT** — read the plan-of-record (`docs/plans/ACTIVE.md`), the binding gate records it
   routes to, and verify ground truth against the live tree (never trust a doc over the tree).
2. **DESIGN** — Fable writes the scratch design with open forks BEFORE any code.
3. **DESIGN GATE** — Codex issues `DESIGN-VERDICT` (operator-ratified XHIGH, 2026-07-19; the
   two-REVISE convergence cap above applies). No build before the design's binding state:
   APPROVE, or lawful convergence with findings folded (verified at the patch gates).
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
12. **COMMIT** — conductor only, after all approvals; commit diff must reproduce the reviewed
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
