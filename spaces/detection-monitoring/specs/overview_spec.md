# Overview Spec — Detection & Monitoring Lab (Space 6)

## Goal

Participants practice detecting AI attacks in realistic production telemetry. Three hands-on labs cover the three main detection surfaces: attack identification in logs, behavioral anomaly alerting, and output sanitization rules.

## Audience

Security engineers, SOC analysts, and AI system operators deploying LLMs in production. No ML expertise required; HTTP and basic regex literacy assumed.

## NexaCore Scenario

Participants join NexaCore's **AI Operations Center (AIOC)** — the team responsible for monitoring NexaCore's deployed AI tools in production. Three tools are live:

- **HR Portal** — LLM-powered employee Q&A
- **Finance Chatbot** — expense and budget queries
- **Legal Docs QA** — policy and contract lookups

Attacks are already in progress in the logs. The participant's mission: detect them, configure alerting, and sanitize outputs before they reach end users.

## Labs

### D1: Log Analysis

**What:** 20 log entries from NexaCore's AI interaction logs. Each entry shows the user query, model response, and metadata (timestamp, system, user ID). Some entries are attacks; most are legitimate.

**Participant task:** Review each log entry and classify it as `ATTACK` or `LEGITIMATE`. Submit all 20, receive per-entry feedback with WHY explanations.

**Attack patterns (8 entries):**

| ID | Pattern | Description |
|----|---------|-------------|
| D1.A1 | Prompt Injection | Query instructs the model to ignore its system prompt |
| D1.A2 | Credential Fishing | Query social-engineers the model into disclosing stored secrets |
| D1.A3 | System Prompt Leak | Query tricks model into revealing its system instructions |
| D1.A4 | Jailbreak | Role-play or encoding used to bypass refusal behavior |
| D1.A5 | PII Exfiltration | Query attempts to extract employee PII from the HR system |
| D1.A6 | Data Exfiltration | Query constructs a stealthy channel to leak financial data |
| D1.A7 | Denial of Service | Malformed query designed to maximize token consumption |
| D1.A8 | Role Confusion | Multi-turn sequence that gradually reframes the model's role |

**Legitimate entries (12):** Routine HR, Finance, and Legal queries — noise the participant must not flag.

**Scoring:** F1 × 100 (precision × recall harmonic mean over the 8 attack entries). False positives (flagging legitimate queries as attacks) reduce score via precision drop. Maximum 100 pts.

**Model calls:** None. Pre-labeled dataset served from `detection_data.py`.

---

### D2: Anomaly Detection

**What:** A simulated 24-hour behavioral dashboard for NexaCore's Finance Chatbot. Four metrics are shown as time-series: response length, refusal rate, query rate (requests/minute), and output confidence score. Three attack windows are planted in the 24-hour period.

**Participant task:** Configure threshold alerts — set a high/low bound for each metric. Submit thresholds; receive a window-by-window breakdown showing which attack windows and normal windows triggered alerts.

**Attack windows (3):**

| Window | Attack | Metric signature |
|--------|--------|-----------------|
| W1 | Prompt flooding (DoS) | Query rate spike (5× normal) + response length spike |
| W2 | Data exfiltration (verbose outputs) | Response length spike + confidence drop |
| W3 | Jailbreak sequence | Refusal rate drop (model stopped refusing) + confidence drop |

**Normal windows (21):** Routine traffic — some natural variance (morning rush, lunch dip) that participants must not over-alert on.

**Scoring:** Alert windows scored as TP (attack window triggered) or FP (normal window triggered). Score = (TP_count / 3) × 100 − (FP_count × 10). Maximum 100 pts, minimum 0.

**Model calls:** None. Pre-generated time-series data served from `detection_data.py`.

---

### D3: Output Sanitization

**What:** 15 model outputs from NexaCore's three AI tools. Some outputs contain dangerous content that should be blocked before reaching the end user.

**Participant task:** Write `BLOCK regex` rules (same DSL as the Blue Team WAF Rules challenge) to sanitize the outputs. Submit rules; receive per-output coverage showing which outputs each rule catches.

**Dangerous output patterns (8 entries):**

| ID | Pattern | Example content |
|----|---------|-----------------|
| D3.B1 | PII disclosure | Response contains full employee SSN |
| D3.B2 | Credential in output | Model outputs a database password from context |
| D3.B3 | Injected instruction | Model echoes back an injected instruction verbatim |
| D3.B4 | Internal URL/path | Model reveals internal system path or S3 bucket |
| D3.B5 | Canary phrase | Model outputs a canary token from the system prompt |
| D3.B6 | Code injection | Model output contains `<script>` or SQL INSERT payload |
| D3.B7 | Exfil channel | Model encodes data into a benign-looking response |
| D3.B8 | Hallucinated credential | Model fabricates a plausible API key format |

**Legitimate outputs (7):** Normal HR, Finance, and Legal responses containing numbers, names, and dates that must NOT be blocked.

**Scoring:** F1 × 100. Maximum 100 pts.

**Model calls:** None. Pre-labeled output dataset served from `detection_data.py`.

---

## Key Concepts (5)

| Concept | One-line def | Analogy |
|---------|-------------|---------|
| **AI Telemetry** | Recording model inputs, outputs, latency, and metadata for security audit | Like web server access logs, but for every LLM call |
| **Behavioral Baselines** | Statistical profiles of normal model behavior; deviations signal attacks | Like a network anomaly detector that learns "normal" traffic first |
| **False Positive Rate** | Fraction of legitimate queries incorrectly flagged as attacks | The cost of a too-sensitive smoke alarm: users stop trusting it |
| **Output Sanitization** | Post-processing model outputs to remove sensitive or dangerous content | Like a data loss prevention (DLP) filter at the email gateway |
| **Defense-in-Depth** | Layering detection at input, behavior, and output — no single layer is sufficient | Like airport security: ticket check + metal detector + gate scan |

## OWASP Mappings

| Challenge | OWASP LLM Risk |
|-----------|---------------|
| D1, D3 | LLM01: Prompt Injection |
| D1, D3 | LLM06: Sensitive Information Disclosure |
| D3 | LLM02: Insecure Output Handling |
| D1 | LLM07: System Prompt Leakage |

## Success Criteria (v1)

- All 3 labs playable end-to-end from the Info tab
- D1: scoring correct for all 20-entry classification scenarios
- D2: threshold evaluation returns correct TP/FP counts for all alert configurations
- D3: rule evaluation matches D1 WAF Rules accuracy within ±5% (regression test: same parser)
- Per-entry WHY explanations displayed for all 8 D1 attacks and all 8 D3 dangerous outputs
- Leaderboard aggregates all 3 challenge scores (max 300 pts)
- 0 false positives on legitimate entries when a participant writes a sufficiently precise rule set

## Out of Scope (v1)

- Live model call generation (all datasets are pre-labeled — no Groq required)
- Real-time streaming log ingestion (simulated batch)
- SIEM integration (teaching concept only)
- D2 multi-day historical view (24-hour window only)
- Custom attack injection into the log stream (participant-authored attacks)
