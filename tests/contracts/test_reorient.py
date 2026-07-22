"""Failing-first contract for the reorient composer (W8-O rev 3 design as CODE).

The composer derives a live-tree orientation board from git ground truth + a closed,
policy-declared roster of lane records. It OWNS NO TRUTH: every field is a projection; a
receipt binds every input; any drift invalidates it. NO TIMERS exist anywhere (operator
decision 2026-07-16: wall-clock pressure on orientation is a defect, not a feature — RED 1
treats a reintroduced budget/timer section as an unknown-key violation).

Observed-failing law: this suite is authored BEFORE scripts/organization/reorient.py exists.
The pre-build witness class is MODULE-ABSENT (every arm fails on the composer's absence —
recorded as such in the observation receipt); each arm's behavioral bite is then proven
post-build by its named probe (18 probes, §9 of the design), where a probe that flips nothing
is vacuous and fails.

Seam contract (REVIEWED design surface, not incidental internals — the build must provide):
- ``reorient.main(argv) -> int`` (importable; the CLI wraps it).
- ``reorient._records_manifest(repo_root, policy)`` — called once per observation pass
  (pass A and pass B both), returning the record/census manifest the passes compare.
- Pair writes go through ``os.replace`` (board first, receipt last — the commit point).
No other internals are contract. Tests never modify this repository; every fixture is a
throwaway temp repo. RED numbering matches the design (RED 19 WITHDRAWN by operator —
placeholder comment below; numbering preserved).
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest

try:  # the landed slice-0 mechanism (test_doc_authority.py): stdlib on 3.11+, tomli before
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - platform-dependent import path
    import tomli as tomllib
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_REL = "contracts/reorient_policy.toml"
TOOL_REL = "scripts/organization/reorient.py"
BOARD_REL = "scratchpad/active/reorient/board/board.json"
RECEIPT_REL = "scratchpad/active/reorient/board/board.receipt.json"
NOW = "2026-07-16T00:00:00Z"

DISCIPLINE_KEYS = {
    "read_only_snapshots", "no_self_fold", "conductor_only_integration",
    "receipt_interrupt_triggers", "unverified_scout", "one_writer_per_lane",
    "fan_out_ceiling", "exact_key_caching", "discipline_enforced",
}
TOP_KEYS = {
    "contract_id", "schema_version", "board_schema_version", "receipt_schema_version",
    "discipline", "job_states", "verdict_grammar", "census", "lane",
}
BOARD_TOP_KEYS = {
    "contract_id", "schema_version", "repo", "branches", "worktrees", "lanes",
    "undeclared", "policy_sha256",
}
RECEIPT_KEYS = {
    "contract_id", "schema_version", "provenance", "toolchain", "repo_head_sha",
    "git_state_sha256", "policy_sha256", "tool_sha256", "board_sha256", "inputs",
    "inputs_manifest_sha256", "discipline", "discipline_enforced",
}
LANE_ROW_KEYS = {"id", "priority", "charter", "records", "verification"}
RECORD_ROW_KEYS = {"path", "exists", "sha256", "verdict_lines"}
WT_ROW_KEYS = {"path", "status", "head_sha", "branch_or_detached", "dirty_line_count", "lane_lock"}
REAL_LANE_IDS = {
    "plan", "w8o", "w7", "org", "slice-patch", "ratchet", "source-foundation",
    "e2e-fixture", "w6", "w8", "lexguard", "slice0",
}
CHARTERS = {"ACTIVE", "QUEUED", "PARKED", "LANDED", "RECORD"}


def _sha256(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git(cwd, *args, env=None):
    return subprocess.run(["git", *args], cwd=str(cwd), env=env,
                          capture_output=True, text=True, check=True)


def _policy_toml(lanes, watch_globs=None, discipline_enforced="false", extra=""):
    """A complete, closed fixture policy. `lanes` = [(id, priority, charter, [records])]."""
    globs = watch_globs or ["scratchpad/work/*.md", "scratchpad/active/*/*/*"]
    parts = [
        'contract_id = "ReorientPolicy"',
        "schema_version = 1",
        "board_schema_version = 1",
        "receipt_schema_version = 1",
        "",
        "[discipline]",
        "read_only_snapshots = true",
        "no_self_fold = true",
        "conductor_only_integration = true",
        'receipt_interrupt_triggers = ["failure", "invalidation", "gate-readiness"]',
        "unverified_scout = true",
        "one_writer_per_lane = true",
        "fan_out_ceiling = 6",
        "exact_key_caching = true",
        f"discipline_enforced = {discipline_enforced}",
        "",
        "[job_states]",
        'values = ["PASS", "FAIL", "INFRA_BLOCKED", "CANCELLED", "STALE"]',
        "",
        "[verdict_grammar]",
        "patterns = [",
        '  "^DESIGN-VERDICT: .+$",',
        '  "^VERDICT: .+$",',
        '  "^ADVERSARIAL-VERDICT: .+$",',
        '  "^[A-Z][A-Z0-9-]*-STATUS: .+$",',
        "]",
        "",
        "[census]",
        "watch_globs = [" + ", ".join(f'"{g}"' for g in globs) + "]",
        "",
    ]
    for lane_id, prio, charter, records in lanes:
        parts += [
            "[[lane]]",
            f'id = "{lane_id}"',
            f"priority = {prio}",
            f'charter = "{charter}"',
            "records = [" + ", ".join(f'"{r}"' for r in records) + "]",
            "",
        ]
    return "\n".join(parts) + extra


class _Repo:
    """Throwaway fixture repo with its own policy + one declared record."""

    def __init__(self, lanes=None, **policy_kw):
        self.dir = tempfile.TemporaryDirectory(prefix="reorient-fixture-")
        self.root = Path(self.dir.name).resolve()
        _git(self.root, "init", "-q")
        _git(self.root, "config", "user.email", "t@t")
        _git(self.root, "config", "user.name", "t")
        # unique seed bytes per fixture: two repos minted in the same second must
        # still get DISTINCT trees/commits (RED 11 compares two repos' heads)
        (self.root / "seed.txt").write_text(f"seed {os.urandom(8).hex()}\n")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "seed")
        (self.root / "contracts").mkdir()
        (self.root / "scratchpad" / "work").mkdir(parents=True)
        (self.root / "scratchpad" / "active" / "alpha" / "design").mkdir(parents=True)
        self.record = self.root / "scratchpad" / "work" / "alpha.md"
        self.record.write_text("prose\nDESIGN-VERDICT: REVISE (r1)\nmore prose\n")
        lanes = lanes or [("alpha", 1, "ACTIVE", ["scratchpad/work/alpha.md"])]
        (self.root / POLICY_REL).write_text(_policy_toml(lanes, **policy_kw))

    def cleanup(self):
        self.dir.cleanup()


def _run_tool(repo_root, *args, env=None, cwd=REPO_ROOT):
    argv = [sys.executable, "-m", "scripts.organization.reorient",
            "--repo", str(repo_root), *args]
    return subprocess.run(argv, cwd=str(cwd), env=env or dict(os.environ),
                          capture_output=True, text=True)


def _check(repo_root, now=NOW, env=None, cwd=REPO_ROOT):
    return _run_tool(repo_root, "--now", now, "check", env=env, cwd=cwd)


def _verify(repo_root, env=None, cwd=REPO_ROOT):
    return _run_tool(repo_root, "verify", env=env, cwd=cwd)


def _board(repo_root):
    return json.loads((Path(repo_root) / BOARD_REL).read_text())


def _receipt(repo_root):
    return json.loads((Path(repo_root) / RECEIPT_REL).read_text())


def _import_tool():
    import importlib
    return importlib.import_module("scripts.organization.reorient")


class ReorientContract(unittest.TestCase):
    def setUp(self):
        self.fx = _Repo()
        self.addCleanup(self.fx.cleanup)

    def _fresh(self, **kw):
        fx = _Repo(**kw)
        self.addCleanup(fx.cleanup)
        return fx

    # -- RED 1: the policy contract is CLOSED (and the timer removal is enforced) ----
    def test_policy_exists_and_closed(self):
        real = REPO_ROOT / POLICY_REL
        self.assertTrue(real.exists(), "cargo policy missing from the worktree under test")
        data = tomllib.loads(real.read_text())
        self.assertEqual(set(data), TOP_KEYS, "top-level policy keys are a CLOSED set")
        self.assertEqual(set(data["discipline"]), DISCIPLINE_KEYS)
        self.assertIs(data["discipline"]["discipline_enforced"], False)
        self.assertEqual(len(data["job_states"]["values"]), 5)
        self.assertEqual(len(data["verdict_grammar"]["patterns"]), 4)
        rows = data["lane"]
        self.assertEqual({r["id"] for r in rows}, REAL_LANE_IDS)
        self.assertEqual(len(rows), 12, "eleven work lanes + the plan record")
        prios = [r["priority"] for r in rows]
        self.assertEqual(len(prios), len(set(prios)), "priorities are UNIQUE")
        for r in rows:
            self.assertIn(r["charter"], CHARTERS)
            self.assertTrue(r["records"], f"lane {r['id']} roster must be non-empty")
        # Violation fixtures run through the TOOL: fail-closed exit 2, nothing written.
        bad_budget = self._fresh(extra="\n[budgets]\nstart_barrier_seconds = 180\n")
        p = _check(bad_budget.root)
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertTrue(p.stdout.startswith("REORIENT: FAIL policy"),
                        "a reintroduced timer section is an unknown-key violation")
        self.assertFalse((bad_budget.root / BOARD_REL).exists())
        dup = self._fresh(lanes=[("a", 1, "ACTIVE", ["scratchpad/work/alpha.md"]),
                                 ("b", 1, "QUEUED", ["scratchpad/work/alpha.md"])])
        p = _check(dup.root)
        self.assertEqual(p.returncode, 2)
        self.assertTrue(p.stdout.startswith("REORIENT: FAIL policy"))
        weird = self._fresh(lanes=[("a", 1, "SOMEDAY", ["scratchpad/work/alpha.md"])])
        p = _check(weird.root)
        self.assertEqual(p.returncode, 2)
        # Positive control: the minimal valid fixture passes.
        p = _check(self.fx.root)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    # -- RED 2: board == independently computed git answers ---------------------------
    def test_board_derives_from_git_ground_truth(self):
        wt = Path(tempfile.mkdtemp(prefix="reorient-wt-")).resolve() / "wt"
        _git(self.fx.root, "worktree", "add", "-q", str(wt))
        self.addCleanup(lambda: _git(self.fx.root, "worktree", "remove", "--force", str(wt)))
        p = _check(self.fx.root)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        board = _board(self.fx.root)
        head = _git(self.fx.root, "rev-parse", "HEAD").stdout.strip()
        branch = _git(self.fx.root, "branch", "--show-current").stdout.strip()
        tracked = len(_git(self.fx.root, "ls-files").stdout.splitlines())
        self.assertEqual(board["repo"]["head_sha"], head)
        self.assertEqual(board["repo"]["head_branch_or_detached"], branch)
        self.assertEqual(board["repo"]["tracked_file_count"], tracked)
        names = {b["name"] for b in board["branches"]}
        self.assertIn(branch, names)
        wt_rows = [w for w in board["worktrees"] if w["path"] == str(wt.resolve())]
        self.assertEqual(len(wt_rows), 1, board["worktrees"])
        self.assertEqual(wt_rows[0]["status"], "present")
        self.assertEqual(wt_rows[0]["dirty_line_count"], 0)

    # -- RED 3: verdict lines are anchored, ordered, byte-verbatim --------------------
    def test_board_projects_verdict_lines_verbatim(self):
        self.fx.record.write_text(
            "intro prose\n"
            "DESIGN-VERDICT: REVISE (r1)\n"
            "note that DESIGN-VERDICT: approve appearing mid-sentence must not match\n"
            "VERDICT: approve\n"
        )
        self.assertEqual(_check(self.fx.root).returncode, 0)
        (lane,) = _board(self.fx.root)["lanes"]
        (rec,) = lane["records"]
        self.assertEqual(rec["verdict_lines"],
                         ["DESIGN-VERDICT: REVISE (r1)", "VERDICT: approve"],
                         "anchored match, file order, byte-verbatim, no decoys")

    # -- RED 4: golden closed shape; the board never owns a status (M1) ---------------
    def test_board_schema_is_closed_and_never_owns_status(self):
        wt_parent = Path(tempfile.mkdtemp(prefix="reorient-missing-"))
        wt = wt_parent / "gone"
        _git(self.fx.root, "worktree", "add", "-q", str(wt))
        shutil.rmtree(wt)  # a worktree whose directory vanished: reported, never skipped
        self.addCleanup(lambda: _git(self.fx.root, "worktree", "prune"))
        self.assertEqual(_check(self.fx.root).returncode, 0)
        board = _board(self.fx.root)
        self.assertEqual(set(board), BOARD_TOP_KEYS)
        self.assertEqual(set(board["repo"]),
                         {"head_sha", "head_branch_or_detached", "status_clean",
                          "status_line_count", "tracked_file_count"})
        for row in board["worktrees"]:
            self.assertEqual(set(row), WT_ROW_KEYS)
        missing = [w for w in board["worktrees"] if w["status"] == "missing"]
        self.assertTrue(missing, "the vanished worktree must appear with status=missing")
        for m in missing:
            self.assertIsNone(m["head_sha"])
            self.assertIsNone(m["branch_or_detached"])
            self.assertIsNone(m["dirty_line_count"])
            self.assertIsNone(m["lane_lock"])
        for lane in board["lanes"]:
            self.assertEqual(set(lane), LANE_ROW_KEYS)
            self.assertEqual(lane["verification"], "UNVERIFIED")
            for rec in lane["records"]:
                self.assertEqual(set(rec), RECORD_ROW_KEYS)

    # -- RED 5: the receipt binds every input + the tool itself -----------------------
    def test_receipt_binds_every_input_and_the_tool(self):
        self.assertEqual(_check(self.fx.root).returncode, 0)
        rec = _receipt(self.fx.root)
        self.assertEqual(set(rec), RECEIPT_KEYS)
        self.assertEqual(set(rec["provenance"]), {"generated_utc", "command"})
        self.assertEqual(set(rec["toolchain"]), {"python", "git"})
        self.assertEqual(rec["policy_sha256"], _sha256(self.fx.root / POLICY_REL))
        self.assertEqual(rec["tool_sha256"], _sha256(REPO_ROOT / TOOL_REL))
        self.assertEqual(rec["board_sha256"], _sha256(self.fx.root / BOARD_REL))
        paths = {i["path"] for i in rec["inputs"]}
        self.assertIn("scratchpad/work/alpha.md", paths)
        for i in rec["inputs"]:
            self.assertEqual(i["sha256"], _sha256(self.fx.root / i["path"]))
        self.assertEqual(rec["discipline"]["discipline_enforced"], False)
        self.assertIs(rec["discipline_enforced"], False)

    # -- RED 6: one drifted record byte ⇒ STALE ---------------------------------------
    def test_stale_input_invalidates_receipt(self):
        self.assertEqual(_check(self.fx.root).returncode, 0)
        self.assertEqual(_verify(self.fx.root).returncode, 0, "positive control")
        self.fx.record.write_text(self.fx.record.read_text() + "x")
        p = _verify(self.fx.root)
        self.assertEqual(p.returncode, 3)
        self.assertIn("STALE drifted=scratchpad/work/alpha.md", p.stdout)

    # -- RED 7: policy or tool drift ⇒ STALE -------------------------------------------
    def test_stale_tool_or_policy_invalidates_receipt(self):
        self.assertEqual(_check(self.fx.root).returncode, 0)
        pol = self.fx.root / POLICY_REL
        original = pol.read_text()
        pol.write_text(original + "\n# drifted\n")
        self.assertEqual(_verify(self.fx.root).returncode, 3)
        pol.write_text(original)
        self.assertEqual(_verify(self.fx.root).returncode, 0, "restore control")
        # tool drift: run verify through a byte-drifted COPY of the module tree
        alt = Path(tempfile.mkdtemp(prefix="reorient-toolcopy-"))
        for rel in ["scripts/__init__.py", "scripts/organization/__init__.py", TOOL_REL]:
            src = REPO_ROOT / rel
            dst = alt / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.exists():
                dst.write_bytes(src.read_bytes())
            else:
                dst.write_bytes(b"")
        p = _verify(self.fx.root, cwd=alt)
        self.assertEqual(p.returncode, 0, "identical copy still verifies: " + p.stdout + p.stderr)
        with (alt / TOOL_REL).open("ab") as fh:
            fh.write(b"\n# drift\n")
        p = _verify(self.fx.root, cwd=alt)
        self.assertEqual(p.returncode, 3, "a modified composer cannot keep an old board alive")

    # -- RED 8: missing declared input fails closed, writes NOTHING (M3) --------------
    def test_missing_declared_input_fails_closed(self):
        self.fx.record.unlink()
        p = _check(self.fx.root)
        self.assertEqual(p.returncode, 2)
        self.assertIn("REORIENT: FAIL missing=scratchpad/work/alpha.md", p.stdout)
        self.assertFalse((self.fx.root / BOARD_REL).exists())
        self.assertFalse((self.fx.root / RECEIPT_REL).exists())

    # -- RED 9: identical state ⇒ byte-identical outputs ------------------------------
    def test_board_bytes_are_deterministic(self):
        self.assertEqual(_check(self.fx.root).returncode, 0)
        b1 = (self.fx.root / BOARD_REL).read_bytes()
        r1 = (self.fx.root / RECEIPT_REL).read_bytes()
        self.assertEqual(_check(self.fx.root).returncode, 0)
        self.assertEqual((self.fx.root / BOARD_REL).read_bytes(), b1)
        self.assertEqual((self.fx.root / RECEIPT_REL).read_bytes(), r1)

    # -- RED 10: generation writes ONLY the pair; .git (incl. index) untouched (M9) ---
    def test_outputs_only_and_git_untouched(self):
        # stat-stale index: touch a tracked file so an optional refresh WOULD rewrite it
        seed = self.fx.root / "seed.txt"
        os.utime(seed, (os.stat(seed).st_atime, os.stat(seed).st_mtime + 5))
        index_before = (self.fx.root / ".git" / "index").read_bytes()
        inventory = {}
        for p in self.fx.root.rglob("*"):
            if p.is_file() and ".git" not in p.parts:
                inventory[str(p.relative_to(self.fx.root))] = _sha256(p)
        self.assertEqual(_check(self.fx.root).returncode, 0)
        self.assertEqual((self.fx.root / ".git" / "index").read_bytes(), index_before,
                         "read-only generation must leave .git/index byte-untouched")
        after = {}
        for p in self.fx.root.rglob("*"):
            if p.is_file() and ".git" not in p.parts:
                after[str(p.relative_to(self.fx.root))] = _sha256(p)
        changed = {k for k in after if inventory.get(k) != after[k]}
        self.assertEqual(changed, {BOARD_REL, RECEIPT_REL},
                         "the ONLY changed/created paths are the two board files")

    # -- RED 11: --repo is a real parameter; no hardcoded roots -----------------------
    def test_repo_is_a_parameter(self):
        other = self._fresh()
        self.assertEqual(_check(self.fx.root).returncode, 0)
        self.assertEqual(_check(other.root).returncode, 0)
        b1, b2 = _board(self.fx.root), _board(other.root)
        self.assertNotEqual(b1["repo"]["head_sha"], b2["repo"]["head_sha"])
        source = (REPO_ROOT / TOOL_REL).read_text()
        self.assertNotIn("/Users/jguida941", source, "portability law: no absolute repo path")

    # -- RED 12: a polluted caller env cannot alter the board (M6) --------------------
    def test_hermetic_git_env(self):
        self.assertEqual(_check(self.fx.root).returncode, 0)
        clean = (self.fx.root / BOARD_REL).read_bytes()
        # the polluting config lives OUTSIDE the repo: the two compared runs must
        # observe byte-identical repo state (fixture-placement fix, 2026-07-16)
        cfg_dir = Path(tempfile.mkdtemp(prefix="reorient-cfg-")).resolve()
        polluted_cfg = cfg_dir / "polluted.cfg"
        polluted_cfg.write_text("[status]\n\tshowUntrackedFiles = no\n")
        env = dict(os.environ)
        env.update({
            "GIT_DIR": "/nonexistent-git-dir",
            "GIT_WORK_TREE": "/nonexistent-worktree",
            "GIT_CONFIG_GLOBAL": str(polluted_cfg),
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "status.showUntrackedFiles",
            "GIT_CONFIG_VALUE_0": "no",
        })
        self.assertEqual(_check(self.fx.root, env=env).returncode, 0)
        self.assertEqual((self.fx.root / BOARD_REL).read_bytes(), clean,
                         "caller GIT_* pollution must not reach the observation")

    # -- RED 13: zero network attempts -------------------------------------------------
    def test_no_network(self):
        reorient = _import_tool()

        def refuse(*a, **kw):
            raise AssertionError("network attempt during reorient")

        with mock.patch.object(socket, "socket", side_effect=refuse):
            self.assertEqual(
                reorient.main(["--repo", str(self.fx.root), "--now", NOW, "check"]), 0)
            self.assertEqual(reorient.main(["--repo", str(self.fx.root), "verify"]), 0)

    # -- RED 14: a hand-edited board is caught (THE stale-frontier arm; M2) -----------
    def test_hand_edited_board_is_stale(self):
        self.assertEqual(_check(self.fx.root).returncode, 0)
        board_path = self.fx.root / BOARD_REL
        raw = bytearray(board_path.read_bytes())
        idx = raw.find(b"UNVERIFIED")
        raw[idx:idx + 10] = b"unverified"
        board_path.write_bytes(bytes(raw))
        p = _verify(self.fx.root)
        self.assertEqual(p.returncode, 3)
        self.assertIn("STALE board-edited", p.stdout, "the sibling-repo lie, caught")

    # -- RED 15: the git-state digest is load-bearing (isolates M7) -------------------
    def test_git_state_digest_is_load_bearing(self):
        # ISOLATING arm: swap one untracked file for another with the SAME status line
        # count, outside census globs and rosters — the recomputed BOARD is identical
        # (same head/branches/clean/count/worktrees/lanes/undeclared) while the porcelain
        # STREAM bytes differ. Only the digest can catch it.
        (self.fx.root / "stray-A.txt").write_text("a\n")
        self.assertEqual(_check(self.fx.root).returncode, 0)
        (self.fx.root / "stray-A.txt").unlink()
        (self.fx.root / "stray-B.txt").write_text("a\n")
        p = _verify(self.fx.root)
        self.assertEqual(p.returncode, 3)
        self.assertIn("STALE drifted=git-state", p.stdout)
        (self.fx.root / "stray-B.txt").unlink()
        # breadth arms — each also drifts the digest (and the board):
        fresh = self._fresh()
        self.assertEqual(_check(fresh.root).returncode, 0)
        _git(fresh.root, "checkout", "-qb", "same-commit-branch")
        self.assertEqual(_verify(fresh.root).returncode, 3)
        fresh2 = self._fresh()
        self.assertEqual(_check(fresh2.root).returncode, 0)
        (fresh2.root / "dirty.txt").write_text("d\n")
        self.assertEqual(_verify(fresh2.root).returncode, 3)

    # -- RED 16: a record mutated between pass A and pass B refuses (M8) --------------
    def test_concurrent_drift_refuses(self):
        reorient = _import_tool()
        real = reorient._records_manifest
        state = {"calls": 0}
        record = self.fx.record

        def racing(*args, **kwargs):
            out = real(*args, **kwargs)
            state["calls"] += 1
            if state["calls"] == 1:  # mutate AFTER pass A, before pass B recomputes
                record.write_text(record.read_text() + "raced\n")
            return out

        with mock.patch.object(reorient, "_records_manifest", side_effect=racing):
            rc = reorient.main(["--repo", str(self.fx.root), "--now", NOW, "check"])
        self.assertEqual(rc, 4, "concurrent drift must refuse with exit 4")
        self.assertGreaterEqual(state["calls"], 2, "both passes must recompute the manifest")
        self.assertFalse((self.fx.root / BOARD_REL).exists(), "writes NOTHING on drift")

    # -- RED 17: census bijection + undeclared visibility (M10/M11/M15) ---------------
    def test_census_bijection_and_undeclared_visibility(self):
        fx = self._fresh(lanes=[
            ("alpha", 1, "ACTIVE", ["scratchpad/work/alpha.md"]),
            ("beta", 2, "QUEUED", ["scratchpad/work/alpha.md", "scratchpad/work/beta.md"]),
        ])
        (fx.root / "scratchpad/work/beta.md").write_text("BETA-STATUS: BANKED\n")
        (fx.root / "scratchpad/work/undeclared-thing.md").write_text("stray\n")
        self.assertEqual(_check(fx.root).returncode, 0)
        board = _board(fx.root)
        policy = tomllib.loads((fx.root / POLICY_REL).read_text())
        self.assertEqual({l["id"] for l in board["lanes"]},
                         {r["id"] for r in policy["lane"]}, "lane-id bijection")
        by_id = {l["id"]: l for l in board["lanes"]}
        for row in policy["lane"]:
            got = [r["path"] for r in by_id[row["id"]]["records"]]
            self.assertEqual(got, sorted(row["records"]),
                             f"per-lane record bijection for {row['id']}")
        self.assertIn("scratchpad/work/undeclared-thing.md", board["undeclared"],
                      "undeclared work is VISIBLE, never silent")
        self.assertNotIn(BOARD_REL, board["undeclared"])

    # -- RED 18: the reuse key is recomputable; provenance is a boundary (M12) --------
    def test_reuse_key_recomputable_and_boundary(self):
        self.assertEqual(_check(self.fx.root).returncode, 0)
        self.assertEqual(_verify(self.fx.root).returncode, 0, "positive control")
        rpath = self.fx.root / RECEIPT_REL
        rec = json.loads(rpath.read_text())
        spoofed = dict(rec)
        spoofed["toolchain"] = dict(rec["toolchain"], git="git version 0.0.0-spoof")
        rpath.write_text(json.dumps(spoofed, indent=2, sort_keys=True) + "\n")
        p = _verify(self.fx.root)
        self.assertEqual(p.returncode, 3, "a different toolchain never reuses: " + p.stdout)
        # boundary negative control: provenance is recorded, never compared
        rpath.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
        self.assertEqual(_verify(self.fx.root).returncode, 0, "byte-identical rewrite sanity")
        edited = dict(rec)
        edited["provenance"] = dict(rec["provenance"], command=["edited", "provenance"])
        rpath.write_text(json.dumps(edited, indent=2, sort_keys=True) + "\n")
        self.assertEqual(_verify(self.fx.root).returncode, 0,
                         "provenance carries no reuse authority (documented boundary)")

    # -- RED 19: WITHDRAWN (operator decision 2026-07-16: NO wall-clock budgets). -----
    # Numbering preserved. RED 1's unknown-key arm guards against any timer section
    # reappearing; there is deliberately no test here.

    # -- RED 20: torn pairs are always detectable; receipt is the commit point (M14) --
    def test_torn_pair_is_stale(self):
        self.assertEqual(_check(self.fx.root).returncode, 0)
        b1 = (self.fx.root / BOARD_REL).read_bytes()
        r1 = (self.fx.root / RECEIPT_REL).read_bytes()
        self.fx.record.write_text(self.fx.record.read_text() + "VERDICT: approve\n")
        self.assertEqual(_check(self.fx.root).returncode, 0)
        b2 = (self.fx.root / BOARD_REL).read_bytes()
        r2 = (self.fx.root / RECEIPT_REL).read_bytes()
        self.assertNotEqual(b1, b2)
        for board_bytes, receipt_bytes in ((b1, r2), (b2, r1)):
            (self.fx.root / BOARD_REL).write_bytes(board_bytes)
            (self.fx.root / RECEIPT_REL).write_bytes(receipt_bytes)
            p = _verify(self.fx.root)
            self.assertEqual(p.returncode, 3,
                             "a cross-generation pair must be STALE, never PASS")
        # interruption arm: the second rename fails; on-disk state stays detectable
        (self.fx.root / BOARD_REL).write_bytes(b2)
        (self.fx.root / RECEIPT_REL).write_bytes(r2)
        self.fx.record.write_text(self.fx.record.read_text() + "VERDICT: revise\n")
        reorient = _import_tool()
        real_replace = os.replace
        state = {"n": 0}

        def failing_second(src, dst):
            state["n"] += 1
            if state["n"] == 2:
                raise OSError("interrupted between the pair renames")
            return real_replace(src, dst)

        with mock.patch.object(reorient.os, "replace", side_effect=failing_second):
            rc = reorient.main(["--repo", str(self.fx.root), "--now", NOW, "check"])
        self.assertNotEqual(rc, 0, "an interrupted pair write must not report success")
        self.assertEqual(_verify(self.fx.root).returncode, 3,
                         "the torn state on disk reads STALE")
        self.assertEqual(_check(self.fx.root).returncode, 0, "a rerun regenerates cleanly")
        self.assertEqual(_verify(self.fx.root).returncode, 0)

    # -- RED 21: every list is sorted by its declared key (M16) -----------------------
    def test_lists_sorted_deterministically(self):
        fx = self._fresh(lanes=[
            ("zulu", 2, "QUEUED", ["scratchpad/work/z2.md", "scratchpad/work/z1.md"]),
            ("alpha", 1, "ACTIVE", ["scratchpad/work/alpha.md"]),
        ])
        (fx.root / "scratchpad/work/z1.md").write_text("Z1-STATUS: A\n")
        (fx.root / "scratchpad/work/z2.md").write_text("Z2-STATUS: B\n")
        (fx.root / "scratchpad/work/stray-b.md").write_text("s\n")
        (fx.root / "scratchpad/work/stray-a.md").write_text("s\n")
        _git(fx.root, "branch", "zz-branch")
        _git(fx.root, "branch", "aa-branch")
        self.assertEqual(_check(fx.root).returncode, 0)
        board = _board(fx.root)
        self.assertEqual([b["name"] for b in board["branches"]],
                         sorted(b["name"] for b in board["branches"]))
        self.assertEqual([w["path"] for w in board["worktrees"]],
                         sorted(w["path"] for w in board["worktrees"]))
        self.assertEqual([l["id"] for l in board["lanes"]],
                         sorted(l["id"] for l in board["lanes"]))
        for lane in board["lanes"]:
            self.assertEqual([r["path"] for r in lane["records"]],
                             sorted(r["path"] for r in lane["records"]))
        self.assertEqual(board["undeclared"], sorted(board["undeclared"]))

    # -- RED 22: discipline rows ride the receipt honestly (M17) ----------------------
    def test_discipline_rows_closed_and_honest(self):
        self.assertEqual(_check(self.fx.root).returncode, 0)
        rec = _receipt(self.fx.root)
        policy = tomllib.loads((self.fx.root / POLICY_REL).read_text())
        self.assertEqual(rec["discipline"], policy["discipline"], "verbatim projection")
        self.assertIs(rec["discipline_enforced"], False, "v1 records; it does not enforce")
        liar = self._fresh(discipline_enforced="true")
        p = _check(liar.root)
        self.assertEqual(p.returncode, 2,
                         "a policy claiming enforcement in v1 is refused at load")
        self.assertTrue(p.stdout.startswith("REORIENT: FAIL policy"))

    # -- RED 23: lane.lock occupancy is projected (M18) --------------------------------
    def test_lane_lock_projected(self):
        base = Path(tempfile.mkdtemp(prefix="reorient-lock-")).resolve()
        held, free = base / "held", base / "free"
        _git(self.fx.root, "worktree", "add", "-q", str(held))
        _git(self.fx.root, "worktree", "add", "-q", str(free))
        self.addCleanup(lambda: _git(self.fx.root, "worktree", "remove", "--force", str(held)))
        self.addCleanup(lambda: _git(self.fx.root, "worktree", "remove", "--force", str(free)))
        (held / "lane.lock").write_text("conductor 2026-07-16\n")
        self.assertEqual(_check(self.fx.root).returncode, 0)
        rows = {w["path"]: w for w in _board(self.fx.root)["worktrees"]}
        self.assertEqual(rows[str(held.resolve())]["lane_lock"], "present",
                         "occupancy is VISIBLE — the two-session collision law")
        self.assertEqual(rows[str(free.resolve())]["lane_lock"], "absent")

    # -- RED 24: priority/charter are projected verbatim from policy DATA (M19) -------
    def test_lane_priority_charter_projected_verbatim(self):
        fx = self._fresh(lanes=[
            ("alpha", 1, "ACTIVE", ["scratchpad/work/alpha.md"]),
            ("beta", 5, "PARKED", ["scratchpad/work/beta.md"]),
        ])
        (fx.root / "scratchpad/work/beta.md").write_text("BETA-STATUS: PARKED\n")
        self.assertEqual(_check(fx.root).returncode, 0)
        by_id = {l["id"]: l for l in _board(fx.root)["lanes"]}
        self.assertEqual((by_id["alpha"]["priority"], by_id["alpha"]["charter"]), (1, "ACTIVE"))
        self.assertEqual((by_id["beta"]["priority"], by_id["beta"]["charter"]), (5, "PARKED"))
        pol = fx.root / POLICY_REL
        pol.write_text(pol.read_text().replace("priority = 5", "priority = 7"))
        self.assertEqual(_check(fx.root).returncode, 0)
        by_id = {l["id"]: l for l in _board(fx.root)["lanes"]}
        self.assertEqual(by_id["beta"]["priority"], 7,
                         "the board projects the policy edit verbatim — it authors nothing")


if __name__ == "__main__":
    unittest.main()


# ============================================================================
# W8R2 tranche — round-2 arms for the W8-O code-gate r1 findings (2026-07-17).
#
# Appended byte-verbatim to the frozen RED (test_reorient.py, sha
# 3146332030c64fbaf2e30d394bf27f195932f3ea81019f6eb1becdcad685c726) per the
# assembly law: final RED = frozen file + this tranche, byte-order. No frozen
# arm is modified or weakened. Binding spec: the fold record
# scratchpad/active/w8o/red/w8o-code-gate-r1-fold-2026-07-17.md section 1
# (families W8R2-H/P/V/L/C/D/S/F/R); probe rider:
# scratchpad/active/w8o/red/w8r2-probe-rider-2026-07-17.md (M16a-e, M20-M26).
#
# Right-reason law: every arm's docstring states its expected pre-GREEN result
# against the PRISTINE module (sha c0fca0927146a070535a5e375a8bcd54b82a18ae9
# 59e54580818bf63efc1b0e5). Arms marked GUARD are expected GREEN against the
# pristine module; each states the post-build invariant it pins.
#
# Hostile-fixture law: every hostile construction is a real side repo/dir/
# symlink/hook built inside the test tmpdir, poisoning around the PUBLIC entry
# points only. The only monkeypatched names are the frozen RED's REVIEWED seam
# surface (reorient._records_manifest, socket.socket for the no-network guard)
# - never the surface under test.
#
# Author seat: W8-O reorient lane, round-2 RED author worker (conductor
# dispatch 2026-07-17). Producing model: claude-fable-5 (execution metadata,
# not authority).
# ============================================================================

import hashlib


def _w8r2_sha_inventory(root):
    """{relpath: sha256} for every regular file under root, .git excluded.

    Symlinks are recorded by name with a 'symlink->' marker instead of being
    followed, so a planted link can never masquerade as its target's bytes.
    """
    root = Path(root)
    out = {}
    for p in root.rglob("*"):
        if ".git" in p.parts:
            continue
        if p.is_symlink():
            out[p.relative_to(root).as_posix()] = "symlink->" + os.readlink(p)
        elif p.is_file():
            out[p.relative_to(root).as_posix()] = _sha256(p)
    return out


def _w8r2_stat_inventory(root):
    """{relpath: (size, mtime_ns)} for every regular file under root (.git excluded).

    Cheap full-checkout snapshot: creation, deletion, and rewrite all change it.
    """
    root = Path(root)
    out = {}
    for p in root.rglob("*"):
        if ".git" in p.parts or p.is_symlink() or not p.is_file():
            continue
        st = p.stat()
        out[p.relative_to(root).as_posix()] = (st.st_size, st.st_mtime_ns)
    return out


def _w8r2_git_dir_inventory(repo_root):
    """{relpath: sha256} over EVERY regular file under <repo_root>/.git."""
    root = Path(repo_root)
    out = {}
    for p in (root / ".git").rglob("*"):
        if p.is_file() and not p.is_symlink():
            out[p.relative_to(root).as_posix()] = _sha256(p)
    return out


def _w8r2_remove_created(root, before_paths):
    """Delete files created under root since `before_paths`; prune empty __pycache__."""
    root = Path(root)
    for rel in sorted(set(_w8r2_stat_inventory(root)) - set(before_paths),
                      key=len, reverse=True):
        try:
            (root / rel).unlink()
        except OSError:
            pass
    for d in sorted(root.rglob("__pycache__"), key=lambda x: len(str(x)), reverse=True):
        try:
            d.rmdir()
        except OSError:
            pass


def _w8r2_hermetic_git_env():
    """The design section 5 hermetic child env, rebuilt independently by the RED."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
    })
    return env


