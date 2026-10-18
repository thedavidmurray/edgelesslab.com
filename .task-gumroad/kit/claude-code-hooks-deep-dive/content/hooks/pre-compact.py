#!/usr/bin/env python3
"""
pre-compact.py - Hook for PreCompact event
Backs up important context before context window compaction.
Ensures critical information is preserved across compactions.

SECURITY HARDENED: 2024-12-23
- Input sanitization before writing to disk
- Secrets scrubbing in context data
- Path validation and size limits
- Safe file operations
"""

import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path

# Configuration
HOOKS_DIR = Path(__file__).parent
BACKUP_DIR = HOOKS_DIR / "context_backups"
MAX_BACKUPS = 10  # Keep last N backups

# Security constants
MAX_INPUT_SIZE = 500000  # 500KB max for context
MAX_BACKUP_SIZE = 100000  # 100KB per backup file
MAX_ITEMS_PER_LIST = 100  # Limit list sizes

# Patterns for secrets that should be redacted
SECRET_PATTERNS = [
    (re.compile(r'sk-[A-Za-z0-9]{20,}'), '[REDACTED_OPENAI_KEY]'),
    (re.compile(r'sk-ant-[A-Za-z0-9-]{20,}'), '[REDACTED_ANTHROPIC_KEY]'),
    (re.compile(r'xoxb-[A-Za-z0-9-]+'), '[REDACTED_SLACK_TOKEN]'),
    (re.compile(r'xoxp-[A-Za-z0-9-]+'), '[REDACTED_SLACK_TOKEN]'),
    (re.compile(r'ghp_[A-Za-z0-9]{36,}'), '[REDACTED_GITHUB_TOKEN]'),
    (re.compile(r'gho_[A-Za-z0-9]{36,}'), '[REDACTED_GITHUB_TOKEN]'),
    (re.compile(r'github_pat_[A-Za-z0-9_]{22,}'), '[REDACTED_GITHUB_PAT]'),
    (re.compile(r'AKIA[A-Z0-9]{16}'), '[REDACTED_AWS_KEY]'),
    (re.compile(r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*'), '[REDACTED_JWT]'),
    (re.compile(r'-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'), '[REDACTED_PRIVATE_KEY]'),
    (re.compile(r'password["\']?\s*[:=]\s*["\'][^"\']{4,}["\']', re.IGNORECASE), 'password=[REDACTED]'),
    (re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\'][^"\']{8,}["\']', re.IGNORECASE), 'api_key=[REDACTED]'),
    (re.compile(r'secret["\']?\s*[:=]\s*["\'][^"\']{8,}["\']', re.IGNORECASE), 'secret=[REDACTED]'),
    (re.compile(r'token["\']?\s*[:=]\s*["\'][^"\']{8,}["\']', re.IGNORECASE), 'token=[REDACTED]'),
]


def scrub_secrets(text: str) -> str:
    """Remove sensitive data from text before writing to disk."""
    if not isinstance(text, str):
        text = str(text)

    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)

    return text


def scrub_dict(data: dict, depth: int = 0) -> dict:
    """Recursively scrub secrets from dictionary values."""
    if depth > 10:  # Prevent infinite recursion
        return {"error": "max_depth_exceeded"}

    scrubbed = {}
    for key, value in list(data.items())[:MAX_ITEMS_PER_LIST]:
        if isinstance(value, str):
            scrubbed[key] = scrub_secrets(value[:10000])
        elif isinstance(value, dict):
            scrubbed[key] = scrub_dict(value, depth + 1)
        elif isinstance(value, list):
            scrubbed[key] = [
                scrub_dict(item, depth + 1) if isinstance(item, dict)
                else scrub_secrets(str(item)[:1000]) if isinstance(item, str)
                else item
                for item in value[:MAX_ITEMS_PER_LIST]
            ]
        else:
            scrubbed[key] = value

    return scrubbed


def validate_path_within_boundary(path: Path, boundary: Path) -> bool:
    """Verify a path resolves within expected boundary."""
    try:
        resolved = path.resolve()
        boundary_resolved = boundary.resolve()
        return str(resolved).startswith(str(boundary_resolved))
    except (OSError, ValueError):
        return False

