# W7 — Role/Seat Integrity: registry-as-data, fail-closed gate for EVERY lane, MODEL-INTEGRITY HALT

> Scratch design record (class: design-record, status: live in `contracts/doc_authority_policy.toml`).
> Author: Fable (claude-fable-5) conductor seat, 2026-07-16. Rev 3 — r1 AND r2 findings are folded
> into this text; disposition ledgers in §9/§9b. Builder: Opus build lane under the bound packet
> `scratchpad/work/packet-w7-role-integrity-2026-07-16.md`. Reviewer: Codex — the next review is
> CODE + ADVERSARIAL on the built patch (never a third prose round).
> Gate history: r1 = revision requested (REVISE, xhigh, 17 findings; transcript
> `scratchpad/work/codex-w7-design-gate-r1-2026-07-16.md`, durable copy to land at
> `dev/reports/reviews/w7-design-gate-r1-2026-07-16.md` per §6); r1 findings folded 2026-07-16
> (rev 2, 17/17). r2 = revision requested (REVISE, xhigh, 11 findings; the re-audit confirmed
> r1 #2 structurally resolved and re-opened the rest as depth gaps inside the 11; transcript
> `scratchpad/work/codex-w7-design-gate-r2-2026-07-16.md`, durable copy to land at
> `dev/reports/reviews/w7-design-gate-r2-2026-07-16.md`). CONVERGENCE INVOKED 2026-07-16 per the
> AGENTS.md review-convergence law: after two REVISE rounds on one artifact, remaining findings
> convert to executable REDs and the work proceeds to build — the r2 findings are folded below
> (§9b, 11/11) and every probeable arm is an exact executable RED (§5 V-series). Build proceeds
> under those REDs.

## §0 Operator law (Mode D — verbatim, 2026-07-16 ~03:25Z)

> "the first thing it's gonna build is a system that allows this shit to not allow Opus …
> being an orchestrator or a coder when it's not … in that goddamn lane in the same way
> semantic TDD does. But not just for the … orchestrator, but for every goddamn lane — coder,
> orchestrator, reviewer, ANYTHING."

> (2026-07-16 ~02:29Z) "You shouldn't be having to hard code and change an agent's MD who is
> the conductor … It should state all of the different lanes … I should be able to just tell
> you whatever agent I want in the different slots … we are not just raw-dogging it and
> changing around text values in the agents MD."

Reference pattern (Mode A mirror): semantic-tdd `state/role_registry.toml`,
`dev/reports/role_assignments/*.json`, `crates/semproof-core/src/role_gate.rs`.
Prior art to harvest (NOT authority): killed lane-E worktree `agent-a3fb94af1ff864da0`
(`contracts/role_registry.toml`, `contracts/slot_assignments/`, `tests/contracts/
test_role_registry.py` — Opus-built, conductor-only, unreviewed).

## §1 Threat model (T1–T5 PROVEN in the 2026-07-15/16 session JSONL `2c5e4cf3…`; T6–T8 added
## by the r1 design gate)

- **T1 — silent conductor seat swap.** Main loop flipped `claude-fable-5` → `claude-opus-4-8`
  4 times (23:43Z, 00:00Z ×328 msgs, 03:19Z, 03:22Z ×84 msgs) — each time AFTER the operator
  had explicitly set `/model` to Fable (23:50, 02:50, 03:20 local-command records). The flips
  cluster at context continuations. No structural control existed; prose law did nothing.
- **T2 — wrong-seat authority actions.** During T1 windows the wrong-seated conductor edited
  doc-law files (AGENTS.md, ACTIVE.md, the slice-0 design), dispatched Codex gates, dispatched
  14 build lanes, and asked to commit (operator rejected). Only operator vigilance + zero-commit
  luck contained it.
- **T3 — lane seat mismatch.** A "Fable audit" lane self-reported it was actually Opus
  (03:23Z). Dispatch-time intent does not bind runtime model.
- **T4 — reviewer spoofing / author-approves.** Nothing machine-checks that a persisted review
  transcript came from the seated reviewer at the required effort, or that reviewer ≠ author.
- **T5 — phantom-registry prose.** AGENTS.md step 7 and HANDOFF.md already REFERENCE
  `contracts/role_registry.*` — which does not exist. Prose drifted ahead of reality; this build
  makes it real and adds a currency RED so it can never dangle again.
- **T6 — enforcement-surface self-reference (r1).** The registry, the gate code, and the hook
  wiring are themselves files the governed actors could rewrite; a check that reads mutable
  working-tree data can be repointed by the very actor it judges. Closed in §2.3/§4.3.
- **T7 — record and transcript substitution (r1).** Assignment records, lane transcripts, and
  review files were self-attestations: a clean-but-unrelated transcript, a backfilled verdict,
  or a hand-written review file could stand in for the real artifact. Closed in §2.4/§3.4/§3.5.
- **T8 — vocabulary gaps (r1).** Authority actions the SOP actually performs (tagging, ref
  surgery, worktree administration, remote publication, staging, integration) had no verb and
  no mapping, so they were ungoverned by construction. Closed in §2.1/§4.2.

## §2 Data model — roles, actors, seats (ALL data; no prose authority)

### §2.1 The registry `contracts/role_registry.toml` (seed content — the builder types this
### VERBATIM; choosing it is design work and already done here)

```toml
contract_id    = "RoleRegistry"
schema_version = 1
purpose = "Roles and seats are DATA. No seat = no action; unknown anything = refuse."

[vocabulary]      # CLOSED verb list, derived from the 13 SOP steps + ACTIVE's tag law (T8).
verbs = [
  "read", "run_demo", "audit_report",
  "design", "author_red", "author_admission", "register_home",
  "dispatch_lane", "gate_dispatch",
  "implement", "verify", "generate_receipts",
  "stage", "integrate", "commit", "tag", "ref_update", "worktree_admin",
  "push", "remote_publish",
  "persist_review", "record_summary", "review_verdict",
  "doc_law_edit", "enforcement_edit", "operator_reslot",
]

[actors.fable]
kind     = "claude-model"
model_id = "claude-fable-5"          # EXACT runtime id; prefix matching FORBIDDEN

[actors.opus]
kind     = "claude-model"
model_id = "claude-opus-4-8"

[actors.codex]        # IDENTITY only — run-level review effort lives in assignment data (§2.4)
kind        = "codex-cli"
binary      = "codex"
model_id    = "gpt-5.6-sol"                  # cross-checked against the structured stream (§3.5)
argv_base   = ["exec", "--sandbox", "read-only", "--model", "gpt-5.6-sol", "--json",
               "--strict-config", "--ignore-user-config"]
    # r2 f6: the pin is EXPLICIT — structured argv, shell=False, model pinned on the command
    # line, structured JSONL output, user-config drift excluded. Closure law: argv_base MUST
    # contain ["--model", model_id] (consistency with the field above; asserted by R8/V6).
effort_argv = ["-c", "model_reasoning_effort=<effort>"]    # <effort> filled from the assignment

[roles.conductor]
authority = ["read", "run_demo", "audit_report", "design", "author_red", "author_admission",
             "register_home", "dispatch_lane", "gate_dispatch", "verify", "generate_receipts",
             "stage", "integrate", "commit", "tag", "ref_update", "worktree_admin", "push",
             "remote_publish", "persist_review", "record_summary", "doc_law_edit",
             "enforcement_edit", "operator_reslot"]
forbidden = ["implement", "review_verdict"]

[roles.builder]
authority = ["read", "implement", "verify", "generate_receipts"]
forbidden = ["run_demo", "audit_report", "design", "author_red", "author_admission",
             "register_home", "dispatch_lane", "gate_dispatch", "stage", "integrate", "commit",
             "tag", "ref_update", "worktree_admin", "push", "remote_publish", "persist_review",
             "record_summary", "review_verdict", "doc_law_edit", "enforcement_edit",
             "operator_reslot"]

[roles.reviewer]
authority = ["read", "review_verdict"]
forbidden = ["run_demo", "audit_report", "design", "author_red", "author_admission",
             "register_home", "dispatch_lane", "gate_dispatch", "implement", "verify",
             "generate_receipts", "stage", "integrate", "commit", "tag", "ref_update",
             "worktree_admin", "push", "remote_publish", "persist_review", "record_summary",
             "doc_law_edit", "enforcement_edit", "operator_reslot"]

[roles.auditor]
authority = ["read", "audit_report"]
forbidden = ["run_demo", "design", "author_red", "author_admission", "register_home",
             "dispatch_lane", "gate_dispatch", "implement", "verify", "generate_receipts",
             "stage", "integrate", "commit", "tag", "ref_update", "worktree_admin", "push",
             "remote_publish", "persist_review", "record_summary", "review_verdict",
             "doc_law_edit", "enforcement_edit", "operator_reslot"]

[roles.demo_runner]
authority = ["read", "run_demo"]
forbidden = ["audit_report", "design", "author_red", "author_admission", "register_home",
             "dispatch_lane", "gate_dispatch", "implement", "verify", "generate_receipts",
             "stage", "integrate", "commit", "tag", "ref_update", "worktree_admin", "push",
             "remote_publish", "persist_review", "record_summary", "review_verdict",
             "doc_law_edit", "enforcement_edit", "operator_reslot"]

[seats]             # closed key set == the role set; SINGLETON string values (no arrays,
conductor   = "fable"        # no OR-authority). The ONLY block the operator edits to re-slot.
builder     = "opus"
reviewer    = "codex"
auditor     = "opus"
demo_runner = "opus"
```

