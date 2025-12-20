# ISR Paper Search Engine

A production-ready academic paper search engine using BM25, BERT embeddings, and PageRank over the ogbn-arxiv citation graph.

## Features

- **BM25 Search**: Fast keyword-based search
- **BERT Search**: Semantic search using sentence transformers
- **PageRank Search**: Authority-based search using citation graph
- **Hybrid Search**: Combined approach for best results
- **FastAPI Backend**: High-performance REST API
- **React Frontend**: Modern, responsive web interface

## Project Structure

```
seekerscholar/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api.py         # FastAPI application and endpoints
│   │   ├── engine.py      # SearchEngine class (2-stage retrieval)
│   │   ├── config.py      # Configuration management
│   │   ├── data_loader.py # Data file loading and downloading
│   │   └── pdf_utils.py   # PDF/document text extraction
│   ├── main.py            # Entry point
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # Docker configuration
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # Main React component
│   │   ├── main.tsx       # React entry point
│   │   └── *.css          # Styles
│   ├── package.json       # Node dependencies
│   └── vite.config.js     # Vite configuration
├── data/                  # Precomputed artifacts
│   ├── df.pkl            # Papers DataFrame
│   ├── bm25.pkl          # BM25 index
│   ├── embeddings.pt     # BERT embeddings
│   └── graph.pkl         # Citation graph
└── README.md
```

## Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Precomputed data artifacts in `data/` directory

