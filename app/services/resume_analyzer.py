"""
InterviewMind - Resume Analyzer
================================
Extracts text from PDF/DOCX/TXT resumes and computes an ATS score.

Pipeline:
1. Read file based on extension
2. Detect resume sections (experience, education, skills, projects)
3. Compare against a role keyword set (configurable)
4. Compute ATS score, coverage, recommendations

Author: InterviewMind Academic Project Team
"""

from __future__ import annotations
import os
import re
import json
from typing import Dict, List, Tuple, Optional


# Role-specific keyword banks (academic-quality, not exhaustive)
ROLE_KEYWORDS: Dict[str, List[str]] = {
    "software_engineer": [
        "python", "java", "javascript", "sql", "git", "docker", "kubernetes",
        "rest", "api", "linux", "agile", "ci/cd", "unit testing", "data structures",
        "algorithms", "system design", "microservices", "aws", "azure",
    ],
    "data_scientist": [
        "python", "r", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
        "machine learning", "deep learning", "nlp", "statistics", "data visualization",
        "matplotlib", "sql", "etl", "feature engineering", "model deployment",
    ],
    "data_analyst": [
        "sql", "excel", "python", "tableau", "power bi", "statistics", "data cleaning",
        "data visualization", "pandas", "etl", "reporting", "dashboard", "kpi",
        "ga4", "segmentation", "a/b testing",
    ],
    "ml_engineer": [
        "python", "tensorflow", "pytorch", "mlops", "model deployment", "docker",
        "kubernetes", "airflow", "kubeflow", "feature store", "model monitoring",
        "ci/cd", "aws sagemaker", "vertex ai", "mlflow",
    ],
    "product_manager": [
        "roadmap", "stakeholder", "user research", "kpi", "okr", "agile", "scrum",
        "a/b testing", "prds", "market research", "go-to-market", "user stories",
        "wireframing", "analytics", "product vision", "competitive analysis",
    ],
    "devops_engineer": [
        "docker", "kubernetes", "terraform", "ansible", "jenkins", "gitlab ci",
        "aws", "azure", "gcp", "linux", "bash", "python", "prometheus", "grafana",
        "helm", "istio", "monitoring", "incident response",
    ],
    "frontend_developer": [
        "html", "css", "javascript", "react", "vue", "angular", "typescript",
        "webpack", "responsive design", "accessibility", "redux", "graphql",
        "tailwind", "next.js", "testing", "web performance",
    ],
    "backend_developer": [
        "python", "java", "go", "node.js", "sql", "postgresql", "mongodb", "redis",
        "docker", "kubernetes", "microservices", "rest", "grpc", "kafka", "rabbitmq",
        "system design", "ci/cd",
    ],
}

# Sections we look for in a resume
EXPECTED_SECTIONS = {
    "experience": [r"\bexperience\b", r"\bwork history\b", r"\bemployment\b"],
    "education": [r"\beducation\b", r"\bacademic\b"],
    "skills": [r"\bskills\b", r"\btechnical skills\b", r"\bcompetencies\b"],
    "projects": [r"\bprojects\b", r"\bportfolio\b"],
    "summary": [r"\bsummary\b", r"\bobjective\b", r"\bprofile\b"],
    "contact": [r"\bcontact\b", r"\bemail\b", r"@"],
}

# Common mistakes that hurt ATS scores
COMMON_ISSUES = {
    "image": r"(\.png|\.jpg|\.jpeg)",
    "table_html": r"<table",
    "multi_column": r"\|.*\|.*\|",  # crude table-detection proxy
}


