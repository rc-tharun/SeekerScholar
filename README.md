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
├── data/                  # Precomputed artifacts (lite format)
│   ├── df.parquet        # Papers DataFrame (compressed Parquet)
│   ├── bm25.pkl          # BM25 index
│   ├── embeddings.f16.npy # BERT embeddings (float16, memory-mapped)
│   ├── embeddings.meta.json # Embeddings metadata
│   └── graph.pkl         # Citation graph
└── README.md
```

## Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Precomputed data artifacts in `data/` directory

**Note:** Artifacts are not stored in GitHub; they are downloaded during build. The backend uses **lite artifacts** for reduced RAM usage:
- `df.parquet` - Compressed columnar format (instead of `df.pkl`)
- `embeddings.f16.npy` - Float16 numpy memmap format (instead of `embeddings.pt`)
- `embeddings.meta.json` - Metadata for embeddings shape/dtype
- `bm25.pkl` - BM25 index (unchanged)
- `graph.pkl` - Citation graph (unchanged)

Artifacts are automatically downloaded from GitHub Releases during deployment. See [Deployment](#deployment) section for details.

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

**Frontend (Vite):**
Create a `.env` file in the `frontend/` directory for local development:
```
VITE_API_BASE_URL=http://localhost:8000
```
Or use `VITE_API_URL` for backward compatibility.

**For Production (Vercel) - RECOMMENDED:**
The frontend defaults to `https://seekerscholar-1.onrender.com` in production, but it's recommended to set `VITE_API_BASE_URL` explicitly in Vercel for clarity and flexibility.

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add environment variable:
   - **Name:** `VITE_API_BASE_URL`
   - **Value:** `https://seekerscholar-1.onrender.com` (or your backend URL)
   - **Environment:** Production (and Preview if desired)
3. **Redeploy** your project after adding the variable

**Note:** The frontend code defaults to `https://seekerscholar-1.onrender.com` in production if `VITE_API_BASE_URL` is not set, so the app will work even without the env var. However, setting it explicitly is recommended for clarity.

**Backend:**
Optional environment variables (create `.env` in `backend/` or set in deployment platform):
- `DATA_DIR`: Path to data directory (default: `data` within backend directory)
- `PORT`: Server port (default: `8000`, auto-set by Render)
- `FRONTEND_ORIGIN`: Frontend origin URL for CORS (e.g., `https://seeker-scholar.vercel.app`)
  - If not set, defaults to localhost origins for local development

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

**Artifact Source:** Lite artifacts are hosted in GitHub Releases (tag: `v1.0.0-models`) and downloaded automatically at runtime:
- `bm25.pkl` → https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/bm25.pkl
- `df.parquet` → https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/df.parquet
- `graph.pkl` → https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/graph.pkl
- `embeddings.f16.npy` → https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/embeddings.f16.npy
- `embeddings.meta.json` → https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/embeddings.meta.json

**Memory Optimization:** The backend uses lazy loading and memory-mapped files to reduce RAM usage:
- DataFrame loads from compressed Parquet (columnar format)
- Embeddings use numpy memmap (memory-mapped, not fully loaded into RAM)
- Artifacts load on-demand, not at startup
- Designed to fit under 512MB RAM on Render

#### Render Python Environment Deployment

This project uses **Render's Python environment** (`env: python`), not Docker. The `Dockerfile` is present but not used by Render in this deployment mode.

**Configuration:** The deployment is configured via `backend/render.yaml`:

```yaml
services:
  - type: web
    name: paper-search-backend
    env: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: python scripts/download_artifacts.py && uvicorn app.api:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATA_DIR
        value: data
      - key: BM25_URL
        value: https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/bm25.pkl
      - key: DF_PARQUET_URL
        value: https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/df.parquet
      - key: GRAPH_URL
        value: https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/graph.pkl
      - key: EMBEDDINGS_NPY_URL
        value: https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/embeddings.f16.npy
      - key: EMBEDDINGS_META_URL
        value: https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/embeddings.meta.json
```

