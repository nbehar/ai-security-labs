# Deployment Spec — Multimodal Security Lab

## Goal

Define hosting, hardware, model loading, env config, and verification for deploying the Multimodal Lab as a HuggingFace Space.

## Hosting

- **Platform:** HuggingFace Spaces
- **SDK:** Docker (consistent with other spaces)
- **Hardware tier:** **ZeroGPU** (Nvidia A100 dynamically allocated per call)
- **Visibility:** Private (consistent with other spaces — workshop access controlled via HF Space link)
- **HF Space name:** `nikobehar/ai-sec-lab4-multimodal` (per platform `ai-sec-lab#-name` convention; this is the 4th workshop deployed)

ZeroGPU rationale (full discussion in 2026-04-27 planning session, summarized):
- Free at workshop volume with the existing HF Pro account
- Self-contained — workshop runs entirely on platform hardware, no external API calls beyond the existing Groq integration (which Multimodal does NOT use; Groq is for text-only spaces)
- Cold-start of ~10–30s on first call after Space wake is acceptable per user input
- ZeroGPU quotas are sufficient for classroom use; pre-warming the Space before sessions is the documented mitigation

## Model

- **Primary:** `Qwen/Qwen2.5-VL-7B-Instruct`
- **License:** Apache 2.0 (open weights, no gating)
- **VRAM:** ~16GB at fp16, fits ZeroGPU A100 (40GB) cleanly with headroom for image preprocessing
- **Configurability:** Model ID stored as env var `MULTIMODAL_MODEL` so we can swap without redeploying. Acceptable alternates listed in spec; switching requires re-running the verification steps.

### Acceptable alternate models (if Qwen2.5-VL-7B is over-aligned or unavailable)

| Model | Reason to consider | Tradeoff |
|-------|--------------------|----------|
| `Qwen/Qwen2.5-VL-3B-Instruct` | Smaller, faster cold-start | Worse OCR — may hurt P5 fidelity |
| `llava-hf/llava-v1.6-mistral-7b-hf` | Older, broadly tested, less safety-aligned | Older OCR quality |
| `mistralai/Pixtral-12B-2409` | Strong OCR, alternative weight class | Larger VRAM, slower cold-start |

DO NOT swap models without re-running the full attack/defense verification matrix.

## Dependencies (`requirements.txt`)

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
jinja2>=3.1.0
python-multipart>=0.0.12
pydantic>=2.0.0
pillow>=10.0.0
torch>=2.4.0
transformers>=4.45.0
accelerate>=0.34.0
spaces>=0.30.0
pytesseract>=0.3.10
slowapi>=0.1.9
qwen-vl-utils>=0.0.8
```

Notes:
- `spaces` package — required for `@spaces.GPU` decorator on inference functions (ZeroGPU integration)
- `qwen-vl-utils` — Qwen2.5-VL's image-preprocessing helpers
- `pytesseract` — for the Image OCR Pre-Scan defense (separate OCR engine, not the model)
- `slowapi` — rate limiting (10 req/min per IP per `api_spec.md`)
- DO NOT include `groq` — Multimodal lab does not use Groq

System dependency: Tesseract binary needs to be installed in the Docker image.

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System deps: build tools + Tesseract OCR engine for the OCR Pre-Scan defense
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

Differences from blue-team/red-team Dockerfile:
- Adds `tesseract-ocr`, `libtesseract-dev`, `libgl1`, `libglib2.0-0` system packages
- Otherwise identical pattern (Python 3.11-slim, port 7860, uvicorn)

## ZeroGPU Integration

Inference function MUST be decorated:

```python
import spaces

@spaces.GPU(duration=60)
def run_vision_inference(image_bytes: bytes, prompt: str) -> str:
    # Model + processor loaded lazily inside this function
    # First call: ~20s for GPU allocation + model load
    # Subsequent calls (within Space lifetime): sub-second
    ...
