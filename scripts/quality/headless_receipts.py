"""Chrome-headless page receipts for visible layout slices.

MF1 requires real browser receipts for pages whose layout changed: a 1280px screenshot and a 390px
DOM overflow probe, both with honest provenance sidecars. This producer shells the local Google
Chrome binary directly and fails closed if Chrome is unavailable.
"""
from __future__ import annotations

import hashlib
import html
import http.server
import json
import re
import subprocess
import tempfile
import threading
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse


CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
SCREENSHOT_KIND = "chrome-headless-screenshot"
DOM_PROBE_KIND = "chrome-headless-dom-probe"
THEME_CONTINUITY_KIND = "chrome-headless-theme-continuity-facts"
THEME_STATE_KIND = "chrome-headless-theme-state-machine-facts"
PAGE_ROUTES = {
    "index": "site/index.html",
    "showcase": "site/showcase.html",
    "settings": "site/settings.html",
    "studio": "site/studio.html",
}

# A horizontal-scroll escape is admissible only in its governed structural location. A class name
# by itself is not authority: adding `.table-scroll` to an arbitrary broad wrapper remains a defect.
DECLARED_HORIZONTAL_SCROLL_CONTAINERS = {
    "index": (
        {"class": "cal-wrap", "parent": "#calendar-panel"},
        {"class": "heat-wrap", "parent": "#rhythm-panel"},
    ),
    "showcase": ({"class": "table-scroll", "parent": ".lang"},),
    "settings": ({"class": "table-scroll", "parent": ".base"},),
    "studio": (),
}

_THEME_STATE_SCENARIOS = {
    "url-over-storage": {
        "storage": "apple-dark", "url_theme": "carbon",
    },
    "invalid-url-falls-to-storage": {
        "storage": "carbon", "url_theme": "not-active",
    },
    "invalid-storage-falls-to-house": {
        "storage": "not-active", "url_theme": None,
    },
    "house-fallback": {
        "storage": None, "url_theme": None,
    },
    "button-persists": {
        "storage": None, "url_theme": None, "click_theme": "carbon",
    },
    "storage-denied-navigation": {
        "storage": None, "url_theme": "carbon", "deny_storage": True,
        "follow_page": "showcase", "follow_via": "nav",
    },
    "storage-denied-breadcrumb": {
        "start_page": "showcase", "storage": None, "url_theme": "carbon",
        "deny_storage": True, "follow_page": "index", "follow_via": "breadcrumb",
    },
}


def _theme_state_inputs(scenario: str) -> dict:
    if scenario not in _THEME_STATE_SCENARIOS:
        raise KeyError(f"unknown theme state scenario {scenario!r}")
    inputs = {
        "start_page": "index",
        "storage": None,
        "url_theme": None,
        "click_theme": None,
        "deny_storage": False,
        "follow_page": None,
        "follow_via": None,
    }
    inputs.update(_THEME_STATE_SCENARIOS[scenario])
    return inputs
DESIGN_PAGES = ("showcase", "settings", "studio")


def _root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "contracts" / "repo_layout.json").is_file():
            return p
    raise RuntimeError("repo root not found")


def _chrome() -> Path:
    if not CHROME.is_file():
        raise FileNotFoundError(f"Chrome binary not found: {CHROME}")
    return CHROME


def _chrome_version(chrome: Path) -> str:
    proc = subprocess.run([str(chrome), "--version"], check=True, capture_output=True, text=True)
    return proc.stdout.strip()


def _route(page: str) -> Path:
    try:
        rel = PAGE_ROUTES[page]
    except KeyError as exc:
        raise KeyError(f"unknown page {page!r}; expected one of {sorted(PAGE_ROUTES)}") from exc
    path = _root() / rel
    if not path.is_file():
        raise FileNotFoundError(f"page is not generated: {path}")
    return path


def _receipt_dir(page: str, *, create: bool = False) -> Path:
    if page not in PAGE_ROUTES:
        raise KeyError(f"unknown page {page!r}; expected one of {sorted(PAGE_ROUTES)}")
    out = _root() / "assets" / "receipts" / "pages" / page
    if create:
        out.mkdir(parents=True, exist_ok=True)
    return out


