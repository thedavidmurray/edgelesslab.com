#!/usr/bin/env bash
# =============================================================================
# secret-scanner.sh — Block commits containing API keys or secrets
# =============================================================================
#
# WHAT IT DOES:
#   Intercepts git commit/push commands and scans staged files for patterns
#   that look like secrets: API keys, tokens, passwords, private keys.
#   Blocks the operation if any are found and prints the offending lines.
#
# WHEN TO USE IT:
#   Always. This is a last line of defence before secrets hit git history.
#   Once committed, secrets need rotating — this prevents that entirely.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/secret-scanner.sh
#   2. Add configuration to .claude/settings.json
#   Optional: Install trufflehog for deeper scanning: brew install trufflehog
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "PreToolUse": [
#         {
#           "matcher": "Bash",
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/secret-scanner.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   SECRET_SCAN_ALLOWLIST  — Colon-separated regex patterns to allow
#   SECRET_USE_TRUFFLEHOG  — Set to "1" to also run trufflehog (slower)
# =============================================================================

set -euo pipefail

# --- Read hook input ---
INPUT="$(cat)"
TOOL_INPUT="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('command', ''))
" 2>/dev/null || echo "")"

# Only run on git commit or push
if ! echo "$TOOL_INPUT" | grep -qE "git (commit|push)"; then
  exit 0
fi

# --- Secret patterns ---
# These are intentionally broad. Adjust for your stack.
PATTERNS=(
  # Generic high-entropy tokens
  'sk-[a-zA-Z0-9]{20,}'                        # OpenAI / Anthropic style
  'xox[baprs]-[0-9a-zA-Z]{10,}'               # Slack tokens
  'ghp_[a-zA-Z0-9]{36}'                        # GitHub personal access token
  'ghs_[a-zA-Z0-9]{36}'                        # GitHub app token
  'AKIA[0-9A-Z]{16}'                            # AWS access key
  'AIza[0-9A-Za-z\-_]{35}'                     # Google API key
  'ya29\.[0-9A-Za-z\-_]+'                      # Google OAuth token
  'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'         # JWT (broad)
  '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY' # Private keys
  '[Pp]assword\s*[:=]\s*["\x27][^"]{8,}'      # Hardcoded passwords
  'api[_-]?key\s*[:=]\s*["\x27][a-zA-Z0-9]{16,}' # Generic API keys
  'secret\s*[:=]\s*["\x27][a-zA-Z0-9]{16,}'   # Generic secrets
  'token\s*[:=]\s*["\x27][a-zA-Z0-9]{16,}'    # Generic tokens
)

# --- Get staged file content ---
STAGED_CONTENT="$(git diff --cached --unified=0 2>/dev/null || echo "")"

if [ -z "$STAGED_CONTENT" ]; then
  exit 0
fi

FOUND_SECRETS=()
ALLOWLIST="${SECRET_SCAN_ALLOWLIST:-}"

for pattern in "${PATTERNS[@]}"; do
  matches="$(echo "$STAGED_CONTENT" | grep -E "^\+" | grep -oE "$pattern" 2>/dev/null || true)"

  if [ -n "$matches" ]; then
    # Check allowlist
    if [ -n "$ALLOWLIST" ]; then
      allowed=0
      IFS=':' read -ra allowlist_patterns <<< "$ALLOWLIST"
      for allow_pattern in "${allowlist_patterns[@]}"; do
        if echo "$matches" | grep -qE "$allow_pattern"; then
          allowed=1
          break
        fi
      done
      [ "$allowed" -eq 1 ] && continue
    fi

    FOUND_SECRETS+=("Pattern: ${pattern}")
    FOUND_SECRETS+=("Match:   $(echo "$matches" | head -1 | cut -c1-60)...")
    FOUND_SECRETS+=("")
  fi
done

# --- Optional: trufflehog deep scan ---
if [ "${SECRET_USE_TRUFFLEHOG:-0}" = "1" ] && command -v trufflehog &>/dev/null; then
  TH_OUTPUT="$(trufflehog git file://. --only-verified --no-update 2>/dev/null || true)"
  if [ -n "$TH_OUTPUT" ]; then
    FOUND_SECRETS+=("TruffleHog found verified secrets:")
    FOUND_SECRETS+=("$TH_OUTPUT")
  fi
fi

if [ "${#FOUND_SECRETS[@]}" -gt 0 ]; then
  REPORT="$(printf '%s\n' "${FOUND_SECRETS[@]}")"
  echo "" >&2
  echo "SECRET SCAN FAILED — commit blocked" >&2
  echo "" >&2
  echo "$REPORT" >&2
  echo "" >&2
  echo "Remove secrets from staged files before committing." >&2
  echo "Use environment variables or a secrets manager instead." >&2
  echo "" >&2

  python3 -c "
import json, sys
report = sys.argv[1]
print(json.dumps({
  'decision': 'block',
  'reason': 'Potential secrets detected in staged changes. Remove before committing.\n\n' + report
}))
" "$REPORT"
  exit 0
fi

echo "Secret scan passed." >&2
exit 0
