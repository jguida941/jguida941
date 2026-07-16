"""W6-C §4 — the universal engine's CAPTURE ladder.

Four rungs turn a live reference page into a frozen, measurable, rights-tracked local copy:

  (a) ``acquire(url)``      — Chrome ``--dump-dom`` + ``--screenshot`` per viewport. The live
                              artifacts are EVIDENCE ONLY (what the page really looked like);
                              they are never the thing we serve.
  (b) ``localize(dom, out)``— a stdlib ``HTMLParser`` pass that enumerates every external ref
                              (stylesheets, @import, url(), img, srcset, fonts), FETCHES each,
                              rewrites it to a content-addressed local path, and STRIPS every
                              <script> (recording the script policy). Each fetch failure becomes
                              a non-fatal ``capture_gaps[]`` row — capture never silently drops.
  (c) ``freeze(staging)``   — a deterministic, content-addressed tree + ``source_tree_sha256``;
                              two freezes of one staging tree are byte-identical.
  (d) ``serve_frozen(pack)``— serves the FROZEN tree on an ephemeral loopback port so the
                              restyle engine can measure it, as a context manager.

``build_candidate_record`` emits the W6-C §8 ReferenceCandidateRecord shape. The file:// path
needs no network; the live ``acquire`` rung needs Chrome and fails honestly without it.
candidate_only; decides no authority.
"""
from __future__ import annotations

import hashlib
import html
import json
import mimetypes
import re
import shutil
import subprocess
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urljoin, urlparse
from urllib.request import url2pathname

from scripts.quality.reference_intake.security import (
    CaptureLimits,
    CaptureRefused,
    assert_capture_allowed,
    check_response,
)


CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
_TOOL = "scripts/quality/reference_intake/capture.py"
_PRODUCER_VERSION = "reference-intake-capture/1"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------------------
# record shapes
# ---------------------------------------------------------------------------------------
@dataclass(frozen=True)
class CaptureGap:
    url: str
    reason: str
    stage: str

    def as_dict(self) -> dict:
        return {"url": self.url, "reason": self.reason, "stage": self.stage}


@dataclass(frozen=True)
class LocalizedAsset:
    url: str
    custody_id: str          # sha256 of the STORED bytes == the content address
    path: str                # staging-relative, e.g. "assets/<sha256>.css"
    content_type: str
    bytes: int


@dataclass
class LocalizeResult:
    index_path: Path
    assets: list[LocalizedAsset]
    gaps: list[CaptureGap]
    script_policy: dict
    base_url: str


@dataclass(frozen=True)
class FrozenPack:
    pack_dir: Path
    source_tree_sha256: str
    files: list[dict]


@dataclass
class LiveEvidence:
    url: str
    dom: str
    screenshots: list[dict]
    chrome_version: str
    commands: list[list[str]]
    captured_at: str


# ---------------------------------------------------------------------------------------
# (b) localize — enumerate + fetch + content-address + strip scripts + record gaps
# ---------------------------------------------------------------------------------------
# One combined pass over CSS: an @import (string OR url() form) takes precedence so a following
# bare url() branch can never re-localize an already-rewritten @import target.
_CSS_REF_RE = re.compile(
    r"@import\s+(?:url\(\s*)?(?P<iq>['\"]?)(?P<import>[^'\")]+)(?P=iq)\s*\)?"
    r"|url\(\s*(?P<uq>['\"]?)(?P<url>[^'\")]+)(?P=uq)\s*\)",
    re.IGNORECASE,
)
_SKIP_REF_PREFIXES = ("data:", "#", "javascript:", "mailto:", "tel:", "about:")


def _skip_ref(raw: str) -> bool:
    return not raw or raw.strip().lower().startswith(_SKIP_REF_PREFIXES)


def _make_default_fetch(base_url: str, limits: CaptureLimits) -> Callable[[str], tuple[bytes, str]]:
    """The default fetcher. file:// refs are permitted ONLY when the capture base is itself
    file:// (a local fixture/staging tree); a remote (http[s]) base may never reach for file://
    or a private host — each remote fetch re-passes the SSRF boundary."""
    allow_file = urlparse(base_url).scheme == "file"

    def fetch(url: str) -> tuple[bytes, str]:
        parsed = urlparse(url)
        if parsed.scheme == "file":
            if not allow_file:
                raise CaptureRefused(f"{url}: file:// ref refused for a remote capture", reason="scheme")
            path = Path(url2pathname(parsed.path))
            if not path.is_file():
                raise FileNotFoundError(url)
            data = path.read_bytes()
            return data, mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        if parsed.scheme in ("http", "https"):
            assert_capture_allowed(url, limits=limits)   # SSRF guard on every remote fetch
            import requests

            resp = requests.get(url, timeout=limits.timeout_s, stream=True)
            resp.raise_for_status()
            ctype = resp.headers.get("Content-Type", "application/octet-stream")
            clen = resp.headers.get("Content-Length")
            check_response(content_type=ctype, content_length=int(clen) if clen else None, limits=limits)
            chunks: list[bytes] = []
            total = 0
            for chunk in resp.iter_content(65536):
                total += len(chunk)
                if total > limits.max_bytes:
                    raise CaptureRefused(f"{url}: body exceeds max_bytes {limits.max_bytes}", reason="size")
                chunks.append(chunk)
            return b"".join(chunks), ctype
        raise CaptureRefused(f"{url}: unsupported scheme {parsed.scheme!r}", reason="scheme")

    return fetch


