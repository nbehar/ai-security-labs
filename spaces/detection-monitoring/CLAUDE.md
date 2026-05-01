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
  app.py                    FastAPI routes + dataset serving (Phase 1 — TO BE BUILT)
  detection_data.py         Pre-labeled datasets: D1 logs, D2 time-series, D3 outputs (Phase 1 — TO BE BUILT)
  waf_parser.py             Reused from blue-team (D3 rule evaluation) (Phase 1 — TO BE BUILT)
  Dockerfile                cpu-basic + Python deps, no ML (Phase 1 — TO BE BUILT)
  requirements.txt          fastapi, uvicorn, jinja2, slowapi, pydantic (Phase 1 — TO BE BUILT)
  README.md                 HF Spaces card with frontmatter (Phase 0 ✅)
  CLAUDE.md                 This file (Phase 0 ✅)
  specs/
    overview_spec.md        v1 scope, scenario, audience, success criteria (Phase 0 ✅)
    frontend_spec.md        UI structure, 5 tabs, educational scaffolding (Phase 0 ✅)
    api_spec.md             FastAPI endpoints + Pydantic schemas (Phase 0 ✅)
    deployment_spec.md      Hardware, Dockerfile, env vars (Phase 0 ✅)
  docs/
    project-status.md       Space-level status tracker (Phase 0 ✅)
  static/
    css/
      luminex-tokens.css    Vendored from ~/luminex/brand-system/design-tokens.json (Phase 1)
      luminex-bridge.css    Framework variable remapping to Luminex tokens (Phase 1)
      luminex-nav.css       Master nav stylesheet (Phase 1)
      detection.css         Space-specific styles (Phase 1)
    js/
      app.js                SPA entry: tab routing, Info tab, Leaderboard tab (Phase 1)
      log_viewer.js         D1 Log Analysis: card rendering, classification, WHY (Phase 1)
      anomaly_dashboard.js  D2 Anomaly Detection: charts, sliders, timeline (Phase 1)
      output_sanitizer.js   D3 Output Sanitization: rule editor, results table (Phase 1)
  templates/
    index.html              Jinja2 HTML shell (Phase 1)
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
| Phase 1 | Core implementation: detection_data.py, app.py, waf_parser.py, HTML/CSS/JS | Planned |
| Phase 2 | Pedagogical pass: Knowledge Check, cross-lab nav, WHY card refinement | Planned |
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
