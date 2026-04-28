# Multimodal Security Lab — Project Status

*Last updated: 2026-04-28 (Phase 1: Backend skeleton complete)*

------------------------------------------------------------------------

## Current Phase

**Phase 1 complete (backend skeleton).** Backend code shipped; awaiting deploy + Qwen verification.

Per platform `/CLAUDE.md`, the next phase (Phase 2: Pre-canned Image Library) requires Planner approval before implementation.

------------------------------------------------------------------------

## Bootstrap Checklist

- [x] `spaces/multimodal/specs/overview_spec.md`
- [x] `spaces/multimodal/specs/frontend_spec.md`
- [x] `spaces/multimodal/specs/api_spec.md`
- [x] `spaces/multimodal/specs/deployment_spec.md`
- [x] `spaces/multimodal/CLAUDE.md`
- [x] `spaces/multimodal/docs/project-status.md` (this file)
- [x] `spaces/multimodal/README.md` updated with v1 scope
- [x] GitHub milestone issue tracking v1 build (filed 2026-04-27)

------------------------------------------------------------------------

## v1 Scope (locked in 2026-04-27 planning session)

| Decision | Value |
|----------|-------|
| Hardware | HF Spaces ZeroGPU (Nvidia A100, dynamic per-call) |
| Model | `Qwen/Qwen2.5-VL-7B-Instruct` (env-overridable via `MULTIMODAL_MODEL`) |
| Labs | P1 Image Prompt Injection (6 attacks) + P5 OCR Poisoning (6 attacks) |
| Scenario | NexaCore DocReceive (internal document intake portal) |
| Image input | Pre-canned library (24 images) + opt-in upload |
| External APIs | None (no Groq, no third-party vision API) |

------------------------------------------------------------------------

## Implementation Status

| Component | Status | Phase |
|-----------|--------|-------|
| Specs | ✅ Complete (4 of 4) | Bootstrap |
| Space-level CLAUDE.md | ✅ Complete | Bootstrap |
| `requirements.txt` | ✅ Complete | Phase 1 |
| `Dockerfile` | ✅ Complete (Tesseract deferred to Phase 3) | Phase 1 |
| `attacks.py` (12 attack defs) | ✅ Complete | Phase 1 |
| `vision_inference.py` (ZeroGPU wrapper) | ✅ Complete | Phase 1 |
| `app.py` (3 endpoints: /health, /api/attacks, /api/attack) | ✅ Complete | Phase 1 |
| `templates/index.html` (Phase 1 placeholder) | ✅ Complete | Phase 1 |
| `static/css/multimodal.css` (empty stub) | ✅ Complete | Phase 1 |
| `scripts/generate_p1_1.py` (PIL receipt generator) | ✅ Complete | Phase 1 |
| `static/images/canned/p1_1_receipt_override.png` | ⬜ **Generated post-pull** (run `python scripts/generate_p1_1.py`) | Phase 1 |
| Pre-canned image library (remaining 11 images) | ⬜ Not started | Phase 2 |
| `defenses.py` (4 defenses) | ⬜ Not started | Phase 3 |
| `ocr_pipeline.py` (Tesseract integration) | ⬜ Not started | Phase 3 |
| Frontend `app.js` + space modules | ⬜ Not started | Phase 4 |
| Frontend full `index.html` (replaces Phase 1 placeholder) | ⬜ Not started | Phase 4 |
| Defense matrix verification (12 attacks × {undefended, +defenses}) | ⬜ Not started | Phase 5 |
| Postman collection | ⬜ Not started | Phase 5 or 6 |
| HF Space created | ⬜ Not started | Phase 6 |
| Deploy verification | ⬜ Not started | Phase 6 |

------------------------------------------------------------------------

## Open Risks

1. **Qwen2.5-VL safety alignment** — Need to verify Qwen's built-in safety doesn't refuse our injection attacks. Plan: test with `P1.1` (least subtle) first; if refused, fall back to `Qwen2.5-VL-3B` or `LLaVA-1.6` per `deployment_spec.md`.
2. **ZeroGPU quota cliff** — Mitigation per `deployment_spec.md`: pre-warm before workshops; document HF Inference Providers as fallback.
3. **Pre-canned attack image authoring** — 24 images need to be created. Plan: PIL/Pillow scripts that programmatically generate the canonical attacks (e.g. white-on-white text, microprint, fake receipts) — keeps images deterministic and easy to regenerate.

------------------------------------------------------------------------

## Next Recommended Task

**Phase 1 verification + Phase 2 kickoff.**

Two-part next-task:

