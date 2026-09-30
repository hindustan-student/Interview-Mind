"""
InterviewMind - Question Bank Routes Blueprint
================================================
Lets users browse the curated question bank by category.
"""

from flask import Blueprint, render_template, request
from app.services import question_bank

questions_bp = Blueprint("questions", __name__)


@questions_bp.route("/")
def index():
    """Browse all questions, optionally filtered by category/difficulty."""
    category = request.args.get("category", "mixed")
    difficulty = request.args.get("difficulty", "mixed")

    questions = question_bank.get_questions(
        category=category,
        difficulty=difficulty,
        count=50,  # show all in browse mode
    )
    categories = question_bank.list_categories()

    return render_template(
        "questions/bank.html",
        questions=questions,
        categories=categories,
        current_category=category,
        current_difficulty=difficulty,
    )
