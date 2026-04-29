# CLAUDE.md — Data Poisoning Lab

This file is the space-level governance for `spaces/data-poisoning/`. The platform-level `/CLAUDE.md` at the repo root applies in addition; this file scopes platform rules to this space and adds anything specific to data-poisoning work.

------------------------------------------------------------------------

# Project Purpose

The Data Poisoning Lab is the AI Security Labs platform's workshop for **RAG corpus poisoning attacks**. Participants attack a small NexaCore knowledge-base RAG system by introducing poisoned documents into the retrieval corpus, then watch how those documents skew the LLM's responses to legitimate employee queries.

**v1 scope:** 1 attack class (RP — RAG Poisoning) with 6 attacks anchored in the **NexaCore Knowledge Hub** scenario. Single-corpus, single-LLM stack (Groq LLaMA 3.3 70B + sentence-transformers MiniLM-L6 embeddings).

The repository — not conversation history — is the system of record.

------------------------------------------------------------------------

# Reading Order (Space-Level)

When working in this space, Claude MUST read in this order:

1. Platform `/CLAUDE.md`
2. Platform `/docs/project-status.md`
3. This file (`spaces/data-poisoning/CLAUDE.md`)
4. `spaces/data-poisoning/specs/overview_spec.md`
5. `spaces/data-poisoning/specs/frontend_spec.md`
6. `spaces/data-poisoning/specs/api_spec.md`
7. `spaces/data-poisoning/specs/deployment_spec.md`
8. `spaces/data-poisoning/docs/project-status.md`

Plus relevant memory entries:
- `~/.claude/projects/-Users-niko-ai-security-labs/memory/brand-architecture.md` — all spaces in this monorepo are sections within AI Security Labs (one Luminex product, AISL violet)
- `~/.claude/projects/-Users-niko-ai-security-labs/memory/owasp-brand-policy.md` — brand-before-public policy

------------------------------------------------------------------------

# Repository Structure (this space)

```
spaces/data-poisoning/
  app.py                    FastAPI routes + RAG attack orchestration (Phase 1 — TO BE BUILT)
  attacks.py                6 RP attack definitions (Phase 1 — TO BE BUILT)
  corpus.py                 Corpus loader + embedding precompute (Phase 1 — TO BE BUILT)
  rag_pipeline.py           Embed → retrieve → generate (Phase 1 — TO BE BUILT)
  defenses.py               4 defense layers (Phase 3 — TO BE BUILT)
  Dockerfile                cpu-basic + Python deps (Phase 1 — TO BE BUILT)
  requirements.txt          fastapi, sentence-transformers, groq, slowapi, etc. (Phase 1 — TO BE BUILT)
  README.md                 HF Spaces card with frontmatter (bootstrap pending — currently has stale 2025 issue refs)
  CLAUDE.md                 This file (Phase 0 — bootstrap ✅)
  .gitignore                Vendored framework copies + brand assets (Phase 1)
  specs/
    overview_spec.md        v1 scope, scenario, audience, success criteria (Phase 0 ✅)
    frontend_spec.md        UI structure, 4 tabs, educational scaffolding (Phase 0 ✅)
    api_spec.md             FastAPI endpoints + Pydantic schemas (Phase 0 ✅)
    deployment_spec.md      Hardware, models, Dockerfile, env vars (Phase 0 ✅)
  docs/
    project-status.md       Space-level status tracker (Phase 0 ✅)
  static/
    owl.svg                 Vendored Luminex brand mark (Phase 4b — gitignored, copied from ~/luminex/)
    css/
      luminex-tokens.css    Vendored from ~/luminex/brand-system/design-tokens.json (Phase 4b)
      luminex-bridge.css    Maps framework styles vars → Luminex tokens (Phase 4b)
      luminex-nav.css       Master nav (Phase 4b)
      data-poisoning.css    Space-specific styles (Phase 4b)
      styles.css            Framework copy (Phase 4b — gitignored)
    js/
      app.js                SPA entry, tab routing, /health probe (Phase 4b — TO BE BUILT)
      attack_runner.js      RAG Poisoning tab renderer (Phase 4b — TO BE BUILT)
      corpus_browser.js     Corpus Browser tab renderer (Phase 4b — TO BE BUILT)
      document_upload.js    Doc upload + validation (Phase 4b — TO BE BUILT)
      core.js               Framework copy (Phase 4b — gitignored)
  templates/
    index.html              4-tab SPA shell with Luminex master nav (Phase 4b — TO BE BUILT)
  postman/
    data-poisoning-lab.postman_collection.json   API testing contract (Phase 4a)
```

