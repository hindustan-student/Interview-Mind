"""
InterviewMind - Main Routes Blueprint
======================================
Handles landing page, about, features, contact.
"""

from flask import Blueprint, render_template, request
from flask_login import current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Landing page with neon particle animation."""
    return render_template(
        "index.html",
        user=current_user if current_user.is_authenticated else None,
    )


@main_bp.route("/about")
def about():
    """About page - project overview, academic context."""
    return render_template("about.html")


@main_bp.route("/features")
def features():
    """Features page - lists all InterviewMind capabilities."""
    features_list = [
        {
            "icon": "brain",
            "title": "AI Mock Interview",
            "desc": "Simulates a real interviewer with role-specific questions, difficulty levels, "
                    "and instant STAR-method feedback on every answer.",
            "color": "cyan",
        },
        {
            "icon": "file-text",
            "title": "Resume ATS Analyzer",
            "desc": "Upload PDF / DOCX / TXT resume and get an instant ATS score with keyword "
                    "coverage, missing sections, and tailored recommendations.",
            "color": "magenta",
        },
        {
            "icon": "database",
            "title": "Curated Question Bank",
            "desc": "Hand-curated questions across behavioral, technical, system design, coding, "
                    "HR, and situational categories — modeled on top tech interview prep.",
            "color": "purple",
        },
        {
            "icon": "chart-line",
            "title": "Performance Dashboard",
            "desc": "Track every mock interview, see your score trends, identify weak categories, "
                    "and watch your confidence grow over time.",
            "color": "green",
        },
        {
            "icon": "shield",
            "title": "Secure Auth",
            "desc": "Flask-Login sessions, Werkzeug password hashing (PBKDF2-SHA256), CSRF protection, "
                    "and per-session interview history.",
            "color": "yellow",
        },
        {
            "icon": "bolt",
            "title": "Real-Time Feedback",
            "desc": "After every answer: score, strengths, improvements, STAR breakdown, "
                    "keyword match, and confidence proxy — all computed locally, no API needed.",
            "color": "blue",
        },
    ]
    return render_template("features.html", features=features_list)


@main_bp.route("/contact")
def contact():
    """Contact page."""
    return render_template("contact.html")


@main_bp.route("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "InterviewMind", "version": "1.0.0"}, 200
