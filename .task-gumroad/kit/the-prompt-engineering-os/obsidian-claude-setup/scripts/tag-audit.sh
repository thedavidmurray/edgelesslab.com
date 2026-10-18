#!/usr/bin/env bash
set -euo pipefail

# tag-audit.sh - Find orphan and unused tags in an Obsidian vault

SCRIPT_NAME="$(basename "$0")"

show_help() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS] [vault-path]

Audit tags in an Obsidian vault. Finds tags used only once (orphans),
shows tag frequency, and identifies potential duplicates.

Arguments:
  vault-path            Path to Obsidian vault (default: current directory)

Options:
  -m, --min N           Minimum usage count to display (default: 1)
  -o, --orphans         Show only orphan tags (used once)
  -f, --frequency       Show tag frequency table (default behavior)
  -d, --duplicates      Show potential duplicate tags (similar names)
  -h, --help            Show this help message

Examples:
  $SCRIPT_NAME ~/my-vault
  $SCRIPT_NAME --orphans ~/my-vault
  $SCRIPT_NAME --min 5 ~/my-vault
EOF
    exit 0
}

MIN_COUNT=1
MODE="frequency"
VAULT_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help) show_help ;;
        -m|--min) MIN_COUNT="$2"; shift 2 ;;
        -o|--orphans) MODE="orphans"; shift ;;
        -f|--frequency) MODE="frequency"; shift ;;
        -d|--duplicates) MODE="duplicates"; shift ;;
        -*) echo "Unknown option: $1" >&2; exit 1 ;;
        *) VAULT_PATH="$1"; shift ;;
    esac
done

VAULT_PATH="${VAULT_PATH:-.}"

if [[ ! -d "$VAULT_PATH" ]]; then
    echo "Error: '$VAULT_PATH' is not a directory." >&2
    exit 1
fi

# Collect all tags from frontmatter and inline
collect_tags() {
    find "$VAULT_PATH" -name "*.md" -not -path "*/.obsidian/*" -not -path "*/.trash/*" -type f -print0 2>/dev/null | while IFS= read -r -d '' file; do
        # Frontmatter tags (from tags: [tag1, tag2] or tags: \n - tag1)
        sed -n '/^---$/,/^---$/p' "$file" 2>/dev/null | grep -oE 'tags:.*' | grep -oE '\b[a-zA-Z][a-zA-Z0-9_-]+\b' | grep -v "^tags$" || true
        # Inline tags (#tag-name)
        grep -oE '#[a-zA-Z][a-zA-Z0-9_/-]+' "$file" 2>/dev/null | sed 's/^#//' || true
    done
}

TAGS_FILE=$(mktemp)
trap "rm -f $TAGS_FILE" EXIT

collect_tags | sort > "$TAGS_FILE"

case "$MODE" in
    frequency)
        echo "# Tag Frequency"
        echo ""
        echo "| Tag | Count |"
        echo "|-----|-------|"
        sort "$TAGS_FILE" | uniq -c | sort -rn | while read -r count tag; do
            if [[ "$count" -ge "$MIN_COUNT" ]]; then
                echo "| $tag | $count |"
            fi
        done
        TOTAL=$(wc -l < "$TAGS_FILE" | tr -d ' ')
        UNIQUE=$(sort "$TAGS_FILE" | uniq | wc -l | tr -d ' ')
        echo ""
        echo "**Total tag uses:** $TOTAL"
        echo "**Unique tags:** $UNIQUE"
        ;;

    orphans)
        echo "# Orphan Tags (Used Once)"
        echo ""
        ORPHANS=$(sort "$TAGS_FILE" | uniq -c | sort -rn | awk '$1 == 1 {print $2}')
        ORPHAN_COUNT=$(echo "$ORPHANS" | grep -c "." 2>/dev/null || echo "0")
        echo "**Found:** $ORPHAN_COUNT orphan tags"
        echo ""
        if [[ "$ORPHAN_COUNT" -gt 0 ]]; then
            echo "$ORPHANS" | while read -r tag; do
                if [[ -n "$tag" ]]; then
                    # Find which file uses this tag
                    FILE=$(grep -rl "#$tag\b\|$tag" "$VAULT_PATH" --include="*.md" 2>/dev/null | head -1 | sed "s|^$VAULT_PATH/||" || echo "unknown")
                    echo "- \`$tag\` in $FILE"
                fi
            done
        fi
        ;;

    duplicates)
        echo "# Potential Duplicate Tags"
        echo ""
        echo "Tags that look similar (differ by plural, hyphen, or case):"
        echo ""
        UNIQUE_TAGS=$(sort "$TAGS_FILE" | uniq)

        # Check for plural variants
        echo "$UNIQUE_TAGS" | while read -r tag; do
            if [[ -n "$tag" ]]; then
                # Check if tag + "s" exists
                PLURAL="${tag}s"
                if echo "$UNIQUE_TAGS" | grep -qx "$PLURAL" 2>/dev/null; then
                    echo "- \`$tag\` / \`$PLURAL\` (singular vs plural)"
                fi
                # Check for hyphen vs no-hyphen
                NO_HYPHEN=$(echo "$tag" | tr -d '-')
                if [[ "$NO_HYPHEN" != "$tag" ]]; then
                    if echo "$UNIQUE_TAGS" | grep -qx "$NO_HYPHEN" 2>/dev/null; then
                        echo "- \`$tag\` / \`$NO_HYPHEN\` (with/without hyphen)"
                    fi
                fi
            fi
        done
        ;;
esac
