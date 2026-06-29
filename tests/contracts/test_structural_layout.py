"""P5-0 ORG-AS-INVARIANT — the closed-cover structural-layout guard.

`contracts/repo_layout.json` `structural_layout` declares a HOME for every governed
file (which group / subdir it belongs to); this guard reddens on any undeclared OR
misplaced file. A closed cover: declared == actual parity (both drift directions) +
a negative control proving the guard CAN redden (no tautology).

This is the per-repo half of the kernel's organization invariant — the LAW (this test)
carries zero repo literals; the DATA (`repo_layout.json`) is the per-repo shape, so the
SAME guard governs any repo. It generalizes the WS1 scripts/tests layout contracts into
ONE target-shape over every surface, and is the RED a future "add a file" must satisfy
in the same slice it adds the file. Ported from
repo-surface-scout/tests/test_structural_layout.py. candidate_only; decides no authority.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path


def _repo_root() -> Path:
    """Walk up to the dir holding both scripts/ and tests/ (depth-independent)."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root not found")


REPO_ROOT = _repo_root()
_LAYOUT = json.loads((REPO_ROOT / "contracts" / "repo_layout.json").read_text(encoding="utf-8"))
_STRUCT = _LAYOUT["structural_layout"]
_ENUMERATED = ("source_layout", "test_layout")


def _actual_files(section: dict, *, root: Path | None = None) -> set[str]:
    """On-disk files under a section root, home-relative. A subpackage __init__.py marker
    (in a subdir, not the root) is a packaging artifact, not a declared module → skipped.
    `root` is injectable so the anti-tautology control proves this reads DISK."""
    root = root if root is not None else REPO_ROOT / section["root"]
    data_dirs = set(section.get("data_dirs", []))
    out: set[str] = set()
    for path in root.glob(section["glob"]):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if rel.parts and rel.parts[0] in data_dirs:
            continue
        if path.name == "__init__.py" and len(rel.parts) > 1:
            continue
        out.add(rel.as_posix())
    return out


def _declared_basenames(section: dict) -> set[str]:
    declared = set(section.get("root_allowlist", []))
    for group in section.get("groups", []):
        declared.update(group["members"])
    return declared


def _declared_homes(section: dict) -> set[str]:
    """Declared home PATH (section-root-relative) for every governed file: a root-allowlisted
    file keeps its basename; a group member lives at `<target_dir>/<member>` when
    placement_enforced, else flat. Home-aware so the same parity test governs before AND after
    a placement_enforced flip."""
    enforced = bool(section.get("placement_enforced", False))
    homes = set(section.get("root_allowlist", []))
    for group in section.get("groups", []):
        for member in group["members"]:
            homes.add(f"{group['target_dir']}/{member}" if enforced else member)
    return homes


class StructuralLayoutContract(unittest.TestCase):
    # --- closed-cover parity: every governed file has a declared home ---

    def test_every_src_module_has_a_declared_home(self):
        section = _STRUCT["source_layout"]
        self.assertEqual(
            _actual_files(section), _declared_homes(section),
            "scripts/ layout cover drifted — declare every module's home in "
            "contracts/repo_layout.json structural_layout.source_layout",
        )

    def test_every_test_file_has_a_declared_home(self):
        section = _STRUCT["test_layout"]
        self.assertEqual(
            _actual_files(section), _declared_homes(section),
            "tests/ layout cover drifted — declare every test's home in structural_layout.test_layout",
        )

    def test_every_contract_json_has_a_declared_home(self):
        section = _STRUCT["contracts_layout"]
        root = REPO_ROOT / section["root"]
        allow, group_dirs = set(section["root_allowlist"]), set(section["group_dirs"])
        undeclared: list[str] = []
        for path in root.glob(section["glob"]):
            if not path.is_file():
                continue
            rel = path.relative_to(root).parts
            if (len(rel) == 1 and rel[0] not in allow) or (len(rel) > 1 and rel[0] not in group_dirs):
                undeclared.append(path.relative_to(root).as_posix())
        self.assertEqual([], sorted(undeclared),
                         "contract JSON with no declared home — add to structural_layout.contracts_layout")

    # --- inverse drift: no phantom declarations ---

    def test_declared_homes_have_no_phantom_members(self):
        phantom: list[str] = []
        for name in _ENUMERATED:
            section = _STRUCT[name]
            root = REPO_ROOT / section["root"]
            for member in _declared_basenames(section):
                if not any((root / member).exists() or (root / g["target_dir"] / member).exists()
                           for g in [{"target_dir": "."}] + section.get("groups", [])):
                    phantom.append(f"{name}:{member}")
        self.assertEqual([], sorted(phantom), "declared homes reference files that do not exist on disk")

    # --- placement + no escape hatches ---

    def test_placement_enforced_groups_live_in_their_subdir(self):
        offenders: list[str] = []
        for name in _ENUMERATED:
            section = _STRUCT[name]
            root = REPO_ROOT / section["root"]
            enforced = section["placement_enforced"]
            for group in section.get("groups", []):
                for member in group["members"]:
                    home = root / group["target_dir"] / member if enforced else root / member
                    if not home.is_file():
                        offenders.append(f"{name}:{member}")
        self.assertEqual([], sorted(offenders), "placement drift — a member is not where its flag says")

    def test_no_group_dir_shadows_a_root_module(self):
        for name in _ENUMERATED:
            section = _STRUCT[name]
            root_stems = {Path(m).stem for m in section.get("root_allowlist", [])}
            for group in section.get("groups", []):
                self.assertNotIn(group["target_dir"], root_stems,
                                 f"{name}: group dir {group['target_dir']!r} shadows a root module")

    def test_no_flat_escape_hatch(self):
        for name in _ENUMERATED:
            tds = [g["target_dir"] for g in _STRUCT[name].get("groups", [])]
            self.assertTrue(all(td not in (".", "", None) for td in tds), f"{name}: a group target_dir is flat")
            self.assertEqual(len(tds), len(set(tds)), f"{name}: duplicate group target_dir")
        cd = _STRUCT["contracts_layout"]["group_dirs"]
        self.assertNotIn(".", cd)
        self.assertEqual(len(cd), len(set(cd)))

    # --- anti-tautology negative control: the cover CAN redden ---

    def test_guard_fires_on_a_forged_or_misplaced_file(self):
        import tempfile
        section = _STRUCT["source_layout"]
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "forged_actual.py").write_text("x = 1\n", encoding="utf-8")
            (tmp / "pkg").mkdir()
            (tmp / "pkg" / "__init__.py").write_text("", encoding="utf-8")
            self.assertEqual({"forged_actual.py"}, _actual_files(section, root=tmp),
                             "_actual_files must read real disk, not echo the manifest")
        actual, declared = _actual_files(section), _declared_homes(section)
        self.assertEqual(actual, declared, "the real cover must be green now")
        self.assertNotEqual(actual | {"a_forged_undeclared.py"}, declared, "an undeclared add must break parity")
        self.assertNotEqual(actual - {sorted(declared)[0]}, declared, "a vanished declared file must break parity")
        enf = {"placement_enforced": True, "root_allowlist": [], "groups": [{"target_dir": "rendering", "members": ["x.py"]}]}
        self.assertEqual({"rendering/x.py"}, _declared_homes(enf))
        self.assertEqual({"x.py"}, _declared_homes({**enf, "placement_enforced": False}))


if __name__ == "__main__":
    unittest.main()
