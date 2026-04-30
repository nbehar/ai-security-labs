# Project Status — Detection & Monitoring Lab (Space 6)

Last updated: 2026-04-30

---

## Current Phase: Phase 1 — Core Implementation Complete

All 16 Phase 1 source files written and pushed to GitHub (commits `cf4042b`, `a41a1fa`). Ready for Phase 2 (pedagogical pass) or direct deploy.

---

## v1 Scope

| Item | Value |
|------|-------|
| HF Space | `nikobehar/ai-sec-lab6-detection` |
| Hardware | cpu-basic |
| Model | None (model-free v1) |
| API key required | No |
| D1 entries | 20 (8 attacks, 12 legit) |
| D2 windows | 24 (3 attack, 21 normal) |
| D3 outputs | 15 (8 dangerous, 7 legit) |
| Max score | 300 pts (D1: 100, D2: 100, D3: 100) |

---

## Phase 0: Bootstrap

| Artifact | Status |
|----------|--------|
| `specs/overview_spec.md` | ✅ Written 2026-04-29 |
| `specs/frontend_spec.md` | ✅ Written 2026-04-29 |
| `specs/api_spec.md` | ✅ Written 2026-04-29 |
| `specs/deployment_spec.md` | ✅ Written 2026-04-29 |
| `CLAUDE.md` | ✅ Written 2026-04-29 |
| `docs/project-status.md` | ✅ This file |
| GitHub milestone issue | ✅ #27 filed 2026-04-29 |

---

## Phase 1: Core Implementation ✅ Complete

| File | Status |
|------|--------|
| `detection_data.py` | ✅ Written 2026-04-30 — 20 logs (8A/12L), 24 windows (3A), 15 outputs (8D/7L) |
| `app.py` | ✅ Written 2026-04-30 — 9 endpoints, F1/D2/D3 scoring, leaderboard |
| `waf_parser.py` | ✅ Written 2026-04-30 — BLOCK/ALLOW DSL, 30-rule limit |
| `requirements.txt` | ✅ Written 2026-04-30 |
| `Dockerfile` | ✅ Written 2026-04-30 — python:3.11-slim, no ML deps |
| `templates/index.html` | ✅ Written 2026-04-30 — Luminex nav, cold-start banner |
| `static/css/luminex-tokens.css` | ✅ Written 2026-04-30 |
| `static/css/luminex-bridge.css` | ✅ Written 2026-04-30 |
| `static/css/luminex-nav.css` | ✅ Written 2026-04-30 |
| `static/css/detection.css` | ✅ Written 2026-04-30 — NR-8 compliant, all D1/D2/D3 components |
| `static/js/app.js` | ✅ Written 2026-04-30 — 5 tabs, Info w/ KC + objectives + cross-lab nav |
| `static/js/log_viewer.js` | ✅ Written 2026-04-30 — pagination, immediate WHY feedback |
| `static/js/anomaly_dashboard.js` | ✅ Written 2026-04-30 — SVG sparklines, threshold configurator |
| `static/js/output_sanitizer.js` | ✅ Written 2026-04-30 — rule editor, F1 scoring, beat-baseline indicator |

---

## Open Risks

| Risk | Mitigation |
|------|----------|
| D2 sparkline charts require SVG/CSS without external chart library | Keep to simple polyline SVG — 24 points is well within manual rendering scope |
| D3 WAF parser reuse depends on blue-team waf_parser.py staying stable | Pin to current blue-team version; any changes go to blue-team first |
| D2 scoring formula (TP/3 × 100 − FP × 10) can go negative | Spec says min 0 — clamp in backend scoring logic |

---

## Acceptance Check Status (Phase 1 — pending deploy)

From `specs/api_spec.md`:
- [ ] `GET /health` returns 200 with `d1_log_count: 20, d2_window_count: 24, d3_output_count: 15`
- [ ] `POST /api/logs/classify` with all 20 correct answers returns `score: 100, f1: 1.0`
- [ ] `POST /api/logs/classify` with 19 entries returns 422
- [ ] `POST /api/anomaly/evaluate` with `response_length.high: 1` returns `tp: 3, fp: 21`
- [ ] `POST /api/outputs/evaluate` with `BLOCK .*` returns `tp: 8, fp: 7`
- [ ] `POST /api/outputs/evaluate` with invalid regex `BLOCK [` returns 422
- [ ] All POST endpoints return 429 after 10 req/min

From `specs/frontend_spec.md`:
- [ ] All 5 tabs render without JS errors
- [ ] D1 WHY card appears immediately after each classification
- [ ] D2 sparkline charts render for all 4 metrics with baseline band
- [ ] D3 `BLOCK \b\d{3}-\d{2}-\d{4}\b` catches D3.B1 without flagging legit outputs
- [ ] Knowledge Check answers reveal on click

**Local sanity checks (pre-deploy, no FastAPI):**
- ✅ D1=20 (8 attack, 12 legit) verified
- ✅ D2=24 (3 attack hours: 9/14/19) verified
- ✅ D3=15 (8 dangerous, 7 legit) verified
- ✅ `BLOCK .*` → tp=8, fp=7 (F1≈0.533) verified
- ✅ SSN rule `BLOCK \b\d{3}-\d{2}-\d{4}\b` → 1 hit (D3.01) verified
- ✅ `waf_parser.py` + `detection_data.py` import clean

---

## Session History

| Date | Work |
|------|------|
| 2026-04-29 | Phase 0 bootstrap: all 4 specs, CLAUDE.md, project-status.md written |
| 2026-04-30 | Phase 1 complete: all 16 source files written + pushed (commits `cf4042b`, `a41a1fa`, refs #27). D1=20, D2=24, D3=15. NR-8 compliant. Knowledge Check + learning objectives + cross-lab nav in Info tab. |
