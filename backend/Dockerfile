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

# Note: Data directory should be mounted or copied separately
# For deployment, ensure data/ folder is available at ../data relative to backend/

# Expose port (Render will set PORT env var)
EXPOSE 8000

# Run the application
# Use PORT environment variable if set, otherwise default to 8000
# Note: For Render, use the start command directly: uvicorn app.api:app --host 0.0.0.0 --port $PORT
CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port ${PORT:-8000}"]

