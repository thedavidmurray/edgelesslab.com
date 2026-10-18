#!/usr/bin/env python3
"""Block commits that don't meet quality standards.

Template hook for PreToolUse event.
Customize the CONFIG section below for your project.

Usage in settings.json:
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "command": "python3 .claude/hooks/pre-commit-quality-gate.py"
    }]
  }
}
"""

import json
import os
import subprocess
import sys

# ============================================================
# CONFIG -- customize these for your project
# ============================================================

REQUIRED_TESTS = True
TEST_COMMAND = ["npm", "test"]
TEST_TIMEOUT = 120  # seconds

MAX_FILE_SIZE_KB = 500

BLOCKED_EXTENSIONS = [".env", ".key", ".pem", ".p12", ".pfx"]
BLOCKED_FILENAMES = ["credentials.json", "secrets.yaml", ".env.local"]

REQUIRE_LINT = False
LINT_COMMAND = ["npx", "eslint", "--quiet", "."]

# ============================================================


def get_staged_files() -> list[str]:
    """Get list of files staged for commit."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().split("\n") if f]


def check_blocked_files(staged: list[str]) -> str | None:
    """Check for files that should never be committed."""
    for filepath in staged:
        basename = os.path.basename(filepath)
        if basename in BLOCKED_FILENAMES:
            return f"Blocked file: {filepath}"
        if any(filepath.endswith(ext) for ext in BLOCKED_EXTENSIONS):
            return f"Blocked file type: {filepath}"
    return None


def check_file_sizes(staged: list[str]) -> str | None:
    """Check that no staged file exceeds the size limit."""
    for filepath in staged:
        if not os.path.exists(filepath):
            continue
        size_kb = os.path.getsize(filepath) / 1024
        if size_kb > MAX_FILE_SIZE_KB:
            return f"File too large ({size_kb:.0f}KB > {MAX_FILE_SIZE_KB}KB): {filepath}"
    return None


def check_tests() -> str | None:
    """Run tests and check they pass."""
    if not REQUIRED_TESTS:
        return None
    try:
        result = subprocess.run(
            TEST_COMMAND, capture_output=True, text=True, timeout=TEST_TIMEOUT
        )
        if result.returncode != 0:
            return f"Tests failed (exit {result.returncode}). Fix before committing."
    except subprocess.TimeoutExpired:
        return f"Tests timed out after {TEST_TIMEOUT}s"
    except FileNotFoundError:
        return f"Test command not found: {TEST_COMMAND[0]}"
    return None


def check_lint() -> str | None:
    """Run linter and check it passes."""
    if not REQUIRE_LINT:
        return None
    try:
        result = subprocess.run(
            LINT_COMMAND, capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return "Lint errors found. Fix before committing."
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # Non-blocking -- lint failure shouldn't prevent commit
    return None


def main():
    try:
        raw = sys.stdin.read()
        if len(raw) > 100_000:  # 100KB input limit
            sys.exit(0)

        hook_input = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        sys.exit(0)  # Fail open

    tool = hook_input.get("tool_name", "")
    if tool != "Bash":
        sys.exit(0)

    command = hook_input.get("tool_input", {}).get("command", "")
    if "git commit" not in command:
        sys.exit(0)

    staged = get_staged_files()
    if not staged:
        sys.exit(0)

    # Run checks that take the staged file list
    for check_fn in (check_blocked_files, check_file_sizes):
        error = check_fn(staged)
        if error:
            print(json.dumps({"error": error}))
            sys.exit(2)

    # Run checks that are standalone
    for check_fn in (check_tests, check_lint):
        error = check_fn()
        if error:
            print(json.dumps({"error": error}))
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
