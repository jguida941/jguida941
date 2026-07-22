#!/usr/bin/env python3
"""Ratchet-aware pinned-guard runner (org L1, CR-18).

Runs the pinned guard modules named on argv and fails ONLY on failures/errors whose test id is
not already banked in ``contracts/correction_baseline.json`` (subset law — the same grammar as
the failure ratchet). This lets the pre-commit hook pin ``test_doc_authority`` +
``test_structural_layout`` without blocking every commit on the five baseline-held
``test_structural_layout`` identities observed at the slice-0 tip.

Never runs full-suite auto-collection: only the explicitly named modules are loaded, so the
intentionally-RED ratchet set is never executed by the commit hook.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASELINE = ROOT / "contracts" / "correction_baseline.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _baseline_ids() -> set:
    """Failing test identities banked at slice-0 landing, normalised to unittest id form."""
    if not BASELINE.is_file():
        return set()
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    ids = set()
    for row in data.get("failing", []):
        rid = str(row.get("id", "")).replace("::", ".").strip()
        if rid:
            ids.add(rid)
    return ids


def run(modules: list) -> int:
    baseline = _baseline_ids()
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for module in modules:
        suite.addTests(loader.loadTestsFromName(module))
    result = unittest.TestResult()
    suite.run(result)
    offenders = []
    for test, _tb in list(result.failures) + list(result.errors):
        tid = test.id().replace("::", ".")
        if tid not in baseline:
            offenders.append(tid)
    if offenders:
        sys.stderr.write(
            "pinned-guard BLOCK — failures outside contracts/correction_baseline.json:\n")
        for offender in sorted(offenders):
            sys.stderr.write(f"  {offender}\n")
        return 1
    sys.stdout.write(
        "pinned guards OK — every failure is within the correction_baseline ratchet "
        f"({len(result.failures)} failures + {len(result.errors)} errors, all baseline-held)\n")
    return 0


def main(argv: list) -> int:
    modules = argv[1:]
    if not modules:
        sys.stderr.write("usage: run_pinned_guards.py <module> [<module> ...]\n")
        return 2
    return run(modules)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
