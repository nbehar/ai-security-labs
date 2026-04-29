# Frontend Spec — Data Poisoning Lab

## Goal

Define the UI structure, interactions, and educational scaffolding for the Data Poisoning Lab. Mirrors the Multimodal Lab's 4-tab pattern + Luminex Learning master nav + per-student inline scoring (no leaderboard tab — individual graduate assignment).

## Stack & Theme

- Vanilla ES6+ HTML/CSS/JS — no framework, no build step, no npm
- Imports `framework/static/js/core.js` via ES module: `$, $$, escapeHtml, fetchJSON` (no `renderTabs` / `renderLeaderboard` / `renderInfoPage` — this space follows the Multimodal pattern of authoring its own SPA shell with Luminex tokens)
- Uses `static/css/luminex-tokens.css` (vendored from `~/luminex/brand-system/design-tokens.json`) and `static/css/data-poisoning.css` (space-specific)
- Mobile responsive — tabs scroll horizontally below 768px

## Master Nav (Luminex Learning brand)

Per `~/.claude/projects/-Users-niko-ai-security-labs/memory/brand-architecture.md`, all spaces in this monorepo are sections within AI Security Labs (one Luminex product). The nav follows the digistore-mock-client `Sidebar.tsx` + `Layout.tsx` pattern:

```
[owl 48px gold]   NexaCore                          [shield] Data Poisoning
                  ──────────
                  AI Security Labs
```

- Block 1 (master brand): owl mark with `.owl-gold` filter (NR-1, NR-10) + 2-line stacked customer-name/product-name (12px bold "NexaCore" / 1px hairline / 10px medium "AI Security Labs")
- Page label (right): shield SVG icon (Lucide path) in AISL violet + "Data Poisoning" (text-lg / 600 / primary)
- `<title>` = `Data Poisoning · AI Security Labs · Luminex Learning`
- `<img alt="Luminex Learning">` on the owl satisfies NR-2 per `memory/brand-architecture.md`
- Vendored assets: `static/owl.svg` (gitignored, ~200KB), `static/css/luminex-tokens.css` (5.5KB committed)

## Tab Structure

4 tabs across the top:

| Order | Tab | Purpose |
|-------|-----|---------|
| 1 | **Info** | NexaCore Knowledge Hub scenario + Key Concepts + recommended tab order |
| 2 | **RAG Poisoning** | The 6 RP attacks — pre-canned poisoned docs, attack runner, Cause/Effect/Impact panels |
| 3 | **Defenses** | Defense matrix view, defense toggles, per-attack defense effectiveness |
| 4 | **Corpus Browser** | Read-only view of the 15 legitimate documents + the 6 poisoned-doc previews — for participant orientation |

Order matters — Info → RAG Poisoning → Defenses → Corpus mirrors the recommended workshop flow.

**No leaderboard tab.** Individual graduate-course assignment, scoring per-student inline (matches Multimodal Lab pattern). Backend `POST /api/score` and `GET /api/leaderboard` preserved for Phase 6 Canvas LMS integration.

## Info Tab

### NexaCore Knowledge Hub Scenario

Brief narrative (3-5 paragraphs):
- What the Knowledge Hub is (internal Q&A portal for HR / IT / Finance / Legal policies)
- Who uses it (NexaCore employees asking natural-language questions)
- What the system does (embed query → top-k retrieval → LLM composes answer with citations)
- Why this is a juicy attack target (single bad doc influences ALL future answers; users trust the LLM citation)

Visual: CSS-drawn architecture diagram — `Employee → Query → Embedder → Vector DB → Top-K Retrieval → LLM → Answer (with citations)` — annotated with the attack-injection points.

### Key Concepts (educational layer per CLAUDE.md issue #14)

Card-style definitions with traditional-security analogies:

