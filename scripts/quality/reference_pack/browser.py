"""Chrome transport for approved rendered-reference packs.

The browser lane is deliberately separate from manifest/schema code. It renders a frozen
HTML+fixture pair through an iframe whose CSS viewport is exact even when Chrome enforces a
larger minimum native window.
"""
from __future__ import annotations

import html
import http.server
import json
import re
import shutil
import subprocess
import threading
from contextlib import contextmanager
from functools import partial
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse


CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


class _FactsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._active = False
        self._parts: list[str] = []
        self.payloads: list[dict] = []

    def handle_starttag(self, tag, attrs):  # noqa: ANN001 - HTMLParser callback
        if tag == "script" and dict(attrs).get("id") == "reference-facts":
            self._active = True
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._active:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._active:
            self.payloads.append(json.loads("".join(self._parts)))
            self._active = False


def _host_html(theme: str, width: int, height: int) -> str:
    target = "/site/index.html?" + urlencode({"theme": theme})
    config = json.dumps({"theme": theme, "width": width, "height": height})
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>approved reference capture</title>
<style>html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:#000}}
iframe{{display:block;width:{width}px;height:{height}px;border:0}}</style></head>
<body><iframe id="target" data-src="{html.escape(target)}"></iframe>
<script>
(function () {{
  const config = {config};
  const frame = document.getElementById("target");
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const round = (value) => Math.round(value * 100) / 100;
  function rect(doc, selector) {{
    const node = doc.querySelector(selector);
    if (!node) return null;
    const box = node.getBoundingClientRect();
    return {{left:round(box.left),top:round(box.top),right:round(box.right),bottom:round(box.bottom),
      width:round(box.width),height:round(box.height)}};
  }}
  function paint(win, doc, selector) {{
    const node = doc.querySelector(selector);
    if (!node) return null;
    const css = win.getComputedStyle(node);
    return {{background_color:css.backgroundColor,border_color:css.borderColor,
      border_width:css.borderWidth,border_radius:css.borderRadius,box_shadow:css.boxShadow,
      backdrop_filter:css.backdropFilter || css.webkitBackdropFilter || "none"}};
  }}
  async function run() {{
    for (let attempt = 0; attempt < 120; attempt += 1) {{
      const doc = frame.contentDocument;
      const value = doc && doc.querySelector('[data-bind="snapshot.last_year_contributions"]');
      if (value && value.textContent.trim() !== "—") break;
      await sleep(50);
    }}
    const win = frame.contentWindow;
    const doc = frame.contentDocument;
    await sleep(100);
    const root = doc.documentElement;
    const style = win.getComputedStyle(root);
    const tokenNames = ["--accent","--backdrop","--surface","--surface-raised","--hairline",
      "--ink-strong","--ink","--ink-dim","--radius-panel","--radius-tile"];
    const tokens = Object.fromEntries(tokenNames.map((name) => [name, style.getPropertyValue(name).trim()]));
    const facts = {{
      contract_id:"ApprovedReferenceRenderedFacts",schema_version:1,
      theme:config.theme,observed_theme:root.dataset.theme,
      viewport:{{width:root.clientWidth,height:config.height}},hydrated:true,
      tokens:tokens,
      geometry:{{page:rect(doc,".wrap"),hero:rect(doc,".hero"),section:rect(doc,".panel:nth-of-type(1)"),
        selector:rect(doc,".switcher"),metric_group:rect(doc,".mgroup"),metric_row:rect(doc,".mrow")}},
      paint:{{hero:paint(win,doc,".hero"),section:paint(win,doc,".panel:nth-of-type(1)"),
        selector:paint(win,doc,".switcher"),metric_group:paint(win,doc,".mgroup"),
        metric_row:paint(win,doc,".mrow")}},
      selection:{{selector_count:doc.querySelectorAll(".switcher").length,
        selected_count:doc.querySelectorAll('.switcher [aria-pressed="true"]').length}}
    }};
    const marker = document.createElement("script");
    marker.id = "reference-facts";
    marker.type = "application/json";
    marker.textContent = JSON.stringify(facts);
    document.body.append(marker);
  }}
  frame.addEventListener("load", () => run().catch((error) => {{
    const marker = document.createElement("script");
    marker.id = "reference-facts";
    marker.type = "application/json";
    marker.textContent = JSON.stringify({{error:String(error)}});
    document.body.append(marker);
  }}));
  frame.src = frame.dataset.src;
}}());
</script></body></html>"""


class _ReferenceHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args) -> None:  # noqa: ANN001 - server callback
        return

    def do_GET(self) -> None:  # noqa: N802 - stdlib callback
        parsed = urlparse(self.path)
        if parsed.path != "/__capture__.html":
            super().do_GET()
            return
        try:
            query = parse_qs(parsed.query, strict_parsing=True)
            body = _host_html(query["theme"][0], int(query["width"][0]), int(query["height"][0]))
        except (KeyError, ValueError, IndexError) as exc:
            self.send_error(400, f"invalid capture query: {exc}")
            return
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


@contextmanager
def reference_server(directory: Path):
    handler = partial(_ReferenceHandler, directory=str(directory))
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


def chrome_version() -> str:
    if not CHROME.is_file():
        raise FileNotFoundError(f"Chrome binary not found: {CHROME}")
    return subprocess.run(
        [str(CHROME), "--version"], check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()


def capture(*, base_url: str, theme: str, width: int, height: int, screenshot: Path) -> tuple[dict, list[str]]:
    """Capture one exact iframe viewport and return rendered facts plus the real command."""
    raw = screenshot.with_name(f"{screenshot.name}.raw.png")
    query = urlencode({"theme": theme, "width": width, "height": height})
    command = [
        str(CHROME), "--headless=new", "--no-first-run", "--no-default-browser-check",
        "--hide-scrollbars", "--run-all-compositor-stages-before-draw",
        f"--window-size={max(500, width)},{height}", "--virtual-time-budget=15000",
        "--dump-dom", f"--screenshot={raw}", f"{base_url}/__capture__.html?{query}",
    ]
    proc = subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
    parser = _FactsParser()
    parser.feed(proc.stdout)
    parser.close()
    if len(parser.payloads) != 1 or parser.payloads[0].get("error"):
        raise RuntimeError(f"reference capture did not publish one facts packet: {parser.payloads!r}")
    facts = parser.payloads[0]
    if facts.get("observed_theme") != theme or facts.get("viewport", {}).get("width") != width:
        raise RuntimeError("reference capture theme/viewport mismatch")
    if width < 500:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg is required to crop Chrome's minimum window to an exact mobile viewport")
        subprocess.run(
            [ffmpeg, "-loglevel", "error", "-y", "-i", str(raw),
             "-vf", f"crop={width}:{height}:0:0", str(screenshot)],
            check=True, capture_output=True, text=True, timeout=30,
        )
        raw.unlink()
    else:
        raw.replace(screenshot)
    return facts, command
