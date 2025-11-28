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
│   │   ├── engine.py      # PaperSearchEngine class
│   │   └── api.py         # FastAPI application
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

**Note:** The data files (`df.pkl`, `bm25.pkl`, `embeddings.pt`, `graph.pkl`) are not included in this repository due to GitHub's file size limits. You need to:
1. Generate them using the `ISR_Project.ipynb` notebook, OR
2. Download them from a cloud storage location (if provided), OR
3. Use your own precomputed data files

Place all data files in the `data/` directory at the repository root.

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
Search for papers.

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
[
  {
    "id": 12345,
    "title": "Paper Title",
    "abstract": "Paper abstract...",
    "link": "https://arxiv.org/search/?query=...",
    "score": 0.9234,
    "method": "hybrid"
  }
]
```

### `GET /search`
Convenience GET endpoint with query parameters:
- `query`: Search query (required)
- `method`: Search method (default: "hybrid")
- `top_k`: Number of results (default: 10)

Example: `GET /search?query=neural%20networks&method=bert&top_k=5`

## Deployment

### Backend Deployment (Render)

#### Step 1: Prepare Data Files

Since data files exceed GitHub's 100MB limit, you need to host them elsewhere. Choose one option:

**Option A: Cloud Storage (Recommended)**
1. Upload your data files to one of these services:
   - **Google Drive**: Upload files, get shareable links, use `gdown` to download
   - **AWS S3**: Upload to S3 bucket, use `aws s3 cp` in build script
   - **Dropbox/OneDrive**: Upload and get direct download URLs
   - **Any web server**: Host files and get direct URLs

2. Set environment variables in Render with download URLs:
   - `DATA_DF_URL`: URL to download `df.pkl`
   - `DATA_BM25_URL`: URL to download `bm25.pkl`
   - `DATA_EMBEDDINGS_URL`: URL to download `embeddings.pt`
   - `DATA_GRAPH_URL`: URL to download `graph.pkl`

**Option B: Render Persistent Disk**
1. Create a persistent disk in Render
2. SSH into your Render instance
3. Upload data files via SCP:
   ```bash
   scp data/*.pkl data/*.pt root@your-render-instance:/path/to/data/
   ```
4. Set `DATA_DIR` environment variable to the disk mount point

**Option C: Compress and Split Files**
1. Compress files: `gzip data/*.pkl data/*.pt`
2. Split large files: `split -b 50M data/df.pkl.gz data/df.pkl.gz.part`
3. Upload parts to GitHub or cloud storage
4. Create build script to reassemble during deployment

#### Step 2: Configure Render Service

1. **Create a Render account** and create a new Web Service

2. **Configure the service:**
   - **Root Directory:** `backend`
   - **Environment:** Python 3.11
   - **Build Command:** 
     ```bash
     pip install -r requirements.txt && python download_data.py && python check_data.py
     ```
     The `check_data.py` script verifies all files were downloaded correctly. Check build logs to confirm.
     (Or use `bash download_data.sh` if using shell script)
   - **Start Command:** `uvicorn app.api:app --host 0.0.0.0 --port $PORT`
   
   **Important:** The build command downloads data files. Make sure the build completes successfully before the service starts.

3. **Set environment variables:**
   - `PORT`: Automatically set by Render (do not override)
   - `DATA_DIR`: (Optional) Path to data directory. Defaults to `../data` relative to backend root
     - For Render with root directory `backend`, use `../data` (this points to repo root/data)
     - Alternative: Use absolute path like `/opt/render/project/src/data` if needed
   - `DATA_DF_URL`: (Optional, if using custom URLs) URL to download df.pkl
   - `DATA_BM25_URL`: (Optional, if using custom URLs) URL to download bm25.pkl
   - `DATA_EMBEDDINGS_URL`: (Optional, if using custom URLs) URL to download embeddings.pt
   - `DATA_GRAPH_URL`: (Optional, if using custom URLs) URL to download graph.pkl
   
   **Note:** If you don't set the DATA_*_URL variables, the script will use the pre-configured Google Drive file IDs.

4. **Deploy:**
   - Connect your GitHub repository
   - Render will automatically deploy on push

**Health Check:** Render will use `GET /health` endpoint for health checks.

#### Quick Setup with Google Drive (Already Configured!)

✅ **Your Google Drive files are already configured!**

The download scripts are pre-configured with your Google Drive file IDs:
- `df.pkl`: 1DzBhRncYzif5bsbgIDxxgxb05T9mh8-h
- `bm25.pkl`: 1LZBDvDHKCylR2YRzUrywvDaREVXpEc4Y
- `embeddings.pt`: 12e382jL02z56gz5fPOINxBxHYVTBqIBb
- `graph.pkl`: 1KX1Bl54xINL75QOhtA9Av_9SBJxVuYPU

**Render Configuration:**
- **Build Command:** `pip install -r requirements.txt && python download_data.py`
- **Start Command:** `uvicorn app.api:app --host 0.0.0.0 --port $PORT`

The script will automatically download all data files from Google Drive during the build process.

**Important:** Make sure your Google Drive files are set to "Anyone with the link can view" for the download to work.

### Frontend Deployment (Vercel)

1. **Deploy via Vercel Dashboard (Recommended):**
   - Connect your GitHub repository
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build` (auto-detected)
   - **Output Directory:** `dist` (auto-detected)
   - **Install Command:** `npm install` (auto-detected)

2. **Set environment variables:**
   - `VITE_API_BASE_URL`: Your backend API URL (e.g., `https://your-backend.onrender.com`)
     - Note: Also accepts `VITE_API_URL` for backward compatibility

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

The search engine has been optimized for low latency:

### Optimizations

1. **FAISS for BERT Search**: BERT semantic search uses FAISS (Facebook AI Similarity Search) for fast approximate nearest neighbor search. This provides sub-second query times even with large embedding corpora.

2. **Precomputed PageRank Scores**: Base PageRank scores are precomputed at startup and stored in memory. Query-specific personalization is applied efficiently using vectorized operations.

3. **Vectorized Operations**: BM25 and hybrid search use NumPy vectorized operations instead of Python loops for faster computation.

4. **Query Caching**: An in-memory LRU cache (256 entries) caches search results for frequently repeated queries, providing near-instant responses for cached queries.

5. **Text Extraction Limits**: File uploads (PDF, DOCX, TXT) are limited to the first 4000 characters to prevent very long documents from slowing down BERT encoding.

6. **Efficient Model Loading**: All models and embeddings are loaded once at startup, not per-request.

### Performance Characteristics

- **BERT Search**: Typically < 100ms on CPU for top_k=10
- **BM25 Search**: Typically < 50ms for top_k=10
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

### Logging

The system logs performance metrics for each search query:
- Query latency (total time)
- Method used (BM25, BERT, PageRank, Hybrid)
- Number of results returned
- File extraction time (for file uploads)

Logs are output at INFO level and can be configured via Python's logging module.

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

