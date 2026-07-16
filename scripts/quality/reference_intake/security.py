"""W6-C §5 — the URL security boundary for reference capture.

Capture points a fetcher at an operator-supplied URL, so it is an SSRF surface. This
module is the fail-closed gate every acquire/fetch must pass through:

  * PUBLIC, UNAUTHENTICATED http(s) ONLY — no file:/ftp:/data:, no ``user:pass@`` creds;
  * DENY private / loopback / link-local / reserved hosts (10./127./169.254./192.168./
    ::1/localhost and the rest of the private space), whether given as a literal IP, a
    ``*.localhost`` name, or a hostname that RESOLVES into that space — AND deny redirects
    that land there;
  * size / time / MIME response limits;
  * a robots.txt verdict via ``urllib.robotparser`` (an operator override is RECORDED, never
    silent).

``assert_capture_allowed`` raises :class:`CaptureRefused` on any violation and otherwise
returns a :class:`CaptureAllowance` recording the decision (host, ip, robots verdict, limits)
so the caller can embed it in the capture record. Resolver + robots data are INJECTABLE so
the boundary is testable with no real DNS or network. candidate_only; decides no authority.
"""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional, Sequence
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser


DEFAULT_USER_AGENT = "w6c-reference-intake"
_PUBLIC_SCHEMES = ("http", "https")


class CaptureRefused(Exception):
    """The capture boundary refused a URL. ``reason`` is a short machine code."""

    def __init__(self, message: str, *, reason: str = "policy") -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class CaptureLimits:
    max_bytes: int = 25 * 1024 * 1024
    timeout_s: float = 20.0
    # a captured page's OWN bytes are markup/style/media/fonts — never an executable payload
    allowed_mime_prefixes: tuple[str, ...] = ("text/", "image/", "font/", "application/font")


@dataclass(frozen=True)
class CaptureAllowance:
    allowed: bool
    url: str
    host: str
    ip: Optional[str]
    robots: dict
    limits: CaptureLimits = field(default_factory=CaptureLimits)


Resolver = Callable[[str], Iterable[str]]


def _default_resolver(host: str) -> list[str]:
    return [info[4][0] for info in socket.getaddrinfo(host, None)]


def _as_ip(value: str):
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


def _deny_if_non_public(ip, url: str) -> None:
    if (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    ):
        raise CaptureRefused(f"{url}: non-public address {ip}", reason="private")


def _assert_url_public(url: str, resolver: Resolver) -> tuple[str, Optional[str]]:
    parsed = urlparse(url)
    if parsed.scheme not in _PUBLIC_SCHEMES:
        raise CaptureRefused(f"{url}: only public http(s) is allowed, got {parsed.scheme!r}",
                             reason="scheme")
    if parsed.username or parsed.password:
        raise CaptureRefused(f"{url}: embedded credentials are not unauthenticated access",
                             reason="credentials")
    host = parsed.hostname
    if not host:
        raise CaptureRefused(f"{url}: no host", reason="host")

    literal = _as_ip(host)
    if literal is not None:
        _deny_if_non_public(literal, url)
        return host, str(literal)

    lowered = host.lower()
    if lowered == "localhost" or lowered.endswith(".localhost"):
        raise CaptureRefused(f"{url}: loopback host {host!r}", reason="loopback")

    resolved: list[str] = []
    for addr in resolver(host):
        ip = _as_ip(addr)
        if ip is None:
            continue
        _deny_if_non_public(ip, url)   # a name that RESOLVES into private space is refused too
        resolved.append(str(ip))
    return host, (resolved[0] if resolved else None)


def _robots_verdict(
    url: str,
    *,
    robots_txt: Optional[str],
    robots_fetcher: Optional[Callable[[str], object]],
    user_agent: str,
    override: bool,
) -> dict:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    checked = False
    allowed = True
    if robots_txt is not None:
        parser = RobotFileParser()
        parser.parse(robots_txt.splitlines())
        allowed = parser.can_fetch(user_agent, url)
        checked = True
    elif robots_fetcher is not None:
        try:
            body = robots_fetcher(robots_url)
            lines = body.splitlines() if isinstance(body, str) else body.decode("utf-8", "replace").splitlines()
            parser = RobotFileParser()
            parser.parse(lines)
            allowed = parser.can_fetch(user_agent, url)
            checked = True
        except Exception:
            # a robots.txt we could not fetch/parse is NOT a silent allow-all: recorded unchecked
            allowed, checked = True, False
    return {
        "checked": checked,
        "allowed": allowed,
        "override": bool(override),
        "url": robots_url,
        "user_agent": user_agent,
    }


def assert_capture_allowed(
    url: str,
    *,
    resolver: Optional[Resolver] = None,
    robots_txt: Optional[str] = None,
    robots_fetcher: Optional[Callable[[str], object]] = None,
    override: bool = False,
    redirect_chain: Sequence[str] = (),
    limits: Optional[CaptureLimits] = None,
    user_agent: str = DEFAULT_USER_AGENT,
) -> CaptureAllowance:
    """Fail-closed admission for a capture target. Raises :class:`CaptureRefused` on any
    scheme / credential / SSRF / robots violation (including a redirect hop that lands on a
    private host); returns a :class:`CaptureAllowance` recording the decision otherwise."""
    limits = limits or CaptureLimits()
    resolver = resolver or _default_resolver

    host, ip = _assert_url_public(url, resolver)
    for hop in redirect_chain:
        _assert_url_public(hop, resolver)   # DENY redirects into private/loopback space

    robots = _robots_verdict(
        url, robots_txt=robots_txt, robots_fetcher=robots_fetcher,
        user_agent=user_agent, override=override,
    )
    if robots["checked"] and not robots["allowed"] and not override:
        raise CaptureRefused(f"{url}: robots.txt disallows capture", reason="robots")

    return CaptureAllowance(allowed=True, url=url, host=host, ip=ip, robots=robots, limits=limits)


def check_response(*, content_type: Optional[str], content_length: Optional[int],
                   limits: Optional[CaptureLimits] = None) -> None:
    """Enforce the response-side size + MIME limits. Raises :class:`CaptureRefused`."""
    limits = limits or CaptureLimits()
    if content_length is not None and content_length > limits.max_bytes:
        raise CaptureRefused(
            f"content-length {content_length} exceeds max_bytes {limits.max_bytes}", reason="size")
    primary = (content_type or "").split(";")[0].strip().lower()
    if primary and not any(primary.startswith(prefix) for prefix in limits.allowed_mime_prefixes):
        raise CaptureRefused(f"MIME {primary!r} is not an allowed capture type", reason="mime")
