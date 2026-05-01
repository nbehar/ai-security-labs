# AI Security Labs — Platform Project Status

Last updated: 2026-04-30

---

## Live Spaces

| # | Space | HF Space | Status |
|---|-------|------------|--------|
| 1 | owasp-top-10 | `nikobehar/llm-top-10` | ✅ Live |
| 2 | blue-team | `nikobehar/blue-team-workshop` | ✅ Live |
| 3 | red-team | `nikobehar/red-team-workshop` | ✅ Live + Exam Mode (Phase 3 complete) |
| 4 | multimodal | `nikobehar/ai-sec-lab4-multimodal` | ✅ Live (Phase 3 + defenses complete) |
| 5 | data-poisoning | `nikobehar/ai-sec-lab5-data-poisoning` | ✅ Live |
| 6 | detection-monitoring | `nikobehar/ai-sec-lab6-detection` | Phase 2 complete — deploy pending |

---

## Planned Spaces Pipeline

| # | Space | Status |
|---|-------|--------|
| 7 | incident-response | Planned |
| 8 | multi-agent | Planned |
| 9 | model-forensics | Planned |
| 10 | ai-governance | Planned |
| — | exam-admin | Phase 2 complete — deploy pending (private space) |

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
| Phase 5 | exam-admin space (verification UI, LTI grade passback) | ✅ Code complete — deploy pending |
| Phase 6 | Blue Team, Multimodal, Data Poisoning exam routes | Planned |
| Phase 7 | Cross-lab capstone | Deferred |

### Exam Dataset Coverage

| Lab | Section A (exam_v1) | Section B (exam_v2) |
|-----|--------------------|---------------------|
| Red Team | ✅ exam_challenges_v1.py | ✅ exam_challenges_v2.py |
| Detection | ✅ exam_data_v1.py | ✅ exam_data_v2.py |
| Blue Team | Planned | Planned |
| Multimodal | Planned | Planned |
| Data Poisoning | Planned | Planned |

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

## Framework Stability

| Module | In use by |
|--------|----------|
| `groq_client.py` | red-team, blue-team, owasp-top-10, multimodal |
| `scoring.py` | all spaces |
| `exam_token.py` | red-team, detection-monitoring, exam-admin |
| `exam_session.py` | red-team, detection-monitoring |
| `exam_questions.py` | red-team, detection-monitoring, exam-admin |
| `static/js/exam_mode.js` | all exam-mode spaces |

---

## Open Issues

| Issue | Title | Status |
|-------|-------|--------|
| #27 | Detection & Monitoring lab (Space 6) | Open — deploy pending |
| #28 | exam-admin space | Open — code complete, deploy pending |
| #32 | Instructor preview mode | Open — planned |
| #33 | WCAG 2.1 AA audit + remediation | Open — partial (A3/A6/A7 fixed) |
| #34 | Facilitator guides | Open — planned |
| #35 | Course materials package | Open — planned |
| #36 | Additional assessment types | Open — planned |

---

## Blockers

- Detection & Monitoring deploy: requires `./scripts/deploy.sh detection-monitoring` under `op run`
- exam-admin deploy: requires creating private HF Space `nikobehar/ai-sec-lab-exam-admin` manually, then running deploy
- exam-admin LTI: requires Canvas admin access for one-time tool registration (per deployment_spec.md)

---

## Next Recommended Task

Deploy Detection & Monitoring (Space 6) to HF:
```
op run --env-file=.env.op -- ./scripts/deploy.sh detection-monitoring
```
Then run acceptance checks from `spaces/detection-monitoring/specs/api_spec.md`.

After that: create `nikobehar/ai-sec-lab-exam-admin` as a private HF Space and deploy exam-admin.

---

## Session History

| Date | Work |
|------|------|
| 2026-04-28 | Platform architecture established. owasp-top-10, blue-team, red-team live. |
| 2026-04-29 | Multimodal (Space 4) and data-poisoning (Space 5) specs + implementation. Detection & Monitoring (Space 6) Phase 0 bootstrap. |
| 2026-04-30 | Detection & Monitoring Phase 1+2 complete. Summative assessment system Phases 1–5 complete: exam_token.py, exam_session.py, exam_questions.py, exam_mode.js, Red Team exam routes + datasets, Detection exam routes + datasets, exam-admin space (verify UI + LTI grade passback). |
| 2026-04-30 | Instructor support package: `framework/exam_session.py` enhanced with pause/resume/extend_time/reset_exercise + admin_log (`cc80abd9`). exam-admin upgraded to 4-tab UI (Verify/Batch/Roster/Generate) with accommodation panel + roster view + token generator wizard (`f4e67fcb`). red-team/app.py + detection-monitoring/app.py got 6 admin routes each + _ROSTER_MAP + pause check (`5e257f34`). CSS: admin.css updated with .accom-*, .roster-table, .generate-form, .sr-only, .lab-connect-* (`5e257f34`). Issues #29–#31 implemented. |
