"""Governed landing-dashboard surface for W3.

The module owns dashboard layout/data slots only. Generic navigation, switcher, and
grouped cards remain direct invocations of their webkit component emitters.
candidate_only.
"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path


def _contract_path() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "contracts" / "dashboard_surface.json"
        if candidate.is_file():
            return candidate
    raise RuntimeError("contracts/dashboard_surface.json not found")


def load_dashboard_contract() -> dict:
    return json.loads(_contract_path().read_text(encoding="utf-8"))


def empty_state_hidden(hydration_state: str, *, item_count: int | None = None) -> bool:
    """Return whether a no-data claim is admissible for the hydration lifecycle."""
    if hydration_state in {"pending", "error"}:
        return True
    if hydration_state != "complete" or item_count is None or item_count < 0:
        raise ValueError("complete empty-state visibility requires a non-negative item count")
    return item_count > 0


def _binding_attrs(binding: dict) -> str:
    attrs = [f'data-slot="{escape(binding["slot"])}"',
             f'data-bind="{escape(binding["path"])}"']
    if binding["suffix"] is not None:
        attrs.append(f'data-suffix="{escape(binding["suffix"])}"')
    if binding["round"] is not None:
        attrs.append(f'data-round="{binding["round"]}"')
    return " ".join(attrs)


def _section_open(section: dict, owner: str, *, element: str = "section", id_attr: str = "") -> str:
    hidden = " hidden" if section["hidden"] else ""
    return (f'<{element} class="db-section db-{section["id"]}" {owner} '
            f'data-dashboard-section="{section["id"]}"{id_attr}{hidden}>')


def _heading(section: dict, copy: dict, owner: str) -> str:
    title = (f'<h2 class="db-section-title" {owner}>{escape(copy[section["title"]])}</h2>'
             if section["title"] else "")
    return (f'<header class="db-section-head" {owner}>'
            f'<p class="db-eyebrow" {owner}>{escape(copy[section["eyebrow"]])}</p>'
            f'{title}</header>')


def _icon(name: str, owner: str, field: str | None = None) -> str:
    from scripts.rendering.icons import LUCIDE

    attrs = f' data-field="{field}"' if field else ""
    return (f'<svg class="db-icon" {owner}{attrs} viewBox="0 0 24 24" aria-hidden="true">'
            f'{LUCIDE[name]}</svg>')


def _templates(owner: str) -> str:
    return "".join((
        f'<template {owner} data-prototype="language-segment"><i class="db-language-segment" {owner} data-prototype-origin="language-segment" data-field="segment"></i></template>',
        f'<template {owner} data-prototype="language-legend"><div class="db-language-legend-row" {owner} data-prototype-origin="language-legend" data-field="root"><i class="db-language-dot" {owner} data-field="swatch"></i><span class="db-language-name" {owner} data-field="name"></span><span class="db-language-percent" {owner} data-field="percent"></span></div></template>',
        f'<template {owner} data-prototype="repository"><div class="db-repository-row" {owner} data-prototype-origin="repository" data-field="root"><i class="db-language-dot" {owner} data-field="dot"></i><a class="db-repository-name" {owner} data-field="link" rel="noreferrer"></a><span class="db-repository-name" {owner} data-field="name"></span><span class="db-repository-meta" {owner} data-field="meta"></span></div></template>',
        f'<template {owner} data-prototype="focus-item"><div class="db-focus-item" {owner} data-prototype-origin="focus-item" data-field="root"><strong class="db-focus-title" {owner} data-field="title">{_icon("lock", owner, "lock")}<span {owner} data-field="title-text"></span></strong><span class="db-focus-detail" {owner} data-field="detail"></span></div></template>',
        f'<template {owner} data-prototype="calendar-cell"><i class="db-calendar-cell" {owner} data-prototype-origin="calendar-cell" data-field="cell"></i></template>',
        f'<template {owner} data-prototype="calendar-scale"><i class="db-calendar-cell" {owner} data-prototype-origin="calendar-scale" data-field="scale"></i></template>',
        f'<template {owner} data-prototype="heat-day"><span class="db-heat-day" {owner} data-prototype-origin="heat-day" data-field="label"></span></template>',
        f'<template {owner} data-prototype="heat-cell"><i class="db-heat-cell" {owner} data-prototype-origin="heat-cell" data-field="cell"></i></template>',
        f'<template {owner} data-prototype="heat-hour"><span class="db-heat-hour" {owner} data-prototype-origin="heat-hour" data-field="label"></span></template>',
        f'<template {owner} data-prototype="event-mix"><span class="db-event-item" {owner} data-prototype-origin="event-mix" data-field="root"><span class="db-event-track" {owner}><i class="db-event-fill" {owner} data-field="bar"></i></span><span {owner} data-field="label"></span><b {owner} data-field="count"></b></span></template>',
        f'<template {owner} data-prototype="pipeline-status"><span class="db-status" {owner} data-prototype-origin="pipeline-status" data-field="root">{_icon("check", owner, "ok-icon")}{_icon("alert", owner, "warn-icon")}{_icon("cross", owner, "bad-icon")}<span {owner} data-field="label"></span></span></template>',
    ))


def _dashboard_css() -> str:
    from scripts.rendering.webkit.dashboard_style import dashboard_css

    return dashboard_css()


def render_dashboard_surface(house: str) -> tuple[str, str]:
    """Return governed dashboard body markup and component CSS."""
    from scripts.rendering.design import loader
    from scripts.rendering.webkit import components, theme_selector

    active = tuple(loader.load("_index")["active_design_profiles"])
    if house not in active:
        raise KeyError(f"house profile {house!r} is not active")
    contract = load_dashboard_contract()
    copy = contract["copy"]
    sections = {row["id"]: row for row in contract["sections"]}
    bindings = {row["slot"]: row for row in contract["bindings"]}
    owner = 'data-dom-owner="webkit.dashboard"'

    nav_html, nav_css = components.render_switchable_nav(
        house,
        [("home", "index.html"), ("showcase", "showcase.html"),
         ("studio", "studio.html"), ("settings", "settings.html")],
        active="index.html",
    )
    switcher_html, switcher_css = theme_selector.render_theme_selector(house)
    score_rows = (
        components.MetricRow(copy["score_active_days"], detail=copy["score_active_days_detail"], icon="fire", slot="score-active-days", bind="scorecard.active_days_last_year"),
        components.MetricRow(copy["score_active_repos"], detail=copy["score_active_repos_detail"], icon="commit", slot="score-active-repos", bind="scorecard.active_repos_7d"),
        components.MetricRow(copy["score_workflows"], detail=copy["score_workflows_detail"], icon="workflow", slot="score-workflows", bind="scorecard.automation_workflows"),
        components.MetricRow(copy["score_releases"], detail=copy["score_releases_detail"], icon="release", slot="score-releases", bind="scorecard.releases_30d"),
        components.MetricRow(copy["score_primary_language"], detail=copy["score_language_detail"], icon="code", label_id="lang-name", slot="score-language-share", bind="scorecard.primary_lang_share_pct", suffix="%", round_digits=0),
        components.MetricRow(copy["score_last_push"], detail=copy["score_last_push_detail"], icon="calendar", slot="score-last-push", bind="scorecard.days_since_last_push", suffix="d", round_digits=0),
    )
    snapshot_rows = (
        components.MetricRow(copy["snapshot_commits"], snapshot_key="public_scope_commits"),
        components.MetricRow(copy["snapshot_repos"], snapshot_key="total_repos"),
        components.MetricRow(copy["snapshot_private"], snapshot_key="private_owned_repos"),
        components.MetricRow(copy["snapshot_stars"], snapshot_key="total_stars"),
        components.MetricRow(copy["snapshot_prs"], snapshot_key="prs_merged"),
        components.MetricRow(copy["snapshot_ci"], snapshot_key="ci_repos"),
    )
    score_html, score_css = components.render_card(
        house, "dashboard-score", "rest", rows=score_rows, switchable=True,
        surface_context="content",
    )
    snapshot_html, snapshot_css = components.render_card(
        house, "dashboard-snapshot", "rest", rows=snapshot_rows, switchable=True,
        surface_context="content",
    )

    hero = (
        _section_open(sections["hero"], owner)
        + f'<div class="db-hero-top" {owner}><div class="db-hero-copy" {owner}>'
        + f'<p class="db-eyebrow" {owner}>{escape(copy["hero_eyebrow"])}</p>'
        + f'<h1 class="db-hero-title" id="hero-name" data-page-title {owner}>{escape(copy["hero_title"])}</h1>'
        + f'<p class="db-hero-intro" id="hero-tag" data-page-intro {owner}>{escape(copy["hero_intro"])}</p>'
        + f'{nav_html}</div>{switcher_html}</div>'
        + f'<div class="db-hero-kpi" {owner}><div {owner}><div class="db-hero-primary" {owner} {_binding_attrs(bindings["hero-contributions"])}>—</div><div class="db-hero-label" {owner}>{escape(copy["hero_kpi_label"])}</div></div>'
        + f'<div class="db-hero-stats" {owner}>'
        + f'<div class="db-hero-stat" {owner}><span class="db-hero-stat-value" {owner} {_binding_attrs(bindings["hero-active-days"])}>—</span><span class="db-hero-stat-label" {owner}>{escape(copy["hero_active_days"])}</span></div>'
        + f'<div class="db-hero-stat" {owner}><span class="db-hero-stat-value" {owner} {_binding_attrs(bindings["hero-repos"])}>—</span><span class="db-hero-stat-label" {owner}>{escape(copy["hero_public_repos"])}</span></div>'
        + f'<div class="db-hero-stat" {owner}><span class="db-hero-stat-value" {owner} {_binding_attrs(bindings["hero-stars"])}>—</span><span class="db-hero-stat-label" {owner}>{escape(copy["hero_stars"])}</span></div></div></div>'
        + f'<div class="db-live" {owner}><i class="db-live-dot" {owner}></i><span {owner}>{escape(copy["live_prefix"])} <span {owner} id="updated">—</span></span></div></section>'
    )
    scorecard = (
        _section_open(sections["scorecard"], owner) + _heading(sections["scorecard"], copy, owner)
        + f'<div class="db-score-ring-row" {owner}><div class="db-score-ring" {owner} id="ci-ring"><span class="db-score-ring-value" {owner} {_binding_attrs(bindings["ci-coverage"])}>—</span></div>'
        + f'<div class="db-score-copy" {owner}><span class="db-score-label" {owner}>{escape(copy["ci_label"])}</span><span class="db-score-detail" {owner}>{escape(copy["ci_detail"])}</span></div></div>'
        + score_html + '</section>'
    )
    calendar = (
        _section_open(sections["calendar"], owner, id_attr=' id="calendar-panel"')
        + _heading(sections["calendar"], copy, owner)
        + f'<span class="db-section-meta" {owner} id="cal-total">—</span><div class="db-calendar-scroll" {owner}><div class="db-calendar-grid" {owner} id="cal" aria-label="{escape(copy["calendar_label"])}"></div></div>'
        + f'<div class="db-calendar-foot" {owner}><span {owner} id="cal-months"></span><span {owner}>{escape(copy["calendar_less"])} <span class="db-calendar-scale" {owner} id="cal-scale"></span> {escape(copy["calendar_more"])}</span></div></section>'
    )
    languages = (
        _section_open(sections["languages"], owner) + _heading(sections["languages"], copy, owner)
        + f'<span class="db-section-meta" {owner} id="lang-count">—</span><div class="db-language-bar" {owner} id="langbar"></div><div class="db-language-legend" {owner} id="langlegend"></div></section>'
    )
    rhythm = (
        _section_open(sections["rhythm"], owner, id_attr=' id="rhythm-panel"')
        + _heading(sections["rhythm"], copy, owner)
        + f'<span class="db-section-meta" {owner} id="rhythm-meta">—</span><div class="db-rhythm-scroll" {owner}><div class="db-rhythm-grid" {owner} aria-label="{escape(copy["rhythm_label"])}"><div class="db-heat-days" {owner} id="heat-days"></div><div class="db-heat-grid" {owner} id="heat-grid"></div><div class="db-heat-hours" {owner} id="heat-hours"></div></div></div><div class="db-event-mix" {owner} id="event-mix"></div></section>'
    )
    flagship = (
        _section_open(sections["flagship"], owner) + _heading(sections["flagship"], copy, owner)
        + f'<p class="db-empty" {owner} hidden data-empty-state="flagship">{escape(copy["flagship_empty"])}</p>'
        + f'<div class="db-repository-list" {owner} id="flagship"></div></section>'
    )
    focus_lanes = "".join(
        f'<section class="db-focus-lane" {owner} data-focus-lane="{lane}"><h3 class="db-focus-lane-title" {owner}>{escape(copy[f"focus_{lane}"])}</h3><p class="db-empty" {owner} hidden data-empty-state="focus-{lane}">{escape(copy["focus_empty"])}</p><div class="db-focus-items" {owner} data-focus-items="{lane}"></div></section>'
        for lane in contract["geometry"]["focus_lanes"]
    )
    focus = (
        _section_open(sections["focus"], owner) + _heading(sections["focus"], copy, owner)
        + f'<div class="db-focus-lanes" {owner} id="focus">{focus_lanes}</div></section>'
    )
    snapshot = (
        _section_open(sections["snapshot"], owner) + _heading(sections["snapshot"], copy, owner)
        + f'<div class="db-snapshot-card" {owner} id="snap-tiles">{snapshot_html}</div>'
        + f'<h3 class="db-pipeline-title" {owner}>{escape(copy["pipeline_title"])}</h3><div class="db-pipeline" {owner} id="pipeline"></div></section>'
    )
    footer = (f'<footer class="db-footer" {owner}>{escape(copy["footer_prefix"])} '
              f'<a {owner} href="https://github.com/jguida941" rel="noreferrer">{escape(copy["footer_link"])}</a></footer>')
    html = (f'<div class="db-dashboard" {owner} data-dashboard-hydration="pending">'
            + hero + scorecard + calendar + languages
            + rhythm + flagship + focus + snapshot + footer + _templates(owner) + '</div>')
    css = "\n".join((score_css, snapshot_css, switcher_css, nav_css, _dashboard_css()))
    return html, css
