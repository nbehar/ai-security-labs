# Multimodal Security Lab — Project Status

*Last updated: 2026-04-28 (Phase 2: Image library generator complete)*

------------------------------------------------------------------------

## Current Phase

**Phase 2 complete (image-library generator).** All 24 image generators authored in a single PIL script. PNGs themselves are produced post-pull by running the script.

Per platform `/CLAUDE.md`, the next phase (Phase 3: Defenses) requires Planner approval before implementation.

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
| `scripts/generate_p1_1.py` (PIL receipt generator — single-image test harness) | ✅ Complete | Phase 1 |
| `scripts/generate_canned_images.py` (full 24-image library generator) | ✅ Complete | Phase 2 |
| `static/images/canned/*.png` (24 PNGs) | ⬜ **Generated post-pull** (run `python scripts/generate_canned_images.py`) | Phase 1+2 |
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

**Phase 1+2 deploy verification + Phase 3 kickoff.**

Two-part next-task:

1. **Generate + deploy (Operator/Reviewer).** Pre-deploy: install Pillow locally and run `python scripts/generate_canned_images.py` to produce all 24 PNGs in `static/images/canned/`. Commit the 24 PNGs (binary; standard git flow, not MCP). Then deploy: create the HF Space at `nikobehar/multimodal-workshop` (private, ZeroGPU enabled), run `./scripts/deploy.sh multimodal`. Verify:
   - `GET /health` reports `attack_count: 12` and `image_library_size: 12` (only attack PNGs are referenced from the attacks dict; legit PNGs are present but not enumerated)
   - First `POST /api/attack` with each of the 12 attack IDs triggers a model response. Spot-check P1.1 (BANANA SUNDAE) for Phase 1 verification, plus a sample P5 attack for Phase 2 verification.
   - If Qwen refuses any attack: log it for Phase 5 verification matrix; consider model fallback per `specs/deployment_spec.md`.

2. **Phase 3: Defenses.** Implement the 4 defense layers per `specs/overview_spec.md` Defenses section: `ocr_prescan` (Tesseract; requires adding `pytesseract` to requirements.txt and `tesseract-ocr` to Dockerfile), `output_redaction`, `boundary_hardening` (system prompt update), `confidence_threshold`. Each defense is a function in a new `defenses.py` module that returns a defense_log entry. Wire into `app.py` `/api/attack` flow with toggleable per-defense application. Use the 12 legit PNGs to verify each defense doesn't false-positive on legitimate documents.

Per platform CLAUDE.md, propose Phase 3 via Planner Agent and wait for approval before implementing.

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

### 2026-04-28 — Phase 2: Pre-canned Image Library Generator

**What was built:**

- **`scripts/generate_canned_images.py`** (~960 lines) — single consolidated PIL script with 24 image-generator functions:
  - 6 P1 Image Prompt Injection attacks (P1.1 Receipt Override, P1.2 Contract Authority Spoof, P1.3 Badge Self-Approve, P1.4 Watermark Injection, P1.5 Multi-Step Hijack, P1.6 Persona Override)
  - 6 P5 OCR Poisoning attacks (P5.1 White-on-White, P5.2 Microprint, P5.3 Color-Adjacent, P5.4 Layered PDF, P5.5 Rotated Margin, P5.6 Adversarial Font)
  - 6 legitimate P1 documents (clean variants for FP checking)
  - 6 legitimate P5 documents (clean variants for FP checking)
- Shared helpers for fonts (cross-platform fallback chain), colors, headers/footers
- CLI dispatch: `all` (default) | `attacks` | `legit` | individual key (e.g. `p5_3`)
- Each PNG is 800×1100, RGB, optimize-saved. Filenames match the `filename` field in `attacks.py` for the 12 attack images; legit images use `legit_*.png` prefix.

**Verification done:**

- Script AST-parses cleanly (959 lines)

**Verification deferred to Operator/Reviewer (post-pull):**

- Run `python scripts/generate_canned_images.py` locally with Pillow installed and confirm all 24 PNGs are produced
- Spot-check visual content (P1.x attacks should have visible injection text; P5.x attacks should have hidden/obscured payloads; legit images should look like clean documents)
- Verify no PNG exceeds 500KB (per spec — image library budget 12MB total)

**Note on the older `scripts/generate_p1_1.py`:** kept in place as a single-image test harness. The new `generate_canned_images.py p1_1` produces a comparable (not byte-identical) P1.1 image. Last-writer wins on the output file.
