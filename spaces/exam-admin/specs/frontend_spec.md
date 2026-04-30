# Frontend Spec — exam-admin Space

## Goal

A single-page instructor tool: verify signed receipts, review short-answer responses against a rubric, assign scores, and push grades to Canvas. No tabs, two views (Verify and Batch), toggled by a top nav.

---

## Design Constraints

- Luminex design tokens (vendored CSS, identical to other spaces)
- Vanilla ES6+, no framework, no npm
- Responsive down to 1024 px wide (instructor laptops)
- No dark-mode toggle — dark-only (standard platform theme)
- No student-facing content — this is an instructor-only tool
- NR-8 compliant: zero hardcoded hex colors, all via `--color-*` tokens

---

## Views

### View 1 — Verify (default)

**Upload zone:**
- Large drag-drop target, centered, dashed border using `--color-border`
- Label: "Drop a receipt .json file here, or click to browse"
- Accepts single JSON file
- On drop/select: reads file → parses JSON → `POST /api/verify`
- Error states (user-visible, no JS console trace leaking):
  - Not valid JSON: "Not a valid JSON file."
  - JSON but wrong schema (missing `receipt_version`): "File does not look like an AI Security Labs receipt."
  - Network error: "Verification failed — server unreachable."

**Verification result card (appears below upload zone after response):**

```
┌─────────────────────────────────────────────────────────────┐
│  ✓ HMAC VERIFIED  │  student_id    │  exam_id              │
│  (green badge)    │  lab_id        │  receipt_version: 1   │
├──────────────────────────────┬──────────────────────────────┤
│  PRACTICAL                   │  THEORY                      │
│  Level 1:  80 / 100          │  MCQ:  45 / 50              │
│  Level 2:  60 / 100          │  Short Answer: 0 / 60 ◀─── │
│  Level 3: 100 / 100          │  (awaiting instructor score) │
│  Level 4:  40 / 100          │                              │
│  Level 5:   0 / 100          │                              │
│  ─────────────────           │  ──────────────              │
│  Total: 280 / 500            │  Total: 45 / 110            │
└──────────────────────────────┴──────────────────────────────┘
│  Timing: 1h 22m used / 3h limit                             │
│  [▼ Expand Short Answers & Rubric]  [↓ Export CSV Row]      │
└─────────────────────────────────────────────────────────────┘
```

- `✓ HMAC VERIFIED` badge: green (`--color-success`) when valid, red (`--color-danger`) + `✗ INVALID HMAC` when not
- Clicking `[▼ Expand Short Answers & Rubric]` reveals the SA scoring panel

**Short-answer scoring panel (expanded):**

For each short-answer question (3 per lab):
```
┌─────────────────────────────────────────────────────────────┐
│  SA-1 (Bloom L5 — Evaluate)   ·  20 pts possible            │
│  ─────────────────────────────────────────────────────────── │
│  Question: [question text from receipt or rubric API]        │
│  ─────────────────────────────────────────────────────────── │
│  Student response (147 words):                               │
│  [student response text, scrollable, read-only textarea]     │
│  ─────────────────────────────────────────────────────────── │
│  RUBRIC                          Score                       │
│  Technical Accuracy     (×1.0)   [0][1][2][3][4]            │
│  Specificity            (×1.0)   [0][1][2][3][4]            │
│  Professional Framing   (×1.0)   [0][1][2][3][4]            │
│  Coverage               (×1.0)   [0][1][2][3][4]            │
│  Conciseness            (×1.0)   [0][1][2][3][4]            │
│  ─────────────────────────────────────────────────────────── │
│  Subtotal: 0 / 20          [Clear]                          │
└─────────────────────────────────────────────────────────────┘
```

- Score buttons: clicking a number highlights it, clears others in the row
- Running subtotal updates as scores are entered
- Only show SA panel if `theory.submitted == true` in receipt; otherwise: "Student did not submit theory section."

**Action bar (below SA panel):**
- `[Submit Grade to Canvas]` button — active only if LTI is configured (`EXAM_LTI_*` secrets present) and all SA scores entered
- `[↓ Export CSV Row]` button — always active; downloads a single-row CSV: `student_id,lab_id,practical_score,mcq_score,sa_score,total,hmac_valid,exam_id`

---

### View 2 — Batch

**Upload zone:**
- Accepts multiple JSON files (or a zip — v2)
- Drag-drop or click-to-browse, multiple selection

**Results table:**

| student_id | exam_id | lab_id | practical | MCQ | SA | total | HMAC |
|------------|---------|--------|-----------|-----|----|-------|------|
| jsmith@    | spring26| red-team | 280 | 45 | — | 325 | ✓ |
| mjones@    | spring26| red-team | 350 | 40 | — | 390 | ✓ |
| lwang@     | spring26| red-team | 100 | 30 | — | 130 | ✗ |

- ✓ = green badge, ✗ = red badge
- SA column shows `—` until instructor enters scores via row expand
- Click any row to open the single-receipt SA scoring panel in a slide-out drawer
- `[Export CSV]` button: downloads full table as CSV
- `[Submit All Grades to Canvas]` button: posts grades for all ✓ rows with SA scores entered

---

## Navigation

Top bar:
```
[AI Security Labs logo]  Exam Admin    [Verify]  [Batch]    Powered by Luminex
```

Same `.nav-*` classes as other spaces. No Info tab, no Leaderboard tab.

---

## Acceptance Checks

- [ ] Default view on load is Verify
- [ ] Drag-drop zone accepts `.json` file and triggers verification without page reload
- [ ] Invalid JSON shows user-facing error message (not a JS console exception)
- [ ] HMAC badge is green for a valid receipt, red for a tampered one
- [ ] Score buttons in rubric panel are mutually exclusive per row
- [ ] SA subtotal updates in real time as score buttons are clicked
- [ ] Export CSV Row produces a valid CSV file with the correct column headers
- [ ] Batch view table renders after multi-file upload
- [ ] Batch Export CSV button downloads all rows
- [ ] Submit Grade to Canvas button is disabled when LTI is not configured
- [ ] No hardcoded hex colors (NR-8 compliant)
