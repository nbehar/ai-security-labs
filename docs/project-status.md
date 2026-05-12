# AI Security Labs — Platform Project Status

Last updated: 2026-05-11 (Auth verified all spaces; reviewer fixes applied)

---

## Live Spaces

| # | Space | HF Space | Status |
|---|-------|------------|--------|
| 1 | owasp-top-10 | `nikobehar/llm-top-10` | ✅ Live + Firebase Auth ON |
| 1a | owasp-top-10 (private copy) | `nikobehar/ai-sec-lab1-owasp-top-10` | ✅ Live (private) + Firebase Auth ON — **needs GROQ_API_KEY** |
| 2 | blue-team | `nikobehar/blue-team-workshop` | ✅ Live + Exam Mode + Firebase Auth ON |
| 3 | red-team | `nikobehar/red-team-workshop` | ✅ Live + Exam Mode + Firebase Auth ON |
| 4 | multimodal | `nikobehar/ai-sec-lab4-multimodal` | ✅ Live + Exam Mode + Firebase Auth ON |
| 5 | data-poisoning | `nikobehar/ai-sec-lab5-data-poisoning` | ✅ Live + Exam Mode + Firebase Auth ON |
| 6 | detection-monitoring | `nikobehar/ai-sec-lab6-detection` | ✅ Live + Exam Mode + Firebase Auth ON |

---

## Planned Spaces Pipeline

| # | Space | Status |
|---|-------|--------|
| 7 | incident-response | Planned |
| 8 | multi-agent | Planned |
| 9 | model-forensics | Planned |
| 10 | ai-governance | Planned |
| — | exam-admin | ✅ Live (private) — `nikobehar/ai-sec-lab-exam-admin` |

---

## Summative Assessment System

A two-tier exam system layered on top of existing lab spaces.

### Framework Files