class ResumeAnalyzer:
    """Extracts text and computes an ATS-style score for a resume."""

    # --------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------

    def analyze(self, file_path: str, target_role: Optional[str] = None) -> Dict:
        """Analyze a resume file.

        Returns a dict with:
            - text             (str, raw extracted text)
            - word_count       (int)
            - sections_found   (list[str])
            - sections_missing (list[str])
            - matched_keywords (list[str])
            - missing_keywords (list[str])
            - ats_score        (float, 0-100)
            - coverage         (float, 0-1)
            - recommendations  (list[str])
        """
        if not os.path.isfile(file_path):
            return {"error": "File not found", "ats_score": 0}

        text = self._extract_text(file_path)
        if not text or not text.strip():
            return {
                "error": "Could not extract text (likely a scanned image PDF).",
                "ats_score": 0,
            }

        lowered = text.lower()
        word_count = len(lowered.split())

        # Sections
        sections_found, sections_missing = self._detect_sections(lowered)

        # Keywords for the role
        role = self._normalize_role(target_role)
        keywords = ROLE_KEYWORDS.get(role, ROLE_KEYWORDS["software_engineer"])
        matched, missing = self._match_keywords(lowered, keywords)
        coverage = (len(matched) / len(keywords)) if keywords else 0.0

        # Common issues
        issues = self._detect_issues(lowered)

        # ATS Score (weighted)
        ats_score = self._compute_ats_score(
            coverage=coverage,
            sections_found=len(sections_found),
            sections_total=len(EXPECTED_SECTIONS),
            word_count=word_count,
            issues=len(issues),
        )

        recommendations = self._recommendations(
            sections_missing=sections_missing,
            missing_keywords=missing,
            issues=issues,
            word_count=word_count,
        )

        return {
            "text": text,
            "text_preview": text[:1500],
            "word_count": word_count,
            "sections_found": sections_found,
            "sections_missing": sections_missing,
            "matched_keywords": matched,
            "missing_keywords": missing,
            "ats_score": ats_score,
            "coverage": round(coverage, 2),
            "role": role,
            "recommendations": recommendations,
            "issues": issues,
        }

    # --------------------------------------------------------------
    # Text extraction
    # --------------------------------------------------------------

    def _extract_text(self, file_path: str) -> str:
        """Dispatch to the right extractor based on extension."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self._extract_pdf(file_path)
        if ext == ".docx":
            return self._extract_docx(file_path)
        if ext in {".txt", ".md"}:
            return self._extract_text_file(file_path)
        return ""

    def _extract_pdf(self, file_path: str) -> str:
        """Try pdfplumber first, fall back to PyPDF2."""
        text = ""
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages[:3]:  # cap to first 3 pages
                    text += (page.extract_text() or "") + "\n"
            if text.strip():
                return text
        except Exception:
            pass
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            for page in reader.pages[:3]:
                text += (page.extract_text() or "") + "\n"
            return text
        except Exception:
            return ""

    def _extract_docx(self, file_path: str) -> str:
        try:
            import docx
            doc = docx.Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception:
            return ""

    def _extract_text_file(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

    # --------------------------------------------------------------
    # Section + keyword analysis
    # --------------------------------------------------------------

    def _detect_sections(self, text: str) -> Tuple[List[str], List[str]]:
        found, missing = [], []
        for section, patterns in EXPECTED_SECTIONS.items():
            if any(re.search(p, text) for p in patterns):
                found.append(section)
            else:
                missing.append(section)
        return found, missing

    def _normalize_role(self, role: Optional[str]) -> str:
        if not role:
            return "software_engineer"
        role = role.lower().strip().replace(" ", "_").replace("-", "_")
        if role in ROLE_KEYWORDS:
            return role
        # Heuristic mapping for variants
        if "data sci" in role:
            return "data_scientist"
        if "data ana" in role:
            return "data_analyst"
        if "ml" in role or "machine" in role:
            return "ml_engineer"
        if "devops" in role or "sre" in role:
            return "devops_engineer"
        if "product" in role:
            return "product_manager"
        if "frontend" in role or "front-end" in role or "ui" in role:
            return "frontend_developer"
        if "backend" in role or "back-end" in role:
            return "backend_developer"
        return "software_engineer"

    def _match_keywords(self, text: str, keywords: List[str]) -> Tuple[List[str], List[str]]:
        matched, missing = [], []
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw.lower()) + r"\b", text):
                matched.append(kw)
            else:
                missing.append(kw)
        return matched, missing

    def _detect_issues(self, text: str) -> List[str]:
        issues = []
        for name, pattern in COMMON_ISSUES.items():
            if re.search(pattern, text):
                issues.append(name)
        return issues

    # --------------------------------------------------------------
    # Scoring
    # --------------------------------------------------------------

    def _compute_ats_score(
        self,
        coverage: float,
        sections_found: int,
        sections_total: int,
        word_count: int,
        issues: int,
    ) -> float:
        keyword_weight = 0.45
        section_weight = 0.35
        length_weight = 0.15
        issues_weight = 0.05

        section_ratio = sections_found / max(sections_total, 1)
        length_score = (
            100.0 if 300 <= word_count <= 800
            else (50.0 if word_count < 200 else 70.0)
        )
        issues_penalty = max(0, 1 - issues * 0.5)

        score = (
            keyword_weight * (coverage * 100)
            + section_weight * (section_ratio * 100)
            + length_weight * length_score
            + issues_weight * (issues_penalty * 100)
        )
        return round(max(0, min(score, 100)), 1)

    # --------------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------------

    def _recommendations(
        self,
        sections_missing: List[str],
        missing_keywords: List[str],
        issues: List[str],
        word_count: int,
    ) -> List[str]:
        recs = []

        if sections_missing:
            recs.append(
                "Add a clear '" + "', '".join(sections_missing[:3]) +
                "' section header — ATS systems look for these markers."
            )
        if missing_keywords:
            recs.append(
                "Include more role-relevant keywords: " +
                ", ".join(missing_keywords[:8]) +
                ". Naturally embed them in your experience bullets."
            )
        if word_count < 200:
            recs.append(
                f"Resume is short ({word_count} words). "
                "Aim for 300-800 words covering 2-3 roles with quantified impact."
            )
        if word_count > 900:
            recs.append(
                f"Resume is lengthy ({word_count} words). "
                "Tighten to 1-2 pages for ATS readability."
            )
        if "image" in issues:
            recs.append("Detected image references — ATS cannot read images. Use text only.")
        if "table_html" in issues or "multi_column" in issues:
            recs.append("Tables / multi-column layouts confuse ATS. Prefer a single-column text layout.")
        if not recs:
            recs.append("Resume looks well-structured. Keep tailoring keywords per job description.")

        return recs


analyzer = ResumeAnalyzer()
