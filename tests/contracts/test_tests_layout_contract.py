"""Self-enforcing guard: every test lives in its declared semantic home.

Red-first analogue of ``tests/.../test_scripts_layout_contract.py`` but for the
test suite itself: the contract in
``scripts/organization/tests_layout_contract.py`` declares which group directory
each ``test_*.py`` belongs to, and this guard reddens if any test file drifts out
of its home, sits loose at ``tests/`` root, or a group dir stops being a package.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.organization.tests_layout_contract import (
    DESIGN_CONTRACT_GROUPS,
    NON_GROUP_DIRS,
    TEST_GROUPS,
    design_contract_authority,
    group_dirs,
    module_home,
)


def _repo_root() -> Path:
    """Walk up to the directory that holds both ``scripts`` and ``tests`` so this
    guard works regardless of how deep it is nested (no parent-counting trap)."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
TESTS = ROOT / "tests"


class TestsLayoutContract(unittest.TestCase):
    def _discovered(self) -> list[Path]:
        return [p for p in TESTS.rglob("test_*.py") if "__pycache__" not in p.parts]

    def test_every_test_file_in_declared_home(self):
        homes = module_home()
        offenders: list[str] = []
        for path in self._discovered():
            rel = path.relative_to(TESTS)
            if len(rel.parts) != 2:
                offenders.append(f"not in a group dir: tests/{rel.as_posix()}")
                continue
            group, fname = rel.parts
            declared = homes.get(fname)
            if declared is None:
                offenders.append(f"undeclared test module: {fname}")
            elif declared != group:
                offenders.append(f"{fname} in tests/{group} but declared home is tests/{declared}")
        self.assertEqual(
            [], offenders, "tests must live in their declared home:\n  " + "\n  ".join(offenders)
        )

    def test_no_test_files_at_tests_root(self):
        stray = sorted(p.name for p in TESTS.glob("test_*.py"))
        self.assertEqual([], stray, f"test files belong in a group dir, not tests/ root: {stray}")

    def test_declared_modules_exist(self):
        homes = module_home()
        missing = [
            f"tests/{group}/{fname}"
            for fname, group in homes.items()
            if not (TESTS / group / fname).is_file()
        ]
        self.assertEqual([], missing, f"declared test modules missing: {missing}")

    def test_group_dirs_are_packages(self):
        missing = [g for g in group_dirs() if not (TESTS / g / "__init__.py").is_file()]
        self.assertEqual([], missing, f"group dirs must be packages (need __init__.py): {missing}")

    def test_no_unexpected_dirs_at_tests_root(self):
        allowed = set(group_dirs()) | set(NON_GROUP_DIRS)
        unexpected = sorted(
            p.name for p in TESTS.iterdir() if p.is_dir() and p.name not in allowed
        )
        self.assertEqual([], unexpected, f"unexpected dirs under tests/: {unexpected}")

    def test_design_contracts_grouped_by_authority(self):
        """Every contracts-group test file is assigned to exactly one governing
        authority in DESIGN_CONTRACT_GROUPS, and each declared file exists — so the
        design contracts stay organized (and a new one can't drift in undeclared)."""
        contracts_files = set(dict(((g.name, g.modules) for g in TEST_GROUPS))["contracts"])
        authority = design_contract_authority()
        # in sync: the authority axis covers exactly the contracts-group files
        self.assertEqual(
            contracts_files,
            set(authority),
            "DESIGN_CONTRACT_GROUPS must cover exactly the contracts-group files "
            f"(missing: {sorted(contracts_files - set(authority))}; "
            f"stale: {sorted(set(authority) - contracts_files)})",
        )
        # no file declared under two authorities
        seen, dupes = set(), []
        for mods in DESIGN_CONTRACT_GROUPS.values():
            for m in mods:
                (dupes.append(m) if m in seen else seen.add(m))
        self.assertEqual([], dupes, f"design-contract files declared under >1 authority: {dupes}")
        # every declared file exists
        missing = [m for m in authority if not (TESTS / "contracts" / m).is_file()]
        self.assertEqual([], missing, f"declared design-contract files missing: {missing}")


if __name__ == "__main__":
    unittest.main()
