#!/usr/bin/env bash
# =============================================================================
# sync-to-vault.sh — Obsidian + Claude Code Setup Kit
#
# Syncs project findings into the Obsidian vault. Designed to be run after
# a Claude Code session that produced research, decisions, or captures worth
# preserving in long-term knowledge storage.
#
# What it syncs:
#   - Any *.md files in a configurable SOURCE_DIRS list
#   - Git log summary (last N commits) → 01-Projects/<project>/git-log.md
#   - Session logs from .claude/hooks output (if any)
#
# Usage:
#   bash scripts/sync-to-vault.sh [options]
#
# Options:
#   --vault PATH        Vault path (default: $OBSIDIAN_VAULT or ~/obsidian-vault)
#   --project PATH      Project root (default: current directory)
#   --source DIR        Additional source directory to sync (repeatable)
#   --git-log N         Include last N git commits in sync (default: 20, 0 to skip)
#   --dry-run           Print what would be synced without writing
#   -h, --help          Show this help
#
# Destination mapping:
#   docs/*.md               → 02-Knowledge/<project>/
#   research/*.md           → 02-Knowledge/<project>/research/
#   decisions/*.md          → 02-Knowledge/<project>/decisions/
#   notes/*.md              → 00-Inbox/
#   (other .md in root)     → 00-Inbox/
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TARGET_VAULT="${OBSIDIAN_VAULT:-${HOME}/obsidian-vault}"
TARGET_PROJECT="${PWD}"
GIT_LOG_COUNT=20
DRY_RUN=false
EXTRA_SOURCES=()

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

log_info()  { echo -e "${BLUE}[info]${RESET}  $*"; }
log_ok()    { echo -e "${GREEN}[ok]${RESET}    $*"; }
log_warn()  { echo -e "${YELLOW}[warn]${RESET}  $*"; }
log_error() { echo -e "${RED}[error]${RESET} $*" >&2; }
log_step()  { echo -e "\n${BOLD}==> $*${RESET}"; }

sync_file() {
  local src="$1"
  local dest_dir="$2"
  local dest_file="${dest_dir}/$(basename "$src")"

  if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}[dry-run]${RESET} cp '${src}' → '${dest_dir}/'"
    return
  fi

  mkdir -p "$dest_dir"

  if [[ -f "$dest_file" ]]; then
    # Append a sync block rather than overwrite, to preserve manual edits
    {
      echo ""
      echo "---"
      echo "<!-- synced from: ${src} on $(date '+%Y-%m-%d %H:%M') -->"
      echo ""
      cat "$src"
    } >> "$dest_file"
    log_info "Appended: $(basename "$src") → ${dest_dir}/"
  else
    cp "$src" "$dest_file"
    log_ok "Copied: $(basename "$src") → ${dest_dir}/"
  fi
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --vault)     TARGET_VAULT="$2";       shift 2 ;;
    --project)   TARGET_PROJECT="$2";     shift 2 ;;
    --source)    EXTRA_SOURCES+=("$2");   shift 2 ;;
    --git-log)   GIT_LOG_COUNT="$2";      shift 2 ;;
    --dry-run)   DRY_RUN=true;            shift ;;
    -h|--help)
      sed -n '/^# Usage:/,/^# ========/p' "$0" | head -n -1 | sed 's/^# \{0,2\}//'
      exit 0
      ;;
    *)
      log_error "Unknown option: $1"
      exit 1
      ;;
  esac
done

PROJECT_NAME="$(basename "$TARGET_PROJECT")"

# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------
log_step "Pre-flight checks"

if [[ ! -d "$TARGET_VAULT" ]]; then
  log_error "Vault not found at: ${TARGET_VAULT}"
  log_error "Run setup.sh first, or set --vault to the correct path."
  exit 1
fi
log_ok "Vault found: ${TARGET_VAULT}"

if [[ ! -d "$TARGET_PROJECT" ]]; then
  log_error "Project directory not found: ${TARGET_PROJECT}"
  exit 1