class _Session:
    def __init__(self, out_dir: Path, base_url: str, fetch: Callable[[str], tuple[bytes, str]]) -> None:
        self.out_dir = out_dir
        self.assets_dir = out_dir / "assets"
        self.base_url = base_url
        self.fetch = fetch
        self._html_cache: dict[str, str] = {}
        self._css_cache: dict[str, str] = {}
        self.assets: list[LocalizedAsset] = []
        self.gaps: list[CaptureGap] = []

    def _store(self, data: bytes, ext: str) -> tuple[str, str]:
        digest = _sha256(data)
        name = f"{digest}{ext}"
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        dest = self.assets_dir / name
        if not dest.exists():
            dest.write_bytes(data)
        return digest, name

    @staticmethod
    def _ext_for(resolved: str, content_type: str) -> str:
        suffix = Path(urlparse(resolved).path).suffix
        if suffix and len(suffix) <= 6:
            return suffix
        guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip() or "")
        return guessed or ".bin"

    def localize(self, raw: str, kind: str, *, base: Optional[str] = None, css_context: bool = False) -> str:
        """Fetch + content-address one ref, returning its local rewrite. On any fetch failure a
        capture_gap is recorded and the ORIGINAL ref is returned unchanged (honest, non-fatal)."""
        if _skip_ref(raw):
            return raw
        base = base or self.base_url
        resolved = urljoin(base, raw.strip())
        cache = self._css_cache if css_context else self._html_cache
        if resolved in cache:
            return cache[resolved]
        try:
            data, ctype = self.fetch(resolved)
        except Exception as exc:  # never fatal — a missing/blocked asset is a recorded gap
            self.gaps.append(CaptureGap(url=resolved, reason=f"{type(exc).__name__}: {exc}", stage="localize"))
            return raw
        if kind == "css":
            data = self._process_css(data, base=resolved).encode("utf-8")
            ctype = "text/css"
            ext = ".css"
        else:
            ext = self._ext_for(resolved, ctype)
        digest, name = self._store(data, ext)
        self.assets.append(LocalizedAsset(url=resolved, custody_id=digest,
                                          path=f"assets/{name}", content_type=ctype, bytes=len(data)))
        # inside CSS the sibling asset is same-dir; in HTML it lives under assets/
        ref = name if css_context else f"assets/{name}"
        cache[resolved] = ref
        return ref

    def _process_css(self, data: bytes, *, base: str) -> str:
        text = data.decode("utf-8", "replace")

        def repl(match: re.Match) -> str:
            imported = match.group("import")
            if imported is not None:
                raw = imported.strip()
                if _skip_ref(raw):
                    return match.group(0)
                kind = "css" if raw.split("?")[0].split("#")[0].endswith(".css") else "binary"
                return match.group(0).replace(raw, self.localize(raw, kind, base=base, css_context=True))
            raw = (match.group("url") or "").strip()
            if _skip_ref(raw):
                return match.group(0)
            return f"url({self.localize(raw, 'binary', base=base, css_context=True)})"

        return _CSS_REF_RE.sub(repl, text)

    def localize_srcset(self, value: str) -> str:
        out = []
        for candidate in value.split(","):
            candidate = candidate.strip()
            if not candidate:
                continue
            bits = candidate.split()
            out.append(" ".join([self.localize(bits[0], "binary")] + bits[1:]))
        return ", ".join(out)

    def rewrite_inline_style(self, value: str) -> str:
        return self._process_css(value.encode("utf-8"), base=self.base_url)


