# API Spec — Detection & Monitoring Lab (Space 6)

## Stack

- **Framework:** FastAPI + Uvicorn (Python 3.11+)
- **Port:** 7860 (HuggingFace Spaces standard)
- **Model calls:** None in v1 — all 3 labs use pre-labeled datasets from `detection_data.py`
- **Rate limiting:** `slowapi` — 10 requests/minute per IP on POST endpoints
- **Input validation:** Pydantic on all request bodies
- **Output:** JSON only (no SSE needed — no streaming)

---

## Endpoints

### `GET /`
Serves `templates/index.html` via Jinja2.

### `GET /health`
```json
{
  "status": "ok",
  "lab": "detection-monitoring",
  "version": "1.0.0",
  "d1_log_count": 20,
  "d2_window_count": 24,
  "d3_output_count": 15
}
```

### `GET /api/logs`
Returns the 20 D1 log entries. Labels are NOT included (server-side only). Order is randomized per request (seeded by session if provided).

**Response:**
```json
{
  "logs": [
    {
      "id": "D1.01",
      "system": "HR Portal",
      "timestamp": "2026-04-28T10:14:32Z",
      "user_query": "...",
      "model_response": "...",
      "metadata": { "user_id": "emp_447", "response_tokens": 142 }
    }
  ]
}
```

**Validation:** None required (read-only).

**Errors:** 500 if dataset not loaded.

---

### `POST /api/logs/classify`
Submit all 20 classifications. Returns score + per-entry feedback.

**Request:**
```json
{
  "classifications": [
    { "id": "D1.01", "label": "LEGITIMATE" },
    { "id": "D1.02", "label": "ATTACK" }
  ],
  "session_id": "optional-uuid"
}
```

**Validation:**
- `classifications` must contain exactly 20 entries
- Each `id` must be a valid log ID
- Each `label` must be `"ATTACK"` or `"LEGITIMATE"`
- 422 on any validation failure

**Response:**
```json
{
  "score": 87.5,
  "f1": 0.875,
  "precision": 1.0,
  "recall": 0.75,
  "tp": 6,
  "fp": 0,
  "fn": 2,
  "tn": 12,
  "entries": [
    {
      "id": "D1.01",
      "submitted_label": "LEGITIMATE",
      "correct_label": "LEGITIMATE",
      "correct": true,
      "why": "Routine HR query — no attack signals. The employee asked about vacation policy using natural language."
    }
  ]
}
```

**Rate limit:** 10/min per IP.

---

### `GET /api/anomaly/data`
Returns the D2 time-series data (24 hourly buckets) without labeling which windows are attacks.

**Response:**
```json
{
  "metrics": ["response_length", "refusal_rate", "query_rate", "confidence"],
  "baseline": {
    "response_length": { "mean": 312, "std": 45 },
    "refusal_rate":    { "mean": 0.08, "std": 0.03 },
    "query_rate":      { "mean": 18, "std": 5 },
    "confidence":      { "mean": 0.82, "std": 0.06 }
  },
  "windows": [
    {
      "hour": 0,
      "response_length": 290,
      "refusal_rate": 0.07,
      "query_rate": 16,
      "confidence": 0.84
    }
  ]
}
```

---

### `POST /api/anomaly/evaluate`
Submit threshold configuration, receive window-level results.

**Request:**
```json
{
  "thresholds": {
    "response_length": { "high": 700 },
    "refusal_rate":    { "low": 0.02 },
    "query_rate":      { "high": 50 },
    "confidence":      { "low": 0.6 }
  },
  "session_id": "optional-uuid"
}
```

**Validation:**
- Each threshold key must be one of the 4 valid metric names
- `high` and `low` are optional per metric (omit = no threshold on that direction)
- 422 on invalid metric name or non-numeric values

**Response:**
```json
{
  "score": 80,
  "tp": 2,
  "fp": 1,
  "attack_windows_detected": ["W1", "W2"],
  "attack_window_missed": ["W3"],
  "windows": [
    {
      "hour": 2,
      "alerted": false,
      "is_attack_window": false,
      "verdict": "TN"
    },
    {
      "hour": 7,
      "alerted": true,
      "is_attack_window": true,
      "attack_id": "W1",
      "verdict": "TP",
      "why": "Query rate spiked to 94 req/min — your threshold of 50 caught this correctly."
    }
  ],
  "missed_why": {
    "W3": "Jailbreak sequence (W3) dropped refusal rate to 0.01. You configured a low-threshold of 0.02 — just below the attack value. Tighten the refusal_rate threshold."
  }
}
```

