#!/bin/bash
# run.sh — Autoresearch loop across all 6 CLAUDE.md templates.
#
# Usage:
#   bash run.sh          # 10 iterations (default)
#   bash run.sh 3        # 3 iterations
#   bash run.sh 1 true   # 1 iteration, dry-run (score only, no git operations)
#
# For each (iteration, template) pair:
#   1. Score the current template (baseline)
#   2. Print score — the human or outer agent decides the improvement
#   3. (Future: plug in a generate.py that proposes and applies the change)
#
# In the simplest form this script is a scored survey runner: it visits every
# template once per iteration and emits composite scores to results.tsv so you
# can see where to focus manual improvements.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_MD_DIR="${SCRIPT_DIR}/../claude-md"
PYTHON="${PYTHON:-python3.11}"

ITERATIONS="${1:-10}"
DRY_RUN="${2:-false}"

TEMPLATES=(solo-dev data-engineer frontend backend-api devops research)

echo "========================================================"
echo "  CLAUDE.md Template Autoresearch"
echo "  Iterations : ${ITERATIONS}"
echo "  Templates  : ${#TEMPLATES[@]}"
echo "  Total evals: $(( ITERATIONS * ${#TEMPLATES[@]} ))"
echo "========================================================"

for i in $(seq 1 "${ITERATIONS}"); do
    for t in "${TEMPLATES[@]}"; do
        TEMPLATE_PATH="${CLAUDE_MD_DIR}/${t}.md"
        EXPERIMENT_ID="iter${i}-${t}"

        echo ""
        echo "=== Iteration ${i} / ${ITERATIONS} — ${t} ==="

        if [[ ! -f "${TEMPLATE_PATH}" ]]; then
            echo "  [SKIP] Template not found: ${TEMPLATE_PATH}"
            continue
        fi

        if [[ "${DRY_RUN}" == "true" ]]; then
            echo "  [DRY RUN] Would score: ${TEMPLATE_PATH}"
            continue
        fi

        "${PYTHON}" "${SCRIPT_DIR}/prepare.py" "${TEMPLATE_PATH}" --id "${EXPERIMENT_ID}"
    done
done

echo ""
echo "========================================================"
echo "  Run complete. Showing best scores:"
echo "========================================================"
"${PYTHON}" "${SCRIPT_DIR}/prepare.py" --best
