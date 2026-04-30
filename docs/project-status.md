# Project Status — AI Security Labs Platform

*Last updated: 2026-04-30 (Assessment Phases 3+4 complete: Red Team exam mode + theory question bank + exam_mode.js. Commits `86beaab`, `b75f89b`, `c330df4`. refs #27)*

---------------------------------------------------------------------

## Platform Overview

Interactive AI security training platform by Prof. Nikolas Behar. 3 workshops live, 7 planned. Shared framework with one-command deploys.

**Monorepo:** https://github.com/nbehar/ai-security-labs

---------------------------------------------------------------------

## Live Products

| # | Space | Status | Content | Hardware |
|---|-------|--------|---------|----------|
| 1 | `nikobehar/llm-top-10` | Running, private | OWASP 3-part workshop (25 attacks, 5 defenses, 3 pills) | CPU |
| 2 | `nikobehar/blue-team-workshop` | Running, private | Prompt Hardening (5 levels, scoring, WHY explanations, leaderboard) | CPU |
| 3 | `nikobehar/red-team-workshop` | Running, private | Red Team Levels (5 targets) + Jailbreak Lab (15 techniques, leaderboard) + Exam Mode | CPU |

### OWASP Top 10 Workshop (Space 1)
- **3 workshop pills:** LLM Top 10 (10 attacks) + MCP Top 10 (9 attacks) + Agentic AI (6 attacks)
- **5 defense tools:** Meta Prompt Guard 2, LLM Guard Output/Context, System Prompt Hardening, Guardrail Model
- **Features:** Info tab with NexaCore scenario + infra diagram, slide deck (4 per attack, OWASP cheat sheet content), defense-specific slides, SSE scorecard streaming, EN/ES translations, difficulty badges, collapsible slides, detection method badges
- **All 25 attacks verified** against LLaMA 3.3 70B (25/25 succeed undefended)
- **Defense matrix verified** for all 5 tools across all 25 attacks

### Blue Team Workshop (Space 2)
- **4 of 4 challenges built:**
  1. **Prompt Hardening** — 5 progressive levels (3→15 attacks), 15 attacks with WHY explanations, scoring + leaderboard
  2. **WAF Rules** — Write regex/pattern rules in a DSL, scored by F1 (precision × recall), compared to Prompt Guard 2 baseline (70% F1)
  3. **Defense Pipeline Builder** — Visual pipeline with 5 toggleable defense stages, presets (None/Fast & Cheap/Kitchen Sink), coverage+efficiency scoring (0-100), per-attack results showing which stage caught each attack. No API calls — uses pre-computed defense effectiveness matrix. Kitchen Sink: 14/15 blocked, score 84
  4. **Model Behavioral Testing** — 12 hidden vulnerabilities across 6 categories (Bias, Toxicity, PII Leakage, Instruction Following, Refusal Bypass, Factual Accuracy), participants write test prompts against subtly flawed system, discovery + efficiency scoring (max 160). Uses Groq API
- **20 legitimate queries** for false positive checking
- **Features:** Guided practice (5 steps), level briefing cards, progress stars, WHY explanations, hints, leaderboard (aggregates all 4 challenges), 6 tabs (Info/Prompt Hardening/WAF Rules/Pipeline Builder/Behavioral Testing/Leaderboard)

### Red Team Workshop (Space 3)
- **Red Team Levels:** 5 progressively hardened NexaCore systems
  - L1: HR Portal — no defenses (secret: CRIMSON FALCON) ✅ extractable with simple ask
  - L2: Finance — basic refusal (secret: SHADOW PROTOCOL) ✅ extractable with authority claim
  - L3: Legal — XML hardening (secret: IRON CASCADE) ✅ extractable with translation
  - L4: DevOps — **Input Scanner** + prompt hardening (secret: GHOST MERIDIAN)
  - L5: Executive — **Input Scanner** (40+ patterns) + prompt hardening + **Output Redaction** + **Guardrail Model** (secret: OMEGA THRESHOLD)
- **Jailbreak Lab:** 15 pre-loaded techniques across 5 categories
- **Exam Mode** (Phase 3, 2026-04-30): two parallel exam datasets (v1: Research/Procurement/Compliance/SecurityOps/BoardSecretariat; v2: CustomerSuccess/SupplyChain/Privacy&Legal/InfraOps/ExecutiveManagement). 4 exam routes wired. slowapi rate limiting added.

---------------------------------------------------------------------

## Summative Assessment System

### Assessment Architecture (Two-Tier)

**Tier 1 — Practical Exam** (machine-scored)
- Same lab UIs switched to Exam Mode via URL token (`?exam_token=TOKEN`)
- Alternate dataset: prevents workshop familiarity from transferring to exam scores
- Time-limited countdown + attempt caps per exercise
- Signed score artifact download (WebCrypto HMAC, client-side)

**Tier 2 — Theory Assessment** (partially instructor-graded)
- 10 MCQ (Bloom's 4–6, machine-scored) + 3 short answers (Bloom's 5–6, instructor-graded with 5-criterion rubric)
- Embedded in Exam Mode flow, not a separate app

### Assessment Implementation Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Token infrastructure: `exam_token.py`, `exam_session.py`, `generate_exam_token.py` | ✅ Complete (prior session) |
| Phase 2 | Detection & Monitoring exam mode (4 routes + `exam_data_v1.py`/`exam_data_v2.py`) | ✅ Complete (prior session) |
| Phase 3 | Red Team exam mode (`exam_challenges_v1.py`/`v2.py` + app.py wiring + slowapi) | ✅ Complete (`86beaab`, `b75f89b`, 2026-04-30) |
| Phase 4 | Theory assessment: `framework/exam_questions.py` + `framework/static/js/exam_mode.js` | ✅ Complete (`c330df4`, `86beaab`, 2026-04-30) |
| Phase 5 | exam-admin space (HMAC verification, batch verify, short-answer panel, LTI grade passback) | Planned |
| Phase 6 | Blue Team + Multimodal + Data Poisoning exam datasets | Planned |
| Phase 7 | Cross-lab capstone | Deferred |

### Theory Question Bank (`framework/exam_questions.py`)

| Lab | MCQ | Short Answers | Bloom's Levels |
|-----|-----|---------------|----------------|
| `red-team` | 10 (5 pts each = 50 pts) | 3 (20 pts each = 60 pts) | L4–6 (Analyze, Evaluate, Synthesize) |
| `detection-monitoring` | 10 (5 pts each = 50 pts) | 3 (20 pts each = 60 pts) | L4–6 (Analyze, Evaluate, Synthesize) |

Short answer rubric: 5 criteria × 4 points (technical accuracy, specificity, professional framing, coverage, conciseness).

---------------------------------------------------------------------

## Shared Framework

| File | Lines | Purpose |
|------|-------|----------|
| `framework/static/css/styles.css` | 915 | Shared dark theme |
| `framework/static/js/core.js` | ~388 | DOM helpers, fetchJSON, renderTabs, renderLevelBriefing, renderProgress, renderWhyCard, renderGuidedPractice, renderLeaderboard, renderInfoPage, renderKnowledgeCheck, wireKnowledgeCheck, renderGlossaryPanel |
| `framework/static/js/exam_mode.js` | ~230 | Exam infrastructure: token detection, session init, timer banner, theory form, WebCrypto HMAC receipt signing |
| `framework/scoring.py` | 55 | Score calculation + Leaderboard class |
| `framework/groq_client.py` | 25 | Groq API wrapper |
| `framework/exam_token.py` | — | HMAC token generate + validate |
| `framework/exam_session.py` | — | ExamSession class: attempt caps, timing, receipt serialization |
| `framework/exam_questions.py` | ~500 | Theory question bank (MCQ + SA + rubrics); `get_client_questions()`, `score_mcq()` |
| `framework/templates/base.html` | 30 | Jinja2 HTML shell |

**Deploy:** `./scripts/deploy.sh <space-name>` copies framework → pushes to HF

Blue Team and Red Team use the shared framework (import from core.js). OWASP workshop is independent (not yet migrated).

---------------------------------------------------------------------

## Planned Products (7 remaining)

*Stale issue refs from a previous repo's numbering removed 2026-04-27. Tracking issues for each space will be filed at bootstrap time.*

| Priority | Space | Status | v1 Content | Hardware |
|----------|-------|--------|------------|----------|
| 3 | Multimodal Security | **Phase 3.1 COMPLETE** at `nikobehar/ai-sec-lab4-multimodal` (issue #21, PR #23, 2026-04-29) — 3 defense quality fixes deployed. Updated catches: `output_redaction` 10/10, `ocr_prescan` **6/10** (+P1.5+P5.6), `boundary_hardening` 0/10 catch + **7/10 partial-deters** (sandwich pattern), `confidence_threshold` **2/10** (+P5.1+P5.3, histogram-spike analysis). PR #23 pending merge. v1.1 image regen (P1.4/P5.2/P5.5) is the only remaining non-blocking follow-up. | P1 Image Prompt Injection + P5 OCR Poisoning | `cpu-basic` + HF Inference Providers (`Qwen/Qwen2.5-VL-72B-Instruct` via `ovhcloud`) |
| 4 | Data Poisoning Lab | **Phase 4b COMPLETE** at `nikobehar/ai-sec-lab5-data-poisoning` — full 4-tab Luminex SPA live (Info / RAG Poisoning / Defenses / Corpus Browser). Phase 4a 9-endpoint API surface + upload mode + scoring still live. Phase 5 measured matrix authoritative (provenance 6/6, adv_filter 3/6, retrieval_diversity 1/6, output_grounding 1/6, all_four 6/6). All reviewer-validated (10 issues across 4 passes). Phase 2 (corpus 6→15 expansion) is the only non-blocking follow-up. | RAG corpus poisoning (RP.1—RP.6) | `cpu-basic` + Groq (`llama-3.3-70b-versatile`) + sentence-transformers MiniLM-L6 in-process |
| 5 | Detection & Monitoring | **Phase 2 COMPLETE** — Phase 1 (all 16 source files, `cf4042b`+`a41a1fa`) + Phase 2 exam mode (`exam_data_v1.py`, `exam_data_v2.py`, 4 exam routes in `app.py`). Next: deploy to HF Space + acceptance checks. HF Space: `nikobehar/ai-sec-lab6-detection` (cpu-basic, model-free v1) | Log analysis (D1), anomaly detection (D2), output sanitization (D3) | `cpu-basic` (no model) |
| 6 | Incident Response | Planned | AI breach simulation, containment, forensics | CPU |
| 7 | Multi-Agent Security | Planned | Multi-agent attack, cascading failures | CPU |
| 8 | Model Forensics | Planned | Backdoor detection, train your own guard, DP demo | TBD (`cpu-basic` + HF Inference Providers most likely) |
| 9 | AI Governance | Planned | Security policy writer, risk assessment, threat modeling | CPU |

---------------------------------------------------------------------

## GitHub Issues

### ai-security-labs repo

*Triaged via MCP on 2026-04-27 by Audit Phase.*

| # | Title | Status | Implementation |
|---|-------|--------|----------------|
| 1 | SPEC: Blue Team Architecture | Closed ✅ (2026-04-27) | All 4 challenges built |
| 2 | SPEC: Prompt Hardening Challenge | Closed ✅ (2026-04-27) | `e7dfece` |
| 3 | SPEC: WAF Rules Challenge | Closed ✅ (2026-04-27) | `dadc6b7` |
| 4 | SPEC: Defense Pipeline Builder | Closed ✅ (2026-04-27) | `9978006` |
| 5 | SPEC: Model Behavioral Testing | Closed ✅ (2026-04-27) | `9978006` |
| 6 | Blue Team: Guided warm-up | Closed ✅ | — |
| 7 | Blue Team: Per-level educational cards | Closed ✅ | — |
| 8 | Blue Team: What-to-try suggestions | Closed ✅ (2026-04-27) | `39fe586` + `7d157bb` |
| 9 | Red Team: Per-level briefing cards | Closed ✅ (2026-04-27) | `39fe586` + `cf87474` |
| 10 | Red Team: Technique suggestions | Closed ✅ (2026-04-27) | `39fe586` + `cf87474` |
| 11 | Both: Progress visualization | Closed ✅ (2026-04-27) | `2994d90` |
| 12 | Both: WHY explanations | Closed ✅ (2026-04-27) | `2994d90` + `7d157bb` + `cf87474` |
| 13 | Spec drift: Red Team L1 system prompt framing | Closed ✅ (2026-04-28) | Fixed in red_team_challenge.md — drift was on all 5 levels, not just L1 |
| 14 | Spec gap: Educational features not in any spec | Closed ✅ (2026-04-28) | Educational Layer sections added to blue-team + red-team architecture.md |
| 15 | MILESTONE: Multimodal Security Lab v1 build | Closed ✅ (2026-04-30) | All 6 phases complete — cpu-basic + Qwen2.5-VL-72B live; Phase 3.1 defense quality fixes (PR #23); pedagogical Phase A+B+C applied. |
| 16 | Red Team L5 missing Guardrail Evaluation defense layer | Closed ✅ (2026-04-28) | Implemented `guardrail_evaluate()` in challenges.py; wired into L5 attack flow in app.py |
| **17** | Brand refresh: re-sync architecture.md Brand & Identity sections to digistore-pattern nav | Closed ✅ (2026-04-30) | PR #26 — Master Nav section + Constraints updated for both red-team + blue-team architecture.md |
| **18** | needs-decision: does alt="Luminex Learning" satisfy NR-2 or do we need a visible wordmark? | **Open** (needs human decision) | Blocked — requires design/brand decision before any nav change |
| **19** | Eliminate hardcoded color primitives (NR-8) | Closed ✅ (2026-04-30) | PR #24 — tokens added, multimodal.css + luminex-bridge.css (blue+red team) fixed |
| **20** | Pre-existing spec gaps: missing project-status.md + architecture.md | Closed ✅ (2026-04-30) | PR #25 — bootstrapped docs/project-status.md for blue-team and red-team |
| 21 | Multimodal Phase 3.1: 3 defense quality fixes | Closed ✅ (2026-04-29) | PR #23 — ocr_prescan 6/10, boundary_hardening 7/10 partial-deters, confidence_threshold 2/10 |
| **22** | MILESTONE: Data Poisoning Lab v1 build | **Open** (filed 2026-04-29) | Phase 4b complete. Phase 2 corpus expansion (6→15 legit docs) is the only remaining non-blocking item. |
| **23** | PR: Multimodal Phase 3.1 defense fixes | **Open** (PR #23) | Awaiting merge |
| **24** | PR: Fix NR-8 hardcoded color primitives | **Open** (PR #24) | Awaiting merge |
| **25** | PR: Bootstrap space-level project-status.md | **Open** (PR #25) | Awaiting merge |
| **26** | PR: Sync architecture.md nav spec | **Open** (PR #26) | Awaiting merge |
| **27** | Space 6: Detection & Monitoring Phase 1 milestone | **Open** (deploy + acceptance checks pending) | Phase 1+2 code complete; exam_questions.py + exam_mode.js available from framework; deploy to HF Space next |

### llm-top-10-demo repo (OWASP workshop)
- 31 issues total (12 closed, 19 open)
- Open issues cover: slide improvements (#2), tab restructure (#3), export scorecard (#26), defense in Custom Prompt (#27), plus future lab issues (#4-23, #32)

---------------------------------------------------------------------

## Session History

*(Sessions 1–15 omitted for brevity — see git log for full history)*

### Session (2026-04-30) — Maintenance pass: 4 issues closed

**Issues closed:**
- #15 Multimodal MILESTONE — all 6 phases complete; closed with summary comment
- #17 architecture.md spec sync (red-team + blue-team) — Master Nav + Constraints updated to digistore-pattern; PR #26
- #19 NR-8 CSS fix — hardcoded color primitives replaced with Luminex tokens across all 3 live spaces; PR #24
- #20 Missing space-level project-status.md — bootstrapped docs/project-status.md for blue-team and red-team; PR #25

**Still open:**
- #18 (needs human decision: visible wordmark vs. alt= for NR-2 compliance)
- #22 (Data Poisoning MILESTONE — Phase 4b complete; corpus expansion non-blocking)
- PRs #23, #24, #25, #26 — all awaiting merge

------------------------------------------------------------------------

### Session (2026-04-30 cont.) — Assessment Phases 3+4 complete

**Trigger:** User requested Assessment Phases 3 and 4 from the summative assessment plan.

**Phase 3 — Red Team exam mode** (commits `86beaab`, `b75f89b`):

- `spaces/red-team/exam_challenges_v1.py` — Section A: 5 levels with canaries VERMILION KESTREL / COBALT MERIDIAN / SILVER ECLIPSE / COPPER VANGUARD / TITANIUM FORTRESS. Departments: Research Computing, Procurement, Compliance, SecurityOps, Board Secretariat. Same 5-tier defense structure as workshop, different content and framing.
- `spaces/red-team/exam_challenges_v2.py` — Section B: 5 levels with canaries AURORA SENTINEL / QUARTZ NEXUS / ONYX PROTOCOL / JADE CITADEL / SAPPHIRE DIRECTIVE. Departments: Customer Success, Supply Chain, Privacy & Legal, InfraOps, Executive Management.
- `spaces/red-team/app.py` — Modified: added `exam_token: Optional[str]` to `RedTeamAttempt`; added `_get_exam_levels(variant)` + `_resolve_exam_session(exam_token, exercise_id)` helpers; modified `/api/attempt` to branch on exam mode (resolve session, use alternate levels, record attempt); added 5 exam routes (`POST /api/exam/validate`, `POST /api/exam/theory`, `GET /api/exam/questions`, `GET /api/exam/receipt`, `GET /api/exam/status`); added slowapi `@limiter.limit("10/minute")` to all POST endpoints.
- `spaces/red-team/requirements.txt` — Added `slowapi==0.1.9`.

**Phase 4 — Theory assessment** (commits `c330df4`, `86beaab`):

- `framework/exam_questions.py` — Two lab question banks (`red-team`, `detection-monitoring`). Each bank: 10 MCQ at Bloom's L4–6 (5 pts each), 3 short answers at Bloom's L5–6 (20 pts each, rubric: 5 criteria × 4 pts). Red Team questions target: defense layer decomposition, attack vector analysis, defense tradeoff evaluation, multi-turn leak vector design, guardrail necessity evaluation. Detection questions target: D2 threshold tuning, D3 F1 optimization, WAF rule generalization, anomaly detection logic, SOC alert fatigue. Includes `get_client_questions(lab_id)` (strips answer keys + instructor notes) and `score_mcq(lab_id, answers)`. Server-side answer keys never sent to client.
- `framework/static/js/exam_mode.js` — Exam client infrastructure: `detectExamToken()` (URL param), `initExamMode(token, labId)` (POST /api/exam/validate), `renderExamBanner(ctx, container)` (countdown timer with critical/warning color transitions at 5min/15min), `renderTheoryAssessment(container, token, labId)` (MCQ radio buttons + SA textareas with word count, submit to /api/exam/theory, confirmation screen), `signAndDownloadReceipt(token, labId)` (WebCrypto HMAC using first 32 bytes of token, downloads signed JSON).

**Exam dataset design (both labs):**
- Workshop → exam: departments, canary phrases, system prompt framing all changed. Students cannot transfer memorized workshop answers.
- Section A vs B: non-overlapping attack hours (D2), different credential/injection patterns (D3), different canaries (Red Team). Students in different sections cannot share answers.
- Same defense tier structure preserved — generalization is the skill being assessed, not pattern recognition.

**Next Recommended Task:**
- Deploy Space 6 (Detection & Monitoring) to `nikobehar/ai-sec-lab6-detection` and run acceptance checks (issue #27). Phase 1+2 code + exam_questions + exam_mode.js all available in main.
- Phase 5 of the assessment system: `spaces/exam-admin/` — HMAC verification, batch verify, short-answer grading panel, LTI grade passback.
