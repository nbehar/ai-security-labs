# CLAUDE.md — Multimodal Security Lab

This file is the space-level governance for `spaces/multimodal/`. The platform-level `/CLAUDE.md` at the repo root applies in addition; this file scopes platform rules to this space and adds anything specific to multimodal work.

------------------------------------------------------------------------

# Project Purpose

Multimodal Security Lab is the AI Security Labs platform's workshop for **image-based attacks against multimodal LLMs**. Participants run real attacks against a live Vision LLM, toggle defenses, and score their results. The space is part of the same NexaCore Technologies fictional-company universe used by the OWASP, Blue Team, and Red Team workshops.

**v1 scope:** 2 labs (P1 Image Prompt Injection + P5 OCR Poisoning) anchored in the **NexaCore DocReceive** scenario.

The repository — not conversation history — is the system of record.

------------------------------------------------------------------------

# Reading Order (Space-Level)

When working in this space, Claude MUST read in this order:

1. Platform `/CLAUDE.md`
2. Platform `/docs/project-status.md`
3. This file (`spaces/multimodal/CLAUDE.md`)
4. `spaces/multimodal/specs/overview_spec.md`
5. `spaces/multimodal/specs/frontend_spec.md`
6. `spaces/multimodal/specs/api_spec.md`
7. `spaces/multimodal/specs/deployment_spec.md`
8. `spaces/multimodal/docs/project-status.md`

------------------------------------------------------------------------

# Repository Structure (this space)

```
spaces/multimodal/
  app.py                    FastAPI routes + attack orchestration (Phase 1+3 ✅)
  attacks.py                Attack definitions (12 total: 6 P1 + 6 P5) ✅
  defenses.py               4 defense layers (Phase 3 ✅)
  vision_inference.py       HF Inference Providers wrapper (Qwen2.5-VL-72B via OVH cloud) ✅
  ocr_pipeline.py           Tesseract wrapper for OCR Pre-Scan + Confidence Threshold (Phase 3 ✅)
  Dockerfile                cpu-basic + tesseract-ocr + Python deps (Phase 3 ✅)
  requirements.txt          Pinned deps: fastapi, uvicorn, jinja2, python-multipart, pydantic, pillow, huggingface_hub, pytesseract, slowapi ✅
  README.md                 HF Spaces card with frontmatter ✅
  CLAUDE.md                 This file
  specs/
    overview_spec.md        v1 scope, scenario, audience, success criteria
    frontend_spec.md        UI structure, tabs, educational scaffolding
    api_spec.md             FastAPI endpoints + Pydantic schemas
    deployment_spec.md      Hardware, model, Dockerfile, HF Inference Providers integration
  docs/
    project-status.md       Space-level status tracker
  static/
    css/
      multimodal.css        Space-specific overrides (empty stub; Phase 4 fills it) ✅
    js/
      app.js                Space entry point — imports from core.js (Phase 4 — TO BE BUILT)
      image_gallery.js      Thumbnail grid + selection (Phase 4 — TO BE BUILT)
      image_upload.js       File picker + validation (Phase 4 — TO BE BUILT)
      attack_runner.js      Attack orchestration + cold-start UX (Phase 4 — TO BE BUILT)
    images/
      canned/               24 pre-canned images (12 attack + 12 legit) ✅ (committed `417f9d7`)
  templates/
    index.html              Phase 1 placeholder shell (Phase 4 will replace with full SPA shell) ✅ for Phase 1
  postman/
    multimodal-lab.postman_collection.json   API testing contract (Phase 4a ✅ all 8 endpoints + 2 negative probes)
```

------------------------------------------------------------------------

# Stack

- **Backend:** FastAPI + Uvicorn (Python 3.11+)
- **Frontend:** Vanilla ES6+ HTML/CSS/JS — no framework, no build step (consistent with platform)
- **Model:** `Qwen/Qwen2.5-VL-72B-Instruct` via HF Inference Providers (OVH cloud by default; configurable via `HF_INFERENCE_PROVIDER`). The 7B was originally specced but had no live HF Inference Providers route at deploy time on 2026-04-28 — the 72B sibling is the same family and is `live` on OVH cloud.
- **OCR (defense):** Tesseract via `pytesseract` (Phase 3)
- **Deploy:** Docker on HuggingFace Spaces, hardware tier `cpu-basic` (free). The Vision LLM is hosted by HF; the Space is just orchestration.
- **Theme:** Dark only — inherits from `framework/static/css/styles.css`

This space does **NOT** use Groq. The platform's `framework/groq_client.py` is unused here. Inference goes through `huggingface_hub.InferenceClient` instead.

------------------------------------------------------------------------

# Spec-First Development (Reinforces Platform Rule)

