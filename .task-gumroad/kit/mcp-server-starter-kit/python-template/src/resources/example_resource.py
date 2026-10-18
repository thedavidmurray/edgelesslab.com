"""
Example resource implementation.

A resource is a piece of content Claude can read. Resources have:
  - a URI that uniquely identifies them
  - a name and optional description
  - a mimeType
  - content returned by a handler

Resources can be static (fixed URI) or templated (URI with variables).

Static example:  "config://app/settings"
Template example: "file://{path}" — Claude fills in {path}
"""

from __future__ import annotations

import json
from datetime import datetime, timezone


# ──────────────────────────────────────────────
# Static resource — fixed URI
# ──────────────────────────────────────────────

STATIC_RESOURCE_URI = "example://status"
STATIC_RESOURCE_NAME = "Server Status"
STATIC_RESOURCE_DESCRIPTION = "Current status and uptime of the MCP server"
STATIC_RESOURCE_MIME = "application/json"


async def handle_static_resource() -> str:
    """Return server status as JSON text."""
    status = {
        "status": "ok",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0",
    }
    return json.dumps(status, indent=2)


# ──────────────────────────────────────────────
# Template resource — parameterized URI
# ──────────────────────────────────────────────
# URI template uses {variable} placeholders (RFC 6570).
# Claude fills them in based on context or user requests.

TEMPLATE_RESOURCE_TEMPLATE = "example://items/{id}"
TEMPLATE_RESOURCE_NAME = "Example Item"
TEMPLATE_RESOURCE_DESCRIPTION = (
    "Retrieve a named item by ID. Replace {id} with the item identifier."
)
TEMPLATE_RESOURCE_MIME = "application/json"


def _parse_item_id(uri: str) -> str:
    """Extract the item ID from example://items/{id}."""
    prefix = "example://items/"
    if not uri.startswith(prefix):
        raise ValueError(f"Unexpected URI: {uri}")
    return uri[len(prefix):]


async def handle_template_resource(uri: str) -> str:
    """Return a JSON representation of the requested item."""
    item_id = _parse_item_id(uri)

    # In a real server, look this up from a database or external API.
    item = {
        "id": item_id,
        "name": f"Item {item_id}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data": "Replace this with real data from your source",
    }
    return json.dumps(item, indent=2)
