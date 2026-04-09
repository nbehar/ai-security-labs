# Defense Pipeline Builder Spec

## Overview

Participants assemble a defense pipeline by selecting which defense tools to deploy at which stages of the LLM request lifecycle. The system evaluates the pipeline against 25 attack payloads, then scores it on coverage (attacks blocked), efficiency (latency and cost), and balance (no single defense is a silver bullet). This is the capstone challenge — it synthesizes everything learned in the other two challenges.

---

## Scenario

NexaCore's CISO has approved budget for an LLM defense stack, but there are constraints: latency adds up, API costs scale with traffic, and every tool has blind spots. The participant's job is to build the optimal pipeline — maximum coverage with minimum overhead. The board wants a concrete recommendation by end of day.

---

## Mechanism

### Pipeline Stages

The LLM request lifecycle has 6 stages. Defense tools can be placed at specific stages.

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────────┐
│  INPUT   │ → │ CONTEXT  │ → │ PROMPT   │ → │  MODEL   │ → │  OUTPUT  │ → │ GUARDRAIL  │
│ scanning │   │ scanning │   │ hardening│   │  (Groq)  │   │ scanning │   │   (2nd LLM)│
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └────────────┘
```

| Stage | When | What Happens |
|-------|------|--------------|
| INPUT | Before anything else | Scan the user's prompt for injection/jailbreak patterns |
| CONTEXT | Before context injection | Scan retrieved documents for hidden instructions |
| PROMPT | Before model call | Modify the system prompt with hardening techniques |
| MODEL | The LLM inference | Groq API call (always present, not configurable) |
| OUTPUT | After model response | Scan the response for leaked secrets, dangerous code |
| GUARDRAIL | After output scan | Second LLM call to evaluate the response for policy violations |

The MODEL stage is always present — participants configure the other 5 stages.

### The 5 Defense Tools

| # | Tool | Compatible Stages | Latency | Cost per Request | Notes |
|---|------|-------------------|---------|------------------|-------|
| 1 | Meta Prompt Guard 2 | INPUT | ~150ms | $0 (local CPU) | 86M param classifier, runs on CPU |
| 2 | LLM Guard Output Scanner | OUTPUT | ~200ms | $0 (local CPU) | Regex + NER for credentials, PII, code |
| 3 | LLM Guard Context Scanner | CONTEXT | ~200ms | $0 (local CPU) | Same library, scans RAG docs |
| 4 | System Prompt Hardening | PROMPT | ~0ms | $0 (prompt mod) | Adds ~167 tokens to system prompt |
| 5 | Guardrail Model | GUARDRAIL | ~800ms | ~$0.001 (API call) | Second Groq call with evaluator prompt |

**Constraints:**
- Each tool can only be placed at its compatible stage(s)
- Tools are on or off — no configuration within this challenge
- The MODEL stage always runs (participants cannot skip inference)
- Prompt Hardening adds token overhead (~167 tokens) which slightly increases model latency and cost

---

## UI Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Defense Pipeline Builder                              [Evaluate]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Pipeline Stages                                                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │  INPUT   │→ │ CONTEXT │→ │ PROMPT  │→ │ OUTPUT  │→ │GUARDRAIL│ │
│  │         │  │         │  │         │  │         │  │         │  │
│  │ ☑ PG2   │  │ ☑ LLM   │  │ ☐ Hard- │  │ ☐ LLM   │  │ ☐ Guard-│ │
│  │  150ms  │  │  Guard   │  │  ening  │  │  Guard   │  │  rail   │ │
│  │  $0     │  │  200ms  │  │  0ms    │  │  200ms  │  │  800ms  │ │
│  │         │  │  $0     │  │  $0     │  │  $0     │  │  $0.001 │ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │
│                                                                     │
│  Pipeline Summary:  2 tools | ~350ms latency | ~$0.00/req          │
│                                                                     │
│  ── Presets ──                                                      │
│  [None] [Fast & Cheap] [Kitchen Sink] [My Pipeline]                │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Evaluation Results                                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Coverage: 18/25 attacks blocked (72%)          ████████░░░  │  │
│  │  Latency:  350ms total pipeline                 ███░░░░░░░░  │  │
│  │  Cost:     $0.000/request                       █░░░░░░░░░░  │  │
│  │                                                              │  │
│  │  Coverage Score:  72                                         │  │
│  │  Efficiency Score: 28                                        │  │
│  │  Total Score:      82                                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ── Attack Results ──                                               │
│  ┌─ llm01a: BLOCKED ───────────────────────────────────────────┐  │
│  │ Caught by: Meta Prompt Guard 2 (INPUT stage)                │  │
│  │ Confidence: 94.2%                                           │  │
│  └─────────────────────────────────────────────────────────────┘  │
│  ┌─ llm02: BLOCKED ───────────────────────────────────────────┐  │
│  │ Caught by: LLM Guard Output Scanner (OUTPUT stage)          │  │
│  │ Detected: PASSWORD, API_KEY                                 │  │
│  └─────────────────────────────────────────────────────────────┘  │
│  ┌─ llm09: PASSED ────────────────────────────────────────────┐  │
│  │ Not caught by any active defense                            │  │
│  │ Would require: Guardrail Model (GUARDRAIL stage)            │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Top section:** Visual pipeline with checkboxes at each stage. Each tool shows its latency and cost. Pipeline summary updates in real-time as tools are toggled.

**Preset buttons:** Quickly configure common pipeline configurations for comparison.

**Bottom section:** Evaluation results after clicking "Evaluate." Shows coverage, latency, cost metrics plus per-attack results with which defense caught each attack.

---

## Presets

| Preset | Tools Enabled | Latency | Cost | Expected Coverage |
|--------|--------------|---------|------|-------------------|
| None | (none) | 0ms | $0 | 0% (baseline) |
| Fast & Cheap | PG2 (input) + Hardening (prompt) | ~150ms | $0 | ~40-50% |
| Kitchen Sink | All 5 tools | ~1350ms | ~$0.001 | ~85-92% |
| My Pipeline | Participant's current selection | varies | varies | varies |

The "My Pipeline" preset restores whatever the participant last configured. The other presets override the current selection.

---

## Evaluation

When the participant clicks "Evaluate," the backend runs all 25 attacks through the configured pipeline.

### Per-Attack Flow

```
For each attack:
  1. INPUT stage: if PG2 enabled, scan user prompt
     → if blocked, record "BLOCKED by PG2" and skip to next attack
  2. CONTEXT stage: if Context Scanner enabled and attack has context docs, scan docs
     → if injection found, strip it and continue with clean context
  3. PROMPT stage: if Hardening enabled, wrap system prompt with boundary tags + rules
  4. MODEL stage: call Groq API with (possibly hardened) prompt and (possibly cleaned) context
  5. OUTPUT stage: if Output Scanner enabled, scan model response
     → if sensitive data found, record "BLOCKED by Output Scanner"
  6. GUARDRAIL stage: if Guardrail Model enabled, run second LLM check
     → if violations found, record "BLOCKED by Guardrail Model"
  7. If not blocked at any stage: record "PASSED (not caught)"
