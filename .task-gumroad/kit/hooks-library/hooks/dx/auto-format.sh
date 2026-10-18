#!/usr/bin/env bash
# =============================================================================
# auto-format.sh — Format code automatically after edits
# =============================================================================
#
# WHAT IT DOES:
#   After each file edit, runs the appropriate formatter for the file type.
#   Covers Python (ruff/black), JavaScript/TypeScript (prettier), Go (gofmt),
#   Rust (rustfmt), and shell scripts (shfmt). Formats in-place silently.
#
# WHEN TO USE IT:
#   Any project with a formatter. Ensures every file Claude touches is
#   consistently formatted without requiring a separate format step.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/auto-format.sh
#   2. Install formatters for your languages (see below)
#   3. Add configuration to .claude/settings.json
#
# RECOMMENDED FORMATTERS:
#   Python:     pip install ruff  (or pip install black)
#   JS/TS:      npm install -g prettier
#   Go:         comes with Go toolchain
#   Rust:       comes with rustup
#   Shell:      brew install shfmt
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "PostToolUse": [
#         {
#           "matcher": "Write|Edit|MultiEdit",
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/auto-format.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   FORMAT_PYTHON    — Formatter for .py files: ruff|black|none (default: ruff)
#   FORMAT_JS        — Formatter for .js/.ts: prettier|none (default: prettier)
#   FORMAT_DISABLED  — Set to "1" to disable all formatting
# =============================================================================

set -euo pipefail

[ "${FORMAT_DISABLED:-0}" = "1" ] && exit 0

PYTHON_FMT="${FORMAT_PYTHON:-ruff}"
JS_FMT="${FORMAT_JS:-prettier}"

# --- Read edited file ---
INPUT="$(cat)"
FILE_PATH="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ti = d.get('tool_input', {})
print(ti.get('path', ti.get('file_path', '')))
" 2>/dev/null || echo "")"

[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

EXTENSION="${FILE_PATH##*.}"

format_python() {
  case "$PYTHON_FMT" in
    ruff)
      if command -v ruff &>/dev/null; then
        ruff format --quiet "$FILE_PATH" 2>/dev/null && echo "Formatted (ruff): ${FILE_PATH}" >&2
      elif command -v black &>/dev/null; then
        black --quiet "$FILE_PATH" 2>/dev/null && echo "Formatted (black): ${FILE_PATH}" >&2
      fi
      ;;
    black)
      command -v black &>/dev/null && black --quiet "$FILE_PATH" 2>/dev/null
      ;;
    none) ;;
  esac
}

format_js() {
  case "$JS_FMT" in
    prettier)
      if command -v prettier &>/dev/null; then
        prettier --write --log-level silent "$FILE_PATH" 2>/dev/null && echo "Formatted (prettier): ${FILE_PATH}" >&2
      elif [ -f "node_modules/.bin/prettier" ]; then
        node_modules/.bin/prettier --write --log-level silent "$FILE_PATH" 2>/dev/null
      fi
      ;;
    none) ;;
  esac
}

format_go() {
  command -v gofmt &>/dev/null && gofmt -w "$FILE_PATH" 2>/dev/null && echo "Formatted (gofmt): ${FILE_PATH}" >&2 || true
}

format_rust() {
  command -v rustfmt &>/dev/null && rustfmt --edition 2021 "$FILE_PATH" 2>/dev/null && echo "Formatted (rustfmt): ${FILE_PATH}" >&2 || true
}

format_shell() {
  command -v shfmt &>/dev/null && shfmt -w -i 2 -ci "$FILE_PATH" 2>/dev/null && echo "Formatted (shfmt): ${FILE_PATH}" >&2 || true
}

format_json() {
  python3 -c "
import json, sys
with open('${FILE_PATH}') as f:
    data = json.load(f)
with open('${FILE_PATH}', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
" 2>/dev/null && echo "Formatted (json): ${FILE_PATH}" >&2 || true
}

format_yaml() {
  if command -v yq &>/dev/null; then
    yq eval '.' -i "$FILE_PATH" 2>/dev/null && echo "Formatted (yq): ${FILE_PATH}" >&2 || true
  fi
}

case "$EXTENSION" in
  py)            format_python ;;
  js|jsx|ts|tsx|mjs|cjs) format_js ;;
  go)            format_go ;;
  rs)            format_rust ;;
  sh|bash|zsh)  format_shell ;;
  json)          format_json ;;
  yml|yaml)      format_yaml ;;
  *)             exit 0 ;;
esac

exit 0