class _Localizer(HTMLParser):
    """Re-serializing parser: strips <script> wholesale, rewrites asset-bearing attributes to
    their localized refs, and passes everything else through unchanged."""

    _ASSET_LINK_RELS = {"stylesheet", "preload", "icon", "apple-touch-icon", "mask-icon", "shortcut"}

    def __init__(self, session: _Session) -> None:
        super().__init__(convert_charrefs=False)
        self.session = session
        self.out: list[str] = []
        self._script_depth = 0
        self.scripts_removed = 0

    # --- passthrough events ---
    def handle_decl(self, decl: str) -> None:
        self.out.append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        self.out.append(f"<?{data}>")

    def unknown_decl(self, data: str) -> None:
        self.out.append(f"<![{data}]>")

    def handle_comment(self, data: str) -> None:
        if not self._script_depth:
            self.out.append(f"<!--{data}-->")

    def handle_entityref(self, name: str) -> None:
        if not self._script_depth:
            self.out.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if not self._script_depth:
            self.out.append(f"&#{name};")

    def handle_data(self, data: str) -> None:
        if not self._script_depth:
            self.out.append(data)

    # --- element events ---
    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "script":
            self._script_depth += 1
            self.scripts_removed += 1
            return
        if self._script_depth:
            return
        self.out.append(self._emit(tag, attrs, close=False))

    def handle_startendtag(self, tag: str, attrs) -> None:
        if tag == "script":
            self.scripts_removed += 1
            return
        if self._script_depth:
            return
        self.out.append(self._emit(tag, attrs, close=True))

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            if self._script_depth:
                self._script_depth -= 1
            return
        if not self._script_depth:
            self.out.append(f"</{tag}>")

    def _emit(self, tag: str, attrs, *, close: bool) -> str:
        parts = [tag]
        for name, value in self._rewrite_attrs(tag, attrs):
            if value is None:
                parts.append(name)
            else:
                parts.append(f'{name}="{html.escape(value, quote=True)}"')
        inner = " ".join(parts)
        return f"<{inner}/>" if close else f"<{inner}>"

    def _rewrite_attrs(self, tag: str, attrs):
        rels = set()
        if tag == "link":
            rels = {r.lower() for r in (dict(attrs).get("rel") or "").split()}
        out = []
        for name, value in attrs:
            if value is not None:
                nl = name.lower()
                if tag == "link" and nl == "href" and rels & self._ASSET_LINK_RELS:
                    kind = "css" if "stylesheet" in rels else "binary"
                    value = self.session.localize(value, kind)
                elif nl == "src" and tag in ("img", "source", "video", "audio", "input", "track", "embed"):
                    value = self.session.localize(value, "binary")
                elif nl == "poster" and tag == "video":
                    value = self.session.localize(value, "binary")
                elif nl == "srcset":
                    value = self.session.localize_srcset(value)
                elif nl == "style":
                    value = self.session.rewrite_inline_style(value)
            out.append((name, value))
        return out


def localize(dom, out_dir, *, base_url: str, fetch=None, limits: Optional[CaptureLimits] = None) -> LocalizeResult:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    limits = limits or CaptureLimits()
    fetch = fetch or _make_default_fetch(base_url, limits)
    session = _Session(out_dir, base_url, fetch)

    text = dom.decode("utf-8") if isinstance(dom, (bytes, bytearray)) else str(dom)
    parser = _Localizer(session)
    parser.feed(text)
    parser.close()

    index_path = out_dir / "index.html"
    index_path.write_text("".join(parser.out), encoding="utf-8")
    script_policy = {
        "action": "stripped" if parser.scripts_removed else "none",
        "removed": parser.scripts_removed,
        "strategy": "drop-all-script-elements",
    }
    return LocalizeResult(index_path=index_path, assets=session.assets, gaps=session.gaps,
                          script_policy=script_policy, base_url=base_url)