### §2.2 Registry closure law (every rule is a load-time refusal, never a warning)

- Exact key sets: top level exactly `{contract_id, schema_version, purpose, vocabulary,
  actors, roles, seats}`; `roles` exactly the five above; `seats` keys == `roles` keys
  (bijection). Unknown or missing key anywhere ⇒ refuse.
- Disposition law: per role, `authority ∪ forbidden == vocabulary.verbs` AND
  `authority ∩ forbidden == ∅` — every verb carries exactly one disposition for every role.
  (Kills silent grants: a mutant that hands `commit` to the reviewer or `dispatch_lane` to the
  builder is a shape violation, not a judgment call.)
- Seats are singletons: each seat names exactly ONE declared actor. A list, an unknown actor
  name, or a missing seat ⇒ refuse.
- Principal uniqueness: no two actors may resolve to the same principal (claude actors:
  `model_id` unique; codex actors: `(binary, model_id)` unique). Author/reviewer separation
  (§2.4) compares RESOLVED principals, never actor labels.
- The r1 `designer`/`red_author` alias seats are REMOVED: "the conductor designs and authors
  REDs" is carried by the conductor role's `design` + `author_red` grants — role data, no alias
  seats, and no way to split them without a `schema_version` bump.
- `kind ∈ {claude-model, codex-cli}` closed; claude actors bind by exact `message.model`
  equality; the codex actor binds by the structured-stream identity fields (binary, model,
  sandbox, effort — §3.5).
- **Seat-binding law (r2 f1):** authority NEVER derives from a record's `actor` field alone.
  At every load, `record.actor` MUST equal `seats[record.role]` in the committed registry — a
  mismatch (e.g. `{role: "conductor", actor: "opus"}` while `seats.conductor = "fable"`) ⇒
  refuse `reason=seat_mismatch`. `dispatched_by` MUST equal the actor seated as conductor at
  dispatch time, and the dispatching session's own epoch scan (§3.1) must pass for that seat.
  The expected principal at check time is derived `role → seats[role] → actor → principal`;
  the record's `actor` is a cross-check, never a source of authority.

### §2.3 Trust root (T6): authority data is read from the COMMITTED tree, never from arguments

- The gate accepts NO registry path argument. It resolves the registry internally via
  `git -C <repo_root> cat-file blob HEAD:contracts/role_registry.toml`. A working-tree edit to
  the registry confers nothing until a commit lands — and `commit` is itself a gated verb.
- Enforcement-surface drift check: before any authority OK, the gate byte-compares working
  tree vs HEAD blobs for the closed surface set `{contracts/role_registry.toml,
  scripts/organization/role_gate.py, scripts/organization/role_gate_hook.py,
  scripts/organization/gate_runner.py, .claude/settings.json, .gitignore}`. Any drift ⇒
  `HALT reason=enforcement_drift` — except the attested-reslot flow below. (The RUNNING code is
  already HEAD's — §4.3 — so drift is inert; this check also makes it loud.)
- `operator_reslot`: a seats/actors change lands ONLY as a commit whose tree also contains a
  fresh attestation record `dev/reports/role_assignments/reslot-<utc>.json` = `{record:
  "SeatReslot", old_registry_sha256, new_registry_sha256, operator_ref (verbatim operator
  message citation), ts}`. The gate validates the transition under the PREVIOUS committed
  registry (whose conductor seat holds `operator_reslot`), and the drift exception admits
  exactly {the registry + that record} while the reslot commit is in flight. Missing or
  malformed attestation ⇒ HALT. Re-slotting is an operator-attested data change, never an edit
  that silently takes effect.

### §2.4 Assignment records `dev/reports/role_assignments/<lane_run_id>.jsonl`
### (typed committed home; one per lane activation, conductor-broker-written; r2 f9: the file
### is APPEND-ONLY JSONL — line k is a FULL record snapshot, so the history chain is
### recomputable from the file alone; the last line is the current record)

```json
{
  "record": "RoleAssignment", "schema_version": 1,
  "lane_run_id": "w7-build-r1", "execution_kind": "build_lane",
  "role": "builder", "actor": "opus",
  "dispatched_by": "fable", "dispatch_ts": "…Z", "base_sha": "…",
  "registry_sha256": "<sha256 of the COMMITTED registry blob at dispatch>",
  "dispatch_nonce": "<32 hex chars from os.urandom(16); also injected into the lane's first prompt>",
  "session_binding": {
    "session_ids": ["<harness session id>"],
    "transcript_paths": ["<canonical harness transcript path>"],
    "worktree": ".claude/worktrees/agent-… OR null",
    "parent_session_id": "<dispatching conductor session id>"
  },
  "packet": {
    "design_sha256": "…",
    "design_verdict_ref": {"path": "dev/reports/reviews/…", "sha256": "…"},
    "red_sha256": "…", "admission_sha256": "…",
    "allowed_paths": ["…"]
  },
  "review_profile": {"round": 1, "required_effort": "max", "operator_override_ref": null},
  "author_actor": "opus", "reviewer_actor": "codex",
  "standin": {"active": false, "standin_actor": null,
               "retro_review_queued": false, "retro_review_ref": null},
  "status": "dispatched",
  "completion": {"output_patch_sha256": null, "transcript_manifest_sha256": null},
  "review": {"reviewed_patch_sha256": null, "review_refs": []},
  "verification": {"verified_model_ids": [], "verified_at": null, "verdict": null},
  "events": [{"ts": "…Z", "to_status": "dispatched", "prev_sha256": null}]
}
```

Record law (each rule a load-time or transition-time refusal):

- **Home law:** records live ONLY under `dev/reports/role_assignments/` (corpus-home
  membership, mirroring the reference `role_gate.rs` corpus-home floor). A record referenced
  from any other path ⇒ refuse. `contracts/` holds LAW; per-run records are reports.
- **No self-declared expectations:** there is NO `expected_model_id` field. The expected
  principal is DERIVED at check time from `actor` → registry (committed blob). Editing a
  record cannot change what is expected of it.
- **Nonce binding (T7):** `dispatch_nonce` is minted by the broker at dispatch and injected
  verbatim into the lane's first prompt. A transcript whose FIRST user record does not contain
  the nonce can never verify — an unrelated clean transcript is structurally useless.
- **Session binding (T7):** written at dispatch from harness-returned identifiers; a resumed
  lane APPENDS its new session id/transcript before further lane work; at check time EVERY
  listed transcript must exist and pass. A `Task`/`Agent` tool_use inside a lane transcript
  with no declared child record ⇒ REJECT (§3.4).
- **Status + transition graph (r2 f2):** `∈ {prepared, dispatched, complete, reviewed,
  integrated, rejected, killed, historical_unverified}` (closed; unknown ⇒ refuse). The ONLY
  legal edges: `prepared→dispatched`, `dispatched→complete`, `complete→reviewed`,
  `reviewed→integrated`, any live status → `rejected` | `killed`; `historical_unverified` is
  assigned at creation to retroactive records and never transitions. Any other edge ⇒ refuse
  `reason=transition`. `killed` and `historical_unverified` are PERMANENTLY non-integrable —
  `integrate` on them ⇒ REJECT, forever. An additional Boolean `pre_enforcement: true` marks
  only the §7 bootstrap-covered records — non-precedential.
- **The dispatch handshake (r2 f2 — solves record-before-session-id):** (1) the broker writes
  snapshot line 1: `status=prepared`, nonce minted, `session_binding.session_ids = []`;
  (2) the conductor COMMITS the record file (a records-only commit — the durable anchor for
  the nonce, r2 f9); (3) the lane launches with the nonce in its first prompt; (4) the
  harness-returned session id is appended as snapshot line 2: `status=dispatched` (bound).
  `prepared` with nonempty sessions, or `dispatched` with zero sessions ⇒ refuse.
- **Status-dependent required fields:** `dispatched` ⇒ base_sha, registry_sha256,
  dispatch_nonce, session_binding (≥1 session), and — for builder lanes — the full packet
  {design_sha256, design_verdict_ref{path,sha256}, red_sha256, admission_sha256,
  allowed_paths}; reviewer/auditor/demo lanes carry artifact refs in `packet` instead.
  `allowed_paths` must be nonempty, canonical repo-relative, and contain no `..`, no absolute
  path, no symlink-escaping entry — empty or escaping ⇒ refuse at load.
- **Packet floor by role (r2 f7):** a BUILDER record whose `allowed_paths` include
  `tests/contracts/**` (RED-authoring surface), doc-law paths, or `.claude/**` ⇒ refuse
  `reason=packet_floor`; enforcement-surface paths are lawful in a builder packet ONLY when
  `design_verdict_ref` is present (the §4.2 packet-scoped exception).
- **Per-lane completion shapes (r2 f2 — closed by role):** builder `complete` ⇒
  completion{output_patch_sha256, transcript_manifest_sha256}; reviewer/auditor/demo_runner
  `complete` ⇒ completion{report_ref{path, sha256}, transcript_manifest_sha256} with
  `output_patch_sha256` REQUIRED-null (a patch-shaped completion on a non-builder lane ⇒
  refuse). `rejected`/`killed` ⇒ + a final event {ts, to_status, reason}. `reviewed` ⇒ +
  review{reviewed_patch_sha256 == completion.output_patch_sha256, review_refs nonempty
  (path + sha256 of persisted review transcripts)}. `integrated` ⇒ granted only by the
  integration recompute (§3.4), never by editing the field. `execution_kind ∈ {main,
  build_lane, verify_scratch, session_only, historical_killed}` is a REQUIRED field of the
  closed schema (r2 f2) and must agree with the §3.6 census classification.
- **Review profile (effort law as data):** `{round, required_effort, operator_override_ref}` —
  round 1 = `max` (or `ultra`) unless `operator_override_ref` cites an operator directive;
  every repeat round = `xhigh`. This mirrors AGENTS/ACTIVE instead of freezing one session's
  override into the actor (the r1 `codex-xhigh` actor is gone; identity and run profile are
  separate).
- **Stand-in law:** `standin` expresses the AGENTS Codex-unavailable fallback: an independent
  Claude reviewer may take `standin_actor` with `retro_review_queued: true`; while ANY
  integrated record has `retro_review_queued` and no `retro_review_ref`, the `push` and
  `remote_publish` verbs REFUSE (retroactive review blocks publication, as AGENTS requires).
- **Author-never-approves:** `author_actor` and `reviewer_actor` resolving to the same
  principal ⇒ refuse at load (compared by resolved principal, §2.2).
- **Events chain (r2 f9 — recomputable from the file alone):** the record file is
  append-only JSONL of FULL snapshots; snapshot k carries `events[-1] = {ts, to_status,
  prev_sha256}` where `prev_sha256` = sha256 of snapshot line k−1's exact bytes (line 1:
  null). The verifier recomputes every link from the retained lines; any mismatch, or an
  earlier snapshot's events not being a prefix of a later one's ⇒ refuse `reason=chain`.
