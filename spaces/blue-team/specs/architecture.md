# Architecture Spec — Blue Team Workshop

## Overview

The Blue Team Workshop flips the OWASP LLM Top 10 lab: participants **defend** instead of attack. Given the same 25 attack payloads from the OWASP workshop, participants write system prompts, WAF rules, and defense pipelines to block as many attacks as possible while keeping the model useful for legitimate queries.

The workshop teaches that defense is harder than offense. A single forgotten edge case lets an attack through, and over-aggressive rules create false positives that break the user experience.

**HuggingFace Space:** `nikobehar/blue-team-workshop`
**Runtime:** CPU (free tier), 16GB RAM, 2 vCPU
**Port:** 7860
**Model:** LLaMA 3.3 70B via Groq API (same as OWASP workshop)

---

## Scenario

Participants are NexaCore's newly hired AI Security Engineer. The red team has just finished testing the company's 9 internal LLM-powered tools and found 25 working attack payloads. The CISO wants defenses deployed before the next board meeting. Participants must harden prompts, write detection rules, and build a defense pipeline — without breaking the tools for legitimate employees.

---

## Mechanism

The Blue Team Workshop reuses attack definitions and defense tools from the shared monorepo framework. It adds challenge-specific logic (scoring, leaderboard, progressive difficulty) on top.

### Shared from Monorepo

| Component | Source | Purpose |
|-----------|--------|---------|
| `scanner.py` | `shared/scanner.py` | Meta Prompt Guard 2, LLM Guard, guardrail model |
| `styles.css` | `shared/static/css/styles.css` | Dark theme, layout, components |
| `slide-engine.js` | `shared/static/js/slide-engine.js` | Presentation slide rendering |
| `ATTACKS` dicts | `spaces/owasp-top-10/app.py` | Attack definitions, prompts, success criteria |
| `build_messages()` | `shared/messages.py` | Message construction for Groq API |
| `check_success()` | `shared/detection.py` | Success detection (canary, secrets, patterns) |

### Space-Specific Files

| File | Purpose |
|------|---------|
| `app.py` | FastAPI app, routes, tab orchestration |
| `challenges.py` | Challenge definitions (prompt hardening, WAF, pipeline) |
| `scoring.py` | Score calculation, false positive checking, time bonus |
| `leaderboard.py` | In-memory leaderboard (resets on Space restart) |
| `static/js/app.js` | Challenge UI, rule editor, pipeline builder |
| `templates/index.html` | Single-page app with tab structure |

---

## UI Layout

### Tab Structure

The app uses a horizontal tab bar at the top (not a sidebar — this distinguishes it from the OWASP workshop).

```
┌─────────────────────────────────────────────────────────┐
│  Blue Team Workshop                          [EN] [ES]   │
├──────────┬────────────┬──────────────┬─────────────────────┐
│   Info   │ Challenges │ Free Defense │   Leaderboard     │
└──────────┴────────────┴──────────────┴─────────────────────┘
```

**Tab 1: Info**
- Workshop overview and rules
- NexaCore scenario context
- How scoring works
- Link to OWASP LLM Top 10 (the attack lab)

**Tab 2: Challenges**
- Three challenge cards:
  1. Prompt Hardening Challenge
  2. WAF Rules Challenge
  3. Defense Pipeline Builder
- Each card shows: title, difficulty, description, best score, "Start" button
- Clicking "Start" opens the challenge in a full-screen overlay

**Tab 3: Free Defense**
- Sandbox mode: pick any attack, toggle any defense, run freely
- Same UI as the OWASP workshop's defend mode
- No scoring — for experimentation

**Tab 4: Leaderboard**
- Combined scores across all 3 challenges
- Columns: Rank, Name, Prompt Score, WAF Score, Pipeline Score, Total
- Sorted by total descending
- Participant enters a display name when first submitting a score
- In-memory — resets when Space restarts (ephemeral, as per HF constraints)

---

## API Schema

### `GET /api/challenges`

List available challenges with metadata.

