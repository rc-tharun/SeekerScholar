"""
Configuration management for SeekerScholar backend.
Handles data paths, model settings, and performance limits.
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Application configuration."""
    
    # Data directory configuration
    DATA_DIR: Optional[str] = None
    
    # Model configuration
    BERT_MODEL_NAME: str = "all-MiniLM-L6-v2"
    
    # Performance limits
    MAX_QUERY_LENGTH: int = 2048  # Characters - truncate queries longer than this
    MAX_TOP_K: int = 100
    MIN_TOP_K: int = 1
    DEFAULT_TOP_K: int = 10
    
    # 2-stage retrieval settings
    CANDIDATE_POOL_SIZE: int = 300  # BM25 candidates to generate before re-ranking
    
    # Search method weights (for hybrid search)
    HYBRID_WEIGHTS = {
        "bm25": 0.3,
        "bert": 0.5,
        "pagerank": 0.2
    }
    
    # Cache configuration
    CACHE_SIZE: int = 256
    
    @classmethod
    def get_data_dir(cls) -> str:
        """
        Get the data directory path, resolving relative paths correctly.
        
        Priority:
        1. DATA_DIR environment variable (if set)
        2. data (within backend directory, default)
        
        Returns:
            Absolute path to data directory
        """
        if cls.DATA_DIR:
            return cls.DATA_DIR
        
        # Get backend root (where this file is located)
        backend_root = Path(__file__).parent.parent
        
        # Check environment variable
        data_dir_env = os.getenv("DATA_DIR")
        if data_dir_env:
            if os.path.isabs(data_dir_env):
                cls.DATA_DIR = data_dir_env
                return cls.DATA_DIR
            # Relative path - resolve from backend root
            resolved = backend_root / data_dir_env
            cls.DATA_DIR = str(resolved.resolve())
            return cls.DATA_DIR
        
        # Default: data (within backend directory)
        cls.DATA_DIR = str((backend_root / "data").resolve())
        return cls.DATA_DIR
    
    @classmethod
    def artifact_path(cls, filename: str) -> str:
        """
        Get the full path to an artifact file.
        
        Args:
            filename: Name of the artifact file (e.g., "bm25.pkl")
            
        Returns:
            Absolute path to the artifact file
        """
        data_dir = cls.get_data_dir()
        return os.path.join(data_dir, filename)
    
    @classmethod
    def validate_top_k(cls, top_k: int) -> None:
        """Validate top_k parameter."""
        if not (cls.MIN_TOP_K <= top_k <= cls.MAX_TOP_K):
            raise ValueError(
                f"top_k must be between {cls.MIN_TOP_K} and {cls.MAX_TOP_K}"
            )
    
    @classmethod
    def validate_method(cls, method: str) -> None:
        """Validate search method."""
        valid_methods = ["bm25", "bert", "pagerank", "hybrid"]
        if method not in valid_methods:
            raise ValueError(
                f"Invalid method: {method}. Must be one of: {', '.join(valid_methods)}"
            )


# Initialize data directory on import
Config.get_data_dir()
