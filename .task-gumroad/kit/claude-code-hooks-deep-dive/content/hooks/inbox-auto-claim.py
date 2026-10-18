#!/usr/bin/env python3
"""
inbox-auto-claim.py - Auto-claim a session inbox on first prompt.

Runs on UserPromptSubmit. Two phases:
  1. First prompt: claim inbox, ask for frequency
  2. Second prompt: if user replies with frequency, instruct Claude to start loop

Uses a PID-based marker file with state tracking.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

INBOX_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).parent.parent.parent)) / ".inboxes"
REGISTRY = INBOX_ROOT / "registry.json"
CLAIM_MARKER = Path(f"/tmp/claude-inbox-claimed-{os.getppid()}")


def ok(context=None):
    """Return a valid UserPromptSubmit hook response (allow prompt)."""
    if context:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context
            }
        }))
    else:
        print(json.dumps({}))


def main():
    hook_input = {}
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        pass

    user_prompt = hook_input.get("prompt", "").strip().lower()

    # Phase 2: Already claimed, waiting for frequency selection
    if CLAIM_MARKER.exists():
        try:
            marker_data = json.loads(CLAIM_MARKER.read_text())
        except (json.JSONDecodeError, OSError):
            ok()
            return

        # Already has frequency? Done.
        if marker_data.get("frequency"):
            ok()
            return

        # Check if this prompt is a frequency selection
        claimed_id = marker_data.get("session", "")
        inbox_path = INBOX_ROOT / claimed_id / "inbox"

        freq = None
        for f in ["5m", "15m", "30m", "60m"]:
            if user_prompt == f:
                freq = f
                break

        if freq:
            # Save frequency to marker
            marker_data["frequency"] = freq
            CLAIM_MARKER.write_text(json.dumps(marker_data))

            ok(
                f"Starting **{claimed_id}** inbox check loop at **{freq}** intervals.\n\n"
                f"Inbox path: `{inbox_path}`\n\n"
                f"Run: `/loop {freq} check inbox at {inbox_path} for new .md files, process any tasks found, write responses to {INBOX_ROOT / claimed_id}/outbox/, and move processed files to {inbox_path}/processed/`"
            )
        elif user_prompt == "skip":
            marker_data["frequency"] = "skip"
            CLAIM_MARKER.write_text(json.dumps(marker_data))

            ok(f"Inbox **{claimed_id}** active, no auto-check. Check manually: `python3 .inboxes/check_inbox.py {claimed_id}`")
        else:
            # Not a frequency reply -- just continue
            ok()
        return

    # Phase 1: First prompt -- claim an inbox

    if not REGISTRY.exists():
        ok()
        return

    try:
        registry = json.loads(REGISTRY.read_text())
    except (json.JSONDecodeError, OSError):
        ok()
        return

    sessions = registry.get("sessions", {})

    # Find first unclaimed numbered session
    claimed_id = None
    for sid in sorted(sessions.keys()):
        if sid == "dispatch":
            continue
        info = sessions[sid]
        if not info.get("claimed", False):
            claimed_id = sid
            break

    if not claimed_id:
        ok("All session inboxes are claimed. Run `/assign-inbox status` to see who has what.")
        return

    # Claim it
    sessions[claimed_id] = {
        "claimed": True,
        "claimed_by": f"pid-{os.getppid()}",
        "claimed_at": datetime.now().isoformat()
    }
    registry["sessions"] = sessions

    try:
        REGISTRY.write_text(json.dumps(registry, indent=2) + "\n")
    except OSError:
        ok()
        return

    # Write marker WITHOUT frequency (phase 1 complete)
    CLAIM_MARKER.write_text(json.dumps({
        "session": claimed_id,
        "pid": os.getppid(),
        "claimed_at": datetime.now().isoformat(),
        "frequency": None
    }))

    # Ensure inbox/outbox dirs exist
    inbox_path = INBOX_ROOT / claimed_id / "inbox"
    outbox_path = INBOX_ROOT / claimed_id / "outbox"
    inbox_path.mkdir(parents=True, exist_ok=True)
    outbox_path.mkdir(parents=True, exist_ok=True)

    ok(
        f"Auto-claimed inbox: **{claimed_id}**\n"
        f"Inbox: `{inbox_path}`\n"
        f"Outbox: `{outbox_path}`\n\n"
        f"Inbox check frequency? `5m` `15m` `30m` `60m` `skip`"
    )


if __name__ == "__main__":
    main()
