"""
InterviewMind - AI Interview Engine
=====================================
The rule-based AI engine that simulates a real interviewer.

Pipeline:
1. Select role + difficulty + category
2. Generate / pull questions for that role
3. Score the candidate's answer against:
   - Length / structure (STAR method detection)
   - Keyword coverage
   - Clarity proxy (avg sentence length)
   - Confidence proxy (no-hedge word count)
4. Produce textual feedback + strengths + improvements

This module is intentionally dependency-light so the academic project
runs without paid AI APIs. It can be swapped to call OpenAI / Gemini
later via the same `score_answer()` interface.

Author: InterviewMind Academic Project Team
"""

from __future__ import annotations
import re
import json
import random
import string
from typing import Dict, List, Tuple, Optional


# Hedge / filler words (low-confidence markers)
HEDGE_WORDS = {
    "um", "uh", "like", "you know", "kind of", "sort of",
    "i guess", "i think maybe", "probably", "i'm not sure",
    "i don't really know", "whatever", "stuff", "things",
}

# STAR signal words
STAR_SIGNALS = {
    "situation": ["situation", "context", "background", "scenario", "when i"],
    "task": ["task", "responsibility", "challenge", "goal", "objective", "my role"],
    "action": ["action", "did", "implemented", "decided", "approach", "i led", "i built",
                "i designed", "i created", "i managed", "i analyzed"],
    "result": ["result", "outcome", "achieved", "delivered", "improved", "reduced",
               "increased", "%", "percent", "saved", "won", "shipped"],
}

# Action verbs for resume / answer quality
ACTION_VERBS = {
    "led", "developed", "implemented", "designed", "built", "launched",
    "optimized", "analyzed", "architected", "engineered", "automated",
    "spearheaded", "orchestrated", "streamlined", "transformed", "scaled",
    "mentored", "shipped", "delivered", "reduced", "increased", "improved",
}


