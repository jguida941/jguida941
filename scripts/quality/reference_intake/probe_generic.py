"""W6-P — the universal engine's generic foreign-DOM rendered-facts probe.

This is the "invariant against every aspect" measurement CORE. It measures EVERY visible aspect of
ANY served page, with NO dependence on the site's own ``data-dom-owner`` / hydration sentinels —
foreign pages have none. It:

* serves a given HTML directory on an ephemeral loopback port (a rewritten COPY, so the served
  bytes carry forced-pseudo marker classes but the caller's source is untouched);
* drives local Google Chrome (headless, subprocess) to an EXACT-viewport iframe — the CLI window
  has a ~500px floor, so a bare ``--window-size`` silently over-measures; the iframe gives the true
  layout viewport and the probe FAILS CLOSED if the measured client width differs from the declared
  viewport;
* extracts, per subject found by heuristics (buttons / links / landmarks / card-clusters /
  heading-tuples), the computed-style vector across the §3.1 aspect families
  (palette / typography / spacing / geometry / radius / border / shadow / material / motion), the DOM
  structure (tag / role / attributes-of-interest), and the reachable pseudo-states (:hover / :focus /
  :active, forced via marker classes on the served copy).

The output is a CLOSED, deterministic packet::

    {contract_id: "ExternalReferenceRenderedFacts", schema_version: 1,
     viewport, subjects: [...], aspects_measured: [<§3.1 ids covered>]}

"Every aspect" is by CONSTRUCTION: the probe captures the computed CSS + DOM + reachable states, not
a hand-picked subset. If Chrome is unavailable the probe raises :class:`ChromeUnavailable` — it never
fabricates facts.

The §3.1 aspect vocabulary below is referenced as CONSTANTS (not imported): a `reference_intake`
vocabulary package is not assumed to exist in this base. The ids are reconstructed from the W6
design brief's family list plus ``docs/DESIGN_SPEC.md`` Part 0, because the canonical
``docs/plans/handoff/w3c-0-design-closure.md`` §3.1 is not present in this standalone worktree.
"""
from __future__ import annotations

import functools
import html
import http.server
import json
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path


CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
CONTRACT_ID = "ExternalReferenceRenderedFacts"
SCHEMA_VERSION = 1
HOST_FILENAME = "__probe_host__.html"
_FACTS_PRE_ID = "probe-facts-json"


class ChromeUnavailable(RuntimeError):
    """Raised when the Chrome binary is missing — the probe FAILS HONESTLY, never fabricates."""


# --- §3.1 aspect vocabulary (31 ids) ----------------------------------------------------------
# Each computed aspect maps to (family, representative-key) in a subject's `computed` block; the
# family dict itself carries the full longhand set (all four sides, etc.) as richer measured facts.
_COMPUTED_ASPECTS: dict[str, tuple[str, str]] = {
    # palette
    "palette.color": ("palette", "color"),
    "palette.background": ("palette", "background-color"),
    "palette.border-color": ("palette", "border-top-color"),
    # typography
    "type.font-family": ("type", "font-family"),
    "type.font-size": ("type", "font-size"),
    "type.font-weight": ("type", "font-weight"),
    "type.line-height": ("type", "line-height"),
    "type.letter-spacing": ("type", "letter-spacing"),
    "type.text-transform": ("type", "text-transform"),
    # spacing
    "spacing.margin": ("spacing", "margin-top"),
    "spacing.padding": ("spacing", "padding-top"),
    "spacing.gap": ("spacing", "row-gap"),
    # geometry
    "geometry.box": ("geometry", "width"),
    "geometry.display": ("geometry", "display"),
    "geometry.position": ("geometry", "position"),
    # radius
    "radius.border-radius": ("radius", "border-top-left-radius"),
    # border
    "border.width": ("border", "border-top-width"),
    "border.style": ("border", "border-top-style"),
    # shadow
    "shadow.box-shadow": ("shadow", "box-shadow"),
    "shadow.text-shadow": ("shadow", "text-shadow"),
    # material
    "material.backdrop-filter": ("material", "backdrop-filter"),
    "material.filter": ("material", "filter"),
    "material.opacity": ("material", "opacity"),
    # motion
    "motion.transition": ("motion", "transition-duration"),
    "motion.animation": ("motion", "animation-name"),
}
_STRUCTURE_ASPECTS: tuple[str, ...] = ("structure.tag", "structure.role", "structure.attributes")
_STATE_ASPECTS: dict[str, str] = {"state.hover": "hover", "state.focus": "focus", "state.active": "active"}

