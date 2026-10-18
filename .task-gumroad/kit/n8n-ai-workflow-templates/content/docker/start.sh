#!/bin/bash
# Start n8n AI Workflow environment.
# Validates env, starts compose stack, polls /healthz until ready.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

red()   { printf "\033[31m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
yellow(){ printf "\033[33m%s\033[0m\n" "$*"; }

# --- 1. Prereqs ---
if ! command -v docker &>/dev/null; then
    red "Error: Docker is not installed. Install from https://docker.com"
    exit 1
fi

if ! docker compose version &>/dev/null; then
    red "Error: Docker Compose v2 is not available."
    exit 1
fi

# --- 2. .env presence ---
if [ ! -f .env ]; then
    yellow "No .env file found. Copying from .env.example..."
    cp .env.example .env
    red "Edit .env with real API keys and passwords, then re-run this script."
    exit 1
fi

# --- 3. Validate required env vars (fail fast) ---
# shellcheck disable=SC1091
set -a; source ./.env; set +a

missing=()
for var in GOOGLE_GEMINI_API_KEY POSTGRES_PASSWORD; do
    val="${!var}"
    if [ -z "$val" ] || [[ "$val" == *"your-"* ]] || [[ "$val" == *"change-me"* ]]; then
        missing+=("$var")
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    red "Missing or placeholder values in .env:"
    for v in "${missing[@]}"; do red "  - $v"; done
    red "Edit .env and set real values, then re-run."
    exit 1
fi

# --- 4. Data directories ---
mkdir -p n8n-data workflows credentials health-state

# --- 5. Start ---
green "Starting n8n stack (n8n + postgres)..."
docker compose up -d

# --- 6. Health poll ---
echo "Waiting for n8n to start..."
for i in {1..30}; do
    if curl -fsS http://localhost:5678/healthz 2>/dev/null | grep -q "ok"; then
        echo
        green "n8n is running at http://localhost:5678"
        echo
        echo "First-run setup:"
        echo "  1. Open http://localhost:5678"
        echo "  2. Create the owner account when prompted"
        echo "  3. Settings -> Import from File -> select a JSON in workflows/"
        echo "  4. Activate the workflow"
        exit 0
    fi
    printf "."
    sleep 2
done

echo
red "n8n did not start within 60 seconds. Check logs:"
red "  docker compose logs n8n"
exit 1
