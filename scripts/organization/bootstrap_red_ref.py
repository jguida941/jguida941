#!/usr/bin/env python3
"""P5-0c BOOTSTRAP-RED-REF gate — no mutation without a named RED reference.

The keystone of the organization-as-invariant rule: BEFORE adding/moving a file or any
mutation, a task must name a failing RED; a cleanup/reorg/SHAPE task's RED must itself be an
executable TARGET-SHAPE contract (this repo's is tests/contracts/test_structural_layout.py),
not just any RED. A read-only task may proceed (but is mutation-forbidden). Unknown intent
fails CLOSED (requires a RED).

This is the verdict-free GATHER half (ported from semantic-tdd scripts/check_bootstrap_red_ref.py,
`# lift=python_glue`): it classifies the task + RELAYS the same rule the sealed Rust
`MissingRedTestRef` authority (preflight.rs) decides. It DECIDES no new authority; the typed Rust
oracle is the named successor. The INVARIANT is repo-independent; only WHICH RED gets authored is
repo-specific. candidate_only.
"""
from __future__ import annotations

import json
import re
import sys

# Verbs that make a task MUTATION-CAPABLE (it will change files). Conservative: any hit -> mutation.
_MUTATION_VERBS = (
    "organize", "reorganize", "clean up", "cleanup", "reorg", "restructure", "consolidate",
    "move", "archive", "delete", "remove", "prune", "tidy", "rename", "refactor", "fold",
    "fix", "edit", "add", "build", "implement", "wire", "write", "create", "update", "migrate",
)
# A CLEANUP/REORG/SHAPE change needs an executable TARGET-SHAPE contract, not just any RED.
_SHAPE_VERBS = (
    "organize", "reorganize", "reorg", "restructure", "consolidate", "sprawl", "layout",
    "structure", "tidy", "clean up", "cleanup",
)
# Read-only intent (only honored when NO mutation verb is present — mutation always wins).
_READONLY_SIGNALS = ("read-only", "read only", "readonly", "analyze", "inventory", "audit", "investigate")
# A file-op reorg (move/rename/archive/delete a FILE) is the shape class applied to ORGANIZATION:
# it needs a shape RED only when a POSITIVE file-layout signal is present (path token / source-file
# extension / file-or-dir noun), WITHOUT false-blocking a code refactor that names no file.
_REORG_FILE_VERBS = frozenset((
    "move", "moves", "moving", "moved", "rename", "renames", "renaming", "renamed",
    "archive", "archives", "archiving", "archived", "delete", "deletes", "deleting", "deleted",
    "remove", "removes", "removing", "removed", "prune", "prunes", "pruning", "pruned",
    "relocate", "relocates", "relocating", "relocated",
))
_FILE_LAYOUT_NOUNS = frozenset((
    "file", "files", "directory", "directories", "folder", "folders", "subdir", "subdirs",
    "subdirectory", "subdirectories", "dir", "dirs", "module", "modules", "package", "packages",
    "script", "scripts", "doc", "docs", "documentation", "receipt", "receipts", "report",
    "reports", "fixture", "fixtures", "path", "paths", "test", "tests", "contract", "contracts",
))
_CODE_SYMBOL_TERMS = frozenset((
    "function", "functions", "method", "methods", "class", "classes", "logic", "variable",
    "variables", "import", "imports", "parameter", "parameters", "field", "fields", "constant", "constants",
))
_WORD_RE = re.compile(r"[a-z0-9]+")
_EXT_RE = re.compile(r"\.(py|rs|toml|md|json|txt|cfg|ini|yaml|yml|sh|ts|tsx|js|jsx|lock|rst|html|css)\b")

# A shape RED must be an executable target-shape contract — this repo's closed-cover layout guard.
SHAPE_CONTRACT_TOKENS = ("test_structural_layout", "structural_layout", "repo_layout")


def classify(task: str) -> dict:
    """task text -> {mutation_capable, kind, requires_shape_red, read_only}. Plain, conservative."""
    t = (task or "").lower()
    words = set(_WORD_RE.findall(t))
    has_reorg_file_verb = bool(words & _REORG_FILE_VERBS)
    has_mutation = has_reorg_file_verb or any(v in t for v in _MUTATION_VERBS)
    has_readonly = any(s in t for s in _READONLY_SIGNALS)
    is_shape = any(v in t for v in _SHAPE_VERBS)
    has_path = "/" in t
    has_ext = bool(_EXT_RE.search(t))
    has_file_noun = bool(words & _FILE_LAYOUT_NOUNS)
    has_file_layout_signal = has_path or has_ext or has_file_noun
    is_code_into_file_move = (
        has_reorg_file_verb and bool(words & _CODE_SYMBOL_TERMS)
        and has_ext and not has_path and not has_file_noun
    )
    reorg_needs_shape = has_reorg_file_verb and has_file_layout_signal and not is_code_into_file_move
    requires_shape_red = is_shape or reorg_needs_shape
    if has_mutation:
        return {"mutation_capable": True, "kind": "cleanup_reorg" if requires_shape_red else "code",
                "requires_shape_red": requires_shape_red, "read_only": False}
    if has_readonly:
        return {"mutation_capable": False, "kind": "read_only_analysis",
                "requires_shape_red": False, "read_only": True}
    return {"mutation_capable": True, "kind": "code", "requires_shape_red": False, "read_only": False}


def gate(task: str, red_ref: str | None = None) -> dict:
    """Verdict-free relay: classify the task + state whether a RED ref is sufficient. The sealed
    Rust MissingRedTestRef authority is the decider; this only gathers + relays the rule."""
    cls = classify(task)
    ref = (red_ref or "").strip()
    if not cls["mutation_capable"]:
        admit, reason = True, "read-only task: may proceed (mutation-forbidden)"
    elif not ref:
        admit, reason = False, "MUTATION with no named RED — name the failing RED first"
    elif cls["requires_shape_red"] and not any(tok in ref.lower() for tok in SHAPE_CONTRACT_TOKENS):
        admit, reason = False, ("SHAPE/reorg task: the RED must be an executable target-shape "
                                "contract (tests/contracts/test_structural_layout.py), not just any RED")
    else:
        admit, reason = True, "RED reference present and sufficient for the task kind"
    return {
        "contract_id": "BootstrapRedRefClaim",
        "authority_status": "candidate_only",
        "cannot_mark_done": True,
        "task_classification": cls,
        "red_ref": ref,
        "admit": admit,
        "reason": reason,
        "decider": "semantic-tdd preflight.rs :: MissingRedTestRef (this is the verdict-free gather/relay)",
    }


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    task = argv[0] if argv else ""
    red_ref = argv[1] if len(argv) > 1 else None
    verdict = gate(task, red_ref)
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["admit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
