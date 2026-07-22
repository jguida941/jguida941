# dev/ — development evidence homes

Governed by `contracts/repo_layout.json` (the ratified root-shape owner) and enforced by
`tests/contracts/test_org_rootwide.py` (the `test_org_rootwide` guard). The guard LAW carries
zero repo literals; this tree is the per-repo evidence surface it governs.

## `dev/reports/` — the closed FIVE evidence categories

Each category home carries a typed `manifest.json` (the artifact bijection) plus this family
guide. Homes land EMPTY at org L1 (zero artifact rows); durable evidence is routed in later
through the data-driven birth router (`scripts/organization/birth_router.py`), never dropped by
hand.

- `design_reviews/` — final independent Codex design / code / adversarial gate verdicts.
- `admissions/` — admission envelopes, ratifications, operator records.
- `worker_reviews/` — worker self-verifications, audits, dossiers.
- `archive/` — subject-scoped frozen evidence trees kept for provenance (e.g. a demo tree).
- `role_assignments/` — reserved for W7 role-assignment records (empty until W7 activates).

Every populated manifest row is fully typed (path, sha256, schema_id, schema_version, subject,
producer, produced_utc, retention_class, referenced_by) and is checked against the real tree:
the artifact must exist, be tracked, recompute its digest, and be cited by a real tracked doc.
Permanent-retention rows land finalized (sealed) with digest-bearing back-references.

## Retired law (do NOT reintroduce)

- The killed lane's `proposals` category is retired and permanently barred from re-entry.
- The old `candidate_only` / `singleton`-enforcement teaching is superseded by the
  ratified root-shape-owner metadata on `contracts/repo_layout.json`.
