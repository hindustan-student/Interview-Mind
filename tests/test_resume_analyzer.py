"""
InterviewMind - Resume Analyzer Tests
======================================
Unit tests for the ATS resume scoring engine.
"""

import os
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.services.resume_analyzer import ResumeAnalyzer, ROLE_KEYWORDS


def write_temp_resume(text: str) -> str:
    """Write a .txt resume file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="resume_test_")
    with os.fdopen(fd, "w") as f:
        f.write(text)
    return path


def test_analyzer_instantiation():
    analyzer = ResumeAnalyzer()
    assert analyzer is not None


def test_missing_file_returns_error():
    analyzer = ResumeAnalyzer()
    result = analyzer.analyze("/nonexistent/path/resume.txt")
    assert "error" in result
    assert result["ats_score"] == 0


def test_text_extraction():
    text = "John Doe\nSoftware Engineer\n\nExperience: 5 years at Acme\nSkills: Python, JavaScript, SQL"
    path = write_temp_resume(text)
    try:
        analyzer = ResumeAnalyzer()
        result = analyzer.analyze(path, target_role="Software Engineer")
        assert "error" not in result
        assert result["word_count"] > 0
        assert "python" in result["matched_keywords"]
    finally:
        os.remove(path)


def test_section_detection():
    text = """
    John Doe
    john@example.com

    Summary: Senior software engineer with 5 years of experience.

    Experience: Acme Corp (2020-2024) - Built scalable APIs.

    Education: B.Tech Computer Science, IIT Delhi.

    Skills: Python, JavaScript, SQL, Docker, AWS.

    Projects: InterviewMind - AI interview prep system.
    """
    path = write_temp_resume(text)
    try:
        analyzer = ResumeAnalyzer()
        result = analyzer.analyze(path, target_role="Software Engineer")
        sections_found = result["sections_found"]
        # Should detect most common sections
        assert "experience" in sections_found
        assert "education" in sections_found
        assert "skills" in sections_found
        assert "summary" in sections_found
    finally:
        os.remove(path)


def test_keyword_coverage():
    text = "Experienced Python developer with AWS, Docker, Kubernetes, REST APIs."
    path = write_temp_resume(text)
    try:
        analyzer = ResumeAnalyzer()
        result = analyzer.analyze(path, target_role="Software Engineer")
        assert result["coverage"] > 0
        assert "python" in result["matched_keywords"]
        assert "docker" in result["matched_keywords"]
    finally:
        os.remove(path)


def test_ats_score_in_range():
    text = "Brief resume with limited content."
    path = write_temp_resume(text)
    try:
        analyzer = ResumeAnalyzer()
        result = analyzer.analyze(path, target_role="Software Engineer")
        assert 0 <= result["ats_score"] <= 100
    finally:
        os.remove(path)


def test_role_normalization():
    analyzer = ResumeAnalyzer()
    assert analyzer._normalize_role("Data Scientist") == "data_scientist"
    assert analyzer._normalize_role("ml-engineer") == "ml_engineer"
    assert analyzer._normalize_role(None) == "software_engineer"
    assert analyzer._normalize_role("") == "software_engineer"
    assert analyzer._normalize_role("Frontend Developer") == "frontend_developer"


def test_recommendations_generated():
    text = "Short"
    path = write_temp_resume(text)
    try:
        analyzer = ResumeAnalyzer()
        result = analyzer.analyze(path, target_role="Software Engineer")
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0
    finally:
        os.remove(path)


def test_role_keyword_bank_present():
    """Sanity check: every curated role has at least 10 keywords."""
    for role, kws in ROLE_KEYWORDS.items():
        assert len(kws) >= 10, f"{role} has too few keywords"
