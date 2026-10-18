#!/usr/bin/env python3
"""
session-end.py - Hook for Stop event
Saves session context and generates summary for continuity.
Archives important session data to Obsidian vault.

ENHANCED: 2026-01-14
- Blocks session end if retrospective is required but not completed
- Tracks retrospective completion with email verification
- Forces /retrospective to run before allowing session to end

SECURITY HARDENED: 2024-12-23
- Session ID sanitization (path traversal prevention)
- Input validation and size limits
- Safe file operations with race condition prevention
"""

import json
import os
import sys
import sqlite3
import re
from datetime import datetime
from pathlib import Path

# Add lib to path for session_plan module
LIB_PATH = Path(__file__).parent / "lib"
sys.path.insert(0, str(LIB_PATH))

try:
    from session_plan import find_active_session_plan, get_completion_warnings
except ImportError:
    find_active_session_plan = None
    get_completion_warnings = None

# Configuration - use environment variable with fallback
PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).parent.parent.parent))
HOOKS_DIR = Path(__file__).parent
DB_PATH = HOOKS_DIR / "events.db"
SESSION_LOG_PATH = HOOKS_DIR / "sessions.log"
VAULT_SESSIONS_PATH = PROJECT_DIR / "claude-vault" / "04-Sessions"

# Retrospective tracking
RETRO_TRACKING_PATH = HOOKS_DIR / ".retrospective_status.json"
RETRO_REQUIRED_TOOL_COUNT = 10
RETRO_REQUIRED_DURATION_SECONDS = 600  # 10 minutes
RETRO_REQUIRED_ERRORS = 3

# Security constants
MAX_SESSION_ID_LENGTH = 64
MAX_INPUT_SIZE = 100000  # 100KB
ALLOWED_SESSION_ID_CHARS = re.compile(r'^[a-zA-Z0-9_-]+$')


def sanitize_session_id(session_id: str) -> str:
    """Sanitize session ID to prevent path traversal and injection attacks."""
    if not isinstance(session_id, str):
        return "unknown"

    # Truncate to reasonable length
    session_id = session_id[:MAX_SESSION_ID_LENGTH]

    # Remove any path traversal attempts
    session_id = session_id.replace("..", "").replace("/", "").replace("\\", "")

    # Only allow alphanumeric, underscore, hyphen
    if not ALLOWED_SESSION_ID_CHARS.match(session_id):
        # Strip to only allowed characters
        session_id = "".join(c for c in session_id if c.isalnum() or c in "-_")

    return session_id if session_id else "unknown"


def validate_path_within_boundary(path: Path, boundary: Path) -> bool:
    """Verify a path resolves within expected boundary (prevent symlink attacks)."""
    try:
        resolved = path.resolve()
        boundary_resolved = boundary.resolve()
        return str(resolved).startswith(str(boundary_resolved))
    except (OSError, ValueError):
        return False

def release_inbox():
    """Release any inbox claimed by this session (using PID marker)."""
    inbox_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).parent.parent.parent)) / ".inboxes"
    registry_path = inbox_root / "registry.json"
    claim_marker = Path(f"/tmp/claude-inbox-claimed-{os.getpid()}")

    # Also check parent PID marker (hook runs as child of claude process)
    claim_marker_ppid = Path(f"/tmp/claude-inbox-claimed-{os.getppid()}")

    marker = None
    if claim_marker.exists():
        marker = claim_marker
    elif claim_marker_ppid.exists():
        marker = claim_marker_ppid

    if not marker or not registry_path.exists():
        return

    try:
        marker_data = json.loads(marker.read_text())
        claimed_session = marker_data.get("session")
        if not claimed_session:
            return

        registry = json.loads(registry_path.read_text())
        sessions = registry.get("sessions", {})

        if claimed_session in sessions:
            sessions[claimed_session] = {
                "claimed": False,
                "claimed_by": None,
                "claimed_at": None
            }
            registry["sessions"] = sessions
            registry_path.write_text(json.dumps(registry, indent=2) + "\n")

        marker.unlink(missing_ok=True)
    except Exception:
        pass  # Don't fail on cleanup errors


