#!/bin/bash
# Script to download data files for deployment
# This script can be customized to download from your preferred storage solution

set -e

DATA_DIR="${DATA_DIR:-../data}"
mkdir -p "$DATA_DIR"

echo "Downloading data files..."

# Option 1: Download from Google Drive (using gdown)
# Install gdown: pip install gdown
# Uncomment and replace with your Google Drive file IDs:
# gdown --id YOUR_FILE_ID -O "$DATA_DIR/df.pkl"
# gdown --id YOUR_FILE_ID -O "$DATA_DIR/bm25.pkl"
# gdown --id YOUR_FILE_ID -O "$DATA_DIR/embeddings.pt"
# gdown --id YOUR_FILE_ID -O "$DATA_DIR/graph.pkl"

# Option 2: Download from S3
# Uncomment and configure with your S3 bucket:
# aws s3 cp s3://your-bucket/data/df.pkl "$DATA_DIR/df.pkl"
# aws s3 cp s3://your-bucket/data/bm25.pkl "$DATA_DIR/bm25.pkl"
# aws s3 cp s3://your-bucket/data/embeddings.pt "$DATA_DIR/embeddings.pt"
# aws s3 cp s3://your-bucket/data/graph.pkl "$DATA_DIR/graph.pkl"

# Option 3: Download from a direct URL (if you host them somewhere)
# Uncomment and replace with your URLs:
# curl -L "https://your-domain.com/data/df.pkl" -o "$DATA_DIR/df.pkl"
# curl -L "https://your-domain.com/data/bm25.pkl" -o "$DATA_DIR/bm25.pkl"
# curl -L "https://your-domain.com/data/embeddings.pt" -o "$DATA_DIR/embeddings.pt"
# curl -L "https://your-domain.com/data/graph.pkl" -o "$DATA_DIR/graph.pkl"

# Option 4: Use environment variables for download URLs
if [ -n "$DATA_DF_URL" ]; then
    echo "Downloading df.pkl from $DATA_DF_URL"
    curl -L "$DATA_DF_URL" -o "$DATA_DIR/df.pkl"
fi

if [ -n "$DATA_BM25_URL" ]; then
    echo "Downloading bm25.pkl from $DATA_BM25_URL"
    curl -L "$DATA_BM25_URL" -o "$DATA_DIR/bm25.pkl"
fi

if [ -n "$DATA_EMBEDDINGS_URL" ]; then
    echo "Downloading embeddings.pt from $DATA_EMBEDDINGS_URL"
    curl -L "$DATA_EMBEDDINGS_URL" -o "$DATA_DIR/embeddings.pt"
fi

if [ -n "$DATA_GRAPH_URL" ]; then
    echo "Downloading graph.pkl from $DATA_GRAPH_URL"
    curl -L "$DATA_GRAPH_URL" -o "$DATA_DIR/graph.pkl"
fi

echo "Data download complete!"
ls -lh "$DATA_DIR"

