"""
Semantic Job Matching using Transformer Embeddings
====================================================
Modern ML approach replacing TF-IDF with BERT-based embeddings.
"""

import logging
from typing import Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Load model once at module level (singleton pattern)
_model = None


def _get_model() -> SentenceTransformer:
    """Lazy load the sentence transformer model."""
    global _model
    if _model is None:
        logger.info("Loading sentence-transformers model...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, 80MB model
    return _model


def calculate_semantic_match(
    resume_text: str,
    job_description: str,
) -> Dict[str, float]:
    """
    Calculate semantic similarity using transformer embeddings.
    
    This understands that 'ML' and 'Machine Learning' are similar,
    unlike TF-IDF which treats them as different terms.
    
    Parameters
    ----------
    resume_text : str
        The full resume text (summary + skills + experience).
    job_description : str
        The full job posting text.
    
    Returns
    -------
    dict
        {
            'semantic_score': float (0-100),
            'embedding_distance': float
        }
    """
    if not resume_text or not job_description:
        return {
            'semantic_score': 0.0,
            'embedding_distance': 1.0,
        }
    
    model = _get_model()
    
    # Generate embeddings (384-dimensional vectors)
    embeddings = model.encode([resume_text, job_description])
    
    # Calculate cosine similarity
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    score = float(similarity) * 100
    
    return {
        'semantic_score': min(score, 100.0),
        'embedding_distance': float(1 - similarity),
    }


def calculate_hybrid_match_score(
    resume_text: str,
    job_description: str,
) -> dict:
    """
    Combine semantic (transformer) and keyword (TF-IDF) scoring.
    
    Best of both worlds:
    - Semantic understanding of meaning
    - Keyword matching for specific terms
    
    Parameters
    ----------
    resume_text : str
        The full resume text (summary + skills + experience).
    job_description : str
        The full job posting text.
    
    Returns
    -------
    dict
        {
            'score': float (0-100),
            'semantic_score': float,
            'keyword_score': float,
            'top_keywords': list[str],
            'analysis': str
        }
    """
    from .job_matcher import calculate_match_score as tfidf_match
    
    # Get both scores
    semantic = calculate_semantic_match(resume_text, job_description)
    tfidf = tfidf_match(resume_text, job_description)
    
    # Weighted combination (60% semantic, 40% keywords)
    hybrid_score = (
        semantic['semantic_score'] * 0.6 +
        tfidf['score'] * 0.4
    )
    
    # Generate analysis
    if hybrid_score >= 80:
        analysis = (
            f"Excellent match ({hybrid_score:.1f}%)! Strong semantic alignment "
            f"(semantic: {semantic['semantic_score']:.1f}%, keywords: {tfidf['score']:.1f}%). "
            f"Your resume aligns well with the job requirements."
        )
    elif hybrid_score >= 60:
        analysis = (
            f"Good match ({hybrid_score:.1f}%). "
            f"Semantic similarity: {semantic['semantic_score']:.1f}%, "
            f"Keyword overlap: {tfidf['score']:.1f}%. "
            f"Consider adding more relevant keywords to improve further."
        )
    elif hybrid_score >= 40:
        analysis = (
            f"Moderate match ({hybrid_score:.1f}%). "
            f"Semantic: {semantic['semantic_score']:.1f}%, Keywords: {tfidf['score']:.1f}%. "
            f"Focus on incorporating more job-specific terminology and relevant experience."
        )
    else:
        analysis = (
            f"Low match ({hybrid_score:.1f}%). "
            f"Significant gaps exist. Consider tailoring your resume more closely "
            f"to the job description with relevant keywords and context."
        )
    
    return {
        'score': round(hybrid_score, 2),
        'semantic_score': round(semantic['semantic_score'], 2),
        'keyword_score': round(tfidf['score'], 2),
        'top_keywords': tfidf.get('top_keywords', []),
        'analysis': analysis,
    }
