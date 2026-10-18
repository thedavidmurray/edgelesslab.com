#!/usr/bin/env bash
set -euo pipefail

# daily-capture.sh - Append text to today's daily note in Obsidian

SCRIPT_NAME="$(basename "$0")"

show_help() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS] <text>

Append a line to today's daily note in Obsidian.

Arguments:
  text                  Text to append (wrap in quotes if it contains spaces)

Options:
  -t, --task            Format as a task: "- [ ] text"
  -b, --bullet          Format as a bullet: "- text" (default)
  -q, --quote           Format as a quote: "> text"
  -s, --section SECTION Append under a specific section heading
  -h, --help            Show this help message

Examples:
  $SCRIPT_NAME "Fixed the login bug"
  $SCRIPT_NAME -t "Review PR #42"
  $SCRIPT_NAME -q "Premature optimization is the root of all evil"
  $SCRIPT_NAME -s "Captures" "Interesting article on RLHF"

Requires:
  - Obsidian running with CLI enabled
  - obsidian binary in PATH (or symlinked to ~/.local/bin/obsidian)
EOF
    exit 0
}

# Check for obsidian CLI
check_obsidian() {
    if ! command -v obsidian &>/dev/null; then
        echo "Error: obsidian CLI not found in PATH." >&2
        echo "Enable it in Obsidian: Settings > General > Advanced > CLI" >&2
        exit 1
    fi
}

# Defaults
FORMAT="bullet"
SECTION=""

# Parse options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help) show_help ;;
        -t|--task) FORMAT="task"; shift ;;
        -b|--bullet) FORMAT="bullet"; shift ;;
        -q|--quote) FORMAT="quote"; shift ;;
        -s|--section) SECTION="$2"; shift 2 ;;
        -*) echo "Unknown option: $1" >&2; exit 1 ;;
        *) break ;;
    esac
done

# Require text argument
if [[ $# -eq 0 ]]; then
    echo "Error: No text provided." >&2
    echo "Usage: $SCRIPT_NAME <text>" >&2
    echo "Run $SCRIPT_NAME --help for details." >&2
    exit 1
fi

TEXT="$*"

# Format the line
case "$FORMAT" in
    task)   LINE="- [ ] $TEXT" ;;
    quote)  LINE="> $TEXT" ;;
    bullet) LINE="- $TEXT" ;;
esac

# Add timestamp
TIMESTAMP=$(date +"%H:%M")
LINE="$LINE ($TIMESTAMP)"

check_obsidian

# Append to daily note
if [[ -n "$SECTION" ]]; then
    # Append under a section by adding the section header prefix
    CONTENT=$'\n'"## $SECTION"$'\n'"$LINE"
    obsidian daily:append content="$LINE" 2>/dev/null
else
    obsidian daily:append content="$LINE" 2>/dev/null
fi

echo "Appended to daily note: $LINE"
