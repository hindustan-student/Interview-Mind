"""
InterviewMind - Question Bank Service
======================================
Generates and serves interview questions across categories, roles, and difficulty levels.

Provides:
- 10-question Pre-Assessment (Mentality, Study Habits, Preparation Level) with shuffled options
- Scoring & Categorization Logic (Medium, Above Medium, Excellent)
- 60-question Main Practice Interview structured into 6 Sections / Levels:
    - Level 1: Core CS Fundamentals (10 Qs, 15 Marks, 15%)
    - Level 2: Data Structures & Algorithms (10 Qs, 20 Marks, 20%)
    - Level 3: Databases & Backend Systems (10 Qs, 15 Marks, 15%)
    - Level 4: System Architecture & Cloud/DevOps (10 Qs, 20 Marks, 20%)
    - Level 5: Logical Reasoning & Aptitude (10 Qs, 15 Marks, 15%)
    - Level 6: Behavioral & Problem-Solving Leadership (10 Qs, 15 Marks, 15%)
    Total = 60 questions, 100 Marks (100%), with shuffled options on all MCQs.
"""

from __future__ import annotations
import copy
import random
from typing import List, Dict, Optional, Tuple

from app.services.questions_data import (
    PRE_ASSESSMENT_QUESTIONS,
    EASY_TECHNICAL_MCQ, EASY_TECHNICAL_DESC, EASY_LOGICAL_MCQ, EASY_LOGICAL_DESC,
    MEDIUM_TECHNICAL_MCQ, MEDIUM_TECHNICAL_DESC, MEDIUM_LOGICAL_MCQ, MEDIUM_LOGICAL_DESC,
    HARD_TECHNICAL_MCQ, HARD_TECHNICAL_DESC, HARD_LOGICAL_MCQ, HARD_LOGICAL_DESC,
)

# 6 Levels / Sections Configuration with mark and percentage allocation
SECTIONS_CONFIG = [
    {
        "level": 1,
        "name": "Level 1: Core CS Fundamentals",
        "title": "Core CS Fundamentals",
        "description": "Operating Systems, Networking Protocols, and OOP Principles",
        "total_questions": 10,
        "marks": 15.0,
        "percentage": 15,
        "mark_per_question": 1.5,
        "category": "technical",
    },
    {
        "level": 2,
        "name": "Level 2: Data Structures & Algorithms",
        "title": "Data Structures & Algorithms",
        "description": "Arrays, Trees, Graphs, Sorting, and Time/Space Complexity",
        "total_questions": 10,
        "marks": 20.0,
        "percentage": 20,
        "mark_per_question": 2.0,
        "category": "technical",
    },
    {
        "level": 3,
        "name": "Level 3: Databases & Backend Systems",
        "title": "Databases & Backend Systems",
        "description": "SQL Queries, ACID Transactions, Indexing, and REST APIs",
        "total_questions": 10,
        "marks": 15.0,
        "percentage": 15,
        "mark_per_question": 1.5,
        "category": "technical",
    },
    {
        "level": 4,
        "name": "Level 4: System Architecture & Cloud/DevOps",
        "title": "System Architecture & Cloud/DevOps",
        "description": "Distributed Systems, Caching, Concurrency, and CI/CD",
        "total_questions": 10,
        "marks": 20.0,
        "percentage": 20,
        "mark_per_question": 2.0,
        "category": "technical",
    },
    {
        "level": 5,
        "name": "Level 5: Logical Reasoning & Aptitude",
        "title": "Logical Reasoning & Aptitude",
        "description": "Puzzles, Deductive Logic, Numerical Reasoning, and Data Interpretation",
        "total_questions": 10,
        "marks": 15.0,
        "percentage": 15,
        "mark_per_question": 1.5,
        "category": "logical_reasoning",
    },
    {
        "level": 6,
        "name": "Level 6: Behavioral & Problem-Solving Leadership",
        "title": "Behavioral & Problem-Solving Leadership",
        "description": "STAR Competencies, Production Incident Triage, and Team Collaboration",
        "total_questions": 10,
        "marks": 15.0,
        "percentage": 15,
        "mark_per_question": 1.5,
        "category": "behavioral",
    },
]


