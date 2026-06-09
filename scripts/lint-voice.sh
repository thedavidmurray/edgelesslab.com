#!/bin/bash
#
# Wrapper for the voice/tone linter. The actual linter lives outside this
# repo on the original dev machine (../scripts/lint-voice.sh relative to the
# repo root). On machines/CI where it isn't present, skip instead of failing
# so `npm run lint` works on a fresh clone.
#
# Usage: ./scripts/lint-voice.sh <file> [...]

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
EXTERNAL_LINTER="$PROJECT_DIR/../scripts/lint-voice.sh"

if [ -x "$EXTERNAL_LINTER" ]; then
  exec "$EXTERNAL_LINTER" "$@"
else
  echo "[lint:voice] skipped: $EXTERNAL_LINTER not found (external tool)"
  exit 0
fi
