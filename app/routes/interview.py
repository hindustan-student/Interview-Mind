"""
InterviewMind - Interview Routes Blueprint
============================================
Manages mock interview lifecycle:
    /interview/start               -> configure & start pre-assessment
    /interview/<id>                -> render current question or transition
    /interview/<id>/start_main     -> initialize 60-question main practice (6 levels)
    /interview/<id>/answer         -> submit an answer (AJAX or form)
    /interview/<id>/results        -> final report with CGPA, pre-assessment & level-by-level metrics
"""

import json
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, abort, flash
from flask_login import current_user
from app.security import login_required_unless_static
from app.extensions import db
from app.models import InterviewSession, Answer
from app.services import ai_engine, question_bank

interview_bp = Blueprint("interview", __name__)


@interview_bp.route("/start", methods=["GET", "POST"])
@login_required_unless_static
def start():
    """Configure and start a new interview session."""
    if request.method == "POST":
        cgpa_val = request.form.get("cgpa", "").strip()
        try:
            cgpa = round(float(cgpa_val), 2)
            if cgpa < 0.0 or cgpa > 10.0:
                raise ValueError()
        except (ValueError, TypeError):
            flash("Please enter a valid CGPA between 0.00 and 10.00", "danger")
            return render_template("interview/start.html")

        # Save CGPA to current user
        current_user.cgpa = cgpa

        role = (current_user.target_role or "Software Engineer").strip()
        pre_questions = question_bank.get_pre_assessment_questions()

        session = InterviewSession(
            user_id=current_user.id,
            role=role,
            category="mixed",
            difficulty="medium",
            cgpa=cgpa,
            phase="pre_assessment",
            total_questions=len(pre_questions),
            answered_count=0,
        )
        db.session.add(session)
        db.session.flush()

        for q in pre_questions:
            ans = Answer(
                session_id=session.id,
                phase="pre_assessment",
                question_type="mcq",
                question_index=q["index"],
                question_text=q["q"],
                question_category=q.get("category", "mentality"),
                options=json.dumps(q.get("options", [])),
                correct_option=q.get("correct_option"),
                explanation=q.get("explanation"),
                model_answer=q.get("correct_option"),
                marks_allocated=1.0,
            )
            db.session.add(ans)

        db.session.commit()
        return redirect(url_for("interview.session", session_id=session.id))

    return render_template("interview/start.html")


@interview_bp.route("/play")
@login_required_unless_static
def play():
    """Client-side interview player used by the static Vercel export."""
    return render_template(
        "interview/play.html",
        sections_config=question_bank.get_sections_config(),
    )


@interview_bp.route("/report")
@login_required_unless_static
def static_report():
    """Client-side results page used by the static Vercel export."""
    return render_template("interview/results_static.html")


