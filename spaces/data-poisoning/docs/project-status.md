# Data Poisoning Lab — Project Status

*Last updated: 2026-04-29 (Phase 0 / Bootstrap complete; specs authored; awaiting approval to start Phase 1)*

------------------------------------------------------------------------

## Current Phase

**Phase 0 (Bootstrap) complete.** All 4 specs + space CLAUDE.md + this file authored 2026-04-29 in response to the user's "build out the next lab" direction during the Phase 5 close-out of the Multimodal Lab. GitHub milestone issue **#22** filed via MCP.

No implementation code yet. Per platform CLAUDE.md, Phase 1 (backend skeleton) requires explicit approval before code lands.

------------------------------------------------------------------------

## Bootstrap Checklist

- [x] `spaces/data-poisoning/specs/overview_spec.md` — v1 scope, scenario, audience, success criteria
- [x] `spaces/data-poisoning/specs/frontend_spec.md` — UI structure, 4 tabs, educational scaffolding
- [x] `spaces/data-poisoning/specs/api_spec.md` — 9 FastAPI endpoints + Pydantic schemas
- [x] `spaces/data-poisoning/specs/deployment_spec.md` — `cpu-basic` + Groq + sentence-transformers stack
- [x] `spaces/data-poisoning/CLAUDE.md` — space governance modeled on `spaces/multimodal/CLAUDE.md`
- [x] `spaces/data-poisoning/docs/project-status.md` (this file)
- [x] `spaces/data-poisoning/README.md` updated with v1 frontmatter
- [x] GitHub milestone issue tracking v1 build (#22)
- [ ] Platform-level `docs/project-status.md` Planned Products row updated to "in bootstrap"

------------------------------------------------------------------------

## v1 Scope (locked in 2026-04-29 bootstrap)

| Decision | Value |
|----------|-------|
| Hardware | HF Spaces `cpu-basic` (free) |
| LLM | Groq `llama-3.3-70b-versatile` (consistency with red-team / blue-team / OWASP) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` in-process |
| Vector store | in-memory cosine similarity over numpy (no FAISS at v1) |
| Attack class | RAG Poisoning (RP) — 6 attacks, single class for v1 clarity |
| Scenario | NexaCore Knowledge Hub (internal Q&A portal) |
| Corpus | 15 legitimate NexaCore policy docs + 6 pre-canned poisoned attack docs (21 total) |
| Document upload | Opt-in, PDF / Markdown / plain text only, ≤16KB, in-memory only |
| External APIs | Groq only (no HF Inference Providers, no Together / Replicate) |
| Brand | Luminex Learning master nav + AI Security Labs / Data Poisoning section (per `memory/brand-architecture.md`) |
| Privacy | Private at v1 (matches all other live spaces) |

------------------------------------------------------------------------

## Implementation Status

| Component | Status | Phase |
|-----------|--------|-------|
| Specs (4 of 4) | ✅ Complete | Bootstrap |
| Space-level CLAUDE.md | ✅ Complete | Bootstrap |
| GitHub milestone issue (#22) | ✅ Filed | Bootstrap |
| Space-level project-status.md | ✅ Complete (this file) | Bootstrap |
| `README.md` | ✅ Complete (HF Spaces card with frontmatter) | Bootstrap |
| Platform `docs/project-status.md` row | ⬜ Pending — Planned Products row #4 still says "Planned" | Bootstrap |
| `requirements.txt` | ⬜ Not started | Phase 1 |
| `Dockerfile` | ⬜ Not started | Phase 1 |
| `attacks.py` (6 RP defs) | ⬜ Not started | Phase 1 |
| `corpus.py` (loader + embedding precompute) | ⬜ Not started | Phase 1 |
| `rag_pipeline.py` (embed → retrieve → generate) | ⬜ Not started | Phase 1 |
| `app.py` (3 endpoints — /, /health, /api/attacks, /api/attack canned-only) | ⬜ Not started | Phase 1 |
| 21 corpus documents (15 legit + 6 attack) | ⬜ Not started | Phase 2 |
| HF Space created (`nikobehar/ai-sec-lab5-data-poisoning`, private, Docker, cpu-basic) | ⬜ Not started | Phase 1+2 |
| Phase 1+2 deploy verification | ⬜ Not started | Phase 1+2 |
| `defenses.py` (4 defenses) | ⬜ Not started | Phase 3 |
| `app.py` defense wiring + form-field validation | ⬜ Not started | Phase 3 |
| 6-attack baseline run vs LLaMA 3.3 70B (Phase 3 prep / calibration) | ⬜ Not started | Phase 3 prep |
| `GET /api/corpus`, `/api/corpus/{id}`, `/api/queries` routes | ⬜ Not started | Phase 4a |
| `POST /api/attack` upload mode | ⬜ Not started | Phase 4a |
| `POST /api/score` + in-memory leaderboard schema | ⬜ Not started | Phase 4a |
| `GET /api/leaderboard` route | ⬜ Not started | Phase 4a |
| `slowapi` 10/min rate limit on `/api/attack` | ⬜ Not started | Phase 4a |
| Postman collection (9 endpoints + 2 negative probes) | ⬜ Not started | Phase 4a |
| Frontend SPA (4 tabs: Info / RAG Poisoning / Defenses / Corpus Browser) | ⬜ Not started | Phase 4b |
| Defense matrix verification (6 attacks × 6 conditions = 36 cells) | ⬜ Not started | Phase 5 |
| Canvas LMS integration | ⬜ Not started | Phase 6 (cross-lab) |

------------------------------------------------------------------------

## Open Risks

1. **MiniLM-L6 (384-dim) too small to differentiate attack vs benign at this corpus size.** Resolution: Phase 3 prep calibration run will measure cosine similarity for each (attack, target query) pair. If MiniLM-L6 underperforms (poisoned doc consistently ranks below trusted on legitimate queries — the OPPOSITE of what we want for the educational point), escalate to `all-mpnet-base-v2` (768-dim). Embedding model is env-overridable per `deployment_spec.md`.
2. **RAG retrieval determinism.** sentence-transformers is deterministic given pinned input + model. Pinning `numpy` random seeds for argpartition tie-breaking. If non-determinism shows up in smoke testing, switch to deterministic top-k (sort by score then doc_id).
3. **Corpus authoring time.** 21 documents at ~400 words each = ~8K words to author. Two-phase strategy: (a) AI-generate drafts using Claude in-session, (b) hand-edit for NexaCore continuity + factual coherence. Cap at 18 docs if 21 is too much; the educational point holds at 12+6.
4. **Groq rate limit at workshop scale.** Same risk as red-team / blue-team. 30 students × 6 attacks × 5 retries = ~900 calls per session; well within Groq Pro quotas. slowapi 10/min/IP backstop catches anyone in a stuck retry loop.
5. **Cold-start of MiniLM model.** ~2-3s first encode after container start. Mitigation in `deployment_spec.md` Dockerfile: pre-download the model into the image at build time, then warm-encode the 15 seed docs at app init so the first user request is hot.
6. **Defense matrix may be lopsided** (similar to Multimodal where output_redaction did 10/10 and the others 0-4/10). The 4 RP defenses are designed to catch DIFFERENT attack subsets — provenance catches RP.4 (citation spoof), adversarial filter catches RP.1/RP.2 (explicit injection wording), retrieval diversity catches RP.5 (embedding adjacency) + RP.6 (multi-doc consensus), output grounding catches RP.3 (outdated info override) + RP.4 (citation spoof). If Phase 5 measures show 1 defense doing all the work, the educational layer should reframe rather than the design (consistent with Multimodal lessons learned).
7. **Brand consistency.** Per `memory/brand-architecture.md`, this space inherits the Luminex Learning master brand pattern from Multimodal Lab. If the brand pattern shifts before Phase 4b ships, Data Poisoning needs to follow the new pattern. If it ships during a stable window (which is the current expectation), no risk.

------------------------------------------------------------------------

## Next Recommended Task

**Phase 1 — Backend skeleton.** Per `specs/api_spec.md` + `specs/deployment_spec.md`:

- `requirements.txt` — fastapi, uvicorn, jinja2, python-multipart, pydantic, sentence-transformers, numpy, groq, slowapi, pillow (for favicon only)
- `Dockerfile` — Python 3.11-slim + sentence-transformers MiniLM-L6 prefetch + standard FastAPI bootstrap
- `attacks.py` — 6 RP attack definitions with poisoned-doc bodies, target queries, canary phrases (12 distinct two-word canaries to match the Multimodal pattern)
- `corpus.py` — load 15 legitimate docs (Phase 2 work — initial Phase 1 ships 3-5 stub docs to enable end-to-end smoke), embed at startup, expose `get_top_k(query_embedding, k)` retrieval helper
- `rag_pipeline.py` — `compose_answer(query, docs, defenses) -> AttackResponse` orchestration
- `app.py` — minimum 3 endpoints: `/`, `/health`, `/api/attacks`, `POST /api/attack` (canned-only mode)
- `templates/index.html` — Phase 1 placeholder shell (replaced in Phase 4b)
- `static/css/data-poisoning.css` — empty stub
- HF Space provisioning: user creates `nikobehar/ai-sec-lab5-data-poisoning` (private, Docker SDK, cpu-basic), adds `GROQ_API_KEY` Space secret
- `hf upload` deploy
- Smoke verification: `/health` returns 200, `POST /api/attack attack_id=RP.1` returns 200 with the canary leaked end-to-end

Per platform CLAUDE.md, propose Phase 1 plan via Planner Agent and wait for approval before implementing.

**Optionally first — Phase 3 prep (calibration).** Run RP.1 — RP.6 against an undefended baseline once Phase 1+2 deploys, measure how often the poisoned doc retrieves vs trusted, and whether the LLM consistently emits the canary. Same pattern as Multimodal Lab Phase 3 prep. Drives the v1 catch-rate verification baseline.

------------------------------------------------------------------------

## Session History

### 2026-04-29 — Bootstrap (Phase 0)

**Trigger:** User direction during the Phase 5 close-out of the Multimodal Lab. Asked to start the next planned space (priority #4 in platform CLAUDE.md Planned Products list).

**Decisions locked in (planning before any code):**

- Hardware: HF Spaces `cpu-basic` (free; matches Multimodal post-ZeroGPU pivot)
- LLM: Groq LLaMA 3.3 70B (consistency with the 3 other Groq-backed live spaces)
- Embeddings: sentence-transformers MiniLM-L6, in-process (env-overridable)
- v1 scope: RAG poisoning only — 6 attacks, single attack class (fine-tuning + synthetic data deferred to v2)
- Scenario: NexaCore Knowledge Hub (data-poisoning analog of Multimodal's NexaCore DocReceive)
- Audience: graduate-level individual assignment (matches Multimodal Lab framing)
- Privacy: private at v1
- Brand: Luminex Learning master nav (digistore Sidebar + Layout pattern) — inherits the brand-architecture.md memory entry from Multimodal

**Artifacts created:**

- `spaces/data-poisoning/specs/overview_spec.md` (~9KB)
- `spaces/data-poisoning/specs/frontend_spec.md` (~7KB)
- `spaces/data-poisoning/specs/api_spec.md` (~9KB)
- `spaces/data-poisoning/specs/deployment_spec.md` (~5KB)
- `spaces/data-poisoning/CLAUDE.md` (~7KB)
- `spaces/data-poisoning/docs/project-status.md` (this file)
- `spaces/data-poisoning/README.md` (HF Spaces card)
- GitHub milestone issue **#22** filed via MCP (https://github.com/nbehar/ai-security-labs/issues/22)

**Out of scope for this bootstrap:** any implementation code. Specs only, per CLAUDE.md "Creating a New Space" rules.

**Note (2026-04-29):** Initial push commit (`d9bfb1a`) accidentally pushed literal `<<PLACEHOLDER>>` strings as file contents (an MCP tool-call template substitution mistake — the placeholders were left in instead of expanded with file bytes). The 7 files were re-pushed with real content via individual `create_or_update_file` calls (commits `cf8ee0f`, `f0f9657`, `5f6559e`, `f3caad3`, `87c2ae8`, this one, and the README fix). All 7 files now contain real content; no data lost.

**Pending follow-up:**

- Update platform `/docs/project-status.md` Planned Products row #4 ("Planned" → "in bootstrap")
- After approval: Phase 1 backend skeleton
