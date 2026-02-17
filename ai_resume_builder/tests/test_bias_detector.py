"""
Tests for Bias Detection Module
=================================
"""

import pytest
from app.bias_detector import (
    scan_for_bias,
    fix_bias_issues,
    validate_resume_content,
    BiasIssue
)


class TestBiasDetection:
    """Test bias scanning functionality."""
    
    def test_clean_text_is_safe(self):
        """Text without bias should pass."""
        text = "Experienced software engineer with strong Python skills"
        result = scan_for_bias(text)
        
        assert result['is_safe'] is True
        assert result['total_issues'] == 0
        assert result['score'] == 100.0
    
    def test_gendered_pronouns_detected(self):
        """Should detect gendered pronouns."""
        text = "He is an excellent engineer with his team"
        result = scan_for_bias(text)
        
        assert result['is_safe'] is False
        assert result['total_issues'] > 0
        assert any(issue['type'] == 'gender' for issue in result['issues'])
    
    def test_age_indicators_detected(self):
        """Should detect age-related terms."""
        text = "Born in 1995, young professional with fresh perspective"
        result = scan_for_bias(text)
        
        assert result['is_safe'] is False
        assert any(issue['type'] == 'age' for issue in result['issues'])
    
    def test_disability_terms_detected(self):
        """Should detect inappropriate disability mentions."""
        text = "Not handicapped, able to perform all duties"
        result = scan_for_bias(text)
        
        assert result['is_safe'] is False
        assert any(issue['type'] == 'disability' for issue in result['issues'])
    
    def test_multiple_issues_detected(self):
        """Should detect multiple types of bias."""
        text = "He is 25 years old and not disabled"
        result = scan_for_bias(text)
        
        assert result['total_issues'] >= 3
        assert result['score'] < 100
    
    def test_empty_text_is_safe(self):
        """Empty text should be considered safe."""
        result = scan_for_bias("")
        assert result['is_safe'] is True
        assert result['total_issues'] == 0


class TestBiasFixes:
    """Test automatic bias fixing."""
    
    def test_fix_gendered_pronouns(self):
        """Should replace gendered pronouns with neutral ones."""
        text = "He completed his work and helped him succeed"
        fixed = fix_bias_issues(text)
        
        assert 'he' not in fixed.lower()
        assert 'his' not in fixed.lower()
        assert 'him' not in fixed.lower()
        assert 'they' in fixed.lower() or 'their' in fixed.lower()
    
    def test_fix_preserves_meaning(self):
        """Fixes should preserve the general meaning."""
        text = "She led her team to success"
        fixed = fix_bias_issues(text)
        
        # Should still mention leading team
        assert 'led' in fixed.lower() or 'lead' in fixed.lower()
        assert 'team' in fixed.lower()
    
    def test_fix_empty_text(self):
        """Should handle empty text."""
        fixed = fix_bias_issues("")
        assert fixed == ""
    
    def test_fix_age_references(self):
        """Should remove age references."""
        text = "25 years old engineer"
        fixed = fix_bias_issues(text)
        
        assert 'years old' not in fixed.lower()


class TestResumeValidation:
    """Test full resume content validation."""
    
    def test_validate_clean_resume(self):
        """Resume without bias should validate."""
        summary = "Experienced engineer with Python skills"
        skills = "Python, JavaScript, Docker"
        experience = "Led development of REST API"
        
        result = validate_resume_content(summary, skills, experience)
        
        assert result['overall_safe'] is True
        assert result['total_issues'] == 0
    
    def test_validate_biased_resume(self):
        """Resume with bias should be flagged."""
        summary = "He is an experienced engineer"
        skills = "Young, energetic, Python skills"
        experience = "Led his team to success"
        
        result = validate_resume_content(summary, skills, experience)
        
        assert result['overall_safe'] is False
        assert result['total_issues'] > 0
        assert result['summary']['total_issues'] > 0
    
    def test_validation_provides_section_details(self):
        """Should provide details for each section."""
        summary = "Engineer with skills"
        skills = "He has Python skills"  # Has bias
        experience = "Led team successfully"
        
        result = validate_resume_content(summary, skills, experience)
        
        assert 'summary' in result
        assert 'skills' in result
        assert 'experience' in result
        assert result['skills']['total_issues'] > 0
        assert result['summary']['total_issues'] == 0


class TestBiasIssueClass:
    """Test BiasIssue class."""
    
    def test_bias_issue_to_dict(self):
        """Should convert to dictionary correctly."""
        issue = BiasIssue(
            type='gender',
            term='he',
            severity='medium',
            suggestion='Use gender-neutral language'
        )
        
        result = issue.to_dict()
        
        assert result['type'] == 'gender'
        assert result['term'] == 'he'
        assert result['severity'] == 'medium'
        assert 'suggestion' in result


class TestBiasScoring:
    """Test bias scoring system."""
    
    def test_score_decreases_with_issues(self):
        """Score should decrease as issues increase."""
        clean_text = "Software engineer with Python experience"
        biased_text = "He is 25 years old and works on his projects"
        
        clean_result = scan_for_bias(clean_text)
        biased_result = scan_for_bias(biased_text)
        
        assert clean_result['score'] > biased_result['score']
    
    def test_score_minimum_is_zero(self):
        """Score should not go below 0."""
        # Text with many issues
        text = "He is 25 years old, she is his manager, they are both young graduates from 1995"
        result = scan_for_bias(text)
        
        assert result['score'] >= 0
