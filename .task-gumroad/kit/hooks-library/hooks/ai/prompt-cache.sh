#!/usr/bin/env bash
# =============================================================================
# prompt-cache.sh — Cache frequently used prompts and context snippets
# =============================================================================
#
# WHAT IT DOES:
#   Maintains a local cache of prompts and context snippets that get injected
#   into session context at startup. Cache entries are tagged, searchable,
#   and expire on a configurable TTL. Reduces token usage by surfacing
#   relevant prompts without repeating them in conversation.
#
# WHEN TO USE IT:
#   Projects where you find yourself repeatedly typing the same context:
#   tech stack details, coding conventions, domain vocabulary, or system
#   architecture descriptions.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/prompt-cache.sh
#   2. Populate cache with: bash .claude/hooks/prompt-cache.sh add "tag" "content"
#   3. Add configuration to .claude/settings.json
#
# USAGE:
#   Add to cache:    bash prompt-cache.sh add <tag> <content>
#   List cache:      bash prompt-cache.sh list
#   Remove entry:    bash prompt-cache.sh remove <tag>
#   Clear expired:   bash prompt-cache.sh prune
#   Inject context:  bash prompt-cache.sh inject (used by hook)
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "SessionStart": [
#         {
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/prompt-cache.sh inject"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   PROMPT_CACHE_FILE   — Cache storage (default: .claude/prompt-cache.json)
#   PROMPT_CACHE_TTL    — TTL in days (default: 30, 0 = never expire)
#   PROMPT_CACHE_TAGS   — Colon-separated tags to inject (default: all)
# =============================================================================

set -euo pipefail

CACHE_FILE="${PROMPT_CACHE_FILE:-.claude/prompt-cache.json}"
TTL_DAYS="${PROMPT_CACHE_TTL:-30}"
FILTER_TAGS="${PROMPT_CACHE_TAGS:-}"
ACTION="${1:-inject}"

mkdir -p "$(dirname "$CACHE_FILE")"

# Initialize cache if missing
if [ ! -f "$CACHE_FILE" ]; then
  echo '{"entries": []}' > "$CACHE_FILE"
fi

case "$ACTION" in
  add)
    TAG="${2:?Usage: prompt-cache.sh add <tag> <content>}"
    CONTENT="${3:?Usage: prompt-cache.sh add <tag> <content>}"
    ADDED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    python3 << PYEOF
import json, sys
with open('${CACHE_FILE}') as f:
    cache = json.load(f)

# Remove existing entry with same tag
cache['entries'] = [e for e in cache['entries'] if e.get('tag') != '${TAG}']

cache['entries'].append({
    'tag': '${TAG}',
    'content': '${CONTENT}',
    'added_at': '${ADDED_AT}',
    'ttl_days': ${TTL_DAYS}
})

with open('${CACHE_FILE}', 'w') as f:
    json.dump(cache, f, indent=2)

print(f"Cached prompt with tag: ${TAG}")
PYEOF
    ;;

  list)
    python3 << PYEOF
import json
from datetime import datetime, timezone

with open('${CACHE_FILE}') as f:
    cache = json.load(f)

entries = cache.get('entries', [])
if not entries:
    print("Cache is empty.")
else:
    print(f"{'Tag':<20} {'Added':<12} {'Preview'}")
    print("-" * 70)
    for e in entries:
        tag = e['tag'][:18]
        added = e.get('added_at', '')[:10]
        preview = e['content'][:40].replace('\n', ' ')
        print(f"{tag:<20} {added:<12} {preview}...")
PYEOF
    ;;

  remove)
    TAG="${2:?Usage: prompt-cache.sh remove <tag>}"
    python3 << PYEOF
import json
with open('${CACHE_FILE}') as f:
    cache = json.load(f)
before = len(cache['entries'])
cache['entries'] = [e for e in cache['entries'] if e.get('tag') != '${TAG}']
after = len(cache['entries'])
with open('${CACHE_FILE}', 'w') as f:
    json.dump(cache, f, indent=2)
print(f"Removed {before - after} entry/entries with tag '${TAG}'")
PYEOF
    ;;

  prune)
    python3 << PYEOF
import json
from datetime import datetime, timezone, timedelta

with open('${CACHE_FILE}') as f:
    cache = json.load(f)

now = datetime.now(timezone.utc)
kept, pruned = [], 0
for e in cache['entries']:
    ttl = e.get('ttl_days', ${TTL_DAYS})
    if ttl == 0:
        kept.append(e)
        continue
    added = datetime.fromisoformat(e.get('added_at', '2000-01-01T00:00:00Z').replace('Z', '+00:00'))
    if now - added < timedelta(days=ttl):
        kept.append(e)
    else:
        pruned += 1

cache['entries'] = kept
with open('${CACHE_FILE}', 'w') as f:
    json.dump(cache, f, indent=2)
print(f"Pruned {pruned} expired entries. {len(kept)} remaining.")
PYEOF
    ;;

  inject)
    python3 << PYEOF
import json
from datetime import datetime, timezone, timedelta

with open('${CACHE_FILE}') as f:
    cache = json.load(f)

now = datetime.now(timezone.utc)
filter_tags = [t for t in '${FILTER_TAGS}'.split(':') if t]
active = []

for e in cache['entries']:
    ttl = e.get('ttl_days', ${TTL_DAYS})
    if ttl > 0:
        added = datetime.fromisoformat(e.get('added_at', '2000-01-01T00:00:00Z').replace('Z', '+00:00'))
        if now - added >= timedelta(days=ttl):
            continue

    if filter_tags and e.get('tag') not in filter_tags:
        continue

    active.append(e)

if active:
    print("=== Cached Context ===")
    for e in active:
        print(f"\n[{e['tag']}]")
        print(e['content'])
    print("\n=== End Cached Context ===")
    import sys
    print(f"Injected {len(active)} cached prompt(s).", file=sys.stderr)
PYEOF
    ;;

  *)
    echo "Usage: prompt-cache.sh [add|list|remove|prune|inject]" >&2
    exit 1
    ;;
esac

exit 0
