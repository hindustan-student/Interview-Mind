/* ============================================================
   InterviewMind - Interview session front-end logic
   ============================================================
   Handles:
     - MCQ option selection & styling
     - Word count & real-time guidance
     - Session timer
     - AJAX submission (MCQ and Descriptive)
     - Real-time feedback rendering
     - Transition to main practice interview & results
   ============================================================ */

(function () {
    'use strict';

    const form = document.getElementById('answer-form');
    if (!form) return;

    const textarea = document.getElementById('user_answer');
    const wordCount = document.getElementById('word-count');
    const timeElapsed = document.getElementById('time-elapsed');
    const submitBtn = document.getElementById('submit-btn');
    const feedbackCard = document.getElementById('feedback-card');
    const feedbackContent = document.getElementById('feedback-content');
    const nextBtn = document.getElementById('next-btn');
    const answerIdInput = document.getElementById('answer-id');
    const questionTypeInput = document.getElementById('question-type');

    let startTime = Date.now();
    let timer = null;

    // Timer
    function updateTimer() {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const s = String(elapsed % 60).padStart(2, '0');
        if (timeElapsed) {
            timeElapsed.textContent = `${m}:${s}`;
        }
    }
    timer = setInterval(updateTimer, 1000);

    // MCQ option click handling
    const mcqCards = document.querySelectorAll('.mcq-option-card');
    mcqCards.forEach(card => {
        card.addEventListener('click', function () {
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                mcqCards.forEach(c => c.classList.remove('is-selected'));
                this.classList.add('is-selected');
            }
        });
    });

    // Descriptive word count
    if (textarea && wordCount) {
        textarea.addEventListener('input', function () {
            const words = (textarea.value.trim().match(/\S+/g) || []).length;
            wordCount.textContent = `${words} word${words === 1 ? '' : 's'}`;
            if (words < 20) {
                wordCount.style.color = '#fca5a5';
            } else if (words < 50) {
                wordCount.style.color = '#fde68a';
            } else if (words <= 250) {
                wordCount.style.color = '#86efac';
            } else {
                wordCount.style.color = '#fde68a';
            }
        });
    }

    // Submit handler
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const qType = questionTypeInput ? questionTypeInput.value : 'descriptive';
        let answer = '';

        if (qType === 'mcq') {
            const selectedRadio = form.querySelector('input[name="user_answer_mcq"]:checked');
            if (!selectedRadio) {
                alert('Please select an option before submitting.');
                return;
            }
            answer = selectedRadio.value;
        } else {
            answer = (textarea ? textarea.value : '').trim();
            if (answer.length < 10) {
                alert('Please provide a more complete answer before submitting (at least 10 characters).');
                return;
            }
        }

        submitBtn.disabled = true;
        submitBtn.textContent = 'Evaluating...';

        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const payload = {
            answer_id: answerIdInput.value,
            user_answer: answer,
            time_taken: elapsed,
            csrf_token: form.querySelector('[name=csrf_token]').value,
        };

        fetch(`/interview/${window.INTERVIEW_SESSION_ID}/answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': payload.csrf_token,
            },
            body: JSON.stringify(payload),
        })
        .then(r => r.json())
        .then(data => {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Answer →';
            renderFeedback(data, qType, answer);
        })
        .catch(err => {
            console.error('Submit failed:', err);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Answer →';
            alert('Submission error — please try again.');
        });
    });

    function renderFeedback(data, qType, userAnswer) {
        const score = data.score !== undefined ? data.score : 0;
        const scoreColor = score >= 80 ? '#86efac' : score >= 50 ? '#fde68a' : '#fca5a5';

        // Highlight selected MCQ card
        if (qType === 'mcq') {
            mcqCards.forEach(card => {
                const radio = card.querySelector('input[type="radio"]');
                if (radio && radio.checked) {
                    if (score > 0) {
                        card.classList.add('is-correct');
                    } else {
                        card.classList.add('is-incorrect');
                    }
                }
            });
        }

        let html = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:12px;">
                <div>
                    <div style="font-family:'Space Grotesk',sans-serif;font-size:2rem;color:${scoreColor};font-weight:700;text-shadow:0 0 18px ${scoreColor}66;">
                        ${qType === 'mcq' ? (score > 0 ? '✓ Correct (100%)' : '✗ Incorrect (0%)') : score + '/100'}
                    </div>
                </div>
                <div class="text-secondary">
                    Confidence: <strong style="color:var(--neon-cyan);">${Math.round((data.confidence || 0) * 100)}%</strong>
                </div>
            </div>
            <p style="font-size:1.02rem;line-height:1.6;margin-bottom:16px;">${data.feedback || ''}</p>
        `;

        if (data.strengths && data.strengths.length) {
            html += `<h4 style="color:#86efac;margin-bottom:8px;">✓ Strengths</h4><ul style="margin-bottom:16px;padding-left:20px;line-height:1.7;">`;
            data.strengths.forEach(s => { html += `<li>${s}</li>`; });
            html += `</ul>`;
        }

        if (data.improvements && data.improvements.length) {
            html += `<h4 style="color:#fde68a;margin-bottom:8px;">→ Focus Area</h4><ul style="margin-bottom:16px;padding-left:20px;line-height:1.7;">`;
            data.improvements.forEach(s => { html += `<li>${s}</li>`; });
            html += `</ul>`;
        }

        feedbackContent.innerHTML = html;
        feedbackCard.style.display = 'block';
        feedbackCard.scrollIntoView({ behavior: 'smooth' });

        // Hide form once submitted
        form.style.display = 'none';

        if (data.pre_assessment_completed) {
            nextBtn.style.display = 'inline-flex';
            nextBtn.textContent = 'View Pre-Assessment Results →';
            nextBtn.onclick = () => {
                window.location.href = data.redirect || window.location.href;
            };
        } else if (data.completed) {
            nextBtn.style.display = 'inline-flex';
            nextBtn.textContent = 'View Final Results →';
            nextBtn.onclick = () => {
                window.location.href = data.redirect || window.INTERVIEW_NEXT_URL;
            };
        } else {
            nextBtn.style.display = 'inline-flex';
            nextBtn.textContent = 'Next Question →';
            nextBtn.onclick = () => {
                window.location.reload();
            };
        }
    }
})();
