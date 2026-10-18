#!/usr/bin/env python3
"""Scan file writes and edits for accidentally included secrets.

Template hook for PreToolUse event.
Blocks Write/Edit operations that would introduce secrets into tracked files.

Usage in settings.json:
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Write|Edit",
      "command": "python3 .claude/hooks/secrets-scanner.py"
    }]
  }
}
"""

import json
import re
import sys

# ============================================================
# CONFIG -- add patterns for your organization's secrets
# ============================================================

SECRET_PATTERNS = [
    # API Keys (generic)
    (r"(?i)(api[_-]?key|api[_-]?secret)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{20,}", "API key"),
    # OpenAI
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API key"),
    # Anthropic
    (r"sk-ant-[a-zA-Z0-9\-]{20,}", "Anthropic API key"),
    # GitHub PAT
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub PAT"),
    (r"github_pat_[a-zA-Z0-9_]{82}", "GitHub fine-grained PAT"),
    # AWS
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"(?i)aws_secret_access_key\s*[:=]\s*[a-zA-Z0-9/+=]{40}", "AWS secret key"),
    # Private keys
    (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "Private key"),
    # JWTs
    (r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]+", "JWT"),
    # Database URLs with credentials
    (r"(?i)(postgres|mysql|mongodb)://[^:]+:[^@]+@", "Database URL with credentials"),
    # Slack tokens
    (r"xox[baprs]-[0-9]{10,13}-[a-zA-Z0-9-]+", "Slack token"),
    # Stripe
    (r"sk_live_[a-zA-Z0-9]{24,}", "Stripe secret key"),
    # Twilio
    (r"(?i)twilio.*['\"][a-f0-9]{32}['\"]", "Twilio auth token"),
    # Generic password assignments
    (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Hardcoded password"),
]

# Files where secrets are expected (won't trigger alerts)
ALLOWLISTED_PATHS = [
    ".env.example",
    ".env.template",
    "test_",
    "_test.",
    ".test.",
    "mock",
    "fixture",
]

# ============================================================


def is_allowlisted(filepath: str) -> bool:
    """Check if file is in the allowlist."""
    return any(pattern in filepath for pattern in ALLOWLISTED_PATHS)


def scan_content(content: str) -> list[tuple[str, str]]:
    """Scan content for secret patterns. Returns list of (match, type)."""
    findings = []
    for pattern, secret_type in SECRET_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            # Don't include the actual secret in the finding
            findings.append((secret_type, f"{len(matches)} occurrence(s)"))
    return findings


def main():
    try:
        raw = sys.stdin.read()
        if len(raw) > 500_000:  # 500KB limit
            sys.exit(0)
        hook_input = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        sys.exit(0)

    tool = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only check Write and Edit operations
    if tool == "Write":
        filepath = tool_input.get("file_path", "")
        content = tool_input.get("content", "")
    elif tool == "Edit":
        filepath = tool_input.get("file_path", "")
        content = tool_input.get("new_string", "")
    else:
        sys.exit(0)

    if not filepath or not content:
        sys.exit(0)

    if is_allowlisted(filepath):
        sys.exit(0)

    findings = scan_content(content)
    if findings:
        types = ", ".join(f"{t} ({c})" for t, c in findings)
        print(
            json.dumps(
                {
                    "error": (
                        f"Potential secrets detected in {filepath}: {types}. "
                        "Remove secrets before writing. Use environment variables instead."
                    )
                }
            )
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
