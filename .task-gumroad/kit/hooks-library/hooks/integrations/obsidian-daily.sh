#!/usr/bin/env bash
# =============================================================================
# obsidian-daily.sh — Append Claude Code activity to Obsidian daily note
# =============================================================================
#
# WHAT IT DOES:
#   Appends a structured activity entry to your Obsidian daily note at session
#   start and end. Uses the Obsidian CLI if available (v1.12.4+), otherwise
#   falls back to direct file append. Integrates naturally with daily review
#   workflows and Dataview queries.
#
# WHEN TO USE IT:
#   Obsidian users who want AI-assisted work activity to show up in their
#   daily notes automatically. Works alongside session-logger.sh or standalone.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/obsidian-daily.sh
#   2. Set OBSIDIAN_VAULT_PATH to your vault location
#   3. Optionally enable Obsidian CLI: Settings → General → Advanced → CLI
#   4. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "SessionStart": [
#         {
#           "hooks": [
#             { "type": "command", "command": "bash .claude/hooks/obsidian-daily.sh start" }
#           ]
#         }
#       ],
#       "Stop": [
#         {
#           "hooks": [
#             { "type": "command", "command": "bash .claude/hooks/obsidian-daily.sh stop" }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   OBSIDIAN_VAULT_PATH    — Required. Path to your Obsidian vault
#   OBSIDIAN_DAILY_FOLDER  — Folder for daily notes (default: Daily)
#   OBSIDIAN_CLI_PATH      — Path to obsidian CLI (default: auto-detected)
#   OBSIDIAN_SECTION       — Section header to append under (default: ## AI Work)
# =============================================================================

set -euo pipefail

VAULT_PATH="${OBSIDIAN_VAULT_PATH:-${HOME}/obsidian-vault}"
DAILY_FOLDER="${OBSIDIAN_DAILY_FOLDER:-Daily}"
OBSIDIAN_CLI="${OBSIDIAN_CLI_PATH:-${HOME}/.local/bin/obsidian}"
SECTION="${OBSIDIAN_SECTION:-## AI Work}"
ACTION="${1:-start}"

PROJECT="$(basename "$(pwd)")"
TIMESTAMP="$(date +"%H:%M")"
DATE="$(date +"%Y-%m-%d")"

# --- Build content to append ---
case "$ACTION" in
  start)
    CONTENT="- ${TIMESTAMP} Claude Code session started — \`${PROJECT}\`"
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
    CONTENT="- ${TIMESTAMP} Claude Code session ended — \`${PROJECT}\` (${DURATION})"
    ;;
  *)
    CONTENT="- ${TIMESTAMP} ${ACTION} — \`${PROJECT}\`"
    ;;
esac

# --- Method 1: Obsidian CLI (preferred) ---
if command -v "$OBSIDIAN_CLI" &>/dev/null; then
  "$OBSIDIAN_CLI" daily:append content="${CONTENT}" 2>/dev/null && {
    echo "Appended to Obsidian daily note via CLI." >&2
    exit 0
  } || true
fi

# --- Method 2: Direct file write fallback ---
DAILY_DIR="${VAULT_PATH}/${DAILY_FOLDER}"
mkdir -p "$DAILY_DIR"
DAILY_FILE="${DAILY_DIR}/${DATE}.md"

# Create daily note if it doesn't exist
if [ ! -f "$DAILY_FILE" ]; then
  cat > "$DAILY_FILE" << HEADER
---
date: ${DATE}
tags: [daily]
---

# ${DATE}

${SECTION}

HEADER
fi

# Ensure section exists
if ! grep -q "^${SECTION}" "$DAILY_FILE" 2>/dev/null; then
  echo "" >> "$DAILY_FILE"
  echo "${SECTION}" >> "$DAILY_FILE"
  echo "" >> "$DAILY_FILE"
fi

# Append the content after the section
python3 << PYEOF
content = open('${DAILY_FILE}').read()
section = '${SECTION}'
entry = '${CONTENT}'

if section in content:
    idx = content.index(section) + len(section)
    # Find end of section or file
    next_section = -1
    for i, line in enumerate(content[idx:].split('\n')):
        if line.startswith('## ') and i > 0:
            next_section = idx + content[idx:].index(line)
            break

    if next_section == -1:
        content = content.rstrip() + '\n' + entry + '\n'
    else:
        insert_at = next_section - 1
        content = content[:insert_at].rstrip() + '\n' + entry + '\n\n' + content[insert_at:]
else:
    content = content.rstrip() + '\n\n' + section + '\n\n' + entry + '\n'

with open('${DAILY_FILE}', 'w') as f:
    f.write(content)
PYEOF

echo "Appended to Obsidian daily note: ${DAILY_FILE}" >&2
exit 0
