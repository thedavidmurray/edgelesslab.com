#!/usr/bin/env python3
"""Track estimated session costs and enforce budget limits.

Template hook for PostToolUse event.
Tracks running cost estimates and blocks execution when budget exceeded.

Usage in settings.json:
{
  "hooks": {
    "PostToolUse": [{
      "command": "python3 .claude/hooks/cost-tracker.py"
    }]
  }
}

Environment variables:
  MAX_SESSION_COST  -- Maximum cost in USD before blocking (default: 5.00)
  COST_TRACKER_DIR  -- Directory for state files (default: /tmp)
"""

import json
import os
import sys
import time

# ============================================================
# CONFIG
# ============================================================

MAX_COST = float(os.environ.get("MAX_SESSION_COST", "5.0"))
STATE_DIR = os.environ.get("COST_TRACKER_DIR", "/tmp")
STATE_FILE = os.path.join(STATE_DIR, f"claude-cost-{os.getppid()}.json")

# Rough cost estimates per tool call (USD)
# These are approximations -- adjust based on your model and usage
COST_ESTIMATES = {
    "Bash": 0.005,
    "Read": 0.003,
    "Write": 0.008,
    "Edit": 0.008,
    "Grep": 0.002,
    "Glob": 0.001,
    "Agent": 0.05,  # Subagents are expensive
    "WebFetch": 0.01,
    "WebSearch": 0.01,
}
DEFAULT_COST = 0.005

# ============================================================


def load_state() -> dict:
    """Load running cost state."""
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "total_cost": 0.0,
            "tool_count": 0,
            "started_at": time.time(),
            "tools": {},
        }


def save_state(state: dict):
    """Save running cost state atomically."""
    tmp = STATE_FILE + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(state, f)
        os.rename(tmp, STATE_FILE)
    except OSError:
        pass  # Non-critical -- don't crash


def main():
    try:
        raw = sys.stdin.read()
        if len(raw) > 100_000:
            sys.exit(0)
        hook_input = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        sys.exit(0)

    tool = hook_input.get("tool_name", "unknown")
    cost = COST_ESTIMATES.get(tool, DEFAULT_COST)

    state = load_state()
    state["total_cost"] += cost
    state["tool_count"] += 1
    state["tools"][tool] = state["tools"].get(tool, 0) + 1

    save_state(state)

    if state["total_cost"] > MAX_COST:
        elapsed = (time.time() - state["started_at"]) / 60
        print(
            json.dumps(
                {
                    "error": (
                        f"Session cost limit reached: ${state['total_cost']:.2f} / ${MAX_COST:.2f} "
                        f"({state['tool_count']} tools in {elapsed:.0f}min). "
                        f"Set MAX_SESSION_COST env var to increase."
                    )
                }
            )
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