------------------------------------------------------------------------

# Stack

- **Backend:** FastAPI + Uvicorn (Python 3.11+)
- **Frontend:** Vanilla ES6+ HTML/CSS/JS — no framework, no build step (consistent with platform; Multimodal Lab pattern)
- **LLM:** `llama-3.3-70b-versatile` via Groq API (consistency with red-team / blue-team / OWASP)
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` in-process (env-overridable via `EMBEDDING_MODEL`)
- **Vector store:** in-memory cosine similarity over numpy (no FAISS dependency at v1; corpus ≤30 docs)
- **Deploy:** Docker on HuggingFace Spaces, hardware tier `cpu-basic` (free)
- **Theme:** Dark only — Luminex Learning brand. Master nav (owl + NexaCore / AI Security Labs + shield + "Data Poisoning") matches the digistore reference pattern shipped to red-team / blue-team / multimodal.

This space uses Groq, NOT HF Inference Providers. The Multimodal Lab uses HF Inference Providers because Qwen2.5-VL-72B isn't on Groq; LLaMA 3.3 70B is, so we follow the cheaper / consistent path here.

------------------------------------------------------------------------

# Spec-First Development (Reinforces Platform Rule)

1. The 4 specs in `spaces/data-poisoning/specs/` are authoritative.
2. New attacks (beyond v1's 6) require a spec entry in `overview_spec.md` + an `attacks.py` definition.
3. Defense additions require an `overview_spec.md` defense matrix update.
4. UI changes require a `frontend_spec.md` update before code.
5. API changes require an `api_spec.md` update + a Postman collection update.
6. Deployment/hardware changes require a `deployment_spec.md` update.

**If code disagrees with spec → code is wrong** (platform rule, restated for clarity).

------------------------------------------------------------------------

# Attack List (v1)

| ID | Name | Mechanism | OWASP | Success Check |
|----|------|-----------|-------|---------------|
| **RP.1** | Direct Injection | Poisoned doc explicitly instructs the model to emit canary | LLM01 + LLM03 | canary in response |
| **RP.2** | Authority Spoof | Poisoned doc claims policy authority ("AS APPROVED BY CISO 2026-04-15...") | LLM03 | canary + action keyword |
| **RP.3** | Outdated-Info Override | Poisoned doc claims to supersede the trusted doc on the same topic | LLM03 + LLM04 | model cites poisoned doc as authoritative |
| **RP.4** | Citation Spoof | Poisoned doc fabricates citation chains to appear legitimate | LLM03 + LLM05 | canary in response |
| **RP.5** | Embedding Adjacency | Poisoned doc has high cosine similarity to common queries via keyword stuffing | LLM03 | poisoned doc retrieved over trusted doc |
| **RP.6** | Multi-Doc Consensus | Three poisoned docs mutually reinforce a false fact | LLM03 + LLM04 | model treats consensus as truth |

Exact poisoned-document content + system prompts + canary phrases per attack are defined in `attacks.py` ✅ once Phase 1 ships, sourced from `overview_spec.md` + per-attack mini-specs.

------------------------------------------------------------------------

# Defense List (v1)

| # | Defense | Implementation File |
|---|---------|---------------------|
| 1 | Provenance Check | `defenses.py` (allowlist of trusted source URIs) |
| 2 | Adversarial Filter | `defenses.py` (regex/keyword pre-scan on ingested docs) |
| 3 | Retrieval Diversity | `defenses.py` (rerank to penalize single-source clusters) |
| 4 | Output Grounding | `defenses.py` (post-LLM check that every claim cites a real doc) |

Defense effectiveness matrix lives in `overview_spec.md` (design-intent at v1 build time, replaced with measured numbers after Phase 5 verification — same pattern as Multimodal Lab).

------------------------------------------------------------------------

# Security Posture (Space-Specific)

The platform-level "Intentionally Vulnerable" rule applies. Specific to data-poisoning:

- The RAG system MUST be deployed without input-side defenses on by default — we want corpus poisoning to succeed undefended for the educational point
- Document uploads MUST be validated (PDF / Markdown / plain text only, ≤16KB, magic-bytes / format check)
- Document content is processed in-memory only — never persisted to disk, never added to the long-term corpus
- The pre-canned poisoned-doc library is part of the workshop content; review for content appropriateness, but the *attack* content is the educational point
- `GROQ_API_KEY` MUST NOT be committed; set as HF Space secret
- No `HF_TOKEN` required — this lab does not use HF Inference Providers

------------------------------------------------------------------------

# Hosting Constraints (HuggingFace Spaces — cpu-basic + Groq + in-process embeddings)

Per `deployment_spec.md`:
- Hardware: `cpu-basic` (free; the Space is a thin FastAPI orchestrator + small embedding model)
- LLM: Groq Cloud API (`llama-3.3-70b-versatile`)
- Embeddings: sentence-transformers MiniLM-L6, in-process, ~90MB model pre-downloaded into Docker image at build time
- Cold-start: ~10–30s on Space-wake (Docker container start), then 1–3s per attack (Groq + embed)
- Required Space secret: `GROQ_API_KEY`
- No GPU on the Space, no in-process LLM load

------------------------------------------------------------------------

# Anti-Hallucination Rules

Claude MUST NOT:
- Invent attack scenarios not in `overview_spec.md`
- Claim a defense behavior without testing it (Phase 5 verification per Multimodal Lab precedent — measured > design-intent)
- Add an attack to the UI without a spec entry
- Document a defense as "catches X" without verifying against the actual deployed model
- Invent NexaCore departments not in the existing fictional universe (HR / IT / Finance / Legal / DevOps are established; new departments require a NexaCore continuity update across all spaces)

If uncertain about RAG behavior → run a test against the deployed Space before claiming a result in code or specs.

------------------------------------------------------------------------

# NexaCore Continuity

This space participates in the platform-wide NexaCore fictional-company scenario. The Knowledge Hub is fictional but realistic and consistent with NexaCore's existing departments referenced in red-team / blue-team / multimodal.

Claude MUST NOT:
- Invent NexaCore departments not described in `overview_spec.md`
- Use real company names or real policy templates as attack examples
- Rename "Knowledge Hub" without updating all 4 specs + this file
- Use "NexaCore" or "NexaCore Technologies" as a Luminex brand name in nav copy (NR-4 — NexaCore is the in-product fictional target; the Luminex product is "AI Security Labs" and the section is "Data Poisoning")

------------------------------------------------------------------------

# Brand & Identity

This space ships under the **Luminex Learning** master brand as the "Data Poisoning" section within **AI Security Labs**. Per `~/.claude/projects/-Users-niko-ai-security-labs/memory/brand-architecture.md`:

- Master nav: `[owl 48px gold] NexaCore / hairline / AI Security Labs … [shield] Data Poisoning` — matches the digistore Sidebar.tsx + Layout.tsx reference
- Page title: `Data Poisoning · AI Security Labs · Luminex Learning`
- AISL violet accent (`--color-accent-aisl-highlight #a78bfa`, `--color-accent-aisl-interactive #7c3aed`) for active tabs and primary CTAs
- Brand gold (`#fbbf24`) reserved for the master nav owl + wordmark filter
- Page background: `#09090f` / `--color-bg-base` (NR-3)
- Inter + JetBrains Mono fonts only (NR-5); no DM Serif Display in product UI
- Vendored: `static/owl.svg` (gitignored), `static/css/luminex-tokens.css` (committed), `static/css/luminex-bridge.css`, `static/css/luminex-nav.css`

