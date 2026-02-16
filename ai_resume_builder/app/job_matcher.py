"""
Job Matcher Module
====================
ML-based resume ↔ job-description similarity scoring using TF-IDF
and cosine similarity.
"""

import re
import logging
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Text Preprocessing
# ---------------------------------------------------------------------------

_STOP_ADDITIONS = {
    "etc", "using", "including", "also", "well", "able", "will",
    "working", "work", "experience", "year", "years", "job",
}


def _preprocess(text: str) -> str:
    """
    Clean and normalise text for vectorisation.

    * Lowercases
    * Strips non-alphanumeric characters (keeps spaces)
    * Collapses whitespace
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Keyword Extraction
# ---------------------------------------------------------------------------

def _extract_top_keywords(
    resume_text: str,
    job_description: str,
    top_n: int = 10,
) -> list[str]:
    """
    Return the *top_n* most important overlapping keywords between the
    resume and the job description, ranked by combined TF-IDF weight.
    """
    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=500,
        ngram_range=(1, 2),
    )
    tfidf_matrix = vectorizer.fit_transform([resume_text, job_description])
    feature_names = vectorizer.get_feature_names_out()

    # Get TF-IDF scores for both documents
    resume_scores = dict(zip(feature_names, tfidf_matrix[0].toarray()[0]))
    job_scores = dict(zip(feature_names, tfidf_matrix[1].toarray()[0]))

    # Keywords present in BOTH documents, scored by combined weight
    common: dict[str, float] = {}
    for word in feature_names:
        r_score = resume_scores.get(word, 0.0)
        j_score = job_scores.get(word, 0.0)
        if r_score > 0 and j_score > 0:
            common[word] = r_score + j_score

    sorted_keywords = sorted(common, key=common.get, reverse=True)  # type: ignore[arg-type]
    return sorted_keywords[:top_n]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_match_score(
    resume_text: str,
    job_description: str,
) -> dict:
    """
    Calculate how well a resume matches a job description.

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
            "score": float          # 0 – 100 percentage
            "top_keywords": list    # overlapping keyword list
            "analysis": str         # human-readable summary
        }
    """
    if not resume_text or not job_description:
        return {
            "score": 0.0,
            "top_keywords": [],
            "analysis": "Insufficient text provided for analysis.",
        }

    # Preprocess
    clean_resume = _preprocess(resume_text)
    clean_job = _preprocess(job_description)

    # TF-IDF + cosine similarity
    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=1000,
        ngram_range=(1, 2),
        sublinear_tf=True,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform([clean_resume, clean_job])
    except ValueError:
        # Edge case: empty vocabulary after stop-word removal
        return {
            "score": 0.0,
            "top_keywords": [],
            "analysis": "Could not extract meaningful content for comparison.",
        }

    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    score = round(float(similarity) * 100, 2)

    # Cap at 100
    score = min(score, 100.0)

    # Top keywords
    top_keywords = _extract_top_keywords(clean_resume, clean_job)

    # Human-readable analysis
    if score >= 80:
        analysis = (
            f"Excellent match ({score}%)! Your resume aligns strongly with the "
            "job requirements. Fine-tune specific metrics and achievements."
        )
    elif score >= 60:
        analysis = (
            f"Good match ({score}%). Your resume covers many requirements. "
            "Consider adding missing keywords and quantifiable results."
        )
    elif score >= 40:
        analysis = (
            f"Moderate match ({score}%). There are notable gaps. Focus on "
            "incorporating more job-specific terminology and relevant experience."
        )
    else:
        analysis = (
            f"Low match ({score}%). Significant gaps exist between your resume "
            "and the job description. Consider tailoring your resume specifically "
            "for this role."
        )

    return {
        "score": score,
        "top_keywords": top_keywords,
        "analysis": analysis,
    }


def get_missing_keywords(
    resume_text: str,
    job_description: str,
    top_n: int = 10,
) -> list[str]:
    """
    Identify important keywords present in the job description but absent
    from the resume.

    Useful for gap analysis and resume improvement suggestions.
    """
    clean_resume = _preprocess(resume_text)
    clean_job = _preprocess(job_description)

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=500,
        ngram_range=(1, 2),
    )

    try:
        tfidf_matrix = vectorizer.fit_transform([clean_resume, clean_job])
    except ValueError:
        return []

    feature_names = vectorizer.get_feature_names_out()
    resume_scores = dict(zip(feature_names, tfidf_matrix[0].toarray()[0]))
    job_scores = dict(zip(feature_names, tfidf_matrix[1].toarray()[0]))

    # Words with high TF-IDF in the JD but zero in the resume
    missing: dict[str, float] = {}
    for word in feature_names:
        if resume_scores.get(word, 0.0) == 0.0 and job_scores.get(word, 0.0) > 0:
            missing[word] = job_scores[word]

    sorted_missing = sorted(missing, key=missing.get, reverse=True)  # type: ignore[arg-type]
    return sorted_missing[:top_n]
