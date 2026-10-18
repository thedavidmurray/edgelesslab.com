#!/usr/bin/env bash
# =============================================================================
# session-end.sh
# Claude Code hook — fires when an agent session ends.
#
# What it does:
#   1. Locates the most recent session log for the current project.
#   2. Appends an "Outcomes" block with:
#      - End timestamp
#      - Files modified during the session (via git diff)
#      - Exit status of the session
#   3. Sets the session log frontmatter status to "complete".
#   4. Appends a completion marker to today's daily note.
#
# Requirements:
#   - Obsidian running in the background (optional — falls back to direct write)
#   - $OBSIDIAN_VAULT set to the absolute path of your vault
#   - Git available in the project directory
#
# Usage: called automatically by Claude Code hooks system.
#        Place this file at .claude/hooks/session-end.sh in your project.
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VAULT="${OBSIDIAN_VAULT:-}"
OBSIDIAN_BIN="${HOME}/.local/bin/obsidian"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M')"
DATE="$(date '+%Y-%m-%d')"
PROJECT_NAME="$(basename "$PWD")"
SESSION_DIR_REL="01-Projects/${PROJECT_NAME}/sessions"

# ---------------------------------------------------------------------------
# Guard: vault must be set
# ---------------------------------------------------------------------------
if [[ -z "$VAULT" ]]; then
  echo "[session-end] WARNING: OBSIDIAN_VAULT is not set. Skipping vault update." >&2
  exit 0
fi

if [[ ! -d "$VAULT" ]]; then
  echo "[session-end] WARNING: OBSIDIAN_VAULT path does not exist: $VAULT" >&2
  exit 0
fi

# ---------------------------------------------------------------------------
# Find the most recent session log for today
# ---------------------------------------------------------------------------
SESSION_DIR="${VAULT}/${SESSION_DIR_REL}"
SESSION_FILE=""

if [[ -d "$SESSION_DIR" ]]; then
  # Find the most recently modified session log from today
  SESSION_FILE=$(find "$SESSION_DIR" -name "${DATE}-*-session.md" -type f \
    | sort | tail -1)
fi

if [[ -z "$SESSION_FILE" ]]; then
  echo "[session-end] No session log found for today (${DATE}) in ${SESSION_DIR}." >&2
  echo "[session-end] Was session-start.sh called? Skipping." >&2
  exit 0
fi

echo "[session-end] Updating session log: ${SESSION_FILE}" >&2

# ---------------------------------------------------------------------------
# Collect changed files from git
# ---------------------------------------------------------------------------
CHANGED_FILES=""
if git -C "$PWD" rev-parse --git-dir > /dev/null 2>&1; then
  CHANGED_FILES=$(git -C "$PWD" diff --name-only HEAD 2>/dev/null \
    | sed 's/^/- /' || echo "- (no git changes detected)")
else
  CHANGED_FILES="- (not a git repository)"
fi

# ---------------------------------------------------------------------------
# Build the outcomes block to append
# ---------------------------------------------------------------------------
OUTCOMES_BLOCK="
---

## Session End

**Ended**: ${TIMESTAMP}
**Status**: complete

### Files Modified

${CHANGED_FILES:-"- (none)"}

### Summary

<!-- Agent: write 2–4 sentences summarising what was accomplished this session. -->
"

# ---------------------------------------------------------------------------
# Append outcomes to the session log
# ---------------------------------------------------------------------------
echo "$OUTCOMES_BLOCK" >> "$SESSION_FILE"

# ---------------------------------------------------------------------------
# Update frontmatter status to "complete" using sed (portable)
# Note: obsidian properties:set can also do this but sed is safer offline.
# ---------------------------------------------------------------------------
if [[ "$(uname)" == "Darwin" ]]; then
  # macOS sed requires empty string after -i
  sed -i '' 's/^status: in-progress/status: complete/' "$SESSION_FILE"
else
  sed -i 's/^status: in-progress/status: complete/' "$SESSION_FILE"
fi

# ---------------------------------------------------------------------------
# Append to daily note
# ---------------------------------------------------------------------------
DAILY_ENTRY="| ${TIMESTAMP} | ${PROJECT_NAME} | session complete | done |"

use_cli=true
if [[ ! -x "$OBSIDIAN_BIN" ]]; then
  use_cli=false
fi

if [[ "$use_cli" == true ]]; then
  "$OBSIDIAN_BIN" daily:append content="$DAILY_ENTRY" 2>/dev/null || true
fi

echo "[session-end] Done. Session marked complete: $(basename "$SESSION_FILE")"
