#!/bin/bash
cd "$(dirname "$0")"

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check required environment variables
REQUIRED_VARS=("SUPABASE_URL" "SUPABASE_KEY" "ALPACA_API_KEY" "ALPACA_SECRET_KEY" "OPENROUTER_API_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "ERROR: Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Create data directory if it doesn't exist (for backwards compatibility)
mkdir -p app/data/history app/data/routines

# Run the app using uv
PORT=${PORT:-8080}
echo "🚀 Starting DeepDiver Trading System on http://localhost:$PORT"
uv run run.py

