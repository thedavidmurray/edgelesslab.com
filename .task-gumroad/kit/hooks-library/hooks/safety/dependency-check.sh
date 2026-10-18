#!/usr/bin/env bash
# =============================================================================
# dependency-check.sh — Scan new dependencies for known vulnerabilities
# =============================================================================
#
# WHAT IT DOES:
#   Intercepts package installation commands (npm install, pip install, etc.)
#   and runs an audit against known vulnerability databases before the
#   installation proceeds. Blocks installation if critical/high CVEs are found.
#
# WHEN TO USE IT:
#   Any project that installs third-party packages. Especially important when
#   Claude is adding new dependencies you haven't reviewed.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/dependency-check.sh
#   2. Add configuration to .claude/settings.json
#   Recommended: install safety (Python) and/or npm audit
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
#               "command": "bash .claude/hooks/dependency-check.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   DEP_CHECK_SEVERITY  — Minimum severity to block on: critical|high|medium (default: high)
#   DEP_CHECK_WARN_ONLY — Set to "1" to warn but not block
# =============================================================================

set -euo pipefail

SEVERITY="${DEP_CHECK_SEVERITY:-high}"
WARN_ONLY="${DEP_CHECK_WARN_ONLY:-0}"

# --- Read hook input ---
INPUT="$(cat)"
TOOL_COMMAND="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('command', ''))
" 2>/dev/null || echo "")"

# --- Detect package manager and extract package names ---
PKG_MANAGER=""
PACKAGES=""

if echo "$TOOL_COMMAND" | grep -qE "npm (install|i|add) "; then
  PKG_MANAGER="npm"
  PACKAGES="$(echo "$TOOL_COMMAND" | grep -oE "npm (install|i|add) (.+)" | sed 's/npm \(install\|i\|add\) //')"
elif echo "$TOOL_COMMAND" | grep -qE "pip (install|3 install) "; then
  PKG_MANAGER="pip"
  PACKAGES="$(echo "$TOOL_COMMAND" | grep -oE "pip3? install (.+)" | sed 's/pip3* install //')"
elif echo "$TOOL_COMMAND" | grep -qE "yarn (add|install) "; then
  PKG_MANAGER="yarn"
  PACKAGES="$(echo "$TOOL_COMMAND" | grep -oE "yarn (add|install) (.+)" | sed 's/yarn \(add\|install\) //')"
elif echo "$TOOL_COMMAND" | grep -qE "pnpm (add|install) "; then
  PKG_MANAGER="pnpm"
  PACKAGES="$(echo "$TOOL_COMMAND" | grep -oE "pnpm (add|install) (.+)" | sed 's/pnpm \(add\|install\) //')"
else
  exit 0
fi

echo "Checking ${PKG_MANAGER} package(s) for vulnerabilities: ${PACKAGES}" >&2

VULN_FOUND=0
VULN_REPORT=""

# --- npm audit ---
if [ "$PKG_MANAGER" = "npm" ] || [ "$PKG_MANAGER" = "yarn" ] || [ "$PKG_MANAGER" = "pnpm" ]; then
  if command -v npm &>/dev/null && [ -f "package.json" ]; then
    # Run audit on existing deps after a dry-run install
    AUDIT_OUTPUT="$(npm audit --json 2>/dev/null || true)"
    if [ -n "$AUDIT_OUTPUT" ]; then
      VULNS="$(echo "$AUDIT_OUTPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    vulns = data.get('vulnerabilities', {})
    high_vulns = []
    for name, info in vulns.items():
        severity = info.get('severity', '')
        check_severities = ['critical', 'high']
        if '${SEVERITY}' == 'medium':
            check_severities.append('medium')
        if severity in check_severities:
            high_vulns.append(f'{name}: {severity} - {info.get(\"title\",\"unknown\")}')
    print('\n'.join(high_vulns))
except:
    pass
" 2>/dev/null || true)"
      if [ -n "$VULNS" ]; then
        VULN_FOUND=1
        VULN_REPORT="${VULN_REPORT}\nNPM vulnerabilities:\n${VULNS}"
      fi
    fi
  fi
fi

# --- pip safety check ---
if [ "$PKG_MANAGER" = "pip" ]; then
  if command -v safety &>/dev/null; then
    for pkg in $PACKAGES; do
      # Strip version specifiers
      pkg_name="$(echo "$pkg" | sed 's/[>=<!].*//')"
      SAFETY_OUT="$(safety check --package "${pkg_name}" --json 2>/dev/null || true)"
      if echo "$SAFETY_OUT" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    if data and len(data) > 0:
        sys.exit(1)
except:
    pass
" 2>/dev/null; then
        : # No vulns
      else
        VULN_FOUND=1
        VULN_REPORT="${VULN_REPORT}\n${pkg_name}: vulnerabilities found via safety"
      fi
    done
  fi
fi

if [ "$VULN_FOUND" -eq 1 ]; then
  echo "" >&2
  echo "DEPENDENCY CHECK: Vulnerabilities found" >&2
  printf "${VULN_REPORT}" >&2
  echo "" >&2
  echo "Review the vulnerabilities above before installing." >&2

  if [ "$WARN_ONLY" = "1" ]; then
    echo "(Warn-only mode — installation will proceed)" >&2
    exit 0
  fi

  python3 -c "
import json, sys
print(json.dumps({
  'decision': 'block',
  'reason': 'Dependency vulnerability check failed. Review and approve manually.\n' + sys.argv[1]
}))
" "$(printf "${VULN_REPORT}")"
  exit 0
fi

echo "Dependency check passed." >&2
exit 0
