"""
InterviewMind - API Blueprint (AJAX endpoints)
================================================
Lightweight REST-ish API used by the front-end during interview sessions.
"""

import json
from flask import Blueprint, request, jsonify, url_for
from flask_login import current_user
from app.security import login_required_unless_static
from app.extensions import db
from app.models import InterviewSession, Answer
from app.services import ai_engine, question_bank

api_bp = Blueprint("api", __name__)


@api_bp.route("/categories")
def categories():
    """List all interview categories."""
    return jsonify({"categories": question_bank.list_categories()})


@api_bp.route("/questions/sample")
def sample_questions():
    """Return a sample of questions for the front-end preview."""
    cat = request.args.get("category", "mixed")
    diff = request.args.get("difficulty", "medium")
    items = question_bank.get_questions(category=cat, difficulty=diff, count=5)
    return jsonify({"questions": [{"q": i["q"], "category": i.get("category", "technical")} for i in items]})


@api_bp.route("/interview/<int:session_id>/answer", methods=["POST"])
@login_required_unless_static
def submit_answer_api(session_id):
    """AJAX endpoint to submit an answer and get instant feedback."""
    sess = InterviewSession.query.get_or_404(session_id)
    if sess.user_id != current_user.id:
        return jsonify({"error": "forbidden"}), 403
    if sess.status == "completed":
        return jsonify({"error": "Session already completed"}), 400

    data = request.get_json() or {}
    answer_id = data.get("answer_id")
    user_answer = (data.get("user_answer") or "").strip()
    time_taken = int(data.get("time_taken") or 0)

    answer = Answer.query.get_or_404(answer_id)
    if answer.session_id != sess.id:
        return jsonify({"error": "forbidden"}), 403

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
        expected = json.loads(answer.keywords_expected) if answer.keywords_expected else []
        result = ai_engine.score_answer(
            question=answer.question_text,
            user_answer=user_answer,
            expected_keywords=expected,
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

    # Pre-assessment phase check
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

    # Next question
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
            "type": next_answer.question_type if next_answer else "descriptive",
            "options": next_options,
        } if next_answer else None,
    })
