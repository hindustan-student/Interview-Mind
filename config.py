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
    # In Vercel serverless environment, the filesystem is read-only except /tmp
    IS_VERCEL = bool(os.environ.get("VERCEL"))

    _env_db = os.environ.get("DATABASE_URL", "")
    if _env_db:
        # Render and Heroku use postgres:// which SQLAlchemy 2.0 requires as postgresql://
        if _env_db.startswith("postgres://"):
            _env_db = _env_db.replace("postgres://", "postgresql://", 1)
        if _env_db.startswith("sqlite://") or _env_db.startswith("postgresql") or _env_db.startswith("mysql"):
            SQLALCHEMY_DATABASE_URI = _env_db
        elif IS_VERCEL:
            SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/interviewmind.db"
        else:
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'instance' / 'interviewmind.db'}"
    elif IS_VERCEL:
        SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/interviewmind.db"
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'instance' / 'interviewmind.db'}"
        try:
            os.makedirs(BASE_DIR / "instance", exist_ok=True)
        except OSError:
            pass
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- File Uploads ---
    if IS_VERCEL:
        UPLOAD_FOLDER = "/tmp/uploads"
    else:
        UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5 MB
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    except OSError:
        pass

    # --- Static export (Vercel static academic demo) ---
    STATIC_EXPORT = os.environ.get("STATIC_EXPORT", "").lower() in ("1", "true", "yes")

    # --- Security ---
    BCRYPT_LOG_ROUNDS = int(os.environ.get("BCRYPT_LOG_ROUNDS", 12))
    WTF_CSRF_ENABLED = False if STATIC_EXPORT else True
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
