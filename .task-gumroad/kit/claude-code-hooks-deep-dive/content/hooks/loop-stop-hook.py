#!/usr/bin/env python3
"""
loop-stop-hook.py - Stop hook for Ralph Wiggum loops

Prevents Claude from exiting prematurely during active loops by:
1. Checking for official Ralph state file at .claude/.ralph-loop.local.md
2. Enforcing max iteration limit (default 50)
3. Looking for completion signal in conversation context
4. Returning exit code 0 (allow exit) or 2 (block exit)

Integration:
- Works with official /ralph-loop skill (ralph-wiggum:ralph-loop)
- Use /cancel-ralph to stop an active loop
- Respects binary completion criteria from task-92 (verify-completion.py)

Exit Codes:
    0 - Allow session exit (no active loop or completion criteria met)
    2 - Block session exit (loop active, continue working)

Usage:
    Automatically called by Claude Code during Stop event.
    Add to .claude/settings.local.json hooks.Stop configuration.

SECURITY HARDENED: 2026-01-16
- Input validation and sanitization
- Safe file operations
- Bounded iteration limits
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Configuration
PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).parent.parent.parent))
# Official Ralph Wiggum state file (created by /ralph-loop skill)
RALPH_MARKER = PROJECT_DIR / ".claude" / ".ralph-loop.local.md"
# Legacy state file (deprecated - left for backwards compatibility)
STATE_FILE = PROJECT_DIR / ".claude" / "loops" / "state.json"

# Safety limits
MAX_ITERATIONS = 50
MAX_SESSION_DURATION_HOURS = 8

# Completion signals to look for
COMPLETION_SIGNALS = [
    "<promise>COMPLETE</promise>",
    "<promise>ALL PROJECTS COMPLETE</promise>",
    "ALL PROJECTS COMPLETE",
    "task completed and verified"
]


def load_state() -> dict:
    """Load current loop state with error handling."""
    if not STATE_FILE.exists():
        return {}

    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
            if not isinstance(state, dict):
                return {}
            return state
    except (json.JSONDecodeError, OSError):
        return {}


def is_ralph_active() -> bool:
    """Check if Ralph plugin is active."""
    return RALPH_MARKER.exists()


def check_iteration_limit(state: dict) -> tuple[bool, str]:
    """Check if iteration limit exceeded.

    Returns:
        (exceeded, message) tuple
    """
    iteration = state.get("iteration", 0)
    if iteration >= MAX_ITERATIONS:
        return True, f"Max iterations ({MAX_ITERATIONS}) reached. Session will exit."
    return False, ""


def check_session_duration(state: dict) -> tuple[bool, str]:
    """Check if session has been running too long.

    Returns:
        (exceeded, message) tuple
    """
    session_start = state.get("session_start")
    if not session_start:
        return False, ""

    try:
        start = datetime.fromisoformat(session_start.replace("Z", "+00:00"))
        duration_hours = (datetime.now().astimezone() - start.astimezone()).total_seconds() / 3600

        if duration_hours >= MAX_SESSION_DURATION_HOURS:
            return True, f"Session duration ({duration_hours:.1f} hours) exceeded limit ({MAX_SESSION_DURATION_HOURS} hours)."
    except (ValueError, TypeError):
        pass

    return False, ""


def check_completion_signal(hook_input: dict) -> bool:
    """Check if completion signal is present in conversation context.

    Args:
        hook_input: Hook input from stdin (may contain conversation context)

    Returns:
        True if completion signal found
    """
    # Check if hook input contains completion signals
    input_str = json.dumps(hook_input).lower()

    for signal in COMPLETION_SIGNALS:
        if signal.lower() in input_str:
            return True

    return False


def is_loop_active(state: dict) -> bool:
    """Determine if loop is currently active.

    Loop is active if:
    - current_project is set
    - OR Ralph plugin is active
    """
    has_current_project = bool(state.get("current_project"))
    ralph_active = is_ralph_active()

    return has_current_project or ralph_active


def should_block_exit(hook_input: dict) -> tuple[bool, str]:
    """Determine if session exit should be blocked.

    Returns:
        (block, reason) tuple
    """
    state = load_state()

    # Check if any loop is active
    if not is_loop_active(state):
        return False, "No active loop detected"

    # Check for completion signal
    if check_completion_signal(hook_input):
        return False, "Completion signal detected"

    # Check iteration limit (safety exit)
    limit_exceeded, limit_msg = check_iteration_limit(state)
    if limit_exceeded:
        return False, limit_msg

    # Check session duration (safety exit)
    duration_exceeded, duration_msg = check_session_duration(state)
    if duration_exceeded:
        return False, duration_msg

    # Loop is active and no completion signal - block exit
    iteration = state.get("iteration", 0)
    current_project = state.get("current_project", "unknown")
    last_action = state.get("last_action", "unknown")

    reason = (
        f"Loop is active (iteration {iteration}):\n"
        f"   Current project: {current_project}\n"
        f"   Last action: {last_action}\n"
        f"   Complete the task or use /cancel-loop to exit"
    )

    return True, reason


def main():
    """Main hook entry point."""
    # Read hook input from stdin (with size limit for security)
    MAX_INPUT_SIZE = 100000  # 100KB

    try:
        raw_input = sys.stdin.read(MAX_INPUT_SIZE)
        hook_input = json.loads(raw_input)
        if not isinstance(hook_input, dict):
            hook_input = {}
    except (json.JSONDecodeError, ValueError):
        hook_input = {}

    # Determine if we should block exit
    block, reason = should_block_exit(hook_input)

    if block:
        # Block exit - print clear message to stderr
        print(f"\n🔄 SESSION EXIT BLOCKED - Loop Active", file=sys.stderr)
        print(f"   {reason}\n", file=sys.stderr)

        # Exit with code 2 to block session end
        sys.exit(2)
    else:
        # Allow exit - optionally print reason to stderr
        if "No active loop" not in reason:
            print(f"\n✅ Loop exit allowed: {reason}", file=sys.stderr)

        # Exit with code 0 to allow session end
        sys.exit(0)


if __name__ == "__main__":
    main()