Full Brand & Identity section will be added to `specs/architecture.md` if the space gets one (currently consolidated in `frontend_spec.md`).

------------------------------------------------------------------------

# Current Status

**Phase 0 (Bootstrap) complete** as of 2026-04-29. Specs authored, GitHub milestone issue **#22** filed, space directory scaffolded. No implementation code yet.

**Workshop usage:** Individual graduate-course assignments (not competitive). Phase 4b will ship 4 tabs (Info / RAG Poisoning / Defenses / Corpus Browser) — no leaderboard tab. The `POST /api/score` and `GET /api/leaderboard` backend endpoints will preserve for the eventual **Phase 6: Canvas LMS integration** (autograde + score push).

**Next phase:** Phase 1 — backend skeleton (`app.py`, `attacks.py`, `corpus.py`, `rag_pipeline.py`, Dockerfile, requirements.txt). Per platform CLAUDE.md, propose Phase 1 plan via Planner Agent and wait for approval before implementing.

See `docs/project-status.md` for active task and next steps.

------------------------------------------------------------------------

# Default Startup Behavior (When Working in This Space)

1. Read platform `/CLAUDE.md`
2. Read this file
3. Read all 4 specs
4. Read `docs/project-status.md`
5. Read relevant memory entries (brand-architecture.md, owasp-brand-policy.md)
6. Check `app.py`/`attacks.py`/etc. existence to know if we're in Bootstrap, Build, or Maintenance phase
7. Propose next task per spec-first rules

Claude MUST NOT begin implementation automatically — wait for approval per platform Plan Mode rules.
