# CLAUDE.md — Detection & Monitoring Lab

This file is the space-level governance for `spaces/detection-monitoring/`. The platform-level `/CLAUDE.md` at the repo root applies in addition; this file scopes platform rules to this space and adds anything specific to detection-monitoring work.

------------------------------------------------------------------------

# Project Purpose

The Detection & Monitoring Lab is the AI Security Labs platform's workshop for **detecting AI attacks in production telemetry**. Participants review realistic NexaCore log data, configure behavioral alerting thresholds, and write output sanitization rules — the three main detection surfaces for deployed LLM systems.

**v1 scope:** 3 labs (D1 Log Analysis, D2 Anomaly Detection, D3 Output Sanitization) anchored in the **NexaCore AI Operations Center (AIOC)** scenario. Fully model-free: all datasets are pre-labeled and served from `detection_data.py`. No Groq API key required.

The repository — not conversation history — is the system of record.

------------------------------------------------------------------------

# Reading Order (Space-Level)

When working in this space, Claude MUST read in this order:

1. Platform `/CLAUDE.md`
2. Platform `/docs/project-status.md`
3. This file (`spaces/detection-monitoring/CLAUDE.md`)
4. `spaces/detection-monitoring/specs/overview_spec.md`
5. `spaces/detection-monitoring/specs/frontend_spec.md`
6. `spaces/detection-monitoring/specs/api_spec.md`
7. `spaces/detection-monitoring/specs/deployment_spec.md`
8. `spaces/detection-monitoring/docs/project-status.md`

Plus relevant memory entries:
- `~/.claude/projects/-Users-niko-ai-security-labs/memory/brand-architecture.md` — all spaces in this monorepo are sections within AI Security Labs (one Luminex product, AISL violet)

------------------------------------------------------------------------

# Repository Structure (this space)

```
spaces/detection-monitoring/
  app.py                    FastAPI routes + dataset serving
  detection_data.py         Pre-labeled datasets: D1 logs, D2 time-series, D3 outputs
  exam_data_v1.py           Section A exam dataset (IT/Procurement/Compliance)
  exam_data_v2.py           Section B exam dataset (Executive/Engineering/Sales)
  waf_parser.py             Reused from blue-team (D3 rule evaluation)
  exam_token.py             Copied from framework at deploy time
  exam_session.py           Copied from framework at deploy time
  Dockerfile                cpu-basic + Python deps, no ML
  requirements.txt          fastapi, uvicorn, jinja2, slowapi, pydantic
  README.md                 HF Spaces card with frontmatter
  CLAUDE.md                 This file
  specs/
    overview_spec.md
    frontend_spec.md
    api_spec.md
    deployment_spec.md
  docs/
    project-status.md
  static/
    css/
      luminex-tokens.css
      luminex-bridge.css
      luminex-nav.css
      detection.css
    js/
      app.js
      log_viewer.js
      anomaly_dashboard.js
      output_sanitizer.js
  templates/
    index.html
```

------------------------------------------------------------------------

# Architecture

## Stack

- **Backend:** FastAPI + Uvicorn (Python 3.11+), port 7860
- **Frontend:** Vanilla ES6+, no framework, no build step
- **Model:** None (v1 is fully model-free — all datasets are pre-labeled)
- **Deploy:** Docker on HuggingFace Space `nikobehar/ai-sec-lab6-detection`, cpu-basic
- **Rate limiting:** `slowapi` — 10 req/min per IP on POST endpoints

## Key Design Decision: Model-Free v1

Unlike multimodal (HF Inference Providers) and data-poisoning (Groq), Detection & Monitoring v1 serves pre-labeled datasets. This makes the space:
- Fast: no model cold-start, no inference latency
- Reliable: deterministic dataset means reproducible scores for workshop use
- Pedagogically appropriate: SOC detection rule development against known patterns mirrors real-world practice

No `GROQ_API_KEY` or `HF_TOKEN` required for v1.

## D3 DSL Reuse

The Output Sanitization lab (D3) reuses the `BLOCK regex` DSL from the Blue Team WAF Rules challenge. `waf_parser.py` is copied from `spaces/blue-team/` at deploy time (via `deploy.sh`). Any changes to the DSL must be applied to the blue-team source first, then redeployed here.

------------------------------------------------------------------------

# Phase Plan

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 0 | Specs + CLAUDE.md + project-status.md | ✅ Complete |
| Phase 1 | Core implementation: detection_data.py, app.py, waf_parser.py, HTML/CSS/JS | ✅ Complete |
| Phase 2 | Exam mode: exam_data_v1.py, exam_data_v2.py, 4 exam routes in app.py | ✅ Complete |
| Phase 3 | Deploy to HF Space + acceptance check verification | Planned |

------------------------------------------------------------------------

# Dataset Specifications

## D1: Log Analysis (20 entries)

8 attack entries (D1.A1–D1.A8): Prompt Injection, Credential Fishing, System Prompt Leak, Jailbreak, PII Exfiltration, Data Exfiltration, Denial of Service, Role Confusion.
12 legitimate entries: Routine HR, Finance, and Legal queries.

Scoring: F1 × 100 (max 100 pts). False positives reduce score via precision drop.

## D2: Anomaly Detection (24 hourly windows)

4 metrics: response_length, refusal_rate, query_rate, confidence.
3 attack windows (W1 Prompt flooding, W2 Data exfiltration, W3 Jailbreak sequence).
21 normal windows with natural variance.

Scoring: (TP_count / 3) × 100 − (FP_count × 10). Max 100, min 0.

## D3: Output Sanitization (15 outputs)

8 dangerous outputs (D3.B1–D3.B8): PII disclosure, credential in output, injected instruction, internal URL/path, canary phrase, code injection, exfil channel, hallucinated credential.
7 legitimate outputs: Normal HR/Finance/Legal responses.

Scoring: F1 × 100 (max 100 pts).

------------------------------------------------------------------------

# Security Posture

These datasets are **intentionally designed** to represent attack content for educational purposes. All NexaCore data is fictional. No real credentials, no real people, no real SSNs.

The `BLOCK \b\d{3}-\d{2}-\d{4}\b` SSN example in specs is a regex pattern, not a real SSN.

------------------------------------------------------------------------

# Definition of Done (Space-Level)

Work completes ONLY when:

- All Acceptance Checks in all 4 specs pass
- This `docs/project-status.md` updated
- Platform `docs/project-status.md` updated
- GitHub milestone issue closed with reference commit
- HF Space `nikobehar/ai-sec-lab6-detection` shows `/health` 200
- No hardcoded color literals (NR-8 compliant from day 1)
