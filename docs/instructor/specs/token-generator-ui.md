# Spec: Web-Based Batch Token Generator

**Space:** `spaces/exam-admin/`
**Category:** UX — instructor adoption blocker for non-technical faculty
**Issue:** #31

---

## Goal

Replace the CLI-only `scripts/generate_exam_token.py` with a web form in exam-admin that lets an instructor upload a student roster CSV, configure exam parameters, and download a ready-to-distribute token CSV — no terminal required.

---

## Inputs

- Instructor uploads `roster.csv`: `student_id` column (LMS usernames)
- Instructor fills form: exam ID, section (A/B), duration hours, date/time the exam opens and closes
- EXAM_SECRET (already in HF Space secrets — never touches the browser)

---

## New API Endpoint (exam-admin `app.py`)

### `POST /api/admin/generate-tokens`
```json
{
  "exam_id": "spring2026-final",
  "student_ids": ["jsmith@univ.edu", "mjones@univ.edu"],
  "lab_ids": ["red-team", "detection-monitoring"],
  "section": "A",
  "duration_hours": 3,
  "opens_at": 1746100000,
  "expires_at": 1746200000
}
```
Server calls `generate_token(payload, EXAM_SECRET)` for each student.
Returns:
```json
{
  "tokens": [
    { "student_id": "jsmith@univ.edu", "token": "eyJ...", "exam_url": "https://...?exam_token=eyJ..." },
    ...
  ],
  "count": 32
}
```
Rate limit: 5 req/min (token generation is a privileged operation).

---

## Exam-Admin UI Changes

Add a **Generate** view (fourth tab in the view nav):

**Step 1 — Exam Configuration** (form):
- Exam ID text field (e.g. `spring2026-final`)
- Section radio: A / B (maps to `exam_v1` / `exam_v2`)
- Labs multi-select checkboxes (one per deployed lab)
- Duration: number input in hours (default: 3)
- Opens: datetime-local input
- Closes: datetime-local input (auto-sets token `expires_at`)

**Step 2 — Upload Roster**:
- Drag-drop CSV upload zone; accepts `student_id` column (other columns ignored)
- Preview table: shows first 5 rows, count of total students found

**Step 3 — Generate**:
- "Generate Tokens" button → calls `/api/admin/generate-tokens`
- Progress indicator while generating

**Step 4 — Download**:
- Result summary: `32 tokens generated`
- **Download Token CSV** button — produces `spring2026-final_tokens.csv`:
  ```
  student_id,token,exam_url
  jsmith@univ.edu,eyJ...,https://huggingface.co/spaces/nikobehar/red-team-workshop?exam_token=eyJ...
  ```
- **Copy Canvas Announcement** button — copies a pre-written Canvas announcement template to clipboard:
  > "Your exam token is in the Feedback column of the [Assignment Name] submission. Click the lab URL to begin. Tokens expire at [closes_at time]." 
  (Instructor pastes to Canvas; Canvas bulk feedback upload handles individual token distribution.)

---

## Expected Outputs

- Instructor can generate tokens for 35 students in under 2 minutes, no terminal
- Downloaded CSV is ready to upload to Canvas as bulk feedback comments
- Token URLs encode the lab URL so students don't need to navigate manually

---

## Acceptance Checks

- [ ] Upload of a 35-row CSV produces 35 tokens within 5 seconds
- [ ] Each generated token passes `validate_token(token, EXAM_SECRET, lab_id)` for all selected lab_ids
- [ ] `expires_at` in token payload matches the closes_at field from the form
- [ ] Downloaded CSV has `student_id`, `token`, `exam_url` columns
- [ ] Endpoint returns 401 without EXAM_SECRET header
- [ ] Malformed CSV (missing student_id column) returns 422 with a human-readable error
- [ ] Generating tokens for 100 students completes without timeout (≤ 10s)

---

## What Could Go Wrong

- **Instructor uploads wrong CSV column** — student_id column name varies by LMS export. Mitigation: accept first column if `student_id` header not found; warn in preview.
- **Tokens distributed before exam opens** — `opens_at` / `issued_at` enforcement prevents early use. Instructor must set opens_at correctly.
- **EXAM_SECRET not configured** — Generate tab shows a warning banner and disables the Generate button if `/health` reports `exam_secret_configured: false`.
