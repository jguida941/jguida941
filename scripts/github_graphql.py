"""GraphQL query execution for the GitHub API."""

from __future__ import annotations

import requests

from scripts.settings import Settings
from scripts.github_transport import _auth_headers

GRAPHQL_ENDPOINT = "https://api.github.com/graphql"


def graphql_query(
    query: str,
    variables: dict,
    settings: Settings,
) -> dict | None:
    """Execute a GraphQL query against the GitHub API.

    Returns the ``data`` portion of the response, or ``None`` on any error.
    """
    try:
        resp = requests.post(
            GRAPHQL_ENDPOINT,
            headers=_auth_headers(settings),
            json={"query": query, "variables": variables},
        )
    except requests.RequestException:
        return None
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
    return payload.get("data")
