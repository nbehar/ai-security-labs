# Overview Spec — Data Poisoning Lab

## Goal

Teach OWASP LLM03 (Training Data Poisoning) and LLM04 (Data and Model Poisoning) through hands-on **RAG corpus poisoning** attacks. Participants attack a small NexaCore knowledge-base RAG system by introducing poisoned documents, then watch how those documents skew the model's responses to legitimate employee queries.

The pedagogical thesis: **the AI doesn't know which documents are trusted** — provenance and grounding are the security boundary, not the model itself. Defenses live at ingestion (provenance, adversarial filtering) and at retrieval (diversity, grounded citations), not inside the LLM.

## Scenario

**NexaCore Knowledge Hub** — internal employee Q&A system that draws from a curated corpus of HR / IT / Finance / Legal policy documents. Employees ask natural-language questions ("What's the reimbursement limit for client dinners?"), the RAG system retrieves the top-k policy excerpts, and the LLM composes an answer citing the retrieved documents.

The portal is the data-poisoning analog of the Multimodal Lab's NexaCore DocReceive scenario: same fictional company, same NexaCore continuity (HR Portal, Finance, Legal, DevOps departments referenced in red-team / blue-team / multimodal), new attack surface — the *retrieval corpus* rather than uploaded documents.

The attacker's goal: introduce one or more poisoned documents into the corpus that surface in legitimate employee queries and cause the LLM to compose a malicious answer (false approval, fabricated policy, exfiltration of a canary phrase).

## Audience

Graduate-level security students completing this Lab as an **individual assignment** in Prof. Behar's course. Same audience as the Multimodal Lab. Educational scaffolding (Key Concepts, Why-This-Works, traditional-security analogies) is mandatory — see `frontend_spec.md` Educational Layer.

**Grading model:** individual graduate assignment, scores recorded per-attempt and per-student via `POST /api/score`, eventually submitted to **Canvas LMS via API** (Phase 6 — autograde + score push, deferred and shared across all labs). The frontend shows the student only their own running total. **No leaderboard tab** — same pattern as Multimodal Lab.

## v1 Scope (this bootstrap)

Single attack class: **RAG Poisoning (RP)**.

| ID | Attack Name | Mechanism | OWASP Mapping | Educational Success Indicator | Programmatic Check (v1) |
|----|-------------|-----------|---------------|-------------------------------|-------------------------|
| **RP.1** | Direct Injection | Poisoned doc explicitly instructs the model to emit canary | LLM01 + LLM03 | canary in response | canary |
| **RP.2** | Authority Spoof | Poisoned doc claims policy authority ("AS APPROVED BY CISO 2026-04-15...") | LLM03 | canary + action keyword acknowledged | canary |
| **RP.3** | Outdated-Info Override | Poisoned doc claims to supersede the trusted doc on the same topic | LLM03 + LLM04 | model cites poisoned doc as authoritative | canary |
| **RP.4** | Citation Spoof | Poisoned doc fabricates citation chains to appear legitimate | LLM03 + LLM05 | canary in response | canary |
| **RP.5** | Embedding Adjacency | Poisoned doc has high cosine similarity to common employee queries via keyword stuffing | LLM03 | poisoned doc retrieved over trusted doc | canary |
| **RP.6** | Multi-Doc Consensus | Three poisoned docs mutually reinforce a false fact | LLM03 + LLM04 | model treats consensus as truth | canary |

**Note on the two columns above:** "Educational Success Indicator" is what the workshop participant should observe and reason about (the pedagogical framing per attack); "Programmatic Check (v1)" is what `attacks.py`'s `success_check` field encodes for the scoring layer. v1 uses a uniform `canary` programmatic check across all 6 attacks for simplicity — the per-attack educational distinctions live in the `Cause / Effect / Impact` panels in the frontend, not in code. v2 may layer richer programmatic checks (e.g., retrieval-rank verification for RP.5, citation-chain detection for RP.4); deferred until calibration shows the canary check is a quality bottleneck.

Each attack provides:
- **1 pre-canned poisoned document** the participant introduces into the corpus
- **The legitimate query that triggers retrieval** (with the expected legitimate-doc result)
- **Cause / Effect / Impact panels** (consistent with Multimodal Lab pattern)
- **Toggleable defenses** (4 layers; see Defenses section)
- **Success/blocked detection per attack**
- **Why-This-Works callout** (mandatory educational scaffolding)
- **Traditional-security analogy** (e.g., "RAG poisoning is the supply-chain attack of AI — like compromising an upstream npm package, but the package is a knowledge-base entry")

