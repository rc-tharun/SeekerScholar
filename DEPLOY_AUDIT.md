# Deploy Readiness Audit Report
**Date:** 2024  
**Repo:** https://github.com/rc-tharun/SeekerScholar

---

## A) Deploy Ready Checklist

### 1. Repo Structure + Build

| Check | Status | Notes |
|-------|--------|-------|
| Frontend framework identified | ✅ | **Vite** (React + TypeScript) |
| Frontend builds from clean clone | ✅ | `npm install && npm run build` works |
| Backend entrypoint identified | ✅ | `app.api:app` (FastAPI) |
| Backend starts on $PORT | ✅ | Uses `uvicorn app.api:app --host 0.0.0.0 --port ${PORT:-8000}` |
| Python deps pinned | ⚠️ | Some deps use `>=` (torch, pydantic, transformers) - acceptable but not fully pinned |
| Python deps installable | ✅ | `requirements.txt` is valid |

**Issues Found:**
- Some dependencies use `>=` instead of `==` (torch, pydantic, transformers, huggingface-hub). This is acceptable for ML libraries that need flexibility, but could cause version drift.

### 2. Artifact Workflow Verification

| Check | Status | Notes |
|-------|--------|-------|
| .gitignore excludes data/ | ✅ | `data/`, `backend/data/`, `*.pkl`, `*.pt`, `*.pk` all excluded |
| .gitignore excludes large files | ✅ | All artifact patterns covered |
| Backend downloads artifacts automatically | ✅ | `scripts/download_artifacts.py` runs in `start.sh` |
| Uses DATA_DIR consistently | ✅ | `Config.get_data_dir()` used throughout |
| Download script is idempotent | ✅ | Checks `os.path.exists()` before downloading |
| Validates file presence | ✅ | Checks existence and non-zero size |
| Validates non-zero file size | ✅ | Validates `file_size > 0` after download |
| URLs configurable via env vars | ✅ | `BM25_URL`, `DF_URL`, `GRAPH_URL`, `EMBEDDINGS_URL` |
| Defaults to GitHub Releases URLs | ✅ | Uses `v1.0.0-models` tag URLs |

**All artifact workflow checks pass! ✅**

### 3. Runtime Correctness Checks

| Check | Status | Notes |
|-------|--------|-------|
| Stateless (no writes outside DATA_DIR) | ✅ | Only writes to `DATA_DIR` and temp files (deleted) |
| /health endpoint exists | ✅ | Returns artifact status |
| /health reports artifact availability | ✅ | Returns `artifacts: {bm25, df, graph, embeddings}` |
| CORS configured | ✅ | Configurable via `CORS_ORIGINS` env var |
| CORS allows Vercel frontend | ✅ | Can be set via env var (defaults to `*` for dev) |

**All runtime checks pass! ✅**

### 4. Platform-Specific Checks

#### Render/Fly (Backend)

| Check | Status | Notes |
|-------|--------|-------|
| Build command provided | ✅ | `pip install -r requirements.txt` |
| Start command provided | ✅ | `bash start.sh` |
| start.sh exists | ✅ | Located at `backend/start.sh` |
| start.sh is executable | ✅ | Has `#!/bin/bash` and executable permissions |
| Uses bash | ✅ | Script uses `bash` |

#### Vercel (Frontend)

| Check | Status | Notes |
|-------|--------|-------|
| Root Directory specified | ✅ | `frontend` |
| Build Command specified | ✅ | `npm run build` (auto-detected) |
| Output Directory specified | ✅ | `dist` (auto-detected) |
| Env var name documented | ✅ | `VITE_API_BASE_URL` (with fallback to `VITE_API_URL`) |

**All platform checks pass! ✅**

---

## B) Required Environment Variables

### Backend (Render/Fly)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | ✅ Auto-set | - | Server port (set by platform) |
| `DATA_DIR` | ❌ | `backend/data` | Path to data directory |
| `BM25_URL` | ❌ | GitHub Releases URL | Override URL for `bm25.pkl` |
| `DF_URL` | ❌ | GitHub Releases URL | Override URL for `df.pkl` |
| `GRAPH_URL` | ❌ | GitHub Releases URL | Override URL for `graph.pkl` |
| `EMBEDDINGS_URL` | ❌ | GitHub Releases URL | Override URL for `embeddings.pt` |
| `CORS_ORIGINS` | ❌ | `*` | Comma-separated allowed origins (e.g., `https://your-app.vercel.app`) |

**Default GitHub Releases URLs:**
- `bm25.pkl`: https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/bm25.pkl
- `df.pkl`: https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/df.pkl
- `graph.pkl`: https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/graph.pkl
- `embeddings.pt`: https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/embeddings.pt

### Frontend (Vercel)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE_URL` | ✅ | `http://localhost:8000` | Backend API URL (e.g., `https://your-backend.onrender.com`) |
| `VITE_API_URL` | ❌ | - | Fallback (backward compatibility) |

---

## C) Exact Deploy Steps

### Backend on Render

1. **Create New Web Service**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect GitHub repository: `rc-tharun/SeekerScholar`

2. **Configure Service Settings**
   - **Name:** `seekerscholar-backend` (or your choice)
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Build Command:** 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     bash start.sh
     ```

3. **Set Environment Variables**
   - Go to "Environment" tab
   - Add:
     - `CORS_ORIGINS`: `https://your-frontend.vercel.app` (after frontend is deployed)
     - (Optional) `DATA_DIR`: Custom path if needed
     - (Optional) `BM25_URL`, `DF_URL`, `GRAPH_URL`, `EMBEDDINGS_URL`: Custom URLs if not using GitHub Releases

4. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete (downloads artifacts automatically)
   - Note the service URL (e.g., `https://seekerscholar-backend.onrender.com`)

### Frontend on Vercel

1. **Import Project**
   - Go to https://vercel.com/dashboard
   - Click "Add New..." → "Project"
   - Import Git repository: `rc-tharun/SeekerScholar`

2. **Configure Project Settings**
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite (auto-detected)
   - **Build Command:** `npm run build` (auto-detected)
   - **Output Directory:** `dist` (auto-detected)
   - **Install Command:** `npm install` (auto-detected)

3. **Set Environment Variables**
   - Go to "Settings" → "Environment Variables"
   - Add:
     - `VITE_API_BASE_URL`: `https://your-backend.onrender.com` (use your actual Render backend URL)

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Note the deployment URL (e.g., `https://seekerscholar.vercel.app`)

5. **Update Backend CORS (if needed)**
   - Go back to Render dashboard
   - Update `CORS_ORIGINS` environment variable to your Vercel URL
   - Redeploy backend

---

## D) If Something Fails

### Backend Issues

#### Issue: "Module not found" or import errors
**Cause:** Python dependencies not installed or wrong Python version  
**Fix:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Issue: "Artifacts not found" or download fails
**Cause:** GitHub Releases URLs incorrect or network issue  
**Fix:**
1. Verify GitHub Releases tag exists: https://github.com/rc-tharun/SeekerScholar/releases/tag/v1.0.0-models
2. Check download script logs in Render build output
3. Manually test download: `curl -I https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/bm25.pkl`
4. If needed, set custom URLs via env vars: `BM25_URL`, `DF_URL`, etc.

#### Issue: "Port already in use" or server won't start
**Cause:** PORT env var not set or conflicting  
**Fix:**
- Render automatically sets `PORT` - don't override it
- For local testing: `export PORT=8000` or use `uvicorn app.api:app --port 8000`

#### Issue: CORS errors from frontend
**Cause:** CORS_ORIGINS not configured correctly  
**Fix:**
1. Set `CORS_ORIGINS` in Render to your Vercel frontend URL (comma-separated if multiple)
2. Example: `CORS_ORIGINS=https://seekerscholar.vercel.app`
3. Redeploy backend

#### Issue: "/health returns degraded status"
**Cause:** Artifacts missing or download failed  
**Fix:**
1. Check Render build logs for download errors
2. Verify GitHub Releases URLs are accessible
3. Check `DATA_DIR` is writable
4. Manually run: `python3 scripts/download_artifacts.py` in Render shell

### Frontend Issues

#### Issue: "Cannot connect to API" or CORS errors
**Cause:** `VITE_API_BASE_URL` not set or incorrect  
**Fix:**
1. Verify env var is set in Vercel: `VITE_API_BASE_URL=https://your-backend.onrender.com`
2. Ensure no trailing slash in URL
3. Redeploy frontend after setting env var
4. Check browser console for exact error

#### Issue: Build fails with TypeScript errors
**Cause:** Type errors or missing dependencies  
**Fix:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

#### Issue: "404 Not Found" on routes
**Cause:** Vercel routing not configured  
**Fix:**
- Vite builds to `dist/` which Vercel auto-detects
- If using custom routing, add `vercel.json` with redirect rules

### General Issues

#### Issue: Slow first request after deployment
**Cause:** Cold start - artifacts loading  
**Fix:**
- Normal behavior - first request may take 10-30 seconds while artifacts load
- Subsequent requests are fast
- Consider using Render's "Always On" plan to avoid cold starts

#### Issue: Out of memory errors
**Cause:** Artifacts are large (~1GB total)  
**Fix:**
- Ensure Render instance has at least 2GB RAM
- Upgrade to a plan with more memory if needed

---

## E) Smoke Test Commands

### Backend Local Test

```bash
# From repo root
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download artifacts (idempotent - safe to run multiple times)
python3 scripts/download_artifacts.py

# Start server
python3 main.py
# Or: uvicorn app.api:app --host 0.0.0.0 --port 8000

# In another terminal, test health endpoint
curl http://localhost:8000/health
# Expected: {"status":"ok","message":"API is healthy","artifacts":{"bm25":true,"df":true,"graph":true,"embeddings":true},"data_dir":"..."}

# Test search endpoint
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"machine learning","method":"hybrid","top_k":5}'
```

### Frontend Local Test

```bash
# From repo root
cd frontend

# Install dependencies
npm install

# Build (production test)
npm run build

# Start dev server
npm run dev
# Opens at http://localhost:3000

# In browser, test API connection
# Open browser console and check for API calls
# Or manually test:
curl http://localhost:8000/health
```

### Full Integration Test

```bash
# Terminal 1: Start backend
cd backend
source venv/bin/activate
python3 main.py

# Terminal 2: Start frontend
cd frontend
npm run dev

# Terminal 3: Test API
curl http://localhost:8000/health
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"neural networks","method":"hybrid","top_k":3}'

# Browser: Open http://localhost:3000 and test search
```

---

## Summary

✅ **Overall Status: DEPLOY READY**

All critical checks pass. The repository is ready for deployment to:
- **Backend:** Render or Fly.io (or any Linux host)
- **Frontend:** Vercel

**Minor Recommendations:**
1. Consider pinning more Python dependencies to exact versions for reproducibility
2. Set `CORS_ORIGINS` in production to your actual Vercel domain (not `*`)
3. Monitor artifact download times in production (first deploy may take 5-10 minutes)

**Files Changed During Audit:**
- `backend/app/api.py` - Made CORS configurable via `CORS_ORIGINS` env var

