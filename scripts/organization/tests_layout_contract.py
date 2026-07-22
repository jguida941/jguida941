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
            "test_bootstrap_red_ref.py",
            "test_card_contracts.py",
            "test_data_semantics.py",
            "test_design_button.py",
            "test_design_card.py",
            "test_design_character.py",
            "test_design_chip.py",
            "test_design_conformance.py",
            "test_design_contract.py",
            "test_design_distinctness.py",
            "test_design_profiles_schema.py",
            "test_doc_authority.py",
            "test_dashboard_surface.py",
            "test_dashboard_visual_authority.py",
            "test_page_archetype.py",
            "test_dom_cover.py",
            "test_glass_preserved.py",
            "test_icon_system.py",
            "test_label_legibility.py",
            "test_page_shell.py",
            "test_page_manifest.py",
            "test_design_motion.py",
            "test_design_nav.py",
            "test_official_source_parity.py",
            "test_orchestration_exchange.py",
            "test_orchestration_exchange_adversarial.py",
            "test_rendered_fact_adversarial.py",
            "test_rendered_fact_density_adversarial.py",
            "test_rendered_fact_paint_adversarial.py",
            "test_rendered_facts.py",
            "test_public_data_privacy.py",
            "test_readme_projection.py",
            "test_reference_pack.py",
            "test_scripts_layout_contract.py",
            "test_settings_composition.py",
            "test_showcase_coverage.py",
            "test_skill_structure.py",
            "test_structural_layout.py",
            "test_studio.py",
            "test_tests_layout_contract.py",
            "test_theme_continuity.py",
            "test_theme_roster_authority.py",
            "test_theme_system.py",
            "test_tile_composition.py",
            "test_typography_restraint.py",
            "test_visual_receipt_provenance.py",
            "test_web_dashboard.py",
            "test_reference_capture.py",
            "test_reference_lane_contracts.py",
            "test_reference_probe_generic.py",
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
    "tokens": (
        "test_theme_roster_authority.py", # public web theme roster == active design-profile roster
        "test_theme_system.py",         # single token source: themes complete/legible/restrained
    ),
    "design_languages": (
        "test_design_character.py",     # P5: each theme positively EXPRESSES its language (proper style)
        "test_design_distinctness.py",  # P5: themes are DISTINCT design languages (anti-convergence)
    ),
    "skill": (
        "test_skill_structure.py",      # P5: the design-language-tdd skill structure (the repeatable engine)
    ),
    "data_semantics": (
        "test_data_semantics.py",       # P5-DATA: the computed metrics are honest (value+label match meaning)
    ),
    "design_profiles": (
        "test_design_profiles_schema.py",  # P5-PROFILE-SPINE: design profiles are DATA w/ a closed aspect cover
    ),
    "organization": (
        "test_doc_authority.py",        # T0: one plan-of-record + lifecycled/capped plan docs (fail-closed)
        "test_orchestration_exchange.py",  # A13/A14: single-conductor + exchange law parity vs AGENTS.md/ACTIVE.md/HANDOFF (fail-closed)
        "test_orchestration_exchange_adversarial.py",  # A13/A14 r9: frozen adversarial review-to-RED bank over the exchange-guard predicates (fail-closed)
    ),
    "reference_intake": (
        "test_reference_lane_contracts.py",   # W6-K: reference-capture lane record contracts (w3c-0 §8, R1-R8) + 31-id vocabulary
        "test_reference_probe_generic.py",    # W6-P: generic foreign-DOM rendered-facts probe — computed CSS + DOM + reachable states
        "test_reference_capture.py",          # W6-C: capture pipeline (acquire/localize/freeze/serve) + URL security boundary + BACKUP-BEFORE-TRANSFORM
    ),
    "webkit": (
        "test_design_button.py",        # P5-WEBKIT-BUTTON: profile-driven rendered components (anatomy hook)
        "test_design_card.py",          # P5-COMPONENTS-GROW: the CARD grouped-metric PATTERN (single-container, chrome-less rows)
        "test_design_chip.py",          # P5-COMPONENTS-GROW: the chip/tag (2nd component; reuses the runner + only-new predicate)
    ),
    "conformance": (
        "test_design_conformance.py",   # P5-CONFORM: the generic conform() runner (predicate dispatch + honest verdict split + receipt seam)
    ),
    "showcase": (
        "test_showcase_coverage.py",    # P5-SHOWCASE: the conformance receipts rendered — closed cover, drift-guarded, honest verdicts
    ),
    "settings": (
        "test_settings_composition.py", # P5-SETTINGS: the governed control plane — compose->conform->reject-invalid, ONE Python decider
    ),
    "receipts": (
        "test_visual_receipt_provenance.py",  # P5-RECEIPT-PROVENANCE: a receipt kind must name its real producer (no proxy wearing a pixel-truth label)
    ),
    "studio": (
        "test_studio.py",               # P5-STUDIO: the interactive design-system studio — archetype + governed swap (one Python decider) + drift-guarded page
    ),
    "page_chrome": (
        "test_dashboard_surface.py",     # W3: governed landing surface + closed prototype hydration
        "test_dom_cover.py",             # W2: exact emitter-owned static DOM cover + ratcheting index debt
        "test_design_nav.py",           # P5-BOARD B-1b: the governed nav component — per-language anatomy, every page connected
        "test_design_motion.py",        # P5-BOARD B-1: motion is DATA — cited duration/easing tokens, band law, token-only page motion
        "test_rendered_fact_adversarial.py",  # W4: negative controls for selector, geometry, and visible-content proof
        "test_rendered_fact_density_adversarial.py",  # W4: negative controls for content-density paint and clipping
        "test_rendered_fact_paint_adversarial.py",  # W4: negative controls for paint containment and contrast
        "test_rendered_facts.py",       # W4: post-hydration computed-style facts + rendered predicate dispatch
        "test_page_manifest.py",        # D-SHELL-2: every page declares intent + archetype + required regions (fail-closed, committed-bytes primary)
        "test_page_archetype.py",       # 2026-07-14 correction: per-language page composition DATA + anti-reskin structure
        "test_page_shell.py",           # P5-CHROME: the switchable governed page-shell — the site's own chrome is a rendered instance of a language (token-only + provenance + conform)
        "test_theme_continuity.py",      # W1: one persisted choice controls tokens + governed chrome anatomy on every page
    ),
    "reference_evidence": (
        "test_dashboard_visual_authority.py",  # W3 correction: visible dashboard choices require named authority
        "test_reference_pack.py",              # W3 correction: operator-approved evidence is frozen and hash-bound
    ),
    "official_source_evidence": (
        "test_official_source_parity.py",  # Mode A: profile literals equal pinned official code
    ),
    "cross_projection": (
        "test_web_dashboard.py",        # Law 3: web projection generated, token-parity, a11y
        "test_public_data_privacy.py",  # the public snapshot JSON leaks no token/credentials
    ),
    "layout": (
        "test_bootstrap_red_ref.py",
        "test_scripts_layout_contract.py",
        "test_structural_layout.py",
        "test_tests_layout_contract.py",
    ),
}


def design_contract_authority() -> dict[str, str]:
    """Map each design-contract filename to its governing authority."""
    return {mod: auth for auth, mods in DESIGN_CONTRACT_GROUPS.items() for mod in mods}