The legitimate corpus seeds with **15 NexaCore policy documents** (5 HR / 4 IT / 3 Finance / 3 Legal), each <500 words. Embeddings precomputed at startup using `sentence-transformers/all-MiniLM-L6-v2` (384-dim).

**Upload mode (advanced participants):** opt-in document upload. PDF/Markdown/plain-text only, ≤16KB, single document at a time, processed in-memory only. Per CLAUDE.md API safety rules.

## Defenses (v1)

Four toggleable defenses, mirroring the Multimodal Lab's Phase 5 defense matrix pattern:

| # | Defense | Type | Mechanism (one-line) |
|---|---------|------|----------------------|
| 1 | **Provenance Check** | Ingestion-side allowlist | Reject documents not from a curated `trusted_sources` list. Educational analog: code-signing for RAG corpus. |
| 2 | **Adversarial Filter** | Ingestion-side keyword/regex | Pre-scan ingested docs for injection patterns (`ignore prior`, `as approved by`, `auto-approve`, etc.). Cheap & deterministic. |
| 3 | **Retrieval Diversity** | Retrieval-side rerank | Penalize results from single-source clusters. Forces the model to see multiple perspectives, breaking single-doc poisoning. |
| 4 | **Output Grounding** | Generation-side constraint | Require the model to emit specific document IDs in its citations. Post-hoc check: every claim must trace to a doc. Catches the bare-claim hallucination + fabricated-citation classes. |

No single defense covers all 6 attacks — that's the educational point, mirroring the Multimodal Lab.

**Per CLAUDE.md anti-hallucination rule:** the catch-rate matrix is **design intent only** at v1 build time. Phase 5 verification (full 6 × 6 measured matrix against the deployed model) replaces design-intent claims with measured numbers before the lab is declared educationally honest. See Multimodal Lab Phase 5 (`spaces/multimodal/docs/phase3-calibration.md`) for the precedent and methodology.

## Out of Scope (v1)

| Class | Reason for v2+ |
|-------|----------------|
| Fine-Tuning Poisoning | Needs training-pipeline access — incompatible with API-served LLaMA via Groq. Would need a separate stack (PEFT + small model on GPU). |
| Synthetic Data Poisoning | Pedagogical overlap with RAG poisoning; the same supply-chain lesson applies. Defer for clarity. |
| Backdoor Detection | Different stack (model forensics) — covered by planned Lab 9 Model Forensics. |
| Membership Inference | Privacy-attack class; out of scope for a poisoning lab. |
| Prompt Injection (cross-modal) | Already covered by Multimodal Lab P1 + Red Team Jailbreak Lab. |

## Success Criteria

The Data Poisoning Lab v1 is "done" (per CLAUDE.md Definition of Done) when:

- All 6 RP attacks succeed against the undefended NexaCore RAG system (poisoned doc retrieved + LLM complies)
- All 12 legitimate queries return correctly (no false positives) across the recommended defense stack
- Defense matrix is **measured** (not just design-intent) — Phase 5 verification per Multimodal precedent
- Cold-start UX is documented (Space-wake ~10–30s; embedding compute on-startup ~1-2s)
- Educational layer complete (Key Concepts, Why-This-Works, analogies)
- Live on HF Space, **private**, accessible via workshop link
- Brand: Luminex Learning master nav (per `~/.claude/projects/-Users-niko-ai-security-labs/memory/brand-architecture.md`)

## Stack

- **Backend:** FastAPI + Uvicorn (Python 3.11+)
- **LLM:** LLaMA 3.3 70B via Groq API (consistency with red-team / blue-team / OWASP)
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim) — small, CPU-friendly, runs in-process via the `sentence-transformers` Python package
- **Vector store:** in-memory cosine similarity over numpy arrays (no FAISS dependency for v1; corpus size ≤30 docs makes brute-force retrieval trivial)
- **Frontend:** Vanilla ES6+ HTML/CSS/JS (consistent with platform; matches Multimodal Lab pattern)
- **Deploy:** Docker on HuggingFace Spaces, `cpu-basic`. **Required Space secret: `GROQ_API_KEY`.**
- **Theme:** Dark only — Luminex Learning brand (master nav with owl + Luminex Learning + AI Security Labs / Data Poisoning section, AISL violet accent)

## Acceptance Checks (bootstrap phase)

