"""
SearchEngine - High-performance 2-stage retrieval pipeline.
Stage 1: Fast BM25 candidate generation (always runs first)
Stage 2: Optional lightweight re-ranking on small candidate set only

All document-side data is precomputed; only query-side processing happens per request.
"""
import pickle
import torch
import pandas as pd
import networkx as nx
import numpy as np
import urllib.parse
import os
import logging
from typing import List, Tuple, Dict, Optional
from sentence_transformers import SentenceTransformer, util
import hashlib

from app.config import Config

# Set up logging for performance profiling
logger = logging.getLogger(__name__)


# PyTorch 2.6+ compatibility fix
_original_torch_load = torch.load
def permissive_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = permissive_load


def normalize_and_truncate_query(text: str, max_chars: int = None) -> str:
    """
    Normalize and truncate query text for fast processing.
    
    Args:
        text: Raw query text
        max_chars: Maximum characters (defaults to Config.MAX_QUERY_LENGTH)
        
    Returns:
        Normalized and truncated query
    """
    if max_chars is None:
        max_chars = Config.MAX_QUERY_LENGTH
    
    # Basic normalization: strip, lowercase, collapse whitespace
    text = text.strip()
    text = " ".join(text.split())
    
    # Truncate if needed
    if len(text) > max_chars:
        text = text[:max_chars]
    
    return text


