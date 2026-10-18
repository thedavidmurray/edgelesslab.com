#!/usr/bin/env bash
# =============================================================================
# time-tracker.sh — Track time spent per task
# =============================================================================
#
# WHAT IT DOES:
#   Records task start/end times in a local JSON ledger. On session end,
#   appends a summary to a daily time log (Markdown). Useful for billing,
#   estimating, and understanding where time actually goes.
#
# WHEN TO USE IT:
#   Consultants, freelancers, or anyone who wants accurate time data.
#   The log file works as a stand-alone record — no external service needed.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/time-tracker.sh
#   2. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "SessionStart": [
#         {
#           "hooks": [
#             { "type": "command", "command": "bash .claude/hooks/time-tracker.sh start" }
#           ]
#         }
#       ],
#       "Stop": [
#         {
#           "hooks": [
#             { "type": "command", "command": "bash .claude/hooks/time-tracker.sh stop" }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   TIME_TRACKER_LOG_DIR    — Directory for time logs (default: .claude/time-logs)
#   TIME_TRACKER_STATE      — State file path (default: /tmp/claude-time-state.json)
#   TIME_TRACKER_PROJECT    — Project name override (default: directory name)
# =============================================================================

set -euo pipefail

LOG_DIR="${TIME_TRACKER_LOG_DIR:-.claude/time-logs}"
STATE_FILE="${TIME_TRACKER_STATE:-/tmp/claude-time-state.json}"
PROJECT="${TIME_TRACKER_PROJECT:-$(basename "$(pwd)")}"
ACTION="${1:-start}"

mkdir -p "$LOG_DIR"

DATE="$(date +"%Y-%m-%d")"
TIMESTAMP="$(date +"%Y-%m-%dT%H:%M:%S")"
TIME_LOCAL="$(date +"%H:%M")"
EPOCH="$(date +%s)"

DAILY_LOG="${LOG_DIR}/${DATE}.md"

case "$ACTION" in
  start)
    python3 -c "
import json, time
state = {
    'project': '${PROJECT}',
    'start_epoch': ${EPOCH},
    'start_time': '${TIMESTAMP}',
    'date': '${DATE}'
}
with open('${STATE_FILE}', 'w') as f:
    json.dump(state, f, indent=2)
print('Time tracking started: ${TIMESTAMP}')
" >&2
    ;;

  stop|end)
    if [ ! -f "$STATE_FILE" ]; then
      echo "No active time tracking session found." >&2
      exit 0
    fi

    SUMMARY="$(python3 << 'PYEOF'
import json, time, os

state_file = os.environ.get('TIME_TRACKER_STATE', '/tmp/claude-time-state.json')
with open(state_file) as f:
    state = json.load(f)

now = time.time()
elapsed = now - state['start_epoch']
hours = int(elapsed // 3600)
mins = int((elapsed % 3600) // 60)
secs = int(elapsed % 60)

duration_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m {secs}s"

print(f"project={state['project']}")
print(f"start={state['start_time']}")
print(f"elapsed_secs={int(elapsed)}")
print(f"duration={duration_str}")
PYEOF
)"

    PROJECT_NAME="$(echo "$SUMMARY" | grep '^project=' | cut -d= -f2)"
    START_TIME="$(echo "$SUMMARY" | grep '^start=' | cut -d= -f2)"
    DURATION="$(echo "$SUMMARY" | grep '^duration=' | cut -d= -f2)"
    ELAPSED_SECS="$(echo "$SUMMARY" | grep '^elapsed_secs=' | cut -d= -f2)"

    # Initialize daily log if new
    if [ ! -f "$DAILY_LOG" ]; then
      cat > "$DAILY_LOG" << HEADER
# Time Log — ${DATE}

| Start | End | Project | Duration |
|-------|-----|---------|----------|
HEADER
    fi

    # Append entry
    echo "| ${START_TIME##*T} | ${TIME_LOCAL} | ${PROJECT_NAME} | ${DURATION} |" >> "$DAILY_LOG"

    echo "" >&2
    echo "Time tracked: ${DURATION} on ${PROJECT_NAME}" >&2
    echo "Log: ${DAILY_LOG}" >&2

    rm -f "$STATE_FILE"
    ;;

  report)
    # Print today's log
    if [ -f "$DAILY_LOG" ]; then
      cat "$DAILY_LOG"
    else
      echo "No entries for ${DATE}." >&2
    fi
    ;;

  *)
    echo "Usage: time-tracker.sh [start|stop|report]" >&2
    exit 1
    ;;
esac

exit 0
