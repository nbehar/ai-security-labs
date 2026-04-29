# Project Status — AI Security Labs Platform

*Last updated: 2026-04-29 (Multimodal Phase 5 measured matrix verified + 4 reviewer-pass issues filed + Phase 3.1 issue filed + Data Poisoning Lab Phase 0 bootstrap + Phase 1 backend deployed)*

---------------------------------------------------------------------

## Platform Overview

Interactive AI security training platform by Prof. Nikolas Behar. **5 spaces with deployed code (1 product, 5 sections), 5 still-planned.** The monorepo is ONE Luminex Learning product — **AI Security Labs**. The individual spaces (`spaces/red-team/`, `spaces/blue-team/`, `spaces/multimodal/`, `spaces/owasp-top-10/`, `spaces/data-poisoning/`, plus the 5 still-planned ones) are **sections within AI Security Labs**, not standalone Luminex products. Every space uses the same Luminex Learning master nav (gold owl + "Luminex Learning" wordmark via alt) and the same AISL violet accent (`#a78bfa` highlight, `#7c3aed` interactive) for product-scoped UI; the section label varies (Red Team / Blue Team / Multimodal / OWASP Top 10 / Data Poisoning).

The standalone "Red Team Labs" / "Blue Team Labs" / "GRC Labs" mentioned in `~/luminex/brand-system/design-tokens.json` are separate Luminex products at the company level — not sections in this repo. See `~/.claude/projects/-Users-niko-ai-security-labs/memory/brand-architecture.md` for the canonical brand-architecture explainer; `~/.claude/projects/-Users-niko-ai-security-labs/memory/owasp-brand-policy.md` for the brand-before-public policy that governs the OWASP space refresh timing.

**Monorepo:** https://github.com/nbehar/ai-security-labs

---------------------------------------------------------------------

## Live Products

| # | Space | Status | Content | Hardware |
|---|-------|--------|---------|----------|
| 1 | `nikobehar/llm-top-10` | Running, private | OWASP 3-part workshop (25 attacks, 5 defenses, 3 pills). **Brand refresh pending** (separate CSS pipeline). Per `memory/owasp-brand-policy.md`, brand refresh required before going public. | CPU |
| 2 | `nikobehar/blue-team-workshop` | Running, private | **AI Blue Team / AI Security Labs** (Luminex brand, AISL violet). 6 tabs incl. Leaderboard. Master nav shipped 2026-04-29. | CPU |
| 3 | `nikobehar/red-team-workshop` | Running, private | **AI Red Team / AI Security Labs** (Luminex brand, AISL violet). 5 tabs incl. Leaderboard. Master nav shipped 2026-04-29. | CPU |
| 4 | `nikobehar/ai-sec-lab4-multimodal` | Running, private | **AI Security Labs / Multimodal** (Luminex brand). 4-tab SPA (Info / P1 / P5 / Defenses). Per-student inline scoring. Defenses tab serves Phase 5 measured matrix (output_redaction 10/10 · ocr_prescan 4/10 · boundary_hardening 0/10 + 2/10 deters · confidence_threshold 0/10 · all-four 9/10). | `cpu-basic` + HF Inference Providers (`Qwen/Qwen2.5-VL-72B-Instruct` via `ovhcloud`) |
| 5 | `nikobehar/ai-sec-lab5-data-poisoning` | **Phase 1 deployed** 2026-04-29; backend-only | **AI Security Labs / Data Poisoning** (Luminex brand). RAG corpus poisoning lab. Phase 1 ships placeholder shell + 4 API endpoints; full SPA in Phase 4b. RP.1 verified end-to-end (canary AURORA SAILBOAT leaked in 0.5s). Tracking issue #22. | `cpu-basic` + Groq `llama-3.3-70b-versatile` + sentence-transformers MiniLM-L6 |

### OWASP Top 10 Workshop (Space 1)
- 3 workshop pills (LLM Top 10 / MCP Top 10 / Agentic AI), 25 attacks, 5 defense tools.
- All 25 attacks verified against LLaMA 3.3 70B; defense matrix verified.
- **Brand status:** independent of `framework/` (separate CSS pipeline). Brand refresh deferred while space stays private (per `memory/owasp-brand-policy.md`); becomes a hard requirement before going public.

### AI Blue Team / Blue Team Workshop (Space 2)
- 4 of 4 challenges built (Prompt Hardening 5 levels / WAF Rules / Pipeline Builder / Behavioral Testing). Tested with zero false positives across 20 legitimate queries.
- **Brand:** Luminex master nav + "Blue Team / AI Security Labs". Bridge-cascade approach. See `spaces/blue-team/specs/architecture.md` Brand & Identity section.

