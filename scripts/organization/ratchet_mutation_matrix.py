"""Reproducible mutation matrix for the correction failure-ratchet (§13.2, F6).

The correction-ratchet suite claims "zero survivors across the named defenses".
This module makes that claim REPRODUCIBLE rather than asserted: it holds a data
table of named defenses in ``scripts/organization/correction_ratchet.py``, each
paired with a *neutralizing patch spec* — a literal search/replace applied to a
COPY of the module in a temp dir (never the real file). For each entry it:

  1. reads the real module source (read-only), applies the neutralization to an
     in-memory copy, and writes the mutant to a temp file;
  2. runs the focused suite ``tests.contracts.test_correction_ratchet`` against
     the mutant (loaded in a child process that shadows
     ``scripts.organization.correction_ratchet`` with the mutant while keeping the
     real ``__file__`` so live repo-root discovery still works);
  3. records kill/survive, the reddened test ids, and a sha256 of the child's run
     output.

A defense is KILLED when at least one test reddens under its neutralization and
SURVIVES when the whole suite still passes — a survivor means the defense is not
load-bearing. The runner is itself proven non-vacuous by a deliberately vacuous
entry (``vacuous_comment_noop``, a comment-only edit) that MUST survive.

Pure stdlib, no network. The witness JSON path is passed by argument (no fixed
output home). ``run_matrix`` / ``main`` exit nonzero if ANY selected entry
survives OR any patch spec fails to apply (a spec that no longer matches the
module is itself a failure — specs must track the code).

CLI::

    python3 -m scripts.organization.ratchet_mutation_matrix --out witness.json
    python3 -m scripts.organization.ratchet_mutation_matrix \
        --entries zero_tests_guard,executor_top_region --out witness.json
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

MODULE_DOTTED = "scripts.organization.ratchet_mutation_matrix"
TARGET_DOTTED = "scripts.organization.correction_ratchet"
TEST_MODULE = "tests.contracts.test_correction_ratchet"
RESULT_MARKER = "@@RATCHET_MATRIX_RESULT@@ "


def _repo_root():
    """The repo root that holds both ``scripts/`` and ``tests/``."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root (a dir holding both scripts/ and tests/) not found")


def _module_path(repo_root):
    return repo_root / "scripts" / "organization" / "correction_ratchet.py"


# --------------------------------------------------------------------------- #
# The named-defense table. Each entry neutralizes ONE guard by a literal
# search/replace that must match the current module verbatim; ``kills`` names the
# contract test whose right-reason failure proves the defense is load-bearing.
# --------------------------------------------------------------------------- #

