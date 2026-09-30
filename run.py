"""
InterviewMind - Application Entry Point
========================================
Run the InterviewMind Flask application.

Usage:
    python run.py                    # Development server (default)
    python run.py --env production   # Production WSGI server entry
    python run.py --port 8080        # Custom port

Author: InterviewMind Academic Project Team
"""

import argparse
import os
from app import create_app
from app.extensions import db
from app.models import User, InterviewSession, Answer, ResumeReport

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.shell_context_processor
def make_shell_context():
    """Provide shell context for `flask shell`."""
    return {
        "db": db,
        "User": User,
        "InterviewSession": InterviewSession,
        "Answer": Answer,
        "ResumeReport": ResumeReport,
    }


@app.cli.command("init-db")
def init_db():
    """Initialize the database with default schema."""
    db.create_all()
    print("✓ Database initialized successfully.")


@app.cli.command("seed-db")
def seed_db():
    """Seed the database with default interview questions."""
    from app.services.question_bank import QuestionBank
    qb = QuestionBank()
    count = qb.seed_defaults()
    print(f"✓ Seeded {count} default interview questions.")


def parse_args():
    parser = argparse.ArgumentParser(description="Run InterviewMind Flask application")
    parser.add_argument("--env", default="development",
                        choices=["development", "testing", "production"],
                        help="Configuration environment")
    parser.add_argument("--port", type=int, default=5000,
                        help="Port to bind the server")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Host to bind the server")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    app = create_app(args.env)
    print(f"\n{'=' * 60}")
    print(f"  InterviewMind - AI Interview Preparation System")
    print(f"  Environment: {args.env}")
    print(f"  Running at:  http://{args.host}:{args.port}")
    print(f"{'=' * 60}\n")
    app.run(host=args.host, port=args.port, debug=(args.env == "development"))
