#!/usr/bin/env bash
# =============================================================================
# auto-branch.sh — Create feature branch from task name
# =============================================================================
#
# WHAT IT DOES:
#   When Claude starts working on a task that begins with a recognized prefix
#   (fix, feat, chore, etc.), automatically creates and checks out a new
#   branch named from the task description. Ensures work is always on a
#   feature branch, never directly on main.
#
# WHEN TO USE IT:
#   Projects following git-flow or feature-branch workflow. Eliminates the
#   manual step of creating branches and enforces consistent naming.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/auto-branch.sh
#   2. Add configuration to .claude/settings.json
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
#               "command": "bash .claude/hooks/auto-branch.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   AUTO_BRANCH_PROTECT    — Branch names to protect (default: main master)
#   AUTO_BRANCH_MAX_LEN    — Max branch name length (default: 50)
#   AUTO_BRANCH_DISABLED   — Set to "1" to disable
# =============================================================================

set -euo pipefail

[ "${AUTO_BRANCH_DISABLED:-0}" = "1" ] && exit 0

PROTECTED_BRANCHES="${AUTO_BRANCH_PROTECT:-main master develop}"
MAX_LEN="${AUTO_BRANCH_MAX_LEN:-50}"

# --- Read hook input ---
INPUT="$(cat)"
TOOL_COMMAND="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('command', ''))
" 2>/dev/null || echo "")"

# Only care about git operations
if ! echo "$TOOL_COMMAND" | grep -q "^git "; then
  exit 0
fi

# Don't interfere with branch/checkout commands themselves
if echo "$TOOL_COMMAND" | grep -qE "git (branch|checkout|switch)"; then
  exit 0
fi

# --- Check if we're on a protected branch ---
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
[ -z "$CURRENT_BRANCH" ] && exit 0

IS_PROTECTED=0
for protected in $PROTECTED_BRANCHES; do
  if [ "$CURRENT_BRANCH" = "$protected" ]; then
    IS_PROTECTED=1
    break
  fi
done

[ "$IS_PROTECTED" -eq 0 ] && exit 0

# --- Try to infer branch name from task context ---
# Look at recent Claude messages / task description from environment or stdin
TASK_HINT="${CLAUDE_TASK_DESCRIPTION:-}"

if [ -z "$TASK_HINT" ]; then
  # Try to extract from git log
  TASK_HINT="$(git log -1 --format="%s" 2>/dev/null || echo "")"
fi

# Sanitize into branch name
make_branch_name() {
  local raw="$1"
  # Lowercase, replace spaces/special chars with hyphens, strip leading/trailing hyphens
  echo "$raw" \
    | tr '[:upper:]' '[:lower:]' \
    | sed 's/[^a-z0-9]/-/g' \
    | sed 's/--*/-/g' \
    | sed 's/^-//; s/-$//' \
    | cut -c1-"$MAX_LEN"
}

if [ -n "$TASK_HINT" ]; then
  BRANCH_NAME="$(make_branch_name "$TASK_HINT")"
  TIMESTAMP="$(date +%Y%m%d%H%M%S)"
  BRANCH_NAME="auto/${BRANCH_NAME}-${TIMESTAMP}"
else
  BRANCH_NAME="auto/work-$(date +%Y%m%d%H%M%S)"
fi

# --- Create and switch to new branch ---
echo "" >&2
echo "AUTO-BRANCH: On protected branch '${CURRENT_BRANCH}'. Creating feature branch..." >&2
echo "Branch: ${BRANCH_NAME}" >&2

git checkout -b "$BRANCH_NAME" >&2

echo "Switched to branch '${BRANCH_NAME}'." >&2
echo "Continue your work. Push with: git push -u origin ${BRANCH_NAME}" >&2

exit 0
