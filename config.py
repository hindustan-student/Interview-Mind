"""
InterviewMind - Configuration Module
====================================
Centralized configuration for the InterviewMind academic project.
Supports multiple environments: Development, Testing, Production.

Author: InterviewMind Academic Project Team
Version: 1.0.0
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project base directory
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base configuration shared across all environments."""

    # --- Core Flask Settings ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "interviewmind-dev-secret-key-change-me")
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds

    # --- Database ---
    # Use a project-local SQLite by default. Ignore DATABASE_URL if it's
    # not a SQLAlchemy-compatible URI (e.g. parent environment may set
    # DATABASE_URL to something else entirely).
    _env_db = os.environ.get("DATABASE_URL", "")
    if _env_db and (_env_db.startswith("sqlite://") or _env_db.startswith("postgres")
                     or _env_db.startswith("mysql")):
        SQLALCHEMY_DATABASE_URI = _env_db
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'instance' / 'interviewmind.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- File Uploads ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5 MB
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # --- Security ---
    BCRYPT_LOG_ROUNDS = int(os.environ.get("BCRYPT_LOG_ROUNDS", 12))
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # --- Application Metadata ---
    APP_NAME = os.environ.get("APP_NAME", "InterviewMind")
    APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
    APP_AUTHOR = "Academic Project Team"

    # --- AI Engine Settings ---
    MAX_INTERVIEW_QUESTIONS = 10
    ANSWER_MIN_WORDS = 30
    ANSWER_MAX_WORDS = 800

    # --- Resume Analyzer ---
    ATS_KEYWORD_MIN_MATCH = 0.35
    RESUME_MAX_PAGES = 3


class DevelopmentConfig(Config):
    """Development configuration - verbose logging, auto-reload."""

    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = False
    TEMPLATES_AUTO_RELOAD = True


class TestingConfig(Config):
    """Testing configuration - in-memory DB, no CSRF, no rate limits."""

    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    BCRYPT_LOG_ROUNDS = 4  # Faster hashing during tests
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024
    SERVER_NAME = "localhost.localdomain"


class ProductionConfig(Config):
    """Production configuration - hardened settings."""

    DEBUG = False
    TESTING = False
    # Enforce strong SECRET_KEY in production
    SECRET_KEY = os.environ.get("SECRET_KEY") or "fallback-not-secure-please-set-secret"


# Configuration registry
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