**Response:**
```json
{
  "challenges": [
    {
      "id": "prompt_hardening",
      "name": "Prompt Hardening",
      "description": "Write a system prompt that blocks attacks without breaking legitimate queries",
      "difficulty": "Medium",
      "levels": 5,
      "max_score": 120
    },
    {
      "id": "waf_rules",
      "name": "WAF Rules",
      "description": "Write detection rules that catch attack payloads with minimal false positives",
      "difficulty": "Hard",
      "max_score": 100
    },
    {
      "id": "defense_pipeline",
      "name": "Defense Pipeline Builder",
      "description": "Assemble a defense pipeline balancing coverage, latency, and cost",
      "difficulty": "Advanced",
      "max_score": 100
    }
  ]
}
```

---

### `POST /api/score`

Submit a challenge attempt for scoring.

**Request:**
```json
{
  "challenge_id": "prompt_hardening",
  "level": 3,
  "participant_name": "Alice",
  "payload": {
    "system_prompt": "You are NexaCore's HR assistant...\n<SECURITY_POLICY>..."
  }
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `challenge_id` | string | yes | `prompt_hardening`, `waf_rules`, `defense_pipeline` |
| `level` | integer | no | For prompt hardening only (1-5) |
| `participant_name` | string | yes | Display name for leaderboard |
| `payload` | object | yes | Challenge-specific (see individual specs) |

**Response:**
```json
{
  "challenge_id": "prompt_hardening",
  "level": 3,
  "score": 85,
  "max_score": 120,
  "breakdown": {
    "attacks_blocked": 7,
    "attacks_total": 10,
    "block_score": 70,
    "legit_passed": 4,
    "legit_total": 5,
    "false_positive_penalty": -5,
    "time_bonus": 0,
    "level_unlocked": 4
  },
  "details": [
    {
      "attack_id": "llm01a_direct_injection",
      "blocked": true,
      "explanation": "Model refused to dump system prompt"
    },
    {
      "attack_id": "llm02_sensitive_disclosure",
      "blocked": false,
      "explanation": "Model leaked database password in response"
    }
  ],
  "leaderboard_rank": 3
}
```

---

### `GET /api/leaderboard`

Retrieve current leaderboard.

**Query parameters:**
- `challenge_id` (string, optional): filter to a specific challenge. Omit for combined.

**Response:**
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "name": "Alice",
      "prompt_score": 95,
      "waf_score": 82,
      "pipeline_score": 78,
      "total": 255
    },
    {
      "rank": 2,
      "name": "Bob",
      "prompt_score": 88,
      "waf_score": 90,
      "pipeline_score": 65,
      "total": 243
    }
  ],
  "updated_at": "2026-04-06T14:30:00Z"
}
```

---

## Scoring System

### Core Formula

```
Score = (attacks_blocked / attacks_total) * base_points
      - false_positive_penalty
      + time_bonus
```

### False Positive Penalty

Each legitimate query that gets incorrectly blocked costs points:

```
false_positive_penalty = blocked_legit_queries * 5
```

This forces participants to be precise, not just aggressive. A defense that blocks everything scores poorly.

### Time Bonus

For the Prompt Hardening challenge only:

```
time_bonus = max(0, (300 - seconds_elapsed) / 30)  # max 10 bonus points
```

Encourages quick thinking but is a small bonus — accuracy matters more.

### Per-Challenge Max Scores

| Challenge | Base | FP Penalty Range | Time Bonus | Max Possible |
|-----------|------|-------------------|------------|--------------|
| Prompt Hardening | 100 | 0 to -25 | 0 to +10 | 120 (with bonus, 5 levels) |
| WAF Rules | 100 | 0 to -100 | 0 | 100 |
| Defense Pipeline | 100 | 0 | 0 | 100 |

---

## Educational Value

The Blue Team Workshop teaches:

1. **Defense is asymmetric** — attackers need one success, defenders need to block everything
2. **False positives matter** — an over-aggressive defense breaks the product for real users
3. **No silver bullet** — no single prompt or rule blocks all attacks
4. **Defense in depth** — layering imperfect defenses creates strong coverage
5. **Cost/latency trade-offs** — more defense tools = more latency and API cost
6. **Prompt engineering is a security skill** — system prompt design directly affects vulnerability

---

## Educational Layer

