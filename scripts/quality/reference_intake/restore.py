"""W6-C §6 — BACKUP-BEFORE-TRANSFORM (the restore-point boundary).

The engine RESTYLES a target's real bytes, so a mistake is destructive. ACTIVE.md makes
BACKUP-BEFORE-TRANSFORM a hard law: before any restyle, capture a hash-pinned snapshot of the
target's CURRENT state, and refuse to transform without one.

  * ``snapshot_target(repo)`` writes a commit-tree of the target's current bytes (tracked AND
    untracked, via a throwaway index that never touches the working index/HEAD) and tags it —
    a hash-pinned restore point. Returns a :class:`RestorePoint` whose ``commit_sha`` is a real
    git object.
  * ``restore(point)`` reverts the working tree to those exact bytes.
  * ``guarded_transform(point, fn)`` is FAIL-CLOSED: it raises :class:`SnapshotRequired` unless
    ``point`` references a committed snapshot — so a transform can never run un-backed-up.

Git is the byte-custody backend; a screenshot/visual rung is recorded as deferred (honest),
never faked. candidate_only; decides no authority.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional


class SnapshotRequired(RuntimeError):
    """A transform was attempted without a committed BACKUP-BEFORE-TRANSFORM restore point."""


class RestoreError(RuntimeError):
    """A restore point could not be created or applied."""


@dataclass
class RestorePoint:
    repo_path: str
    commit_sha: str
    tree_sha: str
    tag: str
    created_at: str
    committed: bool
    manifest: dict = field(default_factory=dict)
    manifest_path: Optional[str] = None
    screenshot: Optional[str] = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git(repo: Path, *args: str, env: Optional[dict] = None) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, text=True,
        env=({**os.environ, **env} if env else None),
    )
    return proc.stdout.strip()


def _assert_worktree(repo: Path) -> None:
    try:
        inside = _git(repo, "rev-parse", "--is-inside-work-tree")
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RestoreError(f"{repo}: not a git work tree") from exc
    if inside != "true":
        raise RestoreError(f"{repo}: not a git work tree")


def _head_sha(repo: Path) -> Optional[str]:
    try:
        return _git(repo, "rev-parse", "--verify", "HEAD")
    except subprocess.CalledProcessError:
        return None  # unborn branch — the very first snapshot has no parent


def snapshot_target(repo_path, *, tag: Optional[str] = None, out_dir=None) -> RestorePoint:
    """Commit + tag a hash-pinned snapshot of the target's CURRENT bytes WITHOUT touching the
    working index or HEAD (a throwaway ``GIT_INDEX_FILE`` captures tracked + untracked state)."""
    repo = Path(repo_path).resolve()
    _assert_worktree(repo)
    head = _head_sha(repo)

    tmp_index = Path(tempfile.mkdtemp(prefix="w6c-index-")) / "index"
    env = {"GIT_INDEX_FILE": str(tmp_index)}
    try:
        if head:
            _git(repo, "read-tree", head, env=env)
        _git(repo, "add", "-A", env=env)
        tree_sha = _git(repo, "write-tree", env=env)
        commit_args = ["commit-tree", tree_sha, "-m", "w6c pre-restyle snapshot"]
        if head:
            commit_args += ["-p", head]
        commit_sha = _git(repo, *commit_args, env=env)
    finally:
        try:
            tmp_index.unlink()
            tmp_index.parent.rmdir()
        except OSError:
            pass

    tag = tag or f"w6c-restore-{commit_sha[:12]}"
    _git(repo, "tag", "-f", tag, commit_sha)   # a named, hash-pinned restore point

    files = [line.split("\t", 1)[-1] for line in _git(repo, "ls-tree", "-r", "--name-only", commit_sha).splitlines() if line]
    committed = _object_exists(repo, commit_sha)
    manifest = {
        "contract_id": "RestorePoint",
        "repo_path": str(repo),
        "commit_sha": commit_sha,
        "tree_sha": tree_sha,
        "tag": tag,
        "created_at": _now_iso(),
        "file_count": len(files),
        "files": files,
        # honest: the byte-pack is authoritative; the visual rung is deferred, not faked
        "screenshot": {"captured": False,
                       "reason": "target is a repo byte-tree; visual receipt deferred to the served-surface rung"},
        "authority_status": "candidate_only",
        "cannot_mark_done": True,
    }
    manifest_path = None
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        manifest_path = out / f"{tag}.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return RestorePoint(
        repo_path=str(repo), commit_sha=commit_sha, tree_sha=tree_sha, tag=tag,
        created_at=manifest["created_at"], committed=committed, manifest=manifest,
        manifest_path=str(manifest_path) if manifest_path else None, screenshot=None,
    )


def _object_exists(repo: Path, sha: str) -> bool:
    try:
        _git(repo, "cat-file", "-e", f"{sha}^{{commit}}")
        return True
    except subprocess.CalledProcessError:
        return False


def is_committed(point: RestorePoint) -> bool:
    """True iff the restore point references a real, committed git object."""
    if point is None or not getattr(point, "commit_sha", None):
        return False
    return _object_exists(Path(point.repo_path), point.commit_sha)


def restore(point: RestorePoint) -> bool:
    """Revert the target's working tree to the snapshot's exact bytes. Fail-closed: refuses if
    the restore point is not a committed object."""
    if not is_committed(point):
        raise RestoreError("restore point is not a committed git object — nothing safe to restore to")
    repo = Path(point.repo_path)
    _git(repo, "checkout", point.commit_sha, "--", ".")
    return True


def guarded_transform(point: Optional[RestorePoint], transform: Callable, *args, **kwargs):
    """Run ``transform`` ONLY behind a committed BACKUP-BEFORE-TRANSFORM snapshot. Raises
    :class:`SnapshotRequired` (and never calls ``transform``) otherwise — this is the fail-closed
    law that makes an un-backed-up restyle structurally impossible to run."""
    if point is None or not getattr(point, "committed", False) or not is_committed(point):
        raise SnapshotRequired(
            "BACKUP-BEFORE-TRANSFORM: a committed restore point is required before any transform")
    return transform(*args, **kwargs)
