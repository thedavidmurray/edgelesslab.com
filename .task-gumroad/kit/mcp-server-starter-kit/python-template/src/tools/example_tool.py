"""
Example tool implementation.

A tool is a function Claude can call. It has:
  - a name (string, snake_case)
  - a description Claude uses to decide when to call it
  - an input schema (JSON Schema dict or Pydantic model)
  - a handler function

Tools are registered on the MCP server in server.py.
"""

from __future__ import annotations

from typing import Any


# Input schema as a plain JSON Schema dict.
# You can also use a Pydantic model — the MCP SDK accepts both.
EXAMPLE_TOOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "message": {
            "type": "string",
            "description": "The message to echo back",
        },
        "repeat": {
            "type": "integer",
            "minimum": 1,
            "maximum": 10,
            "default": 1,
            "description": "How many times to repeat the message (1–10)",
        },
    },
    "required": ["message"],
}


async def handle_example_tool(message: str, repeat: int = 1) -> list[dict[str, str]]:
    """
    Echo a message back, optionally repeated.

    Returns a list of content blocks. Each block is a dict with at minimum
    a 'type' key. Supported types:
      - {"type": "text", "text": "..."}
      - {"type": "image", "data": "<base64>", "mimeType": "image/png"}

    Raise any exception to signal failure; the SDK wraps it as isError=True.
    """
    lines = [message] * repeat
    return [{"type": "text", "text": "\n".join(lines)}]
