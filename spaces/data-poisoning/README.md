---
title: Data Poisoning Lab
emoji: 📚
colorFrom: violet
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
short_description: RAG corpus poisoning attacks against an internal Q&A system
---

# Data Poisoning Lab

**Status:** Phase 0 (bootstrap) · **Hardware:** `cpu-basic` · **Tracking:** issue [#22](https://github.com/nbehar/ai-security-labs/issues/22)

Section of **AI Security Labs** under the **Luminex Learning** master brand. Workshop by Prof. Nikolas Behar.

## v1 scope

Single attack class: **RAG Poisoning (RP)** — 6 attacks anchored in the **NexaCore Knowledge Hub** scenario. Participants attack a small internal-Q&A RAG system by introducing poisoned documents into the retrieval corpus, then watch how those documents skew the LLM's responses to legitimate employee queries.

| ID | Attack |
|----|--------|
| RP.1 | Direct Injection — explicit canary instruction |
| RP.2 | Authority Spoof — "as approved by CISO..." |
| RP.3 | Outdated-Info Override — claims to supersede the trusted doc |
| RP.4 | Citation Spoof — fabricated citation chains |
| RP.5 | Embedding Adjacency — keyword stuffing for retrieval rank |
| RP.6 | Multi-Doc Consensus — 3 docs reinforce a false fact |

4 toggleable defenses: Provenance Check · Adversarial Filter · Retrieval Diversity · Output Grounding.

## Stack

- FastAPI + Uvicorn (Python 3.11+)
- LLM: Groq `llama-3.3-70b-versatile`
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` in-process
- Vector store: in-memory cosine similarity over numpy
- Frontend: vanilla HTML/CSS/JS, Luminex Learning master nav, AISL violet accent
- Deploy: HuggingFace Spaces, Docker, `cpu-basic`

## Specs

`specs/` directory:
- `overview_spec.md` — v1 scope, scenario, audience, success criteria
- `frontend_spec.md` — UI structure (4 tabs: Info / RAG Poisoning / Defenses / Corpus Browser)
- `api_spec.md` — 9 FastAPI endpoints + Pydantic schemas
- `deployment_spec.md` — hardware, models, Dockerfile, env vars

Plus `CLAUDE.md` for Claude-Code-driven space governance and `docs/project-status.md` for the build tracker.

## Audience

Graduate-level security students completing this Lab as an **individual assignment** in Prof. Behar's course. Per-student inline scoring (no leaderboard tab); scores will route to **Canvas LMS via API** in a future cross-lab phase.

## Status

This space is **in bootstrap** — specs are authored, no implementation code yet. See `docs/project-status.md` for the current phase, open risks, and recommended next task.

## Deploy

Once Phase 1 ships:
```bash
hf upload nikobehar/ai-sec-lab5-data-poisoning . --type=space
```

`GROQ_API_KEY` must be set as a HF Space secret. No `HF_TOKEN` required (this lab does not use HF Inference Providers).
