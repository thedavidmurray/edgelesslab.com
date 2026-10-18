#!/usr/bin/env bash
# =============================================================================
# telegram-notify.sh — Send Telegram message on Claude Code events
# =============================================================================
#
# WHAT IT DOES:
#   Sends a Telegram message to a configured chat when Claude Code sessions
#   start, end, or when a task is completed. Works with both personal bots
#   and group chats. Useful for mobile awareness of long-running tasks.
#
# WHEN TO USE IT:
#   When you want mobile notifications without setting up a full push
#   notification service. Telegram bots are free, private, and reliable.
#
# HOW TO INSTALL:
#   1. Create a bot via @BotFather on Telegram
#   2. Get your chat_id: message your bot, then visit
#      https://api.telegram.org/bot<TOKEN>/getUpdates
#   3. Copy to .claude/hooks/telegram-notify.sh
#   4. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
#   5. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "Stop": [
#         {
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/telegram-notify.sh stop"
#             }
#           ]
#         }
#       ],
#       "SessionStart": [
#         {
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/telegram-notify.sh start"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   TELEGRAM_BOT_TOKEN   — Required. Bot token from @BotFather
#   TELEGRAM_CHAT_ID     — Required. Chat ID (personal or group)
#   TELEGRAM_PARSE_MODE  — Message format: Markdown|HTML (default: Markdown)
# =============================================================================

set -euo pipefail

# --- Load .env if present ---
if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source .env 2>/dev/null || true
  set +a
fi

BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
CHAT_ID="${TELEGRAM_CHAT_ID:-}"
PARSE_MODE="${TELEGRAM_PARSE_MODE:-Markdown}"
ACTION="${1:-stop}"

if [ -z "$BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
  echo "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skipping." >&2
  exit 0
fi

if ! command -v curl &>/dev/null; then
  echo "curl not found — cannot send Telegram message." >&2
  exit 0
fi

PROJECT="$(basename "$(pwd)")"
TIMESTAMP="$(date +"%H:%M")"
DATE="$(date +"%Y-%m-%d")"

# --- Build message ---
case "$ACTION" in
  start)
    MESSAGE="*Claude Code session started*
Project: \`${PROJECT}\`
Time: ${DATE} ${TIMESTAMP}"
    ;;

  stop|end)
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
    secs = int(elapsed % 60)
    print(f'{mins}m {secs}s')
except:
    print('unknown')
" 2>/dev/null || echo "unknown")"
    fi

    MESSAGE="*Claude Code session ended*
Project: \`${PROJECT}\`
Duration: ${DURATION}
Time: ${DATE} ${TIMESTAMP}"
    ;;

  task)
    TASK_NAME="${2:-task complete}"
    MESSAGE="*Task complete*
Project: \`${PROJECT}\`
Task: ${TASK_NAME}
Time: ${DATE} ${TIMESTAMP}"
    ;;

  *)
    MESSAGE="${ACTION}"
    ;;
esac

# --- Send via Telegram Bot API ---
API_URL="https://api.telegram.org/bot${BOT_TOKEN}/sendMessage"

RESPONSE="$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json, sys
print(json.dumps({
    'chat_id': '${CHAT_ID}',
    'text': sys.argv[1],
    'parse_mode': '${PARSE_MODE}'
}))
" "${MESSAGE}")" \
  "$API_URL" 2>/dev/null)"

if [ "$RESPONSE" = "200" ]; then
  echo "Telegram notification sent." >&2
else
  echo "Telegram notification failed (HTTP ${RESPONSE})." >&2
fi

exit 0