def screenshot_artifact(page: str, width: int = 1280) -> Path:
    return _receipt_dir(page) / f"screenshot-{width}.png"


def dom_probe_artifact(page: str, viewport: int = 390) -> Path:
    return _receipt_dir(page) / f"dom-probe-{viewport}.json"


def theme_continuity_artifact(page: str, theme: str, viewport: int) -> Path:
    from scripts.rendering import design_tokens

    if theme not in design_tokens.ACTIVE_THEME_NAMES:
        raise KeyError(f"unknown active theme {theme!r}")
    if not isinstance(viewport, int) or viewport <= 0:
        raise ValueError(f"viewport must be a positive integer, got {viewport!r}")
    return _receipt_dir(page) / f"theme-continuity-{theme}-{viewport}.json"


def theme_state_artifact(scenario: str) -> Path:
    start_page = _theme_state_inputs(scenario)["start_page"]
    return _receipt_dir(start_page) / f"theme-state-{scenario}.json"


def provenance_path(artifact: Path) -> Path:
    return Path(f"{artifact}.provenance.json")


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    # fail-closed: a Chrome that hangs (observed: first-run tasks under a fresh --user-data-dir
    # kept the process alive after the artifact was written) is an ERROR, never an infinite wait.
    return subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)


def _rel(path: Path) -> str:
    return path.relative_to(_root()).as_posix()


def _write_provenance(
    *,
    page: str,
    artifact: Path,
    kind: str,
    command: list[str],
    chrome_version: str,
    viewport: dict,
    extra: dict | None = None,
) -> Path:
    route = _root() / PAGE_ROUTES[page]
    payload = {
        "contract_id": "PageHeadlessReceiptProvenance",
        "page": page,
        "route": PAGE_ROUTES[page],
        # the receipt is PINNED to the exact page bytes it was captured from (stand-in SF-2):
        # a stale or hand-authored artifact reddens the hermetic guard without needing Chrome.
        "page_sha256": hashlib.sha256(route.read_bytes()).hexdigest(),
        "artifact": _rel(artifact),
        "kind": kind,
        "producer": "scripts/quality/headless_receipts.py",
        "command": command,
        "chrome_version": chrome_version,
        "viewport": viewport,
        "authority_status": "candidate_only",
        "cannot_mark_done": True,
    }
    if extra:
        payload.update(extra)
    out = provenance_path(artifact)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def screenshot_page(page: str, width: int = 1280) -> Path:
    """Write `assets/receipts/pages/<page>/screenshot-<width>.png` via Chrome headless."""
    chrome = _chrome()
    chrome_version = _chrome_version(chrome)
    route = _route(page)
    _receipt_dir(page, create=True)
    artifact = screenshot_artifact(page, width)
    height = max(900, round(width * 1.2))
    # NO --user-data-dir: a custom fresh profile dir makes --headless=new hang after writing the
    # artifact (observed); the ephemeral auto-profile exits cleanly (the session-proven invocation).
    command = [
        str(chrome),
        "--headless=new",
        "--no-first-run",
        "--no-default-browser-check",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        f"--screenshot={artifact}",
        route.as_uri(),
    ]
    _run(command)
    if not artifact.is_file() or artifact.stat().st_size <= 0:
        raise RuntimeError(f"{artifact}: Chrome did not produce a nonempty screenshot")
    _write_provenance(
        page=page,
        artifact=artifact,
        kind=SCREENSHOT_KIND,
        command=command,
        chrome_version=chrome_version,
        viewport={"width": width, "height": height},
    )
    return artifact