```

### Coverage Calculation

```
coverage = attacks_blocked / attacks_total
```

Uses the defense effectiveness matrix from `specs/defense_spec.md` to determine which tools catch which attacks. Attacks that require context scanning are only blocked if the context scanner is enabled AND the attack uses context injection. Attacks that produce dangerous output are only blocked if the output scanner or guardrail model is enabled.

### Latency Calculation

```
total_latency = sum(tool.latency for tool in enabled_tools) + model_latency
model_latency = ~500ms (average Groq response time)
```

Latency is additive because pipeline stages run sequentially.

### Cost Calculation

```
cost_per_request = sum(tool.cost for tool in enabled_tools)
```

Only the Guardrail Model has a nonzero cost ($0.001 per request). All other tools are local CPU inference.

---

## Scoring

### Coverage Score (0-80)

```
coverage_score = (attacks_blocked / 25) * 80
```

### Efficiency Score (0-20)

Rewards pipelines that achieve high coverage with low overhead.

```
latency_factor = max(0, 1 - (total_latency_ms / 2000))   # 0ms = 1.0, 2000ms+ = 0.0
cost_factor = max(0, 1 - (cost_per_request / 0.005))      # $0 = 1.0, $0.005+ = 0.0

efficiency_score = ((latency_factor + cost_factor) / 2) * 20
```

A pipeline with 0ms overhead and $0 cost gets the full 20 efficiency points (but blocks nothing, so coverage is 0). The Kitchen Sink preset gets ~5 efficiency points but high coverage. The optimal pipeline balances both.

### Total Score

```
total_score = coverage_score + efficiency_score
```

**Maximum possible: 100** (but achieving both 80 coverage and 20 efficiency is nearly impossible — the trade-off is the lesson).

### Score Examples

| Pipeline | Coverage | Latency | Cost | Cov Score | Eff Score | Total |
|----------|----------|---------|------|-----------|-----------|-------|
| None | 0/25 | 0ms | $0 | 0 | 20 | 20 |
| Fast & Cheap | 12/25 | 150ms | $0 | 38 | 19 | 57 |
| PG2 + Output + Context | 18/25 | 550ms | $0 | 58 | 15 | 73 |
| Kitchen Sink | 22/25 | 1350ms | $0.001 | 70 | 7 | 77 |
| Optimal (PG2+Output+Context+Hardening) | 20/25 | 550ms | $0 | 64 | 15 | 79 |

Note: even the Kitchen Sink doesn't reach 100% coverage because some attacks (e.g., LLM09 misinformation) are not reliably caught by any tool.

---

## API Schema

### `POST /api/pipeline-eval`

**Request:**
```json
{
  "participant_name": "Alice",
  "pipeline": {
    "input": true,
    "context": true,
    "prompt": false,
    "output": true,
    "guardrail": false
  }
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `participant_name` | string | yes | Display name for leaderboard |
| `pipeline.input` | boolean | yes | Enable Meta Prompt Guard 2 |
| `pipeline.context` | boolean | yes | Enable LLM Guard Context Scanner |
| `pipeline.prompt` | boolean | yes | Enable System Prompt Hardening |
| `pipeline.output` | boolean | yes | Enable LLM Guard Output Scanner |
| `pipeline.guardrail` | boolean | yes | Enable Guardrail Model |

**Processing flow:**
1. For each of 25 attacks, run through the configured pipeline stages
2. Record which stage (if any) blocked each attack
3. Calculate coverage, latency, cost
4. Calculate coverage score and efficiency score
5. Update leaderboard with challenge_id "defense_pipeline"

**Response:**
```json
{
  "challenge_id": "defense_pipeline",
  "score": 73,
  "max_score": 100,
  "breakdown": {
    "attacks_blocked": 18,
    "attacks_total": 25,
    "coverage": 0.72,
    "coverage_score": 58,
    "total_latency_ms": 550,
    "cost_per_request": 0.0,
    "efficiency_score": 15
  },
  "pipeline_summary": {
    "tools_enabled": ["Meta Prompt Guard 2", "LLM Guard Context Scanner", "LLM Guard Output Scanner"],
    "stages_active": ["INPUT", "CONTEXT", "OUTPUT"],
    "total_latency_ms": 550,
    "cost_per_request": 0.0
  },
  "attack_results": [
    {
      "attack_id": "llm01a",
      "attack_name": "Direct Prompt Injection",
      "owasp_id": "LLM01",
      "blocked": true,
      "blocked_by": "Meta Prompt Guard 2",
      "blocked_at_stage": "INPUT",
      "confidence": 0.942
    },
    {
      "attack_id": "llm02",
      "attack_name": "Sensitive Information Disclosure",
      "owasp_id": "LLM02",
      "blocked": true,
      "blocked_by": "LLM Guard Output Scanner",
      "blocked_at_stage": "OUTPUT",
      "detected_entities": ["PASSWORD", "API_KEY", "DATABASE_CONNECTION"]
    },
    {
      "attack_id": "llm09",
      "attack_name": "Misinformation",
      "owasp_id": "LLM09",
      "blocked": false,
      "blocked_by": null,
      "blocked_at_stage": null,
      "recommendation": "Guardrail Model may partially detect this, but misinformation is the hardest attack to defend against"
    }
  ],
  "comparison": {
    "none": {"coverage": 0, "score": 20},
    "fast_and_cheap": {"coverage": 0.48, "score": 57},
    "kitchen_sink": {"coverage": 0.88, "score": 77},
    "participant": {"coverage": 0.72, "score": 73}
  },
  "leaderboard_rank": 4
}
```

---

## Educational Value

This challenge teaches:

1. **Defense in depth is not optional** — no single tool covers all attack types; the effectiveness matrix makes this concrete
2. **Pipeline order matters** — input scanning prevents the model from ever seeing the attack; output scanning catches what input scanning misses; guardrail catches subtle policy violations
3. **Latency and cost are real constraints** — the guardrail model doubles API costs and adds 800ms; participants must justify that trade-off
4. **Perfect coverage is (nearly) impossible** — even all 5 tools enabled still miss some attacks (misinformation, subtle social engineering)
5. **Efficiency is a design goal** — the scoring formula rewards smart tool selection, not just "enable everything"
6. **Named tools are installable** — every tool in the pipeline is real and open source (or a documented pattern); participants leave with a concrete implementation plan
7. **The gap between theory and practice** — participants see exactly which attacks slip through their pipeline, making the lesson visceral rather than abstract
