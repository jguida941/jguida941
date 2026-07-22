"""Scratch hygiene + fork-visibility preflight (org L1, CR-16 / design delta A4).

A LOCAL preflight — it is deliberately NOT wired into any contract test's pass/fail (running it
on ignored scratch content must never block a clean clone). It reports two families of finding
over the closed two-root scratch grammar declared in ``contracts/repo_layout.json``
``scratch_grammar``:

* grammar findings — a scratch path that is not under ``scratchpad/active/<lane>/<kind>/`` or
  ``scratchpad/archive/<YYYY-MM-DD>/<lane>/<kind>/``, or any NEW file under the frozen
  ``scratchpad/work/`` legacy root.
* fork-visibility findings — divergent content-kin: two paths whose basenames match after a
  producer prefix (``fable-`` / ``local-`` / ``codex-`` / ``opus-``) is stripped but whose bytes
  differ, and neither loser is named by a ``SUPERSEDED-BY.json`` supersession pointer. Identical
  digests across paths are LAWFUL multiplicity (determinism witnesses keep their multiplicity).

Exit status is advisory (0 clean / 1 findings) for local use only.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONTRACT = _REPO_ROOT / "contracts" / "repo_layout.json"

KIN_PRODUCER_PREFIXES = ("fable-", "local-", "codex-", "opus-")
_ARCHIVE_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SUPERSEDE_FILENAME = "SUPERSEDED-BY.json"


def _grammar(contract_path: Path | str | None = None) -> dict:
    path = Path(contract_path) if contract_path is not None else _CONTRACT
    return json.loads(path.read_text(encoding="utf-8")).get("scratch_grammar", {})


def kin_key(relpath: str) -> str:
    base = relpath.rsplit("/", 1)[-1]
    for pref in KIN_PRODUCER_PREFIXES:
        if base.startswith(pref):
            return base[len(pref):]
    return base


def fork_findings(path_digests: dict, supersessions: list) -> list:
    """Divergent-kin detection. ``path_digests``: {relpath: sha256}. ``supersessions``: list of
    {loser, winner} rows. Returns sorted ``divergent_kin:<key>`` findings."""
    superseded = {s.get("loser") for s in supersessions if isinstance(s, dict)}
    by_kin: dict = {}
    for p, d in path_digests.items():
        by_kin.setdefault(kin_key(p), []).append((p, d))
    findings = []
    for kin, entries in sorted(by_kin.items()):
        if len(entries) < 2:
            continue
        if len({d for _, d in entries}) == 1:
            continue
        survivors = [p for p, _ in entries if p not in superseded]
        if len(survivors) > 1:
            findings.append(f"divergent_kin:{kin}")
    return findings


def grammar_findings(scratch_paths: list, grammar: dict) -> list:
    active = grammar.get("active_root", "scratchpad/active")
    archive = grammar.get("archive_root", "scratchpad/archive")
    frozen = tuple(grammar.get("frozen_roots", ["scratchpad/work"]))
    findings = []
    for rel in sorted(scratch_paths):
        parts = rel.split("/")
        if any(rel == f or rel.startswith(f + "/") for f in frozen):
            findings.append(f"frozen_work_new_file:{rel}")
            continue
        if rel.startswith(active + "/"):
            # scratchpad/active/<lane>/<kind>/...
            if len(parts) < 5:
                findings.append(f"active_grammar:{rel}")
            continue
        if rel.startswith(archive + "/"):
            # scratchpad/archive/<YYYY-MM-DD>/<lane>/<kind>/...
            if len(parts) < 6 or not _ARCHIVE_DATE_RE.match(parts[2]):
                findings.append(f"archive_grammar:{rel}")
            continue
        findings.append(f"outside_scratch_grammar:{rel}")
    return findings


def _sweep(scratch_root: Path):
    paths, digests, supersessions = [], {}, []
    if not scratch_root.is_dir():
        return paths, digests, supersessions
    for p in sorted(scratch_root.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        rel = "scratchpad/" + str(p.relative_to(scratch_root))
        paths.append(rel)
        try:
            digests[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:
            continue
        if p.name == _SUPERSEDE_FILENAME:
            try:
                doc = json.loads(p.read_text(encoding="utf-8"))
                rows = doc if isinstance(doc, list) else [doc]
                for row in rows:
                    if isinstance(row, dict) and row.get("loser"):
                        supersessions.append(row)
            except (OSError, ValueError):
                pass
    return paths, digests, supersessions


def main(argv: list) -> int:
    grammar = _grammar()
    scratch_root = _REPO_ROOT / "scratchpad"
    paths, digests, supersessions = _sweep(scratch_root)
    findings = grammar_findings(paths, grammar) + fork_findings(digests, supersessions)
    if findings:
        sys.stdout.write("scratch preflight findings (advisory):\n")
        for f in findings:
            sys.stdout.write(f"  {f}\n")
        return 1
    sys.stdout.write("scratch preflight clean\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
