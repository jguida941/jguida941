"""Hermetic slice-patch pipeline (w3c-0-design-closure.md §13.2 as executable code).

This module encodes, byte-for-byte, the "Patch-isolated review-BEFORE-commit
sequence" hermetic git mechanism ratified in §13.2 of
``docs/plans/handoff/w3c-0-design-closure.md`` (rev 14 DELEGATES to this module +
``tests/contracts/test_slice_patch.py`` as the binding authority over the prose).

Every git invocation runs under the fixed ``H-GIT`` environment allowlist
(:func:`hermetic_env`), which is built FROM SCRATCH -- never an ``os.environ``
passthrough beyond ``PATH``/``TMPDIR``.  Inherited behaviour variables
(``GIT_DIFF_OPTS``, ``GIT_CONFIG_COUNT``/``GIT_CONFIG_KEY_*``,
``GIT_EXTERNAL_DIFF``, a hostile ``GIT_CONFIG_GLOBAL``, ``XDG_CONFIG_HOME``,
locale/pager/editor controls, ...) are absent by construction, so ambient
hostility cannot alter the canonical patch bytes.  The source preflight and the
ignored-file scan fail closed on exactly the surfaces §13.2 enumerates -- among
them a per-worktree ``config.worktree`` honoured ONLY while
``extensions.worktreeConfig`` is enabled (a dormant one is inert, ADV-4) and any
in-tree ``.gitattributes`` whose scope reaches an allowed path and carries a
byte-affecting builtin
(``text``/``eol``/``working-tree-encoding``/``binary``/``crlf``/``ident``/``diff``).

Declared trust assumption (the ONLY one)
----------------------------------------
The ``git`` binary is resolved through the ambient ``PATH`` -- the single value
(alongside ``TMPDIR``) carried from the caller's environment into
:func:`hermetic_env`.  ``PATH`` is therefore the one and only trust root of this
pipeline: whoever controls ``PATH`` chooses which ``git`` runs.  Pinning or
otherwise verifying the ``git`` binary itself is explicitly OUT OF SCOPE for
§13.2.  Every *other* environment name is rebuilt from scratch, so no other
ambient variable can influence the canonical bytes.

Public API (imported by ``tests/contracts/test_slice_patch.py``):
``HermeticGitError``, :func:`hermetic_env`, :func:`source_preflight`,
:func:`stage_allowed`, :func:`ignored_scan`, :func:`canonical_patch`.
"""

import os
import stat
import subprocess
from pathlib import Path, PurePosixPath

__all__ = [
    "HermeticGitError",
    "hermetic_env",
    "source_preflight",
    "stage_allowed",
    "ignored_scan",
    "canonical_patch",
]


class HermeticGitError(Exception):
    """Raised when a hermetic git step fails or a fail-closed guard refuses."""


# --- §13.2 H-GIT environment allowlist --------------------------------------
# `env -i PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" HOME=/nonexistent LC_ALL=C
#  GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null GIT_ATTR_NOSYSTEM=1
#  GIT_TERMINAL_PROMPT=0 GIT_NO_REPLACE_OBJECTS=1 git ...`


