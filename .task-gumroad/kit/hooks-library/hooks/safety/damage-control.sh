#!/usr/bin/env bash
# =============================================================================
# damage-control.sh — Block writes to protected directories
# =============================================================================
#
# WHAT IT DOES:
#   Intercepts Write, Edit, and MultiEdit tool calls and blocks any attempt
#   to write to directories you've marked as protected. Also blocks
#   destructive shell commands (rm -rf, truncate, etc.) on protected paths.
#
# WHEN TO USE IT:
#   Always. Protects production configs, backup dirs, archived files, and
#   any path that should never be modified by an AI session. This is the
#   most important safety hook in this library.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/damage-control.sh
#   2. Edit PROTECTED_PATHS below for your project
#   3. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "PreToolUse": [
#         {
#           "matcher": "Write|Edit|MultiEdit|Bash",
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/damage-control.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   DAMAGE_CONTROL_PATHS  — Colon-separated additional protected paths
#   DAMAGE_CONTROL_LOG    — File to log blocked attempts (default: /tmp/damage-control.log)
# =============================================================================

set -euo pipefail

BLOCK_LOG="${DAMAGE_CONTROL_LOG:-/tmp/damage-control.log}"

# --- Protected paths (edit these for your project) ---
# These paths will NEVER be written to. Use absolute or relative paths.
PROTECTED_PATHS=(
  ".env"
  ".env.production"
  ".env.prod"
  "backups/"
  "archive/"
  ".claude/hooks/"          # Don't let AI modify its own hooks
  "secrets/"
  "credentials/"
  "dist/"                   # Don't touch build output directly
  "node_modules/"
  ".git/"
)

# Add extra paths from environment
if [ -n "${DAMAGE_CONTROL_PATHS:-}" ]; then
  IFS=':' read -ra EXTRA_PATHS <<< "$DAMAGE_CONTROL_PATHS"
  PROTECTED_PATHS+=("${EXTRA_PATHS[@]}")
fi

# Destructive shell patterns to block on protected paths
DESTRUCTIVE_PATTERNS=(
  "rm -rf"
  "rm -r "
  "truncate"
  "> "          # Output redirect (destructive)
  "dd if="
  "shred"
)

# --- Read hook input ---
INPUT="$(cat)"
TOOL_NAME="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_name', ''))
" 2>/dev/null || echo "")"

TOOL_INPUT="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ti = d.get('tool_input', {})
# For file tools
path = ti.get('path', ti.get('file_path', ''))
# For Bash tools
cmd = ti.get('command', '')
print(path + '|||' + cmd)
" 2>/dev/null || echo "|||")"

FILE_PATH="$(echo "$TOOL_INPUT" | cut -d'|' -f1)"
BASH_CMD="$(echo "$TOOL_INPUT" | cut -d'|' -f4)"

block_action() {
  local reason="$1"
  local timestamp
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  echo "${timestamp} BLOCKED: ${reason}" >> "$BLOCK_LOG" 2>/dev/null || true
  echo "" >&2
  echo "DAMAGE CONTROL: Blocked" >&2
  echo "Reason: ${reason}" >&2
  echo "" >&2

  python3 -c "
import json, sys
print(json.dumps({
  'decision': 'block',
  'reason': 'Damage control: ' + sys.argv[1]
}))
" "$reason"
  exit 0
}

# --- Check file write tools ---
if [ -n "$FILE_PATH" ] && echo "$TOOL_NAME" | grep -qE "^(Write|Edit|MultiEdit)$"; then
  for protected in "${PROTECTED_PATHS[@]}"; do
    # Normalize: strip trailing slash for comparison
    clean_protected="${protected%/}"
    if echo "$FILE_PATH" | grep -qE "(^|/)${clean_protected}(/|$)|^${clean_protected}$"; then
      block_action "Attempt to write to protected path: ${FILE_PATH} (matches: ${protected})"
    fi
  done
fi

# --- Check Bash commands ---
if [ -n "$BASH_CMD" ] && [ "$TOOL_NAME" = "Bash" ]; then
  for pattern in "${DESTRUCTIVE_PATTERNS[@]}"; do
    if echo "$BASH_CMD" | grep -qF "$pattern"; then
      # Check if any protected path is also mentioned
      for protected in "${PROTECTED_PATHS[@]}"; do
        clean_protected="${protected%/}"
        if echo "$BASH_CMD" | grep -q "$clean_protected"; then
          block_action "Destructive command '${pattern}' on protected path '${clean_protected}': ${BASH_CMD}"
        fi
      done
    fi
  done
fi

exit 0
