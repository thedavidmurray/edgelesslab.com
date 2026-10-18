#!/usr/bin/env bash
# =============================================================================
# doc-generator.sh — Generate documentation from code changes
# =============================================================================
#
# WHAT IT DOES:
#   After editing source files, runs the appropriate documentation generator
#   for the language. Generates API docs from docstrings/JSDoc comments.
#   Supports Python (pdoc), JavaScript/TypeScript (typedoc), Go (godoc).
#   Output is written to docs/ directory.
#
# WHEN TO USE IT:
#   Libraries and packages where API documentation should stay in sync with
#   code. Ensures docs are never stale after Claude edits function signatures
#   or adds new public APIs.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/doc-generator.sh
#   2. Install doc generators:
#      Python: pip install pdoc
#      JS/TS:  npm install -g typedoc
#      Go:     comes with Go toolchain
#   3. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "PostToolUse": [
#         {
#           "matcher": "Write|Edit",
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/doc-generator.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   DOC_OUTPUT_DIR       — Output directory (default: docs/api)
#   DOC_PYTHON_TOOL      — Tool for Python: pdoc|sphinx (default: pdoc)
#   DOC_DISABLED         — Set to "1" to disable
# =============================================================================

set -euo pipefail

[ "${DOC_DISABLED:-0}" = "1" ] && exit 0

OUTPUT_DIR="${DOC_OUTPUT_DIR:-docs/api}"
PYTHON_TOOL="${DOC_PYTHON_TOOL:-pdoc}"

# --- Read edited file ---
INPUT="$(cat)"
EDITED_FILE="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ti = d.get('tool_input', {})
print(ti.get('path', ti.get('file_path', '')))
" 2>/dev/null || echo "")"

[ -z "$EDITED_FILE" ] && exit 0
[ ! -f "$EDITED_FILE" ] && exit 0

EXTENSION="${EDITED_FILE##*.}"

# Skip test files and private modules
if echo "$EDITED_FILE" | grep -qE "(test_|_test\.|__pycache__|\.pyc)"; then
  exit 0
fi

mkdir -p "$OUTPUT_DIR"

# --- Python documentation ---
generate_python_docs() {
  local file="$1"
  local module
  module="$(echo "$file" | sed 's/\//./g' | sed 's/\.py$//')"

  case "$PYTHON_TOOL" in
    pdoc)
      if command -v pdoc &>/dev/null; then
        pdoc --output-dir "$OUTPUT_DIR" "$file" 2>/dev/null && \
          echo "Docs generated (pdoc): ${OUTPUT_DIR}/${module}.html" >&2
      fi
      ;;
    sphinx)
      if command -v sphinx-apidoc &>/dev/null; then
        PACKAGE_DIR="$(dirname "$file")"
        sphinx-apidoc -o "$OUTPUT_DIR" "$PACKAGE_DIR" 2>/dev/null && \
          echo "Sphinx apidoc updated: ${OUTPUT_DIR}" >&2
      fi
      ;;
  esac
}

# --- JavaScript/TypeScript documentation ---
generate_js_docs() {
  if command -v typedoc &>/dev/null || [ -f "node_modules/.bin/typedoc" ]; then
    TYPEDOC="$(command -v typedoc 2>/dev/null || echo "node_modules/.bin/typedoc")"

    if [ -f "tsconfig.json" ]; then
      "$TYPEDOC" --out "$OUTPUT_DIR" --entryPoints "$(dirname "$1")" \
        --logLevel Error 2>/dev/null && \
        echo "Docs generated (typedoc): ${OUTPUT_DIR}" >&2 || true
    fi
  elif command -v jsdoc &>/dev/null; then
    jsdoc "$1" -d "$OUTPUT_DIR" 2>/dev/null && \
      echo "Docs generated (jsdoc): ${OUTPUT_DIR}" >&2 || true
  fi
}

# --- Go documentation ---
generate_go_docs() {
  if command -v go &>/dev/null; then
    PKG_DIR="$(dirname "$1")"
    go doc -all "./${PKG_DIR}" > "${OUTPUT_DIR}/$(basename "$PKG_DIR").txt" 2>/dev/null && \
      echo "Docs generated (go doc): ${OUTPUT_DIR}/$(basename "$PKG_DIR").txt" >&2 || true
  fi
}

case "$EXTENSION" in
  py)          generate_python_docs "$EDITED_FILE" ;;
  ts|tsx)      generate_js_docs "$EDITED_FILE" ;;
  js|jsx)      generate_js_docs "$EDITED_FILE" ;;
  go)          generate_go_docs "$EDITED_FILE" ;;
  *)           exit 0 ;;
esac

exit 0
