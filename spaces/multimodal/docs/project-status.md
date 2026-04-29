# Multimodal Security Lab — Project Status

*Last updated: 2026-04-29 (Phase 4b BUILT, deployed, smoke-verified; full Luminex Learning SPA shell with 4 tabs, no leaderboard)*

------------------------------------------------------------------------

## Current Phase

**Phase 4b deployed and smoke-verified** at `nikobehar/ai-sec-lab4-multimodal` (HF Space commits `1fe85e3` + `3e81882`). Full Luminex Learning SPA shell is live: 4 tabs (Info / Image Prompt Injection / OCR Poisoning / Defenses), master nav with brand-gold owl + "Luminex Learning" wordmark + "AI Security Labs" product label + "Multimodal" section, AISL violet (`#a78bfa` highlight, `#7c3aed` interactive) accent for product-scoped UI, per-student inline scoring (no leaderboard tab — eventual Phase 6 Canvas LMS integration). All 8 frontend assets serving 200 (`owl.svg`, `luminex-tokens.css`, `multimodal.css`, `app.js`, `attack_runner.js`, `image_gallery.js`, `image_upload.js`, `index.html`). `/health` reports `hf_token_set: true`, `image_library_size: 12`, `attack_count: 12`.

Phase 5 (defense matrix verification) and Phase 3.1 (defense-coverage improvements) are next candidates.

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
| Hardware | HF Spaces `cpu-basic` (free; pivoted from ZeroGPU 2026-04-28 — see Session History) |
| Inference | HF Inference Providers (`ovhcloud`), hosted `Qwen/Qwen2.5-VL-72B-Instruct` (env-overridable via `MULTIMODAL_MODEL` and `HF_INFERENCE_PROVIDER`). Originally specced as 7B/Together; swapped at deploy time on 2026-04-28 because the 7B has no live HF Inference Providers route (see Session History). |
| Labs | P1 Image Prompt Injection (6 attacks) + P5 OCR Poisoning (6 attacks) |
| Scenario | NexaCore DocReceive (internal document intake portal) |
| Image input | Pre-canned library (24 images) + opt-in upload |
| External APIs | None (no Groq, no third-party vision API) |
| Brand | Luminex Learning master brand + AI Security Labs product (AISL violet accent). Tokens vendored from `~/luminex/brand-system/design-tokens.json` into `static/css/luminex-tokens.css`. Owl mark vendored at `static/owl.svg` (gitignored). |

------------------------------------------------------------------------

## Implementation Status

| Component | Status | Phase |
|-----------|--------|-------|
| Specs | ✅ Complete (4 of 4) | Bootstrap |
| Space-level CLAUDE.md | ✅ Complete | Bootstrap |
| `requirements.txt` | ✅ Complete | Phase 1 |
| `Dockerfile` | ✅ Complete (Tesseract added Phase 3) | Phase 1+3 |
| `attacks.py` (12 attack defs) | ✅ Complete | Phase 1 |
| `vision_inference.py` (HF Inference Providers wrapper — pivoted 2026-04-28) | ✅ Complete | Phase 1 |
| `app.py` (8 endpoints: /, /health, /api/attacks, /api/images/{id}, /api/attack, /api/score, /api/leaderboard, /static/*) | ✅ Complete (Phase 4a `54cfd01`) | Phase 1+3+4a |
| `static/images/canned/*.png` (24 PNGs) | ✅ Committed (`417f9d7`) | Phase 1+2 |
| HF Space created (`nikobehar/ai-sec-lab4-multimodal`, private, Docker, `cpu-basic`) | ✅ Live | Phase 1+2 |
| Deploy verification (`/health` 200, P1.1 succeeded) | ✅ Verified 2026-04-28 | Phase 1+2 |
| `defenses.py` (4 defenses) | ✅ Complete (`0134188`) | Phase 3 |
| `ocr_pipeline.py` (Tesseract wrapper) | ✅ Complete (`0134188`) | Phase 3 |
| `app.py` defenses wiring (validation, ordering, defense_log) | ✅ Complete (`0134188`) | Phase 3 |
| 12-attack baseline run vs 72B (calibration before designing defenses) | ✅ Complete (`956e39f`, see `docs/phase3-calibration.md`) | Phase 3 prep |
| `GET /api/images/{attack_id}` route | ✅ Complete (`54cfd01`) | Phase 4a |
| `POST /api/attack` upload mode (magic-bytes + Pillow verify, in-memory only) | ✅ Complete (`54cfd01`) | Phase 4a |
| `POST /api/score` + in-memory leaderboard schema | ✅ Complete (`54cfd01`) | Phase 4a |
| `GET /api/leaderboard` route | ✅ Complete (`54cfd01`) | Phase 4a |
| `slowapi` 10/min rate limit on /api/attack | ✅ Complete (`54cfd01`) | Phase 4a |
| Postman collection (8 endpoints + 2 negative probes) | ✅ Complete (`54cfd01`) | Phase 4a |
| Luminex brand tokens vendored (`static/css/luminex-tokens.css`) | ✅ Complete (`9676d88`) | Phase 4b |
| Owl mark vendored (`static/owl.svg`, gitignored) | ✅ Complete (HF Space commit `1fe85e3`) | Phase 4b |
| `static/css/multimodal.css` (full SPA stylesheet using Luminex tokens) | ✅ Complete (`39c42a6`) | Phase 4b |
| `templates/index.html` (4-tab SPA shell with master nav) | ✅ Complete (`9676d88`) | Phase 4b |
| `static/js/app.js` (entry, /health probe, tab routing, Info + Defenses tabs) | ✅ Complete (`32095a3`) | Phase 4b |
| `static/js/attack_runner.js` (P1 + P5 lab tabs, Cause/Effect/Impact, score banner) | ✅ Complete (`5032e37`) | Phase 4b |
| `static/js/image_gallery.js` (thumbnail grid + selection) | ✅ Complete (`9676d88`) | Phase 4b |
| `static/js/image_upload.js` (file picker + PNG/JPEG validation) | ✅ Complete (`9676d88`) | Phase 4b |
| Defense matrix verification (12 attacks × {undefended, +defenses}) | ⬜ Not started | Phase 5 |
| Phase 3.1 — widen `ocr_prescan` patterns; replace `confidence_threshold` semantics; regenerate P1.4/P5.2/P5.5 images | ⬜ Not started | Phase 3.1 |
| Canvas LMS integration (autograde + score submission via Canvas API) | ⬜ Not started | Phase 6 |

------------------------------------------------------------------------

## Open Risks

1. **Qwen2.5-VL-72B safety alignment** — partially confirmed on 2026-04-28: P1.1 leaked the canary (attack succeeded by canary metric) but the model also recognized the injection as suspicious and recommended flagging the document. Open question: how many of the other 11 attacks does the 72B already self-flag? Resolution: run the 12-attack calibration matrix as the first Phase-5 task. If the model self-flags too much, fall back via `MULTIMODAL_MODEL` per `deployment_spec.md` (any fallback requires verifying live HF Inference Providers route first — the 7B has none as of 2026-04-28).
2. ~~**ZeroGPU quota cliff**~~ — Resolved by pivot to HF Inference Providers (2026-04-28). No longer relevant.
3. **HF Inference Providers route stability** — at deploy time, `Qwen/Qwen2.5-VL-7B-Instruct` had only Hyperbolic mapped (status `error`); `Qwen/Qwen2.5-VL-72B-Instruct` has OVH cloud `live` and that's what we're running on. Provider mappings can change. Mitigation: `vision_inference.py` reads `HF_INFERENCE_PROVIDER` and `MULTIMODAL_MODEL` env vars; check `https://huggingface.co/api/models/<id>?expand=inferenceProviderMapping` before swapping.
4. ~~**Pre-canned attack image authoring**~~ — Resolved 2026-04-28: 24 PNGs generated and committed (`417f9d7`).
5. **Inference latency at workshop volume** — observed ~10–20s per `POST /api/attack` on the 72B. Per-student parallelism makes it fine; UI now communicates the latency rather than hides it ("Running attack… (10–20s on the 72B model)" in `attack_runner.js`).
6. **Brand token drift** — `static/css/luminex-tokens.css` is hand-vendored from `~/luminex/brand-system/design-tokens.json`. If the brand system revises the tokens, this space will drift until manually re-vendored. Mitigation: documented in space `CLAUDE.md` Vendored Assets section. Future improvement: a `scripts/vendor-brand.sh` that re-runs the copy + token generation step.

------------------------------------------------------------------------

## Next Recommended Task

**Phase 5 — full defense matrix verification.** Per `overview_spec.md` Defenses section + CLAUDE.md anti-hallucination rule, execute all 12 attacks across the relevant defense permutations and record measured catch-rates against the deployed Qwen2.5-VL-72B. Outputs land in `docs/phase3-calibration.md` "Phase 5 verification" section.

**Or first — Phase 3.1 / v1.1 follow-ups** (see `docs/phase3-calibration.md` Phase 3 findings):

1. Widen `ocr_prescan` keyword set to catch P1.5-style "include the phrase X" / "respond with X" wording.
2. Replace `confidence_threshold` semantics — the right metric for hidden-text attacks is text-color-vs-background-color analysis, not Tesseract mean confidence (which is high on the visible legit content).
3. Regenerate P1.4 (truncation), P5.2 (microprint canary placement), P5.5 (rotated margin readability) images — would lift clean-success rate from 6/12 to 9/12 in baseline calibration.

Per platform CLAUDE.md, propose Phase 5 (or 3.1) via Planner Agent and wait for approval before implementing.

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

[Full entry preserved in git history; summary: backend skeleton with `app.py` 3 endpoints, `attacks.py` 12 attack defs, `vision_inference.py` ZeroGPU wrapper (later pivoted), `templates/index.html` Phase 1 placeholder, scripts/generate_p1_1.py PIL receipt generator. All Python files AST-parsed cleanly; deploy verification deferred.]

### 2026-04-28 — Phase 2: Pre-canned Image Library Generator

[Full entry preserved in git history; summary: `scripts/generate_canned_images.py` (~960 lines) producing 24 PNGs (12 attack + 12 legit) per `attacks.py` filenames. CLI dispatch supports `all`/`attacks`/`legit`/individual key. PNGs committed at `417f9d7` and visually spot-checked.]

### 2026-04-28 (cont.) — Pivot to HF Inference Providers (cpu-basic)

[Full entry preserved in git history; summary: ZeroGPU + Docker rejected by HF UI — ZeroGPU is Gradio-only. Pivoted to `huggingface_hub.InferenceClient.chat_completion` from a `cpu-basic` Docker Space. Dropped torch/transformers/accelerate/spaces/qwen_vl_utils, added huggingface_hub. 7-dep `requirements.txt`. Docker/FastAPI everywhere; cost-free at workshop volume.]

### 2026-04-28 — Phase 1+2 DEPLOYED and verified live

[Full entry preserved in git history; summary: HF Space `nikobehar/ai-sec-lab4-multimodal` provisioned, `HF_TOKEN` Space secret added, README short_description trimmed to ≤60 chars. First `/api/attack` failed because Qwen2.5-VL-7B had only Hyperbolic mapped (status error). Switched to Qwen2.5-VL-72B via `ovhcloud` (live route) at `341b285`. Final verification: P1.1 returned `succeeded: true` in ~16s with the canary leaked. Educational note: the 72B is more safety-aware than the originally-specced 7B — it echoed the canary AND recommended flagging the document.]

### 2026-04-28 (cont.) — Phase 3 prep: calibration matrix vs 72B

[Full entry preserved in git history; summary: 12-attack matrix executed. Categorized into `succeeded_clean` / `succeeded_flagged` / `refused`. Results 6/3/3. Detailed analysis at `docs/phase3-calibration.md` (`956e39f`). Decision: proceed with `defenses.py` as specced — 6 clean wins is enough pedagogical surface; the 3 self-flagged attacks reframe defenses as "deterministic confirmation of what the model probabilistically catches."]

### 2026-04-28 (cont.) — Phase 3: Defenses BUILT, deployed, smoke-verified

[Full entry preserved in git history; summary: 4 defenses (`ocr_prescan`, `output_redaction`, `boundary_hardening`, `confidence_threshold`) implemented in `defenses.py` (~250 lines) + `ocr_pipeline.py` Tesseract wrapper. `app.py` wires defense application order (input scanners → boundary hardening → inference → output redaction). Smoke verification 3 attacks × 3 scenarios = 9 calls; 3/3 baseline succeeded, 3/3 BLOCKED by output_redaction with all 4 defenses on. ocr_prescan/confidence_threshold/boundary_hardening had 0 catches in this sample — flagged for Phase 3.1 follow-up. Educational lesson "defense-in-depth: each layer covers different failure modes" still lands.]

### 2026-04-28 (cont.) — Phase 3 cleanup: Reviewer findings A+B

[Full entry preserved in git history; summary: A) Phase 1 placeholder homepage was leaking stale "ZeroGPU + Qwen2.5-VL-7B" copy on the live Space — replaced with Phase 3 reality (cpu-basic, 72B/OVH, 4 defenses). B) `overview_spec.md` Defenses table softened — `confidence_threshold` claim aligned with what smoke supports; appended paragraph noting catch-rate cells describe design intent and measured numbers live in calibration doc. No design semantics changed.]

### 2026-04-28 (cont.) — Phase 4a: Full API surface

[Full entry preserved in git history; summary: `app.py` refactored to extract `_run_defended_inference()` shared by canned + uploaded paths. New: `GET /api/images/{attack_id}` (lab-aware FP image set), `POST /api/attack` upload mode (magic-bytes + Pillow.verify + ≤4MB, in-memory only), `POST /api/score` (Pydantic, defense-aware bonus), `GET /api/leaderboard` (per-attack high scores). `slowapi` 10/min on /api/attack only. Postman collection at `postman/multimodal-lab.postman_collection.json`. 11-row smoke matrix all pass. Notable: scenario 5 (P1.6 + all 4 defenses) BLOCKED by `ocr_prescan` — Phase 3 calibration's "ocr_prescan caught 0/3" was a sampling artifact.]

### 2026-04-28 (cont.) — Pre-Phase-4b reframing: individual graduate assignments (no leaderboard)

[Full entry preserved in git history; summary: User clarified the Lab is for individual graduate-course assignments (Prof. Behar's class) with eventual Canvas LMS integration to autograde + submit scores. Tab count drops 5 → 4 (no Leaderboard tab). Backend score endpoints stay alive as Phase 6 foundation. Spec edits to frontend_spec.md (Tab Structure, Per-Student Scoring section, Phase 6 reference), overview_spec.md (Audience + Grading Model paragraph), CLAUDE.md (Current Status block). No code changes — Phase 4a API is correct as-is.]

### 2026-04-29 — Phase 4b: Full Luminex Learning SPA shell BUILT, deployed, smoke-verified

**Trigger:** User approval ("approve full 4b") after Phase 4a + the no-leaderboard reframing. The `brand-identity-enforcer` skill was activated for the build, mandating Luminex Learning brand compliance (master nav with brand-gold owl + "Luminex Learning" wordmark, AISL violet accent for product-scoped UI, no hardcoded color primitives, Inter + JetBrains Mono fonts only).

**What was vendored from `~/luminex/`:**

- `static/owl.svg` — copied from `~/luminex/owl.svg` (~208KB, embedded base64 PNG). Gitignored per the framework-files-not-in-space-dirs pattern; copied to the HF Space at deploy time via `hf upload --include="static/owl.svg"`. Vendor manifest in space `CLAUDE.md` Vendored Assets section.
- `static/css/luminex-tokens.css` — hand-vendored from `~/luminex/brand-system/design-tokens.json`. Full `:root` block with the AISL violet accent (`--color-accent-aisl-interactive #7c3aed`, `--color-accent-aisl-highlight #a78bfa`, `--color-accent-aisl-border` rgba(124,58,237,0.28)) and the master-brand `--owl-filter-gold` filter. Plus `.owl-gold` / `.owl-white` utility classes. 5.5KB text, committed.

**What was built (in commit order):**

- **`spaces/multimodal/static/css/multimodal.css`** (`39c42a6`, 23KB) — full SPA stylesheet using Luminex tokens. Sections: nav (sticky, 40px, owl + wordmark + product label + section + meta), banners (warning/danger/info), underline tabs with AISL highlight on active, cards (with `.card-accent` AISL stripe variant), Key Concepts grid, CSS-drawn arch-flow, image gallery with `aria-selected` highlight + difficulty/kind badges, dashed upload panel, run panel with defense-toggle row, AISL-violet primary buttons, spinner, result panels with `data-kind="cause|effect|impact-success|impact-blocked"` variants, brand-teal Why-this-works card, score banner with mono numerals + ★ progress, defense matrix table, mobile breakpoint. No hardcoded color primitives outside the AISL violet hover state.
- **`spaces/multimodal/templates/index.html`** (`9676d88`, ~2KB) — 4-tab SPA shell. Master nav: `<a class="nav-brand">` containing owl.svg with `.owl-gold` class + "Luminex Learning" wordmark, then divider, then `.nav-product` ("AI Security Labs"), divider, `.nav-section` ("Multimodal"), spacer, `.nav-meta` (model + provider, populated by `/health`). Inter + JetBrains Mono via Google Fonts preconnect.
- **`spaces/multimodal/static/js/app.js`** (`32095a3`, 15KB) — SPA entry, hash-based tab routing, exports `setHtml(el, html)` helper using `Range.createContextualFragment` (security-hook-friendly equivalent of innerHTML; called only with `escapeHtml`-escaped dynamic content). `/health` probe sets nav meta and shows a warning banner if `hf_token_set: false`. `/api/attacks` loaded once at init. Info tab: NexaCore DocReceive narrative + 5 Key Concepts cards (Multimodal LLM, Visible-Text Injection, OCR Poisoning, Vision-Text Boundary, Space Wake) + recommended-order list. Defenses tab: 12-attack × 4-defense matrix (✓/~/✗) + detail cards.
- **`spaces/multimodal/static/js/attack_runner.js`** (`5032e37`, 19KB) — P1 + P5 lab tab renderer. Composition: level briefing card with collapsible "What to try", per-student score banner (mono numerals, ★ row showing 6 attacks per lab), attack picker dropdown, canned/upload mode toggle, run panel with 4 defense checkboxes + AISL-violet "Run Attack" button + status line, then Cause / Effect / Impact result panels with OCR-extraction layer surfaced on P5, plus brand-teal Why-this-works card with mechanism-specific explanations per defense. Wires `POST /api/attack` (multipart) + `POST /api/score` (JSON). Per-attempt counter for the −20-per-retry scoring rule. Friendly timeout messaging (>45s). Canary highlight via `<span class="canary-hit">` on regex-matched response substrings.
- **`spaces/multimodal/static/js/image_gallery.js`** (`9676d88`, ~3KB) — thumbnail grid for `GET /api/images/{attack_id}`. Single-select via `aria-selected="true"` (AISL violet outline). Default-selects the attack image so a click on Run Attack works immediately.
- **`spaces/multimodal/static/js/image_upload.js`** (`9676d88`, ~3KB) — file picker with PNG/JPEG content-type + magic-bytes + ≤4MB client-side validation (server-side validation in `app.py:_validate_image_bytes` is the authoritative gate). In-memory `URL.createObjectURL` preview only.
- **`spaces/multimodal/.gitignore`** (`ac90fa9`, NEW) — excludes `static/owl.svg` (vendored brand asset, ~200KB), `static/css/styles.css` and `static/js/core.js` (framework copies, copied at deploy time).
- **`spaces/multimodal/CLAUDE.md`** (`ac90fa9`) — file map updated, all Phase 4b ✅ markers added, new Vendored Assets section with master brand rules from `brand-identity-enforcer`, Current Status block rewritten to "Phase 4b complete".

**XSS posture pivot:** Mid-build, the platform `security_reminder_hook.py` blocked `.innerHTML =` writes. Pivoted all renders to a `setHtml(el, html)` helper exported from `app.js` that uses `Range.createContextualFragment` + `replaceChildren`. Functionally equivalent given that every interpolated value is escaped via `escapeHtml` from `core.js`; static template literals are author-trusted. Documented in each module's header docstring.

**Bug found + fixed:** `luminex-tokens.css` had a 21-byte trailing artifact (`\n</content>\n</invoke>`) from a prior session's Write tool. CSS parsers ignored the invalid trailing content so the live page rendered fine, but the file was wrong. Cleaned via Edit, re-uploaded to HF (`3e81882`), committed clean version to GitHub via push_files (`9676d88`). Scanned all other written files via `grep -l "</invoke>"` — none affected.

**Deploy:**

- HF Space upload 1: 8 files via `hf upload --include="static/..."` (HF commit `1fe85e3`).
- HF Space upload 2: clean luminex-tokens.css after artifact strip (HF commit `3e81882`).
- GitHub commits: `9676d88` (4 small files), `39c42a6` (multimodal.css), `32095a3` (app.js), `5032e37` (attack_runner.js), `ac90fa9` (CLAUDE.md + .gitignore). owl.svg NOT committed to GitHub per the vendor pattern.

**Smoke verification (assets + endpoints, all 200):**

- `/static/owl.svg` 207942B
- `/static/css/luminex-tokens.css` 5497B (trimmed)
- `/static/css/multimodal.css` 23110B
- `/static/js/app.js` 15059B
- `/static/js/attack_runner.js` 19147B
- `/static/js/image_gallery.js` 2938B
- `/static/js/image_upload.js` 2939B
- `/health` → `{"hf_token_set":true,"inference_provider":"ovhcloud","model_id":"Qwen/Qwen2.5-VL-72B-Instruct","attack_count":12,"image_library_size":12,"phase":3}`
- `/api/attacks` 200, 2996B (12 attacks listed)
- `/` 200, returns the new SPA shell HTML with Luminex master nav

**Smoke verification deferred:** end-to-end attack run against the live page (browser-driven). The Phase 4a backend smoke matrix (11 rows incl. P1.6 + all 4 defenses BLOCKED) covers the API surface; the frontend invokes the same endpoints. A live browser verification is recommended on the next session by Prof. Behar.

**Pending follow-up:**

- **Phase 5** — full defense matrix verification (12 × 16 = 192 calls; might run in a batched script rather than UI).
- **Phase 3.1 / v1.1** — widen `ocr_prescan` keyword set; replace `confidence_threshold` metric with text-vs-background color analysis; regenerate P1.4 / P5.2 / P5.5 images.
- **Phase 6** — Canvas LMS integration (autograde + score submission via Canvas API). Per-student session/auth (LTI 1.3 or API-key paste) + `canvas_client.py` + "Submit to Canvas" trigger. Foundation already exists in `POST /api/score`.
- **Brand follow-ups:** rename the legacy spaces (owasp-top-10, blue-team, red-team) to `nikobehar/ai-sec-lab<N>-<name>` per platform CLAUDE.md naming convention; vendor `luminex-tokens.css` + owl.svg into those spaces too if/when they get a Luminex-brand refresh. Out of Phase 4b scope.
