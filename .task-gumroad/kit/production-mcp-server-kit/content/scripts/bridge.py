#!/usr/bin/env python3
"""
Subprocess IPC bridge for MCP servers.

Reads JSON-RPC requests from stdin, processes them, writes results to stdout.
Used by TypeScript MCP servers to call Python code without HTTP overhead.

Protocol:
  Request:  {"id": 1, "method": "search", "params": {"query": "test"}}
  Response: {"id": 1, "result": {"matches": [...]}}
  Error:    {"id": 1, "error": "Something went wrong"}

Usage:
  Spawned as a subprocess by the MCP server. Not run directly.
"""

import json
import sys
from typing import Any


def handle_search(params: dict) -> dict:
    """Example: search handler. Replace with your logic."""
    query = params.get("query", "")
    limit = params.get("limit", 10)

    # Your search logic here
    results = [
        {"id": f"doc-{i}", "content": f"Result {i} for '{query}'", "score": 0.9 - i * 0.1}
        for i in range(min(limit, 5))
    ]

    return {"results": results, "total": len(results)}


def handle_embed(params: dict) -> dict:
    """Example: embedding handler. Replace with your model."""
    text = params.get("text", "")

    # Your embedding logic here (e.g., sentence-transformers)
    # Placeholder: return a fake embedding
    embedding = [0.1] * 384  # 384-dim placeholder

    return {"embedding": embedding, "dimensions": len(embedding)}


def handle_health(_params: dict) -> dict:
    """Health check."""
    return {"status": "ok", "python_version": sys.version}


# Route table -- add your methods here
HANDLERS = {
    "search": handle_search,
    "embed": handle_embed,
    "health": handle_health,
}


def process_request(request: dict) -> dict:
    """Process a single JSON-RPC request."""
    req_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    handler = HANDLERS.get(method)
    if not handler:
        return {"id": req_id, "error": f"Unknown method: {method}"}

    try:
        result = handler(params)
        return {"id": req_id, "result": result}
    except Exception as e:
        return {"id": req_id, "error": str(e)}


def main():
    """Main loop: read JSON from stdin, write JSON to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            response = {"id": None, "error": f"Invalid JSON: {e}"}
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue

        response = process_request(request)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()  # Critical: don't buffer


if __name__ == "__main__":
    main()
