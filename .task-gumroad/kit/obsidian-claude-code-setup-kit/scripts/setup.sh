#!/usr/bin/env bash
# =============================================================================
# setup.sh — Obsidian + Claude Code Setup Kit
#
# One-click setup script that:
#   1. Copies the vault template to a target vault location
#   2. Installs community plugins via the Obsidian CLI
#   3. Patches (or creates) CLAUDE.md in your project with Obsidian integration
#   4. Installs session hooks into .claude/hooks/
#   5. Prints a post-install checklist
#
# Usage:
#   bash setup.sh [options]
#
# Options:
#   --vault PATH        Target vault directory (default: ~/obsidian-vault)
#   --project PATH      Target project directory (default: current dir)
#   --skip-plugins      Skip plugin installation (if Obsidian CLI unavailable)
#   --skip-claude-md    Do not modify or create CLAUDE.md
#   --dry-run           Print what would happen without making changes
#   -h, --help          Show this help
#
# Requirements:
#   - bash >= 3.2
#   - jq >= 1.6  (brew install jq / apt install jq)
#   - Obsidian >= 1.5.0 with CLI enabled (for plugin install)
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VAULT_TEMPLATE="${KIT_ROOT}/vault-template"
CLAUDE_CONFIG="${KIT_ROOT}/claude-config"

TARGET_VAULT="${HOME}/obsidian-vault"
TARGET_PROJECT="${PWD}"
SKIP_PLUGINS=false
SKIP_CLAUDE_MD=false
DRY_RUN=false

OBSIDIAN_BIN="${HOME}/.local/bin/obsidian"

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log_info()    { echo -e "${BLUE}[info]${RESET}  $*"; }
log_ok()      { echo -e "${GREEN}[ok]${RESET}    $*"; }
log_warn()    { echo -e "${YELLOW}[warn]${RESET}  $*"; }
log_error()   { echo -e "${RED}[error]${RESET} $*" >&2; }
log_step()    { echo -e "\n${BOLD}==> $*${RESET}"; }

run() {
  if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}[dry-run]${RESET} $*"
  else
    eval "$@"
  fi
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --vault)       TARGET_VAULT="$2";  shift 2 ;;
    --project)     TARGET_PROJECT="$2"; shift 2 ;;
    --skip-plugins)   SKIP_PLUGINS=true;  shift ;;
    --skip-claude-md) SKIP_CLAUDE_MD=true; shift ;;
    --dry-run)     DRY_RUN=true; shift ;;
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

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}Obsidian + Claude Code Setup Kit${RESET}"
echo "================================================="
echo "  Vault target  : ${TARGET_VAULT}"
echo "  Project target: ${TARGET_PROJECT}"
echo "  Dry run       : ${DRY_RUN}"
echo "================================================="
echo ""

# ---------------------------------------------------------------------------
# Step 1 — Verify dependencies
# ---------------------------------------------------------------------------
log_step "1. Checking dependencies"

if ! command -v jq &>/dev/null; then
  log_error "jq is required but not installed."
  log_error "  macOS: brew install jq"
  log_error "  Linux: apt install jq / yum install jq"
  exit 1
fi
log_ok "jq found: $(jq --version)"

if [[ ! -x "$OBSIDIAN_BIN" ]] && [[ "$SKIP_PLUGINS" == false ]]; then
  log_warn "Obsidian CLI not found at ${OBSIDIAN_BIN}."
  log_warn "Plugin installation will be skipped. Pass --skip-plugins to suppress this warning."
  log_warn "To enable: Settings → General → Advanced → CLI, then:"
  log_warn "  ln -s /Applications/Obsidian.app/Contents/MacOS/Obsidian ~/.local/bin/obsidian"
  SKIP_PLUGINS=true
fi

if [[ -x "$OBSIDIAN_BIN" ]]; then
  log_ok "Obsidian CLI found: $OBSIDIAN_BIN"
fi

# ---------------------------------------------------------------------------
# Step 2 — Copy vault template
# ---------------------------------------------------------------------------
log_step "2. Setting up vault at ${TARGET_VAULT}"