**Note:** Artifacts are not stored in GitHub; they are downloaded during build. The data files (`df.pkl`, `bm25.pkl`, `embeddings.pt`, `graph.pkl`) are automatically downloaded from GitHub Releases (tag: `v1.0.0-models`) during deployment or first run. See [Deployment](#deployment) section for details.

## Local Development

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the FastAPI server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API Documentation (Swagger UI): `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Environment Variables

**Frontend:**
Create a `.env` file in the `frontend/` directory:
```
VITE_API_BASE_URL=http://localhost:8000
```
Or use `VITE_API_URL` for backward compatibility.

**Backend:**
Optional environment variables (create `.env` in `backend/` or set in deployment platform):
- `DATA_DIR`: Path to data directory (default: `../data`)
- `PORT`: Server port (default: `8000`, auto-set by Render)

## API Endpoints

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "message": "API is healthy"
}
```

### `POST /search`
Search for papers using text query.

**Request Body:**
```json
{
  "query": "graph neural networks",
  "method": "hybrid",
  "top_k": 10
}
```

**Methods:**
- `bm25`: Keyword-based search
- `bert`: Semantic search
- `pagerank`: Authority-based search
- `hybrid`: Combined approach (default)

**Response:**
```json
{
  "query": "graph neural networks",
  "method": "hybrid",
  "top_k": 10,
  "results": [
    {
      "id": 12345,
      "title": "Paper Title",
      "abstract": "Paper abstract...",
      "link": "https://arxiv.org/search/?query=...",
      "score": 0.9234,
      "method": "hybrid"
    }
  ]
}
```

### `POST /search-from-pdf`
Search for papers by uploading a PDF, DOCX, or TXT file.

**Request:** multipart/form-data
- `file`: PDF, DOCX, or TXT file (required)
- `method`: Search method - "bm25", "bert", "pagerank", or "hybrid" (default: "hybrid")
- `top_k`: Number of results (default: 10)

**Note:** The backend extracts text from the file and uses only the **first 100 words** as the search query for faster performance, while returning the full extracted text in the response.

**Response:**
```json
{
  "extracted_query": "Full extracted text from file...",
  "method": "hybrid",
  "top_k": 10,
  "results": [
    {
      "id": 12345,
      "title": "Paper Title",
      "abstract": "Paper abstract...",
      "link": "https://arxiv.org/search/?query=...",
      "score": 0.9234,
      "method": "hybrid"
    }
  ]
}
```

### `GET /search`
Convenience GET endpoint with query parameters:
- `query`: Search query (required)
- `method`: Search method (default: "hybrid")
- `top_k`: Number of results (default: 10)

Example: `GET /search?query=neural%20networks&method=bert&top_k=5`

## Deployment

### Backend Deployment (Render)

Artifacts are automatically downloaded from GitHub Releases during startup. No need to commit large files to GitHub!

**Artifact Source:** Artifacts are hosted in GitHub Releases (tag: `v1.0.0-models`) and downloaded automatically at runtime:
- `bm25.pkl` → https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/bm25.pkl
- `df.pkl` → https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/df.pkl
- `graph.pkl` → https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/graph.pkl
- `embeddings.pt` → https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/embeddings.pt

#### Step 1: Configure Render Service

1. **Create a Render account** and create a new Web Service

2. **Configure the service:**
   - **Root Directory:** `backend`
   - **Environment:** Python 3.11
   - **Build Command:** 
     ```bash
     pip install -r requirements.txt && python3 scripts/download_artifacts.py
     ```
   - **Start Command:** 
     ```bash
     uvicorn app.api:app --host 0.0.0.0 --port $PORT
     ```
   
   **Important:** Artifacts are downloaded during the BUILD command, not the START command. This ensures the server binds to `$PORT` immediately, preventing "No open ports detected" errors.

3. **Set environment variables (optional):**
   
   **Required:**
   - `PORT`: Automatically set by Render (do not override)
   
   **Data Directory (Optional):**
   - `DATA_DIR`: Path to data directory (defaults to `data` within backend directory)
   
   **Artifact URLs (Optional - override default GitHub Releases URLs):**
   - `BM25_URL`: Custom URL to download `bm25.pkl`
   - `DF_URL`: Custom URL to download `df.pkl`
   - `GRAPH_URL`: Custom URL to download `graph.pkl`
   - `EMBEDDINGS_URL`: Custom URL to download `embeddings.pt`
   
   **Note:** If environment variables are not set, the script uses the default GitHub Releases URLs listed above.

4. **Deploy:**
   - Connect your GitHub repository
   - Render will automatically deploy on push
   - Check build logs to verify artifact downloads

**Health Check:** The `/health` endpoint reports artifact status. Render will use `GET /health` for health checks. Response includes:
```json
{
  "status": "ok",
  "message": "API is healthy",
  "artifacts": {
    "bm25": true,
    "df": true,
    "graph": true,
    "embeddings": true
  },
  "data_dir": "/path/to/data"
}
```

### Frontend Deployment (Vercel)

The frontend is a Vite React app and builds without backend artifacts.

1. **Deploy via Vercel Dashboard (Recommended):**
   - Connect your GitHub repository
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite (auto-detected)
   - **Build Command:** `npm run build` (auto-detected)
   - **Output Directory:** `dist` (auto-detected)
   - **Install Command:** `npm install` (auto-detected)

2. **Set environment variables:**
   - `VITE_API_BASE_URL`: Your backend API URL (e.g., `https://your-backend.onrender.com`)
     - Note: Also accepts `VITE_API_URL` for backward compatibility
     - **Important:** Point this to your deployed backend URL (Render, Fly.io, etc.)

3. **Alternative: Deploy via Vercel CLI:**
   ```bash
   cd frontend
   npm i -g vercel
   vercel
   ```
   - Follow the prompts
   - Set environment variable: `VITE_API_BASE_URL` (or `VITE_API_URL`)

**Important:** After deployment, ensure the environment variable is set in Vercel dashboard:
- Go to Project Settings → Environment Variables
- Add `VITE_API_BASE_URL` with your Render backend URL
- Redeploy if needed

### Frontend Deployment (Netlify)

1. **Create `netlify.toml` in `frontend/` directory:**
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

2. **Deploy:**
   - Install Netlify CLI: `npm i -g netlify-cli`
   - Run `netlify deploy --prod` in the `frontend/` directory
   - Or connect via Netlify dashboard

3. **Set environment variables:**
   - `VITE_API_URL`: Your backend API URL

### Docker Deployment (Backend)

1. **Build the Docker image:**
```bash
cd backend
docker build -t paper-search-backend .
```

2. **Run the container:**
```bash
docker run -p 8000:8000 -v $(pwd)/../data:/app/data paper-search-backend
```

**Note:** Adjust the volume mount path based on where your `data/` folder is located.

## Performance

The search engine has been optimized for low latency using a 2-stage retrieval pipeline:

### Architecture

1. **2-Stage Retrieval Pipeline**:
   - **Stage 1**: Fast BM25 candidate generation (always runs first, retrieves top 300 candidates)
   - **Stage 2**: Optional lightweight re-ranking on the small candidate set only
   - This ensures all methods are fast, with neural models only processing ~300 documents instead of the full corpus

2. **Precomputed PageRank Scores**: PageRank scores are precomputed at startup and stored in memory for fast re-weighting.

3. **Query Truncation**: Queries are normalized and truncated to 2048 characters to ensure consistent performance regardless of input length.

4. **PDF Upload Optimization**: File uploads use only the **first 100 words** of extracted text as the search query, significantly speeding up searches for long documents.

5. **Query Caching**: An in-memory LRU cache (256 entries) caches search results for frequently repeated queries, providing near-instant responses for cached queries.

6. **Efficient Model Loading**: All models and embeddings are loaded once at startup, not per-request.

### Performance Characteristics

- **BM25 Search**: Typically < 50ms for top_k=10
- **BERT Search**: Typically < 150ms for top_k=10 (only processes ~300 candidates)
- **PageRank Search**: Typically < 60ms for top_k=10
- **Hybrid Search**: Typically < 200ms for top_k=10
- **Cached Queries**: < 10ms

### Production Deployment

For production, use multiple workers to handle concurrent requests:

```bash
# Using uvicorn with multiple workers
uvicorn app.api:app --host 0.0.0.0 --port 8000 --workers 2

# Or using gunicorn with uvicorn workers
gunicorn app.api:app -k uvicorn.workers.UvicornWorker -w 2 --bind 0.0.0.0:8000
```

**Note**: When using multiple workers, each worker will load its own copy of the models and embeddings. Ensure sufficient memory (recommended: 4GB+ per worker).

## Development Notes

- The backend expects the `data/` folder to be at `../data` relative to the `backend/` directory
- All heavy computations (BM25 index, embeddings, graph) are precomputed
- The engine loads all artifacts on startup, which may take a few seconds
- For production, consider adding rate limiting and monitoring

## Troubleshooting

### Backend Issues

- **Import errors:** Ensure you're running from the `backend/` directory or have the correct Python path
- **Data not found:** Verify the `data/` folder exists at the repository root
- **Port already in use:** Change the port in `main.py` or use `--port` flag with uvicorn

### Frontend Issues

- **API connection errors:** Check that `VITE_API_URL` is set correctly and the backend is running
- **CORS errors:** Ensure CORS is enabled in the backend (already configured in `api.py`)
- **Build errors:** Make sure all dependencies are installed with `npm install`

## Deployment Status

✅ **Backend: Deploy-ready on Render**
- Uses `$PORT` environment variable (auto-set by Render)
- Configurable data directory via `DATA_DIR` environment variable
- Health check endpoint at `/health`
- CORS configured for frontend integration
- All dependencies in `requirements.txt`
- Entry point: `uvicorn app.api:app --host 0.0.0.0 --port $PORT`

✅ **Frontend: Deploy-ready on Vercel**
- Build command: `npm run build`
- Output directory: `dist`
- API base URL configurable via `VITE_API_BASE_URL` or `VITE_API_URL`
- All API calls use configurable base URL (no hardcoded localhost)
- Production-ready error handling

## License

This project is for educational/research purposes.

## Acknowledgments

- Uses the ogbn-arxiv dataset from OGB
- BERT embeddings via SentenceTransformers
- BM25 implementation via rank-bm25
- PageRank via NetworkX

