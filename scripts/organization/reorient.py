"""Reorient composer: orientation-as-a-service (W8-O rev 3 design as code).

Derives a live-tree orientation board from git ground truth plus a CLOSED,
policy-declared roster of lane records (``contracts/reorient_policy.toml``), and a
freshness receipt binding every input. The composer OWNS NO TRUTH: every field is a
projection of record bytes, policy data, or git observation; any input drift
invalidates the receipt. No timers exist anywhere (operator decision 2026-07-16).

CLI contract::

    python3 -m scripts.organization.reorient --repo <path> [--now <iso8601Z>] check
    python3 -m scripts.organization.reorient --repo <path> verify

Exit codes: 0 PASS; 2 policy violation / missing declared input (writes nothing);
3 STALE (verify; writes nothing); 4 concurrent drift between the two observation
passes (writes nothing); 1 operational failure (git observation / interrupted write).

Reviewed seam surface (design section 8; the RED patches these by name):
- ``main(argv) -> int`` -- importable entry point; the CLI wraps it.
- ``_records_manifest(repo_root, policy)`` -- one observation pass over the record
  axis; ``check`` calls it once per pass (pass A and pass B) and refuses on drift.
- Pair writes go through ``os.replace``: board.json FIRST, board.receipt.json LAST
  (the receipt rename is the commit point; a torn pair is always detectable).

Outputs (success path only): ``scratchpad/active/reorient/board/board.json`` and
``scratchpad/active/reorient/board/board.receipt.json`` under ``--repo``. ``verify``
recomputes the entire projection from live inputs and never writes.

Git observation is hermetic: inherited ``GIT_*`` is stripped; config/attributes are
neutralized; ``GIT_OPTIONAL_LOCKS=0`` plus the GLOBAL ``--no-optional-locks`` flag
position keep generation byte-read-only over ``.git`` (including the index).

The repository root is ALWAYS the ``--repo`` parameter -- never a hardcoded path
(portability law).
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

try:  # the landed slice-0 mechanism: stdlib tomllib on 3.11+, tomli before
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - platform-dependent import path
    import tomli as tomllib

# --- F3 purity seam (codex r1 finding 3; probe M20 removes it) -------------------
# The DOCUMENTED CLI is `python3 -m scripts.organization.reorient ...` with no -B
# and no env override, and it must leave the checkout exactly as it found it. That
# bootstrap writes bytecode caches for this module's own import chain
# (scripts/__init__, scripts/organization/__init__, this file) into the checkout
# BEFORE any tool code runs. Those caches are regenerable interpreter artifacts,
# never tool outputs: on the CLI path the tool suppresses every further bytecode
# write and removes the caches its own bootstrap just wrote (then prunes the
# cache directories it emptied), so generation stays pure without a -B crutch.
if __name__ == "__main__" and not sys.dont_write_bytecode:
    import importlib.util

    sys.dont_write_bytecode = True
    _self_source = os.path.abspath(__file__)
    _bootstrap_caches = []
    for _source in (
        _self_source,
        os.path.join(os.path.dirname(_self_source), "__init__.py"),
        os.path.join(os.path.dirname(os.path.dirname(_self_source)), "__init__.py"),
    ):
        try:
            _bootstrap_caches.append(importlib.util.cache_from_source(_source))
        except NotImplementedError:  # pragma: no cover - interpreter without a cache tag
            pass
    for _cache in _bootstrap_caches:
        try:
            os.unlink(_cache)
        except OSError:
            pass
    for _cache_dir in sorted({os.path.dirname(_cache) for _cache in _bootstrap_caches}):
        try:
            os.rmdir(_cache_dir)
        except OSError:
            pass

POLICY_REL = "contracts/reorient_policy.toml"
TOOL_REL = "scripts/organization/reorient.py"
OUTPUT_DIR_REL = "scratchpad/active/reorient/board"
BOARD_REL = OUTPUT_DIR_REL + "/board.json"
RECEIPT_REL = OUTPUT_DIR_REL + "/board.receipt.json"

_SELF_PATH = Path(os.path.abspath(__file__))

_TOP_KEYS = {
    "contract_id", "schema_version", "board_schema_version", "receipt_schema_version",
    "discipline", "job_states", "verdict_grammar", "census", "lane",
}
_DISCIPLINE_KEYS = {
    "read_only_snapshots", "no_self_fold", "conductor_only_integration",
    "receipt_interrupt_triggers", "unverified_scout", "one_writer_per_lane",
    "fan_out_ceiling", "exact_key_caching", "discipline_enforced",
}
_DISCIPLINE_BOOL_KEYS = (
    "read_only_snapshots", "no_self_fold", "conductor_only_integration",
    "unverified_scout", "one_writer_per_lane", "exact_key_caching",
)
_LANE_KEYS = {"id", "priority", "charter", "records"}
_CHARTERS = {"ACTIVE", "QUEUED", "PARKED", "LANDED", "RECORD"}
# The CLOSED job-state vocabulary (design section 4): reviewed data, not a shape —
# any five unique strings is NOT a policy (codex r1 finding 6, probe M23a).
_JOB_STATES = ["PASS", "FAIL", "INFRA_BLOCKED", "CANCELLED", "STALE"]
_GRAMMAR_PATTERN_COUNT = 4


class _PolicyError(ValueError):
    """A policy contract violation (fail closed, exit 2, write nothing)."""


class _GitError(RuntimeError):
    """A git observation failure (operational, exit 1, write nothing)."""


# --------------------------------------------------------------------------- helpers

def _sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def _dumps(obj):
    """Deterministic JSON bytes: sorted keys, fixed 2-space indent, trailing newline."""
    return (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


# ---------------------------------------------------------------------------- policy

def _parse_policy(policy_bytes):
    """Parse + validate the closed policy contract. Raises _PolicyError on violation."""
    try:
        data = tomllib.loads(policy_bytes.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise _PolicyError(f"parse-error ({exc})") from exc
    _validate_policy(data)
    return data


def _validate_policy(data):
    if set(data) != _TOP_KEYS:
        unknown = ",".join(sorted(set(data) - _TOP_KEYS)) or "-"
        missing = ",".join(sorted(_TOP_KEYS - set(data))) or "-"
        raise _PolicyError(f"top-level-keys unknown={unknown} missing={missing}")
    if data["contract_id"] != "ReorientPolicy":
        raise _PolicyError("contract_id")
    for key in ("schema_version", "board_schema_version", "receipt_schema_version"):
        if not _is_int(data[key]) or data[key] != 1:
            raise _PolicyError(key)

    disc = data["discipline"]
    if not isinstance(disc, dict) or set(disc) != _DISCIPLINE_KEYS:
        raise _PolicyError("discipline-keys")
    for key in _DISCIPLINE_BOOL_KEYS:
        # The mandated discipline laws are TRUE by operator decision; a policy
        # recording one as false is a contract lie, refused at load (codex r1
        # finding 6 - semantic closure, not shape closure).
        if disc[key] is not True:
            raise _PolicyError(f"discipline-{key}-must-be-true")
    if disc["discipline_enforced"] is not False:
        raise _PolicyError("discipline_enforced-must-be-false-in-v1")
    triggers = disc["receipt_interrupt_triggers"]
    if (not isinstance(triggers, list) or not triggers
            or not all(isinstance(t, str) and t for t in triggers)):
        raise _PolicyError("discipline-receipt_interrupt_triggers")
    if not _is_int(disc["fan_out_ceiling"]) or disc["fan_out_ceiling"] <= 0:
        raise _PolicyError("discipline-fan_out_ceiling")

    job_states = data["job_states"]
    if not isinstance(job_states, dict) or set(job_states) != {"values"}:
        raise _PolicyError("job_states-keys")
    if job_states["values"] != _JOB_STATES:
        raise _PolicyError("job_states-values-not-the-closed-vocabulary")

    grammar = data["verdict_grammar"]
    if not isinstance(grammar, dict) or set(grammar) != {"patterns"}:
        raise _PolicyError("verdict_grammar-keys")
    patterns = grammar["patterns"]
    if not isinstance(patterns, list) or len(patterns) != _GRAMMAR_PATTERN_COUNT:
        raise _PolicyError("verdict_grammar-count")
    for pattern in patterns:
        if not isinstance(pattern, str) or not pattern:
            raise _PolicyError("verdict_grammar-pattern-type")
        # Only whole-line shapes may project: every pattern is ^...$-anchored
        # (codex r1 finding 6, probe M23b - compilable is not enough).
        if not (pattern.startswith("^") and pattern.endswith("$")):
            raise _PolicyError("verdict_grammar-pattern-unanchored")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise _PolicyError(f"verdict_grammar-pattern-invalid ({exc})") from exc

    census = data["census"]
    if not isinstance(census, dict) or set(census) != {"watch_globs"}:
        raise _PolicyError("census-keys")
    globs = census["watch_globs"]
    if (not isinstance(globs, list) or not globs
            or not all(isinstance(g, str) and g for g in globs)):
        raise _PolicyError("census-watch_globs")

    rows = data["lane"]
    if not isinstance(rows, list) or not rows:
        raise _PolicyError("lane-rows-empty")
    seen_ids = set()
    seen_priorities = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != _LANE_KEYS:
            raise _PolicyError("lane-row-keys")
        lane_id = row["id"]
        if not isinstance(lane_id, str) or not lane_id:
            raise _PolicyError("lane-id")
        if lane_id in seen_ids:
            raise _PolicyError(f"duplicate-lane-id:{lane_id}")
        seen_ids.add(lane_id)
        priority = row["priority"]
        if not _is_int(priority) or priority <= 0:
            raise _PolicyError(f"lane-priority:{lane_id}")
        if priority in seen_priorities:
            raise _PolicyError(f"duplicate-priority:{priority}")
        seen_priorities.add(priority)
        if row["charter"] not in _CHARTERS:
            raise _PolicyError(f"lane-charter:{lane_id}")
        records = row["records"]
        if (not isinstance(records, list) or not records
                or not all(isinstance(r, str) and r for r in records)):
            raise _PolicyError(f"lane-records:{lane_id}")
        if len(set(records)) != len(records):
            raise _PolicyError(f"lane-records-duplicate:{lane_id}")


def _declared_paths(policy):
    seen = set()
    for row in policy["lane"]:
        seen.update(row["records"])
    return sorted(seen)


def _roster_escape(repo_root, rel):
    """True when a declared record path leaves ``--repo`` (codex r1 finding 6,
    probe M23c): an absolute path, a ``..`` traversal, or a path whose symlink
    resolution lands outside the resolved repo root. Roster paths are
    repo-relative projections INSIDE the observed repository - anything else is
    refused before a single byte is read or projected."""
    if os.path.isabs(rel):
        return True
    if ".." in Path(rel).parts:
        return True
    root = Path(repo_root).resolve()
    try:
        target = (root / rel).resolve()
    except OSError:  # unresolvable (e.g. a symlink loop) never projects
        return True
    return not target.is_relative_to(root)


def _first_roster_escape(repo_root, policy):
    """The first escaping declared record path (sorted order), or None."""
    for rel in _declared_paths(policy):
        if _roster_escape(repo_root, rel):
            return rel
    return None


# ---------------------------------------------------------------------- record axis

def _census_listing(repo_root, policy):
    """Files under the repo root matching the census watch globs (sorted, POSIX-rel)."""
    root = Path(repo_root)
    hits = set()
    for pattern in policy["census"]["watch_globs"]:
        for path in root.glob(pattern):
            if path.is_file():
                hits.add(path.relative_to(root).as_posix())
    return tuple(sorted(hits))


def _records_manifest(repo_root, policy):
    """One observation pass over the record axis (reviewed seam, called once per pass).

    Returns the declared-record digest map (sha256 or None for unreadable) plus the
    resolved census-glob file listing; ``check`` compares pass A against pass B and
    refuses with exit 4 on ANY difference.
    """
    root = Path(repo_root)
    digests = {}
    for rel in _declared_paths(policy):
        try:
            digests[rel] = _sha256_hex((root / rel).read_bytes())
        except OSError:
            digests[rel] = None
    return {"records": digests, "census": _census_listing(repo_root, policy)}


def _read_records(repo_root, policy):
    """Read every declared record once. Returns (contents, unreadable_paths)."""
    root = Path(repo_root)
    contents = {}
    unreadable = []
    for rel in _declared_paths(policy):
        try:
            data = (root / rel).read_bytes()
            data.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            unreadable.append(rel)
        else:
            contents[rel] = data
    return contents, unreadable


def _verdict_lines(data, grammar):
    """Lines matching the policy's anchored grammar: file order, byte-verbatim."""
    out = []
    for line in data.decode("utf-8").split("\n"):
        for regex in grammar:
            if regex.search(line):
                out.append(line)
                break
    return out


