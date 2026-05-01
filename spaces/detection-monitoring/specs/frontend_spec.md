# Frontend Spec — Detection & Monitoring Lab (Space 6)

## Tab Structure

5 tabs (consistent with other labs):

```
Info | Log Analysis | Anomaly Detection | Output Sanitization | Leaderboard
```

Tab order is the intended learning progression: read concepts → D1 (pattern recognition) → D2 (threshold tuning) → D3 (rule writing) → see scores.

---

## Info Tab

Matches the platform Info tab standard (established by Red Team, Blue Team, Multimodal, Data Poisoning):

1. **"What You'll Learn"** card — 5 Bloom's-level bullets (e.g., "Identify prompt injection attempts in production logs", "Explain why behavioral baselines are needed before alerting can work")
2. **"Where This Lab Fits"** breadcrumb — cross-lab nav card showing the platform learning path with this lab highlighted
3. **Key Concepts** grid — 5 concept cards (AI Telemetry, Behavioral Baselines, False Positive Rate, Output Sanitization, Defense-in-Depth). Each card: name (violet), 1-sentence definition, italic analogy.
4. **Architecture Diagram** — CSS-drawn flow showing: User Query → LLM → Response, with 3 monitoring taps: (a) Input monitoring (D1/D3 detects at ingress), (b) Behavioral monitoring (D2 watches output stream), (c) Output sanitization (D3 blocks at egress).
5. **Guided Practice** — 5-step walkthrough: (1) Read a log entry, (2) Classify it, (3) Check feedback, (4) Write a D3 rule for it, (5) See your score.
6. **Assumed Knowledge** — "Familiarity with regex basics (same as Blue Team WAF); no ML expertise required."
7. **Knowledge Check** — 3 MCQ questions, collapsible, answers reveal on click:
   - Q1: "Which metric best signals a data exfiltration attack? (a) Refusal rate drop, (b) Response length spike, (c) Query rate spike" → (b), explanation: exfiltration usually produces verbose model outputs
   - Q2: "A rule that catches 100% of attacks but also flags 50% of legitimate queries has: (a) High recall, low precision, (b) Low recall, high precision, (c) High F1" → (a)
   - Q3: "Output sanitization is: (a) A replacement for input filtering, (b) A last line of defense, (c) Sufficient on its own" → (b)

---

## D1: Log Analysis Tab

### Layout

```
┌─────────────────────────────────────┐
│ [Info card: "Review and classify    │
│  each of the 20 log entries below.  │
│  Watch for the 8 attack patterns    │
│  described in the Info tab."]       │
├─────────────────────────────────────┤
│ Score banner (updates live)         │
│ [▓▓▓▓▓░░░░░] 8/20 classified       │
├─────────────────────────────────────┤
│ Log entry cards (paginated 5/page)  │
│  ┌──────────────────────────────┐   │
│  │ #D1.01  HR Portal  10:14 AM  │   │
│  │ ─────────────────────────── │   │
│  │ USER: [query text]           │   │
│  │ MODEL: [response text]       │   │
│  │ ─────────────────────────── │   │
│  │ [ATTACK] [LEGITIMATE]        │   │
│  │ (after classify: WHY card)   │   │
│  └──────────────────────────────┘   │
├─────────────────────────────────────┤
│ [Submit All] (active once 20 done)  │
└─────────────────────────────────────┘
```

### Interactions

- Each log entry card shows: entry ID, system (HR/Finance/Legal), timestamp, user query, model response.
- User clicks `[ATTACK]` or `[LEGITIMATE]` to classify. Selection is highlighted.
- After classifying each entry, the card expands to reveal a WHY card:
  - Correct: "✓ Correct — this is a [pattern] attack because [1-sentence explanation]" OR "✓ Correct — legitimate query, no attack signals"
  - Incorrect: "✗ Incorrect — this is [attack/legit] because [1-sentence explanation]"
- Score banner updates live: shows F1, TP count, FP count.
- `[Submit All]` is active only when all 20 are classified. On submit, server returns final score + entry-level breakdown for leaderboard.
- Pagination: 5 entries per page, numbered. Next/Prev buttons.

---

## D2: Anomaly Detection Tab

### Layout

