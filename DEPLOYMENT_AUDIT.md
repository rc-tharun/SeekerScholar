# SeekerScholar Deployment Configuration Audit
**Date:** 2025-12-20  
**Frontend:** https://seeker-scholar.vercel.app/  
**Backend:** https://seekerscholar-1.onrender.com

## A) Backend (Render) Audit

### A1) ASGI Entrypoint ✅
- **Status:** ✅ CORRECT
- **render.yaml:** Uses `uvicorn app.api:app --host 0.0.0.0 --port $PORT`
- **main.py:** Uses `uvicorn.run("app.api:app", ...)` for local dev
- **No issues:** No accidental "uvicorn main:app" usage found

### A2) Start Command ✅
- **Status:** ✅ CORRECT
- **render.yaml line 7:** `python scripts/download_artifacts.py && uvicorn app.api:app --host 0.0.0.0 --port $PORT`
- **Downloader runs first:** ✅
- **Binds to $PORT:** ✅

### A3) Environment Variables ✅
- **Status:** ✅ CORRECT
- **render.yaml contains:**
  - ✅ `DATA_DIR=data`
  - ✅ `DF_PARQUET_URL` (points to v1.0.0-models/df.parquet)
  - ✅ `EMBEDDINGS_NPY_URL` (points to v1.0.0-models/embeddings.f16.npy)
  - ✅ `EMBEDDINGS_META_URL` (points to v1.0.0-models/embeddings.meta.json)
  - ✅ `BM25_URL` (points to v1.0.0-models/bm25.pkl)
  - ✅ `GRAPH_URL` (points to v1.0.0-models/graph.pkl)
  - ✅ `FRONTEND_ORIGIN=https://seeker-scholar.vercel.app`

### A4) Downloader Downloads Lite Assets ✅
- **Status:** ✅ CORRECT
- **download_artifacts.py line 216:** Artifacts list is:
  - `["bm25.pkl", "df.parquet", "graph.pkl", "embeddings.f16.npy", "embeddings.meta.json"]`
- **No old assets:** ✅ No `df.pkl` or `embeddings.pt` in artifact list
- **URLs correct:** ✅ All point to v1.0.0-models tag

### A5) Resource Loading ✅
- **Status:** ✅ CORRECT
- **resources.py get_df():**
  - ✅ Uses `pd.read_parquet(columns=["index", "title", "abstract"])`
  - ✅ Only loads needed columns
- **resources.py get_embeddings():**
  - ✅ Reads `embeddings.meta.json` for shape
  - ✅ Uses `np.memmap(path, dtype=np.float16, mode="r", shape=(N,D))`
  - ✅ No copying - returns memmap directly
- **resources.py get_bm25() & get_graph():**
  - ✅ Lazy-loaded (only when needed)
  - ✅ No import-time loading
- **No eager loading:** ✅ All loads happen inside getters, cached after first access

### A6) CORS Configuration ✅
- **Status:** ✅ CORRECT
- **api.py lines 98-120:**
  - ✅ Uses `CORSMiddleware`
  - ✅ Reads `FRONTEND_ORIGIN` from env var
  - ✅ Allows only Vercel origin in production: `https://seeker-scholar.vercel.app`
  - ✅ Falls back to localhost origins for development
  - ✅ `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`

### A7) /health Endpoint ✅
- **Status:** ✅ CORRECT
- **api.py lines 240-266:**
  - ✅ Returns JSON with:
    - `status`: "ok" or "degraded"
    - `data_dir`: path string
    - `files`: dict with file existence booleans
    - `loaded`: dict with resource loaded status booleans
  - ✅ Uses `check_files_exist()` and `get_loaded_status()` from resources module

## B) Frontend (Vercel) Audit

### B1) No localhost in Production ✅
- **Status:** ✅ CORRECT
- **api.ts lines 9-22:**
  - ✅ Production defaults to `https://seekerscholar-1.onrender.com`
  - ✅ Only uses localhost in development (`import.meta.env.PROD` check)
  - ✅ No hardcoded localhost in production code paths

### B2) Environment Variable Configuration ✅
- **Status:** ✅ CORRECT
- **api.ts line 10:** Uses `import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL`
- **Production default:** Falls back to `https://seekerscholar-1.onrender.com` if env var not set
- **README:** Documents `VITE_API_BASE_URL` requirement (though code has safe default)

### B3) Centralized API Helper ✅
- **Status:** ✅ CORRECT
- **App.tsx line 3:** Imports `apiPost, apiPostFormData` from `./lib/api`
- **App.tsx line 62:** Uses `apiPost<SearchResponse>()` for search
- **App.tsx line 175:** Uses `apiPostFormData<PdfSearchResponse>()` for file upload
- **No direct fetch calls:** ✅ All API calls go through centralized helper

## C) Final "Everything Correct" Report

### ✅ All Items Pass

| Category | Item | Status |
|----------|------|--------|
| **Backend** | ASGI entrypoint (app.api:app) | ✅ |
| **Backend** | Start command with downloader | ✅ |
| **Backend** | Environment variables | ✅ |
| **Backend** | Lite asset downloads | ✅ |
| **Backend** | Resource lazy loading | ✅ |
| **Backend** | CORS configuration | ✅ |
| **Backend** | /health endpoint | ✅ |
| **Frontend** | No localhost in production | ✅ |
| **Frontend** | Env var for backend URL | ✅ |
| **Frontend** | Centralized API helper | ✅ |

### Memory Optimization Verification

- ✅ **Parquet selective loading:** Only loads `["index", "title", "abstract"]` columns
- ✅ **Numpy memmap:** Embeddings use `np.memmap(mode="r")` - no full RAM load
- ✅ **Lazy loading:** All artifacts load on-demand, not at import time
- ✅ **No eager loading:** Verified no `pd.read_pickle`, `torch.load`, or `pickle.load` at module level

### Smoke Test Plan

1. **Frontend Search Test:**
   - Open https://seeker-scholar.vercel.app/
   - Perform a search query (e.g., "neural networks")
   - Open browser DevTools → Network tab
   - Verify requests go to `https://seekerscholar-1.onrender.com/search`
   - ✅ Should NOT see `localhost:8000` in production

2. **CORS Verification:**
   - Check browser console for CORS errors
   - ✅ Should see no CORS errors
   - ✅ Requests should succeed

3. **Health Endpoint Test:**
   ```bash
   curl https://seekerscholar-1.onrender.com/health
   ```
   Expected response:
   ```json
   {
     "status": "ok",
     "data_dir": "/path/to/data",
     "files": {
       "df.parquet": true,
       "embeddings.f16.npy": true,
       "embeddings.meta.json": true,
       "bm25.pkl": true,
       "graph.pkl": true
     },
     "loaded": {
       "df": true/false,
       "embeddings": true/false,
       "bm25": true/false,
       "graph": true/false
     }
   }
   ```

4. **Backend Logs Check:**
   - Check Render logs for:
     - ✅ "CORS: Allowing origin from FRONTEND_ORIGIN: https://seeker-scholar.vercel.app"
     - ✅ Artifact download success messages
     - ✅ "Search engine initialized successfully" (after first search)

## Summary

**✅ ALL CHECKS PASSED**

The deployment configuration is correct and production-ready:
- Backend uses lite artifacts with lazy loading (fits 512MB RAM)
- Frontend correctly points to Render backend
- CORS is properly configured
- All environment variables are set correctly
- No localhost references in production code

**No fixes required.** The configuration is ready for deployment.

