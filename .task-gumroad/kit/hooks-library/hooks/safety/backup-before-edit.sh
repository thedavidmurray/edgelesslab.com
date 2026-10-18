#!/usr/bin/env bash
# =============================================================================
# backup-before-edit.sh — Auto-backup files before major edits
# =============================================================================
#
# WHAT IT DOES:
#   Before any file edit, creates a timestamped backup copy in a local
#   backup directory. Keeps the last N versions. Makes it trivial to recover
#   from an AI edit that went wrong.
#
# WHEN TO USE IT:
#   When editing configuration files, important scripts, or any file where
#   you want a quick undo path outside of git. Pairs well with damage-control
#   as a secondary safety net.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/backup-before-edit.sh
#   2. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "PreToolUse": [
#         {
#           "matcher": "Edit|MultiEdit",
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/backup-before-edit.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   BACKUP_DIR         — Where to store backups (default: .claude/backups)
#   BACKUP_MAX_COPIES  — Max versions to keep per file (default: 5)
#   BACKUP_MIN_SIZE    — Min file size in bytes to backup (default: 0)
#   BACKUP_EXTENSIONS  — Colon-separated extensions to backup (default: all)
# =============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-.claude/backups}"
MAX_COPIES="${BACKUP_MAX_COPIES:-5}"
MIN_SIZE="${BACKUP_MIN_SIZE:-0}"
BACKUP_EXTENSIONS="${BACKUP_EXTENSIONS:-}"

# --- Read hook input ---
INPUT="$(cat)"
FILE_PATH="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ti = d.get('tool_input', {})
print(ti.get('path', ti.get('file_path', '')))
" 2>/dev/null || echo "")"

[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

# --- Extension filter ---
if [ -n "$BACKUP_EXTENSIONS" ]; then
  EXTENSION="${FILE_PATH##*.}"
  MATCHED=0
  IFS=':' read -ra ALLOWED_EXTS <<< "$BACKUP_EXTENSIONS"
  for ext in "${ALLOWED_EXTS[@]}"; do
    if [ "$EXTENSION" = "$ext" ]; then
      MATCHED=1
      break
    fi
  done
  [ "$MATCHED" -eq 0 ] && exit 0
fi

# --- Size filter ---
FILE_SIZE="$(wc -c < "$FILE_PATH" 2>/dev/null || echo 0)"
if [ "$FILE_SIZE" -lt "$MIN_SIZE" ]; then
  exit 0
fi

# --- Create backup ---
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
# Flatten path: replace / with __ for the backup filename
FLAT_NAME="$(echo "$FILE_PATH" | sed 's|/|__|g')"
BACKUP_SUBDIR="${BACKUP_DIR}/$(dirname "$FILE_PATH")"

mkdir -p "$BACKUP_SUBDIR"

BACKUP_PATH="${BACKUP_DIR}/${FLAT_NAME}.${TIMESTAMP}.bak"
cp "$FILE_PATH" "$BACKUP_PATH"

echo "Backed up: ${FILE_PATH} → ${BACKUP_PATH}" >&2

# --- Prune old copies ---
EXISTING_BACKUPS=($(ls -t "${BACKUP_DIR}/${FLAT_NAME}".*.bak 2>/dev/null || true))
TOTAL="${#EXISTING_BACKUPS[@]}"

if [ "$TOTAL" -gt "$MAX_COPIES" ]; then
  PRUNE_COUNT=$(( TOTAL - MAX_COPIES ))
  # Delete oldest (last in list since sorted by -t newest-first)
  for (( i=MAX_COPIES; i<TOTAL; i++ )); do
    rm -f "${EXISTING_BACKUPS[$i]}"
    echo "Pruned old backup: ${EXISTING_BACKUPS[$i]}" >&2
  done
fi

exit 0
