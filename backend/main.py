"""
Main entry point for running the FastAPI server.
"""
import os
import uvicorn

if __name__ == "__main__":
    # Use PORT environment variable if set (for Render), otherwise default to 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.api:app", host="0.0.0.0", port=port, reload=True)

