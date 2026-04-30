# Project Status — AI Security Labs Platform

*Last updated: 2026-04-29 (Phase C complete — reflection prompts + platform glossary. All 4 live labs fully updated through Phase A+B+C pedagogical improvements. QM S1/S2/S3/S7 gaps addressed. Multimodal Phase 3.1 COMPLETE — 3 defense quality fixes, issue #21 closed, PR #23 open.)*

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
| 5 | Detection & Monitoring | Not started | Anomaly detection, rate limiting, behavioral analysis | CPU |
| 6 | Incident Response | Not started | IR playbooks, log analysis, containment procedures | CPU |
| 7 | Multi-Agent Security | Not started | Agent trust, tool use attacks, orchestration vulnerabilities | CPU |
| 8 | Model Forensics | Not started | Model extraction, membership inference, watermarking | `cpu-basic` + HF Inference Providers |
| 9 | AI Governance | Not started | Risk frameworks, red-teaming standards, policy compliance | CPU |

---------------------------------------------------------------------

## Open GitHub Issues

*Use GitHub MCP to query: `mcp__github__list_issues({owner:"nbehar", repo:"ai-security-labs", state:"open"})`*

Recently closed:
- **#21** (Multimodal Phase 3.1: 3 defense quality fixes) — CLOSED 2026-04-29. PR #23 pending merge.

---------------------------------------------------------------------

## Active Blockers

None currently blocking workshop use.

---------------------------------------------------------------------

## Next Recommended Tasks

### Immediate
1. **Merge PR #23** (Multimodal Phase 3.1) — all 5 files reviewed, issue #21 closed.

### Near-term
2. **Multimodal v1.1 image regen** — P1.4 (truncation at `max_tokens=512`), P5.2 (microprint canary placement), P5.5 (rotated margin OCR miss). Would lift clean-success baseline from 6/12 to 9/12. Medium priority; lab is usable as-is.
3. **Data Poisoning Phase 2** — expand corpus from 6 to 15 documents. Non-blocking follow-up.

### Deferred
4. **Phase 6 (Canvas LMS)** for Multimodal — autograde + score submission via Canvas API.
5. **Lab 6–10 builds** — bootstrap when next lab is prioritized.

---------------------------------------------------------------------

## Session History (Platform-Level)

### 2026-04-27 — Platform bootstrap + Space 4 (Multimodal) bootstrap

- Created monorepo `nbehar/ai-security-labs`
- Established platform conventions (specs-first, deploy.sh, framework/)
- Bootstrapped Multimodal Security Lab (4 specs + CLAUDE.md + project-status.md)
- Filed GitHub milestone issue #15 for Multimodal v1

### 2026-04-28 — Multimodal Phase 1+2+3+4a+4b

[Full entry preserved in git history; summary: 5 phases in one day. Phase 1 backend skeleton, Phase 2 pre-canned image library (24 PNGs), Phase 3 defenses.py + ocr_pipeline.py + Tesseract wiring, Phase 3 prep calibration matrix (12 attacks vs 72B, 6/3/3 clean/flagged/refused), Phase 4a full API surface + Postman collection, Phase 4b full Luminex Learning SPA shell (4 tabs, brand-gold owl, AISL violet accent). All deployed live at `nikobehar/ai-sec-lab4-multimodal`. Note: ZeroGPU → HF Inference Providers pivot at Phase 1+2; Qwen2.5-VL-7B → 72B pivot at deploy time (7B has no live HF Inference Providers route).]

### 2026-04-29 — Data Poisoning Lab Phase 1 through 4b

[Full entry preserved in git history; summary: Full bootstrap and build for Lab 5 (Data Poisoning) in one session. 4 specs, 6 attack definitions (RP.1–RP.6), RAG pipeline with sentence-transformers MiniLM-L6, 4 defenses (provenance/adv_filter/retrieval_diversity/output_grounding), Phase 4a API surface (9 endpoints), Phase 4b Luminex SPA shell (4 tabs), Phase 5 measured matrix (6 attacks × 5 conditions = 30 cells). All deployed live at `nikobehar/ai-sec-lab5-data-poisoning`. 10 reviewer-identified issues resolved across 4 passes.]

### 2026-04-29 (cont.) — Pedagogical Review (Phase A+B+C) across all 4 live labs

[Full entry preserved in git history; summary: QM-framework-informed review identified 10 improvements across Red Team, Blue Team, Multimodal, and Data Poisoning labs. Phases A (learning objectives + knowledge checks + cross-lab nav + assumed knowledge), B (Multimodal known-limitation badges, RP.5 headline callout, cold-start banner, WAF regex primer), and C (reflection prompts + platform glossary) all implemented and deployed. Issue #20 filed and closed. Core.js now exports renderKnowledgeCheck, wireKnowledgeCheck, renderGlossaryPanel. All 4 `app.js` files updated.]

### 2026-04-29 (cont.) — Multimodal Phase 3.1: Defense Quality Fixes

**Issue #21 closed.** Three defense quality fixes measured and deployed.

- **Fix 1 (`ocr_prescan` widening):** +6 keyword patterns. ocr_prescan 4/10 → 6/10.
- **Fix 2b (`confidence_threshold` histogram-spike):** Pillow pixel-count analysis catches near-white hidden text (Tesseract-independent). confidence_threshold 0/10 → 2/10.
- **Fix 3 (`boundary_hardening` sandwich):** Post-document reminder appended to user message after image. boundary_hardening partial-deters 2/10 → 7/10.

All files deployed live to HF Space. PR #23 open on branch `multimodal-phase3.1-defense-fixes`.

---------------------------------------------------------------------

## Pedagogical Improvement Plan (Phase A+B+C)

*Completed 2026-04-29. Issue #20 closed.*

### Phase A — Learning Objectives + Knowledge Checks + Cross-Lab Nav + Assumed Knowledge

**Status: COMPLETE.** All 4 live labs updated.

- Added "What You'll Learn" (Bloom's-level objectives) to each Info tab
- Added "Assumed Knowledge" section to each Info tab
- Added "Recommended Learning Path" cross-lab navigation to each Info tab
- Added 4-question Knowledge Check (`renderKnowledgeCheck` + `wireKnowledgeCheck`) to each Info tab
- Added `renderKnowledgeCheck`, `wireKnowledgeCheck` to `framework/static/js/core.js`

**Files modified:** `framework/static/js/core.js` (new exports), `spaces/{red-team,blue-team,multimodal,data-poisoning}/static/js/app.js` (Info tab content + KC questions)

### Phase B — Targeted Fixes + Cold-Start Banner + WAF Primer

**Status: COMPLETE.** All targeted fixes deployed.

1. **Multimodal known-limitation badges (P1.4, P5.5):** Added `known_limitation: true` + tooltip to attack picker in `spaces/multimodal/static/js/app_js` (attack definitions)
   - *Note: P1.4 truncation and P5.5 OCR miss are image-side issues; badges surface this to students before they run the attack*
2. **RP.5 headline callout (Data Poisoning):** Added dedicated semantic-attack callout card in `spaces/data-poisoning/static/js/attack_runner.js` after RP.5 results
3. **Cold-start banner:** Added health-probe retry loop with cold-start messaging to all 4 `app.js` files
4. **WAF regex primer:** Added collapsible primer card in `spaces/blue-team/static/js/app.js` WAF Rules tab

### Phase C — Reflection Prompts + Platform Glossary

**Status: COMPLETE.**

1. **Reflection prompts:** Added end-of-lab collapsible reflection card to `attack_runner.js` in Multimodal and Data Poisoning; per-level reflection in Red Team Levels; Blue Team deferred (challenge completion state spans 4 tabs — non-trivial to detect)
2. **Platform glossary:** Added `renderGlossaryPanel` to `framework/static/js/core.js`; wired into all 4 `app.js` Info tabs as a collapsible "Glossary" section at the bottom. 25 terms: canary token, system prompt, RAG, embedding, cosine similarity, provenance, grounding, jailbreak, prompt injection, WAF, F1 score, false positive, defense-in-depth, OCR, vision model, multimodal LLM, corpus poisoning, adversarial filter, retrieval diversity, output grounding, rate limiting, red team, blue team, guardrail, behavioral testing.

---------------------------------------------------------------------

## Deferred Items

- Multimodal v1.1 image regen: P1.4 (truncation), P5.2 (microprint canary), P5.5 (rotated margin OCR miss) — would lift clean-success baseline from 6/12 to 9/12
- Data Poisoning Phase 2: corpus expansion from 6 to 15 documents
- Multimodal Phase 6: Canvas LMS autograde + score submission
- OWASP workshop framework migration (still independent, not on Luminex brand)
- Legacy space renames: `nikobehar/llm-top-10` → `nikobehar/ai-sec-lab1-owasp`, etc.
- Red Team reflection prompt in Jailbreak Lab (jailbreaks don't have a completion threshold — deferred)
- Blue Team reflection prompt (challenge completion state spans 4 tabs — deferred)