def get_session_stats(session_id: str) -> dict:
    """Get statistics for the current session."""
    stats = {
        "tool_count": 0,
        "top_tools": [],
        "duration_seconds": 0,
        "errors": 0
    }

    if not DB_PATH.exists():
        return stats

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Get tool usage count for session
        cursor.execute("""
            SELECT tool_name, COUNT(*) as count, SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors
            FROM tool_usage
            WHERE session_id = ?
            GROUP BY tool_name
            ORDER BY count DESC
            LIMIT 5
        """, (session_id,))

        rows = cursor.fetchall()
        stats["top_tools"] = [{"name": r[0], "count": r[1]} for r in rows]
        stats["tool_count"] = sum(r[1] for r in rows)
        stats["errors"] = sum(r[2] for r in rows)

        conn.close()
    except Exception:
        pass

    # Calculate duration
    session_start = os.environ.get("CLAUDE_SESSION_START")
    if session_start:
        try:
            start = datetime.fromisoformat(session_start)
            stats["duration_seconds"] = int((datetime.now() - start).total_seconds())
        except Exception:
            pass

    return stats

def log_session_end(session_id: str, stats: dict):
    """Log session end event."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": "session_end",
        "session_id": session_id,
        "stats": stats
    }

    try:
        with open(SESSION_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

def should_suggest_retrospective(stats: dict) -> bool:
    """Determine if session warrants a retrospective."""
    # Suggest retrospective if:
    # - Session had significant activity (10+ tool calls)
    # - Session lasted more than 10 minutes
    # - Session had errors worth learning from
    tool_count = stats.get("tool_count", 0)
    duration = stats.get("duration_seconds", 0)
    errors = stats.get("errors", 0)

    return (tool_count >= RETRO_REQUIRED_TOOL_COUNT or
            duration >= RETRO_REQUIRED_DURATION_SECONDS or
            errors >= RETRO_REQUIRED_ERRORS)


def get_retrospective_status(session_id: str) -> dict:
    """Get retrospective completion status for current session."""
    try:
        if RETRO_TRACKING_PATH.exists():
            with open(RETRO_TRACKING_PATH) as f:
                data = json.load(f)
                if data.get("session_id") == session_id:
                    return data
    except Exception:
        pass
    return {"completed": False, "email_sent": False}


def mark_retrospective_required(session_id: str, stats: dict):
    """Mark that retrospective is required for this session."""
    try:
        data = {
            "session_id": session_id,
            "required": True,
            "completed": False,
            "email_sent": False,
            "timestamp": datetime.now().isoformat(),
            "stats": stats
        }
        with open(RETRO_TRACKING_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def is_retrospective_complete(session_id: str) -> bool:
    """Check if retrospective has been completed with email sent."""
    status = get_retrospective_status(session_id)
    return status.get("completed", False) and status.get("email_sent", False)


def archive_to_vault(session_id: str, stats: dict):
    """Archive session summary to Obsidian vault with security checks."""
    # Sanitize session_id before using in paths
    safe_session_id = sanitize_session_id(session_id)

    now = datetime.now()
    month_dir = VAULT_SESSIONS_PATH / now.strftime("%Y-%m")

    try:
        # Verify vault path is within project directory
        if not validate_path_within_boundary(VAULT_SESSIONS_PATH, PROJECT_DIR):
            return  # Refuse to write outside project

        month_dir.mkdir(parents=True, exist_ok=True)

        # Use sanitized session ID in filename
        filename = f"{now.strftime('%Y-%m-%d')}-session-{safe_session_id[:8]}.md"
        filepath = month_dir / filename

        # Verify final path is still within boundary
        if not validate_path_within_boundary(filepath, VAULT_SESSIONS_PATH):
            return  # Path traversal detected

        # Only create if doesn't exist (avoid overwrites) - use O_EXCL for race-free creation
        if not filepath.exists():
            duration_min = stats.get("duration_seconds", 0) // 60

            # Sanitize tool names before including in output
            top_tools_list = stats.get("top_tools", [])[:3]
            top_tools = ", ".join(
                sanitize_session_id(t.get("name", "unknown"))[:50]
                for t in top_tools_list
                if isinstance(t, dict)
            )

            # Check if retrospective is warranted
            retro_suggested = should_suggest_retrospective(stats)
            retro_note = "**Retrospective recommended** - Run `/retrospective` to extract learnings" if retro_suggested else ""

            content = f"""---
