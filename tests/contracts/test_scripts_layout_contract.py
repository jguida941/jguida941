from pathlib import Path
import unittest

from scripts.organization.layout_audit import audit_scripts_layout
from scripts.organization.layout_contract import (
    MODULE_HOMES,
    ROOT_ENTRYPOINT_SHIMS,
    allowed_python_paths,
    import_rewrite_map,
)
from scripts.organization.migrate_scripts_layout import planned_moves


ROOT = Path(__file__).resolve().parents[1]


class ScriptsLayoutContractTests(unittest.TestCase):
    def test_every_declared_module_has_one_source_and_target(self):
        sources = [home.source_path for home in MODULE_HOMES]
        targets = [home.target_path for home in MODULE_HOMES]

        self.assertEqual(len(sources), len(set(sources)))
        self.assertEqual(len(targets), len(set(targets)))

    def test_live_scripts_tree_matches_semantic_contract(self):
        findings = audit_scripts_layout(ROOT)

        self.assertEqual([], [f"{finding.finding_id}: {finding.detail}" for finding in findings])

    def test_migration_plan_is_empty_after_contract_is_satisfied(self):
        moves = planned_moves(ROOT)

        self.assertEqual([], [f"{src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}" for src, dst in moves])

    def test_root_python_files_are_only_declared_entrypoint_shims(self):
        root_python_files = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "scripts").glob("*.py")
            if path.name != "__init__.py"
        }

        self.assertEqual(ROOT_ENTRYPOINT_SHIMS, root_python_files)

    def test_root_entrypoint_shims_stay_lightweight(self):
        for shim in sorted(ROOT_ENTRYPOINT_SHIMS):
            text = (ROOT / shim).read_text(encoding="utf-8")

            self.assertLessEqual(len(text.splitlines()), 30, f"{shim} should stay a wrapper")
            self.assertIn("from scripts.", text)

    def test_import_rewrite_map_has_no_ambiguous_targets(self):
        rewrites = import_rewrite_map()

        self.assertEqual(len(rewrites.values()), len(set(rewrites.values())))
        for target in rewrites.values():
            target_path = target.replace(".", "/") + ".py"
            package_init = target.replace(".", "/") + "/__init__.py"
            self.assertTrue(
                target_path in allowed_python_paths() or package_init in allowed_python_paths(),
                f"{target} must point at a declared semantic path",
            )


if __name__ == "__main__":
    unittest.main()