# ------------------------------------------------------------------------- git axis

def _git_env():
    """Hermetic git environment: no inherited GIT_*, no user/system config, no locks."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    env["GIT_ATTR_NOSYSTEM"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def _git_bytes(env, argv):
    proc = subprocess.run(
        argv, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", errors="replace").strip()
        raise _GitError(f"{' '.join(argv)} -> exit {proc.returncode}: {detail}")
    return proc.stdout


def _git_repo(env, path, *args):
    """Run git against a path with the GLOBAL --no-optional-locks flag position
    and the repo-local config seam neutralized: the hermetic env silences user
    and system config, but a checkout-injected ``core.fsmonitor`` command would
    still execute inside the child git during "read-only" observation (codex r1
    finding 9; probe M26 drops this neutralizer). The command-line config
    override outranks every config file, so the hook can never run."""
    return _git_bytes(env, [
        "git", "--no-optional-locks", "-c", "core.fsmonitor=false",
        "-C", str(path), *args,
    ])


def _git_version(env):
    return _git_bytes(env, ["git", "--version"]).decode("utf-8", errors="replace").strip()


def _dirty_count(status_stream):
    """Porcelain-v1 line count over tracked changes (untracked ?? lines excluded).

    PINNED to the ROOT status fields only (design section 6): untracked files are
    the census's job and always drift the git-state digest, so the root clean
    flag never flaps on scratch noise. Worktree rows use the FULL count below.
    """
    return sum(
        1 for line in status_stream.decode("utf-8", errors="replace").splitlines()
        if line and not line.startswith("??")
    )


def _porcelain_line_count(status_stream):
    """FULL porcelain-v1 line count, untracked ?? lines included - the design
    section 6 semantics for a worktree row's ``dirty_line_count`` (codex r1
    finding 7; probe M24 re-applies the ?? filter here)."""
    return sum(
        1 for line in status_stream.decode("utf-8", errors="replace").splitlines()
        if line
    )


def _parse_worktree_list(stream):
    entries = []
    current = None
    for line in stream.decode("utf-8", errors="replace").splitlines():
        if not line:
            current = None
            continue
        if line.startswith("worktree "):
            current = {"path": line[len("worktree "):], "head_sha": None, "branch": None}
            entries.append(current)
        elif current is not None:
            if line.startswith("HEAD "):
                current["head_sha"] = line[len("HEAD "):]
            elif line.startswith("branch "):
                ref = line[len("branch "):]
                if ref.startswith("refs/heads/"):
                    ref = ref[len("refs/heads/"):]
                current["branch"] = ref
            # "detached", "bare", "locked", "prunable" annotations carry no board data

    return entries


def _observe_git(repo_root, env):
    """One observation pass over the git axis: canonical streams + parsed views.

    The canonical bundle (design section 7) is the exact byte streams of rev-parse
    HEAD, branch --show-current, status --porcelain=v1, for-each-ref refs/heads,
    worktree list --porcelain, and each worktree's status stream, concatenated in
    that fixed order with NUL separators.
    """
    head_raw = _git_repo(env, repo_root, "rev-parse", "HEAD")
    branch_raw = _git_repo(env, repo_root, "branch", "--show-current")
    status_raw = _git_repo(env, repo_root, "status", "--porcelain=v1")
    refs_raw = _git_repo(env, repo_root, "for-each-ref", "refs/heads")
    wtlist_raw = _git_repo(env, repo_root, "worktree", "list", "--porcelain")
    tracked_raw = _git_repo(env, repo_root, "ls-files")

    worktrees = []
    wt_streams = []
    for entry in _parse_worktree_list(wtlist_raw):
        present = os.path.isdir(entry["path"])
        stream = _git_repo(env, entry["path"], "status", "--porcelain=v1") if present else b""
        wt_streams.append(stream)
        if present:
            lock = "present" if os.path.exists(os.path.join(entry["path"], "lane.lock")) else "absent"
            worktrees.append({
                "path": entry["path"],
                "present": True,
                "head_sha": entry["head_sha"],
                "branch": entry["branch"],
                "dirty_line_count": _porcelain_line_count(stream),
                "lane_lock": lock,
            })
        else:
            worktrees.append({
                "path": entry["path"],
                "present": False,
                "head_sha": None,
                "branch": None,
                "dirty_line_count": None,
                "lane_lock": None,
            })

    branches = []
    for line in refs_raw.decode("utf-8", errors="replace").splitlines():
        fields = line.split("\t", 1)
        if len(fields) != 2:
            continue
        sha = fields[0].split(" ", 1)[0]
        ref = fields[1]
        name = ref[len("refs/heads/"):] if ref.startswith("refs/heads/") else ref
        branches.append({"name": name, "sha": sha})
    branches.sort(key=lambda b: b["name"])

    bundle = b"\x00".join([head_raw, branch_raw, status_raw, refs_raw, wtlist_raw, *wt_streams])
    head_branch = branch_raw.decode("utf-8", errors="replace").strip()
    return {
        "head_sha": head_raw.decode("utf-8", errors="replace").strip(),
        "head_branch_or_detached": head_branch if head_branch else "(detached)",
        "status_line_count": _dirty_count(status_raw),
        "tracked_file_count": len(tracked_raw.decode("utf-8", errors="replace").splitlines()),
        "branches": branches,
        "worktrees": worktrees,
        "bundle_sha256": _sha256_hex(bundle),
    }


def _lane_lock_states(obs):
    """The lane.lock occupancy projection in a pass-comparable shape. A lock file
    is ordinarily gitignored, so it is INVISIBLE to every stream in the canonical
    git bundle - yet it is a live board input. It therefore rides the two-pass
    drift compare explicitly: a lock created or removed between pass A and pass B
    is concurrent drift, never PASS-then-STALE (codex r1 finding 5; probe M22
    removes this surface from the compare)."""
    return [(wt["path"], wt["lane_lock"]) for wt in obs["worktrees"]]


# ------------------------------------------------------------------------ projection

def _build_board(obs, record_bytes, census_listing, policy, policy_sha256):
    """Assemble the closed board schema v1. Pure projection; no timestamps, no status."""
    grammar = [re.compile(p) for p in policy["verdict_grammar"]["patterns"]]

    lanes = []
    for row in sorted(policy["lane"], key=lambda r: r["id"]):
        records = []
        for rel in sorted(row["records"]):
            data = record_bytes[rel]
            records.append({
                "path": rel,
                "exists": True,
                "sha256": _sha256_hex(data),
                "verdict_lines": _verdict_lines(data, grammar),
            })
        lanes.append({
            "id": row["id"],
            "priority": row["priority"],
            "charter": row["charter"],
            "records": records,
            "verification": "UNVERIFIED",
        })

    worktree_rows = []
    for wt in obs["worktrees"]:
        if wt["present"]:
            worktree_rows.append({
                "path": wt["path"],
                "status": "present",
                "head_sha": wt["head_sha"],
                "branch_or_detached": wt["branch"] if wt["branch"] else "(detached)",
                "dirty_line_count": wt["dirty_line_count"],
                "lane_lock": wt["lane_lock"],
            })
        else:
            worktree_rows.append({
                "path": wt["path"],
                "status": "missing",
                "head_sha": None,
                "branch_or_detached": None,
                "dirty_line_count": None,
                "lane_lock": None,
            })
    worktree_rows.sort(key=lambda r: r["path"])

    declared = set()
    for row in policy["lane"]:
        declared.update(row["records"])
    undeclared = sorted(
        path for path in census_listing
        if path not in declared and path not in (BOARD_REL, RECEIPT_REL)
    )

    return {
        "contract_id": "ReorientBoard",
        "schema_version": 1,
        "repo": {
            "head_sha": obs["head_sha"],
            "head_branch_or_detached": obs["head_branch_or_detached"],
            "status_clean": obs["status_line_count"] == 0,
            "status_line_count": obs["status_line_count"],
            "tracked_file_count": obs["tracked_file_count"],
        },
        "branches": obs["branches"],
        "worktrees": worktree_rows,
        "lanes": lanes,
        "undeclared": undeclared,
        "policy_sha256": policy_sha256,
    }


def _inputs_manifest_sha256(inputs):
    blob = b"".join(
        "{0}\x00{1}\n".format(item["path"], item["sha256"]).encode("utf-8")
        for item in sorted(inputs, key=lambda item: item["path"])
    )
    return _sha256_hex(blob)


def _tool_sha256():
    return _sha256_hex(_SELF_PATH.read_bytes())


def _toolchain(env):
    return {"python": sys.version.split()[0], "git": _git_version(env)}


_RECEIPT_KEYS = {
    "contract_id", "schema_version", "provenance", "toolchain", "repo_head_sha",
    "git_state_sha256", "policy_sha256", "tool_sha256", "board_sha256", "inputs",
    "inputs_manifest_sha256", "discipline", "discipline_enforced",
}
_INPUT_ROW_KEYS = {"path", "sha256"}


def _receipt_closure_violation(receipt):
    """The CLOSED receipt schema v1 on verify (codex r1 finding 4): pinned
    schema_version (M21a), zero unknown top-level keys (M21b), the honesty bit
    literally false in v1 (M21c), and the exact ``inputs`` row shape. Returns the
    first violation label, or None. Provenance stays NON-authoritative (RED 18's
    documented boundary): the closed key set requires its presence, but its
    values are never judged - here or anywhere in verify."""
    if set(receipt) != _RECEIPT_KEYS:
        return "top-level-keys"
    if not _is_int(receipt["schema_version"]) or receipt["schema_version"] != 1:
        return "schema_version"
    if receipt["discipline_enforced"] is not False:
        return "discipline_enforced-lie"
    inputs = receipt["inputs"]
    if not isinstance(inputs, list):
        return "inputs"
    for row in inputs:
        if (not isinstance(row, dict) or set(row) != _INPUT_ROW_KEYS
                or not isinstance(row["path"], str)
                or not isinstance(row["sha256"], str)):
            return "inputs-row"
    return None


# -------------------------------------------------------------------------- commands

def _cmd_check(repo_root, now, command_argv):
    env = _git_env()
    root = Path(repo_root)

    try:
        policy_bytes = (root / POLICY_REL).read_bytes()
    except OSError:
        print(f"REORIENT: FAIL missing={POLICY_REL}")
        return 2
    try:
        policy = _parse_policy(policy_bytes)
    except _PolicyError as exc:
        print(f"REORIENT: FAIL policy={exc}")
        return 2
    policy_sha256 = _sha256_hex(policy_bytes)

    escape = _first_roster_escape(repo_root, policy)
    if escape is not None:
        print(f"REORIENT: FAIL record-escape={escape}")
        return 2

    # Pass A: both axes.
    obs_a = _observe_git(repo_root, env)
    manifest_a = _records_manifest(repo_root, policy)

    missing = sorted(p for p, digest in manifest_a["records"].items() if digest is None)
    if missing:
        print(f"REORIENT: FAIL missing={missing[0]}")
        return 2

    contents, unreadable = _read_records(repo_root, policy)
    if unreadable:
        print(f"REORIENT: FAIL missing={sorted(unreadable)[0]}")
        return 2
    content_digests = {rel: _sha256_hex(data) for rel, data in contents.items()}

    # Pass B: recompute both axes; ANY difference is concurrent drift. Every live
    # board input rides this compare: the git bundle, the record/census manifest,
    # AND the lane.lock occupancy states (gitignored locks are invisible to the
    # bundle streams - finding 5).
    obs_b = _observe_git(repo_root, env)
    manifest_b = _records_manifest(repo_root, policy)
    if (obs_a["bundle_sha256"] != obs_b["bundle_sha256"]
            or obs_a["tracked_file_count"] != obs_b["tracked_file_count"]
            or _lane_lock_states(obs_a) != _lane_lock_states(obs_b)
            or manifest_a != manifest_b
            or content_digests != manifest_b["records"]):
        print("REORIENT: FAIL concurrent-drift")
        return 4

    board = _build_board(obs_a, contents, manifest_a["census"], policy, policy_sha256)
    board_bytes = _dumps(board)
    board_sha256 = _sha256_hex(board_bytes)

    inputs = [{"path": rel, "sha256": content_digests[rel]} for rel in sorted(content_digests)]
    receipt = {
        "contract_id": "ReorientReceipt",
        "schema_version": 1,
        "provenance": {"generated_utc": now, "command": list(command_argv)},
        "toolchain": _toolchain(env),
        "repo_head_sha": obs_a["head_sha"],
        "git_state_sha256": obs_a["bundle_sha256"],
        "policy_sha256": policy_sha256,
        "tool_sha256": _tool_sha256(),
        "board_sha256": board_sha256,
        "inputs": inputs,
        "inputs_manifest_sha256": _inputs_manifest_sha256(inputs),
        "discipline": policy["discipline"],
        "discipline_enforced": False,
    }
    receipt_bytes = _dumps(receipt)

    # Pair write law: temps in the output dir, then rename board FIRST, receipt LAST
    # (the receipt rename is the commit point). Success path only. Staging is
    # HOSTILE-PLANT-SAFE (codex r1 finding 8; probe M25 reverts it): every temp is
    # opened via mkstemp - an UNPREDICTABLE fresh name created O_EXCL, so a
    # pre-planted symlink can neither be guessed nor followed, and no byte is ever
    # written through an attacker-controlled name onto a tracked file or .git.
    out_dir = root / OUTPUT_DIR_REL
    staged = []
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        for payload in (board_bytes, receipt_bytes):
            fd, tmp_name = tempfile.mkstemp(dir=str(out_dir), suffix=".tmp")
            staged.append(tmp_name)
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
        os.replace(staged[0], root / BOARD_REL)
        os.replace(staged[1], root / RECEIPT_REL)
    except OSError as exc:
        for leftover in staged:
            try:
                os.unlink(leftover)
            except OSError:
                pass
        print("REORIENT: FAIL write-error")
        print(f"reorient: pair write interrupted: {exc}", file=sys.stderr)
        return 1

    print(f"REORIENT: PASS board={board_sha256} inputs={len(inputs)}")
    return 0


def _cmd_verify(repo_root):
    env = _git_env()
    root = Path(repo_root)
    board_path = root / BOARD_REL
    receipt_path = root / RECEIPT_REL

    if not board_path.is_file() or not receipt_path.is_file():
        print("REORIENT: STALE missing-receipt")
        return 3
    try:
        receipt = json.loads(receipt_path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        print("REORIENT: STALE missing-receipt")
        return 3
    if not isinstance(receipt, dict) or receipt.get("contract_id") != "ReorientReceipt":
        print("REORIENT: STALE missing-receipt")
        return 3

    violation = _receipt_closure_violation(receipt)
    if violation is not None:
        print(f"REORIENT: STALE receipt-schema={violation}")
        return 3

    # Reuse key, field by field, every one recomputed from live inputs.
    # Provenance (generated_utc, command) is recorded execution metadata and is
    # deliberately NEVER compared: verify cannot recompute a producer's argv or
    # timestamp without trusting the field under test, so it carries no reuse
    # authority (design section 7; the documented boundary).
    try:
        policy_bytes = (root / POLICY_REL).read_bytes()
    except OSError:
        print(f"REORIENT: FAIL missing={POLICY_REL}")
        return 2
    policy_sha256 = _sha256_hex(policy_bytes)
    if receipt.get("policy_sha256") != policy_sha256:
        print(f"REORIENT: STALE drifted={POLICY_REL}")
        return 3
    try:
        policy = _parse_policy(policy_bytes)
    except _PolicyError as exc:
        print(f"REORIENT: FAIL policy={exc}")
        return 2

    escape = _first_roster_escape(repo_root, policy)
    if escape is not None:
        print(f"REORIENT: FAIL record-escape={escape}")
        return 2

    # Discipline rows are a verbatim projection of the (sha-matched) policy: a
    # receipt whose rows differ from the policy's is a lie about reviewed data,
    # never a reusable receipt (finding 4 - byte-honesty; probe M21c).
    if receipt["discipline"] != policy["discipline"]:
        print("REORIENT: STALE receipt-schema=discipline-rows")
        return 3

    contents, unreadable = _read_records(repo_root, policy)
    live_digests = {rel: _sha256_hex(data) for rel, data in contents.items()}
    for rel in unreadable:
        live_digests[rel] = None
    recorded = {}
    for item in receipt.get("inputs") or []:
        if isinstance(item, dict) and "path" in item:
            recorded[item["path"]] = item.get("sha256")
    for rel in sorted(set(live_digests) | set(recorded)):
        if live_digests.get(rel) != recorded.get(rel):
            print(f"REORIENT: STALE drifted={rel}")
            return 3
    if unreadable:
        print(f"REORIENT: STALE drifted={sorted(unreadable)[0]}")
        return 3
    inputs = [{"path": rel, "sha256": live_digests[rel]} for rel in sorted(live_digests)]
    if receipt.get("inputs_manifest_sha256") != _inputs_manifest_sha256(inputs):
        print("REORIENT: STALE drifted=inputs-manifest")
        return 3

    obs = _observe_git(repo_root, env)
    if (receipt.get("git_state_sha256") != obs["bundle_sha256"]
            or receipt.get("repo_head_sha") != obs["head_sha"]):
        print("REORIENT: STALE drifted=git-state")
        return 3

    if receipt.get("tool_sha256") != _tool_sha256():
        print(f"REORIENT: STALE drifted={TOOL_REL}")
        return 3

    if receipt.get("toolchain") != _toolchain(env):
        print("REORIENT: STALE drifted=toolchain")
        return 3

    # Total freshness: rebuild the board in memory and compare BOTH the receipt's
    # board binding and the on-disk bytes against the recomputation.
    recomputed = _dumps(_build_board(
        obs, contents, _census_listing(repo_root, policy), policy, policy_sha256))
    try:
        disk_bytes = board_path.read_bytes()
    except OSError:
        print("REORIENT: STALE missing-receipt")
        return 3
    if (receipt.get("board_sha256") != _sha256_hex(disk_bytes)
            or recomputed != disk_bytes):
        print("REORIENT: STALE board-edited")
        return 3

    print("REORIENT: PASS")
    return 0


# ------------------------------------------------------------------------------- CLI

def main(argv=None):
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    parser = argparse.ArgumentParser(
        prog="reorient",
        description="Derive (check) or re-verify (verify) the orientation board "
                    "for the repository at --repo.",
    )
    parser.add_argument("--repo", required=True,
                        help="repository root to observe (required; never hardcoded)")
    parser.add_argument("--now", default=None,
                        help="ISO-8601Z timestamp recorded in receipt provenance "
                             "(default: real UTC; the board itself carries no timestamp)")
    parser.add_argument("command", choices=("check", "verify"))
    args = parser.parse_args(argv)

    try:
        if args.command == "check":
            now = args.now if args.now is not None else _utc_now()
            return _cmd_check(args.repo, now, argv)
        return _cmd_verify(args.repo)
    except _GitError as exc:
        print("REORIENT: FAIL git-observation")
        print(f"reorient: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
