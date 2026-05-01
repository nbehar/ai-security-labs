# Red Team Workshop — Project Status

*Last updated: 2026-04-29 (bootstrapped — resolves #20; lifted from platform docs/project-status.md)*

------------------------------------------------------------------------

## Current Phase

**Live + maintenance.** Red Team Levels (5 targets) + Jailbreak Lab (15 techniques) are built and verified at `nikobehar/red-team-workshop` (HF Space, CPU free tier). Brand refresh (Luminex Learning nav, digistore pattern) applied 2026-04-29. Pedagogical improvements Phase A+B+C applied 2026-04-29.

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

------------------------------------------------------------------------

## Level Reference

| Level | System | Defense Layers | Secret |
|-------|--------|----------------|--------|
| L1 | HR Portal | None | CRIMSON FALCON |
| L2 | Finance | Basic refusal | SHADOW PROTOCOL |
| L3 | Legal | XML hardening | IRON CASCADE |
| L4 | DevOps | Input Scanner (keyword blocking) + prompt hardening | GHOST MERIDIAN |
| L5 | Executive | Input Scanner (40+ patterns) + prompt hardening + Output Redaction + Guardrail Model | OMEGA THRESHOLD |

------------------------------------------------------------------------

## Jailbreak Lab Categories

| Category | Techniques |
|----------|-----------|
| Direct Override | 3 techniques |
| Encoding | 3 techniques |
| Role-Play | 3 techniques |
| Social Engineering | 3 techniques |
| Advanced | 3 techniques |

------------------------------------------------------------------------

## Open Risks

- None blocking. L1 uses "internal reference notes" framing (not "classified") to avoid LLaMA's built-in safety rejecting an undefended level — this is by design.
- `architecture.md` Brand & Identity section is stale (pre-dates digistore-pattern nav) — tracked in #17.

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

*Full session details in platform `docs/project-status.md` Session History.*
