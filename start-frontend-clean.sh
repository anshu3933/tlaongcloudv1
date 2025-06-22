#!/bin/bash

echo "Starting TLA Frontend..."

# Set the frontend directory
FRONTEND_DIR="/Users/anshu/Documents/GitHub/v0-tla-front-endv01"

# Check if directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "Error: Frontend directory not found at $FRONTEND_DIR"
    exit 1
fi

# Change to frontend directory and start dev server
cd "$FRONTEND_DIR" || exit 1

echo "Installing dependencies..."
npm install

echo "Starting development server on port 3000..."
npm run dev -- --port 3000