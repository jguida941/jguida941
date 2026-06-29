"""Semantic homes for the profile build scripts package.

The contract is intentionally explicit: every Python module under ``scripts/``
must have one declared home, and the migration tool may only move modules that
appear here.

This contract describes the *current* nested layout of this repository
(``scripts/analytics``, ``scripts/render``, ``scripts/diagnostics`` …) and the
canonical packages it should be reorganised into
(``scripts/core``, ``scripts/contracts``, ``scripts/github``,
``scripts/pipeline``, ``scripts/rendering``, ``scripts/quality``,
``scripts/cli``).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleHome:
    source_path: str
    target_path: str
    semantic_group: str
    meaning: str
    public_entrypoint: bool = False

    @property
    def source_module(self) -> str:
        return _module_name(self.source_path)

    @property
    def target_module(self) -> str:
        return _module_name(self.target_path)


def _module_name(path: str) -> str:
    if not path.endswith(".py"):
        raise ValueError(f"Python module path expected, got {path!r}")
    stem = path[:-3]
    if stem.endswith("/__init__"):
        stem = stem[: -len("/__init__")]
    return stem.replace("/", ".")


MODULE_HOMES: tuple[ModuleHome, ...] = (
    # --- core: shared configuration and runtime --------------------------------
    ModuleHome("scripts/config.py", "scripts/core/config.py", "core", "theme and shared constants"),
    ModuleHome("scripts/settings.py", "scripts/core/settings.py", "core", "GitHub API settings"),
    ModuleHome("scripts/runtime_env.py", "scripts/core/runtime_env.py", "core", "runtime environment parsing"),
    # --- contracts: profile data and metric definitions ------------------------
    ModuleHome("scripts/contracts/schema.py", "scripts/contracts/__init__.py", "contracts", "profile data and README contracts"),
    ModuleHome("scripts/contracts/metrics.py", "scripts/contracts/profile_contract.py", "contracts", "metric definitions and formatting rules"),
    # --- github: API facade, transports and repo auditing ----------------------
    ModuleHome("scripts/github/client.py", "scripts/github/github_client.py", "github", "GitHub API facade"),
    ModuleHome("scripts/github/transport.py", "scripts/github/github_transport.py", "github", "GitHub HTTP transport"),
    ModuleHome("scripts/github/graphql.py", "scripts/github/github_graphql.py", "github", "GitHub GraphQL transport"),
    ModuleHome("scripts/github/cache.py", "scripts/github/github_cache.py", "github", "GitHub API response cache"),
    ModuleHome("scripts/github/gh_cli.py", "scripts/github/gh_cli.py", "github", "GitHub CLI JSON wrapper"),
    ModuleHome("scripts/diagnostics/actions_audit.py", "scripts/github/actions_audit.py", "github", "GitHub Actions run auditing"),
    ModuleHome("scripts/diagnostics/branch_protection.py", "scripts/github/branch_protection.py", "github", "branch protection auditing and updates"),
    # --- pipeline: data collection, modelling and output orchestration ---------
    ModuleHome("scripts/analytics/collect.py", "scripts/pipeline/collect_data.py", "pipeline", "GitHub data collection"),
    ModuleHome("scripts/analytics/model.py", "scripts/pipeline/compute_metrics.py", "pipeline", "profile model computation"),
    ModuleHome("scripts/analytics/helpers.py", "scripts/pipeline/profile_helpers.py", "pipeline", "profile pipeline helpers"),
    ModuleHome("scripts/profile_pipeline.py", "scripts/pipeline/profile_pipeline.py", "pipeline", "profile pipeline orchestration"),
    ModuleHome("scripts/render/outputs.py", "scripts/pipeline/render_outputs.py", "pipeline", "output rendering orchestration"),
    ModuleHome("scripts/pipeline/web_render.py", "scripts/pipeline/web_render.py", "pipeline", "web dashboard generator (token-driven, themed)"),
    # --- rendering: SVG theme helpers and card renderers -----------------------
    ModuleHome("scripts/render/card_theme.py", "scripts/rendering/card_theme.py", "rendering", "SVG card theme helpers"),
    ModuleHome("scripts/render/svg_utils.py", "scripts/rendering/svg_utils.py", "rendering", "SVG formatting utilities"),
    ModuleHome("scripts/render/glass_kit.py", "scripts/rendering/glass_kit.py", "rendering", "glass UI kit helpers"),
    ModuleHome("scripts/rendering/icons.py", "scripts/rendering/icons.py", "rendering", "vendored Lucide icon set"),
    ModuleHome("scripts/rendering/design_tokens.py", "scripts/rendering/design_tokens.py", "rendering", "single design-token source + themes (SVG values + web CSS)"),
    ModuleHome("scripts/rendering/components.py", "scripts/rendering/components.py", "rendering", "reusable token-driven SVG components"),
    ModuleHome("scripts/render/cards/generate_activity_heatmap.py", "scripts/rendering/generate_activity_heatmap.py", "rendering", "activity heatmap renderer"),
    ModuleHome("scripts/render/cards/generate_badges.py", "scripts/rendering/generate_badges.py", "rendering", "badge renderer"),
    ModuleHome("scripts/render/cards/generate_builder_scorecard.py", "scripts/rendering/generate_builder_scorecard.py", "rendering", "builder scorecard renderer"),
    ModuleHome("scripts/render/cards/generate_contribution_panel.py", "scripts/rendering/generate_contribution_panel.py", "rendering", "contribution panel renderer"),
    ModuleHome("scripts/render/cards/generate_currently_working.py", "scripts/rendering/generate_currently_working.py", "rendering", "currently working renderer"),
    ModuleHome("scripts/render/cards/generate_engineering_cadence.py", "scripts/rendering/generate_engineering_cadence.py", "rendering", "engineering cadence renderer"),
    ModuleHome("scripts/render/cards/generate_focus_board.py", "scripts/rendering/generate_focus_board.py", "rendering", "focus board renderer"),
    ModuleHome("scripts/render/cards/generate_language_chart.py", "scripts/rendering/generate_language_chart.py", "rendering", "language chart renderer"),
    ModuleHome("scripts/render/cards/generate_metrics_general.py", "scripts/rendering/generate_metrics_general.py", "rendering", "general metrics renderer"),
    ModuleHome("scripts/render/cards/generate_repo_spotlight.py", "scripts/rendering/generate_repo_spotlight.py", "rendering", "repo spotlight renderer"),
    ModuleHome("scripts/render/cards/generate_snapshot_panel.py", "scripts/rendering/generate_snapshot_panel.py", "rendering", "snapshot panel renderer"),
    ModuleHome("scripts/render/cards/generate_streak_summary.py", "scripts/rendering/generate_streak_summary.py", "rendering", "streak summary renderer"),
    # --- quality: validation, diagnostics and triage ---------------------------
    ModuleHome("scripts/render/metrics_svg.py", "scripts/quality/metrics_svg.py", "quality", "metrics SVG parser and checks"),
    ModuleHome("scripts/render/validate.py", "scripts/quality/validate_generated_profile.py", "quality", "generated profile validator", public_entrypoint=True),
    ModuleHome("scripts/diagnostics/diagnostics.py", "scripts/quality/diagnostics.py", "quality", "runtime diagnostics"),
    ModuleHome("scripts/diagnostics/severity.py", "scripts/quality/severity.py", "quality", "severity comparisons"),
    ModuleHome("scripts/diagnostics/triage.py", "scripts/quality/triage.py", "quality", "profile health triage"),
    # --- cli: command-line entrypoint ------------------------------------------
    ModuleHome("scripts/profile_cli.py", "scripts/cli/profile_cli.py", "cli", "profile command-line interface", public_entrypoint=True),
    # --- organization: layout tooling (self-declared) --------------------------
    ModuleHome("scripts/organization/layout_audit.py", "scripts/organization/layout_audit.py", "organization", "live scripts layout audit"),
    ModuleHome("scripts/organization/layout_contract.py", "scripts/organization/layout_contract.py", "organization", "semantic scripts layout contract"),
    ModuleHome("scripts/organization/migrate_scripts_layout.py", "scripts/organization/migrate_scripts_layout.py", "organization", "semantic scripts layout migration tool"),
    ModuleHome("scripts/organization/tests_layout_contract.py", "scripts/organization/tests_layout_contract.py", "organization", "semantic test-suite layout contract"),
)

ROOT_ENTRYPOINT_SHIMS: frozenset[str] = frozenset(
    {
        "scripts/build_readme.py",
        "scripts/profile_cli.py",
        "scripts/validate_generated_profile.py",
    }
)

PACKAGE_INIT_PATHS: frozenset[str] = frozenset(
    {
        "scripts/__init__.py",
        "scripts/cli/__init__.py",
        "scripts/contracts/__init__.py",
        "scripts/core/__init__.py",
        "scripts/github/__init__.py",
        "scripts/organization/__init__.py",
        "scripts/pipeline/__init__.py",
        "scripts/quality/__init__.py",
        "scripts/rendering/__init__.py",
    }
)


def module_homes_by_source() -> dict[str, ModuleHome]:
    return {home.source_path: home for home in MODULE_HOMES}


def module_homes_by_target() -> dict[str, ModuleHome]:
    return {home.target_path: home for home in MODULE_HOMES}


def import_rewrite_map() -> dict[str, str]:
    return {
        home.source_module: home.target_module
        for home in MODULE_HOMES
        if home.source_module != home.target_module
    }


def allowed_python_paths() -> set[str]:
    return set(PACKAGE_INIT_PATHS) | ROOT_ENTRYPOINT_SHIMS | set(module_homes_by_target())
