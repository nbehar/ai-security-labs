# Project Status — AI Security Labs Platform

*Last updated: 2026-04-29 (Multimodal Phase 5 measured matrix verified + 4 reviewer-pass issues filed + Phase 3.1 issue filed + Data Poisoning Lab Phase 0 bootstrap complete)*

---------------------------------------------------------------------

## Platform Overview

Interactive AI security training platform by Prof. Nikolas Behar. **3 workshops live (1 product, 3 sections), 1 in bootstrap, 5 planned.** The monorepo is ONE Luminex Learning product — **AI Security Labs**. The individual spaces (`spaces/red-team/`, `spaces/blue-team/`, `spaces/multimodal/`, plus `spaces/owasp-top-10/`, plus `spaces/data-poisoning/` in bootstrap, plus the 5 still-planned ones) are **sections within AI Security Labs**, not standalone Luminex products. Every space uses the same Luminex Learning master nav (gold owl + "Luminex Learning" wordmark) and the same AISL violet accent (`#a78bfa` highlight, `#7c3aed` interactive) for product-scoped UI; the section label varies (Red Team / Blue Team / Multimodal / OWASP Top 10 / Data Poisoning).

The standalone "Red Team Labs" / "Blue Team Labs" / "GRC Labs" mentioned in `~/luminex/brand-system/design-tokens.json` are separate Luminex products at the company level — not sections in this repo. See `~/.claude/projects/-Users-niko-ai-security-labs/memory/brand-architecture.md` for the canonical brand-architecture explainer; `~/.claude/projects/-Users-niko-ai-security-labs/memory/owasp-brand-policy.md` for the brand-before-public policy that governs the OWASP space refresh timing.

**Monorepo:** https://github.com/nbehar/ai-security-labs

---------------------------------------------------------------------

## Live Products

| # | Space | Status | Content | Hardware |
|---|-------|--------|---------|----------|
| 1 | `nikobehar/llm-top-10` | Running, private | OWASP 3-part workshop (25 attacks, 5 defenses, 3 pills). **Brand refresh pending** (separate CSS pipeline; not yet under Luminex Learning master nav). Per `memory/owasp-brand-policy.md`, brand refresh becomes a hard requirement before this space goes public. | CPU |
| 2 | `nikobehar/blue-team-workshop` | Running, private | **AI Blue Team / AI Security Labs** (Luminex Learning brand, AISL violet). 6 tabs (Info / Prompt Hardening / WAF Rules / Pipeline Builder / Behavioral Testing / Leaderboard). Competitive workshop; leaderboard tab kept. Master nav shipped 2026-04-29. | CPU |
| 3 | `nikobehar/red-team-workshop` | Running, private | **AI Red Team / AI Security Labs** (Luminex Learning brand, AISL violet). 5 tabs (Info / Red Team Levels / Jailbreak Lab / Social Engineering / Leaderboard). Master nav shipped 2026-04-29. | CPU |
| 4 | `nikobehar/ai-sec-lab4-multimodal` | Running, private | **AI Security Labs / Multimodal** (Luminex Learning brand). 4-tab SPA: Info / Image Prompt Injection (P1, 6 attacks) / OCR Poisoning (P5, 6 attacks) / Defenses (4 toggleable). Per-student inline scoring; no leaderboard tab (graduate-course assignment, Canvas LMS integration deferred). **Defenses tab now serves measured matrix from Phase 5 verification (2026-04-29):** `output_redaction` 10/10 · `ocr_prescan` 4/10 · `boundary_hardening` 0/10 catches + 2/10 partial-deters · `confidence_threshold` 0/10 · all four combined 9/10. | `cpu-basic` + HF Inference Providers (`Qwen/Qwen2.5-VL-72B-Instruct` via `ovhcloud`) |

