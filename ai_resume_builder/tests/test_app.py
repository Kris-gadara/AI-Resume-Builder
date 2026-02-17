"""
AI Resume Builder – Test Suite
================================
Unit and integration tests for the core modules.

Run with:
    pytest tests/test_app.py -v
"""

import os
import sys
import pytest

# Ensure the project root is on the path so imports work when running
# pytest from the ai_resume_builder directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ======================================================================
# job_matcher tests (no external API required)
# ======================================================================

from app.job_matcher import calculate_match_score, get_missing_keywords


class TestJobMatcher:
    """Tests for the TF-IDF + cosine-similarity job matcher."""

    SAMPLE_RESUME = (
        "Experienced Python developer with expertise in FastAPI, machine learning, "
        "REST APIs, Docker, AWS, and PostgreSQL. Built scalable microservices and "
        "data pipelines. Led agile teams and delivered production systems."
    )
    SAMPLE_JOB = (
        "We are looking for a Senior Python Developer with strong experience "
        "in FastAPI, machine learning, cloud deployment on AWS, and database "
        "management with PostgreSQL. REST API design is essential."
    )

    def test_match_returns_dict(self):
        result = calculate_match_score(self.SAMPLE_RESUME, self.SAMPLE_JOB)
        assert isinstance(result, dict)
        assert "score" in result
        assert "top_keywords" in result
        assert "analysis" in result

    def test_score_range(self):
        result = calculate_match_score(self.SAMPLE_RESUME, self.SAMPLE_JOB)
        assert 0 <= result["score"] <= 100

    def test_high_similarity(self):
        """A highly overlapping resume+JD should score above 10 (TF-IDF on short texts)."""
        result = calculate_match_score(self.SAMPLE_RESUME, self.SAMPLE_JOB)
        assert result["score"] > 10

    def test_low_similarity(self):
        """Completely unrelated texts should score low."""
        result = calculate_match_score(
            "Chef with 10 years of culinary experience in Italian cuisine.",
            "Looking for a quantum physics researcher with PhD.",
        )
        assert result["score"] < 20

    def test_identical_texts(self):
        """Identical texts should produce a perfect or near-perfect score."""
        result = calculate_match_score(self.SAMPLE_JOB, self.SAMPLE_JOB)
        assert result["score"] >= 95

    def test_empty_input(self):
        result = calculate_match_score("", "")
        assert result["score"] == 0.0

    def test_keywords_are_list(self):
        result = calculate_match_score(self.SAMPLE_RESUME, self.SAMPLE_JOB)
        assert isinstance(result["top_keywords"], list)

    def test_missing_keywords(self):
        missing = get_missing_keywords(
            "Python developer with Flask experience",
            "Senior Python developer with FastAPI, Docker, Kubernetes, and AWS",
        )
        assert isinstance(missing, list)
        # "docker" or "kubernetes" should appear as missing
        lower_missing = [m.lower() for m in missing]
        assert any(
            kw in " ".join(lower_missing)
            for kw in ("docker", "kubernetes", "fastapi")
        )


# ======================================================================
# resume_generator tests (no external API required)
# ======================================================================

from app.resume_generator import generate_pdf


class TestResumeGenerator:
    """Tests for PDF generation."""

    SAMPLE_DATA = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "+1-555-000-0000",
        "summary": "Experienced software engineer with a focus on Python.",
        "skills": "Python, FastAPI, Docker",
        "experience": (
            "Software Engineer | Acme Corp | 2021-2024\n"
            "• Built REST APIs serving 1M requests/day\n"
            "• Led migration to microservices architecture"
        ),
        "education": "B.S. Computer Science, State University, 2020",
    }

    def test_pdf_created(self, tmp_path):
        """A PDF file should be created at the returned path."""
        path = generate_pdf(self.SAMPLE_DATA, filename=f"test_resume_{id(self)}")
        assert os.path.isfile(path)
        assert path.endswith(".pdf")
        # Cleanup
        os.remove(path)

    def test_pdf_non_empty(self, tmp_path):
        """The generated PDF should have a non-trivial file size."""
        path = generate_pdf(self.SAMPLE_DATA, filename=f"test_size_{id(self)}")
        assert os.path.getsize(path) > 500  # should be several KB
        os.remove(path)

    def test_pdf_minimal_data(self):
        """Should work even with minimal data (only name)."""
        path = generate_pdf(
            {"name": "Minimal", "email": "", "phone": "", "summary": "",
             "skills": "", "experience": "", "education": ""},
            filename=f"test_minimal_{id(self)}",
        )
        assert os.path.isfile(path)
        os.remove(path)


