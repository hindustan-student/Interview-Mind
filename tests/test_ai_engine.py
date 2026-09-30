"""
InterviewMind - AI Interview Engine Tests
==========================================
Unit tests for the scoring engine (pure functions, no I/O).
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.services.ai_engine import AIInterviewEngine


def test_engine_instantiation():
    engine = AIInterviewEngine()
    assert engine is not None


def test_empty_answer():
    engine = AIInterviewEngine()
    result = engine.score_answer(
        question="Tell me about yourself.",
        user_answer="",
        expected_keywords=["introduction", "role"],
    )
    assert result["score"] == 0.0
    assert result["confidence"] == 0.0
    assert result["improvements"]


def test_perfect_star_answer_scores_high():
    engine = AIInterviewEngine()
    answer = (
        "Situation: At Acme Corp, our checkout page had a 35% cart abandonment rate. "
        "Task: As the lead frontend engineer, I was responsible for reducing this within one quarter. "
        "Action: I implemented a one-page checkout, added a progress indicator, and A/B tested two layouts. "
        "Result: We reduced cart abandonment by 18% and increased conversion by 12% within 6 weeks."
    )
    result = engine.score_answer(
        question="Describe a project you led that improved a key business metric.",
        user_answer=answer,
        expected_keywords=["checkout", "frontend", "a/b", "conversion", "result"],
    )
    assert result["score"] >= 80
    assert all(result["star_breakdown"].values()), "All 4 STAR stages should be detected"
    assert result["word_count"] >= 50


def test_short_answer_scores_low():
    engine = AIInterviewEngine()
    result = engine.score_answer(
        question="Tell me about a project you led.",
        user_answer="I built a thing.",
        expected_keywords=["project", "led"],
    )
    assert result["score"] < 60
    assert "brief" in " ".join(result["improvements"]).lower()


def test_keyword_match_logic():
    engine = AIInterviewEngine()
    result = engine.score_answer(
        question="Explain REST APIs.",
        user_answer="REST APIs use HTTP methods like GET POST PUT DELETE and are stateless.",
        expected_keywords=["rest", "http", "get", "post", "stateless"],
    )
    assert set(result["keyword_match"]) >= {"rest", "http", "get", "post", "stateless"}
    assert not result["keyword_miss"]


def test_hedge_words_lower_confidence():
    engine = AIInterviewEngine()
    confident = "I led the team to deliver the project on time with 20% improvement."
    hedgy = "Um, like, I, you know, kind of led the team to, like, deliver the project, I guess."
    r1 = engine.score_answer("Q", confident, [])
    r2 = engine.score_answer("Q", hedgy, [])
    assert r1["confidence"] > r2["confidence"]


def test_difficulty_weights_differ():
    engine = AIInterviewEngine()
    w_easy = engine._difficulty_weights("easy")
    w_hard = engine._difficulty_weights("hard")
    assert w_easy != w_hard
    assert "length" in w_easy
    assert "star" in w_hard


def test_score_to_grade_thresholds():
    engine = AIInterviewEngine()
    assert "Excellent" in engine._score_to_grade(95)
    assert "Strong" in engine._score_to_grade(85)
    assert "Good" in engine._score_to_grade(75)
    assert "Insufficient" in engine._score_to_grade(20)


def test_long_answer_penalized():
    engine = AIInterviewEngine()
    long_answer = " ".join(["word"] * 1000)
    result = engine.score_answer("Q", long_answer, [])
    assert result["score"] < 100  # shouldn't be perfect due to length penalty


def test_star_breakdown_structure():
    engine = AIInterviewEngine()
    result = engine.score_answer("Q", "Situation, Task, Action, Result", [])
    assert set(result["star_breakdown"].keys()) == {"situation", "task", "action", "result"}
