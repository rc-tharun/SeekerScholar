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
    Check if all required data files exist (lite format).
    
    Args:
        data_dir: Directory to check
        
    Returns:
        Tuple of (all_exist: bool, missing_files: List[str])
    """
    required_files = ["df.parquet", "bm25.pkl", "embeddings.f16.npy", "embeddings.meta.json", "graph.pkl"]
    missing_files = []
    
    for filename in required_files:
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            missing_files.append(filename)
    
    return len(missing_files) == 0, missing_files


def download_data_files(data_dir: str) -> bool:
    """
    Download data files from GitHub Releases if they don't exist.
    This function is deprecated - use scripts/download_artifacts.py instead.
    
    Args:
        data_dir: Directory to download files to
        
    Returns:
        True if all files downloaded successfully, False otherwise
    """
    print(f"⚠ WARNING: download_data_files() is deprecated.")
    print(f"Please use scripts/download_artifacts.py for artifact downloads.")
    print(f"Checking if files already exist in: {data_dir}")
    
    # Just check if files exist, don't download
    all_exist, missing_files = check_data_files(data_dir)
    if all_exist:
        print("✓ All data files found!")
        return True
    else:
        print(f"✗ Missing files: {', '.join(missing_files)}")
        print(f"  Run: python3 scripts/download_artifacts.py")
        return False


def ensure_data_files(data_dir: str) -> None:
    """
    DEPRECATED: This function is no longer used.
    Artifacts should be downloaded during BUILD command using scripts/download_artifacts.py.
    
    This function is kept for backward compatibility but does nothing.
    It will NOT raise FileNotFoundError to avoid crashing at import time.
    
    Args:
        data_dir: Directory containing data files
    """
    # Do nothing - artifacts should be downloaded during BUILD command
    # This prevents crashes at import time
    pass





