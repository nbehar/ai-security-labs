---
title: AI Security Labs — Exam Admin
emoji: 🔐
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# AI Security Labs — Exam Admin

Instructor verification and grading tool for the AI Security Labs summative assessment system.

**This space is private — instructor use only.**

## What This Does

- Verifies HMAC-signed score receipts downloaded by students from exam-mode lab spaces
- Displays practical scores, MCQ results, and short-answer responses
- Provides a short-answer rubric panel for instructor scoring
- Posts final grades to Canvas/Moodle via LTI 1.3 grade passback
- Supports batch verification for entire course sections

## Required Secrets

| Secret | Purpose |
|--------|----------|
| `EXAM_SECRET` | HMAC key shared with all lab spaces — used to verify receipt authenticity |
| `EXAM_LTI_CLIENT_ID` | Canvas LTI 1.3 client_id (optional — required for Canvas grade passback) |
| `EXAM_LTI_PLATFORM_URL` | Canvas instance URL (optional) |
| `EXAM_LTI_LINEITEM_URL` | Canvas AGS lineitem URL for the active assignment (optional) |
| `EXAM_LTI_PRIVATE_KEY_PEM` | RSA private key for LTI JWT signing (optional) |

See `spaces/exam-admin/specs/deployment_spec.md` for LTI 1.3 one-time setup instructions.

## Part of AI Security Labs

This tool is part of the [AI Security Labs](https://github.com/nbehar/ai-security-labs) platform — 10 interactive workshops for graduate-level AI security training.