def _probe_html(page: str, route: Path, viewport: int, height: int) -> str:
    """A HOST page embedding the REAL site page in an iframe of exactly `viewport` CSS px —
    Chrome's CLI window has a ~500px minimum width, so a bare --window-size=390 silently measures
    at 500 (stand-in MF-1). The iframe gives a true 390 layout viewport; the probe measures the
    iframe's contentDocument and the producer FAILS CLOSED if the measured client width differs
    from the declared viewport."""
    scroll_rules = json.dumps(
        list(DECLARED_HORIZONTAL_SCROLL_CONTAINERS[page]), sort_keys=True)
    host = f"""<!doctype html>
<html><head><title>probe host</title></head>
<body style="margin:0">
<iframe id="target" src="{route.as_uri()}"
        style="width:{viewport}px;height:{height}px;border:0" scrolling="no"></iframe>
{{script}}
</body></html>"""
    script = f"""
<script>
(function () {{
  var done = false;
  var scrollRules = {scroll_rules};
  function cls(el) {{
    return String(el.className || "").replace(/\\s+/g, " ").trim();
  }}
  function probe() {{
    if (done) return;
    var frame = document.getElementById("target");
    var doc = frame && frame.contentDocument;
    if (!doc || !doc.body) {{ window.setTimeout(probe, 100); return; }}
    done = true;
    var root = doc.documentElement;
    var body = doc.body;
    var clientWidth = root.clientWidth || {viewport};
    var bodyScrollWidth = body ? body.scrollWidth : 0;
    var scrollWidth = Math.max(root.scrollWidth || 0, bodyScrollWidth);
    var offenders = [];
    Array.prototype.forEach.call(doc.querySelectorAll("*"), function (el) {{
      var style = frame.contentWindow.getComputedStyle(el);
      if (style.display === "none" || style.visibility === "hidden") return;
      var rect = el.getBoundingClientRect();
      if (!rect || (rect.width === 0 && rect.height === 0)) return;
      var overLeft = Math.max(0, -rect.left);
      var overRight = Math.max(0, rect.right - clientWidth);
      if (overLeft > 1 || overRight > 1) {{
        var scrollInfo = null;
        var contained = false;
        var ancestor = el.parentElement;
        while (ancestor) {{
          var ancestorClasses = cls(ancestor).split(" ");
          var rule = scrollRules.find(function (candidate) {{
            return ancestorClasses.indexOf(candidate.class) !== -1
              && ancestor.parentElement
              && ancestor.parentElement.matches(candidate.parent);
          }});
          if (rule) {{
            var scrollStyle = frame.contentWindow.getComputedStyle(ancestor);
            var scrollRect = ancestor.getBoundingClientRect();
            var inViewport = scrollRect.left >= -1 && scrollRect.right <= clientWidth + 1;
            contained = (scrollStyle.overflowX === "auto" || scrollStyle.overflowX === "scroll")
              && inViewport && scrollRect.width > 1;
            scrollInfo = {{
              "tag": ancestor.tagName.toLowerCase(),
              "id": ancestor.id || "",
              "class": cls(ancestor),
              "left": Math.round(scrollRect.left * 100) / 100,
              "right": Math.round(scrollRect.right * 100) / 100,
              "width": Math.round(scrollRect.width * 100) / 100,
              "overflow_x": scrollStyle.overflowX,
              "in_viewport": inViewport,
              "rule": rule,
              "parent": {{
                "tag": ancestor.parentElement.tagName.toLowerCase(),
                "id": ancestor.parentElement.id || "",
                "class": cls(ancestor.parentElement)
              }}
            }};
            break;
          }}
          ancestor = ancestor.parentElement;
        }}
        offenders.push({{
          "tag": el.tagName.toLowerCase(),
          "id": el.id || "",
          "class": cls(el),
          "left": Math.round(rect.left * 100) / 100,
          "right": Math.round(rect.right * 100) / 100,
          "width": Math.round(rect.width * 100) / 100,
          "overflow_px": Math.round(Math.max(overLeft, overRight) * 100) / 100,
          "contained_by_declared_scroll": contained,
          "scroll_container": scrollInfo
        }});
      }}
    }});
    var overflowPx = Math.max(0, scrollWidth - clientWidth);
    var uncontained = offenders.filter(function (o) {{
      return o.contained_by_declared_scroll !== true;
    }});
    var result = {{
      "contract_id": "PageHeadlessDomProbe",
      "page": "{page}",
      "route": "{PAGE_ROUTES[page]}",
      "kind": "{DOM_PROBE_KIND}",
      "viewport": {{"width": {viewport}, "height": {height}}},
      "client_width": clientWidth,
      "scroll_width": scrollWidth,
      "body_scroll_width": bodyScrollWidth,
      "declared_scroll_containers": scrollRules,
      "horizontal_overflow": overflowPx > 1 || uncontained.length > 0,
      "overflow_px": overflowPx,
      "offender_count": offenders.length,
      "uncontained_offender_count": uncontained.length,
      "offenders": offenders.slice(0, 20),
      "authority_status": "candidate_only",
      "cannot_mark_done": true
    }};
    document.documentElement.innerHTML = "<head><title>probe</title></head><body><pre id=\\"headless-probe-json\\"></pre></body>";
    document.getElementById("headless-probe-json").textContent = JSON.stringify(result);
  }}
  var frame0 = document.getElementById("target");
  frame0.addEventListener("load", function () {{
    requestAnimationFrame(function () {{ requestAnimationFrame(probe); }});
  }});
  window.setTimeout(probe, 800);
}}());
</script>
"""
    return host.replace("{script}", script)