- **Anchor law (r2 f9):** the prepared snapshot is COMMITTED before launch (handshake step
  2); at check/integration time the HEAD blob of the record file must be a byte-PREFIX of
  the working file (append-only versus HEAD; line 1 byte-equal ⇒ the nonce is durably
  anchored). Never committed, or HEAD not a prefix ⇒ refuse `reason=unanchored_record`.
  Honest ceiling, stated: between handshake commits, a same-session rewrite of
  not-yet-committed suffix lines is caught by the chain + the integration recompute; the
  durable anchor IS the commit. Verification stored on disk is a record of a past check —
  never authority (§3.4 recomputes).

## §3 The gate — `scripts/organization/role_gate.py` (pure stdlib, fail-closed)

### §3.0 Global refusal law (applies to every subcommand)

Exactly one machine line per run — `ROLE-GATE: OK …` | `ROLE-GATE: HALT reason=…` |
`ROLE-GATE: REJECT reason=…` — exit 0 only on OK, exit 2 otherwise. Refuse (exit 2) on ANY of:
missing file, non-regular file, symlink anywhere in the resolved path chain, non-UTF-8 bytes,
invalid JSON/TOML, a PARTIAL trailing JSONL line, an unknown record type, an unknown field in
a closed schema, `isSidechain` present but non-Boolean (the string `"false"` and the number
`0` both refuse), an unknown enum token, an empty required set (zero assistant records, empty
glob, missing directory — never vacuous success), duplicate keys, or any persistence failure.
State writes are temp-file + fsync + rename, and the OK/REJECT line prints only AFTER the
write lands (decide → persist → print; a failed write ⇒ exit 2 with no OK).
Transcript record schema: a CLOSED type list harvested from REAL session JSONL (assistant,
user, system, summary, and whatever the harvest proves exists) — the harvested list rides in
`tests/fixtures/role_gate/` with provenance; an unlisted type ⇒ refuse (relaxable only by a
`schema_version` bump, never silently).

### §3.1 `check-conductor --transcript T` — the EPOCH SCAN (F3 resolved, mandatory-strong)

Scan EVERY main-chain assistant record (`isSidechain` absent-or-false under the strict Boolean
law) in the session file, from the later of (session start | the last operator-attested
quarantine mark): each must carry `message.model` == the conductor seat principal (committed
registry). ANY foreign model anywhere in the epoch ⇒ `HALT reason=tainted_epoch` — a restored
right-seat tail can never bless a wrong-seat window, so "last record" and "last N" are both
gone. Zero assistant records ⇒ HALT. Recovery ONLY via an operator-attested quarantine record
`dev/reports/role_assignments/quarantine-<utc>.json` = `{record: "EpochQuarantine",
session_id, tainted_span (first/last record uuid), operator_ref, clean_tree_sha}`; the scan
resumes after the mark. Wrong-seat work performed inside a tainted span stays quarantined:
nothing from it integrates (§3.4 recompute is downstream of this check).

### §3.2 `assert-authority --action VERB --transcript T`

§3.1 AND `VERB ∈ vocabulary.verbs` AND `VERB ∈ roles[conductor].authority`. An unknown verb ⇒
HALT (default-deny, never default-allow).

### §3.3 `authorize-tool` — the hook entry; EVERY lane, session→assignment binding

Input: the harness PreToolUse stdin JSON. REQUIRED fields (missing any ⇒ exit 2):
`session_id`, `transcript_path`, `cwd`, `hook_event_name`, `tool_name`, `tool_input`;
`hook_event_name != "PreToolUse"` ⇒ exit 2 `reason=wrong_event` (r2 f3 — the real input
schema is stated, not assumed). Documented optional fields (`permission_mode`,
`tool_use_id`, `prompt_id`, `effort`) are read when present — `tool_use_id`/`prompt_id` are
echoed into every refusal line for the audit trail; UNKNOWN extra harness fields are
tolerated (the harness may evolve; closed-schema refusal applies to OUR records, never to
harness input). The harness flushes the transcript asynchronously, so the epoch scan sees
records up to the last flush; the residual window is stated exactly in §4.5.
Resolve the CURRENT session to exactly ONE assignment record: conductor
sessions self-register (below); lane sessions match `session_binding.session_ids`. Two live
records matching one session, or one session matching two records ⇒ refuse.

- **No record ⇒ the READ floor:** only the closed read-safe tool list passes (seed:
  `Read, Glob, Grep, ToolSearch, WebFetch, WebSearch` — closed DATA in the hook; extending it
  is `enforcement_edit`). Everything else refuses. One exception, exactly: a no-record session
  whose epoch scan passes for the CONDUCTOR seat may perform ONE mutation — creating its own
  conductor record `conductor-<session_id>.json` (the session-start self-registration; solves
  the chicken-and-egg without a silent pass).
- **With a record:** map `(tool_name, tool_input)` → verb via the §4.2 matrix; verb ∉ the
  role's authority ⇒ refuse; claude-actor sessions additionally pass the epoch scan against
  THEIR OWN seat principal (a wrong-seated builder lane loses its shell exactly like a
  wrong-seated conductor). Unknown tool name ⇒ refuse.

### §3.4 `check-lane --assignment A.json` — transcripts resolve FROM THE RECORD ONLY

There is NO transcript argument (caller substitution abolished). For EVERY session in
`session_binding`: the transcript exists and parses under §3.0; the FIRST user record contains
`dispatch_nonce`; EVERY assistant record (sidechain included) carries the seat principal
derived from registry[record.actor]; every `Task`/`Agent` tool_use maps to a declared child
record via the parent edge (undeclared child ⇒ REJECT); zero assistant records ⇒ REJECT.
Writes `verification{verified_model_ids, verified_at, verdict}` + an event (persist-then-
print). **Integration law (r2 f5 — integration is a GATE SUBCOMMAND, never raw git):**
integration happens ONLY via `role_gate.py integrate --assignment A.jsonl --patch P`, which
in ONE run (1) re-runs check-lane FRESH; (2) requires sha256(P) ==
`review.reviewed_patch_sha256` == `completion.output_patch_sha256`; (3) recomputes P's
changed-path set and requires it ⊆ `packet.allowed_paths` — ANY escape rejects the whole
patch `reason=path_escape` (the AGENTS allowed-paths law, recomputed at the moment of
integration, r2 f14); (4) requires every `review_refs` path to exist IN HEAD with matching
sha256 — reviews are committed before integration is lawful (r2 f6),
`reason=unanchored_review` otherwise; (5) requires census OK (§3.6), the §2.4 anchor law,
and status outside the non-integrable set; then and only then applies the patch itself and
appends the `integrated` snapshot. The hook (§4.2) REFUSES raw integration-shaped git
(`merge`, `apply`, `am`, `cherry-pick`, `rebase`, `revert`) for EVERY session including the
seated conductor — there is no path from a manual clean `check-lane` to an unrelated merge.
A stored `verdict: "ok"` is inert history — a backfilled edit changes nothing the gate trusts.