#: The closed §3.1 aspect vocabulary — 31 rendered-fact ids the probe can measure.
ASPECT_VOCABULARY: tuple[str, ...] = tuple(
    sorted(set(_COMPUTED_ASPECTS) | set(_STRUCTURE_ASPECTS) | set(_STATE_ASPECTS))
)

#: Aspect ids grouped by family (documentation / callers).
ASPECT_FAMILIES: dict[str, tuple[str, ...]] = {
    family: tuple(sorted(a for a in ASPECT_VOCABULARY if a.split(".")[0] == family))
    for family in ("palette", "type", "spacing", "geometry", "radius", "border", "shadow",
                   "material", "motion", "structure", "state")
}


def chrome_available() -> bool:
    """True iff the local Chrome binary this probe drives is present."""
    return CHROME.is_file()


# --- forced-pseudo CSS rewrite -----------------------------------------------------------------
# A foreign page has no way to be "hovered" in a headless dump, so we rewrite the SERVED copy: every
# selector carrying :hover/:focus/:active gets a parallel marker-class selector, and the probe toggles
# that class on a subject to sample the pseudo-state's computed vector. Limitation (documented): only
# pseudos ON the subject element are reachable this way (a parent `.card:hover .btn` effect is not),
# and :focus-visible / :focus-within are left untouched.
_PSEUDO_MARKERS: tuple[tuple[str, str], ...] = (
    (":hover", "__probe_force_hover"),
    (":focus", "__probe_force_focus"),
    (":active", "__probe_force_active"),
)
_NO_ANIM_CLASS = "__probe_no_anim"
# A CSS transition would capture the STARTING frame of a state change (a synchronous read right after
# toggling the marker sees the pre-transition value); this rule, applied only during state sampling,
# makes the pseudo-state's steady value land instantly. It does NOT touch rest measurement, so the
# motion family's transition/animation descriptors stay honest.
_PROBE_STYLE_TAG = (
    f'<style id="__probe_style">.{_NO_ANIM_CLASS}, .{_NO_ANIM_CLASS} * '
    "{ transition: none !important; animation: none !important; }</style>"
)
_RULE_HEADER = re.compile(r"([^{}]+)\{")
_CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_STYLE_BLOCK = re.compile(r"(<style\b[^>]*>)(.*?)(</style>)", re.IGNORECASE | re.DOTALL)


def _forced_selectors(selector_list: str) -> list[str]:
    parts = [p.strip() for p in selector_list.split(",") if p.strip()]
    forced: list[str] = []
    for pseudo, marker in _PSEUDO_MARKERS:
        pat = re.compile(re.escape(pseudo) + r"(?![\w-])")
        for part in parts:
            if pat.search(part):
                forced.append(pat.sub("." + marker, part))
    # stable, de-duplicated (a selector already emitted for one pseudo isn't emitted twice).
    seen: set[str] = set()
    uniq: list[str] = []
    for sel in forced:
        if sel not in seen:
            seen.add(sel)
            uniq.append(sel)
    return uniq


def _rewrite_rule_header(match: re.Match) -> str:
    header = match.group(1)
    forced = _forced_selectors(header)  # @media/@supports/@keyframes preludes carry no pseudo → []
    if not forced:
        return match.group(0)
    return header.rstrip() + ", " + ", ".join(forced) + " {"


