"""W7 REDs — the role registry (design: docs/plans/handoff/w7-role-integrity-design.md §5).

Conductor-authored (Fable). The build lane makes these green WITHOUT editing
this file (packet: scratchpad/work/packet-w7-role-integrity-2026-07-16.md).

Seam pins (conductor decisions, binding on the builder):
- scripts/organization/role_gate.py exposes at module level:
    GateRefusal(Exception) with a non-empty str attribute `.reason`
    load_registry(repo_root) -> dict     (HEAD-blob resolution + full closure law;
                                          raises GateRefusal on any violation)
    resolve_principal(registry, actor_name) -> str
    validate_record(record, registry)    (raises GateRefusal; reason contains
                                          "author" for the author==reviewer law)
    reslot_chain_ok(repo_root) -> bool   (True iff every seats/actors divergence
                                          from the seed is covered by an attested
                                          reslot chain)
- scripts/organization/role_gate_hook.py exposes BASH_EFFECT_VERBS,
  PATH_EFFECT_VERBS, DISPATCH_EFFECT_VERBS (verb-name collections).

Working-tree vs HEAD decision: assertions against THIS repository read the
WORKING-TREE registry file (the builder can green them without committing);
the HEAD-blob resolution law is proven here via temp-repo mechanism tests and
re-checked against the real repository by the conductor's activation probes at
integration time (design §7).
"""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 — repo pattern (test_doc_authority)
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "contracts" / "role_registry.toml"
GATE_PATH = REPO_ROOT / "scripts" / "organization" / "role_gate.py"
HOOK_PATH = REPO_ROOT / "scripts" / "organization" / "role_gate_hook.py"
AGENTS_PATH = REPO_ROOT / "AGENTS.md"

VERBS = (
    "read", "run_demo", "audit_report",
    "design", "author_red", "author_admission", "register_home",
    "dispatch_lane", "gate_dispatch",
    "implement", "verify", "generate_receipts",
    "stage", "integrate", "commit", "tag", "ref_update", "worktree_admin",
    "push", "remote_publish",
    "persist_review", "record_summary", "review_verdict",
    "doc_law_edit", "enforcement_edit", "operator_reslot",
)

ROLE_AUTHORITY = {
    "conductor": [
        "read", "run_demo", "audit_report", "design", "author_red",
        "author_admission", "register_home", "dispatch_lane", "gate_dispatch",
        "verify", "generate_receipts", "stage", "integrate", "commit", "tag",
        "ref_update", "worktree_admin", "push", "remote_publish",
        "persist_review", "record_summary", "doc_law_edit",
        "enforcement_edit", "operator_reslot",
    ],
    "builder": ["read", "implement", "verify", "generate_receipts"],
    "reviewer": ["read", "review_verdict"],
    "auditor": ["read", "audit_report"],
    "demo_runner": ["read", "run_demo"],
}

CODEX_ARGV_BASE = ["exec", "--sandbox", "read-only", "--model", "gpt-5.6-sol",
                   "--json", "--strict-config", "--ignore-user-config"]
CODEX_PIN = ["--model", "gpt-5.6-sol", "--json", "--strict-config",
             "--ignore-user-config"]
EFFORT_ARGV = ["-c", "model_reasoning_effort=<effort>"]

SEED = {
    "contract_id": "RoleRegistry",
    "schema_version": 1,
    "purpose": "Roles and seats are DATA. No seat = no action; "
               "unknown anything = refuse.",
    "vocabulary": {"verbs": list(VERBS)},
    "actors": {
        "fable": {"kind": "claude-model", "model_id": "claude-fable-5"},
        "opus": {"kind": "claude-model", "model_id": "claude-opus-4-8"},
        "codex": {"kind": "codex-cli", "binary": "codex",
                  "model_id": "gpt-5.6-sol",
                  "argv_base": list(CODEX_ARGV_BASE),
                  "effort_argv": list(EFFORT_ARGV)},
    },
    "roles": {
        role: {
            "authority": list(auth),
            "forbidden": [v for v in VERBS if v not in auth],
        }
        for role, auth in ROLE_AUTHORITY.items()
    },
    "seats": {
        "conductor": "fable",
        "builder": "opus",
        "reviewer": "codex",
        "auditor": "opus",
        "demo_runner": "opus",
    },
}

AGENTS_MARKER = "seat occupants are data: contracts/role_registry.toml"


def _toml_value(value):
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(v) for v in value) + "]"
    raise TypeError(f"unsupported TOML value: {value!r}")


