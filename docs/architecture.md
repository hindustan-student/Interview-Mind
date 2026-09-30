# Architecture

## Overview

InterviewMind follows a **layered, single-flask-app architecture** optimized
for academic readability:

```
┌─────────────────────────────────────────────────────────┐
│                     Presentation                         │
│   (Jinja2 templates + static CSS/JS + particle canvas)   │
├─────────────────────────────────────────────────────────┤
│                       Routes                             │
│   (Blueprints: main, auth, interview, resume,           │
│    questions, dashboard, api)                            │
├─────────────────────────────────────────────────────────┤
│                      Services                             │
│   (Pure-Python: ai_engine, resume_analyzer, question_bank)│
├─────────────────────────────────────────────────────────┤
│                       Models                              │
│   (SQLAlchemy ORM: User, InterviewSession, Answer,       │
│    ResumeReport, QuestionBankItem)                       │
├─────────────────────────────────────────────────────────┤
│                    Extensions & DB                        │
│   (Flask-SQLAlchemy, Login, Bcrypt, WTF-CSRF, Migrate)   │
└─────────────────────────────────────────────────────────┘
```

## Design Principles

1. **Application Factory Pattern** — `create_app(config_name)` in `app/__init__.py`
   builds a fresh Flask app per environment. This allows multiple instances
   (dev, test, prod) with isolated state.

2. **Blueprints for Routing** — Each concern has its own blueprint:
   - `main_bp` → public pages
   - `auth_bp` → registration / login / logout
   - `interview_bp` → mock interview lifecycle
   - `resume_bp` → upload + ATS analysis
   - `questions_bp` → public question bank browser
   - `dashboard_bp` → user analytics
   - `api_bp` → JSON endpoints for AJAX

3. **Service Layer** — All business logic (AI scoring, resume analysis,
   question generation) lives in `app/services/`. Services are pure-Python
   (no I/O beyond file reads in the resume analyzer) which keeps them
   unit-testable without spinning up Flask.

4. **Thin Controllers** — Routes do only: parse input, call service, persist
   to DB, render template or return JSON. No business logic in routes.

5. **Single Source of Truth for Extensions** — `app/extensions.py` owns
   the SQLAlchemy, LoginManager, Bcrypt, CSRF, and Migrate singletons.
   The factory `init_app()`s them onto the app. This prevents circular
   imports between `models.py` and `routes/*.py`.

## Data Model

```
User ──┬──< InterviewSession ──< Answer
       └──< ResumeReport

QuestionBankItem  (separate; seeded by QuestionBank.seed_defaults)
```

### Cardinality
- User → InterviewSession: 1-to-many (cascade delete)
- InterviewSession → Answer: 1-to-many (cascade delete)
- User → ResumeReport: 1-to-many (cascade delete)

## AI Engine Swap-In Pattern

The `AIInterviewEngine.score_answer()` interface is the only contract between
routes and the AI. To swap the rule-based engine for a real LLM, create a new
class with the same method signature:

```python
class LLMInterviewEngine:
    def score_answer(self, question, user_answer,
                     expected_keywords=None, model_answer=None,
                     difficulty="medium"):
        # call OpenAI / Gemini here
        return {
            "score": ..., "confidence": ...,
            "keyword_match": [...], "keyword_miss": [...],
            "star_score": ..., "star_breakdown": {...},
            "strengths": [...], "improvements": [...],
            "feedback": "...",
        }
```

Then in `app/services/__init__.py`, replace `engine = AIInterviewEngine()`
with `engine = LLMInterviewEngine()`. No route changes needed.

## Particle Canvas Architecture

`app/static/js/particles.js` is an IIFE (immediately-invoked function
expression) that runs once on page load. It:

1. Queries the canvas via `[data-particle-canvas]` selector.
2. Checks `prefers-reduced-motion` and bails out if set.
3. Initializes a particle array sized to viewport area.
4. Starts a `requestAnimationFrame` loop that:
   - Updates positions (with mouse repulsion)
   - Draws connection lines between near particles
   - Draws each particle (glow gradient + core + colored ring)
5. Listens for resize / mouse / touch / visibility events.

Performance characteristics:
- O(n²) for connection lines — capped at 140 particles to stay under 16ms/frame
- Additive blending (`lighter`) for neon glow stacking
- DPR-aware (max 2x) to avoid blowing up fillrate on retina
- Auto-pause when tab hidden
