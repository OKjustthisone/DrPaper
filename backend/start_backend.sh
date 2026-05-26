#!/bin/bash
# DrPaper - Backend startup script
# Starts the Python FastAPI backend server

cd "$(dirname "$0")"

echo "========================================="
echo "  DrPaper Backend Setup"
echo "========================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt

# Set Google API Key if provided as argument or from env
if [ -n "$1" ]; then
    export GOOGLE_API_KEY="$1"
fi

if [ -z "$GOOGLE_API_KEY" ]; then
    echo ""
    echo "WARNING: GOOGLE_API_KEY is not set."
    echo "Set it via: GOOGLE_API_KEY=your_key ./start_backend.sh"
    echo "Or configure models via the Settings page in the app."
    echo ""
fi

echo "Starting DrPaper backend on http://localhost:8000 ..."
python3 run.py