# ======================================================================
# FastAPI endpoint tests (no Gemini key needed for non-AI endpoints)
# ======================================================================

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """Integration tests for non-AI API endpoints."""

    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        # Root now serves HTML frontend
        assert "AI Resume Builder" in resp.text

    def test_api_info(self):
        resp = client.get("/api")
        assert resp.status_code == 200
        data = resp.json()
        assert "application" in data
        assert data["application"] == "AI Resume Builder"

    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_analyze_match(self):
        resp = client.post(
            "/api/analyze-match",
            json={
                "resume_text": "Python developer with FastAPI and ML skills",
                "job_description": "Looking for Python FastAPI developer with ML",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "score" in data
        assert 0 <= data["score"] <= 100

    def test_analyze_match_empty(self):
        resp = client.post(
            "/api/analyze-match",
            json={"resume_text": "", "job_description": "some job"},
        )
        # Pydantic validation should reject empty strings
        assert resp.status_code == 422

    def test_generate_pdf_endpoint(self):
        resp = client.post(
            "/api/generate-pdf",
            json={
                "name": "API Test User",
                "email": "api@test.com",
                "phone": "",
                "summary": "Test summary paragraph.",
                "skills": "Python, Testing",
                "experience": "Software Engineer | Test Co | 2023\n• Tested things",
                "education": "B.S. CS, 2022",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pdf_path" in data
        # Cleanup generated file
        if os.path.isfile(data["pdf_path"]):
            os.remove(data["pdf_path"])

    def test_download_missing_file(self):
        resp = client.get("/api/download/nonexistent.pdf")
        assert resp.status_code == 404


# ======================================================================
# prompts sanity checks
# ======================================================================

from app.prompts import (
    RESUME_SUMMARY_PROMPT,
    SKILLS_OPTIMIZATION_PROMPT,
    EXPERIENCE_ENHANCEMENT_PROMPT,
)


class TestPrompts:
    """Basic sanity checks for prompt templates."""

    def test_summary_prompt_has_placeholders(self):
        assert "{name}" in RESUME_SUMMARY_PROMPT
        assert "{skills}" in RESUME_SUMMARY_PROMPT
        assert "{target_role}" in RESUME_SUMMARY_PROMPT

    def test_skills_prompt_has_placeholders(self):
        assert "{skills}" in SKILLS_OPTIMIZATION_PROMPT
        assert "{target_role}" in SKILLS_OPTIMIZATION_PROMPT

    def test_experience_prompt_has_placeholders(self):
        assert "{experience}" in EXPERIENCE_ENHANCEMENT_PROMPT
        assert "{target_role}" in EXPERIENCE_ENHANCEMENT_PROMPT

    def test_prompt_formatting(self):
        """Prompts should format without errors when given valid data."""
        result = RESUME_SUMMARY_PROMPT.format(
            name="Alice",
            skills="Python",
            experience="3 years",
            target_role="Developer",
        )
        assert "Alice" in result


class TestMetricsEndpoint:
    """Test new monitoring metrics endpoint."""
    
    def test_metrics_endpoint_exists(self):
        """Metrics endpoint should be accessible."""
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/metrics")
        
        # Should return Prometheus metrics format
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
    
    def test_metrics_contains_api_metrics(self):
        """Metrics should include API request metrics."""
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/metrics")
        
        content = response.text
        # Should contain our custom metrics
        assert "api_" in content or "gemini_" in content or "HELP" in content