def _force_states_in_css(css: str) -> str:
    # Strip CSS comments FIRST: a comment that happens to contain ':hover'/':focus'/':active'
    # (e.g. a rule's doc-comment) would otherwise be swept into the next rule header by the
    # selector-list regex and corrupt the stylesheet. Comments are non-semantic to rendering.
    css = _CSS_COMMENT.sub("", css)
    return _RULE_HEADER.sub(_rewrite_rule_header, css)


def _force_states_in_html(html_text: str) -> str:
    return _STYLE_BLOCK.sub(
        lambda m: m.group(1) + _force_states_in_css(m.group(2)) + m.group(3), html_text
    )


def _inject_probe_style(html_text: str) -> str:
    """Insert the no-animation helper stylesheet into a served page's head (or body)."""
    lowered = html_text.lower()
    head = lowered.rfind("</head>")
    if head != -1:
        return html_text[:head] + _PROBE_STYLE_TAG + html_text[head:]
    body = lowered.find("<body")
    if body != -1:
        gt = html_text.find(">", body)
        if gt != -1:
            return html_text[: gt + 1] + _PROBE_STYLE_TAG + html_text[gt + 1:]
    return _PROBE_STYLE_TAG + html_text


def _rewrite_served_copy(served: Path) -> None:
    for css in served.rglob("*.css"):
        css.write_text(_force_states_in_css(css.read_text(encoding="utf-8")), encoding="utf-8")
    for page in served.rglob("*.html"):
        text = _force_states_in_html(page.read_text(encoding="utf-8"))
        page.write_text(_inject_probe_style(text), encoding="utf-8")


