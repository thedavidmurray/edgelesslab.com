#!/usr/bin/env bash
# =============================================================================
# slack-notify.sh — Post to Slack on task completion
# =============================================================================
#
# WHAT IT DOES:
#   When a Claude Code session ends (Stop event), sends a summary notification
#   to a Slack channel via webhook. Includes project name, session duration,
#   and a brief summary from the session context.
#
# WHEN TO USE IT:
#   Teams where multiple people want visibility into when AI-assisted work
#   completes. Also useful for personal Slack bots to track your own output.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/slack-notify.sh
#   2. Create a Slack incoming webhook: https://api.slack.com/messaging/webhooks
#   3. Set SLACK_WEBHOOK_URL in your environment or .env file
#   4. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "Stop": [
#         {
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/slack-notify.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   SLACK_WEBHOOK_URL   — Required. Slack incoming webhook URL
#   SLACK_CHANNEL       — Override channel (uses webhook default if not set)
#   SLACK_ICON_EMOJI    — Emoji icon (default: :robot_face:)
#   SLACK_USERNAME      — Bot display name (default: Claude Code)
# =============================================================================

set -euo pipefail

# --- Load .env if present ---
if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source .env 2>/dev/null || true
  set +a
fi

WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
ICON="${SLACK_ICON_EMOJI:-:robot_face:}"
USERNAME="${SLACK_USERNAME:-Claude Code}"

if [ -z "$WEBHOOK_URL" ]; then
  echo "SLACK_WEBHOOK_URL not set — skipping Slack notification." >&2
  exit 0
fi

if ! command -v curl &>/dev/null; then
  echo "curl not found — cannot send Slack notification." >&2
  exit 0
fi

# --- Build message ---
PROJECT="$(basename "$(pwd)")"
TIMESTAMP="$(date +"%Y-%m-%d %H:%M")"

# Read session state if available
DURATION="unknown"
STATE_FILE="${SESSION_STATE_FILE:-/tmp/claude-session-state.json}"
if [ -f "$STATE_FILE" ]; then
  DURATION="$(python3 -c "
import json, time
try:
    with open('${STATE_FILE}') as f:
        state = json.load(f)
    elapsed = time.time() - state['start_time']
    mins = int(elapsed // 60)
    print(f'{mins}m')
except:
    print('unknown')
" 2>/dev/null || echo "unknown")"
fi

PAYLOAD="$(python3 -c "
import json
payload = {
    'username': '${USERNAME}',
    'icon_emoji': '${ICON}',
    'text': 'Claude Code session completed',
    'blocks': [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '*Claude Code session ended*'
            }
        },
        {
            'type': 'section',
            'fields': [
                {'type': 'mrkdwn', 'text': f'*Project:*\n${PROJECT}'},
                {'type': 'mrkdwn', 'text': f'*Duration:*\n${DURATION}'},
                {'type': 'mrkdwn', 'text': f'*Time:*\n${TIMESTAMP}'},
            ]
        }
    ]
}
print(json.dumps(payload))
" 2>/dev/null)"

# Add channel override if set
if [ -n "${SLACK_CHANNEL:-}" ]; then
  PAYLOAD="$(echo "$PAYLOAD" | python3 -c "
import json, sys
d = json.load(sys.stdin)
d['channel'] = '${SLACK_CHANNEL}'
print(json.dumps(d))
")"
fi

# --- Send ---
RESPONSE="$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "$WEBHOOK_URL" 2>/dev/null)"

if [ "$RESPONSE" = "200" ]; then
  echo "Slack notification sent." >&2
else
  echo "Slack notification failed (HTTP ${RESPONSE})." >&2
fi

exit 0
