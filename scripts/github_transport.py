"""HTTP GET/POST with auth headers, rate-limit handling, and public fallback."""

from __future__ import annotations

import time

import requests

from scripts.settings import Settings


def _auth_headers(settings: Settings) -> dict[str, str]:
    """Return request headers including auth when a token is available."""
    h: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if settings.token:
        h["Authorization"] = f"Bearer {settings.token}"
    return h


_PUBLIC_HEADERS: dict[str, str] = {"Accept": "application/vnd.github+json"}


def request_with_retry(
    url: str,
    settings: Settings,
    *,
    headers: dict[str, str] | None = None,
    params: dict | None = None,
    max_retries: int = 3,
) -> requests.Response:
    """Send an authenticated GET request and retry on 429/5xx."""
    hdrs = headers or _auth_headers(settings)
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