if [[ -d "$TARGET_VAULT" ]]; then
  log_warn "Vault directory already exists: ${TARGET_VAULT}"

  # Check if it already has our structure
  if [[ -f "${TARGET_VAULT}/.obsidian/app.json" ]]; then
    log_warn "Existing Obsidian config detected. Creating backup before overwriting..."
    BACKUP_PATH="${TARGET_VAULT}.backup.$(date +%Y%m%d%H%M%S)"
    run "cp -r '${TARGET_VAULT}/.obsidian' '${BACKUP_PATH}'"
    log_ok "Backup created: ${BACKUP_PATH}"
  fi

  # Merge (do not overwrite existing user notes)
  log_info "Merging vault template (existing notes are safe)..."
  run "rsync -a --ignore-existing '${VAULT_TEMPLATE}/' '${TARGET_VAULT}/'"
else
  log_info "Creating vault at ${TARGET_VAULT}..."
  run "cp -r '${VAULT_TEMPLATE}' '${TARGET_VAULT}'"
fi

log_ok "Vault template applied."

# ---------------------------------------------------------------------------
# Step 3 — Set OBSIDIAN_VAULT in shell profile
# ---------------------------------------------------------------------------
log_step "3. Configuring OBSIDIAN_VAULT environment variable"

SHELL_PROFILE=""
if [[ -f "${HOME}/.zshrc" ]]; then
  SHELL_PROFILE="${HOME}/.zshrc"
elif [[ -f "${HOME}/.bashrc" ]]; then
  SHELL_PROFILE="${HOME}/.bashrc"
elif [[ -f "${HOME}/.bash_profile" ]]; then
  SHELL_PROFILE="${HOME}/.bash_profile"
fi

if [[ -n "$SHELL_PROFILE" ]]; then
  if grep -q "OBSIDIAN_VAULT" "$SHELL_PROFILE" 2>/dev/null; then
    log_info "OBSIDIAN_VAULT already set in ${SHELL_PROFILE}. Skipping."
  else
    EXPORT_LINE="export OBSIDIAN_VAULT=\"${TARGET_VAULT}\""
    run "echo '' >> '${SHELL_PROFILE}'"
    run "echo '# Obsidian + Claude Code Setup Kit' >> '${SHELL_PROFILE}'"
    run "echo '${EXPORT_LINE}' >> '${SHELL_PROFILE}'"
    log_ok "Added OBSIDIAN_VAULT to ${SHELL_PROFILE}"
    log_info "Run: source ${SHELL_PROFILE}  (or open a new terminal)"
  fi
else
  log_warn "No shell profile found. Add manually:"
  echo "    export OBSIDIAN_VAULT=\"${TARGET_VAULT}\""
fi

# ---------------------------------------------------------------------------
# Step 4 — Install community plugins
# ---------------------------------------------------------------------------
log_step "4. Installing Obsidian community plugins"

PLUGINS=(
  "dataview"
  "templater-obsidian"
  "omnisearch"
  "obsidian-excalidraw-plugin"
  "tag-wrangler"
  "auto-link-title"
  "obsidian-copilot"
)

if [[ "$SKIP_PLUGINS" == true ]]; then
  log_warn "Plugin installation skipped."
  log_warn "Install manually from Obsidian: Settings → Community Plugins → Browse"
  log_warn "Required plugins: ${PLUGINS[*]}"
else
  for plugin in "${PLUGINS[@]}"; do
    log_info "Installing plugin: ${plugin}"
    run "$OBSIDIAN_BIN plugin:install id=\"${plugin}\" enable 2>/dev/null" || \
      log_warn "  Could not install ${plugin} — install manually from Obsidian."
  done
  log_ok "Plugin installation complete."
fi

# ---------------------------------------------------------------------------
# Step 5 — Install Claude hooks
# ---------------------------------------------------------------------------
log_step "5. Installing Claude Code hooks into ${TARGET_PROJECT}/.claude/hooks/"

HOOKS_DIR="${TARGET_PROJECT}/.claude/hooks"
run "mkdir -p '${HOOKS_DIR}'"