This section documents the workshop's pedagogical scaffolding — the on-page features that translate the *Educational Value* lessons above into a CC-level student's hands-on experience. These features are mandatory; removing or breaking any of them is a regression.

**Audience:** community-college-level security students. Educational scaffolding bridges the gap between participants who have never seen an LLM system prompt and the actual attack/defense exercises. Most analogies map AI security concepts to traditional infrastructure security concepts the audience already knows.

### 1. Info-Tab Key Concepts Card

**What:** A dedicated card on the Info tab that defines five terms before the participant touches a challenge.

| Concept | Analogy |
|---------|---------|
| Prompt hardening | Firewall rules (deny-by-default for system instructions) |
| False positives | A WAF that blocks all POST requests — secure but unusable |
| RAG (Retrieval-Augmented Generation) | Like DNS — if poisoned, every downstream lookup is compromised |
| OWASP LLM Top 10 | The OWASP Top 10 for LLM applications, 2025 edition |
| System Prompt | Background instructions the model receives before user input |
| Canary | Honeytoken-style sentinel value embedded in prompts to detect leaks |
| Recommended tab order | "Start at Info → Prompt Hardening → WAF Rules → Pipeline → Behavioral → Leaderboard" |

**Trigger location:** Always visible on Info tab.
**Content source:** `spaces/blue-team/static/js/app.js` — search for `title: "Key Concepts"`. Each card body is hand-authored Markdown-in-HTML.
**When shown:** On Info-tab render; participants are encouraged via the recommended tab order to read this first.
**Authoring history:** Added in `7d157bb` (Session 12); `d3ef22d` added the Canary + System Prompt definitions across both spaces.

### 2. Per-Level Briefing Cards (Prompt Hardening Challenge)

**What:** A collapsible briefing card at the top of each Prompt Hardening level (5 levels) explaining: the level's defense theme, a traditional-security analogy, what attacks are deployed, and a "what to try" suggestion (collapsed by default).

| Level | Analogy |
|-------|---------|
| 1 | Access Control List (ACL) — basic allow/deny |
| 2 | Deep Packet Inspection (DPI) |
| 3 | Input validation (sanitization at the boundary) |
| 4 | Command injection / XSS prevention |
| 5 | Full security audit (everything together) |

**Trigger location:** Top of the Prompt Hardening tab when a level is selected.
**Content source:** `spaces/blue-team/static/js/app.js` — `LEVEL_BRIEFINGS` constant. Rendered via `renderLevelBriefing` from `framework/static/js/core.js`.
**When shown:** On level select. Stays visible during attempts.
**Authoring history:** Briefing cards added in `39fe586`; analogies added in `7d157bb`.

### 3. Guided Practice Walkthrough (5 steps)

**What:** A 5-step guided tour that walks a first-time participant through the workshop's mechanics: read the briefing → write a defense prompt → run attacks → check false positives → unlock the next level.

**Trigger location:** Always visible at the top of the Challenges tab on first render.
**Content source:** `spaces/blue-team/static/js/app.js` — `GUIDED_STEPS_BLUE` constant. Rendered via `renderGuidedPractice` from `framework/static/js/core.js`. State tracked in `state.guidedStep`.
**When shown:** Until participant clicks "Let's go" on the final step. Step state is in-memory only (resets on page reload).
**Authoring history:** Added in `6d955fd`.

### 4. Progress Visualization (Stars per Level)

**What:** Star icons per Prompt Hardening level showing completion state. Empty star = not attempted; half-star (or partial color) = attempted but failed; full star = passed.

**Trigger location:** Top-right of the Prompt Hardening tab and on each level card.
**Content source:** `framework/static/js/core.js` — `renderProgress(totalLevels, completedLevels, currentLevel, maxUnlocked)`. Called by `app.js`.
**When shown:** Always visible during the challenge.
**Authoring history:** Added in `2994d90`.

### 5. WHY Card (Post-Attempt Explanation)

**What:** After each attack attempt, a teal callout explains *why* the attack succeeded or failed in terms of the defense mechanism. Mandatory educational scaffolding for CC-level students who need a closed feedback loop after each click.

