# API Spec — exam-admin Space

## Base

- Base path: `/`
- Port: 7860
- Content-Type: `application/json`
- Rate limiting: `slowapi` — 10 req/min per IP on POST endpoints
- Auth: `EXAM_SECRET` env var is used server-side; clients never send it

---

## Endpoints

### `GET /health`

Returns server status and whether `EXAM_SECRET` is configured.

**Response 200:**
```json
{
  "status": "ok",
  "exam_secret_configured": true,
  "lti_configured": false
}
```

`exam_secret_configured`: `true` if `EXAM_SECRET` env var is non-empty.
`lti_configured`: `true` if all four `EXAM_LTI_*` env vars are set.

---

### `POST /api/verify`

Verify a single signed receipt JSON.

**Request body:**
```json
{
  "receipt": { ...full receipt JSON object including hmac_sha256... }
}
```

**Response 200:**
```json
{
  "hmac_valid": true,
  "receipt_version": "1",
  "exam_id": "spring2026-final",
  "student_id": "jsmith@univ.edu",
  "lab_id": "red-team",
  "practical": {
    "exercises": [
      {
        "exercise_id": "level_1",
        "display_name": "Level 1",
        "max_score": 100,
        "earned_score": 80,
        "attempt_cap": 3,
        "attempts": [...]
      }
    ],
    "total_practical_score": 280,
    "max_practical_score": 500
  },
  "theory": {
    "submitted": true,
    "mcq_score": 45,
    "mcq_max": 50,
    "short_answer_max": 60,
    "short_answers": [...],
    "short_answer_requires_instructor_grading": true
  },
  "timing": {
    "total_elapsed_seconds": 4400,
    "time_limit_seconds": 7200
  }
}
```

**`hmac_valid: false` case (200, not 4xx):**
```json
{
  "hmac_valid": false,
  "error": "HMAC signature mismatch — receipt may have been tampered.",
  "student_id": "jsmith@univ.edu",
  "exam_id": "spring2026-final"
}
```

Note: always return 200 even on HMAC failure; 4xx is reserved for malformed requests.

**Response 400** — body missing `receipt` field or `receipt` is not a JSON object.
**Response 422** — Pydantic validation error.

---

### `POST /api/batch-verify`

Verify multiple receipts in one request.

**Request body:**
```json
{
  "receipts": [
    { ...receipt1 including hmac_sha256... },
    { ...receipt2 including hmac_sha256... }
  ]
}
```

Max 100 receipts per request. Returns 400 if exceeded.

**Response 200:**
```json
{
  "results": [
    {
      "index": 0,
      "hmac_valid": true,
      "student_id": "jsmith@univ.edu",
      "exam_id": "spring2026-final",
      "lab_id": "red-team",
      "practical_score": 280,
      "max_practical_score": 500,
      "mcq_score": 45,
      "mcq_max": 50,
      "theory_submitted": true,
      "elapsed_seconds": 4400,
      "time_limit_seconds": 7200
    }
  ],
  "total": 2,
  "valid_count": 1,
  "invalid_count": 1
}
```

---

### `GET /api/rubric/{lab_id}`

Return short-answer rubric for a lab.

**Path param:** `lab_id` — e.g. `red-team`, `detection-monitoring`.

**Response 200:**
```json
{
  "lab_id": "red-team",
  "short_answers": [
    {
      "question_id": "rt_sa_1",
      "bloom_level": 5,
      "points": 20,
      "word_limit": 200,
      "question": "...",
      "rubric": {
        "technical_accuracy": {"weight": 1.0, "description": "..."},
        "specificity":        {"weight": 1.0, "description": "..."},
        "professional_framing": {"weight": 1.0, "description": "..."},
        "coverage":           {"weight": 1.0, "description": "..."},
        "conciseness":        {"weight": 1.0, "description": "..."}
      }
    }
  ]
}
```

Note: `sample_answer_notes` is NOT included in the response (instructor-internal field stays server-side).

**Response 404** — lab_id not found in QUESTION_BANKS.

---

### `GET /api/lti/jwks`

Return the public JWK Set for LTI 1.3 OIDC verification.

**Response 200:**
```json
{
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "alg": "RS256",
      "kid": "...",
      "n": "...",
      "e": "AQAB"
    }
  ]
}
```

If `EXAM_LTI_PRIVATE_KEY_PEM` is not set, returns `{"keys": []}` with 200.

---

### `POST /api/lti/grade`

Post a single student's grade to Canvas via LTI 1.3 AGS.

**Request body:**
```json
{
  "student_id": "jsmith@univ.edu",
  "lab_id": "red-team",
  "practical_score": 280,
  "max_practical_score": 500,
  "mcq_score": 45,
  "mcq_max": 50,
  "sa_score": 52,
  "sa_max": 60,
  "total_score": 377,
  "total_max": 610,
  "exam_id": "spring2026-final"
}
```

**Response 200:**
```json
{
  "status": "posted",
  "student_id": "jsmith@univ.edu",
  "canvas_response_status": 200
}
```

**Response 503** — LTI not configured.
**Response 502** — Canvas returned a non-2xx response.

---

### `POST /api/lti/batch-grade`

Post grades for multiple students in one call. Body: `{"grades": [...list of /api/lti/grade bodies...]}`. Max 100 entries.

**Response 200:**
```json
{
  "results": [
    {"student_id": "jsmith@univ.edu", "status": "posted"},
    {"student_id": "lwang@univ.edu",  "status": "error", "detail": "..."}
  ]
}
```

---

## Pydantic Schemas

```python
class VerifyRequest(BaseModel):
    receipt: dict

class BatchVerifyRequest(BaseModel):
    receipts: list[dict]

class GradeRequest(BaseModel):
    student_id: str
    lab_id: str
    practical_score: int
    max_practical_score: int
    mcq_score: int
    mcq_max: int
    sa_score: int
    sa_max: int
    total_score: int
    total_max: int
    exam_id: str

class BatchGradeRequest(BaseModel):
    grades: list[GradeRequest]
```

---

## Acceptance Checks

- [ ] `GET /health` returns `exam_secret_configured: true` when env var is set
- [ ] `POST /api/verify` with a receipt signed by `sign_receipt()` returns `hmac_valid: true`
- [ ] `POST /api/verify` with `hmac_sha256` flipped to `"aaaa"` returns `hmac_valid: false` (not 4xx)
- [ ] `POST /api/verify` with `receipt` field missing returns 400
- [ ] `POST /api/batch-verify` with 101 receipts returns 400
- [ ] `GET /api/rubric/red-team` returns a `short_answers` array with 3 entries
- [ ] `GET /api/rubric/unknown` returns 404
- [ ] `GET /api/lti/jwks` returns `{"keys": []}` when `EXAM_LTI_PRIVATE_KEY_PEM` is not set
- [ ] POST endpoints return 429 after 10 req/min per IP
