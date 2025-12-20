"""
Lazy-loading resource manager for SeekerScholar artifacts.

Loads artifacts on-demand to reduce RAM usage:
- df.parquet: Loaded with pandas (columnar, compressed)
- embeddings.f16.npy: Loaded as numpy memmap (memory-mapped, no full load)
- bm25.pkl: Loaded only when needed
- graph.pkl: Loaded only when needed

Thread-safe singleton pattern with locks to prevent concurrent first-load.
"""
import os
import pickle
import threading
import json
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any
import logging

from app.config import Config

logger = logging.getLogger(__name__)

# Singleton cache
_cache: Dict[str, Any] = {}
_locks: Dict[str, threading.Lock] = {}
_data_dir: Optional[str] = None


def _get_data_dir() -> str:
    """Get data directory path."""
    global _data_dir
    if _data_dir is None:
        _data_dir = Config.get_data_dir()
    return _data_dir


def _get_lock(key: str) -> threading.Lock:
    """Get or create a lock for a resource key."""
    if key not in _locks:
        _locks[key] = threading.Lock()
    return _locks[key]


def get_df() -> pd.DataFrame:
    """
    Lazy-load DataFrame from parquet file.
    
    Returns:
        DataFrame with columns: index, title, abstract
    """
    key = "df"
    lock = _get_lock(key)
    
    if key not in _cache:
        with lock:
            # Double-check after acquiring lock
            if key not in _cache:
                data_dir = _get_data_dir()
                parquet_path = os.path.join(data_dir, "df.parquet")
                
                if not os.path.exists(parquet_path):
                    raise FileNotFoundError(
                        f"DataFrame parquet file not found: {parquet_path}\n"
                        f"Run: python scripts/download_artifacts.py"
                    )
                
                logger.info(f"Loading DataFrame from {parquet_path}...")
                # Load only needed columns for API: title, abstract, and index (for row lookup)
                # This reduces memory usage significantly - Parquet columnar format allows selective loading
                df = pd.read_parquet(
                    parquet_path,
                    engine="pyarrow",
                    columns=["index", "title", "abstract"]  # Only load columns used by _format_result in engine.py
                )
                
                # Set index column as the DataFrame index for efficient iloc lookups
                df = df.set_index("index")
                
                _cache[key] = df
                logger.info(f"✓ Loaded DataFrame: {len(df)} rows, {len(df.columns)} columns")
    
    return _cache[key]


def get_embeddings() -> np.ndarray:
    """
    Lazy-load embeddings as numpy memmap (memory-mapped, no full RAM load).
    
    Returns:
        numpy memmap array of shape (N, D) with dtype float16
    """
    key = "embeddings"
    lock = _get_lock(key)
    
    if key not in _cache:
        with lock:
            # Double-check after acquiring lock
            if key not in _cache:
                data_dir = _get_data_dir()
                npy_path = os.path.join(data_dir, "embeddings.f16.npy")
                meta_path = os.path.join(data_dir, "embeddings.meta.json")
                
                if not os.path.exists(npy_path):
                    raise FileNotFoundError(
                        f"Embeddings file not found: {npy_path}\n"
                        f"Run: python scripts/download_artifacts.py"
                    )
                
                if not os.path.exists(meta_path):
                    raise FileNotFoundError(
                        f"Embeddings metadata not found: {meta_path}\n"
                        f"Run: python scripts/download_artifacts.py"
                    )
                
                # Load metadata
                with open(meta_path, "r") as f:
                    metadata = json.load(f)
                
                shape = tuple(metadata["shape"])
                dtype = np.dtype(metadata["dtype"])
                
                logger.info(f"Loading embeddings from {npy_path}...")
                logger.info(f"  Shape: {shape}, dtype: {dtype}")
                
                # Load as memory-mapped array (doesn't load into RAM)
                embeddings = np.memmap(
                    npy_path,
                    dtype=dtype,
                    mode="r",  # Read-only
                    shape=shape
                )
                
                _cache[key] = embeddings
                logger.info(f"✓ Loaded embeddings as memmap: {shape}")
    
    return _cache[key]


def get_bm25():
    """
    Lazy-load BM25 index from pickle file.
    
    Returns:
        BM25 index object
    """
    key = "bm25"
    lock = _get_lock(key)
    
    if key not in _cache:
        with lock:
            # Double-check after acquiring lock
            if key not in _cache:
                data_dir = _get_data_dir()
                bm25_path = os.path.join(data_dir, "bm25.pkl")
                
                if not os.path.exists(bm25_path):
                    raise FileNotFoundError(
                        f"BM25 index not found: {bm25_path}\n"
                        f"Run: python scripts/download_artifacts.py"
                    )
                
                logger.info(f"Loading BM25 index from {bm25_path}...")
                with open(bm25_path, "rb") as f:
                    bm25 = pickle.load(f)
                
                _cache[key] = bm25
                logger.info("✓ Loaded BM25 index")
    
    return _cache[key]


def get_graph():
    """
    Lazy-load NetworkX graph from pickle file.
    
    Returns:
        NetworkX graph object
    """
    key = "graph"
    lock = _get_lock(key)
    
    if key not in _cache:
        with lock:
            # Double-check after acquiring lock
            if key not in _cache:
                data_dir = _get_data_dir()
                graph_path = os.path.join(data_dir, "graph.pkl")
                
                if not os.path.exists(graph_path):
                    raise FileNotFoundError(
                        f"Graph file not found: {graph_path}\n"
                        f"Run: python scripts/download_artifacts.py"
                    )
                
                logger.info(f"Loading graph from {graph_path}...")
                with open(graph_path, "rb") as f:
                    graph = pickle.load(f)
                
                _cache[key] = graph
                logger.info(f"✓ Loaded graph: {len(graph)} nodes")
    
    return _cache[key]


def is_loaded(key: str) -> bool:
    """
    Check if a resource is loaded in cache.
    
    Args:
        key: Resource key ("df", "embeddings", "bm25", "graph")
        
    Returns:
        True if loaded, False otherwise
    """
    return key in _cache


def get_loaded_status() -> Dict[str, bool]:
    """
    Get status of all resources (loaded or not).
    
    Returns:
        Dictionary mapping resource keys to loaded status
    """
    return {
        "df": is_loaded("df"),
        "embeddings": is_loaded("embeddings"),
        "bm25": is_loaded("bm25"),
        "graph": is_loaded("graph"),
    }


def check_files_exist() -> Dict[str, bool]:
    """
    Check if all required artifact files exist.
    
    Returns:
        Dictionary mapping filenames to existence status
    """
    data_dir = _get_data_dir()
    files = {
        "df.parquet": os.path.exists(os.path.join(data_dir, "df.parquet")),
        "embeddings.f16.npy": os.path.exists(os.path.join(data_dir, "embeddings.f16.npy")),
        "embeddings.meta.json": os.path.exists(os.path.join(data_dir, "embeddings.meta.json")),
        "bm25.pkl": os.path.exists(os.path.join(data_dir, "bm25.pkl")),
        "graph.pkl": os.path.exists(os.path.join(data_dir, "graph.pkl")),
    }
    return files

