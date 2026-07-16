# W8 — Process-improvement design: the constellation's machinery, judged piece by piece

> Scratch design record (class: design-record, status: live in `contracts/doc_authority_policy.toml`).
> Author: Fable synthesis lane, 2026-07-16. Status: **awaiting DESIGN-VERDICT** — review effort
> xhigh per the operator's standing session directive (this session's reviews run at xhigh).
> Nothing in this record is authority until gated; the SOP amendments in §9 are PROPOSALS and
> change no AGENTS.md text by themselves.

## §0 Sources, method, and two inventory corrections

Inputs: `scratchpad/work/constellation-inventory-2026-07-16.md` (15 mechanisms across the scout,
the translation-proof adapter, semantic-tdd primary, and the evidence ledger, plus the reference
system's own standing review findings); this repo's AGENTS.md 13-step SOP; ACTIVE.md
(orchestration + the MODULARITY law); the four live build packets in `scratchpad/work/`
(w6-fixes, ratchet-r4, w7-role-integrity, org-integration); the W7 design rev 3; the ratchet
(`scripts/organization/correction_ratchet.py`); the admission records
(`scratchpad/work/*admission*.json`); and two read-only fan-outs run for this record:
a defect-pattern hunt over THIS repo and a spot-check of the constellation files each judgment
leans on.

Spot-check outcome: the load-bearing inventory facts are confirmed against source (the miner's
hardcoded doctrine/lens tuples; the slice-proof validator's sealed result type, its
pre-green-failure requirement with a real nonzero exit code, and its hardcoded obligation
strings; the role gate's sealed authority type and fixed record homes; candidate-only stamps
throughout; the pinned-commit sharing pattern). **Two counts in the inventory are wrong and are
corrected here:** the translation-proof run receipt carries **16** equivalence clauses (the
inventory's "7" counted a core prefix) and **4** verdict channels (not 5), and both live in the
adapter's core code (`core/verdict.py`, `core/receipts.py`), not in its spec schema. No judgment
below depends on the miscounted numbers; §6 builds only on the named clauses that were verified
(mutations must flip red, target untouched, no-overclaim text present).

## §1 The discipline under judgment — and the reference's own honest standing

Six patterns recur across every constellation tool: (1) **gather/decide split** — a read-only
gatherer emits verdict-free facts; a separate validator is the only thing that mints an
admissible/sufficient/done brand; (2) **candidate-only outputs** — every gatherer stamps itself
unable to mark anything done; (3) **status never outruns proof** — a record's declared status
requires the proof artifacts behind it; (4) **contracts-as-data** — vocabularies, rosters, and
policy live in TOML/JSON, not code constants; (5) **target-parameterization** — tools take the
target as a parameter, write outside it, and prove it untouched with before/after manifests;
(6) **pinned-commit sharing** — siblings consume the one shared engine at a pinned commit,
never a vendored copy.

The reference's own 2026-07-15 reviews judged its end-to-end chain REVISE: the checkers are
sound, but several links are written-not-enforced — a verified authority result gets computed
and then dropped instead of being consumed by the real effect; proof booleans get computed from
file existence and text presence; admission records assert their own validity instead of being
issued and then consumed. §5 hunts exactly those three failure shapes in THIS repo. The headline
of the hunt: **our verification layer has the same standing** — the ratchet, the slice-patch
extractor, the admission tool, and the receipt validators are each internally strong and
hostilely tested, and none of their verdicts is consumed by any commit-path mechanism. W7's
design already closes this for lane work (its integrate subcommand recomputes everything it
trusts); the adoptions below close it for the rest of the slice ritual.

---

## §2 (a) THE MINER — claim-audit against this repo and future targets — **ADAPT**

**What it is (confirmed):** a read-only lane that crawls a target repo's text surfaces plus a
doctrine-file list under four lenses (missing-red, authority-overclaim, stale-documentation,
candidate-boundary), derives the repo's intended process, emits candidate findings + proposed
RED shapes, and proves the target byte-unchanged afterward. It mints nothing.

**Judgment: ADAPT — consume it as an external audit tool at a pinned commit; do not rebuild it;
do not vendor it.** Two uses:

1. **Against THIS repo (standing audit lane).** Our docs-currency guard
   (`tests/contracts/test_process_docs_currency.py`, upgraded by org CR-10..CR-13) is a CLOSED
   enforcement: it checks declared rows. The miner is the OPEN discovery instrument: it finds
   the stale claims and missing REDs we never declared. The two compose as
   discovery-then-enforcement: miner findings either become new concept rows in the currency
   policy, become Fable-authored REDs, or are refuted — never a fourth, silent state.
2. **Against future target repos (product-side).** Before a restyle lane touches a target
   (odinproject, DEMO B), a claim-audit run gives the target's own stale-doc/overclaim map as
   declared preconditions, and its ingress candidate is already the same record shape our
   capture engine emits (candidate-only, source-referenced).

**Composition with SOP step 4 (RED authoring):** the miner's `proposed_reds.json` is INPUT to
step 4, never a substitute for it. Fable reads the candidates and authors the actual failing
tests; the tool that mined a claim never mints the law that governs it — the same
author-never-approves separation the SOP already runs on. **Composition with the untouched-
receipt discipline:** the miner's before/after manifest receipt is the read-only-lane analog of
our worktree isolation; an audit run whose receipt shows the target changed is inadmissible as
evidence, full stop.

**Why ADAPT and not ADOPT:** its doctrine list and lens seeds are hardcoded module tuples tuned
to semantic-tdd (confirmed at source). Against this repo it runs only under the `generic`
profile, which honestly downgrades its own confidence. The right fix — doctrine/lenses as
swappable contract data — is an upstream change to the scout, recorded here as a candidate for
that repo's own process, not work in this one.

- **Replaces:** nothing; augments SOP step 1 (REORIENT) and the docs-currency guard.
- **REDs:** R-W8-1, R-W8-2 (§10).
- **Cost:** small (a runner script + intake law; the miner already exists).
- **Placement:** a standing auditor-role lane (W7 vocabulary: `audit_report`), output under
  `dev/reports/audits/`, startable after org L1/L2 land the governed homes; product-side it
  rides the DEMO-B pre-capture step.

## §3 (b) THE VALIDATOR DISCIPLINE — sealed verdicts, consumed admissions — **ADOPT (phased)**

**The rule (confirmed at source):** only a validator mints "admissible/done"; records carry no
capability; a status may never outrun its proof. The reference seals this in Rust types whose
constructors are private to the validator.

**Audit of OUR admissions and ratchet against it:**

- `scratchpad/work/{ratchet,slice-patch}-admission.json` are honest about being candidates
  (they carry candidate-only stamps) but they are **assertion-shaped**: the recorded
  `observed_output_sha256` is recomputed from the record's OWN embedded output string — a
  self-referential check; the validating tool (`scripts/organization/bootstrap_red_ref.py`)
  freshness-binds the RED file hash, base revision, command shape, and age window, but its
  `gate()` accepts an externally supplied observation dict it never re-runs; there is no
  issuer, no per-run nonce, and — decisive — **nothing consumes an admission**: no commit-path
  mechanism ever demands one. `slice-0-admission.json` is the exemplar: the embedded tool
  verdict says the task is not admissible, and a prose note explains that away.
- The admissions also live only in the gitignored scratchpad — no typed committed home (org L2
  fixes the home; this section fixes the trust shape).
- The ratchet's `run_and_verify` is genuinely a trusted runner (it runs the pinned command
  itself, validates the run's honesty, loads the parent via git, verifies inseparably) — the
  best validator in the repo — but its verdict dict is consumed **only by its own tests**; CI
  runs plain unittest discovery, and no integrate/commit step demands a ratchet pass.

**Do we adopt issued-capability-style admissions? Yes — by folding into W7, not by building a
second mechanism.** W7's record law already is the issued shape for lane work: broker-minted
nonce, committed anchor, integrate-time recompute. The adoption is three moves:

1. **Close the self-report seam:** the admission tool's public gate derives its observation
   from its own execution (it already knows how — `observe_red` runs the test); an externally
   supplied observation dict is refused. Same move ratchet-r4 finding #2 makes on the ratchet.
2. **Make admissions consumed:** the slice-proof gate (§4) resolves each RED arm's admission
   record from the committed home, recomputes the RED-file hash against the slice base, and
   refuses on any mismatch — an admission becomes evidence a gate consumes, not a file that
   sits there. W7's `integrate` then consumes the slice-proof record (§4), completing the chain.
3. **Status backing for the plan:** ACTIVE.md rows claiming LANDED/DONE must name commit or
   proof refs that resolve — the evidence-ledger's "status never outruns proof" law applied to
   our one plan file, as an upgrade to the docs-currency guard (org CR-13 starts this with
   projection-owner rows; R-W8-5 finishes the landed-claims arm).

**Honest ceiling, stated:** Python has no compiler-sealed constructors. Our seal is the same
one the ratchet and W7 use — a single public entry with no injection parameters, gather and
decide in one trusted run, decide→persist→print, and downstream consumption by hash. That is
the reference's discipline at this repo's language ceiling.

- **Replaces:** free-floating admission JSONs + prose "done" statuses.
- **REDs:** R-W8-3, R-W8-4, R-W8-5 (§10).
- **Cost:** R-W8-3 small; R-W8-4 small once §4 exists; R-W8-5 medium (rides the org L4
  docs-currency slice).
- **Placement:** admission hardening = its own small W8 slice; consumption = §4's gate;
  status backing = org L4.

## §4 (c) THE SLICE-PROOF WIRE — compile SOP steps 8–11 into ONE accept/deny — **ADOPT**

**What the reference does (confirmed):** its most mature machinery binds a real green proof
run + taxonomy completeness + per-arm RED conformance (a real pre-green failing witness with a
nonzero exit code) + mutation proof + an independent review receipt into ONE validator whose
success mints a sealed result; the asserted outcome is audit-only and never trusted.

**Our steps 8–11 today are the same conjunction executed as ritual:** the conductor re-runs the
suite and ratchet (8), demands mutation witnesses (9), demands MF1 receipts (10), and dispatches
the code+adversarial review (11) — four hand-carried obligations whose conjunction no mechanism
checks. The hunt (§5) shows what that costs: every one of those elements exists and none is
structurally consumed.

**Judgment: ADOPT — compile the conjunction.** Design:

- **Files:** `scripts/organization/slice_proof_gate.py` (pure stdlib; distinct from the
  existing `slice_patch.py`, which stays the patch extractor) +
  `contracts/slice_proof_policy.toml` + REDs in `tests/contracts/test_slice_proof_gate.py`.
- **Entry:** `slice-proof --slice-id S --base REF`. One machine line
  `SLICE-PROOF: OK | REJECT reason=<code>`, exit 0 only on OK, decide→persist→print; the record
  lands at `dev/reports/admissions/slice-proof-<slice>.json` (closed schema, full-snapshot
  style like W7's records).
- **The gate GATHERS fresh, trusts no note:**
  1. **proof runs** — it invokes the ratchet's `run_and_verify` itself (the trusted runner
     becomes structurally load-bearing for the first time) plus the slice's pinned focused
     command; asserted results in any input are audit-only.
  2. **RED arms** — per slice RED: `{red_ref, admission_ref, pre_green_exit_code (1..255 from
     the admission witness), failure fingerprint, mutation_ref}`; refusal codes mirror the
     reference: missing arm · no pre-green failing witness · failure-reason mismatch · target
     not the live surface · mutation unproven. Consumes §3's hardened admissions.
  3. **mutation matrix** — the witness table (mutant id → reddened test → output digest) with
     zero survivors; a probe that flips nothing is vacuous and refuses.
  4. **receipts** — the MF1 roster is DERIVED (touched visible paths × the page manifest ×
     the theme/viewport matrix), never hand-listed; every roster receipt passes the strong
     provenance validator with recomputed hashes (§5's byte-binding arm).
  5. **review receipts** — resolved through W7's verify-review (verdict grammar, provenance
     sidecar, author ≠ reviewer by resolved principal), refs committed in HEAD.
  6. **taxonomy completeness** — `slice_proof_policy.toml` declares closed rows per slice
     kind (seed rows: red_arm, mutation, property, ratchet, focused_suite, receipts_1280,
     probe_390, provenance, theme_matrix, review_code, review_adversarial, docs_updated,
     homes_registered); every row carries a disposition `satisfied | not_applicable + reason`;
     an unaddressed row refuses. This is the COMPLETENESS mechanism applied to process.
- **Consumption (the part that kills validate-then-drop):** W7's `integrate` gains one clause —
  a builder-lane record cannot transition reviewed→integrated without a fresh SLICE-PROOF OK
  whose record ref + hash ride the assignment. The SOP steps 8–11 remain the human-readable
  law; the gate is their compiled form; the policy file cites the step numbers so prose and
  data cannot drift apart silently.

- **Replaces:** the ritual conjunction of steps 8–11 (steps stay as text; enforcement moves
  into the gate).
- **REDs:** R-W8-6..R-W8-9 (§10).
- **Cost:** large — the flagship W8 build.
- **Placement:** its own slice AFTER the W7 build (needs verify-review + record law) and after
  ratchet-r4 (needs the hardened runner); in force before correction slice 10 so the merge
  review consumes it. Being an engine piece, it is born portable per §8 (policy as data, target
  parameter, no repo literals).

## §5 (d) THE CONSTELLATION'S OWN DEFECTS AS CAUTIONARY REDS — the hunt, and what it found

Three failure shapes from the reference's own reviews, hunted here read-only (fan-out over the
ratchet, slice-patch, receipts pipeline, provenance validators, admissions, docs-currency guard,
and the W7 design):

**D1 — computed-then-dropped verdicts (found, systemic).** `run_and_verify` is called only by
its own tests; CI is plain unittest discovery; the real baseline is never gated through the
trusted runner. `slice_patch.py` ends at `canonical_patch` returning reviewable bytes — no
mechanism binds those bytes to the commit that follows (AGENTS step 12's "commit reproduces the
reviewed patch hash" is ritual today). No minting/consuming token exists anywhere in
`scripts/organization/`. → Covered by: the §4 gate consuming the ratchet (R-W8-6) and W7
integrate consuming the gate (R-W8-9); W7's own V5 (patch-hash equality at integrate) covers
the slice-patch binding — the wiring note is that integrate should obtain its patch bytes via
`canonical_patch`, keeping one extractor. W7's design already internalized this shape
(recompute-at-integrate; stored verdicts inert) — audited clean.

**D2 — file-existence / text-presence proof booleans (found, split verdict).** The strong path
is real: `rendered_facts/provenance.py::validate_provenance` has a closed field set, rehashes
artifact and content bytes, and re-derives the canonical compressed payload — better than the
reference's Python was. But: five contract-test files still accept receipt EXISTENCE as proof
(`test_visual_receipt_provenance.py` in places, `test_page_manifest.py`,
`test_theme_continuity.py`, `test_design_conformance.py`, `test_dashboard_surface.py`);
producer honesty everywhere is a claimed string (producer field equality, browser version
prefix, command substrings — the recorded command is never re-executed); and the docs-currency
guard is itself a pure text-presence check (it proves the skill MENTIONS the process, not that
the process holds). → REDs R-W8-10 (regenerate-and-compare in the gate: DOM probes re-produced
in the clean worktree and compared by content hash; screenshots rehashed + non-blank + strong
validator — the render-nondeterminism ceiling for pixel bytes is stated, not hidden) and
R-W8-11 (one shared strong-validation helper; a forged self-consistent receipt bundle fixture
must refuse through the helper; the five existence-only call sites migrate to it). Org CR-13's
projection-owner rows are the docs-currency arm of the same fix (cited, not duplicated);
R-W8-5 (§3) adds the landed-claims arm.

**D3 — assertion-shaped admissions (found).** Fully audited in §3; REDs R-W8-3/R-W8-4. The
already-packeted members of these same families are cited as such, not re-specified: ratchet-r4
findings #1 (candidate command executes before verification) and #2 (injection seams on the
public entry), and w6-fixes items 3 (restore authority not bound to its target), 8 (validators
that skip their law when peer evidence is omitted), and 12 (hash fields format-checked, not
recomputed). The pattern class is demonstrably live here; the packets already carry those REDs.

## §6 (e) TPA — the translation-proof shape at our transform boundary — **ADAPT the receipt,
## SKIP the engine**

**What it does (confirmed, with §0's count correction):** proves a SECOND artifact preserves a
declared observable contract of a FIRST — at least two legs, declared observations, named
mutations pinned `expected_effect: red` (a mutation that fails to flip red fails the clause),
target-untouched manifests, mandatory no-overclaim text — decided as one clause receipt.

**Where it earns a place in our chain:** NOT inside measured facts → invariants → REDs — that
chain is single-artifact and §4 governs it. It earns its place exactly where our program has
TWO artifacts that must agree:

1. **The restyle boundary (O5 / DEMO B):** leg A = the pre-restyle frozen pack (the
   hash-pinned restore point ACTIVE.md already mandates); leg B = the post-restyle rendered
   site. Observations = the preserved-aspect invariants (everything the owner did NOT elect to
   change); mutations = named token/rule mutants that must flip the preserved-aspect predicate
   red; no-overclaim = our existing brand-claim law ("satisfies <profile> vN — receipts
   attached"). One clause receipt decides the restyle's fidelity instead of scattered checks.
2. **The design-doc lane (DEMO A):** leg A = profile DATA from the document; leg B = the
   generated site; fidelity-confirm becomes the same closed receipt.

**SKIP:** the adapter engine itself (its subject is compiled-program behavior under pinned
toolchains; nothing there transfers). We adopt the record SHAPE and clause LAW as our own
contract, sized to our clauses — not the miscounted 16.

- **Replaces:** ad-hoc fidelity-confirm assertions in the DEMO plans.
- **RED:** R-W8-12 (§10).
- **Cost:** medium.
- **Placement:** the O5/DEMO-B lane, after the w6-fixes packet lands (needs the served-tree
  custody digest from its item 17).

## §7 (f) MUTATION + PROPERTY ENFORCEMENT — packet audit + the template rule — **ADOPT**

Audit of every current packet against SOP steps 4 (RED + pitfall matrix + property cases) and
9 (mutation + property proof):

| Packet | Step 4 | Step 9 | Gap |
|---|---|---|---|
| ratchet-r4 | REDs with right-reason + witnesses | full mutation matrix, zero survivors, witness table | no property row (unittest-output parsing IS generative) |
| w7-role-integrity | REDs + pitfall matrix (design §5 L1–L5) | M1–M6 named mutants in acceptance | no property row (registry disposition law IS generative) |
| w6-fixes | 20 REDs, pre-green witness + load-bearing clause | per-RED witnesses only | no zero-survivor matrix; no pitfall section; no property row (host normalization, srcset grammar ARE generative) |
| org-integration | CR-1..14 with fails-today column | none in the packet (named mutant kills live in the design doc only) | packet does not bind the matrix; no pitfall/property rows |
| W6 capability lanes A/B/C | — | — | **no persisted packet files at all** — the bindings existed at dispatch and were not retained, so they cannot be audited |

Verdict: the discipline is real but ENCODED UNEVENLY — strongest where review rounds forced it
(ratchet-r4), weakest where a packet leans on its design doc or was never persisted. The three
W6 capability packets named in this job's brief do not exist as files; that absence is itself
the finding.

**The rule that makes it structural:** a build packet is valid only with four closed sections —
(1) RED table (test id, right-reason failure, pre-green witness command); (2) PITFALL matrix
(top ~5 authority-poisoning lies → guard, or an explicit recorded n/a); (3) MUTATION matrix
(named mutant → killing test; zero-survivor requirement; witness digests due back with the
patch); (4) PROPERTY row per generative domain (or an explicit non-generative declaration).
Enforcement: `contracts/build_packet_policy.toml` + a validator; the packet artifact is
committed and referenced by path+sha256 from its W7 assignment record (packets stop being
scratch-only); W7's dispatch broker refuses a lane whose packet is unresolvable or shape-invalid.

- **Replaces:** packet quality by author habit.
- **REDs:** R-W8-13, R-W8-14 (§10).
- **Cost:** small–medium.
- **Placement:** validator + policy = an early small W8 slice (applies to every packet authored
  from then on); broker consumption lands with the W7 integration commit.

## §8 (g) PORTABILITY — the packaging rules our engine pieces must follow — **ADOPT as data**

The reference's portability failures are precise: hardcoded doctrine/lens tuples, fixed
record-home constants, obligation strings baked into validator code, operator-specific seat
tokens. Our MODULARITY law (ACTIVE.md, 2026-07-16) already outlaws the class; these are the
concrete rules, each stated so a RED can hold it:

1. **Authority vocabularies are data.** Any closed vocabulary/roster/policy an engine piece
   enforces loads from a contract file, never a module tuple. (Live in-repo violation: the
   probe's invented in-code aspect vocabulary — already w6-fixes item 5; cited, not
   re-specified.) Stated exception: enforcement-surface constants pinned by their own REDs
   (W7's read-floor tool list) are lawful — they are the enforcement itself, changed only via
   the reviewed maintenance flow.
2. **Targets are parameters.** Every engine entry point takes its target (root/URL/ledger
   path) as a parameter; outputs land outside the target; read-only tools prove the target
   untouched (before/after manifests). No engine module embeds this repo's absolute paths or
   repo-name literals.
3. **Obligation strings route through policy.** Refusal contracts cite rows of the loaded
   policy file, never a foreign doc path baked into code (the reference's validator pins its
   plan-section strings in source — the exact thing an adopter cannot rehome).
4. **Capability ships as skills.** `skills/<name>/SKILL.md` with `{name, description}`
   frontmatter; donors named by reference, never vendored; generated/derived skills carry
   candidate posture until reviewed.
5. **Cross-repo consumption is pinned.** Any invocation of a sibling engine (the §2 miner; our
   engine consumed by a target repo) references a pinned commit — never a floating path, never
   a copy.

- **Replaces:** MODULARITY as prose only.
- **REDs:** R-W8-15, R-W8-16 (§10); rule 5 is asserted inside R-W8-2's fixture.
- **Cost:** small each.
- **Placement:** one W8 portability slice + the org L4 skill refresh; new engine pieces
  (§4's gate included) are born under these rules.

## §9 (h) UI-SPECIFIC SOP AMENDMENTS — PROPOSALS ONLY (gated; no SOP text changes here)

Our slices prove rendered surfaces, so the generic SOP steps have UI-shaped sharpenings. Each
is a proposal for the normal design→gate→doc-law-edit flow:

- **P-H1 (step 4):** for a visible-surface slice, the pre-green witness includes a
  rendered-fact run (probe packet digest), not source-text parsing alone; and the property row
  is concrete: the declared viewport × theme × state matrix IS the generative domain — REDs
  enumerate it from manifest data with per-cell coverage or declared gaps (the same
  matrix-cover law w6-fixes item 9 applies to packs). Enforced via the §7 packet validator's
  ui-slice rows (R-W8-17).
- **P-H2 (step 8):** conductor verification in the clean patched worktree includes SERVING the
  site and probing every affected route — rendered verification, not unittest alone; the fresh
  probe packet rides the verification record. Enforced as a §4 taxonomy row (R-W8-18).
- **P-H3 (step 9):** every visual invariant names at least one rendered-surface mutant (token
  flip, rule delete, owner swap) that flips its predicate on the SERVED page; a mutant that
  only flips a source-text assertion is not a visual witness. Enforced inside R-W8-17's packet
  rows + §4's mutation arm.
- **P-H4 (step 10):** the receipt roster is DERIVED (touched paths × page manifest × theme
  matrix), never hand-listed, and every sidecar passes the strong byte-binding validator.
  Enforced by §4 arm 4 (R-W8-8, R-W8-10).

- **Replaces (once gated):** the generic phrasing of steps 4/8/9/10 for UI slices.
- **Cost:** small — every proposal rides machinery already specified above.
- **Placement:** text amendments land with the same commits that land their enforcing REDs
  (§4 and §7 slices); until then the proposals bind nothing.

## §10 RED index — 18 new REDs specified by this design

All conductor-authored, observed failing for the right reason before their builds; today each
fails because its module/policy/fixture does not exist — the same witness shape as the existing
admissions. Files named per slice.

| ID | Test (file :: name) | Proves | Cost |
|---|---|---|---|
| R-W8-1 | `test_miner_intake.py::test_audit_finding_requires_disposition` | an accepted miner finding carries disposition red-authored / declared-gap / refuted + source refs; a dispositionless finding reddens | S |
| R-W8-2 | `test_miner_intake.py::test_miner_invocation_is_pinned_and_read_only` | the runner config pins the scout commit (40-hex) and the run receipt shows target unchanged + no target commands | S |
| R-W8-3 | `test_bootstrap_red_ref.py::test_gate_refuses_unexecuted_observation` | the public gate derives its observation from its own run; an externally supplied observation dict refuses | S |
| R-W8-4 | `test_slice_proof_gate.py::test_red_arm_resolves_and_rebinds_admission` | each RED arm's admission resolves from the committed home; RED-file hash recomputed against the slice base; mismatch refuses | S |
| R-W8-5 | `test_process_docs_currency.py::test_landed_claims_resolve_to_commits` | every ACTIVE.md landed/done row names a commit/proof ref that resolves in history | M |
| R-W8-6 | `test_slice_proof_gate.py::test_gate_runs_ratchet_itself` | the gate invokes the trusted runner; an asserted-green input without a fresh run refuses | L* |
| R-W8-7 | `test_slice_proof_gate.py::test_vacuous_mutation_matrix_refuses` | a matrix with a survivor, or a probe that flips nothing, refuses | L* |
| R-W8-8 | `test_slice_proof_gate.py::test_receipt_roster_is_derived` | a patch touching a visible path with no matching roster receipt refuses; hand-listed extras refuse | L* |
| R-W8-9 | `test_role_gate.py::test_integrate_consumes_slice_proof` | reviewed→integrated without a fresh SLICE-PROOF OK ref+hash refuses (extends W7 V-series) | S |
| R-W8-10 | `test_slice_proof_gate.py::test_dom_probes_regenerated_and_compared` | DOM probes re-produced in the clean worktree match committed content hashes; screenshots rehashed + non-blank + strong-validated | L* |
| R-W8-11 | `test_visual_receipt_provenance.py::test_forged_bundle_refused_via_shared_helper` | one shared strong-validation helper; a self-consistent forged bundle fixture refuses; the five existence-only call sites route through it | M |
| R-W8-12 | `test_transform_equivalence.py::test_receipt_requires_all_clauses` | a restyle receipt missing any clause (restore-point ref, preserved-aspect observations on both legs, mutants flipped red, no-overclaim text, custody digests) refuses | M |
| R-W8-13 | `test_build_packet_policy.py::test_packet_requires_four_sections` | fixture packets missing RED/pitfall/mutation/property sections refuse; recorded n/a passes | S |
| R-W8-14 | `test_role_gate.py::test_dispatch_refuses_invalid_packet` | broker refuses a lane whose packet ref is unresolvable or shape-invalid (extends W7 §4.2) | S |
| R-W8-15 | `test_engine_portability.py::test_engine_modules_carry_no_repo_literals` | closed engine-module roster: no absolute paths / repo-name literals; entry points expose their declared target parameter (signature name-set assertions) | S |
| R-W8-16 | `test_engine_portability.py::test_skills_are_reference_packaged` | every skill has parsing `{name, description}` frontmatter; no vendored sibling sources under `skills/` | S |
| R-W8-17 | `test_build_packet_policy.py::test_ui_slice_packet_rows` | a ui-kind packet must carry the viewport×theme×state matrix row and a rendered-surface mutant row | S |
| R-W8-18 | `test_slice_proof_gate.py::test_visible_slice_requires_fresh_probe` | a visible-surface slice-proof without a fresh clean-worktree probe packet refuses | L* |

L* = rides the §4 gate build (one large slice carries R-W8-6/7/8/10/18).

## §11 Sequencing + cost ledger

| Slice | Contents | Cost | After |
|---|---|---|---|
| W8-1 | packet policy + validator (R-W8-13/14/17; 14 activates at W7 integration) | S | now |
| W8-2 | admission hardening (R-W8-3) | S | ratchet-r4 lands |
| W8-3 | receipt byte-binding helper + call-site migration (R-W8-11) | S–M | now |
| W8-4 | **the slice-proof gate** (R-W8-4/6/7/8/9/10/18) | L | W7 build + ratchet-r4 |
| W8-5 | portability contract + skill law (R-W8-15/16) | S | with org L4 |
| W8-6 | miner consumption lane (R-W8-1/2) | S | org L1/L2 homes |
| W8-7 | transform-equivalence receipt (R-W8-12) | M | w6-fixes; O5/DEMO-B lane |
| — | docs-currency landed-claims arm (R-W8-5) | M | org L4 |
| — | SOP amendments P-H1..P-H4 (text) | S | gated with W8-1/W8-4 |

Every W8 slice runs the full 13-step ritual itself — designs gated, REDs observed failing,
Opus-built under bound packets, mutation-witnessed, reviewed, conductor-committed. The gate and
validator pieces are engine pieces under the MODULARITY law and are born under §8's rules.

## §12 Gate

This design ends here, **awaiting DESIGN-VERDICT** (xhigh per the operator's standing session
directive). On APPROVE: W8-1 packets first (cheapest structural win), then the §11 order.