**Key Points:**
- **Environment:** Python 3.11 (`env: python`)
- **Root Directory:** `backend` (Render will look for `render.yaml` in the repo root, but `rootDir` sets the working directory)
- **Build Command:** Installs dependencies only
- **Start Command:** Downloads artifacts first, then starts the server. Artifacts are downloaded at startup with retry logic (4 attempts with exponential backoff).
- **Data Directory:** Set via `DATA_DIR` environment variable (defaults to `data` within backend directory)
- **Artifact URLs:** Pre-configured in `render.yaml`, but can be overridden via environment variables if needed

**Deployment Steps:**

1. **Connect Repository:**
   - Create a Render account and create a new Web Service
   - Connect your GitHub repository
   - Render will automatically detect `backend/render.yaml` and use it for configuration

2. **Verify Configuration:**
   - Render should auto-detect the `render.yaml` file
   - Ensure the service shows:
     - **Root Directory:** `backend`
     - **Environment:** Python 3.11
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `python scripts/download_artifacts.py && uvicorn app.api:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables:**
   - All required environment variables are set in `render.yaml`, including:
     - `FRONTEND_ORIGIN`: Set to `https://seeker-scholar.vercel.app` for CORS
     - `DATA_DIR`: Set to `data` (artifacts directory)
     - Artifact download URLs (BM25_URL, DF_URL, GRAPH_URL, EMBEDDINGS_URL)
   - `PORT` is automatically set by Render (do not override)
   - You can override environment variables via Render dashboard if needed

4. **Deploy:**
   - Render will automatically deploy on push
   - Check build logs to verify:
     - Dependencies are installed
     - Artifacts are downloaded (with retry logic if needed)
     - Server starts successfully

**Note:** The downloader script includes retry logic (4 attempts with 2s/4s/8s exponential backoff) to handle transient network errors, timeouts, and HTTP 500+ errors.

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

2. **Set environment variables (REQUIRED):**
   - `VITE_API_BASE_URL`: Your backend API URL (e.g., `https://seekerscholar-1.onrender.com`)
     - **REQUIRED:** This variable must be set in production. The app will fail if missing.
     - Note: Also accepts `VITE_API_URL` for backward compatibility
     - **Important:** After setting or changing environment variables in Vercel, you must redeploy for changes to take effect
     - Go to Project Settings → Environment Variables in Vercel dashboard
     - Set for Production environment (and Preview if desired)

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

6. **Lazy Loading & Memory Optimization**: 
   - Artifacts load on-demand, not at startup
   - DataFrame uses compressed Parquet format
   - Embeddings use numpy memmap (memory-mapped, not fully loaded into RAM)
   - Designed to fit under 512MB RAM on Render

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

**Note**: With lazy loading, each worker only loads artifacts when needed. However, for production on Render with 512MB RAM limit, use a single worker (default). Multiple workers are not recommended due to memory constraints.

## Development Notes

- The backend expects the `data/` folder to be at `../data` relative to the `backend/` directory (or set via `DATA_DIR` env var)
- All heavy computations (BM25 index, embeddings, graph) are precomputed
- **Lazy Loading:** Artifacts load on-demand, not at startup, to reduce RAM usage
- **Memory Optimization:** Uses Parquet for DataFrame and numpy memmap for embeddings
- For production, consider adding rate limiting and monitoring

### Converting Artifacts to Lite Format

To convert existing heavy artifacts (`df.pkl`, `embeddings.pt`) to lite format:

1. **Run conversion script locally:**
   ```bash
   cd backend
   python scripts/convert_artifacts.py
   ```

2. **Upload converted files to GitHub Releases:**
   - `df.parquet`
   - `embeddings.f16.npy`
   - `embeddings.meta.json`
   - Keep existing: `bm25.pkl`, `graph.pkl`

3. **Update `render.yaml` with new URLs** (if using a new release tag)

The conversion script:
- Converts `df.pkl` → `df.parquet` (compressed, columnar format)
- Converts `embeddings.pt` → `embeddings.f16.npy` (float16, memory-mapped)
- Creates `embeddings.meta.json` with shape and dtype information
- Reduces file sizes significantly for faster downloads and lower RAM usage

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