**Rate limit:** 10/min per IP.

---

### `GET /api/outputs`
Returns the 15 D3 output entries. Labels are NOT included.

**Response:**
```json
{
  "outputs": [
    {
      "id": "D3.01",
      "system": "Finance Chatbot",
      "text": "Your SSN on file is 472-83-9201. Would you like to update it?"
    }
  ]
}
```

---

### `POST /api/outputs/evaluate`
Submit sanitization rules, receive per-output coverage and score.

**Request:**
```json
{
  "rules": "BLOCK \\b\\d{3}-\\d{2}-\\d{4}\\b\nBLOCK (?i)password\\s*[:=]\\s*\\S+",
  "session_id": "optional-uuid"
}
```

**Validation:**
- `rules`: string, max 4096 chars
- Each non-empty line must match `^(BLOCK|ALLOW)\s+\S+$` — 422 otherwise
- Regex syntax errors return 422 with the offending line identified

**Response:**
```json
{
  "score": 75.0,
  "f1": 0.75,
  "precision": 1.0,
  "recall": 0.625,
  "tp": 5,
  "fp": 0,
  "fn": 3,
  "baseline_f1": 0.50,
  "beat_baseline": true,
  "outputs": [
    {
      "id": "D3.01",
      "blocked": true,
      "should_block": true,
      "correct": true,
      "matched_rule": "BLOCK \\b\\d{3}-\\d{2}-\\d{4}\\b",
      "why": "SSN pattern matched. Real output from a Finance Chatbot — SSNs should never appear in model responses."
    }
  ]
}
```

**Rate limit:** 10/min per IP.

---

### `POST /api/score`
Submit final composite score for leaderboard.

**Request:**
```json
{
  "session_id": "uuid",
  "d1_score": 87.5,
  "d2_score": 80.0,
  "d3_score": 75.0,
  "nickname": "optional"
}
```

**Response:**
```json
{
  "total": 242.5,
  "rank": 3
}
```

**Validation:** All three scores must be present, 0–100 each.

---

### `GET /api/leaderboard`
Returns top 20 entries sorted by total descending.

**Response:**
```json
{
  "entries": [
    {
      "rank": 1,
      "nickname": "anon_7a4f",
      "d1": 100.0,
      "d2": 100.0,
      "d3": 87.5,
      "total": 287.5
    }
  ]
}
```

---

## Pydantic Schemas (summary)

```python
class LogClassification(BaseModel):
    id: str
    label: Literal["ATTACK", "LEGITIMATE"]

class ClassifyRequest(BaseModel):
    classifications: list[LogClassification]  # exactly 20
    session_id: str | None = None

class ThresholdValue(BaseModel):
    high: float | None = None
    low:  float | None = None

class AnomalyRequest(BaseModel):
    thresholds: dict[str, ThresholdValue]  # keys: metric names
    session_id: str | None = None

class OutputEvalRequest(BaseModel):
    rules: str = Field(max_length=4096)
    session_id: str | None = None

class ScoreSubmit(BaseModel):
    session_id: str
    d1_score: float = Field(ge=0, le=100)
    d2_score: float = Field(ge=0, le=100)
    d3_score: float = Field(ge=0, le=100)
    nickname: str | None = None
```

---

## Error Handling

- All OCR-style graceful degradation is N/A (no model calls in v1).
- Regex syntax errors in D3 rules: catch `re.error`, return 422 with `{"detail": "Invalid regex at line N: <error>"}`.
- Dataset not loaded: 500 with `{"detail": "Dataset unavailable"}`.
- Rate limit exceeded: 429 with `{"detail": "Rate limit exceeded"}`.

---

## Acceptance Checks

- [ ] `GET /health` returns 200 with correct `d1_log_count: 20`, `d2_window_count: 24`, `d3_output_count: 15`
- [ ] `POST /api/logs/classify` with all 20 correct answers returns `score: 100, f1: 1.0`
- [ ] `POST /api/logs/classify` with 19 entries returns 422
- [ ] `POST /api/anomaly/evaluate` with `response_length.high: 1` (catches everything) returns `tp: 3, fp: 21`
- [ ] `POST /api/outputs/evaluate` with `BLOCK .*` returns `tp: 8, fp: 7, f1: ≈0.53` (catches all dangerous, also catches all legit)
- [ ] `POST /api/outputs/evaluate` with invalid regex `BLOCK [` returns 422 with line number
- [ ] All POST endpoints return 429 after 10 requests/minute
