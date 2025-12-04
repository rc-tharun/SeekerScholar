"""
Data loading and initialization utilities.
Handles loading precomputed data files and optional downloading if missing.
"""
import os
import sys
from pathlib import Path
from typing import List

from app.config import Config


def check_data_files(data_dir: str) -> tuple[bool, List[str]]:
    """
    Check if all required data files exist.
    
    Args:
        data_dir: Directory to check
        
    Returns:
        Tuple of (all_exist: bool, missing_files: List[str])
    """
    required_files = ["df.pkl", "bm25.pkl", "embeddings.pt", "graph.pkl"]
    missing_files = []
    
    for filename in required_files:
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            missing_files.append(filename)
    
    return len(missing_files) == 0, missing_files


def download_data_files(data_dir: str) -> bool:
    """
    Download data files from Google Drive if they don't exist.
    
    Args:
        data_dir: Directory to download files to
        
    Returns:
        True if all files downloaded successfully, False otherwise
    """
    print(f"Downloading data files to: {data_dir}")
    
    # Ensure directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # Import gdown
        try:
            import gdown
        except ImportError:
            print("Installing gdown...")
            import subprocess
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "gdown"], 
                capture_output=True
            )
            import gdown
        
        # Google Drive file IDs
        gdrive_files = {
            "df.pkl": "1DzBhRncYzif5bsbgIDxxgxb05T9mh8-h",
            "bm25.pkl": "1LZBDvDHKCylR2YRzUrywvDaREVXpEc4Y",
            "embeddings.pt": "12e382jL02z56gz5fPOINxBxHYVTBqIBb",
            "graph.pkl": "1KX1Bl54xINL75QOhtA9Av_9SBJxVuYPU",
        }
        
        downloaded = []
        failed = []
        
        for filename, file_id in gdrive_files.items():
            output_path = os.path.join(data_dir, filename)
            url = f"https://drive.google.com/uc?id={file_id}"
            
            try:
                print(f"Downloading {filename}...")
                gdown.download(url, output_path, quiet=False)
                
                if os.path.exists(output_path):
                    size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    print(f"✓ {filename}: {size_mb:.2f} MB")
                    downloaded.append(filename)
                else:
                    print(f"✗ {filename}: Download completed but file not found")
                    failed.append(filename)
            except Exception as e:
                print(f"✗ {filename}: Error - {e}")
                failed.append(filename)
        
        if failed:
            print(f"\nFailed to download: {', '.join(failed)}")
            return False
        
        print(f"\n✓ Successfully downloaded all {len(downloaded)} files!")
        return True
        
    except Exception as e:
        print(f"ERROR during download: {e}")
        import traceback
        traceback.print_exc()
        return False


def ensure_data_files(data_dir: str) -> None:
    """
    Ensure all required data files exist, downloading if necessary.
    
    Args:
        data_dir: Directory containing data files
        
    Raises:
        FileNotFoundError: If files are missing and download fails
    """
    all_exist, missing_files = check_data_files(data_dir)
    
    if all_exist:
        print("✓ All data files found!")
        return
    
    print(f"\n{'='*60}")
    print(f"MISSING DATA FILES: {', '.join(missing_files)}")
    print(f"{'='*60}\n")
    
    # Try to download missing files
    success = download_data_files(data_dir)
    
    if not success:
        print("\nERROR: Download failed!")
    
    # Check again
    all_exist, still_missing = check_data_files(data_dir)
    
    if not all_exist:
        print(f"\n{'='*60}")
        print(f"ERROR: Could not obtain files: {', '.join(still_missing)}")
        print(f"{'='*60}")
        print(f"Data directory: {data_dir}")
        if os.path.exists(data_dir):
            print(f"Directory contents: {os.listdir(data_dir)}")
        else:
            print("Data directory does not exist!")
        raise FileNotFoundError(f"Data files not found: {', '.join(still_missing)}")
    
    print("✓ All data files available!")


