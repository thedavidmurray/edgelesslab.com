#!/usr/bin/env python3
"""Block financial operations until verification protocol is completed.

Template hook for PreToolUse event.
Detects commands that interact with wallets, tokens, or exchanges
and requires explicit verification steps before proceeding.

Usage in settings.json:
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "command": "python3 .claude/hooks/financial-gate.py"
    }]
  }
}

----------------------------------------------------------------
SECURITY NOTE -- fix shipped 2026-04-07
----------------------------------------------------------------
Earlier versions of this hook stored verification state at
  /tmp/claude-financial-verification.json
which is world-writable on shared systems and had no session
scoping. Two concurrent Claude sessions would share a single
"verified" flag, so verifying a $1 test transfer in Session A
would silently unlock a $10,000 transfer in Session B.

The state file now lives at
  ~/.claude/state/financial-verification-<session_id>.json
with 0600 permissions, scoped to CLAUDE_SESSION_ID (falling back
to the current PID if not set). Cross-session leakage is no
longer possible.
----------------------------------------------------------------
"""

import json
import os
import re
import stat
import sys
import time
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================

# Patterns that indicate financial operations
FINANCIAL_PATTERNS = [
    r"(?i)transfer\s",
    r"(?i)send\s.*\b(eth|usdc|usdt|dai|matic|sol)\b",
    r"(?i)cast\s+send",  # Foundry
    r"(?i)npx\s+hardhat\s+.*transfer",
    r"(?i)approve\s+.*token",
    r"0x[a-fA-F0-9]{40}",  # Ethereum address
    r"(?i)(deposit|withdraw)\s",
    r"(?i)swap\s",
]

# Verification window: protocol completion is valid for 5 minutes
VERIFICATION_TTL_SECONDS = 300

# ============================================================


def _state_dir() -> Path:
    d = Path.home() / ".claude" / "state"
    d.mkdir(parents=True, exist_ok=True)
    # Tighten perms on the state dir too (0700)
    try:
        os.chmod(d, stat.S_IRWXU)
    except OSError:
        pass
    return d


def _session_id() -> str:
    return os.environ.get("CLAUDE_SESSION_ID") or f"pid-{os.getpid()}"


def _state_path() -> Path:
    return _state_dir() / f"financial-verification-{_session_id()}.json"


def is_financial_command(command: str) -> bool:
    """Check if command involves financial operations."""
    return any(re.search(p, command) for p in FINANCIAL_PATTERNS)


def verification_completed() -> bool:
    """Check if the verification protocol has been completed recently."""
    path = _state_path()
    try:
        with open(path) as f:
            state = json.load(f)
        if time.time() - state.get("timestamp", 0) < VERIFICATION_TTL_SECONDS:
            return bool(state.get("verified", False))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return False


def mark_verified() -> None:
    """Mark the verification protocol as completed for this session."""
    path = _state_path()
    state = {
        "verified": True,
        "timestamp": time.time(),
        "session_id": _session_id(),
    }
    # Write atomically, then lock to 0600
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    os.replace(tmp, path)
    print(
        f"Financial verification recorded for session {_session_id()}. "
        f"Valid for {VERIFICATION_TTL_SECONDS // 60} minutes."
    )


def main() -> None:
    try:
        raw = sys.stdin.read()
        if len(raw) > 100_000:
            sys.exit(0)
        hook_input = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        sys.exit(0)

    tool = hook_input.get("tool_name", "")
    if tool != "Bash":
        sys.exit(0)

    command = hook_input.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    if not is_financial_command(command):
        sys.exit(0)

    if verification_completed():
        sys.exit(0)  # Protocol already completed, allow

    print(
        json.dumps(
            {
                "error": (
                    "Financial operation detected. Complete the verification protocol first:\n"
                    "1. Read the transfer/deposit source code\n"
                    "2. Trace the full path (source -> intermediaries -> destination)\n"
                    "3. Test with minimum amount\n"
                    "4. Get user confirmation of destination address\n"
                    "Then run: python3 .claude/hooks/financial-gate.py --verify"
                )
            }
        )
    )
    sys.exit(2)


if __name__ == "__main__":
    if "--verify" in sys.argv:
        mark_verified()
    else:
        main()