### OWASP Top 10 Workshop (Space 1)
- **3 workshop pills:** LLM Top 10 (10 attacks) + MCP Top 10 (9 attacks) + Agentic AI (6 attacks)
- **5 defense tools:** Meta Prompt Guard 2, LLM Guard Output/Context, System Prompt Hardening, Guardrail Model
- **Features:** Info tab with NexaCore scenario + infra diagram, slide deck (4 per attack, OWASP cheat sheet content), defense-specific slides, SSE scorecard streaming, EN/ES translations, difficulty badges, collapsible slides, detection method badges
- **All 25 attacks verified** against LLaMA 3.3 70B (25/25 succeed undefended)
- **Defense matrix verified** for all 5 tools across all 25 attacks
- **Brand status:** the OWASP space is independent of `framework/` (separate CSS pipeline). The Luminex master nav has NOT been applied; doing so requires a one-off integration. Per `memory/owasp-brand-policy.md` (set 2026-04-29), this is acceptable while the space stays private; brand refresh becomes a hard requirement before the visibility flips to public.

### AI Blue Team / Blue Team Workshop (Space 2)
- **4 of 4 challenges built:** Prompt Hardening (5 levels) · WAF Rules (DSL + F1) · Defense Pipeline Builder (visual pipeline + presets) · Model Behavioral Testing (12 hidden vulns)
- **Features:** Guided practice (5 steps), level briefing cards, progress stars, WHY explanations, hints, leaderboard (aggregates all 4 challenges), 6 tabs
- **Tested:** Prompt Hardening L1=130, L2=130, L3=105, L4=90, L5=110 — zero false positives. WAF Rules: 9 rules → 50% F1, 100% precision, 33% recall. Pipeline Builder: Kitchen Sink 84/100. Behavioral Testing: PII Leakage V5 detected first-query.
- **Brand:** Luminex Learning master nav (gold owl + wordmark + "Blue Team / AI Security Labs" stacked block). AISL violet accent via `luminex-bridge.css` cascade. Brand & Identity section in `spaces/blue-team/specs/architecture.md`.

### AI Red Team / Red Team Workshop (Space 3)
- **Red Team Levels:** 5 progressively hardened NexaCore systems (L1 HR Portal → L5 Executive 4-layer defense)
- **Jailbreak Lab:** 15 pre-loaded techniques across 5 categories
- **Technique Effectiveness Heatmap:** Live success rates across all participants
- **Features:** Guided practice, level briefing cards, progress stars, scoring, leaderboard, hints, defense log per attempt
- **Brand:** Luminex Learning master nav with "Red Team / AI Security Labs" stacked block. AISL violet accent. RTL crimson `#e11d48` deliberately NOT used (NR-9). Brand & Identity section in `spaces/red-team/specs/architecture.md`.

### Multimodal Lab (Space 4)
- **4 tabs:** Info / Image Prompt Injection / OCR Poisoning / Defenses (no Leaderboard — individual graduate assignment)
- **NexaCore DocReceive scenario:** internal document-intake portal that OCRs uploaded receipts/contracts/badges and routes to expense/vendor/badge systems
- **Attacks:** 12 total, 6 P1 visible-text injections + 6 P5 hidden-text/OCR-poisoning. 24 canned PNGs (12 attack + 12 legit), opt-in PNG/JPEG upload mode (≤4MB, in-memory only)
- **Defenses (4 toggleable):** OCR Pre-Scan, Output Redaction, Boundary Hardening, Confidence Threshold. **Phase 5 measured catch rates (2026-04-29):** output_redaction 10/10, ocr_prescan 4/10, boundary_hardening 0/10 catches + 2/10 partial-deters, confidence_threshold 0/10. With all four enabled, 9/10 attacks block. Full data: `docs/phase5-matrix-raw.json` (regen via `scripts/run_phase5_matrix.py`).
- **Inference:** Qwen2.5-VL-72B via HF Inference Providers (OVH cloud), ~1-3s/call median (was specced 10–20s; actual p95 is 15.3s).
- **Brand:** Luminex Learning master nav (digistore Sidebar + Layout pattern: owl + NexaCore / AI Security Labs left, shield + "Multimodal" right). AISL violet accent.
- **Educational layer:** Info tab with NexaCore narrative + arch diagram + 5 Key Concepts cards. Per-lab level briefing with traditional-security analogy. Per-attempt Cause/Effect/Impact result panels + brand-teal Why-this-works card. Defenses tab: 12×4 measured matrix + per-defense detail cards.
- **Scoring:** 100 first try, −20 per retry, floor 20, +50 if a defense blocks. Per-student inline (no leaderboard); `POST /api/score` and `GET /api/leaderboard` endpoints stay alive for Phase 6 Canvas LMS integration

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