### AI Red Team / Red Team Workshop (Space 3)
- Red Team Levels (5 hardened NexaCore systems, L1—L5) + Jailbreak Lab (15 techniques, effectiveness heatmap) + per-attempt Defense Log.
- **Brand:** Luminex master nav + "Red Team / AI Security Labs". RTL crimson `#e11d48` deliberately NOT used (NR-9). See `spaces/red-team/specs/architecture.md`.

### Multimodal Lab (Space 4)
- 4 tabs: Info / Image Prompt Injection / OCR Poisoning / Defenses (no leaderboard — graduate-individual assignment).
- 12 attacks (6 P1 visible-text + 6 P5 OCR-poisoning) anchored in NexaCore DocReceive scenario.
- **Phase 5 measured matrix (2026-04-29):** output_redaction 10/10 · ocr_prescan 4/10 · boundary_hardening 0/10 catches + 2/10 partial-deters · confidence_threshold 0/10. With all four enabled, 9/10 attacks block. n=72 cells; median 12.0s, p95 15.3s. Full data: `spaces/multimodal/docs/phase5-matrix-raw.json` (regen via `scripts/run_phase5_matrix.py`).
- **Brand:** Luminex Learning master nav (digistore Sidebar+Layout pattern). AISL violet accent.
- **Open:** Phase 3.1 defense quality fixes (issue #21) and v1.1 image regen for P1.4/P5.5.

### Data Poisoning Lab (Space 5 — Phase 1)
- **Phase 1 status (2026-04-29):** backend skeleton + Luminex master nav placeholder shell deployed. 4 endpoints live: `/`, `/health`, `/api/attacks`, `POST /api/attack` (canned mode only; defenses field accepted but Phase 3 enforces). slowapi 10/min/IP rate limit on `/api/attack`.
- 6 RP attacks defined (Direct Injection / Authority Spoof / Outdated-Info Override / Citation Spoof / Embedding Adjacency / Multi-Doc Consensus). Anchored in NexaCore Knowledge Hub scenario.
- Corpus: 6 legitimate NexaCore policy docs (Finance / IT / HR / Legal) + 8 poisoned attack docs (one per RP.1—RP.5; 3 sibling docs for RP.6 multi-doc consensus). `CorpusStore` lazy-loads MiniLM-L6, encodes all 14 docs at startup via `@app.on_event("startup")`, serves brute-force cosine top-k with deterministic tie-break.
- **Smoke (HF commit `7ab5e0b`):** RP.1 succeeded in 0.5s; canary AURORA SAILBOAT detected in response. Educational point lands: legit doc retrieves at higher cosine (0.732 vs 0.669) but LLM still complies with poisoned instructions — Phase 3 `output_grounding` defense will close this.
- **Brand:** Luminex Learning master nav (NexaCore / AI Security Labs left, shield + "Data Poisoning" right). NR-1 through NR-10 verified at write time.
- **Pending phases:** Phase 2 corpus expansion (6 → 15 legit docs); Phase 3 defenses (`defenses.py` with 4 layers); Phase 3 prep calibration; Phase 4a remaining endpoints (corpus / queries / scoring / upload); Phase 4b full SPA; Phase 5 defense matrix verification.

---------------------------------------------------------------------

## Shared Framework

| File | Lines | Purpose |
|------|-------|---------|
| `framework/static/css/styles.css` | 915 | Shared dark theme |
| `framework/static/js/core.js` | ~220 | DOM helpers, fetchJSON, render* helpers |
| `framework/scoring.py` | 55 | Score calculation + Leaderboard class |
| `framework/groq_client.py` | 25 | Groq API wrapper |
| `framework/templates/base.html` | 30 | Jinja2 HTML shell |

**Deploy:** `./scripts/deploy.sh <space-name>` copies framework → pushes to HF

Blue Team and Red Team use the shared framework (import from core.js). OWASP workshop is independent (not yet migrated). **Multimodal and Data Poisoning** use `escapeHtml`/`fetchJSON` from `core.js` but render their own SPA shells with Luminex tokens; they don't import `styles.css`.

**Luminex brand integration (post-2026-04-29):** Blue Team and Red Team retain framework `styles.css` unmodified; Luminex tokens are layered on top via space-local `luminex-bridge.css` + `luminex-nav.css`. Multimodal and Data Poisoning skip the bridge entirely (own CSS).

---------------------------------------------------------------------

## Planned Products (5 remaining)

| Priority | Space | Status | v1 Content | Hardware |
|----------|-------|--------|------------|----------|
| 5 | Detection & Monitoring | Planned | Log analysis, anomaly detection, output sanitization | CPU |
| 6 | Incident Response | Planned | AI breach simulation, containment, forensics | CPU |
| 7 | Multi-Agent Security | Planned | Multi-agent attack, cascading failures | CPU |
| 8 | Model Forensics | Planned | Backdoor detection, train your own guard, DP demo | TBD |
| 9 | AI Governance | Planned | Security policy writer, risk assessment, threat modeling | CPU |

---------------------------------------------------------------------

## GitHub Issues

### ai-security-labs repo

| # | Title | Status |
|---|-------|--------|
| 1-12 | (Spec/feature issues from Sessions 1-12) | Closed ✅ |
| 13 | Spec drift: Red Team L1-L5 system prompt framing | Closed ✅ (2026-04-28) |
| 14 | Spec gap: Educational features not in any spec | Closed ✅ (2026-04-28) |
| **15** | MILESTONE: Multimodal Security Lab v1 build | **Open** (filed 2026-04-27) — Phases 1+2+3+4a+4b+5 shipped; Phase 3.1 (#21) and v1.1 image regen remain. Phase 6 (Canvas) deferred. |
| 16 | Red Team L5 missing Guardrail Evaluation defense layer | Closed ✅ (2026-04-28) |
| **17** | Re-sync architecture.md Brand & Identity sections to digistore-pattern nav | **Open** (2026-04-29 reviewer pass) |
| **18** | needs-decision: does `alt="Luminex Learning"` satisfy NR-2? | **Open** (decision required) |
| **19** | Eliminate hardcoded color primitives (NR-8) — multimodal.css + framework/styles.css | **Open** |
| **20** | Pre-existing spec gaps: red-team / blue-team missing project-status.md; multimodal missing architecture.md | **Open** |
| **21** | Phase 3.1 defense quality fixes (multimodal): widen ocr_prescan, replace confidence_threshold, strengthen boundary_hardening | **Open** (filed from Phase 5 measured matrix) |
| **22** | MILESTONE: Data Poisoning Lab v1 build (priority #4) | **Open** — Phase 0 (bootstrap) + Phase 1 (backend skeleton) shipped; Phases 2/3/4a/4b/5 remain. |

### llm-top-10-demo repo (OWASP workshop)
- 31 issues total (12 closed, 19 open). Open issues cover slide improvements, tab restructure, export scorecard, defense in Custom Prompt, plus future lab issues.

---------------------------------------------------------------------

## Session History

### Sessions 1-12 (2026-04-06 to 2026-04-09 + Audit 2026-04-27)
[Full entries preserved in git history; summary: built OWASP Top 10 Workshop, then monorepo + framework + Blue Team Workshop (4 challenges) + Red Team Workshop (5 levels + Jailbreak Lab). QA fixes, educational enhancements. Issues #1-12 closed; #13 (Red Team spec drift) and #14 (educational layer not in specs) filed and resolved 2026-04-28.]

### 2026-04-28 — Multimodal Lab build (Phases 0-4a)
[Full entries preserved in git history; summary: bootstrap + Phase 1 backend + Phase 2 image library + ZeroGPU→HF Inference Providers pivot + Phase 1+2 deploy verify (Qwen2.5-VL-72B/ovhcloud) + Phase 3 defenses + Phase 4a full API surface.]

### 2026-04-29 — Multimodal Phase 4b (Luminex Learning SPA shell)
[Full entry preserved in git history; summary: 4-tab SPA shell with Luminex master nav, AISL violet accent, per-student inline scoring. XSS posture pivot to `Range.createContextualFragment`.]

### 2026-04-29 (cont.) — Brand refresh (red-team + blue-team) + nav pivots
[Full entries preserved in git history; summary: extended Luminex compliance to red-team / blue-team. After user clarification ("these are all AI labs"), architecture is ONE Luminex product (AI Security Labs), three sections. Bridge-layer cascade approach. Nav redesigned twice based on user-supplied brand screenshot + reference to digistore-mock-client `Sidebar.tsx`/`Layout.tsx`. Final layout: `[owl 48px gold] NexaCore / hairline / AI Security Labs … [shield] <Section>`.]

### 2026-04-29 (cont.) — Multimodal Phase 5 (measured defense matrix)
[Full entry preserved in git history; summary: 12 attacks × 6 conditions = 72 calls executed; output_redaction 10/10, ocr_prescan 4/10, boundary_hardening 0/10 + 2/10 deters, confidence_threshold 0/10. With all four on, 9/10 block. Latency p95 15.3s. Issue #15 progress comment + #21 filed for Phase 3.1 fixes.]

### 2026-04-29 (cont.) — Reviewer pass + 4 follow-up issues
[Full entry preserved in git history; summary: brand refresh accepted, no NR violations. 4 soft flags filed: #17 (spec drift), #18 (NR-2 needs-decision), #19 (hardcoded primitives), #20 (pre-existing gaps).]

### 2026-04-29 (cont.) — Data Poisoning Lab Phase 0 bootstrap (issue #22)
[Full entry preserved in git history; summary: 4 specs + CLAUDE.md + project-status + README authored. v1 scope locked: RAG Poisoning only (6 attacks). Stack: cpu-basic + Groq + sentence-transformers. MCP push hiccup (placeholder substitution mistake) recovered via 7 individual file pushes.]

### 2026-04-29 (cont.) — Data Poisoning Phase 1 (backend skeleton) DEPLOYED + verified

**Trigger:** User approval ("proceed and make sure to use brand-identity-enforcer when designing this space") after Phase 0 complete.

**What was built (10 files, individual MCP commits to avoid the Phase 0 placeholder hiccup):**

| File | Commit |
|---|---|
| `requirements.txt` | `bbc70ed` |
| `Dockerfile` | `056803d` |
| `.gitignore` | `e9f9ae8` |
| `attacks.py` | `33bfe87` |
| `corpus.py` | `6d8497c` |
| `rag_pipeline.py` | `b9cd7c4` |
| `app.py` | `2495a1e` |
| `templates/index.html` | `3447b11` |
| `static/css/data-poisoning.css` | `872fe44` |
| `static/css/luminex-tokens.css` | `3d12352` |

Plus space project-status.md update (`fcc0677`) and platform project-status.md update (this commit).

**Brand-identity-enforcer applied at write-time:** NR-1 owl in nav (48px, `.owl-gold` filter) · NR-2 "Luminex Learning" via `alt` text · NR-3 page bg `#09090f` via tokens · NR-4 NexaCore demoted to in-product fictional customer · NR-5 Inter + JetBrains Mono only · NR-10 owl always brand-gold.

**HF Space:** `nikobehar/ai-sec-lab5-data-poisoning` (private, Docker, cpu-basic) provisioned by user; `GROQ_API_KEY` Space secret set. `hf upload` shipped HF commit `7ab5e0b`.

**Smoke verification (against deployed Space):**

```
=== /health ===
{"groq_api_key_set":true, "embeddings_loaded":true, "attack_count":6, "corpus_size":14, "phase":1}

=== POST /api/attack RP.1 ===
succeeded=True  blocked_by=None  elapsed=0.5s
canary detected: AURORA SAILBOAT

top-k retrieval (deterministic):
  legitimate   0.732  fin-001-reimbursement-2025
  attack       0.669  rp1-poison
  legitimate   0.595  fin-002-travel-policy
```

**Educational observation:** legitimate doc actually retrieves at *higher* cosine similarity (0.732) than the poisoned doc (0.669). The retriever ranked correctly. **The model still complied with the poisoned instructions** because both docs are present in the LLM context and the LLM has no robust way to decide which is authoritative. Phase 3 `output_grounding` will close this; Phase 3 `provenance_check` will reject `rp1-poison` at ingestion.

**Latency:** 0.5s end-to-end (Groq is fast; embedding cache is warm post-startup).

**Pending follow-up:**
- Phase 2 — corpus expansion 6 → 15 legit docs (Phase 1 ships 6 to enable smoke)
- Phase 3 prep — calibration on RP.1—RP.6 against undefended baseline
- Phase 3 — defenses (`defenses.py` with 4 layers + wiring)
- Phase 4a — remaining endpoints (corpus / queries / scoring / leaderboard / upload)
- Phase 4b — full SPA shell (4 tabs)
- Phase 5 — defense matrix verification (6 × 6 = 36 cells)

---------------------------------------------------------------------

## Pending follow-up (cross-cutting)

- **OWASP Top 10 brand refresh** — separate CSS pipeline; deferred while space stays private (per `memory/owasp-brand-policy.md`).
- **Legacy space rename** — `nikobehar/llm-top-10`, `nikobehar/blue-team-workshop`, `nikobehar/red-team-workshop` → `nikobehar/ai-sec-lab<N>-<name>` per platform CLAUDE.md naming convention.
- **Multimodal Phase 3.1** (issue #21) — defense quality fixes.
- **Multimodal v1.1 image regen** — P1.4 max_tokens budget bump; P5.5 rotated-margin moved to top/bottom.
- **Multimodal Phase 6** — Canvas LMS integration (cross-lab).
- **Brand & Identity reviewer findings** — issues #17, #18, #19, #20.
- **Data Poisoning Phase 2 / 3 / 4 / 5** — see space-level project-status.md.
