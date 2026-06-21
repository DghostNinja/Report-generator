#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WEB_DIR="$SCRIPT_DIR/web"

# Kill any existing instance of this app on port 5000
if lsof -ti:5000 &>/dev/null; then
    kill $(lsof -ti:5000) 2>/dev/null
    sleep 1
fi

cd "$WEB_DIR"

# Clean Python cache files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "Starting SAST Report Generator..."
echo "Access at: http://localhost:5000"
echo ""

# Start Flask
FLASK_APP=app.py python3 -m flask run --host 0.0.0.0 --port 5000 --reload