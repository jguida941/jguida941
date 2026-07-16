"""Closed policy/data projection for W4 rendered computed facts."""
from __future__ import annotations

import hashlib
import json
from datetime import date
from math import floor
from pathlib import Path


RENDERED_FACT_KIND = "chrome-headless-rendered-computed-facts"


def root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "contracts" / "rendered_fact_policy.json").is_file():
            return parent
    raise RuntimeError("repo root not found")


def load_policy() -> dict:
    data = json.loads((root() / "contracts" / "rendered_fact_policy.json").read_text(
        encoding="utf-8"))
    if data.get("contract_id") != "RenderedFactPolicy":
        raise RuntimeError("rendered fact policy has the wrong contract_id")
    from scripts.quality.rendered_facts.doctrine import validate_policy_doctrine
    validate_policy_doctrine(data)
    return data


def page_routes() -> dict[str, str]:
    manifest = json.loads((root() / "contracts" / "page_manifest.json").read_text(
        encoding="utf-8"))
    return {row["id"]: row["route"] for row in manifest["pages"]}


def active_profiles() -> list[str]:
    return json.loads((root() / "contracts" / "design_profiles" / "_index.json").read_text(
        encoding="utf-8"))["active_design_profiles"]


def receipt_dir(page: str, *, create: bool = False) -> Path:
    if page not in page_routes():
        raise KeyError(f"unknown page {page!r}")
    path = root() / "assets" / "receipts" / "pages" / page
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def artifact_path(page: str, theme: str, viewport: int) -> Path:
    if page not in page_routes():
        raise KeyError(f"unknown page {page!r}")
    if theme not in active_profiles():
        raise KeyError(f"unknown active theme {theme!r}")
    widths = {row["width"] for row in load_policy()["matrix"]["viewports"]}
    if viewport not in widths:
        raise ValueError(f"viewport {viewport!r} is outside the rendered-fact matrix")
    extension = load_policy()["artifact_encoding"]["extension"]
    return receipt_dir(page) / f"rendered-facts-{theme}-{viewport}{extension}"


def provenance_path(artifact: Path) -> Path:
    return Path(f"{artifact}.provenance.json")


def digest(relative: str) -> str:
    return hashlib.sha256((root() / relative).read_bytes()).hexdigest()


def input_hashes(page: str, theme: str) -> dict:
    routes = page_routes()
    inputs = {
        "page_sha256": digest(routes[page]),
        "policy_sha256": digest("contracts/rendered_fact_policy.json"),
        "rendered_doctrine_sha256": digest("docs/design/pageshell.md"),
        "page_manifest_sha256": digest("contracts/page_manifest.json"),
        "profile_sha256": digest(f"contracts/design_profiles/{theme}.json"),
        "profile_index_sha256": digest("contracts/design_profiles/_index.json"),
        "policy_projection_sha256": digest("scripts/quality/rendered_facts/policy.py"),
        "doctrine_sha256": digest("scripts/quality/rendered_facts/doctrine.py"),
        "codec_sha256": digest("scripts/quality/rendered_facts/codec.py"),
        "provenance_sha256": digest("scripts/quality/rendered_facts/provenance.py"),
        "samples_sha256": digest("scripts/quality/rendered_facts/samples.py"),
        "geometry_sha256": digest("scripts/quality/rendered_facts/geometry.py"),
        "inventory_sha256": digest("scripts/quality/rendered_facts/inventory.py"),
        "packet_types_sha256": digest("scripts/quality/rendered_facts/packet_types.py"),
        "probe_sha256": digest("scripts/quality/rendered_facts/probe.py"),
        "producer_sha256": digest("scripts/quality/rendered_facts/producer.py"),
        "schema_sha256": digest("scripts/quality/rendered_facts/schema.py"),
        "subject_identity_sha256": digest(
            "scripts/quality/rendered_facts/subject_identity.py"),
        "state_authority_sha256": digest(
            "scripts/quality/rendered_facts/state_authority.py"),
        "settings_admissibility_sha256": digest(
            "scripts/quality/settings_admissibility.py"),
        "headless_runtime_sha256": digest("scripts/quality/headless_receipts.py"),
        "dashboard_surface_sha256": None,
        "data_sha256": None,
    }
    if page == "index":
        inputs["dashboard_surface_sha256"] = digest("contracts/dashboard_surface.json")
        inputs["data_sha256"] = digest("site/data/profile_snapshot.json")
    return inputs


def state_plan(page: str) -> list[dict]:
    if page not in page_routes():
        raise KeyError(page)
    policy = load_policy()
    if page != "studio":
        return [{"state_id": policy["state_plan"]["default_state_id"], "base": None,
                 "component": None, "source": None, "variant": None}]
    from scripts.quality.rendered_facts.state_authority import studio_state_plan

    declared = policy["state_plan"]["studio"]["states"]
    rows = studio_state_plan()
    if declared != rows:
        raise RuntimeError("rendered Studio states differ from admissible-space authority")
    ids = [row["state_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise RuntimeError("rendered Studio state plan contains duplicate ids")
    return [dict(row) for row in rows]


def expected_density_count(surface: dict) -> int:
    if "count" in surface:
        return int(surface["count"])
    source = surface.get("count_source")
    if source == "contracts/dashboard_surface.json#/sections":
        return len(json.loads((root() / "contracts" / "dashboard_surface.json").read_text(
            encoding="utf-8"))["sections"])
    if source == "contracts/design_profiles/_index.json#/active_design_profiles":
        return len(active_profiles())
    raise RuntimeError(f"unknown density count source {source!r}")


def _dashboard_number(value: object) -> str:
    number = float(value or 0)
    if abs(number) >= 10000:
        return f"{floor(number / 1000 + 0.5)}k"
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,}"


def expected_index_hydration_facts() -> dict:
    """Derive the W3 hydration witness from public data and dashboard DATA."""
    data_path = root() / "site" / "data" / "profile_snapshot.json"
    contract_path = root() / "contracts" / "dashboard_surface.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    limits, geometry = contract["limits"], contract["geometry"]
    languages = (data.get("top_languages") if isinstance(data.get("top_languages"), list)
                 else [])[:limits["languages"]]
    repositories = (data.get("featured_repo_facts")
                    if isinstance(data.get("featured_repo_facts"), list) else [])
    repositories = repositories[:limits["repositories"]]
    focus = data.get("focus") if isinstance(data.get("focus"), dict) else {}
    counts = {row["id"]: 0 for row in contract["prototypes"]}
    counts.update({"language-segment": len(languages), "language-legend": len(languages),
                   "repository": len(repositories),
                   "focus-item": sum(min(len(focus.get(lane, []))
                       if isinstance(focus.get(lane), list) else 0,
                       limits["focus_items_per_lane"]) for lane in geometry["focus_lanes"]),
                   "pipeline-status": len(contract["status"]["pipeline"])})
    calendar = data.get("contribution_calendar")
    if (isinstance(calendar, dict) and isinstance(calendar.get("weeks"), list)
            and calendar["weeks"] and float(calendar.get("total") or 0) > 0):
        days = [day for week in calendar["weeks"] if isinstance(week, list)
                for day in week if isinstance(day, dict) and day.get("date")]
        days = days[:limits["calendar_days"]]
        first = ((date.fromisoformat(str(days[0]["date"])).weekday() + 1) % 7) if days else 0
        counts["calendar-cell"] = min(first, limits["calendar_leading_blanks"]) + len(days)
        counts["calendar-scale"] = len(contract["intensity"]["calendar_opacity_pct"])
    rhythm = data.get("activity_rhythm")
    if (isinstance(rhythm, dict) and isinstance(rhythm.get("matrix"), list)
            and float(rhythm.get("total") or 0) > 0):
        counts.update({"heat-day": len(geometry["weekdays"]),
                       "heat-cell": limits["heat_rows"] * limits["heat_columns"],
                       "heat-hour": len(geometry["hour_labels"]),
                       "event-mix": min(len(rhythm.get("event_mix") or {}), limits["event_mix"])})
    snapshot = data.get("snapshot") if isinstance(data.get("snapshot"), dict) else {}
    sentinels = {
        "hero-contributions": _dashboard_number(snapshot.get("last_year_contributions")),
        "lang-count": f"{_dashboard_number(snapshot.get('languages_count') or len(languages))} languages",
        "cal-total": (f"{_dashboard_number(calendar.get('total'))} contributions"
                      if isinstance(calendar, dict) and float(calendar.get("total") or 0) > 0 else "—"),
        "rhythm-meta": (f"{_dashboard_number(rhythm.get('total'))} events · {str(rhythm.get('timezone') or '')}"
                        if isinstance(rhythm, dict) and float(rhythm.get("total") or 0) > 0 else "—"),
        "lang-name": str(languages[0].get("name") or "") if languages else "primary language",
    }
    return {"data_sha256": digest("site/data/profile_snapshot.json"),
            "sentinel_values": sentinels, "prototype_origin_counts": dict(sorted(counts.items())),
            "empty_state_hidden": {"flagship": bool(repositories), **{
                f"focus-{lane}": bool(focus.get(lane)) for lane in geometry["focus_lanes"]}}}