Blue Team and Red Team use the shared framework (import from core.js). OWASP workshop is independent (not yet migrated). Multimodal Lab uses `escapeHtml` and `fetchJSON` from `core.js` but renders its own SPA shell with Luminex tokens; deliberately does not use `renderTabs` / `renderLeaderboard` / `renderInfoPage` because the Luminex underline-tab + AISL-accent pattern differs from the existing spaces' filled-tab pattern.

**Luminex brand integration (post-2026-04-29):** Blue Team and Red Team retain framework `styles.css` unmodified; Luminex tokens are layered on top via space-local `luminex-bridge.css` (which retokens `--bg/--surface/--blue/--red/...` to Luminex variables) and `luminex-nav.css` (master nav structure). Minimal-blast-radius cascade approach.

---------------------------------------------------------------------

## In Bootstrap

| Priority | Space | Status | v1 Content | Hardware |
|----------|-------|--------|------------|----------|
| 4 | **Data Poisoning Lab** | **Phase 0 complete** as of 2026-04-29. 4 specs + CLAUDE.md + docs/project-status + README authored. Milestone issue #22 filed. Phase 1 (backend skeleton) requires explicit approval before code lands. | RAG Poisoning (RP) — 6 attacks anchored in NexaCore Knowledge Hub. 4 toggleable defenses (Provenance Check / Adversarial Filter / Retrieval Diversity / Output Grounding). | `cpu-basic` + Groq LLaMA 3.3 70B + `sentence-transformers/all-MiniLM-L6-v2` in-process embeddings |

---------------------------------------------------------------------

## Planned Products (5 remaining)

| Priority | Space | Status | v1 Content | Hardware |
|----------|-------|--------|------------|----------|
| 5 | Detection & Monitoring | Planned | Log analysis, anomaly detection, output sanitization | CPU |
| 6 | Incident Response | Planned | AI breach simulation, containment, forensics | CPU |
| 7 | Multi-Agent Security | Planned | Multi-agent attack, cascading failures | CPU |
| 8 | Model Forensics | Planned | Backdoor detection, train your own guard, DP demo | TBD (`cpu-basic` + HF Inference Providers most likely) |
| 9 | AI Governance | Planned | Security policy writer, risk assessment, threat modeling | CPU |

---------------------------------------------------------------------

## GitHub Issues

### ai-security-labs repo

