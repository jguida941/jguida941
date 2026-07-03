"""Chrome-headless page receipts for visible layout slices.

MF1 requires real browser receipts for pages whose layout changed: a 1280px screenshot and a 390px
DOM overflow probe, both with honest provenance sidecars. This producer shells the local Google
Chrome binary directly and fails closed if Chrome is unavailable.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import tempfile
from pathlib import Path


CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
SCREENSHOT_KIND = "chrome-headless-screenshot"
DOM_PROBE_KIND = "chrome-headless-dom-probe"
PAGE_ROUTES = {
    "index": "site/index.html",
    "showcase": "site/showcase.html",
    "settings": "site/settings.html",
    "studio": "site/studio.html",
}
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
        var scroller = el.closest ? el.closest(".table-scroll") : null;
        var scrollInfo = null;
        var contained = false;
        if (scroller && scroller !== el) {{
          var scrollStyle = frame.contentWindow.getComputedStyle(scroller);
          var scrollRect = scroller.getBoundingClientRect();
          var inViewport = scrollRect.left >= -1 && scrollRect.right <= clientWidth + 1;
          scrollInfo = {{
            "tag": scroller.tagName.toLowerCase(),
            "id": scroller.id || "",
            "class": cls(scroller),
            "left": Math.round(scrollRect.left * 100) / 100,
            "right": Math.round(scrollRect.right * 100) / 100,
            "width": Math.round(scrollRect.width * 100) / 100,
            "overflow_x": scrollStyle.overflowX,
            "in_viewport": inViewport
          }};
          contained = cls(scroller).split(" ").indexOf("table-scroll") !== -1
            && scrollStyle.overflowX === "auto"
            && inViewport
            && scrollRect.width > 1;
        }}
        offenders.push({{
          "tag": el.tagName.toLowerCase(),
          "id": el.id || "",
          "class": cls(el),
          "left": Math.round(rect.left * 100) / 100,
          "right": Math.round(rect.right * 100) / 100,
          "width": Math.round(rect.width * 100) / 100,
          "overflow_px": Math.round(Math.max(overLeft, overRight) * 100) / 100,
          "contained_by_table_scroll": contained,
          "scroll_container": scrollInfo
        }});
      }}
    }});
    var overflowPx = Math.max(0, scrollWidth - clientWidth);
    var uncontained = offenders.filter(function (o) {{ return o.contained_by_table_scroll !== true; }});
    var result = {{
      "contract_id": "PageHeadlessDomProbe",
      "page": "{page}",
      "route": "{PAGE_ROUTES[page]}",
      "kind": "{DOM_PROBE_KIND}",
      "viewport": {{"width": {viewport}, "height": {height}}},
      "client_width": clientWidth,
      "scroll_width": scrollWidth,
      "body_scroll_width": bodyScrollWidth,
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
    match = re.search(r'<pre id="headless-probe-json">(?P<payload>.*?)</pre>', dump, flags=re.S)
    if not match:
        raise RuntimeError("Chrome DOM dump did not contain the headless probe payload")
    return json.loads(html.unescape(match.group("payload")))


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
    return out


def main() -> None:
    for path in write_all_page_receipts():
        print(path.relative_to(_root()))


if __name__ == "__main__":
    main()
