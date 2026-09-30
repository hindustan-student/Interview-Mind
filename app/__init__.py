"""
InterviewMind - Application Factory
====================================
Modular Flask application using the application factory pattern.

This module initializes:
- Flask app instance
- Database (SQLAlchemy)
- Login manager
- CSRF protection
- Blueprints registration
- Template context processors

Author: InterviewMind Academic Project Team
"""

import logging
from flask import Flask, render_template_string
from config import config

# Extensions (initialized once, attached to app in factory)
from app.extensions import db, login_manager, bcrypt, csrf, migrate

login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


def create_app(config_name="development"):
    """Application factory pattern.

    Args:
        config_name (str): One of 'development', 'testing', 'production'

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Configure logging
    _configure_logging(app)

    # Register all blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    # Register template context processors
    _register_context_processors(app)

    # Auto-create database on first run
    if config_name in ("development", "testing"):
        with app.app_context():
            try:
                db.create_all()
                _ensure_db_schema()
                app.logger.info("Database tables and columns created/verified.")
            except Exception as exc:
                app.logger.error(f"Database initialization failed: {exc}")

    app.logger.info(f"InterviewMind app started in '{config_name}' mode.")
    return app


def _ensure_db_schema():
    """Ensure newly added columns exist in database tables."""
    from sqlalchemy import text, inspect
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if "users" in tables:
            user_cols = {c["name"] for c in inspector.get_columns("users")}
            if "cgpa" not in user_cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN cgpa FLOAT"))

        if "interview_sessions" in tables:
            sess_cols = {c["name"] for c in inspector.get_columns("interview_sessions")}
            if "cgpa" not in sess_cols:
                db.session.execute(text("ALTER TABLE interview_sessions ADD COLUMN cgpa FLOAT"))
            if "phase" not in sess_cols:
                db.session.execute(text("ALTER TABLE interview_sessions ADD COLUMN phase VARCHAR(30) DEFAULT 'pre_assessment'"))
            if "pre_assessment_score" not in sess_cols:
                db.session.execute(text("ALTER TABLE interview_sessions ADD COLUMN pre_assessment_score FLOAT"))
            if "pre_assessment_category" not in sess_cols:
                db.session.execute(text("ALTER TABLE interview_sessions ADD COLUMN pre_assessment_category VARCHAR(50)"))

        if "answers" in tables:
            ans_cols = {c["name"] for c in inspector.get_columns("answers")}
            if "phase" not in ans_cols:
                db.session.execute(text("ALTER TABLE answers ADD COLUMN phase VARCHAR(30) DEFAULT 'main'"))
            if "question_type" not in ans_cols:
                db.session.execute(text("ALTER TABLE answers ADD COLUMN question_type VARCHAR(20) DEFAULT 'descriptive'"))
            if "options" not in ans_cols:
                db.session.execute(text("ALTER TABLE answers ADD COLUMN options TEXT"))
            if "correct_option" not in ans_cols:
                db.session.execute(text("ALTER TABLE answers ADD COLUMN correct_option VARCHAR(255)"))
            if "explanation" not in ans_cols:
                db.session.execute(text("ALTER TABLE answers ADD COLUMN explanation TEXT"))
            if "section_number" not in ans_cols:
                db.session.execute(text("ALTER TABLE answers ADD COLUMN section_number INTEGER"))
            if "section_name" not in ans_cols:
                db.session.execute(text("ALTER TABLE answers ADD COLUMN section_name VARCHAR(120)"))
            if "marks_allocated" not in ans_cols:
                db.session.execute(text("ALTER TABLE answers ADD COLUMN marks_allocated FLOAT DEFAULT 1.0"))

        db.session.commit()
    except Exception as e:
        db.session.rollback()


def _configure_logging(app):
    """Configure structured logging."""
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    if not app.logger.handlers:
        app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG if app.config["DEBUG"] else logging.INFO)


def _register_blueprints(app):
    """Register all application blueprints with proper URL prefixes."""
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.interview import interview_bp
    from app.routes.resume import resume_bp
    from app.routes.questions import questions_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(interview_bp, url_prefix="/interview")
    app.register_blueprint(resume_bp, url_prefix="/resume")
    app.register_blueprint(questions_bp, url_prefix="/questions")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(api_bp, url_prefix="/api")


def _register_error_handlers(app):
    """Register custom error pages."""

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template_string("""
        {% extends 'base.html' %}
        {% block title %}404 - Page Not Found | InterviewMind{% endblock %}
        {% block content %}
        <div class="error-container">
            <h1 class="error-code">404</h1>
            <h2 class="error-title">Page Not Found</h2>
            <p class="error-message">The page you're looking for seems to have taken a different career path.</p>
            <a href="{{ url_for('main.index') }}" class="btn btn-primary">Back to Home</a>
        </div>
        {% endblock %}
        """), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template_string("""
        {% extends 'base.html' %}
        {% block title %}500 - Server Error | InterviewMind{% endblock %}
        {% block content %}
        <div class="error-container">
            <h1 class="error-code">500</h1>
            <h2 class="error-title">Server Error</h2>
            <p class="error-message">Our servers need a coffee break. Please try again shortly.</p>
            <a href="{{ url_for('main.index') }}" class="btn btn-primary">Back to Home</a>
        </div>
        {% endblock %}
        """), 500

    @app.errorhandler(413)
    def payload_too_large(e):
        return render_template_string("""
        {% extends 'base.html' %}
        {% block title %}413 - File Too Large | InterviewMind{% endblock %}
        {% block content %}
        <div class="error-container">
            <h1 class="error-code">413</h1>
            <h2 class="error-title">File Too Large</h2>
            <p class="error-message">The uploaded file exceeds the maximum allowed size (5 MB).</p>
            <a href="{{ url_for('resume.upload') }}" class="btn btn-primary">Try Again</a>
        </div>
        {% endblock %}
        """), 413


def _register_context_processors(app):
    """Inject global template variables."""

    @app.context_processor
    def inject_globals():
        return {
            "APP_NAME": app.config["APP_NAME"],
            "APP_VERSION": app.config["APP_VERSION"],
            "CURRENT_YEAR": __import__("datetime").datetime.now().year,
        }