def ensure_backup_dir():
    """Ensure backup directory exists."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def cleanup_old_backups():
    """Remove old backups beyond MAX_BACKUPS."""
    try:
        backups = sorted(BACKUP_DIR.glob("context_*.json"), reverse=True)
        for old_backup in backups[MAX_BACKUPS:]:
            old_backup.unlink()
    except Exception:
        pass

def sanitize_session_id(session_id: str) -> str:
    """Sanitize session ID for safe use in filenames."""
    if not isinstance(session_id, str):
        return "unknown"
    # Only allow alphanumeric, underscore, hyphen
    return "".join(c for c in session_id[:64] if c.isalnum() or c in "-_") or "unknown"


def save_context_backup(context_data: dict) -> str:
    """Save context backup with security checks and return filename."""
    # Verify backup directory is within hooks directory
    if not validate_path_within_boundary(BACKUP_DIR, HOOKS_DIR):
        return "error: backup_dir_outside_boundary"

    ensure_backup_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"context_{timestamp}.json"
    filepath = BACKUP_DIR / filename

    # Verify final path is still within boundary
    if not validate_path_within_boundary(filepath, BACKUP_DIR):
        return "error: path_traversal_detected"

    # Sanitize session ID
    session_id = sanitize_session_id(os.environ.get("CLAUDE_SESSION_ID", "unknown"))

    # Scrub secrets from context data
    scrubbed_context = scrub_dict(context_data) if isinstance(context_data, dict) else {}

    backup_data = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "context": scrubbed_context,
        "metadata": {
            "hook_version": "2.0.0-hardened",
            "reason": "pre_compact"
        }
    }

    try:
        # Serialize and check size
        content = json.dumps(backup_data, indent=2, default=str)
        if len(content) > MAX_BACKUP_SIZE:
            # Truncate context if too large
            backup_data["context"] = {"truncated": True, "reason": "size_limit_exceeded"}
            backup_data["metadata"]["original_size"] = len(content)
            content = json.dumps(backup_data, indent=2, default=str)

        # Use atomic write pattern
        temp_filepath = filepath.with_suffix('.tmp')
        with open(temp_filepath, "w") as f:
            f.write(content)
        temp_filepath.rename(filepath)

        cleanup_old_backups()
        return filename
    except Exception as e:
        # Scrub error message before returning
        return f"error: {scrub_secrets(str(e)[:100])}"

def extract_critical_context(hook_input: dict) -> dict:
    """Extract and sanitize critical context that should be preserved."""
    critical = {
        "todos": [],
        "important_files": [],
        "key_decisions": [],
        "session_notes": []
    }

    if not isinstance(hook_input, dict):
        return critical

    # Extract and sanitize todos if present
    todos = hook_input.get("todos", [])
    if isinstance(todos, list):
        critical["todos"] = [
            scrub_secrets(str(t)[:500]) if isinstance(t, str)
            else scrub_dict(t) if isinstance(t, dict)
            else t
            for t in todos[:MAX_ITEMS_PER_LIST]
        ]

    # Extract and sanitize conversation summary if present
    summary = hook_input.get("summary", "")
    if isinstance(summary, str) and summary:
        critical["session_notes"].append(scrub_secrets(summary[:5000]))

    # Extract and sanitize any explicitly marked important items
    important = hook_input.get("important", [])
    if isinstance(important, list):
        critical["key_decisions"] = [
            scrub_secrets(str(item)[:500]) if isinstance(item, str)
            else scrub_dict(item) if isinstance(item, dict)
            else item
            for item in important[:MAX_ITEMS_PER_LIST]
        ]

    # Extract and sanitize file context if present
    files = hook_input.get("files", [])
    if isinstance(files, list):
        # Only keep file paths, sanitize them
        critical["important_files"] = [
            scrub_secrets(str(f)[:500])
            for f in files[:20]
            if isinstance(f, str)
        ]

    return critical

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

    # Extract and sanitize critical context
    critical_context = extract_critical_context(hook_input)

    # Save backup (function handles its own security checks)
    backup_result = save_context_backup({
        "critical": critical_context,
        # Only include key names, not values, to avoid data leakage
        "raw_input_keys": [
            str(k)[:50] for k in list(hook_input.keys())[:20]
        ] if hook_input else []
    })

    # Build response with correct schema
    # Claude Code expects: continue (bool), decision (approve|block), not "decision": "continue"
    response = {
        "continue": True
    }

    # Output JSON response
    print(json.dumps(response))

if __name__ == "__main__":
    main()
