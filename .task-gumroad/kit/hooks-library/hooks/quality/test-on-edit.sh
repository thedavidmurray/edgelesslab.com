#!/usr/bin/env bash
# =============================================================================
# test-on-edit.sh — Auto-run relevant tests when files change
# =============================================================================
#
# WHAT IT DOES:
#   After any file edit (Write, Edit, MultiEdit tool), discovers and runs the
#   tests most likely related to the changed file. Uses naming conventions to
#   find test files (e.g. src/auth.py → tests/test_auth.py).
#
# WHEN TO USE IT:
#   Projects with unit tests. Gives immediate feedback without running the
#   full suite on every change. Catches regressions as you go.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/test-on-edit.sh
#   2. Add the configuration below to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "PostToolUse": [
#         {
#           "matcher": "Edit|Write|MultiEdit",
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/test-on-edit.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   TEST_RUNNER       — Override test command (default: auto-detected)
#   TEST_TIMEOUT      — Seconds before tests time out (default: 30)
#   SKIP_TEST_ON_EDIT — Set to "1" to temporarily disable
# =============================================================================

set -euo pipefail

[ "${SKIP_TEST_ON_EDIT:-0}" = "1" ] && exit 0

TEST_TIMEOUT="${TEST_TIMEOUT:-30}"

# --- Read the edited file path from hook input ---
INPUT="$(cat)"
EDITED_FILE="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ti = d.get('tool_input', {})
print(ti.get('path', ti.get('file_path', '')))
" 2>/dev/null || echo "")"

if [ -z "$EDITED_FILE" ]; then
  exit 0
fi

# Skip if the edited file IS a test file — let those run from CI
if echo "$EDITED_FILE" | grep -qE "(test_|_test\.|\.test\.|\.spec\.)"; then
  exit 0
fi

BASENAME="$(basename "$EDITED_FILE" | sed 's/\.[^.]*$//')"
EXTENSION="${EDITED_FILE##*.}"

# --- Find related test file ---
find_test_file() {
  local name="$1"
  local ext="$2"
  local candidates=()

  case "$ext" in
    py)
      candidates=(
        "tests/test_${name}.py"
        "test/test_${name}.py"
        "${name}_test.py"
        "tests/${name}_test.py"
      )
      ;;
    ts|tsx|js|jsx)
      candidates=(
        "${name}.test.${ext}"
        "${name}.spec.${ext}"
        "__tests__/${name}.test.${ext}"
        "src/__tests__/${name}.test.${ext}"
      )
      ;;
    go)
      dir="$(dirname "$EDITED_FILE")"
      candidates=("${dir}/${name}_test.go")
      ;;
    rb)
      candidates=(
        "spec/${name}_spec.rb"
        "test/${name}_test.rb"
      )
      ;;
  esac

  for candidate in "${candidates[@]}"; do
    if [ -f "$candidate" ]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

TEST_FILE="$(find_test_file "$BASENAME" "$EXTENSION" 2>/dev/null || echo "")"

if [ -z "$TEST_FILE" ]; then
  # No specific test found — skip silently
  exit 0
fi

# --- Auto-detect test runner ---
detect_runner() {
  local tf="$1"
  case "$tf" in
    *.py)
      if command -v pytest &>/dev/null; then echo "pytest -x -q"; else echo "python -m unittest"; fi ;;
    *.ts|*.tsx|*.js|*.jsx)
      if [ -f "package.json" ] && grep -q '"jest"' package.json 2>/dev/null; then echo "npx jest --testPathPattern"
      elif [ -f "vitest.config.*" ]; then echo "npx vitest run"; fi ;;
    *.go) echo "go test" ;;
    *.rb) echo "bundle exec rspec" ;;
    *) echo "" ;;
  esac
}

RUNNER="${TEST_RUNNER:-$(detect_runner "$TEST_FILE")}"

if [ -z "$RUNNER" ]; then
  exit 0
fi

echo "Running tests for ${EDITED_FILE}: ${RUNNER} ${TEST_FILE}" >&2

OUTPUT=$(timeout "${TEST_TIMEOUT}" bash -c "${RUNNER} ${TEST_FILE}" 2>&1) || EXIT_CODE=$?

if [ "${EXIT_CODE:-0}" -ne 0 ]; then
  echo "" >&2
  echo "TESTS FAILED for ${BASENAME}:" >&2
  echo "${OUTPUT}" >&2
  echo "" >&2
else
  echo "Tests passed." >&2
fi

exit 0
