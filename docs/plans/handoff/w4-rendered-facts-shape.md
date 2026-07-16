# W4 - RENDERED FACTS semantic package shape (SHAPE gate input)

> **BLOCKED AS AN INDEPENDENT COMPLETION PATH (2026-07-14):** package structure and raw rendered
> facts cannot certify page composition. This slice must serve the binding W3 corrective gate and
> may not claim independent completion, merge, push, or publication while that gate remains `REVISE`.
> A bounded correction-branch dependency commit is permitted only after its own `AGENTS.md` slice/review gates.
> See the [Codex corrective audit](w3-visual-regression-correction.md#codex-corrective-audit--binding-gate-2026-07-14).

Historical pre-hardening observation (non-authorizing), 2026-07-13: `bootstrap_red_ref` returned
`admit: true` for task "restructure W4 rendered facts into semantic package", RED
`tests/contracts/test_structural_layout.py`. Before any new mutation, re-observe under the corrected
closed scope and persist the observation+claim admission envelope required by the W3 correction.

## Observed shape failure

`scripts/quality/headless_receipts.py` already held screenshot, mobile DOM, theme-continuity, and
theme-state machinery. Adding the W4 policy loader, reachable-state planner, browser program,
packet validator, provenance validator, and conformance bundle loader would push unrelated semantic
owners through one module. The operator rejects 1000-line guide/code files. W4 must establish its
package boundary before the new mechanism grows further.

## Target shape

`scripts/quality/rendered_facts/` is one semantic observation package. Its owners are deliberately
small and acyclic:

1. `doctrine.py` pins the complete policy digest; `policy.py` validates and resolves policy DATA;
   `state_authority.py` projects Studio states from `settings_admissibility.py::admissible_space()` and
   rejects any copied-policy mismatch.
2. `probe.py` renders the verdict-free browser program. `subject_identity.py` owns selector parsing,
   stable DOM identities, and subject membership.
3. `geometry.py`, `packet_types.py`, and `samples.py` validate finite geometry, closed packet leaves,
   and deterministic text-hit samples without importing browser or verdict code.
4. `inventory.py` closes the exact physical 24-packet/24-sidecar matrix. `codec.py` owns bounded
   canonical JSON/gzip; `provenance.py` validates artifact/runtime/Chrome provenance; `schema.py`
   coordinates packet, sidecar, state, and complete-bundle validation.
5. `producer.py` accepts the narrow `RenderedFactsRuntime` transport protocol, stages captures, and
   delegates validation. It never imports or calls `headless_receipts.py`.
6. `__init__.py` is a small public facade exporting only artifact/state-plan/validate/load/capture/
   write-all entry points.

`scripts/quality/headless_receipts.py` remains a compatibility orchestrator for this slice: its
rendered route lazily imports `probe.py`; rendered public names are <=3-line lazy delegates that pass
its local transport adapter into `producer.py`. No W4 module imports the facade, and no W4 browser
program/schema logic remains there. The existing W3 index-readiness calculation moves into `policy.py`;
the legacy private name becomes a lazy delegate, removing duplication and keeping schema independent.

W7 then completes the same rule for the legacy headless concerns: move common transport/provenance,
MF1 page capture, and theme/state capture into bounded `scripts/quality/headless/` modules, leaving
`headless_receipts.py` as a <=250-line compatibility facade. That broader move is gated by W7's
`system_graph_policy.toml`; W4 does not mix a risky rewrite of already-green W1-W3 evidence with the
new facts mechanism.

The four browser-fact decisions live behind `scripts/contracts/rendered_predicates.py`, a small
compatibility facade. Pure implementations are split under `scripts/contracts/rendered/`:
`contrast.py`, `density.py`, and `interaction.py` own laws; `common.py` owns visibility/geometry;
`effects.py` owns escape-paint containment; `paint.py` owns spatial paint-stack reasoning; and
`values.py` owns closed numeric/color parsing.
None imports filesystem, browser, renderer, or conformance code. `design_predicates.py` remains the
closed registry facade and imports only the four public functions.

## Shape authority and RED

- `contracts/repo_layout.json` declares exact `rendered-facts` and `rendered-predicates` source
  groups, per-module line caps, complete allowed internal-import graphs (including `__init__.py`),
  forbidden dependency prefixes, and narrow facade imports/exports.
- The legacy `scripts/organization/layout_contract.py` mirror is updated in the same slice because
  it remains live until W7 subsumes it: every module gets a `ModuleHome`, and
  `scripts/quality/rendered_facts/__init__.py` joins `PACKAGE_INIT_PATHS`. W7 proves the canonical TOML
  graph and deletes this duplicate.
- `tests/contracts/test_rendered_facts.py`, `test_rendered_fact_adversarial.py`, and the focused
  `test_rendered_fact_density_adversarial.py` / `test_rendered_fact_paint_adversarial.py` lanes
  remain in the contracts group/authority registry.
- RED order: declare the package members first; `test_structural_layout.py` fails because the exact
  files are absent. Land the package and remove W4 bodies from the monolith; the shape RED greens.
- `test_rendered_facts.py` reads the group policy from `repo_layout.json`; an import-boundary mutation
  or line-cap mutation reds without hard-coding a second package map. Behavioral schema/predicate tests
  stay in focused classes and split into another homed test before this file approaches its own cap.
  W7 owns the final facade cap for legacy headless code.

## Dependency graph

```text
contracts/rendered_fact_policy.json
        -> doctrine.py -> policy.py -> state_authority.py -> settings_admissibility.py
probe.py -> policy.py + subject_identity.py
packet_types.py -> geometry.py
inventory.py -> policy.py
provenance.py -> codec.py + policy.py
schema.py -> codec.py + geometry.py + inventory.py + packet_types.py + policy.py
             + provenance.py + samples.py + subject_identity.py
producer.py -> policy.py + probe.py + schema.py
headless_receipts facade/transport -> producer.py + probe.py (lazy only)
design_invariants.py        -> rendered_facts.schema.load_bundle
design_predicates.py        -> rendered_predicates.py facade
rendered_predicates.py      -> rendered/{contrast,density,interaction}.py
paint.py                    -> rendered/{common,effects,values}.py
```

No module imports `design_invariants` or `design_predicates`; observation cannot depend on a conformance
verdict. `state_authority.py` has one explicit reachability dependency on the pre-existing admissibility
decision source and returns only the closed state projection.

## Verification

Structural RED/green, module-size/import-boundary mutations, W4 packet/predicate mutations, full
pytest, real Chrome matrix, MF1 refresh for CSS changes, and independent CODE/ADVERSARIAL gates.
