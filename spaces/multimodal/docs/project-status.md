# Multimodal Security Lab — Project Status

*Last updated: 2026-04-27*

------------------------------------------------------------------------

## Current Phase

**Bootstrap.** Specs exist; no implementation code yet.

Per platform `/CLAUDE.md` "Creating a New Space" checklist, this space is past the spec-creation gate and may proceed to implementation when approved.

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

| Component | Status |
|-----------|--------|
| Specs | ✅ Complete (4 of 4) |
| Space-level CLAUDE.md | ✅ Complete |
| `app.py` | ⬜ Not started |
| `attacks.py` (12 attack defs) | ⬜ Not started |
| `defenses.py` (4 defenses) | ⬜ Not started |
| `vision_inference.py` (ZeroGPU wrapper) | ⬜ Not started |
| `ocr_pipeline.py` (Tesseract integration) | ⬜ Not started |
| Frontend `app.js` + space modules | ⬜ Not started |
| Frontend `index.html` | ⬜ Not started |
| `static/css/multimodal.css` overrides | ⬜ Not started |
| Pre-canned image library (24 images) | ⬜ Not started |
| Postman collection | ⬜ Not started |
| Dockerfile | ⬜ Not started |
| `requirements.txt` | ⬜ Not started |
| HF Space created | ⬜ Not started |
| Deploy verification | ⬜ Not started |

------------------------------------------------------------------------

## Open Risks

1. **Qwen2.5-VL safety alignment** — Need to verify Qwen's built-in safety doesn't refuse our injection attacks. Plan: test with `P1.1` (least subtle) first; if refused, fall back to `Qwen2.5-VL-3B` or `LLaVA-1.6` per `deployment_spec.md`.
2. **ZeroGPU quota cliff** — Mitigation per `deployment_spec.md`: pre-warm before workshops; document HF Inference Providers as fallback.
3. **Pre-canned attack image authoring** — 24 images need to be created. Plan: PIL/Pillow scripts that programmatically generate the canonical attacks (e.g. white-on-white text, microprint, fake receipts) — keeps images deterministic and easy to regenerate.

------------------------------------------------------------------------

## Next Recommended Task

**Implementation Phase 1: Backend skeleton**

Build `app.py` + `attacks.py` + `vision_inference.py` minimally enough to:
- Serve `/health`
- Serve `/api/attacks` returning the 12 attack defs
- Run `/api/attack` for `P1.1` against canned image only (no upload, no defenses)
- Verify against deployed `Qwen2.5-VL-7B-Instruct` on ZeroGPU

Target: prove the cold-start UX works and Qwen accepts the first attack. Defer image library, defenses, frontend, and remaining attacks to later phases.

This task SHOULD be proposed via Planner Agent and wait for approval per platform Plan Mode rules.

------------------------------------------------------------------------

## Session History

### 2026-04-27 — Bootstrap

- Decided hardware path (ZeroGPU + Qwen2.5-VL-7B) with HF Pro account
- Locked v1 scope to P1 + P5 only (P6 deepfake → v2)
- Authored 4 specs + space CLAUDE.md + this file
- Updated `README.md` to drop stale issue refs and reflect v1 scope
- Updated platform `/docs/project-status.md` with multimodal bootstrap state
- Filed GitHub milestone issue (number TBD on commit)

No implementation code in this session — bootstrap phase only.
