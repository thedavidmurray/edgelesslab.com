"""
Database Query MCP Server

Exposes four tools for interacting with a SQLite database:
  - list_tables     — discover all tables in the database
  - describe_table  — get column names, types, and constraints
  - query           — run a SELECT statement
  - explain_query   — show the query plan without executing

Only read operations are permitted. No INSERT, UPDATE, DELETE, DROP, or DDL.

Configure via environment variables:
  DATABASE_PATH  — absolute path to the SQLite database file (required)

Usage:
  DATABASE_PATH=/path/to/app.db python -m src.server
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

DATABASE_PATH = os.environ.get("DATABASE_PATH", "")

mcp = FastMCP(
    name="database-query-server",
    version="0.1.0",
)

# SQL keywords that indicate write or structural operations.
# We block these to keep the server read-only.
_WRITE_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|REPLACE|TRUNCATE|ATTACH|DETACH)\b",
    re.IGNORECASE,
)


def _get_connection() -> sqlite3.Connection:
    """Open a read-only connection to the database."""
    if not DATABASE_PATH:
        raise RuntimeError("DATABASE_PATH environment variable is not set")
    if not os.path.isfile(DATABASE_PATH):
        raise RuntimeError(f"Database file not found: {DATABASE_PATH}")
    # Open in read-only mode via URI
    uri = f"file:{DATABASE_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _assert_read_only(sql: str) -> None:
    """Raise ValueError if the SQL contains write operations."""
    stripped = sql.strip()
    if _WRITE_PATTERN.search(stripped):
        raise ValueError(
            "Only SELECT statements and EXPLAIN are allowed. "
            "Write operations are not permitted."
        )


def _rows_to_dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    """Convert cursor rows to a list of plain dicts."""
    columns = [desc[0] for desc in cursor.description or []]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


@mcp.tool()
async def list_tables() -> str:
    """
    List all tables in the database.

    Returns:
        JSON array of table names.
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        return json.dumps(tables)
    finally:
        conn.close()


@mcp.tool()
async def describe_table(table_name: str) -> str:
    """
    Get the schema of a table: column names, types, nullability, and defaults.

    Args:
        table_name: The name of the table to describe.

    Returns:
        JSON array of column definition objects.
    """
    # Validate table name — only allow alphanumeric and underscores
    if not re.match(r"^\w+$", table_name):
        raise ValueError(f"Invalid table name: {table_name}")

    conn = _get_connection()
    try:
        cursor = conn.execute(f"PRAGMA table_info({table_name})")  # noqa: S608
        columns = _rows_to_dicts(cursor)
        if not columns:
            raise ValueError(f"Table not found or has no columns: {table_name}")
        return json.dumps(columns, indent=2)
    finally:
        conn.close()


@mcp.tool()
async def query(sql: str, max_rows: int = 100) -> str:
    """
    Execute a SELECT query against the database and return results as JSON.

    Only SELECT statements are allowed. The result is limited to max_rows rows.
    Use LIMIT in your SQL for more control over result size.

    Args:
        sql: A SELECT SQL statement.
        max_rows: Maximum number of rows to return (1–1000, default 100).

    Returns:
        JSON object with 'columns', 'rows', and 'row_count' fields.
    """
    if not 1 <= max_rows <= 1000:
        raise ValueError("max_rows must be between 1 and 1000")

    _assert_read_only(sql)

    conn = _get_connection()
    try:
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in (cursor.description or [])]
        rows = [list(row) for row in cursor.fetchmany(max_rows)]
        return json.dumps(
            {"columns": columns, "rows": rows, "row_count": len(rows)},
            indent=2,
            default=str,  # handle dates, decimals, etc.
        )
    finally:
        conn.close()


@mcp.tool()
async def explain_query(sql: str) -> str:
    """
    Show the query execution plan without running the query.

    Useful for understanding how SQLite will execute a complex query
    before committing to running it.

    Args:
        sql: A SELECT SQL statement.

    Returns:
        JSON array of query plan steps.
    """
    _assert_read_only(sql)

    conn = _get_connection()
    try:
        cursor = conn.execute(f"EXPLAIN QUERY PLAN {sql}")
        plan = _rows_to_dicts(cursor)
        return json.dumps(plan, indent=2, default=str)
    finally:
        conn.close()


def run() -> None:
    """Entry point."""
    if not DATABASE_PATH:
        print("Error: DATABASE_PATH environment variable must be set", file=sys.stderr)
        print("Example: DATABASE_PATH=/path/to/app.db python -m src.server", file=sys.stderr)
        sys.exit(1)
    print(f"Database query server starting (db: {DATABASE_PATH})", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