fi
log_ok "Project: ${TARGET_PROJECT} (${PROJECT_NAME})"

# ---------------------------------------------------------------------------
# Step 1 — Sync docs/
# ---------------------------------------------------------------------------
log_step "1. Syncing docs/*.md → 02-Knowledge/${PROJECT_NAME}/"

DOCS_DIR="${TARGET_PROJECT}/docs"
DEST_KNOWLEDGE="${TARGET_VAULT}/02-Knowledge/${PROJECT_NAME}"

if [[ -d "$DOCS_DIR" ]]; then
  COUNT=0
  while IFS= read -r -d '' file; do
    sync_file "$file" "$DEST_KNOWLEDGE"
    ((COUNT++)) || true
  done < <(find "$DOCS_DIR" -maxdepth 2 -name "*.md" -type f -print0 2>/dev/null)

  if [[ $COUNT -eq 0 ]]; then
    log_info "No markdown files found in ${DOCS_DIR}/"
  else
    log_ok "Synced ${COUNT} file(s) from docs/"
  fi
else
  log_info "No docs/ directory found — skipping."
fi

# ---------------------------------------------------------------------------
# Step 2 — Sync research/
# ---------------------------------------------------------------------------
log_step "2. Syncing research/*.md → 02-Knowledge/${PROJECT_NAME}/research/"

RESEARCH_DIR="${TARGET_PROJECT}/research"
DEST_RESEARCH="${TARGET_VAULT}/02-Knowledge/${PROJECT_NAME}/research"

if [[ -d "$RESEARCH_DIR" ]]; then
  COUNT=0
  while IFS= read -r -d '' file; do
    sync_file "$file" "$DEST_RESEARCH"
    ((COUNT++)) || true
  done < <(find "$RESEARCH_DIR" -maxdepth 2 -name "*.md" -type f -print0 2>/dev/null)

  if [[ $COUNT -eq 0 ]]; then
    log_info "No markdown files found in ${RESEARCH_DIR}/"
  else
    log_ok "Synced ${COUNT} file(s) from research/"
  fi
else
  log_info "No research/ directory found — skipping."
fi

# ---------------------------------------------------------------------------
# Step 3 — Sync decisions/ (ADRs, lightweight decision records)
# ---------------------------------------------------------------------------
log_step "3. Syncing decisions/*.md → 02-Knowledge/${PROJECT_NAME}/decisions/"

DECISIONS_DIR="${TARGET_PROJECT}/decisions"
DEST_DECISIONS="${TARGET_VAULT}/02-Knowledge/${PROJECT_NAME}/decisions"

if [[ -d "$DECISIONS_DIR" ]]; then
  COUNT=0
  while IFS= read -r -d '' file; do
    sync_file "$file" "$DEST_DECISIONS"
    ((COUNT++)) || true
  done < <(find "$DECISIONS_DIR" -maxdepth 2 -name "*.md" -type f -print0 2>/dev/null)

  if [[ $COUNT -eq 0 ]]; then
    log_info "No markdown files found in ${DECISIONS_DIR}/"
  else
    log_ok "Synced ${COUNT} file(s) from decisions/"
  fi
else
  log_info "No decisions/ directory found — skipping."
fi

# ---------------------------------------------------------------------------
# Step 4 — Sync notes/ and root *.md → 00-Inbox/
# ---------------------------------------------------------------------------
log_step "4. Syncing loose notes → 00-Inbox/"

DEST_INBOX="${TARGET_VAULT}/00-Inbox"

# Root-level markdown files (excluding README, CLAUDE, LICENSE, CHANGELOG)
SKIP_FILES=(README.md CLAUDE.md LICENSE.md CHANGELOG.md)
COUNT=0

while IFS= read -r -d '' file; do
  BASENAME="$(basename "$file")"
  SKIP=false
  for skip in "${SKIP_FILES[@]}"; do
    [[ "$BASENAME" == "$skip" ]] && SKIP=true && break
  done
  [[ "$SKIP" == true ]] && continue

  sync_file "$file" "$DEST_INBOX"
  ((COUNT++)) || true
