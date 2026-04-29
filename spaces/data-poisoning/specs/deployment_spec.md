# Deployment Spec — Data Poisoning Lab

## Goal

Define the runtime: hardware tier, model + embedding choices, Dockerfile, environment variables, deploy mechanism. Locks the `cpu-basic` + Groq + sentence-transformers stack as the v1 reference.

## Hardware

- **HF Space tier:** `cpu-basic` (free; matches Multimodal Lab pattern post-ZeroGPU pivot)
- **RAM:** ~16 GB (default cpu-basic) — ample for MiniLM-L6 (90MB) + corpus embeddings (~23 × 384 floats × 4 bytes ≈ 35KB negligible) + FastAPI + slowapi
- **No GPU.** Embedding compute on CPU: encoding the seed docs at startup ≈ 1-2s. Per-query encode ≈ 10-30ms. LLM is hosted by Groq, not in-process.

## HF Space

- **Name:** `nikobehar/ai-sec-lab5-data-poisoning` (per platform CLAUDE.md naming convention starting from Lab 4)
- **SDK:** Docker
- **Visibility:** **private** at v1 (matches all other live spaces; per `memory/owasp-brand-policy.md`, going public requires the brand refresh + a curriculum sign-off)
- **Hardware:** `cpu-basic`
- **Sleep timeout:** default (172800s = 48h idle → sleep)

## Inference Stack

### LLM — Groq + LLaMA 3.3 70B

- **Provider:** Groq Cloud API
- **Model:** `llama-3.3-70b-versatile`
- **Wrapper:** Reuse `framework/groq_client.py` (vendored at deploy time per the framework-files-not-in-space-dirs pattern)
- **Why this model:** Consistency with red-team / blue-team / OWASP workshops. Same audience expectations, same response style. Fast (~1-3s for a typical RAG generation).

### Embeddings — sentence-transformers MiniLM-L6

- **Library:** `sentence-transformers>=2.5.0,<5.0.0`
- **Model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- **Why this model:** Standard educational embedding choice. Small (90MB download, instant load on CPU). Fast (10-30ms per encode on cpu-basic). Differentiates well between semantically distinct docs at corpus scale ≤30.
- **Env-overridable:** `EMBEDDING_MODEL` env var — operator can swap to `all-mpnet-base-v2` (768-dim, 5× larger, more accurate) if MiniLM-L6 turns out insufficient during defense matrix verification.

### Vector store — in-memory cosine similarity

- No FAISS / Qdrant / Pinecone dependency. Numpy array of shape `(N_docs, 384)` + per-query `np.dot` + argpartition for top-k.
- Trivial at corpus size ≤30; faster than spinning up FAISS for this scale.
- Pre-computed at startup; rebuilt only if `corpus.py` is reloaded (i.e., never in production).

## Dependencies

`requirements.txt`:

```
# Pinned with narrow major-version ranges to prevent breaking changes between
# rebuilds. `>=X,<Y` allows patch + minor security updates within the major
# but blocks API-breaking major bumps. Update intentionally with each phase.
fastapi>=0.110.0,<1.0.0
uvicorn[standard]>=0.27.0,<1.0.0
jinja2>=3.1.3,<4.0.0
python-multipart>=0.0.9,<1.0.0
pydantic>=2.6.0,<3.0.0
pillow>=10.2.0,<12.0.0          # only for the favicon, not used at runtime
sentence-transformers>=2.5.0,<5.0.0
numpy>=1.24.0,<3.0.0
groq>=0.4.0,<1.0.0               # the Groq Python SDK
slowapi>=0.1.9,<1.0.0
```

Note: `sentence-transformers` pulls in `torch` (CPU wheel ~200MB). Total Docker image size ≈ 1.2 GB. Comparable to Multimodal Lab post-Tesseract.

## Dockerfile

