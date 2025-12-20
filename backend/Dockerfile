FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Copy scripts directory (needed for artifact download)
COPY scripts/ ./scripts/

# Create data directory
RUN mkdir -p /app/data

# Set default DATA_DIR for Docker environment
ENV DATA_DIR=/app/data

# Expose port (Render will set PORT env var)
EXPOSE 8000

# Download artifacts first, then start uvicorn
# This ensures artifacts are present before the server binds to $PORT
CMD ["sh", "-c", "python scripts/download_artifacts.py && uvicorn app.api:app --host 0.0.0.0 --port ${PORT:-8000}"]