# --- the host probe page (STATIC — target/viewport arrive via URL query, so it is byte-stable) --
# Same-origin with the served target (both http://127.0.0.1:<port>/…), so the host reads the iframe's
# contentDocument without any file-access flag. The measurement JS builds a fixed-key-order object;
# Python re-serializes with sort_keys, so the packet is deterministic regardless of JS key order.
_HOST_HTML = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>rendered-facts probe host</title></head>
<body style="margin:0">
<script>
(function () {
  "use strict";
  var params = new URLSearchParams(window.location.search);
  var target = params.get("target");
  var vw = parseInt(params.get("vw"), 10);
  var vh = parseInt(params.get("vh"), 10);

  var FAMILIES = {
    "palette": {
      "color": "color", "background-color": "backgroundColor",
      "background-image": "backgroundImage", "border-top-color": "borderTopColor"
    },
    "type": {
      "font-family": "fontFamily", "font-size": "fontSize", "font-weight": "fontWeight",
      "line-height": "lineHeight", "letter-spacing": "letterSpacing", "text-transform": "textTransform"
    },
    "spacing": {
      "margin-top": "marginTop", "margin-right": "marginRight",
      "margin-bottom": "marginBottom", "margin-left": "marginLeft",
      "padding-top": "paddingTop", "padding-right": "paddingRight",
      "padding-bottom": "paddingBottom", "padding-left": "paddingLeft",
      "row-gap": "rowGap", "column-gap": "columnGap"
    },
    "geometry": { "display": "display", "position": "position", "box-sizing": "boxSizing" },
    "radius": {
      "border-top-left-radius": "borderTopLeftRadius", "border-top-right-radius": "borderTopRightRadius",
      "border-bottom-right-radius": "borderBottomRightRadius", "border-bottom-left-radius": "borderBottomLeftRadius"
    },
    "border": {
      "border-top-width": "borderTopWidth", "border-right-width": "borderRightWidth",
      "border-bottom-width": "borderBottomWidth", "border-left-width": "borderLeftWidth",
      "border-top-style": "borderTopStyle", "border-right-style": "borderRightStyle",
      "border-bottom-style": "borderBottomStyle", "border-left-style": "borderLeftStyle"
    },
    "shadow": { "box-shadow": "boxShadow", "text-shadow": "textShadow" },
    "material": {
      "backdrop-filter": "backdropFilter", "webkit-backdrop-filter": "webkitBackdropFilter",
      "filter": "filter", "opacity": "opacity"
    },
    "motion": {
      "transition-property": "transitionProperty", "transition-duration": "transitionDuration",
      "transition-timing-function": "transitionTimingFunction", "transition-delay": "transitionDelay",
      "animation-name": "animationName", "animation-duration": "animationDuration",
      "transform": "transform"
    }
  };
  var ATTRS = ["href", "type", "role", "aria-label", "aria-current", "aria-hidden", "alt",
               "title", "name", "for", "disabled", "target", "rel", "value", "placeholder"];
  var IMPLICIT_ROLE = {
    a: "link", nav: "navigation", header: "banner", footer: "contentinfo", main: "main",
    aside: "complementary", button: "button", h1: "heading", h2: "heading", h3: "heading",
    h4: "heading", h5: "heading", h6: "heading"
  };
  var MAX_PER_KIND = 16;

  function round2(x) { return Math.round(x * 100) / 100; }
  function tokens(el) {
    return (el.getAttribute("class") || "").split(/\s+/).filter(Boolean).sort();
  }
  function implicitRole(el) {
    var tag = el.tagName.toLowerCase();
    if (tag === "a" && !el.hasAttribute("href")) return "";
    return IMPLICIT_ROLE[tag] || "";
  }
  function domPath(el) {
    var parts = [], n = el;
    while (n && n.parentElement) {
      parts.unshift(Array.prototype.indexOf.call(n.parentElement.children, n));
      n = n.parentElement;
    }
    return parts.join("/");
  }
  function selectorOf(el) {
    var s = el.tagName.toLowerCase();
    if (el.id) s += "#" + el.id;
    var cls = tokens(el);
    if (cls.length) s += "." + cls.join(".");
    return s;
  }
  function familyVector(win, el) {
    var cs = win.getComputedStyle(el), out = {};
    Object.keys(FAMILIES).forEach(function (fam) {
      var props = FAMILIES[fam], d = {};
      Object.keys(props).forEach(function (k) {
        var v = cs[props[k]];
        d[k] = (v === undefined || v === null) ? "" : String(v);
      });
      out[fam] = d;
    });
    var r = el.getBoundingClientRect();
    out.geometry.width = round2(r.width) + "px";
    out.geometry.height = round2(r.height) + "px";
    return out;
  }
  function stateVectors(win, el) {
    var states = {};
    el.classList.add("__probe_no_anim");     // freeze transitions/animations so pseudo values land instantly
    void el.offsetWidth;
    [["hover", "__probe_force_hover"], ["focus", "__probe_force_focus"],
     ["active", "__probe_force_active"]].forEach(function (pair) {
      el.classList.add(pair[1]);
      void el.offsetWidth;                    // force a reflow so the pseudo cascade lands
      states[pair[0]] = familyVector(win, el);
      el.classList.remove(pair[1]);
    });
    el.classList.remove("__probe_no_anim");
    return states;
  }
  function structureOf(el) {
    var attrs = {};
    ATTRS.forEach(function (a) { if (el.hasAttribute(a)) attrs[a] = el.getAttribute(a); });
    return {
      tag: el.tagName.toLowerCase(),
      id: el.id || "",
      classes: tokens(el),
      role: el.getAttribute("role") || implicitRole(el) || "",
      attributes: attrs
    };
  }
  function q(doc, sel) { return Array.prototype.slice.call(doc.querySelectorAll(sel)); }
  function cardClusters(doc) {
    var out = [];
    q(doc, "*").forEach(function (el) {
      var kids = Array.prototype.filter.call(el.children, function (c) { return c.nodeType === 1; });
      if (kids.length < 2) return;
      var groups = {};
      kids.forEach(function (c) {
        if (!(c.getAttribute("class") || "").trim()) return;  // require a shared class (anti over-match)
        var key = c.tagName.toLowerCase() + "|" + tokens(c).join(".");
        groups[key] = (groups[key] || 0) + 1;
      });
      var max = 0;
      Object.keys(groups).forEach(function (k) { if (groups[k] > max) max = groups[k]; });
      if (max >= 2) out.push(el);
    });
    return out;
  }
  function findSubjects(doc) {
    var claimed = [], subjects = [], counts = {};
    function add(kind, el) {
      if (claimed.indexOf(el) !== -1) return;
      counts[kind] = (counts[kind] || 0);
      if (counts[kind] >= MAX_PER_KIND) return;
      counts[kind]++;
      claimed.push(el);
      subjects.push({ kind: kind, el: el });
    }
    q(doc, "button, [role=button], input[type=button], input[type=submit], input[type=reset], .btn")
      .forEach(function (el) { add("button", el); });
    q(doc, "a[href]").forEach(function (el) { add("link", el); });
    q(doc, "nav, header, footer, main, aside, [role=navigation], [role=banner], [role=contentinfo], "
         + "[role=main], [role=complementary], [role=region]").forEach(function (el) { add("landmark", el); });
    cardClusters(doc).forEach(function (el) { add("card-cluster", el); });
    q(doc, "h1, h2, h3, h4, h5, h6").forEach(function (el) { add("heading-tuple", el); });
    return subjects;
  }

  function emit(obj) {
    var pre = document.createElement("pre");
    pre.id = "probe-facts-json";
    pre.textContent = JSON.stringify(obj);
    document.body.innerHTML = "";
    document.body.appendChild(pre);
  }

  var done = false;
  function measure() {
    if (done) return;
    var frame = document.getElementById("target");
    var doc = frame && frame.contentDocument;
    var win = frame && frame.contentWindow;
    if (!doc || !doc.body || !win) { window.setTimeout(measure, 100); return; }
    done = true;
    try {
      var clientWidth = doc.documentElement.clientWidth || vw;
      var found = findSubjects(doc);
      var subjects = found.map(function (rec) {
        var el = rec.el;
        return {
          id: rec.kind + ":" + domPath(el),
          kind: rec.kind,
          dom_path: domPath(el),
          selector: selectorOf(el),
          structure: structureOf(el),
          computed: familyVector(win, el),
          states: stateVectors(win, el)
        };
      });
      emit({ client_width: clientWidth, subjects: subjects });
    } catch (err) {
      emit({ error: String(err && err.stack || err) });
    }
  }

  var iframe = document.createElement("iframe");
  iframe.id = "target";
  iframe.setAttribute("scrolling", "no");
  iframe.style.cssText = "width:" + vw + "px;height:" + vh + "px;border:0";
  iframe.addEventListener("load", function () {
    requestAnimationFrame(function () { requestAnimationFrame(measure); });
  });
  iframe.src = target;
  document.body.appendChild(iframe);
  window.setTimeout(measure, 1500);
}());
</script>
</body></html>
"""


def _present(subject: dict, aspect: str) -> bool:
    if aspect in _COMPUTED_ASPECTS:
        family, key = _COMPUTED_ASPECTS[aspect]
        value = subject.get("computed", {}).get(family, {}).get(key)
        return isinstance(value, str) and value != ""
    if aspect == "structure.tag":
        return bool(subject.get("structure", {}).get("tag"))
    if aspect == "structure.role":
        return bool(subject.get("structure", {}).get("role"))
    if aspect == "structure.attributes":
        return bool(subject.get("structure", {}).get("attributes"))
    state = _STATE_ASPECTS.get(aspect)
    if state is not None:
        return bool(subject.get("states", {}).get(state))
    return False


def _aspects_measured(subjects: list[dict]) -> list[str]:
    """The §3.1 ids GENUINELY populated by at least one subject — an honest coverage list."""
    return sorted(a for a in ASPECT_VOCABULARY if any(_present(s, a) for s in subjects))


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep the probe silent + deterministic
        return


class _LoopbackServer:
    """Serve `directory` on an ephemeral 127.0.0.1 port in a background thread."""

    def __init__(self, directory: Path) -> None:
        handler = functools.partial(_QuietHandler, directory=str(directory))
        self._httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    def __enter__(self) -> "_LoopbackServer":
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join(timeout=5)


def _pick_target(src: Path, target: str | None) -> str:
    if target is not None:
        if not (src / target).is_file():
            raise FileNotFoundError(f"target page not found in {src}: {target}")
        return target
    if (src / "index.html").is_file():
        return "index.html"
    pages = sorted(p.relative_to(src).as_posix() for p in src.rglob("*.html"))
    if not pages:
        raise FileNotFoundError(f"no .html page found under {src}")
    return pages[0]


def _chrome_version() -> str:
    proc = subprocess.run([str(CHROME), "--version"], check=True, capture_output=True, text=True)
    return proc.stdout.strip()


def _run_chrome(url: str, host_w: int, host_h: int) -> str:
    command = [
        str(CHROME),
        "--headless=new",
        "--no-first-run",
        "--no-default-browser-check",
        "--hide-scrollbars",
        "--virtual-time-budget=5000",
        "--dump-dom",
        f"--window-size={host_w},{host_h}",
        url,
    ]
    # fail-closed: a hung Chrome is an ERROR, never an infinite wait.
    proc = subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
    return proc.stdout


def _parse_facts(dump: str) -> dict:
    match = re.search(rf'<pre id="{_FACTS_PRE_ID}">(?P<payload>.*?)</pre>', dump, flags=re.S)
    if not match:
        raise RuntimeError("Chrome DOM dump did not contain the rendered-facts payload")
    return json.loads(html.unescape(match.group("payload")))


def probe(
    html_dir: Path | str,
    *,
    target: str | None = None,
    viewport: tuple[int, int] = (1024, 768),
) -> dict:
    """Measure the rendered facts of a served page and return the closed facts packet.

    ``html_dir`` is served (a rewritten copy) on an ephemeral loopback port; ``target`` selects the
    page (defaults to ``index.html`` or the first ``*.html``). ``viewport`` is the exact CSS-pixel
    layout viewport enforced via the iframe. Raises :class:`ChromeUnavailable` if Chrome is missing
    (never fabricates), and fails closed if the measured client width != the declared viewport.
    """
    if not chrome_available():
        raise ChromeUnavailable(f"Chrome binary not found: {CHROME}")
    src = Path(html_dir)
    if not src.is_dir():
        raise NotADirectoryError(f"not a directory: {src}")
    vw, vh = int(viewport[0]), int(viewport[1])
    page = _pick_target(src, target)

    with tempfile.TemporaryDirectory(prefix="reference-probe-") as tmp:
        served = Path(tmp) / "served"
        shutil.copytree(src, served)
        _rewrite_served_copy(served)
        (served / HOST_FILENAME).write_text(_HOST_HTML, encoding="utf-8")

        with _LoopbackServer(served) as server:
            # HOST window must exceed the iframe (CLI ~500px floor); the iframe IS the viewport.
            host_w = max(vw + 80, 900)
            host_h = vh + 120
            url = (f"http://127.0.0.1:{server.port}/{HOST_FILENAME}"
                   f"?target={page}&vw={vw}&vh={vh}")
            dump = _run_chrome(url, host_w, host_h)

    raw = _parse_facts(dump)
    if "error" in raw:
        raise RuntimeError(f"in-page measurement failed (no facts fabricated): {raw['error']}")
    if raw.get("client_width") != vw:
        raise RuntimeError(
            f"probe measured client_width={raw.get('client_width')} != declared viewport {vw} — "
            "refusing to write an over-claiming packet")

    subjects = sorted(raw.get("subjects", []), key=lambda s: s["id"])
    return {
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "viewport": {"width": vw, "height": vh},
        "subjects": subjects,
        "aspects_measured": _aspects_measured(subjects),
    }


def canonical_json(packet: dict) -> str:
    """Deterministic, gzip-safe serialization: sorted keys, stable spacing, trailing newline."""
    return json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_dir", help="directory of HTML to serve and probe")
    parser.add_argument("--target", default=None, help="page to probe (default: index.html / first)")
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=768)
    args = parser.parse_args(argv)

    packet = probe(args.html_dir, target=args.target, viewport=(args.width, args.height))
    print(canonical_json(packet), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
