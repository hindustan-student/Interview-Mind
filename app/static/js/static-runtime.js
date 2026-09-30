/* Client runtime for the static Vercel academic export */
(function () {
    'use strict';
    if (document.body.getAttribute('data-static') !== 'true') return;

    const KEYS = {
        users: 'im_users',
        session: 'im_session',
        interviews: 'im_interviews',
        reports: 'im_reports',
        active: 'im_active_interview'
    };

    function load(key, fallback) {
        try {
            const raw = localStorage.getItem(key);
            return raw ? JSON.parse(raw) : fallback;
        } catch (e) {
            return fallback;
        }
    }
    function save(key, value) {
        localStorage.setItem(key, JSON.stringify(value));
    }

    function path() {
        return (location.pathname.replace(/\/+$/, '') || '/').toLowerCase();
    }

    function flash(message, category) {
        const box = document.getElementById('client-flash');
        if (!box) return;
        const el = document.createElement('div');
        el.className = 'alert alert-' + (category || 'info');
        el.textContent = message;
        box.appendChild(el);
        setTimeout(() => el.remove(), 5000);
    }

    async function sha256(text) {
        const data = new TextEncoder().encode(text);
        const buf = await crypto.subtle.digest('SHA-256', data);
        return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, '0')).join('');
    }

    function currentUser() {
        return load(KEYS.session, null);
    }

    function requireAuth() {
        if (currentUser()) return true;
        location.href = '/auth/login/?next=' + encodeURIComponent(location.pathname);
        return false;
    }

    function renderNav() {
        const ul = document.getElementById('nav-links');
        if (!ul) return;
        const user = currentUser();
        const items = [
            ['/', 'Home'],
            ['/features/', 'Features'],
            ['/about/', 'About']
        ];
        let html = items.map(([href, label]) => `<li><a href="${href}">${label}</a></li>`).join('');
        if (user) {
            html += `
                <li><a href="/dashboard/">Dashboard</a></li>
                <li><a href="/interview/start/">Mock Interview</a></li>
                <li><a href="/resume/upload/">Resume ATS</a></li>
                <li><a href="/auth/logout/" id="logout-link">Logout (${escapeHtml(user.username)})</a></li>`;
        } else {
            html += `
                <li><a href="/auth/login/">Login</a></li>
                <li><a href="/auth/register/" class="btn btn-primary" style="padding:6px 14px;font-size:0.88rem;">Get Started</a></li>`;
        }
        ul.innerHTML = html;
        const logout = document.getElementById('logout-link');
        if (logout) {
            logout.addEventListener('click', function (e) {
                e.preventDefault();
                localStorage.removeItem(KEYS.session);
                flash('You have been logged out.', 'info');
                location.href = '/';
            });
        }
    }

    function escapeHtml(str) {
        return String(str || '').replace(/[&<>"']/g, (ch) => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[ch]));
    }

    function shuffle(arr) {
        const copy = arr.slice();
        for (let i = copy.length - 1; i > 0; i -= 1) {
            const j = Math.floor(Math.random() * (i + 1));
            [copy[i], copy[j]] = [copy[j], copy[i]];
        }
        return copy;
    }

    function evaluatePre(score) {
        if (score <= 5.5) {
            return {
                score,
                category: 'Medium',
                difficulty: 'easy',
                summary: 'Your pre-assessment indicates emerging study habits. Your 60-question practice interview is calibrated to Easy difficulty across all 6 levels to solidify your core foundations.'
            };
        }
        if (score <= 8.5) {
            return {
                score,
                category: 'Above Medium',
                difficulty: 'medium',
                summary: 'Your pre-assessment demonstrates disciplined preparation and consistent problem-solving. Your 60-question practice interview is calibrated to Medium difficulty across all 6 levels.'
            };
        }
        return {
            score,
            category: 'Excellent',
            difficulty: 'hard',
            summary: 'Outstanding pre-assessment performance reflecting deep conceptual clarity and resilience. Your 60-question practice interview is calibrated to Tough/Hard difficulty across all 6 levels.'
        };
    }

    function tagSection(questions, sec) {
        questions.forEach((q) => {
            q.section_number = sec.level;
            q.section_name = sec.name;
            q.section_title = sec.title;
            q.marks_allocated = sec.mark_per_question;
            q.category = sec.level <= 4 ? 'technical' : sec.category;
        });
        return questions;
    }

    function buildMainQuestions(data, role, difficulty) {
        const diff = ['easy', 'medium', 'hard'].includes(difficulty) ? difficulty : 'medium';
        const bank = data.banks[diff];
        const techMcq = bank.tech_mcq.slice(0, 32).map((q) => Object.assign({}, q, {
            type: 'mcq', options: shuffle(q.options || []), role, diff
        }));
        const techDesc = bank.tech_desc.slice(0, 8).map((q) => Object.assign({}, q, {
            type: 'descriptive',
            keywords_list: String(q.kw || '').split(',').map((k) => k.trim()).filter(Boolean),
            role, diff
        }));
        const logicMcq = bank.logic_mcq.slice(0, 16).map((q) => Object.assign({}, q, {
            type: 'mcq', options: shuffle(q.options || []), role, diff
        }));
        const logicDesc = bank.logic_desc.slice(0, 4).map((q) => Object.assign({}, q, {
            type: 'descriptive',
            keywords_list: String(q.kw || '').split(',').map((k) => k.trim()).filter(Boolean),
            role, diff
        }));
        const sections = data.sections;
        const combined = []
            .concat(tagSection(techMcq.slice(0, 8).concat(techDesc.slice(0, 2)), sections[0]))
            .concat(tagSection(techMcq.slice(8, 16).concat(techDesc.slice(2, 4)), sections[1]))
            .concat(tagSection(techMcq.slice(16, 24).concat(techDesc.slice(4, 6)), sections[2]))
            .concat(tagSection(techMcq.slice(24, 32).concat(techDesc.slice(6, 8)), sections[3]))
            .concat(tagSection(logicMcq.slice(0, 8).concat(logicDesc.slice(0, 2)), sections[4]))
            .concat(tagSection(logicMcq.slice(8, 16).concat(logicDesc.slice(2, 4)), sections[5]));
        combined.forEach((q, i) => {
            q.index = i + 1;
            q.phase = 'main';
            q.id = 'm' + q.index;
        });
        return combined;
    }

    async function loadBank() {
        const res = await fetch('/static/data/questions.json');
        return res.json();
    }

    function persistInterview(session) {
        const all = load(KEYS.interviews, []);
        const idx = all.findIndex((s) => s.id === session.id);
        if (idx >= 0) all[idx] = session;
        else all.unshift(session);
        save(KEYS.interviews, all);
        save(KEYS.active, session);
    }

    function interviewsForUser() {
        const user = currentUser();
        if (!user) return [];
        return load(KEYS.interviews, []).filter((s) => s.user_id === user.id);
    }

    function reportsForUser() {
        const user = currentUser();
        if (!user) return [];
        return load(KEYS.reports, []).filter((r) => r.user_id === user.id);
    }

    function bindAuthForms() {
        const p = path();
        if (p === '/auth/register' || p === '/auth/register/') {
            const form = document.querySelector('form');
            if (!form) return;
            form.addEventListener('submit', async function (e) {
                e.preventDefault();
                const username = form.username.value.trim();
                const email = form.email.value.trim().toLowerCase();
                const password = form.password.value;
                const confirm = form.confirm_password.value;
                if (username.length < 3 || username.length > 20) return flash('Username must be 3-20 characters.', 'danger');
                if (!email.includes('@')) return flash('Please enter a valid email address.', 'danger');
                if (password.length < 8) return flash('Password must be at least 8 characters.', 'danger');
                if (password !== confirm) return flash('Passwords do not match.', 'danger');
                const users = load(KEYS.users, []);
                if (users.some((u) => u.username === username)) return flash('Username already taken.', 'danger');
                if (users.some((u) => u.email === email)) return flash('Email already registered.', 'danger');
                users.push({
                    id: Date.now(),
                    username,
                    email,
                    full_name: form.full_name.value.trim() || username,
                    target_role: form.target_role.value || 'Software Engineer',
                    password_hash: await sha256(password)
                });
                save(KEYS.users, users);
                flash('Account created. You can now log in.', 'success');
                location.href = '/auth/login/';
            });
        }
        if (p === '/auth/login' || p === '/auth/login/') {
            const form = document.querySelector('form');
            if (!form) return;
            form.addEventListener('submit', async function (e) {
                e.preventDefault();
                const email = form.email.value.trim().toLowerCase();
                const password = form.password.value;
                const users = load(KEYS.users, []);
                const hash = await sha256(password);
                const user = users.find((u) => u.email === email && u.password_hash === hash);
                if (!user) return flash('Invalid email or password.', 'danger');
                save(KEYS.session, user);
                flash('Welcome back, ' + user.username + '!', 'success');
                const next = new URLSearchParams(location.search).get('next');
                location.href = next && next.startsWith('/') ? next : '/dashboard/';
            });
        }
        if (p === '/contact' || p === '/contact/') {
            const form = document.querySelector('form');
            if (!form) return;
            form.addEventListener('submit', function (e) {
                e.preventDefault();
                flash('Thanks — this static demo stores your note locally only. For a live backend, run Flask locally.', 'success');
                form.reset();
            });
        }
    }

    function bindInterviewStart() {
        const p = path();
        if (!(p === '/interview/start' || p === '/interview/start/')) return;
        if (!requireAuth()) return;
        const form = document.querySelector('form');
        if (!form) return;
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            const cgpa = Number(form.cgpa.value);
            if (Number.isNaN(cgpa) || cgpa < 0 || cgpa > 10) {
                return flash('Please enter a valid CGPA between 0.00 and 10.00', 'danger');
            }
            const user = currentUser();
            user.cgpa = cgpa;
            save(KEYS.session, user);
            const data = await loadBank();
            const pre = data.pre_assessment.map((q, i) => Object.assign({}, q, {
                id: 'p' + (i + 1),
                index: i + 1,
                phase: 'pre_assessment',
                type: 'mcq',
                options: shuffle(q.options || []),
                user_answer: null,
                score: null
            }));
            const session = {
                id: 's' + Date.now(),
                user_id: user.id,
                role: user.target_role || 'Software Engineer',
                cgpa,
                phase: 'pre_assessment',
                difficulty: 'medium',
                status: 'in_progress',
                started_at: new Date().toISOString(),
                pre: pre,
                main: [],
                answered_count: 0,
                total_questions: pre.length
            };
            persistInterview(session);
            location.href = '/interview/play/';
        });
    }

    function bindResumeUpload() {
        const p = path();
        if (!(p === '/resume/upload' || p === '/resume/upload/')) return;
        if (!requireAuth()) return;
        const form = document.querySelector('form');
        if (!form) return;
        const hint = document.createElement('p');
        hint.className = 'text-muted';
        hint.style.marginTop = '8px';
        hint.textContent = 'Static demo: TXT files work best in the browser. You can also paste resume text into a .txt file.';
        form.appendChild(hint);
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            const file = form.resume.files[0];
            if (!file) return flash('No file selected.', 'danger');
            const name = file.name.toLowerCase();
            if (!(name.endsWith('.txt') || name.endsWith('.md') || name.endsWith('.pdf') || name.endsWith('.docx'))) {
                return flash('Allowed formats: PDF, DOCX, TXT.', 'danger');
            }
            let text = '';
            try {
                text = await file.text();
            } catch (err) {
                return flash('Could not read that file in the browser. Try a .txt resume.', 'danger');
            }
            if (name.endsWith('.pdf') || name.endsWith('.docx')) {
                if (!text || text.length < 40 || text.indexOf('%PDF') === 0) {
                    return flash('PDF/DOCX cannot be parsed in this static demo. Upload a .txt resume (or run Flask locally for full parsing).', 'danger');
                }
            }
            const result = window.InterviewMindATS.analyzeText(text, form.target_role.value);
            if (result.error) return flash(result.error, 'danger');
            const user = currentUser();
            const report = Object.assign({
                id: 'r' + Date.now(),
                user_id: user.id,
                filename: file.name,
                target_role: form.target_role.value || result.role,
                created_at: new Date().toISOString()
            }, result);
            const reports = load(KEYS.reports, []);
            reports.unshift(report);
            save(KEYS.reports, reports);
            location.href = '/resume/view/?id=' + encodeURIComponent(report.id);
        });
    }

    function renderDashboard() {
        const p = path();
        if (!(p === '/dashboard' || p === '/dashboard/')) return;
        if (!requireAuth()) return;
        const user = currentUser();
        const name = document.getElementById('dash-username');
        if (name) name.textContent = user.username;
        const sessions = interviewsForUser();
        const completed = sessions.filter((s) => s.status === 'completed');
        const reports = reportsForUser();
        const avg = completed.length ? Math.round((completed.reduce((a, s) => a + (s.overall_score || 0), 0) / completed.length) * 10) / 10 : 0;
        const best = completed.reduce((m, s) => Math.max(m, s.overall_score || 0), 0);
        const conf = completed.length ? Math.round((completed.reduce((a, s) => a + (s.avg_confidence || 0), 0) / completed.length) * 100) : 0;
        const ats = reports.length ? Math.round((reports.reduce((a, r) => a + (r.ats_score || 0), 0) / reports.length) * 10) / 10 : 0;
        const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        set('kpi-sessions', sessions.length);
        set('kpi-completed', completed.length);
        set('kpi-avg', avg);
        set('kpi-best', best);
        set('kpi-confidence', conf + '%');
        set('kpi-ats', ats);

        const iv = document.getElementById('dash-interviews');
        if (iv) {
            const recent = sessions.slice(0, 5);
            iv.innerHTML = '<h2 class="mb-2">Recent Interviews</h2>' + (recent.length
                ? '<div style="display:flex;flex-direction:column;gap:8px;">' + recent.map((s) =>
                    `<a href="/interview/report/?id=${encodeURIComponent(s.id)}" style="display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(255,255,255,0.03);border-radius:8px;text-decoration:none;color:inherit;border:1px solid var(--border-soft);">
                        <div><strong>${escapeHtml(s.role)}</strong><br><span class="text-muted" style="font-size:0.82rem;">${new Date(s.started_at).toLocaleString()}</span></div>
                        <div class="text-right"><strong style="color:var(--neon-cyan);">${s.overall_score || '—'}</strong></div>
                    </a>`).join('') + '</div>'
                : '<p class="text-muted">No interviews yet. <a href="/interview/start/">Start your first →</a></p>');
        }
        const rp = document.getElementById('dash-reports');
        if (rp) {
            const recent = reports.slice(0, 3);
            rp.innerHTML = '<h2 class="mb-2">Recent Resume Reports</h2>' + (recent.length
                ? '<div style="display:flex;flex-direction:column;gap:8px;">' + recent.map((r) =>
                    `<a href="/resume/view/?id=${encodeURIComponent(r.id)}" style="display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(255,255,255,0.03);border-radius:8px;text-decoration:none;color:inherit;border:1px solid var(--border-soft);">
                        <div><strong style="font-size:0.88rem;">${escapeHtml(r.filename)}</strong></div>
                        <strong style="color:var(--neon-cyan);">${r.ats_score}/100</strong>
                    </a>`).join('') + '</div>'
                : '<p class="text-muted">No resume reports yet. <a href="/resume/upload/">Upload your resume →</a></p>');
        }
    }

    function renderHistory() {
        const p = path();
        if (p === '/interview/history' || p === '/interview/history/') {
            if (!requireAuth()) return;
            const root = document.getElementById('history-root');
            if (!root) return;
            const sessions = interviewsForUser();
            if (!sessions.length) return;
            root.innerHTML = `<table class="table"><thead><tr>
                <th>Date</th><th>Role</th><th>CGPA</th><th>Pre-Assessment</th><th>Difficulty</th><th>Answered</th><th>Score</th><th>Status</th><th>Action</th>
            </tr></thead><tbody>${sessions.map((s) => `<tr>
                <td>${new Date(s.started_at).toLocaleString()}</td>
                <td>${escapeHtml(s.role)}</td>
                <td>${s.cgpa != null ? s.cgpa : '—'}</td>
                <td>${s.pre_assessment_category ? `<span class="tag tag-cyan">${escapeHtml(s.pre_assessment_category)}</span>` : '—'}</td>
                <td>${s.difficulty || '—'}</td>
                <td>${s.answered_count}/${s.total_questions}</td>
                <td>${s.overall_score != null ? s.overall_score : '—'}</td>
                <td>${s.status}</td>
                <td><a class="btn btn-ghost" href="/interview/report/?id=${encodeURIComponent(s.id)}">View</a></td>
            </tr>`).join('')}</tbody></table>`;
        }
        if (p === '/resume/history' || p === '/resume/history/') {
            if (!requireAuth()) return;
            const root = document.getElementById('resume-history-root');
            if (!root) return;
            const reports = reportsForUser();
            if (!reports.length) return;
            root.innerHTML = `<table class="table"><thead><tr>
                <th>Date</th><th>Filename</th><th>Role</th><th>Words</th><th>ATS Score</th><th>Action</th>
            </tr></thead><tbody>${reports.map((r) => `<tr>
                <td>${new Date(r.created_at).toLocaleString()}</td>
                <td>${escapeHtml(r.filename)}</td>
                <td>${escapeHtml(r.target_role || 'Auto')}</td>
                <td>${r.word_count}</td>
                <td>${r.ats_score}/100</td>
                <td><a class="btn btn-ghost" href="/resume/view/?id=${encodeURIComponent(r.id)}">View</a></td>
            </tr>`).join('')}</tbody></table>`;
        }
    }

    function renderAtsReport() {
        const p = path();
        if (!(p === '/resume/view' || p === '/resume/view/')) return;
        if (!requireAuth()) return;
        const id = new URLSearchParams(location.search).get('id');
        const report = reportsForUser().find((r) => r.id === id) || reportsForUser()[0];
        const root = document.getElementById('ats-report-root');
        if (!root) return;
        if (!report) {
            root.innerHTML = '<div class="card text-center"><p>No report found. <a href="/resume/upload/">Upload a resume</a>.</p></div>';
            return;
        }
        root.innerHTML = `
            <div class="flex items-center justify-between mb-3" style="flex-wrap:wrap;gap:12px;">
                <h1>Resume ATS Report</h1>
                <a href="/resume/upload/" class="btn btn-secondary">+ Upload Another</a>
            </div>
            <div class="card mb-3 text-center">
                <div class="score-ring" style="--pct:${report.ats_score};"><div class="score-text">${report.ats_score}</div></div>
                <h2 class="mb-1">ATS Score</h2>
                <p class="text-secondary"><strong>${escapeHtml(report.filename)}</strong> · ${report.word_count} words</p>
            </div>
            <div class="grid grid-2 mb-3">
                <div class="card"><h3 class="mb-2">Matched Keywords</h3>${(report.matched_keywords || []).map((k) => `<span class="tag tag-success">${escapeHtml(k)}</span>`).join(' ')}</div>
                <div class="card color-magenta"><h3 class="mb-2">Missing Keywords</h3>${(report.missing_keywords || []).slice(0, 12).map((k) => `<span class="tag tag-danger">${escapeHtml(k)}</span>`).join(' ')}</div>
            </div>
            <div class="card mb-3"><h2 class="mb-2">Recommendations</h2><ol style="line-height:1.9;padding-left:20px;">${(report.recommendations || []).map((r) => `<li>${escapeHtml(r)}</li>`).join('')}</ol></div>
            <div class="text-center mt-3">
                <a href="/resume/history/" class="btn btn-ghost">View All Reports</a>
                <a href="/interview/start/" class="btn btn-primary">Practice Interview →</a>
            </div>`;
    }

    function currentQuestion(session) {
        const list = session.phase === 'main' ? session.main : session.pre;
        return (list || []).find((q) => !q.user_answer);
    }

    function renderPlay() {
        const p = path();
        if (!(p === '/interview/play' || p === '/interview/play/')) return;
        if (!requireAuth()) return;
        const root = document.getElementById('play-root');
        const session = load(KEYS.active, null);
        if (!root) return;
        if (!session) {
            root.innerHTML = '<div class="card text-center"><p>No active session. <a href="/interview/start/">Start one</a>.</p></div>';
            return;
        }
        if (session.phase === 'pre_assessment_completed') {
            renderPreComplete(root, session);
            return;
        }
        const q = currentQuestion(session);
        if (!q) {
            if (session.phase === 'pre_assessment') {
                finishPre(session);
                renderPreComplete(root, session);
                return;
            }
            completeMain(session);
            location.href = '/interview/report/?id=' + encodeURIComponent(session.id);
            return;
        }
        const list = session.phase === 'main' ? session.main : session.pre;
        const answered = list.filter((x) => x.user_answer).length;
        const letters = ['A', 'B', 'C', 'D'];
        const mcq = (q.type === 'mcq')
            ? `<div class="mcq-options-container">${(q.options || []).map((opt, i) =>
                `<label class="mcq-option-card"><input type="radio" name="user_answer_mcq" value="${escapeHtml(opt)}" class="mcq-radio">
                <span class="mcq-badge">${letters[i] || (i + 1)}</span><span class="mcq-text">${escapeHtml(opt)}</span></label>`
            ).join('')}</div>`
            : `<div class="form-group"><label for="user_answer">Your Written Answer</label>
                <textarea id="user_answer" class="form-control" required></textarea></div>`;
        root.innerHTML = `
            <div class="card mb-3">
                <div class="flex items-center justify-between" style="flex-wrap:wrap;gap:12px;">
                    <div class="flex items-center gap-1" style="flex-wrap:wrap;">
                        <span class="tag tag-cyan">${session.phase === 'pre_assessment' ? 'Phase 1: Pre-Assessment (10 Qs)' : 'Main Practice'}</span>
                        <span class="tag">${escapeHtml(session.role)}</span>
                        <span class="tag">${escapeHtml(session.difficulty)}</span>
                    </div>
                    <div class="text-secondary">Question <strong style="color:var(--neon-cyan);">${q.index}</strong> of ${list.length}</div>
                </div>
                <div class="progress-bar mt-2"><div class="progress-fill" style="width:${(answered / list.length) * 100}%;"></div></div>
            </div>
            <div class="card mb-3">
                <h2 style="font-size:1.45rem;line-height:1.45;margin-bottom:24px;">${escapeHtml(q.q || q.question_text)}</h2>
                <form id="answer-form">${mcq}
                    <div class="flex items-center justify-between gap-2" style="flex-wrap:wrap;">
                        <span class="text-muted" id="word-count"></span>
                        <span class="text-muted" id="time-elapsed">00:00</span>
                        <button type="submit" class="btn btn-primary" id="submit-btn">Submit Answer →</button>
                    </div>
                </form>
            </div>
            <div class="card mb-3" id="feedback-card" style="display:none;">
                <h3 class="mb-2" style="color:var(--neon-cyan);">Instant Feedback</h3>
                <div id="feedback-content"></div>
                <div class="text-right mt-3"><button class="btn btn-primary" id="next-btn" style="display:none;">Next Question →</button></div>
            </div>`;

        document.querySelectorAll('.mcq-option-card').forEach((card) => {
            card.addEventListener('click', function () {
                const radio = this.querySelector('input[type="radio"]');
                if (radio) {
                    radio.checked = true;
                    document.querySelectorAll('.mcq-option-card').forEach((c) => c.classList.remove('is-selected'));
                    this.classList.add('is-selected');
                }
            });
        });
        const start = Date.now();
        setInterval(() => {
            const elapsed = Math.floor((Date.now() - start) / 1000);
            const el = document.getElementById('time-elapsed');
            if (el) el.textContent = String(Math.floor(elapsed / 60)).padStart(2, '0') + ':' + String(elapsed % 60).padStart(2, '0');
        }, 1000);
        const ta = document.getElementById('user_answer');
        const wc = document.getElementById('word-count');
        if (ta && wc) {
            ta.addEventListener('input', () => {
                const n = (ta.value.trim().match(/\S+/g) || []).length;
                wc.textContent = n + ' word' + (n === 1 ? '' : 's');
            });
        }
        document.getElementById('answer-form').addEventListener('submit', function (e) {
            e.preventDefault();
            let answer = '';
            if (q.type === 'mcq') {
                const selected = this.querySelector('input[name="user_answer_mcq"]:checked');
                if (!selected) return alert('Please select an option before submitting.');
                answer = selected.value;
            } else {
                answer = (ta && ta.value || '').trim();
                if (answer.length < 10) return alert('Please provide a more complete answer before submitting (at least 10 characters).');
            }
            let score = 0;
            let confidence = 0.3;
            let feedback = '';
            let strengths = [];
            let improvements = [];
            if (q.type === 'mcq') {
                const ok = answer === (q.correct_option || '').trim();
                score = ok ? 100 : 0;
                confidence = ok ? 1 : 0.3;
                feedback = ok
                    ? ('✓ Correct! ' + (q.explanation || ''))
                    : ('✗ Incorrect. The optimal answer is: ' + q.correct_option + '. ' + (q.explanation || ''));
                strengths = ok ? ['Accurate selection: Demonstrated clear conceptual grasp of this topic.'] : [];
                improvements = ok ? [] : ['Recommended review: ' + String(q.category || 'topic').replace(/_/g, ' ') + '.'];
            } else {
                const result = window.InterviewMindAI.scoreAnswer(q.q, answer, q.keywords_list || [], session.difficulty);
                score = result.score;
                confidence = result.confidence;
                feedback = result.feedback;
                strengths = result.strengths;
                improvements = result.improvements;
            }
            q.user_answer = answer;
            q.score = score;
            q.confidence = confidence;
            q.feedback = feedback;
            q.strengths = strengths;
            q.improvements = improvements;
            session.answered_count = (session.pre.concat(session.main || [])).filter((x) => x.user_answer).length;
            persistInterview(session);
            const card = document.getElementById('feedback-card');
            const content = document.getElementById('feedback-content');
            content.innerHTML = `<div style="font-size:1.6rem;color:var(--neon-cyan);font-weight:700;">${q.type === 'mcq' ? (score > 0 ? '✓ Correct (100%)' : '✗ Incorrect (0%)') : score + '/100'}</div>
                <p style="white-space:pre-wrap;margin-top:12px;">${escapeHtml(feedback)}</p>`;
            card.style.display = 'block';
            document.getElementById('answer-form').style.display = 'none';
            const next = document.getElementById('next-btn');
            next.style.display = 'inline-flex';
            next.onclick = () => location.reload();
        });
    }

    function finishPre(session) {
        const correct = session.pre.filter((q) => q.user_answer && q.user_answer.trim() === (q.correct_option || '').trim()).length;
        const evalRes = evaluatePre(correct);
        session.pre_assessment_score = evalRes.score;
        session.pre_assessment_category = evalRes.category;
        session.difficulty = evalRes.difficulty;
        session.phase = 'pre_assessment_completed';
        session.pre_summary = evalRes.summary;
        persistInterview(session);
        return evalRes;
    }

    async function startMain(session) {
        const data = await loadBank();
        session.main = buildMainQuestions(data, session.role, session.difficulty);
        session.phase = 'main';
        session.total_questions = session.main.length;
        persistInterview(session);
        location.reload();
    }

    function renderPreComplete(root, session) {
        loadBank().then((data) => {
            const evalRes = {
                score: session.pre_assessment_score,
                category: session.pre_assessment_category,
                difficulty: session.difficulty,
                summary: session.pre_summary || ''
            };
            root.innerHTML = `
                <div class="assessment-result-banner animate-fade-up mb-3">
                    <span class="tag tag-cyan mb-2">Initial Assessment Phase Complete</span>
                    <h1 class="mb-2">Candidate Evaluation Results</h1>
                    <div class="card mb-3" style="max-width:640px;margin:0 auto;">
                        <div class="grid grid-2" style="text-align:center;">
                            <div><div class="text-secondary">Assessment Score</div>
                            <div style="font-size:3rem;font-weight:700;color:var(--neon-cyan);">${evalRes.score}/10</div></div>
                            <div><div class="text-secondary">Evaluation Level</div>
                            <div class="mt-1"><span class="tag tag-cyan">${escapeHtml(evalRes.category)}</span></div></div>
                        </div>
                        <p class="mt-2 text-secondary">${escapeHtml(evalRes.summary)}</p>
                    </div>
                    <div class="card mb-3" style="max-width:680px;margin:0 auto;text-align:left;">
                        ${(data.sections || []).map((sec) => `
                            <div style="padding:10px 0;border-bottom:1px solid var(--border-soft);">
                                <strong>Level ${sec.level}: ${escapeHtml(sec.title)}</strong>
                                <span class="text-muted"> · ${sec.marks} marks · ${sec.percentage}%</span>
                            </div>`).join('')}
                    </div>
                    <button class="btn btn-primary btn-lg" id="begin-main">Begin Main Practice Interview (60 Questions) →</button>
                </div>`;
            document.getElementById('begin-main').addEventListener('click', () => startMain(session));
        });
    }

    function completeMain(session) {
        const answers = session.main || [];
        const scores = answers.map((a) => a.score || 0);
        session.overall_score = scores.length ? Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10 : 0;
        session.avg_confidence = answers.length ? answers.reduce((a, q) => a + (q.confidence || 0), 0) / answers.length : 0;
        session.status = 'completed';
        persistInterview(session);
    }

    function renderResults() {
        const p = path();
        if (!(p === '/interview/report' || p === '/interview/report/')) return;
        if (!requireAuth()) return;
        const id = new URLSearchParams(location.search).get('id');
        const session = interviewsForUser().find((s) => s.id === id) || load(KEYS.active, null);
        const root = document.getElementById('results-root');
        if (!root) return;
        if (!session) {
            root.innerHTML = '<div class="card text-center"><p>No results found. <a href="/interview/start/">Start an interview</a>.</p></div>';
            return;
        }
        if (session.status !== 'completed' && session.main && session.main.every((q) => q.user_answer)) completeMain(session);
        root.innerHTML = `
            <div class="card mb-3 text-center">
                <h1 class="mb-2">Interview Performance Report</h1>
                <p class="text-secondary mb-3">${escapeHtml(session.role)} · ${escapeHtml(session.difficulty || '')}</p>
                <div class="score-ring" style="--pct:${session.overall_score || 0};"><div class="score-text">${session.overall_score || 0}%</div></div>
                <p class="text-secondary">Pre-assessment: ${escapeHtml(session.pre_assessment_category || '—')} (${session.pre_assessment_score || 0}/10)</p>
            </div>
            <div class="card mb-3">
                <h2 class="mb-2">Question Review</h2>
                ${(session.main || session.pre || []).slice(0, 12).map((q) => `
                    <div style="padding:10px 0;border-bottom:1px solid var(--border-soft);">
                        <strong>Q${q.index}.</strong> ${escapeHtml(q.q || '')}
                        <div class="text-secondary">Score: ${q.score == null ? '—' : q.score}</div>
                    </div>`).join('')}
            </div>
            <div class="text-center">
                <a class="btn btn-primary" href="/interview/start/">Take Another Interview</a>
                <a class="btn btn-secondary" href="/dashboard/">View Dashboard</a>
            </div>`;
    }

    function protectPages() {
        const p = path();
        const guarded = [
            '/dashboard', '/interview/start', '/interview/play', '/interview/report',
            '/interview/history', '/resume/upload', '/resume/view', '/resume/history'
        ];
        if (guarded.includes(p) && !currentUser()) {
            location.href = '/auth/login/?next=' + encodeURIComponent(location.pathname);
        }
    }

    function renderHomeCta() {
        const p = path();
        if (p !== '/') return;
        const user = currentUser();
        const cta = document.querySelector('.hero-cta');
        if (!cta || !user) return;
        cta.innerHTML = `
            <a href="/interview/start/" class="btn btn-primary btn-lg">Start Mock Interview</a>
            <a href="/resume/upload/" class="btn btn-secondary btn-lg">Analyze Resume</a>`;
    }

    renderNav();
    renderHomeCta();
    protectPages();
    bindAuthForms();
    bindInterviewStart();
    bindResumeUpload();
    renderDashboard();
    renderHistory();
    renderAtsReport();
    renderPlay();
    renderResults();
})();