def hermetic_env(ambient_env=None):
    """Return the fixed §13.2 ``H-GIT`` environment as a fresh dict.

    Only ``PATH`` and ``TMPDIR`` are sourced from ONE environment -- from
    ``ambient_env`` when it is supplied, otherwise from ``os.environ`` -- and
    every other name is pinned to its §13.2 value regardless of the ambient
    environment.  In particular ``GIT_CONFIG_GLOBAL`` is ALWAYS ``/dev/null``,
    so a hostile ambient ``GIT_CONFIG_GLOBAL`` file is inert, and hostile
    behaviour variables such as ``GIT_DIFF_OPTS`` / ``GIT_CONFIG_COUNT`` /
    ``GIT_EXTERNAL_DIFF`` are never propagated because the returned dict is the
    complete environment.

    When ``ambient_env`` is supplied its ``PATH`` is used VERBATIM -- even if
    missing or empty -- and ``os.environ`` is never consulted as a second
    source (that would contradict "the env is built solely from the supplied
    source", and would silently rescue a caller who meant to run with no
    ``PATH``).  ``os.environ`` supplies ``PATH``/``TMPDIR`` ONLY when
    ``ambient_env`` is ``None``.  ``PATH`` is the pipeline's one declared trust
    root -- see the module docstring.

    ``GIT_NO_REPLACE_OBJECTS=1`` is pinned so git honours NO ``refs/replace/*``
    substitution: a replacement ref that swaps a HEAD blob for the staged blob
    would otherwise let ``git diff --cached HEAD`` omit a real change, and the
    fixed value neutralises that whether or not the caller's environment set it.
    """
    source = os.environ if ambient_env is None else ambient_env
    return {
        # Verbatim from the single chosen source; never a second-source fallback.
        "PATH": source.get("PATH", ""),
        "TMPDIR": source.get("TMPDIR") or "/tmp",
        "HOME": "/nonexistent",
        "LC_ALL": "C",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        # refs/replace/* is honoured by default; pin it OFF so a replacement ref
        # cannot hide a real change from the canonical `git diff --cached HEAD`.
        "GIT_NO_REPLACE_OBJECTS": "1",
    }


def _run_git(repo_root, git_args, ambient_env):
    """Run ``git <git_args>`` under the hermetic env; wrap ALL failures.

    Output is captured as raw bytes (no text decoding) so binary patch content
    survives untouched.  A non-zero exit (``check=True``) is re-raised as a
    clear :class:`HermeticGitError`; so is any :class:`OSError` -- an absent or
    unexecutable ``git`` (e.g. an empty ``PATH`` yields ``FileNotFoundError``),
    a ``PermissionError``, or a bad ``cwd`` -- which ``subprocess`` raises
    BEFORE the child ever starts and would otherwise leak past the hermetic
    boundary uncaught.
    """
    argv = ["git", *(str(arg) for arg in git_args)]
    try:
        return subprocess.run(
            argv,
            cwd=str(repo_root),
            env=hermetic_env(ambient_env),
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or b"").decode("utf-8", "surrogateescape").strip()
        raise HermeticGitError(
            "hermetic git command failed (exit {code}): {cmd}\n{err}".format(
                code=exc.returncode, cmd=" ".join(argv), err=stderr
            )
        ) from exc
    except OSError as exc:
        raise HermeticGitError(
            "hermetic git command could not execute: {cmd}\n{err}".format(
                cmd=" ".join(argv), err=exc
            )
        ) from exc


# --- §13.2 source preflight -------------------------------------------------
# Combined, case-insensitive local + worktree key set must contain none of
# these; presence REFUSES.
_FORBIDDEN_KEY_PREFIXES = ("diff.", "apply.", "status.", "filter.")
_FORBIDDEN_KEYS = frozenset(
    {
        "core.attributesfile",
        "core.autocrlf",
        "core.eol",
        "core.safecrlf",
        "core.excludesfile",
        # core.bigFileThreshold is never written by `git init`/`git clone`, so
        # ANY local/worktree occurrence is a deliberate override (a small value
        # would flip a text blob to binary): refuse outright.
        "core.bigfilethreshold",
        # attr.tree redirects git's attribute lookup to an ARBITRARY tree/ref
        # (git >=2.40), bypassing the entire working-tree/index .gitattributes
        # candidate scan: a local/active-worktree occurrence refuses outright.
        "attr.tree",
    }
)
# Keys that git DOES write by default, where only a hostile VALUE refuses -- the
# benign default must never trip the preflight.  ``core.fileMode=false``
# suppresses mode-only staging changes (its git-init default is the harmless
# ``true``), so it refuses on false alone.
_FORBIDDEN_WHEN_FALSE = frozenset({"core.filemode"})
_GIT_BOOL_FALSE = frozenset({"false", "no", "off", "0", ""})