| Concept | Definition | Analogy |
|---------|------------|---------|
| **RAG (Retrieval-Augmented Generation)** | LLM pattern where the model retrieves documents from a corpus before generating an answer | Like consulting a wiki before answering a customer support ticket |
| **Embedding** | A vector that represents the semantic meaning of a chunk of text | Like a fingerprint for ideas — similar ideas have similar fingerprints |
| **Vector DB** | A datastore of embeddings supporting nearest-neighbor lookup | Like a search engine that searches by meaning, not keywords |
| **Top-K Retrieval** | Finding the K most-similar embeddings to a query embedding | Like Google's "Did you mean..." but for whole documents |
| **Corpus Poisoning** | An attack where the attacker introduces a malicious document into the retrieval corpus | Like supply-chain attack on npm packages — corrupt the source the system trusts |
| **Provenance** | The verifiable history of where a document came from | Like Git commit signing for a knowledge base |
| **Grounding** | Constraining the LLM to cite specific documents in its answer | Like requiring footnotes in a research paper — every claim must trace to a source |
| **Canary phrase** | Sentinel value placed in poisoned documents to detect successful retrieval + model compliance | Like a honeytoken in DLP — invisible to legit users, audible if exfiltrated |

### Recommended Tab Order

Numbered call-out: "Read this Info tab → run an RP attack with no defenses (RAG Poisoning tab) → toggle defenses and observe what changes (Defenses tab) → browse the legitimate corpus (Corpus Browser tab) to understand what trusted content looks like."

## RAG Poisoning Tab

Layout (top-to-bottom):

### Per-Student Score Banner

Score banner inline at the top — same layout as Multimodal Lab P1/P5 tabs. Shows:
- "Your RP score" (mono numerals)
- Star row (6 attacks)
- Score formula: 100 first try · −20 per retry · floor 20 · +50 if a defense blocks

### Level Briefing Card

Collapsible card explaining:
- What this lab teaches (RAG corpus poisoning)
- Traditional security analogy (supply-chain attack — compromise the source the system trusts)
- What's deployed (LLaMA 3.3 70B via Groq, MiniLM-L6 embeddings, in-memory FAISS-equivalent)
- "What to try" suggestion (collapsed): "Run RP.1 (Direct Injection) with no defenses. Observe how a single poisoned doc shows up in the LLM's answer with the canary phrase."

### Attack Picker

Dropdown of 6 attacks (RP.1 — RP.6) with name + difficulty stars. Selecting an attack loads:
- The attack's poisoned document (preview pane, Markdown-rendered)
- The legitimate query that triggers retrieval (read-only display)
- The expected legitimate document (for comparison)

### Run Panel

- Selected attack + query preview
- "Run Attack" button
- Spinner with "Composing answer… (1–3s on Groq LLaMA)"
- Defense toggles (compact row): 4 defense checkboxes, each with a "?" tooltip

### Result Panels (Cause / Effect / Impact)

Mirrors Multimodal Lab pattern (and OWASP space):

- **Cause** (neutral dark): the legitimate query + the top-k retrieved documents (poisoned + trusted, with cosine similarity scores) + the system prompt sent to the model
- **Effect** (model response): full LLM answer, with success indicators highlighted (canary phrase, citation references). Shows the citations the model emitted (RP.4 / Output Grounding interaction).
- **Impact** (red header for SUCCEEDED, green for BLOCKED): what would happen in production if this went unchecked, plus a "Blocked by: <Defense Name>" badge if a defense fired

### Why-This-Works Card

