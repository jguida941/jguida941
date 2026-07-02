# AGENTS.md

## Role protocol (operator-ratified, 2026-07-02)

**Fable (Claude, main loop) owns the work**: reorientation, slice design (written to a scratch
design doc with open forks BEFORE any code), all implementation, diff review, gates, commits,
merges, pushes. Implementation follows the slice SOP below regardless of who types it.

**codex is the review authority only — never a builder**: three gate roles, each ending in a
machine-checkable verdict line —
- DESIGN gate before implementation (`DESIGN-VERDICT: APPROVE | REVISE` + numbered must-fixes),
- CODE gate on the finished diff (`VERDICT: approve | revise`),
- ADVERSARIAL gate attacking the proof surface (`ADVERSARIAL-VERDICT: ...`).
Findings fold RED-first; merge to main only on approve. When codex is unavailable, slices may land
on their branch with an independent Claude reviewer standing in, and every such diff is QUEUED
(scratch review-queue) for a retroactive codex adversarial pass before the next push to main.

Claude subagents (Opus-tier) are limited to read-only fan-outs: audits, research extraction,
independent review stand-ins. They never mutate the tree.

## The slice SOP

Admission (`python -m scripts.organization.bootstrap_red_ref "<task>" "<red_ref>"`) → RED observed
failing for the right reason → new files homed in the 3 registries same slice → every literal
doc-cited → implement → full suite green + mutation proof (a probe that flips nothing is vacuous)
→ receipts (below) → review gates → commit; docs updated in the same commit.

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