_ENTRIES = [
    # -- run-honesty parsing / _check_run (Items 1 & 3) --------------------- #
    {
        "id": "zero_tests_guard",
        "kills": "test_ran_zero_rejected_even_when_all_modules_masked",
        "search": "    if ran == 0:\n",
        "replace": "    if False and ran == 0:\n",
    },
    {
        "id": "summary_count_anchor",
        "kills": "test_summary_count_comes_from_final_anchor",
        "search": "            summary_idx = i  # the LAST summary wins — count AND status anchor here\n",
        "replace": "            summary_idx = i if summary_idx is None else summary_idx  # neutralized: FIRST summary\n",
    },
    {
        "id": "status_after_summary",
        "kills": "test_status_before_summary_is_not_a_valid_terminal_status",
        "search": (
            "    tail = [ln for ln in lines[summary_idx + 1:] if ln.strip()]\n"
            "    status = None\n"
            "    if tail:\n"
            "        match = _STATUS_RE.match(tail[-1])\n"
            "        status = match.group(1) if match else None\n"
            "    return ran, status\n"
        ),
        "replace": (
            "    statuses = [_STATUS_RE.match(ln).group(1) for ln in lines if _STATUS_RE.match(ln)]\n"
            "    status = statuses[-1] if statuses else None\n"
            "    return ran, status\n"
        ),
    },
    {
        "id": "missing_status_guard",
        "kills": "test_missing_status_rejected_when_all_modules_execute",
        "search": "    if status is None:\n        raise RatchetRunError(\"no terminal OK/FAILED status line",
        "replace": "    if status is None and False:\n        raise RatchetRunError(\"no terminal OK/FAILED status line",
    },
    {
        "id": "rc_ok_disagree",
        "kills": "test_returncode_disagrees_with_ok_status_rejected",
        "search": "    if status == \"OK\" and returncode != 0:\n",
        "replace": "    if False and status == \"OK\" and returncode != 0:\n",
    },
    {
        "id": "rc_failed_disagree",
        "kills": "test_returncode_disagrees_with_failed_status_rejected",
        "search": "    if status == \"FAILED\" and returncode == 0:\n",
        "replace": "    if False and status == \"FAILED\" and returncode == 0:\n",
    },
    {
        "id": "undiscovered_module_guard",
        "kills": "test_check_run_isolates_zero_and_undiscovered",
        "search": "    if undiscovered:\n",
        "replace": "    if False and undiscovered:\n",
    },
    {
        "id": "executor_top_region",
        "kills": "test_embedded_ok_line_is_not_counted_as_module_discovery",
        "search": "        if _SEPARATOR_RE.match(line) or _SUMMARY_RE.match(line):\n            break\n",
        "replace": "        if False and (_SEPARATOR_RE.match(line) or _SUMMARY_RE.match(line)):\n            break\n",
    },
    {
        "id": "fq_ordinary_identity",
        "kills": "test_non_fully_qualified_identity_rejected_directly",
        "search": "        if not any(class_path == mod or class_path.startswith(mod + \".\") for mod in named):\n",
        "replace": "        if False and not any(class_path == mod or class_path.startswith(mod + \".\") for mod in named):\n",
    },
    {
        "id": "loader_fq_recovery",
        "kills": "test_failed_test_keys_fully_qualified_module",
        "search": "    if no_module:\n        return no_module\n",
        "replace": "    if False and no_module:\n        return no_module\n",
    },
    # -- the closed seven-id atomic extractor family ------------------------- #
    {
        "id": "extractor_src_home",
        "kills": "test_each_structural_extractor_yields_nonempty_atoms_on_a_fixture",
        "search": "def _extract_src_home(root):\n    return _extract_parity(root, \"source_layout\")\n",
        "replace": "def _extract_src_home(root):\n    return set()  # neutralized\n",
    },
    {
        "id": "extractor_test_home",
        "kills": "test_each_structural_extractor_yields_nonempty_atoms_on_a_fixture",
        "search": "def _extract_test_home(root):\n    return _extract_parity(root, \"test_layout\")\n",
        "replace": "def _extract_test_home(root):\n    return set()  # neutralized\n",
    },
    {
        "id": "extractor_guard",
        "kills": "test_each_structural_extractor_yields_nonempty_atoms_on_a_fixture",
        "search": (
            "def _extract_guard(root):\n"
            "    # The negative control's live assertion is the same source_layout parity\n"
            "    # (\"the real cover must be green now\").\n"
            "    return _extract_parity(root, \"source_layout\")\n"
        ),
        "replace": "def _extract_guard(root):\n    return set()  # neutralized\n",
    },
    {
        "id": "extractor_phantom",
        "kills": "test_each_structural_extractor_yields_nonempty_atoms_on_a_fixture",
        "search": "def _extract_phantom(root):\n    struct = _load_structural_sections(root)\n",
        "replace": "def _extract_phantom(root):\n    return set()  # neutralized\n    struct = _load_structural_sections(root)\n",
    },
    {
        "id": "extractor_placement",
        "kills": "test_each_structural_extractor_yields_nonempty_atoms_on_a_fixture",
        "search": "def _extract_placement(root):\n    struct = _load_structural_sections(root)\n",
        "replace": "def _extract_placement(root):\n    return set()  # neutralized\n    struct = _load_structural_sections(root)\n",
    },
    {
        "id": "extractor_declared_modules",
        "kills": "test_each_structural_extractor_yields_nonempty_atoms_on_a_fixture",
        "search": "def _extract_declared_modules_exist(root):\n    from scripts.organization.tests_layout_contract import module_home\n",
        "replace": "def _extract_declared_modules_exist(root):\n    return set()  # neutralized\n    from scripts.organization.tests_layout_contract import module_home\n",
    },
    {
        "id": "extractor_authority",
        "kills": "test_each_structural_extractor_yields_nonempty_atoms_on_a_fixture",
        "search": "def _extract_authority_axis(root):\n    from scripts.organization.tests_layout_contract import (\n",
        "replace": "def _extract_authority_axis(root):\n    return set()  # neutralized\n    from scripts.organization.tests_layout_contract import (\n",
    },
    # -- subset law / seed-parent refusal / projection ---------------------- #
    {
        "id": "subset_added_guard",
        "kills": "test_added_unit_reddens",
        "search": "    added = child - parent\n    if added:\n",
        "replace": "    added = child - parent\n    if False and added:\n",
    },
    {
        "id": "subset_shrink_classify",
        "kills": "test_strict_subset_shrunk",
        "search": "    return \"unchanged\" if child == parent else \"shrunk\"\n",
        "replace": "    return \"unchanged\"\n",
    },
    {
        "id": "refuse_seed_parent",
        "kills": "test_slice0_seed_is_refused_as_ratchet_parent",
        "search": "    if seed_shape(parent_ledger) == \"slice0-seed\":\n        raise RatchetViolation(\n            \"parent ledger is a slice-0 seed;",
        "replace": "    if False and seed_shape(parent_ledger) == \"slice0-seed\":\n        raise RatchetViolation(\n            \"parent ledger is a slice-0 seed;",
    },
    {
        "id": "projection_symmetry",
        "kills": "test_projection_is_invoked",
        "search": "    if problems:\n        raise RatchetViolation(\"observation projection mismatch; \" + \"; \".join(problems))\n",
        "replace": "    if False and problems:\n        raise RatchetViolation(\"observation projection mismatch; \" + \"; \".join(problems))\n",
    },
]

