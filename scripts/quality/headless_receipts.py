"""Chrome-headless page receipts for visible layout slices.

MF1 requires real browser receipts for pages whose layout changed: a 1280px screenshot and a 390px
DOM overflow probe, both with honest provenance sidecars. This producer shells the local Google
Chrome binary directly and fails closed if Chrome is unavailable.
"""
from __future__ import annotations

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
    payload = {
        "contract_id": "PageHeadlessReceiptProvenance",
        "page": page,
        "route": PAGE_ROUTES[page],
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
    source = route.read_text(encoding="utf-8")
    base = f'<base href="{(_root() / "site").as_uri()}/">'
    if re.search(r"<head[^>]*>", source, flags=re.I):
        source = re.sub(r"(<head[^>]*>)", r"\1" + base, source, count=1, flags=re.I)
    else:
        source = base + source
    script = f"""
<script>
(function () {{
  var done = false;
  function cls(el) {{
    return String(el.className || "").replace(/\\s+/g, " ").trim();
  }}
  function probe() {{
    if (done) return;
    done = true;
    var root = document.documentElement;
    var body = document.body;
    var clientWidth = root.clientWidth || window.innerWidth || {viewport};
    var bodyScrollWidth = body ? body.scrollWidth : 0;
    var scrollWidth = Math.max(root.scrollWidth || 0, bodyScrollWidth);
    var offenders = [];
    Array.prototype.forEach.call(document.querySelectorAll("*"), function (el) {{
      var style = window.getComputedStyle(el);
      if (style.display === "none" || style.visibility === "hidden") return;
      var rect = el.getBoundingClientRect();
      if (!rect || (rect.width === 0 && rect.height === 0)) return;
      var overLeft = Math.max(0, -rect.left);
      var overRight = Math.max(0, rect.right - clientWidth);
      if (overLeft > 1 || overRight > 1) {{
        offenders.push({{
          "tag": el.tagName.toLowerCase(),
          "id": el.id || "",
          "class": cls(el),
          "left": Math.round(rect.left * 100) / 100,
          "right": Math.round(rect.right * 100) / 100,
          "width": Math.round(rect.width * 100) / 100,
          "overflow_px": Math.round(Math.max(overLeft, overRight) * 100) / 100
        }});
      }}
    }});
    var overflowPx = Math.max(0, scrollWidth - clientWidth);
    var result = {{
      "contract_id": "PageHeadlessDomProbe",
      "page": "{page}",
      "route": "{PAGE_ROUTES[page]}",
      "kind": "{DOM_PROBE_KIND}",
      "viewport": {{"width": {viewport}, "height": {height}}},
      "client_width": clientWidth,
      "scroll_width": scrollWidth,
      "body_scroll_width": bodyScrollWidth,
      "horizontal_overflow": overflowPx > 1,
      "overflow_px": overflowPx,
      "offenders": offenders.slice(0, 20),
      "authority_status": "candidate_only",
      "cannot_mark_done": true
    }};
    document.documentElement.innerHTML = "<head><title>probe</title></head><body><pre id=\\"headless-probe-json\\"></pre></body>";
    document.getElementById("headless-probe-json").textContent = JSON.stringify(result);
  }}
  window.addEventListener("load", function () {{
    requestAnimationFrame(function () {{ requestAnimationFrame(probe); }});
  }});
  window.setTimeout(probe, 500);
}}());
</script>
"""
    if re.search(r"</body\s*>", source, flags=re.I):
        # lambda replacement: the script body contains backslash escapes (e.g. /\s+/) that would
        # be misread as template escapes by a plain-string repl
        return re.sub(r"</body\s*>", lambda _m: script + "</body>", source, count=1, flags=re.I)
    return source + script


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
            f"--window-size={viewport},{height}",
            "--virtual-time-budget=1500",
            "--dump-dom",
            probe_file.as_uri(),
        ]
        proc = _run(command)
    payload = _parse_probe_dump(proc.stdout)
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
