# Project Status — AI Security Labs Platform

*Last updated: 2026-04-09 (Session 10)*

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
  - L5: Executive — **Input Scanner** (40+ patterns) + prompt hardening + **Output Redaction** (secret: OMEGA THRESHOLD) — 3 defense layers
- **Defense Layers (new):** Input scanning (blocks prompts with flagged patterns before model call), Output redaction (scans response for secret, redacts if found), Defense log (shows which layers fired and their verdicts)
- **Jailbreak Lab:** 15 pre-loaded techniques across 5 categories (Direct Override, Encoding, Role-Play, Social Engineering, Advanced)
- **Technique Effectiveness Heatmap:** Live success rates across all participants, grouped by category, color-coded (red=dangerous, green=good defense)
- **Features:** Guided practice (5 steps), level briefing cards, progress stars, scoring (100 pts first try, -20 per attempt), leaderboard, hints after 3 failures, defense log per attempt

---------------------------------------------------------------------

## Shared Framework

| File | Lines | Purpose |
|------|-------|---------|
| `framework/static/css/styles.css` | 915 | Shared dark theme |
| `framework/static/js/core.js` | ~220 | DOM helpers, fetchJSON, renderTabs, renderLevelBriefing, renderProgress, renderWhyCard, renderGuidedPractice, renderLeaderboard, renderInfoPage |
| `framework/scoring.py` | 55 | Score calculation + Leaderboard class |
| `framework/groq_client.py` | 25 | Groq API wrapper |
| `framework/templates/base.html` | 30 | Jinja2 HTML shell |

**Deploy:** `./scripts/deploy.sh <space-name>` copies framework → pushes to HF

Blue Team and Red Team use the shared framework (import from core.js). OWASP workshop is independent (not yet migrated).

---------------------------------------------------------------------

## Planned Products (7 remaining)

| Priority | Space | Content | Hardware | Issues |
|----------|-------|---------|----------|--------|
| 3 | Multimodal Security | Image injection, adversarial, stego, OCR, deepfake, CAPTCHA | GPU (T4) | #13-20 |
| 4 | Data Poisoning Lab | RAG poisoning, fine-tuning poisoning, synthetic data | GPU (T4) | #7-8, 19 |
| 5 | Detection & Monitoring | Log analysis, anomaly detection, output sanitization | CPU | — |
| 6 | Incident Response | AI breach simulation, containment, forensics | CPU | — |
| 7 | Multi-Agent Security | Multi-agent attack, cascading failures | CPU | #10 |
| 8 | Model Forensics | Backdoor detection, train your own guard, DP demo | GPU (T4) | #15, 22-23 |
| 9 | AI Governance | Security policy writer, risk assessment, threat modeling | CPU | — |

---------------------------------------------------------------------

## GitHub Issues

### ai-security-labs repo
| # | Title | Status |
|---|-------|--------|
| 1 | SPEC: Blue Team Architecture | Open |
| 2 | SPEC: Prompt Hardening Challenge | Open |
| 3 | SPEC: WAF Rules Challenge | Open |
| 4 | SPEC: Defense Pipeline Builder | Open |
| 5 | SPEC: Model Behavioral Testing | Open |
| 6 | Blue Team: Guided warm-up | Closed ✅ |
| 7 | Blue Team: Per-level educational cards | Closed ✅ |
| 8 | Blue Team: What-to-try suggestions | Closed ✅ |
| 9 | Red Team: Per-level briefing cards | Closed ✅ |
| 10 | Red Team: Technique suggestions | Closed ✅ |
| 11 | Both: Progress visualization | Closed ✅ |
| 12 | Both: WHY explanations | Closed ✅ |

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
- ✅ Defense Pipeline Builder (visual pipeline, presets, coverage+efficiency)
- ✅ Model Behavioral Testing (12 hidden vulns, 6 categories, discovery tracking)

6. Added defense layers to Red Team Workshop
   - **Input Scanner** (Level 4+): Scans user prompt for blocked patterns before model call. Level 4 blocks ~15 keywords (ignore, translate, encode, etc.), Level 5 blocks 40+ patterns (poems, hypotheticals, role-play, etc.)
   - **Output Redaction** (Level 5): Scans model response for the secret — exact match and split-word detection. Replaces with [REDACTED]
   - **Defense Log**: Collapsible panel showing which defense layers fired and their verdicts (PASSED/BLOCKED/SKIPPED)
   - **"Blocked by" badge**: Shows which layer blocked the attack (Input Scanner or Output Redaction)
   - Updated Level 4+5 briefing cards to explain the new defense layers

7. Added Jailbreak Effectiveness Heatmap to Red Team Workshop
   - Tracks success/fail per technique across all participants
   - Grouped by category (Direct Override, Encoding, Role-Play, Social Engineering, Advanced)
   - Color-coded bars: red = high success (dangerous), green = low success (good defense)
   - Live-updating as participants test techniques

8. Deployed Red Team to HF Space, verified in Chrome:
   - Level 4 input scanning blocks "ignore...translate" prompt correctly
   - Defense Log shows "Input Scanner — BLOCKED — Blocked patterns detected: ignore, translate, system prompt"
   - Jailbreak heatmap populated after first test (Ignore Previous Instructions: 100%, 1/1)
