"""
InterviewMind - Interview Flow & Pre-Assessment Tests
======================================================
Tests for:
1. 'Configure Mock Interview' page:
   - Target Role field removed
   - Difficulty Level field removed
   - Number of Questions field removed
   - CGPA field added and saved
2. Initial Assessment Phase:
   - 10 common questions evaluating mentality, study habits, preparation level
   - Scoring & Categorization logic:
     - ~5 marks -> "Medium"
     - ~7 marks -> "Above Medium"
     - 10 marks -> "Excellent"
3. Main Practice Interview:
   - Exactly 60 questions
   - Dynamic difficulty adjustment:
     - Medium -> Easy
     - Above Medium -> Medium
     - Excellent -> Hard
   - Topic Breakdown: 40 Technical, 20 Logical/Common
   - Question Formats: 48 MCQ (majority), 12 Descriptive (10 to 15 range)
4. UI / Styling:
   - Dropdown text color is black
"""

from app.services.question_bank import question_bank
from app.models import InterviewSession, Answer, User
from app.extensions import db


def test_configure_page_fields(logged_in_client):
    """Verify Configure Mock Interview page fields."""
    response = logged_in_client.get("/interview/start")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # CGPA field must be present
    assert 'name="cgpa"' in html
    assert 'CGPA' in html

    # Target Role, Difficulty, and Number of Questions must NOT be present
    assert 'name="role"' not in html
    assert 'name="difficulty"' not in html
    assert 'name="count"' not in html


def test_pre_assessment_questions_count_and_categories():
    """Verify 10 pre-assessment questions evaluating mentality, study habits, preparation level."""
    questions = question_bank.get_pre_assessment_questions()
    assert len(questions) == 10

    categories = {q["category"] for q in questions}
    assert "mentality" in categories
    assert "study_habits" in categories
    assert "preparation_level" in categories

    for q in questions:
        assert q["type"] == "mcq"
        assert len(q["options"]) == 4
        assert q["correct_option"] in q["options"]
        assert q["explanation"]


def test_scoring_and_categorization_logic():
    """Verify pre-assessment scoring & categorization logic:
    ~5 marks -> Medium (calibrated to Easy)
    ~7 marks -> Above Medium (calibrated to Medium)
    10 marks -> Excellent (calibrated to Hard)
    """
    # Score ~5 marks
    res_5 = question_bank.evaluate_pre_assessment(5.0)
    assert res_5["category"] == "Medium"
    assert res_5["difficulty"] == "easy"

    # Score ~7 marks
    res_7 = question_bank.evaluate_pre_assessment(7.0)
    assert res_7["category"] == "Above Medium"
    assert res_7["difficulty"] == "medium"

    # Score 10 marks
    res_10 = question_bank.evaluate_pre_assessment(10.0)
    assert res_10["category"] == "Excellent"
    assert res_10["difficulty"] == "hard"


def test_main_practice_60_questions_breakdown_and_formats():
    """Verify main practice interview has exactly 60 questions:
    - 40 Technical / Job Role-specific
    - 20 Logical reasoning, problem-solving, common
    - Majority MCQ (48)
    - Exactly 10 to 15 Descriptive (12)
    """
    for diff in ["easy", "medium", "hard"]:
        questions = question_bank.get_main_practice_questions(role="Software Engineer", difficulty=diff)
        assert len(questions) == 60

        technical = [q for q in questions if q["category"] in ("technical", "system_design", "coding")]
        logical_common = [q for q in questions if q["category"] in ("logical_reasoning", "behavioral", "hr")]

        assert len(technical) == 40
        assert len(logical_common) == 20

        mcq = [q for q in questions if q["type"] == "mcq"]
        descriptive = [q for q in questions if q["type"] == "descriptive"]

        assert len(mcq) == 48
        assert len(descriptive) == 12
        assert 10 <= len(descriptive) <= 15
        assert len(mcq) > len(descriptive)


