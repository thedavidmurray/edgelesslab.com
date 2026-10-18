#!/usr/bin/env bash
# =============================================================================
# complexity-guard.sh — Warn on high cyclomatic complexity
# =============================================================================
#
# WHAT IT DOES:
#   After editing source files, measures cyclomatic complexity of the changed
#   file. Warns (but does not block) when complexity exceeds the threshold.
#   Supports Python (radon), JavaScript/TypeScript (complexity-report), Go.
#
# WHEN TO USE IT:
#   When you want to keep functions maintainable. Complexity > 10 is a signal
#   that a function should be broken up. This hook surfaces that signal
#   immediately rather than waiting for code review.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/complexity-guard.sh
#   2. Install analysis tool for your language:
#      Python: pip install radon
#      JS/TS:  npm install -g complexity-report
#   3. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "PostToolUse": [
#         {
#           "matcher": "Edit|Write",
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/complexity-guard.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   COMPLEXITY_THRESHOLD  — Max acceptable complexity score (default: 10)
#   COMPLEXITY_BLOCK      — Set to "1" to block edits (default: warn only)
# =============================================================================

set -euo pipefail

COMPLEXITY_THRESHOLD="${COMPLEXITY_THRESHOLD:-10}"
COMPLEXITY_BLOCK="${COMPLEXITY_BLOCK:-0}"

# --- Read edited file ---
INPUT="$(cat)"
EDITED_FILE="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ti = d.get('tool_input', {})
print(ti.get('path', ti.get('file_path', '')))
" 2>/dev/null || echo "")"

[ -z "$EDITED_FILE" ] && exit 0
[ ! -f "$EDITED_FILE" ] && exit 0

EXTENSION="${EDITED_FILE##*.}"

# --- Python complexity via radon ---
check_python() {
  if ! command -v radon &>/dev/null; then
    return 0
  fi

  OUTPUT="$(radon cc -s -n C "$EDITED_FILE" 2>/dev/null || true)"
  if [ -z "$OUTPUT" ]; then
    return 0
  fi

  echo "" >&2
  echo "COMPLEXITY WARNING in ${EDITED_FILE}:" >&2
  echo "${OUTPUT}" >&2
  echo "" >&2
  echo "Functions with grade C or worse exceed complexity ${COMPLEXITY_THRESHOLD}." >&2
  echo "Consider breaking them into smaller, focused functions." >&2

  if [ "$COMPLEXITY_BLOCK" = "1" ]; then
    python3 -c "
import json
print(json.dumps({
  'decision': 'block',
  'reason': 'Cyclomatic complexity too high. Refactor before continuing.'
}))
"
  fi
}

# --- JavaScript/TypeScript complexity ---
check_js() {
  if ! command -v cr &>/dev/null; then
    return 0
  fi

  OUTPUT="$(cr --format plain --threshold ${COMPLEXITY_THRESHOLD} "$EDITED_FILE" 2>/dev/null || true)"
  if echo "$OUTPUT" | grep -q "too complex"; then
    echo "" >&2
    echo "COMPLEXITY WARNING in ${EDITED_FILE}:" >&2
    echo "${OUTPUT}" >&2
    echo "" >&2
  fi
}

# --- Go complexity via gocyclo ---
check_go() {
  if ! command -v gocyclo &>/dev/null; then
    return 0
  fi

  OUTPUT="$(gocyclo -over "${COMPLEXITY_THRESHOLD}" "$EDITED_FILE" 2>/dev/null || true)"
  if [ -n "$OUTPUT" ]; then
    echo "" >&2
    echo "COMPLEXITY WARNING in ${EDITED_FILE}:" >&2
    echo "${OUTPUT}" >&2
    echo "Functions above complexity ${COMPLEXITY_THRESHOLD}. Consider splitting." >&2
    echo "" >&2
  fi
}

case "$EXTENSION" in
  py)          check_python ;;
  js|ts|jsx|tsx) check_js ;;
  go)          check_go ;;
  *)           exit 0 ;;
esac

exit 0