| File | Status |
|------|--------|
| `framework/exam_token.py` | ✅ Complete — HMAC token generation + validation |
| `framework/exam_session.py` | ✅ Complete — attempt caps, timing, receipt serialization, pause/resume/extend/reset |
| `framework/exam_questions.py` | ✅ Complete — 10 MCQ + 3 SA per lab (Bloom's 4–6), Red Team + Detection |
| `framework/static/js/exam_mode.js` | ✅ Complete — timer banner, theory form, WebCrypto receipt signing |
| `scripts/generate_exam_token.py` | ✅ Complete — instructor CLI |

### Exam Phases

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Token infrastructure (exam_token.py, exam_session.py, deploy.sh) | ✅ Complete |
| Phase 2 | Detection & Monitoring exam mode (exam_data_v1/v2.py, app.py routes) | ✅ Complete |
| Phase 3 | Red Team exam mode (exam_challenges_v1/v2.py, app.py routes + slowapi) | ✅ Complete |
| Phase 4 | Theory assessment (exam_questions.py, exam_mode.js) | ✅ Complete |
| Phase 5 | exam-admin space (verification UI, LTI grade passback) | ✅ Live — `nikobehar/ai-sec-lab-exam-admin` |
| Phase 6 | Blue Team, Multimodal, Data Poisoning exam routes | ✅ Complete |
| Phase 7 | Cross-lab capstone | Deferred |

### Exam Dataset Coverage

| Lab | Section A (exam_v1) | Section B (exam_v2) |
|-----|--------------------|---------------------|
| Red Team | ✅ exam_challenges_v1.py | ✅ exam_challenges_v2.py |
| Detection | ✅ exam_data_v1.py | ✅ exam_data_v2.py |
| Blue Team | ✅ exam_challenges_v1.py | ✅ exam_challenges_v2.py |
| Multimodal | ✅ exam_attacks_v1.py | ✅ exam_attacks_v2.py |
| Data Poisoning | ✅ exam_attacks_v1.py | ✅ exam_attacks_v2.py |

---

## Instructor Support Package

ADA Section 504 accommodations, class roster dashboard, and token generator for exam administration.

| Issue | Feature | Status | Commit |
|-------|---------|--------|--------|
| #29 | ADA accommodation controls (extend-time, reset-attempts, pause/resume) | ✅ Implemented | `5e257f34` |
| #30 | Class roster dashboard (live student status, 30s auto-refresh) | ✅ Implemented | `5e257f34` |
| #31 | Web-based batch token generator (CSV upload → tokens CSV download) | ✅ Implemented | `f4e67fcb` |
| #32 | Instructor preview mode | Planned | — |
| #33 | WCAG 2.1 AA audit + remediation | Partial (A3/A6/A7 fixed) | — |
| #34 | Facilitator guides (3 live labs) | Planned | — |
| #35 | Course materials package | Planned | — |
| #36 | Additional assessment types | Planned | — |

**Admin routes added to lab spaces (`5e257f34`):**
- `spaces/red-team/app.py` — 6 admin routes: roster, load-roster, extend-time, reset-attempts, pause-exam, resume-exam + pause check in practical endpoint
- `spaces/detection-monitoring/app.py` — same 6 admin routes + pause check in `_resolve_exam_session`
- `framework/exam_session.py` — `pause()`, `resume()`, `extend_time()`, `reset_exercise()`, `is_paused()`, `_admin_log`

---

## Firebase Authentication

All student-facing spaces are gated behind Firebase Auth (server-side `app_auth.py` middleware + client-side `firebase_auth.js` overlay).

| Component | Status |
|-----------|--------|
| `framework/app_auth.py` | ✅ Deployed — FastAPI middleware, token from Bearer header or `firebase_token` query param (SSE workaround) |
| `framework/static/js/firebase_auth.js` | ✅ Deployed — email magic link, Google, GitHub, SMS sign-in; gold owl overlay |
| Firebase project | `ai-security-labs` — `ai-security-labs.firebaseapp.com` |
| HF Space secrets | `FIREBASE_API_KEY` + `FIREBASE_CREDENTIALS` + `FIREBASE_PROJECT_ID` + `FIREBASE_AUTH_DOMAIN` set on all 5 live spaces |
| Space visibility | All 5 student-facing spaces set to **protected** (HF login required before auth overlay) |

**Spaces with Firebase auth verified (all 7 checked 2026-05-11):**
- `nikobehar/llm-top-10` ✅ RUNNING
- `nikobehar/ai-sec-lab1-owasp-top-10` ✅ RUNNING (private; requires HF cookie auth for programmatic access)
- `nikobehar/red-team-workshop` ✅ RUNNING
- `nikobehar/blue-team-workshop` ✅ RUNNING
- `nikobehar/ai-sec-lab5-data-poisoning` ✅ RUNNING (fixed: added `firebase-admin` to requirements.txt)
- `nikobehar/ai-sec-lab6-detection` ✅ RUNNING
- `nikobehar/ai-sec-lab4-multimodal` ✅ RUNNING

**Auth implementation — reviewer fixes applied (`65b26bd`):**
- `getIdToken()`: added `forceRefresh:true` fallback in catch block — prevents silent null return after network-disrupted refresh
- `app_auth.py`: `/api/admin/` prefix added to pass-through list — admin routes protected by `EXAM_SECRET` alone (server-to-server); no Firebase token required from exam-admin proxy
- SSE token injection was already correct (`owasp-top-10/app.js:1497-1499`)

**Pending (user action required):**
- `ai-sec-lab1-owasp-top-10`: set `GROQ_API_KEY` in HF Space Settings (copy from `llm-top-10`)
- Custom domains `aisl1`–`aisl6.luminexlab.app` — set via HF Space Settings UI (no API)
- All `aisl*.luminexlab.app` domains → Firebase Console → Authentication → Authorized domains
- Namecheap DNS CNAMEs: each `aisl*.luminexlab.app` → `nikobehar-{space-name}.hf.space`

---

## Framework Stability

| Module | In use by |
|--------|----------|
| `groq_client.py` | red-team, blue-team, owasp-top-10, multimodal |
| `scoring.py` | all spaces |
| `app_auth.py` | all 6 live spaces (+ data-poisoning locally) |
| `static/js/firebase_auth.js` | all 6 live spaces |
| `exam_token.py` | red-team, detection-monitoring, blue-team, multimodal, data-poisoning, exam-admin |
| `exam_session.py` | red-team, detection-monitoring, blue-team, multimodal, data-poisoning |
| `exam_questions.py` | red-team, detection-monitoring, blue-team, multimodal, data-poisoning, exam-admin |
| `static/js/exam_mode.js` | all exam-mode spaces (5 labs) |

---

## Open Issues

| Issue | Title | Status |
|-------|-------|--------|
| #27 | Detection & Monitoring lab (Space 6) | ✅ Closed — deployed `nikobehar/ai-sec-lab6-detection` |
| #28 | exam-admin space | ✅ Closed — deployed `nikobehar/ai-sec-lab-exam-admin` |
| #32 | Instructor preview mode | Open — planned |
| #33 | WCAG 2.1 AA audit + remediation | Open — partial (A3/A6/A7 fixed) |
| #34 | Facilitator guides | Open — planned |
| #35 | Course materials package | Open — planned |
| #36 | Additional assessment types | Open — planned |

---

## Blockers

- exam-admin LTI: requires Canvas admin access for one-time tool registration (per `specs/deployment_spec.md`)

---

## Next Recommended Task

**Immediate (user action):**
1. Set `GROQ_API_KEY` on `ai-sec-lab1-owasp-top-10` in HF Space Settings
2. Set custom domains `aisl1`–`aisl6.luminexlab.app` in each HF Space Settings → Custom domain
3. Add those domains to Firebase Console → Authentication → Authorized domains
4. Add Namecheap CNAMEs: each `aisl*.luminexlab.app` → `nikobehar-{space}.hf.space`

**Code backlog (no blockers):**
- bd-bk7 (P4): Fix root CLAUDE.md "3 live workshops" → "6 live workshops"
- bd-n6y (P4): Facilitator guides for 3 live labs (GitHub issue #34)
- bd-qoq (P4): Course materials package (GitHub issue #35)
- bd-t51 (P4): Additional assessment types (GitHub issue #36)

---

## Session History

| Date | Work |
|------|------|
| 2026-04-28 | Platform architecture established. owasp-top-10, blue-team, red-team live. |
| 2026-04-29 | Multimodal (Space 4) and data-poisoning (Space 5) specs + implementation. Detection & Monitoring (Space 6) Phase 0 bootstrap. |
| 2026-04-30 | Detection & Monitoring Phase 1+2 complete. Summative assessment system Phases 1–5 complete: exam_token.py, exam_session.py, exam_questions.py, exam_mode.js, Red Team exam routes + datasets, Detection exam routes + datasets, exam-admin space (verify UI + LTI grade passback). |
| 2026-04-30 | Instructor support package: `framework/exam_session.py` enhanced with pause/resume/extend_time/reset_exercise + admin_log (`cc80abd9`). exam-admin upgraded to 4-tab UI (Verify/Batch/Roster/Generate) with accommodation panel + roster view + token generator wizard (`f4e67fcb`). red-team/app.py + detection-monitoring/app.py got 6 admin routes each + _ROSTER_MAP + pause check (`5e257f34`). CSS: admin.css updated with .accom-*, .roster-table, .generate-form, .sr-only, .lab-connect-* (`5e257f34`). Issues #29–#31 implemented. |
| 2026-05-01 | Deployed detection-monitoring (Space 6) to `nikobehar/ai-sec-lab6-detection` — all acceptance checks pass. Deployed exam-admin to `nikobehar/ai-sec-lab-exam-admin` (private) — all 8 acceptance checks pass (`6df83b0`). Closed GitHub issues #27 + #28. Closed 5 superseded PRs (#23 #24 #25 #26 #38). Initialized Beads issue tracker + Agent Mail. |
| 2026-05-01 | Phase 6 complete: Blue Team exam mode (`18b79b6`), Multimodal exam mode (`3e3ccbe`, `d44e8cb`), Data Poisoning exam mode (`d44e8cb`). All 5 labs now have exam mode with attempt caps, theory assessment, signed receipts. Exam datasets: 12 variants across 5 labs (2 sections each). framework/exam_questions.py has all 5 lab sections (10 MCQ + 3 SA each, Bloom's 4–6). Closed bd-wk3, bd-6xr, bd-asb, bd-aen. |
| 2026-05-06–08 | Firebase Auth rollout: `framework/app_auth.py` + `framework/static/js/firebase_auth.js` deployed to all 6 live spaces. Root cause fixed: `core.js` with `renderPreviewBanner` export was blocked by space `.gitignore` — removed exclusion and uploaded via Python API. Gold owl CSS filter added to auth overlay. Private copy of owasp-top-10 created (`ai-sec-lab1-owasp-top-10`). Data poisoning space created (`ai-sec-lab5-data-poisoning`). All 5 student-facing spaces set to `protected` visibility. Firebase project `ai-security-labs` configured; HF secrets set on all spaces. Auth verified via Puppeteer on all 5 awake spaces. Custom domains (`aisl*.luminexlab.app`) pending user DNS setup. |
