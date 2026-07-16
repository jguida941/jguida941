# W3C-ORG — Root-wide organization law (scratch design 2026-07-15; rev 2, r1+r2 findings folded 2026-07-16)

> Conductor-authored design record (Fable). Gate history: r1 `DESIGN-VERDICT: REVISE`
> (8 findings — 2 critical, 6 high; folded 2026-07-16). r2 `DESIGN-VERDICT: REVISE` at xhigh
> (7 findings — 4 blocking, 2 major, 1 minor; r1 disposition: f3/f7/f8 resolved,
> f1/f2/f4/f5/f6 aspects re-opened). **AGENTS.md review-convergence law INVOKED 2026-07-16**
> (two REVISE rounds on one artifact): every remaining finding is folded into this rev AND
> converted to an executable RED (§RED-convergence, CR-1..CR-14); the work proceeds to BUILD
> under those REDs — the reviewer next sees code and test output on the exact final patch,
> never a third prose round. Fold map in §gate.

## Context — the gap, and the proof-system correction

`contracts/repo_layout.json` (`ProfileRepoLayout`) was a PARTIAL port of the kernel's org law:
it governs `scripts/ tests/ contracts/ docs/ site/ assets/receipts/` but has **no root-wide
top-level census**, no `dev/reports` category taxonomy, no retention, and does not list
`scratchpad/` as clutter. Consequence (observed 2026-07-15): `scratchpad/` and `dev/` appeared as
undeclared top-level dirs with no failing test, and 14 Codex gate transcripts (~4.6 MB) got
staged toward a public commit.

**The correction is NOT "delete the mess."** The Codex gate transcripts and admission records are
**typed durable proof** in the semantic-TDD system — the evidence chain that each DESIGN / CODE /
ADVERSARIAL gate actually happened, referenced by path + sha256. The reference kernel commits them
to `dev/reports/<category>/` with typed retention; only regenerable working files live in the
gitignored `scratchpad/`. So this law does two things: (1) makes `scratchpad/` ephemeral
(gitignored clutter — done as a reversible interim step), and (2) **relocates the durable proof
to committed governed homes** so it enters the proof system instead of being lost or dumped loose.

Reference authorities (verbatim patterns extracted read-only): kernel
`primary/semantic-tdd/tests/org_layout_policy.toml` (`OrgLayoutEndStatePolicy`) +
`dev/THE-REPO-SHAPE.md` (whole-tree bijection census) + `scripts/checks_org/check_org_layout.py`;
sibling `repo-surface-scout/contracts/repo_layout.json` org fields +
`tests/process/test_plan_layout.py`.

## Authority ownership matrix (r1-f6 — binding; one owner per axis, overlap reddens)

- `contracts/repo_layout.json` (`ProfileRepoLayout`) owns **placement only**: census, shapes,
  clutter, evidence-home registration. Its legacy `required_docs` / `live_docs` /
  `stale_reference_tokens` fields are **deprecated as rosters** in the same slice that lands this
  law (marked deprecated, retained as pointers to the owning contracts until removed) — no
  duplicated roster survives in a non-owner (`duplicate_authority_roster` reddens).
  **Ratified owner (r2-g2):** slice L1 transitions the contract's own authority metadata —
  `authority_status: candidate_only → ratified_root_shape_owner`, `cannot_mark_done` dropped,
  the external-decider sentence retired from `purpose`, `schema_version` 1→2 — so the contract
  and the AGENTS.md "shape authority" claim finally agree. The in-code rosters `MODULE_HOMES`
  (`scripts/organization/layout_contract.py`) and `TEST_GROUPS`
  (`scripts/organization/tests_layout_contract.py`) become **checked projections** of this
  contract, registered in a new `projections` section; the guard asserts contract↔code parity
  and divergence reddens (`unregistered_projection`) — no independent roster owner survives.
- `contracts/doc_authority_policy.toml` owns **plan/lifecycle membership** (which handoff docs
  are `live | folded | superseded`) and is the **machine-readable slice-DONE authority**: a slice
  is DONE when its design-record `[[doc]]` row's status leaves `live`.
- `contracts/process_docs_currency_policy.toml` (new) **consumes** the two above and owns the
  model-facing register + block-ID projections (what the process docs must teach — §docs-currency).
- `contracts/role_registry.*` owns **actor/seat data** (who builds, who reviews). AGENTS.md owns
  SOP *process prose*; role facts asserted anywhere else must be projections of the registry.
  **Interim state (r2-g4):** the registry does not exist yet — AGENTS.md and HANDOFF.md cite it
  with explicit until-W7 interim language, which is the binding source until the W7 design
  lands it. No guard in this design ever asserts against the nonexistent file: the
  docs-currency slice (L4) is SEQUENCED AFTER the W7 registry lands, and its role rows carry
  an explicit `interim_source` field until then (§docs-currency).
- `repo_layout.json [dev_reports]` owns **evidence schema + retention classes** (§law-3);
  categories other designs need (W7 `role_assignments`) are reserved here, never forked.

## The law (extends `ProfileRepoLayout`, COMPOSE-NOT-FORK — one contract, new sections)