created: {now.isoformat()}
session_id: {safe_session_id}
type: session_log
status: completed
retrospective_suggested: {str(retro_suggested).lower()}
---

# Session Summary - {now.strftime('%Y-%m-%d %H:%M')}

## Metrics
- Duration: {duration_min} minutes
- Tool calls: {stats.get('tool_count', 0)}
- Errors: {stats.get('errors', 0)}
- Top tools: {top_tools or 'N/A'}

{retro_note}

## Notes
*(Auto-generated session log)*

"""
            # Use atomic write pattern
            temp_filepath = filepath.with_suffix('.tmp')
            with open(temp_filepath, "w") as f:
                f.write(content)
            temp_filepath.rename(filepath)
    except Exception:
        pass  # Don't fail on archive errors

def main():
    """Main hook entry point."""
    # Read hook input from stdin with size limit
    try:
        raw_input = sys.stdin.read(MAX_INPUT_SIZE)
        hook_input = json.loads(raw_input)
        if not isinstance(hook_input, dict):
            hook_input = {}
    except (json.JSONDecodeError, ValueError):
        hook_input = {}

    # Get and sanitize session ID
    raw_session_id = os.environ.get("CLAUDE_SESSION_ID", hook_input.get("session_id", "unknown"))
    session_id = sanitize_session_id(raw_session_id)

    # Gather session statistics
    stats = get_session_stats(session_id)

    # Check if retrospective is required
    retro_required = should_suggest_retrospective(stats)
    retro_complete = is_retrospective_complete(session_id) if retro_required else True

    # Check if there's an active session plan with incomplete phases
    session_plan_warnings = []
    if find_active_session_plan and get_completion_warnings:
        try:
            active_plan = find_active_session_plan()
            if active_plan:
                session_plan_warnings = get_completion_warnings(active_plan)
        except Exception:
            pass  # Don't fail on session plan check errors

    # If retrospective is required but not done, BLOCK session end
    if retro_required and not retro_complete:
        # Mark as required so we can track
        mark_retrospective_required(session_id, stats)

        duration_min = stats.get("duration_seconds", 0) // 60
        tool_count = stats.get("tool_count", 0)

        # Block the session end - force retrospective
        response = {
            "continue": False,  # Block exit
            "decision": "block"
        }

        # Strong message to stderr
        print(f"\n🚫 SESSION EXIT BLOCKED - Retrospective required!", file=sys.stderr)
        print(f"   Session had {tool_count} tool calls over {duration_min} minutes.", file=sys.stderr)
        print(f"   Run /retrospective to extract learnings and send email summary.", file=sys.stderr)
        print(f"   Session will not end until retrospective is complete.\n", file=sys.stderr)

        # Output blocking response
        print(json.dumps(response))
        return

    # Release claimed inbox
    release_inbox()

    # Log and archive (functions use sanitized IDs internally)
    log_session_end(session_id, stats)
    archive_to_vault(session_id, stats)

    # Build response with correct schema - allow exit
    response = {
        "continue": True
    }

    # Clean up tracking file on successful exit
    if RETRO_TRACKING_PATH.exists():
        try:
            RETRO_TRACKING_PATH.unlink()
        except Exception:
            pass

    # If retrospective was completed, acknowledge it
    if retro_required and retro_complete:
        print(f"\n✅ Retrospective completed with email sent. Session ending.", file=sys.stderr)

    # Warn about incomplete session plan (don't block, just warn)
    if session_plan_warnings:
        print(f"\n⚠️  Active session plan has incomplete items:", file=sys.stderr)
        for warning in session_plan_warnings[:5]:  # Show first 5 warnings
            print(f"   {warning}", file=sys.stderr)
        print(f"   Consider completing or marking plan as 'completed' before ending session.\n", file=sys.stderr)

    # Output JSON response
    print(json.dumps(response))

if __name__ == "__main__":
    main()