class AIInterviewEngine:
    """Simulates an AI interviewer with rule-based NLP scoring.

    All methods are pure (no I/O) which keeps the engine testable.
    """

    # --------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------

    def score_answer(
        self,
        question: str,
        user_answer: str,
        expected_keywords: Optional[List[str]] = None,
        model_answer: Optional[str] = None,
        difficulty: str = "medium",
    ) -> Dict:
        """Score a single interview answer.

        Returns a dict with:
            - score           (0-100 float)
            - confidence      (0-1 float)
            - keyword_match   (list[str])
            - keyword_miss    (list[str])
            - star_score      (0-4 int, STAR stages present)
            - star_breakdown  (dict of stage -> bool)
            - strengths       (list[str])
            - improvements    (list[str])
            - feedback        (str, multi-line, human-readable)
        """
        if not user_answer or not user_answer.strip():
            return self._empty_answer_feedback(question, expected_keywords or [])

        tokens = self._tokenize(user_answer)
        words = self._word_list(user_answer)
        word_count = len(words)
        sentences = self._split_sentences(user_answer)
        avg_sentence_len = (
            sum(len(self._word_list(s)) for s in sentences) / len(sentences)
            if sentences else 0
        )

        expected_keywords = [k.lower().strip() for k in (expected_keywords or []) if k.strip()]
        matched, missed = self._keyword_match(user_answer, expected_keywords)

        star_breakdown = self._detect_star(user_answer)
        star_score = sum(1 for v in star_breakdown.values() if v)

        confidence = self._confidence_proxy(words, sentences)
        length_score = self._length_score(word_count)
        clarity_score = self._clarity_score(avg_sentence_len)
        keyword_score = (
            (len(matched) / len(expected_keywords)) * 100
            if expected_keywords
            else 60.0  # neutral baseline when no keyword list
        )
        star_pct = (star_score / 4) * 100

        # Weighted final score
        weights = self._difficulty_weights(difficulty)
        final_score = (
            weights["length"] * length_score
            + weights["clarity"] * clarity_score
            + weights["keyword"] * keyword_score
            + weights["star"] * star_pct
        )
        final_score = round(min(max(final_score, 0), 100), 1)

        strengths, improvements = self._feedback_points(
            word_count=word_count,
            avg_sentence_len=avg_sentence_len,
            matched=matched,
            missed=missed,
            star_breakdown=star_breakdown,
            confidence_proxy=confidence,
        )

        feedback = self._compose_feedback(
            question=question,
            score=final_score,
            word_count=word_count,
            matched=matched,
            missed=missed,
            star_breakdown=star_breakdown,
            strengths=strengths,
            improvements=improvements,
        )

        return {
            "score": final_score,
            "confidence": round(confidence, 2),
            "keyword_match": matched,
            "keyword_miss": missed,
            "star_score": star_score,
            "star_breakdown": star_breakdown,
            "strengths": strengths,
            "improvements": improvements,
            "feedback": feedback,
            "word_count": word_count,
            "avg_sentence_len": round(avg_sentence_len, 1),
        }

    # --------------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------------

    def _difficulty_weights(self, difficulty: str) -> Dict[str, float]:
        difficulty = (difficulty or "medium").lower()
        if difficulty == "easy":
            return {"length": 0.30, "clarity": 0.20, "keyword": 0.30, "star": 0.20}
        if difficulty == "hard":
            return {"length": 0.15, "clarity": 0.25, "keyword": 0.25, "star": 0.35}
        return {"length": 0.20, "clarity": 0.25, "keyword": 0.30, "star": 0.25}

    def _tokenize(self, text: str) -> List[str]:
        return [t.lower().strip(string.punctuation) for t in text.split()]

    def _word_list(self, text: str) -> List[str]:
        return [w for w in self._tokenize(text) if w]

    def _split_sentences(self, text: str) -> List[str]:
        # Lightweight sentence splitter (no NLTK dependency at runtime)
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s for s in sentences if s.strip()]

    def _keyword_match(self, text: str, keywords: List[str]) -> Tuple[List[str], List[str]]:
        lowered = text.lower()
        matched, missed = [], []
        for kw in keywords:
            kw = kw.lower().strip()
            if not kw:
                continue
            if kw in lowered:
                matched.append(kw)
            else:
                missed.append(kw)
        return matched, missed

    def _detect_star(self, text: str) -> Dict[str, bool]:
        lowered = text.lower()
        result = {}
        for stage, signals in STAR_SIGNALS.items():
            result[stage] = any(sig in lowered for sig in signals)
        return result

    def _confidence_proxy(self, words: List[str], sentences: List[str]) -> float:
        """Confidence proxy in [0,1]. Higher = more confident."""
        if not words:
            return 0.0
        hedge_hits = sum(
            1 for w in words if w in HEDGE_WORDS
        )
        # Hedge density penalizes confidence
        hedge_density = hedge_hits / len(words)
        confidence = max(0.0, 1.0 - hedge_density * 8)
        # Bonus for action verbs
        action_hits = sum(1 for w in words if w in ACTION_VERBS)
        confidence = min(1.0, confidence + min(0.15, action_hits * 0.05))
        return confidence

    def _length_score(self, word_count: int) -> float:
        """Bell-curve length score: too short or too long is bad."""
        if word_count < 20:
            return word_count * 2.5  # up to 50 for 20 words
        if word_count <= 250:
            return 100.0
        if word_count <= 500:
            return 90.0
        if word_count <= 800:
            return 75.0
        return 60.0

    def _clarity_score(self, avg_sentence_len: float) -> float:
        """Clarity: 12-22 word sentences score 100; lower outside."""
        if avg_sentence_len <= 0:
            return 0.0
        if 12 <= avg_sentence_len <= 22:
            return 100.0
        if 8 <= avg_sentence_len < 12 or 22 < avg_sentence_len <= 28:
            return 80.0
        if 5 <= avg_sentence_len < 8 or 28 < avg_sentence_len <= 35:
            return 60.0
        return 40.0

    def _feedback_points(
        self,
        word_count: int,
        avg_sentence_len: float,
        matched: List[str],
        missed: List[str],
        star_breakdown: Dict[str, bool],
        confidence_proxy: float,
    ) -> Tuple[List[str], List[str]]:
        strengths, improvements = [], []

        # Length
        if 80 <= word_count <= 250:
            strengths.append(f"Answer length is well-calibrated ({word_count} words).")
        elif word_count < 80:
            improvements.append(f"Answer is brief ({word_count} words); aim for 80-250 words for a complete response.")
        else:
            improvements.append(f"Answer is lengthy ({word_count} words); tighten for impact.")

        # Clarity
        if 12 <= avg_sentence_len <= 22:
            strengths.append(f"Sentences are well-structured (avg {avg_sentence_len:.1f} words).")
        else:
            improvements.append(f"Vary sentence length — current average is {avg_sentence_len:.1f} words (target 12-22).")

        # Keywords
        if matched:
            strengths.append(f"Strong keyword coverage: {', '.join(matched[:5])}.")
        if missed:
            improvements.append(f"Missing important terms: {', '.join(missed[:5])}.")

        # STAR
        for stage, present in star_breakdown.items():
            if present:
                strengths.append(f"Used the {stage.upper()} component (STAR method).")
            else:
                improvements.append(f"Strengthen the {stage.upper()} component for a complete STAR answer.")

        # Confidence
        if confidence_proxy >= 0.85:
            strengths.append("Confident tone — minimal filler or hedge words.")
        elif confidence_proxy < 0.6:
            improvements.append("Reduce hedge/filler words (um, like, I guess) to sound more confident.")

        # Always have at least one entry of each
        if not strengths:
            strengths.append("Answer addresses the question directly.")
        if not improvements:
            improvements.append("Refine for tighter, more impact-driven delivery.")

        return strengths, improvements

    def _compose_feedback(self, **kwargs) -> str:
        score = kwargs["score"]
        word_count = kwargs["word_count"]
        matched = kwargs["matched"]
        missed = kwargs["missed"]
        star = kwargs["star_breakdown"]
        strengths = kwargs["strengths"]
        improvements = kwargs["improvements"]
        question = kwargs["question"]

        grade = self._score_to_grade(score)
        lines = []
        lines.append(f"Overall: {score}/100 — {grade}")
        lines.append("")
        lines.append(f"Question: {question}")
        lines.append(f"Your answer: {word_count} words")
        lines.append("")
        lines.append("STAR analysis:")
        for stage, present in star.items():
            mark = "✓" if present else "✗"
            lines.append(f"  {mark} {stage.upper()}")
        lines.append("")
        lines.append("Strengths:")
        for s in strengths:
            lines.append(f"  + {s}")
        lines.append("")
        lines.append("Improvements:")
        for i in improvements:
            lines.append(f"  → {i}")
        return "\n".join(lines)

    @staticmethod
    def _score_to_grade(score: float) -> str:
        if score >= 90:
            return "Excellent — hire with high confidence"
        if score >= 80:
            return "Strong — likely hire"
        if score >= 70:
            return "Good — borderline hire"
        if score >= 60:
            return "Average — needs more depth"
        if score >= 50:
            return "Below average — significant gaps"
        return "Insufficient — major rework needed"

    def _empty_answer_feedback(self, question: str, expected_keywords: List[str]) -> Dict:
        return {
            "score": 0.0,
            "confidence": 0.0,
            "keyword_match": [],
            "keyword_miss": expected_keywords,
            "star_score": 0,
            "star_breakdown": {k: False for k in STAR_SIGNALS},
            "strengths": ["—"],
            "improvements": ["Provide a complete answer to receive feedback."],
            "feedback": (
                f"Score: 0/100 — No answer submitted.\n\n"
                f"Question: {question}\n"
                "Please provide a complete response using the STAR method "
                "(Situation, Task, Action, Result)."
            ),
            "word_count": 0,
            "avg_sentence_len": 0.0,
        }


# Singleton accessor for the Flask app
engine = AIInterviewEngine()
