"""
File Search MCP Server

Exposes three tools:
  - search_by_name    — glob pattern matching on file names
  - search_by_content — search file contents (uses ripgrep if available, grep as fallback)
  - read_file         — read a file by absolute path

Configure via environment variables:
  ROOT_DIR  — the directory searches are scoped to (required)

Usage:
  ROOT_DIR=/Users/you/projects python -m src.server
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

ROOT_DIR = os.environ.get("ROOT_DIR", "")

mcp = FastMCP(
    name="file-search-server",
    version="0.1.0",
)


def _validate_root() -> Path:
    """Ensure ROOT_DIR is set and exists."""
    if not ROOT_DIR:
        raise RuntimeError("ROOT_DIR environment variable is required")
    root = Path(ROOT_DIR).expanduser().resolve()
    if not root.is_dir():
        raise RuntimeError(f"ROOT_DIR does not exist or is not a directory: {root}")
    return root


def _safe_path(root: Path, path: str) -> Path:
    """
    Resolve a path and verify it is inside the root directory.
    Raises ValueError if path traversal is attempted.
    """
    resolved = (root / path).resolve()
    if not str(resolved).startswith(str(root)):
        raise ValueError(f"Path is outside the allowed root directory: {path}")
    return resolved


@mcp.tool()
async def search_by_name(pattern: str, max_results: int = 50) -> str:
    """
    Search for files matching a glob pattern within the configured root directory.

    Args:
        pattern: Glob pattern relative to root, e.g. '**/*.py' or 'src/*.ts'.
        max_results: Maximum number of results to return (1–200).

    Returns:
        JSON array of objects with 'path', 'size_bytes', and 'modified' fields.
    """
    if not 1 <= max_results <= 200:
        raise ValueError("max_results must be between 1 and 200")

    root = _validate_root()
    full_pattern = str(root / pattern)
    matches = glob.glob(full_pattern, recursive=True)

    results = []
    for match in matches[:max_results]:
        p = Path(match)
        if p.is_file():
            stat = p.stat()
            results.append({
                "path": str(p),
                "size_bytes": stat.st_size,
                "modified": stat.st_mtime,
            })

    return json.dumps(results, indent=2)


@mcp.tool()
async def search_by_content(
    query: str,
    file_glob: str = "**/*",
    max_results: int = 30,
    case_sensitive: bool = False,
) -> str:
    """
    Search file contents for a string or regex pattern.

    Uses ripgrep (rg) if installed, falls back to grep. Searches within the
    configured root directory only.

    Args:
        query: The string or regex to search for.
        file_glob: Limit search to files matching this glob pattern (e.g. '*.py').
        max_results: Maximum number of matching files to return (1–100).
        case_sensitive: Whether the search is case-sensitive.

    Returns:
        JSON array of objects with 'path' and 'match_count' fields.
    """
    if not 1 <= max_results <= 100:
        raise ValueError("max_results must be between 1 and 100")

    root = _validate_root()

    # Try ripgrep first, fall back to grep
    try:
        cmd = ["rg", "--json", "-l"]
        if not case_sensitive:
            cmd.append("-i")
        cmd += ["--glob", file_glob, query, str(root)]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        lines = [json.loads(line) for line in result.stdout.splitlines() if line]
        paths = [
            entry["data"]["path"]["text"]
            for entry in lines
            if entry.get("type") == "match"
        ]
    except FileNotFoundError:
        # ripgrep not available, use grep
        grep_flags = ["-r", "-l"]
        if not case_sensitive:
            grep_flags.append("-i")
        cmd = ["grep"] + grep_flags + [query, str(root)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        paths = [line for line in result.stdout.splitlines() if line]

    output = []
    for path in paths[:max_results]:
        output.append({"path": path})

    return json.dumps(output, indent=2)


@mcp.tool()
async def read_file(path: str, max_chars: int = 20000) -> str:
    """
    Read the contents of a file.

    The file must be within the configured root directory. Use search_by_name
    or search_by_content to find file paths first.

    Args:
        path: Absolute path to the file.
        max_chars: Maximum characters to return (default 20000, max 100000).

    Returns:
        The file contents as a string. Truncated if larger than max_chars.
    """
    if not 1 <= max_chars <= 100000:
        raise ValueError("max_chars must be between 1 and 100000")

    root = _validate_root()

    # Validate that path is inside root
    file_path = Path(path).resolve()
    if not str(file_path).startswith(str(root)):
        raise ValueError(f"Path is outside the allowed root directory: {path}")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    content = file_path.read_text(errors="replace")

    if len(content) > max_chars:
        truncation_note = f"\n\n[Truncated: showing {max_chars} of {len(content)} characters]"
        return content[:max_chars] + truncation_note

    return content


def run() -> None:
    """Entry point."""
    if not ROOT_DIR:
        print("Error: ROOT_DIR environment variable must be set", file=sys.stderr)
        print("Example: ROOT_DIR=/Users/you/projects python -m src.server", file=sys.stderr)
        sys.exit(1)
    print(f"File search server starting (root: {ROOT_DIR})", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