@interview_bp.route("/<int:session_id>")
@login_required_unless_static
def session(session_id):
    """Render the interview session page with current question or transition modal."""
    sess = InterviewSession.query.get_or_404(session_id)
    if sess.user_id != current_user.id:
        abort(403)
    if sess.status == "completed":
        return redirect(url_for("interview.results", session_id=sess.id))

    sections_config = question_bank.get_sections_config()

    # If pre-assessment completed and waiting to start main
    if sess.phase == "pre_assessment_completed":
        return render_template(
            "interview/session.html",
            session=sess,
            answer=None,
            pre_assessment_summary={
                "score": sess.pre_assessment_score or 0,
                "category": sess.pre_assessment_category or "Medium",
                "difficulty": sess.difficulty,
                "summary": question_bank.evaluate_pre_assessment(sess.pre_assessment_score or 0)["summary"],
            },
            sections_config=sections_config,
            progress={"current": 10, "total": 10, "answered": 10},
        )

    # Find the first unanswered question in current phase
    current_answer = (
        Answer.query
        .filter_by(session_id=sess.id, phase=sess.phase)
        .filter(Answer.user_answer.is_(None))
        .order_by(Answer.question_index)
        .first()
    )

    if not current_answer:
        if sess.phase == "pre_assessment":
            # All 10 pre-assessment questions answered — evaluate
            pre_answers = Answer.query.filter_by(session_id=sess.id, phase="pre_assessment").all()
            correct_count = sum(
                1 for a in pre_answers
                if a.user_answer and a.user_answer.strip() == (a.correct_option or "").strip()
            )
            eval_res = question_bank.evaluate_pre_assessment(correct_count)
            sess.pre_assessment_score = eval_res["score"]
            sess.pre_assessment_category = eval_res["category"]
            sess.difficulty = eval_res["difficulty"]
            sess.phase = "pre_assessment_completed"
            db.session.commit()

            return render_template(
                "interview/session.html",
                session=sess,
                answer=None,
                pre_assessment_summary=eval_res,
                sections_config=sections_config,
                progress={"current": 10, "total": 10, "answered": 10},
            )
        else:
            # All 60 main questions answered — finalize session
            sess.mark_completed()
            db.session.commit()
            return redirect(url_for("interview.results", session_id=sess.id))

    total = Answer.query.filter_by(session_id=sess.id, phase=sess.phase).count()
    answered = Answer.query.filter_by(session_id=sess.id, phase=sess.phase).filter(Answer.user_answer.isnot(None)).count()
    options = json.loads(current_answer.options) if current_answer.options else []

    return render_template(
        "interview/session.html",
        session=sess,
        answer=current_answer,
        options=options,
        sections_config=sections_config,
        progress={"current": current_answer.question_index, "total": total, "answered": answered},
    )


@interview_bp.route("/<int:session_id>/start_main", methods=["GET", "POST"])
@login_required_unless_static
def start_main(session_id):
    """Transition from pre-assessment to the 60-question main practice test across 6 levels."""
    sess = InterviewSession.query.get_or_404(session_id)
    if sess.user_id != current_user.id:
        abort(403)
    if sess.status == "completed":
        return redirect(url_for("interview.results", session_id=sess.id))

    # Initialize 60 questions if not already initialized
    existing_main_count = Answer.query.filter_by(session_id=sess.id, phase="main").count()
    if existing_main_count < 60:
        # Delete any partial main answers if re-triggering
        Answer.query.filter_by(session_id=sess.id, phase="main").delete()

        questions = question_bank.get_main_practice_questions(
            role=sess.role,
            difficulty=sess.difficulty,
        )

        for q in questions:
            ans = Answer(
                session_id=sess.id,
                phase="main",
                section_number=q.get("section_number"),
                section_name=q.get("section_name"),
                marks_allocated=q.get("marks_allocated", 1.5),
                question_type=q["type"],
                question_index=q["index"],
                question_text=q["q"],
                question_category=q["category"],
                options=json.dumps(q.get("options", [])) if q.get("options") else None,
                correct_option=q.get("correct_option"),
                explanation=q.get("explanation"),
                model_answer=q.get("model_answer") or q.get("correct_option"),
                keywords_expected=json.dumps(q.get("keywords_list", [])),
            )
            db.session.add(ans)

        sess.phase = "main"
        sess.total_questions = len(questions)
        sess.answered_count = 0
        db.session.commit()

    return redirect(url_for("interview.session", session_id=sess.id))


