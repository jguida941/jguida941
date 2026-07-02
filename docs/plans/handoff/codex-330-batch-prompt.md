Retroactive dual review (CODE + ADVERSARIAL in one pass, per AGENTS.md — codex was unavailable;
interim Claude stand-ins reviewed; you are the authority now). Repo: /Users/jguida941/dev/jguida941,
branch d-shell-1 (NOT yet merged to main — your approve gates the merge).

Review the QUEUED diffs in this dir, in order (later supersedes earlier where they overlap):
1. review-queue-d-shell-1.diff — D-SHELL-1 as first committed (747d54cd).
2. review-queue-d-shell-1b.diff — cumulative after the stand-in review folds (c6c5f3bf): iframe-at-390
   probe with fail-closed measured-width, page_sha256 byte-pinned receipts, .table-scroll wrappers
   (a11y), aspect_coverage value cross-check.
3. review-queue-d-shell-2*.diff if present — the manifest/grouping slice (its own design gate record
   is scratchpad codex-dshell0*-out.txt + the stand-in outputs; read d-shell-0-design.md +
   d-shell-2-design.md for the ratified laws).

Context docs in this dir: d-shell-0-design.md (ratified, with MF1-4 addendum), d-shell-1-build-brief.md,
d-shell-2-design.md. The stand-in review already found + we folded: the 500px-viewport overclaim,
unpinned receipts, display:block a11y loss, unverified coverage labels — attack the FOLDS for new
holes (e.g. iframe probe: scrolling="no" masking overflow? sha pinning: anything unpinned that
matters — Chrome version drift? tokens? the coverage cross-check: any remaining flip path?).
Then attack anything the stand-ins missed entirely. Run the suite + any spot mutations you want
(read-only sandbox: report the commands for me to run if you cannot).

Output: numbered findings with file:line + severity, then BOTH machine-checkable lines:
VERDICT: approve | revise
ADVERSARIAL-VERDICT: clean | holes-found
Merge to main happens only on approve+clean.
