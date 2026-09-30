"""
InterviewMind - Database Models
================================
SQLAlchemy models for users, interview sessions, answers, and resume reports.

Schema:
    User              -> Core user account
    InterviewSession  -> One mock-interview attempt by a user
    Answer            -> A single answer in an interview session
    ResumeReport      -> A resume ATS analysis report

Author: InterviewMind Academic Project Team
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


# ---------------------------------------------------------------------------
# Association Tables
# ---------------------------------------------------------------------------


class User(UserMixin, db.Model):
    """User account model.

    Stores credentials and serves as the anchor for all interview activity.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    target_role = db.Column(db.String(120), nullable=True)
    years_experience = db.Column(db.Integer, default=0)
    cgpa = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    sessions = db.relationship(
        "InterviewSession",
        backref="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    resume_reports = db.relationship(
        "ResumeReport",
        backref="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # --- Password handling ---
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # --- Flask-Login required helpers ---
    def get_id(self) -> str:
        return str(self.id)

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id: int):
    """Flask-Login user loader callback."""
    return User.query.get(int(user_id))


class InterviewSession(db.Model):
    """One mock-interview attempt by a user.

    Tracks the question category, the user's target role, the running score,
    and final performance metrics.
    """

    __tablename__ = "interview_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False, default="mixed")
    difficulty = db.Column(db.String(20), default="medium")  # easy, medium, hard
    cgpa = db.Column(db.Float, nullable=True)  # Candidate CGPA
    phase = db.Column(db.String(30), default="pre_assessment")  # pre_assessment, main, completed
    pre_assessment_score = db.Column(db.Float, nullable=True)  # score out of 10
    pre_assessment_category = db.Column(db.String(50), nullable=True)  # Medium, Above Medium, Excellent
    total_questions = db.Column(db.Integer, default=10)
    answered_count = db.Column(db.Integer, default=0)
    overall_score = db.Column(db.Float, default=0.0)  # 0-100
    avg_confidence = db.Column(db.Float, default=0.0)
    feedback_summary = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="in_progress")  # in_progress, completed, abandoned

    answers = db.relationship(
        "Answer",
        backref="session",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Answer.question_index",
    )

    def mark_completed(self):
        """Finalize session and compute aggregate metrics."""
        self.completed_at = datetime.now(timezone.utc)
        self.status = "completed"
        self.phase = "completed"
        # Prioritize main practice answers for final score if completed
        main_answers = [a for a in self.answers if a.phase == "main" and a.score is not None]
        target_answers = main_answers if main_answers else [a for a in self.answers if a.score is not None]
        if target_answers:
            total_marks_allocated = sum(a.marks_allocated or 1.0 for a in target_answers)
            if total_marks_allocated > 0:
                total_marks_earned = sum(((a.score or 0.0) / 100.0) * (a.marks_allocated or 1.0) for a in target_answers)
                self.overall_score = round((total_marks_earned / total_marks_allocated) * 100.0, 2)
            else:
                self.overall_score = round(sum(a.score for a in target_answers) / len(target_answers), 2)
            confidences = [a.confidence for a in target_answers if a.confidence is not None]
            if confidences:
                self.avg_confidence = round(sum(confidences) / len(confidences), 2)

    def __repr__(self) -> str:
        return f"<InterviewSession id={self.id} user={self.user_id} role={self.role}>"


class Answer(db.Model):
    """A single Q&A pair within an interview session."""

    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("interview_sessions.id"), nullable=False)
    phase = db.Column(db.String(30), default="main")  # pre_assessment, main
    section_number = db.Column(db.Integer, nullable=True)  # 1 to 6 (Levels 1 to 6)
    section_name = db.Column(db.String(120), nullable=True)  # e.g. "Level 1: Core CS Fundamentals"
    marks_allocated = db.Column(db.Float, default=1.0)  # marks for this question
    question_type = db.Column(db.String(20), default="descriptive")  # mcq, descriptive
    options = db.Column(db.Text, nullable=True)  # JSON-serialized list
    correct_option = db.Column(db.String(255), nullable=True)
    explanation = db.Column(db.Text, nullable=True)
    question_index = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_category = db.Column(db.String(80), nullable=False)
    user_answer = db.Column(db.Text, nullable=True)
    model_answer = db.Column(db.Text, nullable=True)
    keywords_expected = db.Column(db.Text, nullable=True)  # JSON-serialized list
    keywords_matched = db.Column(db.Text, nullable=True)  # JSON-serialized list
    score = db.Column(db.Float, default=0.0)  # 0-100
    confidence = db.Column(db.Float, default=0.0)  # 0-1
    feedback = db.Column(db.Text, nullable=True)
    strengths = db.Column(db.Text, nullable=True)
    improvements = db.Column(db.Text, nullable=True)
    time_taken_seconds = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Answer q{self.question_index} score={self.score}>"


class ResumeReport(db.Model):
    """An ATS analysis report for a user-uploaded resume."""

    __tablename__ = "resume_reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    target_role = db.Column(db.String(120), nullable=True)
    extracted_text_length = db.Column(db.Integer, default=0)
    word_count = db.Column(db.Integer, default=0)
    ats_score = db.Column(db.Float, default=0.0)  # 0-100
    keyword_coverage = db.Column(db.Float, default=0.0)  # 0-1
    matched_keywords = db.Column(db.Text, nullable=True)  # JSON-serialized list
    missing_keywords = db.Column(db.Text, nullable=True)  # JSON-serialized list
    sections_found = db.Column(db.Text, nullable=True)  # JSON-serialized list
    recommendations = db.Column(db.Text, nullable=True)  # JSON-serialized list
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<ResumeReport id={self.id} ats={self.ats_score}>"


class QuestionBankItem(db.Model):
    """Pre-built interview questions across categories.

    Seeded by the question-bank service; can be extended by an admin later.
    """

    __tablename__ = "question_bank"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    difficulty = db.Column(db.String(20), nullable=False, default="medium")
    question_text = db.Column(db.Text, nullable=False)
    model_answer = db.Column(db.Text, nullable=True)
    expected_keywords = db.Column(db.Text, nullable=True)  # comma-separated
    role_tags = db.Column(db.Text, nullable=True)  # comma-separated
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<QuestionBankItem #{self.id} cat={self.category}>"
