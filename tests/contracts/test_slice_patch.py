"""Hostile-case contract for the hermetic slice-patch pipeline (w3c-0 §13.2 as CODE).

Convergence-law artifact (AGENTS.md): the git mechanism that consumed design-gate rounds 7-11
as prose is an executable module with hostile-environment tests. Every test builds a THROWAWAY
git repo; hostile ambient config/env MUST NOT change canonical patch bytes, and the fail-closed
scans MUST refuse what they were designed to refuse.

Each test is load-bearing: it fails against a no-op implementation. Byte-equality alone is not
trusted -- the env allowlist SHAPE is asserted directly, the ignored scan's bytes are inspected,
the emitted binary patch is actually APPLIED to a fresh worktree, and the fail-closed guards
(empty/exclusion rosters, linked-worktree preflight, forbidden config keys/values, an
unresolvable git binary) are each exercised.

Slice-1 registry note: this module + scripts/organization/slice_patch.py register their homes
in the slice-1 landing (kept out of slice 0's closed allowed paths by design).
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.organization.slice_patch as slice_patch

from scripts.organization.slice_patch import (
    HermeticGitError,
    canonical_patch,
    hermetic_env,
    ignored_scan,
    source_preflight,
    stage_allowed,
)


def _run(cwd, *args, env=None):
    return subprocess.run(["git", *args], cwd=cwd, env=env or hermetic_env(),
                          capture_output=True, text=True, check=True)


# The complete §13.2 H-GIT allowlist -- hermetic_env must return EXACTLY these names.
_EXPECTED_HGIT_KEYS = {
    "PATH", "TMPDIR", "HOME", "LC_ALL",
    "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM",
    "GIT_ATTR_NOSYSTEM", "GIT_TERMINAL_PROMPT",
    "GIT_NO_REPLACE_OBJECTS",
}
# Ambient behaviour variables that must NEVER survive into the hermetic env.
_LEAK_NAMES = (
    "GIT_DIFF_OPTS", "GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0",
    "GIT_EXTERNAL_DIFF", "GIT_PAGER", "GIT_EDITOR", "XDG_CONFIG_HOME",
)

_NEW_PNG = "89504e470d0a1a0a0000000d49484452000000020000000208060000001e"


class _RepoFixture:
    def __init__(self):
        self.dir = tempfile.TemporaryDirectory(prefix="slice-patch-fixture-")
        self.root = Path(self.dir.name)
        _run(self.root, "init", "-q")
        _run(self.root, "config", "user.email", "t@t")
        _run(self.root, "config", "user.name", "t")
        (self.root / "governed").mkdir()
        (self.root / "governed" / "a.txt").write_text("alpha\n")
        png = bytes.fromhex("89504e470d0a1a0a0000000d494844520000000100000001080600000010")
        (self.root / "governed" / "seed.png").write_bytes(png)
        _run(self.root, "add", "-A")
        _run(self.root, "commit", "-qm", "seed")

    def mutate(self):
        (self.root / "governed" / "a.txt").write_text("alpha\nbeta\n")
        (self.root / "governed" / "new.png").write_bytes(bytes.fromhex(_NEW_PNG))

    def cleanup(self):
        self.dir.cleanup()


HOSTILE_ENVS = [
    {"GIT_DIFF_OPTS": "-u99"},
    {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "diff.noprefix", "GIT_CONFIG_VALUE_0": "true"},
    {"GIT_EXTERNAL_DIFF": "/bin/false"},
]
HOSTILE_GLOBALS = ["diff.noprefix=true", "diff.interHunkContext=999",
                   "diff.suppressBlankEmpty=true", "diff.indentHeuristic=false"]


class SlicePatchHermeticity(unittest.TestCase):
    def setUp(self):
        self.fx = _RepoFixture()
        self.addCleanup(self.fx.cleanup)
        self.paths = ["governed"]

    # -- helpers -------------------------------------------------------------
    def _emit(self, extra_env=None, global_cfg=None):
        env = dict(os.environ)
        if extra_env:
            env.update(extra_env)
        if global_cfg:
            cfg = self.fx.root / "hostile-global.cfg"
            with cfg.open("a") as fh:
                section, kv = global_cfg.split(".", 1)
                key, value = kv.split("=", 1)
                fh.write(f"[{section}]\n\t{key} = {value}\n")
            env["GIT_CONFIG_GLOBAL"] = str(cfg)
        source_preflight(self.fx.root, ambient_env=env)
        stage_allowed(self.fx.root, self.paths, ambient_env=env)
        self.assertEqual(ignored_scan(self.fx.root, self.paths, ambient_env=env), b"")
        return canonical_patch(self.fx.root, self.paths, ambient_env=env)

    def _assert_hermetic_shape(self, ambient):
        """Assert hermetic_env(ambient) is EXACTLY the pinned allowlist (finding 6)."""
        env = hermetic_env(ambient)
        self.assertEqual(set(env), _EXPECTED_HGIT_KEYS,
                         "H-GIT env must be exactly the §13.2 allowlist, no more, no less")
        self.assertEqual(env["GIT_CONFIG_GLOBAL"], "/dev/null")
        self.assertEqual(env["GIT_CONFIG_SYSTEM"], "/dev/null")
        self.assertEqual(env["GIT_ATTR_NOSYSTEM"], "1")
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        # refs/replace/* pinned OFF so a replacement ref cannot hide a change.
        self.assertEqual(env["GIT_NO_REPLACE_OBJECTS"], "1")
        self.assertEqual(env["HOME"], "/nonexistent")
        self.assertEqual(env["LC_ALL"], "C")
        for name in _LEAK_NAMES:
            self.assertNotIn(name, env, f"{name} leaked into the hermetic env")
        return env

    def _fresh(self):
        """A throwaway seeded repo whose lifetime is bound to this test."""
        fx = _RepoFixture()
        self.addCleanup(fx.cleanup)
        return fx

    # -- env allowlist SHAPE (finding 6, finding 2) --------------------------
    def test_hermetic_env_is_exactly_the_allowlist(self):
        hostile = dict(os.environ)
        hostile.update({"GIT_DIFF_OPTS": "-u99", "GIT_CONFIG_COUNT": "1",
                        "GIT_EXTERNAL_DIFF": "/bin/false", "GIT_PAGER": "cat",
                        "XDG_CONFIG_HOME": "/tmp/evil", "GIT_CONFIG_GLOBAL": "/tmp/evil.cfg"})
        env = self._assert_hermetic_shape(hostile)
        # PATH is the single declared trust root: carried VERBATIM from the source.
        self.assertEqual(env["PATH"], hostile["PATH"])
        # finding 2: a supplied ambient missing PATH yields an EMPTY PATH -- never an
        # os.environ rescue (which would silently defeat "built solely from the source").
        self.assertEqual(hermetic_env({"TMPDIR": "/x"})["PATH"], "")
        self.assertEqual(hermetic_env({"PATH": ""})["PATH"], "")

    # -- binary receipts survive AND apply (RED: make apply real) ------------
    def test_binary_receipts_survive_and_apply(self):
        self.fx.mutate()
        patch = self._emit()
        self.assertIn(b"GIT binary patch", patch, "binary content must be carried replayably")
        # The name promises apply: replay onto a fresh, clean worktree at the same
        # seed commit and assert the binary receipt materialises byte-identical.
        dest = tempfile.TemporaryDirectory(prefix="slice-patch-apply-")
        self.addCleanup(dest.cleanup)
        destroot = Path(dest.name)
        _run(destroot, "clone", "-q", str(self.fx.root), ".")
        (destroot / "slice.patch").write_bytes(patch)
        _run(destroot, "apply", "--binary", "slice.patch")
        self.assertEqual((destroot / "governed" / "new.png").read_bytes(),
                         bytes.fromhex(_NEW_PNG),
                         "binary receipt did not survive extraction + apply")
        self.assertEqual((destroot / "governed" / "a.txt").read_text(), "alpha\nbeta\n",
                         "text change did not survive extraction + apply")

    # -- hostile ambient env is inert (RED: assert env SHAPE too) ------------
    def test_hostile_environment_variables_are_inert(self):
        self.fx.mutate()
        baseline = self._emit()
        for hostile in HOSTILE_ENVS:
            with self.subTest(hostile=hostile):
                ambient = dict(os.environ)
                ambient.update(hostile)
                # A no-op env passthrough would leak these names; the SHAPE assertion
                # fails there BEFORE byte-equality is ever consulted.
                self._assert_hermetic_shape(ambient)
                self.assertEqual(self._emit(extra_env=hostile), baseline,
                                 f"{hostile} changed canonical patch bytes")

    # -- hostile global config is inert (RED: assert env SHAPE too) ----------
    def test_hostile_global_config_is_inert(self):
        self.fx.mutate()
        baseline = self._emit()
        for cfg in HOSTILE_GLOBALS:
            with self.subTest(cfg=cfg):
                self.assertEqual(self._emit(global_cfg=cfg), baseline,
                                 f"ambient {cfg} changed canonical patch bytes")
        # A no-op env passthrough would forward the hostile GIT_CONFIG_GLOBAL; the
        # allowlist pins it to /dev/null regardless of the ambient value.
        ambient = dict(os.environ)
        ambient["GIT_CONFIG_GLOBAL"] = str(self.fx.root / "hostile-global.cfg")
        env = self._assert_hermetic_shape(ambient)
        self.assertEqual(env["GIT_CONFIG_GLOBAL"], "/dev/null",
                         "a hostile ambient GIT_CONFIG_GLOBAL must be pinned to /dev/null")

    # -- fail-closed source preflight ----------------------------------------
    def test_forbidden_local_config_refuses(self):
        _run(self.fx.root, "config", "--local", "diff.noprefix", "true")
        with self.assertRaises(HermeticGitError):
            source_preflight(self.fx.root)

    def test_nonempty_info_attributes_refuses(self):
        attrs = self.fx.root / ".git" / "info" / "attributes"
        attrs.parent.mkdir(exist_ok=True)
        attrs.write_text("* binary\n")
        with self.assertRaises(HermeticGitError):
            source_preflight(self.fx.root)

    def test_preflight_handles_linked_worktree(self):
        # §13.2 runs the preflight INSIDE a linked worktree, where `git config
        # --worktree` is fatal unless extensions.worktreeConfig is enabled.  The
        # preflight must not use that flag: it must SUCCEED here (a regression to
        # --worktree raises the fatal error and fails this assertIsNone)...
        holder = tempfile.TemporaryDirectory(prefix="slice-patch-linked-")
        self.addCleanup(holder.cleanup)
        linked = Path(holder.name) / "wt"
        _run(self.fx.root, "worktree", "add", "--detach", "--no-checkout", str(linked))
        self.assertIsNone(source_preflight(linked))
        # ...and still ENFORCE: a forbidden shared-config key refuses from the linked wt.
        _run(self.fx.root, "config", "--local", "diff.noprefix", "true")
        with self.assertRaises(HermeticGitError):
            source_preflight(linked)

    # -- finding 4: bigFileThreshold pinned + forbidden ----------------------
    def test_local_big_file_threshold_is_inert_and_refused(self):
        self.fx.mutate()
        stage_allowed(self.fx.root, self.paths)
        baseline = canonical_patch(self.fx.root, self.paths)
        self.assertIsInstance(baseline, bytes)
        self.assertIn(b"+beta", baseline)
        # The -c core.bigFileThreshold pin overrides a hostile local value: a local
        # core.bigFileThreshold=1 must NOT change the emitted bytes.
        _run(self.fx.root, "config", "--local", "core.bigFileThreshold", "1")
        stage_allowed(self.fx.root, self.paths)
        self.assertEqual(canonical_patch(self.fx.root, self.paths), baseline,
                         "core.bigFileThreshold pin failed to neutralise a local override")
        # ...and the preflight refuses the override outright (fails vs a no-op preflight).
        with self.assertRaises(HermeticGitError):
            source_preflight(self.fx.root)

    # -- finding 4: fileMode staging pin + value-aware refusal ---------------
    def test_filemode_staging_pin_and_false_refusal(self):
        # A content change AND an exec-bit flip on the same tracked governed file.
        self.fx.mutate()
        os.chmod(self.fx.root / "governed" / "a.txt", 0o755)
        _run(self.fx.root, "config", "--local", "core.fileMode", "true")  # exec bit honoured
        stage_allowed(self.fx.root, self.paths)
        patch = canonical_patch(self.fx.root, self.paths)
        # Content is staged -> fails against a no-op stage_allowed.
        self.assertIn(b"+beta", patch, "stage_allowed must actually stage the governed slice")
        # Mode-only noise is dropped by the core.fileMode=false staging pin -> fails if
        # that staging pin is removed (local core.fileMode=true would record 100755).
        self.assertNotIn(b"new mode 100755", patch,
                         "core.fileMode staging pin must keep mode-only bits out of the patch")
        # Value-aware preflight: the benign git-init default (true) is ALLOWED -- a naive
        # name-only forbid would wrongly refuse here and fail this assertion.
        self.assertIsNone(source_preflight(self.fx.root))
        # ...but a hostile local core.fileMode=false (mode-suppression) REFUSES.
        _run(self.fx.root, "config", "--local", "core.fileMode", "false")
        with self.assertRaises(HermeticGitError):
            source_preflight(self.fx.root)

    # -- finding 5: roster validation ----------------------------------------
    def test_empty_roster_refuses(self):
        for fn in (stage_allowed, ignored_scan, canonical_patch):
            with self.subTest(fn=fn.__name__):
                with self.assertRaises(HermeticGitError):
                    fn(self.fx.root, [])

    def test_exclusion_pathspec_roster_refuses(self):
        for fn in (stage_allowed, ignored_scan, canonical_patch):
            with self.subTest(fn=fn.__name__):
                with self.assertRaises(HermeticGitError):
                    fn(self.fx.root, [":(exclude)governed/seed.png"])

    def test_magic_absolute_and_traversal_roster_refuses(self):
        for bad in ["governed/*.png", "/etc/passwd", "../escape", "governed/../../x"]:
            with self.subTest(bad=bad):
                with self.assertRaises(HermeticGitError):
                    stage_allowed(self.fx.root, [bad])

    # -- ignored governed artifact is caught (RED: bytes nonzero + staging) ---
    def test_ignored_governed_file_is_caught(self):
        self.fx.mutate()  # real staged content so the staging step is load-bearing
        (self.fx.root / ".gitignore").write_text("governed/hidden.bin\n")
        _run(self.fx.root, "add", ".gitignore")
        _run(self.fx.root, "commit", "-qm", "ignore rule")
        (self.fx.root / "governed" / "hidden.bin").write_bytes(b"x")
        self.assertIsNone(stage_allowed(self.fx.root, self.paths))
        # Staging is load-bearing: the governed mutation is really in the index now
        # (a no-op stage_allowed leaves --cached empty and fails here).
        staged = _run(self.fx.root, "diff", "--cached", "--name-only").stdout
        self.assertIn("governed/a.txt", staged,
                      "stage_allowed must actually stage the governed slice")
        scan = ignored_scan(self.fx.root, self.paths)
        self.assertIsInstance(scan, bytes, "a no-op scan returning None must fail")
        self.assertNotEqual(scan, b"",
                            "an ignored governed artifact must be reported, never hidden")
        self.assertIn(b"governed/hidden.bin", scan)

    # -- finding 2 + 3: unresolvable git wraps as HermeticGitError -----------
    def test_empty_path_raises_hermetic_error(self):
        # An empty ambient PATH is used VERBATIM (finding 2), so git cannot be found;
        # the resulting OSError is wrapped in HermeticGitError, not leaked as
        # FileNotFoundError (finding 3).  A no-op of either fix fails this assertion.
        with self.assertRaises(HermeticGitError):
            canonical_patch(self.fx.root, self.paths, ambient_env={"PATH": ""})

    def test_double_extraction_is_byte_identical(self):
        # Determinism ALONE is vacuously true for a constant/empty no-op, so the
        # extraction must ALSO be proven to reflect real staged content: identical,
        # non-empty, and carrying the changed governed path + its staged text edit.
        self.fx.mutate()
        first = self._emit()
        second = canonical_patch(self.fx.root, self.paths)
        self.assertEqual(first, second, "the canonical extraction must be deterministic")
        self.assertNotEqual(first, b"", "a constant/empty no-op extraction must fail here")
        self.assertIn(b"governed/a.txt", first,
                      "the extraction must name the changed governed path")
        self.assertIn(b"+beta", first,
                      "the extraction must carry the staged text change, not a constant")

    # -- ADV-4: config.worktree DORMANCY (defect 1) --------------------------
    def _write_worktree_config(self, fx, body):
        wt = fx.root / ".git" / "config.worktree"
        wt.write_text(body)
        return wt

    def test_config_worktree_dormancy(self):
        # A DORMANT config.worktree (extensions.worktreeConfig OFF) is INERT exactly
        # as git treats it: git never reads it, so the preflight must not either.
        #
        # Arm 1 -- dormant forbidden KEY must NOT falsely refuse.  The pre-fix module
        # read config.worktree unconditionally and would raise on diff.noprefix here.
        dormant = self._fresh()
        self._write_worktree_config(dormant, "[diff]\n\tnoprefix = true\n")
        self.assertIsNone(source_preflight(dormant.root),
                          "a dormant config.worktree must be inert, not a false refusal")

        # Arm 2 -- dormant value must NOT MASK an effective common value.  A common
        # core.fileMode=false (forbidden) with a dormant config.worktree core.fileMode=true
        # must STILL refuse; the pre-fix module let the worktree 'true' hide the refusal.
        masked = self._fresh()
        _run(masked.root, "config", "--local", "core.fileMode", "false")
        self._write_worktree_config(masked, "[core]\n\tfileMode = true\n")
        with self.assertRaises(HermeticGitError):
            source_preflight(masked.root)

        # Arm 3 -- when extensions.worktreeConfig IS enabled, an ACTIVE config.worktree
        # forbidden key DOES refuse (the fix must not blanket-ignore config.worktree).
        active = self._fresh()
        _run(active.root, "config", "--local", "extensions.worktreeConfig", "true")
        self._write_worktree_config(active, "[diff]\n\tnoprefix = true\n")
        with self.assertRaises(HermeticGitError):
            source_preflight(active.root)

    # -- unbound in-tree .gitattributes (defect 2) ---------------------------
    def test_intree_gitattributes_hostility_refuses(self):
        # git consults working-tree .gitattributes during `git add`/`git diff`;
        # a hostile in-tree file carrying a byte-affecting builtin re-encodes the
        # staged/extracted bytes and, being outside the roster, escapes the scans.
        # Both attribute-consulting operations must fail closed.
        self.fx.mutate()
        (self.fx.root / ".gitattributes").write_text("governed/* text eol=crlf\n")
        for fn in (stage_allowed, canonical_patch):
            with self.subTest(fn=fn.__name__, form="root text eol=crlf"):
                with self.assertRaises(HermeticGitError):
                    fn(self.fx.root, self.paths)

        # The `binary` macro at a NESTED in-scope location is caught too.
        (self.fx.root / ".gitattributes").unlink()
        (self.fx.root / "governed" / ".gitattributes").write_text("* binary\n")
        with self.assertRaises(HermeticGitError):
            stage_allowed(self.fx.root, self.paths)
        with self.assertRaises(HermeticGitError):
            canonical_patch(self.fx.root, self.paths)

        # Negative control 1: an OUT-OF-SCOPE .gitattributes (sibling subtree) with a
        # byte-affecting builtin does NOT refuse -- the guard is scoped, not blanket.
        (self.fx.root / "governed" / ".gitattributes").unlink()
        (self.fx.root / "other").mkdir()
        (self.fx.root / "other" / ".gitattributes").write_text("* binary\n")
        self.assertIsNone(stage_allowed(self.fx.root, self.paths),
                          "an out-of-scope .gitattributes must not trip the guard")

        # Negative control 2: an in-scope but NON-byte-affecting attribute is allowed,
        # proving the content parse is specific (fails a 'refuse on any .gitattributes').
        (self.fx.root / "other" / ".gitattributes").unlink()
        (self.fx.root / "governed" / ".gitattributes").write_text("* export-ignore\n")
        self.assertIsNone(stage_allowed(self.fx.root, self.paths),
                          "a benign in-scope attribute must not trip the guard")

    # -- r3b finding 1: crlf/ident/diff are byte-affecting builtins too -------
    def test_intree_crlf_ident_diff_attrs_refuse(self):
        # git's `crlf` (legacy text/eol alias), `ident` ($Id$ check-in transform),
        # and `diff` (text-vs-binary patch generation) each re-encode staged or
        # extracted bytes, so an in-scope .gitattributes carrying ANY of them must
        # fail closed on BOTH attribute-consuming operations.  Dropping a name from
        # _BYTE_AFFECTING_ATTRS reddens exactly its subTest.
        for attr in ("ident", "crlf", "diff"):
            (self.fx.root / ".gitattributes").write_text("governed/* {0}\n".format(attr))
            for fn in (stage_allowed, canonical_patch):
                with self.subTest(attr=attr, fn=fn.__name__):
                    with self.assertRaises(HermeticGitError):
                        fn(self.fx.root, self.paths)

    # -- r3b finding 2: local attr.tree redirects the attribute lookup --------
    def test_local_attr_tree_refuses(self):
        # attr.tree makes git read .gitattributes from an ARBITRARY tree/ref,
        # bypassing the entire working-tree/index candidate scan.  A local value
        # must refuse in the preflight; a forbidden-key set omitting "attr.tree"
        # (or a case-sensitive miss) reddens this test.
        _run(self.fx.root, "config", "--local", "attr.tree", "HEAD")
        with self.assertRaises(HermeticGitError):
            source_preflight(self.fx.root)

    # -- r3b finding 3: a case-variant .GITATTRIBUTES is still caught ---------
    def test_case_insensitive_gitattributes_refuses(self):
        # On a case-insensitive filesystem git resolves its lowercase
        # `.gitattributes` lookup to an on-disk `.GITATTRIBUTES`; ls-files reports
        # that file under its literal (uppercase) name, so the candidate basename
        # comparison must be case-INSENSITIVE.  A case-sensitive compare drops the
        # uppercase file from the roster and reddens this test (the guard here is
        # our scan, so the refusal is deterministic on any filesystem).
        (self.fx.root / "governed" / ".GITATTRIBUTES").write_text("* text eol=crlf\n")
        for fn in (stage_allowed, canonical_patch):
            with self.subTest(fn=fn.__name__):
                with self.assertRaises(HermeticGitError):
                    fn(self.fx.root, self.paths)

    # -- r3b finding 4: staged-only .gitattributes (deleted from worktree) ----
    def test_staged_only_gitattributes_fallback_refuses(self):
        # git falls back to the INDEX copy of .gitattributes when the worktree file
        # is missing, so a hostile .gitattributes staged then deleted from the
        # worktree still governs `git add`/`git diff`.  The scan must inspect the
        # staged blob (ls-files --cached + cat-file :0:); deleting that index-
        # fallback arm of _gitattributes_is_hostile reddens this test.
        ga = self.fx.root / "governed" / ".gitattributes"
        ga.write_text("* text eol=crlf\n")
        _run(self.fx.root, "add", "governed/.gitattributes")  # live in the index
        ga.unlink()                                            # ...absent from the worktree
        self.assertFalse(ga.exists(), "the worktree copy must be gone for this arm")
        for fn in (stage_allowed, canonical_patch):
            with self.subTest(fn=fn.__name__):
                with self.assertRaises(HermeticGitError):
                    fn(self.fx.root, self.paths)

    # -- r3b finding 5: a replacement ref cannot hide a real change ----------
    def test_replacement_ref_is_neutralized(self):
        # git honours refs/replace/* by default: replacing the HEAD blob of a
        # changed file with its staged blob makes `git diff --cached HEAD` show
        # NOTHING.  GIT_NO_REPLACE_OBJECTS=1 (pinned in hermetic_env) neutralises
        # it, so the canonical extraction must still carry the change.
        self.fx.mutate()  # governed/a.txt -> alpha\nbeta ; governed/new.png added
        stage_allowed(self.fx.root, self.paths)  # staged blob of a.txt now in the DB
        old_blob = _run(self.fx.root, "rev-parse", "HEAD:governed/a.txt").stdout.strip()
        new_blob = _run(self.fx.root, "rev-parse", ":governed/a.txt").stdout.strip()
        self.assertNotEqual(old_blob, new_blob, "the staged blob must differ from HEAD")
        _run(self.fx.root, "replace", old_blob, new_blob)  # HEAD blob -> staged blob

        # Positive control: with refs/replace/* HONOURED the +beta change is hidden,
        # proving the attack is real (so the neutralization below is load-bearing,
        # not vacuous).  Rebuild the hermetic env WITHOUT the pin to honour replaces.
        honoured = hermetic_env()
        honoured.pop("GIT_NO_REPLACE_OBJECTS", None)
        raw = subprocess.run(
            ["git", "diff", "--cached", "HEAD", "--", "governed/a.txt"],
            cwd=str(self.fx.root), env=honoured, capture_output=True,
        ).stdout
        self.assertNotIn(b"+beta", raw,
                         "sanity: the replacement ref must actually hide the change")

        # The canonical extraction pins GIT_NO_REPLACE_OBJECTS=1 -> +beta reappears.
        patch = canonical_patch(self.fx.root, self.paths)
        self.assertIn(b"+beta", patch,
                      "GIT_NO_REPLACE_OBJECTS must neutralize a hostile replacement ref")

    # -- non-regular $GIT_DIR/info/attributes RED ----------------------------
    def test_symlink_info_attributes_refuses(self):
        # $GIT_DIR/info/attributes as a SYMLINK to a nonempty file must REFUSE: the
        # preflight lstat()s the path and rejects any non-regular type BEFORE it could
        # read the (out-of-band) target bytes.  Asserting the 'not a regular file'
        # message proves the TYPE guard fired -- an os.stat() mutant (follow-symlink)
        # would instead refuse via the 'non-empty' branch and miss this arm.
        info = self.fx.root / ".git" / "info"
        info.mkdir(exist_ok=True)
        target = self.fx.root / ".git" / "info" / "attributes.target"
        target.write_text("governed/* text eol=crlf\n")
        link = info / "attributes"
        os.symlink(target, link)
        with self.assertRaises(HermeticGitError) as caught:
            source_preflight(self.fx.root)
        self.assertIn("not a regular file", str(caught.exception),
                      "the symlink must be refused on TYPE, not merely on size")

    # -- _run_git actually passes hermetic_env to subprocess.run -------------
    def test_run_git_passes_hermetic_env_to_subprocess(self):
        # A mutant that dropped `env=hermetic_env(...)` (inheriting os.environ) or
        # passed os.environ directly must be killed.  Spy on subprocess.run and assert
        # every git child receives EXACTLY the hermetic env: shaped as the allowlist,
        # carrying the ambient TMPDIR marker, and free of the hostile ambient var.
        captured = []
        real_run = slice_patch.subprocess.run

        def spy(argv, *args, **kwargs):
            captured.append(kwargs.get("env"))
            return real_run(argv, *args, **kwargs)

        ambient = dict(os.environ)
        marker = "/tmp/slice-patch-tmpdir-marker"
        ambient["TMPDIR"] = marker
        ambient["GIT_DIFF_OPTS"] = "-u99"  # hostile: must never reach the child
        with mock.patch.object(slice_patch.subprocess, "run", spy):
            source_preflight(self.fx.root, ambient_env=ambient)

        self.assertTrue(captured, "the preflight must actually spawn git via subprocess.run")
        expected = hermetic_env(ambient)
        for env in captured:
            self.assertIsNotNone(
                env, "_run_git must pass an explicit env, never inherit os.environ")
            self.assertEqual(set(env), _EXPECTED_HGIT_KEYS,
                             "the child env must be exactly the §13.2 allowlist")
            self.assertEqual(env["TMPDIR"], marker,
                             "the ambient TMPDIR must plumb through hermetic_env to the child")
            self.assertNotIn("GIT_DIFF_OPTS", env,
                             "a hostile ambient var must not reach subprocess.run")
            self.assertEqual(env, expected,
                             "the child env must equal hermetic_env(ambient) verbatim")


if __name__ == "__main__":
    unittest.main()