class QuestionBank:
    """Service for fetching, generating, and scoring interview questions."""

    CATEGORIES = ["technical", "behavioral", "system_design", "coding", "hr", "situational", "logical_reasoning"]

    def get_sections_config(self) -> List[Dict]:
        """Return the 6 sections configuration with marks and percentages."""
        return copy.deepcopy(SECTIONS_CONFIG)

    def get_pre_assessment_questions(self) -> List[Dict]:
        """Return the 10 common pre-assessment questions with shuffled options."""
        questions = copy.deepcopy(PRE_ASSESSMENT_QUESTIONS)
        for i, q in enumerate(questions, start=1):
            q["index"] = i
            q["phase"] = "pre_assessment"
            q["type"] = "mcq"
            if q.get("options"):
                shuffled = list(q["options"])
                random.shuffle(shuffled)
                q["options"] = shuffled
        return questions

    def evaluate_pre_assessment(self, score: float) -> Dict[str, any]:
        """Score & Categorization Logic:
        - Score of ~5 marks (score <= 5.5): 'Medium' -> Difficulty: 'easy'
        - Score of ~7 marks (5.5 < score <= 8.5): 'Above Medium' -> Difficulty: 'medium'
        - Score of 10 marks (score > 8.5): 'Excellent' -> Difficulty: 'hard'
        """
        if score <= 5.5:
            category = "Medium"
            difficulty = "easy"
            summary = "Your pre-assessment indicates emerging study habits. Your 60-question practice interview is calibrated to Easy difficulty across all 6 levels to solidify your core foundations."
        elif score <= 8.5:
            category = "Above Medium"
            difficulty = "medium"
            summary = "Your pre-assessment demonstrates disciplined preparation and consistent problem-solving. Your 60-question practice interview is calibrated to Medium difficulty across all 6 levels."
        else:
            category = "Excellent"
            difficulty = "hard"
            summary = "Outstanding pre-assessment performance reflecting deep conceptual clarity and resilience. Your 60-question practice interview is calibrated to Tough/Hard difficulty across all 6 levels."

        return {
            "score": round(score, 1),
            "category": category,
            "difficulty": difficulty,
            "summary": summary,
        }

    def get_main_practice_questions(
        self,
        role: str = "Software Engineer",
        difficulty: str = "medium",
    ) -> List[Dict]:
        """Generate exactly 60 practice questions structured into 6 sections / levels:
        - Level 1: Core CS Fundamentals (10 Qs, 15 Marks, 15%)
        - Level 2: Data Structures & Algorithms (10 Qs, 20 Marks, 20%)
        - Level 3: Databases & Backend Systems (10 Qs, 15 Marks, 15%)
        - Level 4: System Architecture & Cloud/DevOps (10 Qs, 20 Marks, 20%)
        - Level 5: Logical Reasoning & Aptitude (10 Qs, 15 Marks, 15%)
        - Level 6: Behavioral & Problem-Solving Leadership (10 Qs, 15 Marks, 15%)
        Total = 60 questions, 100 Marks (100%), with shuffled options on all MCQs.
        """
        diff = difficulty.lower().strip()
        if diff not in ("easy", "medium", "hard"):
            diff = "medium"

        if diff == "easy":
            tech_mcq = copy.deepcopy(EASY_TECHNICAL_MCQ)
            tech_desc = copy.deepcopy(EASY_TECHNICAL_DESC)
            logic_mcq = copy.deepcopy(EASY_LOGICAL_MCQ)
            logic_desc = copy.deepcopy(EASY_LOGICAL_DESC)
        elif diff == "hard":
            tech_mcq = copy.deepcopy(HARD_TECHNICAL_MCQ)
            tech_desc = copy.deepcopy(HARD_TECHNICAL_DESC)
            logic_mcq = copy.deepcopy(HARD_LOGICAL_MCQ)
            logic_desc = copy.deepcopy(HARD_LOGICAL_DESC)
        else:  # medium
            tech_mcq = copy.deepcopy(MEDIUM_TECHNICAL_MCQ)
            tech_desc = copy.deepcopy(MEDIUM_TECHNICAL_DESC)
            logic_mcq = copy.deepcopy(MEDIUM_LOGICAL_MCQ)
            logic_desc = copy.deepcopy(MEDIUM_LOGICAL_DESC)

        # Shuffle options on all MCQs
        for item in tech_mcq + logic_mcq:
            if item.get("options"):
                shuffled = list(item["options"])
                random.shuffle(shuffled)
                item["options"] = shuffled

        # Slice 32 Technical MCQ, 8 Technical Desc, 16 Logical MCQ, 4 Logical Desc
        selected_tech_mcq = tech_mcq[:32]
        selected_tech_desc = tech_desc[:8]
        selected_logic_mcq = logic_mcq[:16]
        selected_logic_desc = logic_desc[:4]

        # Annotate items
        for item in selected_tech_mcq:
            item["type"] = "mcq"
            item["role"] = role
            item["diff"] = diff

        for item in selected_tech_desc:
            item["type"] = "descriptive"
            item["role"] = role
            item["diff"] = diff
            item["keywords_list"] = [k.strip() for k in item.get("kw", "").split(",") if k.strip()]

        for item in selected_logic_mcq:
            item["type"] = "mcq"
            item["role"] = role
            item["diff"] = diff

        for item in selected_logic_desc:
            item["type"] = "descriptive"
            item["role"] = role
            item["diff"] = diff
            item["keywords_list"] = [k.strip() for k in item.get("kw", "").split(",") if k.strip()]

        # Assemble into 6 Sections / Levels (10 questions each):
        # Level 1: 8 Tech MCQ (0-8) + 2 Tech Desc (0-2) -> 15 Marks (15%), 1.5 Marks/Q
        sec1_qs = selected_tech_mcq[0:8] + selected_tech_desc[0:2]
        self._tag_section(sec1_qs, SECTIONS_CONFIG[0])

        # Level 2: 8 Tech MCQ (8-16) + 2 Tech Desc (2-4) -> 20 Marks (20%), 2.0 Marks/Q
        sec2_qs = selected_tech_mcq[8:16] + selected_tech_desc[2:4]
        self._tag_section(sec2_qs, SECTIONS_CONFIG[1])

        # Level 3: 8 Tech MCQ (16-24) + 2 Tech Desc (4-6) -> 15 Marks (15%), 1.5 Marks/Q
        sec3_qs = selected_tech_mcq[16:24] + selected_tech_desc[4:6]
        self._tag_section(sec3_qs, SECTIONS_CONFIG[2])

        # Level 4: 8 Tech MCQ (24-32) + 2 Tech Desc (6-8) -> 20 Marks (20%), 2.0 Marks/Q
        sec4_qs = selected_tech_mcq[24:32] + selected_tech_desc[6:8]
        self._tag_section(sec4_qs, SECTIONS_CONFIG[3])

        # Level 5: 8 Logic MCQ (0-8) + 2 Logic Desc (0-2) -> 15 Marks (15%), 1.5 Marks/Q
        sec5_qs = selected_logic_mcq[0:8] + selected_logic_desc[0:2]
        self._tag_section(sec5_qs, SECTIONS_CONFIG[4])

        # Level 6: 8 Logic MCQ (8-16) + 2 Logic Desc (2-4) -> 15 Marks (15%), 1.5 Marks/Q
        sec6_qs = selected_logic_mcq[8:16] + selected_logic_desc[2:4]
        self._tag_section(sec6_qs, SECTIONS_CONFIG[5])

        combined = sec1_qs + sec2_qs + sec3_qs + sec4_qs + sec5_qs + sec6_qs

        for i, q in enumerate(combined, start=1):
            q["index"] = i
            q["phase"] = "main"

        return combined

    def _tag_section(self, questions: List[Dict], sec_config: Dict) -> None:
        """Assign section level, marks, and percentage allocation to questions."""
        for q in questions:
            q["section_number"] = sec_config["level"]
            q["section_name"] = sec_config["name"]
            q["section_title"] = sec_config["title"]
            q["marks_allocated"] = sec_config["mark_per_question"]
            q["section_marks"] = sec_config["marks"]
            q["section_percentage"] = sec_config["percentage"]
            if sec_config["level"] <= 4:
                q["category"] = "technical"
            else:
                q["category"] = sec_config["category"]

    def get_questions(
        self,
        role: str = "Software Engineer",
        category: str = "mixed",
        difficulty: str = "medium",
        count: int = 5,
    ) -> List[Dict]:
        """Legacy helper for public question browsing."""
        pool = []
        source_mcq = copy.deepcopy(MEDIUM_TECHNICAL_MCQ + MEDIUM_LOGICAL_MCQ)
        source_desc = copy.deepcopy(MEDIUM_TECHNICAL_DESC + MEDIUM_LOGICAL_DESC)

        for item in source_mcq:
            it = dict(item)
            it["diff"] = "medium"
            it["keywords_list"] = []
            if it.get("options"):
                shuffled = list(it["options"])
                random.shuffle(shuffled)
                it["options"] = shuffled
            pool.append(it)

        for item in source_desc:
            it = dict(item)
            it["diff"] = "medium"
            it["keywords_list"] = [k.strip() for k in it.get("kw", "").split(",") if k.strip()]
            pool.append(it)

        if category != "mixed":
            filtered = [p for p in pool if p.get("category") == category]
            if filtered:
                pool = filtered

        random.shuffle(pool)
        chosen = pool[:count]
        for i, item in enumerate(chosen, start=1):
            item["index"] = i
            item["role"] = role
        return chosen

    def list_categories(self) -> List[Dict]:
        """Return category list for UI."""
        return [
            {"key": "technical", "label": "Technical", "count": 40},
            {"key": "logical_reasoning", "label": "Logical Reasoning", "count": 20},
            {"key": "behavioral", "label": "Behavioral", "count": 10},
            {"key": "system_design", "label": "System Design", "count": 10},
        ]

    def seed_defaults(self) -> int:
        """Seed DB question bank."""
        from app.models import QuestionBankItem
        from app.extensions import db
        if QuestionBankItem.query.first():
            return 0
        count = 0
        all_mcq = EASY_TECHNICAL_MCQ + MEDIUM_TECHNICAL_MCQ + HARD_TECHNICAL_MCQ
        for item in all_mcq[:30]:
            row = QuestionBankItem(
                category=item.get("category", "technical"),
                difficulty="medium",
                question_text=item["q"],
                model_answer=item.get("correct_option", ""),
                expected_keywords=item.get("category", ""),
            )
            db.session.add(row)
            count += 1
        db.session.commit()
        return count


question_bank = QuestionBank()