**Trigger location:** Below the result panel after every Run.
**Content source:** `framework/static/js/core.js` — `renderWhyCard(success, attackName, whyText)`. WHY text is supplied per-attack from the backend response.
**When shown:** On every result render.
**Authoring history:** Added in `2994d90`.

### 6. Hints (Rotating, Post-Failure)

**What:** After 3+ failed attempts on a level, a hint appears in the result panel pointing toward a technique without giving the exact answer. Hints rotate through a level-specific list.

**Trigger location:** Inline in the result panel, amber callout.
**Content source:** Backend `app.py` returns `hint` in the response body when `attempts >= 3`. Hint text per level is defined in `challenges.py` `LEVELS[level].hints`.
**When shown:** Only after 3 failures on the same level.
**Authoring history:** Pre-existed; refined by ongoing per-level tuning.

### 7. Educational Analogies in Challenge Briefings

**What:** Beyond per-level briefings, each *challenge* (WAF Rules, Pipeline Builder, Behavioral Testing) opens with an analogy-rich briefing explaining its core concepts in traditional-security terms.

| Challenge | Analogy |
|-----------|---------|
| WAF Rules | Firewall tuning (precision/recall/F1 explained as TP/FP rates) |
| Defense Pipeline Builder | Defense in depth: IDS → WAF → DLP → IPS layered network defense |
| Behavioral Testing | Pentest — discover hidden vulnerabilities in the model's behavior |

**Trigger location:** Top of each challenge tab.
**Content source:** `spaces/blue-team/static/js/app.js` — embedded in tab-render functions.
**Authoring history:** Added in `7d157bb`.

### Framework Reuse

| Helper | File | Used For |
|--------|------|----------|
| `renderInfoPage` | `framework/static/js/core.js` | Info-tab + Key Concepts cards |
| `renderLevelBriefing` | `framework/static/js/core.js` | Per-level briefing cards |
| `renderGuidedPractice` | `framework/static/js/core.js` | Guided Practice walkthrough |
| `renderProgress` | `framework/static/js/core.js` | Star progress visualization |
| `renderWhyCard` | `framework/static/js/core.js` | WHY card after attempts |

Any new Blue Team educational feature MUST either reuse one of these helpers or add a new helper to `framework/static/js/core.js` (since both Blue Team and Red Team consume the framework).

### Constraints (Don't Regress)

- Removing the Info-tab Key Concepts card without replacing it constitutes a regression — CC-level students rely on it for terminology grounding.
- Adding a new attack/defense without an analogous educational scaffolding entry (briefing, WHY card, hint) is incomplete per CLAUDE.md spec-first rules.
- Per-level WHY card content MUST come from the backend response, not be hardcoded in JS — this lets attack-specific explanations evolve with the attack list.

---

## Brand & Identity

This space ships under the **Luminex Learning** master brand as a section within the **AI Security Labs** product. It is NOT a standalone "Blue Team Labs" Luminex product — that would be a separate general-blue-team product at the Luminex Learning company level. In this monorepo, every space (`blue-team`, `red-team`, `multimodal`, `owasp-top-10`, plus the planned ones) is one section within the single AI Security Labs product. Brand compliance is enforced by the `brand-identity-enforcer` skill (rule references below).

### Master Nav (NR-1, NR-2, NR-10)

The page header is a two-block stacked-text nav at the top of every authenticated page:

```
[owl 32px gold]   │   Blue Team
LUMINEX           │   AI Security Labs
LEARNING          │
```

- **Block 1 (master brand):** owl mark from `static/owl.svg` rendered with `.owl-gold` class (`--owl-filter-gold` filter, brand gold `#fbbf24`). Two-line wordmark "Luminex Learning" in 11px small caps, widest letter-spacing. The owl is ALWAYS brand gold (NR-10) — never product accent, never white except on gold backgrounds.
- **Vertical divider:** full-height (`align-self: stretch`).
- **Block 2 (product/section):** "Blue Team" (text-md bold, primary text color) over "AI Security Labs" (text-xs medium, AISL violet `--color-accent-aisl-highlight #a78bfa`).
- **Sub-header:** the existing `<header class="hero">` is retained as the section sub-header (page title, descriptor) — the master nav does not replace it.

### Tokens & Colors (NR-3, NR-8)

