#!/usr/bin/env bash
# =============================================================================
# session-start.sh
# Claude Code hook — fires when an agent session begins.
#
# What it does:
#   1. Resolves the vault path from $OBSIDIAN_VAULT (with fallback).
#   2. Determines the current project name from the working directory.
#   3. Creates a timestamped session log note in 01-Projects/<project>/sessions/.
#   4. Appends an entry to today's daily note.
#
# Requirements:
#   - Obsidian running in the background
#   - obsidian CLI symlinked to ~/.local/bin/obsidian
#   - $OBSIDIAN_VAULT set to the absolute path of your vault
#
# Usage: called automatically by Claude Code hooks system.
#        Place this file at .claude/hooks/session-start.sh in your project.
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VAULT="${OBSIDIAN_VAULT:-}"
OBSIDIAN_BIN="${HOME}/.local/bin/obsidian"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M')"
DATE="$(date '+%Y-%m-%d')"
TIME="$(date '+%H%M')"

# Derive project name from working directory basename
PROJECT_NAME="$(basename "$PWD")"

# ---------------------------------------------------------------------------
# Guard: vault must be set
# ---------------------------------------------------------------------------
if [[ -z "$VAULT" ]]; then
  echo "[session-start] WARNING: OBSIDIAN_VAULT is not set. Skipping vault integration." >&2
  echo "[session-start] Set it with: export OBSIDIAN_VAULT=/path/to/your/vault" >&2
  exit 0
fi

if [[ ! -d "$VAULT" ]]; then
  echo "[session-start] WARNING: OBSIDIAN_VAULT path does not exist: $VAULT" >&2
  exit 0
fi

# ---------------------------------------------------------------------------
# Guard: Obsidian CLI must be available
# ---------------------------------------------------------------------------
use_cli=true
if [[ ! -x "$OBSIDIAN_BIN" ]]; then
  echo "[session-start] INFO: Obsidian CLI not found at $OBSIDIAN_BIN — falling back to direct file write." >&2
  use_cli=false
fi

# ---------------------------------------------------------------------------
# Build session log content
# ---------------------------------------------------------------------------
SESSION_DIR="01-Projects/${PROJECT_NAME}/sessions"
SESSION_FILE="${SESSION_DIR}/${DATE}-${TIME}-session.md"

SESSION_CONTENT="---
type: session-log
date: ${DATE}
time: ${TIMESTAMP}
project: ${PROJECT_NAME}
working_dir: ${PWD}
status: in-progress
tags: [session, ${PROJECT_NAME}]
---

# Session Log — ${TIMESTAMP}

**Project**: ${PROJECT_NAME}
**Working Dir**: \`${PWD}\`
**Started**: ${TIMESTAMP}

## Goal

<!-- Claude will populate this from the first task description -->

## Changes

<!-- Auto-populated during session -->

## Outcomes

<!-- Populated by session-end.sh hook -->
"

# ---------------------------------------------------------------------------
# Write session log
# ---------------------------------------------------------------------------
if [[ "$use_cli" == true ]]; then
  # Ensure the sessions directory exists as an Obsidian folder
  mkdir -p "${VAULT}/${SESSION_DIR}"

  # Write the file directly (obsidian create doesn't support multi-line content well)
  echo "$SESSION_CONTENT" > "${VAULT}/${SESSION_FILE}"

  echo "[session-start] Session log created: ${SESSION_FILE}" >&2
else
  # Direct file write fallback
  mkdir -p "${VAULT}/${SESSION_DIR}"
  echo "$SESSION_CONTENT" > "${VAULT}/${SESSION_FILE}"
  echo "[session-start] Session log created (direct write): ${SESSION_FILE}" >&2
fi

# ---------------------------------------------------------------------------
# Append to daily note
# ---------------------------------------------------------------------------
DAILY_ENTRY="| ${TIMESTAMP} | ${PROJECT_NAME} | (see session log) | in-progress |"

if [[ "$use_cli" == true ]]; then
  "$OBSIDIAN_BIN" daily:append content="$DAILY_ENTRY" 2>/dev/null || true
fi

echo "[session-start] Done. Session log: ${SESSION_FILE}"
