"""
InterviewMind - Resume Routes Blueprint
========================================
Handles resume upload, ATS analysis, and report display.
"""

import os
import json
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import current_user
from app.security import login_required_unless_static
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import ResumeReport
from app.services import resume_analyzer
from config import Config

resume_bp = Blueprint("resume", __name__)


def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    )


@resume_bp.route("/upload", methods=["GET", "POST"])
@login_required_unless_static
def upload():
    """Upload a resume for ATS analysis."""
    if request.method == "POST":
        if "resume" not in request.files:
            flash("No file selected.", "danger")
            return redirect(url_for("resume.upload"))
        file = request.files["resume"]
        if not file or file.filename == "":
            flash("No file selected.", "danger")
            return redirect(url_for("resume.upload"))
        if not allowed_file(file.filename):
            flash("Allowed formats: PDF, DOCX, TXT.", "danger")
            return redirect(url_for("resume.upload"))

        # Secure filename + user-prefixed
        original = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_name = f"user{current_user.id}_{timestamp}_{original}"
        upload_dir = os.path.join(Config.UPLOAD_FOLDER)
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, saved_name)
        file.save(file_path)

        # Analyze
        target_role = (request.form.get("target_role") or "").strip()
        result = resume_analyzer.analyze(file_path, target_role=target_role)

        if "error" in result:
            flash(result["error"], "danger")
            return redirect(url_for("resume.upload"))

        # Persist report
        report = ResumeReport(
            user_id=current_user.id,
            filename=original,
            target_role=target_role or None,
            extracted_text_length=result.get("text") and len(result["text"]) or 0,
            word_count=result.get("word_count", 0),
            ats_score=result.get("ats_score", 0),
            keyword_coverage=result.get("coverage", 0),
            matched_keywords=json.dumps(result.get("matched_keywords", [])),
            missing_keywords=json.dumps(result.get("missing_keywords", [])),
            sections_found=json.dumps(result.get("sections_found", [])),
            recommendations=json.dumps(result.get("recommendations", [])),
        )
        db.session.add(report)
        db.session.commit()

        flash(f"Resume analyzed. ATS score: {report.ats_score}/100", "success")
        return redirect(url_for("resume.report", report_id=report.id))

    return render_template("resume/upload.html")


@resume_bp.route("/view")
@login_required_unless_static
def view_static():
    """Client-side ATS report used by the static Vercel export."""
    return render_template("resume/report_static.html")


@resume_bp.route("/report/<int:report_id>")
@login_required_unless_static
def report(report_id):
    """Display a single resume ATS report."""
    rep = ResumeReport.query.get_or_404(report_id)
    if rep.user_id != current_user.id:
        abort(403)
    matched = json.loads(rep.matched_keywords) if rep.matched_keywords else []
    missing = json.loads(rep.missing_keywords) if rep.missing_keywords else []
    sections = json.loads(rep.sections_found) if rep.sections_found else []
    recs = json.loads(rep.recommendations) if rep.recommendations else []
    return render_template(
        "resume/report.html",
        report=rep,
        matched=matched,
        missing=missing,
        sections=sections,
        recommendations=recs,
    )


@resume_bp.route("/history")
@login_required_unless_static
def history():
    """List all of the user's resume reports."""
    if not current_user.is_authenticated:
        return render_template("resume/history.html", reports=[])
    reports = (
        ResumeReport.query
        .filter_by(user_id=current_user.id)
        .order_by(ResumeReport.created_at.desc())
        .all()
    )
    return render_template("resume/history.html", reports=reports)