@interview_bp.route("/<int:session_id>/answer", methods=["POST"])
@login_required_unless_static
def submit_answer(session_id):
    """Submit an answer for the current question. Returns JSON for AJAX."""
    sess = InterviewSession.query.get_or_404(session_id)
    if sess.user_id != current_user.id:
        abort(403)
    if sess.status == "completed":
        return jsonify({"error": "Session already completed"}), 400

    data = request.get_json() if request.is_json else request.form
    answer_id = data.get("answer_id")
    user_answer = (data.get("user_answer") or "").strip()
    time_taken = int(data.get("time_taken") or 0)

    answer = Answer.query.get_or_404(answer_id)
    if answer.session_id != sess.id:
        abort(403)

    if answer.question_type == "mcq":
        correct_opt = (answer.correct_option or "").strip()
        is_correct = (user_answer == correct_opt)
        score = 100.0 if is_correct else 0.0
        confidence = 1.0 if is_correct else 0.3
        if is_correct:
            feedback = f"✓ Correct! {answer.explanation or ''}"
            strengths = ["Accurate selection: Demonstrated clear conceptual grasp of this topic."]
            improvements = []
        else:
            feedback = f"✗ Incorrect. The optimal answer is: {answer.correct_option}. {answer.explanation or ''}"
            strengths = []
            improvements = [f"Recommended review: {answer.question_category.replace('_', ' ').title()}."]
        keyword_match = []
    else:  # descriptive
        expected_keywords = json.loads(answer.keywords_expected) if answer.keywords_expected else []
        result = ai_engine.score_answer(
            question=answer.question_text,
            user_answer=user_answer,
            expected_keywords=expected_keywords,
            model_answer=answer.model_answer,
            difficulty=sess.difficulty,
        )
        score = result["score"]
        confidence = result["confidence"]
        feedback = result["feedback"]
        strengths = result["strengths"]
        improvements = result["improvements"]
        keyword_match = result.get("keyword_match", [])

    answer.user_answer = user_answer
    answer.score = score
    answer.confidence = confidence
    answer.feedback = feedback
    answer.strengths = json.dumps(strengths)
    answer.improvements = json.dumps(improvements)
    answer.keywords_matched = json.dumps(keyword_match)
    answer.time_taken_seconds = time_taken
    sess.answered_count += 1
    db.session.commit()

    # Check phase completion
    if sess.phase == "pre_assessment":
        remaining_pre = Answer.query.filter_by(session_id=sess.id, phase="pre_assessment").filter(Answer.user_answer.is_(None)).count()
        if remaining_pre == 0:
            pre_answers = Answer.query.filter_by(session_id=sess.id, phase="pre_assessment").all()
            correct_count = sum(
                1 for a in pre_answers
                if a.user_answer and a.user_answer.strip() == (a.correct_option or "").strip()
            )
            eval_res = question_bank.evaluate_pre_assessment(correct_count)
            sess.pre_assessment_score = eval_res["score"]
            sess.pre_assessment_category = eval_res["category"]
            sess.difficulty = eval_res["difficulty"]
            sess.phase = "pre_assessment_completed"
            db.session.commit()

            return jsonify({
                "completed": False,
                "pre_assessment_completed": True,
                "score": eval_res["score"],
                "category": eval_res["category"],
                "calibrated_difficulty": eval_res["difficulty"],
                "summary": eval_res["summary"],
                "feedback": feedback,
                "strengths": strengths,
                "improvements": improvements,
                "start_main_url": url_for("interview.start_main", session_id=sess.id),
                "redirect": url_for("interview.session", session_id=sess.id),
            })
    elif sess.phase == "main":
        remaining_main = Answer.query.filter_by(session_id=sess.id, phase="main").filter(Answer.user_answer.is_(None)).count()
        if remaining_main == 0:
            sess.mark_completed()
            db.session.commit()
            return jsonify({
                "completed": True,
                "redirect": url_for("interview.results", session_id=sess.id),
                "score": score,
                "feedback": feedback,
                "strengths": strengths,
                "improvements": improvements,
            })

    # Next question in current phase
    next_answer = (
        Answer.query
        .filter_by(session_id=sess.id, phase=sess.phase)
        .filter(Answer.user_answer.is_(None))
        .order_by(Answer.question_index)
        .first()
    )

    next_options = json.loads(next_answer.options) if next_answer and next_answer.options else []

    return jsonify({
        "completed": False,
        "score": score,
        "feedback": feedback,
        "strengths": strengths,
        "improvements": improvements,
        "next_question": {
            "answer_id": next_answer.id if next_answer else None,
            "index": next_answer.question_index if next_answer else None,
            "text": next_answer.question_text if next_answer else None,
            "category": next_answer.question_category if next_answer else None,
            "section_number": next_answer.section_number if next_answer else None,
            "section_name": next_answer.section_name if next_answer else None,
            "marks_allocated": next_answer.marks_allocated if next_answer else 1.0,
            "type": next_answer.question_type if next_answer else "descriptive",
            "options": next_options,
        } if next_answer else None,
    })


