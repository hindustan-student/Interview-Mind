"""
InterviewMind - Dashboard Routes Blueprint
==========================================
User analytics dashboard — interview history, ATS reports, score trends.
"""

import json
from collections import defaultdict
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import InterviewSession, ResumeReport, Answer

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    """User dashboard home."""
    sessions = (
        InterviewSession.query
        .filter_by(user_id=current_user.id)
        .order_by(InterviewSession.started_at.desc())
        .all()
    )
    reports = (
        ResumeReport.query
        .filter_by(user_id=current_user.id)
        .order_by(ResumeReport.created_at.desc())
        .all()
    )

    # --- Stats ---
    total_sessions = len(sessions)
    completed_sessions = [s for s in sessions if s.status == "completed"]
    avg_score = (
        round(sum(s.overall_score for s in completed_sessions) / len(completed_sessions), 1)
        if completed_sessions else 0
    )
    best_score = max((s.overall_score for s in completed_sessions), default=0)
    avg_confidence = (
        round(sum(s.avg_confidence for s in completed_sessions) / len(completed_sessions), 2)
        if completed_sessions else 0
    )

    # Score trend (last 10 sessions)
    trend_sessions = list(reversed(completed_sessions))[-10:]
    score_trend = [
        {"label": s.started_at.strftime("%m/%d"), "score": s.overall_score}
        for s in trend_sessions
    ]

    # Category breakdown across all answers
    cat_scores = defaultdict(list)
    for s in completed_sessions:
        for a in s.answers:
            if a.score is not None:
                cat_scores[a.question_category or "other"].append(a.score)
    cat_summary = [
        {"category": k.replace("_", " ").title(),
         "avg": round(sum(v) / len(v), 1),
         "count": len(v)}
        for k, v in cat_scores.items()
    ]

    # Recent activity
    recent_sessions = sessions[:5]
    recent_reports = reports[:3]

    # ATS summary
    avg_ats = (
        round(sum(r.ats_score for r in reports) / len(reports), 1)
        if reports else 0
    )

    return render_template(
        "dashboard/index.html",
        total_sessions=total_sessions,
        completed_sessions=len(completed_sessions),
        avg_score=avg_score,
        best_score=best_score,
        avg_confidence=avg_confidence,
        score_trend=score_trend,
        cat_summary=cat_summary,
        recent_sessions=recent_sessions,
        recent_reports=recent_reports,
        avg_ats=avg_ats,
        total_reports=len(reports),
    )
