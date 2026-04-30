# Project Status — Detection & Monitoring Lab (Space 6)

Last updated: 2026-04-29

---

## Current Phase: Phase 0 — Bootstrap Complete / Phase 1 Planned

All 4 specs written. CLAUDE.md and this file complete. Ready for Phase 1 implementation.

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
| GitHub milestone issue | Pending (to be filed) |

---

## Phase 1: Core Implementation (Planned)

| File | Status |
|------|--------|
| `detection_data.py` | Not started |
| `app.py` | Not started |
| `waf_parser.py` | Not started (copy from blue-team) |
| `requirements.txt` | Not started |
| `Dockerfile` | Not started |
| `templates/index.html` | Not started |
| `static/css/luminex-tokens.css` | Not started (copy from multimodal) |
| `static/css/luminex-bridge.css` | Not started (copy from blue-team) |
| `static/css/luminex-nav.css` | Not started (copy from blue-team) |
| `static/css/detection.css` | Not started |
| `static/js/app.js` | Not started |
| `static/js/log_viewer.js` | Not started |
| `static/js/anomaly_dashboard.js` | Not started |
| `static/js/output_sanitizer.js` | Not started |

---

## Open Risks

| Risk | Mitigation |
|------|------------|
| D2 sparkline charts require SVG/CSS without external chart library | Keep to simple polyline SVG — 24 points is well within manual rendering scope |
| D3 WAF parser reuse depends on blue-team waf_parser.py staying stable | Pin to current blue-team version; any changes go to blue-team first |
| D2 scoring formula (TP/3 × 100 − FP × 10) can go negative | Spec says min 0 — clamp in backend scoring logic |

---

## Acceptance Check Status (Phase 1, pre-build)

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

---

## Session History

| Date | Work |
|------|------|
| 2026-04-29 | Phase 0 bootstrap: all 4 specs, CLAUDE.md, project-status.md written |