def _git_bool_is_false(value):
    """Return True iff a raw git config string denotes boolean ``false``.

    ``value is None`` marks a *valueless* key (``[core]\\n\\tfileMode``), which
    git reads as boolean ``true`` -- so it is NOT false.  An explicit empty
    string, like ``false`` / ``no`` / ``off`` / ``0`` (case-insensitive), IS
    false, matching ``git config --type=bool``.
    """
    if value is None:
        return False
    return value.strip().lower() in _GIT_BOOL_FALSE


def _config_name_values(stdout):
    """Yield ``(lowercased-name, raw-value-or-None)`` from ``git config -z --list``.

    ``-z`` separates entries with NUL and, within an entry, the name from the
    value with a single newline; a key with no value at all yields ``None`` (git
    reads such a key as boolean true).  NUL/newline framing is robust against a
    value that itself contains newlines.
    """
    for entry in stdout.split(b"\x00"):
        if not entry:
            continue
        text = entry.decode("utf-8", "surrogateescape")
        name, sep, value = text.partition("\n")
        yield name.strip().lower(), (value if sep else None)


def _worktree_config_path(repo_root, ambient_env):
    """Resolve ``$GIT_DIR/config.worktree`` for the CURRENT worktree, or ``None``.

    ``git config --worktree`` is fatal in a linked worktree unless
    ``extensions.worktreeConfig`` is enabled ("--worktree cannot be used with
    multiple working trees ..."), and §13.2 runs the preflight inside exactly
    such a linked worktree.  So the per-worktree config is never read through
    that flag; instead ``git rev-parse --git-path`` resolves the file (correct
    for both the main and any linked worktree) and the caller reads it directly
    when it exists.
    """
    proc = _run_git(
        repo_root, ["rev-parse", "--git-path", "config.worktree"], ambient_env
    )
    raw = proc.stdout.decode("utf-8", "surrogateescape").strip()
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = Path(repo_root) / path
    return path


