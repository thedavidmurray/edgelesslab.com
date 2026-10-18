#!/usr/bin/env python3
"""Block actions that exceed the scope of what was explicitly requested.

Template hook for PreToolUse event.
Detects when an agent is about to take a high-risk action that wasn't
explicitly part of the original instruction.

Usage in settings.json:
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "command": "python3 .claude/hooks/scope-guard.py"
    }]
  }
}
"""

import json
import re
import sys

# ============================================================
# CONFIG
# ============================================================

# Verbs that require explicit authorization in the user's instruction
HIGH_RISK_VERBS = {
    # Financial
    "send", "transfer", "deposit", "withdraw", "swap", "approve",
    # Destructive
    "delete", "remove", "drop", "destroy", "wipe", "format", "purge",
    # Publishing
    "publish", "deploy", "release", "push",
    # Administrative
    "merge", "revoke", "reset", "force", "override",
}

# Commands that are always allowed (override high-risk verb detection)
SAFE_COMMANDS = [
    "git status",
    "git log",
    "git diff",
    "ls",
    "cat",
    "grep",
    "find",
    "echo",
    "pwd",
    "which",
    "npm test",
    "npm run",
    "python -m pytest",
]

# ============================================================


def extract_verbs(text: str) -> set[str]:
    """Extract words that match high-risk verb list."""
    words = set(re.findall(r"\b\w+\b", text.lower()))
    return words & HIGH_RISK_VERBS


def is_safe_command(command: str) -> bool:
    """Check if command matches a known-safe pattern."""
    cmd_lower = command.strip().lower()
    return any(cmd_lower.startswith(safe) for safe in SAFE_COMMANDS)


def main():
    try:
        raw = sys.stdin.read()
        if len(raw) > 100_000:
            sys.exit(0)
        hook_input = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        sys.exit(0)  # Fail open

    tool = hook_input.get("tool_name", "")
    if tool != "Bash":
        sys.exit(0)

    command = hook_input.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    if is_safe_command(command):
        sys.exit(0)

    risky_verbs = extract_verbs(command)
    if risky_verbs:
        verbs_str = ", ".join(sorted(risky_verbs))
        print(
            json.dumps(
                {
                    "error": (
                        f"Scope guard: high-risk action detected ({verbs_str}). "
                        "Verify this was explicitly requested before proceeding."
                    )
                }
            )
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
