#!/usr/bin/env bash
set -euo pipefail

# weekly-review.sh - Summarize vault activity from the last 7 days

SCRIPT_NAME="$(basename "$0")"

show_help() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS] [vault-path]

Summarize Obsidian vault activity from the last 7 days.

Arguments:
  vault-path            Path to Obsidian vault (default: current directory)

Options:
  -d, --days N          Look back N days instead of 7
  -o, --output FILE     Write summary to file instead of stdout
  -h, --help            Show this help message

Output includes:
  - Notes created in the period
  - Notes modified in the period
  - File counts by folder
  - Tag frequency from modified files

Examples:
  $SCRIPT_NAME ~/my-vault
  $SCRIPT_NAME --days 14 ~/my-vault
  $SCRIPT_NAME -o weekly-summary.md ~/my-vault
EOF
    exit 0
}

DAYS=7
OUTPUT=""
VAULT_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help) show_help ;;
        -d|--days) DAYS="$2"; shift 2 ;;
        -o|--output) OUTPUT="$2"; shift 2 ;;
        -*) echo "Unknown option: $1" >&2; exit 1 ;;
        *) VAULT_PATH="$1"; shift ;;
    esac
done

VAULT_PATH="${VAULT_PATH:-.}"

if [[ ! -d "$VAULT_PATH" ]]; then
    echo "Error: '$VAULT_PATH' is not a directory." >&2
    exit 1
fi

# Date threshold
if [[ "$(uname)" == "Darwin" ]]; then
    SINCE=$(date -v-${DAYS}d +%Y-%m-%d)
else
    SINCE=$(date -d "$DAYS days ago" +%Y-%m-%d)
fi

TODAY=$(date +%Y-%m-%d)

generate_report() {
    echo "# Weekly Vault Review"
    echo ""
    echo "**Period:** $SINCE to $TODAY ($DAYS days)"
    echo "**Vault:** $VAULT_PATH"
    echo ""

    # Notes created
    echo "## Notes Created"
    echo ""
    CREATED=$(find "$VAULT_PATH" -name "*.md" -not -path "*/.obsidian/*" -not -path "*/.trash/*" -newer <(echo) -newermt "$SINCE" -type f 2>/dev/null | sort)
    CREATED_COUNT=$(echo "$CREATED" | grep -c "." 2>/dev/null || echo "0")
    echo "**Total:** $CREATED_COUNT notes"
    echo ""

    if [[ "$CREATED_COUNT" -gt 0 ]]; then
        echo "$CREATED" | while IFS= read -r file; do
            if [[ -n "$file" ]]; then
                REL=$(echo "$file" | sed "s|^$VAULT_PATH/||")
                echo "- $REL"
            fi
        done
        echo ""
    fi

    # Notes modified
    echo "## Notes Modified"
    echo ""
    MODIFIED=$(find "$VAULT_PATH" -name "*.md" -not -path "*/.obsidian/*" -not -path "*/.trash/*" -newermt "$SINCE" -type f 2>/dev/null | sort)
    MODIFIED_COUNT=$(echo "$MODIFIED" | grep -c "." 2>/dev/null || echo "0")
    echo "**Total:** $MODIFIED_COUNT notes"
    echo ""

    # Folder breakdown
    echo "## Activity by Folder"
    echo ""
    echo "| Folder | Modified Notes |"
    echo "|--------|---------------|"

    if [[ "$MODIFIED_COUNT" -gt 0 ]]; then
        echo "$MODIFIED" | sed "s|^$VAULT_PATH/||" | cut -d'/' -f1 | sort | uniq -c | sort -rn | while read -r count folder; do
            echo "| $folder | $count |"
        done
    fi
    echo ""

    # Tag frequency from modified files
    echo "## Tag Frequency (Modified Notes)"
    echo ""
    if [[ "$MODIFIED_COUNT" -gt 0 ]]; then
        echo "$MODIFIED" | while IFS= read -r file; do
            if [[ -n "$file" ]]; then
                # Extract tags from frontmatter
                sed -n '/^---$/,/^---$/p' "$file" 2>/dev/null | grep -oE '\b[a-z][a-z0-9-]+\b' || true
                # Extract inline tags
                grep -oE '#[a-zA-Z][a-zA-Z0-9_/-]+' "$file" 2>/dev/null || true
            fi
        done | sort | uniq -c | sort -rn | head -20 | while read -r count tag; do
            echo "- **$tag**: $count"
        done
    else
        echo "No modified notes found."
    fi
    echo ""

    # Vault stats
    echo "## Vault Totals"
    echo ""
    TOTAL_NOTES=$(find "$VAULT_PATH" -name "*.md" -not -path "*/.obsidian/*" -not -path "*/.trash/*" -type f 2>/dev/null | wc -l | tr -d ' ')
    TOTAL_FOLDERS=$(find "$VAULT_PATH" -type d -not -path "*/.obsidian/*" -not -path "*/.trash/*" -not -name ".*" 2>/dev/null | wc -l | tr -d ' ')
    echo "- **Total notes:** $TOTAL_NOTES"
    echo "- **Total folders:** $TOTAL_FOLDERS"
}

if [[ -n "$OUTPUT" ]]; then
    generate_report > "$OUTPUT"
    echo "Summary written to $OUTPUT"
else
    generate_report
fi
