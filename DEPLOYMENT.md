# Deployment Readiness Checklist

## ✅ Backend (Render) - DEPLOY-READY

### Configuration
- ✅ FastAPI entry point: `app.api:app`
- ✅ Start command: `uvicorn app.api:app --host 0.0.0.0 --port $PORT`
- ✅ PORT environment variable: Uses `$PORT` (auto-set by Render)
- ✅ Data directory: Configurable via `DATA_DIR` env var (default: `../data`)
- ✅ Health check: `GET /health` endpoint exists
- ✅ CORS: Configured (allows all origins, can be restricted in production)

### Dependencies
- ✅ All required packages in `requirements.txt`:
  - fastapi, uvicorn[standard]
  - pandas, numpy, torch
  - sentence-transformers, rank-bm25, networkx
  - pypdf, python-docx, python-multipart
  - pydantic

### Render Configuration
```
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.api:app --host 0.0.0.0 --port $PORT
Environment: Python 3.11
```

### Environment Variables
- `PORT`: Auto-set by Render (do not override)
- `DATA_DIR`: (Optional) Path to data directory. Default: `../data`

### Data Directory Options
1. **Include in repo** (if < 100MB): Set `DATA_DIR=../data`
2. **Cloud storage**: Download during build, set `DATA_DIR` to downloaded path
3. **Persistent disk**: Mount and set `DATA_DIR` to mount point

---

## ✅ Frontend (Vercel) - DEPLOY-READY

### Configuration
- ✅ Build command: `npm run build`
- ✅ Output directory: `dist`
- ✅ Framework: Vite (auto-detected by Vercel)
- ✅ API base URL: Configurable via environment variable

### Environment Variables
- `VITE_API_BASE_URL`: Backend API URL (e.g., `https://your-backend.onrender.com`)
- `VITE_API_URL`: Alternative (backward compatible)

### Vercel Configuration
```
Root Directory: frontend
Framework Preset: Vite
Build Command: npm run build (auto-detected)
Output Directory: dist (auto-detected)
Install Command: npm install (auto-detected)
```

### API Integration
- ✅ All API calls use `API_BASE_URL` (no hardcoded localhost)
- ✅ Error handling for unreachable backend
- ✅ Loading states for async operations

---

## Deployment Steps

### Backend (Render)
1. Push code to GitHub
2. Create new Web Service on Render
3. Connect GitHub repository
4. Set Root Directory: `backend`
5. Set Build Command: `pip install -r requirements.txt`
6. Set Start Command: `uvicorn app.api:app --host 0.0.0.0 --port $PORT`
7. Set Environment: Python 3.11
8. Configure `DATA_DIR` if data is not at `../data`
9. Deploy

### Frontend (Vercel)
1. Push code to GitHub
2. Import project in Vercel
3. Set Root Directory: `frontend`
4. Add Environment Variable: `VITE_API_BASE_URL` = your Render backend URL
5. Deploy

---

## Verification Checklist

### Backend
- [x] FastAPI app loads without errors
- [x] Health endpoint responds: `GET /health`
- [x] Search endpoints work: `POST /search`, `POST /search-with-evaluation`
- [x] File upload works: `POST /search-file-with-evaluation`
- [x] Config endpoint works: `GET /config/teacher-model`
- [x] CORS allows frontend requests
- [x] No hardcoded ports or localhost references

### Frontend
- [x] Build completes successfully: `npm run build`
- [x] All API calls use configurable base URL
- [x] No hardcoded localhost in production code
- [x] Environment variables properly prefixed with `VITE_`
- [x] Error handling for API failures

---

## Notes

- **CORS**: Currently allows all origins (`*`). For production, consider restricting to your Vercel domain.
- **Data Size**: If data artifacts are large, consider using cloud storage or Render's persistent disk.
- **Model Downloads**: Sentence-transformers models are downloaded on first use and cached.
- **Startup Time**: Backend may take 30-60 seconds to load models and artifacts on first startup.

---

## Status

✅ **Backend: Deploy-ready on Render**  
✅ **Frontend: Deploy-ready on Vercel**

