#!/usr/bin/env python3
"""
sandbox-observer.py - E2B Sandbox Observability Hook
PostToolUse hook for tracking code execution in E2B sandboxes.

FEATURES:
- Logs sandbox executions to events database
- Tracks execution times and success rates
- Alerts on failed executions or timeouts
- Cross-references with trading operations

SECURITY: 2024-12-29
- Code snippets truncated to 500 chars for logging
- No sensitive data captured from sandbox output
"""

import json
import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# Add lib to path
HOOKS_DIR = Path(__file__).parent
LIB_DIR = HOOKS_DIR / "lib"
sys.path.insert(0, str(LIB_DIR))

from trading_helper import identify_agent

# Configuration
DB_PATH = HOOKS_DIR / "events.db"
LOG_PATH = HOOKS_DIR / "sandbox.log"
MAX_INPUT_SIZE = 50000
CODE_PREVIEW_LENGTH = 500

# Schema for sandbox events
SANDBOX_SCHEMA = """
CREATE TABLE IF NOT EXISTS sandbox_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    session_id TEXT,
    agent TEXT NOT NULL,
    event_type TEXT NOT NULL,
    code_preview TEXT,
    language TEXT,
    execution_time_ms REAL,
    success INTEGER,
    error_preview TEXT,
    output_length INTEGER,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_sandbox_events_agent ON sandbox_events(agent);
CREATE INDEX IF NOT EXISTS idx_sandbox_events_timestamp ON sandbox_events(timestamp);
"""


def get_connection():
    """Get database connection with sandbox tables initialized."""
    conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")

    # Initialize sandbox table
    cursor = conn.cursor()
    cursor.executescript(SANDBOX_SCHEMA)
    conn.commit()

    return conn


def is_sandbox_operation(tool_name: str, tool_input: dict) -> bool:
    """Check if this is a sandbox-related operation."""
    sandbox_indicators = [
        "e2b",
        "sandbox",
        "code_interpreter",
        "execute_code",
        "run_code",
    ]

    tool_lower = tool_name.lower()
    for indicator in sandbox_indicators:
        if indicator in tool_lower:
            return True

    # Check input for sandbox patterns
    if isinstance(tool_input, dict):
        input_str = str(tool_input).lower()
        if any(ind in input_str for ind in sandbox_indicators):
            return True

    return False


def extract_sandbox_metadata(tool_name: str, tool_input: dict) -> dict:
    """Extract sandbox-specific metadata from tool input."""
    metadata = {
        "event_type": "code_execution",
        "timestamp": datetime.now().isoformat(),
    }

    if isinstance(tool_input, dict):
        # Code content
        code = tool_input.get("code", tool_input.get("source", ""))
        if code:
            metadata["code_preview"] = str(code)[:CODE_PREVIEW_LENGTH]
            metadata["code_length"] = len(str(code))

        # Language
        metadata["language"] = tool_input.get("language", "python")

        # Timeout
        if "timeout" in tool_input:
            metadata["timeout"] = tool_input["timeout"]

    return metadata


def log_sandbox_event(conn, event_data: dict) -> int:
    """Log a sandbox event to the database."""
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sandbox_events
        (timestamp, session_id, agent, event_type, code_preview,
         language, execution_time_ms, success, error_preview, output_length, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_data.get("timestamp", datetime.now().isoformat()),
        event_data.get("session_id"),
        event_data.get("agent", "unknown"),
        event_data.get("event_type", "code_execution"),
        event_data.get("code_preview", "")[:CODE_PREVIEW_LENGTH],
        event_data.get("language", "python"),
        event_data.get("execution_time_ms"),
        1 if event_data.get("success", True) else 0,
        event_data.get("error_preview", "")[:500],
        event_data.get("output_length", 0),
        json.dumps(event_data.get("metadata", {}))
    ))

    conn.commit()
    return cursor.lastrowid


def main():
    """Main hook entry point."""
    # Read hook input
    try:
        raw_input = sys.stdin.read(MAX_INPUT_SIZE)
        hook_input = json.loads(raw_input)
        if not isinstance(hook_input, dict):
            hook_input = {}
    except (json.JSONDecodeError, ValueError):
        hook_input = {}

    # Extract tool info
    tool_name = hook_input.get("tool", hook_input.get("tool_name", "unknown"))
    tool_input = hook_input.get("input", hook_input.get("tool_input", {}))
    tool_output = hook_input.get("output", hook_input.get("result", {}))

    # Check if this is a sandbox operation
    if not is_sandbox_operation(tool_name, tool_input):
        # Not sandbox-related, just pass through
        print(json.dumps({"continue": True}))
        return

    # Identify the agent
    agent = identify_agent()
    session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")

    # Determine success
    success = True
    error_preview = ""
    execution_time = None
    output_length = 0

    if isinstance(tool_output, dict):
        success = tool_output.get("success", not tool_output.get("error", False))
        error_preview = str(tool_output.get("error", ""))[:500]
        execution_time = tool_output.get("execution_time_ms")
        output_length = len(str(tool_output.get("output", "")))
    elif isinstance(tool_output, str):
        if "error" in tool_output.lower():
            success = False
            error_preview = tool_output[:500]
        output_length = len(tool_output)

    # Extract metadata
    metadata = extract_sandbox_metadata(
        tool_name,
        tool_input if isinstance(tool_input, dict) else {}
    )

    # Build event data
    event_data = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "agent": agent,
        "event_type": metadata.get("event_type", "code_execution"),
        "code_preview": metadata.get("code_preview", ""),
        "language": metadata.get("language", "python"),
        "execution_time_ms": execution_time,
        "success": success,
        "error_preview": error_preview,
        "output_length": output_length,
        "metadata": metadata
    }

    try:
        conn = get_connection()
        log_sandbox_event(conn, event_data)
        conn.close()

        # Log to file for visibility
        log_msg = (
            f"{datetime.now().isoformat()} "
            f"SANDBOX [{agent}] "
            f"{'OK' if success else 'FAIL'} "
            f"({execution_time or 0:.0f}ms)\n"
        )
        with open(LOG_PATH, "a") as f:
            f.write(log_msg)

    except Exception as e:
        # Log error but don't fail the hook
        try:
            with open(LOG_PATH, "a") as f:
                f.write(f"{datetime.now().isoformat()} ERROR: {str(e)[:200]}\n")
        except Exception:
            pass

    # Always continue
    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