def source_preflight(repo_root, ambient_env=None):
    """Fail closed unless the repo is hermetically safe to patch (§13.2).

    The combined, case-insensitive local + per-worktree config key set must
    contain none of ``diff.*``, ``apply.*``, ``status.*``, ``filter.*``,
    ``core.attributesFile``, ``core.autocrlf``, ``core.eol``, ``core.safecrlf``,
    ``core.excludesFile``, ``core.bigFileThreshold``, or ``attr.tree`` (any
    presence refuses -- ``attr.tree`` would read attributes from an arbitrary
    tree, escaping the in-tree ``.gitattributes`` scan), and ``core.fileMode``
    must not resolve to boolean ``false`` (its benign
    git-init default ``true`` is allowed).  The shared/common config is read
    with ``--local`` (safe in main AND linked worktrees); the per-worktree
    config ``$GIT_DIR/config.worktree`` is read (by direct path, because ``git
    config --worktree`` is fatal in a linked worktree) and honoured ONLY when
    ``extensions.worktreeConfig`` is enabled in the common config -- a dormant
    config.worktree (extension off) is inert exactly as git treats it, so it can
    neither falsely refuse nor mask an effective common value (ADV-4).
    ``git rev-parse --git-path info/attributes`` must resolve to a missing path
    or a zero-byte regular file (``$GIT_DIR/info/attributes`` outranks every
    versioned ``.gitattributes``); any byte or any other file type raises.
    """
    # 1. Shared/common config: `--local` reads $GIT_COMMON_DIR/config and works
    #    identically in the main worktree and in any linked worktree.
    local_pairs = list(
        _config_name_values(
            _run_git(
                repo_root,
                ["config", "--local", "--includes", "-z", "--list"],
                ambient_env,
            ).stdout
        )
    )
    # 2. Per-worktree config ($GIT_DIR/config.worktree) is git-EFFECTIVE only when
    #    `extensions.worktreeConfig` is enabled in the common config.  A DORMANT
    #    config.worktree (extension off) is INERT exactly as git treats it, so it
    #    is neither read -- a forbidden key there would FALSELY refuse -- nor
    #    allowed to mask an effective common value (ADV-4): a dormant
    #    core.fileMode=true must NOT hide a common core.fileMode=false.  The
    #    extension is honoured only from the common config (git never reads
    #    config.worktree to discover it), so it is resolved from `local_pairs`;
    #    the last occurrence wins, matching git.
    worktree_config_enabled = False
    for name, value in local_pairs:
        if name == "extensions.worktreeconfig":
            worktree_config_enabled = not _git_bool_is_false(value)
    config_sources = [local_pairs]
    if worktree_config_enabled:
        wt_path = _worktree_config_path(repo_root, ambient_env)
        if wt_path is not None and wt_path.exists():
            config_sources.append(
                list(
                    _config_name_values(
                        _run_git(
                            repo_root,
                            ["config", "--file", str(wt_path),
                             "--includes", "-z", "--list"],
                            ambient_env,
                        ).stdout
                    )
                )
            )

    effective = {}
    for pairs in config_sources:
        for name, value in pairs:
            if name in _FORBIDDEN_KEYS or name.startswith(_FORBIDDEN_KEY_PREFIXES):
                raise HermeticGitError(
                    "forbidden local/worktree git config key present: {0}".format(name)
                )
            # An ACTIVE worktree config (appended second) overrides local, per git.
            effective[name] = value
    for key in sorted(_FORBIDDEN_WHEN_FALSE):
        if key in effective and _git_bool_is_false(effective[key]):
            raise HermeticGitError(
                "forbidden local/worktree git config value: {0}={1!r} "
                "(mode-only staging changes would be suppressed)".format(
                    key, effective[key]
                )
            )

    # 3. $GIT_DIR/info/attributes must be missing or a zero-byte regular file.
    proc = _run_git(
        repo_root, ["rev-parse", "--git-path", "info/attributes"], ambient_env
    )
    raw = proc.stdout.decode("utf-8", "surrogateescape").strip()
    attr_path = Path(raw)
    if not attr_path.is_absolute():
        attr_path = Path(repo_root) / attr_path
    if os.path.lexists(attr_path):
        st = os.lstat(attr_path)
        if not stat.S_ISREG(st.st_mode):
            raise HermeticGitError(
                "$GIT_DIR/info/attributes is not a regular file: {0}".format(attr_path)
            )
        if st.st_size != 0:
            raise HermeticGitError(
                "$GIT_DIR/info/attributes is non-empty ({0} bytes): {1}".format(
                    st.st_size, attr_path
                )
            )
    return None


# --- §13.2 pinned staging / scan / extraction commands ----------------------
# core.bigFileThreshold is pinned LARGE (512m) so no local value can flip a text
# blob to binary, and core.fileMode is pinned false so exec-bit variance across
# filesystems can never add or drop a mode line -- on BOTH the staging and the
# extraction command, since the mode a diff shows is recorded at `git add` time.
_STAGE_PINS = [
    "-c", "core.autocrlf=false",
    "-c", "core.eol=lf",
    "-c", "core.safecrlf=false",
    "-c", "core.attributesFile=/dev/null",
    "-c", "core.excludesFile=/dev/null",
    "-c", "core.bigFileThreshold=512m",
    "-c", "core.fileMode=false",
]

_EXTRACT_PINS = [
    "-c", "core.quotePath=false",
    "-c", "core.autocrlf=false",
    "-c", "core.eol=lf",
    "-c", "core.safecrlf=false",
    "-c", "diff.algorithm=myers",
    "-c", "diff.noprefix=false",
    "-c", "diff.mnemonicPrefix=false",
    "-c", "diff.suppressBlankEmpty=false",
    "-c", "diff.indentHeuristic=true",
    "-c", "core.attributesFile=/dev/null",
    "-c", "core.bigFileThreshold=512m",
    "-c", "core.fileMode=false",
]

_EXTRACT_FLAGS = [
    "diff", "--binary", "--full-index", "--no-color", "--no-ext-diff",
    "--no-textconv", "--no-renames", "--submodule=short",
    "--inter-hunk-context=0", "-O/dev/null", "--src-prefix=a/", "--dst-prefix=b/",
    "-U3", "--cached", "HEAD",
]

