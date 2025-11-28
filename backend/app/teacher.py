"""
TeacherEvaluator - Uses a pre-trained cross-encoder to evaluate search results.
Acts as a teacher model to compare different search methods.
"""
import torch
from typing import List, Dict
from sentence_transformers import CrossEncoder


class TeacherEvaluator:
    """
    Uses a pre-trained cross-encoder to score query-document pairs.
    Acts as a teacher model to evaluate search method performance.
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize the teacher evaluator with a pre-trained cross-encoder.
        
        Args:
            model_name: Name of the cross-encoder model from sentence-transformers
        """
        self.model_name = model_name  # Store model name for API exposure
        print(f"Loading teacher model: {model_name}...")
        self.model = CrossEncoder(model_name)
        self.model.eval()  # Set to evaluation mode
        print("Teacher model loaded!")
    
    def score_pairs(self, query: str, docs: List[str]) -> List[float]:
        """
        Given a query and a list of doc texts (e.g., title + abstract),
        return a list of teacher relevance scores (higher = more relevant).
        
        Args:
            query: Search query string
            docs: List of document texts (title + abstract or full text)
            
        Returns:
            List of relevance scores (higher = more relevant)
        """
        if not docs:
            return []
        
        # Create query-document pairs
        pairs = [(query, doc) for doc in docs]
        
        # Score pairs using the cross-encoder (automatically uses no_grad internally)
        with torch.no_grad():
            scores = self.model.predict(pairs)
        
        # Convert to list of floats
        if hasattr(scores, 'tolist'):
            return [float(s) for s in scores.tolist()]
        return [float(s) for s in scores]
    
    def evaluate_search_results(
        self, 
        query: str, 
        results: List[Dict],
        text_field: str = "abstract"
    ) -> Dict:
        """
        Evaluate a list of search results for a given query.
        
        Args:
            query: Search query string
            results: List of result dictionaries with at least 'title' and text_field
            text_field: Field to use for document text (default: 'abstract')
            
        Returns:
            Dictionary with evaluation metrics:
            - mean_score: Average relevance score
            - max_score: Maximum relevance score
            - min_score: Minimum relevance score
            - scores: List of individual scores
        """
        if not results:
            return {
                "mean_score": 0.0,
                "max_score": 0.0,
                "min_score": 0.0,
                "scores": []
            }
        
        # Prepare document texts (title + abstract)
        docs = []
        for result in results:
            title = result.get("title", "")
            text = result.get(text_field, "")
            doc_text = f"{title} {text}".strip()
            docs.append(doc_text)
        
        # Get scores from teacher model
        scores = self.score_pairs(query, docs)
        
        if not scores:
            return {
                "mean_score": 0.0,
                "max_score": 0.0,
                "min_score": 0.0,
                "scores": []
            }
        
        return {
            "mean_score": float(sum(scores) / len(scores)),
            "max_score": float(max(scores)),
            "min_score": float(min(scores)),
            "scores": [float(s) for s in scores]
        }