@interview_bp.route("/<int:session_id>/results")
@login_required_unless_static
def results(session_id):
    """Display final interview results with 6-level mark and percentage breakdown."""
    sess = InterviewSession.query.get_or_404(session_id)
    if sess.user_id != current_user.id:
        abort(403)
    if sess.status != "completed":
        sess.mark_completed()
        db.session.commit()

    answers = sess.answers.filter_by(phase="main").all()
    if not answers:
        answers = sess.answers.all()

    sections_config = question_bank.get_sections_config()
    section_map = {s["level"]: s for s in sections_config}

    # Aggregate level / section scores
    level_data = {}
    cat_scores = {}
    mcq_scores = []
    desc_scores = []

    for a in answers:
        # Category summary
        cat = a.question_category or "uncategorized"
        cat_scores.setdefault(cat, []).append(a.score)
        if a.question_type == "mcq":
            mcq_scores.append(a.score)
        else:
            desc_scores.append(a.score)

        # Section / Level breakdown
        sec_num = a.section_number or 1
        sec_info = section_map.get(sec_num, {
            "level": sec_num,
            "name": f"Level {sec_num}",
            "title": f"Level {sec_num}",
            "marks": 15.0,
            "percentage": 15,
        })

        if sec_num not in level_data:
            level_data[sec_num] = {
                "level": sec_num,
                "name": sec_info.get("name", f"Level {sec_num}"),
                "title": sec_info.get("title", f"Level {sec_num}"),
                "total_marks": sec_info.get("marks", 15.0),
                "percentage_weight": sec_info.get("percentage", 15),
                "earned_marks": 0.0,
                "question_count": 0,
                "mcq_count": 0,
                "desc_count": 0,
            }

        mark_weight = a.marks_allocated or 1.0
        earned = ((a.score or 0.0) / 100.0) * mark_weight
        level_data[sec_num]["earned_marks"] += earned
        level_data[sec_num]["question_count"] += 1
        if a.question_type == "mcq":
            level_data[sec_num]["mcq_count"] += 1
        else:
            level_data[sec_num]["desc_count"] += 1

    level_summary = []
    for sec_num in sorted(level_data.keys()):
        ld = level_data[sec_num]
        pct = round((ld["earned_marks"] / ld["total_marks"]) * 100.0, 1) if ld["total_marks"] > 0 else 0
        level_summary.append({
            "level": ld["level"],
            "name": ld["name"],
            "title": ld["title"],
            "total_marks": ld["total_marks"],
            "earned_marks": round(ld["earned_marks"], 1),
            "percentage_weight": ld["percentage_weight"],
            "achieved_percentage": pct,
            "question_count": ld["question_count"],
            "mcq_count": ld["mcq_count"],
            "desc_count": ld["desc_count"],
        })

    cat_summary = [
        {"category": k.replace("_", " ").title(),
         "avg": round(sum(v) / len(v), 1),
         "count": len(v)}
        for k, v in cat_scores.items()
    ]

    total_marks_earned = sum(l["earned_marks"] for l in level_summary)
    total_marks_possible = sum(l["total_marks"] for l in level_summary)

    metrics = {
        "mcq_avg": round(sum(mcq_scores) / len(mcq_scores), 1) if mcq_scores else 0,
        "mcq_count": len(mcq_scores),
        "desc_avg": round(sum(desc_scores) / len(desc_scores), 1) if desc_scores else 0,
        "desc_count": len(desc_scores),
        "total_marks_earned": round(total_marks_earned, 1),
        "total_marks_possible": round(total_marks_possible, 1),
    }

    return render_template(
        "interview/results.html",
        session=sess,
        answers=answers,
        cat_summary=cat_summary,
        level_summary=level_summary,
        metrics=metrics,
    )


@interview_bp.route("/history")
@login_required_unless_static
def history():
    """List all interview sessions for current user."""
    if not current_user.is_authenticated:
        return render_template("interview/history.html", sessions=[])
    sessions = (
        InterviewSession.query
        .filter_by(user_id=current_user.id)
        .order_by(InterviewSession.started_at.desc())
        .all()
    )
    return render_template("interview/history.html", sessions=sessions)
