#!/usr/bin/env bash
# =============================================================================
# linear-sync.sh — Sync task status with Linear
# =============================================================================
#
# WHAT IT DOES:
#   Detects when Claude Code completes a task referencing a Linear issue ID
#   (e.g. ENG-123) in branch names, commit messages, or task descriptions.
#   Updates the corresponding Linear issue to "In Review" or "Done" via API.
#
# WHEN TO USE IT:
#   Teams using Linear for project management. Eliminates the manual step of
#   updating issue status after AI-assisted implementation.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/linear-sync.sh
#   2. Get a Linear API key: Settings → API → Personal API keys
#   3. Set LINEAR_API_KEY in your environment
#   4. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "Stop": [
#         {
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/linear-sync.sh"
#             }
#           ]
#         }
#       ],
#       "PostToolUse": [
#         {
#           "matcher": "Bash",
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/linear-sync.sh commit"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   LINEAR_API_KEY         — Required. Linear personal API key
#   LINEAR_DONE_STATE      — State name when session ends (default: In Review)
#   LINEAR_COMMIT_STATE    — State name on commit (default: In Progress)
#   LINEAR_TEAM_ID         — Scope to specific team (optional)
# =============================================================================

set -euo pipefail

# --- Load .env if present ---
if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source .env 2>/dev/null || true
  set +a
fi

LINEAR_API_KEY="${LINEAR_API_KEY:-}"
DONE_STATE="${LINEAR_DONE_STATE:-In Review}"
COMMIT_STATE="${LINEAR_COMMIT_STATE:-In Progress}"
ACTION="${1:-stop}"

if [ -z "$LINEAR_API_KEY" ]; then
  echo "LINEAR_API_KEY not set — skipping Linear sync." >&2
  exit 0
fi

if ! command -v curl &>/dev/null; then
  exit 0
fi

# --- Extract issue ID from context ---
# Check: current branch name, latest commit message
ISSUE_ID=""

BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
COMMIT_MSG="$(git log -1 --format="%s" 2>/dev/null || echo "")"

for source in "$BRANCH" "$COMMIT_MSG"; do
  ID="$(echo "$source" | grep -oE "[A-Z]+-[0-9]+" | head -1 || true)"
  if [ -n "$ID" ]; then
    ISSUE_ID="$ID"
    break
  fi
done

if [ -z "$ISSUE_ID" ]; then
  echo "No Linear issue ID found in branch or commits — skipping." >&2
  exit 0
fi

echo "Found Linear issue: ${ISSUE_ID}" >&2

# Determine target state
case "$ACTION" in
  stop|end) TARGET_STATE="$DONE_STATE" ;;
  commit)   TARGET_STATE="$COMMIT_STATE" ;;
  *)        TARGET_STATE="$ACTION" ;;
esac

# --- Get issue internal ID ---
QUERY="{\"query\":\"query { issue(id: \\\"${ISSUE_ID}\\\") { id title state { id name } } }\"}"

ISSUE_DATA="$(curl -s \
  -H "Authorization: ${LINEAR_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$QUERY" \
  "https://api.linear.app/graphql" 2>/dev/null)"

ISSUE_INTERNAL_ID="$(echo "$ISSUE_DATA" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d['data']['issue']['id'])
except:
    print('')
" 2>/dev/null || echo "")"

if [ -z "$ISSUE_INTERNAL_ID" ]; then
  echo "Could not find Linear issue ${ISSUE_ID} — check ID and API key." >&2
  exit 0
fi

# --- Get state ID for target state ---
STATE_QUERY="{\"query\":\"query { workflowStates { nodes { id name } } }\"}"
STATE_DATA="$(curl -s \
  -H "Authorization: ${LINEAR_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$STATE_QUERY" \
  "https://api.linear.app/graphql" 2>/dev/null)"

STATE_ID="$(echo "$STATE_DATA" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    states = d['data']['workflowStates']['nodes']
    target = '${TARGET_STATE}'.lower()
    for s in states:
        if s['name'].lower() == target:
            print(s['id'])
            break
except:
    pass
" 2>/dev/null || echo "")"

if [ -z "$STATE_ID" ]; then
  echo "State '${TARGET_STATE}' not found in Linear — check state names." >&2
  exit 0
fi

# --- Update issue state ---
UPDATE_MUTATION="{\"query\":\"mutation { issueUpdate(id: \\\"${ISSUE_INTERNAL_ID}\\\", input: { stateId: \\\"${STATE_ID}\\\" }) { success } }\"}"

RESULT="$(curl -s \
  -H "Authorization: ${LINEAR_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$UPDATE_MUTATION" \
  "https://api.linear.app/graphql" 2>/dev/null)"

SUCCESS="$(echo "$RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d['data']['issueUpdate']['success'])
except:
    print('false')
" 2>/dev/null || echo "false")"

if [ "$SUCCESS" = "True" ]; then
  echo "Linear: ${ISSUE_ID} → ${TARGET_STATE}" >&2
else
  echo "Linear update failed for ${ISSUE_ID}." >&2
fi

exit 0