def _parse_probe_dump(dump: str) -> dict:
    matches = re.findall(r'<pre id="headless-probe-json">(.*?)</pre>', dump, flags=re.S)
    payloads = [html.unescape(payload).strip() for payload in matches if payload.strip()]
    if not payloads:
        raise RuntimeError("Chrome DOM dump did not contain the headless probe payload")
    return json.loads(payloads[-1])


def _theme_probe_html(page: str, theme: str, viewport: int) -> str:
    from scripts.rendering import design_tokens
    from scripts.rendering.pageshell.pageshell import _profile_decls

    route = "/" + PAGE_ROUTES[page]
    variables = list(_profile_decls(theme))
    template = r"""<!doctype html>
<html><head><title>theme continuity probe</title></head><body style="margin:0">
<iframe id="target" style="border:0;width:__VIEWPORT__px;height:1200px"></iframe>
<script>
(function () {
  const seededTheme = __THEME__;
  const storageKey = __STORAGE_KEY__;
  const variables = __VARIABLES__;
  const scrollRules = __SCROLL_RULES__;
  localStorage.setItem(storageKey, seededTheme);
  const frame = document.getElementById("target");
  frame.src = __ROUTE__;
  function className(el) {
    return String(el.className || "").replace(/\s+/g, " ").trim();
  }
  function probe() {
    const doc = frame.contentDocument;
    if (!doc || !doc.body) return;
    const view = frame.contentWindow;
    const root = doc.documentElement;
    const rootStyle = view.getComputedStyle(root);
    const tokens = {};
    variables.forEach((name) => { tokens[name] = rootStyle.getPropertyValue(name).trim(); });
    const activeNavs = doc.querySelectorAll(".site-nav a[aria-current]");
    const activeNav = activeNavs[0];
    const navStyle = activeNav ? view.getComputedStyle(activeNav) : null;
    const navRect = activeNav ? activeNav.getBoundingClientRect() : null;
    let navAncestorHidden = false;
    let navAncestor = activeNav ? activeNav.parentElement : null;
    while (navAncestor) {
      const ancestorStyle = view.getComputedStyle(navAncestor);
      if (ancestorStyle.display === "none" || ancestorStyle.visibility === "hidden"
          || parseFloat(ancestorStyle.opacity) <= 0) {
        navAncestorHidden = true;
        break;
      }
      navAncestor = navAncestor.parentElement;
    }
    const clientWidth = root.clientWidth;
    const scrollWidth = Math.max(root.scrollWidth || 0, doc.body.scrollWidth || 0);
    const offenders = [];
    Array.prototype.forEach.call(doc.querySelectorAll("*"), function (el) {
      const style = view.getComputedStyle(el);
      if (style.display === "none" || style.visibility === "hidden") return;
      const rect = el.getBoundingClientRect();
      if (!rect || (rect.width === 0 && rect.height === 0)) return;
      if (rect.left >= -1 && rect.right <= clientWidth + 1) return;
      let ancestor = el.parentElement;
      let contained = false;
      let scrollContainer = null;
      while (ancestor) {
        const ancestorStyle = view.getComputedStyle(ancestor);
        const ancestorRect = ancestor.getBoundingClientRect();
        const ancestorClasses = className(ancestor).split(" ");
        const rule = scrollRules.find((candidate) =>
          ancestorClasses.includes(candidate.class)
          && ancestor.parentElement
          && ancestor.parentElement.matches(candidate.parent));
        const declaredHere = Boolean(rule);
        if (declaredHere
            && (ancestorStyle.overflowX === "auto" || ancestorStyle.overflowX === "scroll")
            && ancestorRect.width > 1 && ancestorRect.left >= -1
            && ancestorRect.right <= clientWidth + 1) {
          contained = true;
          scrollContainer = {
            tag: ancestor.tagName.toLowerCase(), id: ancestor.id || "",
            class: className(ancestor), overflow_x: ancestorStyle.overflowX,
            rule: rule,
            parent: {
              tag: ancestor.parentElement.tagName.toLowerCase(),
              id: ancestor.parentElement.id || "",
              class: className(ancestor.parentElement)
            },
            left: Math.round(ancestorRect.left * 100) / 100,
            right: Math.round(ancestorRect.right * 100) / 100
          };
          break;
        }
        ancestor = ancestor.parentElement;
      }
      offenders.push({
        tag: el.tagName.toLowerCase(), id: el.id || "", class: className(el),
        left: Math.round(rect.left * 100) / 100,
        right: Math.round(rect.right * 100) / 100,
        width: Math.round(rect.width * 100) / 100,
        contained_by_declared_scroll: contained,
        scroll_container: scrollContainer
      });
    });
    const payload = {
      contract_id: "PageThemeContinuityFacts",
      page: __PAGE__, route: __ROUTE__, kind: __KIND__,
      seeded_theme: seededTheme,
      observed_theme: root.dataset.theme || "",
      house_theme: root.dataset.houseTheme || "",
      viewport: {width: __VIEWPORT__, height: 1200},
      client_width: clientWidth,
      scroll_width: scrollWidth,
      computed_root_tokens: tokens,
      color_scheme: rootStyle.colorScheme,
      nav: navStyle ? {
        active_count: activeNavs.length,
        display: navStyle.display,
        radius_px: parseFloat(navStyle.borderRadius) || 0,
        border_bottom_width_px: parseFloat(navStyle.borderBottomWidth) || 0,
        border_bottom_color: navStyle.borderBottomColor,
        foreground_color: navStyle.color,
        background_color: navStyle.backgroundColor,
        visibility: navStyle.visibility,
        opacity: navStyle.opacity,
        ancestor_hidden: navAncestorHidden,
        has_rendered_box: activeNav.getClientRects().length > 0
          && navRect.width > 0 && navRect.height > 0,
        intersects_viewport: navRect.bottom > 0 && navRect.right > 0
          && navRect.top < root.clientHeight && navRect.left < clientWidth,
        box: {
          left: Math.round(navRect.left * 100) / 100,
          top: Math.round(navRect.top * 100) / 100,
          width: Math.round(navRect.width * 100) / 100,
          height: Math.round(navRect.height * 100) / 100
        }
      } : null,
      pressed_themes: Array.prototype.map.call(
        doc.querySelectorAll('[data-theme-set][aria-pressed="true"]'),
        (button) => button.dataset.themeSet),
      declared_scroll_containers: scrollRules,
      horizontal_overflow: scrollWidth - clientWidth > 1
        || offenders.some((offender) => !offender.contained_by_declared_scroll),
      uncontained_offender_count: offenders.filter(
        (offender) => !offender.contained_by_declared_scroll).length,
      offenders: offenders.slice(0, 20),
      authority_status: "candidate_only",
      cannot_mark_done: true
    };
    document.documentElement.innerHTML = '<head><title>probe</title></head>'
      + '<body><pre id="headless-probe-json"></pre></body>';
    document.getElementById("headless-probe-json").textContent = JSON.stringify(payload);
  }
  frame.addEventListener("load", function () {
    requestAnimationFrame(function () { requestAnimationFrame(function () {
      window.setTimeout(probe, 250);
    }); });
  });
}());
</script></body></html>"""
    replacements = {
        "__PAGE__": json.dumps(page),
        "__ROUTE__": json.dumps(route),
        "__THEME__": json.dumps(theme),
        "__STORAGE_KEY__": json.dumps(design_tokens.THEME_STORAGE_KEY),
        "__VARIABLES__": json.dumps(variables),
        "__SCROLL_RULES__": json.dumps(
            list(DECLARED_HORIZONTAL_SCROLL_CONTAINERS[page]), sort_keys=True),
        "__VIEWPORT__": str(viewport),
        "__KIND__": json.dumps(THEME_CONTINUITY_KIND),
    }
    for needle, value in replacements.items():
        template = template.replace(needle, value)
    return template


