#!/usr/bin/env bash
# =============================================================================
# changelog-updater.sh — Auto-update CHANGELOG on version bump
# =============================================================================
#
# WHAT IT DOES:
#   Detects when a version bump occurs (package.json, pyproject.toml,
#   Cargo.toml, or explicit bump commands) and generates a new CHANGELOG.md
#   section from git commits since the last tag. Follows Keep a Changelog
#   format (https://keepachangelog.com).
#
# WHEN TO USE IT:
#   Projects that maintain a CHANGELOG and use semantic versioning. Eliminates
#   the tedious manual step of writing change entries.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/changelog-updater.sh
#   2. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "PostToolUse": [
#         {
#           "matcher": "Edit|Write",
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/changelog-updater.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   CHANGELOG_FILE         — Path to changelog (default: CHANGELOG.md)
#   CHANGELOG_REPO_URL     — GitHub URL for compare links (optional)
#   CHANGELOG_AUTO_COMMIT  — Set to "1" to auto-commit changelog updates
# =============================================================================

set -euo pipefail

CHANGELOG_FILE="${CHANGELOG_FILE:-CHANGELOG.md}"
REPO_URL="${CHANGELOG_REPO_URL:-}"
AUTO_COMMIT="${CHANGELOG_AUTO_COMMIT:-0}"

# --- Read edited file ---
INPUT="$(cat)"
EDITED_FILE="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ti = d.get('tool_input', {})
print(ti.get('path', ti.get('file_path', '')))
" 2>/dev/null || echo "")"

# Only trigger on version files
VERSION_FILES=("package.json" "pyproject.toml" "Cargo.toml" "setup.py" "VERSION")
IS_VERSION_FILE=0
for vf in "${VERSION_FILES[@]}"; do
  if [ "$(basename "${EDITED_FILE}")" = "$vf" ]; then
    IS_VERSION_FILE=1
    break
  fi
done

[ "$IS_VERSION_FILE" -eq 0 ] && exit 0

# --- Extract new version ---
extract_version() {
  local file="$1"
  case "$(basename "$file")" in
    package.json)
      python3 -c "import json; print(json.load(open('$file'))['version'])" 2>/dev/null || echo ""
      ;;
    pyproject.toml)
      grep -E '^version\s*=' "$file" | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+[^"]*' || echo ""
      ;;
    Cargo.toml)
      grep -E '^version\s*=' "$file" | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+[^"]*' || echo ""
      ;;
    VERSION)
      cat "$file" | tr -d '[:space:]'
      ;;
    *)
      echo ""
      ;;
  esac
}

NEW_VERSION="$(extract_version "$EDITED_FILE")"
if [ -z "$NEW_VERSION" ]; then
  exit 0
fi

# --- Get last tag ---
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "")"
DATE="$(date +"%Y-%m-%d")"

# --- Gather commits since last tag ---
if [ -n "$LAST_TAG" ]; then
  COMMITS="$(git log "${LAST_TAG}..HEAD" --oneline --no-merges 2>/dev/null || true)"
else
  COMMITS="$(git log --oneline --no-merges -20 2>/dev/null || true)"
fi

if [ -z "$COMMITS" ]; then
  COMMITS="Initial release"
fi

# --- Categorize commits by conventional commit type ---
SECTION_CONTENT="$(echo "$COMMITS" | python3 -c "
import sys, re

lines = sys.stdin.read().strip().split('\n')
sections = {
    'Added': [],
    'Fixed': [],
    'Changed': [],
    'Removed': [],
    'Security': [],
    'Other': []
}

type_map = {
    'feat': 'Added',
    'fix': 'Fixed',
    'refactor': 'Changed',
    'chore': 'Changed',
    'docs': 'Changed',
    'style': 'Changed',
    'perf': 'Changed',
    'revert': 'Removed',
    'security': 'Security'
}

for line in lines:
    # Strip commit hash
    parts = line.split(' ', 1)
    msg = parts[1] if len(parts) > 1 else line

    m = re.match(r'^(\w+)(?:\([^)]+\))?: (.+)', msg)
    if m:
        t, desc = m.group(1), m.group(2)
        section = type_map.get(t, 'Other')
    else:
        section = 'Other'
        desc = msg

    sections[section].append(desc)

output = []
for section, items in sections.items():
    if items:
        output.append(f'### {section}')
        for item in items:
            output.append(f'- {item}')
        output.append('')

print('\n'.join(output))
")"

# --- Build new changelog entry ---
COMPARE_LINK=""
if [ -n "$REPO_URL" ] && [ -n "$LAST_TAG" ]; then
  COMPARE_LINK=" ([compare](${REPO_URL}/compare/${LAST_TAG}...v${NEW_VERSION}))"
fi

NEW_ENTRY="## [${NEW_VERSION}] — ${DATE}${COMPARE_LINK}

${SECTION_CONTENT}"

# --- Prepend to CHANGELOG.md ---
if [ ! -f "$CHANGELOG_FILE" ]; then
  cat > "$CHANGELOG_FILE" << HEADER
# Changelog

All notable changes are documented here. Format: [Keep a Changelog](https://keepachangelog.com).

HEADER
fi

EXISTING="$(cat "$CHANGELOG_FILE")"

python3 << PYEOF
existing = open('${CHANGELOG_FILE}').read()
new_entry = """${NEW_ENTRY}"""

# Insert after header (first blank line after the header block)
lines = existing.split('\n')
insert_at = 0
for i, line in enumerate(lines):
    if i > 0 and line.startswith('## '):
        insert_at = i
        break
    elif i > 2 and line == '':
        insert_at = i + 1
        break

if insert_at == 0:
    insert_at = len(lines)

lines.insert(insert_at, new_entry)
lines.insert(insert_at, '')

with open('${CHANGELOG_FILE}', 'w') as f:
    f.write('\n'.join(lines))

print(f"CHANGELOG updated for v${NEW_VERSION}")
PYEOF

echo "Changelog updated: ${CHANGELOG_FILE} (v${NEW_VERSION})" >&2

if [ "$AUTO_COMMIT" = "1" ]; then
  git add "$CHANGELOG_FILE"
  git commit -m "docs(changelog): update for v${NEW_VERSION}" >&2
  echo "Changelog committed." >&2
fi

exit 0
