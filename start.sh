#!/bin/bash

# Stop any existing Flask processes
pkill -f "flask run" 2>/dev/null
pkill -f "app.py" 2>/dev/null
sleep 1

# Navigate to web directory
cd "$(dirname "$0")/web" 2>/dev/null || cd /home/ipsalmy/Test/Report-generator/web

# Clean Python cache files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null

# Remove old PDF files (optional cleanup)
rm -f pdfs/*.pdf 2>/dev/null

echo "Starting SAST Report Generator..."
echo "Access at: http://localhost:5000"
echo ""

# Start Flask with no caching
FLASK_APP=app.py python3 -m flask run --host 0.0.0.0 --port 5000 --reload