# Reject roster entries carrying pathspec glob magic; a leading ':' (pathspec
# long/short magic such as ':(exclude)...') and absolute/'..' escapes are
# checked separately.
_PATHSPEC_GLOB_MAGIC = ("*", "?", "[", "]")


def _validate_roster(allowed_paths):
    """Return a validated list of repo-relative literal paths, or refuse.

    §13.2 stages/scans/extracts EXACTLY the governed roster.  A degenerate empty
    roster would collapse to a bare ``--`` and widen the operation to the whole
    worktree, and an attacker-supplied pathspec (``:(exclude)...``, a glob, an
    absolute path, a ``..`` escape) would silently redefine the surface.  Both
    fail closed: the roster must be NON-EMPTY and every entry must be a plain
    repo-relative path with no pathspec magic, which the caller then pins with
    literal magic so git cannot reinterpret it.
    """
    roster = list(allowed_paths)
    if not roster:
        raise HermeticGitError(
            "empty allowed-paths roster: refusing (a bare '--' widens to the "
            "whole worktree instead of the governed slice)"
        )
    validated = []
    for raw in roster:
        text = str(raw)
        if not text.strip():
            raise HermeticGitError("empty path entry in the allowed-paths roster")
        if text.startswith(":"):
            raise HermeticGitError(
                "pathspec magic is forbidden in a roster entry: {0!r}".format(text)
            )
        if any(ch in text for ch in _PATHSPEC_GLOB_MAGIC):
            raise HermeticGitError(
                "glob pathspec magic is forbidden in a roster entry: {0!r}".format(text)
            )
        pure = PurePosixPath(text)
        if text.startswith("/") or pure.is_absolute():
            raise HermeticGitError(
                "absolute path is forbidden in a roster entry: {0!r}".format(text)
            )
        if ".." in pure.parts:
            raise HermeticGitError(
                "parent-directory escape is forbidden in a roster entry: {0!r}".format(
                    text
                )
            )
        validated.append(text)
    return validated


def _pathspec(allowed_paths):
    """Return the ``-- :(literal)<path> ...`` pathspec tail for a valid roster.

    Each validated entry is encoded with git's ``:(literal)`` magic so no glob
    or magic in the path is ever reinterpreted; an invalid or empty roster
    raises via :func:`_validate_roster`.
    """
    validated = _validate_roster(allowed_paths)
    return ["--", *(":(literal){0}".format(path) for path in validated)]


# --- §13.2 in-tree .gitattributes neutralization (fail-closed) --------------
# git consults working-tree ``.gitattributes`` during ``git add`` AND ``git
# diff``; the built-in attributes below re-encode staged/extracted bytes (CRLF
# via ``text``/``eol``/the legacy ``crlf`` alias, forced ``binary``,
# ``working-tree-encoding``, the check-in ``ident`` ``$Id$`` transform, and
# ``diff`` which flips a path between a textual and a binary patch).  The
# ``core.attributesFile=/dev/null`` + ``GIT_ATTR_NOSYSTEM=1`` pins neutralise the
# USER/SYSTEM attribute files but NOT an in-tree ``.gitattributes``, and a
# dirty/untracked one outside the roster escapes the ignored/status scans (both
# restricted to allowed paths).  So any ``.gitattributes`` whose directory
# subtree overlaps an allowed path and that carries a byte-affecting builtin
# fails closed (closes the re-review "unbound in-tree attributes" hole).
_BYTE_AFFECTING_ATTRS = frozenset(
    {"text", "eol", "working-tree-encoding", "binary", "crlf", "ident", "diff"}
)


