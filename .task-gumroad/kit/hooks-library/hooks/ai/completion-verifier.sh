#!/usr/bin/env bash
# =============================================================================
# completion-verifier.sh — Verify task completion criteria before stopping
# =============================================================================
#
# WHAT IT DOES:
#   Before a session ends, runs a checklist of verifiable completion criteria:
#   - Tests pass
#   - No lint errors
#   - No uncommitted changes (or prompt to commit)
#   - Required files exist
#   - Documentation updated
#   Outputs a verification report and optionally blocks stop if criteria fail.
#
# WHEN TO USE IT:
#   When you want a structured "done means done" gate. Prevents Claude from
#   declaring a task complete when tests are still failing or files are dirty.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/completion-verifier.sh
#   2. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "Stop": [
#         {
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/completion-verifier.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   VERIFY_RUN_TESTS       — Set to "0" to skip test check (default: 1)
#   VERIFY_RUN_LINT        — Set to "0" to skip lint check (default: 1)
#   VERIFY_CLEAN_GIT       — Set to "0" to skip uncommitted changes check (default: 1)
#   VERIFY_REQUIRED_FILES  — Colon-separated files that must exist
#   VERIFY_BLOCK_ON_FAIL   — Set to "1" to block stop on failure (default: 0)
# =============================================================================

set -euo pipefail

RUN_TESTS="${VERIFY_RUN_TESTS:-1}"
RUN_LINT="${VERIFY_RUN_LINT:-1}"
CHECK_GIT="${VERIFY_CLEAN_GIT:-1}"
BLOCK_ON_FAIL="${VERIFY_BLOCK_ON_FAIL:-0}"
REQUIRED_FILES="${VERIFY_REQUIRED_FILES:-}"

PASS=0
FAIL=0
REPORT=""

check() {
  local name="$1"
  local result="$2"
  local detail="${3:-}"

  if [ "$result" = "pass" ]; then
    REPORT="${REPORT}  [PASS] ${name}\n"
    PASS=$(( PASS + 1 ))
  else
    REPORT="${REPORT}  [FAIL] ${name}\n"
    if [ -n "$detail" ]; then
      REPORT="${REPORT}         ${detail}\n"
    fi
    FAIL=$(( FAIL + 1 ))
  fi
}

echo "" >&2
echo "=== Completion Verification ===" >&2

# --- Test suite ---
if [ "$RUN_TESTS" = "1" ]; then
  TEST_CMD=""
  if [ -f "package.json" ] && grep -q '"test"' package.json 2>/dev/null; then
    TEST_CMD="npm test --silent"
  elif command -v pytest &>/dev/null && [ -d "tests" ]; then
    TEST_CMD="pytest -q --tb=no"
  elif [ -f "Makefile" ] && grep -q "^test:" Makefile 2>/dev/null; then
    TEST_CMD="make test"
  fi

  if [ -n "$TEST_CMD" ]; then
    if timeout 60 bash -c "$TEST_CMD" &>/dev/null; then
      check "Tests" "pass"
    else
      check "Tests" "fail" "Run '$TEST_CMD' to see details"
    fi
  fi
fi

# --- Lint ---
if [ "$RUN_LINT" = "1" ]; then
  LINT_CMD=""
  if [ -f "package.json" ] && grep -q '"lint"' package.json 2>/dev/null; then
    LINT_CMD="npm run lint --silent"
  elif command -v ruff &>/dev/null && [ -f "pyproject.toml" ]; then
    LINT_CMD="ruff check ."
  fi

  if [ -n "$LINT_CMD" ]; then
    if timeout 30 bash -c "$LINT_CMD" &>/dev/null; then
      check "Lint" "pass"
    else
      check "Lint" "fail" "Run '$LINT_CMD' to see details"
    fi
  fi
fi

# --- Git cleanliness ---
if [ "$CHECK_GIT" = "1" ] && command -v git &>/dev/null && git rev-parse --git-dir &>/dev/null 2>&1; then
  DIRTY="$(git status --short 2>/dev/null || echo "")"
  if [ -z "$DIRTY" ]; then
    check "Git (clean working tree)" "pass"
  else
    DIRTY_COUNT="$(echo "$DIRTY" | wc -l | tr -d ' ')"
    check "Git (uncommitted changes)" "fail" "${DIRTY_COUNT} file(s) uncommitted"
  fi
fi

# --- Required files ---
if [ -n "$REQUIRED_FILES" ]; then
  IFS=':' read -ra FILES <<< "$REQUIRED_FILES"
  for f in "${FILES[@]}"; do
    if [ -f "$f" ]; then
      check "Required file: ${f}" "pass"
    else
      check "Required file: ${f}" "fail" "File not found"
    fi
  done
fi

# --- Print report ---
echo "" >&2
printf "%b" "$REPORT" >&2
echo "" >&2
echo "Results: ${PASS} passed, ${FAIL} failed" >&2
echo "" >&2

if [ "$FAIL" -gt 0 ] && [ "$BLOCK_ON_FAIL" = "1" ]; then
  python3 -c "
import json
print(json.dumps({
  'decision': 'block',
  'reason': 'Completion verification failed. Fix issues before closing session.'
}))
"
fi

exit 0
