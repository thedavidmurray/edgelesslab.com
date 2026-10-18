#!/usr/bin/env bash
# =============================================================================
# context-preloader.sh — Pre-load relevant context before tasks
# =============================================================================
#
# WHAT IT DOES:
#   At session start, automatically discovers and outputs relevant context
#   files: CLAUDE.md, README, recent git log, open TODO items, and any
#   project-specific context files. Reduces the need for Claude to ask
#   for orientation information at the start of every session.
#
# WHEN TO USE IT:
#   Projects with non-trivial context. Especially useful when rotating
#   between multiple projects — Claude gets grounded immediately without
#   manual context-setting.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/context-preloader.sh
#   2. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "SessionStart": [
#         {
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/context-preloader.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   CONTEXT_MAX_LINES       — Max lines of context to output (default: 200)
#   CONTEXT_GIT_DEPTH       — How many commits to show (default: 5)
#   CONTEXT_EXTRA_FILES     — Colon-separated additional files to include
# =============================================================================

set -euo pipefail

MAX_LINES="${CONTEXT_MAX_LINES:-200}"
GIT_DEPTH="${CONTEXT_GIT_DEPTH:-5}"
EXTRA_FILES="${CONTEXT_EXTRA_FILES:-}"

OUTPUT=""
LINE_COUNT=0

append() {
  local content="$1"
  local lines
  lines="$(echo "$content" | wc -l)"
  OUTPUT="${OUTPUT}${content}\n\n"
  LINE_COUNT=$(( LINE_COUNT + lines ))
}

header() {
  append "=== $1 ==="
}

# --- CLAUDE.md ---
if [ -f "CLAUDE.md" ]; then
  header "CLAUDE.md"
  append "$(head -80 CLAUDE.md)"
fi

# --- README ---
for readme in README.md README.txt README; do
  if [ -f "$readme" ]; then
    header "README"
    append "$(head -40 "$readme")"
    break
  fi
done

# --- Recent git activity ---
if command -v git &>/dev/null && git rev-parse --git-dir &>/dev/null 2>&1; then
  header "Recent Git Activity (last ${GIT_DEPTH} commits)"
  GIT_LOG="$(git log --oneline -"${GIT_DEPTH}" 2>/dev/null || echo "No commits yet")"
  BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"
  append "Branch: ${BRANCH}\n${GIT_LOG}"

  # Uncommitted changes summary
  STATUS="$(git status --short 2>/dev/null || echo "")"
  if [ -n "$STATUS" ]; then
    header "Uncommitted Changes"
    append "$STATUS"
  fi
fi

# --- Open TODO items ---
if command -v grep &>/dev/null; then
  TODOS="$(grep -rn "TODO\|FIXME\|HACK\|XXX" \
    --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.sh" \
    --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv --exclude-dir=dist \
    . 2>/dev/null | head -20 || true)"

  if [ -n "$TODOS" ]; then
    header "Open TODOs (first 20)"
    append "$TODOS"
  fi
fi

# --- Extra files ---
if [ -n "$EXTRA_FILES" ]; then
  IFS=':' read -ra FILES <<< "$EXTRA_FILES"
  for f in "${FILES[@]}"; do
    if [ -f "$f" ]; then
      header "$f"
      append "$(head -50 "$f")"
    fi
  done
fi

# --- Active tasks if backlog exists ---
if [ -d "backlog/tasks" ]; then
  header "Active Tasks"
  TASKS="$(ls backlog/tasks/*.md 2>/dev/null | head -10 | while read -r f; do
    echo "  - $(basename "$f" .md)"
  done || echo "  None")"
  append "$TASKS"
fi

# Trim to max lines
FINAL_OUTPUT="$(printf "%b" "$OUTPUT" | head -"$MAX_LINES")"

if [ -n "$FINAL_OUTPUT" ]; then
  echo "" >&2
  echo "Context preloaded:" >&2
  printf "%b" "$OUTPUT" | head -"$MAX_LINES"
  echo "" >&2
fi

exit 0