def emit_registry_toml(reg):
    """Emit the registry structure as TOML (known shape only)."""
    lines = []
    for key in ("contract_id", "schema_version", "purpose"):
        if key in reg:
            lines.append(f"{key} = {_toml_value(reg[key])}")
    extras = set(reg) - {"contract_id", "schema_version", "purpose",
                         "vocabulary", "actors", "roles", "seats"}
    for key in sorted(extras):
        lines.append(f"{key} = {_toml_value(reg[key])}")
    if "vocabulary" in reg:
        lines.append("")
        lines.append("[vocabulary]")
        for k, v in reg["vocabulary"].items():
            lines.append(f"{k} = {_toml_value(v)}")
    for actor, fields in reg.get("actors", {}).items():
        lines.append("")
        lines.append(f"[actors.{actor}]")
        for k, v in fields.items():
            lines.append(f"{k} = {_toml_value(v)}")
    for role, fields in reg.get("roles", {}).items():
        lines.append("")
        lines.append(f"[roles.{role}]")
        for k, v in fields.items():
            lines.append(f"{k} = {_toml_value(v)}")
    if "seats" in reg:
        lines.append("")
        lines.append("[seats]")
        for k, v in reg["seats"].items():
            lines.append(f"{k} = {_toml_value(v)}")
    return "\n".join(lines) + "\n"


def make_registry_repo(tmpdir, registry_text):
    """Init a temp git repo with the registry committed at the canonical path."""
    root = Path(tmpdir)
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    contracts = root / "contracts"
    contracts.mkdir(exist_ok=True)
    (contracts / "role_registry.toml").write_text(registry_text,
                                                  encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.email=red@test",
         "-c", "user.name=red", "commit", "-qm", "seed"],
        check=True,
    )
    return root