- [x] `spaces/data-poisoning/specs/overview_spec.md` exists (this file)
- [ ] `spaces/data-poisoning/specs/frontend_spec.md` exists
- [ ] `spaces/data-poisoning/specs/api_spec.md` exists
- [ ] `spaces/data-poisoning/specs/deployment_spec.md` exists
- [ ] `spaces/data-poisoning/CLAUDE.md` exists (modeled on `spaces/multimodal/CLAUDE.md`)
- [ ] `spaces/data-poisoning/docs/project-status.md` exists with bootstrap state
- [ ] `spaces/data-poisoning/README.md` updated to reflect v1 scope (currently has stale 2025 issue refs)
- [ ] GitHub milestone issue tracks v1 build (filed as **#22**)
- [ ] No implementation code yet — specs only
- [ ] Platform-level `docs/project-status.md` reflects data-poisoning bootstrap state (Planned Products row → "in bootstrap")

## What Could Go Wrong

| Risk | Mitigation |
|------|------------|
| RAG retrieval is non-deterministic across restarts | Pin embedding seeds; use deterministic top-k; sentence-transformers is deterministic given fixed input |
| MiniLM-L6 (384-dim) too small to differentiate attack vs benign | Tested standard for educational embeddings. If insufficient, escalate to `all-mpnet-base-v2` (768-dim). Keep model ID env-overridable via `EMBEDDING_MODEL`. |
| Corpus authoring takes long | Cap at 18 documents (6 attack + 12 legit); use AI-generated drafts then hand-edit; total <500 words each |
| Cold-start of embedding model | First-call ~2-3s to load MiniLM into memory; subsequent calls <10ms. Pre-warm by encoding the 15 legitimate docs at startup. |
| Single-doc poisoning works too easily — workshop becomes 6×"add doc, see it succeed" | RP.5 / RP.6 (embedding adjacency / multi-doc consensus) explicitly require attacker craft; RP.3 (outdated info) requires reasoning about which doc the model trusts. The pedagogical gradient is built into the attack list. |
| Groq API rate limit at workshop scale | Same risk as red-team / blue-team. 30 students × 6 attacks × maybe 5 retries = ~900 calls per session; well within Groq Pro quotas. Add `slowapi` 10/min/IP rate limit on `/api/attack` (matches Multimodal Lab Phase 4a) |
| Brand drift / NR-4 risk on "NexaCore Knowledge Hub" | NexaCore is an in-product fictional target; explicitly NOT a Luminex brand name. Per `memory/brand-architecture.md`, the master nav reads "Data Poisoning / AI Security Labs", not "NexaCore Knowledge Hub". |

## Phasing (informational — issue #22 tracks the milestone)

| Phase | Deliverable |
|---|---|
| 0 — Bootstrap | This file + 3 other specs + CLAUDE.md + docs/project-status.md + README + milestone issue |
| 1 — Backend skeleton | `app.py`, `attacks.py`, `corpus.py`, `rag_pipeline.py`, Dockerfile, requirements.txt — minimum to run RP.1 against an undefended corpus |
| 2 — Pre-canned corpus | 6 poisoned docs + 12-15 legitimate NexaCore docs; embedding precompute at startup |
| 3 — Defenses | `defenses.py` (4 layers); `app.py` defense wiring; defense_log shape |
| 4a — API surface | `/api/score`, `/api/leaderboard`, `/api/corpus/{doc_id}`, `/api/queries` (the 6 legitimate queries the attacks target), document upload mode, slowapi rate limit, Postman collection |
| 4b — SPA shell | 4-tab Luminex-branded SPA (Info / RAG Poisoning / Defenses / Per-student score) |
| 5 — Defense matrix verification | Phase 5-style measured matrix (6 × 6 = 36 cells); calibration writeup |
| 6 — Canvas LMS integration | Cross-lab — covered by future platform-level Phase 6 |

## NexaCore continuity

This space participates in the NexaCore fictional-company universe. The Knowledge Hub is consistent with NexaCore's existing departments (HR, Finance, Legal, DevOps) referenced in red-team / blue-team / multimodal. Pre-canned legitimate documents reference NexaCore policies (expense reimbursement, badge provisioning, contractor onboarding) without inventing new departments.

Per CLAUDE.md, Claude MUST NOT:
- Invent NexaCore departments not described in this spec
- Use real company names or real policy documents as attack examples
- Rename "Knowledge Hub" without updating all 4 specs + CLAUDE.md
