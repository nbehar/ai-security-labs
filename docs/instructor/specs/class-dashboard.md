# Spec: Class Roster Dashboard

**Space:** `spaces/exam-admin/`
**Category:** Blocker — operational requirement
**Issue:** #30

---

## Goal

Give instructors a live class-level view during an exam: who has started, who is stuck, per-exercise attempt counts, and class-average scores — without requiring individual receipt uploads.

---

## Inputs

- All `ExamSession` objects in the `_SESSIONS` registry (in-memory)
- Optional: instructor uploads a CSV of expected student tokens at session start (maps token → display name)

---

## New API Endpoints (exam-admin `app.py`)

### `GET /api/admin/roster`
Returns summary rows for all active sessions.
```json
{
  "exam_id": "spring2026-final",
  "generated_at": 1746000000,
  "students": [
    {
      "student_id": "jsmith@univ.edu",
      "token_preview": "eyJleGFt...",
      "started": true,
      "elapsed_minutes": 47,
      "remaining_minutes": 133,
      "paused": false,
      "exercises": [
        { "exercise_id": "D1", "attempts": 1, "cap": 1, "best_score": 84, "complete": true },
        { "exercise_id": "D2", "attempts": 2, "cap": 3, "best_score": 60, "complete": false },
        { "exercise_id": "D3", "attempts": 0, "cap": 3, "best_score": 0, "complete": false }
      ],
      "theory_submitted": false,
      "total_so_far": 144
    }
  ],
  "class_averages": {
    "D1": 78,
    "D2": 55,
    "D3": 0,
    "theory_mcq": null
  },
  "not_started": ["mjones@univ.edu", "kwilliams@univ.edu"]
}
```

### `POST /api/admin/load-roster`
Accepts a CSV upload: `student_id,token` — stores a display-name mapping for the current session.
```
Content-Type: multipart/form-data
file: roster.csv
```
Returns: `{ "loaded": 32, "unrecognized": 0 }`

---

## Exam-Admin UI Changes

Add a **Roster** view (third tab in the view nav, after Verify and Batch):

**Header bar:**
- Exam ID (auto-detected from first active session)
- Student count: `N active / M expected`
- Auto-refresh toggle (default: every 30 seconds)
- Upload Roster CSV button

**Roster table** (one row per student):
| Student | Time Left | D1 | D2 | D3 | Theory | Total |
|---------|-----------|----|----|----|---------| ------|
| jsmith | 2h 13m | ✅ 84 | ⏳ 60 (2/3) | — | — | 144 |

Status icons: ✅ cap reached or perfect score · ⏳ in progress · ⚠️ cap exhausted, no score · — not started

**Class Averages row** pinned at the bottom of the table.

**Alert strip** (top of table, dismissible): highlights students with:
- Attempt cap exhausted + score < 50 (may need reset)
- < 30 minutes remaining + theory not submitted
- Session paused

---

## Expected Outputs

- Instructor can see at a glance which students need intervention during the exam window
- Class averages identify exercises where the whole class is struggling (may indicate a dataset/scoring issue)
- Not-started list lets instructor ping students via LMS before time runs out

---

## Acceptance Checks

- [ ] `GET /api/admin/roster` returns correct attempt counts and best scores matching session state
- [ ] Row updates within one refresh cycle (≤ 30s) when a student submits an attempt
- [ ] `not_started` list shows tokens that were loaded via CSV but have no session in `_SESSIONS`
- [ ] Paused student row shows ⏸ icon
- [ ] Alert strip fires for attempt-exhausted + low-score condition
- [ ] Endpoint requires EXAM_SECRET header; returns 401 without it
- [ ] Returns `{ "students": [] }` (not 500) if no sessions are active

---

## What Could Go Wrong

- **Performance at 35+ students** — `_SESSIONS` scan is O(n) over all sessions, not just one exam. Mitigation: filter by `exam_id` from the loaded roster; ignore sessions from other exams.
- **Stale data on server restart** — sessions are lost. The dashboard will show all students as "not started" after a restart. Mitigation: note in instructor guide; HF cpu-basic spaces restart infrequently during active use.
- **Privacy** — roster endpoint exposes all student IDs and scores. Mitigation: EXAM_SECRET header auth gates the endpoint; TLS is enforced by HF proxy.
