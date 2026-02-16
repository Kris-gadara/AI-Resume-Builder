"""
AI Resume Builder – FastAPI Application
==========================================
Production-ready REST API for AI-powered resume generation, ATS
optimisation, job matching, and PDF export.
"""

import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .agent import (
    generate_resume_summary,
    optimize_skills,
    enhance_experience,
    generate_cover_letter,
    extract_ats_keywords,
    generate_recommendations,
)
from .job_matcher import calculate_match_score, get_missing_keywords
from .resume_generator import generate_pdf

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Resume Builder",
    description=(
        "Generate professional, ATS-optimised resumes using Gemini AI. "
        "Includes job-matching scores, PDF export, and keyword analysis."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS – allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static Files & Templates
# ---------------------------------------------------------------------------
_base_dir = os.path.dirname(os.path.dirname(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(_base_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(_base_dir, "templates"))

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class UserData(BaseModel):
    """Input payload for full resume generation."""

    name: str = Field(..., min_length=1, examples=["John Doe"])
    email: str = Field(..., examples=["john.doe@email.com"])
    phone: str = Field("", examples=["+1-555-123-4567"])
    skills: str = Field(
        "",
        examples=["Python, FastAPI, Machine Learning, SQL, Docker"],
    )
    experience: str = Field(
        "",
        examples=[
            "Software Engineer at Tech Corp for 3 years. Built REST APIs and ML pipelines."
        ],
    )
    education: str = Field(
        "",
        examples=["B.S. Computer Science, MIT, 2020"],
    )
    target_role: str = Field(
        "",
        examples=["Senior Python Developer"],
    )
    job_description: str = Field(
        "",
        examples=[
            "Looking for a Python developer with FastAPI experience and ML skills."
        ],
    )


class MatchRequest(BaseModel):
    """Input payload for standalone job-match analysis."""

    resume_text: str = Field(..., min_length=1)
    job_description: str = Field(..., min_length=1)


class PDFRequest(BaseModel):
    """Input payload for standalone PDF generation."""

    name: str
    email: str
    phone: str = ""
    summary: str
    skills: str
    experience: str
    education: str = ""


class ResumeResponse(BaseModel):
    """Full response from /api/generate-resume."""

    summary: str
    optimized_skills: str
    enhanced_experience: str
    job_match_score: float
    matching_keywords: list[str]
    recommendations: list[str]
    pdf_path: str


class MatchResponse(BaseModel):
    """Response from /api/analyze-match."""

    score: float
    top_keywords: list[str]
    missing_keywords: list[str]
    analysis: str


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse, tags=["General"])
async def home(request: Request):
    """Serve the main frontend application."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api", tags=["General"])
async def api_info() -> dict:
    """API welcome page with available endpoints."""
    return {
        "application": "AI Resume Builder",
        "version": "1.0.0",
        "description": "AI-powered resume generation, ATS optimisation & job matching",
        "endpoints": {
            "POST /api/generate-resume": "Generate a full AI-optimised resume + PDF",
            "POST /api/generate-pdf": "Generate a PDF from provided resume data",
            "POST /api/analyze-match": "Analyse resume ↔ job description match",
            "POST /api/extract-keywords": "Extract ATS keywords from a job description",
            "GET  /health": "Health check",
            "GET  /docs": "Interactive API documentation (Swagger UI)",
            "GET  /redoc": "Alternative API documentation (ReDoc)",
        },
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check() -> HealthResponse:
    """Health-check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
    )


# ----- Generate Resume (full pipeline) ------------------------------------


@app.post(
    "/api/generate-resume",
    response_model=ResumeResponse,
    tags=["Resume"],
    summary="Generate a full AI-optimised resume",
)
async def generate_resume(data: UserData) -> ResumeResponse:
    """
    End-to-end pipeline:
    1. Generate professional summary via Gemini.
    2. Optimise skills for ATS.
    3. Enhance experience bullet points.
    4. Calculate job-match score.
    5. Generate recommendations.
    6. Export PDF.
    """
    try:
        # --- AI generation ---------------------------------------------------
        logger.info("Generating resume for %s …", data.name)

        # Provide sensible defaults for empty optional fields
        skills_text = data.skills or "General professional skills"
        experience_text = data.experience or "Professional experience"
        target_text = data.target_role or "Professional"

        # Attempt AI generation with graceful fallbacks
        try:
            summary = generate_resume_summary(data.model_dump())
        except Exception as ai_err:
            logger.warning("AI summary generation failed, using fallback: %s", ai_err)
            summary = (
                f"Experienced professional seeking a {target_text} role. "
                f"Skilled in {skills_text}. {experience_text}"
            )

        try:
            optimized_skills = optimize_skills(skills_text, target_text)
        except Exception as ai_err:
            logger.warning("AI skills optimization failed, using fallback: %s", ai_err)
            optimized_skills = skills_text

        try:
            enhanced_experience = enhance_experience(experience_text, target_text)
        except Exception as ai_err:
            logger.warning("AI experience enhancement failed, using fallback: %s", ai_err)
            enhanced_experience = experience_text

        # --- Job matching -----------------------------------------------------
        resume_text = f"{summary}\n{optimized_skills}\n{enhanced_experience}"
        match_result: dict = {"score": 0.0, "top_keywords": [], "analysis": ""}
        if data.job_description:
            match_result = calculate_match_score(resume_text, data.job_description)

        # --- Recommendations --------------------------------------------------
        recommendations: list[str] = []
        if data.job_description:
            try:
                recommendations = generate_recommendations(
                    summary=summary,
                    skills=optimized_skills,
                    experience=enhanced_experience,
                    job_description=data.job_description,
                    match_score=match_result["score"],
                )
            except Exception as rec_err:
                logger.warning("Recommendation generation failed: %s", rec_err)
                recommendations = [
                    "Strong match! Resume aligns well with job requirements.",
                    "Consider adding more specific metrics and achievements.",
                    "Highlight collaborative projects and team leadership.",
                ]

        # --- PDF generation ---------------------------------------------------
        pdf_path = generate_pdf(
            {
                "name": data.name,
                "email": data.email,
                "phone": data.phone,
                "summary": summary,
                "skills": optimized_skills,
                "experience": enhanced_experience,
                "education": data.education,
            }
        )

        return ResumeResponse(
            summary=summary,
            optimized_skills=optimized_skills,
            enhanced_experience=enhanced_experience,
            job_match_score=match_result["score"],
            matching_keywords=match_result.get("top_keywords", []),
            recommendations=recommendations,
            pdf_path=pdf_path,
        )

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except RuntimeError as re_:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error: {re_}",
        )
    except Exception as exc:
        logger.exception("Unexpected error in generate_resume")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {exc}",
        )


