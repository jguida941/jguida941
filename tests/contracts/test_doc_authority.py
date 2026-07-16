"""DocAuthorityPolicy (T0): ONE plan-of-record, lifecycled + capped plan docs.

Mirrors the constellation's single-plan law (doc_authority_policy.toml pattern:
closed vocab, completeness floor, fail-closed lifecycle). This module is the
slice-0 admission RED: it was observed failing on the pre-consolidation sprawl
(undeclared handoff docs + ACTIVE.md over its line cap) before the fold landed.
"""

import subprocess
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 (local): pinned backport in requirements.txt
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "contracts" / "doc_authority_policy.toml"
HANDOFF_DIR = ROOT / "docs" / "plans" / "handoff"
PLANS_DIR = ROOT / "docs" / "plans"

TOP_KEYS = {"contract_id", "schema_version", "purpose", "mode", "plan_of_record",
            "vocab", "zones", "limits", "completeness", "doc"}


def _policy() -> dict:
    return tomllib.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _handoff_files() -> list[str]:
    # Domain = TRACKED handoff docs (landing reconciliation 2026-07-16). An untracked,
    # in-flight design doc belongs to its own unlanded lane and enters this law when that
    # lane lands its file and lifecycle row together; the bijection is checked against what
    # git carries so the committed snapshot is self-consistent even while a busy worktree
    # holds other lanes' drafts.
    out = subprocess.run(
        ["git", "ls-files", "--", "docs/plans/handoff"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    return sorted(Path(line).name for line in out.splitlines() if line.endswith(".md"))


class DocAuthorityContract(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = _policy()

    def test_policy_shape_is_closed(self) -> None:
        self.assertEqual(self.policy["contract_id"], "DocAuthorityPolicy")
        self.assertEqual(self.policy["schema_version"], 1)
        unknown = set(self.policy) - TOP_KEYS
        self.assertEqual(unknown, set(), f"unknown top-level policy keys: {sorted(unknown)}")
        self.assertIn(self.policy["mode"]["mode"], ("audit", "block"))

    def test_required_docs_exist(self) -> None:
        missing = [d for d in self.policy["completeness"]["required_docs"]
                   if not (ROOT / d).is_file()]
        self.assertEqual(missing, [], f"required docs missing from disk: {missing}")

    def test_exactly_one_plan_of_record(self) -> None:
        por = self.policy["plan_of_record"]
        por_path = ROOT / por["path"]
        self.assertTrue(por_path.is_file(), f"plan-of-record missing: {por['path']}")
        text = por_path.read_text(encoding="utf-8").lower()
        self.assertTrue(
            any(p.lower() in text for p in por["identity_phrases"]),
            "plan-of-record does not carry any of its identity phrases",
        )
        offenders = []
        for md in PLANS_DIR.rglob("*.md"):
            if md.resolve() == por_path.resolve():
                continue
            body = md.read_text(encoding="utf-8").lower()
            for phrase in por["identity_phrases"]:
                if phrase.lower() in body:
                    offenders.append(f"{md.relative_to(ROOT)}: {phrase!r}")
        self.assertEqual(offenders, [], f"a SECOND doc claims plan-of-record identity: {offenders}")

    def test_plan_of_record_respects_line_cap(self) -> None:
        por = self.policy["plan_of_record"]
        lines = (ROOT / por["path"]).read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(
            len(lines), por["max_lines"],
            f"{por['path']} is {len(lines)} lines > cap {por['max_lines']} — fold history "
            f"into docs/history/PLAN-LEDGER.md instead of growing the active plan",
        )

    def test_plans_zone_contains_only_declared_entries(self) -> None:
        zone = self.policy["zones"]["docs/plans"]
        unexpected = []
        for entry in PLANS_DIR.iterdir():
            if entry.name.startswith("."):
                continue
            if entry.is_file() and entry.name not in zone["allowed_files"]:
                unexpected.append(entry.name)
            if entry.is_dir() and entry.name not in zone["allowed_dirs"]:
                unexpected.append(entry.name + "/")
        self.assertEqual(unexpected, [], f"undeclared entries in docs/plans: {unexpected}")

    def test_every_handoff_doc_has_exactly_one_lifecycle_row(self) -> None:
        rows = self.policy.get("doc", [])
        row_paths = [r.get("path", "") for r in rows]
        self.assertEqual(
            len(row_paths), len(set(row_paths)),
            f"duplicate [[doc]] rows: {sorted(p for p in row_paths if row_paths.count(p) > 1)}",
        )
        declared = {Path(p).name for p in row_paths
                    if Path(p).parent == Path("docs/plans/handoff")}
        on_disk = set(_handoff_files())
        undeclared = sorted(on_disk - declared)
        phantom = sorted(declared - on_disk)
        self.assertEqual(
            undeclared, [],
            f"handoff docs with NO lifecycle row (the sprawl fails closed): {undeclared}",
        )
        self.assertEqual(phantom, [], f"[[doc]] rows naming missing files: {phantom}")

    def test_lifecycle_rows_are_well_formed(self) -> None:
        vocab = self.policy["vocab"]
        problems = []
        for row in self.policy.get("doc", []):
            path, cls, status = row.get("path"), row.get("class"), row.get("status")
            if cls not in vocab["doc_classes"]:
                problems.append(f"{path}: class {cls!r} not in vocab")
            if status not in vocab["statuses"]:
                problems.append(f"{path}: status {status!r} not in vocab")
            if status in ("folded", "superseded"):
                succ = row.get("superseded_by", "")
                if not succ:
                    problems.append(f"{path}: {status} row missing superseded_by")
                elif not (ROOT / succ).is_file():
                    problems.append(f"{path}: superseded_by {succ!r} does not exist")
        self.assertEqual(problems, [], f"lifecycle rows malformed: {problems}")

    def test_live_handoff_docs_within_cap(self) -> None:
        cap = self.policy["limits"]["max_live_handoff_docs"]
        live = sorted(r["path"] for r in self.policy.get("doc", [])
                      if r.get("status") == "live")
        self.assertLessEqual(
            len(live), cap,
            f"{len(live)} live handoff docs > cap {cap}: fold or supersede — {live}",
        )


if __name__ == "__main__":
    unittest.main()
