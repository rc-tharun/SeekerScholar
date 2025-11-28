"""
PaperSearchEngine - Core search engine for academic papers.
Uses BM25, BERT embeddings, and PageRank for hybrid search.
"""
import pickle
import torch
import pandas as pd
import networkx as nx
import numpy as np
import urllib.parse
import os
from typing import List, Tuple, Dict
from sentence_transformers import SentenceTransformer, util


# PyTorch 2.6+ compatibility fix
_original_torch_load = torch.load
def permissive_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = permissive_load


class PaperSearchEngine:
    """
    Paper search engine using BM25, BERT embeddings, and PageRank.
    All artifacts are precomputed and loaded from disk.
    """
    
    def __init__(self, data_dir: str = "../data"):
        """
        Initialize the search engine by loading all precomputed artifacts.
        
        Args:
            data_dir: Path to directory containing df.pkl, bm25.pkl, 
                     embeddings.pt, and graph.pkl
        """
        print("Loading search engine components...")
        
        # Load DataFrame
        self.df = pd.read_pickle(os.path.join(data_dir, "df.pkl"))
        
        # Load NetworkX graph
        with open(os.path.join(data_dir, "graph.pkl"), "rb") as f:
            self.G = pickle.load(f)
        
        # Load BM25 index
        with open(os.path.join(data_dir, "bm25.pkl"), "rb") as f:
            self.bm25 = pickle.load(f)
        
        # Load BERT model and embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        # Ensure model is on CPU
        self.device = 'cpu'
        self.corpus_embeddings = torch.load(
            os.path.join(data_dir, "embeddings.pt"), 
            weights_only=False,
            map_location='cpu'
        )
        
        print("System Ready!\n")
    
    def _generate_link(self, title: str) -> str:
        """
        Generate an arXiv search link for a given paper title.
        
        Args:
            title: Paper title
            
        Returns:
            URL to arXiv search with quoted title
        """
        safe_title = urllib.parse.quote(f'"{title}"')
        return f"https://arxiv.org/search/?query={safe_title}&searchtype=title"
    
    def _get_bm25(self, query: str, top_k: int = 100) -> List[Tuple[int, float]]:
        """
        Get BM25 keyword-based search results.
        
        Args:
            query: Search query string
            top_k: Number of top results to return
            
        Returns:
            List of (index, score) tuples
        """
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        top_n = np.argsort(scores)[::-1][:top_k]
        return [(int(idx), float(scores[idx])) for idx in top_n if scores[idx] > 0]
    
    def _get_bert(self, query: str, top_k: int = 100) -> List[Tuple[int, float]]:
        """
        Get BERT semantic search results.
        
        Args:
            query: Search query string
            top_k: Number of top results to return
            
        Returns:
            List of (index, score) tuples
        """
        query_embedding = self.model.encode(query, convert_to_tensor=True, device=self.device)
        cos_scores = util.cos_sim(query_embedding, self.corpus_embeddings)[0]
        top_results = torch.topk(cos_scores, k=min(top_k, len(cos_scores)))
        return [
            (int(idx.item()), float(score.item())) 
            for idx, score in zip(top_results.indices, top_results.values)
        ]
    
    def _get_pagerank(self, query: str, top_k: int = 100) -> List[Tuple[int, float]]:
        """
        Get PageRank-based results using query as personalization.
        
        Args:
            query: Search query string
            top_k: Number of top results to return
            
        Returns:
            List of (index, score) tuples
        """
        # Get seeds from BM25
        bm25_results = self._get_bm25(query, top_k=100)
        
        # Build personalization dict
        personalization = {idx: score for idx, score in bm25_results}
        
        if not personalization:
            return []
        
        # Run PageRank with personalization
        pr_scores = nx.pagerank(self.G, alpha=0.85, personalization=personalization)
        
        # Sort and return top_k
        sorted_results = sorted(pr_scores.items(), key=lambda x: x[1], reverse=True)
        return [(int(idx), float(score)) for idx, score in sorted_results[:top_k]]
    
    def _format_result(self, idx: int, score: float, method: str) -> Dict:
        """
        Format a single search result into a dictionary.
        
        Args:
            idx: Index into DataFrame
            score: Relevance score
            method: Search method name
            
        Returns:
            Dictionary with paper information
        """
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
    
    def search_bm25(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Public method for BM25 search.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            List of result dictionaries
        """
        results = self._get_bm25(query, top_k=top_k)
        formatted = [
            self._format_result(idx, score, "bm25") 
            for idx, score in results
        ]
        return [r for r in formatted if r is not None]
    
    def search_bert(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Public method for BERT semantic search.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            List of result dictionaries
        """
        results = self._get_bert(query, top_k=top_k)
        formatted = [
            self._format_result(idx, score, "bert") 
            for idx, score in results
        ]
        return [r for r in formatted if r is not None]
    
    def search_pagerank(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Public method for PageRank search.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            List of result dictionaries
        """
        results = self._get_pagerank(query, top_k=top_k)
        formatted = [
            self._format_result(idx, score, "pagerank") 
            for idx, score in results
        ]
        return [r for r in formatted if r is not None]
    
    def search_hybrid(self, query: str, top_k: int = 10, 
                     w_bm25: float = 0.3, w_bert: float = 0.5, 
                     w_pr: float = 0.2) -> List[Dict]:
        """
        Hybrid search combining BM25, BERT, and PageRank scores.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            w_bm25: Weight for BM25 scores
            w_bert: Weight for BERT scores
            w_pr: Weight for PageRank scores
            
        Returns:
            List of result dictionaries
        """
        # Get results from each method
        bm25_results = self._get_bm25(query, top_k=top_k * 2)
        bert_results = self._get_bert(query, top_k=top_k * 2)
        pr_results = self._get_pagerank(query, top_k=top_k * 2)
        
        # Create score dictionaries
        bm25_scores = {idx: score for idx, score in bm25_results}
        bert_scores = {idx: score for idx, score in bert_results}
        pr_scores = {idx: score for idx, score in pr_results}
        
        # Normalize scores to [0, 1] range
        def normalize_scores(scores_dict):
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
        
        bm25_norm = normalize_scores(bm25_scores)
        bert_norm = normalize_scores(bert_scores)
        pr_norm = normalize_scores(pr_scores)
        
        # Combine scores
        all_indices = set(bm25_scores.keys()) | set(bert_scores.keys()) | set(pr_scores.keys())
        combined_scores = {}
        
        for idx in all_indices:
            score = (
                w_bm25 * bm25_norm.get(idx, 0) +
                w_bert * bert_norm.get(idx, 0) +
                w_pr * pr_norm.get(idx, 0)
            )
            combined_scores[idx] = score
        
        # Sort by combined score and get top_k
        sorted_results = sorted(
            combined_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:top_k]
        
        # Format results
        formatted = [
            self._format_result(idx, score, "hybrid") 
            for idx, score in sorted_results
        ]
        return [r for r in formatted if r is not None]