# ---------------------------------------------------------------------------------------
# (c) freeze — deterministic content-addressed tree + source_tree_sha256
# ---------------------------------------------------------------------------------------
def freeze(staging_dir, pack_dir) -> FrozenPack:
    staging = Path(staging_dir)
    pack = Path(pack_dir)
    if pack.exists():
        shutil.rmtree(pack)
    pack.mkdir(parents=True, exist_ok=True)

    entries: list[tuple[str, str, int]] = []
    for src in sorted(p for p in staging.rglob("*") if p.is_file()):
        rel = src.relative_to(staging).as_posix()
        data = src.read_bytes()
        digest = _sha256(data)
        dest = pack / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        entries.append((rel, digest, len(data)))

    tree_line = "\n".join(f"{rel}:{digest}" for rel, digest, _ in entries)
    source_tree_sha256 = _sha256(tree_line.encode("utf-8"))
    files = [{"path": rel, "sha256": digest, "bytes": n} for rel, digest, n in entries]
    manifest = {
        "contract_id": "ReferenceFrozenPack",
        "source_tree_sha256": source_tree_sha256,
        "files": files,
        "authority_status": "candidate_only",
        "cannot_mark_done": True,
    }
    (pack / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return FrozenPack(pack_dir=pack, source_tree_sha256=source_tree_sha256, files=files)


# ---------------------------------------------------------------------------------------
# (d) serve_frozen — serve the FROZEN tree on an ephemeral loopback port (measurement only)
# ---------------------------------------------------------------------------------------
@dataclass(frozen=True)
class FrozenServer:
    base_url: str
    port: int

    def url_for(self, rel_path: str) -> str:
        return self.base_url + rel_path.lstrip("/")


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:  # keep the measurement server silent
        pass


@contextmanager
def serve_frozen(pack_dir):
    pack = Path(pack_dir)
    handler = partial(_QuietHandler, directory=str(pack))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield FrozenServer(base_url=f"http://127.0.0.1:{port}/", port=port)
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
        httpd.server_close()


# ---------------------------------------------------------------------------------------
# (a) acquire — live evidence via Chrome (fails honestly when Chrome is absent)
# ---------------------------------------------------------------------------------------
def chrome_available() -> bool:
    return CHROME.is_file()


def _chrome() -> Path:
    if not CHROME.is_file():
        raise FileNotFoundError(f"Chrome binary not found: {CHROME}")
    return CHROME


def acquire(url: str, viewports=(1280, 390), *, out_dir=None, chrome=None) -> LiveEvidence:
    """Capture live EVIDENCE of the target — a DOM dump and a screenshot per viewport. These
    are never served; they record what the page really looked like. Requires Chrome."""
    chrome = Path(chrome) if chrome else _chrome()
    version = subprocess.run([str(chrome), "--version"], check=True, capture_output=True, text=True).stdout.strip()
    out = Path(out_dir or tempfile.mkdtemp(prefix="w6c-acquire-"))
    out.mkdir(parents=True, exist_ok=True)

    dump_cmd = [
        str(chrome), "--headless=new", "--no-first-run", "--no-default-browser-check",
        "--allow-file-access-from-files", "--virtual-time-budget=2500", "--dump-dom", url,
    ]
    dom = subprocess.run(dump_cmd, check=True, capture_output=True, text=True, timeout=120).stdout
    commands = [dump_cmd]
    screenshots: list[dict] = []
    for width in viewports:
        height = max(900, round(width * 1.2))
        shot = out / f"screenshot-{width}.png"
        shot_cmd = [
            str(chrome), "--headless=new", "--no-first-run", "--no-default-browser-check",
            "--hide-scrollbars", "--allow-file-access-from-files",
            f"--window-size={width},{height}", f"--screenshot={shot}", url,
        ]
        subprocess.run(shot_cmd, check=True, capture_output=True, text=True, timeout=120)
        commands.append(shot_cmd)
        if shot.is_file() and shot.stat().st_size > 0:
            screenshots.append({
                "viewport": width,
                "path": str(shot),
                "sha256": _sha256(shot.read_bytes()),
                "bytes": shot.stat().st_size,
            })
    return LiveEvidence(url=url, dom=dom, screenshots=screenshots, chrome_version=version,
                        commands=commands, captured_at=_now_iso())


# ---------------------------------------------------------------------------------------
# §8 — the ReferenceCandidateRecord (origin/producer/source/rights/capture/status)
# ---------------------------------------------------------------------------------------
def build_candidate_record(
    *,
    origin: str,
    source_url: str,
    localize_result: LocalizeResult,
    staging_tree_sha256: str,
    robots: Optional[dict] = None,
    live_evidence: Optional[LiveEvidence] = None,
    fetched_at: Optional[str] = None,
    command: Optional[list[str]] = None,
    redistribution: str = "review-only",
    retention: str = "session-ephemeral",
) -> dict:
    robots = robots or {"checked": False, "allowed": True, "override": False}
    rights = [
        {
            "publication": asset.url,
            "custody_id": asset.custody_id,
            "redistribution": redistribution,
            "retention": retention,
        }
        for asset in localize_result.assets
    ]
    live = None
    if live_evidence is not None:
        live = {
            "dom_sha256": _sha256(live_evidence.dom.encode("utf-8")),
            "screenshots": live_evidence.screenshots,
            "chrome_version": live_evidence.chrome_version,
            "captured_at": live_evidence.captured_at,
        }
    return {
        "contract_id": "ReferenceCandidateRecord",
        "origin": origin,
        "producer": {"tool": _TOOL, "version": _PRODUCER_VERSION, "command": command or []},
        "source": {"url": source_url, "fetched_at": fetched_at or _now_iso(), "robots": robots},
        "rights": rights,
        "capture": {
            "live_evidence": live,
            "staging_tree_sha256": staging_tree_sha256,
            "gaps": [gap.as_dict() for gap in localize_result.gaps],
        },
        "script_policy": localize_result.script_policy,
        "status": "candidate_only",
        "authority_status": "candidate_only",
        "cannot_mark_done": True,
    }
