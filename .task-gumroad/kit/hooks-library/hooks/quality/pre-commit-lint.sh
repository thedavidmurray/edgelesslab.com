#!/usr/bin/env bash
# =============================================================================
# pre-commit-lint.sh — Run linter before commits
# =============================================================================
#
# WHAT IT DOES:
#   Intercepts PreToolUse(Bash) events that contain git commit commands and
#   runs your project's linter first. If the linter fails, the commit is
#   blocked and the output is shown.
#
# WHEN TO USE IT:
#   Any project with a configured linter (ESLint, ruff, golangci-lint, etc.).
#   Prevents committing code that will fail CI.
#
# HOW TO INSTALL:
#   1. Copy this file to your project's .claude/hooks/ directory
#   2. Add the configuration below to .claude/settings.json
#   3. Set LINT_COMMAND to match your project
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "PreToolUse": [
#         {
#           "matcher": "Bash",
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/pre-commit-lint.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   LINT_COMMAND   — Command to run linter (default: auto-detected)
#   LINT_PATHS     — Space-separated paths to lint (default: .)
#   LINT_TIMEOUT   — Seconds before lint times out (default: 60)
# =============================================================================

set -euo pipefail

# --- Configuration ---
LINT_TIMEOUT="${LINT_TIMEOUT:-60}"
LINT_PATHS="${LINT_PATHS:-.}"

# --- Read hook input from stdin ---
INPUT="$(cat)"

# Only run on git commit commands
TOOL_INPUT="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")"

if ! echo "$TOOL_INPUT" | grep -qE "git (commit|push)"; then
  exit 0
fi

# --- Auto-detect lint command ---
detect_lint_command() {
  if [ -f "package.json" ] && grep -q '"lint"' package.json 2>/dev/null; then
    echo "npm run lint"
  elif [ -f "pyproject.toml" ] && command -v ruff &>/dev/null; then
    echo "ruff check ${LINT_PATHS}"
  elif [ -f ".golangci.yml" ] || [ -f ".golangci.yaml" ]; then
    echo "golangci-lint run"
  elif [ -f ".rubocop.yml" ] && command -v rubocop &>/dev/null; then
    echo "rubocop --no-color"
  elif [ -f "Makefile" ] && grep -q "^lint:" Makefile 2>/dev/null; then
    echo "make lint"
  else
    echo ""
  fi
}

LINT_COMMAND="${LINT_COMMAND:-$(detect_lint_command)}"

if [ -z "$LINT_COMMAND" ]; then
  # No linter found — pass through
  exit 0
fi

# --- Run linter ---
echo "Running linter before commit: ${LINT_COMMAND}" >&2

LINT_OUTPUT=$(timeout "${LINT_TIMEOUT}" bash -c "${LINT_COMMAND}" 2>&1) || LINT_EXIT=$?

if [ "${LINT_EXIT:-0}" -ne 0 ]; then
  echo "LINT FAILED — commit blocked" >&2
  echo "" >&2
  echo "${LINT_OUTPUT}" >&2
  echo "" >&2
  echo "Fix the above issues and retry." >&2
  # Output JSON to block the tool call
  python3 -c "
import json, sys
print(json.dumps({
  'decision': 'block',
  'reason': 'Linter failed. Fix lint errors before committing.\n\n' + sys.argv[1]
}))
" "${LINT_OUTPUT}"
  exit 0
fi

echo "Lint passed." >&2
exit 0
