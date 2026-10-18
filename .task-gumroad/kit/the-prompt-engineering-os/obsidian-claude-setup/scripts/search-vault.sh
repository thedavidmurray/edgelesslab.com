#!/usr/bin/env bash
set -euo pipefail

# search-vault.sh - Full-text search with formatted output for Obsidian vaults

SCRIPT_NAME="$(basename "$0")"

show_help() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS] <query> [vault-path]

Search an Obsidian vault with formatted output.

Arguments:
  query                 Search term or regex pattern
  vault-path            Path to Obsidian vault (default: current directory)

Options:
  -t, --type TYPE       Filter by frontmatter type (e.g., project, research, book)
  -s, --status STATUS   Filter by frontmatter status (e.g., active, draft)
  -f, --folder FOLDER   Search only in a specific folder (e.g., 03-Knowledge)
  -c, --context N       Show N lines of context around matches (default: 1)
  -n, --names-only      Show only matching file names, not content
  -i, --ignore-case     Case-insensitive search (default)
  -I, --case-sensitive   Case-sensitive search
  -h, --help            Show this help message

Examples:
  $SCRIPT_NAME "kubernetes" ~/my-vault
  $SCRIPT_NAME --type runbook "scaling" ~/my-vault
  $SCRIPT_NAME --folder 01-Projects --status active "auth" ~/my-vault
  $SCRIPT_NAME --names-only "RLHF" ~/my-vault
EOF
    exit 0
}

QUERY=""
VAULT_PATH=""
TYPE_FILTER=""
STATUS_FILTER=""
FOLDER_FILTER=""
CONTEXT=1
NAMES_ONLY=false
CASE_FLAG="-i"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help) show_help ;;
        -t|--type) TYPE_FILTER="$2"; shift 2 ;;
        -s|--status) STATUS_FILTER="$2"; shift 2 ;;
        -f|--folder) FOLDER_FILTER="$2"; shift 2 ;;
        -c|--context) CONTEXT="$2"; shift 2 ;;
        -n|--names-only) NAMES_ONLY=true; shift ;;
        -i|--ignore-case) CASE_FLAG="-i"; shift ;;
        -I|--case-sensitive) CASE_FLAG=""; shift ;;
        -*) echo "Unknown option: $1" >&2; exit 1 ;;
        *)
            if [[ -z "$QUERY" ]]; then
                QUERY="$1"
            else
                VAULT_PATH="$1"
            fi
            shift
            ;;
    esac
done

if [[ -z "$QUERY" ]]; then
    echo "Error: No search query provided." >&2
    echo "Usage: $SCRIPT_NAME <query> [vault-path]" >&2
    exit 1
fi

VAULT_PATH="${VAULT_PATH:-.}"

if [[ ! -d "$VAULT_PATH" ]]; then
    echo "Error: '$VAULT_PATH' is not a directory." >&2
    exit 1
fi

# Build search path
SEARCH_PATH="$VAULT_PATH"
if [[ -n "$FOLDER_FILTER" ]]; then
    SEARCH_PATH="$VAULT_PATH/$FOLDER_FILTER"
    if [[ ! -d "$SEARCH_PATH" ]]; then
        echo "Error: Folder '$FOLDER_FILTER' not found in vault." >&2
        exit 1
    fi
fi

# Find matching files
MATCH_COUNT=0

find "$SEARCH_PATH" -name "*.md" -not -path "*/.obsidian/*" -not -path "*/.trash/*" -type f -print0 2>/dev/null | while IFS= read -r -d '' file; do
    # Check content match
    if ! grep -q $CASE_FLAG "$QUERY" "$file" 2>/dev/null; then
        continue
    fi

    # Check type filter
    if [[ -n "$TYPE_FILTER" ]]; then
        FILE_TYPE=$(sed -n '/^---$/,/^---$/p' "$file" 2>/dev/null | grep "^type:" | head -1 | sed 's/type: *//' | tr -d '"' | tr -d ' ')
        if [[ "$FILE_TYPE" != "$TYPE_FILTER" ]]; then
            continue
        fi
    fi

    # Check status filter
    if [[ -n "$STATUS_FILTER" ]]; then
        FILE_STATUS=$(sed -n '/^---$/,/^---$/p' "$file" 2>/dev/null | grep "^status:" | head -1 | sed 's/status: *//' | tr -d '"' | tr -d ' ')
        if [[ "$FILE_STATUS" != "$STATUS_FILTER" ]]; then
            continue
        fi
    fi

    REL=$(echo "$file" | sed "s|^$VAULT_PATH/||")

    if [[ "$NAMES_ONLY" == true ]]; then
        echo "$REL"
    else
        echo "---"
        echo "## $REL"
        grep -n $CASE_FLAG -C "$CONTEXT" "$QUERY" "$file" 2>/dev/null | head -20
        echo ""
    fi

    MATCH_COUNT=$((MATCH_COUNT + 1))
done

if [[ "$NAMES_ONLY" == false ]]; then
    echo "---"
    echo "Search complete for: \"$QUERY\""
fi
