#!/usr/bin/env python3
"""
Download artifacts from GitHub Releases for SeekerScholar deployment.

Downloads required data artifacts (df.pkl, bm25.pkl, embeddings.pt, graph.pkl)
from GitHub Releases. Supports overriding URLs via environment variables.

Features:
- Idempotent: skips download if file already exists
- Atomic writes: downloads to .tmp then renames
- Progress tracking for large files
- Validates non-zero file size
- Clear logging
"""
import os
import sys
import shutil
from pathlib import Path
from typing import Tuple

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config

# Default GitHub Releases URLs
DEFAULT_BASE_URL = "https://github.com/rc-tharun/SeekerScholar/releases/download/v1.0.0-models"
DEFAULT_URLS = {
    "bm25.pkl": f"{DEFAULT_BASE_URL}/bm25.pkl",
    "df.pkl": f"{DEFAULT_BASE_URL}/df.pkl",
    "graph.pkl": f"{DEFAULT_BASE_URL}/graph.pkl",
    "embeddings.pt": f"{DEFAULT_BASE_URL}/embeddings.pt",
}

# Environment variable mapping
ENV_VAR_MAP = {
    "bm25.pkl": "BM25_URL",
    "df.pkl": "DF_URL",
    "graph.pkl": "GRAPH_URL",
    "embeddings.pt": "EMBEDDINGS_URL",
}


def download_file(url: str, output_path: str) -> Tuple[bool, str]:
    """
    Download file from URL with progress tracking and atomic write.
    
    Args:
        url: Direct download URL
        output_path: Destination file path
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        import requests
        
        # Check if file already exists
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"  ✓ {os.path.basename(output_path)} already exists ({size_mb:.2f} MB), skipping download")
            return True, "File already exists"
        
        print(f"  Downloading {os.path.basename(output_path)} from {url}...")
        
        # Download to temporary file first (atomic write)
        tmp_path = output_path + ".tmp"
        
        # Stream download with progress
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Check content length for progress
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(tmp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r    Progress: {percent:.1f}% ({downloaded / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB)", end='', flush=True)
        
        print()  # New line after progress
        
        # Validate non-zero file size
        file_size = os.path.getsize(tmp_path)
        if file_size == 0:
            os.remove(tmp_path)
            return False, "Downloaded file is empty"
        
        # Atomic rename
        shutil.move(tmp_path, output_path)
        
        size_mb = file_size / (1024 * 1024)
        print(f"  ✓ Downloaded {os.path.basename(output_path)} ({size_mb:.2f} MB)")
        return True, "Download successful"
        
    except ImportError:
        # Fallback to urllib if requests not available
        try:
            import urllib.request
            print(f"  Downloading {os.path.basename(output_path)} (using urllib)...")
            
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"  ✓ {os.path.basename(output_path)} already exists ({size_mb:.2f} MB), skipping download")
                return True, "File already exists"
            
            tmp_path = output_path + ".tmp"
            urllib.request.urlretrieve(url, tmp_path)
            
            file_size = os.path.getsize(tmp_path)
            if file_size == 0:
                os.remove(tmp_path)
                return False, "Downloaded file is empty"
            
            shutil.move(tmp_path, output_path)
            size_mb = file_size / (1024 * 1024)
            print(f"  ✓ Downloaded {os.path.basename(output_path)} ({size_mb:.2f} MB)")
            return True, "Download successful"
            
        except Exception as e:
            return False, f"Download error: {str(e)}"
    except Exception as e:
        # Clean up temp file on error
        tmp_path = output_path + ".tmp"
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False, f"Download error: {str(e)}"


def main():
    """Main download function."""
    # Get data directory from config (defaults to backend/data)
    data_dir = Config.get_data_dir()
    
    # Ensure directory exists
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"{'='*60}")
    print(f"SeekerScholar Artifact Downloader")
    print(f"{'='*60}")
    print(f"Data directory: {data_dir}")
    print(f"Absolute path: {os.path.abspath(data_dir)}")
    print()
    
    # Define required artifacts
    artifacts = ["bm25.pkl", "df.pkl", "graph.pkl", "embeddings.pt"]
    
    results = {}
    failed = []
    
    for filename in artifacts:
        output_path = os.path.join(data_dir, filename)
        
        # Get URL from environment variable or use default
        env_var = ENV_VAR_MAP.get(filename)
        url = os.getenv(env_var) if env_var else None
        
        if not url:
            url = DEFAULT_URLS.get(filename)
        
        if not url:
            failed.append(f"{filename}: No URL configured")
            results[filename] = (False, "No URL configured")
            continue
        
        print(f"Processing {filename}...")
        success, message = download_file(url, output_path)
        results[filename] = (success, message)
        if not success:
            failed.append(f"{filename}: {message}")
        print()
    
    # Summary
    print(f"{'='*60}")
    print("Download Summary")
    print(f"{'='*60}")
    
    all_success = True
    for filename, (success, message) in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {filename}: {message}")
        if not success:
            all_success = False
    
    print()
    
    # Final check: verify all files exist
    missing_files = []
    for filename in artifacts:
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            missing_files.append(filename)
        else:
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"  ✓ {filename}: {size_mb:.2f} MB")
    
    if missing_files:
        print(f"\n✗ ERROR: Missing required artifacts: {', '.join(missing_files)}")
        print(f"  Data directory: {data_dir}")
        sys.exit(1)
    
    if failed:
        print(f"\n⚠ WARNING: Some downloads had issues:")
        for failure in failed:
            print(f"  - {failure}")
        print("\nHowever, all required files are present. Continuing...")
    
    if all_success and not missing_files:
        print("\n✓ All artifacts downloaded and verified successfully!")
        sys.exit(0)
    else:
        print("\n✗ Some artifacts are missing or failed to download.")
        sys.exit(1)


if __name__ == "__main__":
    main()

