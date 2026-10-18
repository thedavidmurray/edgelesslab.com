#!/usr/bin/env bash
set -euo pipefail

# backup-vault.sh - Create a timestamped backup of an Obsidian vault

SCRIPT_NAME="$(basename "$0")"

show_help() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS] <vault-path> [backup-dir]

Create a timestamped backup of an Obsidian vault.

Arguments:
  vault-path            Path to the Obsidian vault to back up
  backup-dir            Where to store backups (default: ~/obsidian-backups)

Options:
  -z, --zip             Create a zip archive instead of a directory copy
  -k, --keep N          Keep only the N most recent backups (default: keep all)
  -e, --exclude PATTERN Exclude files matching pattern (can be used multiple times)
  -n, --dry-run         Show what would be backed up without doing it
  -h, --help            Show this help message

Examples:
  $SCRIPT_NAME ~/my-vault
  $SCRIPT_NAME --zip ~/my-vault ~/Dropbox/backups
  $SCRIPT_NAME --keep 5 --zip ~/my-vault
  $SCRIPT_NAME --exclude "*.tmp" --exclude ".trash" ~/my-vault

Default excludes:
  .trash, .obsidian/cache, .obsidian/workspace.json
EOF
    exit 0
}

ZIP=false
KEEP=0
DRY_RUN=false
VAULT_PATH=""
BACKUP_DIR=""
EXCLUDES=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help) show_help ;;
        -z|--zip) ZIP=true; shift ;;
        -k|--keep) KEEP="$2"; shift 2 ;;
        -e|--exclude) EXCLUDES+=("$2"); shift 2 ;;
        -n|--dry-run) DRY_RUN=true; shift ;;
        -*)
            echo "Unknown option: $1" >&2; exit 1 ;;
        *)
            if [[ -z "$VAULT_PATH" ]]; then
                VAULT_PATH="$1"
            else
                BACKUP_DIR="$1"
            fi
            shift
            ;;
    esac
done

if [[ -z "$VAULT_PATH" ]]; then
    echo "Error: No vault path provided." >&2
    echo "Usage: $SCRIPT_NAME <vault-path> [backup-dir]" >&2
    exit 1
fi

if [[ ! -d "$VAULT_PATH" ]]; then
    echo "Error: '$VAULT_PATH' is not a directory." >&2
    exit 1
fi

BACKUP_DIR="${BACKUP_DIR:-$HOME/obsidian-backups}"
VAULT_NAME=$(basename "$VAULT_PATH")
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="${VAULT_NAME}-${TIMESTAMP}"

# Build rsync exclude list
RSYNC_EXCLUDES=(
    "--exclude=.trash"
    "--exclude=.obsidian/cache"
    "--exclude=.obsidian/workspace.json"
    "--exclude=.obsidian/workspace-mobile.json"
)

for pattern in "${EXCLUDES[@]}"; do
    RSYNC_EXCLUDES+=("--exclude=$pattern")
done

# Count files
FILE_COUNT=$(find "$VAULT_PATH" -type f -not -path "*/.trash/*" -not -path "*/.obsidian/cache/*" 2>/dev/null | wc -l | tr -d ' ')
VAULT_SIZE=$(du -sh "$VAULT_PATH" 2>/dev/null | cut -f1)

echo "Vault: $VAULT_PATH"
echo "Files: $FILE_COUNT"
echo "Size: $VAULT_SIZE"
echo "Backup: $BACKUP_DIR/$BACKUP_NAME"

if [[ "$DRY_RUN" == true ]]; then
    echo ""
    echo "[Dry run] Would create backup at: $BACKUP_DIR/$BACKUP_NAME"
    if [[ "$ZIP" == true ]]; then
        echo "[Dry run] Format: zip archive"
    else
        echo "[Dry run] Format: directory copy"
    fi
    exit 0
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

if [[ "$ZIP" == true ]]; then
    # Create temp directory, rsync there, then zip
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT

    rsync -a "${RSYNC_EXCLUDES[@]}" "$VAULT_PATH/" "$TEMP_DIR/$BACKUP_NAME/"
    (cd "$TEMP_DIR" && zip -r -q "$BACKUP_DIR/${BACKUP_NAME}.zip" "$BACKUP_NAME")

    BACKUP_SIZE=$(du -sh "$BACKUP_DIR/${BACKUP_NAME}.zip" 2>/dev/null | cut -f1)
    echo "Created: ${BACKUP_NAME}.zip ($BACKUP_SIZE)"
else
    rsync -a "${RSYNC_EXCLUDES[@]}" "$VAULT_PATH/" "$BACKUP_DIR/$BACKUP_NAME/"

    BACKUP_SIZE=$(du -sh "$BACKUP_DIR/$BACKUP_NAME" 2>/dev/null | cut -f1)
    echo "Created: $BACKUP_NAME/ ($BACKUP_SIZE)"
fi

# Prune old backups
if [[ "$KEEP" -gt 0 ]]; then
    echo ""
    echo "Pruning old backups (keeping $KEEP most recent)..."

    if [[ "$ZIP" == true ]]; then
        EXISTING=$(ls -1t "$BACKUP_DIR"/${VAULT_NAME}-*.zip 2>/dev/null || true)
    else
        EXISTING=$(ls -1dt "$BACKUP_DIR"/${VAULT_NAME}-*/ 2>/dev/null | sed 's|/$||' || true)
    fi

    COUNT=0
    echo "$EXISTING" | while IFS= read -r backup; do
        COUNT=$((COUNT + 1))
        if [[ "$COUNT" -gt "$KEEP" && -n "$backup" ]]; then
            echo "  Removing: $(basename "$backup")"
            rm -rf "$backup"
        fi
    done
fi

echo ""
echo "Backup complete."