# The 21 named defenses whose neutralizations MUST be killed (zero survivors).
DEFENSE_IDS = [e["id"] for e in _ENTRIES]
assert len(DEFENSE_IDS) == 21, "expected exactly 21 named defenses, got %d" % len(DEFENSE_IDS)

# A deliberately vacuous entry that MUST survive — it proves the runner is
# non-vacuous (a no-op comment edit changes bytes but never behaviour). It is NOT
# part of the defense set and is only run when selected by id.
_SELF_TEST = [
    {
        "id": "vacuous_comment_noop",
        "kills": None,
        "expect_survive": True,
        "search": "        child_rows.setdefault(r.get(\"id\"), r)  # first wins; any dup already flagged\n",
        "replace": "        child_rows.setdefault(r.get(\"id\"), r)  # first-wins; any duplicate already flagged\n",
    },
]

ENTRIES = {e["id"]: e for e in _ENTRIES + _SELF_TEST}


# --------------------------------------------------------------------------- #
# Mutation application + child-process suite run
# --------------------------------------------------------------------------- #

def _apply(source, entry):
    """Return ``(mutated_source, applied)``. ``applied`` is True only when the
    search string is present AND the replacement actually changes the text."""
    search, replace = entry["search"], entry["replace"]
    if search not in source:
        return source, False
    mutated = source.replace(search, replace, 1)
    return mutated, mutated != source


def _parse_child(stdout):
    """Extract the last ``RESULT_MARKER`` JSON payload from child stdout."""
    payload = None
    for line in stdout.splitlines():
        if line.startswith(RESULT_MARKER):
            payload = json.loads(line[len(RESULT_MARKER):])
    return payload


