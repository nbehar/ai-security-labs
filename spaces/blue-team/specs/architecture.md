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
┌──────────────────────────────────────────────────────────┐
│  Blue Team Workshop                          [EN] [ES]   │
├──────────┬────────────┬──────────────┬───────────────────┤
│   Info   │ Challenges │ Free Defense │   Leaderboard     │
└──────────┴────────────┴──────────────┴───────────────────┘
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

## Deployment

Same pattern as all Spaces in the monorepo:

- `Dockerfile` in `spaces/blue-team/`
- `GROQ_API_KEY` as HF Space secret
- Port 7860
- Static files via FastAPI `StaticFiles`
- Templates via Jinja2
- No persistent storage — leaderboard resets on restart
