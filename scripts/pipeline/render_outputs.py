"""Render SVG assets, dashboard JSON, and README."""

from __future__ import annotations

import json
from pathlib import Path
import re

import jinja2

from scripts.contracts import (
    PROFILE_ARTIFACT_MANIFEST_PATH,
    build_artifact_manifest,
    public_generation_record,
)
from scripts.contracts.profile_contract import metric_claim
from scripts.pipeline.collect_data import CollectedProfileData
from scripts.pipeline.profile_helpers import (
    contains_credential_material as _contains_credential_material,
)
from scripts.rendering.generate_activity_heatmap import generate as gen_heatmap
from scripts.rendering.generate_badges import generate as gen_badges
from scripts.rendering.generate_builder_scorecard import generate as gen_scorecard
from scripts.rendering.generate_contribution_panel import generate as gen_contribution_panel
from scripts.rendering.generate_currently_working import generate as gen_working
from scripts.rendering.generate_engineering_cadence import generate as gen_cadence
from scripts.rendering.generate_focus_board import generate as gen_focus_board
from scripts.rendering.generate_language_chart import generate as gen_lang_chart
from scripts.rendering.generate_metrics_general import generate as gen_metrics_general
from scripts.rendering.generate_repo_spotlight import generate as gen_spotlight
from scripts.rendering.generate_snapshot_panel import generate as gen_snapshot_panel
from scripts.rendering.generate_streak_summary import generate as gen_streak_summary


_CREDENTIAL_FIELD_NAMES = frozenset(
    {
        "access_key",
        "access_token",
        "api_key",
        "api_secret",
        "api_token",
        "auth_mode",
        "authenticated",
        "authentication_mode",
        "authorization",
        "aws_secret_access_key",
        "client_secret",
        "credential",
        "credentials",
        "deploy_key",
        "deploy_token",
        "github_token",
        "id_token",
        "oauth_token",
        "password",
        "passwd",
        "personal_github_token",
        "private_key",
        "proxy_authorization",
        "refresh_token",
        "secret",
        "secret_access_key",
        "secret_key",
        "secrets",
        "ssh_key",
        "token",
        "token_mode",
        "tokens",
        "webhook_secret",
    }
)
_SOURCE_CONTENT_FIELD_NAMES = frozenset(
    {
        "blob_content",
        "code",
        "content",
        "contents",
        "diff",
        "file_body",
        "file_content",
        "file_contents",
        "file_patch",
        "patch",
        "raw_content",
        "raw_source",
        "source",
        "source_code",
        "source_content",
        "source_contents",
        "source_text",
    }
)


def _normalized_public_key(key: str) -> str:
    camel_split = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key)
    return re.sub(r"[^a-z0-9]+", "_", camel_split.casefold()).strip("_")


def _is_prohibited_public_key(key: str) -> bool:
    normalized = _normalized_public_key(key)
    aliases = {normalized}
    for suffix in ("_value", "_text", "_field"):
        if normalized.endswith(suffix):
            aliases.add(normalized[: -len(suffix)])
    if aliases & (_CREDENTIAL_FIELD_NAMES | _SOURCE_CONTENT_FIELD_NAMES):
        return True

    # Catch ordinary API field spellings without treating hyphenated repository
    # names such as ``token-service`` or ``secret-api`` as credentials.
    field_spelling = "_" in key or bool(re.search(r"(?<=[a-z0-9])(?=[A-Z])", key))
    if field_spelling and any(
        alias.endswith(
            ("_credential", "_credentials", "_password", "_secret", "_token")
        )
        for alias in aliases
    ):
        return True
    return _contains_credential_material(key)


def ensure_output_dirs() -> None:
    Path("assets").mkdir(exist_ok=True)
    Path("site/data").mkdir(parents=True, exist_ok=True)


def _primary_language(model: dict) -> str:
    """The dominant language NAME (e.g. 'Python') from the shared snapshot, or ''.

    Null-safe: a missing/None name or a non-list top_languages yields '' (never the
    literal 'None' or a crash), so the tile falls back to its generic noun.
    """
    langs = model.get("top_languages")
    if isinstance(langs, list) and langs and isinstance(langs[0], dict):
        return str(langs[0].get("name") or "").strip()
    return ""