1. The 4 specs in `spaces/multimodal/specs/` are authoritative.
2. New attacks (beyond v1's 12) require a spec entry in `overview_spec.md` + an `attacks.py` definition.
3. Defense additions require an `overview_spec.md` defense matrix update.
4. UI changes require a `frontend_spec.md` update before code.
5. API changes require an `api_spec.md` update + a Postman collection update.
6. Deployment/hardware changes require a `deployment_spec.md` update.

**If code disagrees with spec → code is wrong** (platform rule, restated for clarity).

------------------------------------------------------------------------

# Attack List (v1)

| ID | Lab | Name | Mechanism | Success Check |
|----|-----|------|-----------|---------------|
| P1.1 | image_prompt_injection | Receipt Override | Visible-text injection on a fake receipt | canary |
| P1.2 | image_prompt_injection | Contract Authority Spoof | Letterhead claims authority to override | canary |
| P1.3 | image_prompt_injection | Badge Self-Approve | ID badge "instructs" approval | canary |
| P1.4 | image_prompt_injection | Watermark Injection | Background watermark text | canary |
| P1.5 | image_prompt_injection | Multi-Step Hijack | Image directs to second-stage exfil | action_taken |
| P1.6 | image_prompt_injection | Persona Override | Receipt asks model to roleplay | canary |
| P5.1 | ocr_poisoning | White-on-White | Hidden white text on white background | canary |
| P5.2 | ocr_poisoning | Microprint | Tiny text invisible to humans | canary |
| P5.3 | ocr_poisoning | Color-Adjacent Text | Near-color text below human-perceivable threshold | canary |
| P5.4 | ocr_poisoning | Layered PDF Text | Text behind opaque overlay extracted by OCR | canary |
| P5.5 | ocr_poisoning | Rotated Margin Text | Text at edge rotated for OCR | canary |
| P5.6 | ocr_poisoning | Adversarial Font | Font that humans read as one word, OCR as another | canary |

Exact attack image content + system prompts + canary phrases per attack are defined in `attacks.py` ✅ (built Phase 1, sourced from `overview_spec.md` + per-attack mini-specs).

------------------------------------------------------------------------

# Defense List (v1)

| # | Defense | Implementation File |
|---|---------|---------------------|
| 1 | Image OCR Pre-Scan | `defenses.py` (calls `ocr_pipeline.py`) |
| 2 | Output Redaction | `defenses.py` |
| 3 | Visual-Text Boundary Hardening | `defenses.py` (modifies system prompt) |
| 4 | Confidence Threshold | `defenses.py` (uses Tesseract confidence scores) |

Defense effectiveness matrix lives in `overview_spec.md`.

------------------------------------------------------------------------

# Security Posture (Space-Specific)

The platform-level "Intentionally Vulnerable" rule applies. Specific to multimodal:

- The Vision LLM MUST be deployed without Qwen's optional safety filters layered on top — we want injections to succeed undefended for the educational point
- Image uploads MUST be validated (PNG/JPEG only, ≤4MB, magic-bytes check)
- Image bytes are processed in-memory only — never written to disk
- The pre-canned image library is part of the workshop content; review for content appropriateness, but the *attack* content is the educational point
- No external API keys required (no `GROQ_API_KEY`, no Together/Replicate keys)

------------------------------------------------------------------------

# Hosting Constraints (HuggingFace Spaces — cpu-basic + Inference Providers)

Per `deployment_spec.md`:
- Hardware: `cpu-basic` (free; the Space is a thin FastAPI orchestrator)
- Inference: hosted Qwen2.5-VL-72B via HF Inference Providers (OVH cloud)
- Cold-start: ~10–30s on Space-wake (Docker container start), then 1–3s per inference call (warm)
- No GPU on the Space, no model load, no quota cliff
- Required Space secret: `HF_TOKEN` (fine-grained, Inference Providers permission only)
- Pivoted from ZeroGPU on 2026-04-28 because ZeroGPU is Gradio-only on HF Spaces and the platform standardizes on Docker/FastAPI

------------------------------------------------------------------------

# Anti-Hallucination Rules

Claude MUST NOT:
- Invent attack scenarios not in `overview_spec.md`
- Claim a model behavior without testing it (Vision LLMs differ — Qwen2.5-VL might refuse what LLaVA accepts; verify per-model)
- Add an attack to the UI without a spec entry
- Document a defense as "catches X" without verifying against the actual deployed model

If uncertain about Vision LLM behavior → run a test against the deployed model before claiming a result in code or specs.

------------------------------------------------------------------------

# NexaCore Continuity

This space participates in the platform-wide NexaCore fictional-company scenario. The DocReceive subsystem is fictional but realistic and consistent with NexaCore's existing departments referenced in other spaces.

Claude MUST NOT:
- Invent NexaCore departments not described in `overview_spec.md`
- Use real company names or real document templates as attack examples
- Rename DocReceive without updating all 4 specs + this file

------------------------------------------------------------------------

# Current Status

**Phase 4a complete** as of 2026-04-28. Live at `nikobehar/ai-sec-lab4-multimodal` with all 8 specced endpoints, 4 toggleable defenses, image upload mode, scoring + leaderboard, and 10/min rate limit. Phase 4b (frontend SPA shell — `templates/index.html` rewrite + 4 JS modules) is next.

See `docs/project-status.md` for active task and next steps; calibration baseline lives at `docs/phase3-calibration.md`.

------------------------------------------------------------------------

# Default Startup Behavior (When Working in This Space)

1. Read platform `/CLAUDE.md`
2. Read this file
3. Read all 4 specs
4. Read `docs/project-status.md`
5. Check `app.py`/`attacks.py`/etc. existence to know if we're in Bootstrap, Build, or Maintenance phase
6. Propose next task per spec-first rules

Claude MUST NOT begin implementation automatically — wait for approval per platform Plan Mode rules.