done < <(find "$TARGET_PROJECT" -maxdepth 1 -name "*.md" -type f -print0 2>/dev/null)

# notes/ subdirectory
NOTES_DIR="${TARGET_PROJECT}/notes"
if [[ -d "$NOTES_DIR" ]]; then
  while IFS= read -r -d '' file; do
    sync_file "$file" "$DEST_INBOX"
    ((COUNT++)) || true
  done < <(find "$NOTES_DIR" -maxdepth 2 -name "*.md" -type f -print0 2>/dev/null)
fi

if [[ $COUNT -eq 0 ]]; then
  log_info "No loose notes to sync."
else
  log_ok "Synced ${COUNT} file(s) to 00-Inbox/"
fi

# ---------------------------------------------------------------------------
# Step 5 — Extra source directories
# ---------------------------------------------------------------------------
if [[ ${#EXTRA_SOURCES[@]} -gt 0 ]]; then
  log_step "5. Syncing extra source directories"
  for src_dir in "${EXTRA_SOURCES[@]}"; do
    if [[ -d "$src_dir" ]]; then
      COUNT=0
      DEST="${TARGET_VAULT}/00-Inbox/$(basename "$src_dir")"
      while IFS= read -r -d '' file; do
        sync_file "$file" "$DEST"
        ((COUNT++)) || true
      done < <(find "$src_dir" -name "*.md" -type f -print0 2>/dev/null)
      log_ok "Synced ${COUNT} file(s) from ${src_dir}/"
    else
      log_warn "Extra source not found: ${src_dir}"
    fi
  done
fi

# ---------------------------------------------------------------------------
# Step 6 — Git log summary
# ---------------------------------------------------------------------------
if [[ $GIT_LOG_COUNT -gt 0 ]]; then
  log_step "6. Generating git log summary"

  GIT_LOG_DEST="${TARGET_VAULT}/01-Projects/${PROJECT_NAME}/git-log.md"

  if git -C "$TARGET_PROJECT" rev-parse --git-dir > /dev/null 2>&1; then
    GIT_LOG_CONTENT="# Git Log — ${PROJECT_NAME}

*Last ${GIT_LOG_COUNT} commits — synced $(date '+%Y-%m-%d %H:%M')*

\`\`\`
$(git -C "$TARGET_PROJECT" log --oneline -"${GIT_LOG_COUNT}" 2>/dev/null || echo "(no commits)")
\`\`\`
"
    if [[ "$DRY_RUN" == true ]]; then
      echo -e "${YELLOW}[dry-run]${RESET} Would write git log to: ${GIT_LOG_DEST}"
    else
      mkdir -p "$(dirname "$GIT_LOG_DEST")"
      echo "$GIT_LOG_CONTENT" > "$GIT_LOG_DEST"
      log_ok "Git log written to: 01-Projects/${PROJECT_NAME}/git-log.md"
    fi
  else
    log_info "Not a git repository — skipping git log."
  fi
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo -e "${GREEN}${BOLD}Sync complete.${RESET}"
echo ""
echo "  Vault: ${TARGET_VAULT}"
echo "  Open Obsidian to review new content in:"
echo "    00-Inbox/     ← loose notes and captures"
echo "    01-Projects/${PROJECT_NAME}/  ← project session logs"
echo "    02-Knowledge/${PROJECT_NAME}/ ← docs, research, decisions"
echo ""

# Remind user to process inbox
INBOX_COUNT=$(find "${TARGET_VAULT}/00-Inbox" -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
if [[ "$INBOX_COUNT" -gt 5 ]]; then
  log_warn "00-Inbox/ has ${INBOX_COUNT} files — consider processing it now."
fi

echo -e "${BLUE}Tip: run 'obsidian search query=\"${PROJECT_NAME}\"' to verify sync.${RESET}"
echo ""