# ----- Generate PDF (standalone) ------------------------------------------


@app.post(
    "/api/generate-pdf",
    tags=["Resume"],
    summary="Generate a PDF from resume data",
)
async def generate_pdf_endpoint(data: PDFRequest) -> dict:
    """Generate a downloadable PDF resume from pre-built content."""
    try:
        pdf_path = generate_pdf(data.model_dump())
        return {
            "message": "PDF generated successfully",
            "pdf_path": pdf_path,
            "filename": os.path.basename(pdf_path),
        }
    except Exception as exc:
        logger.exception("PDF generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {exc}",
        )


# ----- Download PDF -------------------------------------------------------


@app.get(
    "/api/download/{filename}",
    tags=["Resume"],
    summary="Download a generated PDF",
)
async def download_pdf(filename: str) -> FileResponse:
    """Serve a previously generated PDF file for download."""
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    filepath = os.path.join(output_dir, filename)

    if not os.path.isfile(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{filename}' not found.",
        )

    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=filename,
    )


# ----- Analyse Match (standalone) ----------------------------------------


@app.post(
    "/api/analyze-match",
    response_model=MatchResponse,
    tags=["Job Matching"],
    summary="Analyse resume ↔ job description match",
)
async def analyze_match(data: MatchRequest) -> MatchResponse:
    """Calculate similarity score and keyword analysis."""
    try:
        result = calculate_match_score(data.resume_text, data.job_description)
        missing = get_missing_keywords(data.resume_text, data.job_description)

        return MatchResponse(
            score=result["score"],
            top_keywords=result["top_keywords"],
            missing_keywords=missing,
            analysis=result["analysis"],
        )
    except Exception as exc:
        logger.exception("Match analysis failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Match analysis failed: {exc}",
        )


# ----- Extract ATS Keywords (standalone) ---------------------------------


@app.post(
    "/api/extract-keywords",
    tags=["Job Matching"],
    summary="Extract ATS keywords from a job description",
)
async def extract_keywords(job_description: str) -> dict:
    """Use Gemini AI to extract and categorise ATS keywords."""
    if not job_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="job_description must not be empty.",
        )
    try:
        keywords = extract_ats_keywords(job_description)
        return {"keywords": keywords}
    except Exception as exc:
        logger.exception("Keyword extraction failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error: {exc}",
        )
