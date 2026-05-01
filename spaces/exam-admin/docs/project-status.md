# Project Status — exam-admin Space

Last updated: 2026-04-30

---

## Current Phase: Phase 2 Complete — Phase 3 (Deploy) Pending

All Phase 0 bootstrap artifacts + Phase 1 backend + Phase 2 frontend written and pushed.

---

## v1 Scope

| Item | Value |
|------|-------|
| HF Space | `nikobehar/ai-sec-lab-exam-admin` |
| Visibility | Private (instructor-only) |
| Hardware | cpu-basic |
| Model | None (model-free) |
| EXAM_SECRET required | Yes |
| LTI optional | Yes (EXAM_LTI_* secrets) |

---

## Phase 0: Bootstrap

| Artifact | Status |
|----------|--------|
| `specs/overview_spec.md` | ✅ Written 2026-04-30 |
| `specs/frontend_spec.md` | ✅ Written 2026-04-30 |
| `specs/api_spec.md` | ✅ Written 2026-04-30 |
| `specs/deployment_spec.md` | ✅ Written 2026-04-30 |
| `CLAUDE.md` | ✅ Written 2026-04-30 |
| `README.md` | ✅ Written 2026-04-30 |
| GitHub issue | ✅ #28 filed 2026-04-30 |

---

## Phase 1: Core Backend ✅ Complete

| File | Status |
|------|--------|
| `app.py` | ✅ Written 2026-04-30 — verify, batch-verify, rubric, lti, health |
| `lti.py` | ✅ Written 2026-04-30 — JWKS + AGS passback (cryptography + httpx, no pylti1p3) |
| `Dockerfile` | ✅ Written 2026-04-30 |
| `requirements.txt` | ✅ Written 2026-04-30 |

---

## Phase 2: Frontend ✅ Complete

| File | Status |
|------|--------|
| `templates/index.html` | ✅ Written 2026-04-30 — Verify + Batch views |
| `static/css/admin.css` | ✅ Written 2026-04-30 — NR-8 compliant |
| `static/css/luminex-tokens.css` | ✅ Written 2026-04-30 — vendored |
| `static/css/luminex-bridge.css` | ✅ Written 2026-04-30 — vendored |
| `static/css/luminex-nav.css` | ✅ Written 2026-04-30 — vendored |
| `static/js/admin.js` | ✅ Written 2026-04-30 — verify, batch, SA panel, LTI button, CSV export |
| `static/owl.svg` | ✅ Written 2026-04-30 — geometric placeholder |

---

## Phase 3: Deploy — Pending

**Blocker:** HF Space `nikobehar/ai-sec-lab-exam-admin` must be created manually (private space).
**Action required:**
1. Create private HF Space `nikobehar/ai-sec-lab-exam-admin` (Docker, cpu-basic, private)
2. Add HF remote to `spaces/exam-admin/` git repo
3. Set `EXAM_SECRET` as HF Space secret
4. Run `./scripts/deploy.sh exam-admin` (under `op run`)
5. Verify `GET /health` returns 200

---

## Acceptance Check Status (pending deploy)

From `specs/api_spec.md`:
- [ ] `GET /health` returns `exam_secret_configured: true` when env var is set
- [ ] `POST /api/verify` with valid receipt returns `hmac_valid: true`
- [ ] `POST /api/verify` with tampered receipt returns `hmac_valid: false`
- [ ] `GET /api/rubric/red-team` returns 3 short-answer entries
- [ ] `GET /api/lti/jwks` returns `{"keys": []}` when LTI not configured
- [ ] POST endpoints return 429 after 10 req/min

From `specs/frontend_spec.md`:
- [ ] Verify view renders without JS errors
- [ ] Drag-drop triggers verification without page reload
- [ ] HMAC badge is green for valid, red for invalid
- [ ] SA scoring panel updates subtotal in real time
- [ ] Export CSV Row downloads a valid CSV

---

## Session History

| Date | Work |
|------|------|
| 2026-04-30 | Phase 0 bootstrap: all 4 specs, CLAUDE.md, project-status.md, README.md written. GitHub issue #28 filed. |
| 2026-04-30 | Phase 1+2 complete: app.py, lti.py, Dockerfile, requirements.txt, index.html, admin.css, admin.js, Luminex CSS, owl.svg. LTI implemented via cryptography+httpx (no pylti1p3). |
