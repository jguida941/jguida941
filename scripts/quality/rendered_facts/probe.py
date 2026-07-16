"""Verdict-free browser program for W4 rendered facts."""
from __future__ import annotations

import json
from urllib.parse import urlencode

from scripts.quality.rendered_facts.policy import (
    expected_index_hydration_facts, input_hashes, load_policy, page_routes, state_plan,
)
from scripts.quality.rendered_facts.subject_identity import IDENTITY_DOMAIN, compiled_policy

_INDEX_SENTINELS = {
    "hero-contributions": "[data-slot=\"hero-contributions\"]",
    "lang-count": "#lang-count", "cal-total": "#cal-total",
    "rhythm-meta": "#rhythm-meta", "lang-name": "#lang-name",
}

def probe_html(page: str, theme: str, viewport: int, height: int) -> str:
    """Return a host that emits raw post-hydration facts for every policy state.

    Stable node identity is stored once. Mutable attributes, computed styles, boxes, scroll data,
    pseudo styles, and text ranges are captured index-aligned for each reachable state.
    """
    policy = load_policy()
    subject_matchers = compiled_policy(policy)
    inputs = input_hashes(page, theme)
    plan = state_plan(page)
    route = "/" + page_routes()[page] + "?" + urlencode({"theme": theme})
    index_expected = expected_index_hydration_facts() if page == "index" else {
        "sentinel_values": {}, "prototype_origin_counts": {}, "empty_state_hidden": {},
    }
    template = r'''<!doctype html>
<html><head><title>rendered facts host</title></head><body style="margin:0">
<iframe id="target" src=__ROUTE_ATTR__ style="border:0;width:__VIEWPORT__px;height:__HEIGHT__px"></iframe>
<script>
(async function () {
  "use strict";
  const page = __PAGE__;
  const theme = __THEME__;
  const policy = __POLICY__;
  const inputs = __INPUTS__;
  const statePlan = __STATE_PLAN__;
  const route = __ROUTE__;
  const routePath = new URL(route, location.href).pathname;
  const indexSentinels = __INDEX_SENTINELS__;
  const prototypeIds = __PROTOTYPE_IDS__;
  const emptyStateIds = __EMPTY_STATE_IDS__;
  const subjectMatchers = __SUBJECT_MATCHERS__;
  const identityDomain = __IDENTITY_DOMAIN__;
  const frame = document.getElementById("target");

  function publish(payload) {
    const pre = document.createElement("pre");
    pre.id = "headless-probe-json";
    pre.textContent = JSON.stringify(payload);
    document.body.append(pre);
  }
  function round(value) {
    const scale = Math.pow(10, policy.enumeration.css_px_precision);
    return Math.round(Number(value || 0) * scale) / scale;
  }
  function box(rect) {
    return {x: round(rect.x), y: round(rect.y), left: round(rect.left), top: round(rect.top),
      right: round(rect.right), bottom: round(rect.bottom), width: round(rect.width),
      height: round(rect.height)};
  }
  function normalized(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }
  function directText(el) {
    return normalized(Array.prototype.filter.call(el.childNodes, function (node) {
      return node.nodeType === Node.TEXT_NODE;
    }).map(function (node) { return node.nodeValue || ""; }).join(" "));
  }
  function dataIdentity(el) {
    const out = {};
    Array.prototype.forEach.call(el.attributes || [], function (attr) {
      if (attr.name.indexOf("data-") === 0) out[attr.name] = attr.value;
    });
    return Object.keys(out).sort().reduce(function (acc, key) {
      acc[key] = out[key]; return acc;
    }, {});
  }
  function hrefIdentity(el) {
    const raw = el.getAttribute("href");
    if (raw === null) return null;
    const resolved = new URL(raw, el.ownerDocument.baseURI);
    if (resolved.origin === location.origin) {
      return resolved.pathname + resolved.search + resolved.hash;
    }
    return raw;
  }
  function styleFacts(style) {
    const out = {};
    policy.computed_style_fields.forEach(function (field) {
      const cssName = (field.indexOf("webkit_") === 0 ? "-" : "")
        + field.replace(/_/g, "-");
      let value = style.getPropertyValue(cssName).trim();
      if (field === "backdrop_filter" && !value) {
        value = style.getPropertyValue("-webkit-backdrop-filter").trim();
      }
      out[field] = value;
    });
    return out;
  }
  function pseudoFacts(view, el, pseudo) {
    const style = view.getComputedStyle(el, pseudo);
    const content = style.getPropertyValue("content").trim();
    if (content === "none" || content === "normal") return {content: content};
    const out = {};
    policy.pseudo_style_fields.forEach(function (field) {
      const cssName = field.replace(/_/g, "-");
      let value = style.getPropertyValue(cssName).trim();
      if (field === "backdrop_filter" && !value) {
        value = style.getPropertyValue("-webkit-backdrop-filter").trim();
      }
      out[field] = value;
    });
    return out;
  }
  function documentElementFacts(view, el) {
    return {box: box(el.getBoundingClientRect()), rect_count: el.getClientRects().length,
      hidden: el.hasAttribute("hidden"), client_width: el.clientWidth,
      client_height: el.clientHeight, scroll_width: el.scrollWidth,
      scroll_height: el.scrollHeight, computed: styleFacts(view.getComputedStyle(el)),
      pseudo: {before: pseudoFacts(view, el, "::before"),
        after: pseudoFacts(view, el, "::after")}};
  }
  function forcedTurn(doc, turn) {
    return new Promise(function (resolve, reject) {
      let finished = false;
      const deadline = window.setTimeout(function () {
        if (!finished) reject(new Error("settle-turn-timeout:" + turn));
      }, policy.readiness.settle.turn_deadline_ms);
      window.setTimeout(function () {
        try {
          const root = doc.documentElement;
          const display = doc.defaultView.getComputedStyle(root).display;
          const rootBox = box(root.getBoundingClientRect());
          finished = true;
          window.clearTimeout(deadline);
          resolve({turn: turn, root_display: display, root_box: rootBox});
        } catch (error) {
          finished = true;
          window.clearTimeout(deadline);
          reject(error);
        }
      }, 0);
    });
  }
  async function settle(doc) {
    const reads = [];
    for (let turn = 1; turn <= policy.readiness.settle.turns; turn += 1) {
      reads.push(await forcedTurn(doc, turn));
    }
    const animations = doc.getAnimations().map(function (animation) {
      const target = animation.effect && animation.effect.target;
      return {id: animation.id || "", play_state: animation.playState,
        pending: Boolean(animation.pending), current_time: animation.currentTime === null
          ? null : Number(animation.currentTime),
        target: target ? {tag: target.tagName.toLowerCase(), id: target.id || "",
          class: normalized(target.className)} : null};
    });
    return {mechanism: policy.readiness.settle.mechanism,
      turns: policy.readiness.settle.turns, reads: reads, animations: animations};
  }
  async function waitForDocument() {
    for (let attempt = 0; attempt < 240; attempt += 1) {
      const doc = frame.contentDocument;
      if (doc && doc.body && frame.contentWindow.location.pathname === routePath) return doc;
      await new Promise(function (resolve) { window.setTimeout(resolve, 50); });
    }
    throw new Error("frame-document-timeout");
  }
  async function waitForReady(doc, view) {
    let hydration = null;
    for (let attempt = 0; attempt < 160; attempt += 1) {
      const root = doc.querySelector(policy.readiness.index_hydration_selector);
      hydration = root ? root.getAttribute("data-dashboard-hydration") : null;
      const themeReady = doc.documentElement.getAttribute(policy.readiness.theme_attribute) === theme;
      const hydrationReady = page !== "index" || hydration === policy.readiness.index_ready_value;
      if (themeReady && hydrationReady) break;
      await new Promise(function (resolve) { window.setTimeout(resolve, 50); });
    }
    if (doc.documentElement.getAttribute(policy.readiness.theme_attribute) !== theme) {
      throw new Error("theme-not-ready");
    }
    if (page === "index" && hydration !== policy.readiness.index_ready_value) {
      throw new Error("hydration-not-ready:" + hydration);
    }
    await doc.fonts.ready;
    return {hydration: hydration, settle: await settle(doc)};
  }
  function identityTable(doc) {
    const elements = Array.from(doc.body.querySelectorAll(policy.enumeration.selector));
    const indexByNode = new Map(elements.map(function (el, index) { return [el, index]; }));
    const nodes = elements.map(function (el, index) {
      return {index: index, parent_index: indexByNode.has(el.parentElement)
          ? indexByNode.get(el.parentElement) : null,
        tag: el.tagName.toLowerCase(), id: el.id || "", owner: el.getAttribute("data-dom-owner"),
        role: el.getAttribute("role"), href: hrefIdentity(el), type: el.getAttribute("type"),
        for: el.getAttribute("for"), tabindex: el.getAttribute("tabindex"),
        contenteditable: el.getAttribute("contenteditable"), direct_text: directText(el),
        text_content: normalized(el.textContent), data: dataIdentity(el)};
    });
    const textNodes = [];
    const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
    let textNode;
    while ((textNode = walker.nextNode())) {
      if (!normalized(textNode.nodeValue)) continue;
      textNodes.push({index: textNodes.length,
        parent_index: indexByNode.has(textNode.parentElement)
          ? indexByNode.get(textNode.parentElement) : null,
        child_index: textNode.parentElement
          ? Array.prototype.indexOf.call(textNode.parentElement.childNodes, textNode) : null,
        text: normalized(textNode.nodeValue)});
    }
    return {elements: elements, index_by_node: indexByNode, nodes: nodes,
      text_nodes: textNodes};
  }
  function matcherValue(node, name) {
    return name.indexOf("data-") === 0 ? node.data[name] : node[name];
  }
  function matchesCompiled(node, className, compounds) {
    return compounds.some(function (compound) {
      if (compound.tag !== null && node.tag !== compound.tag) return false;
      const classes = className.split(/\s+/).filter(Boolean);
      if (compound.classes.some(function (name) { return classes.indexOf(name) < 0; })) {
        return false;
      }
      return compound.attributes.every(function (attr) {
        const value = matcherValue(node, attr.name);
        let result = attr.operator === "present" ? value !== undefined && value !== null
          : value === attr.value;
        if (attr.operator === "not-equals") result = !result;
        return result;
      });
    });
  }
  function subjectIndices(table, matcher) {
    return table.nodes.filter(function (node, index) {
      return matchesCompiled(node, normalized(table.elements[index].className), matcher);
    }).map(function (node) { return node.index; });
  }
  function staticTable(doc) {
    const table = identityTable(doc);
    const contrast = {};
    Object.keys(subjectMatchers.contrast).forEach(function (id) {
      contrast[id] = subjectIndices(table, subjectMatchers.contrast[id]);
    });
    const density = {};
    Object.keys(subjectMatchers.density[page]).forEach(function (selector) {
      density[selector] = subjectIndices(table, subjectMatchers.density[page][selector]);
    });
    table.subjects = {interactive: subjectIndices(table, subjectMatchers.interactive),
      contrast: contrast, density: density};
    return table;
  }
  async function identityDigest(table) {
    const nodeRows = table.nodes.map(function (node) {
      return policy.stable_node_fields.map(function (field) {
        if (field !== "data") return node[field];
        return Object.keys(node.data).sort().map(function (key) { return [key, node.data[key]]; });
      });
    });
    const textRows = table.text_nodes.map(function (row) {
      return policy.text_node_fields.map(function (field) { return row[field]; });
    });
    const bytes = new TextEncoder().encode(identityDomain + JSON.stringify([nodeRows, textRows]));
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest)).map(function (byte) {
      return byte.toString(16).padStart(2, "0");
    }).join("");
  }
  function isDescendantIndex(table, index, ancestor) {
    let current = index;
    while (current !== null) {
      if (current === ancestor) return true;
      current = table.nodes[current].parent_index;
    }
    return false;
  }
  function sampleAxis(start, end, step) {
    if (end <= start) return [];
    const values = [];
    for (let value = start + Math.min(step / 2, (end - start) / 2);
         value < end; value += step) values.push(value);
    const center = (start + end) / 2;
    if (!values.some(function (value) { return Math.abs(value - center) < 0.01; })) {
      values.push(center);
    }
    return values.sort(function (left, right) { return left - right; });
  }
  function contrastHits(doc, table, textRanges) {
    const out = {};
    const step = policy.predicate_parameters.contrast_hit_grid_css_px;
    Object.keys(table.subjects.contrast).sort().forEach(function (subjectId) {
      out[subjectId] = table.subjects.contrast[subjectId].map(function (subjectIndex) {
        const samples = [];
        table.text_nodes.forEach(function (textNode, textIndex) {
          if (textNode.parent_index === null
              || !isDescendantIndex(table, textNode.parent_index, subjectIndex)) return;
          textRanges[textIndex].rects.forEach(function (rect) {
            sampleAxis(rect.left, rect.right, step).forEach(function (x) {
              sampleAxis(rect.top, rect.bottom, step).forEach(function (y) {
                const hit = doc.elementsFromPoint(x, y)[0] || null;
                samples.push({x: round(x), y: round(y),
                  top_index: hit === null || !table.index_by_node.has(hit)
                    ? -1 : table.index_by_node.get(hit), visual_top_index: null});
              });
            });
          });
        });
        return {subject_index: subjectIndex, samples: samples};
      });
    });
    const restored = [];
    table.elements.forEach(function (el) {
      if (doc.defaultView.getComputedStyle(el).pointerEvents !== "none") return;
      restored.push({el: el, style: el.getAttribute("style")});
      el.style.setProperty("pointer-events", "auto", "important");
    });
    try {
      Object.values(out).forEach(function (rows) {
        rows.forEach(function (row) {
          row.samples.forEach(function (sample) {
            const hit = doc.elementsFromPoint(sample.x, sample.y)[0] || null;
            sample.visual_top_index = hit === null || !table.index_by_node.has(hit)
              ? -1 : table.index_by_node.get(hit);
          });
        });
      });
    } finally {
      restored.forEach(function (row) {
        if (row.style === null) row.el.removeAttribute("style");
        else row.el.setAttribute("style", row.style);
      });
    }
    return out;
  }
  function stateVector(doc, view, table, stateId, settleFacts, domIdentitySha256) {
    const elements = table.elements;
    const vector = elements.map(function (el, index) {
      const style = view.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return {index: index, class: normalized(el.className), hidden: el.hasAttribute("hidden"),
        checked: "checked" in el ? Boolean(el.checked) : null,
        disabled: "disabled" in el ? Boolean(el.disabled) : null,
        aria_hidden: el.getAttribute("aria-hidden"), aria_checked: el.getAttribute("aria-checked"),
        aria_pressed: el.getAttribute("aria-pressed"), aria_selected: el.getAttribute("aria-selected"),
        box: box(rect), rect_count: el.getClientRects().length,
        scroll: {client_width: el.clientWidth, client_height: el.clientHeight,
          scroll_width: el.scrollWidth, scroll_height: el.scrollHeight},
        computed: styleFacts(style),
        pseudo: {before: pseudoFacts(view, el, "::before"),
          after: pseudoFacts(view, el, "::after")}};
    });
    const textRanges = table.text_nodes.map(function (row) {
      const parent = row.parent_index === null ? null : elements[row.parent_index];
      if (!parent) return {index: row.index, rects: []};
      const node = parent.childNodes[row.child_index];
      if (!node || node.nodeType !== Node.TEXT_NODE || normalized(node.nodeValue) !== row.text) {
        return {index: row.index, rects: []};
      }
      const range = doc.createRange();
      range.selectNodeContents(node);
      return {index: row.index, rects: Array.from(range.getClientRects()).map(box)};
    });
    const root = doc.documentElement;
    const body = doc.body;
    const rootStyle = view.getComputedStyle(root);
    const tokens = {};
    policy.root_token_fields.forEach(function (name) {
      tokens[name] = rootStyle.getPropertyValue(name).trim();
    });
    const stageDisplays = Array.from(doc.querySelectorAll(".stage[data-lang]")).map(function (el) {
      return {lang: el.getAttribute("data-lang"), display: view.getComputedStyle(el).display};
    });
    const activeOptions = Array.from(doc.querySelectorAll(".swap-opt.active")).map(function (el) {
      return {base: el.getAttribute("data-base"), component: el.getAttribute("data-component"),
        source: el.getAttribute("data-source")};
    });
    const variants = Array.from(doc.querySelectorAll(".variant[data-variant]")).map(function (el) {
      return {variant: el.getAttribute("data-variant"), hidden: el.hasAttribute("hidden"),
        display: view.getComputedStyle(el).display};
    });
    return {state_id: stateId, settle: settleFacts,
      dom_identity_sha256: domIdentitySha256,
      witness: {checked_radio_ids: Array.from(doc.querySelectorAll(".lang-radio:checked"))
          .map(function (el) { return el.id; }), stage_displays: stageDisplays,
        active_options: activeOptions, variants: variants},
      document: {root: documentElementFacts(view, root),
        body: documentElementFacts(view, body), root_tokens: tokens},
      elements: vector, text_ranges: textRanges,
      contrast_hits: contrastHits(doc, table, textRanges)};
  }
  async function activate(doc, view, row) {
    if (page !== "studio") return settle(doc);
    const base = row.base;
    const radio = doc.getElementById("lang-" + base);
    if (!radio) throw new Error("missing-base-radio:" + base);
    radio.click();
    const baseOption = doc.querySelector('.swap-opt[data-base="' + base
      + '"][data-component="button"][data-source="' + base + '"]:not([disabled])');
    if (!baseOption) throw new Error("missing-base-option:" + base);
    baseOption.click();
    if (row.source !== base) {
      const swap = doc.querySelector('.swap-opt[data-base="' + base + '"][data-component="'
        + row.component + '"][data-source="' + row.source + '"]:not([disabled])');
      if (!swap) throw new Error("missing-swap-option:" + row.state_id);
      swap.click();
    }
    return settle(doc);
  }
  function indexFacts(doc) {
    const sentinelValues = {};
    Object.keys(indexSentinels).forEach(function (name) {
      const node = doc.querySelector(indexSentinels[name]);
      sentinelValues[name] = node ? normalized(node.textContent) : null;
    });
    const prototypeOriginCounts = {};
    prototypeIds.forEach(function (id) {
      prototypeOriginCounts[id] = doc.querySelectorAll('[data-prototype-origin="' + id + '"]').length;
    });
    const emptyStateHidden = {};
    emptyStateIds.forEach(function (id) {
      const node = doc.querySelector('[data-empty-state="' + id + '"]');
      emptyStateHidden[id] = node ? node.hidden : null;
    });
    return {sentinel_values: sentinelValues, prototype_origin_counts: prototypeOriginCounts,
      empty_state_hidden: emptyStateHidden};
  }

  try {
    const doc = await waitForDocument();
    const view = frame.contentWindow;
    const ready = await waitForReady(doc, view);
    const table = staticTable(doc);
    const states = [];
    for (const row of statePlan) {
      const stateSettle = await activate(doc, view, row);
      const currentTable = identityTable(doc);
      currentTable.subjects = table.subjects;
      const domIdentitySha256 = await identityDigest(currentTable);
      states.push(stateVector(
        doc, view, currentTable, row.state_id, stateSettle, domIdentitySha256));
    }
    publish({contract_id: "RenderedComputedFacts", schema_version: 1,
      page: page, route: __PAGE_ROUTE__, theme: theme,
      viewport: {width: Number(view.innerWidth), height: Number(view.innerHeight),
        device_scale_factor: Number(view.devicePixelRatio)},
      inputs: inputs,
      readiness: {observed_theme: doc.documentElement.getAttribute("data-theme"),
        hydration_state: ready.hydration, fonts: "ready", settle: ready.settle,
        index: indexFacts(doc)},
      nodes: table.nodes, text_nodes: table.text_nodes, subjects: table.subjects, states: states});
  } catch (error) {
    publish({contract_id: "RenderedComputedFacts", schema_version: 1, page: page,
      theme: theme, error: String(error && error.message || error)});
  }
})();
</script></body></html>'''
    replacements = {
        "__VIEWPORT__": str(viewport),
        "__HEIGHT__": str(height),
        "__PAGE__": json.dumps(page),
        "__THEME__": json.dumps(theme),
        "__POLICY__": json.dumps(policy, sort_keys=True, separators=(",", ":")),
        "__INPUTS__": json.dumps(inputs, sort_keys=True, separators=(",", ":")),
        "__STATE_PLAN__": json.dumps(plan, sort_keys=True, separators=(",", ":")),
        "__ROUTE_ATTR__": json.dumps(route),
        "__ROUTE__": json.dumps(route),
        "__PAGE_ROUTE__": json.dumps(page_routes()[page]),
        "__INDEX_SENTINELS__": json.dumps(_INDEX_SENTINELS if page == "index" else {}, sort_keys=True),
        "__PROTOTYPE_IDS__": json.dumps(sorted(index_expected["prototype_origin_counts"])),
        "__EMPTY_STATE_IDS__": json.dumps(sorted(index_expected["empty_state_hidden"])),
        "__SUBJECT_MATCHERS__": json.dumps(
            subject_matchers, sort_keys=True, separators=(",", ":")),
        "__IDENTITY_DOMAIN__": json.dumps(IDENTITY_DOMAIN),
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template