def test_start_interview_flow_with_cgpa(logged_in_client, app):
    """Verify starting an interview with CGPA initiates pre-assessment with 10 questions."""
    response = logged_in_client.post("/interview/start", data={
        "cgpa": "8.75"
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        sess = InterviewSession.query.order_by(InterviewSession.id.desc()).first()
        assert sess is not None
        assert sess.cgpa == 8.75
        assert sess.phase == "pre_assessment"
        assert sess.total_questions == 10

        answers = Answer.query.filter_by(session_id=sess.id).all()
        assert len(answers) == 10
        for a in answers:
            assert a.phase == "pre_assessment"
            assert a.question_type == "mcq"


def test_complete_interview_lifecycle(logged_in_client, app):
    """End-to-end test:
    1. Start with CGPA
    2. Answer 10 pre-assessment questions with score 7/10 -> Above Medium -> difficulty Medium
    3. Start 60-question main practice
    4. Verify 60 questions created with calibrated difficulty
    """
    # 1. Start
    logged_in_client.post("/interview/start", data={"cgpa": "9.10"}, follow_redirects=True)

    with app.app_context():
        sess = InterviewSession.query.order_by(InterviewSession.id.desc()).first()
        sess_id = sess.id
        pre_answers = Answer.query.filter_by(session_id=sess_id, phase="pre_assessment").order_by(Answer.question_index).all()

    # 2. Answer 10 pre-assessment questions (7 correct, 3 incorrect)
    for i, a in enumerate(pre_answers):
        user_choice = a.correct_option if i < 7 else "Incorrect Distractor"
        resp = logged_in_client.post(f"/interview/{sess_id}/answer", json={
            "answer_id": a.id,
            "user_answer": user_choice,
            "time_taken": 10,
        })
        assert resp.status_code == 200

    with app.app_context():
        sess = InterviewSession.query.get(sess_id)
        assert sess.phase == "pre_assessment_completed"
        assert sess.pre_assessment_score == 7.0
        assert sess.pre_assessment_category == "Above Medium"
        assert sess.difficulty == "medium"

    # 3. Start main practice
    start_main_resp = logged_in_client.post(f"/interview/{sess_id}/start_main", follow_redirects=True)
    assert start_main_resp.status_code == 200

    with app.app_context():
        sess = InterviewSession.query.get(sess_id)
        assert sess.phase == "main"
        assert sess.total_questions == 60
        assert sess.difficulty == "medium"

        main_answers = Answer.query.filter_by(session_id=sess_id, phase="main").all()
        assert len(main_answers) == 60

        # Check section allocation
        levels = {a.section_number for a in main_answers}
        assert levels == {1, 2, 3, 4, 5, 6}

        total_marks = sum(a.marks_allocated for a in main_answers)
        assert round(total_marks, 1) == 100.0


def test_six_sections_levels_marks_and_percentages():
    """Verify 6 sections / levels with explicit marks and percentages."""
    sections = question_bank.get_sections_config()
    assert len(sections) == 6

    total_marks = sum(s["marks"] for s in sections)
    total_percentage = sum(s["percentage"] for s in sections)
    total_questions = sum(s["total_questions"] for s in sections)

    assert total_marks == 100.0
    assert total_percentage == 100
    assert total_questions == 60

    for i, sec in enumerate(sections, start=1):
        assert sec["level"] == i
        assert sec["total_questions"] == 10
        assert sec["marks"] > 0
        assert sec["percentage"] > 0
        assert sec["mark_per_question"] == sec["marks"] / sec["total_questions"]


def test_option_shuffling():
    """Verify that multiple-choice options are shuffled."""
    pre_q = question_bank.get_pre_assessment_questions()
    for q in pre_q:
        assert q["correct_option"] in q["options"]
        assert len(q["options"]) == 4

    main_q = question_bank.get_main_practice_questions(role="Software Engineer", difficulty="medium")
    mcq_questions = [q for q in main_q if q["type"] == "mcq"]
    assert len(mcq_questions) == 48

    for q in mcq_questions:
        assert q["correct_option"] in q["options"]
        assert len(q["options"]) == 4

    # Run multiple times to observe shuffling across independent generations
    q1 = question_bank.get_main_practice_questions(difficulty="medium")
    q2 = question_bank.get_main_practice_questions(difficulty="medium")
    # Across 48 MCQs, at least one question will have different option order
    order_differs = False
    for item1, item2 in zip(q1, q2):
        if item1["type"] == "mcq" and item1.get("options") != item2.get("options"):
            order_differs = True
            break
    assert order_differs, "Expected randomized option ordering across questions"


def test_dropdown_text_color_css(client):
    """Verify dropdown styling in style.css has color: #000000 for visibility."""
    resp = client.get("/static/css/style.css")
    assert resp.status_code == 200
    css = resp.data.decode("utf-8")
    assert "select" in css
    assert "color: #000000 !important;" in css
    assert "background-color: #ffffff !important;" in css

