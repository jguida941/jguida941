"""R-W3-RATCHET-1 (w3c-0 design closure §13.2): the correction failure-ratchet.

Stdlib verifier for ``contracts/correction_baseline.json``. The ledger is the
exact failing/erroring set of the focused 17-module correction command at a
slice landing; across the w3-correction branch it may only SHRINK. This module
holds the mechanics AND the trusted runner that makes them binding; the contract
test ``tests/contracts/test_correction_ratchet.py`` exercises them hostilely.

A *failure unit* is the COMPLETE typed identity of one red thing:

  * ``("ordinary", test_id, fingerprint)`` — one fingerprint of a failing row;
  * ``("loader", module, fingerprint, unmask_rule)`` — one loader (import) mask,
    identity INCLUDING its unmask rule, so weakening the rule is a new unit;
  * ``("setupclass", cls, fingerprint, unmask_rule)`` — one ``setUpClass`` mask,
    likewise carrying its unmask rule.

Because the mask identity carries ``unmask_rule``, editing a mask's rule turns it
into a unit the parent never had — a subset check reddens rather than silently
accepting a loosened mask.

Totals semantics (§13.2, r13)
-----------------------------
``totals.unique_test_ids`` is the count of unique OBSERVED ids, which is one per
ordinary failing row PLUS one per loader mask PLUS one per ``setUpClass`` mask
(each mask is a real ``_FailedTest`` / ``setUpClass`` observation in the run).
For the slice-0 seed that is ``7 ordinary + 9 loader + 0 setupclass = 16`` — NOT
``len(failing)``. ``failures`` counts ``kind == "failure"`` rows; ``errors``
counts ``kind == "error"`` rows plus every loader and ``setUpClass`` mask.
:func:`_derived_totals` recomputes all three so a hand-edited total reddens.

Atomic-member fingerprints for the seven structural ids (§13.2)
---------------------------------------------------------------
For the aggregate structural assertions (``test_structural_layout`` /
``test_tests_layout_contract``) the fingerprint is NOT the truncated terminal
exception line — it is the sorted set of atomic ``category|side|member``
violations recomputed from the LIVE declared-versus-actual collections by the
closed seven-id map :data:`STRUCTURAL_EXTRACTOR_IDS` / :func:`structural_atoms`.
Adding or removing one declared home changes exactly one atom, so the add-only
subset check bites at member granularity; a mapped test that fails but yields no
atom falls back to the exception line, which is unledgered and therefore reddens.

Trusted runner — the honesty boundary (§13.2)
---------------------------------------------
The three ``verify_*`` functions are PURE dict functions: given a hand-built
``observed`` set they will bless it, so they are NOT the trust boundary on their
own. The binding entry point is :func:`run_and_verify`, and its ORDERING is
load-bearing — everything that can be checked without a run happens FIRST, so a
candidate can never make its own edited ``command`` execute before that command
has been verified. It (1) loads the candidate ledger, (2) loads the PARENT ledger
via ``git show <base_ref>:contracts/correction_baseline.json`` (the caller cannot
substitute a parent), (3) confirms the candidate's frozen structure — INCLUDING
the ``command`` scalar — with :func:`verify_frozen_structure` and the shrink-only
subset law with :func:`verify_subset_of_parent`, so a tampered command reddens
BEFORE anything runs, (4) RUNS the PARENT-pinned command (never the candidate's
unverified string) as a subprocess in the clean worktree and validates the run is
honest — a ``Ran N`` summary with ``N > 0``, a terminal ``OK``/``FAILED`` status,
a return code consistent with that status, that every named module was DISCOVERED
(executed at least one test or is a declared loader mask — a deleted or
unmask-to-zero-tests module is rejected, never silent progress), and that every
observed identity is fully qualified, then derives ``observed`` from that real
output (never hand-assembled), rewriting the seven structural ids to their atomic
members, and (5) invokes :func:`verify_observation_projection` INSEPARABLY with
step 3 — any raise across 3–5 aborts the whole verification.

Seed shape and the one-way bootstrap (§13.2)
--------------------------------------------
The on-disk ``contracts/correction_baseline.json`` committed at slice 0 is a
best-effort SEED, a shape distinct from a canonical ratchet ledger and never
silently normalised into one. :func:`seed_shape` recognises it as
``"slice0-seed"`` from its actual facts: its ``totals`` use the six-key seed
vocabulary :data:`_SEED_TOTALS_KEYS` (``{failures, errors, ordinary_failing_rows,
loader_masks, setupclass_masks, observed_identities}`` — there is NO
``unique_test_ids`` key on the seed), every failing row's ``fingerprint_mode`` is
``"seed-terminal-line"`` (the terminal exception line, not an atomic
``category|side|member`` set), its loader ``module`` keys are bare basenames
rather than fully qualified, and it carries an extra ``ratchet_status``
annotation key. Because a seed is not a canonical parent, the ``verify_*``
functions REFUSE a slice-0 seed as a ratchet parent. The one-way bootstrap
:func:`regenerate_canonical_seed` mints the canonical ledger from the seed and one
real honest run — fully-qualified loader keys, atomic-member fingerprints from
:func:`structural_atoms`, canonical ``{failures, errors, unique_test_ids}``
totals, ``ratchet_status`` dropped — while projecting the observed identities
onto the seed's set: an ADDED identity is refused (no new failure may be smuggled
in) while a legitimately MISSING one (a fixed test) shrinks out. It is valid only
at slice-1 landing. The public path-only :func:`bootstrap_canonical_from_seed`
runs the seed's own pinned command through the trusted runner so synthetic output
cannot mint canonical authority.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from collections import namedtuple
from pathlib import Path


class RatchetViolation(Exception):
    """Raised when a ledger breaks the shrink-only correction ratchet law."""


class RatchetRunError(RatchetViolation):
    """A dishonest or unusable RUN — zero discovery, tampered summary, bad
    return code, an undiscovered module, or an unretrievable parent ledger.

    Subclasses :class:`RatchetViolation` so callers that guard the ratchet with
    ``except RatchetViolation`` fail closed on a dishonest run as well.
    """


class ExtractorUnavailable(Exception):
    """The live declared-versus-actual collections for a structural id could not
    be recomputed (missing layout data / unimportable contract). The runner
    treats this as "no atom" and keeps the terminal line, which then reddens."""


# --------------------------------------------------------------------------- #
# JSON loading — duplicate keys are corruption, never tolerated
# --------------------------------------------------------------------------- #

def _reject_duplicate_keys(pairs):
    """``object_pairs_hook`` that refuses any duplicate key in a JSON object.

    A duplicate key is silent data loss under the default ``dict`` behaviour, so
    it is treated as a corrupt ledger rather than tolerated. The hook fires for
    every object in the document, so nested duplicates are rejected too.
    """
    obj: dict = {}
    for key, value in pairs:
        if key in obj:
            raise RatchetViolation(f"duplicate key in ledger JSON: {key!r}")
        obj[key] = value
    return obj


def _loads_no_dupes(text):
    """``json.loads`` that raises :class:`RatchetViolation` on ANY duplicate key.

    The single JSON entry point for this module; :func:`load_ledger` uses it so
    that a duplicated object key — at any nesting depth — is caught before the
    lossy ``dict`` collapse can hide a forged or corrupted ledger.
    """
    return json.loads(text, object_pairs_hook=_reject_duplicate_keys)


def load_ledger(path):
    """Parse the correction ledger, rejecting duplicate object keys (nested too).

    The parsed dict is returned verbatim; no normalisation or defaulting is done
    so that shape assertions see the ledger exactly as written on disk.
    """
    with open(Path(path), "r", encoding="utf-8") as handle:
        return _loads_no_dupes(handle.read())


def _sorted(items):
    """Deterministic, crash-proof ordering for tuples in error messages."""
    return sorted(items, key=str)


# --------------------------------------------------------------------------- #
# Failure units — COMPLETE typed identities
# --------------------------------------------------------------------------- #

def _ordinary_units(ledger):
    """``{("ordinary", id, fp)}`` over every fingerprint of every failing row."""
    return {
        ("ordinary", row["id"], fp)
        for row in ledger.get("failing", [])
        for fp in row.get("fingerprints", [])
    }


def _loader_units(ledger):
    """``{("loader", module, fp, unmask_rule)}`` — full loader-mask identities."""
    return {
        ("loader", m["module"], m["fingerprint"], m["unmask_rule"])
        for m in ledger.get("loader_masks", [])
    }


def _setupclass_units(ledger):
    """``{("setupclass", cls, fp, unmask_rule)}`` — full setUpClass-mask ids."""
    return {
        ("setupclass", m["class"], m["fingerprint"], m["unmask_rule"])
        for m in ledger.get("setupclass_masks", [])
    }


def failure_units(ledger):
    """The complete set of typed failure-unit tuples for ``ledger``.

    Ordinary ``("ordinary", id, fp)`` triples plus loader and ``setUpClass`` mask
    identities as ``("loader"/"setupclass", name, fp, unmask_rule)`` 4-tuples.
    The kind tag keeps the three namespaces from colliding; the trailing
    ``unmask_rule`` makes a rule edit a genuinely different unit.
    """
    return _ordinary_units(ledger) | _loader_units(ledger) | _setupclass_units(ledger)


# --------------------------------------------------------------------------- #
# Observation parsing — the ONLY sanctioned source of an observed set
# --------------------------------------------------------------------------- #

_HEADER_RE = re.compile(r"^(?:FAIL|ERROR):\s+(\S+)\s+\((.+)\)\s*$")
_SEPARATOR_RE = re.compile(r"^(?:=+|-+)\s*$")
_SUMMARY_RE = re.compile(r"^Ran\s+\d+\s+tests?\b")
_LOADER_PREFIX = "unittest.loader._FailedTest"
_FAILED_IMPORT_RE = re.compile(r"Failed to import test module:\s*(\S+)")
_NO_MODULE_RE = re.compile(r"No module named ['\"]([^'\"]+)['\"]")


def _loader_module_identity(lines, start, end, header_method, suffix):
    """FULLY-QUALIFIED module identity for one ``_FailedTest`` block.

    unittest renders the ``_FailedTest`` header with only the module's LAST
    component (``definitely_missing_module``), so keying off the header basename
    is ambiguous — two ``pkg.a.same`` / ``pkg.b.same`` modules would collide
    (§13.2 fully-qualified requirement; the r2 basename finding). The dotted
    identity is recovered from the block body instead:

      * ``Failed to import test module: <name>`` — unittest emits the FQ dotted
        name here for a module that EXISTS but fails to import; for a genuinely
        MISSING module it degrades to the bare basename;
      * ``ModuleNotFoundError: No module named '<dotted>'`` — carries the FQ
        module for the missing-module case.

    The fully-qualified candidate wins: the import line when it is already
    dotted, else the ``No module named`` dotted name, else the bare import line,
    else the 3.11+ header suffix, else the bare header method.
    """
    failed_import = None
    no_module = None
    for j in range(start + 1, end):
        line = lines[j]
        if _SUMMARY_RE.match(line):
            break
        if failed_import is None:
            hit = _FAILED_IMPORT_RE.search(line)
            if hit:
                failed_import = hit.group(1)
        hit = _NO_MODULE_RE.search(line)
        if hit:
            no_module = hit.group(1)
    if failed_import and "." in failed_import:
        return failed_import
    if no_module:
        return no_module
    if failed_import:
        return failed_import
    return suffix if suffix else header_method


def observe_from_unittest_output(text):
    """Parse real ``python -m unittest -v`` / ``discover`` output into an
    observed failure set.

    Returns ``{"ordinary": set[(id, fp)], "loader": set[(module, fp)],
    "setupclass": set[(cls, fp)]}``.

    Each ``FAIL:``/``ERROR:`` detail block contributes one observation:

      * an ordinary block ``FAIL: test_x (pkg.mod.Case)`` plus its final
        exception line becomes ``("pkg.mod.Case::test_x", "<exception line>")``;
      * an ``ERROR`` whose class path is ``unittest.loader._FailedTest[.<module>]``
        becomes a loader observation keyed by the FULLY-QUALIFIED module name
        recovered from the block body (:func:`_loader_module_identity`), never the
        ambiguous header basename, so ``u[0]`` is the dotted module;
      * an ``ERROR: setUpClass (pkg.mod.Case)`` becomes a setUpClass observation
        keyed by the class path.

    The unmask rule is a ledger-side policy annotation, not something a test run
    emits, so loader/setUpClass observations carry only ``(name, fingerprint)``.
    :func:`verify_observation_projection` matches masks on that pair; the rule
    itself is frozen by :func:`verify_subset_of_parent` /
    :func:`verify_frozen_structure`.

    This function exists so callers derive ``observed`` from a REAL run instead
    of hand-forging it (see the module docstring's honesty note).
    """
    lines = text.splitlines()
    header_idx = [i for i, ln in enumerate(lines) if _HEADER_RE.match(ln)]

    ordinary: set = set()
    loader: set = set()
    setupclass: set = set()

    for pos, start in enumerate(header_idx):
        match = _HEADER_RE.match(lines[start])
        method, class_path = match.group(1), match.group(2)

        # The block body runs until the next detail header (blocks are also
        # bounded by the trailing "Ran N tests" summary or end of text). The
        # fingerprint is the block's last non-blank, non-separator line — i.e.
        # the terminal exception line, skipping the "===="/"----" rules unittest
        # draws around each block.
        end = header_idx[pos + 1] if pos + 1 < len(header_idx) else len(lines)
        fingerprint = None
        for j in range(start + 1, end):
            line = lines[j]
            if _SUMMARY_RE.match(line):
                break
            if line.strip() == "" or _SEPARATOR_RE.match(line):
                continue
            fingerprint = line.rstrip()
        if fingerprint is None:
            continue

        if class_path == _LOADER_PREFIX or class_path.startswith(_LOADER_PREFIX + "."):
            suffix = class_path[len(_LOADER_PREFIX):].lstrip(".")
            module = _loader_module_identity(lines, start, end, method, suffix)
            loader.add((module, fingerprint))
        elif method == "setUpClass" or method.startswith("setUpClass"):
            setupclass.add((class_path, fingerprint))
        else:
            # Normalise the Python 3.11+ "(pkg.mod.Case.test_x)" form (method
            # duplicated inside the parens) back to the bare class path.
            if class_path.endswith("." + method):
                class_path = class_path[: -(len(method) + 1)]
            ordinary.add((f"{class_path}::{method}", fingerprint))

    return {"ordinary": ordinary, "loader": loader, "setupclass": setupclass}


# --------------------------------------------------------------------------- #
# Observation projection — ledger is the exact bidirectional image of a run
# --------------------------------------------------------------------------- #

def _pair(observed_tuple):
    """Normalise an observed tuple to its ``(name, fingerprint)`` match key.

    Ordinary observations are already ``(id, fp)``; loader/setUpClass tuples may
    carry a trailing ``unmask_rule`` (when assembled from the ledger) which is
    not part of the observation identity and is dropped here.
    """
    return (observed_tuple[0], observed_tuple[1])


def _ordinary_ledger_pairs(ledger):
    return [
        (row["id"], fp)
        for row in ledger.get("failing", [])
        for fp in row.get("fingerprints", [])
    ]


def _loader_ledger_pairs(ledger):
    return [(m["module"], m["fingerprint"]) for m in ledger.get("loader_masks", [])]


def _setupclass_ledger_pairs(ledger):
    return [(m["class"], m["fingerprint"]) for m in ledger.get("setupclass_masks", [])]


def _dedupe_or_raise(kind, pairs):
    """Collapse ``pairs`` to a set, but raise if a duplicate would be hidden.

    A duplicated ledger row or mask must not silently vanish into set
    membership; multiplicity is checked here so the projection stays honest.
    """
    seen: set = set()
    for pair in pairs:
        if pair in seen:
            raise RatchetViolation(
                f"{kind}: duplicate ledger entry would silently collapse: {pair!r}"
            )
        seen.add(pair)
    return seen


def verify_observation_projection(ledger, observed):
    """Assert the ledger is the EXACT bidirectional projection of ``observed``.

    ``observed`` is ``{"ordinary": set[(id, fp)], "loader": set[(module, fp)],
    "setupclass": set[(cls, fp)]}`` (mask tuples may carry a trailing
    ``unmask_rule`` which is ignored for matching). For each of the three
    namespaces every ledger entry must be observed AND every observed entry must
    be in the ledger. Any asymmetry — a masked module that unmasks to a red test
    outside the ledger, a ledgered failure that no longer reproduces, a stale
    mask — raises :class:`RatchetViolation`. A duplicated ledger row or mask
    raises rather than collapsing.

    ``observed`` MUST be produced by :func:`observe_from_unittest_output` from a
    real run; passing a hand-built set defeats the whole defense.
    """
    checks = (
        ("ordinary", _ordinary_ledger_pairs(ledger), observed.get("ordinary", ())),
        ("loader", _loader_ledger_pairs(ledger), observed.get("loader", ())),
        ("setupclass", _setupclass_ledger_pairs(ledger), observed.get("setupclass", ())),
    )
    problems = []
    for kind, ledger_pairs, observed_tuples in checks:
        ledgered = _dedupe_or_raise(kind, ledger_pairs)
        seen = {_pair(t) for t in observed_tuples}
        unobserved = ledgered - seen
        unledgered = seen - ledgered
        if unobserved:
            problems.append(f"{kind}: ledger entries not observed: {_sorted(unobserved)}")
        if unledgered:
            problems.append(f"{kind}: observed entries absent from ledger: {_sorted(unledgered)}")
    if problems:
        raise RatchetViolation("observation projection mismatch; " + "; ".join(problems))


# --------------------------------------------------------------------------- #
# Ledger shape — the slice-0 seed and the canonical ledger are DISTINCT shapes,
# never silently interconverted; the seed→canonical bootstrap is one-way (§13.2)
# --------------------------------------------------------------------------- #

# The declared slice-0 SEED totals vocabulary (six keys, NO ``unique_test_ids``).
# The on-disk ``contracts/correction_baseline.json`` is written to exactly this
# set and the module + test docstrings are documented around it. The CANONICAL
# totals key set is :data:`_TOTALS_KEYS` (``{failures, errors, unique_test_ids}``),
# declared with the frozen structure below.
_SEED_TOTALS_KEYS = frozenset(
    {"failures", "errors", "ordinary_failing_rows",
     "loader_masks", "setupclass_masks", "observed_identities"}
)

# The CLOSED top-level key set of a slice-0 seed ledger — exactly these eleven
# keys, no more and no less. An unknown top-level key on a seed is a smuggled
# annotation and refuses regeneration (:func:`_validate_seed_schema`).
_SEED_LEDGER_KEYS = frozenset(
    {"contract_id", "schema_version", "purpose", "observed_utc", "command",
     "measurement_context", "totals", "setupclass_masks", "loader_masks",
     "failing", "ratchet_status"}
)

# The ONE production-authority loader unmask rule. Regeneration canonicalizes
# every regenerated mask to this exact text (never the seed's nonconformant
# rule), so the minted rules carry the discovery / zero-test / stale-mask
# obligations. The contract test keeps a byte-identical copy; THIS constant is
# the authority the production code enforces.
CANONICAL_UNMASK_RULE = (
    "when this module becomes importable its loader mask MUST be removed in that "
    "same slice; discovery MUST yield at least the slice's bound RED test and every "
    "discovered test executes; any failure/error/setUpClass error/new fingerprint "
    "must already be in the ordinary ledger; importable-with-zero-tests, a stale "
    "mask, a changed loader fingerprint, or an unmasked red test all redden"
)


def seed_shape(ledger):
    """Classify a parsed ledger as ``"slice0-seed"``, ``"canonical"`` or
    ``"unknown"`` WITHOUT mutating or normalising it.

    Seed classification is ALL-OR-NOTHING. A slice-0 seed carries THREE distinct
    signals together: the six-key seed totals vocabulary
    (:data:`_SEED_TOTALS_KEYS`), a ``ratchet_status`` annotation key, and at least
    one ``fingerprint_mode == "seed-terminal-line"`` row. A canonical ledger
    carries NONE of the three and the three-key ``{failures, errors,
    unique_test_ids}`` totals (:data:`_TOTALS_KEYS`). A ledger carrying SOME but
    not ALL seed signals is ambiguous — a canonical ledger wearing one seed marker,
    or a half-built seed — and is never silently classified: it raises
    :class:`RatchetViolation` rather than being blessed as either shape.

    The two shapes are deliberately never collapsed into each other: the one-way
    bootstrap from seed to canonical is :func:`regenerate_canonical_seed` /
    :func:`bootstrap_canonical_from_seed`, valid only at slice-1 landing, and the
    ``verify_*`` ratchet functions refuse a seed as a parent.
    """
    totals = ledger.get("totals")
    totals_keys = frozenset(totals) if isinstance(totals, dict) else frozenset()
    signals = (
        totals_keys == _SEED_TOTALS_KEYS,
        "ratchet_status" in ledger,
        any(row.get("fingerprint_mode") == "seed-terminal-line"
            for row in ledger.get("failing", [])),
    )
    present = sum(signals)
    if present == len(signals):
        return "slice0-seed"
    if present == 0:
        return "canonical" if totals_keys == _TOTALS_KEYS else "unknown"
    raise RatchetViolation(
        "partial seed signals: a ledger must carry ALL slice-0 seed markers "
        "(six-key totals vocabulary, a ratchet_status annotation, and "
        "seed-terminal-line rows) or NONE — a partial set is neither a seed nor a "
        "canonical ledger and is refused rather than silently classified"
    )


def _refuse_seed_parent(parent_ledger):
    """Raise if ``parent_ledger`` is a slice-0 seed — a seed may never be a ratchet
    parent (the bootstrap is one-way, valid only at slice-1 landing)."""
    if seed_shape(parent_ledger) == "slice0-seed":
        raise RatchetViolation(
            "parent ledger is a slice-0 seed; the seed is not a ratchet parent "
            "(the bootstrap is one-way, valid only at slice-1 landing — mint the "
            "canonical parent with regenerate_canonical_seed first)"
        )


# --------------------------------------------------------------------------- #
# Subset law — the child's failure units may only shrink
# --------------------------------------------------------------------------- #

def verify_subset_of_parent(child_ledger, parent_ledger):
    """Assert child failure units are a subset of the parent's; classify shrink.

    Units are the COMPLETE identities from :func:`failure_units`, so a loosened
    ``unmask_rule`` is a child unit absent from the parent. Returns
    ``"unchanged"`` when the unit sets are identical and ``"shrunk"`` when the
    child is a strict subset. Any child unit not present in the parent — a new
    failure or an edited mask — raises :class:`RatchetViolation`. A slice-0 seed
    used as the parent is refused up front (the bootstrap is one-way).
    """
    _refuse_seed_parent(parent_ledger)
    child = failure_units(child_ledger)
    parent = failure_units(parent_ledger)
    added = child - parent
    if added:
        raise RatchetViolation(
            "child failure units are not a subset of the parent; "
            f"units added: {_sorted(added)}"
        )
    return "unchanged" if child == parent else "shrunk"


# --------------------------------------------------------------------------- #
# Frozen structure — everything except a shrink is immutable
# --------------------------------------------------------------------------- #

_SCALAR_FROZEN_KEYS = (
    "contract_id", "schema_version", "purpose",
    "observed_utc", "command", "measurement_context",
)
_ROW_KEYS = frozenset({"id", "kind", "fingerprint_mode", "subtest_vectors", "fingerprints"})
_LOADER_KEYS = frozenset({"module", "fingerprint", "unmask_rule"})
_SETUPCLASS_KEYS = frozenset({"class", "fingerprint", "unmask_rule"})
_TOTALS_KEYS = frozenset({"failures", "errors", "unique_test_ids"})


def _derived_totals(ledger):
    """Recompute ``totals`` from live rows and masks (never free-edited).

    ``failures`` counts ``kind == "failure"`` rows; ``errors`` counts
    ``kind == "error"`` rows PLUS every loader and ``setUpClass`` mask (each
    masked import/class error is an erroring unit); ``unique_test_ids`` is the
    count of unique OBSERVED ids — one per failing row PLUS one per loader mask
    PLUS one per ``setUpClass`` mask (each mask is a real ``_FailedTest`` /
    ``setUpClass`` observation in the run), i.e. ``16`` for the slice-0 seed
    (``7 + 9 + 0``), NOT ``len(failing)`` (§13.2 r13).
    """
    rows = ledger.get("failing", [])
    loader = ledger.get("loader_masks", [])
    setupclass = ledger.get("setupclass_masks", [])
    failures = sum(1 for r in rows if r.get("kind") == "failure")
    errors = (
        sum(1 for r in rows if r.get("kind") == "error")
        + len(loader)
        + len(setupclass)
    )
    unique_test_ids = len(rows) + len(loader) + len(setupclass)
    return {"failures": failures, "errors": errors, "unique_test_ids": unique_test_ids}


def _check_masks(field, keyset, name_key, child_ledger, parent_ledger):
    """Freeze a mask list: key sets fixed, no duplicates, only removals."""
    problems = []
    child_masks = child_ledger.get(field, [])
    parent_masks = parent_ledger.get(field, [])

    for mask in child_masks:
        if set(mask) != keyset:
            problems.append(
                f"{field} key set changed for {mask.get(name_key)!r} "
                f"(is {_sorted(set(mask))}, must be {_sorted(keyset)})"
            )

    seen: set = set()
    for mask in child_masks:
        identity = (mask.get(name_key), mask.get("fingerprint"), mask.get("unmask_rule"))
        if identity in seen:
            problems.append(f"duplicate {field}: {identity!r}")
        seen.add(identity)

    parent_identities = {
        (m.get(name_key), m.get("fingerprint"), m.get("unmask_rule")) for m in parent_masks
    }
    added = seen - parent_identities
    if added:
        problems.append(f"{field} added (only removal allowed): {_sorted(added)}")
    return problems


def verify_frozen_structure(child_ledger, parent_ledger):
    """Assert every non-removal structural invariant is frozen vs the parent.

    Removals (fewer rows, masks, or fingerprints) are the only permitted change.
    Any of the following raises :class:`RatchetViolation`:

      * the top-level key SET differs (a key was added, removed, or renamed);
      * any frozen top-level scalar changed — ``contract_id``, ``schema_version``,
        ``purpose``, ``observed_utc``, ``command``, or ``measurement_context``;
      * ``totals`` is not a dict with exactly ``{failures, errors,
        unique_test_ids}``, or any of those disagrees with the value DERIVED from
        the rows and masks (a forged ``unique_test_ids`` or a mis-counted total,
        including one that ignores ``setUpClass`` masks, is caught here);
      * a duplicate failing ``id`` or a duplicate mask;
      * a failing row whose key set is not exactly
        ``{id, kind, fingerprint_mode, subtest_vectors, fingerprints}``, or whose
        ``fingerprints`` list is empty;
      * a surviving id whose ``kind`` or ``fingerprint_mode`` changed, whose
        ``subtest_vectors`` INCREASED, or which gained a fingerprint;
      * a failing id or a loader/``setUpClass`` mask ADDED versus the parent, or a
        mask whose key set changed.

    Returns ``"frozen"`` when the child is a clean shrink of / identical to the
    parent. A slice-0 seed used as the parent is refused up front (the bootstrap
    is one-way).
    """
    _refuse_seed_parent(parent_ledger)
    problems = []

    # -- top-level key set frozen -------------------------------------------- #
    child_keys, parent_keys = set(child_ledger), set(parent_ledger)
    if child_keys != parent_keys:
        problems.append(
            f"top-level key set changed (added={_sorted(child_keys - parent_keys)}, "
            f"removed={_sorted(parent_keys - child_keys)})"
        )

    # -- frozen top-level scalar values -------------------------------------- #
    for key in _SCALAR_FROZEN_KEYS:
        if child_ledger.get(key) != parent_ledger.get(key):
            problems.append(f"top-level value changed: {key!r}")

    # -- failing rows: self-contained shape checks --------------------------- #
    child_rows_list = child_ledger.get("failing", [])
    ids = [r.get("id") for r in child_rows_list]
    if len(ids) != len(set(ids)):
        dups = _sorted({i for i in ids if ids.count(i) > 1})
        problems.append(f"duplicate failing id(s): {dups}")
    for row in child_rows_list:
        if set(row) != _ROW_KEYS:
            problems.append(
                f"failing row key set changed for {row.get('id')!r} "
                f"(is {_sorted(set(row))}, must be {_sorted(_ROW_KEYS)})"
            )
        if not row.get("fingerprints"):
            problems.append(f"empty fingerprints for row {row.get('id')!r}")

    # -- failing rows: parent-relative (only-shrink) checks ------------------ #
    parent_rows = {r["id"]: r for r in parent_ledger.get("failing", [])}
    child_rows: dict = {}
    for r in child_rows_list:
        child_rows.setdefault(r.get("id"), r)  # first wins; any dup already flagged

    new_ids = set(child_rows) - set(parent_rows)
    if new_ids:
        problems.append(f"failing rows added (only removal allowed): {_sorted(new_ids)}")

    for tid in set(child_rows) & set(parent_rows):
        child_row, parent_row = child_rows[tid], parent_rows[tid]
        if child_row.get("kind") != parent_row.get("kind"):
            problems.append(f"kind changed for {tid!r}")
        if child_row.get("fingerprint_mode") != parent_row.get("fingerprint_mode"):
            problems.append(f"fingerprint_mode changed for {tid!r}")
        if child_row.get("subtest_vectors", 0) > parent_row.get("subtest_vectors", 0):
            problems.append(f"subtest_vectors increased for {tid!r}")
        added_fps = set(child_row.get("fingerprints", ())) - set(parent_row.get("fingerprints", ()))
        if added_fps:
            problems.append(f"fingerprints added for {tid!r}: {_sorted(added_fps)}")

    # -- masks: key sets frozen, no duplicates, only removals ---------------- #
    problems += _check_masks("loader_masks", _LOADER_KEYS, "module", child_ledger, parent_ledger)
    problems += _check_masks("setupclass_masks", _SETUPCLASS_KEYS, "class", child_ledger, parent_ledger)

    # -- totals fully derived and checked ------------------------------------ #
    totals = child_ledger.get("totals")
    if not isinstance(totals, dict) or set(totals) != _TOTALS_KEYS:
        shown = _sorted(set(totals)) if isinstance(totals, dict) else totals
        problems.append(f"totals key set changed (is {shown}, must be {_sorted(_TOTALS_KEYS)})")
        totals = totals if isinstance(totals, dict) else {}
    derived = _derived_totals(child_ledger)
    for key in ("failures", "errors", "unique_test_ids"):
        if totals.get(key) != derived[key]:
            problems.append(f"totals.{key}={totals.get(key)} != derived {derived[key]}")

    if problems:
        raise RatchetViolation("frozen-structure violation; " + "; ".join(problems))
    return "frozen"


# --------------------------------------------------------------------------- #
# Atomic-member extractor — the closed seven-id map (§13.2)
#
# For the aggregate structural assertions the ledger fingerprint is the sorted
# set of atomic ``category|side|member`` violations, recomputed HERE from the
# LIVE declared-versus-actual collections (``contracts/repo_layout.json`` +
# disk + the tests-layout contract), never the truncated terminal exception
# line. Adding/removing one declared home flips exactly one atom, so the
# add-only subset check bites at member granularity.
# --------------------------------------------------------------------------- #

_ENUMERATED = ("source_layout", "test_layout")
_SL_ID = "tests.contracts.test_structural_layout.StructuralLayoutContract"
_TL_ID = "tests.contracts.test_tests_layout_contract.TestsLayoutContract"


def symmetric_atoms(category, left_label, left, right_label, right):
    """Atoms for a two-set parity: ``category|left_label|m`` for each member only
    on the left, ``category|right_label|m`` for each member only on the right."""
    left, right = set(left), set(right)
    return (
        {f"{category}|{left_label}|{m}" for m in left - right}
        | {f"{category}|{right_label}|{m}" for m in right - left}
    )


def _discover_repo_root():
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise ExtractorUnavailable("repo root (a dir holding both scripts/ and tests/) not found")


def _load_structural_sections(root):
    """The live ``structural_layout`` block (dup-key-safe load, same data the
    structural-layout guard reads)."""
    path = root / "contracts" / "repo_layout.json"
    return _loads_no_dupes(path.read_text(encoding="utf-8"))["structural_layout"]


def _sl_declared_homes(section):
    """Declared home path per governed file (mirrors the structural guard):
    root-allowlisted files keep their basename; group members live at
    ``<target_dir>/<member>`` when ``placement_enforced`` else flat."""
    enforced = bool(section.get("placement_enforced", False))
    homes = set(section.get("root_allowlist", []))
    for group in section.get("groups", []):
        for member in group["members"]:
            homes.add(f"{group['target_dir']}/{member}" if enforced else member)
    return homes


def _sl_actual_files(section, root):
    """On-disk governed files under a section root, home-relative (data dirs and
    subpackage ``__init__.py`` markers excluded, exactly as the guard does)."""
    section_root = root / section["root"]
    data_dirs = set(section.get("data_dirs", []))
    out = set()
    for path in section_root.glob(section["glob"]):
        if not path.is_file():
            continue
        rel = path.relative_to(section_root)
        if rel.parts and rel.parts[0] in data_dirs:
            continue
        if path.name == "__init__.py" and len(rel.parts) > 1:
            continue
        out.add(rel.as_posix())
    return out


def _sl_declared_basenames(section):
    declared = set(section.get("root_allowlist", []))
    for group in section.get("groups", []):
        declared.update(group["members"])
    return declared


def _extract_parity(root, section_name):
    section = _load_structural_sections(root)[section_name]
    declared = _sl_declared_homes(section)
    actual = _sl_actual_files(section, root)
    return symmetric_atoms(section_name, "missing", declared, "undeclared", actual)


def _extract_src_home(root):
    return _extract_parity(root, "source_layout")


def _extract_test_home(root):
    return _extract_parity(root, "test_layout")


def _extract_guard(root):
    # The negative control's live assertion is the same source_layout parity
    # ("the real cover must be green now").
    return _extract_parity(root, "source_layout")


def _extract_phantom(root):
    struct = _load_structural_sections(root)
    atoms = set()
    for name in _ENUMERATED:
        section = struct[name]
        section_root = root / section["root"]
        homes = [{"target_dir": "."}] + section.get("groups", [])
        for member in _sl_declared_basenames(section):
            found = any(
                (section_root / member).exists()
                or (section_root / g["target_dir"] / member).exists()
                for g in homes
            )
            if not found:
                atoms.add(f"{name}|phantom|{member}")
    return atoms


def _extract_placement(root):
    struct = _load_structural_sections(root)
    atoms = set()
    for name in _ENUMERATED:
        section = struct[name]
        section_root = root / section["root"]
        enforced = section["placement_enforced"]
        for group in section.get("groups", []):
            for member in group["members"]:
                home = (
                    section_root / group["target_dir"] / member
                    if enforced
                    else section_root / member
                )
                if not home.is_file():
                    atoms.add(f"{name}|misplaced|{member}")
    return atoms


def _extract_declared_modules_exist(root):
    from scripts.organization.tests_layout_contract import module_home

    tests_root = root / "tests"
    atoms = set()
    for fname, group in module_home().items():
        if not (tests_root / group / fname).is_file():
            atoms.add(f"tests_module_home|missing|tests/{group}/{fname}")
    return atoms


def _extract_authority_axis(root):
    from scripts.organization.tests_layout_contract import (
        DESIGN_CONTRACT_GROUPS,
        TEST_GROUPS,
        design_contract_authority,
    )

    contracts_files = set(dict((g.name, g.modules) for g in TEST_GROUPS)["contracts"])
    authority = design_contract_authority()
    authority_files = set(authority)
    atoms = symmetric_atoms(
        "authority_axis", "uncovered", contracts_files, "stale", authority_files
    )
    seen = set()
    for mods in DESIGN_CONTRACT_GROUPS.values():
        for member in mods:
            if member in seen:
                atoms.add(f"authority_axis|duplicate|{member}")
            seen.add(member)
    tests_contracts = root / "tests" / "contracts"
    for member in authority_files:
        if not (tests_contracts / member).is_file():
            atoms.add(f"authority_axis|missing_file|{member}")
    return atoms


# The CLOSED seven-id map. Keys are the EXACT fully-qualified failing ids of the
# slice-0 seed; a mapped test's fingerprint is the sorted set these produce.
STRUCTURAL_EXTRACTORS = {
    f"{_SL_ID}::test_declared_homes_have_no_phantom_members": _extract_phantom,
    f"{_SL_ID}::test_every_src_module_has_a_declared_home": _extract_src_home,
    f"{_SL_ID}::test_every_test_file_has_a_declared_home": _extract_test_home,
    f"{_SL_ID}::test_guard_fires_on_a_forged_or_misplaced_file": _extract_guard,
    f"{_SL_ID}::test_placement_enforced_groups_live_in_their_subdir": _extract_placement,
    f"{_TL_ID}::test_declared_modules_exist": _extract_declared_modules_exist,
    f"{_TL_ID}::test_design_contracts_grouped_by_authority": _extract_authority_axis,
}
STRUCTURAL_EXTRACTOR_IDS = frozenset(STRUCTURAL_EXTRACTORS)


def structural_atoms(test_id, repo_root=None):
    """Sorted-set atomic ``category|side|member`` violations for a mapped
    structural ``test_id``, recomputed from the LIVE collections.

    Returns ``None`` for an unmapped id (an ordinary test keeps its terminal
    fingerprint). Raises :class:`ExtractorUnavailable` if the live collections
    cannot be read — the runner then keeps the terminal line, which is
    unledgered and reddens (§13.2 "no atom ⇒ the exception line reddens").
    """
    fn = STRUCTURAL_EXTRACTORS.get(test_id)
    if fn is None:
        return None
    root = Path(repo_root) if repo_root is not None else _discover_repo_root()
    try:
        return set(fn(root))
    except ExtractorUnavailable:
        raise
    except Exception as exc:  # unreadable layout data / unimportable contract
        raise ExtractorUnavailable(f"{test_id}: {exc!r}") from exc


# --------------------------------------------------------------------------- #
# Trusted runner — runs the pinned command, validates honesty, verifies
# INSEPARABLY against the git-loaded parent (§13.2). This is the binding
# entry point; the pure verifiers above are not the trust boundary alone.
# --------------------------------------------------------------------------- #

RunResult = namedtuple("RunResult", ("output", "returncode"))

_RAN_RE = re.compile(r"^Ran\s+(\d+)\s+tests?\b", re.M)
_STATUS_RE = re.compile(r"^(OK|FAILED)\b")
_VERBOSE_RE = re.compile(r"^\S+ \(([\w.]+)\) \.\.\. ")


def _command_modules(command):
    """The fully-qualified test modules named after ``python -m unittest`` in the
    pinned command string (flags and the env prefix dropped)."""
    tokens = shlex.split(command)
    try:
        idx = tokens.index("unittest")
    except ValueError:
        raise RatchetRunError("pinned command is not a 'python -m unittest' invocation")
    modules = [t for t in tokens[idx + 1:] if not t.startswith("-") and "." in t]
    if not modules:
        raise RatchetRunError("pinned command names no fully-qualified test modules")
    return modules


_PYTHON_INTERP_RE = re.compile(r"^python(?:\d+(?:\.\d+)?)?$")


def _validate_pinned_command(command):
    """Refuse a pinned command the trusted runner would not actually execute.

    A canonical ledger may only be minted from a command that IS a real
    ``python -m unittest`` invocation: after dropping the leading ``VAR=value``
    env prefix, the executable word must be a python interpreter (``python``,
    ``python3``, ``python3.11`` …), and the command must name at least one
    fully-qualified test module. A forged interpreter (e.g. ``forged-python``)
    cannot be run by the trusted runner, so synthetic output under it cannot mint
    canonical authority — this is the seam that stops synthetic injection.
    """
    tokens = shlex.split(command, posix=True)
    idx = 0
    for token in tokens:
        if _ENV_ASSIGN_RE.match(token):
            idx += 1
        else:
            break
    argv = tokens[idx:]
    if not argv:
        raise RatchetRunError("pinned command has no executable after the env prefix")
    interpreter = os.path.basename(argv[0])
    if not _PYTHON_INTERP_RE.match(interpreter):
        raise RatchetViolation(
            f"pinned command interpreter {argv[0]!r} is not a python the trusted "
            "runner executes; synthetic authority (a command the real runner never "
            "ran) cannot mint a canonical ledger"
        )
    _command_modules(command)  # raises unless it is a '-m unittest' run naming modules


def _terminal_summary(output):
    """The run's test COUNT and completion STATUS, read from the SAME final
    ``Ran N tests`` summary block — one anchor, by construction, so the two can
    never disagree. Returns ``(ran, status)``:

      * ``ran`` is the count from the LAST ``Ran N tests`` line (the terminal
        summary), or ``None`` when the output carries no summary at all;
      * ``status`` is ``OK``/``FAILED`` ONLY when it is the final non-empty line
        AFTER that summary, in canonical unittest order; a status that appears
        BEFORE the summary, or a missing post-summary status, yields ``None``.

    Anchoring the COUNT on the LAST summary (never the first ``re.search`` match)
    is load-bearing: an early captured ``Ran 1 test`` line followed by a real
    terminal ``Ran 0 tests`` must report ``0`` and redden at the zero-tests
    guard, never slip past it as ``1``. Because both values come from
    ``summary_idx``, ``ran`` and ``status`` can never be read from two different
    blocks (the F8 first-vs-last-summary residual)."""
    lines = output.splitlines()
    summary_idx = None
    for i, line in enumerate(lines):
        if _SUMMARY_RE.match(line):
            summary_idx = i  # the LAST summary wins — count AND status anchor here
    if summary_idx is None:
        return None, None
    ran = int(_RAN_RE.match(lines[summary_idx]).group(1))
    tail = [ln for ln in lines[summary_idx + 1:] if ln.strip()]
    status = None
    if tail:
        match = _STATUS_RE.match(tail[-1])
        status = match.group(1) if match else None
    return ran, status


def _executed_modules(output, modules):
    """Named modules that produced at least one executed verbose test line, taken
    ONLY from the top streaming region — the lines BEFORE the first detail
    separator (``====`` / ``----``) or the ``Ran N`` summary. A verbose-shaped
    line printed INSIDE a later detail block is another test's captured output,
    not discovery evidence, so a forged ``smoke (pkg.mod.C) ... ok`` planted in a
    traceback can never forge discovery of a zero-test module."""
    seen = set()
    for line in output.splitlines():
        if _SEPARATOR_RE.match(line) or _SUMMARY_RE.match(line):
            break
        match = _VERBOSE_RE.match(line)
        if not match:
            continue
        class_path = match.group(1)
        for mod in modules:
            if class_path == mod or class_path.startswith(mod + "."):
                seen.add(mod)
    return seen


def _module_of_class(class_path):
    return class_path.rsplit(".", 1)[0] if "." in class_path else class_path


def _check_run(output, returncode, modules, observed_raw):
    """Assert the RUN itself is honest, returning ``(ran, status)``.

    Rejects: no ``Ran N`` summary; ``Ran 0`` (deleting tests / unmasking a
    zero-test module is not progress); no terminal status; a return code that
    disagrees with that status; a named module that was never DISCOVERED
    (neither executed a test nor is a declared loader/``setUpClass`` mask); and
    any observed identity that is not fully qualified under a named module.
    """
    ran, status = _terminal_summary(output)
    if ran is None:
        raise RatchetRunError("no 'Ran N tests' summary — the run crashed or its output was truncated")
    if ran == 0:
        raise RatchetRunError("zero tests ran — deleting tests or unmasking to zero tests is a dishonest shrink")
    if status is None:
        raise RatchetRunError("no terminal OK/FAILED status line — the run output is truncated or forged")

    problems = []
    if status == "OK" and returncode != 0:
        problems.append(f"terminal status OK but return code {returncode} (expected 0)")
    if status == "FAILED" and returncode == 0:
        problems.append("terminal status FAILED but return code 0 (expected nonzero)")

    executed = _executed_modules(output, modules)
    masked = {mod for mod, _fp in observed_raw["loader"]}
    masked |= {_module_of_class(cls) for cls, _fp in observed_raw["setupclass"]}
    undiscovered = [mod for mod in modules if mod not in executed and mod not in masked]
    if undiscovered:
        problems.append(f"named modules never discovered (zero tests and not masked): {sorted(undiscovered)}")

    named = set(modules)
    for tid, _fp in observed_raw["ordinary"]:
        class_path = tid.split("::", 1)[0]
        if not any(class_path == mod or class_path.startswith(mod + ".") for mod in named):
            problems.append(f"observed ordinary id not fully qualified under a named module: {tid!r}")
    for mod, _fp in observed_raw["loader"]:
        if mod not in named:
            problems.append(f"observed loader module is not a named fully-qualified module: {mod!r}")
    for cls, _fp in observed_raw["setupclass"]:
        if _module_of_class(cls) not in named:
            problems.append(f"observed setUpClass is not under a named module: {cls!r}")

    if problems:
        raise RatchetRunError("dishonest run; " + "; ".join(problems))
    return ran, status


def _apply_atomic_extractor(observed, atomic_extractor, repo_root):
    """Rewrite the seven structural ids' ordinary fingerprints to their atomic
    members; every other observation is passed through unchanged. A mapped id
    whose extractor yields no atom keeps its terminal line (which reddens)."""
    extract = atomic_extractor or (lambda tid: structural_atoms(tid, repo_root))
    ordinary = set()
    for tid, fp in observed["ordinary"]:
        if tid in STRUCTURAL_EXTRACTOR_IDS:
            try:
                atoms = extract(tid)
            except ExtractorUnavailable:
                atoms = None
            if atoms:
                for atom in atoms:
                    ordinary.add((tid, atom))
                continue
        ordinary.add((tid, fp))
    return {
        "ordinary": ordinary,
        "loader": set(observed["loader"]),
        "setupclass": set(observed["setupclass"]),
    }


_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def _split_env_prefix(command):
    """Split a frozen parent command into ``(env_overlay, argv)`` with NO shell.

    The command is tokenised with :func:`shlex.split` (POSIX). Leading
    ``VAR=value`` tokens — each a valid shell identifier followed by ``=`` — are
    lifted into an environment overlay ``{VAR: value}``; the FIRST token that is
    not such an assignment begins the command word, and no later token is treated
    as an assignment (matching shell env-prefix semantics). The remaining tokens
    are the argv executed with ``shell=False``. Because ``shlex`` never expands,
    a ``$(…)``/``$VAR``/``;`` metacharacter in a value or an argument is carried
    through LITERALLY."""
    tokens = shlex.split(command, posix=True)
    overlay = {}
    idx = 0
    for token in tokens:
        if _ENV_ASSIGN_RE.match(token):
            name, value = token.split("=", 1)
            overlay[name] = value
            idx += 1
        else:
            break
    return overlay, tokens[idx:]


def _closed_command_env(overlay):
    """A CLOSED, minimal, explicit execution environment for the pinned command.

    The child does NOT inherit ``os.environ``: a poisoned ``PYTHONPATH`` (an
    injected ``sitecustomize``), a ``PYTHONHOME``, or a ``PATH`` prepended with a
    hijacked interpreter must never reach the pinned command. The base is built
    from scratch — a ``PATH`` that resolves the interpreter to the running
    Python's own directory (with the standard system directories as a fallback)
    so the command still executes with the real interpreter, and nothing else.
    The command's OWN pinned ``VAR=value`` prefix is the only overlay applied on
    top; it is the single sanctioned way the frozen command influences its env.
    """
    base = {"PATH": os.path.dirname(sys.executable) + os.pathsep + os.defpath}
    base.update(overlay)
    return base


def _default_subprocess_runner(command, repo_root):
    """Run the PARENT-pinned command in ``repo_root`` with NO shell, capturing
    output.

    There is no shell between the frozen command and execution. The leading
    ``VAR=value`` tokens of the pinned command become an environment overlay via
    :func:`_split_env_prefix`; the remainder is the argv, executed with
    ``shell=False``. The child runs in a CLOSED constructed environment
    (:func:`_closed_command_env`) — ``os.environ`` is NOT inherited, so a poisoned
    ``PATH`` / ``PYTHONPATH`` / ``PYTHONHOME`` / ``sitecustomize`` cannot reach it —
    with the command's own pinned env prefix (e.g.
    ``PYTHONDONTWRITEBYTECODE=1 python -m unittest …``) as the only overlay.
    Because ``shlex`` never expands, a shell metacharacter that ever appears in an
    argument or an overlay value reaches the child LITERALLY rather than being
    interpreted.

    The string handed here is always the parent-pinned ``command`` (verified
    byte-equal to the parent by :func:`verify_frozen_structure` before this runs
    — never the candidate's unverified string), so behaviour is defined only for
    that frozen parent-pinned string; the trust boundary is unchanged."""
    overlay, argv = _split_env_prefix(command)
    if not argv:
        raise RatchetRunError("pinned command has no executable after the env prefix")
    env = _closed_command_env(overlay)
    proc = subprocess.run(
        argv, shell=False, cwd=str(repo_root), capture_output=True, text=True, env=env
    )
    return RunResult(output=(proc.stdout or "") + (proc.stderr or ""), returncode=proc.returncode)


def _sanitized_git_env():
    """A git environment that CANNOT be redirected to a forged repository.

    Every ``GIT_*`` selection variable (``GIT_DIR``, ``GIT_WORK_TREE``,
    ``GIT_COMMON_DIR``, ``GIT_INDEX_FILE``, ``GIT_OBJECT_DIRECTORY``,
    ``GIT_ALTERNATE_OBJECT_DIRECTORIES``, ``GIT_NAMESPACE``, and the
    ``GIT_CONFIG_COUNT`` / ``GIT_CONFIG_KEY_n`` / ``GIT_CONFIG_VALUE_n`` config
    vector) is stripped, and global/system config is disabled, so the parent
    lookup is bound to the repository discovered from ``repo_root`` alone. An
    ambient ``GIT_DIR`` pointing at an attacker's alternate repo can no longer
    substitute the parent ledger the ratchet loads (r5 finding F2)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    return env


def _default_git_show(base_ref, rel_path, repo_root):
    proc = subprocess.run(
        ["git", "show", f"{base_ref}:{rel_path}"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        env=_sanitized_git_env(),
    )
    if proc.returncode != 0:
        raise RatchetRunError(f"git show {base_ref}:{rel_path} failed: {(proc.stderr or '').strip()}")
    return proc.stdout


def run_and_verify(baseline_path, base_ref):
    """Public binding ratchet check — NO injection seams.

    Takes only ``baseline_path`` and ``base_ref``; it always uses the real
    subprocess runner, real ``git show`` and the live :func:`structural_atoms`, so
    the trusted boundary is not opt-out: a caller cannot substitute a synthetic
    run, a fake parent, or a fake extractor. Hermetic tests drive the module-private
    :func:`_run_and_verify_with` seam directly instead of the public function.
    """
    return _run_and_verify_with(baseline_path, base_ref=base_ref)


def _run_and_verify_with(baseline_path, *, base_ref, subprocess_runner=None, git_show=None, atomic_extractor=None):
    """The binding ratchet check: verify what can be checked BEFORE running, then
    RUN the parent-pinned command, validate honesty, and close projection.

    Ordering is load-bearing (§13.2): everything that can be settled without a run
    happens FIRST, so a candidate can never make its own edited ``command`` execute
    before that command has been verified against the parent.

    1. Load the candidate ledger (its pinned ``command`` is a frozen scalar).
    2. Load the PARENT ledger via ``git show <base_ref>:<rel path>`` — the caller
       supplies only ``base_ref``, never a parent object, so a candidate cannot be
       its own parent except by literally being unchanged at ``base_ref``.
    3. Confirm the candidate's frozen structure — INCLUDING the ``command`` scalar
       — with :func:`verify_frozen_structure`, and the shrink-only subset law with
       :func:`verify_subset_of_parent`. A tampered command differs from the
       parent's and reddens here, before anything runs.
    4. RUN the PARENT-pinned command (never the candidate's unverified string;
       after step 3 they are byte-equal) as a subprocess in the worktree root, then
       validate the run with :func:`_check_run` (``Ran N>0``, terminal status,
       return-code agreement, module discovery, fully-qualified identities) and
       derive ``observed`` from the REAL output, rewriting the seven structural ids
       to atomic members via the extractor.
    5. Invoke :func:`verify_observation_projection` — INSEPARABLE with step 3: any
       raise anywhere in 3–5 aborts the whole verification.

    Returns ``{ran, status, returncode, modules, ledger_change, frozen}`` on a
    clean pass. ``subprocess_runner`` / ``git_show`` / ``atomic_extractor`` are
    injectable for hermetic tests; the defaults are the real subprocess, real
    ``git show`` and the live :func:`structural_atoms`.
    """
    baseline_path = Path(baseline_path).resolve()
    repo_root = baseline_path.parent.parent
    rel_path = baseline_path.relative_to(repo_root).as_posix()

    candidate = load_ledger(baseline_path)
    command = candidate.get("command")
    if not isinstance(command, str) or not command.strip():
        raise RatchetRunError("candidate ledger has no pinned 'command' to run")

    # (2) Parent FIRST — provenance is git, never the caller.
    parent_text = git_show(base_ref, rel_path) if git_show else _default_git_show(base_ref, rel_path, repo_root)
    parent = _loads_no_dupes(parent_text)

    # A slice-0 seed is a VALID ratchet parent EXACTLY ONCE — here, on the public
    # verifier, to land the canonical ledger. (Everywhere else — the pure verify_*
    # functions — a seed is still refused as a parent.) The transition is validated
    # against the seed's OWN pinned command rather than the shrink-only subset law,
    # which does not apply across the one-way seed→canonical boundary.
    if seed_shape(parent) == "slice0-seed":
        return _verify_seed_transition(
            candidate, parent, repo_root,
            subprocess_runner=subprocess_runner, atomic_extractor=atomic_extractor)

    # (3) Freeze the candidate's structure (incl. the `command` scalar) and the
    #     subset law BEFORE any command runs. A tampered command reddens here.
    ledger_change = verify_subset_of_parent(candidate, parent)
    frozen = verify_frozen_structure(candidate, parent)

    # (4) The command that is EXECUTED is the PARENT-pinned command, never the
    #     candidate's. After (3) froze the scalar they are byte-equal; running the
    #     parent's makes the provenance explicit. The pinned command carries an env
    #     prefix (e.g. `PYTHONDONTWRITEBYTECODE=1 python -m unittest …`) which the
    #     runner lifts into a child-environment overlay and executes with
    #     shell=False (no shell between the frozen command and execution); the exact
    #     trusted string is pinned here.
    pinned_command = parent["command"]
    modules = _command_modules(pinned_command)

    run = subprocess_runner(pinned_command) if subprocess_runner else _default_subprocess_runner(pinned_command, repo_root)
    output, returncode = run.output, run.returncode

    observed_raw = observe_from_unittest_output(output)
    ran, status = _check_run(output, returncode, modules, observed_raw)
    observed = _apply_atomic_extractor(observed_raw, atomic_extractor, repo_root)

    # (5) Projection closes the loop — INSEPARABLE with (3).
    verify_observation_projection(candidate, observed)

    return {
        "ran": ran,
        "status": status,
        "returncode": returncode,
        "modules": modules,
        "ledger_change": ledger_change,
        "frozen": frozen,
    }


# --------------------------------------------------------------------------- #
# Seed → canonical bootstrap — one-way, valid only at slice-1 landing (§13.2)
# --------------------------------------------------------------------------- #

def _derived_seed_totals(seed):
    """Recompute the SIX-key seed totals vocabulary from the seed's own rows and
    masks, so a hand-edited seed total (a corrupt ``failures`` or
    ``observed_identities``) is caught before regeneration trusts the seed."""
    rows = seed.get("failing", [])
    loader = seed.get("loader_masks", [])
    setup = seed.get("setupclass_masks", [])
    return {
        "failures": sum(1 for r in rows if r.get("kind") == "failure"),
        "errors": sum(1 for r in rows if r.get("kind") == "error") + len(loader) + len(setup),
        "ordinary_failing_rows": len(rows),
        "loader_masks": len(loader),
        "setupclass_masks": len(setup),
        "observed_identities": len(rows) + len(loader) + len(setup),
    }


def _validate_seed_schema(seed):
    """Assert the seed schema is CLOSED and its totals are DERIVED, before it is
    ever used to mint a canonical ledger.

    An unknown top-level key (a smuggled annotation beyond the eleven declared
    seed keys :data:`_SEED_LEDGER_KEYS`) and a ``totals`` block that is not the
    six-key seed vocabulary or does not recompute from the seed's own rows/masks
    both raise :class:`RatchetViolation` — a seed the ratchet cannot trust may not
    become canonical authority."""
    unknown = set(seed) - _SEED_LEDGER_KEYS
    missing = _SEED_LEDGER_KEYS - set(seed)
    if unknown or missing:
        raise RatchetViolation(
            "seed schema is not closed "
            f"(unknown keys {_sorted(unknown)}, missing keys {_sorted(missing)})"
        )
    totals = seed.get("totals")
    if not isinstance(totals, dict) or frozenset(totals) != _SEED_TOTALS_KEYS:
        shown = _sorted(set(totals)) if isinstance(totals, dict) else totals
        raise RatchetViolation(
            f"seed totals must use the six-key seed vocabulary (is {shown})"
        )
    derived = _derived_seed_totals(seed)
    if totals != derived:
        raise RatchetViolation(
            f"seed totals are not derivable from its rows (declared {totals}, "
            f"derived {derived})"
        )


def _validate_seed_mask_rows(seed):
    """Validate ALL live seed loader-mask rows before regeneration: each must
    carry a non-empty ``unmask_rule``. A blanked or missing rule is a
    nonconformant mask the regeneration must not silently canonicalize over."""
    for mask in seed.get("loader_masks", []):
        rule = mask.get("unmask_rule")
        if not isinstance(rule, str) or not rule.strip():
            raise RatchetViolation(
                f"seed loader mask {mask.get('module')!r} carries no unmask rule; "
                "every live seed mask row must be validated before regeneration"
            )


def regenerate_canonical_seed(seed, run_result, atomic_extractor=None, *, repo_root=None):
    """Mint the CANONICAL ratchet ledger from the slice-0 SEED and one real run.

    The bootstrap is ONE-WAY and valid only at slice-1 landing. The seed is first
    validated: it must be a slice-0 seed, its schema must be CLOSED with totals
    recomputed from its rows (:func:`_validate_seed_schema`), its pinned command
    must be one the trusted runner actually executes
    (:func:`_validate_pinned_command` — synthetic authority under a forged
    interpreter is refused), and all its live loader-mask rows must be valid
    (:func:`_validate_seed_mask_rows`). Then, given a real honest ``run_result``,
    this returns the canonical ledger: fully-qualified loader keys,
    ``atomic-members`` fingerprints for the seven structural ids recomputed from
    the run via ``atomic_extractor``, canonical ``{failures, errors,
    unique_test_ids}`` totals, the ``ratchet_status`` annotation dropped, and every
    regenerated loader rule CANONICALIZED to :data:`CANONICAL_UNMASK_RULE` (never
    the seed's nonconformant text).

    Transition semantics against the seed's identity set:

      * an ADDED identity (observed but NOT in the seed — a new ordinary id, a new
        loader module, a new ``setUpClass``) raises :class:`RatchetViolation`: no
        new failure may be smuggled in during the conversion;
      * a MISSING identity (in the seed but legitimately NOT observed — the test
        was fixed) SHRINKS: its row/mask is dropped and the totals recompute.
    """
    if seed_shape(seed) != "slice0-seed":
        raise RatchetViolation("regenerate_canonical_seed requires a slice-0 seed as input")
    _validate_seed_schema(seed)
    _validate_pinned_command(seed["command"])
    _validate_seed_mask_rows(seed)

    output, returncode = run_result.output, run_result.returncode
    modules = _command_modules(seed["command"])
    observed_raw = observe_from_unittest_output(output)
    _check_run(output, returncode, modules, observed_raw)
    observed = _apply_atomic_extractor(observed_raw, atomic_extractor, repo_root)

    # Project onto the seed's identity set: an ADDED identity reddens (a smuggled
    # failure); a MISSING identity shrinks (a fixed test drops out).
    seed_ordinary = {row["id"] for row in seed.get("failing", [])}
    obs_ordinary = {tid for tid, _fp in observed["ordinary"]}
    seed_loader_bases = {m["module"].rsplit(".", 1)[-1] for m in seed.get("loader_masks", [])}
    obs_loader_fq = {mod for mod, _fp in observed["loader"]}
    obs_loader_bases = {mod.rsplit(".", 1)[-1] for mod in obs_loader_fq}
    seed_setup = {m["class"] for m in seed.get("setupclass_masks", [])}
    obs_setup = {cls for cls, _fp in observed["setupclass"]}

    added = (
        [("ordinary", i) for i in _sorted(obs_ordinary - seed_ordinary)]
        + [("loader", i) for i in _sorted(obs_loader_bases - seed_loader_bases)]
        + [("setupclass", i) for i in _sorted(obs_setup - seed_setup)]
    )
    if added:
        raise RatchetViolation(
            "regeneration would add identities absent from the seed set (smuggled "
            "failures): " + ", ".join(f"{kind}:{ident}" for kind, ident in added)
        )

    # Canonical failing rows: atomic-member fingerprints for each OBSERVED seed
    # row (a missing row shrinks out); seed kind + order preserved.
    atoms_by_id: dict = {}
    for tid, fp in observed["ordinary"]:
        atoms_by_id.setdefault(tid, set()).add(fp)
    failing = []
    for row in seed.get("failing", []):
        tid = row["id"]
        if tid not in obs_ordinary:
            continue  # legitimately fixed — SHRINK
        fingerprints = _sorted(atoms_by_id.get(tid, set()))
        if not fingerprints:
            raise RatchetViolation(f"no observed fingerprint for seed row {tid!r}")
        failing.append({
            "id": tid,
            "kind": row.get("kind", "failure"),
            "fingerprint_mode": "atomic-members",
            "subtest_vectors": row.get("subtest_vectors", 0),
            "fingerprints": fingerprints,
        })

    # Canonical loader masks: FQ module keys + observed fingerprint + the ONE
    # canonicalized production rule; an unobserved seed mask shrinks out.
    fq_by_base = {mod.rsplit(".", 1)[-1]: mod for mod in obs_loader_fq}
    obs_loader_fp = {mod: fp for mod, fp in observed["loader"]}
    loader_masks = []
    for m in seed.get("loader_masks", []):
        base = m["module"].rsplit(".", 1)[-1]
        if base not in fq_by_base:
            continue  # legitimately unmasked — SHRINK
        fq = fq_by_base[base]
        loader_masks.append({
            "module": fq,
            "fingerprint": obs_loader_fp[fq],
            "unmask_rule": CANONICAL_UNMASK_RULE,
        })

    setupclass_masks = [
        dict(m) for m in seed.get("setupclass_masks", []) if m.get("class") in obs_setup
    ]

    canonical = {
        "contract_id": seed["contract_id"],
        "schema_version": seed["schema_version"],
        "purpose": seed["purpose"],
        "observed_utc": seed["observed_utc"],
        "command": seed["command"],
        "measurement_context": seed["measurement_context"],
        "totals": {"failures": 0, "errors": 0, "unique_test_ids": 0},
        "setupclass_masks": setupclass_masks,
        "loader_masks": loader_masks,
        "failing": failing,
    }
    canonical["totals"] = _derived_totals(canonical)
    return canonical


def bootstrap_canonical_from_seed(baseline_path):
    """Public PATH-ONLY trusted bootstrap for the seed→canonical transition.

    Takes ONLY a filesystem path. It loads the committed seed bytes, executes the
    seed's OWN stored pinned command through the REAL subprocess runner in the
    repository root, and mints the canonical ledger with the LIVE atomic extractor
    — there is no ``run_result`` / ``atomic_extractor`` / ``output`` parameter, so
    a caller cannot inject a synthetic run to mint canonical authority. A seed
    whose pinned command the trusted runner would not execute (e.g. a forged
    interpreter) is refused (:func:`_validate_pinned_command`)."""
    baseline_path = Path(baseline_path).resolve()
    repo_root = baseline_path.parent.parent
    seed = load_ledger(baseline_path)
    if seed_shape(seed) != "slice0-seed":
        raise RatchetViolation(
            "bootstrap_canonical_from_seed requires the on-disk ledger to be a "
            "slice-0 seed"
        )
    pinned_command = seed["command"]
    _validate_pinned_command(pinned_command)
    run = _default_subprocess_runner(pinned_command, repo_root)
    return regenerate_canonical_seed(seed, run, None, repo_root=repo_root)


def _verify_transition_onto_seed(candidate, seed):
    """Assert the canonical CANDIDATE adds no identity absent from the SEED.

    The one-time seed→canonical transition may only SHRINK the seed's identity
    set (a fixed test drops out); a candidate carrying an ordinary id, loader
    module, or ``setUpClass`` the seed never had is a smuggled failure and raises
    :class:`RatchetViolation`."""
    seed_ordinary = {r["id"] for r in seed.get("failing", [])}
    cand_ordinary = {r["id"] for r in candidate.get("failing", [])}
    seed_loader = {m["module"].rsplit(".", 1)[-1] for m in seed.get("loader_masks", [])}
    cand_loader = {m["module"].rsplit(".", 1)[-1] for m in candidate.get("loader_masks", [])}
    seed_setup = {m["class"] for m in seed.get("setupclass_masks", [])}
    cand_setup = {m["class"] for m in candidate.get("setupclass_masks", [])}
    added = (
        (cand_ordinary - seed_ordinary)
        | (cand_loader - seed_loader)
        | (cand_setup - seed_setup)
    )
    if added:
        raise RatchetViolation(
            "seed→canonical transition would add identities absent from the seed: "
            f"{_sorted(added)}"
        )


def _verify_seed_transition(candidate, seed, repo_root, *, subprocess_runner=None, atomic_extractor=None):
    """Validate the ONE-TIME seed→canonical transition on the public verifier.

    The committed parent is a slice-0 seed and the working candidate is its
    canonical projection. This runs the SEED's own pinned command, confirms the
    run is honest, confirms the candidate is a canonical ledger that is the EXACT
    bidirectional image of that run, and confirms it adds nothing beyond the seed's
    identity set. Returns the ordinary result shape with
    ``ledger_change == "seed-bootstrap"``."""
    if seed_shape(candidate) != "canonical":
        raise RatchetViolation(
            "seed→canonical transition requires the candidate ledger to be in the "
            "canonical shape"
        )
    pinned_command = seed["command"]
    _validate_pinned_command(pinned_command)
    modules = _command_modules(pinned_command)
    run = subprocess_runner(pinned_command) if subprocess_runner else _default_subprocess_runner(pinned_command, repo_root)
    output, returncode = run.output, run.returncode
    observed_raw = observe_from_unittest_output(output)
    ran, status = _check_run(output, returncode, modules, observed_raw)
    observed = _apply_atomic_extractor(observed_raw, atomic_extractor, repo_root)

    verify_observation_projection(candidate, observed)
    _verify_transition_onto_seed(candidate, seed)

    return {
        "ran": ran,
        "status": status,
        "returncode": returncode,
        "modules": modules,
        "ledger_change": "seed-bootstrap",
        "frozen": "canonical",
    }
