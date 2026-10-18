#!/usr/bin/env bash
# =============================================================================
# session-logger.sh — Log session start/end to Obsidian vault
# =============================================================================
#
# WHAT IT DOES:
#   Creates a structured session log entry in your Obsidian vault when a
#   Claude Code session starts (SessionStart event) or ends (Stop event).
#   Logs: timestamp, working directory, initial task, duration.
#
# WHEN TO USE IT:
#   If you use Obsidian for personal knowledge management and want an
#   automatic record of AI-assisted work sessions. Useful for weekly reviews
#   and time tracking.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/session-logger.sh
#   2. Set OBSIDIAN_VAULT_PATH below or export as environment variable
#   3. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "SessionStart": [
#         {
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/session-logger.sh start"
#             }
#           ]
#         }
#       ],
#       "Stop": [
#         {
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/session-logger.sh end"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   OBSIDIAN_VAULT_PATH    — Path to Obsidian vault (required)
#   SESSION_LOG_FOLDER     — Subfolder for logs (default: Sessions)
#   SESSION_STATE_FILE     — Temp file to track session start time
# =============================================================================

set -euo pipefail

VAULT_PATH="${OBSIDIAN_VAULT_PATH:-${HOME}/obsidian-vault}"
LOG_FOLDER="${SESSION_LOG_FOLDER:-Sessions}"
STATE_FILE="${SESSION_STATE_FILE:-/tmp/claude-session-state.json}"
ACTION="${1:-start}"

TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
DATE="$(date +"%Y-%m-%d")"
TIME_LOCAL="$(date +"%H:%M")"
YEAR_MONTH="$(date +"%Y-%m")"
PROJECT_DIR="$(pwd)"
PROJECT_NAME="$(basename "$PROJECT_DIR")"

LOG_DIR="${VAULT_PATH}/${LOG_FOLDER}/${YEAR_MONTH}"
LOG_FILE="${LOG_DIR}/$(date +"%Y-%m-%d")-sessions.md"

mkdir -p "$LOG_DIR"

case "$ACTION" in
  start)
    # Save session start time to state file
    python3 -c "
import json, time
state = {'start_time': time.time(), 'project': '${PROJECT_NAME}', 'dir': '${PROJECT_DIR}'}
with open('${STATE_FILE}', 'w') as f:
    json.dump(state, f)
" 2>/dev/null || true

    # Append session start to daily log
    cat >> "$LOG_FILE" << ENTRY

## Session — ${TIME_LOCAL}
- **Project**: ${PROJECT_NAME}
- **Directory**: \`${PROJECT_DIR}\`
- **Started**: ${TIMESTAMP}
- **Status**: in-progress
ENTRY

    echo "Session logged: ${LOG_FILE}" >&2
    ;;

  end)
    # Calculate duration if state file exists
    DURATION=""
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
      rm -f "$STATE_FILE"
    fi

    # Append session end
    cat >> "$LOG_FILE" << ENTRY
- **Ended**: ${TIMESTAMP}
- **Duration**: ${DURATION:-unknown}

ENTRY

    echo "Session end logged. Duration: ${DURATION:-unknown}" >&2
    ;;

  *)
    echo "Usage: session-logger.sh [start|end]" >&2
    exit 1
    ;;
esac

exit 0
