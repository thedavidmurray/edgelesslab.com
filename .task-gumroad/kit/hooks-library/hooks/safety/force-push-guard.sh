#!/usr/bin/env bash
# =============================================================================
# force-push-guard.sh — Prevent force pushes to main/master
# =============================================================================
#
# WHAT IT DOES:
#   Intercepts Bash tool calls containing git push commands. Blocks any
#   force push (--force or -f) targeting a protected branch. Also warns
#   when pushing directly to a protected branch at all.
#
# WHEN TO USE IT:
#   Always, on any shared repository. Force pushing to main rewrites history
#   for every other collaborator. This hook makes it impossible for Claude
#   to accidentally do it.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/force-push-guard.sh
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
#               "command": "bash .claude/hooks/force-push-guard.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   FORCE_PUSH_PROTECTED  — Space-separated list of protected branches
#                           (default: main master production release)
#   FORCE_PUSH_WARN_ONLY  — Set to "1" to warn but allow (not recommended)
# =============================================================================

set -euo pipefail

PROTECTED="${FORCE_PUSH_PROTECTED:-main master production release}"
WARN_ONLY="${FORCE_PUSH_WARN_ONLY:-0}"

# --- Read hook input ---
INPUT="$(cat)"
TOOL_COMMAND="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('command', ''))
" 2>/dev/null || echo "")"

# Only care about git push commands
if ! echo "$TOOL_COMMAND" | grep -qE "git push"; then
  exit 0
fi

# --- Check for force flags ---
HAS_FORCE=0
if echo "$TOOL_COMMAND" | grep -qE "(--force|-f)(\s|$)"; then
  HAS_FORCE=1
fi

if echo "$TOOL_COMMAND" | grep -q -- "--force-with-lease"; then
  HAS_FORCE=1
fi

[ "$HAS_FORCE" -eq 0 ] && exit 0

# --- Check if targeting a protected branch ---
TARGETED_BRANCH=""
for branch in $PROTECTED; do
  if echo "$TOOL_COMMAND" | grep -q "$branch"; then
    TARGETED_BRANCH="$branch"
    break
  fi
done

# Also check current branch
if [ -z "$TARGETED_BRANCH" ]; then
  CURRENT="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
  for branch in $PROTECTED; do
    if [ "$CURRENT" = "$branch" ]; then
      TARGETED_BRANCH="$branch"
      break
    fi
  done
fi

if [ -z "$TARGETED_BRANCH" ]; then
  # Force push to a non-protected branch — allowed
  echo "Force push to non-protected branch — allowed." >&2
  exit 0
fi

ERROR_MSG="Force push to '${TARGETED_BRANCH}' is not allowed.

Command: ${TOOL_COMMAND}

Force pushing to ${TARGETED_BRANCH} rewrites git history for all collaborators.
This operation requires explicit human authorization.

Alternatives:
  - Create a pull request instead
  - Revert commits with: git revert HEAD
  - Ask a human to approve before force pushing"

echo "" >&2
echo "FORCE-PUSH GUARD: Blocked" >&2
echo "" >&2
echo "$ERROR_MSG" >&2

if [ "$WARN_ONLY" = "1" ]; then
  echo "(Warning only — push will proceed)" >&2
  exit 0
fi

python3 -c "
import json, sys
print(json.dumps({
  'decision': 'block',
  'reason': sys.argv[1]
}))
" "$ERROR_MSG"

exit 0
