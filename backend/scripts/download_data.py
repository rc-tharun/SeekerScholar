#!/usr/bin/env python3
"""
Robust artifact downloader for SeekerScholar deployment.

Downloads required data artifacts (df.pkl, bm25.pkl, embeddings.pt, graph.pkl)
from either:
- Direct URLs (via environment variables, preferred)
- Google Drive file IDs (fallback)

Features:
- Idempotent: skips download if file already exists
- Atomic writes: downloads to .tmp then renames
- Progress tracking for large files
- SHA256 verification (optional, via env vars)
- Clear error messages
"""
import os
import sys
import hashlib
import shutil
from pathlib import Path
from typing import Optional, Tuple

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config


def verify_sha256(filepath: str, expected_sha256: str) -> bool:
    """
    Verify file SHA256 hash.
    
    Args:
        filepath: Path to file
        expected_sha256: Expected SHA256 hash (hex string)
        
    Returns:
        True if hash matches, False otherwise
    """
    try:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_hash = sha256_hash.hexdigest()
        return actual_hash.lower() == expected_sha256.lower()
    except Exception as e:
        print(f"  ⚠ Error verifying SHA256: {e}")
        return False


def download_from_url(url: str, output_path: str, expected_sha256: Optional[str] = None) -> Tuple[bool, str]:
    """
    Download file from URL with progress tracking and atomic write.
    
    Args:
        url: Direct download URL
        output_path: Destination file path
        expected_sha256: Optional SHA256 hash for verification
        
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
        
        print(f"  Downloading {os.path.basename(output_path)} from URL...")
        
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
        
        # Verify file size > 0
        if os.path.getsize(tmp_path) == 0:
            os.remove(tmp_path)
            return False, "Downloaded file is empty"
        
        # Verify SHA256 if provided
        if expected_sha256:
            print(f"  Verifying SHA256...")
            if not verify_sha256(tmp_path, expected_sha256):
                os.remove(tmp_path)
                return False, "SHA256 verification failed"
            print(f"  ✓ SHA256 verified")
        
        # Atomic rename
        shutil.move(tmp_path, output_path)
        
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
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
            
            if os.path.getsize(tmp_path) == 0:
                os.remove(tmp_path)
                return False, "Downloaded file is empty"
            
            if expected_sha256:
                if not verify_sha256(tmp_path, expected_sha256):
                    os.remove(tmp_path)
                    return False, "SHA256 verification failed"
            
            shutil.move(tmp_path, output_path)
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
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


def download_from_gdrive(file_id: str, output_path: str, expected_sha256: Optional[str] = None) -> Tuple[bool, str]:
    """
    Download file from Google Drive using gdown.
    
    Args:
        file_id: Google Drive file ID
        output_path: Destination file path
        expected_sha256: Optional SHA256 hash for verification
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        import gdown
    except ImportError:
        print("  Installing gdown...")
        import subprocess
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "gdown"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        import gdown
    
    try:
        # Check if file already exists
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"  ✓ {os.path.basename(output_path)} already exists ({size_mb:.2f} MB), skipping download")
            return True, "File already exists"
        
        print(f"  Downloading {os.path.basename(output_path)} from Google Drive (ID: {file_id})...")
        
        url = f"https://drive.google.com/uc?id={file_id}"
        tmp_path = output_path + ".tmp"
        
        gdown.download(url, tmp_path, quiet=False)
        
        if not os.path.exists(tmp_path):
            return False, "Download completed but file not found"
        
        if os.path.getsize(tmp_path) == 0:
            os.remove(tmp_path)
            return False, "Downloaded file is empty"
        
        # Verify SHA256 if provided
        if expected_sha256:
            print(f"  Verifying SHA256...")
            if not verify_sha256(tmp_path, expected_sha256):
                os.remove(tmp_path)
                return False, "SHA256 verification failed"
            print(f"  ✓ SHA256 verified")
        
        # Atomic rename
        shutil.move(tmp_path, output_path)
        
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✓ Downloaded {os.path.basename(output_path)} ({size_mb:.2f} MB)")
        return True, "Download successful"
        
    except Exception as e:
        # Clean up temp file on error
        tmp_path = output_path + ".tmp"
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False, f"Google Drive download error: {str(e)}"


def main():
    """Main download function."""
    # Get data directory from config
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
    artifacts = {
        "df.pkl": {
            "url_env": "DATA_DF_URL",
            "id_env": "DATA_DF_ID",
            "sha256_env": "DATA_DF_SHA256",
            "gdrive_id": "1DzBhRncYzif5bsbgIDxxgxb05T9mh8-h"
        },
        "bm25.pkl": {
            "url_env": "BM25_INDEX_URL",
            "id_env": "BM25_INDEX_ID",
            "sha256_env": "BM25_INDEX_SHA256",
            "gdrive_id": "1LZBDvDHKCylR2YRzUrywvDaREVXpEc4Y"
        },
        "embeddings.pt": {
            "url_env": "BERT_MODEL_URL",
            "id_env": "BERT_MODEL_ID",
            "sha256_env": "BERT_MODEL_SHA256",
            "gdrive_id": "12e382jL02z56gz5fPOINxBxHYVTBqIBb"
        },
        "graph.pkl": {
            "url_env": "PAGERANK_URL",
            "id_env": "PAGERANK_ID",
            "sha256_env": "PAGERANK_SHA256",
            "gdrive_id": "1KX1Bl54xINL75QOhtA9Av_9SBJxVuYPU"
        }
    }
    
    results = {}
    failed = []
    
    for filename, config in artifacts.items():
        output_path = os.path.join(data_dir, filename)
        url = os.getenv(config["url_env"])
        drive_id = os.getenv(config["id_env"])
        sha256 = os.getenv(config["sha256_env"])
        
        print(f"Processing {filename}...")
        
        # Priority 1: Direct URL from env var
        if url:
            success, message = download_from_url(url, output_path, sha256)
            results[filename] = (success, message)
            if not success:
                failed.append(f"{filename}: {message}")
        
        # Priority 2: Google Drive ID from env var
        elif drive_id:
            success, message = download_from_gdrive(drive_id, output_path, sha256)
            results[filename] = (success, message)
            if not success:
                failed.append(f"{filename}: {message}")
        
        # Priority 3: Default Google Drive ID
        else:
            success, message = download_from_gdrive(config["gdrive_id"], output_path, sha256)
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
    for filename in artifacts.keys():
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