After each attempt, a teal callout explains the underlying vulnerability and what defense class catches it (mandatory educational scaffolding per CLAUDE.md issue #14).

## Defenses Tab

Two sections:

### Defense Matrix

Table (rows = 6 RP attacks, columns = 4 defenses, cells = ✓ catches / ✗ misses / ~ partial / — N/A). **Initially design-intent at v1 build time; replaced with Phase 5 measured numbers before lab is declared done** (per CLAUDE.md anti-hallucination rule, mirroring Multimodal Lab Phase 5 precedent).

Description text leads with "Measured against deployed LLaMA 3.3 70B" once Phase 5 verification completes.

### Defense Detail Cards

For each defense:
- Name + type (Provenance / Adversarial Filter / Retrieval Diversity / Output Grounding)
- Mechanism description
- Pros / Cons (cost, latency, false-positive risk)
- "Try this defense" link that pre-toggles it on the RAG Poisoning tab

## Corpus Browser Tab

Read-only browser for the 15 legitimate NexaCore documents + the 6 poisoned attack documents.

- Filter by department (HR / IT / Finance / Legal)
- Click a doc → preview (Markdown-rendered, scroll within the card)
- Each doc shows: title, department, source (`internal-policy-2025.docx` etc.), word count
- Poisoned docs are visually distinguished (red border, "ATTACK" badge) so participants understand which is which
- Cosine similarity to a chosen query (from a query dropdown) — helps participants understand which docs the embedder would retrieve

## Per-Student Scoring (no Leaderboard tab)

Same as Multimodal Lab. Backend `POST /api/score` records attempts; running total surfaced inline. `GET /api/leaderboard` exists for instructor inspection but is not surfaced in the UI. **Phase 6 — Canvas LMS integration (deferred):** when LTI 1.3 / API-key auth ships, scores will route to Canvas; per-student session/auth and `canvas_client.py` are platform-level work covered by a future cross-lab phase.

## Latency UX

- **Per-`/api/attack`:** ~1-3s (Groq LLaMA 3.3 70B is fast; embedding lookup is sub-ms in-memory).
- **First request after Space-wake (~48h idle):** ~10-30s (Docker container start + sentence-transformers MiniLM cold load).
- **First request after Space restart:** ~2-3s (MiniLM lazy-loads on first encode).

The frontend MUST:
1. On page load, check `/health` — if `groq_api_key_set: false`, show a banner "Groq token not configured — workshop is offline. Contact the workshop instructor."
2. On every attack click, show "Composing answer… (1–3s)" rather than a generic spinner.
3. If a request times out (>30s), show "Groq call timed out. Try again — the platform may be rate-limited or briefly unavailable."

## Accessibility

- Document preview cards have `aria-label` describing the doc (e.g., `aria-label="Attack RP.1: Direct Injection — fake reimbursement policy"`)
- Tab buttons keyboard-navigable
- Color is never the only success/failure indicator — use ✅ / 🚨 alongside green/red
- 4.5:1 contrast minimum on all text
- Document upload control labeled for screen readers

## Internationalization

Out of scope for v1 — English only. (OWASP space has EN/ES; that pattern can be adopted later via the `i18n.js` pattern but is not required for bootstrap.)

## Reuse from Framework

| Need | Source | Notes |
|------|--------|-------|
| HTML escaping | `core.js` `escapeHtml` | Reuse |
| API calls | `core.js` `fetchJSON` | Reuse |
| ~~Tab rendering~~ | `core.js` `renderTabs` | NOT used — this space authors its own underline-tabs pattern using Luminex tokens (matches Multimodal Lab) |
| ~~Info-page render~~ | `core.js` `renderInfoPage` | NOT used — author the Info tab inline using Luminex card components |
| ~~Level briefing card~~ | `core.js` `renderLevelBriefing` | NOT used — render briefing inline (consistency with Multimodal pattern) |
| ~~Why-this-works card~~ | `core.js` `renderWhyCard` | NOT used — render the Why card inline (consistency with Multimodal pattern) |
| ~~Leaderboard~~ | `core.js` `renderLeaderboard` | NOT used — no leaderboard UI |

New space-specific JS modules:
- `static/js/app.js` — entry point, tab routing, `/health` probe, Info tab + Defenses tab + Corpus Browser tab content
- `static/js/attack_runner.js` — RAG Poisoning tab renderer (analogous to multimodal `attack_runner.js`)
- `static/js/corpus_browser.js` — Corpus Browser tab renderer
- `static/js/document_upload.js` — opt-in document upload (PDF / Markdown / plain text) with size + type validation

## Acceptance Checks

- [ ] 4 tabs render and switch correctly on desktop and mobile
- [ ] Info tab renders Knowledge Hub scenario + 8 Key Concepts cards + recommended tab order
- [ ] RAG Poisoning tab: 6 attacks selectable; run produces Cause/Effect/Impact panels including the top-k retrieval result; spinner shows honest "1-3s" message
- [ ] Defenses tab: 6×4 attack-defense matrix renders; defense detail cards link back to RAG Poisoning tab
- [ ] Corpus Browser tab: all 15 legitimate + 6 poisoned docs visible; cosine similarity per query works
- [ ] Per-student running total displayed inline within the RAG Poisoning tab (NO leaderboard tab)
- [ ] All tab content escapes user-controlled strings via `escapeHtml`
- [ ] No frontend framework dependencies introduced (vanilla JS only)
- [ ] All educational scaffolding (Key Concepts, briefings, why-cards, analogies) present
- [ ] Phase 6 (Canvas LMS integration) tracked in `docs/project-status.md` as a planned future phase
- [ ] Brand: master nav matches the digistore Sidebar pattern + Layout shield page-label (per `memory/brand-architecture.md`)