| # | Title | Status | Implementation |
|---|-------|--------|----------------|
| 1-12 | (Spec/feature issues from Sessions 1-12) | Closed ✅ | See git history |
| 13 | Spec drift: Red Team L1-L5 system prompt framing | Closed ✅ (2026-04-28) | red_team_challenge.md rewritten |
| 14 | Spec gap: Educational features not in any spec | Closed ✅ (2026-04-28) | Educational Layer sections in blue-team + red-team architecture.md |
| **15** | MILESTONE: Multimodal Security Lab v1 build | **Open** (filed 2026-04-27) | Phases 1+2+3+4a+4b+5 shipped. Phase 3.1 (defense quality fixes — see #21) and v1.1 image regen remain. Phase 6 (Canvas LMS) deferred. |
| 16 | Red Team L5 missing Guardrail Evaluation defense layer | Closed ✅ (2026-04-28) | Implemented + wired into L5 |
| **17** | Re-sync architecture.md Brand & Identity sections to digistore-pattern nav | **Open** (filed 2026-04-29 by reviewer pass) | red-team / blue-team architecture specs describe the OLD nav pattern; need re-sync to the digistore split brand-block + page-label layout |
| **18** | needs-decision: does `alt="Luminex Learning"` satisfy NR-2 or do we need a visible wordmark? | **Open** (decision required) | Brand-owner call. Currently relying on alt text + `<title>` only. |
| **19** | Eliminate hardcoded color primitives (NR-8) — multimodal.css + framework/styles.css | **Open** (filed 2026-04-29 by reviewer pass) | `#6d28d9` (multimodal hover), `#2563eb` and rgba(59,130,246,0.06) (framework hover/highlight). Recommended fix: bridge layer overrides to keep blast radius low. |
| **20** | Pre-existing spec gaps: red-team / blue-team missing project-status.md; multimodal missing architecture.md | **Open** (filed 2026-04-29 by reviewer pass) | Surfaced during reviewer pass; pre-existing, not introduced by brand refresh. Low priority. |
| **21** | Phase 3.1 defense quality fixes (multimodal): widen ocr_prescan, replace confidence_threshold, strengthen boundary_hardening | **Open** (filed 2026-04-29 from Phase 5 measured matrix) | Phase 5 surfaced 0/10 catch on confidence_threshold and boundary_hardening; this issue scopes the fixes. |
| **22** | MILESTONE: Data Poisoning Lab v1 build (priority #4) | **Open** (filed 2026-04-29) | Phase 0 (bootstrap) complete; Phase 1 (backend skeleton) requires approval. |

### llm-top-10-demo repo (OWASP workshop)
- 31 issues total (12 closed, 19 open). Open issues cover slide improvements, tab restructure, export scorecard, defense in Custom Prompt, plus future lab issues.

---------------------------------------------------------------------

## Session History

### Sessions 1-12 (2026-04-06 to 2026-04-09 + Audit 2026-04-27)
[Full entries preserved in git history; summary: built OWASP Top 10 Workshop, then monorepo + framework + Blue Team Workshop (4 challenges) + Red Team Workshop (5 levels + Jailbreak Lab). QA fixes, educational enhancements (Key Concepts, traditional-security analogies). Issues #1-12 closed; #13 (Red Team spec drift) and #14 (educational layer not in specs) filed and resolved 2026-04-28.]

### 2026-04-28 — Multimodal Lab build (Phases 0-4a)
[Full entries preserved in git history; summary: bootstrap (4 specs + space CLAUDE.md + milestone issue #15), Phase 1 backend skeleton, Phase 2 image library, ZeroGPU→HF Inference Providers pivot, Phase 1+2 deploy + verify (Qwen2.5-VL-72B via ovhcloud), Phase 3 defenses (4 layers), Phase 3 cleanup (Reviewer findings A+B), Phase 4a full API surface (8 endpoints + scoring + slowapi + Postman). Per-space detail in `spaces/multimodal/docs/project-status.md`.]

### 2026-04-29 — Multimodal Phase 4b (Luminex Learning SPA shell)
[Full entry preserved in git history; summary: 4-tab SPA shell (Info / P1 / P5 / Defenses) with Luminex master nav, AISL violet accent, per-student inline scoring. 7 GitHub commits + 2 HF Space commits. XSS posture pivot to `Range.createContextualFragment`. Issue #15 still open as v1 milestone.]

### 2026-04-29 (cont.) — AI Red Team + AI Blue Team brand refresh + spec drift cleanup
[Full entry preserved in git history; summary: extended `brand-identity-enforcer` compliance to red-team + blue-team. After user clarification ("these are all AI labs"), the architecture is ONE Luminex Learning product (AI Security Labs), three sections. All sections share AISL violet. Bridge-layer cascade approach so framework `styles.css` is unmodified. Saved `memory/brand-architecture.md`. 5 commits: `63cc0b8`, `aaf2b1f`, `eb8fbf0`, `ccf9a9f`, `3396e61`.]

### 2026-04-29 (cont.) — Nav pivots: stacked-block → digistore-pattern
[Full entry preserved in git history; summary: nav redesigned twice in response to user-supplied brand screenshot + reference to `~/digistore/digistore-mock-client/frontend-v2/src/components/Sidebar.tsx` and `Layout.tsx`. Final layout: `[owl 48px gold] NexaCore / hairline / AI Security Labs … [shield] <Section>`. Applied to all 3 live spaces. Commits `7970f74`, `16b6fbc`, `83b500a`, `19d4112`.]

### 2026-04-29 (cont.) — Multimodal Phase 5 (measured defense matrix)

**Trigger:** User direction during Phase 4b close-out — close the integrity gap where the Defenses tab claimed design-intent catch rates without verification.

**What was done:** 12 attacks × 6 conditions = 72 calls executed against deployed `Qwen/Qwen2.5-VL-72B-Instruct` (HF Space `f01d8ef`); 0 errors; ~17 min wall time. Runner committed at `714f0f4` (`spaces/multimodal/scripts/run_phase5_matrix.py` — rate-limit-aware, persists incrementally to JSON, reproducible).

**Headline measured catch rates (over 10 attacks that succeed at baseline):**

| Defense | Catches | Rate |
|---|---|---|
| `output_redaction` | 10 | **10/10** |
| `ocr_prescan` | 4 | 4/10 |
| `boundary_hardening` | 0 catches; 2 partial-deters | 0/10 + 2 RFS |
| `confidence_threshold` | 0 | 0/10 |
| `all_four` (combined) | 9 | **9/10** |

The 2 N/A attacks (P1.4, P5.5) don't succeed at baseline — image-side issues from Phase 3 calibration (`max_tokens` truncation, rotated-margin OCR failure). Defenses can't help.

**Latency:** n=72, median 12.0s, mean 11.0s, p95 15.3s — well within deployment_spec.md "10–20s typical" budget.

**What landed:**
- `714f0f4` — `scripts/run_phase5_matrix.py` (reproducible runner)
- `f01d8ef` — HF Space deploy (Defenses tab serves measured COVERAGE)
- `0e19e1b` — `app.js` updated (measured COVERAGE constant + description text leads with "Measured against deployed Qwen2.5-VL-72B (ovhcloud) on 2026-04-29"); `phase3-calibration.md` extended with full Phase 5 section (methodology, headlines, latency stats, per-attack table, defense-by-defense narrative, recommended pedagogical sequence)

Issue #15 progress comment posted via MCP. Phase 3.1 follow-ups filed as issue #21 (defense quality fixes — widen ocr_prescan, replace confidence_threshold, strengthen boundary_hardening).

### 2026-04-29 (cont.) — Reviewer pass + 4 follow-up issues filed

**Trigger:** User asked the reviewer agent to validate the brand-refresh work after the digistore-pattern nav pivots.

**Result:** Brand refresh accepted. No NR-1 through NR-10 hard blocks. 5 soft flags surfaced; 4 of them filed as GitHub issues:

- **#17** — Spec drift: red-team / blue-team architecture.md Brand & Identity sections describe the OLD stacked-block nav, not the digistore split pattern that actually shipped
- **#18** — needs-decision: NR-2 satisfaction (`alt="Luminex Learning"` only, no visible wordmark in rendered nav) — brand-owner call
- **#19** — NR-8 violation: hardcoded color primitives in `multimodal.css` (`#6d28d9`, `#ffffff`) and `framework/styles.css` (`#2563eb`, `rgba(59,130,246,0.06)`) survive the bridge cascade on hover states
- **#20** — pre-existing gaps: red-team and blue-team missing `docs/project-status.md`; multimodal missing `architecture.md` parallel

The 5th flag was cosmetic class-naming inconsistency (BEM vs non-BEM across the 3 spaces) — not filed; harmonize in future cleanup.

### 2026-04-29 (cont.) — Data Poisoning Lab Phase 0 bootstrap (issue #22)

**Trigger:** User direction during the Phase 5 close-out: "build out the next lab" (priority #4 in the Planned Products queue).

**Decisions locked in:**
- Hardware: HF Spaces `cpu-basic` (free; matches Multimodal post-ZeroGPU pivot)
- LLM: Groq `llama-3.3-70b-versatile` (consistency with red-team / blue-team / OWASP)
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` in-process (env-overridable via `EMBEDDING_MODEL`)
- Vector store: in-memory cosine similarity over numpy (no FAISS at v1)
- v1 scope: RAG Poisoning (RP) only — 6 attacks anchored in NexaCore Knowledge Hub. Fine-tuning + synthetic data poisoning deferred to v2.
- Defenses: 4 toggleable (Provenance Check, Adversarial Filter, Retrieval Diversity, Output Grounding)
- Audience: graduate-level individual assignment (matches Multimodal). No leaderboard tab.
- Privacy: private at v1 (matches all live spaces).
- Brand: Luminex Learning master nav matching the digistore reference pattern. Inherits `memory/brand-architecture.md` and `memory/owasp-brand-policy.md`.

**Artifacts created (all 7 bootstrap files):**
- `spaces/data-poisoning/specs/overview_spec.md` (~12KB) — v1 scope, scenario, audience, attack/defense lists, success criteria, stack, phasing, risks
- `spaces/data-poisoning/specs/frontend_spec.md` (~13KB) — UI structure (4 tabs: Info / RAG Poisoning / Defenses / Corpus Browser), 8 Key Concepts cards, no-leaderboard pattern
- `spaces/data-poisoning/specs/api_spec.md` (~12KB) — 9 endpoints, defense_log contract shared with Multimodal, 10/min rate limit, doc upload validation
- `spaces/data-poisoning/specs/deployment_spec.md` (~8KB) — `cpu-basic` + Groq + sentence-transformers, Dockerfile with MiniLM prefetch, env vars, troubleshooting matrix
- `spaces/data-poisoning/CLAUDE.md` (~14KB) — space governance: reading order, attack list, defense list, security posture, NexaCore continuity, brand & identity, anti-hallucination rules
- `spaces/data-poisoning/docs/project-status.md` (~12KB) — Phase 0 tracker, implementation status table, 7 open risks, recommended next task (Phase 1)
- `spaces/data-poisoning/README.md` (~3KB) — HF Spaces card with frontmatter

**GitHub milestone issue:** **#22** filed via MCP.

**MCP push hiccup:** Initial push attempt (`d9bfb1a`) substituted literal `<<PLACEHOLDER>>` strings as file content via a tool-call template error. Recovered via 7 individual `create_or_update_file` calls (`cf8ee0f`, `f0f9657`, `5f6559e`, `f3caad3`, `87c2ae8`, `504952d`, `e95495e`). All 7 files now contain the real authored content; no data lost.

**Out of scope for this bootstrap:** any implementation code. Specs only, per CLAUDE.md "Creating a New Space" rules.

**Next phase:** Phase 1 — backend skeleton. Per platform CLAUDE.md, propose Phase 1 plan via Planner Agent and wait for approval before implementing.

---------------------------------------------------------------------

## Pending follow-up (cross-cutting)

- **OWASP Top 10 brand refresh** — separate CSS pipeline; deferred while space stays private (per `memory/owasp-brand-policy.md`). Required before going public.
- **Legacy space rename** — `nikobehar/llm-top-10`, `nikobehar/blue-team-workshop`, `nikobehar/red-team-workshop` → `nikobehar/ai-sec-lab<N>-<name>` per platform CLAUDE.md naming convention. URL change requires student communication; deferred.
- **Multimodal Phase 3.1** (issue #21) — defense quality fixes (widen ocr_prescan, replace confidence_threshold metric, strengthen boundary_hardening).
- **Multimodal v1.1 image regen** — P1.4 max_tokens budget bump; P5.5 rotated-margin moved to top/bottom.
- **Multimodal Phase 6** — Canvas LMS integration (autograde + score push). Cross-lab — affects all spaces with `POST /api/score`.
- **Brand & Identity reviewer findings** — issues #17, #18, #19, #20.
- **Data Poisoning Phase 1** (after approval) — backend skeleton per `spaces/data-poisoning/specs/`.
