"""Generate the governed public dashboard at ``site/index.html``.

W3 makes this module composition-only: pageshell owns chrome, webkit owns
navigation/switcher/cards/dashboard surface, and this file owns document assembly
plus the hash-pinned, prototype-only hydration program. candidate_only.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.rendering.design_tokens import DEFAULT_THEME


DATA_URL = "./data/profile_snapshot.json"


def _lang_colors_json() -> str:
    from scripts.core.config import LANG_COLORS

    return json.dumps(LANG_COLORS, sort_keys=True, separators=(",", ":"))


def _runtime_contract_json() -> str:
    from scripts.rendering.webkit.dashboard import load_dashboard_contract

    contract = load_dashboard_contract()
    payload = {
        "bindings": contract["bindings"],
        "copy": contract["copy"],
        "custom_properties": contract["custom_properties"],
        "geometry": contract["geometry"],
        "hydration_writes": contract["hydration_writes"],
        "intensity": contract["intensity"],
        "limits": contract["limits"],
        "prototypes": contract["prototypes"],
        "runtime_policy": contract["runtime_policy"],
        "status": contract["status"],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _script() -> str:
    """Return the frozen prototype-only hydration program with data placeholders."""
    return """
<script>
(function () {
  "use strict";
  const DATA_URL = "__DATA_URL__";
  const LANG_COLORS = __LANG_COLORS__;
  const RUNTIME = __RUNTIME_CONTRACT__;
  const PROTOTYPES = new Map(RUNTIME.prototypes.map((row) => [row.id, row]));
  const STATIC_WRITES = RUNTIME.hydration_writes;
  const counts = new Map();

  const fmt = (value) => {
    if (value == null || Number.isNaN(Number(value))) return "—";
    const number = Number(value);
    if (Math.abs(number) >= 1000000) return (number / 1000000).toFixed(1) + "M";
    if (Math.abs(number) >= 10000) return Math.round(number / 1000) + "k";
    return number.toLocaleString("en-US");
  };
  const get = (object, path) => path.split(".").reduce(
    (value, key) => value == null ? undefined : value[key], object);
  const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(maximum, Number(value) || 0));
  const sourceColor = (name) => Object.prototype.hasOwnProperty.call(LANG_COLORS, name)
    ? LANG_COLORS[name] : "var(--accent)";
  const level = (value, maximum) => {
    const ratio = maximum > 0 ? Number(value || 0) / maximum : 0;
    if (ratio <= 0) return "0";
    if (ratio <= RUNTIME.intensity.thresholds[1]) return "1";
    if (ratio <= RUNTIME.intensity.thresholds[2]) return "2";
    if (ratio <= RUNTIME.intensity.thresholds[3]) return "3";
    return "4";
  };

  function permitted(writes, field, sink, name) {
    return writes.some((row) => row.field === field && row.sink === sink && row.name === (name || null));
  }

  function writer(root, policy) {
    const fields = new Map();
    if (root.dataset.field) fields.set(root.dataset.field, root);
    root.querySelectorAll("[data-field]").forEach((node) => {
      if (fields.has(node.dataset.field)) throw new Error("duplicate prototype field");
      fields.set(node.dataset.field, node);
    });
    const nodeFor = (field, sink, name) => {
      if (!permitted(policy.writes, field, sink, name)) throw new Error("undeclared prototype write");
      const node = fields.get(field);
      if (!node) throw new Error("missing prototype field");
      return node;
    };
    return Object.freeze({
      text(field, value) { nodeFor(field, "text", null).textContent = String(value == null ? "" : value); },
      title(field, value) { nodeFor(field, "title", null).title = String(value == null ? "" : value); },
      hidden(field, value) { nodeFor(field, "hidden", null).hidden = Boolean(value); },
      dataEnum(field, name, value) {
        const node = nodeFor(field, "data-enum", name);
        const allowed = RUNTIME.runtime_policy.data_axes[name] || [];
        const normalized = String(value);
        if (!allowed.includes(normalized)) throw new Error("off-enum data axis");
        node.dataset[name] = normalized;
      },
      customNumber(field, name, value) {
        const node = nodeFor(field, "custom-number", name);
        const rule = RUNTIME.custom_properties[name];
        if (!rule || rule.kind !== "number") throw new Error("undeclared numeric property");
        node.style.setProperty(name, String(clamp(value, rule.minimum, rule.maximum)));
      },
      customColor(field, name, value) {
        const node = nodeFor(field, "custom-color", name);
        const rule = RUNTIME.custom_properties[name];
        if (!rule || rule.kind !== "closed-color-map") throw new Error("undeclared color property");
        const allowed = value === "var(--accent)" || Object.values(LANG_COLORS).includes(value);
        if (!allowed) throw new Error("off-map color");
        node.style.setProperty(name, value);
      },
      safeHref(field, value) {
        const node = nodeFor(field, "safe-href", "href");
        const url = new URL(String(value || ""), location.href);
        const policy = RUNTIME.runtime_policy.allowed_url;
        if (!policy.protocols.includes(url.protocol) || !policy.hosts.includes(url.hostname)) {
          throw new Error("unsafe repository URL");
        }
        node.href = url.href;
      }
    });
  }

  function targetFor(targetId, budgetKey) {
    if (targetId !== "focus") return document.getElementById(targetId);
    if (!RUNTIME.geometry.focus_lanes.includes(budgetKey)) throw new Error("off-enum focus lane");
    return document.querySelector('[data-focus-items="' + budgetKey + '"]');
  }

  function appendClone(prototypeId, targetId, budgetKey, configure) {
    const policy = PROTOTYPES.get(prototypeId);
    if (!policy || policy.target !== targetId) throw new Error("undeclared prototype/target pair");
    const count = counts.get(prototypeId) || 0;
    if (count >= policy.max_clones) throw new Error("prototype clone cap exceeded");
    const template = document.querySelector('template[data-prototype="' + prototypeId + '"]');
    const target = targetFor(targetId, budgetKey);
    if (!template || !target || target.dataset.domOwner !== policy.target_owner) {
      throw new Error("prototype endpoint mismatch");
    }
    const node = template.content.firstElementChild.cloneNode(true);
    if (!node || node.dataset.prototypeOrigin !== prototypeId
        || node.dataset.domOwner !== policy.unit.owner) throw new Error("prototype unit mismatch");
    configure(writer(node, policy));
    target.append(node);
    counts.set(prototypeId, count + 1);
  }

  function resetTargets() {
    counts.clear();
    for (const row of RUNTIME.prototypes) {
      if (row.target === "focus") continue;
      const target = document.getElementById(row.target);
      if (!target) throw new Error("missing prototype target");
      target.replaceChildren();
    }
    document.querySelectorAll("[data-focus-items]").forEach((target) => target.replaceChildren());
  }

  function staticPolicy(target, sink, name) {
    return STATIC_WRITES.some((row) => row.target === target && row.sink === sink
      && row.name === (name || null));
  }
  function staticNode(target) {
    const node = target.startsWith("[") ? document.querySelector(target)
      : document.getElementById(target);
    if (!node) throw new Error("missing static write target");
    return node;
  }
  function staticText(target, value) {
    if (!staticPolicy(target, "text", null)) throw new Error("undeclared static text write");
    staticNode(target).textContent = String(value == null ? "" : value);
  }
  function staticHidden(target, value) {
    if (!staticPolicy(target, "hidden", null)) throw new Error("undeclared static hidden write");
    staticNode(target).hidden = Boolean(value);
  }
  function staticSelectorHidden(target, value) {
    if (!target.startsWith("[data-empty-state=")) throw new Error("invalid empty-state selector");
    staticHidden(target, value);
  }
  function hideAllEmptyStates() {
    STATIC_WRITES.filter((row) => row.target.startsWith('[data-empty-state="'))
      .forEach((row) => staticSelectorHidden(row.target, true));
  }
  function setEmptyStateForSuccess(target, itemCount) {
    staticSelectorHidden(target, Number(itemCount) > 0);
  }
  function staticDataEnum(target, name, value) {
    if (!staticPolicy(target, "data-enum", name)) throw new Error("undeclared static data write");
    const allowed = RUNTIME.runtime_policy.data_axes[name] || [];
    const normalized = String(value);
    if (!allowed.includes(normalized)) throw new Error("off-enum static data axis");
    staticNode(target).dataset[name] = normalized;
  }
  function staticNumber(target, name, value) {
    if (!staticPolicy(target, "custom-number", name)) throw new Error("undeclared static number write");
    const rule = RUNTIME.custom_properties[name];
    staticNode(target).style.setProperty(name, String(clamp(value, rule.minimum, rule.maximum)));
  }

  function hydrateBindings(data) {
    const declared = new Map(RUNTIME.bindings.map((row) => [row.slot, row]));
    document.querySelectorAll("[data-bind]").forEach((node) => {
      const rule = declared.get(node.dataset.slot);
      if (!rule || rule.path !== node.dataset.bind) throw new Error("binding placement drift");
      let value = get(data, rule.path);
      if (value == null) return;
      if (rule.round != null) value = Number(value).toFixed(rule.round);
      node.textContent = (typeof value === "number" || rule.round != null) ? fmt(value) : String(value);
      if (rule.suffix) node.textContent += rule.suffix;
    });
  }

  function hydrate(data) {
    hideAllEmptyStates();
    resetTargets();
    hydrateBindings(data);
    if (data.username) staticText("hero-name", "@" + data.username);
    if (data.generated_at) {
      const date = new Date(data.generated_at);
      staticText("updated", Number.isNaN(date.valueOf()) ? data.generated_at
        : date.toLocaleString("en-US", {month: "short", day: "numeric", hour: "numeric", minute: "2-digit"}));
    }
    const ci = get(data, "scorecard.ci_coverage_pct");
    if (ci != null) staticNumber("ci-ring", "--db-progress", ci);

    const languages = Array.isArray(data.top_languages)
      ? data.top_languages.slice(0, RUNTIME.limits.languages) : [];
    if (languages[0] && languages[0].name) staticText("lang-name", languages[0].name);
    staticText("lang-count", fmt(get(data, "snapshot.languages_count") || languages.length) + " languages");
    languages.forEach((language) => {
      const color = sourceColor(language.name);
      appendClone("language-segment", "langbar", null, (out) => {
        out.customColor("segment", "--db-language-color", color);
        out.customNumber("segment", "--db-share", language.percent || 0);
      });
      appendClone("language-legend", "langlegend", null, (out) => {
        out.customColor("swatch", "--db-language-color", color);
        out.text("name", language.name || "");
        out.text("percent", Number(language.percent || 0).toFixed(1) + "%");
      });
    });

    const repositories = Array.isArray(data.featured_repo_facts)
      ? data.featured_repo_facts.slice(0, RUNTIME.limits.repositories) : [];
    setEmptyStateForSuccess('[data-empty-state="flagship"]', repositories.length);
    repositories.forEach((repository) => appendClone("repository", "flagship", null, (out) => {
      out.customColor("dot", "--db-language-color", sourceColor(repository.language));
      const linked = Boolean(repository.url);
      out.hidden("link", !linked);
      out.hidden("name", linked);
      out.text("link", repository.name || "");
      out.text("name", repository.name || "");
      if (linked) out.safeHref("link", repository.url);
      out.text("meta", (repository.language || "") + " · ★ " + fmt(repository.stars || 0)
        + " · " + (repository.pushed_ago || ""));
    }));

    for (const lane of RUNTIME.geometry.focus_lanes) {
      const items = Array.isArray(get(data, "focus." + lane))
        ? get(data, "focus." + lane).slice(0, RUNTIME.limits.focus_items_per_lane) : [];
      setEmptyStateForSuccess('[data-empty-state="focus-' + lane + '"]', items.length);
      items.forEach((item) => appendClone("focus-item", "focus", lane, (out) => {
        out.hidden("lock", !item.is_private);
        out.text("title-text", item.title || "");
        out.text("detail", item.detail || "");
      }));
    }

    const snapshot = new Map((Array.isArray(data.snapshot_rows) ? data.snapshot_rows : [])
      .map((row) => [row.key, row.display_value]));
    if (!staticPolicy("snap-tiles", "text", "data-snapshot-key")) throw new Error("snapshot write not declared");
    document.querySelectorAll("[data-snapshot-key]").forEach((node) => {
      if (snapshot.has(node.dataset.snapshotKey)) node.textContent = String(snapshot.get(node.dataset.snapshotKey));
    });

    const quality = data.data_quality || {};
    RUNTIME.status.pipeline.forEach((entry) => appendClone("pipeline-status", "pipeline", null, (out) => {
      const raw = String(quality[entry.key] || "unknown");
      const status = RUNTIME.status.map[raw] || "warn";
      const statusLabel = raw === "ok" ? RUNTIME.copy.status_ok
        : raw.charAt(0).toUpperCase() + raw.slice(1);
      out.dataEnum("root", "status", status);
      out.hidden("ok-icon", status !== "ok");
      out.hidden("warn-icon", status !== "warn");
      out.hidden("bad-icon", status !== "bad");
      out.text("label", RUNTIME.copy[entry.label] + " · " + statusLabel);
    }));

    const calendar = data.contribution_calendar;
    if (calendar && Array.isArray(calendar.weeks) && calendar.weeks.length && Number(calendar.total) > 0) {
      const days = calendar.weeks.flat().filter((day) => day && day.date)
        .slice(0, RUNTIME.limits.calendar_days);
      const maximum = Math.max(1, ...days.map((day) => Number(day.count) || 0));
      const first = days.length ? new Date(days[0].date + "T00:00:00Z").getUTCDay() : 0;
      for (let index = 0; index < Math.min(first, RUNTIME.limits.calendar_leading_blanks); index += 1) {
        appendClone("calendar-cell", "cal", null, (out) => out.dataEnum("cell", "level", "0"));
      }
      days.forEach((day) => appendClone("calendar-cell", "cal", null, (out) => {
        out.dataEnum("cell", "level", level(day.count, maximum));
        out.title("cell", day.date + ": " + fmt(day.count) + " contributions");
      }));
      RUNTIME.intensity.calendar_opacity_pct.forEach((unused, index) =>
        appendClone("calendar-scale", "cal-scale", null,
          (out) => out.dataEnum("scale", "level", String(index))));
      staticText("cal-total", fmt(calendar.total) + " contributions");
      if (days.length) {
        const month = (source) => {
          const date = new Date(source + "T00:00:00Z");
          return Number.isNaN(date.valueOf()) ? source
            : date.toLocaleString("en-US", {month: "short", year: "numeric"});
        };
        staticText("cal-months", month(days[0].date) + " – " + month(days[days.length - 1].date));
      }
      staticHidden("calendar-panel", false);
    }

    const rhythm = data.activity_rhythm;
    if (rhythm && Array.isArray(rhythm.matrix) && Number(rhythm.total) > 0) {
      const values = [];
      for (let day = 0; day < RUNTIME.limits.heat_rows; day += 1) {
        const row = Array.isArray(rhythm.matrix[day]) ? rhythm.matrix[day] : [];
        for (let hour = 0; hour < RUNTIME.limits.heat_columns; hour += 1) values.push(Number(row[hour]) || 0);
      }
      const maximum = Math.max(1, ...values);
      RUNTIME.geometry.weekdays.forEach((day) =>
        appendClone("heat-day", "heat-days", null, (out) => out.text("label", day)));
      values.forEach((count, index) => appendClone("heat-cell", "heat-grid", null, (out) => {
        const day = Math.floor(index / RUNTIME.limits.heat_columns);
        const hour = index % RUNTIME.limits.heat_columns;
        out.dataEnum("cell", "level", level(count, maximum));
        out.title("cell", RUNTIME.geometry.weekdays[day] + " " + String(hour).padStart(2, "0")
          + ":00 · " + fmt(count) + " events");
      }));
      RUNTIME.geometry.hour_labels.forEach((hour) => appendClone("heat-hour", "heat-hours", null, (out) => {
        out.text("label", String(hour).padStart(2, "0"));
        out.customNumber("label", "--db-column", hour + 1);
      }));
      const mix = Object.entries(rhythm.event_mix || {}).slice(0, RUNTIME.limits.event_mix);
      const mixMaximum = Math.max(1, ...mix.map((entry) => Number(entry[1]) || 0));
      mix.forEach(([label, count]) => appendClone("event-mix", "event-mix", null, (out) => {
        out.customNumber("bar", "--db-progress", Number(count) / mixMaximum * 100);
        out.text("label", label);
        out.text("count", fmt(count));
      }));
      staticText("rhythm-meta", fmt(rhythm.total) + " events · " + String(rhythm.timezone || ""));
      staticHidden("rhythm-panel", false);
    }
    staticDataEnum("[data-dashboard-hydration]", "dashboardHydration", "complete");
  }

  fetch(DATA_URL, {cache: "no-store"}).then((response) => response.json()).then(hydrate).catch(() => {
    hideAllEmptyStates();
    staticText("hero-tag", RUNTIME.copy.load_error);
    staticDataEnum("[data-dashboard-hydration]", "dashboardHydration", "error");
  });
}());
</script>"""


def render_dashboard(default_theme: str = DEFAULT_THEME) -> str:
    from scripts.rendering import design_tokens
    from scripts.rendering.pageshell.pageshell import (
        document_root_css,
        render_page_shell,
        theme_continuity_script_tag,
    )
    from scripts.rendering.webkit.dashboard import load_dashboard_contract, render_dashboard_surface

    if default_theme not in design_tokens.ACTIVE_THEME_NAMES:
        raise KeyError(f"default theme {default_theme!r} is not active")
    contract = load_dashboard_contract()
    surface_html, surface_css = render_dashboard_surface(default_theme)
    shell_html, shell_css = render_page_shell(
        default_theme,
        title="",
        intro="",
        breadcrumbs=[],
        body_html=surface_html,
        orientation_mode="delegated",
    )
    script = (_script().replace("__DATA_URL__", DATA_URL)
              .replace("__LANG_COLORS__", _lang_colors_json())
              .replace("__RUNTIME_CONTRACT__", _runtime_contract_json()))
    document = contract["document"]
    return f"""<!DOCTYPE html>
<html lang="{document['language']}" data-house-theme="{default_theme}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{theme_continuity_script_tag()}
<title>{document['title']}</title>
<meta name="description" content="{document['description']}">
<style>
{document_root_css()}
{shell_css}
{surface_css}
</style>
</head>
<body>
{shell_html}
{script}
</body>
</html>
"""


def write_dashboard(output_path: str = "site/index.html") -> str:
    Path(output_path).write_text(render_dashboard(), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    print(write_dashboard())
