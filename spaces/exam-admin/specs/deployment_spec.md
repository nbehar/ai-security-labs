# Deployment Spec — exam-admin Space

## HuggingFace Space

| Field | Value |
|-------|-------|
| Space name | `nikobehar/ai-sec-lab-exam-admin` |
| SDK | Docker |
| Hardware | `cpu-basic` |
| Visibility | **Private** (instructor-only tool) |
| Port | 7860 |
| Persistent storage | None (in-memory only) |

---

## Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

No system packages required. No ML libraries. `pylti1p3` is pure Python.

---

## requirements.txt

```
fastapi==0.115.12
uvicorn==0.34.2
jinja2==3.1.6
pydantic==2.11.3
slowapi==0.1.9
pylti1p3==2.0.0
httpx==0.28.1
cryptography==44.0.2
```

`cryptography` provides RSA key operations for LTI 1.3 JWK generation and JWT signing. `httpx` is used for AGS grade passback HTTP calls.

---

## Environment Variables / HF Space Secrets

| Variable | Required | Description |
|----------|----------|-------------|
| `EXAM_SECRET` | Required for verification | Shared HMAC secret used by all lab spaces |
| `EXAM_LTI_CLIENT_ID` | Optional | Canvas LTI 1.3 tool client_id |
| `EXAM_LTI_PLATFORM_URL` | Optional | Canvas instance URL, e.g. `https://canvas.university.edu` |
| `EXAM_LTI_LINEITEM_URL` | Optional | Canvas AGS lineitem URL for the exam assignment |
| `EXAM_LTI_PRIVATE_KEY_PEM` | Optional | RSA private key PEM for LTI JWT signing |

If `EXAM_SECRET` is missing, `/api/verify` always returns `hmac_valid: false` with a warning. The space starts without errors — missing secret is a degraded-but-running state.

If any `EXAM_LTI_*` variable is missing, the grade passback endpoints return 503. The JWKS endpoint returns `{"keys": []}`.

---

## Framework Files (copied by deploy.sh)

The following framework files are copied into the space build context at deploy time:
- `framework/exam_token.py` — `verify_receipt()`, `sign_receipt()`
- `framework/exam_questions.py` — `QUESTION_BANKS` (rubric data)

These are **never stored in `spaces/exam-admin/`** in the monorepo. They are injected by `scripts/deploy.sh` which already handles `framework/exam_token.py` and `framework/exam_questions.py`.

---

## LTI 1.3 Setup (one-time, per Canvas instance)

1. In Canvas: **Admin → Developer Keys → + LTI Key**
   - Redirect URI: `https://nikobehar-ai-sec-lab-exam-admin.hf.space/`
   - JWKS URL: `https://nikobehar-ai-sec-lab-exam-admin.hf.space/api/lti/jwks`
   - Target Link URI: `https://nikobehar-ai-sec-lab-exam-admin.hf.space/`
2. Canvas provides a `client_id` → set as `EXAM_LTI_CLIENT_ID` HF Space secret
3. Create a Canvas assignment of type External Tool, link to exam-admin
4. Canvas provides a `lineitem_url` per assignment → set as `EXAM_LTI_LINEITEM_URL` secret
5. Generate an RSA key pair (2048 bit): private key → `EXAM_LTI_PRIVATE_KEY_PEM`, public key is served at `/api/lti/jwks`

---

## State Model

All state is in-memory. No SQLite, no filesystem writes after startup.

- LTI nonce/state registry: `dict` + `threading.Lock` (standard platform pattern)
- No grading session persistence: each instructor workflow is a fresh upload

Acceptable at course volume (< 30 concurrent instructor sessions). If HF Space restarts mid-grading, instructor re-uploads the artifact.

---

## Acceptance Checks

- [ ] `docker build` completes without errors
- [ ] Container starts with no env vars set and returns `GET /health` 200
- [ ] Container starts with `EXAM_SECRET=test` and `POST /api/verify` with a correctly signed receipt returns `hmac_valid: true`
- [ ] `pylti1p3` imports cleanly (pure Python, no C extensions)
- [ ] No ML libraries in image (image size < 400 MB)
