# Deployment Spec — Multimodal Security Lab

## Goal

Define hosting, hardware, model loading, env config, and verification for deploying the Multimodal Lab as a HuggingFace Space.

## Hosting

- **Platform:** HuggingFace Spaces
- **SDK:** Docker (consistent with other spaces)
- **Hardware tier:** **`cpu-basic`** (free)
- **Visibility:** Private (consistent with other spaces — workshop access controlled via HF Space link)
- **HF Space name:** `nikobehar/ai-sec-lab4-multimodal` (per platform `ai-sec-lab#-name` convention; this is the 4th workshop deployed)
- **Inference path:** HuggingFace Inference Providers (Together AI by default), called via `huggingface_hub.InferenceClient`. Vision inference is *hosted* — no GPU on the Space itself, no local model load, no cold-start.

### Why not ZeroGPU

The 2026-04-27 plan assumed ZeroGPU + a locally loaded Qwen2.5-VL-7B. Discovered at Space creation time that **HF Spaces only allow ZeroGPU on Gradio SDK** — incompatible with the platform's Docker/FastAPI architecture. Pivoted on 2026-04-28 to HF Inference Providers, which:

- Keeps the Docker/FastAPI architecture (matches OWASP / Blue Team / Red Team)
- Eliminates cold-start (HF's hosted Qwen is warm-served)
- Uses HF Pro inference credit (free at workshop volume)
- Simplifies the stack significantly (drops `torch`, `transformers`, `accelerate`, `spaces`, `qwen-vl-utils`, `libgl1`)
- Adds one Space secret (`HF_TOKEN`) instead of one Space hardware tier

### Cost model

`cpu-basic` is free. Inference runs on HF's hosted infrastructure, billed via the user's HF Pro inference credit. Per-call cost for Qwen2.5-VL-7B is on the order of a fraction of a cent; workshop volume (e.g. 30 students × 20 attacks each = 600 calls) easily fits within the monthly Pro credit.

## Model

- **Primary:** `Qwen/Qwen2.5-VL-7B-Instruct` served via the `together` provider (HF Inference Providers default)
- **License:** Apache 2.0 (open weights, no gating)
- **Configurability:** model ID stored as env var `MULTIMODAL_MODEL`; provider as `HF_INFERENCE_PROVIDER`. Switching requires re-running the verification matrix.

### Acceptable alternate models (if Qwen2.5-VL-7B refuses our injections, or the Together provider is unavailable)

| Model | Provider candidates | Reason to consider | Tradeoff |
|-------|--------------------|--------------------|----------|
| `Qwen/Qwen2.5-VL-3B-Instruct` | together, hyperbolic | Smaller, may be less safety-aligned | Worse OCR — may hurt P5 fidelity |
| `llava-hf/llava-v1.6-mistral-7b-hf` | replicate | Older, broadly tested | Older OCR quality |
| `meta-llama/Llama-3.2-11B-Vision-Instruct` | together, fireworks-ai | Different model family | Different injection-following behavior; verify |
| `mistralai/Pixtral-12B-2409` | together | Strong OCR | Larger; slightly more cost per call |

DO NOT swap without re-running the full attack/defense verification matrix.

## Dependencies (`requirements.txt`)

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
jinja2>=3.1.0
python-multipart>=0.0.12
pydantic>=2.0.0
pillow>=10.0.0
huggingface_hub>=0.27.0
```

Notes:
- `huggingface_hub` — provides `InferenceClient` for hosted inference calls. Replaces the previously-planned `torch` / `transformers` / `accelerate` / `spaces` / `qwen-vl-utils` stack (no local model load).
- `pillow` — image bytes parsing only (no model preprocessing locally)
- DO NOT include `groq` — Multimodal lab does not use Groq

Phase 3 will add:
- `pytesseract>=0.3.10` — for the OCR Pre-Scan defense
- `slowapi>=0.1.9` — rate limiting (10 req/min per IP per `api_spec.md`)

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Pillow's manylinux wheel bundles libjpeg/libpng; no apt deps needed for v1.
# Tesseract will be added in Phase 3 when the OCR Pre-Scan defense lands.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

Identical pattern to blue-team / red-team Dockerfile (Python 3.11-slim, port 7860, uvicorn). No system deps in v1.

## Inference Integration (HF Inference Providers)

Inference function uses `huggingface_hub.InferenceClient`:

```python
from huggingface_hub import InferenceClient

client = InferenceClient(provider="together", token=os.environ["HF_TOKEN"])

response = client.chat_completion(
    model="Qwen/Qwen2.5-VL-7B-Instruct",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": data_url}},
            {"type": "text", "text": prompt},
        ],
    }],
    max_tokens=512,
)
```

Latency: 1–3s typical. No cold-start. On Inference Provider errors (rate limit, model unavailable), the exception propagates to the caller (FastAPI returns 503).

If Together AI doesn't have Qwen2.5-VL-7B available, swap providers via `HF_INFERENCE_PROVIDER` env var. Candidates: `together`, `fireworks-ai`, `hyperbolic`, `replicate`.

## HuggingFace Space Metadata

`README.md` MUST contain a YAML frontmatter block (HF requirement):

```yaml
---
title: Multimodal Security Lab
emoji: 🖼️
colorFrom: purple
colorTo: red
sdk: docker
pinned: false
short_description: AI security workshop — image prompt injection + OCR poisoning
---
```

No `hardware` field needed — HF Spaces default to `cpu-basic` for Docker SDK without an explicit hardware tier.

## Environment Variables

| Variable | Required | Set Via | Purpose |
|----------|----------|---------|---------|
| `HF_TOKEN` | **Yes** | HF Space **secret** | Auth to HF Inference Providers. Use a fine-grained token with `Make calls to Inference Providers` permission only — read-only inference, no repo access. |
| `MULTIMODAL_MODEL` | No (default `Qwen/Qwen2.5-VL-7B-Instruct`) | HF Space variable | Override model ID |
| `HF_INFERENCE_PROVIDER` | No (default `together`) | HF Space variable | Override Inference Provider (e.g. `fireworks-ai`, `hyperbolic`, `replicate`) |
| `LOG_LEVEL` | No (default `INFO`) | HF Space variable | Standard Python logging |

This space does NOT use `GROQ_API_KEY`. The `HF_TOKEN` secret should be a fine-grained token with **Inference Providers** permission only — narrowest scope sufficient for inference calls.

## Image Library Storage

Pre-canned attack and legitimate images live in `spaces/multimodal/static/images/canned/` and are committed to the repo. Naming convention:

```
spaces/multimodal/static/images/canned/
  p1_1_receipt_override.png
  p1_2_contract_authority_spoof.png
  ...
  p5_1_white_on_white.png
  p5_2_microprint.png
  ...
  legit_p1_1_office_supplies_receipt.png
  legit_p5_1_genuine_w9_form.png
  ...