1. **Phase 1 deploy + verification (Operator/Reviewer).** Pre-deploy: install Pillow locally and run `python scripts/generate_p1_1.py` to produce `static/images/canned/p1_1_receipt_override.png`. Commit the PNG. Then deploy: create the HF Space at `nikobehar/multimodal-workshop` (private, ZeroGPU enabled), run `./scripts/deploy.sh multimodal`. Verify:
   - `GET /health` reports `attack_count: 12` and `image_library_size: 1` after the PNG is committed
   - First `POST /api/attack` with `attack_id=P1.1, image_source=canned` triggers cold-start (~10–30s), then returns a model response
   - Confirm `succeeded: true` (Qwen2.5-VL-7B follows the BANANA SUNDAE injection)
   - If Qwen refuses: try `MULTIMODAL_MODEL=Qwen/Qwen2.5-VL-3B-Instruct` or `MULTIMODAL_MODEL=llava-hf/llava-v1.6-mistral-7b-hf` per `specs/deployment_spec.md`

2. **Phase 2: Pre-canned image library.** Author 11 more PIL generation scripts (P1.2 – P1.6, P5.1 – P5.6) producing the remaining attack images plus 12 legitimate-document images for false-positive checking (per `specs/overview_spec.md` Image Input section). Subtle visual techniques per attack — white-on-white pixel ops for P5.1, microprint for P5.2, etc.

Per platform CLAUDE.md, propose Phase 2 via Planner Agent and wait for approval before implementing.

------------------------------------------------------------------------

## Session History

### 2026-04-27 — Bootstrap

- Decided hardware path (ZeroGPU + Qwen2.5-VL-7B) with HF Pro account
- Locked v1 scope to P1 + P5 only (P6 deepfake → v2)
- Authored 4 specs + space CLAUDE.md + this file
- Updated `README.md` to drop stale issue refs and reflect v1 scope
- Updated platform `/docs/project-status.md` with multimodal bootstrap state
- Filed GitHub milestone issue **#15** via MCP

No implementation code in this session — bootstrap phase only.

### 2026-04-28 — Phase 1: Backend Skeleton

**What was built:**

- **`requirements.txt`** — Phase 1 minimum: fastapi, uvicorn, jinja2, python-multipart, pydantic, pillow, torch, transformers, accelerate, spaces, qwen-vl-utils. Defers pytesseract (Phase 3) and slowapi (rate limiting, Phase 5/6).
- **`Dockerfile`** — Python 3.11-slim + libgl1 + libglib2.0-0 (for Pillow + transitive deps). Tesseract added in Phase 3.
- **`attacks.py`** — 12 attack definitions as a `dict` (P1.1 – P1.6 + P5.1 – P5.6). Each entry: `id`, `lab`, `name`, `owasp`, `difficulty`, `description`, `success_check`, `canary`, `filename`, `alt`. 12 distinct two-word canary phrases assigned. No model calls — pure data.
- **`vision_inference.py`** — `@spaces.GPU(duration=60)` decorator on `run_vision_inference(image_bytes, prompt) -> str`. Lazy-loads `Qwen/Qwen2.5-VL-7B-Instruct` (env-overridable via `MULTIMODAL_MODEL`). Uses `qwen_vl_utils.process_vision_info` for image preprocessing, `bfloat16` weights, `device_map="auto"`. Includes `is_loaded()` for /health to check readiness.
- **`app.py`** — FastAPI app with three endpoints: `GET /health` (reports `model_loaded`, `attack_count`, `image_library_size`, `phase: 1`), `GET /api/attacks` (returns metadata for the 12 attacks), `POST /api/attack` (canned-image only at this phase; returns 400 for upload mode, 503 if image library not yet shipped, 400 for unknown attack_id). Uses `SYSTEM_PROMPT_DOCRECEIVE` constant per `overview_spec.md` scenario.
- **`templates/index.html`** — Phase 1 placeholder shell with badge + endpoint list + link to issue #15. Frontend ships in Phase 4.
- **`static/css/multimodal.css`** — Empty stub (frontend overrides land in Phase 4).
- **`scripts/generate_p1_1.py`** — PIL script that produces a fake-receipt PNG with the BANANA SUNDAE injection payload framed as `*** SYSTEM INSTRUCTIONS ***`. The PNG itself is **not committed** (binary content doesn't round-trip via MCP push_files); user runs the script post-pull to materialize the image.

**Verification done:**

- All 4 Python files AST-parse cleanly
- HTML and config files committed as-is (no test infrastructure for these)

**Verification deferred to Operator/Reviewer (post-deploy):**

- Qwen2.5-VL-7B actually accepts the P1.1 image-embedded injection
- ZeroGPU cold start completes within ~30s on first call
- `succeeded: true` returned for P1.1 (canary BANANA SUNDAE in response)
- If Qwen refuses: model-fallback path per deployment_spec.md

**Risks status:**

- `Qwen2.5-VL safety alignment` — STILL OPEN (resolved by Phase 1 verification step)
- `ZeroGPU quota cliff` — STILL OPEN (mitigation: pre-warm; relevant for live workshops, not Phase 1)
- `Pre-canned attack image authoring` — Partially addressed (P1.1 script shipped); remaining 11 scripts are Phase 2 work
