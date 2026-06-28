"""HTTP GET/POST with auth headers, rate-limit handling, and public fallback."""

from __future__ import annotations

import time

import requests

from scripts.settings import Settings


def _auth_headers_for_token(token: str) -> dict[str, str]:
    """Return request headers including auth for a specific token."""
    h: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _auth_headers(settings: Settings) -> dict[str, str]:
    """Return request headers including auth when a token is available."""
    return _auth_headers_for_token(settings.token)


def candidate_tokens(settings: Settings) -> tuple[str, ...]:
    """Ordered tokens to try; falls back to the primary token for back-compat."""
    if settings.tokens:
        return settings.tokens
    return (settings.token,) if settings.token else ("",)


_PUBLIC_HEADERS: dict[str, str] = {"Accept": "application/vnd.github+json"}


def _request_once(
    url: str,
    hdrs: dict[str, str],
    params: dict | None,
    max_retries: int,
) -> requests.Response:
    """Single GET attempt with 429/5xx retry; raises on other non-200."""
    last_error: Exception | None = None
    resp: requests.Response | None = None
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=hdrs, params=params)
        except requests.RequestException as exc:
            last_error = exc
            if attempt == max_retries - 1:
                raise
            time.sleep(2**attempt)
            continue
        if resp.status_code == 200:
            return resp
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = int(resp.headers.get("Retry-After", 2**attempt))
            time.sleep(wait)
            continue
        resp.raise_for_status()
    if last_error is not None:
        raise last_error
    assert resp is not None
    return resp


def request_with_retry(
    url: str,
    settings: Settings,
    *,
    headers: dict[str, str] | None = None,
    params: dict | None = None,
    max_retries: int = 3,
) -> requests.Response:
    """Send an authenticated GET request and retry on 429/5xx.

    When the caller does not supply explicit headers, iterate over the
    available tokens and transparently retry with the next token on a 401
    (e.g. an expired PERSONAL_GITHUB_TOKEN falling back to GITHUB_TOKEN).
    """
    if headers is not None:
        return _request_once(url, headers, params, max_retries)

    tokens = candidate_tokens(settings)
    for idx, token in enumerate(tokens):
        try:
            return _request_once(url, _auth_headers_for_token(token), params, max_retries)
        except requests.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status == 401 and idx < len(tokens) - 1:
                continue
            raise
    # Unreachable: tokens always has at least one entry.
    raise RuntimeError("no tokens available for request")


def request_public_with_retry(
    url: str,
    *,
    params: dict | None = None,
    max_retries: int = 2,
) -> requests.Response:
    """Send a public (unauthenticated) GET request for fallback checks."""
    last_error: Exception | None = None
    resp: requests.Response | None = None
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=_PUBLIC_HEADERS, params=params)
        except requests.RequestException as exc:
            last_error = exc
            if attempt == max_retries - 1:
                raise
            time.sleep(2**attempt)
            continue
        if resp.status_code == 200:
            return resp
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = int(resp.headers.get("Retry-After", 2**attempt))
            time.sleep(wait)
            continue
        resp.raise_for_status()
    if last_error is not None:
        raise last_error
    assert resp is not None
    return resp