def load_gate_module():
    import importlib.util

    if not GATE_PATH.is_file():
        raise AssertionError(f"gate module missing: {GATE_PATH}")
    spec = importlib.util.spec_from_file_location("role_gate_under_test",
                                                  GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_hook_module():
    import importlib.util

    if not HOOK_PATH.is_file():
        raise AssertionError(f"hook module missing: {HOOK_PATH}")
    spec = importlib.util.spec_from_file_location("role_gate_hook_under_test",
                                                  HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_worktree_registry(test):
    test.assertTrue(REGISTRY_PATH.is_file(),
                    f"registry missing: {REGISTRY_PATH}")
    return tomllib.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def make_record(**overrides):
    """A plausible dispatched builder-lane assignment snapshot (design §2.4)."""
    record = {
        "record": "RoleAssignment", "schema_version": 1,
        "lane_run_id": "red-fixture-r6", "execution_kind": "build_lane",
        "role": "builder", "actor": "opus",
        "dispatched_by": "fable", "dispatch_ts": "2026-07-16T00:00:00Z",
        "base_sha": "0" * 40,
        "registry_sha256": "0" * 64,
        "dispatch_nonce": "f" * 32,
        "session_binding": {
            "session_ids": ["session-red-1"],
            "transcript_paths": ["/tmp/red-transcript.jsonl"],
            "worktree": ".claude/worktrees/red-fixture",
            "parent_session_id": "session-red-0",
        },
        "packet": {
            "design_sha256": "1" * 64,
            "design_verdict_ref": {"path": "dev/reports/reviews/red.md",
                                   "sha256": "2" * 64},
            "red_sha256": "3" * 64, "admission_sha256": "4" * 64,
            "allowed_paths": ["scripts/organization/example.py"],
        },
        "review_profile": {"round": 1, "required_effort": "max",
                           "operator_override_ref": None},
        "author_actor": "opus", "reviewer_actor": "codex",
        "standin": {"active": False, "standin_actor": None,
                    "retro_review_queued": False, "retro_review_ref": None},
        "status": "dispatched",
        "completion": {"output_patch_sha256": None,
                       "transcript_manifest_sha256": None},
        "review": {"reviewed_patch_sha256": None, "review_refs": []},
        "verification": {"verified_model_ids": [], "verified_at": None,
                         "verdict": None},
        "events": [{"ts": "2026-07-16T00:00:00Z", "to_status": "dispatched",
                    "prev_sha256": None}],
    }
    record.update(overrides)
    return record


class MutantMixin:
    def expect_refusal(self, mutate, label):
        gate = load_gate_module()
        reg = copy.deepcopy(SEED)
        mutate(reg)
        with tempfile.TemporaryDirectory() as tmp:
            root = make_registry_repo(tmp, emit_registry_toml(reg))
            with self.assertRaises(gate.GateRefusal, msg=label) as ctx:
                gate.load_registry(root)
            self.assertTrue(str(getattr(ctx.exception, "reason", "")).strip(),
                            f"{label}: refusal must carry a reason")


class R1RegistryExistsAndResolves(unittest.TestCase):
    def test_r1_working_tree_registry_parses_closed(self):
        reg = parse_worktree_registry(self)
        self.assertEqual(reg["contract_id"], "RoleRegistry")
        self.assertEqual(reg["schema_version"], 1)
        self.assertEqual(
            set(reg),
            {"contract_id", "schema_version", "purpose", "vocabulary",
             "actors", "roles", "seats"},
        )

    def test_r1_head_blob_resolution_mechanism(self):
        gate = load_gate_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = make_registry_repo(tmp, emit_registry_toml(SEED))
            loaded = gate.load_registry(root)
            self.assertEqual(loaded["seats"], SEED["seats"])
            self.assertEqual(loaded["vocabulary"]["verbs"], list(VERBS))

    def test_r1_working_tree_edit_confers_nothing(self):
        """Design §2.3: load_registry reads HEAD, never the working tree."""
        gate = load_gate_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = make_registry_repo(tmp, emit_registry_toml(SEED))
            mutated = copy.deepcopy(SEED)
            mutated["seats"]["builder"] = "fable"
            (root / "contracts" / "role_registry.toml").write_text(
                emit_registry_toml(mutated), encoding="utf-8")
            loaded = gate.load_registry(root)
            self.assertEqual(loaded["seats"]["builder"], "opus",
                             "working-tree edit must confer nothing")


class R2ClosedSchema(unittest.TestCase, MutantMixin):
    def test_r2_refusal_variants(self):
        def extra_top_key(reg):
            reg["extra_key"] = 1

        def missing_seats(reg):
            del reg["seats"]

        def unknown_role(reg):
            reg["roles"]["ghost"] = {"authority": ["read"],
                                     "forbidden": [v for v in VERBS
                                                   if v != "read"]}

        def missing_role(reg):
            del reg["roles"]["auditor"]
            del reg["seats"]["auditor"]

        def unknown_kind(reg):
            reg["actors"]["fable"]["kind"] = "mystery-model"

        def unknown_verb(reg):
            reg["roles"]["builder"]["authority"] = (
                reg["roles"]["builder"]["authority"] + ["levitate"])

        variants = [
            (extra_top_key, "unknown top-level key"),
            (missing_seats, "missing seats table"),
            (unknown_role, "role outside the closed five"),
            (missing_role, "missing role"),
            (unknown_kind, "actor kind outside the closed set"),
            (unknown_verb, "verb outside the vocabulary"),
        ]
        for mutate, label in variants:
            with self.subTest(label=label):
                self.expect_refusal(mutate, label)


class R3SeatsBijection(unittest.TestCase, MutantMixin):
    def test_r3_refusal_variants(self):
        def missing_seat(reg):
            del reg["seats"]["builder"]

        def extra_seat(reg):
            reg["seats"]["ghost"] = "opus"

        def array_seat(reg):
            reg["seats"]["builder"] = ["opus", "fable"]

        def undeclared_actor(reg):
            reg["seats"]["builder"] = "nobody"

        variants = [
            (missing_seat, "seat set smaller than role set"),
            (extra_seat, "seat key outside the role set"),
            (array_seat, "seat value is not a singleton string"),
            (undeclared_actor, "seat names an undeclared actor"),
        ]
        for mutate, label in variants:
            with self.subTest(label=label):
                self.expect_refusal(mutate, label)

    def test_r3_working_tree_seats_shape(self):
        reg = parse_worktree_registry(self)
        self.assertEqual(set(reg["seats"]), set(reg["roles"]))
        for seat, actor in reg["seats"].items():
            self.assertIsInstance(actor, str, seat)
            self.assertIn(actor, reg["actors"], seat)


class R4DispositionLaw(unittest.TestCase, MutantMixin):
    def test_r4_working_tree_dispositions_tile_vocabulary(self):
        reg = parse_worktree_registry(self)
        verbs = set(reg["vocabulary"]["verbs"])
        for role, fields in reg["roles"].items():
            authority = set(fields["authority"])
            forbidden = set(fields["forbidden"])
            self.assertEqual(authority | forbidden, verbs,
                             f"{role}: union must equal the vocabulary")
            self.assertEqual(authority & forbidden, set(),
                             f"{role}: overlap")

    def test_r4_refusal_variants(self):
        def granted_and_forbidden(reg):
            reg["roles"]["reviewer"]["authority"] = (
                reg["roles"]["reviewer"]["authority"] + ["commit"])

        def verb_in_neither(reg):
            reg["roles"]["conductor"]["authority"] = [
                v for v in reg["roles"]["conductor"]["authority"]
                if v != "commit"]

        variants = [
            (granted_and_forbidden, "verb carries two dispositions"),
            (verb_in_neither, "verb carries no disposition"),
        ]
        for mutate, label in variants:
            with self.subTest(label=label):
                self.expect_refusal(mutate, label)


class R5PrincipalUniqueness(unittest.TestCase, MutantMixin):
    def test_r5_duplicate_principal_refused(self):
        def duplicate_principal(reg):
            reg["actors"]["opus"]["model_id"] = "claude-fable-5"

        self.expect_refusal(duplicate_principal,
                            "two actors resolving to one principal")


class R6AuthorNeverApproves(unittest.TestCase):
    def test_r6_author_equals_reviewer_refused(self):
        gate = load_gate_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = make_registry_repo(tmp, emit_registry_toml(SEED))
            registry = gate.load_registry(root)
            record = make_record(author_actor="opus", reviewer_actor="opus")
            with self.assertRaises(gate.GateRefusal) as ctx:
                gate.validate_record(record, registry)
            self.assertIn("author", str(ctx.exception.reason))

    def test_r6_comparison_is_by_resolved_principal(self):
        """Two labels, one principal — must still refuse (design §2.2)."""
        gate = load_gate_module()
        reg = copy.deepcopy(SEED)
        reg["actors"]["opus_alias"] = {"kind": "claude-model",
                                       "model_id": "claude-opus-4-8"}
        with tempfile.TemporaryDirectory() as tmp:
            root = make_registry_repo(tmp, emit_registry_toml(reg))
            try:
                registry = gate.load_registry(root)
            except gate.GateRefusal:
                return  # refusing the duplicate-shaped actor set is lawful
            record = make_record(author_actor="opus",
                                 reviewer_actor="opus_alias")
            with self.assertRaises(gate.GateRefusal):
                gate.validate_record(record, registry)


class R7SeedEquality(unittest.TestCase):
    def test_r7_vocabulary_and_roles_equal_seed(self):
        reg = parse_worktree_registry(self)
        self.assertEqual(reg["vocabulary"]["verbs"], list(VERBS))
        self.assertEqual(reg["roles"], SEED["roles"])

    def test_r7_seats_and_actors_equal_seed_or_attested(self):
        reg = parse_worktree_registry(self)
        if reg["seats"] == SEED["seats"] and reg["actors"] == SEED["actors"]:
            return
        gate = load_gate_module()
        self.assertTrue(gate.reslot_chain_ok(REPO_ROOT),
                        "seats/actors diverge from the seed without an "
                        "attested reslot chain")


class R8CodexArgvPin(unittest.TestCase):
    def _argv_base(self):
        reg = parse_worktree_registry(self)
        codex = reg["actors"]["codex"]
        self.assertEqual(codex["kind"], "codex-cli")
        self.assertEqual(codex["binary"], "codex")
        self.assertEqual(codex["model_id"], "gpt-5.6-sol")
        return codex["argv_base"], codex["effort_argv"]

    def test_r8_exact_pin_present(self):
        argv_base, effort_argv = self._argv_base()
        self.assertEqual(argv_base[:3], ["exec", "--sandbox", "read-only"])
        joined = "\x1f".join(argv_base)
        self.assertIn("\x1f".join(CODEX_PIN), joined,
                      "the exact pin sequence must appear contiguously")
        self.assertEqual(effort_argv, EFFORT_ARGV)

    def test_v6_registry_pins_codex_argv(self):
        argv_base, _ = self._argv_base()
        model_index = argv_base.index("--model")
        self.assertEqual(argv_base[model_index + 1], "gpt-5.6-sol",
                         "argv_base must pin --model to the actor model_id")
        for token in ("--json", "--strict-config", "--ignore-user-config"):
            self.assertIn(token, argv_base)


class V4EffectTables(unittest.TestCase):
    def test_v4_verbs_tile_effect_tables(self):
        hook = load_hook_module()
        table_a = set(hook.BASH_EFFECT_VERBS)
        table_b = set(hook.PATH_EFFECT_VERBS)
        table_c = set(hook.DISPATCH_EFFECT_VERBS)
        for name, table in (("BASH_EFFECT_VERBS", table_a),
                            ("PATH_EFFECT_VERBS", table_b),
                            ("DISPATCH_EFFECT_VERBS", table_c)):
            self.assertTrue(table, f"{name} must not be empty")
        self.assertEqual(table_a | table_b | table_c, set(VERBS),
                         "the effect tables must cover the vocabulary "
                         "exactly — no orphan verb, no stray verb")
        self.assertLessEqual({"commit", "integrate", "push"}, table_a)
        self.assertLessEqual({"implement", "enforcement_edit"}, table_b)
        self.assertLessEqual({"read", "dispatch_lane"}, table_c)


class V8AgentsSeatAuthority(unittest.TestCase):
    def test_v8_agents_names_registry_as_seat_authority(self):
        text = AGENTS_PATH.read_text(encoding="utf-8")
        # Membership checked without assertIn so a failure never dumps the
        # document body into test output.
        self.assertTrue(AGENTS_MARKER in text,
                        "AGENTS.md must carry the seats-as-data marker "
                        "sentence (lands with the W7 integration commit)")


if __name__ == "__main__":
    unittest.main()