class SearchEngine:
    """
    High-performance search engine with 2-stage retrieval:
    1. Fast BM25 candidate generation (always runs first)
    2. Optional lightweight re-ranking on small candidate set only
    
    All document-side artifacts are precomputed and loaded once at initialization.
    """
    
    def __init__(self, data_dir: Optional[str] = None, cache_size: Optional[int] = None):
        """
        Initialize the search engine by loading all precomputed artifacts.
        
        Args:
            data_dir: Path to directory containing df.pkl, bm25.pkl, 
                     embeddings.pt, and graph.pkl (defaults to Config.get_data_dir())
            cache_size: Size of LRU cache for search results (defaults to Config.CACHE_SIZE)
        """
        if data_dir is None:
            data_dir = Config.get_data_dir()
        if cache_size is None:
            cache_size = Config.CACHE_SIZE
        
        logger.info("Loading search engine components...")
        
        # Load DataFrame
        self.df = pd.read_pickle(os.path.join(data_dir, "df.pkl"))
        logger.info(f"Loaded DataFrame with {len(self.df)} papers")
        
        # Load NetworkX graph
        with open(os.path.join(data_dir, "graph.pkl"), "rb") as f:
            self.G = pickle.load(f)
        logger.info(f"Loaded graph with {len(self.G)} nodes")
        
        # Load BM25 index (primary candidate generator)
        with open(os.path.join(data_dir, "bm25.pkl"), "rb") as f:
            self.bm25 = pickle.load(f)
        logger.info("Loaded BM25 index")
        
        # Load BERT model and embeddings (for re-ranking only)
        self.model = SentenceTransformer(Config.BERT_MODEL_NAME)
        self.device = 'cpu'
        self.corpus_embeddings = torch.load(
            os.path.join(data_dir, "embeddings.pt"), 
            weights_only=False,
            map_location='cpu'
        )
        logger.info(f"Loaded BERT model '{Config.BERT_MODEL_NAME}' and {len(self.corpus_embeddings)} embeddings")
        
        # Precompute PageRank scores for all nodes (for fast re-weighting)
        logger.info("Precomputing PageRank scores...")
        self.pagerank_scores = nx.pagerank(self.G, alpha=0.85, max_iter=50, tol=1e-4)
        logger.info("Precomputed PageRank scores")
        
        # Initialize LRU cache for search results
        self._cache = {}
        self._cache_order = []
        self._cache_size = cache_size
        
        logger.info("Search engine ready!")
    
    def _get_cache_key(self, query: str, method: str, top_k: int) -> str:
        """Generate cache key for a search query."""
        key_str = f"{method}:{top_k}:{query.lower().strip()}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """Get result from cache if available."""
        if cache_key in self._cache:
            self._cache_order.remove(cache_key)
            self._cache_order.append(cache_key)
            return self._cache[cache_key]
        return None
    
    def _add_to_cache(self, cache_key: str, results: List[Dict]):
        """Add result to cache with LRU eviction."""
        if cache_key in self._cache:
            self._cache_order.remove(cache_key)
            self._cache_order.append(cache_key)
            return
        
        if len(self._cache) >= self._cache_size:
            lru_key = self._cache_order.pop(0)
            del self._cache[lru_key]
        
        self._cache[cache_key] = results
        self._cache_order.append(cache_key)
    
    def _generate_link(self, title: str) -> str:
        """Generate an arXiv search link for a given paper title."""
        safe_title = urllib.parse.quote(f'"{title}"')
        return f"https://arxiv.org/search/?query={safe_title}&searchtype=title"
    
    def _format_result(self, idx: int, score: float, method: str) -> Optional[Dict]:
        """Format a single search result into a dictionary."""
        if idx >= len(self.df):
            return None
        
        row = self.df.iloc[idx]
        return {
            "id": int(idx),
            "title": str(row.get("title", "")),
            "abstract": str(row.get("abstract", "")),
            "link": self._generate_link(str(row.get("title", ""))),
            "score": float(score),
            "method": method
        }
    
    def _get_bm25_candidates(self, query: str, candidate_pool_size: int = None) -> List[Tuple[int, float]]:
        """
        Stage 1: Fast BM25 candidate generation.
        This is the primary fast retrieval step that runs for ALL methods.
        
        Args:
            query: Search query string (normalized)
            candidate_pool_size: Number of candidates to retrieve (defaults to Config.CANDIDATE_POOL_SIZE)
            
        Returns:
            List of (index, bm25_score) tuples
        """
        if candidate_pool_size is None:
            candidate_pool_size = Config.CANDIDATE_POOL_SIZE
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores (fast - precomputed index)
        scores = self.bm25.get_scores(tokenized_query)
        top_n = np.argsort(scores)[::-1][:candidate_pool_size]
        
        results = [(int(idx), float(scores[idx])) for idx in top_n if scores[idx] > 0]
        
        return results
    
    def _rerank_with_bert(self, query: str, candidates: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """
        Stage 2: BERT-based re-ranking on candidate set only.
        Encodes query once, then computes similarity with candidate embeddings only.
        
        Args:
            query: Search query string (normalized)
            candidates: List of (index, bm25_score) tuples from Stage 1
            
        Returns:
            List of (index, bert_score) tuples
        """
        if not candidates:
            return []
        
        # Encode query once
        query_embedding = self.model.encode(
            query,
            convert_to_tensor=True,
            device=self.device,
            show_progress_bar=False,
            normalize_embeddings=True
        )
        
        # Get embeddings for candidates only (not full corpus!)
        candidate_indices = [idx for idx, _ in candidates]
        candidate_embeddings = self.corpus_embeddings[candidate_indices]
        
        # Compute cosine similarity (query vs candidates only)
        cos_scores = util.cos_sim(query_embedding, candidate_embeddings)[0]
        
        # Create (index, score) pairs
        results = [
            (int(idx), float(score.item()))
            for idx, score in zip(candidate_indices, cos_scores)
        ]
        
        return results
    
    def _rerank_with_pagerank(self, candidates: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """
        Stage 2: PageRank-based re-weighting on candidate set only.
        Uses precomputed PageRank scores for fast re-weighting.
        
        Args:
            candidates: List of (index, bm25_score) tuples from Stage 1
            
        Returns:
            List of (index, combined_score) tuples
        """
        if not candidates:
            return []
        
        # Combine BM25 score with precomputed PageRank score
        combined_scores = []
        for idx, bm25_score in candidates:
            pr_score = self.pagerank_scores.get(idx, 0.0)
            # Simple linear combination (can be tuned)
            combined_score = 0.7 * bm25_score + 0.3 * pr_score
            combined_scores.append((idx, combined_score))
        
        return combined_scores
    
    def _rerank_hybrid(self, query: str, candidates: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """
        Stage 2: Hybrid re-ranking combining BM25, BERT, and PageRank on candidate set only.
        
        Args:
            query: Search query string (normalized)
            candidates: List of (index, bm25_score) tuples from Stage 1
            
        Returns:
            List of (index, hybrid_score) tuples
        """
        if not candidates:
            return []
        
        # Get BERT scores for candidates
        bert_results = self._rerank_with_bert(query, candidates)
        bert_scores = {idx: score for idx, score in bert_results}
        
        # Get BM25 and PageRank scores
        bm25_scores = {idx: score for idx, score in candidates}
        pr_scores = {idx: self.pagerank_scores.get(idx, 0.0) for idx, _ in candidates}
        
        # Normalize scores to [0, 1] range
        def normalize(scores_dict):
            if not scores_dict:
                return {}
            max_score = max(scores_dict.values()) if scores_dict.values() else 1.0
            min_score = min(scores_dict.values()) if scores_dict.values() else 0.0
            if max_score == min_score:
                return {k: 0.5 for k in scores_dict.keys()}
            return {
                k: (v - min_score) / (max_score - min_score)
                for k, v in scores_dict.items()
            }
        
        bm25_norm = normalize(bm25_scores)
        bert_norm = normalize(bert_scores)
        pr_norm = normalize(pr_scores)
        
        # Combine with config weights
        weights = Config.HYBRID_WEIGHTS
        combined_scores = []
        for idx, _ in candidates:
            score = (
                weights["bm25"] * bm25_norm.get(idx, 0) +
                weights["bert"] * bert_norm.get(idx, 0) +
                weights["pagerank"] * pr_norm.get(idx, 0)
            )
            combined_scores.append((idx, score))
        
        return combined_scores
    
    def search_bm25(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        BM25 search - Stage 1 only (no re-ranking).
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            List of result dictionaries
        """
        # Check cache
        cache_key = self._get_cache_key(query, "bm25", top_k)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Normalize query
        normalized_query = normalize_and_truncate_query(query)
        
        # Stage 1: Get BM25 candidates
        candidates = self._get_bm25_candidates(normalized_query, candidate_pool_size=top_k)
        
        # Format results
        formatted = [
            self._format_result(idx, score, "bm25")
            for idx, score in candidates[:top_k]
        ]
        formatted = [r for r in formatted if r is not None]
        
        # Cache and return
        self._add_to_cache(cache_key, formatted)
        return formatted
    
    def search_bert(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        BERT search - Stage 1 (BM25 candidates) + Stage 2 (BERT re-ranking).
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            List of result dictionaries
        """
        # Check cache
        cache_key = self._get_cache_key(query, "bert", top_k)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Normalize query
        normalized_query = normalize_and_truncate_query(query)
        
        # Stage 1: Get BM25 candidates
        candidates = self._get_bm25_candidates(normalized_query)
        
        # Stage 2: Re-rank with BERT (on candidates only!)
        reranked = self._rerank_with_bert(normalized_query, candidates)
        
        # Sort by BERT score and take top_k
        reranked.sort(key=lambda x: x[1], reverse=True)
        
        # Format results
        formatted = [
            self._format_result(idx, score, "bert")
            for idx, score in reranked[:top_k]
        ]
        formatted = [r for r in formatted if r is not None]
        
        # Cache and return
        self._add_to_cache(cache_key, formatted)
        return formatted
    
    def search_pagerank(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        PageRank search - Stage 1 (BM25 candidates) + Stage 2 (PageRank re-weighting).
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            List of result dictionaries
        """
        # Check cache
        cache_key = self._get_cache_key(query, "pagerank", top_k)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Normalize query
        normalized_query = normalize_and_truncate_query(query)
        
        # Stage 1: Get BM25 candidates
        candidates = self._get_bm25_candidates(normalized_query)
        
        # Stage 2: Re-weight with PageRank (on candidates only!)
        reranked = self._rerank_with_pagerank(candidates)
        
        # Sort by combined score and take top_k
        reranked.sort(key=lambda x: x[1], reverse=True)
        
        # Format results
        formatted = [
            self._format_result(idx, score, "pagerank")
            for idx, score in reranked[:top_k]
        ]
        formatted = [r for r in formatted if r is not None]
        
        # Cache and return
        self._add_to_cache(cache_key, formatted)
        return formatted
    
    def search_hybrid(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Hybrid search - Stage 1 (BM25 candidates) + Stage 2 (Hybrid re-ranking).
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            List of result dictionaries
        """
        # Check cache
        cache_key = self._get_cache_key(query, "hybrid", top_k)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Normalize query
        normalized_query = normalize_and_truncate_query(query)
        
        # Stage 1: Get BM25 candidates
        candidates = self._get_bm25_candidates(normalized_query)
        
        # Stage 2: Hybrid re-ranking (on candidates only!)
        reranked = self._rerank_hybrid(normalized_query, candidates)
        
        # Sort by hybrid score and take top_k
        reranked.sort(key=lambda x: x[1], reverse=True)
        
        # Format results
        formatted = [
            self._format_result(idx, score, "hybrid")
            for idx, score in reranked[:top_k]
        ]
        formatted = [r for r in formatted if r is not None]
        
        # Cache and return
        self._add_to_cache(cache_key, formatted)
        return formatted


# Backward compatibility alias
PaperSearchEngine = SearchEngine
