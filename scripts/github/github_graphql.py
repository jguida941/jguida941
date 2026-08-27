"""GraphQL query execution for the GitHub API."""

from __future__ import annotations

from contextvars import ContextVar

import requests

from scripts.core.settings import Settings
from scripts.github.github_transport import _auth_headers_for_token, candidate_tokens

GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
_LAST_SUCCESSFUL_TOKEN_INDEX: ContextVar[int | None] = ContextVar(
    "github_graphql_last_successful_token_index",
    default=None,
)
_LAST_SUCCESSFUL_OAUTH_SCOPES: ContextVar[frozenset[str] | None] = ContextVar(
    "github_graphql_last_successful_oauth_scopes",
    default=None,
)


def last_query_used_fallback_token() -> bool:
    """Whether the most recent query in this context succeeded after token 0."""
    token_index = _LAST_SUCCESSFUL_TOKEN_INDEX.get()
    return token_index is not None and token_index > 0


def last_query_oauth_scopes() -> frozenset[str] | None:
    """Verified OAuth scopes advertised by the most recent successful response.

    ``None`` means the response did not provide scope evidence.  That is distinct
    from an explicitly empty scope header and must never be interpreted as broad
    private-repository access.
    """
    return _LAST_SUCCESSFUL_OAUTH_SCOPES.get()


def _response_oauth_scopes(response: requests.Response) -> frozenset[str] | None:
    headers = getattr(response, "headers", None)
    if not hasattr(headers, "items"):
        return None
    raw_value = next(
        (
            value
            for key, value in headers.items()
            if str(key).casefold() == "x-oauth-scopes"
        ),
        None,
    )
    if raw_value is None:
        return None
    return frozenset(
        scope.strip().casefold()
        for scope in str(raw_value).split(",")
        if scope.strip()
    )


def graphql_query(
    query: str,
    variables: dict,
    settings: Settings,
) -> dict | None:
    """Execute a GraphQL query against the GitHub API.

    Returns the ``data`` portion of the response, or ``None`` on any error.
    On a 401 (e.g. an expired PERSONAL_GITHUB_TOKEN) the next available token
    is tried before giving up.
    """
    tokens = candidate_tokens(settings)
    _LAST_SUCCESSFUL_TOKEN_INDEX.set(None)
    _LAST_SUCCESSFUL_OAUTH_SCOPES.set(None)
    for idx, token in enumerate(tokens):
        try:
            resp = requests.post(
                GRAPHQL_ENDPOINT,
                headers=_auth_headers_for_token(token),
                json={"query": query, "variables": variables},
            )
        except requests.RequestException:
            return None
        if resp.status_code == 401 and idx < len(tokens) - 1:
            continue
        if resp.status_code != 200:
            return None

        try:
            payload = resp.json()
        except ValueError:
            return None
        if not isinstance(payload, dict):
            return None
        if payload.get("errors"):
            return None
        _LAST_SUCCESSFUL_TOKEN_INDEX.set(idx)
        _LAST_SUCCESSFUL_OAUTH_SCOPES.set(_response_oauth_scopes(resp))
        return payload.get("data")
    return None