class W8R2Arms(unittest.TestCase):
    """Round-2 arms: codex CODE+ADVERSARIAL r1 findings folded RED-first."""

    def setUp(self):
        self.fx = _Repo()
        self.addCleanup(self.fx.cleanup)

    def _fresh(self, **kw):
        fx = _Repo(**kw)
        self.addCleanup(fx.cleanup)
        return fx

    # -- W8R2-C (F6): the policy is SEMANTICALLY closed, not just shaped ------------
    def test_w8r2_c_policy_semantics_closed(self):
        """Pre-GREEN vs pristine: FAILS (`0 != 2 : M23a ...`) - the pristine
        validator accepts any five unique job-state strings, unanchored regexes,
        and false discipline laws (module :144-165)."""
        # M23a enum swap: five unique strings that are NOT the closed vocabulary.
        swap = self._fresh()
        pol = swap.root / POLICY_REL
        pol.write_text(pol.read_text().replace('"STALE"', '"SNOOZED"'))
        p = _check(swap.root)
        self.assertEqual(p.returncode, 2,
                         "M23a: job_states is a CLOSED vocabulary, not any five "
                         "unique strings: " + p.stdout + p.stderr)
        self.assertTrue(p.stdout.startswith("REORIENT: FAIL policy"), p.stdout)
        self.assertFalse((swap.root / BOARD_REL).exists(), "writes NOTHING on refusal")
        # M23b unanchored grammar: compilable but not ^...$-anchored.
        un = self._fresh()
        pol = un.root / POLICY_REL
        pol.write_text(pol.read_text().replace('"^VERDICT: .+$"', '"VERDICT: .+"'))
        p = _check(un.root)
        self.assertEqual(p.returncode, 2,
                         "M23b: every verdict-grammar pattern must be anchored "
                         "(^...$): " + p.stdout + p.stderr)
        self.assertTrue(p.stdout.startswith("REORIENT: FAIL policy"), p.stdout)
        # A mandated discipline law recorded as false is a contract violation.
        lie = self._fresh()
        pol = lie.root / POLICY_REL
        pol.write_text(pol.read_text().replace("read_only_snapshots = true",
                                               "read_only_snapshots = false"))
        p = _check(lie.root)
        self.assertEqual(p.returncode, 2,
                         "a false discipline law must be refused, not recorded: "
                         + p.stdout + p.stderr)
        self.assertTrue(p.stdout.startswith("REORIENT: FAIL policy"), p.stdout)
        # Positive control: the untouched closed fixture still passes.
        self.assertEqual(_check(self.fx.root).returncode, 0)

    # -- W8R2-C (F6): roster paths resolve INSIDE --repo, or refuse ------------------
    def test_w8r2_c_roster_paths_stay_inside_root(self):
        """Pre-GREEN vs pristine: FAILS (`0 != 2 : an absolute record path ...`) -
        the pristine module accepts and projects absolute, ../, and
        symlink-escaping roster entries (module :197-199, :234-239)."""
        outside = Path(tempfile.mkdtemp(prefix="reorient-outside-")).resolve()
        external = outside / "external.md"
        external.write_text("EXTERNAL-STATUS: OUTSIDE\n")
        # (a) absolute roster path (target exists and is readable: the ONLY
        # refusal reason is the escape, never a missing file).
        fx = self._fresh(lanes=[("alpha", 1, "ACTIVE", [str(external)])])
        p = _check(fx.root)
        self.assertEqual(p.returncode, 2,
                         "an absolute record path must be refused, never projected: "
                         + p.stdout + p.stderr)
        self.assertTrue(p.stdout.startswith("REORIENT: FAIL"), p.stdout)
        self.assertFalse((fx.root / BOARD_REL).exists(), "writes NOTHING on refusal")
        # (b) M23c: ../ traversal to a real sibling of the repo root.
        fx2 = self._fresh()
        sib = fx2.root.parent / (fx2.root.name + "-escape.md")
        sib.write_text("ESCAPE-STATUS: OUTSIDE\n")
        self.addCleanup(sib.unlink)
        (fx2.root / POLICY_REL).write_text(
            _policy_toml([("alpha", 1, "ACTIVE", ["../" + sib.name])]))
        p = _check(fx2.root)
        self.assertEqual(p.returncode, 2,
                         "M23c: a ../ roster entry must be refused, never projected: "
                         + p.stdout + p.stderr)
        self.assertTrue(p.stdout.startswith("REORIENT: FAIL"), p.stdout)
        self.assertFalse((fx2.root / BOARD_REL).exists())
        # (c) symlink escape: a declared record resolving outside --repo.
        fx3 = self._fresh(lanes=[("alpha", 1, "ACTIVE", ["scratchpad/work/link.md"])])
        os.symlink(external, fx3.root / "scratchpad" / "work" / "link.md")
        p = _check(fx3.root)
        self.assertEqual(p.returncode, 2,
                         "a roster symlink escaping --repo must be refused: "
                         + p.stdout + p.stderr)
        self.assertTrue(p.stdout.startswith("REORIENT: FAIL"), p.stdout)
        self.assertFalse((fx3.root / BOARD_REL).exists())
        # Positive control: an ordinary repo-relative roster still projects.
        self.assertEqual(_check(self.fx.root).returncode, 0)

    # -- W8R2-D (F7): worktree dirty_line_count is the FULL porcelain count ----------
    def test_w8r2_d_worktree_untracked_rides_dirty_count(self):
        """Pre-GREEN vs pristine: FAILS (`0 != 1 : worktree dirty_line_count ...`) -
        _dirty_count drops untracked lines for linked worktrees too (module
        :302-307, :350-362); the design limits that exception to the root
        status fields."""
        wt = Path(tempfile.mkdtemp(prefix="reorient-wtdirty-")).resolve() / "wt"
        _git(self.fx.root, "worktree", "add", "-q", str(wt))
        self.addCleanup(lambda: _git(self.fx.root, "worktree", "remove", "--force", str(wt)))
        (wt / "untracked-note.txt").write_text("scratch\n")
        truth = len(_git(wt, "status", "--porcelain=v1").stdout.splitlines())
        self.assertEqual(truth, 1, "fixture sanity: git sees exactly one untracked line")
        self.assertEqual(_check(self.fx.root).returncode, 0)
        board = _board(self.fx.root)
        rows = {w["path"]: w for w in board["worktrees"]}
        self.assertEqual(rows[str(wt.resolve())]["dirty_line_count"], truth,
                         "worktree dirty_line_count is the FULL porcelain v1 line "
                         "count - untracked lines included (design section 6)")
        # The design's ROOT exception is untouched: untracked files still never
        # flip the root tracked-change fields (pinned semantics, design section 6).
        self.assertEqual(board["repo"]["status_line_count"], 0,
                         "root exception preserved: tracked-change lines only")
        self.assertTrue(board["repo"]["status_clean"])

    # -- W8R2-F (F9): repo-local core.fsmonitor never executes -----------------------
    def test_w8r2_f_repo_local_fsmonitor_never_executes(self):
        """Pre-GREEN vs pristine: FAILS (`... is not false : repo-local
        core.fsmonitor must NOT execute ...`) - the hermetic env neutralizes
        global/system config only; repo-local config still injects a command
        into the child git (module :271-295)."""
        side = Path(tempfile.mkdtemp(prefix="reorient-fsmon-")).resolve()
        marker = side / "hook-ran"
        hook = side / "hostile-fsmonitor.sh"
        hook.write_text("#!/bin/sh\n: > '%s'\nexit 1\n" % marker)
        hook.chmod(0o755)
        _git(self.fx.root, "config", "core.fsmonitor", str(hook))
        self.assertFalse(marker.exists(), "fixture sanity: hook not yet run")
        p = _check(self.fx.root)
        self.assertFalse(marker.exists(),
                         "repo-local core.fsmonitor must NOT execute during "
                         "read-only observation (the child-config seam)")
        self.assertEqual(p.returncode, 0,
                         "observation still works with the hostile config present: "
                         + p.stdout + p.stderr)
        p = _verify(self.fx.root)
        self.assertFalse(marker.exists(), "verify must not execute the hook either")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    # -- W8R2-H (F1): reorient surfaces are HOMED in the layout contracts ------------
    def test_w8r2_h_homing_rows_present(self):
        """Pre-GREEN vs pristine room: FAILS (`'reorient.py' not found in ...`) -
        the r1 patch was module-only; every homing row (design :477 / section 3)
        is absent from all five layout surfaces at base 74fe3ecd."""
        layout = json.loads((REPO_ROOT / "contracts" / "repo_layout.json").read_text())
        sl = layout["structural_layout"]
        (org_row,) = [g for g in sl["source_layout"]["groups"] if g["id"] == "organization"]
        self.assertIn("reorient.py", org_row["members"],
                      "repo_layout.json census row for the composer")
        (tc_row,) = [g for g in sl["test_layout"]["groups"] if g["id"] == "contracts"]
        self.assertIn("test_reorient.py", tc_row["members"],
                      "repo_layout.json census row for the RED")
        self.assertEqual(sl["contracts_layout"].get("toml_members"),
                         ["doc_authority_policy.toml", "reorient_policy.toml"],
                         "the contracts cover gains the CLOSED toml_members list "
                         "(repairs the pre-existing doc_authority_policy.toml gap)")
        import importlib
        lc = importlib.import_module("scripts.organization.layout_contract")
        self.assertIn("scripts/organization/reorient.py",
                      {h.target_path for h in lc.MODULE_HOMES},
                      "layout_contract MODULE_HOMES row for reorient.py")
        tlc = importlib.import_module("scripts.organization.tests_layout_contract")
        (contracts_group,) = [g for g in tlc.TEST_GROUPS if g.name == "contracts"]
        self.assertIn("test_reorient.py", contracts_group.modules,
                      "tests_layout_contract physical home row")
        self.assertIn("test_reorient.py", tlc.DESIGN_CONTRACT_GROUPS["organization"],
                      "tests_layout_contract DESIGN_CONTRACT_GROUPS mirror row")

    # -- W8R2-H (F1): the layout suites cover the reorient surfaces ------------------
    def test_w8r2_h_layout_suites_cover_reorient_surfaces(self):
        """Pre-GREEN vs pristine room: FAILS (`1 != 0 : the two layout-suite
        arms ...`) - the undeclared reorient surfaces redden
        test_every_test_file_in_declared_home and
        test_live_scripts_tree_matches_semantic_contract.

        Scope note (empirical, 2026-07-17): base 74fe3ecd itself fails seven
        OTHER layout arms because eleven declared design-contract test files do
        not exist on w3-correction - out-of-slice, unreachable from this
        packet's allowed paths. This arm therefore pins the exact cargo-caused
        delta (the two arms above, green post-homing), not a literal
        all-suites-green that no in-scope patch could ever satisfy.
        """
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        p = subprocess.run(
            [sys.executable, "-m", "unittest",
             "tests.contracts.test_scripts_layout_contract.ScriptsLayoutContractTests."
             "test_live_scripts_tree_matches_semantic_contract",
             "tests.contracts.test_tests_layout_contract.TestsLayoutContract."
             "test_every_test_file_in_declared_home"],
            cwd=str(REPO_ROOT), env=env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0,
                         "the two layout-suite arms the reorient surfaces redden "
                         "must be green once the homing rows land (F1):\n"
                         + p.stdout + p.stderr)

    # -- W8R2-L (F5): every live board input rides the drift compare -----------------
    def test_w8r2_l_lane_lock_rides_drift_compare(self):
        """Pre-GREEN vs pristine: FAILS (`0 != 4 : a lane.lock created between
        the passes ...`) - lane_lock is read for the board but excluded from
        bundle_sha256 (module :333-395), so an ignored lane.lock created
        between the passes yields PASS-then-STALE instead of refusal."""
        fx = self.fx
        (fx.root / ".gitignore").write_text("lane.lock\n")
        _git(fx.root, "add", ".gitignore")
        _git(fx.root, "commit", "-qm", "ignore lane.lock")
        wt = Path(tempfile.mkdtemp(prefix="reorient-lanelock-")).resolve() / "wt"
        _git(fx.root, "worktree", "add", "-q", str(wt))
        self.addCleanup(lambda: _git(fx.root, "worktree", "remove", "--force", str(wt)))
        reorient = _import_tool()
        real = reorient._records_manifest
        state = {"calls": 0}

        def planting(*args, **kwargs):
            out = real(*args, **kwargs)
            state["calls"] += 1
            if state["calls"] == 1:  # after pass A's git observation, before pass B's
                (wt / "lane.lock").write_text("late writer\n")
            return out

        with mock.patch.object(reorient, "_records_manifest", side_effect=planting):
            rc = reorient.main(["--repo", str(fx.root), "--now", NOW, "check"])
        self.assertEqual(rc, 4,
                         "a lane.lock created between the passes is concurrent "
                         "drift, never PASS-then-STALE")
        self.assertFalse((fx.root / BOARD_REL).exists(), "writes NOTHING on drift")
        self.assertFalse((fx.root / RECEIPT_REL).exists())
        # Positive control: with the lock gone and the state stable, check PASSes.
        (wt / "lane.lock").unlink()
        self.assertEqual(reorient.main(["--repo", str(fx.root), "--now", NOW, "check"]), 0)

    # -- W8R2-P (F3): the DOCUMENTED CLI is pure - no -B, no env override ------------
    def test_w8r2_p_documented_cli_purity_full_room(self):
        """Pre-GREEN vs pristine: FAILS (`Lists differ: ['scripts/__pycache__/...']
        != []`) - the documented CLI writes __pycache__ into the module
        checkout; purity held only under PYTHONDONTWRITEBYTECODE=1. Post-build
        the CLI itself suppresses bytecode (behavior, not docs)."""
        env = dict(os.environ)
        env.pop("PYTHONDONTWRITEBYTECODE", None)   # the documented CLI, no override
        env.pop("PYTHONPYCACHEPREFIX", None)       # and no cache redirection
        room_before = _w8r2_stat_inventory(REPO_ROOT)
        self.addCleanup(lambda: _w8r2_remove_created(REPO_ROOT, set(room_before)))
        fixture_before = _w8r2_sha_inventory(self.fx.root)
        p = _check(self.fx.root, env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        room_after = _w8r2_stat_inventory(REPO_ROOT)
        self.assertEqual(sorted(set(room_after) - set(room_before)), [],
                         "the documented CLI must not create files in the module "
                         "checkout (F3: no __pycache__, no -B crutch)")
        self.assertEqual(room_after, room_before,
                         "the documented CLI must not rewrite checkout files")
        self.assertEqual([str(d) for d in Path(REPO_ROOT).rglob("__pycache__")], [],
                         "zero __pycache__ anywhere in the checkout")
        fixture_after = _w8r2_sha_inventory(self.fx.root)
        changed = {k for k in set(fixture_before) | set(fixture_after)
                   if fixture_before.get(k) != fixture_after.get(k)}
        self.assertEqual(changed, {BOARD_REL, RECEIPT_REL},
                         "check writes exactly its two declared output paths")
        p = _verify(self.fx.root, env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(_w8r2_stat_inventory(REPO_ROOT), room_after,
                         "verify writes nothing in the checkout")
        self.assertEqual(_w8r2_sha_inventory(self.fx.root), fixture_after,
                         "verify writes nothing in the fixture either")

    # -- W8R2-R / RED 10: the FULL .git tree is byte-untouched (GUARD) ---------------
    def test_w8r2_r10_full_git_dir_inventory_untouched(self):
        """GUARD - expected GREEN vs pristine (the optional-locks discipline
        already held for the index). Post-build invariant: EVERY file under
        .git stays byte-identical across check and verify, replacing the
        index-only inventory codex flagged (finding 10)."""
        fx = self.fx
        seed = fx.root / "seed.txt"
        os.utime(seed, (os.stat(seed).st_atime, os.stat(seed).st_mtime + 7))
        before = _w8r2_git_dir_inventory(fx.root)
        self.assertEqual(_check(fx.root).returncode, 0)
        self.assertEqual(_w8r2_git_dir_inventory(fx.root), before,
                         "EVERY file under .git is byte-untouched by check "
                         "(not just the index)")
        self.assertEqual(_verify(fx.root).returncode, 0)
        self.assertEqual(_w8r2_git_dir_inventory(fx.root), before,
                         "verify touches nothing under .git")

    # -- W8R2-R / RED 13: the no-network claim covers the CHILD git seam -------------
    def test_w8r2_r13_no_network_covers_child_git_config(self):
        """Pre-GREEN vs pristine: FAILS (`... is not false : a config-injected
        child command ran ...`) - the parent-process socket guard is blind to
        child git processes; repo-local config injects a command (with a
        network payload) the guard never sees (finding 9/10)."""
        fx = self.fx
        side = Path(tempfile.mkdtemp(prefix="reorient-childnet-")).resolve()
        attempt = side / "attempted-connect"
        hook = side / "netcall-fsmonitor.sh"
        hook.write_text(
            "#!/bin/sh\n"
            ": > '%s'\n"
            "%s -c 'import socket; socket.create_connection((\"127.0.0.1\", 9), 0.2)' "
            "2>/dev/null\n"
            "exit 1\n" % (attempt, sys.executable))
        hook.chmod(0o755)
        _git(fx.root, "config", "core.fsmonitor", str(hook))
        reorient = _import_tool()

        def refuse(*a, **kw):
            raise AssertionError("network attempt during reorient")

        with mock.patch.object(socket, "socket", side_effect=refuse):
            rc_check = reorient.main(["--repo", str(fx.root), "--now", NOW, "check"])
            rc_verify = reorient.main(["--repo", str(fx.root), "verify"])
        self.assertFalse(attempt.exists(),
                         "a config-injected child command ran (and attempted the "
                         "network) while the parent socket guard saw nothing - the "
                         "child git seam must be neutralized")
        self.assertEqual(rc_check, 0)
        self.assertEqual(rc_verify, 0)

    # -- W8R2-R / RED 1: the reviewed policy VALUES are pinned, not just shapes ------
    def test_w8r2_r1_policy_values_pinned_exactly(self):
        """GUARD - expected GREEN vs pristine (the shipped policy already
        matches design section 4 byte-for-byte). Post-build invariant: any r2
        edit that drifts a reviewed policy VALUE - vocabulary, grammar,
        discipline row, or any lane row - reddens here (finding 10, RED 1)."""
        data = tomllib.loads((REPO_ROOT / POLICY_REL).read_text())
        self.assertEqual(data["job_states"]["values"],
                         ["PASS", "FAIL", "INFRA_BLOCKED", "CANCELLED", "STALE"])
        self.assertEqual(data["verdict_grammar"]["patterns"], [
            "^DESIGN-VERDICT: .+$",
            "^VERDICT: .+$",
            "^ADVERSARIAL-VERDICT: .+$",
            "^[A-Z][A-Z0-9-]*-STATUS: .+$",
        ])
        disc = data["discipline"]
        self.assertEqual(disc["receipt_interrupt_triggers"],
                         ["failure", "invalidation", "gate-readiness"])
        self.assertEqual(disc["fan_out_ceiling"], 6)
        for key in ("read_only_snapshots", "no_self_fold", "conductor_only_integration",
                    "unverified_scout", "one_writer_per_lane", "exact_key_caching"):
            self.assertIs(disc[key], True, key)
        self.assertIs(disc["discipline_enforced"], False)
        expected_rows = {
            "plan": (1, "RECORD", ["scratchpad/work/CONTINUATION-PLAN.md"]),
            "w8o": (2, "ACTIVE", [
                "scratchpad/active/w8o/design/w8o-reorient-design-2026-07-16.md",
                "scratchpad/active/w8o/transcripts/codex-w8o-design-gate-r1-2026-07-16.md",
                "scratchpad/active/w8o/transcripts/codex-w8o-design-gate-r2-2026-07-16.md",
            ]),
            "w7": (3, "ACTIVE", ["scratchpad/work/fable-prompt-w7-v12-v13-refinement.txt"]),
            "org": (4, "QUEUED", ["scratchpad/work/fable-prompt-org-red-r3-convergence.txt"]),
            "slice-patch": (5, "ACTIVE", [
                "scratchpad/active/slice-patch/red/slice-patch-r5-convergence-2026-07-16.md",
                "scratchpad/active/slice-patch/packet/slice-patch-r5-packet.json",
            ]),
            "ratchet": (6, "QUEUED", [
                "scratchpad/work/fable-prompt-ratchet-r6-convergence.txt",
                "scratchpad/active/ratchet/prep/prep-receipt-2026-07-16.md",
            ]),
            "source-foundation": (7, "QUEUED", [
                "scratchpad/active/source-foundation/prompts/fable-source-foundation-design-red.txt",
            ]),
            "e2e-fixture": (8, "QUEUED", [
                "scratchpad/active/e2e-fixture/charter/e2e-fixture-charter-2026-07-16.md",
            ]),
            "w6": (9, "QUEUED", ["scratchpad/work/fable-prompt-w6-r2-adoption.txt"]),
            "w8": (10, "QUEUED", ["scratchpad/work/fable-prompt-w8-convergence-reds.txt"]),
            "lexguard": (11, "PARKED", ["scratchpad/work/lexguard-convergence-decisions-2026-07-16.md"]),
            "slice0": (12, "LANDED", [
                "scratchpad/work/fable-slice0-rev16-fold-2026-07-16.md",
                "scratchpad/active/slice0/transcripts/codex-landing-r6-two-closure-APPROVE-2026-07-16.md",
            ]),
        }
        got = {r["id"]: (r["priority"], r["charter"], r["records"]) for r in data["lane"]}
        self.assertEqual(got, expected_rows,
                         "the twelve reviewed lane rows, values pinned (design section 4)")

    # -- W8R2-R / RED 21: worktree sorting proven with TWO linked worktrees (GUARD) --
    def test_w8r2_r21_worktree_sorting_proven_with_two_worktrees(self):
        """GUARD - expected GREEN vs pristine (the sort exists). RED 21's
        single-worktree fixture made the worktree axis vacuously sorted
        (finding 10); this arm makes probe M16c's flip possible: creation
        order is deliberately anti-sorted."""
        fx = self.fx
        base = Path(tempfile.mkdtemp(prefix="reorient-sortwt-")).resolve()
        zz, aa = base / "zz-wt", base / "aa-wt"
        _git(fx.root, "worktree", "add", "-q", str(zz))  # created FIRST
        _git(fx.root, "worktree", "add", "-q", str(aa))  # sorts BEFORE zz
        self.addCleanup(lambda: _git(fx.root, "worktree", "remove", "--force", str(zz)))
        self.addCleanup(lambda: _git(fx.root, "worktree", "remove", "--force", str(aa)))
        self.assertLess(str(aa.resolve()), str(zz.resolve()),
                        "fixture sanity: creation order is anti-sorted")
        self.assertEqual(_check(fx.root).returncode, 0)
        paths = [w["path"] for w in _board(fx.root)["worktrees"]]
        self.assertEqual(len(paths), 3, "main + two linked worktrees, never skipped")
        self.assertEqual(paths, sorted(paths),
                         "worktree rows sorted by path with MULTIPLE linked "
                         "worktrees (the M16c axis)")

    # -- W8R2-R / REDs 2+4: branch/worktree ground truth CLOSED (GUARD) --------------
    def test_w8r2_r2_r4_branch_worktree_ground_truth_closed(self):
        """GUARD - expected GREEN vs pristine. Post-build invariant: branch
        rows equal for-each-ref ground truth in BOTH directions with closed
        {name, sha} row shape (RED 4's gap), and every worktree row carries
        ground-truth identity fields (RED 2's gap). Dirty-count semantics ride
        W8R2-D, not this arm."""
        fx = self.fx
        _git(fx.root, "branch", "zz-side")
        _git(fx.root, "branch", "aa-side")
        base = Path(tempfile.mkdtemp(prefix="reorient-gt-")).resolve()
        wt, det = base / "gt-wt", base / "gt-detached"
        _git(fx.root, "worktree", "add", "-q", str(wt))
        _git(fx.root, "worktree", "add", "-q", "--detach", str(det))
        self.addCleanup(lambda: _git(fx.root, "worktree", "remove", "--force", str(wt)))
        self.addCleanup(lambda: _git(fx.root, "worktree", "remove", "--force", str(det)))
        self.assertEqual(_check(fx.root).returncode, 0)
        board = _board(fx.root)
        truth = {}
        for line in _git(fx.root, "for-each-ref", "refs/heads").stdout.splitlines():
            sha_type, ref = line.split("\t", 1)
            truth[ref[len("refs/heads/"):]] = sha_type.split(" ", 1)[0]
        self.assertEqual({b["name"]: b["sha"] for b in board["branches"]}, truth,
                         "branch rows CLOSED against ground truth, both directions")
        for row in board["branches"]:
            self.assertEqual(set(row), {"name", "sha"},
                             "branch row shape is closed (RED 4's omitted level)")
        expected_paths = {str(fx.root), str(wt.resolve()), str(det.resolve())}
        rows = {w["path"]: w for w in board["worktrees"]}
        self.assertEqual(set(rows), expected_paths,
                         "worktree rows CLOSED against ground truth, both directions")
        for path, row in rows.items():
            self.assertEqual(row["status"], "present")
            self.assertEqual(row["head_sha"],
                             _git(path, "rev-parse", "HEAD").stdout.strip(),
                             f"head_sha ground truth for {path}")
            live_branch = _git(path, "branch", "--show-current").stdout.strip()
            self.assertEqual(row["branch_or_detached"],
                             live_branch if live_branch else "(detached)",
                             f"branch ground truth for {path}")
            self.assertEqual(row["lane_lock"], "absent")

    # -- W8R2-R / RED 5: receipt values recomputed INDEPENDENTLY (GUARD) -------------
    def test_w8r2_r5_receipt_values_recomputed_independently(self):
        """GUARD - expected GREEN vs pristine. Post-build invariant: the
        receipt's repo_head_sha, toolchain, inputs_manifest_sha256, and
        git_state_sha256 all reproduce OUTSIDE the module from the design's
        own formulas (finding 10: 'not independently recomputed')."""
        fx = self.fx
        self.assertEqual(_check(fx.root).returncode, 0)
        rec = _receipt(fx.root)
        self.assertEqual(rec["repo_head_sha"],
                         _git(fx.root, "rev-parse", "HEAD").stdout.strip())
        self.assertEqual(rec["toolchain"]["python"], sys.version.split()[0])
        self.assertEqual(rec["toolchain"]["git"],
                         subprocess.run(["git", "--version"], capture_output=True,
                                        text=True).stdout.strip())
        blob = b"".join(
            "{0}\x00{1}\n".format(i["path"], i["sha256"]).encode("utf-8")
            for i in sorted(rec["inputs"], key=lambda i: i["path"]))
        self.assertEqual(rec["inputs_manifest_sha256"], hashlib.sha256(blob).hexdigest(),
                         "inputs manifest reproduced from the receipt rows "
                         "(design section 7 formula)")
        env = _w8r2_hermetic_git_env()

        def g(path, *args):
            return subprocess.run(
                ["git", "--no-optional-locks", "-C", str(path), *args],
                env=env, capture_output=True, check=True).stdout

        streams = [
            g(fx.root, "rev-parse", "HEAD"),
            g(fx.root, "branch", "--show-current"),
            g(fx.root, "status", "--porcelain=v1"),
            g(fx.root, "for-each-ref", "refs/heads"),
            g(fx.root, "worktree", "list", "--porcelain"),
        ]
        for line in streams[4].decode("utf-8").splitlines():
            if line.startswith("worktree "):
                wt_path = line[len("worktree "):]
                streams.append(g(wt_path, "status", "--porcelain=v1")
                               if os.path.isdir(wt_path) else b"")
        self.assertEqual(rec["git_state_sha256"],
                         hashlib.sha256(b"\x00".join(streams)).hexdigest(),
                         "git_state_sha256 reproduced from the canonical bundle, "
                         "outside the module (design section 7 fixed order)")

    # -- W8R2-R / RED 8: failure paths leave pre-existing outputs untouched (GUARD) --
    def test_w8r2_r8_failures_leave_existing_pair_untouched(self):
        """GUARD - expected GREEN vs pristine (all refusal paths return before
        staging). Post-build invariant: exits 2 and 4 NEVER touch an existing
        pair (finding 10: 'unchanged pre-existing outputs on failure
        untested')."""
        fx = self.fx
        self.assertEqual(_check(fx.root).returncode, 0)
        b0 = (fx.root / BOARD_REL).read_bytes()
        r0 = (fx.root / RECEIPT_REL).read_bytes()
        # (a) missing declared input, exit 2.
        original_record = fx.record.read_bytes()
        fx.record.unlink()
        self.assertEqual(_check(fx.root).returncode, 2)
        self.assertEqual((fx.root / BOARD_REL).read_bytes(), b0,
                         "a failing check leaves the OLD pair byte-unchanged")
        self.assertEqual((fx.root / RECEIPT_REL).read_bytes(), r0)
        fx.record.write_bytes(original_record)
        # (b) policy violation, exit 2.
        pol = fx.root / POLICY_REL
        orig_policy = pol.read_text()
        pol.write_text(orig_policy + "\n[budgets]\nstart_barrier_seconds = 9\n")
        self.assertEqual(_check(fx.root).returncode, 2)
        self.assertEqual((fx.root / BOARD_REL).read_bytes(), b0)
        self.assertEqual((fx.root / RECEIPT_REL).read_bytes(), r0)
        pol.write_text(orig_policy)
        # (c) concurrent drift, exit 4, via the reviewed two-pass seam.
        reorient = _import_tool()
        real = reorient._records_manifest
        state = {"calls": 0}

        def racing(*args, **kwargs):
            out = real(*args, **kwargs)
            state["calls"] += 1
            if state["calls"] == 1:
                fx.record.write_text(fx.record.read_text() + "raced\n")
            return out

        with mock.patch.object(reorient, "_records_manifest", side_effect=racing):
            rc = reorient.main(["--repo", str(fx.root), "--now", NOW, "check"])
        self.assertEqual(rc, 4)
        self.assertEqual((fx.root / BOARD_REL).read_bytes(), b0,
                         "drift refusal leaves the OLD pair byte-unchanged")
        self.assertEqual((fx.root / RECEIPT_REL).read_bytes(), r0)

    # -- W8R2-S (F8): hostile staging symlinks are never followed --------------------
    def test_w8r2_s_hostile_staging_symlinks_never_followed(self):
        """Pre-GREEN vs pristine: FAILS (sha mismatch: `staging must never
        follow a planted symlink onto a tracked file`) - predictable tmp names
        plus write_bytes-through-symlink let a planted board.json.tmp clobber
        seed.txt and a planted board.receipt.json.tmp clobber .git/index
        (module :552-562)."""
        fx = self.fx
        out_dir = fx.root / "scratchpad" / "active" / "reorient" / "board"
        out_dir.mkdir(parents=True, exist_ok=True)
        seed = fx.root / "seed.txt"
        index = fx.root / ".git" / "index"
        seed_sha = _sha256(seed)
        index_sha = _sha256(index)
        os.symlink(seed, out_dir / "board.json.tmp")
        os.symlink(index, out_dir / "board.receipt.json.tmp")
        p = _check(fx.root)
        self.assertEqual(_sha256(seed), seed_sha,
                         "staging must never follow a planted symlink onto a "
                         "tracked file")
        self.assertEqual(_sha256(index), index_sha,
                         "staging must never follow a planted symlink onto .git/index")
        self.assertEqual(p.returncode, 0,
                         "hostile staging plants must not break generation: "
                         + p.stdout + p.stderr)
        board_path = fx.root / BOARD_REL
        receipt_path = fx.root / RECEIPT_REL
        self.assertTrue(board_path.is_file() and not board_path.is_symlink(),
                        "board.json is a regular file, never a renamed plant")
        self.assertTrue(receipt_path.is_file() and not receipt_path.is_symlink(),
                        "board.receipt.json is a regular file, never a renamed plant")
        p = _verify(fx.root)
        self.assertEqual(p.returncode, 0,
                         "the pair written around the plants verifies: "
                         + p.stdout + p.stderr)

    # -- W8R2-V (F4): verify enforces the CLOSED receipt and its honesty fields ------
    def test_w8r2_v_receipt_closure_rejected(self):
        """Pre-GREEN vs pristine: FAILS (`0 != 3 : M21a schema-version lie ...`)
        - verify ignores schema_version, unknown keys, discipline honesty, and
        inputs row shape (module :577-664); every lie below PASSes today.
        Provenance stays non-authoritative (RED 18's boundary, untouched)."""
        self.assertEqual(_check(self.fx.root).returncode, 0)
        rpath = self.fx.root / RECEIPT_REL
        pristine_bytes = rpath.read_bytes()
        self.assertEqual(_verify(self.fx.root).returncode, 0, "positive control")

        def rejected(mutant, label):
            rpath.write_bytes(
                (json.dumps(mutant, indent=2, sort_keys=True) + "\n").encode("utf-8"))
            p = _verify(self.fx.root)
            self.assertEqual(p.returncode, 3,
                             label + ": a receipt outside the closed schema must "
                             "be STALE, never PASS: " + p.stdout + p.stderr)
            self.assertTrue(p.stdout.startswith("REORIENT: STALE"), label + ": " + p.stdout)
            rpath.write_bytes(pristine_bytes)
            self.assertEqual(_verify(self.fx.root).returncode, 0,
                             label + ": restore control")

        m = json.loads(pristine_bytes)
        m["schema_version"] = 999
        rejected(m, "M21a schema-version lie")
        m = json.loads(pristine_bytes)
        m["authority"] = "operator-approved"
        rejected(m, "M21b smuggled top-level key")
        m = json.loads(pristine_bytes)
        m["discipline_enforced"] = True
        rejected(m, "M21c honesty-bit lie")
        m = json.loads(pristine_bytes)
        m["discipline"] = dict(m["discipline"], discipline_enforced=True)
        rejected(m, "M21c discipline rows must stay byte-honest")
        m = json.loads(pristine_bytes)
        m["inputs"] = [dict(m["inputs"][0], note="smuggled")] + m["inputs"][1:]
        rejected(m, "inputs row shape is closed (extra key)")
        m = json.loads(pristine_bytes)
        m["inputs"] = list(m["inputs"]) + ["garbage-row"]
        rejected(m, "inputs row shape is closed (non-dict row)")