```

`duration` is the max GPU allocation per call in seconds. 60s is generous for v1; can tune down once we measure actual inference time.

## HuggingFace Space Metadata

`README.md` MUST contain a YAML frontmatter block (HF requirement):

```yaml
---
title: Multimodal Security Lab
emoji: 🖼️
colorFrom: purple
colorTo: red
sdk: docker
hardware: zero-a10g
pinned: false
short_description: AI security workshop — image prompt injection + OCR poisoning
---
```

(Hardware label `zero-a10g` is the HF tier name for ZeroGPU. Verify the exact label at deploy time — HF has used multiple names.)

## Environment Variables

| Variable | Required | Set Via | Purpose |
|----------|----------|---------|---------|
| `MULTIMODAL_MODEL` | No (default `Qwen/Qwen2.5-VL-7B-Instruct`) | HF Space variable | Override model ID |
| `MAX_GPU_DURATION_SECONDS` | No (default 60) | HF Space variable | Tune `@spaces.GPU(duration=…)` |
| `LOG_LEVEL` | No (default `INFO`) | HF Space variable | Standard Python logging |

This space does NOT use `GROQ_API_KEY`. No external API keys required for v1.

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

Documented for participant + workshop instructor expectations:

| Phase | Duration | What's happening |
|-------|----------|------------------|
| Space sleep → wake | 30–60s | HF spinning up the Docker container |
| Container start → first `/api/attack` | <1s | App server up, but no GPU/model yet |
| First `/api/attack` call | 10–30s | ZeroGPU allocation + model download (cached after first wake) + warm-up inference |
| Subsequent `/api/attack` calls | 1–3s per image | Steady-state inference |
| Idle → Space sleeps | After ~24h idle (HF default) | Container hibernates; next request triggers cold start again |

**Pre-warm strategy for live workshops:** Make a synthetic `/api/attack` call ~5 minutes before the workshop starts to trigger model load. The HF Space stays warm for the workshop duration as long as activity continues.

## Health Verification (Operator Agent)

Per CLAUDE.md, after `deploy.sh multimodal` completes, Reviewer Agent MUST verify:

- `GET /health` returns 200 with `groq_api_key_set: false` (this space doesn't use Groq), `attack_count: 12`, `image_library_size: 24`
- After the first `/api/attack` call, `/health` reports `model_loaded: true`
- No startup errors in HF Space build logs
- All 12 canned attack images succeed against undefended model
- All 12 legitimate images do NOT trigger false positives across the recommended defense stack
- Defense matrix verified — each defense catches what it claims

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `/health` returns 200 but `model_loaded: false` after first attack | ZeroGPU allocation timed out | Retry; if persistent, file an issue and consider model swap |
| `transformers` ImportError on cold start | Pinned versions out of sync | Re-pin `transformers` and `torch` to known-good combination |
| Tesseract not found | Missing apt package in Docker | Verify `tesseract-ocr` in Dockerfile |
| "CUDA out of memory" | Model too large for ZeroGPU A100 (unlikely with 7B) | Drop to `Qwen2.5-VL-3B` via `MULTIMODAL_MODEL` env |
| Cold start exceeds 30s consistently | Model files not cached on Space | First-cold-start is always slow; subsequent cold starts (after sleep + wake) re-pull from HF cache |

## Acceptance Checks

- [ ] HF Space created at `nikobehar/ai-sec-lab4-multimodal` (private)
- [ ] ZeroGPU enabled in Space settings
- [ ] Dockerfile includes Tesseract + Python deps
- [ ] `requirements.txt` pinned and complete
- [ ] `@spaces.GPU` decorator on inference function
- [ ] Pre-canned image library shipped in `spaces/multimodal/static/images/canned/` (24 images)
- [ ] `/health` reports correct values
- [ ] First-call cold start <30s; steady-state inference <5s
- [ ] `MULTIMODAL_MODEL` env var overrides work
- [ ] No `GROQ_API_KEY` referenced in this space's code
- [ ] Pre-warm strategy documented in space-level project-status.md
- [ ] All 12 attacks succeed against undefended model
- [ ] All 12 legit images pass without false positives
- [ ] Defense matrix verified end-to-end on the live Space
