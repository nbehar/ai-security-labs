# CLAUDE.md — exam-admin Space

This file is the space-level governance for `spaces/exam-admin/`. The platform-level `/CLAUDE.md` at the repo root applies in addition; this file scopes platform rules to this space and adds anything specific to exam-admin work.

------------------------------------------------------------------------

# Project Purpose

The exam-admin space is the **instructor verification and grading tool** for the AI Security Labs summative assessment system. It is the counterpart to exam mode in the lab spaces: students download signed receipts from labs, instructors upload them here for HMAC verification, short-answer grading, and Canvas LTI 1.3 grade passback.

**v1 scope:** receipt verification, rubric display, short-answer scoring panel, single and batch workflows, LTI 1.3 grade passback. Model-free.

This space is **private** (instructor-only). It must never be made public.

The repository — not conversation history — is the system of record.

------------------------------------------------------------------------

# Reading Order (Space-Level)

When working in this space, Claude MUST read in this order:

1. Platform `/CLAUDE.md`
2. Platform `/docs/project-status.md`
3. This file (`spaces/exam-admin/CLAUDE.md`)
4. `spaces/exam-admin/specs/overview_spec.md`
5. `spaces/exam-admin/specs/frontend_spec.md`
6. `spaces/exam-admin/specs/api_spec.md`
7. `spaces/exam-admin/specs/deployment_spec.md`
8. `spaces/exam-admin/docs/project-status.md`

Plus relevant memory entries:
- `~/.claude/projects/-Users-niko-ai-security-labs/memory/brand-architecture.md` — all spaces in this monorepo are sections within AI Security Labs (one Luminex product, AISL violet)

------------------------------------------------------------------------

# Repository Structure (this space)

```
spaces/exam-admin/
  app.py                    FastAPI routes: /api/verify, /api/batch-verify,
                             /api/rubric/{lab}, /api/lti/*, /health
  lti.py                    pylti1p3 wiring: JWKS, JWT signing, AGS passback
  Dockerfile                python:3.11-slim, no ML deps
  requirements.txt          fastapi, uvicorn, jinja2, pydantic, slowapi,
                             pylti1p3, httpx, cryptography
  README.md                 HF Spaces card with frontmatter
  CLAUDE.md                 This file
  specs/
    overview_spec.md        Purpose, audience, success criteria
    frontend_spec.md        Verify view, Batch view, SA scoring panel
    api_spec.md             FastAPI endpoints + Pydantic schemas
    deployment_spec.md      Dockerfile, env vars, LTI setup guide
  docs/
    project-status.md       Space-level status tracker
  static/
    css/
      luminex-tokens.css    Vendored design tokens
      luminex-bridge.css    Framework variable remapping
      luminex-nav.css       Master nav stylesheet
      admin.css             Space-specific styles
    js/
      admin.js              Verify view, Batch view, SA scoring panel,
                             LTI grade button, CSV export
  templates/
    index.html              Jinja2 HTML shell
```

------------------------------------------------------------------------

# Architecture

## Stack

- **Backend:** FastAPI + Uvicorn (Python 3.11+), port 7860
- **Frontend:** Vanilla ES6+, no framework, no build step
- **Model:** None (model-free)
- **LTI:** `pylti1p3` for LTI 1.3 OIDC / AGS grade passback
- **Deploy:** Docker on HuggingFace Space `nikobehar/ai-sec-lab-exam-admin` (private), cpu-basic
- **Rate limiting:** `slowapi` — 10 req/min per IP on POST endpoints

## Key Design: No EXAM_SECRET in Responses

`EXAM_SECRET` is used only inside `verify_receipt()` (from `exam_token.py`). It MUST NEVER appear in:
- Any HTTP response body
- Any log line at INFO or below
- Any JavaScript variable or console output
- Any HTML template

Log it only at DEBUG level if absolutely necessary, with a warning comment.

## Framework File Reuse

`exam_token.py` (copied from `framework/` at deploy time) provides `verify_receipt()` — the authoritative HMAC verifier. `exam_questions.py` provides `QUESTION_BANKS` for rubric data.

Do not duplicate HMAC logic in `app.py`. Always call `verify_receipt()`.

## LTI State

All LTI OIDC nonce/state is in-memory (`dict` + `threading.Lock`). No SQLite. Acceptable at course volume (< 30 concurrent instructor sessions on a single HF Space instance).

------------------------------------------------------------------------

# Phase Plan

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 0 | Specs + CLAUDE.md + project-status.md + README | ✅ Complete |
| Phase 1 | Core backend: app.py, lti.py, Dockerfile, requirements.txt | Planned |
| Phase 2 | Frontend: index.html, admin.js, CSS (Verify + Batch + SA panel) | Planned |
| Phase 3 | Deploy to private HF Space + acceptance check verification | Planned |

------------------------------------------------------------------------

# Security Posture

## What IS Sensitive

- `EXAM_SECRET` — the receipt signing key. Never expose it.
- `EXAM_LTI_PRIVATE_KEY_PEM` — RSA private key for LTI JWT signing. Never expose it.
- Student `student_id` values — treat as PII (FERPA). Never log at INFO+.

## What is NOT Sensitive

- Receipt JSON itself — the student already has a copy. It can be displayed.
- Rubric criteria — published and visible to students (they are graded against the rubric).
- `hmac_valid: true/false` — the verification result is the purpose of this tool.

------------------------------------------------------------------------

# Definition of Done (Space-Level)

Work completes ONLY when:

- All Acceptance Checks in all 4 specs pass
- This `docs/project-status.md` updated
- Platform `docs/project-status.md` updated
- GitHub issue #28 closed with reference commit
- HF Space `nikobehar/ai-sec-lab-exam-admin` shows `/health` 200
- `EXAM_SECRET` is confirmed to never appear in any HTTP response
- No hardcoded color literals (NR-8 compliant from day 1)
