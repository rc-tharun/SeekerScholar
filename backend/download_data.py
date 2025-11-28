#!/usr/bin/env python3
"""
Python script to download data files for deployment.
Can be used as an alternative to the shell script.
"""
import os
import sys
import urllib.request
from pathlib import Path

def download_file(url: str, output_path: str):
    """Download a file from URL to output path."""
    print(f"Downloading {output_path} from {url}...")
    urllib.request.urlretrieve(url, output_path)
    print(f"✓ Downloaded {output_path}")

def main():
    data_dir = os.getenv("DATA_DIR", "../data")
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    
    # Option 1: Download from environment variables (recommended for Render)
    files = {
        "df.pkl": os.getenv("DATA_DF_URL"),
        "bm25.pkl": os.getenv("DATA_BM25_URL"),
        "embeddings.pt": os.getenv("DATA_EMBEDDINGS_URL"),
        "graph.pkl": os.getenv("DATA_GRAPH_URL"),
    }
    
    downloaded = False
    for filename, url in files.items():
        if url:
            output_path = os.path.join(data_dir, filename)
            download_file(url, output_path)
            downloaded = True
    
    if not downloaded:
        print("No data URLs provided. Set environment variables:")
        print("  DATA_DF_URL, DATA_BM25_URL, DATA_EMBEDDINGS_URL, DATA_GRAPH_URL")
        print("\nAlternatively, upload data files directly to Render's persistent disk.")
        sys.exit(1)
    
    print("\n✓ All data files downloaded successfully!")

if __name__ == "__main__":
    main()

