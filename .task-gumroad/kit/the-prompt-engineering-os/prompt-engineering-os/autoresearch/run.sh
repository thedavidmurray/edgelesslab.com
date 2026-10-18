#!/bin/bash
# Run N iterations of the autoresearch loop
# Usage: bash run.sh [N]   (default: 20)

ITERATIONS=${1:-20}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

for i in $(seq 1 "$ITERATIONS"); do
  echo "=== Iteration $i/$ITERATIONS ==="
  python3.11 prepare.py
done
