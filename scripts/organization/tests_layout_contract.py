"""Semantic homes for the test suite.

The test files mirror the ``scripts/`` package layout: every ``test_*.py`` lives
in a group directory (``tests/<group>/``) named after the subsystem it exercises,
and that directory is a package (has ``__init__.py``) so ``unittest discover``
recurses into it. This is the test-suite analogue of
``scripts/organization/layout_contract.py``: the contract is explicit so the
guard test (``tests/contracts/test_tests_layout_contract.py``) can red-flag any
test file that drifts out of its declared home.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TestGroup:
    name: str
    meaning: str
    modules: tuple[str, ...]


# Each group mirrors a scripts/ package; modules are bare filenames living in
# tests/<group>/. Keep alphabetical within a group.
TEST_GROUPS: tuple[TestGroup, ...] = (
    TestGroup(
        "contracts",
        "executable design/output/layout contracts (the binding guards)",
        (
            "test_card_contracts.py",
            "test_design_contract.py",
            "test_glass_preserved.py",
            "test_icon_system.py",
            "test_label_legibility.py",
            "test_readme_projection.py",
            "test_scripts_layout_contract.py",
            "test_tests_layout_contract.py",
            "test_tile_composition.py",
            "test_typography_restraint.py",
        ),
    ),
    TestGroup(
        "rendering",
        "per-card SVG renderer behaviour",
        (
            "test_generate_contribution_panel.py",
            "test_generate_streak_summary.py",
        ),
    ),
    TestGroup(
        "pipeline",
        "data collection, model computation and pipeline orchestration",
        (
            "test_compute_metrics_accuracy.py",
            "test_compute_metrics_integration.py",
            "test_profile_pipeline_fixture.py",
        ),
    ),
    TestGroup(
        "github",
        "GitHub API facade, transports, settings and token fallback",
        (
            "test_actions_audit.py",
            "test_branch_protection.py",
            "test_github_client.py",
            "test_settings_tokens.py",
            "test_token_fallback.py",
        ),
    ),
    TestGroup(
        "quality",
        "validation, diagnostics, severity and triage",
        (
            "test_diagnostics.py",
            "test_metrics_svg.py",
            "test_severity.py",
            "test_triage.py",
        ),
    ),
    TestGroup(
        "core",
        "core runtime/env and the CLI entrypoint",
        (
            "test_profile_cli.py",
            "test_runtime_env.py",
        ),
    ),
)

# Directories under tests/ that are not test groups (data / caches).
NON_GROUP_DIRS: frozenset[str] = frozenset({"fixtures", "__pycache__"})


def group_dirs() -> tuple[str, ...]:
    return tuple(g.name for g in TEST_GROUPS)


def module_home() -> dict[str, str]:
    """Map each declared test filename to its group directory name."""
    return {module: g.name for g in TEST_GROUPS for module in g.modules}


def expected_relpath(module: str) -> str | None:
    home = module_home().get(module)
    return f"tests/{home}/{module}" if home else None


# --- Design contracts, grouped by GOVERNING AUTHORITY ------------------------
# The design-contract files all live FLAT in tests/contracts/ (declared above in
# the "contracts" group, which the home-guard enforces). This second axis groups
# them LOGICALLY by the design authority that governs each, so the suite stays
# organized by Apple-HIG / Power-BI / GitHub-SVG / tokens / cross-projection and a
# theme change is reasoned about one authority at a time. A guard
# (test_tests_layout_contract) asserts every design-contract file is declared in
# exactly one authority below and that each declared file exists.
DESIGN_CONTRACT_GROUPS: dict[str, tuple[str, ...]] = {
    "apple_hig": (
        "test_icon_system.py",
        "test_tile_composition.py",
        "test_typography_restraint.py",
        "test_glass_preserved.py",
    ),
    "powerbi_ia": (
        "test_design_contract.py",       # hierarchy / one-dominant-KPI / per-card cards
        "test_label_legibility.py",      # one metric per tile / no clipped labels
    ),
    "github_svg": (
        "test_card_contracts.py",       # per-SVG safety / title / viewBox / camo bans
        "test_readme_projection.py",    # assembled README: uniform <img> sizing policy
    ),
    "layout": (
        "test_scripts_layout_contract.py",
        "test_tests_layout_contract.py",
    ),
}


def design_contract_authority() -> dict[str, str]:
    """Map each design-contract filename to its governing authority."""
    return {mod: auth for auth, mods in DESIGN_CONTRACT_GROUPS.items() for mod in mods}