def _content_has_byte_affecting_attr(data):
    """Return True iff ``.gitattributes`` bytes set a byte-affecting builtin.

    Every non-comment line is ``<pattern> <attr>...`` (or an ``[attr]macro``
    definition); each attribute token is normalised by stripping a leading
    ``-``/``!`` and any ``=value`` suffix, then matched case-insensitively
    against :data:`_BYTE_AFFECTING_ATTRS`.  The match is on the attribute NAME
    regardless of its set/unset/value form, and a macro definition that expands
    to one of these names trips on its own line -- deliberately conservative,
    because a fail-closed over-refusal is safe while a miss re-encodes bytes.
    """
    text = data.decode("utf-8", "surrogateescape")
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        for token in line.split()[1:]:
            name = token.lstrip("-!").split("=", 1)[0].strip().lower()
            if name in _BYTE_AFFECTING_ATTRS:
                return True
    return False


def _subtree_overlap(a_parts, b_parts):
    """Return True iff the path subtrees rooted at ``a_parts``/``b_parts`` overlap.

    Subtrees intersect iff one path is an ancestor-or-equal of the other, i.e.
    the shorter part-tuple prefixes the longer.  Root (``()``) overlaps every
    path.  A ``.gitattributes`` in directory ``a`` can govern an allowed path
    ``b`` exactly when their subtrees overlap (``a`` above ``b`` governs down;
    ``a`` inside ``b``'s subtree governs allowed files there).
    """
    n = min(len(a_parts), len(b_parts))
    return a_parts[:n] == b_parts[:n]


def _gitattributes_is_hostile(repo_root, rel, ambient_env):
    """Return True iff the ``.gitattributes`` at ``rel`` carries a byte-affecting builtin.

    Both the working-tree copy (what ``git add`` reads) and, when the path is
    tracked, the staged blob (a copy deleted from the worktree but live in the
    index) are inspected.  A working-tree ``.gitattributes`` that is present but
    NOT a regular file (symlink/FIFO/dir) cannot be vetted and fails closed here,
    mirroring the ``$GIT_DIR/info/attributes`` non-regular refusal.
    """
    fs = Path(repo_root) / rel
    if os.path.lexists(fs):
        st = os.lstat(fs)
        if not stat.S_ISREG(st.st_mode):
            raise HermeticGitError(
                "in-scope .gitattributes is not a regular file: {0}".format(rel)
            )
        if _content_has_byte_affecting_attr(fs.read_bytes()):
            return True
    listed = _run_git(
        repo_root, ["ls-files", "-z", "--", ":(literal){0}".format(rel)], ambient_env
    ).stdout
    if listed.replace(b"\x00", b""):
        blob = _run_git(
            repo_root, ["cat-file", "-p", ":0:{0}".format(rel)], ambient_env
        ).stdout
        if _content_has_byte_affecting_attr(blob):
            return True
    return False


def _assert_no_hostile_intree_attributes(repo_root, allowed_paths, ambient_env):
    """Fail closed on any in-tree ``.gitattributes`` that could re-encode the slice.

    Candidate ``.gitattributes`` paths are (A) every ancestor directory of a
    roster entry (root included) and (B) every ``.gitattributes`` at/under a
    roster entry's subtree -- the latter found with a roster-scoped ``ls-files``
    over BOTH tracked and untracked entries (``--others`` WITHOUT
    ``--exclude-standard``, because git honours an IGNORED ``.gitattributes``).
    Any candidate whose directory subtree overlaps an allowed path and that
    carries a byte-affecting builtin refuses.
    """
    validated = _validate_roster(allowed_paths)
    roster_parts = [PurePosixPath(path).parts for path in validated]

    candidates = set()
    # (A) ancestor directories -> the exact `.gitattributes` that governs down.
    for parts in roster_parts:
        for depth in range(len(parts)):
            candidates.add("/".join((*parts[:depth], ".gitattributes")))
    # (B) at/under each roster entry, scoped so the scan stays cheap and bounded.
    for scan in (["ls-files", "-z", "--cached"], ["ls-files", "-z", "--others"]):
        stdout = _run_git(repo_root, [*scan, *_pathspec(validated)], ambient_env).stdout
        for entry in stdout.split(b"\x00"):
            if not entry:
                continue
            rel = entry.decode("utf-8", "surrogateescape")
            # Case-INSENSITIVE basename: on a case-insensitive filesystem git
            # resolves its lowercase `.gitattributes` lookup to an on-disk
            # `.GITATTRIBUTES`, so a case-variant name must not escape the scan.
            if PurePosixPath(rel).name.lower() == ".gitattributes":
                candidates.add(rel)

    for rel in sorted(candidates):
        attr_dir = PurePosixPath(rel).parts[:-1]
        if not any(_subtree_overlap(attr_dir, parts) for parts in roster_parts):
            continue
        if _gitattributes_is_hostile(repo_root, rel, ambient_env):
            raise HermeticGitError(
                "in-tree .gitattributes governs an allowed path with a byte-affecting "
                "builtin (text/eol/working-tree-encoding/binary/crlf/ident/diff): "
                "{0}".format(rel)
            )
    return None


