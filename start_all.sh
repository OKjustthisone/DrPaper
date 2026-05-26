#!/bin/bash
# DrPaper - Start All Services

echo "========================================="
echo "  DrPaper - Starting All Services"
echo "========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Start Backend
echo "Starting Backend (port 8000)..."
cd "$SCRIPT_DIR/backend"
./start_backend.sh "$GOOGLE_API_KEY" &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend (port 3000)..."
cd "$SCRIPT_DIR/frontend"
./start_frontend.sh &
FRONTEND_PID=$!

echo ""
echo "========================================="
echo "  DrPaper is starting up!"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "========================================="
echo ""

# Wait for exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
