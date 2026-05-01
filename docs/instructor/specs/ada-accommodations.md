# Spec: ADA Accommodation Controls

**Space:** `spaces/exam-admin/`
**Category:** Blocker — legal compliance
**Issue:** #29

---

## Goal

Allow instructors to extend exam time, reset attempt caps, and pause/resume active exam sessions for individual students — fulfilling Section 504 / ADA accommodation obligations at California Community Colleges.

---

## Inputs

- Active `ExamSession` keyed by token in `_SESSIONS` registry
- Instructor authenticated to exam-admin (EXAM_SECRET header or session cookie — auth spec TBD)
- Student token string (instructor looks up from their roster)

---

## New API Endpoints (exam-admin `app.py`)

### `POST /api/admin/extend-time`
```json
{ "token": "<student_token>", "additional_seconds": 3600 }
```
- Adds `additional_seconds` to `session.time_limit_seconds`.
- Returns: `{ "new_time_limit_seconds": N, "remaining_seconds": N }`
- Error 404 if session not found.

### `POST /api/admin/reset-attempts`
```json
{ "token": "<student_token>", "exercise_id": "D1", "reason": "technical issue" }
```
- Clears `session._attempts[exercise_id]` and `session._scores[exercise_id]`.
- Logs the reset with timestamp + reason to `session._admin_log`.
- Returns: `{ "exercise_id": "D1", "attempts_cleared": N, "reason_logged": true }`

### `POST /api/admin/pause-exam`
```json
{ "token": "<student_token>" }
```
- Sets `session.paused_at = int(time.time())`.
- While paused, all practical and theory POST endpoints for that token return 423 Locked with `{ "error": "exam_paused", "message": "Your exam has been paused by the instructor. Please wait." }`
- Returns: `{ "paused_at": timestamp }`

### `POST /api/admin/resume-exam`
```json
{ "token": "<student_token>" }
```
- Calculates `pause_duration = now - session.paused_at`.
- Adds `pause_duration` to `session.time_limit_seconds` (so paused time doesn't count against the student).
- Clears `session.paused_at`.
- Returns: `{ "pause_duration_seconds": N, "new_time_limit_seconds": N }`

---

## Changes to `ExamSession` (`framework/exam_session.py`)

- Add `paused_at: int | None = None`
- Add `_admin_log: list[dict] = []` — append-only log of all admin actions
- `is_paused() -> bool` — returns `paused_at is not None`
- `elapsed_seconds()` — must subtract total paused duration (track in `_pause_duration_total`)

---

## Exam-Admin UI Changes (`static/js/admin.js`)

Add an **Accommodation Panel** in the Verify view (visible only when a live session is found for the receipt's token):

- **Extend Time** — number input (minutes) + "Add Time" button → calls `/api/admin/extend-time`
- **Reset Attempts** — exercise dropdown + reason text + "Reset" button → calls `/api/admin/reset-attempts`
- **Pause / Resume** — toggle button, shows current pause state + duration → calls pause/resume endpoints

All actions append a timestamped entry to a visible **Admin Action Log** within the panel.

---

## Expected Outputs

- Instructor can grant 1.5× or 2× time for any active session without touching the token
- Student whose attempt cap is exhausted due to tech failure can be reset and continue
- Paused exam stops the clock; resume restores it exactly
- All admin actions are recorded in `_admin_log` and included in the receipt when finalized

---

## Acceptance Checks

- [ ] `POST /api/admin/extend-time` with `additional_seconds: 3600` increases `remaining_seconds` by 3600
- [ ] `POST /api/admin/reset-attempts` clears attempt count; student can submit the exercise again
- [ ] Paused session returns 423 on practical POST endpoints
- [ ] Resume adds pause duration to time limit (clock resumes with same remaining time)
- [ ] Admin actions appear in receipt JSON under `admin_log` field
- [ ] Endpoints return 404 for unknown token (never 500)
- [ ] Endpoints require EXAM_SECRET header; return 401 without it

---

## What Could Go Wrong

- **Server restart loses session state** — existing risk; admin actions can't be recovered. Mitigation: document in instructor guide that HF Space restarts reset in-memory sessions.
- **Race condition on pause/resume** — student submits milliseconds before pause takes effect. Mitigation: accept the submission; log records the sequence.
- **Token lookup by instructor** — instructor must have the student's token string. Mitigation: token CSV from generator UI (issue #31) must be kept by instructor.