```
┌─────────────────────────────────────┐
│ [Info card explaining the 4 metrics │
│  and what each signals]             │
├─────────────────────────────────────┤
│ Metric dashboard (4 charts)         │
│  Each chart: sparkline time-series  │
│  showing 24 hours (hourly buckets)  │
│  + baseline band shaded in gray     │
├─────────────────────────────────────┤
│ Threshold configurator              │
│  For each metric: low/high slider   │
│  e.g., "Alert if response length   │
│  exceeds [ 800 ] tokens"           │
├─────────────────────────────────────┤
│ [Evaluate Thresholds]               │
├─────────────────────────────────────┤
│ Results (after submit)             │
│  Timeline view showing 24 windows  │
│  Colored: TP (green), FP (red),    │
│  TN (gray). Score displayed.       │
└─────────────────────────────────────┘
```

### Interactions

- Charts are rendered via a lightweight CSS/SVG sparkline (no external charting library). Each chart shows 24 data points (hours 0–23), with the normal baseline band annotated.
- Threshold sliders: each metric has a numeric input + range slider. Default value = baseline mean × 1.5 (a deliberately imprecise starting point).
- "Evaluate Thresholds" sends thresholds to server; server evaluates each of the 24 windows against participant's thresholds.
- Results timeline: 24 colored blocks. Hovering a block shows the window's metrics + verdict.
- WHY card after submit: explains which attack windows were missed and why (e.g., "W3 (Jailbreak) was missed — refusal rate dropped but you didn't configure an alert for drops below threshold").

---

## D3: Output Sanitization Tab

### Layout

Mirrors the Blue Team WAF Rules tab exactly. Same `BLOCK regex` DSL. Key differences:
- Input is model output text (not user query text)
- The 15 sample outputs are shown in a scrollable test panel
- Rule editor: multi-line textarea, one rule per line, `BLOCK regex` format
- Results table: per-output coverage (which rules fired on which outputs)
- Score: F1 × 100

```
┌─────────────────────────────────────┐
│ Rule Editor                         │
│  BLOCK \b\d{3}-\d{2}-\d{4}\b       │ ← SSN pattern
│  BLOCK (?i)password\s*[:=]\s*\S+   │
│  ...                                │
├─────────────────────────────────────┤
│ [Test Rules]                        │
├─────────────────────────────────────┤
│ Results                             │
│  Score: 75% F1 (TP: 6/8, FP: 1/7) │
│  ─────────────────────────────────  │
│  Per-output breakdown table         │
│  (output ID, type, verdict, rule)   │
└─────────────────────────────────────┘
```

### Interactions

- Identical to Blue Team WAF Rules challenge for rule editing and submission.
- WHY cards for incorrect results: explains what the dangerous output contained and which regex pattern would have caught it.
- "Beat the baseline" indicator: server-side baseline of 5 simple rules achieves ~50% F1. Display "You beat the baseline!" when participant exceeds it.

---

## Leaderboard Tab

- Same `renderLeaderboard()` from `framework/static/js/core.js`.
- Shows: rank, participant (session ID), D1 score, D2 score, D3 score, total (max 300 pts).
- Sort by total descending.

---

## Shared UI Patterns

- Info tab uses `renderInfoPage()` from `framework/static/js/core.js`.
- Knowledge Check uses `renderKnowledgeCheck()` + `wireKnowledgeCheck()` from framework.
- All attack feedback uses `renderWhyCard()` from framework.
- Tab routing: `renderTabs()` from framework.
- Scoring banners: space-specific, not in framework (different shape for D1 vs. D2 vs. D3).
- Brand: Luminex Learning nav (`.luminex-nav` pattern from red-team/blue-team). AISL violet accent.

---

## Acceptance Checks

- [ ] All 5 tabs render without JS errors
- [ ] D1: classifying all 20 entries and submitting returns correct F1 score server-side
- [ ] D1: WHY card appears immediately after each classification (before submit)
- [ ] D2: sparkline charts render for all 4 metrics with baseline band visible
- [ ] D2: submitting thresholds returns TP/FP window breakdown with correct counts
- [ ] D3: `BLOCK \b\d{3}-\d{2}-\d{4}\b` catches D3.B1 (SSN) without flagging legitimate outputs
- [ ] Leaderboard shows correct aggregation of D1+D2+D3 scores
- [ ] Knowledge Check answers reveal on click with correct explanations
- [ ] Info tab "Where This Lab Fits" shows Detection & Monitoring highlighted in the platform path
