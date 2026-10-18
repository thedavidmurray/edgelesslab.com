#!/usr/bin/env bash
# =============================================================================
# git-conventional.sh — Enforce conventional commit message format
# =============================================================================
#
# WHAT IT DOES:
#   Intercepts git commit commands and validates that the commit message
#   follows Conventional Commits (https://www.conventionalcommits.org/).
#   Blocks commits with non-conforming messages and shows examples.
#
# VALID FORMATS:
#   feat(scope): add user authentication
#   fix: resolve null pointer in parser
#   chore!: drop Node 16 support (breaking change)
#   docs(api): update rate limit documentation
#
# VALID TYPES:
#   feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
#
# WHEN TO USE IT:
#   Teams using semantic versioning, changelog generation, or any tooling
#   that parses commit history. Also useful when working solo to maintain
#   readable git history.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/git-conventional.sh
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
#               "command": "bash .claude/hooks/git-conventional.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   CONVENTIONAL_TYPES    — Colon-separated list of allowed types (overrides defaults)
#   CONVENTIONAL_WARN     — Set to "1" to warn instead of block
# =============================================================================

set -euo pipefail

WARN_ONLY="${CONVENTIONAL_WARN:-0}"

DEFAULT_TYPES="feat:fix:docs:style:refactor:perf:test:build:ci:chore:revert"
ALLOWED_TYPES="${CONVENTIONAL_TYPES:-$DEFAULT_TYPES}"

# Conventional commit regex
# Format: type(optional-scope)!: description
CC_REGEX='^('"$(echo "$ALLOWED_TYPES" | tr ':' '|')"')(\([a-zA-Z0-9_/-]+\))?!?: .{1,100}$'

# --- Read hook input ---
INPUT="$(cat)"
TOOL_COMMAND="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('command', ''))
" 2>/dev/null || echo "")"

# Only intercept git commit
if ! echo "$TOOL_COMMAND" | grep -qE "git commit"; then
  exit 0
fi

# Extract commit message from the command
# Handles: git commit -m "..." and git commit --message="..."
COMMIT_MSG="$(echo "$TOOL_COMMAND" | python3 -c "
import sys, re
cmd = sys.stdin.read()
# Match -m 'msg' or -m \"msg\" or --message='msg'
patterns = [
    r'-m [\"\'](.*?)[\"\']',
    r'--message=[\"\'](.*?)[\"\']',
    r'-m ([\S]+)',
]
for p in patterns:
    m = re.search(p, cmd)
    if m:
        print(m.group(1))
        break
" 2>/dev/null || echo "")"

if [ -z "$COMMIT_MSG" ]; then
  # Can't extract message — let it through (may be using -F or editor)
  exit 0
fi

# --- Validate ---
if echo "$COMMIT_MSG" | grep -qE "$CC_REGEX"; then
  echo "Commit message format: valid" >&2
  exit 0
fi

EXAMPLES="
  feat: add password reset endpoint
  fix(auth): handle expired session tokens
  docs: update API reference for v2
  chore!: remove deprecated --legacy flag
  refactor(parser): split tokenizer into separate module
"

TYPES_LIST="$(echo "$ALLOWED_TYPES" | tr ':' ', ')"

ERROR_MSG="Commit message does not follow Conventional Commits format.

Message received: ${COMMIT_MSG}

Required format:  type(scope): description
Allowed types:    ${TYPES_LIST}

Examples:${EXAMPLES}
See: https://www.conventionalcommits.org"

echo "" >&2
echo "CONVENTIONAL COMMIT: invalid message format" >&2
echo "" >&2
echo "$ERROR_MSG" >&2

if [ "$WARN_ONLY" = "1" ]; then
  echo "(Warning only — commit will proceed)" >&2
  exit 0
fi

python3 -c "
import json, sys
msg = sys.argv[1]
print(json.dumps({
  'decision': 'block',
  'reason': msg
}))
" "$ERROR_MSG"

exit 0
