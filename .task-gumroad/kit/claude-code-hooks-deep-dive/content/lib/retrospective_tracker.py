#!/usr/bin/env python3
"""
retrospective_tracker.py - Helper for tracking retrospective completion

Call from /retrospective skill after email is sent:
    from lib.retrospective_tracker import mark_retrospective_complete
    mark_retrospective_complete(email_message_id="abc123")

Or via command line:
    python -m lib.retrospective_tracker --complete --email-id abc123
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

HOOKS_DIR = Path(__file__).parent.parent
RETRO_TRACKING_PATH = HOOKS_DIR / ".retrospective_status.json"


def get_current_session_id() -> str:
    """Get current session ID from environment."""
    return os.environ.get("CLAUDE_SESSION_ID", "unknown")


def mark_retrospective_complete(email_message_id: str = None) -> bool:
    """
    Mark retrospective as complete for current session.

    Args:
        email_message_id: Gmail message ID if email was sent

    Returns:
        True if successfully marked, False otherwise
    """
    session_id = get_current_session_id()

    try:
        # Load existing tracking or create new
        if RETRO_TRACKING_PATH.exists():
            with open(RETRO_TRACKING_PATH) as f:
                data = json.load(f)
        else:
            data = {"session_id": session_id}

        # Update status
        data["completed"] = True
        data["email_sent"] = bool(email_message_id)
        data["email_message_id"] = email_message_id
        data["completed_at"] = datetime.now().isoformat()

        # Save
        with open(RETRO_TRACKING_PATH, "w") as f:
            json.dump(data, f, indent=2)

        return True
    except Exception as e:
        print(f"Error marking retrospective complete: {e}", file=sys.stderr)
        return False


def is_retrospective_required() -> bool:
    """Check if retrospective is required for current session."""
    try:
        if RETRO_TRACKING_PATH.exists():
            with open(RETRO_TRACKING_PATH) as f:
                data = json.load(f)
                return data.get("required", False) and not data.get("completed", False)
    except Exception:
        pass
    return False


def get_retrospective_status() -> dict:
    """Get full retrospective status."""
    try:
        if RETRO_TRACKING_PATH.exists():
            with open(RETRO_TRACKING_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return {"required": False, "completed": False, "email_sent": False}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Track retrospective completion")
    parser.add_argument("--complete", action="store_true", help="Mark retrospective as complete")
    parser.add_argument("--email-id", type=str, help="Gmail message ID")
    parser.add_argument("--status", action="store_true", help="Show current status")

    args = parser.parse_args()

    if args.status:
        status = get_retrospective_status()
        print(json.dumps(status, indent=2))
    elif args.complete:
        success = mark_retrospective_complete(args.email_id)
        print(f"Retrospective marked complete: {success}")
        if not args.email_id:
            print("WARNING: No email ID provided - email_sent will be False")
    else:
        parser.print_help()