```dockerfile
FROM python:3.11-slim

# No apt deps needed at v1 — sentence-transformers + torch CPU wheels are self-contained.

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model into the image so cold-start doesn't fetch.
# Saves ~30s on first request post-Space-wake.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY . .

EXPOSE 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

The model-prefetch RUN line trades ~90MB image size for ~30s faster cold-start — worth it for workshop UX.

## Environment Variables

| Variable | Required | Set via | Notes |
|----------|----------|---------|-------|
| `GROQ_API_KEY` | yes | HF Space secret | Same key the OWASP / blue-team / red-team workshops use. Never commit, never log, never expose to frontend. |
| `EMBEDDING_MODEL` | no | HF Space secret or env | Default `sentence-transformers/all-MiniLM-L6-v2`. Override only if MiniLM-L6 underperforms during Phase 5. |
| `LLM_MODEL` | no | HF Space secret or env | Default `llama-3.3-70b-versatile`. Override for testing other Groq models (e.g., `llama-3.1-70b-versatile`). |

`HF_TOKEN` NOT required (this lab does not use HF Inference Providers — the LLM is via Groq, the embeddings run in-process).

## HF Space Metadata (`README.md` frontmatter)

```yaml
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
```

`short_description` ≤60 chars (HF requirement learned the hard way during Multimodal Lab deploy on 2026-04-28).

## Deploy Mechanism

Two paths:

### `./scripts/deploy.sh data-poisoning`

Standard platform deploy: copies `framework/static/css/styles.css`, `framework/static/js/core.js`, `framework/groq_client.py`, `framework/scoring.py` into `spaces/data-poisoning/{static,framework}/`, then `hf upload` the directory. The space-level `.gitignore` excludes the framework-copy paths so they don't drift in GitHub.

### Per-file `hf upload` (for incremental redeploys)

```bash
hf upload nikobehar/ai-sec-lab5-data-poisoning spaces/data-poisoning \
  --type=space \
  --include="static/css/data-poisoning.css" \
  --include="static/js/app.js" \
  --commit-message="Phase 4b: SPA shell"
```

Same pattern Multimodal Lab uses post-Phase 4. Faster than full `deploy.sh` for one-file iterations.

## Cold-Start Behavior

- **Space-wake from 48h idle:** ~10-30s for HF to spin up the Docker container.
- **Embedding model first-encode:** model is pre-downloaded into the image (Dockerfile RUN line above) but lazy-loads on first encode → ~1-2s on first `POST /api/attack` after container start. The Multimodal-Lab-style "warm at startup" pattern: encode the seed docs at app init so the first user request is hot.
- **Per `/api/attack`:** ~1-3s for Groq LLaMA + ~10-30ms embed. Well under the deployment_spec.md "10-20s typical" budget.

The frontend MUST display "Composing answer… (1-3s)" rather than the Multimodal Lab's "10-20s on the 72B model" — the latency profile is different here.

## Health Verification

Per platform CLAUDE.md "After deploy, Reviewer MUST verify":

```
curl -s -H "Authorization: Bearer $(cat ~/.cache/huggingface/token)" \
  https://nikobehar-ai-sec-lab5-data-poisoning.hf.space/health
```

Expected fields:
- `status: "ok"`
- `groq_api_key_set: true`
- `embedding_model: "sentence-transformers/all-MiniLM-L6-v2"`
- `llm_model: "llama-3.3-70b-versatile"`
- `attack_count: 6`
- `corpus_size: 14` at Phase 1 (6 legit + 8 attack — RP.6 ships as 3 sibling docs); `corpus_size: 23` post-Phase-2 (15 legit + 8 attack)
- `embeddings_loaded: true`
- `phase: <current phase number>`

If `groq_api_key_set: false`, the workshop is offline; user must add the Space secret. `embeddings_loaded: false` after ~5s post-startup indicates a model-load failure; check the Space logs.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| 503 from `/api/attack` with "embedding model not loaded" | MiniLM didn't load at startup | Restart Space; check logs for `OSError` |
| 503 from `/api/attack` with "Groq call failed" | `GROQ_API_KEY` missing or invalid | Re-add Space secret |
| 429 from `/api/attack` | 10/min/IP rate limit (slowapi) | Wait 1 minute; this is intentional |
| Corpus empty in `/api/corpus` | `corpus.py` import failed | Check Space logs for syntax errors |
| Cold-start >60s | First-image-pull on a freshly-restarted region | Normal; subsequent wakes are <30s |

## Acceptance Checks

- [ ] HF Space `nikobehar/ai-sec-lab5-data-poisoning` exists, private, Docker SDK, cpu-basic
- [ ] `GROQ_API_KEY` Space secret set
- [ ] `Dockerfile` matches the spec (slim Python 3.11 + model prefetch + standard FastAPI bootstrap)
- [ ] `requirements.txt` matches the spec (no extra deps; pinned versions)
- [ ] `/health` returns the expected JSON with all fields populated
- [ ] First `POST /api/attack` after fresh deploy completes in <5s (model warm via pre-download + startup encode)
- [ ] Subsequent `POST /api/attack` calls complete in <3s p95 (matches `frontend_spec.md` budget)
- [ ] `slowapi` 10/min/IP enforced (verify via 11th call returning 429)