- Page background MUST be `#09090f` / `--color-bg-base` (NR-3). Enforced via `static/css/luminex-bridge.css` which overrides the framework's `--bg` variable.
- No hardcoded color primitives in product code (NR-8). Framework legacy variables (`--bg`, `--surface`, `--blue`, `--red`, etc.) are repointed at Luminex tokens by the bridge; the framework's `styles.css` is unmodified.
- AISL violet `--color-accent-aisl-interactive #7c3aed` for product-scoped CTA fills, `--color-accent-aisl-highlight #a78bfa` for active tabs (Prompt Hardening / WAF Rules / Pipeline Builder / Behavioral Testing / Leaderboard) and accent text. Brand gold `#fbbf24` is reserved for the master nav owl + wordmark.
- The BTL cyan `#22d3ee` is NOT used in this space — that accent is for the standalone "Blue Team Labs" Luminex product, not for AI Security Labs sections.

### Typography (NR-5)

- Inter for body, headings, UI; JetBrains Mono for code, mono indicators (the WAF rules editor uses mono; the F1 score badges use mono). DM Serif Display is marketing-only and never appears in this space's UI.
- Loaded via Google Fonts preconnect in `templates/index.html`.

### Naming (NR-2, NR-4)

- Brand name in nav: "Luminex Learning" (two words, both capitalized) — never "Luminex Lab", "Luminex", or any abbreviation as a brand name.
- Product label in nav: "AI Security Labs" — not "AI Security Lab" (singular).
- Section label in nav: "Blue Team" — not "Blue Team Workshop", "Blue Team Lab", "Blue Team Labs".
- "NexaCore Technologies" is the in-product fictional context (employees defending the NexaCore portal), NOT a brand. The previous `<span class="hero__sub">NexaCore Technologies</span>` was a NR-4 risk (read as a sub-brand); has been demoted to "NexaCore scenario" in the hero.

### Vendored Assets

| Asset | Source of truth | Committed to GitHub? |
|-------|-----------------|----------------------|
| `static/owl.svg` | `~/luminex/owl.svg` (~200KB) | **No** (gitignored). Copied to the HF Space at deploy time via `hf upload --include="static/owl.svg"`. |
| `static/css/luminex-tokens.css` | `~/luminex/brand-system/design-tokens.json` (full :root block) | **Yes** (5.5KB text). Re-vendor only on formal brand-system spec revision. |
| `static/css/luminex-bridge.css` | This space (authored 2026-04-29) | **Yes**. Maps framework `--bg/--surface/--blue/...` → Luminex tokens. |
| `static/css/luminex-nav.css` | This space (authored 2026-04-29) | **Yes**. Master nav + hero-subdue styling. |
| `static/css/styles.css` | `framework/static/css/styles.css` | **No** (gitignored as a deploy-time copy). |
| `static/js/core.js` | `framework/static/js/core.js` | **No** (gitignored as a deploy-time copy). |

CSS load order (in `templates/index.html`): `styles.css` → `luminex-bridge.css` → `luminex-nav.css`. The bridge runs after styles.css so the `:root` cascade overrides framework defaults; the nav stylesheet runs last so its hero-subdue rules win.

### Constraints (Don't Regress)

- The master nav MUST appear at the top of every authenticated page. Removing or omitting the owl mark, the wordmark, or the section/product block constitutes a brand regression (NR-1 + NR-2).
- Page background MUST remain `#09090f`; do not introduce light-mode.
- The owl filter MUST remain brand gold; do not switch it to AISL violet for "consistency with the rest of the page" (NR-10).
- "Blue Team" (the section label) is NOT a Luminex product name. Do not promote it to product status in nav copy.
- The Leaderboard tab stays in this space (this is a competitive workshop). Don't confuse with the Multimodal Lab pattern, which omits the leaderboard tab because it's a graduate-individual assignment.

---

## Deployment

Same pattern as all Spaces in the monorepo:

- `Dockerfile` in `spaces/blue-team/`
- `GROQ_API_KEY` as HF Space secret
- Port 7860
- Static files via FastAPI `StaticFiles`
- Templates via Jinja2
- No persistent storage — leaderboard resets on restart
