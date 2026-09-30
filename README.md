# InterviewMind 🧠✨

> **AI-Powered Interview Preparation System** — A world-class academic project built with Flask + HTML5 Canvas, featuring a neon moving-particle animated background, AI mock interviews, a resume ATS analyzer, and a performance dashboard.

<p align="center">
  <img alt="Tech Stack" src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white">
  <img alt="Flask" src="https://img.shields.io/badge/Flask-3.0-black?logo=flask&logoColor=white">
  <img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-2.0-red?logo=sqlalchemy&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green">
  <img alt="Status" src="https://img.shields.io/badge/Status-Academic%20Project-purple">
</p>

---

## 📑 Table of Contents

1. [Overview](#-overview)
2. [Key Features](#-key-features)
3. [Live Demo Workflow](#-live-demo-workflow)
4. [Tech Stack](#-tech-stack)
5. [Project Structure](#-project-structure)
6. [Installation & Setup](#-installation--setup)
7. [Running the Application](#-running-the-application)
8. [Running Tests](#-running-tests)
9. [AI Scoring Algorithm](#-ai-scoring-algorithm)
10. [Neon Particle Animation](#-neon-particle-animation)
11. [Screenshots & Visual Walkthrough](#-screenshots--visual-walkthrough)
12. [Academic Project Objectives Met](#-academic-project-objectives-met)
13. [API Reference](#-api-reference)
14. [Configuration Reference](#-configuration-reference)
15. [Roadmap](#-roadmap)
16. [Contributing](#-contributing)
17. [License](#-license)
18. [Citation](#-citation)

---

## 🎯 Overview

**InterviewMind** is a full-stack web application designed to bridge a critical gap in career-readiness education: most candidates rehearse interview answers in their heads, but rarely get structured, actionable feedback. This system simulates a real interviewer — generating role-appropriate questions, scoring each answer against the **STAR method**, identifying keyword gaps, and surfacing concrete strengths and improvements.

Beyond its functional value, the project doubles as a reference implementation of a clean, layered Flask architecture. Reviewers can audit the application factory pattern, blueprint routing, SQLAlchemy ORM models, and service-layer design patterns in a single readable codebase. The accompanying pytest test suite and documentation make it suitable as a teaching artifact for software-engineering courses or capstone evaluations.

### Why InterviewMind?

- **No external API keys required** — The AI scoring engine runs locally with rule-based NLP, so the project works out-of-the-box in any academic environment.
- **Production-grade architecture** — Application factory pattern, blueprints, SQLAlchemy ORM, service layer, configuration per environment.
- **Modern UI with neon particle animation** — A custom HTML5 Canvas engine delivers an interactive, mouse-reactive neon particle background.
- **Testable end-to-end** — pytest covers routes, AI engine, and resume analyzer.

---

## ✨ Key Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **AI Mock Interview** | Simulates a real interviewer with role-specific questions, difficulty levels, and instant STAR-method feedback on every answer. |
| 2 | **Resume ATS Analyzer** | Upload PDF/DOCX/TXT. Get instant ATS score, keyword coverage, missing sections, and tailored recommendations. |
| 3 | **Curated Question Bank** | 25+ hand-curated questions across behavioral, technical, system design, coding, HR, and situational categories. |
| 4 | **Performance Dashboard** | Tracks every mock interview, score trends, weak categories, and confidence growth over time. |
| 5 | **Real-Time Feedback** | After every answer: score, strengths, improvements, STAR breakdown, keyword match, confidence proxy — computed locally. |
| 6 | **Secure Auth** | Flask-Login sessions, PBKDF2-SHA256 password hashing, CSRF protection, per-user data isolation. |
| 7 | **Neon Particle Background** | Custom canvas engine with mouse interactivity, parallax depth layers, additive blending for glow, DPR-aware rendering. |
| 8 | **Accessibility-Conscious** | Respects `prefers-reduced-motion`, keyboard-navigable forms, ARIA labels, semantic HTML. |
| 9 | **Responsive Design** | Mobile-first layout with collapsible navigation and adaptive grids. |
| 10 | **Print-Friendly** | Hides particle canvas and chrome for clean interview-result printing. |

---

## 🎬 Live Demo Workflow

```
1. Register → /auth/register
2. Login → /auth/login
3. Upload resume → /resume/upload      (instant ATS score)
4. Configure interview → /interview/start
5. Answer questions → /interview/<id>   (real-time AI feedback per answer)
6. View results → /interview/<id>/results
7. Track progress → /dashboard
8. Browse question bank → /questions/
```

---

## 🛠 Tech Stack

### Backend
- **Python 3.10+** — Core runtime
- **Flask 3.0** — Web framework (application factory pattern)
- **Flask-SQLAlchemy 3.1** — ORM
- **Flask-Login 0.6** — Session management
- **Flask-WTF 1.2** — Form + CSRF protection
- **Flask-Bcrypt 1.0** — Password hashing
- **Flask-Migrate 4.0** — Database migrations
- **Werkzeug** — WSGI utility (password hashing, secure filenames)
- **PyPDF2 / python-docx / pdfplumber** — Resume text extraction

### Frontend
- **Jinja2** — Server-side templating
- **HTML5 Canvas API** — Custom particle engine (`particles.js`)
- **CSS3 Custom Properties** — Neon design system tokens
- **Vanilla JavaScript (ES6)** — No framework, no build step
- **Inter + Space Grotesk + JetBrains Mono** — Typography

### Testing & Tooling
- **pytest 7.4** — Test framework
- **pytest-flask 1.3** — Flask test client integration
- **coverage** — Code coverage reporting
- **python-dotenv** — Environment management

---

## 📁 Project Structure

```
InterviewMind/
├── app/                          # Flask application package
│   ├── __init__.py              # Application factory (create_app)
│   ├── extensions.py            # Shared Flask extensions (db, login, bcrypt, csrf)
│   ├── models.py                # SQLAlchemy ORM models (5 tables)
│   ├── routes/                  # Blueprints (URL handlers)
│   │   ├── __init__.py
│   │   ├── main.py              # /, /about, /features, /contact, /health
│   │   ├── auth.py              # /auth/register, /auth/login, /auth/logout
│   │   ├── interview.py         # /interview/start, /interview/<id>, /interview/<id>/results
│   │   ├── resume.py            # /resume/upload, /resume/report/<id>, /resume/history
│   │   ├── questions.py         # /questions/ (curated question bank)
│   │   ├── dashboard.py         # /dashboard/ (analytics)
│   │   └── api.py               # /api/* (AJAX endpoints for interview submission)
│   ├── services/                # Pure-Python business logic (unit-testable)
│   │   ├── __init__.py
│   │   ├── ai_engine.py         # Rule-based interview scoring engine
│   │   ├── resume_analyzer.py  # ATS resume analyzer
│   │   └── question_bank.py    # Curated questions + question generation
│   ├── templates/               # Jinja2 templates
│   │   ├── base.html            # Base layout w/ neon particle canvas
│   │   ├── index.html           # Landing page
│   │   ├── about.html           # Project overview
│   │   ├── features.html        # Feature catalog
│   │   ├── contact.html         # Contact form
│   │   ├── auth/                # login.html, register.html
│   │   ├── interview/           # start.html, session.html, results.html, history.html
│   │   ├── resume/              # upload.html, report.html, history.html
│   │   ├── questions/           # bank.html
│   │   └── dashboard/           # index.html (analytics dashboard)
│   └── static/                  # Static assets
│       ├── css/
│       │   └── style.css        # Neon design system (~700 lines)
│       ├── js/
│       │   ├── particles.js     # Custom canvas particle engine (~230 lines)
│       │   ├── main.js          # Shared front-end helpers
│       │   └── interview.js     # Interview session logic (AJAX submission)
│       └── assets/
│           └── favicon.svg
├── tests/                       # Pytest test suite
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── test_routes.py           # Route smoke tests + auth flow
│   ├── test_ai_engine.py        # AI scoring engine tests
│   └── test_resume_analyzer.py # Resume ATS analyzer tests
├── docs/                        # Documentation
├── instance/                    # SQLite DB storage (auto-created)
├── config.py                    # Configuration classes (dev/test/prod)
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── .gitignore
└── README.md                    # This file
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python **3.10 or higher** (verify with `python --version`)
- `pip` (Python package installer)
- ~200 MB free disk space (for virtualenv + packages)
- A modern web browser (Chrome / Firefox / Edge / Safari)

### Step 1: Clone / Extract the Project

```bash
# If extracted from zip:
cd InterviewMind

# If cloning from a git repo:
git clone <repo-url> InterviewMind
cd InterviewMind
```

### Step 2: Create & Activate a Virtual Environment

**On Linux / macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**On Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your shell prompt.

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
cp .env.example .env
```

Open `.env` and set a strong `SECRET_KEY`:
```ini
SECRET_KEY=your-long-random-string-here-at-least-32-chars
FLASK_ENV=development
```

### Step 5: Initialize the Database

```bash
flask --app run.py init-db
flask --app run.py seed-db   # optional: seeds the question bank in DB
```

> **Note:** In development mode, the database is auto-created on first run. The `init-db` CLI command is provided for explicit initialization.

---

## ▶️ Running the Application

### Development Mode (default)
```bash
python run.py
```

The app will be available at **http://127.0.0.1:5000** (or http://0.0.0.0:5000 on your LAN).

### Custom Port / Host
```bash
python run.py --port 8080 --host 0.0.0.0
```

### Production Mode
```bash
export FLASK_ENV=production
python run.py --env production
```

> For real production deployment, use a WSGI server like **gunicorn**:
> ```bash
> pip install gunicorn
> gunicorn -w 4 -b 0.0.0.0:8000 "run:app"
> ```

### First Run Checklist
1. ✅ Open `http://127.0.0.1:5000` — landing page should load with neon particle background.
2. ✅ Click **Get Started** → register a new account.
3. ✅ After login, click **Mock Interview** → configure → start answering.
4. ✅ Try **Resume ATS** → upload a `.txt` file → see your ATS score.
5. ✅ Visit **Dashboard** to see your progress.

---

## 🧪 Running Tests

The project ships with a pytest test suite covering routes, AI engine, and resume analyzer.

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run only AI engine tests
pytest tests/test_ai_engine.py -v

# Run with coverage report
pip install coverage
coverage run -m pytest
coverage report -m
```

### Test Categories

| Test File | Coverage |
|-----------|----------|
| `tests/test_routes.py` | Landing, auth flow, dashboard auth guard, 404, all blueprint routes |
| `tests/test_ai_engine.py` | Empty answer, STAR detection, hedge word confidence, difficulty weights, score-to-grade thresholds, keyword matching |
| `tests/test_resume_analyzer.py` | Text extraction, section detection, keyword coverage, role normalization, ATS score range, recommendations |

---

## 🧠 AI Scoring Algorithm

The `AIInterviewEngine.score_answer()` method computes a 0–100 score using weighted components:

| Component | Weight (Medium) | What it Measures |
|-----------|-----------------|------------------|
| **Length Score** | 20% | Bell-curve: 80–250 words = 100, below 20 = scaling, above 500 = penalized |
| **Clarity Score** | 25% | Avg sentence length — 12–22 words = 100 (Flesch-aligned heuristic) |
| **Keyword Score** | 30% | % of expected role keywords found in the answer |
| **STAR Score** | 25% | Count of STAR stages detected (Situation/Task/Action/Result) |

### Difficulty Adjusts Weights

| Difficulty | Length | Clarity | Keyword | STAR |
|------------|--------|---------|---------|------|
| Easy       | 0.30   | 0.20    | 0.30    | 0.20 |
| Medium     | 0.20   | 0.25    | 0.30    | 0.25 |
| Hard       | 0.15   | 0.25    | 0.25    | 0.35 |

### Confidence Proxy
A hedge-word density check (`um`, `like`, `I guess`, etc.) plus an action-verb bonus produces a 0–1 confidence score. Lower hedge density → higher confidence.

### Extending to Real LLMs
The same `score_answer(question, user_answer, expected_keywords, model_answer, difficulty)` interface can be reimplemented to call OpenAI / Gemini / Claude — see `docs/architecture.md` for the swap-in pattern.

---

## 🌌 Neon Particle Animation

The particle background is a **custom-built, dependency-free HTML5 Canvas engine** in `app/static/js/particles.js` (~230 lines).

### Features
- **Multi-color neon particles** (cyan #00f0ff, magenta #ff00e5, purple #a855f7)
- **Distance-based connection lines** — particles within 130px draw a network-graph edge with fading opacity
- **Mouse repulsion** — particles flee the cursor within a 160px radius (with depth-weighted force)
- **Particle glow** — radial gradient halos around each particle for true neon look
- **Parallax depth layers** — each particle has a `depth` (0–1) affecting its speed, size, and glow intensity
- **Pulsing animation** — per-particle `phase` oscillates the radius for a breathing effect
- **Additive blending** (`globalCompositeOperation = 'lighter'`) — overlapping glows sum into bright bloom
- **DPR-aware rendering** — auto-scales for retina displays, capped at 2× for performance
- **Reduced-motion respect** — disables itself if the user has `prefers-reduced-motion: reduce`
- **Tab-pause** — pauses when the tab is hidden (battery-friendly)
- **Auto-scaling particle count** — based on viewport area, capped at min/max bounds

### Configuration (via `data-*` attributes on the canvas)

```html
<canvas data-particle-canvas
        data-density="0.00012"
        data-max-particles="140"
        data-min-particles="40"
        data-speed="0.45"
        data-link-distance="130"
        data-link-opacity="0.35"
        data-mouse-radius="160"
        data-mouse-force="0.9"></canvas>
```

---

## 🖼 Screenshots & Visual Walkthrough

> **Note:** Run the app locally and walk through the URLs below to see the neon-animated UI in action.

| Page | URL | What to Look For |
|------|-----|------------------|
| Landing | `/` | Hero with gradient title, neon particle background, mouse-reactive |
| Features | `/features` | 6-card grid with colored glow icons |
| About | `/about` | Mission statement, problem/solution, scope, tech stack |
| Register | `/auth/register` | Glass-morphism form card with neon focus glow |
| Login | `/auth/login` | Compact form, autofocused email field |
| Interview Start | `/interview/start` | Role/category/difficulty/count selectors |
| Interview Session | `/interview/<id>` | Live word count, timer, AJAX feedback card |
| Interview Results | `/interview/<id>/results` | Score ring, category breakdown, per-question analysis |
| Resume Upload | `/resume/upload` | File input + role selector |
| Resume Report | `/resume/report/<id>` | ATS score ring, matched/missing keywords, recommendations |
| Question Bank | `/questions/` | Filterable grid of curated questions with model answers |
| Dashboard | `/dashboard/` | KPI cards, score trend bar chart, category performance |

---

## 🎓 Academic Project Objectives Met

| Objective | How InterviewMind Meets It |
|-----------|-----------------------------|
| Full-stack web application | Flask backend + Jinja2/HTML/CSS/JS frontend |
| Database design & ORM | 5 SQLAlchemy models with relationships, migrations via Flask-Migrate |
| Authentication & security | Flask-Login sessions, PBKDF2-SHA256 hashing, CSRF protection |
| Rule-based NLP / AI | Custom scoring engine with STAR detection, hedge-word confidence, keyword matching |
| Modern UI/UX | Neon particle canvas, glass-morphism, responsive design, accessibility-conscious |
| Test coverage | pytest test suite across routes + AI engine + resume analyzer |
| Documentation | This README + `docs/` folder + inline docstrings |
| Configuration management | Per-environment configs (dev/test/prod) via `config.py` |
| Modular architecture | Application factory pattern, 7 blueprints, service layer |

---

## 🔌 API Reference

Lightweight JSON endpoints (all under `/api/`):

### `GET /api/categories`
Returns all interview categories.
```json
{
  "categories": [
    {"key": "behavioral", "label": "Behavioral", "count": 5},
    ...
  ]
}
```

### `GET /api/questions/sample?category=mixed&difficulty=medium`
Returns 5 sample questions (without model answers).
```json
{
  "questions": [
    {"q": "Tell me about yourself.", "category": "hr"},
    ...
  ]
}
```

### `POST /api/interview/<session_id>/answer`
Submit an answer for instant feedback. Requires authentication.

**Request body:**
```json
{
  "answer_id": 42,
  "user_answer": "Situation: ... Task: ... Action: ... Result: ...",
  "time_taken": 95
}
```

**Response body:**
```json
{
  "completed": false,
  "score": 87.5,
  "confidence": 0.92,
  "feedback": "Overall: 87.5/100 — Strong — likely hire\n...",
  "strengths": ["Answer length is well-calibrated (142 words).", ...],
  "improvements": ["Strengthen the TASK component for a complete STAR answer."]
}
```

### `GET /health`
Health check (no auth required).
```json
{"status": "ok", "service": "InterviewMind", "version": "1.0.0"}
```

---

## ⚙️ Configuration Reference

All settings live in `config.py` and can be overridden via `.env`.

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | `development` / `testing` / `production` |
| `SECRET_KEY` | (dev fallback) | **Set a strong value in production** |
| `DATABASE_URL` | `sqlite:///instance/interviewmind.db` | SQLAlchemy URI |
| `MAX_CONTENT_LENGTH` | 5 MB | Resume upload size cap |
| `ALLOWED_EXTENSIONS` | `pdf, docx, txt` | Resume upload formats |
| `BCRYPT_LOG_ROUNDS` | 12 | Password hash cost (4 in tests) |
| `MAX_INTERVIEW_QUESTIONS` | 10 | Cap on questions per session |
| `ANSWER_MIN_WORDS` / `ANSWER_MAX_WORDS` | 30 / 800 | Soft scoring bounds |
| `ATS_KEYWORD_MIN_MATCH` | 0.35 | Threshold for "low coverage" warning |

---

## 🗺 Roadmap

Future enhancements to make this project even stronger:

- [ ] Real LLM integration (OpenAI / Gemini) behind the same `score_answer()` interface
- [ ] Voice answer recording + speech-to-text for mock interviews
- [ ] Real-time video mock interview with facial-expression analysis
- [ ] Multi-user "interview rooms" (interviewer + candidate sockets via Flask-SocketIO)
- [ ] Question bank import from CSV / JSON
- [ ] Admin panel for question CRUD
- [ ] Leaderboard / class analytics for academic instructors
- [ ] Internationalization (i18n) for non-English candidates

---

## 🤝 Contributing

Contributions are welcome! This is an academic project, but improvements that keep the "no external API" constraint are especially valued.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Write tests for new functionality
4. Run `pytest` to confirm all tests pass
5. Submit a pull request

### Code Style
- Follow **PEP 8** for Python (use `flake8` or `black`).
- JavaScript: ES6, 4-space indentation, semicolons required.
- CSS: 4-space indentation, BEM-ish naming, CSS custom properties for tokens.

---

## 📜 License

Released under the **MIT License**. See the `LICENSE` file for details.

You are free to use, modify, and distribute this project for academic and commercial purposes, provided the copyright notice is preserved.

---

## 📚 Citation

If you use InterviewMind in your academic work, please cite it as:

```bibtex
@misc{interviewmind2026,
  title  = {InterviewMind: AI-Powered Interview Preparation System},
  author = {InterviewMind Academic Project Team},
  year   = {2026},
  note   = {Academic project. Flask + HTML5 Canvas.},
  url    = {https://github.com/your-username/InterviewMind}
}
```

---

<p align="center">
  <strong>Built with care for the next generation of interview-ready graduates. 🎓</strong>
  <br>
  <sub>If this project helped you, give it a ⭐ on GitHub.</sub>
</p>