for hook in session-start.sh session-end.sh; do
  SRC="${CLAUDE_CONFIG}/hooks/${hook}"
  DEST="${HOOKS_DIR}/${hook}"

  if [[ -f "$DEST" ]]; then
    log_warn "Hook already exists: ${DEST} — skipping (delete to reinstall)"
  else
    run "cp '${SRC}' '${DEST}'"
    run "chmod +x '${DEST}'"
    log_ok "Installed hook: ${hook}"
  fi
done

# ---------------------------------------------------------------------------
# Step 6 — Install obsidian-search skill
# ---------------------------------------------------------------------------
log_step "6. Installing obsidian-search skill"

SKILL_DIR="${TARGET_PROJECT}/.claude/skills/obsidian-search"
run "mkdir -p '${SKILL_DIR}'"

SKILL_SRC="${CLAUDE_CONFIG}/skills/obsidian-search/skill.md"
SKILL_DEST="${SKILL_DIR}/skill.md"

if [[ -f "$SKILL_DEST" ]]; then
  log_warn "Skill already exists: ${SKILL_DEST} — skipping."
else
  run "cp '${SKILL_SRC}' '${SKILL_DEST}'"
  log_ok "Installed skill: obsidian-search"
fi

# ---------------------------------------------------------------------------
# Step 7 — Patch or create CLAUDE.md
# ---------------------------------------------------------------------------
log_step "7. Configuring CLAUDE.md"

CLAUDE_MD="${TARGET_PROJECT}/CLAUDE.md"

if [[ "$SKIP_CLAUDE_MD" == true ]]; then
  log_warn "CLAUDE.md modification skipped (--skip-claude-md)."
elif [[ -f "$CLAUDE_MD" ]]; then
  if grep -q "OBSIDIAN_VAULT\|obsidian-search" "$CLAUDE_MD" 2>/dev/null; then
    log_info "CLAUDE.md already contains Obsidian integration. Skipping."
  else
    log_info "Appending Obsidian integration section to existing CLAUDE.md..."
    APPEND_BLOCK="

## Obsidian Vault Integration

This project uses the Obsidian + Claude Code Setup Kit.
See: \`.claude/skills/obsidian-search/skill.md\`

\`\`\`bash
# Search vault
~/.local/bin/obsidian search query=\"<keyword>\" 2>/dev/null

# Append to daily note
~/.local/bin/obsidian daily:append content=\"- note\" 2>/dev/null
\`\`\`

Vault path: \$OBSIDIAN_VAULT (set in your shell profile)
"
    run "echo '${APPEND_BLOCK}' >> '${CLAUDE_MD}'"
    log_ok "Obsidian section appended to CLAUDE.md"
  fi
else
  log_info "No CLAUDE.md found — creating from kit template..."
  run "cp '${CLAUDE_CONFIG}/CLAUDE.md' '${CLAUDE_MD}'"
  log_ok "CLAUDE.md created."
fi

# ---------------------------------------------------------------------------
# Done — Post-install checklist
# ---------------------------------------------------------------------------
echo ""
echo -e "${GREEN}${BOLD}Setup complete!${RESET}"
echo ""
echo "Post-install checklist:"
echo ""
echo "  [ ] Open Obsidian and point it at: ${TARGET_VAULT}"
echo "  [ ] Accept the 'Enable community plugins?' prompt"
echo "  [ ] Open: Settings → Community Plugins → Check for updates"
echo "  [ ] Enable Templater: Settings → Templater → Trigger on new file creation"
echo "  [ ] Set template folder: Settings → Templater → Template folder = _system/templates"
echo "  [ ] Run: source ${SHELL_PROFILE:-~/.zshrc}"
echo "  [ ] Start a Claude Code session to verify session-start.sh fires"
echo ""
echo "Vault     : ${TARGET_VAULT}"
echo "Hooks     : ${TARGET_PROJECT}/.claude/hooks/"
echo "Skill     : ${TARGET_PROJECT}/.claude/skills/obsidian-search/"
echo "CLAUDE.md : ${TARGET_PROJECT}/CLAUDE.md"
echo ""
echo -e "${BLUE}Full docs: ${KIT_ROOT}/README.md${RESET}"
echo ""