def run_entry(entry_id, *, module_path=None, repo_root=None, test_module=None):
    """Neutralize one defense on a module COPY and run the focused suite against
    it in a child process. Returns a result dict."""
    repo_root = Path(repo_root) if repo_root else _repo_root()
    module_path = Path(module_path) if module_path else _module_path(repo_root)
    test_module = test_module or TEST_MODULE
    entry = ENTRIES[entry_id]

    source = module_path.read_text(encoding="utf-8")
    mutated, applied = _apply(source, entry)
    result = {
        "id": entry_id,
        "kills": entry.get("kills"),
        "applied": applied,
        "survived": None,
        "reddened": [],
        "output_sha256": "",
    }
    if not applied:
        return result

    tmp = Path(tempfile.mkdtemp(prefix="ratchet-mutant-"))
    try:
        mutant = tmp / "correction_ratchet_mutant.py"
        mutant.write_text(mutated, encoding="utf-8")

        env = dict(os.environ)
        env["RATCHET_MUTATION_MATRIX"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = os.pathsep.join(
            p for p in (str(repo_root), env.get("PYTHONPATH", "")) if p
        )
        proc = subprocess.run(
            [sys.executable, "-m", MODULE_DOTTED, "--child",
             str(mutant), test_module, str(module_path)],
            cwd=str(repo_root), env=env, capture_output=True, text=True,
        )
        combined = proc.stdout + proc.stderr
        result["output_sha256"] = hashlib.sha256(combined.encode("utf-8")).hexdigest()

        payload = _parse_child(proc.stdout)
        if payload is None:
            result["error"] = "no matrix result emitted (rc=%d); tail:\n%s" % (
                proc.returncode, combined[-2000:])
            return result
        reddened = list(payload.get("failures", [])) + list(payload.get("errors", []))
        result["reddened"] = reddened
        result["survived"] = len(reddened) == 0
        result["tests_run"] = payload.get("testsRun")
        result["skipped"] = payload.get("skipped")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return result


def run_matrix(entries=None, *, module_path=None, repo_root=None,
               test_module=None, out_path=None):
    """Run the selected entries (default: the 21 named defenses). Returns a report
    dict and, if ``out_path`` is given, writes it as a JSON witness table."""
    ids = list(entries) if entries else list(DEFENSE_IDS)
    unknown = [e for e in ids if e not in ENTRIES]
    if unknown:
        raise KeyError("unknown mutation entr%s: %s" % (
            "y" if len(unknown) == 1 else "ies", ", ".join(unknown)))

    results = [run_entry(e, module_path=module_path, repo_root=repo_root,
                         test_module=test_module) for e in ids]
    survivors = [r["id"] for r in results if r["survived"] is True]
    specs_failed = [r["id"] for r in results
                    if not r["applied"] or r["survived"] is None]
    report = {
        "target": TARGET_DOTTED,
        "test_module": TEST_MODULE,
        "total": len(results),
        "survivors": survivors,
        "specs_failed": specs_failed,
        "results": results,
    }
    if out_path is not None:
        Path(out_path).write_text(
            json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def _child_run(mutant_path, test_module, original_module_path):
    """Child mode: shadow ``scripts.organization.correction_ratchet`` with the
    mutant (keeping the real ``__file__`` so live repo-root discovery still
    works), run the focused suite, and emit a JSON result line."""
    import scripts  # noqa: F401
    import scripts.organization as organization

    src = Path(mutant_path).read_text(encoding="utf-8")
    mod = types.ModuleType(TARGET_DOTTED)
    mod.__file__ = original_module_path
    mod.__package__ = "scripts.organization"
    code = compile(src, original_module_path, "exec")
    sys.modules[TARGET_DOTTED] = mod
    setattr(organization, "correction_ratchet", mod)
    exec(code, mod.__dict__)

    suite = unittest.defaultTestLoader.loadTestsFromName(test_module)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)

    def ids(pairs):
        return [str(case) for case, _tb in pairs]

    payload = {
        "failures": ids(result.failures),
        "errors": ids(result.errors),
        "testsRun": result.testsRun,
        "skipped": len(getattr(result, "skipped", [])),
    }
    sys.stdout.write(RESULT_MARKER + json.dumps(payload) + "\n")
    sys.stdout.flush()
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--child":
        return _child_run(argv[1], argv[2], argv[3])

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--entries", help="comma-separated entry ids (default: all 21 defenses)")
    parser.add_argument("--out", help="path to write the JSON witness table")
    parser.add_argument("--module", help="override the module path under test")
    parser.add_argument("--repo-root", help="override the repo root")
    ns = parser.parse_args(argv)

    entries = ns.entries.split(",") if ns.entries else None
    report = run_matrix(entries=entries, module_path=ns.module,
                        repo_root=ns.repo_root, out_path=ns.out)

    for r in report["results"]:
        verdict = ("SURVIVED" if r["survived"] is True
                   else "KILLED" if r["survived"] is False else "ERROR")
        sys.stderr.write("%-32s %-9s %s\n" % (
            r["id"], verdict, (r["reddened"][0] if r["reddened"] else r.get("error", ""))))
    sys.stderr.write("survivors=%d specs_failed=%d of %d\n" % (
        len(report["survivors"]), len(report["specs_failed"]), report["total"]))

    ok = not report["survivors"] and not report["specs_failed"]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
