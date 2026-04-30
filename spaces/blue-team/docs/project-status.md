# Blue Team Workshop — Project Status

*Last updated: 2026-04-29 (bootstrapped — resolves #20; lifted from platform docs/project-status.md)*

------------------------------------------------------------------------

## Current Phase

**Live + maintenance.** All 4 challenges are built and verified at `nikobehar/blue-team-workshop` (HF Space, CPU free tier). Brand refresh (Luminex Learning nav, digistore pattern) applied 2026-04-29. Pedagogical improvements Phase A+B+C applied 2026-04-29 (learning objectives, knowledge checks, cross-lab nav, reflection prompts, WAF regex primer).

------------------------------------------------------------------------

## v1 Scope

| Decision | Value |
|----------|-------|
| HF Space | `nikobehar/blue-team-workshop` (legacy name) |
| Hardware | CPU free tier |
| Model | LLaMA 3.3 70B via Groq API (`llama-3.3-70b-versatile`) |
| Challenges | 4: Prompt Hardening + WAF Rules + Pipeline Builder + Behavioral Testing |
| Scenario | NexaCore Technologies (fictional) — defender role |
| Scoring | Per-challenge + aggregate leaderboard |

------------------------------------------------------------------------

## Implementation Status

| Component | Status |
|-----------|--------|
| `app.py` (FastAPI backend, all 4 challenges) | ✅ Complete |
| `challenges.py` (challenge definitions) | ✅ Complete |
| `waf_parser.py` (BLOCK/ALLOW DSL + regex) | ✅ Complete |
| Prompt Hardening (5 levels, 15 attacks, WHY explanations) | ✅ Complete |
| WAF Rules (F1 scoring, PG2 baseline comparison, confusion matrix) | ✅ Complete |
| Defense Pipeline Builder (5 stages, coverage+efficiency scoring) | ✅ Complete |
| Model Behavioral Testing (12 hidden vulns, 6 categories) | ✅ Complete |
| Guided practice (5 steps) + level briefing cards | ✅ Complete |
| Progress stars + WHY explanations + hints | ✅ Complete |
| Leaderboard (aggregates all 4 challenges) | ✅ Complete |
| Brand: Luminex Learning nav (digistore pattern) | ✅ Complete (2026-04-29) |
| Pedagogical Phase A: learning objectives + knowledge check + cross-lab nav | ✅ Complete (`b093ddb`) |
| Pedagogical Phase B: WAF regex primer + cold-start indicator | ✅ Complete |
| Pedagogical Phase C: reflection prompts + platform glossary | ✅ Complete |
| NR-8 CSS fix (hardcoded colors → tokens) | ✅ Complete (PR #24) |

------------------------------------------------------------------------

## Verified Results

| Challenge | Verified Score / Result |
|-----------|------------------------|
| Prompt Hardening L1 | 130 pts, 0 false positives |
| Prompt Hardening L2 | 130 pts, 0 false positives |
| Prompt Hardening L3 | 105 pts, 0 false positives |
| Prompt Hardening L4 | 90 pts, 0 false positives |
| Prompt Hardening L5 | 110 pts, 0 false positives |
| WAF Rules (9-rule set) | 50% F1, 100% precision, 33% recall |
| Pipeline Builder — Kitchen Sink | 84/100, 14/15 blocked, 93% coverage |
| Pipeline Builder — Fast & Cheap | 81/100 |
| Pipeline Builder — None | 18/100 |
| Behavioral Testing | PII Leakage V5 triggered on first query |

------------------------------------------------------------------------

## Open Risks

- None blocking. The misinformation probe is not caught by any pipeline tool — this is intentional (it is the educational point: behavioral testing surfaces what automated pipelines miss).
- `architecture.md` Brand & Identity section is stale (pre-dates digistore-pattern nav) — tracked in #17.

------------------------------------------------------------------------

## Session History

| Date | Work | Key Commits |
|------|------|-------------|
| 2026-04-09 | Built Prompt Hardening (5 levels, 15 attacks, WHY) | `e7dfece` |
| 2026-04-09 | Built WAF Rules (DSL parser, F1 scoring, PG2 comparison) | `dadc6b7` |
| 2026-04-09 | Built Defense Pipeline Builder + Model Behavioral Testing | `9978006` |
| 2026-04-09 | Guided practice, WHY explanations, progress stars, hints | `39fe586`, `7d157bb`, `2994d90` |
| 2026-04-28 | Red Team L5 guardrail fix (platform-wide) | see platform docs |
| 2026-04-29 | Brand refresh — Luminex Learning nav (digistore pattern) | `7970f74`, `83b500a` |
| 2026-04-29 | Pedagogical improvements Phase A+B+C | `b093ddb` |
| 2026-04-29 | NR-8 CSS fix: hardcoded hover colors → token vars | PR #24 |

*Full session details in platform `docs/project-status.md` Session History.*
