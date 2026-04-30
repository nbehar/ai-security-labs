# Project Status — exam-admin Space

Last updated: 2026-04-30

---

## Current Phase: Phase 0 Complete — Phase 1 Planned

All Phase 0 bootstrap artifacts written. Phase 1 implementation (app.py, lti.py, Dockerfile, requirements.txt) is next.

---

## v1 Scope

| Item | Value |
|------|-------|
| HF Space | `nikobehar/ai-sec-lab-exam-admin` |
| Visibility | Private (instructor-only) |
| Hardware | cpu-basic |
| Model | None (model-free) |
| API key required | No |
| EXAM_SECRET required | Yes (receipt HMAC verification) |
| LTI optional | Yes (EXAM_LTI_* secrets for Canvas grade passback) |

---

## Phase 0: Bootstrap

| Artifact | Status |
|----------|--------|
| `specs/overview_spec.md` | ✅ Written 2026-04-30 |
| `specs/frontend_spec.md` | ✅ Written 2026-04-30 |
| `specs/api_spec.md` | ✅ Written 2026-04-30 |
| `specs/deployment_spec.md` | ✅ Written 2026-04-30 |
| `CLAUDE.md` | ✅ Written 2026-04-30 |
| `docs/project-status.md` | ✅ This file |
| `README.md` | ✅ Written 2026-04-30 |
| GitHub issue | ✅ #28 filed 2026-04-30 |

---

## Phase 1: Core Backend — Planned

| File | Status |
|------|--------|
| `app.py` | Planned — /api/verify, /api/batch-verify, /api/rubric/{lab}, /api/lti/*, /health |
| `lti.py` | Planned — pylti1p3 JWKS + AGS passback |
| `Dockerfile` | Planned — python:3.11-slim, no ML |
| `requirements.txt` | Planned |

---

## Phase 2: Frontend — Planned

| File | Status |
|------|--------|
| `templates/index.html` | Planned — Verify + Batch views |
| `static/css/admin.css` | Planned — NR-8 compliant |
| `static/css/luminex-tokens.css` | Planned — vendored |
| `static/css/luminex-bridge.css` | Planned — vendored |
| `static/css/luminex-nav.css` | Planned — vendored |
| `static/js/admin.js` | Planned — verify, batch, SA scoring, LTI button, CSV export |

---

## Open Risks

| Risk | Mitigation |
|------|------------|
| pylti1p3 LTI 1.3 setup requires Canvas admin access | Document one-time setup steps in deployment_spec.md |
| EXAM_LTI_LINEITEM_URL is per-assignment, not per-space | Instructor sets it as a secret before each exam period |
| In-memory nonce store lost on HF Space restart | Acceptable at course volume; LTI OIDC flow is fast |
| HF Space private visibility must be set manually | Document in deployment_spec.md |

---

## Acceptance Check Status (pending Phase 1)

From `specs/api_spec.md`:
- [ ] `GET /health` returns `exam_secret_configured: true` when env var is set
- [ ] `POST /api/verify` with valid receipt returns `hmac_valid: true`
- [ ] `POST /api/verify` with tampered receipt returns `hmac_valid: false`
- [ ] `GET /api/rubric/red-team` returns 3 short-answer entries
- [ ] `GET /api/lti/jwks` returns `{"keys": []}` when LTI not configured

From `specs/frontend_spec.md`:
- [ ] Verify view renders without JS errors
- [ ] Drag-drop zone triggers verification without page reload
- [ ] HMAC badge is green for valid, red for invalid
- [ ] SA scoring panel updates subtotal in real time
- [ ] Export CSV Row downloads a valid CSV

---

## Session History

| Date | Work |
|------|------|
| 2026-04-30 | Phase 0 bootstrap: all 4 specs, CLAUDE.md, project-status.md, README.md written. GitHub issue #28 filed. |