def _theme_state_probe_html(scenario: str) -> str:
    from scripts.rendering import design_tokens

    inputs = _theme_state_inputs(scenario)
    config = dict(inputs)
    config["scenario"] = scenario
    config["storage_key"] = design_tokens.THEME_STORAGE_KEY
    config["routes"] = PAGE_ROUTES
    template = r"""<!doctype html>
<html><head><title>theme state probe</title></head><body style="margin:0">
<iframe id="target" style="border:0;width:390px;height:1200px"></iframe>
<script>
(function () {
  const config = __CONFIG__;
  const frame = document.getElementById("target");
  let initial = null;
  let followedHref = null;
  let loadCount = 0;
  let done = false;
  if (config.storage === null) localStorage.removeItem(config.storage_key);
  else localStorage.setItem(config.storage_key, config.storage);

  function targetUrl(page, urlTheme) {
    const url = new URL("/" + config.routes[page], location.href);
    if (urlTheme !== null) url.searchParams.set("theme", urlTheme);
    if (config.deny_storage) url.searchParams.set("__deny_storage", "1");
    return url.href;
  }
  function observe() {
    const doc = frame.contentDocument;
    const root = doc.documentElement;
    let storageValue;
    try { storageValue = frame.contentWindow.localStorage.getItem(config.storage_key); }
    catch (error) { storageValue = "__storage_error__"; }
    const linkThemes = Array.from(doc.querySelectorAll("[data-theme-propagate]"))
      .map((link) => new URL(link.href).searchParams.get("theme"));
    return {
      observed_theme: root.dataset.theme || "",
      house_theme: root.dataset.houseTheme || "",
      storage_value: storageValue,
      pressed_themes: Array.from(
        doc.querySelectorAll('[data-theme-set][aria-pressed="true"]'),
        (button) => button.dataset.themeSet),
      propagated_link_themes: Array.from(new Set(linkThemes)).sort()
    };
  }
  function finish(finalObservation) {
    if (done) return;
    done = true;
    const payload = {
      contract_id: "PageThemeStateMachineFacts",
      kind: __KIND__, scenario: config.scenario,
      inputs: __INPUTS__,
      initial: initial, final: finalObservation,
      follow_page: config.follow_page || null,
      followed_href: followedHref,
      authority_status: "candidate_only", cannot_mark_done: true
    };
    document.body.innerHTML = '<pre id="headless-probe-json"></pre>';
    document.getElementById("headless-probe-json").textContent = JSON.stringify(payload);
  }
  frame.addEventListener("load", function () {
    loadCount += 1;
    window.setTimeout(function () {
      if (loadCount === 1 && config.click_theme) {
        const button = frame.contentDocument.querySelector(
          '[data-theme-set="' + config.click_theme + '"]');
        if (!button) throw new Error("click target missing");
        button.click();
        window.setTimeout(function () { finish(observe()); }, 100);
        return;
      }
      if (loadCount === 1 && config.follow_page) {
        initial = observe();
        const suffix = "/" + config.routes[config.follow_page];
        const scope = config.follow_via === "breadcrumb" ? ".ps-crumbs" : ".site-nav";
        const link = Array.from(frame.contentDocument.querySelectorAll(
          scope + " [data-theme-propagate]"))
          .find((candidate) => new URL(candidate.href).pathname.endsWith(suffix));
        if (!link) throw new Error("follow target missing");
        followedHref = link.href;
        const follow = new URL(followedHref);
        if (config.deny_storage) follow.searchParams.set("__deny_storage", "1");
        frame.src = follow.href;
        return;
      }
      finish(observe());
    }, 300);
  });
  frame.src = targetUrl(config.start_page, config.url_theme);
}());
</script></body></html>"""
    return (template
            .replace("__CONFIG__", json.dumps(config, sort_keys=True))
            .replace("__INPUTS__", json.dumps(inputs, sort_keys=True))
            .replace("__KIND__", json.dumps(THEME_STATE_KIND)))


