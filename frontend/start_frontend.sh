#!/bin/bash
# DrPaper - Frontend startup script
# Starts the Next.js development server

cd "$(dirname "$0")"

echo "========================================="
echo "  DrPaper Frontend Setup"
echo "========================================="

# Check Node
if ! command -v node &> /dev/null; then
    echo "ERROR: node not found"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo "Starting DrPaper frontend on http://localhost:3000 ..."
npm run dev
