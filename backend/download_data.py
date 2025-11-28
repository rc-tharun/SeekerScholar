#!/usr/bin/env python3
"""
Python script to download data files for deployment.
Downloads from Google Drive using gdown, or from URLs if provided.
"""
import os
import sys
import subprocess
from pathlib import Path

def download_from_gdrive(file_id: str, output_path: str):
    """Download a file from Google Drive using gdown."""
    try:
        import gdown
        url = f"https://drive.google.com/uc?id={file_id}"
        print(f"Downloading {output_path} from Google Drive (ID: {file_id})...")
        gdown.download(url, output_path, quiet=False)
        print(f"✓ Downloaded {output_path}")
        return True
    except ImportError:
        print("gdown not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])
        import gdown
        url = f"https://drive.google.com/uc?id={file_id}"
        print(f"Downloading {output_path} from Google Drive (ID: {file_id})...")
        gdown.download(url, output_path, quiet=False)
        print(f"✓ Downloaded {output_path}")
        return True
    except Exception as e:
        print(f"✗ Error downloading {output_path}: {e}")
        return False

def download_from_url(url: str, output_path: str):
    """Download a file from a direct URL."""
    try:
        import urllib.request
        print(f"Downloading {output_path} from {url}...")
        urllib.request.urlretrieve(url, output_path)
        print(f"✓ Downloaded {output_path}")
        return True
    except Exception as e:
        print(f"✗ Error downloading {output_path}: {e}")
        return False

def main():
    # For Render: if DATA_DIR not set, use absolute path relative to script location
    default_data_dir = os.getenv("DATA_DIR")
    if not default_data_dir:
        # Try ../data relative to script, or ./data in current directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_data_dir = os.path.join(script_dir, "..", "data")
        # Normalize path
        default_data_dir = os.path.normpath(default_data_dir)
    
    data_dir = os.getenv("DATA_DIR", default_data_dir)
    # Ensure absolute path
    if not os.path.isabs(data_dir):
        data_dir = os.path.abspath(data_dir)
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    print(f"Data directory: {data_dir}")
    print(f"Data directory (absolute): {os.path.abspath(data_dir)}")
    
    # Google Drive file IDs (configured for SeekerScholar)
    gdrive_files = {
        "df.pkl": "1DzBhRncYzif5bsbgIDxxgxb05T9mh8-h",
        "bm25.pkl": "1LZBDvDHKCylR2YRzUrywvDaREVXpEc4Y",
        "embeddings.pt": "12e382jL02z56gz5fPOINxBxHYVTBqIBb",
        "graph.pkl": "1KX1Bl54xINL75QOhtA9Av_9SBJxVuYPU",
    }
    
    # Option 1: Try environment variables first (for custom URLs)
    env_files = {
        "df.pkl": os.getenv("DATA_DF_URL"),
        "bm25.pkl": os.getenv("DATA_BM25_URL"),
        "embeddings.pt": os.getenv("DATA_EMBEDDINGS_URL"),
        "graph.pkl": os.getenv("DATA_GRAPH_URL"),
    }
    
    downloaded = False
    failed = []
    
    for filename, env_url in env_files.items():
        output_path = os.path.join(data_dir, filename)
        
        # If environment variable URL is provided, use it
        if env_url:
            if download_from_url(env_url, output_path):
                downloaded = True
            else:
                failed.append(filename)
        # Otherwise, use Google Drive file ID
        elif filename in gdrive_files:
            if download_from_gdrive(gdrive_files[filename], output_path):
                downloaded = True
            else:
                failed.append(filename)
    
    if failed:
        print(f"\n✗ Failed to download: {', '.join(failed)}")
        sys.exit(1)
    
    if downloaded:
        print("\n✓ All data files downloaded successfully!")
        # Verify files exist
        for filename in gdrive_files.keys():
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                print(f"  {filename}: {size_mb:.2f} MB")
    else:
        print("No data files were downloaded.")
        sys.exit(1)

if __name__ == "__main__":
    main()