```

Each file ≤500KB. 24 files × 500KB = 12MB total. Committed to git (not Git LFS for v1).

## Deployment Flow

```
./scripts/deploy.sh multimodal
```

`scripts/deploy.sh` already:
1. Copies `framework/` files into `spaces/multimodal/`
2. Pushes to the HF remote for the space

What it does NOT yet do (must verify or extend during implementation):
- Confirm the deploy script handles the `static/images/canned/` directory correctly (pre-canned images must ship to HF)
- Confirm HF remote is configured for `nikobehar/ai-sec-lab4-multimodal`

If `deploy.sh` needs changes, file an issue rather than silently modifying it (per CLAUDE.md framework-change rules — `framework/` changes affect all spaces).

## Cold-Start Behavior

Substantially simpler than the original ZeroGPU plan. The Space itself is a tiny FastAPI server; the Vision LLM is hosted by HF, always warm.

| Phase | Duration | What's happening |
|-------|----------|------------------|
| Space sleep → wake | 10–30s | HF spinning up the Docker container (small image, fast pull) |
| Container start → first `/api/attack` | <1s | App server up, ready for requests |
| Each `/api/attack` call | 1–3s | HF Inference Providers call (warm, no cold-start) |
| Idle → Space sleeps | After ~48h idle (HF default for free tier) | Container hibernates; next request triggers a Space wake |

No pre-warm required — even after a sleep, the first request is just the Space-wake (~30s), not a model load.

## Health Verification (Operator Agent)

Per CLAUDE.md, after `deploy.sh multimodal` completes, Reviewer Agent MUST verify:

- `GET /health` returns 200 with `hf_token_set: true`, `inference_provider: together`, `model_id: Qwen/Qwen2.5-VL-7B-Instruct`, `attack_count: 12`, `image_library_size: 12` (the 12 attack PNGs the attacks dict references)
- No startup errors in HF Space build logs
- `POST /api/attack` with `attack_id=P1.1, image_source=canned` returns a model response within ~5s
- All 12 canned attack images succeed against the (undefended) hosted Qwen
- All 12 legitimate images do NOT trigger false positives across the recommended defense stack (Phase 5 task)
- Defense matrix verified — each defense catches what it claims (Phase 5 task)

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `/health` reports `hf_token_set: false` | `HF_TOKEN` not set as Space secret | Add `HF_TOKEN` as a Space secret in HF UI; restart the Space |
| `POST /api/attack` returns 503 with "InferenceClient" error | HF Inference Providers rate limit or provider down | Retry; if persistent, swap provider via `HF_INFERENCE_PROVIDER` env (`fireworks-ai`, `hyperbolic`, `replicate`) |
| `POST /api/attack` returns 503 with "model not available" | Provider doesn't host the requested model | Swap to a provider that does, or change `MULTIMODAL_MODEL` to a model the current provider hosts |
| Inference responses don't follow the image-embedded injection | Qwen2.5-VL-7B safety alignment | Try a less-aligned alternate model via `MULTIMODAL_MODEL` (see Acceptable alternate models) |

## Acceptance Checks

- [ ] HF Space created at `nikobehar/ai-sec-lab4-multimodal` (private, Docker SDK, default `cpu-basic`)
- [ ] `HF_TOKEN` configured as a Space secret (fine-grained, Inference Providers permission only)
- [ ] Dockerfile pulls clean (no apt deps in v1)
- [ ] `requirements.txt` pinned and complete (FastAPI, uvicorn, jinja2, python-multipart, pydantic, pillow, huggingface_hub)
- [ ] `vision_inference.py` uses `huggingface_hub.InferenceClient` (no local model load)
- [ ] Pre-canned image library shipped in `spaces/multimodal/static/images/canned/` (24 images)
- [ ] `/health` reports correct values (`hf_token_set: true`, `inference_provider`, `model_id`, `attack_count: 12`, `image_library_size: 12`)
- [ ] First call to `/api/attack` returns within ~5s (Space-wake + warm hosted inference)
- [ ] `MULTIMODAL_MODEL` and `HF_INFERENCE_PROVIDER` env var overrides work
- [ ] No `GROQ_API_KEY` referenced in this space's code (Multimodal does not use Groq)
- [ ] All 12 attacks succeed against undefended model (Phase 5)
- [ ] All 12 legit images pass without false positives (Phase 5)
- [ ] Defense matrix verified end-to-end on the live Space (Phase 5)
