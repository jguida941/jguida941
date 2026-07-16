"""W7 REDs — the role gate (design: docs/plans/handoff/w7-role-integrity-design.md §3–§5).

Conductor-authored (Fable). The build lane makes these green WITHOUT editing
this file (packet: scratchpad/work/packet-w7-role-integrity-2026-07-16.md).
Shares the seed + helpers with tests/contracts/test_role_registry.py.

Seam pins (conductor decisions, binding on the builder — beyond those already
pinned in test_role_registry.py):
- The gate CLI is `python3 scripts/organization/role_gate.py <subcommand> …`
  run with CWD inside the governed repository; the gate resolves the repo root
  from CWD (git rev-parse), reads the registry ONLY from that repo's HEAD blob,
  prints exactly one machine line (`ROLE-GATE: OK …` | `ROLE-GATE: HALT
  reason=…` | `ROLE-GATE: REJECT reason=…`) and exits 0 only on OK, 2 otherwise.
- Harness transcript records: the gate refuses unknown record TYPES but
  tolerates unknown extra FIELDS inside harness records (closed-schema refusal
  binds OUR records, never harness input — design §3.3).
- Module seams: parse_review_stream(path) -> dict with at least
  {model, effort, sandbox, session_id, final_message};
  verify_review_checks(record, stream_info, sidecar) raising GateRefusal
  (reason tokens pinned below); validate_bootstrap_envelope(env) raising
  GateRefusal on any unknown/missing key.
- Hook module: READ_SAFE_TOOLS is exactly the closed six-tool tuple (V11).
- Reason tokens pinned where the design names them: tainted_epoch,
  seat_mismatch, transition, packet_floor, path_escape, patch_hash,
  unanchored_record, unanchored_review, chain, wrong_event.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.contracts.test_role_registry import (
    GATE_PATH,
    HOOK_PATH,
    SEED,
    emit_registry_toml,
    load_gate_module,
    load_hook_module,
    make_record,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "role_gate"
CANARY_PATH = FIXTURES_DIR / "hook_canary.sh"
REVIEW_STREAM_FIXTURE = FIXTURES_DIR / "review_stream_sample.jsonl"

TS = "2026-07-16T00:00:00Z"
NONCE = "a1b2c3d4e5f60718293a4b5c6d7e8f90"
FABLE_ID = "claude-fable-5"
OPUS_ID = "claude-opus-4-8"

# Design §4.1 — the launcher script (the settings row's command payload).
LAUNCHER_SCRIPT = (
    'fail(){ echo "ROLE-GATE: HALT reason=$1" >&2; exit 2; }; '
    'cd "$CLAUDE_PROJECT_DIR" || fail launcher_cd; '
    'src="$(git cat-file blob HEAD:scripts/organization/role_gate_hook.py)" '
    "|| fail launcher_blob; "
    '[ -n "$src" ] || fail launcher_empty; '
    'python3 -c "$src"; rc=$?; '
    '[ "$rc" -eq 0 ] || [ "$rc" -eq 2 ] || fail "launcher_python_rc$rc"; '
    "exit $rc"
)

READ_SAFE_SEED = ("Read", "Glob", "Grep", "ToolSearch", "WebFetch",
                  "WebSearch")


def sha256_hex(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def git(root, *args, check=True):
    return subprocess.run(
        ["git", "-C", str(root), "-c", "user.email=red@test",
         "-c", "user.name=red", *args],
        capture_output=True, text=True, check=check,
    )


def assistant_rec(uuid, model=FABLE_ID, sidechain=False, content=None,
                  omit_model=False, extra=None):
    message = {} if omit_model else {"model": model}
    if content is not None:
        message["content"] = content
    rec = {"type": "assistant", "uuid": uuid, "isSidechain": sidechain,
           "message": message, "unknown_extra_field": "tolerated"}
    if extra:
        rec.update(extra)
    return rec


def user_rec(uuid, text):
    return {"type": "user", "uuid": uuid,
            "message": {"content": text}}


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records),
                    encoding="utf-8")
    return path


def chain_snapshots(snapshots):
    """Serialize snapshots as append-only JSONL with a correct event chain."""
    lines = []
    events = []
    for snap in snapshots:
        prev = sha256_hex(lines[-1]) if lines else None
        events = events + [{"ts": TS, "to_status": snap["status"],
                            "prev_sha256": prev}]
        snap = dict(snap)
        snap["events"] = events
        lines.append(json.dumps(snap))
    return "\n".join(lines) + "\n"


class LaneRepo:
    """A temp governed repo: seed registry committed, one lane record."""

    def __init__(self, tmp, registry=None):
        self.root = Path(tmp)
        git(self.root, "init", "-q")
        (self.root / "contracts").mkdir(exist_ok=True)
        (self.root / "contracts" / "role_registry.toml").write_text(
            emit_registry_toml(registry or SEED), encoding="utf-8")
        self.records_dir = self.root / "dev" / "reports" / "role_assignments"
        self.records_dir.mkdir(parents=True)
        (self.records_dir / ".gitkeep").write_text("", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "seed")

    def registry_blob_sha(self):
        blob = git(self.root, "cat-file", "blob",
                   "HEAD:contracts/role_registry.toml").stdout
        return sha256_hex(blob)

    def transcript(self, name, records):
        return write_jsonl(self.root / "transcripts" / name, records)

    def lane_record(self, name, snapshots, commit_first_line=True):
        """Write a chained record file; commit line 1, append the rest."""
        path = self.records_dir / name
        text = chain_snapshots(snapshots)
        lines = text.splitlines(keepends=True)
        path.write_text(lines[0], encoding="utf-8")
        if commit_first_line:
            git(self.root, "add", str(path.relative_to(self.root)))
            git(self.root, "commit", "-qm", f"record {name}")
        with path.open("a", encoding="utf-8") as fh:
            fh.writelines(lines[1:])
        return path

    def commit_all(self, message="more"):
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", message)


def run_gate(cwd, *args):
    if not GATE_PATH.is_file():
        raise AssertionError(f"gate module missing: {GATE_PATH}")
    return subprocess.run(
        [sys.executable, str(GATE_PATH), *args],
        capture_output=True, text=True, cwd=str(cwd), timeout=120,
    )


def run_hook(cwd, stdin_obj, env_extra=None):
    if not HOOK_PATH.is_file():
        raise AssertionError(f"hook module missing: {HOOK_PATH}")
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(cwd)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(stdin_obj), capture_output=True, text=True,
        cwd=str(cwd), env=env, timeout=120,
    )


def hook_stdin(session_id, transcript_path, tool_name, tool_input=None,
               event="PreToolUse", drop=None):
    payload = {
        "session_id": session_id,
        "transcript_path": str(transcript_path),
        "cwd": ".",
        "hook_event_name": event,
        "tool_name": tool_name,
        "tool_input": tool_input or {},
    }
    for key in drop or []:
        payload.pop(key, None)
    return payload


def clean_conductor_transcript(repo, session_id="sess-conductor"):
    return repo.transcript(
        f"{session_id}.jsonl",
        [user_rec("u0", "start"),
         assistant_rec("a1"), assistant_rec("a2")],
    )


def dispatched_snapshots(transcript_path, session_id="sess-lane-1",
                         **overrides):
    prepared = make_record(
        status="prepared",
        session_binding={"session_ids": [], "transcript_paths": [],
                         "worktree": ".claude/worktrees/red-fixture",
                         "parent_session_id": "sess-conductor"},
        dispatch_nonce=NONCE,
    )
    dispatched = make_record(
        status="dispatched",
        session_binding={"session_ids": [session_id],
                         "transcript_paths": [str(transcript_path)],
                         "worktree": ".claude/worktrees/red-fixture",
                         "parent_session_id": "sess-conductor"},
        dispatch_nonce=NONCE,
    )
    for snap in (prepared, dispatched):
        snap.pop("events", None)
        snap.update(overrides)
    return [prepared, dispatched]


def opus_lane_transcript(repo, name="lane.jsonl", first_text=None,
                         records=None):
    if records is None:
        records = [user_rec("u0", first_text if first_text is not None
                            else f"packet … nonce {NONCE}"),
                   assistant_rec("a1", model=OPUS_ID),
                   assistant_rec("a2", model=OPUS_ID)]
    return repo.transcript(name, records)


class FixturesShipped(unittest.TestCase):
    def test_harvested_fixtures_present(self):
        self.assertTrue(FIXTURES_DIR.is_dir(),
                        f"fixture home missing: {FIXTURES_DIR}")
        harvested = sorted(FIXTURES_DIR.glob("*.jsonl"))
        self.assertTrue(harvested, "no harvested session fixtures shipped")
        with_sidecar = [p for p in harvested
                        if (p.parent / (p.name + ".provenance.json")).is_file()]
        self.assertTrue(with_sidecar,
                        "harvested fixtures must carry provenance sidecars")

    def test_hook_canary_shipped_executable(self):
        self.assertTrue(CANARY_PATH.is_file(),
                        f"canary missing: {CANARY_PATH}")
        self.assertTrue(os.access(CANARY_PATH, os.X_OK),
                        "canary must be executable")


class G1G2G3EpochScan(unittest.TestCase):
    def check_conductor(self, records):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = repo.transcript("conductor.jsonl", records)
            return run_gate(repo.root, "check-conductor",
                            "--transcript", str(transcript))

    def test_g1_all_conductor_epoch_ok(self):
        result = self.check_conductor(
            [user_rec("u0", "start"), assistant_rec("a1"),
             assistant_rec("a2")])
        self.assertEqual(result.returncode, 0,
                         result.stdout + result.stderr)
        self.assertTrue(result.stdout.startswith("ROLE-GATE: OK"),
                        result.stdout)

    def test_g2_foreign_model_anywhere_halts(self):
        variants = {
            "foreign in the middle": [
                assistant_rec("a1"), assistant_rec("a2", model=OPUS_ID),
                assistant_rec("a3")],
            "stale tail (early foreign, clean tail)": [
                assistant_rec("a1", model=OPUS_ID), assistant_rec("a2"),
                assistant_rec("a3"), assistant_rec("a4")],
        }
        for label, records in variants.items():
            with self.subTest(label=label):
                result = self.check_conductor(records)
                self.assertEqual(result.returncode, 2, label)
                self.assertIn("reason=tainted_epoch",
                              result.stdout + result.stderr, label)

    def test_g2_sidechain_foreign_is_not_main_chain(self):
        result = self.check_conductor(
            [assistant_rec("a1"),
             assistant_rec("a2", model=OPUS_ID, sidechain=True),
             assistant_rec("a3")])
        self.assertEqual(result.returncode, 0,
                         result.stdout + result.stderr)

    def test_g3_model_key_absent_halts(self):
        result = self.check_conductor(
            [assistant_rec("a1"), assistant_rec("a2", omit_model=True)])
        self.assertEqual(result.returncode, 2)

    def test_g3_zero_assistant_records_halts(self):
        result = self.check_conductor([user_rec("u0", "only a user line")])
        self.assertEqual(result.returncode, 2)


class G4RefusalMatrix(unittest.TestCase):
    def run_on_transcript_bytes(self, tmp, data_bytes):
        repo = LaneRepo(tmp)
        path = repo.root / "transcripts" / "t.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data_bytes)
        return run_gate(repo.root, "check-conductor",
                        "--transcript", str(path))

    def test_g4_refusal_variants(self):
        clean_line = json.dumps(assistant_rec("a1")) + "\n"
        byte_variants = {
            "empty file": b"",
            "partial trailing line": (clean_line + '{"type": "assist').encode(),
            "unknown record type": (json.dumps({"type": "mystery",
                                                "uuid": "x"}) + "\n").encode(),
            "string false sidechain": (json.dumps(
                {"type": "assistant", "uuid": "a1", "isSidechain": "false",
                 "message": {"model": FABLE_ID}}) + "\n").encode(),
        }
        for label, data in byte_variants.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmp:
                    result = self.run_on_transcript_bytes(tmp, data)
                    self.assertEqual(result.returncode, 2, label)

    def test_g4_symlink_transcript_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            real = repo.transcript("real.jsonl", [assistant_rec("a1")])
            link = repo.root / "transcripts" / "link.jsonl"
            os.symlink(real, link)
            result = run_gate(repo.root, "check-conductor",
                              "--transcript", str(link))
            self.assertEqual(result.returncode, 2)

    def test_g4_missing_directory_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            result = run_gate(repo.root, "check-conductor", "--transcript",
                              str(repo.root / "nowhere" / "t.jsonl"))
            self.assertEqual(result.returncode, 2)


class G5AssertAuthority(unittest.TestCase):
    def assert_authority(self, verb):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = clean_conductor_transcript(repo)
            return run_gate(repo.root, "assert-authority", "--action", verb,
                            "--transcript", str(transcript))

    def test_g5_verb_matrix(self):
        result = self.assert_authority("commit")
        self.assertEqual(result.returncode, 0,
                         result.stdout + result.stderr)
        for verb, label in (("implement", "held-forbidden verb"),
                            ("levitate", "unknown verb")):
            with self.subTest(label=label):
                result = self.assert_authority(verb)
                self.assertEqual(result.returncode, 2, label)


class G6CheckLane(unittest.TestCase):
    def check_lane(self, repo, record_path):
        return run_gate(repo.root, "check-lane", "--assignment",
                        str(record_path))

    def test_g6_clean_lane_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(repo)
            record = repo.lane_record("lane.jsonl",
                                      dispatched_snapshots(transcript))
            result = self.check_lane(repo, record)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)

    def test_g6_foreign_model_rejects(self):
        # Seat-neutral symmetry (design M3): the lane expects opus; a
        # fable-model transcript must be rejected the same way.
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(
                repo, records=[user_rec("u0", f"nonce {NONCE}"),
                               assistant_rec("a1", model=FABLE_ID)])
            record = repo.lane_record("lane.jsonl",
                                      dispatched_snapshots(transcript))
            result = self.check_lane(repo, record)
            self.assertEqual(result.returncode, 2)

    def test_g6_nonce_missing_transcript_rejects(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(
                repo, first_text="a clean but unrelated transcript")
            record = repo.lane_record("lane.jsonl",
                                      dispatched_snapshots(transcript))
            result = self.check_lane(repo, record)
            self.assertEqual(result.returncode, 2)

    def test_g6_undeclared_child_rejects(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            child_call = [{"type": "tool_use", "name": "Task",
                           "input": {"prompt": "spawn"}}]
            transcript = opus_lane_transcript(
                repo, records=[user_rec("u0", f"nonce {NONCE}"),
                               assistant_rec("a1", model=OPUS_ID,
                                             content=child_call)])
            record = repo.lane_record("lane.jsonl",
                                      dispatched_snapshots(transcript))
            result = self.check_lane(repo, record)
            self.assertEqual(result.returncode, 2)


class G7VerifyReview(unittest.TestCase):
    def stream_info(self, **overrides):
        info = {
            "model": "gpt-5.6-sol",
            "effort": "max",
            "sandbox": "read-only",
            "session_id": "codex-sess-1",
            "final_message": (
                f"review of artifact {'5' * 64} for lane red-fixture-r6 "
                f"nonce {NONCE}\nfindings: none\n"
                "VERDICT: approve\nADVERSARIAL-VERDICT: approve\n"
            ),
        }
        info.update(overrides)
        return info

    def sidecar(self, **overrides):
        side = {
            "lane_run_id": "red-fixture-r6", "argv": ["exec"],
            "prompt_sha256": "6" * 64, "output_sha256": "7" * 64,
            "model": "gpt-5.6-sol", "effort": "max", "sandbox": "read-only",
            "artifact_sha256": "5" * 64, "codex_session_id": "codex-sess-1",
            "exit_status": 0, "nonce": NONCE, "ts": TS,
        }
        side.update(overrides)
        return side

    def record(self):
        return make_record(status="complete",
                           completion={"output_patch_sha256": "5" * 64,
                                       "transcript_manifest_sha256": "8" * 64})

    def test_g7_parse_real_stream_fixture(self):
        gate = load_gate_module()
        self.assertTrue(REVIEW_STREAM_FIXTURE.is_file(),
                        f"harvested stream fixture missing: "
                        f"{REVIEW_STREAM_FIXTURE}")
        info = gate.parse_review_stream(REVIEW_STREAM_FIXTURE)
        for key in ("model", "effort", "sandbox", "session_id",
                    "final_message"):
            self.assertTrue(str(info.get(key, "")).strip(),
                            f"stream parse must yield {key}")

    def test_g7_law_matrix(self):
        gate = load_gate_module()
        base_record = self.record()

        revise_only = self.stream_info(final_message=(
            f"artifact {'5' * 64} lane red-fixture-r6 nonce {NONCE}\n"
            "VERDICT: revise\nADVERSARIAL-VERDICT: revise\n"))
        single_arm = self.stream_info(final_message=(
            f"artifact {'5' * 64} lane red-fixture-r6 nonce {NONCE}\n"
            "VERDICT: approve\n"))
        design_for_code = self.stream_info(final_message=(
            f"artifact {'5' * 64} lane red-fixture-r6 nonce {NONCE}\n"
            "DESIGN-VERDICT: APPROVE\n"))
        effort_mismatch = self.stream_info(effort="xhigh")
        no_artifact_echo = self.stream_info(final_message=(
            f"lane red-fixture-r6 nonce {NONCE}\n"
            "VERDICT: approve\nADVERSARIAL-VERDICT: approve\n"))
        no_lane_echo = self.stream_info(final_message=(
            f"artifact {'5' * 64} nonce {NONCE}\n"
            "VERDICT: approve\nADVERSARIAL-VERDICT: approve\n"))

        cases = {
            "revise is a valid transcript, not approval": revise_only,
            "single-arm code review is not approval": single_arm,
            "a design verdict never satisfies a code review": design_for_code,
            "effort below the review profile": effort_mismatch,
            "missing artifact hash echo": no_artifact_echo,
            "missing lane id echo": no_lane_echo,
        }
        for label, info in cases.items():
            with self.subTest(label=label):
                with self.assertRaises(gate.GateRefusal, msg=label):
                    gate.verify_review_checks(base_record, info,
                                              self.sidecar())

    def test_g7_sidecar_missing_fields_reject(self):
        gate = load_gate_module()
        for missing in ("lane_run_id", "model", "effort", "sandbox",
                        "artifact_sha256"):
            with self.subTest(missing=missing):
                side = self.sidecar()
                side.pop(missing)
                with self.assertRaises(gate.GateRefusal):
                    gate.verify_review_checks(self.record(),
                                              self.stream_info(), side)

    def test_g7_consistent_review_passes(self):
        gate = load_gate_module()
        gate.verify_review_checks(self.record(), self.stream_info(),
                                  self.sidecar())


class G8Census(unittest.TestCase):
    def test_g8_unmatched_worktree_rejects(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            # Inside the tmp sandbox (so cleanup removes it) but outside
            # .claude/worktrees — census must flag it as unmatched.
            git(repo.root, "worktree", "add", "-q", "-b", "stray",
                str(repo.root / "wt" / "stray-worktree"))
            result = run_gate(repo.root, "census")
            self.assertEqual(result.returncode, 2,
                             result.stdout + result.stderr)

    def test_g8_session_only_null_worktree_lane_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = repo.transcript(
                "audit.jsonl", [user_rec("u0", f"nonce {NONCE}"),
                                assistant_rec("a1", model=OPUS_ID)])
            snaps = dispatched_snapshots(transcript, session_id="sess-audit")
            for snap in snaps:
                snap.update({
                    "lane_run_id": "audit-1", "execution_kind": "session_only",
                    "role": "auditor", "actor": "opus",
                    "packet": {"artifact_refs": ["docs/plans/ACTIVE.md"]},
                })
                snap["session_binding"] = dict(snap["session_binding"],
                                               worktree=None)
            repo.lane_record("audit.jsonl", snaps)
            result = run_gate(repo.root, "census")
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)

    def test_g8_two_live_conductor_records_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            for n in (1, 2):
                transcript = clean_conductor_transcript(repo, f"sess-c{n}")
                snaps = dispatched_snapshots(transcript,
                                             session_id=f"sess-c{n}")
                for snap in snaps:
                    snap.update({"lane_run_id": f"conductor-{n}",
                                 "execution_kind": "main",
                                 "role": "conductor", "actor": "fable",
                                 "packet": {"artifact_refs": []}})
                    snap["session_binding"] = dict(snap["session_binding"],
                                                   worktree=None)
                repo.lane_record(f"conductor-{n}.jsonl", snaps)
            result = run_gate(repo.root, "census")
            self.assertEqual(result.returncode, 2)


class G9G10LifecycleAndRecompute(unittest.TestCase):
    def test_g9_backfilled_verdict_cannot_integrate(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(repo)
            snaps = dispatched_snapshots(transcript)
            # Hand-edit: jump straight to an "integrated" snapshot with a
            # backfilled ok verdict — the recompute must refuse regardless.
            forged = dict(snaps[1])
            forged["status"] = "integrated"
            forged["verification"] = {"verified_model_ids": [OPUS_ID],
                                      "verified_at": TS, "verdict": "ok"}
            record = repo.lane_record("lane.jsonl", snaps + [forged],
                                      commit_first_line=True)
            patch = repo.root / "p.patch"
            patch.write_text("diff --git a/x b/x\n", encoding="utf-8")
            result = run_gate(repo.root, "integrate", "--assignment",
                              str(record), "--patch", str(patch))
            self.assertEqual(result.returncode, 2)

    def test_g10_status_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(repo)
            snaps = dispatched_snapshots(transcript)
            snaps[1] = dict(snaps[1], dispatch_nonce="")
            record = repo.lane_record("lane.jsonl", snaps)
            result = run_gate(repo.root, "check-lane", "--assignment",
                              str(record))
            self.assertEqual(result.returncode, 2)

    def test_g10_killed_is_permanently_non_integrable(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(repo)
            snaps = dispatched_snapshots(transcript)
            killed = dict(snaps[1])
            killed["status"] = "killed"
            record = repo.lane_record("lane.jsonl", snaps + [killed])
            patch = repo.root / "p.patch"
            patch.write_text("diff --git a/x b/x\n", encoding="utf-8")
            result = run_gate(repo.root, "integrate", "--assignment",
                              str(record), "--patch", str(patch))
            self.assertEqual(result.returncode, 2)

    def test_g10_retro_review_queue_blocks_push(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(repo)
            snaps = dispatched_snapshots(transcript)
            integrated = dict(snaps[1])
            integrated["status"] = "integrated"
            integrated["standin"] = {"active": True, "standin_actor": "fable",
                                     "retro_review_queued": True,
                                     "retro_review_ref": None}
            repo.lane_record("lane.jsonl", snaps + [integrated])
            repo.commit_all("integrated record")
            conductor_transcript = clean_conductor_transcript(repo)
            result = run_gate(repo.root, "assert-authority", "--action",
                              "push", "--transcript",
                              str(conductor_transcript))
            self.assertEqual(result.returncode, 2,
                             "push must refuse while a retroactive review "
                             "is queued without a ref")


class V1SeatBinding(unittest.TestCase):
    def test_v1_actor_must_match_seat(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = clean_conductor_transcript(repo)
            snaps = dispatched_snapshots(transcript,
                                         session_id="sess-conductor")
            for snap in snaps:
                snap.update({"role": "conductor", "actor": "opus",
                             "execution_kind": "main",
                             "packet": {"artifact_refs": []}})
                snap["session_binding"] = dict(snap["session_binding"],
                                               worktree=None)
            record = repo.lane_record("lane.jsonl", snaps)
            result = run_gate(repo.root, "check-lane", "--assignment",
                              str(record))
            self.assertEqual(result.returncode, 2)
            self.assertIn("reason=seat_mismatch",
                          result.stdout + result.stderr)

    def test_v1_dispatched_by_bound_to_conductor_seat(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(repo)
            record = repo.lane_record(
                "lane.jsonl",
                dispatched_snapshots(transcript, dispatched_by="opus"))
            result = run_gate(repo.root, "check-lane", "--assignment",
                              str(record))
            self.assertEqual(result.returncode, 2)


class V2Lifecycle(unittest.TestCase):
    def run_check(self, repo, record_path):
        return run_gate(repo.root, "check-lane", "--assignment",
                        str(record_path))

    def test_v2_lifecycle_transitions_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(repo)

            prepared_with_sessions = dispatched_snapshots(transcript)[0]
            prepared_with_sessions["session_binding"] = {
                "session_ids": ["sess-early"], "transcript_paths": [],
                "worktree": ".claude/worktrees/red-fixture",
                "parent_session_id": "sess-conductor"}
            record = repo.lane_record(
                "a.jsonl", [prepared_with_sessions])
            self.assertEqual(self.run_check(repo, record).returncode, 2,
                             "prepared with sessions must refuse")

            dispatched_empty = dispatched_snapshots(transcript)[1]
            dispatched_empty["session_binding"] = {
                "session_ids": [], "transcript_paths": [],
                "worktree": ".claude/worktrees/red-fixture",
                "parent_session_id": "sess-conductor"}
            record = repo.lane_record("b.jsonl", [
                dispatched_snapshots(transcript)[0], dispatched_empty])
            self.assertEqual(self.run_check(repo, record).returncode, 2,
                             "dispatched with zero sessions must refuse")

            snaps = dispatched_snapshots(transcript)
            illegal = dict(snaps[0])
            illegal["status"] = "integrated"
            record = repo.lane_record("c.jsonl", [snaps[0], illegal])
            result = self.run_check(repo, record)
            self.assertEqual(result.returncode, 2)
            self.assertIn("reason=transition",
                          result.stdout + result.stderr)

    def test_v2_per_lane_completion_shapes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = repo.transcript(
                "audit.jsonl", [user_rec("u0", f"nonce {NONCE}"),
                                assistant_rec("a1", model=OPUS_ID)])
            snaps = dispatched_snapshots(transcript, session_id="sess-lane-1")
            complete = dict(snaps[1])
            complete.update({
                "role": "auditor", "actor": "opus",
                "execution_kind": "session_only", "status": "complete",
                "packet": {"artifact_refs": []},
                "completion": {"output_patch_sha256": "9" * 64,
                               "transcript_manifest_sha256": "8" * 64},
            })
            for snap in snaps:
                snap.update({"role": "auditor", "actor": "opus",
                             "execution_kind": "session_only",
                             "packet": {"artifact_refs": []}})
                snap["session_binding"] = dict(snap["session_binding"],
                                               worktree=None)
            complete["session_binding"] = dict(complete["session_binding"],
                                               worktree=None)
            record = repo.lane_record("audit.jsonl", snaps + [complete])
            self.assertEqual(self.run_check(repo, record).returncode, 2,
                             "a patch-shaped completion on a non-builder "
                             "lane must refuse")

    def test_v2_missing_execution_kind_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(repo)
            snaps = dispatched_snapshots(transcript)
            for snap in snaps:
                snap.pop("execution_kind", None)
            record = repo.lane_record("lane.jsonl", snaps)
            self.assertEqual(self.run_check(repo, record).returncode, 2)


class V3Launcher(unittest.TestCase):
    def make_hook_repo(self, tmp, hook_source):
        root = Path(tmp)
        git(root, "init", "-q")
        (root / "contracts").mkdir()
        (root / "contracts" / "role_registry.toml").write_text(
            emit_registry_toml(SEED), encoding="utf-8")
        hook_dir = root / "scripts" / "organization"
        hook_dir.mkdir(parents=True)
        (hook_dir / "role_gate_hook.py").write_text(hook_source,
                                                    encoding="utf-8")
        git(root, "add", ".")
        git(root, "commit", "-qm", "seed")
        return root

    def run_launcher(self, root, stdin_text="{}", env_extra=None):
        env = dict(os.environ)
        env["CLAUDE_PROJECT_DIR"] = str(root)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(["/bin/bash", "-c", LAUNCHER_SCRIPT],
                              input=stdin_text, capture_output=True,
                              text=True, cwd=str(root), env=env, timeout=120)

    def test_v3_launcher_normalizes_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_hook_repo(
                tmp, "raise RuntimeError('deliberate failure')\n")
            result = self.run_launcher(root)
            self.assertEqual(result.returncode, 2,
                             result.stdout + result.stderr)
            self.assertIn("ROLE-GATE:", result.stderr)

    def test_v3_missing_interpreter_never_escapes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_hook_repo(tmp, "import sys; sys.exit(0)\n")
            bin_dir = root / "thin-path"
            bin_dir.mkdir()
            for tool in ("bash", "git", "sh", "echo"):
                real = subprocess.run(["/usr/bin/which", tool],
                                      capture_output=True, text=True)
                if real.returncode == 0 and real.stdout.strip():
                    os.symlink(real.stdout.strip(), bin_dir / tool)
            result = self.run_launcher(root,
                                       env_extra={"PATH": str(bin_dir)})
            self.assertEqual(result.returncode, 2,
                             "exit 127 must be normalized to 2")

    def test_v3_hook_input_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = clean_conductor_transcript(repo)
            missing = hook_stdin("sess-x", transcript, "Bash",
                                 drop=["session_id"])
            result = run_hook(repo.root, missing)
            self.assertEqual(result.returncode, 2,
                             "missing session_id must refuse")
            wrong_event = hook_stdin("sess-x", transcript, "Bash",
                                     event="PostToolUse")
            result = run_hook(repo.root, wrong_event)
            self.assertEqual(result.returncode, 2)
            self.assertIn("reason=wrong_event",
                          result.stdout + result.stderr)


class V4HookClassifier(unittest.TestCase):
    def lane(self, tmp, role, actor, model_id, standin=None,
             author_actor="opus"):
        repo = LaneRepo(tmp)
        session_id = f"sess-{role}"
        transcript = repo.transcript(
            f"{session_id}.jsonl",
            [user_rec("u0", f"nonce {NONCE}"),
             assistant_rec("a1", model=model_id)])
        snaps = dispatched_snapshots(transcript, session_id=session_id)
        for snap in snaps:
            snap.update({"role": role, "actor": actor,
                         "lane_run_id": f"{role}-lane-1",
                         "author_actor": author_actor})
            if role != "builder":
                snap["packet"] = {"artifact_refs": []}
                snap["execution_kind"] = "session_only"
                snap["session_binding"] = dict(snap["session_binding"],
                                               worktree=None)
            if standin:
                snap["standin"] = standin
        repo.lane_record(f"{role}.jsonl", snaps)
        return repo, session_id, transcript

    def reviewer_standin(self, tmp):
        return self.lane(
            tmp, "reviewer", "codex", FABLE_ID,
            standin={"active": True, "standin_actor": "fable",
                     "retro_review_queued": True, "retro_review_ref": None},
            author_actor="opus")

    def test_v4_write_shaped_bash_classified(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, session_id, transcript = self.reviewer_standin(tmp)
            stdin = hook_stdin(session_id, transcript, "Bash",
                               {"command": "echo x > site/index.html"})
            result = run_hook(repo.root, stdin)
            self.assertEqual(result.returncode, 2,
                             "a write-shaped command against a governed "
                             "path is implement — forbidden for a reviewer")

    def test_v4_git_default_deny(self):
        cases = [
            ("builder", "opus", OPUS_ID, None,
             "git cherry-pick abc", 2),
            ("reviewer", None, None, "standin", "git apply p.patch", 2),
            ("reviewer", None, None, "standin", "git gc", 2),
        ]
        for role, actor, model, standin_kind, command, expected in cases:
            with self.subTest(command=command, role=role):
                with tempfile.TemporaryDirectory() as tmp:
                    if standin_kind:
                        repo, session_id, transcript = (
                            self.reviewer_standin(tmp))
                    else:
                        repo, session_id, transcript = self.lane(
                            tmp, role, actor, model)
                    stdin = hook_stdin(session_id, transcript, "Bash",
                                       {"command": command})
                    result = run_hook(repo.root, stdin)
                    self.assertEqual(result.returncode, expected, command)

    def test_v4_git_status_allowed_for_seated_lanes(self):
        for role, actor, model in (("builder", "opus", OPUS_ID),
                                   ("auditor", "opus", OPUS_ID),
                                   ("demo_runner", "opus", OPUS_ID)):
            with self.subTest(role=role):
                with tempfile.TemporaryDirectory() as tmp:
                    repo, session_id, transcript = self.lane(
                        tmp, role, actor, model)
                    stdin = hook_stdin(session_id, transcript, "Bash",
                                       {"command": "git status"})
                    result = run_hook(repo.root, stdin)
                    self.assertEqual(result.returncode, 0,
                                     result.stdout + result.stderr)


class V5IntegrateOnlyViaGate(unittest.TestCase):
    def test_v5_integrate_only_via_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            session_id = "sess-conductor"
            transcript = clean_conductor_transcript(repo, session_id)
            stdin = hook_stdin(session_id, transcript, "Bash",
                               {"command": "git merge lane-branch"})
            result = run_hook(repo.root, stdin)
            self.assertEqual(result.returncode, 2,
                             "raw integration-shaped git must refuse even "
                             "for the seated conductor")

    def _reviewed_lane(self, repo):
        """A fully consistent reviewed lane: clean transcript, committed
        review refs, a real patch whose hash the record binds."""
        transcript = opus_lane_transcript(repo)
        allowed = "scripts/organization/example.py"
        work = repo.root / allowed
        work.parent.mkdir(parents=True, exist_ok=True)
        work.write_text("print('v1')\n", encoding="utf-8")
        git(repo.root, "add", allowed)
        git(repo.root, "commit", "-qm", "base module")
        work.write_text("print('v2')\n", encoding="utf-8")
        patch_text = git(repo.root, "diff").stdout
        git(repo.root, "checkout", "--", allowed)
        patch = repo.root / "lane.patch"
        patch.write_text(patch_text, encoding="utf-8")
        patch_sha = sha256_hex(patch_text)

        review_rel = "dev/reports/reviews/lane-review.md"
        review_path = repo.root / review_rel
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text("VERDICT: approve\n", encoding="utf-8")
        git(repo.root, "add", review_rel)
        git(repo.root, "commit", "-qm", "review")
        review_sha = sha256_hex(review_path.read_bytes())

        snaps = dispatched_snapshots(transcript)
        complete = dict(snaps[1])
        complete["status"] = "complete"
        complete["completion"] = {"output_patch_sha256": patch_sha,
                                  "transcript_manifest_sha256": "8" * 64}
        reviewed = dict(complete)
        reviewed["status"] = "reviewed"
        reviewed["review"] = {"reviewed_patch_sha256": patch_sha,
                              "review_refs": [{"path": review_rel,
                                               "sha256": review_sha}]}
        record = repo.lane_record("lane.jsonl",
                                  snaps + [complete, reviewed])
        return record, patch

    def test_v5_integrate_recomputes_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            record, patch = self._reviewed_lane(repo)

            stray = repo.root / "docs"
            stray.mkdir(exist_ok=True)
            (stray / "stray.md").write_text("x\n", encoding="utf-8")
            git(repo.root, "add", "docs/stray.md")
            escape_text = git(repo.root, "diff", "--cached").stdout
            git(repo.root, "reset", "-q")
            (stray / "stray.md").unlink()
            escape_patch = repo.root / "escape.patch"
            escape_patch.write_text(escape_text, encoding="utf-8")

            result = run_gate(repo.root, "integrate", "--assignment",
                              str(record), "--patch", str(escape_patch))
            self.assertEqual(result.returncode, 2)
            out = result.stdout + result.stderr
            self.assertTrue("reason=path_escape" in out
                            or "reason=patch_hash" in out, out)

    def test_v5_patch_hash_equality_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            record, patch = self._reviewed_lane(repo)
            patch.write_text(patch.read_text(encoding="utf-8") + "\n# pad\n",
                             encoding="utf-8")
            result = run_gate(repo.root, "integrate", "--assignment",
                              str(record), "--patch", str(patch))
            self.assertEqual(result.returncode, 2)
            self.assertIn("reason=patch_hash",
                          result.stdout + result.stderr)


class V6ReviewAnchoring(unittest.TestCase):
    def test_v6_reviews_committed_before_integrate(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            helper = V5IntegrateOnlyViaGate()
            record, patch = helper._reviewed_lane(repo)
            record_lines = record.read_text(encoding="utf-8").splitlines()
            last = json.loads(record_lines[-1])
            last["review"]["review_refs"] = [
                {"path": "dev/reports/reviews/never-committed.md",
                 "sha256": "b" * 64}]
            # Rebuild the tail snapshot with a fresh, correct chain so the
            # ONLY defect is the unanchored review reference.
            snaps = [json.loads(line) for line in record_lines]
            for snap in snaps:
                snap.pop("events", None)
            snaps[-1] = {k: v for k, v in last.items() if k != "events"}
            path = repo.records_dir / "lane2.jsonl"
            path.write_text(chain_snapshots(snaps), encoding="utf-8")
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            path.write_text(lines[0], encoding="utf-8")
            git(repo.root, "add",
                str(path.relative_to(repo.root)))
            git(repo.root, "commit", "-qm", "record lane2")
            with path.open("a", encoding="utf-8") as fh:
                fh.writelines(lines[1:])
            result = run_gate(repo.root, "integrate", "--assignment",
                              str(path), "--patch", str(repo.root /
                                                        "lane.patch"))
            self.assertEqual(result.returncode, 2)
            self.assertIn("reason=unanchored_review",
                          result.stdout + result.stderr)


class V7PacketFloor(unittest.TestCase):
    def check(self, repo, record_path):
        return run_gate(repo.root, "check-lane", "--assignment",
                        str(record_path))

    def test_v7_builder_packet_floor(self):
        floor_cases = {
            "red-authoring surface": ["tests/contracts/test_x.py"],
            "doc-law surface": ["docs/plans/ACTIVE.md"],
        }
        for label, allowed in floor_cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = LaneRepo(tmp)
                    transcript = opus_lane_transcript(repo)
                    snaps = dispatched_snapshots(transcript)
                    for snap in snaps:
                        snap["packet"] = dict(snap["packet"],
                                              allowed_paths=allowed)
                    record = repo.lane_record("lane.jsonl", snaps)
                    result = self.check(repo, record)
                    self.assertEqual(result.returncode, 2, label)
                    self.assertIn("reason=packet_floor",
                                  result.stdout + result.stderr, label)

    def test_v7_enforcement_surface_needs_design_verdict(self):
        enforcement_path = "scripts/organization/role_gate.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(repo)
            snaps = dispatched_snapshots(transcript)
            for snap in snaps:
                packet = dict(snap["packet"],
                              allowed_paths=[enforcement_path])
                packet["design_verdict_ref"] = None
                snap["packet"] = packet
            record = repo.lane_record("bare.jsonl", snaps)
            self.assertEqual(self.check(repo, record).returncode, 2,
                             "enforcement path without a design verdict "
                             "ref must refuse")

        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(repo)
            snaps = dispatched_snapshots(transcript)
            for snap in snaps:
                snap["packet"] = dict(snap["packet"],
                                      allowed_paths=[enforcement_path])
            record = repo.lane_record("lawful.jsonl", snaps)
            result = self.check(repo, record)
            self.assertEqual(result.returncode, 0,
                             "the reviewed maintenance lane must stay "
                             "lawful: " + result.stdout + result.stderr)


class V8AttestedReslot(unittest.TestCase):
    def test_v8_attested_reslot_passes_r7(self):
        gate = load_gate_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            old_blob = git(repo.root, "cat-file", "blob",
                           "HEAD:contracts/role_registry.toml").stdout
            flipped = json.loads(json.dumps(SEED))
            flipped["seats"]["builder"] = "fable"
            new_text = emit_registry_toml(flipped)
            (repo.root / "contracts" / "role_registry.toml").write_text(
                new_text, encoding="utf-8")
            attestation = {
                "record": "SeatReslot",
                "old_registry_sha256": sha256_hex(old_blob),
                "new_registry_sha256": sha256_hex(new_text),
                "operator_ref": "operator message 2026-07-16 (verbatim ref)",
                "ts": TS,
            }
            att_path = repo.records_dir / "reslot-20260716T000000Z.json"
            att_path.write_text(json.dumps(attestation, indent=2),
                                encoding="utf-8")
            repo.commit_all("attested reslot")
            loaded = gate.load_registry(repo.root)
            self.assertEqual(loaded["seats"]["builder"], "fable")

    def test_v8_unattested_flip_refuses(self):
        gate = load_gate_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            flipped = json.loads(json.dumps(SEED))
            flipped["seats"]["builder"] = "fable"
            (repo.root / "contracts" / "role_registry.toml").write_text(
                emit_registry_toml(flipped), encoding="utf-8")
            repo.commit_all("silent flip")
            with self.assertRaises(gate.GateRefusal):
                gate.load_registry(repo.root)


class V9ChainAndAnchor(unittest.TestCase):
    def test_v9_event_chain_recomputable(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(repo)
            snaps = dispatched_snapshots(transcript)
            text = chain_snapshots(snaps)
            lines = text.splitlines()
            second = json.loads(lines[1])
            second["events"][-1]["prev_sha256"] = "0" * 64
            path = repo.records_dir / "lane.jsonl"
            path.write_text(lines[0] + "\n", encoding="utf-8")
            git(repo.root, "add", str(path.relative_to(repo.root)))
            git(repo.root, "commit", "-qm", "record")
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(second) + "\n")
            result = run_gate(repo.root, "check-lane", "--assignment",
                              str(path))
            self.assertEqual(result.returncode, 2)
            self.assertIn("reason=chain", result.stdout + result.stderr)

    def test_v9_record_anchored_in_head(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(repo)
            record = repo.lane_record("lane.jsonl",
                                      dispatched_snapshots(transcript),
                                      commit_first_line=False)
            result = run_gate(repo.root, "check-lane", "--assignment",
                              str(record))
            self.assertEqual(result.returncode, 2)
            self.assertIn("reason=unanchored_record",
                          result.stdout + result.stderr)

    def test_v9_head_must_be_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = opus_lane_transcript(repo)
            record = repo.lane_record("lane.jsonl",
                                      dispatched_snapshots(transcript))
            text = record.read_text(encoding="utf-8")
            record.write_text(text.replace(NONCE, "e" * 32),
                              encoding="utf-8")
            result = run_gate(repo.root, "check-lane", "--assignment",
                              str(record))
            self.assertEqual(result.returncode, 2)

    def test_v9_bootstrap_envelope_closed(self):
        gate = load_gate_module()
        good = {
            "record": "BootstrapEnvelope", "schema_version": 1,
            "operator_ref": {"message_ts": TS, "quote": "build it"},
            "covers": ["w7-build-r1"], "pre_enforcement": True,
            "activation_commit": None, "census_at_activation": None,
        }
        gate.validate_bootstrap_envelope(good)
        for defect in ("missing activation_commit",
                       "missing census_at_activation", "unknown key"):
            with self.subTest(defect=defect):
                env = json.loads(json.dumps(good))
                if defect == "unknown key":
                    env["surprise"] = 1
                else:
                    env.pop(defect.split()[-1])
                with self.assertRaises(gate.GateRefusal):
                    gate.validate_bootstrap_envelope(env)


class V10StandinArm(unittest.TestCase):
    def test_v10_standin_arm(self):
        gate = load_gate_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            registry = gate.load_registry(repo.root)

            same_principal = make_record(
                author_actor="opus",
                standin={"active": True, "standin_actor": "opus",
                         "retro_review_queued": True,
                         "retro_review_ref": None})
            with self.assertRaises(gate.GateRefusal):
                gate.validate_record(same_principal, registry)

            unqueued = make_record(
                standin={"active": True, "standin_actor": "fable",
                         "retro_review_queued": False,
                         "retro_review_ref": None})
            with self.assertRaises(gate.GateRefusal):
                gate.validate_record(unqueued, registry)


class V11ReadFloor(unittest.TestCase):
    def test_v11_read_floor_pinned(self):
        hook = load_hook_module()
        self.assertEqual(tuple(hook.READ_SAFE_TOOLS), READ_SAFE_SEED)

    def test_v11_no_record_session_floor(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = LaneRepo(tmp)
            transcript = clean_conductor_transcript(repo, "sess-norecord")
            read_call = hook_stdin("sess-norecord", transcript, "Read",
                                   {"file_path": "/x"})
            result = run_hook(repo.root, read_call)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)
            bash_call = hook_stdin("sess-norecord", transcript, "Bash",
                                   {"command": "git commit -m x"})
            result = run_hook(repo.root, bash_call)
            self.assertEqual(result.returncode, 2,
                             "a record-less session gets the read floor "
                             "only")


if __name__ == "__main__":
    unittest.main()
