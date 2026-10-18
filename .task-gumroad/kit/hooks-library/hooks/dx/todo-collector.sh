#!/usr/bin/env bash
# =============================================================================
# todo-collector.sh — Collect TODOs from the codebase into a tracking file
# =============================================================================
#
# WHAT IT DOES:
#   After edits, scans changed files for TODO/FIXME/HACK/XXX comments and
#   appends new ones to a central TODO.md tracking file. Existing entries
#   are not duplicated. Includes file path, line number, and the TODO text.
#
# WHEN TO USE IT:
#   Projects where TODOs accumulate in code but never get reviewed. Having
#   them in a single Markdown file makes weekly review and backlog triage
#   significantly easier.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/todo-collector.sh
#   2. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "PostToolUse": [
#         {
#           "matcher": "Write|Edit",
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/todo-collector.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   TODO_OUTPUT_FILE   — Where to write collected TODOs (default: TODO.md)
#   TODO_PATTERNS      — Grep patterns to find (default: TODO|FIXME|HACK|XXX)
#   TODO_SCAN_ALL      — Set to "1" to scan entire codebase (default: edited file only)
# =============================================================================

set -euo pipefail

TODO_FILE="${TODO_OUTPUT_FILE:-TODO.md}"
PATTERNS="${TODO_PATTERNS:-TODO|FIXME|HACK|XXX}"
SCAN_ALL="${TODO_SCAN_ALL:-0}"

# --- Read edited file ---
INPUT="$(cat)"
EDITED_FILE="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ti = d.get('tool_input', {})
print(ti.get('path', ti.get('file_path', '')))
" 2>/dev/null || echo "")"

if [ "$SCAN_ALL" = "1" ]; then
  SCAN_TARGET="."
elif [ -n "$EDITED_FILE" ] && [ -f "$EDITED_FILE" ]; then
  SCAN_TARGET="$EDITED_FILE"
else
  exit 0
fi

# --- Find TODOs ---
FOUND="$(grep -rn --include="*.py" --include="*.ts" --include="*.js" --include="*.go" \
  --include="*.sh" --include="*.rb" --include="*.rs" --include="*.java" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv --exclude-dir=dist \
  -E "($PATTERNS)" "$SCAN_TARGET" 2>/dev/null || true)"

if [ -z "$FOUND" ]; then
  exit 0
fi

# Initialize TODO.md if it doesn't exist
if [ ! -f "$TODO_FILE" ]; then
  cat > "$TODO_FILE" << HEADER
# TODOs

Auto-collected from codebase. Review and move to backlog or resolve.

| File | Line | Type | Description |
|------|------|------|-------------|
HEADER
fi

DATE="$(date +"%Y-%m-%d")"
NEW_COUNT=0

while IFS= read -r line; do
  # Parse: filepath:linenum:content
  FILE_PART="$(echo "$line" | cut -d: -f1)"
  LINE_NUM="$(echo "$line" | cut -d: -f2)"
  CONTENT="$(echo "$line" | cut -d: -f3- | sed 's/^[[:space:]]*//')"

  # Extract TODO type
  TODO_TYPE="$(echo "$CONTENT" | grep -oE "(TODO|FIXME|HACK|XXX)" | head -1 || echo "TODO")"

  # Extract description (text after the keyword and any : or space)
  DESCRIPTION="$(echo "$CONTENT" | sed "s/.*${TODO_TYPE}[: ]*//" | sed 's/^[[:space:]]*//' | cut -c1-100)"

  # Check for duplicate (same file + line)
  UNIQUE_KEY="${FILE_PART}:${LINE_NUM}"
  if grep -qF "$UNIQUE_KEY" "$TODO_FILE" 2>/dev/null; then
    continue
  fi

  # Append to TODO.md
  echo "| \`${FILE_PART}\` | ${LINE_NUM} | ${TODO_TYPE} | ${DESCRIPTION} |" >> "$TODO_FILE"
  NEW_COUNT=$(( NEW_COUNT + 1 ))
done <<< "$FOUND"

if [ "$NEW_COUNT" -gt 0 ]; then
  echo "Collected ${NEW_COUNT} new TODO(s) into ${TODO_FILE}" >&2
fi

exit 0
