"""
Freeze InterviewMind into a static site for Vercel (output: public/).
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

os.environ["STATIC_EXPORT"] = "1"
os.environ.setdefault("FLASK_ENV", "production")
os.environ.setdefault("SECRET_KEY", "static-export-not-used-in-browser")

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"


def export_question_bank(dest: Path) -> None:
    from app.services.question_bank import SECTIONS_CONFIG
    from app.services.questions_data import (
        PRE_ASSESSMENT_QUESTIONS,
        EASY_TECHNICAL_MCQ,
        EASY_TECHNICAL_DESC,
        EASY_LOGICAL_MCQ,
        EASY_LOGICAL_DESC,
        MEDIUM_TECHNICAL_MCQ,
        MEDIUM_TECHNICAL_DESC,
        MEDIUM_LOGICAL_MCQ,
        MEDIUM_LOGICAL_DESC,
        HARD_TECHNICAL_MCQ,
        HARD_TECHNICAL_DESC,
        HARD_LOGICAL_MCQ,
        HARD_LOGICAL_DESC,
    )
    from app.services.resume_analyzer import ROLE_KEYWORDS

    payload = {
        "sections": SECTIONS_CONFIG,
        "pre_assessment": PRE_ASSESSMENT_QUESTIONS,
        "role_keywords": ROLE_KEYWORDS,
        "banks": {
            "easy": {
                "tech_mcq": EASY_TECHNICAL_MCQ,
                "tech_desc": EASY_TECHNICAL_DESC,
                "logic_mcq": EASY_LOGICAL_MCQ,
                "logic_desc": EASY_LOGICAL_DESC,
            },
            "medium": {
                "tech_mcq": MEDIUM_TECHNICAL_MCQ,
                "tech_desc": MEDIUM_TECHNICAL_DESC,
                "logic_mcq": MEDIUM_LOGICAL_MCQ,
                "logic_desc": MEDIUM_LOGICAL_DESC,
            },
            "hard": {
                "tech_mcq": HARD_TECHNICAL_MCQ,
                "tech_desc": HARD_TECHNICAL_DESC,
                "logic_mcq": HARD_LOGICAL_MCQ,
                "logic_desc": HARD_LOGICAL_DESC,
            },
        },
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload), encoding="utf-8")


def write_page(public: Path, url_path: str, body: bytes, content_type: str) -> None:
    url_path = url_path.split("?")[0]
    if url_path in ("", "/"):
        target = public / "index.html"
    elif url_path.endswith(".json") or "json" in content_type:
        rel = url_path.strip("/")
        if not rel.endswith(".json"):
            rel = rel + ".json"
        target = public / rel
    else:
        rel = url_path.strip("/")
        target = public / rel / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)


def freeze() -> None:
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir(parents=True)

    from app import create_app

    app = create_app("production")
    app.config["SERVER_NAME"] = "interviewmind.local"
    app.config["PREFERRED_URL_SCHEME"] = "https"

    static_src = ROOT / "app" / "static"
    static_dest = PUBLIC / "static"
    shutil.copytree(static_src, static_dest)
    export_question_bank(static_dest / "data" / "questions.json")

    pages = [
        "/",
        "/about",
        "/features",
        "/contact",
        "/auth/login",
        "/auth/register",
        "/questions/",
        "/dashboard/",
        "/interview/start",
        "/interview/play",
        "/interview/report",
        "/interview/history",
        "/resume/upload",
        "/resume/view",
        "/resume/history",
        "/health",
    ]

    with app.app_context():
        client = app.test_client()
        for url in pages:
            resp = client.get(url, follow_redirects=True)
            ctype = resp.headers.get("Content-Type", "text/html")
            write_page(PUBLIC, url, resp.data, ctype)
            print(f"  [{resp.status_code}] {url}")

        not_found = client.get("/this-page-does-not-exist")
        (PUBLIC / "404.html").write_bytes(not_found.data)

    print(f"\nStatic site written to {PUBLIC}")


if __name__ == "__main__":
    freeze()
