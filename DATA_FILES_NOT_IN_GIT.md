# Data Files Not in Git Repository

The following files are **excluded from Git** due to GitHub's 100MB file size limit:

## Excluded Files

| File Name | Size | Status | Location |
|-----------|------|--------|----------|
| `data/df.pkl` | **400 MB** | ❌ Excluded | Exceeds 100MB limit |
| `data/embeddings.pt` | **263 MB** | ❌ Excluded | Exceeds 100MB limit |
| `data/bm25.pkl` | **222 MB** | ❌ Excluded | Exceeds 100MB limit |
| `data/graph.pkl` | **54 MB** | ❌ Excluded | Over 50MB recommendation |

**Total Size:** ~939 MB

## Why They're Excluded

These files are excluded by `.gitignore` rules:
- `data/*.pkl` - Excludes all .pkl files
- `data/*.pt` - Excludes all .pt files

## Where to Get These Files

### Option 1: GitHub Releases (Automatically Downloaded) ✅

All files are available on GitHub Releases (tag: `v1.0.0-models`) and are automatically downloaded during deployment:

- **df.pkl**: https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/df.pkl
- **bm25.pkl**: https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/bm25.pkl
- **embeddings.pt**: https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/embeddings.pt
- **graph.pkl**: https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models/graph.pkl

The `scripts/download_artifacts.py` script automatically downloads these during the Render build process.

### Option 2: Generate Locally

You can regenerate these files using the `ISR_Project.ipynb` notebook.

### Option 3: Download Manually

1. Download from GitHub Releases links above
2. Place them in the `backend/data/` directory (or set `DATA_DIR` env var)
3. Ensure file permissions allow reading

## For Local Development

If you have these files locally, they should be in:
```
seekerscholar/
└── data/
    ├── df.pkl          (400 MB)
    ├── bm25.pkl        (222 MB)
    ├── embeddings.pt   (263 MB)
    └── graph.pkl       (54 MB)
```

## For Render Deployment

The files are automatically downloaded during the **BUILD** command using the `scripts/download_artifacts.py` script, which downloads from GitHub Releases. This ensures the server can bind to `$PORT` immediately in the START command, preventing "No open ports detected" errors.

## File Descriptions

- **df.pkl**: Pandas DataFrame containing paper metadata (titles, abstracts, etc.)
- **bm25.pkl**: Precomputed BM25 search index
- **embeddings.pt**: Precomputed BERT embeddings for all papers
- **graph.pkl**: NetworkX citation graph for PageRank computation











