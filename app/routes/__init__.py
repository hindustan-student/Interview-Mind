"""InterviewMind - Routes package init."""

from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.interview import interview_bp
from app.routes.resume import resume_bp
from app.routes.questions import questions_bp
from app.routes.dashboard import dashboard_bp
from app.routes.api import api_bp

__all__ = [
    "main_bp", "auth_bp", "interview_bp",
    "resume_bp", "questions_bp", "dashboard_bp", "api_bp",
]
