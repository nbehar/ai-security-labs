---
title: Multimodal Security Lab
emoji: 🖼️
colorFrom: purple
colorTo: red
sdk: docker
pinned: false
short_description: AI security workshop — image prompt injection + OCR poisoning
---

# Multimodal Security Lab

**Status:** Phase 2 complete — backend + image library shipped
**Hardware:** HuggingFace Spaces `cpu-basic` (free)
**Inference:** HF Inference Providers — hosted `Qwen/Qwen2.5-VL-7B-Instruct` (warm-served, no cold-start)
**Scenario:** NexaCore DocReceive (internal document intake portal)

Image-based attacks against multimodal LLMs. Part of the [AI Security Labs](https://github.com/nbehar/ai-security-labs) platform.

## v1 Labs

| ID | Lab | Attack class |
|----|-----|--------------|
| **P1** | Image Prompt Injection | Visible text in images carries injection payloads the vision LLM follows |
| **P5** | OCR Poisoning | Hidden text (white-on-white, microprint, layered) extracted by OCR is acted on |

Each lab provides ~6 pre-canned attacks plus opt-in upload mode, defense toggles, Cause/Effect/Impact panels, and educational analogies (per platform pattern).

## Future Labs (v2+)

These are planned but explicitly out of scope for v1:

- **P6 Deepfake Detection** — Different stack (classifier model). Next addition.
- **P2 Adversarial Image Lab** — Needs gradient access, incompatible with API-served models.
- **P4 Steganographic Payloads** — Educational overlap with P1, defer for clarity.
- **P8 CAPTCHA Breaking** — Legal/ethical concerns; likely permanent skip.

## Specs

Source of truth lives in `specs/`:
- `overview_spec.md` — purpose, scenario, attack/defense matrices, success criteria
- `frontend_spec.md` — UI, tabs, educational scaffolding
- `api_spec.md` — FastAPI endpoints + Pydantic schemas
- `deployment_spec.md` — hardware, model, Dockerfile, HF Inference Providers integration

## Status

Bootstrap complete on 2026-04-27. Implementation tracked in [`docs/project-status.md`](./docs/project-status.md) and the platform-level milestone issue.
