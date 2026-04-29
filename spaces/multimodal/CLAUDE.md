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
  .gitignore                Vendored brand assets + framework copies (Phase 4b ✅)
  specs/
    overview_spec.md        v1 scope, scenario, audience, success criteria
    frontend_spec.md        UI structure, tabs, educational scaffolding
    api_spec.md             FastAPI endpoints + Pydantic schemas
    deployment_spec.md      Hardware, model, Dockerfile, HF Inference Providers integration
  docs/
    project-status.md       Space-level status tracker
    phase3-calibration.md   Calibration baseline for the 4 defenses
  static/
    owl.svg                 Vendored Luminex brand mark (gitignored; see Vendored Assets) ✅
    css/
      luminex-tokens.css    Vendored from ~/luminex/brand-system/design-tokens.json (Phase 4b) ✅
      multimodal.css        Space-specific styles using Luminex tokens (Phase 4b) ✅
      styles.css            Framework copy (gitignored; copied at deploy time)
    js/
      app.js                SPA entry, /health probe, tab routing, Info + Defenses tabs (Phase 4b) ✅
      attack_runner.js      P1 + P5 lab tab renderer, Cause/Effect/Impact panels, score banner (Phase 4b) ✅
      image_gallery.js      Thumbnail grid + selection (Phase 4b) ✅
      image_upload.js       File picker + PNG/JPEG validation (Phase 4b) ✅
      core.js               Framework copy (gitignored; copied at deploy time)
    images/
      canned/               24 pre-canned images (12 attack + 12 legit) ✅ (committed `417f9d7`)
  templates/
    index.html              4-tab SPA shell with Luminex Learning master nav (Phase 4b ✅)
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
- **Theme:** Dark only — Luminex Learning brand system. AISL violet accent for product-scoped UI; brand gold for the master nav owl + wordmark. See Vendored Assets.

This space does **NOT** use Groq. The platform's `framework/groq_client.py` is unused here. Inference goes through `huggingface_hub.InferenceClient` instead.

------------------------------------------------------------------------

# Vendored Assets (Phase 4b)

This space is one of four Luminex Learning products (Red Team Labs, GRC Labs, AI Security Labs, Blue Team Labs). The brand identity is governed by `~/luminex/brand-system/` and enforced by the `brand-identity-enforcer` skill. Two artifacts are vendored into the space at build time:

| Asset | Source of truth | How it ships | Committed? |
|-------|-----------------|--------------|------------|
| `static/owl.svg` | `~/luminex/owl.svg` | `cp` to local working tree, then `hf upload --include="static/owl.svg"` to HF Space | **No** (~200KB, gitignored) |
| `static/css/luminex-tokens.css` | `~/luminex/brand-system/design-tokens.json` (full :root block) | Hand-vendored when tokens revise | **Yes** (5.5KB text, source-of-truth pinned by commit) |

**Master brand rules** (from `brand-identity-enforcer` SKILL.md, non-negotiable):
- Owl mark is rendered with `.owl-gold` (`--owl-filter-gold` filter). Always brand gold, never product accent.
- Wordmark is `Luminex Learning` (two words, both capitalized) in Inter 700.
- Page background is `#09090f` / `--color-bg-base` only.
- Approved fonts: Inter, JetBrains Mono. (DM Serif Display is marketing-only, never product UI.)
- AISL violet (`--color-accent-aisl-highlight #a78bfa`, `--color-accent-aisl-interactive #7c3aed`) is the product-scoped accent for tab underlines, primary CTAs inside lab panels, and the page-eyebrow.
- No hardcoded color primitives outside `luminex-tokens.css`.

If the brand system revises `design-tokens.json`, re-vendor `luminex-tokens.css` and re-deploy the space. Do not modify token values inline.

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
- Frontend XSS posture: every interpolated value passes through `escapeHtml`; renders use `Range.createContextualFragment` (`setHtml` helper in `app.js`) rather than direct innerHTML. Static template literals are author-trusted.

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
- Use `NexaCore` (or `NexaCore Technologies`) as the brand name for this product. The brand is **AI Security Labs / Luminex Learning**. NexaCore is the fictional in-product attack target only.

------------------------------------------------------------------------

# Current Status

**Phase 4b complete** as of 2026-04-29. Live at `nikobehar/ai-sec-lab4-multimodal` with the full Luminex Learning SPA shell: 4 tabs (Info / P1 / P5 / Defenses), master nav with brand-gold owl + "Luminex Learning" wordmark + "AI Security Labs" product label + "Multimodal" section, AISL violet accent for product-scoped UI, per-student inline scoring (no leaderboard tab).

**Workshop usage:** Individual graduate-course assignments (not competitive). The `POST /api/score` and `GET /api/leaderboard` backend endpoints stay alive for the eventual **Phase 6: Canvas LMS integration** (autograde + score submission via Canvas API).

**Next phases:**
- Phase 5: tighten spec gaps surfaced by deployment (calibration drift, defense details).
- Phase 6: Canvas LMS autograde + score push (deferred).

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
