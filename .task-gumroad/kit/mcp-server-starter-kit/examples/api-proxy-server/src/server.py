"""
API Proxy MCP Server

Wraps any REST API as MCP tools. Claude can call the API without knowing
HTTP details, authentication headers, or base URLs.

Exposes four tools:
  - api_get     — GET request with optional query parameters
  - api_post    — POST request with a JSON body
  - api_put     — PUT request with a JSON body
  - api_delete  — DELETE request

Configure via environment variables:
  API_BASE_URL    — base URL of the API (required), e.g. https://api.example.com
  API_KEY         — API key or token (optional)
  API_KEY_HEADER  — header name for the key (default: Authorization)
  API_KEY_PREFIX  — prefix before the key in the header (default: Bearer)
  TIMEOUT_SECONDS — request timeout in seconds (default: 15)

Example — wrap the GitHub API:
  API_BASE_URL=https://api.github.com
  API_KEY=ghp_your_token
  API_KEY_HEADER=Authorization
  API_KEY_PREFIX=token

Usage:
  API_BASE_URL=https://api.example.com API_KEY=key python -m src.server
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.parse import urljoin

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE_URL = os.environ.get("API_BASE_URL", "")
API_KEY = os.environ.get("API_KEY", "")
API_KEY_HEADER = os.environ.get("API_KEY_HEADER", "Authorization")
API_KEY_PREFIX = os.environ.get("API_KEY_PREFIX", "Bearer")
TIMEOUT_SECONDS = float(os.environ.get("TIMEOUT_SECONDS", "15"))

mcp = FastMCP(
    name="api-proxy-server",
    version="0.1.0",
)


def _build_headers() -> dict[str, str]:
    """Build the default headers for every request."""
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "mcp-api-proxy/0.1.0",
    }
    if API_KEY:
        value = f"{API_KEY_PREFIX} {API_KEY}".strip() if API_KEY_PREFIX else API_KEY
        headers[API_KEY_HEADER] = value
    return headers


def _build_url(endpoint: str) -> str:
    """Combine base URL and endpoint path."""
    if not API_BASE_URL:
        raise RuntimeError("API_BASE_URL environment variable is not set")
    base = API_BASE_URL.rstrip("/")
    path = endpoint.lstrip("/")
    return f"{base}/{path}"


def _format_response(response: httpx.Response) -> str:
    """Format the HTTP response for return to Claude."""
    try:
        body = response.json()
        body_text = json.dumps(body, indent=2, default=str)
    except Exception:
        body_text = response.text[:8000]

    return json.dumps(
        {
            "status": response.status_code,
            "ok": response.is_success,
            "headers": dict(response.headers),
            "body": body,
        },
        indent=2,
        default=str,
    )


@mcp.tool()
async def api_get(endpoint: str, params: dict[str, Any] | None = None) -> str:
    """
    Send a GET request to the configured API.

    Args:
        endpoint: API path to request, e.g. '/users' or '/users/42'.
        params: Optional query parameters as a JSON object,
                e.g. {"page": 1, "per_page": 20}.

    Returns:
        JSON object with status, ok, headers, and body fields.
    """
    url = _build_url(endpoint)
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.get(url, params=params or {}, headers=_build_headers())
    return _format_response(response)


@mcp.tool()
async def api_post(endpoint: str, body: dict[str, Any] | None = None) -> str:
    """
    Send a POST request to the configured API with a JSON body.

    Args:
        endpoint: API path to request, e.g. '/users'.
        body: Request body as a JSON object.

    Returns:
        JSON object with status, ok, headers, and body fields.
    """
    url = _build_url(endpoint)
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.post(url, json=body or {}, headers=_build_headers())
    return _format_response(response)


@mcp.tool()
async def api_put(endpoint: str, body: dict[str, Any] | None = None) -> str:
    """
    Send a PUT request to the configured API with a JSON body.

    Args:
        endpoint: API path to request, e.g. '/users/42'.
        body: Request body as a JSON object.

    Returns:
        JSON object with status, ok, headers, and body fields.
    """
    url = _build_url(endpoint)
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.put(url, json=body or {}, headers=_build_headers())
    return _format_response(response)


@mcp.tool()
async def api_delete(endpoint: str) -> str:
    """
    Send a DELETE request to the configured API.

    Args:
        endpoint: API path to delete, e.g. '/users/42'.

    Returns:
        JSON object with status, ok, headers, and body fields.
    """
    url = _build_url(endpoint)
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.delete(url, headers=_build_headers())
    return _format_response(response)


@mcp.resource(
    uri="api://info",
    name="API Information",
    description="Base URL and configuration of the proxied API",
    mime_type="application/json",
)
async def api_info() -> str:
    """Return information about the configured API."""
    info = {
        "base_url": API_BASE_URL,
        "auth_configured": bool(API_KEY),
        "auth_header": API_KEY_HEADER if API_KEY else None,
        "timeout_seconds": TIMEOUT_SECONDS,
    }
    return json.dumps(info, indent=2)


def run() -> None:
    """Entry point."""
    if not API_BASE_URL:
        print("Error: API_BASE_URL environment variable must be set", file=sys.stderr)
        print("Example: API_BASE_URL=https://api.example.com python -m src.server", file=sys.stderr)
        sys.exit(1)
    print(f"API proxy server starting (base: {API_BASE_URL})", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
