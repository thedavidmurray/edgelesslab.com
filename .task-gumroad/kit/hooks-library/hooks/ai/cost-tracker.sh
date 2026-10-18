#!/usr/bin/env bash
# =============================================================================
# cost-tracker.sh — Track API token usage and costs per session
# =============================================================================
#
# WHAT IT DOES:
#   Reads token usage from Claude Code's session output and maintains a running
#   cost ledger in a local JSON file. Outputs a cost summary on session end.
#   Tracks: input tokens, output tokens, cache read/write tokens, total cost.
#
# WHEN TO USE IT:
#   When you want to understand your actual API spend per project or task.
#   Especially useful for long agentic sessions or batch processing work.
#
# HOW TO INSTALL:
#   1. Copy to .claude/hooks/cost-tracker.sh
#   2. Add configuration to .claude/settings.json
#
# SETTINGS.JSON SNIPPET:
#   {
#     "hooks": {
#       "Stop": [
#         {
#           "hooks": [
#             {
#               "type": "command",
#               "command": "bash .claude/hooks/cost-tracker.sh"
#             }
#           ]
#         }
#       ]
#     }
#   }
#
# ENVIRONMENT VARIABLES:
#   COST_LEDGER_FILE       — Path to cost ledger JSON (default: .claude/costs.json)
#   COST_MODEL             — Model ID for pricing (default: claude-sonnet-4-5)
#   COST_BUDGET_ALERT      — Alert if session cost exceeds this USD amount
# =============================================================================

set -euo pipefail

LEDGER_FILE="${COST_LEDGER_FILE:-.claude/costs.json}"
MODEL="${COST_MODEL:-claude-sonnet-4-5}"
BUDGET_ALERT="${COST_BUDGET_ALERT:-}"

# --- Token pricing (USD per 1M tokens) ---
# Update these when Anthropic changes pricing
declare -A INPUT_PRICE=(
  ["claude-opus-4-5"]="15.00"
  ["claude-sonnet-4-5"]="3.00"
  ["claude-haiku-4-5"]="0.80"
  ["claude-opus-4"]="15.00"
  ["claude-sonnet-4"]="3.00"
  ["claude-haiku-3-5"]="0.80"
)
declare -A OUTPUT_PRICE=(
  ["claude-opus-4-5"]="75.00"
  ["claude-sonnet-4-5"]="15.00"
  ["claude-haiku-4-5"]="4.00"
  ["claude-opus-4"]="75.00"
  ["claude-sonnet-4"]="15.00"
  ["claude-haiku-3-5"]="4.00"
)
declare -A CACHE_READ_PRICE=(
  ["claude-opus-4-5"]="1.50"
  ["claude-sonnet-4-5"]="0.30"
  ["claude-haiku-4-5"]="0.08"
)
declare -A CACHE_WRITE_PRICE=(
  ["claude-opus-4-5"]="18.75"
  ["claude-sonnet-4-5"]="3.75"
  ["claude-haiku-4-5"]="1.00"
)

# --- Read hook input (may contain usage data) ---
INPUT="$(cat)"

SESSION_USAGE="$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    usage = d.get('usage', d.get('token_usage', {}))
    print(json.dumps(usage))
except:
    print('{}')
" 2>/dev/null || echo "{}")"

INPUT_TOKENS="$(echo "$SESSION_USAGE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('input_tokens', 0))
" 2>/dev/null || echo "0")"

OUTPUT_TOKENS="$(echo "$SESSION_USAGE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('output_tokens', 0))
" 2>/dev/null || echo "0")"

CACHE_READ_TOKENS="$(echo "$SESSION_USAGE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('cache_read_input_tokens', 0))
" 2>/dev/null || echo "0")"

CACHE_WRITE_TOKENS="$(echo "$SESSION_USAGE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('cache_creation_input_tokens', 0))
" 2>/dev/null || echo "0")"

# --- Calculate cost ---
IN_PRICE="${INPUT_PRICE[$MODEL]:-3.00}"
OUT_PRICE="${OUTPUT_PRICE[$MODEL]:-15.00}"
CR_PRICE="${CACHE_READ_PRICE[$MODEL]:-0.30}"
CW_PRICE="${CACHE_WRITE_PRICE[$MODEL]:-3.75}"

SESSION_COST="$(python3 -c "
in_tok = ${INPUT_TOKENS}
out_tok = ${OUTPUT_TOKENS}
cr_tok = ${CACHE_READ_TOKENS}
cw_tok = ${CACHE_WRITE_TOKENS}

cost = (
    (in_tok / 1_000_000) * ${IN_PRICE} +
    (out_tok / 1_000_000) * ${OUT_PRICE} +
    (cr_tok / 1_000_000) * ${CR_PRICE} +
    (cw_tok / 1_000_000) * ${CW_PRICE}
)
print(f'{cost:.6f}')
")"

PROJECT="$(basename "$(pwd)")"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
DATE="$(date +"%Y-%m-%d")"

mkdir -p "$(dirname "$LEDGER_FILE")"

# --- Update ledger ---
python3 << PYEOF
import json, os

ledger_file = '${LEDGER_FILE}'
project = '${PROJECT}'
date = '${DATE}'
timestamp = '${TIMESTAMP}'
model = '${MODEL}'
session_cost = float('${SESSION_COST}')
in_tok = int('${INPUT_TOKENS}')
out_tok = int('${OUTPUT_TOKENS}')

entry = {
    'timestamp': timestamp,
    'project': project,
    'model': model,
    'input_tokens': in_tok,
    'output_tokens': out_tok,
    'cost_usd': session_cost
}

try:
    with open(ledger_file) as f:
        ledger = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    ledger = {'sessions': [], 'total_cost_usd': 0.0}

ledger['sessions'].append(entry)
ledger['total_cost_usd'] = round(sum(s['cost_usd'] for s in ledger['sessions']), 6)
ledger['last_updated'] = timestamp

with open(ledger_file, 'w') as f:
    json.dump(ledger, f, indent=2)

print(f"Session cost:  \${session_cost:.4f}")
print(f"Total to date: \${ledger['total_cost_usd']:.4f}")
print(f"Tokens:        {in_tok:,} in / {out_tok:,} out")
PYEOF

# --- Budget alert ---
if [ -n "$BUDGET_ALERT" ]; then
  TOTAL="$(python3 -c "
import json
with open('${LEDGER_FILE}') as f:
    d = json.load(f)
print(d.get('total_cost_usd', 0))
" 2>/dev/null || echo "0")"

  python3 -c "
total = float('${TOTAL}')
budget = float('${BUDGET_ALERT}')
if total > budget:
    print(f'COST ALERT: Total spend \${total:.4f} exceeds budget \${budget:.4f}')
" >&2
fi

exit 0
