#!/bin/bash

# Start Frontend Script
echo "Starting TLA Frontend..."

# Navigate to frontend directory
cd /Users/anshu/Documents/GitHub/v0-tla-front-endv01

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the development server
echo "Starting development server..."
npm run dev