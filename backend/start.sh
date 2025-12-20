#!/bin/bash
# Render startup script for SeekerScholar backend
# Downloads artifacts if needed, then starts the FastAPI server

set -e  # Exit on error

echo "=========================================="
echo "SeekerScholar Backend Startup"
echo "=========================================="

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Download artifacts if needed
echo "Checking and downloading artifacts..."
python3 scripts/download_artifacts.py

# Start the FastAPI server
echo ""
echo "Starting FastAPI server..."
echo "PORT: ${PORT:-8000}"
echo ""

# Use PORT environment variable (set by Render), default to 8000
exec uvicorn app.api:app --host 0.0.0.0 --port ${PORT:-8000}