def _ci_coverage_claim(model: dict) -> dict:
    """The one CI-coverage claim every card repeats: value, scope, and status.

    Both cards receive this claim instead of recomputing a percentage from their
    own denominator, so the JSON value and both visible gauges cannot diverge.
    """
    data_scope = model.get("data_scope") or {}
    data_quality = model.get("data_quality") or {}
    scopes = data_scope.get("metric_scopes") or {}
    statuses = data_quality.get("metric_statuses") or {}
    return metric_claim(
        "ci_coverage_pct",
        value=(model.get("scorecard") or {}).get("ci_coverage_pct"),
        scope=scopes.get("ci_coverage_pct"),
        status=statuses.get("ci_coverage_pct"),
    )


def generate_assets(
    collected: CollectedProfileData,
    model: dict,
    logger=print,
    *,
    generation: dict | None = None,
) -> None:
    logger("\n[8/8] Generating SVGs...")
    primary_language = _primary_language(model)
    ci_claim = _ci_coverage_claim(model)
    # Rendered provenance follows the run's bound source kind, so a fixture card
    # cannot present its values as a live provider observation.
    source_kind = str((generation or {}).get("source_kind") or "github-api")

    gen_badges(
        public_nonfork_repos=collected.repo_counts["public_owned_nonfork"],
        public_forks=collected.repo_counts["public_owned_forks"],
        private_owned_repos=collected.repo_counts["private_owned"],
        ci_count=model["snapshot"]["ci_repos"],
        last_year_contributions=collected.total_contributions,
    )
    logger("  -> assets/badges.svg")

    gen_lang_chart(
        model.get("language_bytes", collected.language_bytes),
        data_quality=model.get("data_quality"),
    )
    logger("  -> assets/lang_breakdown.svg")

    gen_working(model["recent_repos"])
    logger("  -> assets/currently_working.svg")

    gen_heatmap(collected.events)
    logger("  -> assets/activity_heatmap.svg")

    gen_contribution_panel(collected.calendar)
    logger("  -> assets/contribution_calendar.svg")

    gen_spotlight(model["spotlight_data"])
    logger("  -> assets/repo_spotlight.svg")

    gen_scorecard(
        model["scorecard"],
        tiles=model["scorecard_cards"],
        primary_language=primary_language,
        data_quality=model.get("data_quality"),
        ci_claim=ci_claim,
        source_kind=source_kind,
    )
    logger("  -> assets/builder_scorecard.svg")

    gen_cadence(
        model["engineering"],
        primary_language=primary_language,
        data_quality=model.get("data_quality"),
        ci_claim=ci_claim,
    )
    logger("  -> assets/engineering_cadence.svg")

    gen_focus_board(model["focus"])
    logger("  -> assets/now_next_shipped.svg")

    gen_streak_summary(
        calendar=collected.calendar,
        current_streak_days=model["snapshot"]["streak_days"],
        total_contributions=collected.total_contributions,
    )
    logger("  -> assets/streak_summary.svg")

    gen_snapshot_panel(
        model["snapshot_rows"],
        model["data_quality"],
        data_scope=model["data_scope"],
    )
    logger("  -> assets/raw_snapshot.svg")

    gen_metrics_general(
        username=model["dashboard_data"]["username"],
        snapshot=model["snapshot"],
        data_scope=model["data_scope"],
        data_quality=model.get("data_quality"),
        generated_at=model["dashboard_data"]["generated_at"],
        output_path="metrics.general.svg",
    )
    logger("  -> metrics.general.svg")


def _public_dashboard_data(dashboard_data: dict) -> dict:
    """Return the publishable projection without erasing repository metadata.

    Private/public classification is useful profile data, so private-marked rows stay
    in place. Credential fields, source/file bodies, internal authentication posture,
    and concrete credential-shaped string values are removed at any depth.
    """
    if type(dashboard_data) is not dict:
        raise TypeError("public dashboard data must be a mapping")

    max_depth = 32
    max_containers = 50_000
    containers_seen = 0
    drop = object()

    def project(value: object, depth: int = 0) -> object:
        nonlocal containers_seen
        if depth > max_depth:
            raise ValueError("public dashboard data exceeds the projection depth limit")
        if type(value) is dict:
            containers_seen += 1
            if containers_seen > max_containers:
                raise ValueError("public dashboard data exceeds the projection size limit")
            projected_mapping = {}
            for key, item in value.items():
                if type(key) is not str:
                    raise ValueError("public dashboard data contains a non-string mapping key")
                if _is_prohibited_public_key(key):
                    continue
                projected_item = project(item, depth + 1)
                if projected_item is not drop:
                    projected_mapping[key] = projected_item
            return projected_mapping
        if type(value) is list:
            containers_seen += 1
            if containers_seen > max_containers:
                raise ValueError("public dashboard data exceeds the projection size limit")
            projected_list = []
            for item in value:
                projected_item = project(item, depth + 1)
                if projected_item is not drop:
                    projected_list.append(projected_item)
            return projected_list
        if type(value) is str and _contains_credential_material(value):
            return drop
        return value

    projected = project(dashboard_data)
    if type(projected) is not dict:
        raise ValueError("public dashboard projection did not produce a mapping")
    return projected


