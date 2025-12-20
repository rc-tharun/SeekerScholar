#!/bin/bash
# Render startup script for SeekerScholar backend
# Starts the FastAPI server (artifacts should be downloaded during BUILD command)

set -e  # Exit on error

echo "=========================================="
echo "SeekerScholar Backend Startup"
echo "=========================================="

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Start the FastAPI server immediately (artifacts downloaded in BUILD command)
echo "Starting FastAPI server..."
echo "PORT: ${PORT:-8000}"
echo ""

# Use PORT environment variable (set by Render), default to 8000
# This must bind immediately to avoid "No open ports detected" error
exec uvicorn app.api:app --host 0.0.0.0 --port ${PORT:-8000}

