"""
MCP Server Template — Entry Point

Wires together tools and resources, then starts the server over stdio.
Claude Code launches this process and communicates via stdin/stdout.

To add a tool:
  1. Create a module in src/tools/
  2. Import the handler and schema here
  3. Register with @mcp.tool()

To add a resource:
  1. Create a module in src/resources/
  2. Import the handler here
  3. Register with @mcp.resource()

Usage:
  python -m src.server        # run directly
  mcp-server                  # if installed via pyproject.toml [scripts]
"""

from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP

from .resources.example_resource import (
    STATIC_RESOURCE_DESCRIPTION,
    STATIC_RESOURCE_MIME,
    STATIC_RESOURCE_NAME,
    STATIC_RESOURCE_URI,
    TEMPLATE_RESOURCE_DESCRIPTION,
    TEMPLATE_RESOURCE_MIME,
    TEMPLATE_RESOURCE_NAME,
    TEMPLATE_RESOURCE_TEMPLATE,
    handle_static_resource,
    handle_template_resource,
)
from .tools.example_tool import handle_example_tool

# ──────────────────────────────────────────────
# Server setup
# ──────────────────────────────────────────────

mcp = FastMCP(
    name="mcp-server-template",
    version="0.1.0",
)

# ──────────────────────────────────────────────
# Register tools
# ──────────────────────────────────────────────


@mcp.tool()
async def example_echo(message: str, repeat: int = 1) -> str:
    """
    Echoes a message back, optionally repeated.

    Args:
        message: The message to echo back.
        repeat: How many times to repeat the message (1–10).

    Returns:
        The message repeated on separate lines.
    """
    if not 1 <= repeat <= 10:
        raise ValueError("repeat must be between 1 and 10")
    result = await handle_example_tool(message, repeat)
    return result[0]["text"]


# ──────────────────────────────────────────────
# Register static resources
# ──────────────────────────────────────────────


@mcp.resource(
    uri=STATIC_RESOURCE_URI,
    name=STATIC_RESOURCE_NAME,
    description=STATIC_RESOURCE_DESCRIPTION,
    mime_type=STATIC_RESOURCE_MIME,
)
async def server_status() -> str:
    """Return the server status as JSON."""
    return await handle_static_resource()


# ──────────────────────────────────────────────
# Register resource templates
# ──────────────────────────────────────────────


@mcp.resource(
    uri=TEMPLATE_RESOURCE_TEMPLATE,
    name=TEMPLATE_RESOURCE_NAME,
    description=TEMPLATE_RESOURCE_DESCRIPTION,
    mime_type=TEMPLATE_RESOURCE_MIME,
)
async def example_item(uri: str) -> str:
    """Return a named item by ID."""
    return await handle_template_resource(uri)


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────


def run() -> None:
    """Run the server via stdio transport."""
    # All debug output must go to stderr — stdout is the MCP protocol channel.
    print("MCP server starting", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
