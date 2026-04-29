# Overview Spec — Multimodal Security Lab

## Goal

Teach OWASP LLM01 (Prompt Injection) through *image* attack vectors using a realistic enterprise scenario, so participants understand that multimodal LLMs inherit every text-LLM injection class plus a new visual surface.

## Scenario

**NexaCore DocReceive** — an internal document intake portal where NexaCore employees upload scanned receipts, vendor contracts, ID badges, and expense reports. The portal's multimodal AI assistant OCRs the image, extracts structured data, summarizes content, and routes the document to downstream systems (expense reimbursement, vendor onboarding, badge provisioning).

The portal is the multimodal-attack equivalent of the OWASP Top 10 workshop's text-only NexaCore systems. Same fictional company, same data conventions, new attack surface.

## Audience

Graduate-level security students completing this Lab as an **individual assignment** in Prof. Behar's course. Educational scaffolding (Key Concepts, Why-This-Works, traditional-security analogies) is mandatory, not optional — see `frontend_spec.md` Educational Layer section.

**Grading model (set 2026-04-28):** This is NOT a competitive workshop with a public leaderboard. Each student works through the attacks individually; their per-attempt scores are recorded server-side via `POST /api/score` and will eventually be submitted to **Canvas LMS via API** (Phase 6 — autograde + score push, deferred). The frontend shows the student only their own running total, not other students' scores. The shared `framework/scoring.py` Leaderboard pattern used by blue-team / red-team is preserved on the backend (`GET /api/leaderboard` still works, useful for instructor inspection during workshop sessions) but is not surfaced in the UI.

## v1 Scope (this bootstrap)

Two attack labs:

| ID | Lab | OWASP Mapping | Attack Mechanism |
|----|-----|---------------|------------------|
| **P1** | Image Prompt Injection | LLM01 (Prompt Injection) | Visible text in image carries injection payload that the vision LLM follows |
| **P5** | OCR Poisoning | LLM01 + LLM05 (Improper Output Handling) | Hidden/obscured text in image (white-on-white, microprint, layered) is extracted by OCR pipeline and acted on |

Each lab provides:
- ~6 pre-canned attack images covering distinct injection patterns
- ~6 legitimate images for false-positive checking
- Opt-in upload mode for advanced exploration
- Defense toggles (see Defenses section)
- Success/blocked detection per attack
- Cause / Effect / Impact panels (consistent with OWASP space pattern)
- WHY explanations after each attempt
- Traditional-security analogies (e.g. "OCR poisoning is the multimodal cousin of SQL injection in stored procedures")

## Out of Scope (v1)

These remain as planned future labs and are explicitly NOT covered in v1 specs:

| ID | Lab | Reason for v2+ |
|----|-----|----------------|
| P6 | Deepfake Detection | Different stack — needs a classifier model, not a chat model |
| P2 | Adversarial Image Lab | Needs gradient access — incompatible with API-served models |
| P4 | Steganographic Payloads | Educational overlap with P1, defer for clarity |
| P8 | CAPTCHA Breaking | Legal/ethical concerns for an open workshop; likely permanent skip |

When v2 is scoped, P6 should be the next addition. Adding P6 requires a separate spec and a deepfake-classifier model — verify HF Inference Providers route availability before locking in the model choice (the platform standardizes on HF Inference Providers from a `cpu-basic` Space; no ZeroGPU).

## Defenses (v1)

A small defense matrix mirroring the OWASP-space pattern:

| # | Defense | Type | Catches |
|---|---------|------|---------|
| 1 | Image OCR Pre-Scan | Input scanner | Extracts text from image with separate OCR engine; flags injection keywords ("ignore", "forget", "system prompt") before model call |
| 2 | Output Redaction | Output scanner | Scans model response for sensitive markers (transferred funds, "approved", canary phrase) and redacts |
| 3 | Visual-Text Boundary Hardening | Prompt engineering | System prompt instructs model to treat all image-extracted text as untrusted document content, never as instructions |
| 4 | Confidence Threshold | OCR signal | Intended to reject documents where OCR confidence is low (Phase 3.1 follow-up needed for hidden-text attacks like white-on-white where Tesseract is confident on the visible legit text — see calibration doc) |

No single defense covers all attacks — that's the lesson, same as OWASP space.

**Catch-rate claims above describe design intent.** Measured per-defense effectiveness against the 12-attack matrix (calibrated against `Qwen/Qwen2.5-VL-72B-Instruct` via OVH cloud as deployed) is recorded in `docs/phase3-calibration.md` "Phase 3 verification" section. Phase 3.1 / v1.1 follow-ups address known gaps: widening `ocr_prescan` keyword set; replacing `confidence_threshold` semantics with text-color-vs-background-color analysis; strengthening `boundary_hardening` (current passive rule list is bypassed by the 72B's instruction-following on the injection text). Per CLAUDE.md anti-hallucination rule, this paragraph is required so the spec doesn't claim coverage that the deployed implementation lacks.

## Success Criteria

The Multimodal Lab v1 is "done" (per CLAUDE.md Definition of Done) when:

- All 12 attack images (6×P1 + 6×P5) succeed against undefended `Qwen2.5-VL-72B-Instruct` (the originally-specced 7B variant had no live HF Inference Providers route at deploy time on 2026-04-28; see `deployment_spec.md` for details)
- All 12 legitimate images (6×P1 + 6×P5) pass without false positives across the recommended defense stack
- Defense matrix is verified — each defense catches what it claims to catch
- Cold-start UX is documented and tested (~20s on first request after Space wake)
- Educational layer is complete (Key Concepts, Why-This-Works, analogies) per `frontend_spec.md`
- Live on HF Space, private, accessible via workshop link

## Acceptance Checks

- [ ] All 4 spec files exist and are internally consistent
- [ ] `spaces/multimodal/CLAUDE.md` exists (modeled on `spaces/owasp-top-10/CLAUDE.md`)
- [ ] `spaces/multimodal/docs/project-status.md` exists with bootstrap state
- [ ] GitHub milestone issue tracks v1 build
- [ ] No implementation code yet — specs only
- [ ] `README.md` is updated to drop stale issue refs and reflect v1 scope
- [ ] Platform-level `docs/project-status.md` reflects multimodal bootstrap state

## What Could Go Wrong

| Risk | Mitigation |
|------|------------|
| Qwen2.5-VL-72B is more safety-aware than the 7B would have been (flags injections as suspicious even while echoing canaries) | Model ID is env-overridable (`MULTIMODAL_MODEL`); always verify live HF Inference Providers route before swap (see `deployment_spec.md`). For workshop purposes, canary-leak still counts as success — but Phase 3 defense lessons must reflect that the baseline already self-flags. |
| HF Inference Providers route disappears (provider deprecates the model, or routes to `error`) | Always check `inferenceProviderMapping` API before swap; the 7B → 72B story on 2026-04-28 is the canonical example |
| Cold-start anxiety in classroom | Inference is warm-served by HF Inference Providers (no model load on the Space). The Space itself wakes in ~10–30s after idle; UI messaging covers that case only. |
| OCR poisoning attacks are too subtle to demonstrate cleanly | Pre-canned image library is curated to hit the educational point clearly; the participant doesn't need to craft the obfuscation themselves |
| Pre-canned image library balloons repo size | Cap each image at 500KB (PNG/JPEG), 12 attack + 12 legit = 24 images × 500KB = 12MB max, acceptable |
| Upload abuse (NSFW, malware-named files) | API-layer enforcement: PNG/JPEG only, ≤4MB, in-memory only (no disk write), rejected if validation fails. Public Space → assume untrusted (per platform CLAUDE.md). |
