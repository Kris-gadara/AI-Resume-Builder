"""
AI Bias Detection for Resume Content
======================================
Scan for problematic language related to age, gender, disability.
"""

import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Bias keyword databases
GENDERED_TERMS = {
    'male': ['he', 'his', 'him', 'himself', 'guy', 'guys', 'men', 'man', 'manly'],
    'female': ['she', 'her', 'hers', 'herself', 'gal', 'gals', 'women', 'woman'],
}

AGE_INDICATORS = [
    r'\b(19|20)\d{2}\b',  # Birth years (1900-2099)
    r'\b\d{2}\s*years?\s*old\b',
    r'\byoung\b',
    r'\byouthful\b',
    r'\bold\b',
    r'\belderly\b',
    r'\bage\b\s*\d+',
]

DISABILITY_TERMS = [
    'handicapped', 'disabled', 'wheelchair', 'blind', 'deaf',
    'mental illness', 'bipolar', 'schizophrenia', 'crazy',
    'insane', 'retarded', 'mentally challenged'
]

# Additional problematic terms
PROBLEMATIC_TERMS = [
    'overqualified',  # Age discrimination code
    'digital native',  # Age bias (implies younger)
    'recent graduate',  # Age indicator
]


class BiasIssue:
    """Represents a detected bias issue."""
    def __init__(self, type: str, term: str, severity: str, suggestion: str):
        self.type = type
        self.term = term
        self.severity = severity
        self.suggestion = suggestion
    
    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'term': self.term,
            'severity': self.severity,
            'suggestion': self.suggestion
        }


def scan_for_bias(text: str) -> Dict[str, any]:
    """
    Scan text for potential bias issues.
    
    Parameters
    ----------
    text : str
        The text to scan for bias.
    
    Returns
    -------
    dict
        {
            'is_safe': bool,
            'issues': List[BiasIssue],
            'score': float (0-100, higher is better),
            'total_issues': int
        }
    """
    if not text:
        return {
            'is_safe': True,
            'issues': [],
            'score': 100.0,
            'total_issues': 0
        }
    
    issues: List[BiasIssue] = []
    text_lower = text.lower()
    
    # Check for gendered language
    for gender, terms in GENDERED_TERMS.items():
        for term in terms:
            if re.search(rf'\b{term}\b', text_lower):
                issues.append(BiasIssue(
                    type='gender',
                    term=term,
                    severity='medium',
                    suggestion=f"Use gender-neutral language instead of '{term}' (e.g., 'they', 'their')"
                ))
    
    # Check for age indicators
    for pattern in AGE_INDICATORS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            issues.append(BiasIssue(
                type='age',
                term=str(match),
                severity='high',
                suggestion="Avoid mentioning age, birth year, or age-related terms"
            ))
    
    # Check for disability terms
    for term in DISABILITY_TERMS:
        if term in text_lower:
            issues.append(BiasIssue(
                type='disability',
                term=term,
                severity='high',
                suggestion=f"Avoid mentioning '{term}' - focus on skills and achievements"
            ))
    
    # Check for other problematic terms
    for term in PROBLEMATIC_TERMS:
        if term in text_lower:
            issues.append(BiasIssue(
                type='discriminatory',
                term=term,
                severity='medium',
                suggestion=f"Remove '{term}' - may indicate bias"
            ))
    
    # Calculate safety score
    is_safe = len(issues) == 0
    score = max(0, 100 - (len(issues) * 15))  # -15 points per issue
    
    if issues:
        logger.warning(f"Detected {len(issues)} bias issues in generated content")
        for issue in issues:
            logger.debug(f"  - {issue.type}: {issue.term}")
    
    return {
        'is_safe': is_safe,
        'issues': [i.to_dict() for i in issues],
        'score': score,
        'total_issues': len(issues)
    }


def fix_bias_issues(text: str) -> str:
    """
    Attempt to automatically fix common bias issues.
    
    Parameters
    ----------
    text : str
        The text to fix.
    
    Returns
    -------
    str
        Text with bias issues fixed (where possible).
    """
    if not text:
        return text
    
    fixed = text
    
    # Replace gendered pronouns with neutral alternatives
    replacements = {
        r'\bhe\b': 'they',
        r'\bshe\b': 'they',
        r'\bhis\b': 'their',
        r'\bher\b': 'their',
        r'\bhim\b': 'them',
        r'\bhimself\b': 'themselves',
        r'\bherself\b': 'themselves',
    }
    
    for pattern, replacement in replacements.items():
        fixed = re.sub(pattern, replacement, fixed, flags=re.IGNORECASE)
    
    # Remove birth years (if standalone)
    fixed = re.sub(r'\b(Born in |Birth year: ?)(19|20)\d{2}\b', '', fixed, flags=re.IGNORECASE)
    
    # Remove age mentions
    fixed = re.sub(r'\b\d{2}\s*years?\s*old\b', '', fixed, flags=re.IGNORECASE)
    
    # Clean up extra spaces
    fixed = re.sub(r'\s+', ' ', fixed).strip()
    
    logger.info("Applied automatic bias fixes to text")
    
    return fixed


def validate_resume_content(summary: str, skills: str, experience: str) -> dict:
    """
    Validate all resume sections for bias.
    
    Parameters
    ----------
    summary : str
        Professional summary text.
    skills : str
        Skills section text.
    experience : str
        Experience section text.
    
    Returns
    -------
    dict
        {
            'overall_safe': bool,
            'summary': dict,
            'skills': dict,
            'experience': dict,
            'total_issues': int
        }
    """
    summary_result = scan_for_bias(summary)
    skills_result = scan_for_bias(skills)
    experience_result = scan_for_bias(experience)
    
    total_issues = (
        summary_result['total_issues'] +
        skills_result['total_issues'] +
        experience_result['total_issues']
    )
    
    return {
        'overall_safe': total_issues == 0,
        'summary': summary_result,
        'skills': skills_result,
        'experience': experience_result,
        'total_issues': total_issues
    }
