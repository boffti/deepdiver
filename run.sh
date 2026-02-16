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

# Function to handle cleanup
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $FLASK_PID $REACT_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Flask backend
export PORT=${PORT:-8080}
echo "🚀 Starting Flask API on http://localhost:$PORT"
uv run run.py &
FLASK_PID=$!

# Wait a moment for Flask to start
sleep 2

# Start React dev server
echo "🚀 Starting React Dev Server on http://localhost:5173"
cd client && PORT=$PORT npm run dev &
REACT_PID=$!

echo ""
echo "=========================================="
echo "DeepDiver is running!"
echo "  - API:    http://localhost:$PORT"
echo "  - Frontend: http://localhost:5173"
echo "=========================================="
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait
