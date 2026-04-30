# Spec: Instructor Preview Mode

**Space:** All lab spaces (platform-level)
**Category:** UX — instructor adoption
**Issue:** #32

---

## Goal

Let instructors walk through any lab as a student would — seeing the full UI, submitting attacks, viewing feedback — without consuming exam attempts, affecting the leaderboard, or requiring a valid exam token.

---

## Inputs

- URL query parameter: `?preview=<PREVIEW_TOKEN>`
- `PREVIEW_TOKEN` is a separate HF Space secret (a short shared password, not an exam token)
- No per-student identity needed; preview mode is instructor/TA only

---

## Backend Changes (each lab `app.py`)

- Add `PREVIEW_TOKEN = os.environ.get("PREVIEW_TOKEN", "")` config
- New dependency `verify_preview_token(request)` — checks `X-Preview-Token` header or `preview` query param against `PREVIEW_TOKEN`
- When preview token is valid:
  - Practical endpoints skip attempt cap enforcement
  - Scores are computed and returned normally (instructor sees real feedback)
  - Responses include an extra field: `"preview_mode": true`
  - **Nothing is written** to `_SESSIONS`, leaderboard, or any persistent state
- When `PREVIEW_TOKEN` env var is empty, preview mode is disabled (no-op; don't expose the feature)

---

## Frontend Changes (`static/js/app.js` + `exam_mode.js`)

- On page load, detect `?preview=TOKEN` in the URL
- Send `X-Preview-Token: TOKEN` header on all API calls
- Render a sticky **Preview Mode banner** at the top of the page:
  > `🔍 INSTRUCTOR PREVIEW — scores are not recorded`
  (Banner uses `--color-warning` token; never shown without a valid preview token response)
- Suppress leaderboard tab in preview mode (or show it read-only without the student's preview score)
- Do not show exam timer or attempt counter in preview mode

---

## Expected Outputs

- Instructor sees exactly what a student sees, including WHY cards, scoring breakdowns, and KC questions
- No preview activity appears in the leaderboard or exam sessions
- Instructor can demo the lab live during a class session without polluting student data

---

## Acceptance Checks

- [ ] `?preview=CORRECT_TOKEN` on any lab URL renders the preview banner
- [ ] `?preview=WRONG_TOKEN` renders no banner and behaves as normal workshop mode
- [ ] Practical submission in preview mode returns a real score response with `preview_mode: true`
- [ ] Leaderboard `GET /api/leaderboard` does not include any preview submissions
- [ ] `_SESSIONS` registry is unchanged after preview submissions
- [ ] When `PREVIEW_TOKEN` env var is unset, `?preview=anything` is silently ignored
- [ ] Preview banner is visible in both workshop and exam-mode UI layouts

---

## What Could Go Wrong

- **Preview token leaked in URL** — browser history, proxy logs, and LMS link-paste could expose it. Mitigation: keep PREVIEW_TOKEN short-lived; rotate each semester. Document in instructor guide.
- **Students discover the preview token** — they could use it to get unlimited attempts. Mitigation: preview mode skips attempt caps but doesn't change dataset (same workshop data); exam integrity relies on the exam token + dataset variant, not on limiting preview.
