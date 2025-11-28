"""
Teacher-based ranking metrics for evaluating search model performance.
Pure functions that compute NDCG, Precision, and other ranking metrics.
"""
import math
from typing import List


def compute_teacher_ndcg_at_k(teacher_scores: List[float], k: int) -> float:
    """
    Compute NDCG@k using teacher scores as relevance grades.
    
    Args:
        teacher_scores: List of teacher relevance scores for ranked results
        k: Cutoff rank (typically 10)
        
    Returns:
        NDCG@k score (0.0 to 1.0, higher is better)
    """
    if not teacher_scores or k <= 0:
        return 0.0
    
    # Limit k to the length of scores
    k = min(k, len(teacher_scores))
    
    # Compute DCG@k for the current ranking
    # Using gain = teacher_score (can also use 2^score - 1, but keeping it simple)
    dcg = 0.0
    for i in range(k):
        gain = teacher_scores[i]
        # Discount factor: log2(i+2) because position is 0-indexed
        discount = math.log2(i + 2)
        dcg += gain / discount
    
    # Compute IDCG@k (ideal DCG) by sorting scores descending
    ideal_scores = sorted(teacher_scores, reverse=True)
    idcg = 0.0
    for i in range(k):
        gain = ideal_scores[i]
        discount = math.log2(i + 2)
        idcg += gain / discount
    
    # Avoid division by zero
    if idcg == 0.0:
        return 0.0
    
    return dcg / idcg


def compute_teacher_precision_at_k(
    teacher_scores: List[float], 
    k: int, 
    threshold: float = 0.0
) -> float:
    """
    Compute Precision@k based on teacher score threshold.
    
    Args:
        teacher_scores: List of teacher relevance scores for ranked results
        k: Cutoff rank (typically 10)
        threshold: Relevance threshold (default: 0.0, meaning score > 0 is relevant)
        
    Returns:
        Precision@k score (0.0 to 1.0, higher is better)
    """
    if not teacher_scores or k <= 0:
        return 0.0
    
    # Limit k to the length of scores
    k = min(k, len(teacher_scores))
    
    # Count relevant documents (score > threshold) in top k
    relevant_count = sum(1 for score in teacher_scores[:k] if score > threshold)
    
    # Precision = relevant_count / k
    return relevant_count / k


def get_teacher_top1_score(teacher_scores: List[float]) -> float:
    """
    Get the teacher score of the top-ranked result.
    
    Args:
        teacher_scores: List of teacher relevance scores for ranked results
        
    Returns:
        Score of the first result, or 0.0 if empty
    """
    if not teacher_scores:
        return 0.0
    return float(teacher_scores[0])


def compute_all_teacher_metrics(
    teacher_scores: List[float],
    k: int = 10,
    threshold: float = 0.0
) -> dict:
    """
    Compute all teacher-based metrics for a ranked list.
    
    Args:
        teacher_scores: List of teacher relevance scores for ranked results
        k: Cutoff rank (typically 10)
        threshold: Relevance threshold for precision computation
        
    Returns:
        Dictionary with all computed metrics
    """
    return {
        "teacher_ndcg_at_10": compute_teacher_ndcg_at_k(teacher_scores, k),
        "teacher_precision_at_10": compute_teacher_precision_at_k(teacher_scores, k, threshold),
        "teacher_top1_score": get_teacher_top1_score(teacher_scores),
    }

