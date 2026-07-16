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

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
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

OBSERVATION_CONTRACT = "BootstrapRedObservation"
OBSERVATION_SCHEMA_VERSION = 1
MAX_OUTPUT_BYTES = 65536
MAX_OBSERVATION_AGE = timedelta(hours=24)
_SCOPE_KEYS = ("routes", "profiles", "aspects")
_GENERIC_FAILURES = frozenset({"failed", "failure", "error", "assertionerror", "traceback"})


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


def _repo_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root).resolve()
    for parent in Path(__file__).resolve().parents:
        if (parent / "contracts" / "repo_layout.json").is_file():
            return parent
    raise RuntimeError("repository root not found")


def _current_revision(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def _red_path(red_ref: str, root: Path) -> Path:
    raw = (red_ref or "").strip()
    if not raw:
        raise ValueError("no named RED")
    if "::" in raw:
        raise ValueError("RED reference must be a Python test file; node selectors are not yet admitted")
    candidate = (root / raw).resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("RED reference escapes repository root") from exc
    if not candidate.is_file():
        raise ValueError(f"RED reference does not exist: {raw}")
    if candidate.suffix != ".py" or not relative.parts or relative.parts[0] != "tests":
        raise ValueError("RED reference must be an executable tests/**/*.py file")
    return candidate


def _test_command(red_ref: str) -> list[str]:
    module = red_ref[:-3].replace("/", ".") if red_ref.endswith(".py") else red_ref
    return [sys.executable, "-m", "unittest", "-v", module]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("observed_at_utc must be an RFC3339 UTC timestamp")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.tzinfo is None:
        raise ValueError("observed_at_utc must carry UTC")
    return parsed.astimezone(timezone.utc)


def _scope_reason(scope) -> str | None:
    if not isinstance(scope, dict) or set(scope) != set(_SCOPE_KEYS):
        return "observation scope must contain exactly routes, profiles, and aspects"
    for key in _SCOPE_KEYS:
        values = scope[key]
        if (not isinstance(values, list) or not values
                or any(not isinstance(value, str) or not value.strip() for value in values)
                or len(values) != len(set(values))):
            return f"observation scope.{key} must be a nonempty unique string list"
    return None


def build_observation(
    task: str,
    red_ref: str,
    *,
    expected_failure_fingerprint: str,
    scope: dict,
    exit_code: int,
    observed_output: str,
    root: str | Path | None = None,
    observed_at: datetime | None = None,
) -> dict:
    """Build the immutable claim from an already-observed test execution.

    Production callers should use :func:`observe_red`, which executes the canonical command. This
    constructor is public so the contract suite can mutation-test the validator without spawning a
    deliberately failing subprocess for every negative vector.
    """
    repo = _repo_root(root)
    path = _red_path(red_ref, repo)
    output = str(observed_output)
    if len(output.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise ValueError(f"RED output exceeds {MAX_OUTPUT_BYTES} bytes")
    moment = (observed_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return {
        "contract_id": OBSERVATION_CONTRACT,
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "authority_status": "candidate_only",
        "cannot_mark_done": True,
        "task": task,
        "task_sha256": _sha256(task.encode("utf-8")),
        "base_revision": _current_revision(repo),
        "red_ref": red_ref,
        "test_sha256": _sha256(path.read_bytes()),
        "command": _test_command(red_ref),
        "exit_code": exit_code,
        "expected_failure_fingerprint": expected_failure_fingerprint,
        "observed_output": output,
        "observed_output_sha256": _sha256(output.encode("utf-8")),
        "observed_at_utc": moment.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "scope": scope,
    }


def observe_red(
    task: str,
    red_ref: str,
    *,
    expected_failure_fingerprint: str,
    scope: dict,
    root: str | Path | None = None,
    timeout_seconds: int = 180,
) -> dict:
    """Execute the canonical RED command and bind its nonzero output to repository state."""
    repo = _repo_root(root)
    _red_path(red_ref, repo)
    completed = subprocess.run(
        _test_command(red_ref),
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout_seconds,
    )
    return build_observation(
        task,
        red_ref,
        expected_failure_fingerprint=expected_failure_fingerprint,
        scope=scope,
        exit_code=completed.returncode,
        observed_output=completed.stdout,
        root=repo,
    )


def _validate_observation(
    task: str,
    red_ref: str,
    observation: dict,
    root: Path,
    *,
    now: datetime | None = None,
) -> str | None:
    if not isinstance(observation, dict):
        return "missing executable RED observation"
    if observation.get("contract_id") != OBSERVATION_CONTRACT:
        return "wrong RED observation contract_id"
    if observation.get("schema_version") != OBSERVATION_SCHEMA_VERSION:
        return "wrong RED observation schema_version"
    if observation.get("authority_status") != "candidate_only" or observation.get("cannot_mark_done") is not True:
        return "RED observation overclaims authority"
    if observation.get("task") != task or observation.get("task_sha256") != _sha256(task.encode("utf-8")):
        return "RED observation task binding is stale"
    if observation.get("red_ref") != red_ref:
        return "RED observation names a different test"
    try:
        path = _red_path(red_ref, root)
    except ValueError as exc:
        return str(exc)
    if observation.get("test_sha256") != _sha256(path.read_bytes()):
        return "RED observation test hash is stale"
    try:
        revision = _current_revision(root)
    except (OSError, subprocess.SubprocessError):
        return "cannot resolve current Git revision"
    if observation.get("base_revision") != revision:
        return "RED observation base revision is stale"
    if observation.get("command") != _test_command(red_ref):
        return "RED observation command is not canonical"
    exit_code = observation.get("exit_code")
    if isinstance(exit_code, bool) or not isinstance(exit_code, int) or exit_code == 0:
        return "RED observation did not record a nonzero test exit"
    output = observation.get("observed_output")
    if not isinstance(output, str) or len(output.encode("utf-8")) > MAX_OUTPUT_BYTES:
        return "RED observation output is missing or unbounded"
    if observation.get("observed_output_sha256") != _sha256(output.encode("utf-8")):
        return "RED observation output hash is stale"
    fingerprint = observation.get("expected_failure_fingerprint")
    if (not isinstance(fingerprint, str) or len(fingerprint.strip()) < 12
            or fingerprint.strip().lower() in _GENERIC_FAILURES):
        return "expected failure fingerprint is missing or generic"
    if fingerprint not in output:
        return "observed failure does not contain the expected fingerprint"
    scope_error = _scope_reason(observation.get("scope"))
    if scope_error:
        return scope_error
    try:
        observed_at = _timestamp(observation.get("observed_at_utc"))
    except (TypeError, ValueError):
        return "RED observation timestamp is invalid"
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    age = current - observed_at
    if age < -timedelta(minutes=5) or age > MAX_OBSERVATION_AGE:
        return "RED observation timestamp is stale"
    return None


def gate(
    task: str,
    red_ref: str | None = None,
    observation: dict | None = None,
    *,
    root: str | Path | None = None,
) -> dict:
    """Fail-closed local admission: a mutation requires a real, current, right-reason RED."""
    cls = classify(task)
    ref = (red_ref or "").strip()
    repo = _repo_root(root)
    if not cls["mutation_capable"]:
        admit, reason = True, "read-only task: may proceed (mutation-forbidden)"
    elif not ref:
        admit, reason = False, "MUTATION with no named RED — name the failing RED first"
    else:
        try:
            _red_path(ref, repo)
        except ValueError as exc:
            admit, reason = False, str(exc)
        else:
            admit, reason = False, ""
    if (cls["mutation_capable"] and ref and not admit
            and reason == ""
            and cls["requires_shape_red"]
            and not any(tok in ref.lower() for tok in SHAPE_CONTRACT_TOKENS)):
        admit, reason = False, ("SHAPE/reorg task: the RED must be an executable target-shape "
                                "contract (tests/contracts/test_structural_layout.py), not just any RED")
    elif cls["mutation_capable"] and ref and not admit and reason == "":
        error = _validate_observation(task, ref, observation, repo)
        admit = error is None
        reason = error or "current nonzero RED observed for the expected reason and bound to scope"
    return {
        "contract_id": "BootstrapRedRefClaim",
        "authority_status": "candidate_only",
        "cannot_mark_done": True,
        "task_classification": cls,
        "red_ref": ref,
        "red_observation_sha256": (
            _sha256(json.dumps(observation, sort_keys=True, separators=(",", ":")).encode("utf-8"))
            if isinstance(observation, dict) else None
        ),
        "admit": admit,
        "reason": reason,
        "decider": "local BootstrapRedObservation validator",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task")
    parser.add_argument("red_ref", nargs="?", default="")
    parser.add_argument("--expect", default="", help="specific failure substring expected in RED output")
    parser.add_argument("--routes", default="", help="comma-separated affected route ids")
    parser.add_argument("--profiles", default="", help="comma-separated affected profile ids")
    parser.add_argument("--aspects", default="", help="comma-separated governed aspect ids")
    parser.add_argument("--write", default="", help="optional repository-relative observation JSON path")
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    observation = None
    cls = classify(args.task)
    if cls["mutation_capable"] and args.red_ref and args.expect:
        split = lambda value: [item.strip() for item in value.split(",") if item.strip()]
        scope = {
            "routes": split(args.routes),
            "profiles": split(args.profiles),
            "aspects": split(args.aspects),
        }
        try:
            observation = observe_red(
                args.task,
                args.red_ref,
                expected_failure_fingerprint=args.expect,
                scope=scope,
            )
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            observation = {"collection_error": str(exc)}
    verdict = gate(args.task, args.red_ref, observation)
    if args.write and verdict["admit"]:
        root = _repo_root()
        target = (root / args.write).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise SystemExit("--write path escapes repository root") from exc
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(observation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        verdict["observation_path"] = target.relative_to(root).as_posix()
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["admit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
