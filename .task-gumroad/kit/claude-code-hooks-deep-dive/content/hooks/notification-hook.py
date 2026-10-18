#!/usr/bin/env python3
"""Send notifications on session events via Telegram, Slack, or webhook.

Template hook for Stop event (session end).
Customize the NOTIFICATION_METHOD and credentials below.

Usage in settings.json:
{
  "hooks": {
    "Stop": [{
      "command": "python3 .claude/hooks/notification-hook.py"
    }]
  }
}

Environment variables:
  TELEGRAM_BOT_TOKEN  -- Telegram bot token
  TELEGRAM_CHAT_ID    -- Telegram chat/user ID
  SLACK_WEBHOOK_URL   -- Slack incoming webhook URL
  WEBHOOK_URL         -- Generic webhook URL (POST with JSON body)
"""

import json
import os
import subprocess
import sys
from urllib.request import Request, urlopen


# ============================================================
# CONFIG
# ============================================================

# Choose: "telegram", "slack", "webhook", or "all"
NOTIFICATION_METHOD = "telegram"

# Which events trigger notifications
NOTIFY_ON = {
    "session_end": True,
    "high_error_count": True,  # 5+ errors in a session
    "long_session": True,  # 60+ minutes
}

ERROR_THRESHOLD = 5
LONG_SESSION_MINUTES = 60

# ============================================================


def send_telegram(message: str) -> bool:
    """Send via Telegram Bot API."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return False

    try:
        subprocess.run(
            [
                "curl",
                "-s",
                "-X",
                "POST",
                f"https://api.telegram.org/bot{token}/sendMessage",
                "-d",
                f"chat_id={chat_id}",
                "-d",
                f"text={message}",
                "-d",
                "parse_mode=Markdown",
            ],
            capture_output=True,
            timeout=10,
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def send_slack(message: str) -> bool:
    """Send via Slack incoming webhook."""
    url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not url:
        return False

    try:
        data = json.dumps({"text": message}).encode()
        req = Request(url, data=data, headers={"Content-Type": "application/json"})
        urlopen(req, timeout=10)
        return True
    except Exception:
        return False


def send_webhook(message: str) -> bool:
    """Send via generic webhook (POST JSON)."""
    url = os.environ.get("WEBHOOK_URL", "")
    if not url:
        return False

    try:
        data = json.dumps({"message": message, "source": "claude-code-hook"}).encode()
        req = Request(url, data=data, headers={"Content-Type": "application/json"})
        urlopen(req, timeout=10)
        return True
    except Exception:
        return False


def notify(message: str):
    """Send notification via configured method(s)."""
    senders = {
        "telegram": send_telegram,
        "slack": send_slack,
        "webhook": send_webhook,
    }

    if NOTIFICATION_METHOD == "all":
        for sender in senders.values():
            sender(message)
    elif NOTIFICATION_METHOD in senders:
        senders[NOTIFICATION_METHOD](message)


def main():
    try:
        raw = sys.stdin.read()
        if len(raw) > 100_000:
            sys.exit(0)
        hook_input = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        sys.exit(0)

    event = hook_input.get("event", "")

    if event == "Stop" and NOTIFY_ON.get("session_end"):
        # Extract session context if available
        session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")
        notify(f"Claude Code session `{session_id}` ended.")

    # Always allow -- notification hooks should never block
    sys.exit(0)


if __name__ == "__main__":
    main()
