# Deployment Spec — Multimodal Security Lab

## Goal

Define hosting, hardware, model loading, env config, and verification for deploying the Multimodal Lab as a HuggingFace Space.

## Hosting

- **Platform:** HuggingFace Spaces
- **SDK:** Docker (consistent with other spaces)
- **Hardware tier:** **`cpu-basic`** (free)
- **Visibility:** Private (consistent with other spaces — workshop access controlled via HF Space link)
- **HF Space name:** `nikobehar/ai-sec-lab4-multimodal` (per platform `ai-sec-lab#-name` convention; this is the 4th workshop deployed)
- **Inference path:** HuggingFace Inference Providers (OVH cloud by default), called via `huggingface_hub.InferenceClient`. Vision inference is *hosted* — no GPU on the Space itself, no local model load, no cold-start.

### Why not ZeroGPU

The 2026-04-27 plan assumed ZeroGPU + a locally loaded Qwen2.5-VL-7B. Discovered at Space creation time that **HF Spaces only allow ZeroGPU on Gradio SDK** — incompatible with the platform's Docker/FastAPI architecture. Pivoted on 2026-04-28 to HF Inference Providers, which:

- Keeps the Docker/FastAPI architecture (matches OWASP / Blue Team / Red Team)
- Eliminates cold-start (HF's hosted Qwen is warm-served)
- Uses HF Pro inference credit (free at workshop volume)
- Simplifies the stack significantly (drops `torch`, `transformers`, `accelerate`, `spaces`, `qwen-vl-utils`, `libgl1`)
- Adds one Space secret (`HF_TOKEN`) instead of one Space hardware tier

### Cost model

`cpu-basic` is free. Inference runs on HF's hosted infrastructure, billed via the user's HF Pro inference credit. Per-call cost for Qwen2.5-VL-72B is on the order of a fraction of a cent; workshop volume (e.g. 30 students × 20 attacks each = 600 calls) easily fits within the monthly Pro credit.

## Model

- **Primary:** `Qwen/Qwen2.5-VL-72B-Instruct` served via the `ovhcloud` provider
- **License:** Apache 2.0 (open weights, no gating)
- **Configurability:** model ID stored as env var `MULTIMODAL_MODEL`; provider as `HF_INFERENCE_PROVIDER`. Switching requires re-running the verification matrix.

### Why 72B and not 7B (set 2026-04-28 at deploy time)

The original spec called for `Qwen/Qwen2.5-VL-7B-Instruct`. At deploy time, querying `https://huggingface.co/api/models/<id>?expand=inferenceProviderMapping` showed:

- `Qwen/Qwen2.5-VL-7B-Instruct` → only Hyperbolic, status `error` (not actually serving)
- `Qwen/Qwen2.5-VL-72B-Instruct` → OVH cloud, status `live` ✅

The 72B sibling is the same Qwen2.5-VL family with stronger OCR/vision behavior — strictly an upgrade for the workshop (P1 visible-text and P5 OCR-poisoning attacks both benefit from better OCR). Cost remains within HF Pro credit at workshop volume. Trade-off: 72B is more safety-aware than 7B would have been; some attacks succeed by canary-leak but the model still flags the document — Phase 3 defense lessons must account for this baseline.

### Verifying provider availability before swapping

```
curl -s "https://huggingface.co/api/models/<MODEL_ID>?expand=inferenceProviderMapping" | python3 -m json.tool
```

Look for at least one provider with `"status": "live"`. Do NOT swap to a model whose only provider is `error` or `staging`.

### Acceptable alternate models (if Qwen2.5-VL-72B refuses our injections, or OVH cloud is unavailable)

| Model | Provider candidates | Reason to consider | Tradeoff |
|-------|--------------------|--------------------|----------|
| `Qwen/Qwen2-VL-7B-Instruct` | check live mapping at swap time | Older Qwen, may be less safety-aligned | Older OCR; verify before swap |
| `google/gemma-3-27b-it` | featherless-ai (live), scaleway (live) | Different model family, multimodal Gemma 3 | Not OCR-specialized; different injection-following behavior |
| `meta-llama/Llama-3.2-11B-Vision-Instruct` | check live mapping | Different family | At time of writing: no live HF Inference Providers route — verify |
| `mistralai/Pixtral-12B-2409` | check live mapping | Strong OCR | At time of writing: no live HF Inference Providers route — verify |

DO NOT swap without (1) verifying live provider availability, and (2) re-running the full attack/defense verification matrix.

## Dependencies (`requirements.txt`)

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
jinja2>=3.1.0
python-multipart>=0.0.12
pydantic>=2.0.0
pillow>=10.0.0
huggingface_hub>=0.27.0
pytesseract>=0.3.10
slowapi>=0.1.9
```

Notes:
- `huggingface_hub` — provides `InferenceClient` for hosted inference calls. Replaces the previously-planned `torch` / `transformers` / `accelerate` / `spaces` / `qwen-vl-utils` stack (no local model load).
- `pillow` — image bytes parsing + magic-bytes verification (`Image.open(BytesIO).verify()` on uploads)
- `pytesseract` — Phase 3, OCR Pre-Scan + Confidence Threshold defenses
- `slowapi` — Phase 4a, 10 req/min per IP rate limit on `/api/attack`
- DO NOT include `groq` — Multimodal lab does not use Groq

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Pillow's manylinux wheel covers libjpeg/libpng.
# Tesseract added in Phase 3 for the OCR Pre-Scan + Confidence Threshold defenses.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

Same Python 3.11-slim base as blue-team / red-team. The single apt layer is `tesseract-ocr` (Phase 3); blue-team/red-team don't need it because they're text-only.

## Inference Integration (HF Inference Providers)

Inference function uses `huggingface_hub.InferenceClient`:

```python
from huggingface_hub import InferenceClient

client = InferenceClient(provider="ovhcloud", token=os.environ["HF_TOKEN"])

response = client.chat_completion(
    model="Qwen/Qwen2.5-VL-72B-Instruct",
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

If OVH cloud doesn't have the configured model available, swap providers via `HF_INFERENCE_PROVIDER` env var. Always verify live availability via the `inferenceProviderMapping` API call shown above before swapping. Common provider IDs: `ovhcloud`, `together`, `fireworks-ai`, `hyperbolic`, `replicate`, `featherless-ai`, `scaleway`, `nebius`.

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
short_description: Image prompt injection + OCR poisoning workshop
---
```

No `hardware` field needed — HF Spaces default to `cpu-basic` for Docker SDK without an explicit hardware tier.

## Environment Variables

| Variable | Required | Set Via | Purpose |
|----------|----------|---------|---------|
| `HF_TOKEN` | **Yes** | HF Space **secret** | Auth to HF Inference Providers. Use a fine-grained token with `Make calls to Inference Providers` permission only — read-only inference, no repo access. |
| `MULTIMODAL_MODEL` | No (default `Qwen/Qwen2.5-VL-72B-Instruct`) | HF Space variable | Override model ID |
| `HF_INFERENCE_PROVIDER` | No (default `ovhcloud`) | HF Space variable | Override Inference Provider (e.g. `together`, `fireworks-ai`, `hyperbolic`, `replicate`, `featherless-ai`, `scaleway`) |
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
| Each `/api/attack` call | 10–20s typical (P1.1 measured at ~16s on 2026-04-28 with `Qwen/Qwen2.5-VL-72B-Instruct` via `ovhcloud`, generating ~500 output tokens) | HF Inference Providers call. Warm-served (no cold-start), but the 72B is meaningfully slower than the originally-specced 7B for vision tasks; latency dominated by output-token generation. Re-baseline if the model is changed. |
| Idle → Space sleeps | After ~48h idle (HF default for free tier) | Container hibernates; next request triggers a Space wake |

No pre-warm required — even after a sleep, the first request is just the Space-wake (~30s), not a model load.

## Health Verification (Operator Agent)

Per CLAUDE.md, after `deploy.sh multimodal` completes, Reviewer Agent MUST verify:

- `GET /health` returns 200 with `hf_token_set: true`, `inference_provider: ovhcloud`, `model_id: Qwen/Qwen2.5-VL-72B-Instruct`, `attack_count: 12`, `image_library_size: 12` (the 12 attack PNGs the attacks dict references)
- No startup errors in HF Space build logs
- `POST /api/attack` with `attack_id=P1.1, image_source=canned` returns a model response within ~20s (72B latency budget; observed 16s on 2026-04-28). Tighten to 1–3s if the model is later swapped to a 7B-class variant.
- All 12 canned attack images succeed against the (undefended) hosted Qwen
- All 12 legitimate images do NOT trigger false positives across the recommended defense stack (Phase 5 task)
- Defense matrix verified — each defense catches what it claims (Phase 5 task)

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `/health` reports `hf_token_set: false` | `HF_TOKEN` not set as Space secret | Add `HF_TOKEN` as a Space secret in HF UI; restart the Space |
| `POST /api/attack` returns 503 with "InferenceClient" error | HF Inference Providers rate limit or provider down | Retry; if persistent, swap provider via `HF_INFERENCE_PROVIDER` env (e.g. `together`, `fireworks-ai`, `hyperbolic`, `replicate`, `featherless-ai`, `scaleway`). Always check live availability via the `inferenceProviderMapping` API before swapping. |
| `POST /api/attack` returns 503 with "model not available" | Provider doesn't host the requested model | Swap to a provider that does, or change `MULTIMODAL_MODEL` to a model the current provider hosts |
| Inference responses don't follow the image-embedded injection | Qwen2.5-VL-72B safety alignment (it tends to flag injections as suspicious) | Try a less-aligned alternate model via `MULTIMODAL_MODEL` (see Acceptable alternate models). Note: at deploy time the 7B variant has no live HF Inference Providers route, so falling back to a smaller Qwen requires checking live mappings first. |

## Acceptance Checks

- [x] HF Space created at `nikobehar/ai-sec-lab4-multimodal` (private, Docker SDK, default `cpu-basic`) — verified 2026-04-28
- [x] `HF_TOKEN` configured as a Space secret (fine-grained, Inference Providers permission only)
- [x] Dockerfile builds clean (Phase 3 added single `tesseract-ocr` apt layer; otherwise matches blue-team/red-team pattern)
- [x] `requirements.txt` pinned and complete (FastAPI, uvicorn, jinja2, python-multipart, pydantic, pillow, huggingface_hub, pytesseract, slowapi as of Phase 4a)
- [x] `vision_inference.py` uses `huggingface_hub.InferenceClient` (no local model load)
- [x] Pre-canned image library shipped in `spaces/multimodal/static/images/canned/` (24 images, committed `417f9d7`)
- [x] `/health` reports correct values (`hf_token_set: true`, `inference_provider`, `model_id`, `attack_count: 12`, `image_library_size: 12`)
- [x] First call to `/api/attack` returns within ~20s (P1.1 measured at ~16s on 2026-04-28; P95 ≈ 60s outlier on verbose responses)
- [x] `MULTIMODAL_MODEL` and `HF_INFERENCE_PROVIDER` env var overrides work (used during the 7B→72B / together→ovhcloud pivot)
- [x] No `GROQ_API_KEY` referenced in this space's code (Multimodal does not use Groq)
- [ ] All 12 attacks succeed against undefended model (Phase 5 — calibration ran 6/12 clean, 3 self-flagged, 3 image-side issues; see `docs/phase3-calibration.md`)
- [ ] All 12 legit images pass without false positives (Phase 5)
- [ ] Defense matrix verified end-to-end on the live Space (Phase 5)
