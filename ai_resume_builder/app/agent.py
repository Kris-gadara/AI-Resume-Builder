"""
Gemini AI Agent Module
========================
Handles all interactions with Google's Gemini API for resume content generation.
Includes retry logic, error handling, and response parsing.
"""

import os
import time
import logging
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv

from .prompts import (
    RESUME_SUMMARY_PROMPT,
    SKILLS_OPTIMIZATION_PROMPT,
    EXPERIENCE_ENHANCEMENT_PROMPT,
    COVER_LETTER_PROMPT,
    ATS_KEYWORD_PROMPT,
    RESUME_RECOMMENDATIONS_PROMPT,
)
from .monitoring import track_gemini_call
from .cache import cached
from .bias_detector import scan_for_bias, fix_bias_issues

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
MAX_RETRIES: int = 3
RETRY_DELAY: float = 2.0  # seconds


def _configure_gemini() -> None:
    """Configure the Gemini API client with the stored API key."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY is not set. Please add a valid key to your .env file. "
            "Get one free at https://aistudio.google.com/"
        )
    genai.configure(api_key=GEMINI_API_KEY)


def _get_model() -> genai.GenerativeModel:
    """Return a configured Gemini GenerativeModel instance."""
    _configure_gemini()
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config={
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 2048,
        },
    )


# ---------------------------------------------------------------------------
# Core helper – call Gemini with retry
# ---------------------------------------------------------------------------

def _call_gemini(prompt: str) -> str:
    """
    Send *prompt* to Gemini and return the response text.

    Retries up to MAX_RETRIES times on transient failures.
    """
    model = _get_model()
    last_error: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = model.generate_content(prompt)

            # Handle blocked / empty responses
            if not response or not response.text:
                raise ValueError("Gemini returned an empty response.")

            return response.text.strip()

        except Exception as exc:
            last_error = exc
            logger.warning(
                "Gemini API attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)  # exponential-ish back-off

    raise RuntimeError(
        f"Gemini API failed after {MAX_RETRIES} attempts. Last error: {last_error}"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@track_gemini_call('generate_resume_summary')
@cached(prefix='resume_summary', ttl=3600)
def generate_resume_summary(user_data: dict) -> str:
    """
    Generate a professional resume summary using Gemini.

    Parameters
    ----------
    user_data : dict
        Must contain keys: name, skills, experience, target_role.

    Returns
    -------
    str
        A 3-4 sentence ATS-optimized professional summary.
    """
    prompt = RESUME_SUMMARY_PROMPT.format(
        name=user_data.get("name", ""),
        skills=user_data.get("skills", ""),
        experience=user_data.get("experience", ""),
        target_role=user_data.get("target_role", ""),
    )
    result = _call_gemini(prompt)
    
    # Check for bias and fix if needed
    bias_check = scan_for_bias(result)
    if not bias_check['is_safe']:
        logger.warning(f"Bias detected in summary: {bias_check['total_issues']} issues")
        result = fix_bias_issues(result)
    
    return result


@track_gemini_call('optimize_skills')
@cached(prefix='optimize_skills', ttl=3600)
def optimize_skills(skills: str, target_role: str = "") -> str:
    """
    Reorganize and enhance a raw skills list for ATS compatibility.

    Parameters
    ----------
    skills : str
        Comma-separated or free-text list of skills.
    target_role : str
        The job title the user is targeting.

    Returns
    -------
    str
        Formatted, categorized skills section.
    """
    prompt = SKILLS_OPTIMIZATION_PROMPT.format(
        skills=skills,
        target_role=target_role,
    )
    return _call_gemini(prompt)


@track_gemini_call('enhance_experience')
@cached(prefix='enhance_experience', ttl=3600)
def enhance_experience(experience: str, target_role: str = "") -> str:
    """
    Convert raw experience text into achievement-oriented bullet points.

    Parameters
    ----------
    experience : str
        Free-text work experience description.
    target_role : str
        The job title the user is targeting.

    Returns
    -------
    str
        Formatted experience section with quantified achievements.
    """
    prompt = EXPERIENCE_ENHANCEMENT_PROMPT.format(
        experience=experience,
        target_role=target_role,
    )
    result = _call_gemini(prompt)
    
    # Check for bias and fix if needed
    bias_check = scan_for_bias(result)
    if not bias_check['is_safe']:
        logger.warning(f"Bias detected in experience: {bias_check['total_issues']} issues")
        result = fix_bias_issues(result)
    
    return result


@track_gemini_call('generate_cover_letter')
@cached(prefix='cover_letter', ttl=3600)
def generate_cover_letter(user_data: dict) -> str:
    """
    Generate a professional cover letter tailored to a specific job.

    Parameters
    ----------
    user_data : dict
        Must contain: name, skills, experience, target_role, company,
        job_description.

    Returns
    -------
    str
        A 3-paragraph cover letter.
    """
    prompt = COVER_LETTER_PROMPT.format(
        name=user_data.get("name", ""),
        skills=user_data.get("skills", ""),
        experience=user_data.get("experience", ""),
        target_role=user_data.get("target_role", ""),
        company=user_data.get("company", "the company"),
        job_description=user_data.get("job_description", ""),
    )
    return _call_gemini(prompt)


@track_gemini_call('extract_ats_keywords')
@cached(prefix='ats_keywords', ttl=7200)
def extract_ats_keywords(job_description: str) -> str:
    """
    Extract important ATS keywords from a job description.

    Parameters
    ----------
    job_description : str
        Full text of the job posting.

    Returns
    -------
    str
        Categorized keywords list.
    """
    prompt = ATS_KEYWORD_PROMPT.format(job_description=job_description)
    return _call_gemini(prompt)


@track_gemini_call('generate_recommendations')
def generate_recommendations(
    summary: str,
    skills: str,
    experience: str,
    job_description: str,
    match_score: float,
) -> list[str]:
    """
    Generate actionable recommendations to improve resume-job fit.

    Returns
    -------
    list[str]
        A list of recommendation strings.
    """
    prompt = RESUME_RECOMMENDATIONS_PROMPT.format(
        summary=summary,
        skills=skills,
        experience=experience,
        job_description=job_description,
        match_score=round(match_score, 1),
    )
    raw = _call_gemini(prompt)

    # Parse numbered list into individual items
    recommendations: list[str] = []
    for line in raw.split("\n"):
        line = line.strip()
        if line and line[0].isdigit():
            # Strip leading number + punctuation (e.g. "1. " or "1) ")
            cleaned = line.lstrip("0123456789.)- ").strip()
            if cleaned:
                recommendations.append(cleaned)
    return recommendations if recommendations else [raw]
