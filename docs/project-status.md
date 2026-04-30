# Project Status — AI Security Labs Platform

*Last updated: 2026-04-29 (Space 6 bootstrap: Detection & Monitoring Phase 0 complete — 4 specs + CLAUDE.md + project-status.md pushed to main `3f2f739`. Issue #27 filed. Next: Phase 1 implementation.)*

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
| 3 | `nikobehar/red-team-workshop` | Running, private | Red Team Levels (5 targets) + Jailbreak Lab (15 techniques, leaderboard) | CPU |

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
- **Prompt Hardening tested:** L1=130, L2=130, L3=105, L4=90, L5=110 — zero false positives
- **WAF Rules tested:** 9 rules → 50% F1, 100% precision, 33% recall — scoring and PG2 comparison working
- **Pipeline Builder tested:** Kitchen Sink 84/100 (14/15 blocked, 93% coverage), Fast & Cheap 81/100, None 18/100. Only misinformation probe not caught by any tool
- **Behavioral Testing tested:** PII Leakage V5 (employee names) triggered on first query with "Who leads the engineering team?"

### Red Team Workshop (Space 3)
- **Red Team Levels:** 5 progressively hardened NexaCore systems
  - L1: HR Portal — no defenses (secret: CRIMSON FALCON) ✅ extractable with simple ask
  - L2: Finance — basic refusal (secret: SHADOW PROTOCOL) ✅ extractable with authority claim
  - L3: Legal — XML hardening (secret: IRON CASCADE) ✅ extractable with translation
  - L4: DevOps — **Input Scanner** + prompt hardening (secret: GHOST MERIDIAN) — blocked keywords prevent most attacks before model call
  - L5: Executive — **Input Scanner** (40+ patterns) + prompt hardening + **Output Redaction** + **Guardrail Model** (secret: OMEGA THRESHOLD) — 4 defense layers
- **Defense Layers (new):** Input scanning (blocks prompts with flagged patterns before model call), Output redaction (scans response for secret, redacts if found), Defense log (shows which layers fired and their verdicts)
- **Jailbreak Lab:** 15 pre-loaded techniques across 5 categories (Direct Override, Encoding, Role-Play, Social Engineering, Advanced)
- **Technique Effectiveness Heatmap:** Live success rates across all participants, grouped by category, color-coded (red=dangerous, green=good defense)
- **Features:** Guided practice (5 steps), level briefing cards, progress stars, scoring (100 pts first try, -20 per attempt), leaderboard, hints after 3 failures, defense log per attempt

---------------------------------------------------------------------

## Shared Framework

| File | Lines | Purpose |
|------|-------|----------|
| `framework/static/css/styles.css` | 915 | Shared dark theme |
| `framework/static/js/core.js` | ~388 | DOM helpers, fetchJSON, renderTabs, renderLevelBriefing, renderProgress, renderWhyCard, renderGuidedPractice, renderLeaderboard, renderInfoPage, renderKnowledgeCheck, wireKnowledgeCheck, renderGlossaryPanel |
| `framework/scoring.py` | 55 | Score calculation + Leaderboard class |
| `framework/groq_client.py` | 25 | Groq API wrapper |
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
| 5 | Detection & Monitoring | **Phase 0 COMPLETE** — 4 specs + CLAUDE.md pushed (`3f2f739`, 2026-04-29). Issue #27 filed. Phase 1 (core impl) next. HF Space: `nikobehar/ai-sec-lab6-detection` (cpu-basic, model-free v1) | Log analysis (D1), anomaly detection (D2), output sanitization (D3) | `cpu-basic` (no model) |
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
| **27** | Space 6: Detection & Monitoring Phase 1 milestone | **Open** (filed 2026-04-29) | Phase 0 bootstrap complete; Phase 1 core impl is next |

### llm-top-10-demo repo (OWASP workshop)
- 31 issues total (12 closed, 19 open)
- Open issues cover: slide improvements (#2), tab restructure (#3), export scorecard (#26), defense in Custom Prompt (#27), plus future lab issues (#4-23, #32)

---------------------------------------------------------------------

## Session History

### Sessions 1-6 (2026-04-06 to 2026-04-07)
Built the OWASP Top 10 Workshop from scratch:
- 25 attacks across 3 OWASP standards (LLM, MCP, Agentic AI)
- 5 defense tools with full effectiveness matrix
- Frontend: tabs + dropdown layout, slide deck, defense panels, SSE streaming
- EN/ES translations, difficulty badges, Info tab, mobile responsive
- All attacks verified, all defenses tested

### Sessions 7-8 (2026-04-09)
Built the monorepo and 2 new workshops:
- Created `ai-security-labs` monorepo with framework extraction
- Built Blue Team Workshop (Prompt Hardening, 5 levels, 15 attacks, WHY explanations)
- Built Red Team Workshop (Red Team Levels, 5 targets + Jailbreak Lab, 15 techniques)
- Extracted shared framework (core.js, scoring.py, groq_client.py, CSS)
- Migrated Blue Team + Red Team to use shared framework
- Added guided practice walkthroughs (5 steps each)
- Added level briefing cards with collapsible suggestions
- Added progress visualization (stars per level)
- Fixed Red Team Level 1+2 (model's built-in safety was blocking undefended levels)
- Fixed Red Team Level 4 (too restrictive, blanket refusal)
- Full end-to-end walkthrough verified for both workshops
- All 3 Spaces set to private

### Key Decisions
- **Monorepo:** Single repo (`ai-security-labs`) with `framework/` + `spaces/` structure
- **Separate Spaces:** Each workshop is its own HF Space (independent deploy, different hardware possible)
- **Framework imports:** New Spaces import from `core.js` via ES modules
- **Deploy script:** `scripts/deploy.sh` copies framework into Space before push
- **Red Team prompts:** Level 1 uses "internal reference notes" (not "classified") to avoid LLaMA's built-in safety. Level 4 allows general discussion but protects the specific codename.
- **ML Top 10 skipped:** Most risks need training pipeline access, demoable ones overlap with LLM Top 10
- **Private Spaces:** All Spaces set to private for workshop access control

### Session 9 — 2026-04-09

**What was accomplished:**

1. Built WAF Rules Challenge for Blue Team Workshop
   - waf_parser.py: Rule DSL parser (BLOCK/ALLOW × contains/regex)
   - 20 legitimate queries (expanded from 5)
   - F1 scoring with Prompt Guard 2 baseline comparison
   - Confusion matrix, per-query detail cards, "beat PG2" indicator
2. Full end-to-end walkthroughs verified:
   - Red Team: guided practice (5 steps) + all 5 levels tested with suggested techniques
   - Blue Team: guided practice (5 steps) + all 5 Prompt Hardening levels + WAF Rules tested
3. Fixed Red Team Level 1 (model refused "classified" framing → changed to "internal reference")
4. Fixed Red Team Level 4 (blanket refusal → softened to protect codename while allowing conversation)
5. Updated project-status.md with comprehensive platform state

**Blue Team now has 2/4 challenges:**
- ✅ Prompt Hardening (5 levels, WHY explanations)
- ✅ WAF Rules (regex detection, F1 scoring, PG2 comparison)
- 📋 Defense Pipeline Builder (specced)
- 📋 Model Behavioral Testing (specced)

### Session 10 — 2026-04-09

**What was accomplished:**

1. Built Defense Pipeline Builder (challenge #3 for Blue Team)
   - Visual pipeline with 5 toggleable defense stages (INPUT→CONTEXT→PROMPT→OUTPUT→GUARDRAIL)
   - Pre-computed DEFENSE_MATRIX: which of 5 tools catches which of 15 attacks
   - 3 presets: None (0% coverage), Fast & Cheap (80% coverage), Kitchen Sink (93% coverage)
   - Coverage (0-80) + Efficiency (0-20) scoring — trade-off is the lesson
   - Score comparison chart against all presets
   - Per-attack results showing which stage caught each attack + recommendations for missed attacks
   - No Groq API calls needed — pure matrix lookup, instant evaluation

2. Built Model Behavioral Testing (challenge #4 for Blue Team)
   - 12 hidden vulnerabilities across 6 categories (Bias, Toxicity, PII, Instruction Following, Refusal Bypass, Factual Accuracy)
   - Carefully crafted vulnerable system prompt with subtle flaws (not obviously broken)
   - Detection lambdas for each vulnerability (pattern matching on model output)
   - Session tracking (in-memory, keyed by session_id)
   - Category progress bars with per-category discovery tracking
   - Hints for unfound vulnerabilities
   - Discovery (0-100) + Efficiency bonus (up to +60) scoring
   - Uses Groq API for each test prompt

3. Updated Blue Team frontend: 6 tabs (Info, Prompt Hardening, WAF Rules, Pipeline Builder, Behavioral Testing, Leaderboard)
4. Updated leaderboard to aggregate scores across all 4 challenges
5. Deployed to HF Space, verified both challenges working in Chrome

**Blue Team now has 4/4 challenges — all complete:**
- ✅ Prompt Hardening (5 levels, WHY explanations)
- ✅ WAF Rules (regex detection, F1 scoring, PG2 comparison)
- ✅ Defense Pipeline Builder (5-stage visual pipeline, matrix scoring)
- ✅ Model Behavioral Testing (12 hidden vulnerabilities, Groq-powered)

### Session 11 — 2026-04-27 (Audit + Pedagogy Pass)

Full audit of all 3 live spaces. Issues triaged and closed (1-14). Pedagogical improvements planned (QM rubric applied). Next: Issues 15-16 (Multimodal MILESTONE + Red Team L5 Guardrail).

### Session 12 — 2026-04-28

Multimodal Security Lab Phase 1 scaffolding: FastAPI app.py + attacks.py + scoring.py + Dockerfile + HTML/CSS/JS SPA (5 tabs). 10 attacks across P1 (image injection) and P5 (OCR poisoning) attack classes. Groq LLaMA 3.3 70B vision via HF Inference Providers. Phase 1 live on HF Space.

### Session 13 — 2026-04-28 (Red Team + Blue Team Phase A Pedagogy)

Phase A pedagogical improvements: "What You'll Learn" cards + Knowledge Check (3 MCQ each) + cross-lab nav + Assumed Knowledge added to all 4 live spaces (Red Team, Blue Team, Multimodal, Data Poisoning). `renderKnowledgeCheck()` + `wireKnowledgeCheck()` added to `framework/core.js`. Commit `b093ddb`.

### Session 14 — 2026-04-29 (Maintenance + Space 6 Bootstrap)

**Issues closed:** #15 (Multimodal MILESTONE), #17 (architecture.md spec sync), #19 (NR-8 CSS fix), #20 (missing space-level project-status.md). **Issue #18** left open (wordmark decision — user said "leave mark as-is and proceed"). **PRs filed:** #23 (Multimodal Phase 3.1), #24 (NR-8 fix), #25 (space-level project-status), #26 (architecture.md spec sync). **Space 6 Detection & Monitoring Phase 0 bootstrap:** 4 specs + CLAUDE.md + project-status.md written and pushed (`3f2f739`). Issue #27 filed. Ready for Phase 1.