def stage_allowed(repo_root, allowed_paths, ambient_env=None):
    """Stage the allowed paths with the single §13.2 pinned staging command.

    ``git -c core.autocrlf=false -c core.eol=lf -c core.safecrlf=false
    -c core.attributesFile=/dev/null -c core.excludesFile=/dev/null
    -c core.bigFileThreshold=512m -c core.fileMode=false add -A --
    :(literal)<allowed paths>``.  The pins neutralise any clean filter /
    attribute / excludes influence and any mode/big-file reinterpretation of the
    staged bytes; the literal pathspec confines staging to the governed roster.
    An in-tree ``.gitattributes`` that git would still consult during ``git add``
    fails closed first via :func:`_assert_no_hostile_intree_attributes`.
    """
    _assert_no_hostile_intree_attributes(repo_root, allowed_paths, ambient_env)
    _run_git(
        repo_root,
        [*_STAGE_PINS, "add", "-A", *_pathspec(allowed_paths)],
        ambient_env,
    )
    return None


def ignored_scan(repo_root, allowed_paths, ambient_env=None):
    """Return the raw bytes of the §13.2 fail-closed ignored-file scan.

    ``git -c core.excludesFile=/dev/null ls-files --others --ignored
    --exclude-standard -z -- :(literal)<allowed paths>``.  ``b""`` means clean;
    any non-empty result names an ignored artifact inside an allowed path that
    must never be hidden from the patch.  The ``core.excludesFile=/dev/null``
    pin prevents an external excludes file from concealing such an artifact while
    still honouring versioned ``.gitignore`` and ``$GIT_DIR/info/exclude``.
    """
    proc = _run_git(
        repo_root,
        [
            "-c", "core.excludesFile=/dev/null",
            "ls-files", "--others", "--ignored", "--exclude-standard", "-z",
            *_pathspec(allowed_paths),
        ],
        ambient_env,
    )
    return proc.stdout


def canonical_patch(repo_root, allowed_paths, ambient_env=None):
    """Return the §13.2 canonical, hermetic, binary-safe patch bytes.

    Runs the exact pinned ``git diff`` extraction (all ``-c`` pins + ``--binary
    --full-index --no-color --no-ext-diff --no-textconv --no-renames
    --submodule=short --inter-hunk-context=0 -O/dev/null --src-prefix=a/
    --dst-prefix=b/ -U3 --cached HEAD -- :(literal)<allowed paths>``).  ``--binary
    --full-index`` carry PNG/gzip receipts replayably; the fixed env plus the
    pins make the output byte-identical across runs and inert to ambient
    hostility, and the literal pathspec confines the diff to the governed roster.
    An in-tree ``.gitattributes`` that git would still consult during extraction
    fails closed first via :func:`_assert_no_hostile_intree_attributes`.
    """
    _assert_no_hostile_intree_attributes(repo_root, allowed_paths, ambient_env)
    proc = _run_git(
        repo_root,
        [*_EXTRACT_PINS, *_EXTRACT_FLAGS, *_pathspec(allowed_paths)],
        ambient_env,
    )
    return proc.stdout