_DENY_STORAGE_SCRIPT = """<script>
Object.defineProperty(window, "localStorage", {
  configurable: true,
  get: function () { throw new Error("storage denied by receipt harness"); }
});
</script>"""


class _ReceiptHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *args) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/__theme_state_probe__.html":
            try:
                query = parse_qs(parsed.query, strict_parsing=True)
                scenario = query["scenario"][0]
                body = _theme_state_probe_html(scenario).encode("utf-8")
            except (KeyError, ValueError, IndexError) as exc:
                self.send_error(400, f"invalid theme state probe query: {exc}")
                return
            self._send_html(body)
            return
        known_route = next(
            (route for route in PAGE_ROUTES.values() if parsed.path == "/" + route), None)
        query = parse_qs(parsed.query)
        if known_route and query.get("__deny_storage") == ["1"]:
            page = (_root() / known_route).read_text(encoding="utf-8")
            marker = "<head>"
            if marker not in page:
                self.send_error(500, f"cannot inject storage-denial harness into {known_route}")
                return
            body = page.replace(marker, marker + _DENY_STORAGE_SCRIPT, 1).encode("utf-8")
            self._send_html(body)
            return
        if parsed.path != "/__theme_probe__.html":
            super().do_GET()
            return
        try:
            query = parse_qs(parsed.query, strict_parsing=True)
            page = query["page"][0]
            theme = query["theme"][0]
            viewport = int(query["viewport"][0])
            if page not in PAGE_ROUTES:
                raise KeyError(page)
            body = _theme_probe_html(page, theme, viewport).encode("utf-8")
        except (KeyError, ValueError, IndexError) as exc:
            self.send_error(400, f"invalid theme probe query: {exc}")
            return
        self._send_html(body)

    def _send_html(self, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@contextmanager
def _site_server():
    handler = partial(_ReceiptHandler, directory=str(_root()))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _theme_continuity_probe(page: str, theme: str, viewport: int, base_url: str) -> Path:
    chrome = _chrome()
    chrome_version = _chrome_version(chrome)
    _route(page)
    _receipt_dir(page, create=True)
    artifact = theme_continuity_artifact(page, theme, viewport)
    query = urlencode({"page": page, "theme": theme, "viewport": viewport})
    url = f"{base_url}/__theme_probe__.html?{query}"
    height = 1300
    command = [
        str(chrome),
        "--headless=new",
        "--no-first-run",
        "--no-default-browser-check",
        f"--window-size={max(800, viewport + 80)},{height}",
        "--virtual-time-budget=3500",
        "--dump-dom",
        url,
    ]
    parse_error: RuntimeError | None = None
    for _attempt in range(3):
        try:
            payload = _parse_probe_dump(_run(command).stdout)
            break
        except RuntimeError as exc:
            parse_error = exc
    else:
        raise RuntimeError(
            f"{page}/{theme}: continuity probe did not finish after 3 captures"
        ) from parse_error
    if payload.get("client_width") != viewport:
        raise RuntimeError(
            f"{page}/{theme}: continuity probe measured client_width="
            f"{payload.get('client_width')} != {viewport}")
    artifact.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_provenance(
        page=page,
        artifact=artifact,
        kind=THEME_CONTINUITY_KIND,
        command=command,
        chrome_version=chrome_version,
        viewport={"width": viewport, "height": 1200},
        extra={
            "seeded_theme": theme,
            "observed_theme": payload.get("observed_theme"),
            "house_theme": payload.get("house_theme"),
        },
    )
    return artifact


def theme_continuity_probe(page: str, theme: str, viewport: int) -> Path:
    """Prove localStorage restoration for one page/theme/viewport on a real HTTP origin."""
    with _site_server() as base_url:
        return _theme_continuity_probe(page, theme, viewport, base_url)


def write_all_theme_continuity_receipts() -> list[Path]:
    from scripts.rendering import design_tokens

    out: list[Path] = []
    with _site_server() as base_url:
        for page in PAGE_ROUTES:
            for theme in design_tokens.ACTIVE_THEME_NAMES:
                for viewport in (1280, 390):
                    out.append(_theme_continuity_probe(page, theme, viewport, base_url))
    return out


def _theme_state_probe(scenario: str, base_url: str) -> Path:
    inputs = _theme_state_inputs(scenario)
    start_page = inputs["start_page"]
    chrome = _chrome()
    chrome_version = _chrome_version(chrome)
    _receipt_dir(start_page, create=True)
    artifact = theme_state_artifact(scenario)
    query = urlencode({"scenario": scenario})
    url = f"{base_url}/__theme_state_probe__.html?{query}"
    command = [
        str(chrome),
        "--headless=new",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=800,1300",
        "--virtual-time-budget=5000",
        "--dump-dom",
        url,
    ]
    parse_error: RuntimeError | None = None
    for _attempt in range(3):
        try:
            payload = _parse_probe_dump(_run(command).stdout)
            break
        except RuntimeError as exc:
            parse_error = exc
    else:
        raise RuntimeError(
            f"{scenario}: theme state probe did not finish after 3 captures"
        ) from parse_error
    artifact.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    extra = {"scenario": scenario}
    follow_page = inputs["follow_page"]
    if follow_page:
        follow_route = _root() / PAGE_ROUTES[follow_page]
        extra.update({
            "follow_page": follow_page,
            "follow_page_sha256": hashlib.sha256(follow_route.read_bytes()).hexdigest(),
        })
    _write_provenance(
        page=start_page,
        artifact=artifact,
        kind=THEME_STATE_KIND,
        command=command,
        chrome_version=chrome_version,
        viewport={"width": 390, "height": 1200},
        extra=extra,
    )
    return artifact


def write_all_theme_state_receipts() -> list[Path]:
    out: list[Path] = []
    with _site_server() as base_url:
        for scenario in _THEME_STATE_SCENARIOS:
            out.append(_theme_state_probe(scenario, base_url))
    return out


def dom_probe(page: str, viewport: int = 390) -> Path:
    """Write `assets/receipts/pages/<page>/dom-probe-<viewport>.json` via Chrome headless."""
    chrome = _chrome()
    chrome_version = _chrome_version(chrome)
    route = _route(page)
    _receipt_dir(page, create=True)
    artifact = dom_probe_artifact(page, viewport)
    height = 1000
    with tempfile.TemporaryDirectory(prefix=f"{page}-probe-") as tmp:
        probe_file = Path(tmp) / f"{page}.html"
        probe_file.write_text(_probe_html(page, route, viewport, height), encoding="utf-8")
        command = [
            str(chrome),
            "--headless=new",
            "--no-first-run",
            "--no-default-browser-check",
            "--allow-file-access-from-files",   # the host page reads its file:// iframe's document
            f"--window-size=800,{height}",      # HOST window (> iframe); the iframe IS the viewport
            "--virtual-time-budget=2500",
            "--dump-dom",
            probe_file.as_uri(),
        ]
        proc = _run(command)
    payload = _parse_probe_dump(proc.stdout)
    if payload.get("client_width") != viewport:
        raise RuntimeError(
            f"{page}: probe measured client_width={payload.get('client_width')} != declared "
            f"viewport {viewport} — refusing to write an overclaiming receipt (stand-in MF-1)")
    artifact.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_provenance(
        page=page,
        artifact=artifact,
        kind=DOM_PROBE_KIND,
        command=command,
        chrome_version=chrome_version,
        viewport={"width": viewport, "height": height},
    )
    return artifact


def write_all_page_receipts() -> list[Path]:
    out: list[Path] = []
    for page in PAGE_ROUTES:
        out.append(screenshot_page(page))
        out.append(dom_probe(page))
    out.extend(write_all_theme_continuity_receipts())
    out.extend(write_all_theme_state_receipts())
    return out


def main() -> None:
    for path in write_all_page_receipts():
        print(path.relative_to(_root()))


if __name__ == "__main__":
    main()