### §3.5 `verify-review --assignment A.json --review-file F` + the gate runner

Reviews are PRODUCED only by `scripts/organization/gate_runner.py` (its invocation is
`gate_dispatch`, conductor-seat-gated): it invokes the pinned codex binary with
`shell=False` structured argv = registry `argv_base` + `effort_argv` (effort from
`review_profile`). The r2 argv pin (`--model <model_id> --json --strict-config
--ignore-user-config`) makes the run STRUCTURED and immune to user-config drift (r2 f6):
the captured output is the JSONL event stream, and the identity fields (model, effort,
sandbox, session id) are read from the stream's session-configuration event — never from a
prose banner. The runner mints the gate nonce, injects nonce + the reviewed artifact's
sha256 + the assignment `lane_run_id` into the prompt, captures the stream ITSELF (the
producer is the runner, not the reviewer's self-report), and writes `F` (the raw stream) +
`F.md` (the extracted final reviewer message, for humans) + `F.provenance.json` =
`{lane_run_id, argv, prompt_sha256, output_sha256, model, effort, sandbox, artifact_sha256,
codex_session_id, exit_status, nonce, ts}` — r2 f6: the sidecar binds assignment id, model,
effort, sandbox, and artifact hash; a sidecar missing any of them ⇒ verify-review REJECT.

`verify-review` then checks, all fail-closed: `review_kind ∈ {design, code_adversarial}`
(from the assignment's review_refs entry); recompute the reviewed artifact's sha256 from disk
— the hex MUST appear in `F` (prompt-echo binding); the nonce AND the assignment
`lane_run_id` MUST appear in `F` (r2 f6 — a review is bound to exactly ONE assignment; a
clean review of something else can never be re-pointed); the stream's session-configuration
fields MUST match the registry actor and the run profile (model == `actors.codex.model_id`,
sandbox == read-only, reasoning effort == `review_profile.required_effort`); recompute
`output_sha256` over `F` and cross-check the sidecar; `author_actor` ≠ `reviewer_actor` by
resolved principal. **Verdict grammar — approval is never mere presence:** `design` ⇒ the LAST
non-empty line is exactly `DESIGN-VERDICT: APPROVE` (a `REVISE` line is a valid transcript
and NOT approval); `code_adversarial` ⇒ the final verdict lines are exactly `VERDICT:
approve` AND `ADVERSARIAL-VERDICT: approve` — one arm missing, or any `revise` value, ⇒ not
approval; a design verdict can never satisfy a code review. Honest ceiling, stated: without
OS-level process attestation the runner's own capture is the trust anchor; the runner runs
under the seat-gated conductor session and its code executes from HEAD (§4.3); the
reviews-in-HEAD requirement (§3.4 (4)) makes a post-hoc rewrite of `F` or its sidecar a
hash mismatch against the committed refs rather than a silent substitution.

**Stand-in arm (r2 f10 / r1-15):** when `standin.active` is true the reviewer seat is NOT
re-slotted — the assignment carries `standin_actor` (a declared claude actor whose resolved
principal ≠ the author's), `retro_review_queued: true`, and verify-review switches to the
claude arm: the review artifact is a nonce-bound lane transcript verified by the SAME epoch
scan + verdict grammar (no codex stream fields expected), and every `push`/`remote_publish`
stays refused until `retro_review_ref` lands (§2.4). A stand-in review carrying codex-arm
fields, or a codex review claiming the stand-in arm, ⇒ REJECT. The singleton seat law and
the stand-in fallback are thereby consistent: the seat never changes; the exception is
attested assignment data with a mandatory retroactive close-out.

### §3.6 `census` — a real worktree census, not a directory scan

Enumerate `git worktree list --porcelain` through the canonical common git dir. Classify
EVERY worktree by closed `execution_kind ∈ {main, build_lane, verify_scratch,
historical_killed}`. Every non-main worktree ↔ exactly one assignment via
`session_binding.worktree` (bijection: an unmatched worktree ⇒ REJECT; a live-status record
whose worktree is absent from the census ⇒ REJECT). Reviewer/auditor session-only lanes
declare `worktree: null` + record `execution_kind: session_only` (r2 f2) — exempt from
worktree mapping, still session-bound; for worktree-bound lanes the record's
`execution_kind` must agree with the census classification. More than one live conductor
record ⇒ REJECT. Census green is an ACTIVATION criterion (§7, r2 f9/f13).

## §4 Harness enforcement — the structural teeth (T1/T2/T6 killers)

### §4.1 Tracked wiring (the hook is a reviewed, committed file — not local state)

`.gitignore` changes from `.claude/` to:

```
.claude/*
!/.claude/settings.json
```

(worktrees and local state stay ignored; the wiring becomes TRACKED). `.claude/settings.json`
and the carve-out are declared in `contracts/repo_layout.json`; REDs assert
`git ls-files --error-unmatch .claude/settings.json` AND a fresh `git worktree add` probe
sees the row (§5 H1/H2). Matcher semantics corrected: a PreToolUse matcher selects TOOL
NAMES — the row uses `"matcher": "*"` (every tool) and ALL classification happens inside the
hook from stdin JSON. The exact row:

```json
{"hooks": {"PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command":
  "bash -c 'fail(){ echo \"ROLE-GATE: HALT reason=$1\" >&2; exit 2; }; cd \"$CLAUDE_PROJECT_DIR\" || fail launcher_cd; src=\"$(git cat-file blob HEAD:scripts/organization/role_gate_hook.py)\" || fail launcher_blob; [ -n \"$src\" ] || fail launcher_empty; python3 -c \"$src\"; rc=$?; [ \"$rc\" -eq 0 ] || [ \"$rc\" -eq 2 ] || fail \"launcher_python_rc$rc\"; exit $rc'"}]}]}}
```

Fail-closed launcher mechanics (r2 f3 — EVERY failure normalizes to exit 2 + a reason
line): the hook JSON arrives on stdin and is preserved for the script (the code travels via
`-c`, never via a stdin pipe). In this harness ONLY exit 2 blocks a tool call — exit 1,
exit 127 (missing interpreter), tracebacks, and signal deaths would otherwise fail OPEN —
so the launcher maps every non-{0,2} exit to 2 (`launcher_python_rcN`), and every internal
branch (`cd`, blob read, empty blob) exits 2 with its own `ROLE-GATE: HALT reason=…` line
on stderr. The hook's own top level additionally wraps everything in a catch-all that
prints a reason line and exits 2 (defense in depth: an unhandled exception is a refusal,
never an allow).

### §4.2 Hook algorithm (default-deny; runs for every tool call in every lane)

1. `tool_name` in the closed read-safe list ⇒ allow (§3.3 seed).
2. `Bash` ⇒ seat law FIRST: the session's epoch scan must pass for its OWN seat — a
   wrong-seated session gets NO shell at all, regardless of command text (the unconditional
   identity gate; spelling games cannot reach a bypass because identity is checked before any
   parsing). Then the command classifier, default-deny:
   - strip wrapper prefixes (`env`, `command`, `nice`, `timeout`, `VAR=…` assignments,
     absolute interpreter/binary paths);
   - git → DEFAULT-DENY (r2 f4): a git invocation in ANY spelling (`-C`, `-c key=val`,
     `--git-dir`, `--work-tree`, `GIT_DIR=`/`GIT_WORK_TREE=` prefixes, absolute git path)
     is REFUSED unless its subcommand is in the closed READ list {status, log, diff, show,
     cat-file, ls-files, ls-tree, rev-parse, blame, grep, describe, merge-base, shortlog,
     branch (list-only), worktree list, remote -v, stash list} — or maps to a verb the role
     HOLDS: `commit→commit` · `merge|apply|am|cherry-pick|rebase|revert→integrate` (raw
     forms refused even for holders — §3.4: only the gate subcommand integrates) ·
     `push→push` · `tag→tag` · `add|restore (any form)|rm|mv|checkout -- <path>|switch|
     stash (mutating)→stage` (the repo-state-mutation-below-commit class) ·
     `update-ref|commit-tree|symbolic-ref|reset|branch -f|branch -D|remote add/set-url|
     config (write form)→ref_update` · `clean|worktree *→worktree_admin`; `gh` `pr merge` |
     non-GET `api` | `release *` | `repo edit` → `remote_publish`; `codex` →
     `gate_dispatch`; `role_gate.py integrate` → `integrate` (the ONLY lawful integration
     spelling); `role_gate.py check-*|verify-review|census` → `verify`. An UNLISTED git/gh
     subcommand ⇒ refuse — never benign (kills the `git gc`/unknown-form fall-through);
   - alias law: `-c alias.<x>=<y>` resolves `<y>` first — reaching an authority subcommand ⇒
     that verb; unresolvable alias ⇒ refuse;
   - indirection law: authority tokens (`git`, `gh`, `codex`, `update-ref`, …) inside
     `sh -c`/`bash -c`/`eval`/`xargs`/command substitution/pipes-to-shell, OR an argv that
     cannot be fully classified while containing an authority token ⇒ refuse (unparseable =
     refused, never allowed);
   - write-shaped law (r2 f4 — generalizes r1's redirection law from two path classes to
     ALL of them): raw text combining ANY repo path token with write-shaped syntax (`>`,
     `>>`, `tee`, `mv`, `cp`, `sed -i`, `rm`, `mkdir`, `touch`, `chmod`, `ln`, `install`,
     `dd`) ⇒ classify by the point-3 path-class table exactly as an Edit to that path would
     be — `echo x > site/index.html` IS `implement`, so a reviewer/auditor/demo lane is
     refused; write-shaped text whose every path token resolves under `scratchpad/**` or
     the harness scratchpad ⇒ benign; write-shaped text with NO classifiable repo path ⇒
     refused for roles that do not hold `implement` (deliberately overbroad — refuses false
     positives rather than admitting false negatives);
   - benign remainder (no authority classification AND no write-shaped token) requires only
     the seat law — test runs and read-only inspection keep working for every
     correctly-seated lane; a demo lane's Bash must additionally either exactly match one
     packet-declared demo entrypoint argv or be read-benign (r2 f4: `run_demo`'s effect
     surface). Fine-grained write TARGETS of arbitrary shell remain governed at integration
     by the allowed-paths recompute (§3.4 (3)) plus worktree isolation;
   - verb→effect closure (r2 f4 — every verb lives in exactly ONE effect table, so no verb
     is orphaned dead authority): (A) Bash classes above carry {commit, integrate, push,
     tag, stage, ref_update, worktree_admin, remote_publish, gate_dispatch, verify,
     run_demo}; (B) the point-3 path-class table carries {enforcement_edit, doc_law_edit,
     design, author_red, persist_review, dispatch_lane, audit_report, generate_receipts,
     record_summary, register_home, implement, operator_reslot (the registry-seats edit,
     §2.3)}; (C) dispatch/metadata surfaces carry {dispatch_lane (Agent/Task — point 4),
     author_admission (admission artifacts inside dispatch packets), read, run_demo
     (entrypoint declaration), audit_report (report refs)}; the registry test asserts
     tables A ∪ B ∪ C cover the 26-verb vocabulary exactly (V4).
3. `Edit`/`Write`/`NotebookEdit` ⇒ closed path-class table (unmatched path ⇒ refuse):
   enforcement surface `{contracts/role_registry.toml, scripts/organization/role_gate.py,
   role_gate_hook.py, gate_runner.py, .claude/settings.json, .gitignore}` → `enforcement_edit`
   — UNLESS the session's assignment packet lists that exact path in `allowed_paths` AND
   carries `design_verdict_ref` (a reviewed design authorizing enforcement work): then the
   edit maps to `implement` (r2 f7 — the lawful maintenance lane; safe because working-tree
   edits are inert under §4.3 and land only through gated review + commit) · doc law
   `{AGENTS.md, docs/plans/ACTIVE.md, contracts/**.toml}` → `doc_law_edit` · design records
   `docs/plans/handoff/**` → `design` (r2 f4: the `design` verb's concrete effect surface) ·
   `tests/**` → `author_red` · `dev/reports/reviews/**` → `persist_review` ·
   `dev/reports/role_assignments/**` → `dispatch_lane` (records are dispatch artifacts) ·
   `dev/reports/audits/**` → `audit_report` (r2 f4: the auditor's concrete report home) ·
   `assets/receipts/**` → `generate_receipts` · `docs/history/**` → `record_summary` ·
   `contracts/repo_layout.json` + `scripts/organization/{layout_contract,
   tests_layout_contract}.py` → `register_home` (roster-ROW registration; the row-only
   constraint on those two .py files is review-enforced, not hook-parsed — r2 f7) ·
   `scratchpad/**` + the harness scratchpad → read floor (allowed for every seated session)
   · `site/**`, `scripts/**`, other governed source homes → `implement`. (The r1 fork F1
   stays RESOLVED-MANDATORY: wrong-seat or wrong-role doc-law and enforcement edits are
   hook-refused, not ritual.)
4. `Agent`/`Task` ⇒ `dispatch_lane` + the broker law: the dispatching session must hold
   `dispatch_lane`; the child record must already exist (nonce minted) before launch; only the
   conductor role may dispatch (builder/reviewer/auditor/demo hold `forbidden:
   dispatch_lane`); a child that would hold commit-capable verbs ⇒ refuse outright — no
   transitive authority through spawning.
5. Every refusal prints the machine line + the mapped verb + the matched rule id, so the
   operator always sees WHY.

### §4.3 Trust-root execution (T6): the code that runs is the code that was committed

The settings row (§4.1) executes the HOOK from the HEAD blob; the hook loads `role_gate.py`
the same way (exec of `git cat-file blob HEAD:scripts/organization/role_gate.py`) and reads
the registry only via the HEAD blob (§2.3). Consequence: editing the gate, the hook, or the
registry in the working tree changes NOTHING until a commit lands, and `commit` is itself
seat- and role-gated. Combined with the §2.3 drift HALT, an in-flight tamper is both inert
and loud. Bootstrap caveat, stated plainly: before the first commit that tracks these files,
HEAD has no blobs and the launcher exits 2 — the pre-activation window is governed by §7's
bootstrap envelope, and this design claims nothing for it.

### §4.4 MODEL-INTEGRITY HALT ritual (AGENTS.md amendment, same commit)

The conductor runs `check-conductor` (a) at session start, (b) after EVERY context
continuation/compaction, (c) before any authority action. (c) is mechanical — the hook runs
the seat law on every mutating tool call; (a)/(b) are ritual + spot-audited via the session
transcript. (d) r2 f3: the session-start ritual includes the hook CANARY
`tests/fixtures/role_gate/hook_canary.sh` — a deliberately-refusable probe whose REFUSAL
proves the hook is live in THIS session; if the canary is NOT refused, enforcement is off
(hooks disabled at the harness level, user-scope override) and the conductor reports that
to the operator BEFORE any authority action — detection, not prevention, per §4.5. On
HALT: every authority action keeps refusing mechanically until the operator lands a
quarantine record (§3.1); the session drops to the read floor; the mismatch is surfaced to
the operator verbatim.

### §4.5 Exact claims + honest ceiling (replaces "structurally impossible")

This design claims exactly: (1) wrong-seat authority ACTIONS through harness tools are
refused at PreToolUse; (2) wrong-seat work product cannot INTEGRATE — integration recomputes
lane verification fresh, with nonce and patch-hash equality; (3) authority DATA cannot change
without a seat-gated commit plus an attested reslot record; (4) any wrong-seat presence in an
epoch is loud and taints the epoch until an operator-attested quarantine record closes it.
It does NOT claim: per-token attestation of the in-flight model — the transcript is flushed
asynchronously, so the FIRST wrong-seat tool call after a fresh swap can precede its own
record (r2 f3/r1-5, stated exactly): that call is caught at the next enforcement point, the
epoch is tainted retroactively, and its work product cannot integrate (claims 2–4 hold
unconditionally; claim 1 holds from the first flushed record onward), with
`tool_use_id`/`prompt_id` logged for the audit trail; defense against a hostile harness or
out-of-band writes that bypass the tool layer — INCLUDING harness-level hook disablement
(user-scope settings, global hook kill-switches, managed policy), which no in-repo file can
prevent: the in-scope counter is DETECTION — the §4.4 (d) canary proves per-session that
the hook is live and alerts the operator when it is not, and the activation probes prove it
end-to-end at landing; cryptographic identity — the reference registry's own posture holds
here: these are harness-honest reported identity tokens. Remote backstop (adoption item,
outside this repo's file surface): branch/tag protection on the origin default branch gives
`push`/`remote_publish` a server-side floor; recorded for the operator in §8 F4.

## §5 REDs (Fable-authored AFTER the DESIGN gate, observed failing BEFORE build)

- `tests/contracts/test_role_registry.py` — R1 registry exists + parses from BOTH the working
  tree and the HEAD blob; R2 closed schema (unknown key/role/seat/verb/kind/status ⇒ refuse);
  R3 seats: key set == role set, singleton strings, values name declared actors; R4
  disposition law: per role `authority ∪ forbidden == vocabulary` and disjoint (kills a
  reviewer+`commit` or builder+`dispatch_lane` mutant as a SHAPE failure); R5 principal
  uniqueness (kills duplicate-principal actor pairs); R6 author==reviewer by resolved
  principal ⇒ refuse; R7 SEED EQUALITY WITH THE LAWFUL-RESLOT CARVE-OUT (r2 f8): the
  committed registry's `vocabulary` + `roles` blocks byte-equal the §2.1 seed (structure
  changes only via a `schema_version` bump), and `[seats]`/`[actors]` either byte-equal the
  seed OR every divergence is covered by a reslot-attestation chain (§2.3) whose links
  connect sha256(seed) → … → sha256(current committed blob) — an unattested seat flip
  reddens; an operator-attested one passes (kills silent seed drift WITHOUT contradicting
  §0's re-slot-by-data law); R8 codex actor: structured argv containing the exact pin
  `["--model", model_id, "--json", "--strict-config", "--ignore-user-config"]` (kills the
  empty-flags and user-config-drift mutants).
- `tests/contracts/test_role_gate.py` — fixtures in `tests/fixtures/role_gate/`: REAL
  harvested session JSONL with provenance sidecars (compaction, sidechain true/false/absent,
  resumption), plus synthetic hostile cases. G1 all-fable epoch ⇒ OK; G2 foreign model
  ANYWHERE in the epoch ⇒ HALT — including the stale-fixture where the LAST record is Fable
  but an earlier window is Opus (kills any last-record shortcut); G3 model key absent ⇒ HALT;
  G4 refusal matrix, each exit 2: empty file · partial trailing line · symlink transcript ·
  unknown record type · string-`"false"` isSidechain · missing directory/empty glob; G5
  assert-authority verb matrix (commit OK for the seated conductor; implement ⇒ HALT even
  seated; unknown verb ⇒ HALT); G6 check-lane: foreign model ⇒ REJECT + persisted verdict ·
  nonce-missing clean transcript ⇒ REJECT (kills transcript substitution) · undeclared
  Task-child ⇒ REJECT; G7 verify-review: `REVISE`-only ⇒ not approval · single-arm code
  review ⇒ not approval · design verdict against code kind ⇒ REJECT · banner effort mismatch
  ⇒ REJECT · missing artifact-hash echo ⇒ REJECT · sidecar hash mismatch ⇒ REJECT; G8 census:
  a temp repo with a linked worktree OUTSIDE `.claude/worktrees` reddens unmatched ·
  null-worktree reviewer lane passes · two live conductor records ⇒ REJECT; G9 integration
  recompute: a record hand-edited to `verdict: "ok"`/`status: integrated` still refuses to
  integrate (kills the backfilled-verdict mutant); G10 lifecycle: each status missing a
  required field ⇒ refuse · killed/historical_unverified integrate ⇒ refuse ·
  `retro_review_queued` without ref blocks `push`.
- Hook REDs (executable end-to-end — empirical domain, scripts from the FIRST round per the
  convergence law): H1 `git ls-files --error-unmatch .claude/settings.json` green + row shape
  asserted from the HEAD blob; H2 fresh `git worktree add` probe sees the tracked settings +
  row; H3 END-TO-END: run the EXACT settings command with real hook stdin JSON — wrong-seat
  commit fixture ⇒ exit 2 (this runs HEAD's code, so a working-tree hook mutated to exit 0
  changes nothing — the exit-0 mutant dies here); right-seat commit ⇒ allow; H4
  hostile-spelling matrix, each ⇒ refuse: `git -C x push` · `git -c alias.c=commit c` ·
  `/usr/bin/git commit` · `env git push` · `command git push` · `GIT_DIR=… git push` ·
  `git --git-dir=… push` · `sh -c 'git push'` · `git commit-tree` · `git update-ref` ·
  `git tag` (wrong role) · `git worktree remove` (wrong role) · `gh pr merge` ·
  `echo x > .claude/settings.json` · `sed -i … contracts/role_registry.toml`; H5 the read
  floor: a no-record session's Bash ⇒ refuse, Read ⇒ allow, and its single permitted
  self-registration write ⇒ allow only with a passing conductor epoch.
- **Pitfall matrix (SOP step 4 — the top 5 authority-poisoning lies → guards):**
  L1 "the registry authorizes me," told via a working-tree edit → HEAD-blob resolution +
  drift HALT (R7, §2.3). L2 "the lane ran clean," told with a substituted transcript →
  nonce + record-resolved transcript paths (G6). L3 "the review approved," told by a
  hand-written file → runner-captured provenance + hash cross-checks + approval grammar (G7).
  L4 "verification says ok," told by a record edit → integration recomputes, stored verdicts
  are inert (G9). L5 "the hook is wired," told by prose or an untracked local file →
  tracked-file + HEAD-blob end-to-end probes (H1–H3).
- **Mutation witnesses (non-vacuous):** M1 temp repo with a conductor seat = `"opus"` registry
  COMMITTED ⇒ G1 flips OK→HALT (the gate reads committed data, not hardcode); M2 temp repo
  with the settings row deleted and committed ⇒ H1/H3 fail there; M3 check-lane expecting
  opus on a fable transcript ⇒ REJECT (seat-neutral symmetry — the gate is not anti-Opus);
  M4 hook mutated to exit 0 UNCOMMITTED ⇒ H3 still blocks (HEAD runs) AND the drift check
  HALTs; the same mutant COMMITTED in a temp repo ⇒ H3 fails there; M5 nonce check deleted ⇒
  the G6 substitution fixture flips; M6 disposition law relaxed ⇒ the R4 mutant grants redden.
- **r2 convergence REDs (V-series) — every probeable r2 finding converted to an exact
  executable RED under the AGENTS.md convergence law. Each fails on TODAY'S tree for the
  right reason: the named enforcement does not exist yet (gate/hook/registry absent, law
  unimplemented), which is precisely the finding. File = `tests/contracts/test_role_gate.py`
  unless noted; hostile records/repos are built in tmp by the test itself:**
  - **V1 (f1)** `test_v1_actor_must_match_seat` — check-lane on a record
    `{role: "conductor", actor: "opus"}` under the seed registry ⇒ exit 2 + line contains
    `reason=seat_mismatch`; and `test_v1_dispatched_by_bound_to_conductor_seat` — a record
    whose `dispatched_by` names an actor other than the seated conductor ⇒ exit 2.
  - **V2 (f2)** `test_v2_lifecycle_transitions_closed` — `prepared` with nonempty
    `session_ids` ⇒ exit 2; `dispatched` with zero sessions ⇒ exit 2; the edge
    `prepared→integrated` in the snapshot chain ⇒ exit 2 `reason=transition`; and
    `test_v2_per_lane_completion_shapes` — an auditor record whose completion carries
    `output_patch_sha256` non-null ⇒ exit 2; any record missing `execution_kind` ⇒ exit 2.
  - **V3 (f3)** `test_v3_launcher_normalizes_exit_codes` — in a tmp repo with the §4.1 row
    committed: a hook blob that raises (python exit 1) ⇒ launcher exit 2 + a `ROLE-GATE:`
    line on stderr; python3 stripped from PATH ⇒ exit 2 (127 never escapes); and
    `test_v3_hook_input_schema` — stdin missing `session_id` ⇒ exit 2; stdin with
    `hook_event_name: "PostToolUse"` ⇒ exit 2 `reason=wrong_event`.
  - **V4 (f4)** `test_v4_write_shaped_bash_classified` — hook stdin Bash
    `echo x > site/index.html` under a reviewer record ⇒ exit 2 (classifies `implement`,
    forbidden); `test_v4_git_default_deny` — `git cherry-pick abc` under a builder record ⇒
    exit 2 (maps `integrate`); `git apply p.patch` under a reviewer ⇒ exit 2; unlisted
    `git gc` under a reviewer ⇒ exit 2; `git status` under every seated role ⇒ exit 0; and
    `test_v4_verbs_tile_effect_tables` (in `test_role_registry.py`) — the §4.2 effect
    tables A ∪ B ∪ C cover the 26-verb vocabulary exactly, no orphan verb.
  - **V5 (f5)** `test_v5_integrate_only_via_gate` — Bash `git merge lane-branch` even under
    the seated conductor ⇒ exit 2 (raw integration refused); and
    `test_v5_integrate_recomputes_paths` — `integrate` with a patch touching one path
    outside `allowed_paths` ⇒ REJECT `reason=path_escape`; with sha256(patch) ≠ the
    reviewed hash ⇒ REJECT `reason=patch_hash`.
  - **V6 (f6)** `test_v6_registry_pins_codex_argv` (in `test_role_registry.py`) — the R8
    exact-pin assertion on the committed registry; `test_v6_sidecar_binds_assignment` — a
    provenance sidecar missing any of {lane_run_id, model, effort, sandbox,
    artifact_sha256} ⇒ verify-review REJECT; `test_v6_review_missing_lane_id_echo` — an
    otherwise-clean review file that does not contain the assignment's `lane_run_id` ⇒
    REJECT; `test_v6_reviews_committed_before_integrate` — `integrate` while any
    `review_refs` path is absent from HEAD ⇒ REJECT `reason=unanchored_review`.
  - **V7 (f7)** `test_v7_builder_packet_floor` — a builder record whose `allowed_paths`
    include `tests/contracts/test_x.py` or `docs/plans/ACTIVE.md` ⇒ exit 2
    `reason=packet_floor`; an enforcement-surface path WITHOUT `design_verdict_ref` ⇒
    exit 2; the same path WITH it ⇒ loads (the maintenance lane stays lawful).
  - **V8 (f8)** `test_v8_attested_reslot_passes_r7` — tmp repo: seed committed, then
    `seats.builder` flipped WITH a valid reslot-attestation record committed ⇒ registry
    check OK; the same flip WITHOUT the attestation ⇒ exit 2; and
    `test_v8_agents_names_registry_as_seat_authority` — AGENTS.md contains the exact marker
    `seat occupants are data: contracts/role_registry.toml` (fails today: the sentence does
    not exist until the §6 amendment lands).
  - **V9 (f9)** `test_v9_event_chain_recomputable` — a record JSONL whose line-2
    `prev_sha256` ≠ sha256(line-1 bytes) ⇒ exit 2 `reason=chain`;
    `test_v9_record_anchored_in_head` — check-lane on a never-committed record ⇒ REJECT
    `reason=unanchored_record`, and HEAD-blob-not-a-prefix-of-working-file ⇒ REJECT; and
    `test_v9_bootstrap_envelope_closed` — an envelope missing `activation_commit` or
    `census_at_activation` keys, or carrying an unknown key ⇒ exit 2.
  - **V10 (f10)** `test_v10_standin_arm` — `standin.active` with `standin_actor` resolving
    to the author's principal ⇒ exit 2; `standin.active` without `retro_review_queued` ⇒
    exit 2; an integrated stand-in record without `retro_review_ref` refuses `push`
    (extends G10).
  - **V11 (f11-F6)** `test_v11_read_floor_pinned` — the hook module's `READ_SAFE_TOOLS`
    equals exactly `("Read", "Glob", "Grep", "ToolSearch", "WebFetch", "WebSearch")` — the
    §8 F6 default pinned as loud data; any change is a reviewed enforcement change.
  - **H6 (f3)** `tests/fixtures/role_gate/hook_canary.sh` — activation/ritual probe
    (H-series executable script, not unittest): a deliberately-refusable command that MUST
    be refused in a live session; non-refusal is the operator alert for disabled
    enforcement (§4.4 (d)).
  - **Non-probeable r2 arms, stated:** f11-F4 (server-side protection) is an operator
    adoption act outside this repo's files — no RED can witness it here; f11-F5 is DECIDED
    by exclusion (§8) — a non-feature has no RED; f10's supersession arms are carried by
    V2/V3/V6/V10 above.

## §6 Build packet (after `DESIGN-VERDICT: APPROVE`)

**Builder allowed paths (closed; r2 f7 — REDs are NOT builder surface):**
`contracts/role_registry.toml` · `scripts/organization/role_gate.py` ·
`scripts/organization/role_gate_hook.py` · `scripts/organization/gate_runner.py` ·
`tests/fixtures/role_gate/` (harvested fixtures + probe scripts, `hook_canary.sh`
included) · `dev/reports/role_assignments/README.md`. Registry seed content comes VERBATIM
from §2.1 — the builder types it, never chooses it. The RED files
`tests/contracts/test_role_registry.py` + `tests/contracts/test_role_gate.py` are
CONDUCTOR-authored (AGENTS: Fable authors REDs) and are NOT in the builder packet — the
builder makes them green without ever editing them. The enforcement files ARE lawful
builder surface here: this packet carries `design_verdict_ref`, so those edits classify as
`implement` under the §4.2 packet-scoped exception (building the gate is implementation
under a reviewed design, not an enforcement self-edit).

**Maintenance flow (r2 f7 — no deadlock after activation):** post-activation changes to the
enforcement surface follow the SAME lane shape forever: Fable designs + authors REDs → an
Opus builder lane whose packet lists the enforcement paths (with `design_verdict_ref`)
implements → Codex reviews CODE + ADVERSARIAL → the conductor integrates via §3.4 and
commits. The conductor's own `enforcement_edit` grant covers exactly the bootstrap wiring
data (§7) and the one-row settings/ignore carve-outs — registration-shaped data, not
implementation (the AGENTS conductor-never-implements rule holds; roster ROWS are
`register_home` data the same way).

**Conductor-owned same-commit roster (final-patch paths OUTSIDE the builder packet, listed
separately so the packet law stays honest):** `.gitignore` (the §4.1 carve-out) ·
`.claude/settings.json` (the ONE row) · `contracts/repo_layout.json` homes for
`{dev/reports/role_assignments/, dev/reports/reviews/, dev/reports/audits/,
tests/fixtures/role_gate/, .claude/settings.json}` + the matching roster ROWS in
`scripts/organization/{layout_contract, tests_layout_contract}.py` · the AGENTS.md
amendment (§4.4 ritual + canary; the step-7 registry reference becomes true; r2 f8: the
routing section's hardcoded Fable/Opus/Codex names become "current seed occupants — data,
not law" plus the exact marker sentence `seat occupants are data:
contracts/role_registry.toml`, so re-slotting never edits AGENTS.md again) · the RED files
`tests/contracts/test_role_registry.py` + `tests/contracts/test_role_gate.py`
(Fable-authored, r2 f7) · the ACTIVE.md status line + POINTERS row naming
`dev/reports/reviews/` as the durable review home (scratchpad stays the working copy) ·
persisted gate transcripts `dev/reports/reviews/w7-design-gate-r*.md` referenced by
path + sha256 · the W7 assignment/bootstrap records themselves.

Reviewer: Codex CODE + ADVERSARIAL at the effort the §2.4 review-profile law requires.
Conductor authors the REDs and the admission, verifies, integrates, commits.

## §7 Seeding, bootstrap, adoption — and supersession of the killed partial, lane by lane

- **Seed seats = §2.1 values** (operator-ratified routing: conductor=Fable, builder=Opus,
  reviewer=codex, auditor/demo=Opus — operator messages 2026-07-16 01:43Z and this session's
  opening directive).
- **Bootstrap (circularity closed honestly; r2 f9 — the envelope is a CLOSED schema):**
  W7's own lanes necessarily predate the gate. ONE operator-attested bootstrap envelope
  `dev/reports/role_assignments/w7-bootstrap.json` = exactly `{record: "BootstrapEnvelope",
  schema_version: 1, operator_ref: {message_ts, quote}, covers: [every W7 lane_run_id — an
  exact census, no wildcard], pre_enforcement: true, activation_commit: null-until-set,
  census_at_activation: null-until-set}` — unknown or missing key ⇒ refuse (V9). It marks
  every W7-build record `pre_enforcement` — non-precedential and excluded from every
  enforcement claim. **Activation** = the first commit where ALL pass in a clean probe
  session: (1) tracked settings + row read from HEAD (H1/H2); (2) trust-root self-check
  green (gate runs from the HEAD blob; drift check clean); (3) the wrong-seat fixture is
  refused end-to-end (H3); (4) r2 f9/f13: the §3.6 census is GREEN — every one of the
  repository's existing non-main worktrees carries its `killed`/`historical_unverified`
  record FIRST. The activation commit hash and the census snapshot are then written into
  the envelope (`activation_commit`, `census_at_activation`) in the activation commit
  itself. Enforcement claims start AT the activation commit — never retroactively.
- **Retroactive census closure:** the historical Opus-era worktrees receive records with
  status `killed` or `historical_unverified` — both permanently non-integrable; census then
  bijects over the real `git worktree list`, not a directory listing.
- **Supersession of `agent-a3fb94af1ff864da0` — EVERY lane, explicitly:**
  - *conductor:* the partial had a seat-law row + a conductor-only model check → superseded by
    the epoch-scan `check-conductor`, the hook seat law on every tool, and quarantine records;
    behaviorally closed (r2 f10) by the V3 launcher normalization + the §4.4 (d) canary + the
    §4.5 exactly-stated first-flush window.
  - *builder:* the partial had one slot record and NO check → superseded by packet-bound
    assignment records + dispatch nonce + `check-lane` + the integration recompute;
    behaviorally closed (r2 f10) by the §2.4 prepared→dispatched handshake (V2) + the anchor
    law (V9).
  - *reviewer:* the partial had a seat row and NO verification → superseded by the gate-runner
    capture, `verify-review` grammar + provenance, and the review-profile effort law;
    behaviorally closed (r2 f10) by the structured argv pin + sidecar/lane-id binding (V6) +
    the stand-in arm (V10).
  - *auditor:* ABSENT from the partial → new `auditor` role/seat, read floor + `audit_report`
    (concrete effect surface `dev/reports/audits/**`), session-only census binding
    (`worktree: null`, `execution_kind: session_only`); behaviorally closed (r2 f10) by the
    per-lane completion shapes (V2).
  - *demo:* ABSENT from the partial → new `demo_runner` role/seat with `run_demo` (concrete
    effect surface: packet-declared entrypoint argv only); behaviorally closed (r2 f10) by
    V2 + the §4.2 entrypoint law.
  - *homes:* the partial's `contracts/slot_assignments/` is REJECTED as a home — `contracts/`
    holds LAW; per-run records live in `dev/reports/role_assignments/` (the reference
    corpus-home law). Its test file is prior art to harvest, never authority. The worktree's
    branch is never merged; it lands in the census as `killed`.
- **On landing:** AGENTS step-7's `contracts/role_registry.*` reference becomes true; every
  NEW dispatch writes its record first — post-activation this is structural
  (`dispatch_lane` refuses without the child record), not procedural; `check-lane` runs
  before ANY integration, mechanically (§3.4).

## §8 Non-goals + fork dispositions (for the r2 DESIGN gate)

- **Resolved-mandatory (were open forks in r1):** F1 doc-law/enforcement edit governance →
  §4.2 path classes. F2 review provenance → §3.5 gate runner. F3 freshness window → §3.1
  whole-epoch scan (a fixed N is rejected as insufficient in both r1 and this text).
- **Non-goals (honest):** defense against a hostile harness or records rewritten beneath the
  tool layer — the harness-written JSONL is the trust base, the same base the audit used;
  per-message enforcement inside a turn (no hook exists for text); cryptographic process or
  model attestation (reported-identity honest ceiling, as the reference registry states);
  OS-level sandboxing of lanes.
- **Operator decision points (r2 f11 — each now carries a DESIGN DEFAULT so the build never
  blocks on them and no operator choice is preempted; the r2 gate judged F5/F6 design-ownable,
  so the design takes a position on each and the operator may override through the normal
  reviewed flow):**
  - **F4 — server-side branch/tag protection on origin.** Genuinely operator-owned: it is
    external repository administration, outside this repo's file surface. DEFAULT while
    undecided: local enforcement only; `push`/`remote_publish` stay locally governed.
    Recommendation stands: adopt it, so publication gains a floor the local hook cannot
    provide.
  - **F5 — auto-drafting the quarantine record after a tainted-epoch HALT.** DECIDED by
    design: EXCLUDED from W7 v1 — pure convenience, confers no authority, adds surface. The
    operator may order it later as its own designed-and-reviewed addition. Nothing in this
    build depends on it.
  - **F6 — breadth of the read-safe tool floor for record-less sessions.** DECIDED by
    design: the uniform closed six-tool list (§3.3 seed) for every role, pinned by RED V11
    so the floor is loud data; per-role read floors are REJECTED for v1 (closure
    simplicity). The operator may ratify or change the list; a change is one data edit plus
    the V11 pin update through the §6 maintenance flow — cheap, loud, reviewed.

## §9 r1 fold ledger (17/17 folded 2026-07-16; none deferred)

| r1 finding (paraphrased) | folded into |
| --- | --- |
| 1 — authority data/gate writable by the governed actor | §2.3 + §4.3: HEAD-blob trust root, no registry argument, drift HALT, attested reslot |
| 2 — hook wiring untracked under the ignore rule | §4.1 carve-out + §6 roster + §5 H1/H2 fresh-worktree probes |
| 3 — matcher semantics wrong; command spellings evade | §4.1 tool-name matcher + §4.2 unconditional seat law, classifier/alias/indirection/redirection laws + §5 H4 |
| 4 — no per-tool enforcement for non-conductor lanes | §3.3 authorize-tool: session→assignment for EVERY lane, read floor, default-deny; F1 mandatory |
| 5 — last-record model check insufficient | §3.1 whole-epoch scan + quarantine records + §4.5 exact claims replacing absolutes |
| 6 — lane check accepts substituted transcripts | §2.4 nonce + session_binding; §3.4 record-resolved transcripts + child-edge law |
| 7 — refusal behavior unspecified for real file/record edge cases | §3.0 global refusal law + harvested closed transcript schema + persist-then-print |
| 8 — registry closure gaps (alias seats, array seats, shared principals, loose grants) | §2.1/§2.2: alias seats removed, singleton seats, disposition law, principal uniqueness |
| 9 — records/verification are editable self-attestations | §2.4 events chain + derived expectations + §3.4 integration recompute + non-integrable retro states |
| 10 — review acceptance too weak (presence, wrong kind, no artifact binding) | §3.5 verdict grammar, kind binding, artifact-hash echo |
| 11 — review provenance unverifiable; codex model unpinned | §3.5 gate runner (F2 mandatory) + §2.1 pinned codex model/argv |
| 12 — authority actions outside the verb map | §2.1 26-verb closed vocabulary + §4.2 effect mapping (integrate, tag, ref_update, worktree_admin, remote_publish, stage) + broker law |
| 13 — census scanned one directory, not the repo's worktrees | §3.6 porcelain census + execution_kind + null-worktree lanes |
| 14 — packet fields below the AGENTS bound-packet law | §2.4 status-dependent fields (design_verdict_ref, output_patch_sha256, allowed-path floors) + §3.4 hash equality |
| 15 — one session's effort override frozen into the actor; no stand-in states | §2.1 identity/profile split + §2.4 review_profile, standin + retro states, push refusal |
| 16 — named mutants survive the listed REDs; pitfall matrix missing | §5 seed-equality + epoch/substitution/review fixtures, H3/H4 end-to-end probes, pitfall matrix, M1–M6 |
| 17 — bootstrap circularity; conductor-owned paths and durable receipts unregistered | §7 bootstrap envelope + activation criteria + §6 conductor roster + durable review home |

## §9b r2 fold ledger (11/11 folded 2026-07-16 under the AGENTS.md convergence law —
## every probeable arm is an executable RED in §5's V-series; none deferred, none dropped)

r2 also re-audited the r1 folds and confirmed only r1 #2 structurally complete; every
remaining r1 depth gap is carried by exactly one row below (no separate r1 re-tracking).

| r2 finding (paraphrased) | folded into | RED |
| --- | --- | --- |
| 1 — a record's actor field can bypass the seat table | §2.2 seat-binding law (actor == seats[role], derived principals, dispatched_by bound) | V1 |
| 2 — record lifecycle impossible/undefined (record-before-session, per-lane shapes, transitions, execution_kind) | §2.4 dispatch handshake + transition graph + per-lane completion shapes + execution_kind; §3.6 agreement | V2 |
| 3 — launcher fails open on non-2 exits; real hook-input schema unstated; harness-level hook disablement unaddressed | §4.1 normalized launcher (every failure → exit 2 + reason); §3.3 input schema; §4.4 (d) canary; §4.5 exact ceiling | V3, H6 |
| 4 — verb closure without effect closure (benign-remainder writes, unmapped git forms, orphan verbs) | §4.2 git default-deny + write-shaped law over ALL path classes + verb→effect tiling; design/audit_report effect surfaces | V4 |
| 5 — integration unbound to the checked assignment | §3.4 integrate-as-subcommand (fresh check-lane + patch-hash equality + allowed-paths recompute); §4.2 raw-integration refusal | V5 |
| 6 — review provenance forgeable; codex pin not implemented | §2.1 explicit argv pin; §3.5 structured stream + sidecar binding + lane_run_id echo; §3.4 (4) reviews-in-HEAD | V6 |
| 7 — ownership split breaks the role protocol; post-activation maintenance deadlock | §6 rework (REDs out of builder paths; packet-scoped enforcement exception; maintenance flow; wiring/rosters as registration data); §2.4 packet floor | V7 |
| 8 — seed byte-equality forbids lawful reslot; AGENTS.md hardcodes the seats | §5 R7 lawful-reslot carve-out; §6 AGENTS amendment (seats-as-data marker sentence) | V8 |
| 9 — event chain unverifiable; records unanchored before launch; bootstrap schema open; census not required at activation | §2.4 JSONL full snapshots + anchor law (HEAD prefix); §7 closed envelope + activation criterion (4) | V9 |
| 10 — supersession true at category level, not behaviorally | §7 per-lane behavioral pointers; §3.5 stand-in arm; §2.4 shapes | V10 (+V2/V3/V6) |
| 11 — two of the three open decisions are design-owned | §8 dispositions: F4 operator-owned with a default, F5 decided-excluded, F6 decided-default pinned | V11 (F6 pin); F4/F5 non-probeable |