1. **`[[top_level]]` closed census over TWO explicit universes (r1-f1).**
   - *Universe A — the candidate shipping tree:* read from `git ls-files --stage -z` over the
     tree under review (in the §13.2 verify worktree the index IS the candidate final-patch tree;
     the census never consults the dirty main worktree's working files). `kind` derives from the
     git MODE, closed vocab `{file 100644, executable 100755, symlink 120000, submodule 160000,
     dir (prefix)}` — never from `Path.is_dir/is_file` dereferencing. Every tracked top-level
     entry has a row `{path, kind, owner, purpose, status: landed|owed}`; bijection both ways:
     an undeclared tracked entry reddens (`undeclared_top_level`); a declared-but-absent `landed`
     row reddens (`phantom_top_level`). An `owed` row must carry `{debt_ref, expires_utc}` —
     owed-with-no-live-debt or owed-past-expiry reddens (composes with §law-4 debt grammar).
     A top-level symlink or submodule with no row explicitly declaring that kind reddens.
     Contract LOAD rejects duplicate census rows (never silent last-wins collapse); the guard
     rejects case-fold and NFC/NFD-normalization collisions across declared and observed paths.
   - *Universe B — the live-control surface (local preflight, never a clone-blocking contract
     test):* a CLOSED enumeration of ignored-but-influential controls. Rows at ratification:
     `.claude/` (agent harness; declared **non-authoritative** — no repo-binding behavior may
     depend on ignored content; SETTLED r2 — the r1 amendment fork is CLOSED: any hook row in
     `.claude/settings.json` is a local convenience mirror ONLY, whose authority derives from
     the tracked `contracts/role_registry.*` plus a tracked mirror-parity check; W7's
     enforcement mechanism CONFORMS to this row — if W7 wants different authority mechanics,
     that is a W7 design amendment at W7's own gate, and this enumeration does not reopen),
     local git config/hooks
     (`core.hooksPath` must be unset or resolve into a tracked governed directory; anything else
     is declared outside the trust model), `.venv/` + caches (inert). An ignored root-level entry
     outside the enumeration is a preflight finding (`unenumerated_control`).
   - Current 16 tracked entries enumerated as `landed`; `dev` and the repo-local `CLAUDE.md`
     enter as `owed` rows (landed by slice 2 and the docs-currency slice respectively);
     `metrics.*.svg`, top-level files, and `assets/` loose SVGs get owned rows. **This is the
     rule that makes a new `scratchpad/`/`dev/` structurally unconstructable-to-ship without a
     declared home.**
2. **`generated_clutter` — typed rows, root-anchored, behavior-probed (r1-f7).** Each clutter
   entry is `{path, kind, class: never-tracked}` with a REQUIRED root-anchored `.gitignore`
   pattern (`/scratchpad/`, `/mutants.out/`, `/.hypothesis/`, `/reports/`) — the current
   unanchored `scratchpad/` line is corrected in the build. A TRACKED clutter path is a hard
   `tracked_clutter` violation (index-based repository gate, deterministic in a clean clone;
   present-untracked is inert). Ignore behavior is proven in HERMETIC temp repos via
   `git check-ignore --no-index` (nested path, later-negation, tracked-exception, linked-worktree
   cases) — never by string-parsing `.gitignore` with slash-stripping. The r0 `misplaced_proof`
   filename heuristic (`codex-*.md` / `*-admission.json` under scratchpad) is RETIRED as a
   contract test: it both misses durable proof under other names and misfires on regenerable
   files, and a blocking test over ignored content diverges between a developer tree and a clean
   clone. Durable-evidence identity comes from producer/schema/manifest membership (§law-3,
   §intake); scratch hygiene runs as a local preflight/intake check.
3. **`[dev_reports]` — typed evidence homes with machine-read manifests (r1-f3).** Closed
   `categories` map, each `{owner, purpose, retention}`. Retention grammar is TYPED:
   `permanent | retire-when-slice-done | keep-newest-N` with `N` a schema-validated positive
   integer (never prefix-string parsing); `keep-newest-N` orders by the required manifest field
   `produced_utc` (ISO-8601 UTC, ties broken by path); `retire-when-slice-done` binds to the
   machine-readable slice-DONE authority (§matrix: the subject design-record's lifecycle status
   leaving `live`). Each category carries a `manifest.json` with one CLOSED row per artifact:
   `{path, sha256, schema_id, schema_version, subject (slice/design id), producer, produced_utc,
   retention_class, referenced_by (nonempty list of tracked paths)}`. The guard RECOMPUTES every
   digest, validates the typed schema, asserts manifest↔file bijection — an unlisted file in a
   registered category reddens (`unmanifested_artifact`; this kills the stray
   `AUTHORIZED-INTENT-MATH-PROOF-1` regardless of parent registration) — and verifies a
   structural back-reference: each `referenced_by` doc exists and cites the artifact's path or
   digest, so mutating a transcript, a digest, or a referencing document reddens. Retirement
   moves rows into the registered `archive` category rooted UNDER `dev/reports/archive/<slice>/`
   (inside the taxonomy — the r0 out-of-taxonomy `dev/archive/reports/` home is dropped); a
   completed-slice retention breach reddens. File-COUNT rules are DROPPED (the r0 singleton rule
   was vacuous and padding-prone); completeness is manifest/schema completeness.
   **Bijection universe + control files (r2-g6):** each category declares a CLOSED
   `control_files` set — its own `manifest.json` and its README/guide — census/shape-registered
   but EXCLUDED from the artifact bijection; the manifest never hashes itself. Legacy `INDEX.md`
   tables are RETIRED (deleted) in the intake slice, never carried as bijection members.
   **Finalization (r2-g6):** rows in `permanent`-retention categories carry `finalized: true`
   once their gate/lane closes; a finalized row is immutable — its recorded `{path, sha256}`
   may never change or vanish (`finalized_row_mutation` reddens) — and its back-references must
   be DIGEST-BEARING (each citing doc states the sha256, not merely the path), so mutating the
   artifact, the manifest row, or the citing consumer ALONE reddens structurally. A fully
   coordinated rewrite of all three in one commit sits outside the structural trust model —
   caught by exact-patch review and git history, and declared so honestly. Categories at
   ratification: `design_reviews` (retire-when-slice-done), `admissions` (permanent),
   `worker_reviews` (retire-when-slice-done), `archive` (permanent), and RESERVED
   `role_assignments` `{schema RoleAssignment/v1, append-only then finalized at lane close,
   retention permanent, manifest-bound}` so W7 lands into a reserved home with an agreed schema
   instead of forking the taxonomy (r1-f6).
4. **Recursive shape grammar — executable, exact-one classification (r1-f2; r2 settled).** Prose
   `intended_shape` is not law. Every governed directory gets a `[[shape]]` section:
   `{root, universe_source, allowed node kinds, semantic groups (closed name lists/globs),
   exclusions (each naming the child contract that governs it), child_contracts}`.
   **Universe source is the candidate INDEX (r2):** the same `git ls-files --stage` universe as
   §law-1, prefix-filtered per root — never a disk walk, so the guard is deterministic in a
   clean clone and blind to ignored working files by construction.
   **Evaluation is exclusion-first, then closed partition (r2):** exclusions carve out
   child-contract territory FIRST; the semantic groups must then partition the remainder
   EXACTLY-ONE — no rule ordering, no first-match-wins; unmatched reddens (`unclassified_path`),
   multi-matched reddens (`ambiguous_home`); an unknown extension or node kind under a governed
   root reddens. Generated families carry pair/arity laws (screenshot ↔ `.provenance.json`
   sidecar; producer-driven allowed-name sets), so a receipt without provenance and an orphan
   provenance both redden. `@expectedFailure` is FORBIDDEN in org guards.
   **Debt is a SELF-CONTAINED in-guard shrink ledger (r2-g1 — REPLACES the r1 ratchet
   coupling, which was structurally impossible: the correction baseline carries no root-shape
   failure identities for `docs/ skills/ templates/ assets/ .github/`, so a fresh failure would
   be forbidden baseline growth, suppression would violate the expected-failure ban, and a
   green focused guard would leave no live identity for a debt row to map to).** An interior
   that cannot be reorganized this slice is frozen as an `org_shape_accepted_debt` row:
   `{finding_id, root, baseline_members (exact path list), baseline_digest = sha256 of the
   canonical JSON of the sorted member list, reason, expires_utc}`. The org guard itself
   enforces the ledger: observed members must be a SUBSET of the row's baseline (monotonic
   shrink — any addition reddens `debt_growth`); past-expiry reddens; a recomputed-digest
   mismatch reddens (tampered baseline); a row whose members have all shrunk away reddens as
   stale debt (the row is deleted in that slice). The correction failure-ratchet is UNTOUCHED —
   no new baseline identities, no `@expectedFailure`, and the focused org guard is green with
   debt rows active. This is the operator-ratified executable debt mechanism compatible with
   the existing ratchet (r2-g1, second arm).
5. **`no_loose_doc_without_intake`** — a new loose `docs/plans/*.md` beyond the `doc_authority`
   authority set needs a lifecycle row (already enforced by `test_doc_authority`); this law adds
   the `dev/` analog (a loose durable doc needs a registered home and a manifest row).
6. **`artifact_family_dirs_requiring_readme: ["skills", "templates", "dev"]`** +
   `root_artifact_guides` — each artifact-family dir carries a README/guide (sibling pattern);
   the READMEs themselves are census/shape-registered, never loose.

## The intake (replaces "the reorg" — migration honesty, r1-f4)

- **Admission-time INTAKE MANIFEST** (`dev/reports/admissions/w3c-org-intake.json`,
  schema-typed): at a FIXED cutoff timestamp, enumerate EVERY durable-evidence source then
  present in scratchpad — `{source_path, source_sha256, destination, classification:
  durable-evidence|perishable|stray, disposition}`. The roster is COMPUTED at admission, not
  fixed in this design: the r0 list (13 transcripts + 2 admissions) was already stale — ratchet,
  slice-patch, W6, W7, and this design's own r1 evidence postdate it, and more accrues until
  cutoff.
- **Honest mechanics:** tracked sources move by `git mv` (history preserved). UNTRACKED/ignored
  sources — which is ALL current scratchpad evidence — are content-addressed intake COPIES:
  `git add` of new files whose manifest rows record the source digests. The r0 claim "every
  relocation is git-mv-tracked" is corrected to exactly that split.
- **Producer cutover:** from this slice forward, gate transcripts and admission envelopes are
  written DIRECTLY to `dev/reports/<category>/` at creation time; scratchpad holds only
  regenerable working files. A post-cutover durable artifact appearing in scratchpad is a
  preflight finding, not a contract-test failure (§law-2 determinism split).
- **Stray disposition:** `dev/reports/design_reviews/AUTHORIZED-INTENT-MATH-PROOF-1/` (cross-repo
  stray) gets an explicit intake row (`classification: stray`, disposition remove-or-adopt with
  owner sign-off); §law-3 manifest bijection enforces whichever outcome is recorded.
- **Executable landing chain — ONE exact sequence (r2-g3 settles the two-first-patches
  contradiction; §homing's slice list is aligned to this chain, which is authoritative):**
  - **L1 — org-law patch:** contract sections + the re-authored guard + the registered category
    homes landed EMPTY (`dev/reports/<category>/manifest.json` with zero artifact rows, plus
    each category's README control file) + the root-anchored `.gitignore` roster. NO intake
    rows, NO evidence copies. Green on its own tree and in a clean clone by construction (the
    guard never blocks on ignored scratch content).
  - **Producer cutover EVENT = the L1 merge commit (r2-g3 — a precise event, not "this slice
    forward"):** every gate transcript and admission envelope produced AFTER L1 lands is
    written DIRECTLY to `dev/reports/<category>/` — the destinations exist because L1 created
    them. Pre-cutover evidence stays untouched in scratchpad until L2.
  - **L2 — intake patch:** fixed cutoff = the L2 admission timestamp; the intake roster is
    COMPUTED over the ENTIRE scratch tree at that cutoff (named evidence lists anywhere in this
    design are illustrative — the computed rule OVERRIDES them, r2-g5); content-addressed
    copies + manifest rows + `dev/reports/admissions/w3c-org-intake.json` + the stray
    disposition row land together.
  - **L3 — slice-0 regeneration:** the slice-0 final patch is REGENERATED/REBASED atop L1+L2
    with its gate log, `ACTIVE.md`, and `HANDOFF.md` pointers ALREADY targeting the governed
    `dev/reports/` paths — no post-land repoint step (this also resolves the r0 instruction to
    edit `w3c-0-design-closure.md`, a file absent from any org lane's tree); exact-patch review
    runs on the regenerated result.
- **Ratchet honesty:** the pre-existing structural-layout REDs on the dirty tree stay owned by
  the correction failure-ratchet with UNCHANGED `(test id, fingerprint)` identities — no
  `@expectedFailure` conversion, no `org_shape_accepted_debt` growth to absorb them.

## RED (conductor authors; build lane makes green — r1-f8 minimum set)

`tests/contracts/test_org_rootwide.py` — conductor-authored FRESH and observed failing pre-build.
The killed-lane file of the same name was authored alongside the implementation it verifies and
is therefore DISQUALIFIED as this RED (author-never-approves applies to REDs too; it may inform,
never substitute). Empirical git behavior is settled by probes in HERMETIC temp repositories from
the first round (AGENTS.md convergence law). Minimum pre-build families:
1. **Census:** tracked entry, candidate-untracked, ignored influential control, symlink,
   submodule, linked worktree, duplicate census row, case-fold + NFC/NFD collision, and the
   final-patch-index universe (probe reads the index, not the working tree).
2. **Recursive classification:** unknown extension/kind, dual-match, unmatched nested file,
   receipt-without-provenance, orphan provenance, attempted growth of an owed legacy baseline.
3. **Evidence homes:** unknown category, unlisted artifact, unknown schema, changed evidence
   bytes (digest recompute), stale/missing digest, missing external back-reference, invalid
   `keep-newest-N`, completed-slice retention breach, archive placement, `RoleAssignment/v1`
   schema row.
4. **Intake honesty:** intake-roster bijection + hash verification, producer-cutover breach,
   unresolved-source rejection, unchanged ratchet identities for the pre-existing structural
   failures.
5. **Docs currency:** one RED per real stale claim (each failing assertion names a live defect),
   pointer/block-ID parity, executable bootstrap argv, HANDOFF/CLAUDE coverage, and the
   cosmetic-satisfaction mutants (§docs-currency).
Named mutant kills (each with a recorded witness; these are the r1 survivors, now killed):
junk-padding a category → manifest schema reddens; editing evidence bytes → digest recompute
reddens; retaining an expired review → retention reddens; standing up ignored
`.claude/settings.json` behavior → universe-B enumeration flags it; a concept keyword in a
comment/glossary → block projection reddens; `--expect` near an unrelated command → argv
execution reddens; a scratchpad pointer left in ACTIVE/HANDOFF/gate log → back-reference check
reddens; a case-colliding home → collision check reddens.

### RED-convergence — the r2 findings as executable REDs (convergence law invoked 2026-07-16)

Per the AGENTS.md convergence cap, every remaining r2 finding (and each re-opened r1 aspect not
absorbed by a numbered finding) is bound below as an EXACT executable RED. Each was verified
against the live tree on 2026-07-16 and fails TODAY for the stated reason; the build makes them
green; the next review round reviews code + test output on the exact final patch. CR-1..CR-9 and
CR-14 live in the conductor-authored `tests/contracts/test_org_rootwide.py`; CR-10..CR-13 are
upgrades landing in the existing `tests/contracts/test_process_docs_currency.py`.

- **CR-1 (r2-g1)** `test_debt_rows_are_self_contained_shrink_ledgers` — load
  `contracts/repo_layout.json`; assert `org_shape_accepted_debt` exists as a list whose every
  row has EXACTLY the keys `{finding_id, root, baseline_members, baseline_digest, reason,
  expires_utc}`; recompute `sha256(canonical JSON of sorted baseline_members)` and assert it
  equals `baseline_digest`; assert no row carries ratchet-coupling keys (`test_id`,
  `fingerprint` forbidden). FAILS TODAY: the contract has no `org_shape_accepted_debt` key —
  the ratchet-compatible debt mechanism is not yet law.
- **CR-2 (r2-g2)** `test_contract_metadata_declares_ratified_root_shape_owner` — load
  `contracts/repo_layout.json`; assert `authority_status == "ratified_root_shape_owner"`,
  `cannot_mark_done` absent or false, `schema_version >= 2`, and `"eventual decider" not in
  purpose`. FAILS TODAY: `authority_status` is `"candidate_only"`, `cannot_mark_done` is true,
  and the purpose text still defers to an external decider.
- **CR-3 (r2-g2)** `test_module_and_test_rosters_are_checked_projections` — assert the contract
  carries a `projections` section registering `scripts/organization/layout_contract.py:
  MODULE_HOMES` and `scripts/organization/tests_layout_contract.py:TEST_GROUPS` with owner
  `contracts/repo_layout.json`; import both rosters and assert one-to-one parity with the
  contract rows. FAILS TODAY: no `projections` section exists; the two scripts are independent
  roster owners.
- **CR-4 (r2-g3)** `test_registered_category_homes_exist_tracked_with_manifests` — for every
  category in `[dev_reports].categories`: `dev/reports/<category>/manifest.json` exists, parses
  against the typed schema, and its path appears in `git ls-files`. FAILS TODAY: the contract
  has no `dev_reports` section and nothing under `dev/` is tracked.
- **CR-5 (r2-g3)** `test_tracked_routing_docs_cite_no_scratch_evidence` — assert the literal
  `scratchpad/work` appears in neither `docs/plans/ACTIVE.md` nor
  `docs/plans/handoff/HANDOFF.md`. FAILS TODAY: `ACTIVE.md` line 120 routes review transcripts
  to `scratchpad/work/codex-*.md`. (The slice-0 gate log's pointers ride the L3 regenerated
  patch and are asserted there.)
- **CR-6 (r2-g6)** `test_manifest_schema_excludes_control_files_and_seals_permanent_rows` —
  assert the `[dev_reports]` schema declares a closed `control_files` set that includes
  `manifest.json` (excluded from the artifact bijection), and that the `permanent` retention
  class requires `finalized: true` rows with digest-bearing back-references. FAILS TODAY: no
  `dev_reports` schema exists.
- **CR-7 (r1-f1 remainder)** `test_live_control_enumeration_is_closed_with_tracked_authority` —
  assert the contract carries the closed `live_controls` enumeration; its `.claude/` row
  declares ignored content non-authoritative with authority = tracked
  `contracts/role_registry.*` + tracked mirror-parity check; no row carries an amendment fork.
  FAILS TODAY: no `live_controls` section exists.
- **CR-8 (r1-f2 remainder)** `test_shape_sections_declare_index_universe_and_exclusion_precedence`
  — assert every `[[shape]]` row carries `universe_source == "index"` and
  `evaluation == "exclusions-then-closed-partition"`, and that each governed root (`scripts`,
  `tests`, `contracts`, `docs`, `site`, `assets/receipts`, `dev`) has a row. FAILS TODAY: the
  contract has no `[[shape]]` rows at all.
- **CR-9 (r2-g5)** `test_dev_reports_category_set_is_the_closed_five` — assert the category set
  equals exactly `{design_reviews, admissions, worker_reviews, archive, role_assignments}` and
  that `proposals` is NOT present. FAILS TODAY: no `dev_reports` section exists (and the RED
  permanently blocks the killed lane's `proposals` category from re-entering).
- **CR-10 (r2-g4)** `test_agents_md_carries_stable_block_ids` — assert `AGENTS.md` contains a
  `<!-- SOP-BLOCK: <id> -->` marker for each canonical AGENTS-owned section (13-step ritual,
  three verdicts, review-convergence law, MF1 receipts, org shape law, failure-ratchet
  exception, Mode C lane, BACKUP-BEFORE-TRANSFORM). FAILS TODAY: `AGENTS.md` contains zero
  block markers.
- **CR-11 (r2-g4)** `test_agents_routes_evidence_to_governed_homes` — assert `AGENTS.md`
  contains no `scratchpad/work` literal and no scratch review-queue routing, and that its
  step-13 RECORD block and its `review transcripts:` pointer name `dev/reports/`. FAILS TODAY:
  step 13 persists transcripts "to the scratch review-queue" and line 120 cites
  `scratchpad/work/codex-*.md`.
- **CR-12 (r2-g4)** `test_handoff_carries_sop_pointer_ids` — assert
  `docs/plans/handoff/HANDOFF.md` contains the required `SOP-POINTER: <block-id>` lines and
  that every cited ID resolves to a `SOP-BLOCK` marker in `AGENTS.md`. FAILS TODAY: HANDOFF.md
  contains zero `SOP-POINTER` lines.
- **CR-13 (r2-g4)** `test_policy_concept_rows_name_projection_owners` — assert
  `contracts/process_docs_currency_policy.toml` exists and every concept row carries
  `projection_owner`; DEMO A/B and Mode-ladder rows name `docs/plans/ACTIVE.md`/design docs;
  role rows name `contracts/role_registry.*` with an explicit `interim_source` until W7 lands.
  FAILS TODAY: the policy file does not exist.
- **CR-14 (r2-g5)** `test_artifact_family_readmes_exist_and_teach_current_law` — assert
  `dev/README.md`, `skills/README.md`, and `templates/README.md` exist, are tracked, and
  contain neither `proposals` nor `candidate_only` nor a singleton-enforcement claim. FAILS
  TODAY: none of the three files exists on the live tree (and the content clause permanently
  blocks the killed lane's stale README teaching, r2-g5).

Non-RED folds: r2-g7 is a prose-precision fix (§docs-currency seed paragraph; the admission
record preserves the exact observed reason) and the r2-g5 base-staleness arm is process law
bound in the integration packet (re-author atop the current base; the worktree is read-only
reference) — neither is probeable as a repo test.

## Homing + slices

- Homes registered same slice: `tests/contracts/test_org_rootwide.py` (TEST_GROUPS +
  DESIGN_CONTRACT_GROUPS `organization`), the new `repo_layout.json` sections, `dev/reports/`
  category dirs + their `manifest.json` files, the intake manifest, the repo-local `CLAUDE.md`
  census row (owed until the docs-currency slice lands it), the design-doc lifecycle row
  (already present in `doc_authority_policy.toml`).
- Slice sequence — ALIGNED to the §intake chain, which is authoritative (r2-g3): (0) this
  design → Codex DESIGN gate (closed at r2 by the convergence law). (L1) build lane extends
  `repo_layout.json` (incl. the authority-metadata transition, §matrix) + authors the guard
  green against the CURRENT tree with the frozen-debt ledger + lands the EMPTY category homes
  and the anchored `.gitignore` — no evidence moved; Codex CODE + ADVERSARIAL. (L2) build lane
  executes the intake (computed roster at cutoff, content-addressed copies + manifests); Codex
  CODE + ADVERSARIAL. (L3) slice-0 patch regeneration + exact-patch review. (L4) docs-currency
  slice, SEQUENCED AFTER the W7 role-registry lands (r2-g4). Universe-B / scratch-hygiene
  preflight ships as a script (`scripts/organization/`), not as clone-blocking contract tests.
  This is a build lane (Opus codes → Codex reviews); mechanical contract data + file intake,
  not hard-tier.

## Interaction with the slice-0 landing

Slice-0's landing allowed-paths DROP `scratchpad/work`; the durable admission records land via
this org slice's `dev/reports/admissions/` home instead. Landing order is the executable chain
of §intake: L1 (org law + empty homes) then L2 (intake) land first against clean HEAD; the
slice-0 correction patch is then regenerated atop them (L3) with its gate log, `ACTIVE.md`, and
`HANDOFF.md` already pointing at the governed proof homes (path + sha256); exact-patch review
runs on that regenerated patch. The correction ratchet's pre-existing structural failures pass
through unchanged (§intake, ratchet honesty).

## Docs-currency guard (operator-directed 2026-07-15; r1-f5 folded — the automation that keeps the system usable)

The process docs must stay fresh or no AI can drive the system. Mirror the kernel's docs-currency
law (`doc_authority_policy.toml [model_facing_register]` + scout `live_docs`/`stale_reference_tokens`
+ `sop_surface_parity_policy.toml`). New `contracts/process_docs_currency_policy.toml`
(`contract_id: ProcessDocsCurrencyPolicy`, `[mode] audit→block`, `[[accepted_debt]]` orphan-fails-
closed):
- **Registered doc set (closed, explicit rows):** `skills/design-language-tdd/SKILL.md`, every
  `skills/design-language-tdd/references/*.md`, `AGENTS.md`, `docs/plans/handoff/HANDOFF.md`,
  and the repo-local `CLAUDE.md` — HANDOFF and CLAUDE are IN scope (the r0 draft omitted
  HANDOFF); each row composes with the ownership matrix (placement via census, lifecycle via
  doc_authority, projections here).
- **Stale claims are scoped CLAIM IDs, not raw token bans:** each row
  `{claim_id, doc_scope, match_rule, positive_fixture, negated_context_fixture}` — so
  "kernel decides" inside a correct negation PASSES, and "centered column" scoped to a single
  page PASSES while the universal-page-layout claim reddens. The r0 raw-ban list ("two-arg
  bootstrap form", "deferred R4 aspect" / "headless proof is deferred", "centered column",
  "self-demonstrating design system", "kernel decides") is retired in favor of claim rows
  covering the same defects with both fixtures.
- **Concept presence is BLOCK PROJECTION, not substrings:** canonical AGENTS.md sections carry
  stable block IDs; pointer-only consumers (SKILL.md, `CLAUDE.md`, HANDOFF.md) name exact IDs
  (`SOP-POINTER: <block-id>`); the `require_block_ids` completeness floor reddens on a dropped
  block, so a keyword appended in a glossary or comment satisfies nothing. Role facts
  (Opus-builds/Codex-reviews, the three verdicts) are PROJECTED from `contracts/role_registry.*`
  — asserted against the registry data, never against a phrase like "build lane". The projected
  concept set covers the 13-step ritual, the three verdicts, the review convergence law, MF1
  Chrome-headless receipts, the org recursive shape law, the failure-ratchet exception, the
  Mode C reference-capture lane, DEMO A/B, the Mode A/B/C/D ladder, and BACKUP-BEFORE-TRANSFORM.
  **Every concept row names its `projection_owner` (r2-g4):** DEMO A/B and the Mode A/B/C/D
  ladder project from `docs/plans/ACTIVE.md` / the design-authority docs — NEVER from AGENTS.md
  blocks (they are plan/design authority, not SOP prose); role facts project from the registry
  (interim per §matrix); SOP-process concepts project from AGENTS.md block IDs.
- **Executable-example binding:** the bootstrap command the skill prints is EXTRACTED as argv
  (quoting-robust: single-quoted, unquoted, and multiline forms all captured — never a
  200-char-window regex) and EXECUTED against a fixture; it must carry `--expect` + scope flags
  and reach the admitting path. Receipt commands are checked against the real
  `scripts/quality/headless_receipts.py` CLI surface; every path a process doc cites must exist.
- **Seed RED status (keeps the 4-of-5 intent coherent):**
  `tests/contracts/test_process_docs_currency.py` currently fails 4 of 5, and each failure names
  a REAL present defect — two stale product claims, two non-functional bootstrap examples,
  six missing live-process concepts, and a missing AGENTS.md route (r2-g7 precision: the ACTIVE
  routing half is PRESENT and passing — the failing half is the AGENTS route only; the
  admission record preserves this exact observed reason per assertion). That observation STANDS
  as the admission witness. Its current weak assertion forms (substring concepts, the 200-char
  `--expect` window) are admission-seed-only: the build upgrades the SAME file to the
  policy-driven claim-ID / block-projection / argv-execution forms above, and each upgraded
  assertion is re-observed failing on the stale skill for the same right reason BEFORE the skill
  refresh lands. Named cosmetic-satisfaction mutants (keyword stuffing, swapped actors, an
  omitted SOP step, a dead pointer, a single-quoted bad command, an unrelated nearby `--expect`)
  are required kills in the RED set (§RED family 5).
Build (Opus lane; slice L4, SEQUENCED AFTER the W7 role-registry lands — r2-g4 — so registry
projections never bind to a nonexistent file; until W7 lands, role rows carry
`interim_source = "AGENTS.md SOP prose"` and assert against the prose block IDs): refresh
SKILL.md + references to teach the 13-step process (retire the stale claims via claim rows),
add the policy TOML + the upgraded guard, add the thin repo-local `CLAUDE.md` pointer (census
row per §law-1), **and the canonical-doc edits the r2 review proved missing from the change
set (r2-g4): AGENTS.md gains the stable block IDs, and its step-13/RECORD routing plus its
`review transcripts:` pointer are retargeted from the scratch review-queue to the governed
`dev/reports/` homes; HANDOFF.md gains its `SOP-POINTER:` ID lines.** Register all homes.
Forward-test: the skill must reject a synthetic generic reskin (handoff:1201).

## Integration deltas (killed-lane worktree `.claude/worktrees/agent-a46ef213d05b316c1` vs THIS design — the design decides; the integration lane applies ALL of these)

**Safety law first (r2-g5):** the killed worktree is READ-ONLY REFERENCE. It holds 27 staged
paths based at `6389c606` — three commits behind the live branch (`64b09040`) — and the
intervening commits modified `repo_layout.json`, `layout_contract.py`, and
`tests_layout_contract.py`. Its staged blobs are NEVER applied (applying them can regress
landed work); every contract/test/doc artifact is RE-AUTHORED atop the current base.

1. `tests/contracts/test_org_rootwide.py` (332 lines): NOT the RED — discard as authority; the
   conductor re-authors per §RED (the lane file was written alongside its own GREEN, carries
   `@expectedFailure` interiors, and checks JSON-node existence where classification is required).
2. `repo_layout.json [top_level]` rows: add the required `status` field (lane rows omit it), the
   owed-row `{debt_ref, expires_utc}` grammar, mode-derived `kind` vocab, and the `CLAUDE.md`
   owed row; the loader must reject duplicate rows instead of collapsing them.
3. `[dev_reports]`: replace the prose `INDEX.md` tables (which no guard reads) with typed
   `manifest.json` rows per §law-3 (recomputed digests, `referenced_by`, `produced_utc`); retype
   retention so `keep-newest-N` requires a positive integer (the lane's prefix check accepts
   non-numeric text); add the `archive` and reserved `role_assignments` categories; the lane's
   `proposals` category is REMOVED — it is not in the closed set and does not survive
   integration (r2-g5).
4. `directory_shapes` prose `intended_shape` rows: replace with the executable `[[shape]]`
   exact-one grammar + frozen legacy-debt baselines (§law-4); delete the five `@expectedFailure`
   escapes.
5. `.gitignore`: root-anchor the clutter lines (`/scratchpad/`, not `scratchpad/`) and carry the
   full declared roster (§law-2); ignore behavior is proven by hermetic `git check-ignore`
   probes, not string parsing.
6. Evidence intake: the lane's 14 design-review files + 3 admission files become intake-manifest
   rows with source digests at the fixed cutoff; ADD the post-r0 evidence the lane omits
   (ratchet, slice-patch, W6, W7, this design's r1+r2 transcripts) and the
   `AUTHORIZED-INTENT-MATH-PROOF-1` disposition row. All names here are ILLUSTRATIVE — the
   §intake computed-cutoff rule OVERRIDES them: the roster is the ENTIRE scratch tree
   enumerated at the L2 cutoff (r2-g5).
7. Pointer repoints the lane skipped: `ACTIVE.md` and the slice-0 gate log still cite
   `scratchpad/work/codex-*.md` — resolved via the §intake landing chain (the slice-0 patch is
   regenerated with governed pointers), never by editing files absent from the org lane's tree.
8. `dev/README.md`, `skills/README.md`, `templates/README.md`: keep as REGISTERED HOMES (law
   §6) but REWRITE the content — the lane copies teach retired law (r2-g5): `dev/README.md`
   drops the singleton-enforcement rule and the `proposals` category; `skills/README.md` +
   `templates/README.md` drop the indefinite-OWED / `candidate_only` teaching (superseded by
   the ratified-owner metadata, §matrix); each registered in census/shape rows.
9. `scripts/organization/tests_layout_contract.py` (+2 lines): keep only the test-home
   registration; re-verify it against the re-authored guard.
10. The lane's bundled 108-line copy of this design doc is superseded by this revision (the
    tracked doc is authoritative).

## Codex DESIGN gate

Gate history: r1 `DESIGN-VERDICT: REVISE` (8 findings — 2 critical, 6 high), findings folded
2026-07-16 into this rev. Fold map: f1→§law-1 (two-universe census, git-mode kinds, collision
rejection, `.claude`/hooks disposition) · f2→§law-4 (exact-one recursive grammar, pair laws,
no-expectedFailure, expiring shrink debt) · f3→§law-3 (typed manifests, digest recompute,
back-references, typed retention, in-taxonomy archive, count rules dropped) · f4→§intake
(admission-time manifest, copy-vs-mv honesty, producer cutover, executable landing chain, ratchet
honesty) · f5→§docs-currency (closed register incl. HANDOFF/CLAUDE, claim IDs over token bans,
block projection, argv execution, seed-RED upgrade path) · f6→§matrix + §law-3 (ownership matrix,
deprecated duplicate rosters, reserved `role_assignments`) · f7→§law-2 (root-anchored typed
clutter, hermetic ignore probes, preflight/contract determinism split, filename heuristics
retired) · f8→§RED (five probe families, named mutant kills, killed-lane test disqualified as the
RED). The r1 transcript is intake-scoped per §intake (durable evidence, destination
`dev/reports/design_reviews/`).

r2 (xhigh, 2026-07-16): `DESIGN-VERDICT: REVISE` — 7 findings (4 blocking, 2 major, 1 minor);
r1 disposition: f3/f7/f8 resolved, f1/f2/f4/f5/f6 aspects re-opened. **Convergence law INVOKED
2026-07-16** (AGENTS.md: second REVISE round on one artifact): all remaining findings are folded
into this rev AND converted to the executable REDs of §RED-convergence; the build proceeds
under those REDs, and the reviewer next sees code + test output on the exact final patch — no
third prose round. r2 fold map: g1→§law-4 (self-contained shrink-debt ledger, ratchet
untouched; CR-1) · g2→§matrix (ratified root-shape owner, roster projections, schema-version
transition; CR-2/CR-3) · g3→§intake+§homing (one L1→L2→L3 chain, cutover = the L1 merge
commit; CR-4/CR-5) · g4→§matrix+§docs-currency (W7-first sequencing, `interim_source` role
rows, AGENTS/HANDOFF edits added to the build set, per-concept projection owners;
CR-10..CR-13) · g5→§deltas+§intake (read-only worktree safety law, re-author atop current
base, `proposals` removed, computed cutoff overrides named examples, README rewrites;
CR-9/CR-14) · g6→§law-3 (control-file exclusions, finalized-row immutability, digest-bearing
back-references; CR-6) · g7→§docs-currency (seed-precision prose fix; non-RED) · r1-f1
remainder→§law-1 (universe-B `.claude/` row settled, amendment fork closed; CR-7) · r1-f2
remainder→§law-4 (index universe, exclusion-first precedence; CR-8). The r2 transcript is
intake-scoped per §intake (durable evidence, destination `dev/reports/design_reviews/`).
Build authorization: the integration packet
(`scratchpad/work/packet-org-integration-2026-07-16.md`, regenerable working file — its content
is restated in the L1 bound packet) binds the build lane to this rev + CR-1..CR-14.
