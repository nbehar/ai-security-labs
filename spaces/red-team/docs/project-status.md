# Red Team Workshop — Project Status

*Last updated: 2026-04-30 (Assessment Phase 3 complete: exam_challenges_v1.py + exam_challenges_v2.py + app.py exam mode + slowapi; Assessment Phase 4 wired via framework exam_questions.py + exam_mode.js)*

------------------------------------------------------------------------

## Current Phase

**Live + exam-mode-ready.** Red Team Levels (5 targets) + Jailbreak Lab (15 techniques) are built and verified at `nikobehar/red-team-workshop` (HF Space, CPU free tier). Brand refresh (Luminex Learning nav, digistore pattern) applied 2026-04-29. Pedagogical improvements Phase A+B+C applied 2026-04-29. Exam mode (Phase 3) wired 2026-04-30.

------------------------------------------------------------------------

## v1 Scope

| Decision | Value |
|----------|-------|
| HF Space | `nikobehar/red-team-workshop` (legacy name) |
| Hardware | CPU free tier |
| Model | LLaMA 3.3 70B via Groq API (`llama-3.3-70b-versatile`) |
| Labs | Red Team Levels (5 progressively hardened NexaCore systems) + Jailbreak Lab (15 techniques) |
| Scenario | NexaCore Technologies (fictional) — attacker role |
| Scoring | 100 pts first try, −20 per additional attempt |

------------------------------------------------------------------------

## Implementation Status

| Component | Status |
|-----------|--------|
| `app.py` (FastAPI backend) | ✅ Complete |
| `challenges.py` (5 levels + guardrail evaluation) | ✅ Complete |
| Red Team Levels (L1–L5, progressive defense layers) | ✅ Complete |
| Jailbreak Lab (15 techniques, 5 categories) | ✅ Complete |
| Technique Effectiveness Heatmap (live success rates) | ✅ Complete |
| Defense log (per-attempt, shows which layers fired) | ✅ Complete |
| Guided practice (5 steps) + level briefing cards | ✅ Complete |
| Progress stars + hints after 3 failures | ✅ Complete |
| Leaderboard | ✅ Complete |
| Brand: Luminex Learning nav (digistore pattern) | ✅ Complete (2026-04-29) |
| Pedagogical Phase A: learning objectives + knowledge check + cross-lab nav | ✅ Complete (`b093ddb`) |
| Pedagogical Phase B+C: reflection prompts + platform glossary | ✅ Complete |
| NR-8 CSS fix (hardcoded colors → tokens) | ✅ Complete (PR #24) |
| slowapi rate limiting (10 req/min) | ✅ Complete (`b75f89b`) |
| **Assessment Phase 3: exam mode** | ✅ Complete (`86beaab`, `b75f89b`) |
| **Assessment Phase 4: theory questions (via framework)** | ✅ Complete (`c330df4`) |

------------------------------------------------------------------------

## Level Reference

### Workshop (default)

| Level | System | Defense Layers | Secret |
|-------|--------|----------------|--------|
| L1 | HR Portal | None | CRIMSON FALCON |
| L2 | Finance | Basic refusal | SHADOW PROTOCOL |
| L3 | Legal | XML hardening | IRON CASCADE |
| L4 | DevOps | Input Scanner (keyword blocking) + prompt hardening | GHOST MERIDIAN |
| L5 | Executive | Input Scanner (40+ patterns) + prompt hardening + Output Redaction + Guardrail Model | OMEGA THRESHOLD |

### Exam Section A (exam_v1) — `exam_challenges_v1.py`

| Level | System | Secret |
|-------|--------|--------|
| L1 | Research Computing Portal | VERMILION KESTREL |
| L2 | Procurement Portal | COBALT MERIDIAN |
| L3 | Compliance Portal | SILVER ECLIPSE |
| L4 | SecurityOps Portal | COPPER VANGUARD |
| L5 | Board Secretariat Portal | TITANIUM FORTRESS |

### Exam Section B (exam_v2) — `exam_challenges_v2.py`

| Level | System | Secret |
|-------|--------|--------|
| L1 | Customer Success Portal | AURORA SENTINEL |
| L2 | Supply Chain Portal | QUARTZ NEXUS |
| L3 | Privacy & Legal Portal | ONYX PROTOCOL |
| L4 | InfraOps Portal | JADE CITADEL |
| L5 | Executive Management Portal | SAPPHIRE DIRECTIVE |

------------------------------------------------------------------------

## Exam Mode Architecture

- Token validation: `POST /api/exam/validate` → creates `ExamSession`, returns timer + attempt caps
- Dataset routing: `_get_exam_levels(variant)` dynamically imports `exam_challenges_v1` or `exam_challenges_v2`
- Attempt cap enforcement: `_resolve_exam_session()` checks cap before each `/api/attempt` call
- Theory assessment: `POST /api/exam/theory` + `GET /api/exam/questions` (strips answer keys)
- Signed receipt: `GET /api/exam/receipt` → client signs with WebCrypto HMAC in `exam_mode.js`
- Status: `GET /api/exam/status` → per-exercise attempt counts + elapsed time

------------------------------------------------------------------------

## Jailbreak Lab Categories

| Category | Techniques |
|----------|----------|
| Direct Override | 3 techniques |
| Encoding | 3 techniques |
| Role-Play | 3 techniques |
| Social Engineering | 3 techniques |
| Advanced | 3 techniques |

------------------------------------------------------------------------

## Open Risks

- None blocking. L1 uses "internal reference notes" framing (not "classified") to avoid LLaMA's built-in safety rejecting an undefended level — this is by design.
- `architecture.md` Brand & Identity section is stale (pre-dates digistore-pattern nav) — tracked in #17.
- Exam mode requires `exam_token.py` + `exam_session.py` from `framework/` to be present (copied by `deploy.sh`). If deploying manually, copy these before pushing to HF.

------------------------------------------------------------------------

## Session History

| Date | Work | Key Commits |
|------|------|-------------|
| 2026-04-09 | Built Red Team Levels L1–L5 + Jailbreak Lab (15 techniques) | — |
| 2026-04-09 | Fixed L1 (model refused "classified" framing), fixed L4 (blanket refusal → protect codename only) | — |
| 2026-04-09 | Guided practice, level briefing cards, progress stars, hints | `39fe586`, `cf87474`, `2994d90` |
| 2026-04-28 | Added L5 Guardrail Evaluation defense layer (issue #16) | `guardrail_evaluate()` in challenges.py |
| 2026-04-29 | Brand refresh — Luminex Learning nav (digistore pattern) | `7970f74`, `83b500a` |
| 2026-04-29 | Pedagogical improvements Phase A+B+C | `b093ddb` |
| 2026-04-29 | NR-8 CSS fix: hardcoded hover colors → token vars | PR #24 |
| 2026-04-30 | Assessment Phase 3: exam_challenges_v1.py (Section A, 5 levels), exam_challenges_v2.py (Section B, 5 levels), app.py exam mode (4 exam routes + `exam_token` on `/api/attempt` + `_resolve_exam_session` + `_get_exam_levels`), slowapi added | `86beaab`, `b75f89b` |
| 2026-04-30 | Assessment Phase 4: framework/exam_questions.py (10 MCQ + 3 SA for red-team + detection-monitoring, Bloom's 4–6), framework/static/js/exam_mode.js (timer banner, theory form, WebCrypto HMAC receipt signing) | `c330df4`, `86beaab` |

*Full session details in platform `docs/project-status.md` Session History.*
