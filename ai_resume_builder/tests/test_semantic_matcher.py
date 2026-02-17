"""
Tests for Semantic Matching Module
====================================
"""

import pytest
from app.semantic_matcher import (
    calculate_semantic_match,
    calculate_hybrid_match_score
)


class TestSemanticMatcher:
    """Test transformer-based semantic matching."""
    
    SAMPLE_RESUME = (
        "ML engineer with 5 years of Python experience. "
        "Built machine learning pipelines with FastAPI and Docker. "
        "Deployed models on AWS."
    )
    
    SAMPLE_JOB = (
        "Looking for Machine Learning engineer with Python expertise. "
        "Experience with FastAPI, cloud deployment (AWS), and containerization required."
    )
    
    def test_semantic_match_identical(self):
        """Identical texts should have very high similarity."""
        text = "Python developer with machine learning experience"
        result = calculate_semantic_match(text, text)
        
        assert 'semantic_score' in result
        assert result['semantic_score'] >= 95
        assert result['embedding_distance'] <= 0.05
    
    def test_semantic_match_synonyms(self):
        """Should recognize ML = Machine Learning."""
        resume = "ML engineer with Python expertise"
        job = "Machine Learning engineer with Python experience"
        result = calculate_semantic_match(resume, job)
        
        # Should have high similarity despite different wording
        assert result['semantic_score'] >= 60
    
    def test_semantic_match_empty_input(self):
        """Empty inputs should return 0 score."""
        result = calculate_semantic_match("", "")
        assert result['semantic_score'] == 0.0
        assert result['embedding_distance'] == 1.0
    
    def test_semantic_match_unrelated(self):
        """Completely unrelated texts should have low similarity."""
        resume = "Chef with culinary arts degree, 10 years cooking Italian food"
        job = "Quantum physics researcher needed with PhD in theoretical physics"
        result = calculate_semantic_match(resume, job)
        
        assert result['semantic_score'] < 40
    
    def test_hybrid_match_returns_all_fields(self):
        """Hybrid match should return all required fields."""
        result = calculate_hybrid_match_score(self.SAMPLE_RESUME, self.SAMPLE_JOB)
        
        assert 'score' in result
        assert 'semantic_score' in result
        assert 'keyword_score' in result
        assert 'top_keywords' in result
        assert 'analysis' in result
        
        assert isinstance(result['score'], (int, float))
        assert isinstance(result['top_keywords'], list)
        assert isinstance(result['analysis'], str)
    
    def test_hybrid_score_in_range(self):
        """Hybrid score should be 0-100."""
        result = calculate_hybrid_match_score(self.SAMPLE_RESUME, self.SAMPLE_JOB)
        assert 0 <= result['score'] <= 100
    
    def test_hybrid_better_than_individual(self):
        """Hybrid should combine strengths of both approaches."""
        result = calculate_hybrid_match_score(self.SAMPLE_RESUME, self.SAMPLE_JOB)
        
        # Both scores should contribute
        assert result['semantic_score'] > 0
        assert result['keyword_score'] > 0
        
        # Hybrid should be in between
        min_score = min(result['semantic_score'], result['keyword_score'])
        max_score = max(result['semantic_score'], result['keyword_score'])
        assert min_score <= result['score'] <= max_score + 10  # Allow some tolerance
    
    def test_high_match_analysis(self):
        """High match should have positive analysis."""
        # Create very similar texts
        text = "Senior Python developer with FastAPI and ML experience"
        result = calculate_hybrid_match_score(text, text)
        
        assert result['score'] >= 80
        assert 'excellent' in result['analysis'].lower() or 'strong' in result['analysis'].lower()
    
    def test_low_match_analysis(self):
        """Low match should suggest improvements."""
        resume = "Junior web designer with HTML/CSS skills"
        job = "Senior backend Python engineer with 10 years experience"
        result = calculate_hybrid_match_score(resume, job)
        
        assert result['score'] < 50
        assert 'gap' in result['analysis'].lower() or 'tailor' in result['analysis'].lower()


class TestSemanticMatcherEdgeCases:
    """Test edge cases and error handling."""
    
    def test_very_long_text(self):
        """Should handle long texts without errors."""
        long_text = "Python developer " * 1000
        result = calculate_semantic_match(long_text, long_text)
        assert result['semantic_score'] > 50
    
    def test_special_characters(self):
        """Should handle special characters."""
        resume = "C++ developer with @cloud & #devops skills!!!"
        job = "C++ engineer needed with cloud and devops experience"
        result = calculate_semantic_match(resume, job)
        assert result['semantic_score'] > 0
    
    def test_mixed_case(self):
        """Should be case-insensitive."""
        resume = "PYTHON DEVELOPER"
        job = "python developer"
        result = calculate_semantic_match(resume, job)
        assert result['semantic_score'] >= 80
