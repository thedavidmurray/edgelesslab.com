#!/usr/bin/env python3
"""
Backlog staleness checker for session-start hook.
Checks if ACTIVE-BACKLOG.md needs regeneration.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import glob

BACKLOG_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).parent.parent.parent)) / "backlog"
TASKS_DIR = BACKLOG_DIR / "tasks"
ACTIVE_BACKLOG = BACKLOG_DIR / "ACTIVE-BACKLOG.md"

def get_task_count():
    """Count .md files in tasks directory."""
    return len(list(TASKS_DIR.glob("task-*.md")))

def get_backlog_metadata():
    """Extract metadata from ACTIVE-BACKLOG.md."""
    if not ACTIVE_BACKLOG.exists():
        return None

    content = ACTIVE_BACKLOG.read_text()
    metadata = {
        "exists": True,
        "last_modified": datetime.fromtimestamp(ACTIVE_BACKLOG.stat().st_mtime),
        "recorded_count": None
    }

    # Extract recorded task count
    for line in content.split("\n"):
        if "Total Active Tasks" in line:
            # Parse "**Total Active Tasks**: 21 (post-cleanup)" or similar
            try:
                count_str = line.split(":")[1].strip().split()[0]
                metadata["recorded_count"] = int(count_str)
            except (IndexError, ValueError):
                pass
            break

    return metadata

def check_staleness():
    """
    Check if backlog needs sync.
    Returns: (is_stale: bool, reason: str, details: dict)
    """
    actual_count = get_task_count()
    metadata = get_backlog_metadata()

    details = {
        "actual_task_count": actual_count,
        "backlog_exists": metadata is not None if metadata else False,
        "recorded_count": metadata.get("recorded_count") if metadata else None,
        "last_modified": str(metadata.get("last_modified")) if metadata else None
    }

    # Check 1: Backlog file doesn't exist
    if not metadata:
        return True, "ACTIVE-BACKLOG.md does not exist", details

    # Check 2: Task count mismatch
    if metadata.get("recorded_count") and metadata["recorded_count"] != actual_count:
        diff = actual_count - metadata["recorded_count"]
        return True, f"Task count mismatch: {metadata['recorded_count']} recorded vs {actual_count} actual ({'+' if diff > 0 else ''}{diff})", details

    # Check 3: File older than 7 days
    age = datetime.now() - metadata["last_modified"]
    if age > timedelta(days=7):
        return True, f"Backlog is {age.days} days old (>7 days)", details

    # All checks passed
    return False, "Backlog is current", details

def main():
    """Main entry point for hook."""
    is_stale, reason, details = check_staleness()

    result = {
        "is_stale": is_stale,
        "reason": reason,
        "details": details,
        "recommendation": "Run /backlog-sync to update" if is_stale else None
    }

    # Output for hook consumption
    print(json.dumps(result, indent=2, default=str))

    # Exit code: 0 = fresh, 1 = stale
    sys.exit(1 if is_stale else 0)

if __name__ == "__main__":
    main()
