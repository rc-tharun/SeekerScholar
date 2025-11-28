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

### Option 1: Google Drive (Already Configured) ✅

All files are available on Google Drive and will be automatically downloaded during Render deployment:

- **df.pkl**: https://drive.google.com/file/d/1DzBhRncYzif5bsbgIDxxgxb05T9mh8-h/view?usp=drive_link
- **bm25.pkl**: https://drive.google.com/file/d/1LZBDvDHKCylR2YRzUrywvDaREVXpEc4Y/view?usp=drive_link
- **embeddings.pt**: https://drive.google.com/file/d/12e382jL02z56gz5fPOINxBxHYVTBqIBb/view?usp=drive_link
- **graph.pkl**: https://drive.google.com/file/d/1KX1Bl54xINL75QOhtA9Av_9SBJxVuYPU/view?usp=drive_link

### Option 2: Generate Locally

You can regenerate these files using the `ISR_Project.ipynb` notebook.

### Option 3: Download Manually

1. Download from Google Drive links above
2. Place them in the `data/` directory at the repository root
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

The files are automatically downloaded during the build process using the `download_data.py` script, which uses the pre-configured Google Drive file IDs.

## File Descriptions

- **df.pkl**: Pandas DataFrame containing paper metadata (titles, abstracts, etc.)
- **bm25.pkl**: Precomputed BM25 search index
- **embeddings.pt**: Precomputed BERT embeddings for all papers
- **graph.pkl**: NetworkX citation graph for PageRank computation

