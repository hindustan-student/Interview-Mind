# User Manual

## Getting Started

1. **Register** an account at `/auth/register`. Pick a target role (Software
   Engineer, Data Scientist, etc.) — this is just a default; you can override
   it per interview.

2. **Login** at `/auth/login`.

3. **Upload your resume** at `/resume/upload`. The system extracts text from
   PDF, DOCX, or TXT files and computes:
   - ATS score (0-100)
   - Keyword coverage (% of role-relevant keywords found)
   - Matched vs missing keywords
   - Sections found vs missing
   - Tailored recommendations

4. **Take a mock interview** at `/interview/start`:
   - Select role, category, difficulty, and number of questions
   - Answer each question using the STAR method
   - Get instant feedback after each submission
   - View the final report with category breakdown

5. **Track progress** at `/dashboard` — see your score trend, average
   ATS score, best interview score, and recent activity.

6. **Browse the question bank** at `/questions/` to study model answers
   without taking a full interview.

## Tips for Better Scores

- **Use the STAR method** explicitly: say "Situation...", "Task...",
  "Action...", "Result..." to max the STAR score component.
- **Aim for 80-250 words** per answer — the length component peaks there.
- **Avoid hedge words** ("um", "like", "I guess") — they tank your confidence
  proxy.
- **Use action verbs** — "led", "implemented", "shipped", "delivered" boost
  the confidence score.
- **Include role keywords** — covering expected keywords boosts the keyword
  score (highest weight component).

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Particle background not visible | Disable `prefers-reduced-motion` in your OS, or check console for errors. |
| Resume upload fails | Ensure file is under 5 MB and is PDF/DOCX/TXT. Scanned-image PDFs return 0 score. |
| Interview won't start | Login is required. Ensure your session hasn't expired (1 hour timeout). |
| 404 on dashboard | Trailing slash matters — `/dashboard/` (with slash) is canonical. |
| Tests fail | Make sure pytest is installed: `pip install pytest pytest-flask`. |

## Browser Support

Tested on:
- Chrome 110+
- Firefox 110+
- Edge 110+
- Safari 16+

The particle engine uses `requestAnimationFrame`, Canvas 2D, and
`globalCompositeOperation = 'lighter'` — all supported in modern browsers.
