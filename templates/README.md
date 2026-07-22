# templates/ — projection templates

Governed by `contracts/repo_layout.json` (the ratified root-shape owner) and enforced by
`tests/contracts/test_org_rootwide.py` (the `test_org_rootwide` guard). This README teaches the
current law for the `templates/` family.

## Current members

- `README.md.tpl` — the source template the README projection is rendered from. The projected
  `README.md` is a checked projection (see the README-projection contract); edit the template,
  never the generated artifact.

Add a template and declare its home in the same slice.

## Retired law (do NOT reintroduce)

- The old `candidate_only` / `singleton`-enforcement teaching is superseded by the ratified
  root-shape-owner metadata on `contracts/repo_layout.json`.
- The killed lane's `proposals` category is retired and permanently barred.
