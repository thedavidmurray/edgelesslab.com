#!/usr/bin/env python3
"""Classify operations by reversibility and enforce appropriate checks.

Template hook for PreToolUse event.
Categorizes each operation as trivial/reversible/soft-irreversible/hard-irreversible
and blocks hard-irreversible actions without confirmation.

Usage in settings.json:
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash|Write|Edit",
      "command": "python3 .claude/hooks/reversibility-classifier.py"
    }]
  }
}
"""

import json
import re
import sys

# ============================================================
# CONFIG -- customize for your project
# ============================================================

CLASSIFICATIONS = {
    "trivial": {
        "patterns": [
            r"^(ls|cat|head|tail|grep|find|which|pwd|echo|date|wc|diff)\b",
            r"^git\s+(status|log|diff|show|branch\s*$)",
            r"^npm\s+(test|run\s+test|run\s+lint)",
            r"^python.*\s+-m\s+pytest",
        ],
        "action": "allow",
    },
    "reversible": {
        "patterns": [
            r"^git\s+(add|commit|stash|checkout\s+-b)",
            r"^npm\s+(install|run\s+build)",
            r"^mkdir\b",
            r"^touch\b",
        ],
        "action": "allow",
    },
    "soft_irreversible": {
        "patterns": [
            r"^git\s+push\b",
            r"^curl\s+.*-X\s+(POST|PUT|DELETE|PATCH)",
            r"^gh\s+(pr|issue)\s+create",
            r"^npm\s+publish",
        ],
        "action": "warn",  # Log warning but allow
    },
    "hard_irreversible": {
        "patterns": [
            r"^git\s+push\s+.*--force",
            r"^git\s+reset\s+--hard",
            r"^rm\s+(-[a-zA-Z]*f|--force)",
            r"(?i)DROP\s+(TABLE|DATABASE)",
            r"(?i)DELETE\s+FROM\s+(?!.*WHERE)",
            r"(?i)(transfer|send)\s+.*\b(eth|usdc|token)\b",
            r"^terraform\s+destroy",
            r"^kubectl\s+delete\s+namespace",
        ],
        "action": "block",
    },
}

# ============================================================


def classify_command(command: str) -> tuple[str, str]:
    """Classify a command by reversibility. Returns (level, action)."""
    cmd = command.strip()

    # Check from most restrictive to least
    for level in ["hard_irreversible", "soft_irreversible", "reversible", "trivial"]:
        config = CLASSIFICATIONS[level]
        for pattern in config["patterns"]:
            if re.search(pattern, cmd, re.IGNORECASE):
                return level, config["action"]

    return "unknown", "allow"  # Default: allow unknown commands


def classify_file_op(tool: str, tool_input: dict) -> tuple[str, str]:
    """Classify file operations by reversibility."""
    filepath = tool_input.get("file_path", "")

    # Writing to critical paths is soft-irreversible
    critical_paths = ["package.json", "CLAUDE.md", ".env", "Dockerfile"]
    if any(filepath.endswith(p) for p in critical_paths):
        return "soft_irreversible", "warn"

    return "reversible", "allow"


def main():
    try:
        raw = sys.stdin.read()
        if len(raw) > 100_000:
            sys.exit(0)
        hook_input = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        sys.exit(0)

    tool = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool == "Bash":
        command = tool_input.get("command", "")
        level, action = classify_command(command)
    elif tool in ("Write", "Edit"):
        level, action = classify_file_op(tool, tool_input)
    else:
        sys.exit(0)

    if action == "block":
        print(
            json.dumps(
                {
                    "error": (
                        f"Hard-irreversible operation detected (level: {level}). "
                        "This action cannot be undone. Verify it was explicitly "
                        "requested and confirm before proceeding."
                    )
                }
            )
        )
        sys.exit(2)

    if action == "warn":
        # Log warning to stderr (doesn't block, but visible in output)
        print(
            f"[safety] Soft-irreversible operation ({level}): consider confirming with user",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