def write_dashboard_json(model: dict, logger=print, *, generation: dict | None = None) -> None:
    output_path = Path("site/data/profile_snapshot.json")
    payload = _public_dashboard_data(model["dashboard_data"])
    if generation is not None:
        payload["generation"] = public_generation_record(generation)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    logger("  -> site/data/profile_snapshot.json")


def write_artifact_manifest(generation: dict, logger=print) -> Path:
    """Seal the exact bytes of every canonical payload this run wrote.

    The manifest is external to the payloads it hashes, so the snapshot JSON's
    own serialized bytes are bound without any self-reference.
    """
    manifest = build_artifact_manifest(generation)
    output_path = Path(PROFILE_ARTIFACT_MANIFEST_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    logger(f"  -> {PROFILE_ARTIFACT_MANIFEST_PATH}")
    return output_path


# The README states where its numbers came from. Fixture output is a legitimate
# local development surface, but it is never a live GitHub observation.
_GENERATION_PROVENANCE = {
    "github-api": "from GitHub repository metadata.",
    "fixture": (
        "from local fixture data. This is a fixture run, not a live GitHub observation."
    ),
}


def render_readme(model: dict, logger=print, *, generation: dict | None = None) -> None:
    logger("\nRendering README.md...")

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("templates"),
        keep_trailing_newline=True,
    )
    template = env.get_template("README.md.tpl")

    source_kind = str((generation or {}).get("source_kind") or "github-api")
    # The cache-bust key is the pre-render identity, so a rerun that changes no
    # render input serves the same bytes from the same URL.
    cache_bust = str((generation or {}).get("render_key") or "")
    if not cache_bust:
        cache_bust = str(model["dashboard_data"].get("generated_at", "")).replace("-", "").replace(":", "").replace("T", "").replace("Z", "")
    if not cache_bust:
        cache_bust = "latest"

    def _dedupe_links(items: list[dict], limit: int = 3) -> list[dict]:
        unique = []
        seen = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url", "")).strip()
            title = str(item.get("title", "")).strip()
            detail = str(item.get("detail", "")).strip()
            key = url or f"{title}|{detail}"
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(item)
            if len(unique) >= limit:
                break
        return unique

    featured_links = [row for row in model["repo_overview_rows"] if row.get("featured")][:6]

    readme = template.render(
        username=model["dashboard_data"]["username"],
        dashboard_url=model["dashboard_data"]["dashboard_url"],
        cache_bust=cache_bust,
        generation_provenance=_GENERATION_PROVENANCE.get(
            source_kind, _GENERATION_PROVENANCE["github-api"]
        ),
        recent_created=model["recent_created"],
        focus_now=model["focus"]["now"],
        focus_next=model["focus"]["next"],
        focus_shipped=model["focus"]["shipped"],
        focus_links_now=_dedupe_links(model["focus"]["now"], 3),
        focus_links_next=_dedupe_links(model["focus"]["next"], 3),
        focus_links_shipped=_dedupe_links(model["focus"]["shipped"], 3),
        featured_links=featured_links,
        recent_releases=model["recent_releases"],
        recent_pull_requests=model["recent_pull_requests"],
        snapshot=model["snapshot"],
        snapshot_rows=model["snapshot_rows"],
        data_quality=model["data_quality"],
        scorecard=model["scorecard"],
        scorecard_cards=model["scorecard_cards"],
        data_scope=model["data_scope"],
        top_languages=model["top_languages"],
        repo_overview_rows=model["repo_overview_rows"],
        activity_feed=model["activity_feed"],
    )

    Path("README.md").write_text(readme, encoding="utf-8")
    logger("-> README.md written")
